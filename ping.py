import subprocess
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext
import requests

# ================= 配置 =================
PING_TARGETS = ["baidu.com", "8.8.8.8", "114.114.114.114"]
HTTP_TARGET = "https://www.baidu.com"
CHECK_INTERVAL = 2
FAIL_THRESHOLD = 3
LOG_FILE = "network_log.txt"

# ================= 核心逻辑 =================
class NetworkMonitor:
    def __init__(self, app):
        self.app = app
        self.fail_count = 0
        self.is_down = False
        self.down_time = None
        self.running = True

    def ping(self, target):
        try:
            result = subprocess.run(
                ["ping", "-n", "1", target],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return "TTL=" in result.stdout
        except:
            return False

    def http_check(self):
        try:
            requests.get(HTTP_TARGET, timeout=3)
            return True
        except:
            return False

    def check_network(self):
        # ping检测（只要一个通就算正常）
        ping_ok = any(self.ping(t) for t in PING_TARGETS)

        # http检测
        http_ok = self.http_check()

        return ping_ok and http_ok

    def log(self, msg):
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")

    def run(self):
        while self.running:
            now = datetime.now().strftime("%H:%M:%S")

            ok = self.check_network()

            if ok:
                self.fail_count = 0

                if self.is_down:
                    up_time = datetime.now()
                    duration = (up_time - self.down_time).seconds
                    msg = f"[{now}] 网络恢复，断网 {duration} 秒"
                    self.app.update_status("正常", "green")
                    self.app.add_log(msg)
                    self.log(msg)
                    self.is_down = False
                else:
                    self.app.update_status("正常", "green")

            else:
                self.fail_count += 1
                self.app.update_status(f"检测失败 {self.fail_count}", "orange")

                if self.fail_count >= FAIL_THRESHOLD and not self.is_down:
                    self.is_down = True
                    self.down_time = datetime.now()
                    msg = f"[{now}] 网络断开！！！"
                    self.app.update_status("断网", "red")
                    self.app.add_log(msg)
                    self.log(msg)

            time.sleep(CHECK_INTERVAL)

# ================= UI =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("网络监控工具")
        self.root.geometry("300x250")
        self.root.attributes("-topmost", True)

        # 状态标签
        self.status_label = tk.Label(root, text="启动中...", font=("Arial", 16))
        self.status_label.pack(pady=10)

        # 日志框
        self.log_area = scrolledtext.ScrolledText(root, height=8)
        self.log_area.pack(fill=tk.BOTH, padx=5, pady=5)

        # 按钮
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        self.start_btn = tk.Button(btn_frame, text="开始", command=self.start)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="停止", command=self.stop)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.monitor = NetworkMonitor(self)
        self.thread = None

    def update_status(self, text, color):
        self.status_label.config(text=text, fg=color)

    def add_log(self, msg):
        self.log_area.insert(tk.END, msg + "\n")
        self.log_area.see(tk.END)

    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.monitor.running = True
            self.thread = threading.Thread(target=self.monitor.run, daemon=True)
            self.thread.start()
            self.add_log("开始监控...")

    def stop(self):
        self.monitor.running = False
        self.add_log("停止监控")

# ================= 入口 =================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
# 打包成exe的命令
# pyinstaller --onefile --noconsole pyautogui/ping.py