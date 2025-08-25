# brute dfs (doesnt support walls)

from solvers.grids import grid

N = len(grid)
start = 1
TEMP_DRAW_RATE = 0.00

end = max([max(row) for row in grid])

visited = set()
path = []

from solvers.utils import draw_path
from random import random


def dfs(r, c, next_search):
    if r < 0 or c < 0 or r >= N or c >= N:
        return False

    if (r, c) in visited:
        return False

    new_next = next_search
    if next_search == grid[r][c]:
        if end == next_search:
            if len(visited) == N * N - 1:
                path.append((r, c))
                print(path)
                draw_path(path, grid, "sol.png")
                return True
            else:
                return False
        else:
            new_next += 1
            if random() < TEMP_DRAW_RATE:
                draw_path(path + [(r, c)], grid, "sol-temp.png")

    elif grid[r][c] != 0:
        return False

    path.append((r, c))
    visited.add((r, c))

    if dfs(r + 1, c, new_next):
        return True
    if dfs(r, c + 1, new_next):
        return True
    if dfs(r - 1, c, new_next):
        return True
    if dfs(r, c - 1, new_next):
        return True
    path.pop()
    visited.remove((r, c))

    return False


for r, row in enumerate(grid):
    for c, x in enumerate(row):
        if x == start:
            dfs(r, c, start)
