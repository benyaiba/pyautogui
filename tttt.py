import tkinter as tk
import subprocess
import threading
import time
import re
import platform

class NetMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("网络监控器")
        self.root.attributes("-topmost", True)
        self.root.geometry("320x200")
        self.root.resizable(False, False)

        # 状态变量
        self.running = True
        self.total = 0
        self.success = 0
        self.fail = 0
        self.last_fail_time = "--"

        # 根据操作系统选择 ping 参数
        self.ping_cmd = ["ping"]
        if platform.system().lower() == "windows":
            self.ping_cmd.append("-n")
        else:
            self.ping_cmd.append("-c")
        self.ping_cmd.append("1")
        self.ping_cmd.append("baidu.com")  # 可修改为任意目标地址

        # UI 组件
        self.label_status = tk.Label(root, text="正在检测...", font=("Arial", 12))
        self.label_status.pack(pady=5)

        self.label_latency = tk.Label(root, text="延迟: -- ms", font=("Arial", 10))
        self.label_latency.pack(pady=2)

        self.label_stats = tk.Label(root, text="成功: 0 | 失败: 0 | 成功率: 0%", font=("Arial", 9))
        self.label_stats.pack(pady=2)

        self.label_last_fail = tk.Label(root, text="最后失败: --", font=("Arial", 9))
        self.label_last_fail.pack(pady=2)

        self.btn_stop = tk.Button(root, text="停止监控", command=self.toggle_monitor)
        self.btn_stop.pack(pady=10)

        # 启动监控线程
        self.start_monitor()

    def start_monitor(self):
        self.running = True
        self.btn_stop.config(text="停止监控")
        self.monitor_thread = threading.Thread(target=self.ping_loop, daemon=True)
        self.monitor_thread.start()

    def toggle_monitor(self):
        if self.running:
            self.running = False
            self.btn_stop.config(text="开始监控")
            self.label_status.config(text="监控已停止")
        else:
            self.start_monitor()

    def ping_loop(self):
        while self.running:
            self.do_ping()
            time.sleep(2)   # 每2秒检测一次

    def do_ping(self):
        try:
            proc = subprocess.run(
                self.ping_cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            output = proc.stdout + proc.stderr
            success = (proc.returncode == 0)   # 返回码0表示网络通

            # 尝试解析延迟（仅用于显示，不影响通断判断）
            latency = None
            if success:
                # 匹配多种语言和格式的延迟表示
                match = re.search(
                    r"[t时间時間][iime]?[m模]?[e等]?[=<\u2248]?\s*(\d+(?:\.\d+)?)\s*ms",
                    output,
                    re.IGNORECASE
                )
                if match:
                    latency = match.group(1)
                else:
                    latency = "未知"   # 无法解析但网络通时显示“未知”

            self.update_ui(success, latency)
        except subprocess.TimeoutExpired:
            self.update_ui(False, None)   # 超时视为失败
        except Exception:
            self.update_ui(False, None)   # 其他异常也视为失败

    def update_ui(self, success, latency):
        self.total += 1
        if success:
            self.success += 1
            status_text = "✅ 网络正常"
            status_color = "green"
            latency_text = f"延迟: {latency} ms" if latency is not None else "延迟: -- ms"
        else:
            self.fail += 1
            status_text = "❌ 网络断开"
            status_color = "red"
            latency_text = "延迟: -- ms"
            self.last_fail_time = time.strftime("%H:%M:%S")

        success_rate = (self.success / self.total) * 100 if self.total > 0 else 0

        # 更新 GUI（主线程）
        def update_gui():
            self.label_status.config(text=status_text, fg=status_color)
            self.label_latency.config(text=latency_text)
            self.label_stats.config(
                text=f"成功: {self.success} | 失败: {self.fail} | 成功率: {success_rate:.1f}%"
            )
            self.label_last_fail.config(text=f"最后失败: {self.last_fail_time}")

        self.root.after(0, update_gui)

if __name__ == "__main__":
    root = tk.Tk()
    app = NetMonitor(root)
    root.mainloop()