import tkinter as tk
import random

LEVELS = {
    "初级": (9, 10),
    "中级": (16, 40),
    "高级": (16, 99)
}

class Minesweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("扫雷")

        self.level = "初级"
        self.frame_top = tk.Frame(root)
        self.frame_top.pack()

        self.frame_game = tk.Frame(root)
        self.frame_game.pack()

        self.create_top_ui()
        self.start_game()

    def create_top_ui(self):
        self.var = tk.StringVar(value=self.level)

        self.menu = tk.OptionMenu(self.frame_top, self.var, *LEVELS.keys(), command=self.change_level)
        self.menu.pack(side=tk.LEFT)

        self.face_btn = tk.Button(self.frame_top, text="😊", width=4, command=self.start_game)
        self.face_btn.pack(side=tk.LEFT, padx=10)

    def change_level(self, val):
        self.level = val
        self.start_game()

    def start_game(self):
        for widget in self.frame_game.winfo_children():
            widget.destroy()

        self.SIZE, self.MINES = LEVELS[self.level]
        self.buttons = []
        self.board = []
        self.revealed = set()
        self.flags = set()
        self.game_over_flag = False

        self.face_btn.config(text="😊")

        self.create_board()
        self.create_ui()

    def create_board(self):
        self.board = [[0]*self.SIZE for _ in range(self.SIZE)]
        mines = set()

        while len(mines) < self.MINES:
            x = random.randint(0, self.SIZE-1)
            y = random.randint(0, self.SIZE-1)
            mines.add((x,y))

        for x,y in mines:
            self.board[x][y] = -1

        for i in range(self.SIZE):
            for j in range(self.SIZE):
                if self.board[i][j] == -1:
                    continue
                count = 0
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:
                        ni, nj = i+dx, j+dy
                        if 0<=ni<self.SIZE and 0<=nj<self.SIZE:
                            if self.board[ni][nj] == -1:
                                count += 1
                self.board[i][j] = count

    def create_ui(self):
        for i in range(self.SIZE):
            row = []
            for j in range(self.SIZE):
                btn = tk.Button(self.frame_game, text="■", width=2, height=1)
                btn.grid(row=i, column=j)

                btn.bind("<Button-1>", lambda e, x=i, y=j: self.left_click(x,y))
                btn.bind("<Button-3>", lambda e, x=i, y=j: self.right_click(x,y))

                row.append(btn)
            self.buttons.append(row)

    def left_click(self, x, y):
        if self.game_over_flag or (x,y) in self.flags:
            return

        if (x,y) in self.revealed:
            return

        self.revealed.add((x,y))

        if self.board[x][y] == -1:
            self.buttons[x][y].config(text="💣", bg="red")
            self.face_btn.config(text="😵")
            self.game_over()
            return

        self.buttons[x][y].config(text=str(self.board[x][y]) if self.board[x][y]>0 else "",
                                  relief=tk.SUNKEN)

        if self.board[x][y] == 0:
            self.expand(x,y)

        if len(self.revealed) == self.SIZE*self.SIZE - self.MINES:
            self.win()

    def right_click(self, x, y):
        if self.game_over_flag or (x,y) in self.revealed:
            return

        if (x,y) in self.flags:
            self.flags.remove((x,y))
            self.buttons[x][y].config(text="■")
        else:
            self.flags.add((x,y))
            self.buttons[x][y].config(text="🚩")

    def expand(self, x, y):
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                nx, ny = x+dx, y+dy
                if 0<=nx<self.SIZE and 0<=ny<self.SIZE:
                    if (nx,ny) not in self.revealed:
                        self.left_click(nx,ny)

    def game_over(self):
        self.game_over_flag = True
        for i in range(self.SIZE):
            for j in range(self.SIZE):
                if self.board[i][j] == -1:
                    self.buttons[i][j].config(text="💣")

    def win(self):
        self.face_btn.config(text="😎")
        self.game_over_flag = True
        for row in self.buttons:
            for btn in row:
                btn.config(bg="lightgreen")


if __name__ == "__main__":
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()

# 打包成exe的命令
# pyinstaller --onefile --noconsole game/minesweeper.py