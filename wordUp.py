import tkinter as tk
import json
import random

# ===== 配置文件路径 =====
CONFIG_PATH = "wordUp_config.json"

# ===== 词库文件路径 =====
# 词库基于https://github.com/5mdld/anki-jlpt-decks 的v3版数据文件 eggrolls-JLPT10k-v3.apkg
# 词库最新地址 https://github.com/5mdld/anki-jlpt-decks/releases
# 本次词库需要使用apkFileTools3.py文件生成json文件
FILE_PATH = "wordUp_words.json"

# ===== 版本 =====
VERSION_INFO = {
    "1": "1.4",# 1：当前软件版本
    "2": "26.03.25_2",# 2：词库版本
}

# ===== 窗口尺寸 =====
WINDOW_SIZES = {
    "1": "500x320", #1：完整模式窗口尺寸
    "2": "400x130" #2：简洁模式窗口尺寸
}

# ===== 自动时间 =====
AUTO_TIMES = {
    "不切换": 0,
    "5秒": 5,
    "15秒": 15,
    "30秒": 30,
    "60秒": 60
}

# ===== 词性映射 =====
pos_map = {
    "n": "名词",
    "adj-i": "い形容词",
    "adj-na": "な形容词",
    "adv": "副词",
    "pn": "代词",
    "conj": "接续词",
    "int": "感叹词",
    "v1": "一类动词 (五段)",
    "v2": "二类动词 (一段)",
    "vs": "サ变动词",
    "vk": "カ变动词",
    "num": "数词",
    "prt": "助词",
    "oth": "其他"
}

# ===== 数据 =====
def load_data():
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===== 配置 =====
def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "mode": "全部",
            "level": "全部",
            "cn": "显示中文",
            "auto": "不切换",
            "ui_mode": "1" #1：完整模式 2：简洁模式
        }

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# ===== 筛选 =====
def get_filtered_data(data, mark_mode, level_mode):
    result = data

    if mark_mode == "已标记":
        result = [w for w in result if w.get("ismark", 0) == 1]
    elif mark_mode == "未标记":
        result = [w for w in result if w.get("ismark", 0) == 0]

    if level_mode != "全部":
        result = [w for w in result if w.get("lv", "").upper() == level_mode]

    return result

# ===== 权重 =====
def get_weight(w):
    base = w.get("freq", 1)
    wrong = w.get("wrong", 0)
    return base + (wrong ** 1.5) * 2

def weighted_choice(words):
    total = 0
    weights = []

    for w in words:
        weight = get_weight(w)
        weights.append((w, weight))
        total += weight

    r = random.uniform(0, total)

    upto = 0
    for w, weight in weights:
        if upto + weight >= r:
            return w
        upto += weight

    return words[-1]

# ===== 主程序 =====
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("WordUp！")

        self.data = load_data()
        self.data_index = {w["id"]: w for w in self.data}

        self.config_data = load_config()
        self.current_word = None
        self.timer_id = None
        self.last_word_id = None

        # ===== UI模式 =====
        self.ui_mode_var = tk.StringVar(value=self.config_data.get("ui_mode", "1"))
        self.root.geometry(WINDOW_SIZES.get(self.ui_mode_var.get(), "500x320"))

        # ===== 顶部 =====
        self.top_frame = tk.Frame(root)
        self.top_frame.pack(pady=5)

        self.mode_var = tk.StringVar(value=self.config_data["mode"])
        tk.OptionMenu(self.top_frame, self.mode_var, "全部", "已标记", "未标记",
                      command=self.on_mode_change).pack(side=tk.LEFT)

        self.level_var = tk.StringVar(value=self.config_data["level"])
        tk.OptionMenu(self.top_frame, self.level_var, "全部", "N5", "N4", "N3",
                      command=self.on_level_change).pack(side=tk.LEFT)

        self.cn_mode = tk.StringVar(value=self.config_data["cn"])
        tk.OptionMenu(self.top_frame, self.cn_mode, "显示中文", "隐藏中文",
                      command=self.on_cn_change).pack(side=tk.LEFT)

        self.auto_var = tk.StringVar(value=self.config_data["auto"])
        tk.OptionMenu(self.top_frame, self.auto_var, *AUTO_TIMES.keys(),
                      command=self.on_auto_change).pack(side=tk.LEFT)

        tk.OptionMenu(self.top_frame, self.ui_mode_var, "1", "2",
                      command=self.on_ui_mode_change).pack(side=tk.LEFT)

        # ===== 内容（改成 Entry）=====
        self.label_id = tk.Label(root, text="", font=("Arial", 10), fg="gray")
        self.label_id.pack(pady=2)

        self.entry_kana = tk.Entry(root, font=("Arial", 12), justify="center", bd=0, highlightthickness=0)
        self.entry_kana.pack(fill="x", padx=10, pady=2)

        self.entry_jp = tk.Entry(root, font=("Arial", 28, "bold"), justify="center")
        self.entry_jp.pack(fill="x", padx=10, pady=5)

        self.entry_cn = tk.Entry(root, font=("Arial", 12), justify="center", bd=0, highlightthickness=0)
        self.entry_cn.pack(fill="x", padx=10, pady=2)

        for e in [self.entry_kana, self.entry_jp, self.entry_cn]:
            e.config(state="readonly")

        self.label_info = tk.Label(root, text="", font=("Arial", 10))
        self.label_info.pack(pady=5)

        # 标记
        self.mark_var = tk.IntVar()
        self.check_mark = tk.Checkbutton(root, text="标记", variable=self.mark_var,
                                         command=self.toggle_mark)
        self.check_mark.pack()

        # 按钮
        self.btn_frame = tk.Frame(root)
        self.btn_frame.pack(pady=5)

        tk.Button(self.btn_frame, text="不会", command=self.mark_wrong).pack(side=tk.LEFT, padx=5)
        tk.Button(self.btn_frame, text="会了", command=self.mark_right).pack(side=tk.LEFT, padx=5)

        # 下一个按钮
        self.btn_next = tk.Button(root, text="下一个", command=self.next_word)
        self.btn_next.pack(pady=8)

        tk.Label(root, text="by yaiba@"+VERSION_INFO.get("1","1.0")+"/"+VERSION_INFO.get("2","1.0"),
                 font=("Arial", 8), fg="#999999")\
            .place(relx=1.0, rely=1.0, anchor="se")

        self.change_auto(None)
        self.apply_ui_mode()
        self.next_word()

        # 快捷键，按空格，切换下一个
        self.root.bind_all("<space>", self.on_space)

        # 窗口置顶
        self.root.attributes("-topmost", True)

        # 或者只在简洁模式启用：
        # if mode == "2":
        #     self.root.attributes("-topmost", True)
        # else:
        #     self.root.attributes("-topmost", False)

    # ===== UI模式 =====
    def on_ui_mode_change(self, _):
        self.config_data["ui_mode"] = self.ui_mode_var.get()
        save_config(self.config_data)

        self.root.geometry(WINDOW_SIZES.get(self.ui_mode_var.get(), "500x320"))
        self.apply_ui_mode()

    def apply_ui_mode(self):
        mode = self.ui_mode_var.get()

        if mode == "2":
            self.top_frame.pack_forget()
            self.label_id.pack_forget()
            self.label_info.pack_forget()
            self.check_mark.pack_forget()
            self.btn_frame.pack_forget()
            self.btn_next.pack_forget()
        else:
            self.top_frame.pack(pady=5)
            self.label_id.pack(pady=2)
            self.label_info.pack(pady=5)
            self.check_mark.pack()
            self.btn_frame.pack(pady=5)
            self.btn_next.pack(pady=8)

    # ===== 配置 =====
    def on_mode_change(self, _):
        self.config_data["mode"] = self.mode_var.get()
        save_config(self.config_data)
        self.next_word()

    def on_level_change(self, _):
        self.config_data["level"] = self.level_var.get()
        save_config(self.config_data)
        self.next_word()

    def on_cn_change(self, _):
        self.config_data["cn"] = self.cn_mode.get()
        save_config(self.config_data)
        self.update_display()

    def on_auto_change(self, _):
        self.config_data["auto"] = self.auto_var.get()
        save_config(self.config_data)
        self.change_auto(None)

    # ===== 设置 Entry 内容 =====
    def set_entry(self, entry, text):
        entry.config(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, text)
        entry.config(state="readonly")

    # ===== 核心 =====
    def next_word(self):
        filtered = get_filtered_data(
            self.data,
            self.mode_var.get(),
            self.level_var.get()
        )

        if not filtered:
            self.set_entry(self.entry_jp, "没有符合条件的词")
            self.set_entry(self.entry_kana, "")
            self.set_entry(self.entry_cn, "")
            self.label_info.config(text="")
            return

        for _ in range(10):
            word = weighted_choice(filtered)
            if word["id"] != self.last_word_id:
                break

        self.current_word = word
        self.last_word_id = word["id"]

        self.update_display()

    def update_display(self):
        if not self.current_word:
            return

        self.set_entry(self.entry_kana, self.current_word["jppjm"])
        self.set_entry(self.entry_jp, self.current_word["jp"])

        if self.cn_mode.get() == "隐藏中文":
            self.set_entry(self.entry_cn, "***")
        else:
            self.set_entry(self.entry_cn, self.current_word["cn"])

        self.label_id.config(text=self.current_word["id"])

        lv = self.current_word["lv"].upper()
        pos = pos_map.get(self.current_word["pos"], self.current_word["pos"])
        wrong = self.current_word.get("wrong", 0)
        freq = self.current_word.get("freq", 0)

        self.label_info.config(text=f"{lv} ｜ {pos} ｜ 词频：{freq} ｜ 不会:{wrong}")
        self.mark_var.set(self.current_word.get("ismark", 0))

    # ===== 数据操作 =====
    def toggle_mark(self):
        w = self.data_index[self.current_word["id"]]
        w["ismark"] = self.mark_var.get()
        save_data(self.data)

    def mark_wrong(self):
        w = self.data_index[self.current_word["id"]]
        w["wrong"] = w.get("wrong", 0) + 1
        save_data(self.data)
        self.next_word()

    def mark_right(self):
        w = self.data_index[self.current_word["id"]]
        w["wrong"] = 0
        save_data(self.data)
        self.next_word()

    # ===== 自动切换 =====
    def change_auto(self, _):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        sec = AUTO_TIMES[self.auto_var.get()]
        if sec > 0:
            self.schedule(sec)

    def schedule(self, sec):
        self.timer_id = self.root.after(sec * 1000, self.auto_next)

    def auto_next(self):
        self.next_word()
        sec = AUTO_TIMES[self.auto_var.get()]
        if sec > 0:
            self.schedule(sec)

    # ===== 空格键 =====
    def on_space(self, event):
        self.root.focus_set()
        self.next_word()


# ===== 启动 =====
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()