import zipfile
import sqlite3
import json
import os
import re
import shutil
import tempfile
import html
from pathlib import Path


def clean_html(text, keep_links=False):
    """
    去除 HTML 标签，保留纯文本。
    如果 keep_links=True，则保留 <a> 标签中的 href 作为文本的一部分。
    """
    if not text:
        return ""
    # 先替换常见的块级换行标签
    text = text.replace('<br>', '\n').replace('<br/>', '\n').replace('<br />', '\n')
    text = text.replace('</div><div>', '\n').replace('</p><p>', '\n')

    if keep_links:
        # 将 <a href="...">text</a> 替换为 "text [url]"
        def repl_link(match):
            link_text = match.group(1)
            url = match.group(2)
            return f"{link_text} [{url}]"

        text = re.sub(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>', repl_link, text, flags=re.IGNORECASE)

    # 移除所有 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 解码 HTML 实体（如 &nbsp; -> 空格）
    text = html.unescape(text)
    # 合并多余的空白行
    text = re.sub(r'\n\s*\n', '\n\n', text).strip()
    return text


def extract_media(apkg_path, output_media_dir):
    """
    从 .apkg 中提取所有媒体文件到 output_media_dir。
    返回一个字典：原始文件名 -> 本地绝对路径。
    """
    media_map = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        # 解压整个 apkg
        with zipfile.ZipFile(apkg_path, 'r') as zf:
            zf.extractall(tmpdir)

        # 查找 media 索引文件
        media_json_path = None
        for f in os.listdir(tmpdir):
            if f == "media" or f.endswith(".media"):
                media_json_path = os.path.join(tmpdir, f)
                break
        if not media_json_path:
            print("未找到 media 索引文件，无媒体文件可提取。")
            return media_map

        # 读取索引：{"filename": "数字文件名"} 或 {"数字文件名": "filename"} ？Anki 2.1 通常是前者
        with open(media_json_path, 'r', encoding='utf-8') as f:
            media_data = json.load(f)

        # media_data 可能有两种格式：
        # 格式1 (Anki 2.0): 列表，索引对应数字文件名，值为原始文件名
        # 格式2 (Anki 2.1): 字典，键为原始文件名，值为数字文件名
        # 我们统一转换为：原始文件名 -> 数字文件名（或直接是路径）
        if isinstance(media_data, list):
            # 列表格式：索引 i 对应文件名，数字文件名为 i（无后缀？）
            # 实际上媒体文件命名为 "i" 或 "i.ext"，需要扫描文件系统
            for idx, fname in enumerate(media_data):
                if fname:
                    # 查找实际文件（可能有扩展名）
                    for ext in ['', '.jpg', '.png', '.mp3', '.ogg', '.wav', '.svg']:
                        candidate = os.path.join(tmpdir, str(idx) + ext)
                        if os.path.exists(candidate):
                            media_map[fname] = candidate
                            break
        elif isinstance(media_data, dict):
            # 字典格式：键为原始文件名，值为数字字符串
            for original_name, idx_str in media_data.items():
                # 查找数字文件（可能有扩展名）
                found = None
                for ext in ['', '.jpg', '.png', '.mp3', '.ogg', '.wav', '.svg']:
                    candidate = os.path.join(tmpdir, idx_str + ext)
                    if os.path.exists(candidate):
                        found = candidate
                        break
                if found:
                    media_map[original_name] = found
                else:
                    # 有些文件直接以数字为名，无扩展名
                    candidate = os.path.join(tmpdir, idx_str)
                    if os.path.exists(candidate):
                        media_map[original_name] = candidate

        # 创建输出目录并复制文件
        os.makedirs(output_media_dir, exist_ok=True)
        new_map = {}
        for original, src_path in media_map.items():
            # 清理文件名中的非法字符
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', original)
            dest_path = os.path.join(output_media_dir, safe_name)
            shutil.copy2(src_path, dest_path)
            new_map[original] = dest_path
            print(f"  媒体文件: {original} -> {dest_path}")

        return new_map


def read_apkg(apkg_path, media_output_dir=None, clean_html_flag=True):
    """
    增强版 apkg 读取器。
    :param apkg_path: .apkg 文件路径
    :param media_output_dir: 媒体文件输出目录，若为 None 则不提取媒体
    :param clean_html_flag: 是否清洗 HTML 标签（若为 False 则保留原始 HTML）
    """
    tmp_dir = None
    conn = None
    try:
        # 1. 临时解压
        tmp_dir = tempfile.TemporaryDirectory()
        extract_path = tmp_dir.name
        with zipfile.ZipFile(apkg_path, 'r') as zf:
            zf.extractall(extract_path)

        # 2. 查找数据库文件
        db_file = None
        for f in os.listdir(extract_path):
            if f.endswith('.anki2'):
                db_file = os.path.join(extract_path, f)
                break
        if not db_file:
            print("未找到 .anki2 数据库文件")
            return

        # 3. 提取媒体文件（如果指定了输出目录）
        media_map = {}
        if media_output_dir:
            media_map = extract_media(apkg_path, media_output_dir)

        # 4. 连接数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # 获取所有表名，判断牌组信息位置
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        has_decks = 'decks' in tables

        # 获取牌组名称映射（如果有 col 表）
        deck_name_map = {}
        if 'col' in tables:
            cursor.execute("SELECT decks FROM col")
            row = cursor.fetchone()
            if row and row[0]:
                try:
                    decks_json = row[0]
                    decks = json.loads(decks_json)
                    # decks 的 key 是 did (int)，value 是 dict，包含 name
                    deck_name_map = {int(did): info.get('name', 'Unknown') for did, info in decks.items()}
                except:
                    pass

        # 构建查询语句
        if has_decks:
            # 直接 JOIN decks 表
            query = """
                SELECT n.id, n.flds, c.id, c.due, d.name
                FROM notes n
                JOIN cards c ON c.nid = n.id
                JOIN decks d ON c.did = d.id
                ORDER BY n.id
            """
            cursor.execute(query)
            rows = cursor.fetchall()
        else:
            # 使用 col 表获取牌组名
            query = """
                SELECT n.id, n.flds, c.id, c.due, c.did
                FROM notes n
                JOIN cards c ON c.nid = n.id
                ORDER BY n.id
            """
            cursor.execute(query)
            rows = cursor.fetchall()

        if not rows:
            print("未找到任何卡片。")
            return

        print(f"成功读取 '{os.path.basename(apkg_path)}'，共 {len(rows)} 张卡片。\n")

        # 5. 处理每张卡片
        for idx, row in enumerate(rows, 1):
            if has_decks:
                note_id, raw_fields, card_id, due_date, deck_name = row
            else:
                note_id, raw_fields, card_id, due_date, did = row
                deck_name = deck_name_map.get(did, "未知牌组")

            # 分割字段
            fields = raw_fields.split('\x1f')

            # 清洗每个字段（如果启用）
            cleaned_fields = []
            for field in fields:
                if clean_html_flag:
                    # 先替换媒体引用为本地路径（如果提取了媒体）
                    text = field
                    if media_map:
                        # 处理 <img src="filename">
                        for orig_name, local_path in media_map.items():
                            # 替换 src="filename" 为 src="local_path" 或直接提示
                            text = text.replace(f'src="{orig_name}"', f'src="{local_path}"')
                            text = text.replace(f"src='{orig_name}'", f"src='{local_path}'")
                            # 处理 [sound:filename] 格式
                            text = text.replace(f'[sound:{orig_name}]', f'[音频: {local_path}]')
                        # 清洗 HTML
                        cleaned = clean_html(text, keep_links=False)
                    else:
                        cleaned = clean_html(field, keep_links=False)
                    cleaned_fields.append(cleaned)
                else:
                    cleaned_fields.append(field)

            # 打印卡片信息
            print(f"卡片 #{idx} (ID: {card_id})")
            print(f"  牌组: {deck_name}")
            print(f"  到期日: {due_date}")
            print("  内容:")
            for i, field in enumerate(cleaned_fields):
                # 限制显示长度
                display_field = field[:300] + ("..." if len(field) > 300 else "")
                print(f"    字段 {i + 1}: {display_field}")
            print("-" * 60)

    except sqlite3.OperationalError as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        if conn:
            conn.close()
        if tmp_dir:
            try:
                tmp_dir.cleanup()
            except PermissionError:
                print(f"警告：临时目录清理失败，可手动删除：{tmp_dir.name}")


if __name__ == "__main__":
    # 使用示例
    apkg_file = r"C:\Users\User\PycharmProjects\PythonProject\pyautogui\eggrolls-JLPT10k-v3.apkg"  # 替换为你的文件路径
    media_folder = r"./extracted_media"  # 媒体文件保存目录，若不需要提取可设为 None

    if not os.path.exists(apkg_file):
        print(f"文件不存在: {apkg_file}")
    else:
        read_apkg(apkg_file, media_output_dir=media_folder, clean_html_flag=True)