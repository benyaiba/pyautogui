import tkinter as tk
import requests
from datetime import datetime

# =============================
# 数据获取部分
# =============================

# 国际金价
def get_gold_price():
    try:
        url = "https://api.metals.live/v1/spot/gold"
        data = requests.get(url, timeout=5).json()
        price_usd = data[0][1]
        return price_usd / 31.1035  # 转换为每克
    except:
        return None


# 上证指数
def get_sh_index():
    try:
        url = "http://hq.sinajs.cn/list=s_sh000001"
        res = requests.get(url).text

        data = res.split(",")
        name = data[0].split('"')[1]
        price = float(data[1])
        change = float(data[2])
        percent = float(data[3])

        return name, price, change, percent
    except:
        return None


# 沪深300
def get_hs300():
    try:
        url = "http://hq.sinajs.cn/list=s_sz399300"
        res = requests.get(url).text

        data = res.split(",")
        name = data[0].split('"')[1]
        price = float(data[1])
        change = float(data[2])
        percent = float(data[3])

        return name, price, change, percent
    except:
        return None


# =============================
# GUI部分
# =============================

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("行情监控")
        self.root.geometry("260x180")
        self.root.resizable(False, False)

        # 主容器
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack()

        self.gold_label = tk.Label(frame, text="💰 金价加载中...")
        self.gold_label.pack(anchor="w")

        self.sh_label = tk.Label(frame, text="📈 上证加载中...")
        self.sh_label.pack(anchor="w")

        self.hs_label = tk.Label(frame, text="📊 沪深300加载中...")
        self.hs_label.pack(anchor="w")

        self.time_label = tk.Label(frame, text="")
        self.time_label.pack(anchor="e", pady=(10, 0))

        self.update_data()

    def update_data(self):
        # 金价
        gold = get_gold_price()
        if gold:
            self.gold_label.config(text=f"💰 金价: {gold:.2f} USD/g")

        # 上证
        sh = get_sh_index()
        if sh:
            name, price, change, percent = sh
            color = "red" if change > 0 else "green"
            arrow = "↑" if change > 0 else "↓"
            self.sh_label.config(
                text=f"📈 {name}: {price:.0f} {arrow}{percent:.2f}%",
                fg=color
            )

        # 沪深300
        hs = get_hs300()
        if hs:
            name, price, change, percent = hs
            color = "red" if change > 0 else "green"
            arrow = "↑" if change > 0 else "↓"
            self.hs_label.config(
                text=f"📊 {name}: {price:.0f} {arrow}{percent:.2f}%",
                fg=color
            )

        # 时间
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f"⏰ {now}")

        # 每30秒刷新
        self.root.after(30000, self.update_data)


# =============================
# 启动
# =============================

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

# pyinstaller --onefile --noconsole pyautogui/gold_biga.py