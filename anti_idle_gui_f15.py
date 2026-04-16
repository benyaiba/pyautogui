import os
import sys

import pyautogui
import threading
import time
import tkinter as tk
from tkinter import ttk

running = False
SLEEP_TIME = 50

def worker():
    global running
    while running:
        try:
            pyautogui.press('f15')
        except:
            pass
        time.sleep(interval_var.get())

def start():
    global running
    if not running:
        running = True
        threading.Thread(target=worker, daemon=True).start()
        status_label.config(text="运行中", foreground="green")

def stop():
    global running
    running = False
    status_label.config(text="已停止", foreground="red")

# GUI
root = tk.Tk()
root.title("F15")
root.geometry("200x150")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="间隔（秒）:").pack()

interval_var = tk.IntVar(value=SLEEP_TIME)
interval_input = ttk.Entry(frame, textvariable=interval_var, width=10)
interval_input.pack()

ttk.Button(frame, text="开始", command=start).pack(pady=5)
ttk.Button(frame, text="停止", command=stop).pack()

status_label = ttk.Label(frame, text="已停止", foreground="red")
status_label.pack(pady=5)

footer_label = tk.Label(
    root,
    text="by yaiba",
    fg="gray",
    font=("微软雅黑", 8)
)
footer_label.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

root.iconbitmap(resource_path("UnplatedFolder.ico"))

root.mainloop()

# 打包成exe的命令
# pyinstaller --onefile --noconsole pyautogui/anti_idle_gui_f15.py

# 打包成白色的图标
# pyinstaller --onefile --noconsole pyautogui/anti_idle_gui_f15.py --add-data "pyautogui/ico/move_to_folder_icon.png;."

# 打包成黄色的图标 ---现在用的是这个
# pyinstaller --onefile --noconsole pyautogui/anti_idle_gui_f15.py --add-data "pyautogui/ico/UnplatedFolder.ico;."