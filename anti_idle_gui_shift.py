import pyautogui
import threading
import time
import tkinter as tk
from tkinter import ttk

running = False

def worker():
    global running
    while running:
        try:
            pyautogui.press('shift')
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
root.title("shift")
root.geometry("200x150")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="间隔（秒）:").pack()

interval_var = tk.IntVar(value=60)
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

root.mainloop()

# 打包成exe的命令
# pyinstaller --onefile --noconsole pyautogui/anti_idle_gui_shift.py