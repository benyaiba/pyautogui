import tkinter as tk
from tkinter import scrolledtext
import requests
import base64
import json
import time
import uuid
from datetime import datetime
import threading
import random
import platform
import os

# ========= GitHub 配置 =========
GITHUB_TOKEN = "----"  # ⚠️ 建议后面改成环境变量
OWNER = "benyaiba"
REPO = "oneEXE"
FILE_PATH = "digu_message.txt"
BRANCH = "main"

# ========= 程序 配置 =========
MAX_MESSAGES = 100 # 显示的最大件数
APP_VERSION = "v1.0.0"
APP_AUTHOR = "yaiba"

# ========= 设备标识 =========
def get_device_name():
    name = platform.node()
    return f"PC-{name[-4:]}"  # 简短唯一标识
# ========= 增加 UID =========
def get_or_create_uid():
    config_dir = os.path.join(os.getenv("APPDATA"), "digu")
    os.makedirs(config_dir, exist_ok=True)

    file = os.path.join(config_dir, "uid.txt")

    if os.path.exists(file):
        with open(file, "r") as f:
            return f.read().strip()
    else:
        uid = uuid.uuid4().hex[:8]
        with open(file, "w") as f:
            f.write(uid)
        return uid


# ========= GitHub =========
def get_file_content():
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    params = {"ref": BRANCH}

    r = requests.get(url, headers=headers, params=params)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content, data["sha"]
    elif r.status_code == 404:
        return "", None
    return "", None


def update_file(new_content, sha, msg):
    url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    data = {
        "message": msg,
        "content": base64.b64encode(new_content.encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha

    return requests.put(url, headers=headers, data=json.dumps(data))


def send_message(user, uid, text):
    if not text.strip():
        return

    for _ in range(3):
        content, sha = get_file_content()

        msg_data = {
            "id": f"{int(time.time()*1000)}_{uuid.uuid4().hex[:4]}",
            "uid": uid,
            "user": user,
            "time": datetime.now().strftime("%H:%M:%S"),
            "msg": text
        }

        line = json.dumps(msg_data, ensure_ascii=False)
        new_content = content.rstrip() + "\n" + line if content.strip() else line

        r = update_file(new_content, sha, f"{user} 发送消息")

        if r.status_code in [200, 201]:
            return
        elif r.status_code == 409:
            time.sleep(0.5)


# ========= UI =========
class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("轻量聊天室")
        self.root.geometry("500x600")

        # ⭐ 固定设备名
        self.device_name = get_device_name()

        # 初始化里增加 UID
        self.uid = get_or_create_uid()

        # ===== 顶部（右上角设备名）=====
        top = tk.Frame(root)
        top.pack(fill=tk.X)

        tk.Label(
            top,
            text=f"设备: {self.device_name}   ID: {self.uid}",
            fg="gray"
        ).pack(side=tk.LEFT, padx=5)

        # ===== 聊天框 =====
        self.chat_box = scrolledtext.ScrolledText(root, state='disabled')
        self.chat_box.pack(expand=True, fill=tk.BOTH)

        # ===== 输入区 =====
        bottom = tk.Frame(root)
        bottom.pack(fill=tk.X)

        self.input_box = tk.Entry(bottom)
        self.input_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Button(bottom, text="发送", command=self.on_send).pack(side=tk.RIGHT)

        self.input_box.bind("<Return>", lambda e: self.on_send())

        # ===== 状态 =====
        self.seen_ids = set()
        self.user_colors = {}

        threading.Thread(target=self.refresh_loop, daemon=True).start()

        # ===== 底部版权信息 =====
        footer = tk.Frame(root)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(
            footer,
            text=f"© 2026 {APP_AUTHOR} | {APP_VERSION}",
            fg="gray",
            font=("Arial", 8)
        ).pack(pady=2)


    def get_user_color(self, user):
        if user not in self.user_colors:
            colors = ["red", "blue", "green", "purple", "orange"]
            self.user_colors[user] = random.choice(colors)
        return self.user_colors[user]

    def add_message(self, msg):
        self.chat_box.config(state='normal')

        tag = msg["user"]
        color = self.get_user_color(msg["user"])

        if tag not in self.chat_box.tag_names():
            self.chat_box.tag_config(tag, foreground=color)

        self.chat_box.insert(
            tk.END,
            f"[{msg['time']}] {msg['user']}：",
            tag
        )
        self.chat_box.insert(tk.END, f"{msg['msg']}\n")

        self.chat_box.config(state='disabled')
        self.chat_box.yview(tk.END)

    def on_send(self):
        text = self.input_box.get()

        self.input_box.delete(0, tk.END)

        threading.Thread(
            target=send_message,
            args=(self.device_name, self.uid, text),
            daemon=True
        ).start()

    def refresh_loop(self):
        while True:
            try:
                content, _ = get_file_content()
                lines = content.splitlines()[-MAX_MESSAGES:]  # 最大加载条数

                for line in lines:
                    try:
                        msg = json.loads(line)
                        if msg["id"] not in self.seen_ids:
                            self.seen_ids.add(msg["id"])
                            self.root.after(0, self.add_message, msg)
                    except:
                        pass

            except Exception as e:
                print("刷新失败", e)

            time.sleep(2)


# ========= 启动 =========
if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()

# pyinstaller --onefile --noconsole pyautogui/digu.py