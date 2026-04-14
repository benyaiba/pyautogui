import pyautogui
import time
import random

pyautogui.FAILSAFE = True  # 鼠标移到左上角可强制停止

while True:
    x, y = pyautogui.position()

    # 随机小范围移动（更像真人）
    pyautogui.moveTo(x + random.randint(-3, 3), y + random.randint(-3, 3), duration=0.2)

    # 偶尔加一个点击（防某些软件检测）
    if random.random() > 0.7:
        pyautogui.click()

    # 随机间隔（30~90秒）
    time.sleep(random.randint(30, 90))