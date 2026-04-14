import zipfile
import sqlite3
import os
import tempfile
import sys

def read_apkg(apkg_path):
    """
    读取 .apkg 文件并打印卡片内容（兼容 Anki 2.0 / 2.1）
    """
    tmp_dir = None
    conn = None
    try:
        # 创建临时目录
        tmp_dir = tempfile.TemporaryDirectory()
        zip_path = tmp_dir.name

        # 1. 解压 .apkg
        with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
            zip_ref.extractall(zip_path)

        # 2. 查找数据库文件
        db_file = None
        for f in os.listdir(zip_path):
            if f.endswith('.anki2') or f == 'collection.anki2':
                db_file = os.path.join(zip_path, f)
                break
        if not db_file:
            print("未找到数据库文件 (.anki2)")
            return

        # 3. 连接数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # 获取所有表名，以便动态适应
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print("数据库中的表:", tables)

        # 检查 decks 表是否存在
        has_decks = 'decks' in tables

        # 构建查询语句
        if has_decks:
            query = """
                SELECT n.id, n.flds, c.id, c.due, d.name
                FROM notes n
                JOIN cards c ON c.nid = n.id
                JOIN decks d ON c.did = d.id
                ORDER BY n.id
            """
        else:
            # 没有 decks 表就只查 notes 和 cards
            query = """
                SELECT n.id, n.flds, c.id, c.due, NULL
                FROM notes n
                JOIN cards c ON c.nid = n.id
                ORDER BY n.id
            """
        cursor.execute(query)
        rows = cursor.fetchall()

        if not rows:
            print("没有找到任何卡片。")
            return

        print(f"成功读取 '{os.path.basename(apkg_path)}'，共 {len(rows)} 张卡片。\n")

        # 4. 解析并打印
        for note_id, raw_fields, card_id, due_date, deck_name in rows:
            # 字段分隔符是 ASCII 31
            fields = raw_fields.split('\x1f')
            print(f"卡片 ID: {card_id}")
            if has_decks and deck_name:
                print(f"牌组: {deck_name}")
            print(f"到期日: {due_date}")
            print("卡片内容:")
            for i, field in enumerate(fields):
                # 简单清理 HTML
                clean = field.replace('<br>', ' ').replace('</div><div>', ' ').strip()
                # 限制长度
                if len(clean) > 100:
                    clean = clean[:100] + "..."
                print(f"  字段 {i+1}: {clean}")
            print("-" * 40)

    except sqlite3.OperationalError as e:
        print(f"数据库错误: {e}")
        print("提示：可能数据库结构不兼容，请检查 .apkg 文件是否损坏或为旧版本。")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        # 确保数据库连接关闭
        if conn:
            conn.close()
        # 删除临时目录
        if tmp_dir:
            try:
                tmp_dir.cleanup()
            except PermissionError:
                # Windows 下有时无法立即删除，可以忽略或稍后重试
                print("警告：临时目录清理失败，可手动删除：", tmp_dir.name)

if __name__ == "__main__":
    # 请修改为你的 .apkg 文件路径
    apkg_file_path = r'C:\Users\User\PycharmProjects\PythonProject\pyautogui\JLPT_N5_Vocab.apkg'
    if not os.path.exists(apkg_file_path):
        print(f"文件不存在: {apkg_file_path}")
        sys.exit(1)
    read_apkg(apkg_file_path)