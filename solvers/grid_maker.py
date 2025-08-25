import matplotlib.pyplot as plt


class GridEditor:
    def __init__(self, N):
        self.N = N
        self.grid = [[0 for _ in range(N)] for _ in range(N)]
        self.walls = set()
        self.fig, self.ax = plt.subplots()
        self.texts = {}
        self.selected_cell = None
        self.input_buffer = ""

        # Draw base grid
        for i in range(N + 1):
            self.ax.plot([0, N], [i, i], color="black", linewidth=1)
            self.ax.plot([i, i], [0, N], color="black", linewidth=1)

        self.ax.set_aspect("equal")
        self.ax.set_xlim(0, N)
        self.ax.set_ylim(0, N)
        self.ax.invert_yaxis()
        self.ax.set_title(
            "Click cell to type number.\nClick near edges to toggle walls.\nClose window when done."
        )
        self.ax.axis("off")

        self.fig.canvas.mpl_connect("button_press_event", self.onclick)
        self.fig.canvas.mpl_connect("key_press_event", self.onkey)

    def onclick(self, event):
        if event.xdata is None or event.ydata is None:
            return
        x, y = int(event.xdata), int(event.ydata)
        dx, dy = event.xdata - x, event.ydata - y

        eps = 0.45  # tolerance → bigger means easier to click wall

        # --- SHIFT + click makes/toggles walls ---
        if event.key == "shift":
            if abs(dx) < eps and y < self.N:  # vertical wall
                if x > 0:
                    self.toggle_wall((y, x - 1), (y, x))
                    return
            if abs(dy) < eps and x < self.N:  # horizontal wall
                if y > 0:
                    self.toggle_wall((y - 1, x), (y, x))
                    return
            return  # if shift pressed but not near a wall, ignore

        # --- Normal click: select cell ---
        if 0 <= x < self.N and 0 <= y < self.N:
            self.selected_cell = (y, x)
            self.input_buffer = ""
            print(f"Selected cell {self.selected_cell}, type a number...")

    def onkey(self, event):
        if self.selected_cell:
            r, c = self.selected_cell
            if event.key.isdigit():  # append digit
                self.input_buffer += event.key
                self.grid[r][c] = int(self.input_buffer)
                self.update_cell(r, c)
            elif event.key == "backspace":  # delete last digit
                self.input_buffer = self.input_buffer[:-1]
                self.grid[r][c] = int(self.input_buffer) if self.input_buffer else 0
                self.update_cell(r, c)
            elif event.key == "enter":  # finalize number
                print(f"Cell {self.selected_cell} set to {self.grid[r][c]}")
                self.selected_cell = None
                self.input_buffer = ""

    def update_cell(self, r, c):
        if (r, c) in self.texts:
            self.texts[(r, c)].remove()
        if self.grid[r][c] != 0:
            self.texts[(r, c)] = self.ax.text(
                c + 0.5,
                r + 0.5,
                str(self.grid[r][c]),
                ha="center",
                va="center",
                color="blue",
                weight="bold",
                fontsize=12,
            )
        self.fig.canvas.draw()

    def toggle_wall(self, cell1, cell2):
        if cell1 == cell2:
            return
        if cell1 > cell2:  # normalize ordering
            cell1, cell2 = cell2, cell1
        if (cell1, cell2) in self.walls:
            self.walls.remove((cell1, cell2))
        else:
            self.walls.add((cell1, cell2))
        self.redraw_walls()

    def redraw_walls(self):
        [line.remove() for line in getattr(self, "_wall_lines", [])]
        self._wall_lines = []
        for (r1, c1), (r2, c2) in self.walls:
            if r1 == r2:  # same row → vertical neighbors
                x = max(c1, c2)
                y1, y2 = r1, r1 + 1
                (line,) = self.ax.plot([x, x], [y1, y2], color="black", linewidth=6)
            elif c1 == c2:  # same column → horizontal neighbors
                y = max(r1, r2)
                x1, x2 = c1, c1 + 1
                (line,) = self.ax.plot([x1, x2], [y, y], color="black", linewidth=6)
            self._wall_lines.append(line)
        self.fig.canvas.draw()

    def run(self):
        plt.show()
        return self.grid, list(self.walls)


if __name__ == "__main__":
    N = int(input("Enter grid size N: "))
    editor = GridEditor(N)
    grid, walls = editor.run()

    print("\nGrid:")
    print(f"grid_{N} = [")
    for row in grid:
        print("    " + str(row) + ",")
    print("]\n")

    print("Walls:")
    print(f"walls_{N} = [")
    for w in walls:
        print(f"    {w},")
    print("]")
