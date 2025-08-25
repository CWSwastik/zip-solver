import matplotlib.pyplot as plt
from matplotlib.widgets import Button
from collections import deque
import multiprocessing as mp
import sys


# --------- Solver process ----------
def solver_process(grid, walls, update_queue, stop_event, update_interval_checks=30000):
    """
    Runs DFS solver in separate process and sends periodic updates via update_queue.
    Messages:
      {"checked": int, "path": [(r,c),...]}  # progress
      {"found": True, "solution": [(r,c),...], "checked": int}  # on success
      {"done": True, "checked": int}  # finished w/o solution
    """
    N = len(grid)

    positions = {
        grid[r][c]: (r, c) for r in range(N) for c in range(N) if grid[r][c] != 0
    }
    if not positions:
        update_queue.put({"done": True, "checked": 0})
        return

    start, end = min(positions), max(positions)

    neighbors = {
        (r, c): [
            (nr, nc)
            for nr, nc in [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
            if 0 <= nr < N and 0 <= nc < N
        ]
        for r in range(N)
        for c in range(N)
    }
    wallset = set(walls)
    for r, c in list(neighbors.keys()):
        neighbors[(r, c)] = [
            (nr, nc)
            for (nr, nc) in neighbors[(r, c)]
            if ((r, c), (nr, nc)) not in wallset and ((nr, nc), (r, c)) not in wallset
        ]

    def is_connected(r, c, new_next, visited):
        """Flood fill from (r,c) through unvisited + future targets.
        Returns True if all required cells are reachable."""
        required = {
            (rr, cc)
            for rr in range(N)
            for cc in range(N)
            if (rr, cc) not in visited
            and (grid[rr][cc] == 0 or grid[rr][cc] >= new_next)
        }
        if not required:
            return True

        dq = deque([(r, c)])
        seen = {(r, c)}
        while dq:
            cr, cc = dq.popleft()
            for nr, nc in neighbors[(cr, cc)]:
                if (nr, nc) in required and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    dq.append((nr, nc))
        return required.issubset(seen)

    sr, sc = positions[start]
    stack = [(sr, sc, start, [], set())]
    checked = 0
    last_update = 0

    while stack and not stop_event.is_set():
        r, c, next_search, path, visited = stack.pop()
        if (r, c) in visited:
            continue

        checked += 1
        if checked - last_update >= update_interval_checks:
            try:
                update_queue.put(
                    {"checked": checked, "path": path + [(r, c)]}, block=False
                )
            except:
                pass
            last_update = checked

        new_next = next_search
        cell_val = grid[r][c]
        if cell_val == next_search:
            if next_search == end:
                if len(visited) == N * N - 1:
                    solution = path + [(r, c)]
                    update_queue.put(
                        {"found": True, "solution": solution, "checked": checked}
                    )
                    return
                else:
                    continue
            else:
                new_next += 1
        elif cell_val != 0:
            continue

        new_path = path + [(r, c)]
        new_visited = visited.copy()
        new_visited.add((r, c))

        if new_next in positions:
            tr, tc = positions[new_next]
            dist = abs(r - tr) + abs(c - tc)
            remaining = N * N - len(new_visited)
            if dist > remaining:
                continue

        if not is_connected(r, c, new_next, new_visited):
            continue

        for nr, nc in neighbors[(r, c)]:
            stack.append((nr, nc, new_next, new_path, new_visited))

    if stop_event.is_set():
        update_queue.put({"done": True, "checked": checked, "stopped": True})
    else:
        update_queue.put({"done": True, "checked": checked})


# --------- GUI + main process ----------
class GridSolverGUI:
    def __init__(self, N):
        self.N = N
        self.grid = [[0 for _ in range(N)] for _ in range(N)]
        self.walls = set()

        # Matplotlib figure
        self.fig, self.ax = plt.subplots()
        plt.subplots_adjust(bottom=0.15)

        self.texts = {}
        self._wall_lines = []
        self._path_artist = None  # use a single line artist
        self.selected_cell = None
        self.input_buffer = ""

        # Solver process
        self.proc = None
        self.queue = None
        self.stop_event = None
        self.poll_timer = None
        self.solving = False
        self.last_checked = 0

        # Draw base grid
        self.draw_grid_base()

        self.ax.set_aspect("equal")
        self.ax.set_xlim(0, N)
        self.ax.set_ylim(0, N)
        self.ax.invert_yaxis()
        self.ax.axis("off")
        self.status_text = self.fig.text(0.02, 0.02, "Idle", fontsize=10)

        # Buttons
        solve_ax = plt.axes([0.62, 0.02, 0.15, 0.06])
        stop_ax = plt.axes([0.79, 0.02, 0.15, 0.06])
        self.solve_btn = Button(solve_ax, "Solve")
        self.stop_btn = Button(stop_ax, "Stop")
        self.solve_btn.on_clicked(self.on_solve)
        self.stop_btn.on_clicked(self.on_stop)

        # Events
        self.fig.canvas.mpl_connect("button_press_event", self.onclick)
        self.fig.canvas.mpl_connect("key_press_event", self.onkey)
        self.fig.canvas.mpl_connect("close_event", self.on_close)

    def draw_grid_base(self):
        self.ax.clear()
        for i in range(self.N + 1):
            self.ax.plot([0, self.N], [i, i], color="black", linewidth=1)
            self.ax.plot([i, i], [0, self.N], color="black", linewidth=1)
        self.redraw_walls()
        self.draw_all_texts()

    def draw_all_texts(self):
        for t in list(self.texts.values()):
            try:
                t.remove()
            except:
                pass
        self.texts = {}
        for r in range(self.N):
            for c in range(self.N):
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
        self.fig.canvas.draw_idle()

    def onclick(self, event):
        if event.xdata is None or event.ydata is None:
            return
        x, y = int(event.xdata), int(event.ydata)
        dx, dy = event.xdata - x, event.ydata - y
        eps = 0.45
        if getattr(event, "key", None) == "shift":
            if abs(dx) < eps and y < self.N and x > 0:
                self.toggle_wall((y, x - 1), (y, x))
                return
            if abs(dy) < eps and x < self.N and y > 0:
                self.toggle_wall((y - 1, x), (y, x))
                return
        if 0 <= x < self.N and 0 <= y < self.N:
            self.selected_cell = (y, x)
            self.input_buffer = ""

    def onkey(self, event):
        if not self.selected_cell or event.key is None:
            return
        r, c = self.selected_cell
        if event.key.isdigit():
            self.input_buffer += event.key
            self.grid[r][c] = int(self.input_buffer)
            self.draw_all_texts()
        elif event.key == "backspace":
            self.input_buffer = self.input_buffer[:-1]
            self.grid[r][c] = int(self.input_buffer) if self.input_buffer else 0
            self.draw_all_texts()
        elif event.key == "enter":
            self.selected_cell, self.input_buffer = None, ""

    def toggle_wall(self, cell1, cell2):
        if cell1 > cell2:
            cell1, cell2 = cell2, cell1
        if (cell1, cell2) in self.walls:
            self.walls.remove((cell1, cell2))
        else:
            self.walls.add((cell1, cell2))
        self.redraw_walls()
        self.fig.canvas.draw_idle()

    def redraw_walls(self):
        for ln in self._wall_lines:
            try:
                ln.remove()
            except:
                pass
        self._wall_lines = []
        for (r1, c1), (r2, c2) in self.walls:
            if r1 == r2:
                x = max(c1, c2)
                y1, y2 = r1, r1 + 1
                (ln,) = self.ax.plot([x, x], [y1, y2], "k", lw=6)
            elif c1 == c2:
                y = max(r1, r2)
                x1, x2 = c1, c1 + 1
                (ln,) = self.ax.plot([x1, x2], [y, y], "k", lw=6)
            self._wall_lines.append(ln)

    # -------- Solver process control --------
    def on_solve(self, event=None):
        if self.solving:
            return
        self.queue, self.stop_event = mp.Queue(), mp.Event()
        grid_copy = [row[:] for row in self.grid]
        walls_copy = list(self.walls)
        self.proc = mp.Process(
            target=solver_process,
            args=(grid_copy, walls_copy, self.queue, self.stop_event),
        )
        self.proc.start()
        self.solving = True
        self.last_checked = 0
        self.status_text.set_text("Solving... checked 0 paths")
        if self.poll_timer is None:
            self.poll_timer = self.fig.canvas.new_timer(interval=100)
            self.poll_timer.add_callback(self.poll_queue)
        self.poll_timer.start()

    def on_stop(self, event=None):
        if self.solving and self.stop_event:
            self.stop_event.set()

    def poll_queue(self):
        if not self.queue:
            return
        updated = False
        last_status = None
        last_path_msg = None

        try:
            # Drain queue, but keep only the latest useful info
            while not self.queue.empty():
                msg = self.queue.get_nowait()
                updated = True

                if msg.get("found"):
                    self.draw_path(msg["solution"], temp=False)
                    self.status_text.set_text(
                        f"Solved! Found after {msg['checked']} checks"
                    )
                    self._clean_proc()
                    return

                if msg.get("done"):
                    if msg.get("stopped"):
                        self.status_text.set_text(
                            f"Stopped after {msg['checked']} checks"
                        )
                    else:
                        self.status_text.set_text(
                            f"No solution after {msg['checked']} checks"
                        )
                    self._clean_proc()
                    return

                if "checked" in msg and "path" in msg:
                    # Only keep the latest progress to display
                    last_status = msg["checked"]
                    last_path_msg = msg

            # Apply only the most recent status update
            if last_status is not None:
                self.last_checked = last_status
                self.status_text.set_text(
                    f"Solving... checked {self.last_checked} paths"
                )
                if self.last_checked % 2000 == 0 and last_path_msg:
                    self.draw_path(last_path_msg["path"], temp=True)

        except Exception as e:
            print("poll error:", e)

        if updated:
            self.fig.canvas.draw_idle()
        if self.solving:
            self.poll_timer.start()

    def _clean_proc(self):
        try:
            if self.proc:
                self.proc.terminate()
        except:
            pass
        self.proc = None
        self.queue = None
        self.stop_event = None
        self.solving = False

    # -------- Path drawing (fast) --------
    def draw_path_fast(self, path, temp=True):
        xs = [c + 0.5 for r, c in path]
        ys = [r + 0.5 for r, c in path]
        if not self._path_artist:
            (self._path_artist,) = self.ax.plot(xs, ys, "b-" if temp else "g-", lw=2)
        else:
            self._path_artist.set_data(xs, ys)
            self._path_artist.set_color("blue" if temp else "green")
        self.fig.canvas.draw_idle()

    def draw_path(self, path, temp=True):
        xs = [c + 0.5 for r, c in path]
        ys = [r + 0.5 for r, c in path]

        # Pick color based on temp
        color = "blue" if temp else "green"

        # Draw path line
        if not self._path_artist:
            (self._path_artist,) = self.ax.plot(xs, ys, "-", color=color, lw=2)
        else:
            self._path_artist.set_data(xs, ys)
            self._path_artist.set_color(color)

        # Remove old arrows if any
        if hasattr(self, "_path_arrows"):
            for arrow in self._path_arrows:
                arrow.remove()
        self._path_arrows = []

        # Draw arrows using annotate
        if len(xs) > 1:
            prev = (xs[0], ys[0])
            for curr in zip(xs[1:], ys[1:]):
                arrow = self.ax.annotate(
                    "",
                    xy=curr,
                    xycoords="data",
                    xytext=prev,
                    textcoords="data",
                    arrowprops=dict(
                        arrowstyle="->",
                        color=color,
                        lw=2,
                        shrinkA=0,
                        shrinkB=0,
                    ),
                )
                self._path_arrows.append(arrow)
                prev = curr

        self.fig.canvas.draw_idle()

    def on_close(self, event):
        if self.stop_event:
            self.stop_event.set()
        if self.proc:
            try:
                self.proc.terminate()
            except:
                pass

    def run(self):
        plt.show()


def main():
    if len(sys.argv) >= 2:
        N = int(sys.argv[1])
    else:
        N = int(input("Enter grid size N: "))
    gui = GridSolverGUI(N)
    gui.run()


if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()
