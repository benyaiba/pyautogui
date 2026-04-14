import tkinter as tk
import json
import random

# ===== 文件路径 =====
FILE_PATH = "wordUp_words.json"
CONFIG_PATH = "wordUp_config.json"

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
            "auto": "不切换"
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

# ===== 优化1：无爆内存权重抽取 =====
def get_weight(w):
    base = w.get("freq", 1)
    wrong = w.get("wrong", 0)

    # 推荐平衡公式（核心升级）
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
        self.root.geometry("320x330")

        self.data = load_data()

        # ===== 优化2：ID索引（O(1)查找）=====
        self.data_index = {w["id"]: w for w in self.data}

        self.config_data = load_config()
        self.current_word = None
        self.timer_id = None
        self.last_word_id = None

        # ===== 顶部 =====
        top = tk.Frame(root)
        top.pack(pady=5)

        self.mode_var = tk.StringVar(value=self.config_data["mode"])
        tk.OptionMenu(top, self.mode_var, "全部", "已标记", "未标记",
                      command=self.on_mode_change).pack(side=tk.LEFT)

        self.level_var = tk.StringVar(value=self.config_data["level"])
        tk.OptionMenu(top, self.level_var, "全部", "N5", "N4", "N3",
                      command=self.on_level_change).pack(side=tk.LEFT)

        self.cn_mode = tk.StringVar(value=self.config_data["cn"])
        tk.OptionMenu(top, self.cn_mode, "显示中文", "隐藏中文",
                      command=self.on_cn_change).pack(side=tk.LEFT)

        self.auto_var = tk.StringVar(value=self.config_data["auto"])
        tk.OptionMenu(top, self.auto_var, *AUTO_TIMES.keys(),
                      command=self.on_auto_change).pack(side=tk.LEFT)

        # ===== 内容 =====
        self.label_id = tk.Label(root, text="", font=("Arial", 10), fg="gray")
        self.label_id.pack()

        self.label_kana = tk.Label(root, text="", font=("Arial", 12), fg="gray")
        self.label_kana.pack()

        self.label_jp = tk.Label(root, text="", font=("Arial", 28, "bold"), bd=1, relief="solid")
        self.label_jp.pack(pady=5)

        self.label_cn = tk.Label(root, text="", font=("Arial", 12), fg="gray")
        self.label_cn.pack()

        self.label_info = tk.Label(root, text="", font=("Arial", 10))
        self.label_info.pack(pady=5)

        # 标记
        self.mark_var = tk.IntVar()
        tk.Checkbutton(root, text="标记", variable=self.mark_var,
                       command=self.toggle_mark).pack()

        # 按钮
        btn = tk.Frame(root)
        btn.pack(pady=5)

        tk.Button(btn, text="不会", command=self.mark_wrong).pack(side=tk.LEFT, padx=5)
        tk.Button(btn, text="会了", command=self.mark_right).pack(side=tk.LEFT, padx=5)

        tk.Button(root, text="下一个", command=self.next_word).pack(pady=8)

        tk.Label(root, text="by yaiba@v1.0",
                 font=("Arial", 8), fg="#999999")\
            .place(relx=1.0, rely=1.0, anchor="se")

        self.change_auto(None)
        self.next_word()

        # ===== 优化3：更稳定的空格键 =====
        self.root.bind_all("<space>", self.on_space)

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

    # ===== 核心 =====
    def next_word(self):
        filtered = get_filtered_data(
            self.data,
            self.mode_var.get(),
            self.level_var.get()
        )

        if not filtered:
            self.label_jp.config(text="没有符合条件的词")
            self.label_kana.config(text="")
            self.label_cn.config(text="")
            self.label_info.config(text="")
            return

        # ===== 优化4：避免连续重复 =====
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

        self.label_kana.config(text=self.current_word["jppjm"])
        self.label_jp.config(text=self.current_word["jp"])
        self.label_id.config(text=self.current_word["id"])

        if self.cn_mode.get() == "隐藏中文":
            self.label_cn.config(text="***")
        else:
            self.label_cn.config(text=self.current_word["cn"])

        lv = self.current_word["lv"].upper()
        pos = pos_map.get(self.current_word["pos"], self.current_word["pos"])
        wrong = self.current_word.get("wrong", 0)
        freq = self.current_word.get("freq", 0)

        self.label_info.config(text=f"{lv} ｜ {pos} ｜ 词频：{freq} ｜ 不会:{wrong}")

        self.mark_var.set(self.current_word.get("ismark", 0))

    # ===== 数据操作（优化5：O(1)查找）=====
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

# pyinstaller --onefile --noconsole pyautogui/wordUp.py

