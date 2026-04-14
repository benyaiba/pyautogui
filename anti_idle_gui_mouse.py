import pyautogui
import random
import tkinter as tk
from tkinter import ttk

running = False

def loop():
    global running
    if running:
        try:
            x, y = pyautogui.position()

            r = range_var.get()
            dx = random.randint(-r, r)
            dy = random.randint(-r, r)

            pyautogui.moveTo(x + dx, y + dy, duration=0.2)
        except:
            pass

        root.after(interval_var.get() * 1000, loop)

def start():
    global running
    if not running:
        running = True
        status_label.config(text="运行中", fg="green")
        loop()  # 立即执行一次

def stop():
    global running
    running = False
    status_label.config(text="已停止", fg="red")

# GUI
root = tk.Tk()
root.title("move")
root.geometry("200x190")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="间隔（秒）:").pack()

interval_var = tk.IntVar(value=60)
ttk.Entry(frame, textvariable=interval_var, width=10).pack()

ttk.Label(frame, text="移动范围（像素）:").pack(pady=(5,0))

range_var = tk.IntVar(value=3)
ttk.Entry(frame, textvariable=range_var, width=10).pack()

ttk.Button(frame, text="开始", command=start).pack(pady=5)
ttk.Button(frame, text="停止", command=stop).pack()

footer_label = tk.Label(
    root,
    text="by yaiba",
    fg="gray",
    font=("微软雅黑", 8)
)
footer_label.place(relx=1.0, rely=1.0, anchor="se", x=-5, y=-5)

# 🔥 关键：用 tk.Label（不是 ttk）
status_label = tk.Label(frame, text="已停止", fg="red")
status_label.pack(pady=5)

root.mainloop()

# pyinstaller --onefile --noconsole pyautogui/anti_idle_gui_mouse.py