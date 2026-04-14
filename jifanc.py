import tkinter as tk
from tkinter import messagebox
import json
import os
from datetime import datetime

DATA_FILE = "jifanc_main.json"
WORKDAY_FILE = "jifanc_workdays.json"

# ===== 初始化文件 =====
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(WORKDAY_FILE):
    with open(WORKDAY_FILE, 'w', encoding='utf-8') as f:
        json.dump({}, f)

# ===== 数据读写 =====
def load_data():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_workdays():
    with open(WORKDAY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_workdays(data):
    with open(WORKDAY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("记饭C")
        self.root.minsize(300, 200)

        self.current_frame = None
        self.month_offset = 0
        self.show_input_page()

    def clear_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    # ================== 录入页面 ==================
    def show_input_page(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20)
        self.current_frame = frame
        self.root.geometry("300x200")

        tk.Label(frame, text="餐别选择").pack(anchor="w")
        self.meal_var = tk.StringVar(value="午餐")

        meal_frame = tk.Frame(frame)
        meal_frame.pack(fill="x", pady=5)
        tk.Radiobutton(meal_frame, text="午餐", variable=self.meal_var, value="午餐").pack(side="left", expand=True)
        tk.Radiobutton(meal_frame, text="晚餐", variable=self.meal_var, value="晚餐").pack(side="left", expand=True)

        tk.Label(frame, text="数量选择").pack(anchor="w")
        qty_frame = tk.Frame(frame)
        qty_frame.pack(fill="x", pady=5)

        self.qty_var = tk.IntVar(value=1)
        for i in range(1, 5):
            tk.Radiobutton(qty_frame, text=f"{i}份", variable=self.qty_var, value=i).pack(side="left", expand=True)

        tk.Button(frame, text="提交", command=self.submit).pack(side="left", expand=True)
        tk.Button(frame, text="查看记录", command=self.show_list_page).pack(side="left", expand=True, pady=10)

    def submit(self):
        meal = self.meal_var.get()
        qty = self.qty_var.get()

        if not meal or not qty:
            messagebox.showwarning("提示", "请选择餐别和数量")
            return

        data = load_data()
        data.append({
            "date": datetime.now().strftime("%Y-%m-%d"),
            "meal": meal,
            "qty": qty
        })
        save_data(data)

        messagebox.showinfo("成功", "记录已保存")

        self.meal_var.set("午餐")
        self.qty_var.set(1)

    # ================== 列表页面 ==================
    def show_list_page(self):
        self.clear_frame()
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=20, fill='both', expand=True)
        self.current_frame = frame
        self.root.geometry("480x470")

        data = load_data()

        # ===== 月份计算 =====
        def get_target_month(offset):
            now = datetime.now()
            year = now.year
            month = now.month + offset
            while month <= 0:
                month += 12
                year -= 1
            while month > 12:
                month -= 12
                year += 1
            return year, month

        year, month = get_target_month(self.month_offset)
        ym = f"{year}-{month:02d}"
        month_str = f"{year}/{month:02d}"

        tk.Label(frame, text=month_str, font=("Arial", 10)).pack(anchor="w")

        # ===== 统计 =====
        lunch_total = sum(d['qty'] for d in data if d['meal'] == '午餐' and d['date'].startswith(ym))
        dinner_total = sum(d['qty'] for d in data if d['meal'] == '晚餐' and d['date'].startswith(ym))

        workdays = load_workdays()
        max_days = workdays.get(ym)

        if max_days:
            lunch_remain = max_days - lunch_total
            dinner_remain = max_days - dinner_total

            info_text = f"午餐：{lunch_total}/{max_days}（剩余{lunch_remain}）  晚餐：{dinner_total}/{max_days}（剩余{dinner_remain}）"

            color = "black"
            if lunch_remain < 0 or dinner_remain < 0:
                color = "red"
                info_text += " ⚠已超额"
        else:
            info_text = f"午餐：{lunch_total}份  晚餐：{dinner_total}份（未设置工作日）"
            color = "gray"

        # ===== 顶部两行结构 =====
        top_container = tk.Frame(frame)
        top_container.pack(pady=10, fill='x')

        # 第一行：统计信息
        info_frame = tk.Frame(top_container)
        info_frame.pack(fill='x', pady=2, padx=5)

        tk.Label(
            info_frame,
            text=info_text,
            font=("Arial", 10),
            fg=color,
            anchor="w"
        ).pack(side='left')

        # 分隔线
        tk.Frame(top_container, height=1, bg="#ccc").pack(fill='x', pady=3)

        # 第二行：按钮
        btn_frame = tk.Frame(top_container)
        btn_frame.pack(fill='x', pady=5, padx=5)

        def prev_month():
            self.month_offset -= 1
            self.show_list_page()

        def next_month():
            self.month_offset += 1
            self.show_list_page()

        def current_month():
            self.month_offset = 0
            self.show_list_page()

        tk.Button(btn_frame, text="← 上月", width=8, command=prev_month).pack(side='left', padx=3)
        tk.Button(btn_frame, text="本月", width=8, command=current_month).pack(side='left', padx=3)
        tk.Button(btn_frame, text="下月 →", width=8, command=next_month).pack(side='left', padx=3)

        tk.Button(btn_frame, text="工作日设置", command=self.show_workday_setting).pack(side='right', padx=5)

        # ===== 滚动区域 =====
        container = tk.Frame(frame)
        container.pack(fill='both', expand=True)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))

        # ===== 数据列表 =====
        filtered_data = [(i, d) for i, d in enumerate(data) if d['date'].startswith(ym)]

        for real_index, record in reversed(filtered_data):
            row = tk.Frame(scrollable_frame, bd=0.5, relief="solid")
            row.pack(fill='x', pady=2)

            tk.Label(
                row,
                text=f"{record['date']} {record['meal']} {record['qty']}份",
                width=43,
                font=("Arial", 10),
                anchor='w'
            ).pack(side='left')

            tk.Button(row, text="编辑", command=lambda idx=real_index: self.edit_record(idx)).pack(side='right')
            tk.Button(row, text="删除", command=lambda idx=real_index: self.delete_record(idx)).pack(side='right')

        tk.Button(frame, text="返回", command=self.show_input_page).pack(pady=10)

    # ================== 删除 ==================
    def delete_record(self, index):
        data = load_data()
        record = data[index]

        if messagebox.askyesno("确认删除", f"{record['date']} {record['meal']} {record['qty']}份"):
            del data[index]
            save_data(data)
            self.show_list_page()

    # ================== 编辑 ==================
    def edit_record(self, index):
        data = load_data()
        record = data[index]

        win = tk.Toplevel(self.root)
        win.title("编辑记录")

        tk.Label(win, text=f"日期：{record['date']}", fg="gray").pack(pady=5)

        meal_var = tk.StringVar(value=record['meal'])
        tk.Radiobutton(win, text="午餐", variable=meal_var, value="午餐").pack()
        tk.Radiobutton(win, text="晚餐", variable=meal_var, value="晚餐").pack()

        qty_var = tk.IntVar(value=record['qty'])
        for i in range(1, 5):
            tk.Radiobutton(win, text=f"{i}份", variable=qty_var, value=i).pack()

        def save_edit():
            record['meal'] = meal_var.get()
            record['qty'] = qty_var.get()
            save_data(data)
            win.destroy()
            self.show_list_page()

        tk.Button(win, text="保存", command=save_edit).pack(side='left', padx=10, pady=10)
        tk.Button(win, text="取消", command=win.destroy).pack(side='left')

    # ================== 工作日设置 ==================
    def show_workday_setting(self):
        win = tk.Toplevel(self.root)
        win.title("工作日设置")
        win.geometry("300x200")

        # ===== 当前查看的月份（和列表页一致）=====
        now = datetime.now()
        year = now.year
        month = now.month + self.month_offset

        while month <= 0:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1

        current_ym = f"{year}-{month:02d}"

        # ===== 读取已有配置 =====
        workdays = load_workdays()
        saved_days = workdays.get(current_ym, '')

        # ===== 绑定变量 =====
        month_var = tk.StringVar(value=current_ym)
        day_var = tk.IntVar(value=saved_days)

        tk.Label(win, text="月份 (YYYY-MM)").pack(pady=5)
        tk.Entry(win, textvariable=month_var).pack(pady=5)
        tk.Label(win, text="工作日天数").pack(pady=5)
        tk.Entry(win, textvariable=day_var).pack(pady=5)

        def save_setting():
            m = month_var.get()
            d = day_var.get()

            if not m or d <= 0:
                messagebox.showwarning("错误", "输入不合法")
                return

            data = load_workdays()
            data[m] = d
            save_workdays(data)

            messagebox.showinfo("成功", f"{m} 已设置为 {d} 天")
            win.destroy()
            self.show_list_page()

        tk.Button(win, text="保存", command=save_setting).pack(pady=10)


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)

    tk.Label(
        root,
        text="by yaiba@v1.2",
        fg="gray",
        font=("Arial", 9)
    ).place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-5)

    root.mainloop()