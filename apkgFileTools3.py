import zipfile
import sqlite3
import json
import os
import re

APKG_FILE = "eggrolls-JLPT10k-v3.apkg"
EXTRACT_DIR = "apkg_extract"
OUTPUT_JSON = "output.json"

#可以读取 https://github.com/5mdld/anki-jlpt-decks 的v3版数据文件
#读取期日语词库然后生成json文件，给wordup.py使用
# -----------------------
# 解压 apkg
# -----------------------
def extract_apkg(apkg_path, extract_dir):
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    with zipfile.ZipFile(apkg_path, 'r') as z:
        z.extractall(extract_dir)

    print("解压完成")


# -----------------------
# 自动选择数据库
# -----------------------
def open_db(extract_dir):
    for name in ["collection.anki21", "collection.anki2"]:
        db_path = os.path.join(extract_dir, name)
        if os.path.exists(db_path):
            print(f"使用数据库: {name}")
            return sqlite3.connect(db_path)

    raise FileNotFoundError("未找到 collection 数据库")


# -----------------------
# 去 HTML 标签
# -----------------------
def clean_html(text):
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("&nbsp;", " ")
    return text.strip()


# -----------------------
# 提取音频
# -----------------------
def extract_sound(text):
    matches = re.findall(r"\[sound:(.*?)\]", text)
    return matches


# -----------------------
# 解析 notes
# -----------------------
def parse_notes(conn):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, flds, tags FROM notes
    """)

    results = []

    for row in cursor.fetchall():
        note_id, flds, tags = row

        fields = [clean_html(f) for f in flds.split("\x1f")]

        sounds = []
        for f in fields:
            sounds.extend(extract_sound(f))

        results.append({
            "id": note_id,
            "fields": fields,
            "tags": tags,
            "sounds": sounds
        })

    return results


# -----------------------
# media 映射
# -----------------------
def load_media_map(extract_dir):
    media_file = os.path.join(extract_dir, "media")

    if not os.path.exists(media_file):
        return {}

    with open(media_file, "r", encoding="utf-8") as f:
        return json.load(f)


# -----------------------
# 转换成你需要的格式（可改）
# -----------------------
def convert_to_vocab(notes):
    vocab_list = []

    for i, n in enumerate(notes, start=1):
        f = n["fields"]

        jp = f[1] if len(f) > 1 else ""        # 单词
        accent = f[2] if len(f) > 2 else ""    # 音调（⓪①②）
        pos = f[3] if len(f) > 3 else ""       # 词性
        kana = f[4] if len(f) > 4 else ""      # 假名（很关键）
        cn = f[5] if len(f) > 5 else ""        # 中文

        vocab_list.append({
            "id": i,
            "jp": jp,
            "jppjm": kana,
            "cn": cn,
            "pos": pos,
            "lv": "",
            "freq": 0,
            "accent": accent
        })

    return vocab_list

def convert_to_wordup_format(notes):
    result = []

    accent_map = {
        "⓪": 0,
        "①": 1,
        "②": 2,
        "③": 3,
        "④": 4,
        "⑤": 5
    }

    # 适配你程序的 pos_map（反向）
    pos_map = {
        "名": "n",
        "動": "v1",
        "动": "v1",
        "形": "adj-i",
        "形動": "adj-na",
        "副": "adv",
        "代": "pn",
        "接续": "conj",
        "感": "int",
        "数": "num",
        "助": "prt"
    }

    for i, n in enumerate(notes, start=1):
        f = n["fields"]

        jp = f[1] if len(f) > 1 else ""
        accent_raw = f[2] if len(f) > 2 else ""
        pos_raw = f[3] if len(f) > 3 else ""
        kana = f[4] if len(f) > 4 else ""
        cn = f[5] if len(f) > 5 else ""

        result.append({
            "id": i,
            "jp": jp,
            "jppjm": kana,
            "cn": cn,
            "pos": pos_map.get(pos_raw, "oth"),
            "lv": guess_level(i),
            "freq": guess_freq(i),
            "wrong": 0,
            "ismark": 0,
            "accent": accent_map.get(accent_raw, -1)
        })

    return result


def guess_level(index):
    if index <= 1500:
        return "N5"
    elif index <= 3000:
        return "N4"
    else:
        return "N3"



def guess_freq(index):
    if index <= 1000:
        return 5
    elif index <= 3000:
        return 4
    elif index <= 6000:
        return 3
    elif index <= 8000:
        return 2
    else:
        return 1

# -----------------------
# 主流程
# -----------------------
def main():
    extract_apkg(APKG_FILE, EXTRACT_DIR)

    print("文件列表:", os.listdir(EXTRACT_DIR))

    conn = open_db(EXTRACT_DIR)

    notes = parse_notes(conn)

    print(f"共读取 {len(notes)} 条 note")

    # 打印前5条看看结构（非常重要）
    for n in notes[:5]:
        print("=" * 50)
        print(n["fields"])

    # 转换
    #vocab = convert_to_vocab(notes)
    vocab = convert_to_wordup_format(notes)

    # 保存 JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(vocab, f, ensure_ascii=False, indent=2)

    print(f"\n已导出 -> {OUTPUT_JSON}")


if __name__ == "__main__":
    main()