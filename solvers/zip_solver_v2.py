# dfs stack and pruning base on manhatten dist

from grids import grid, walls

TEMP_DRAW_RATE = 0.00

N = len(grid)
start = 1

end = max([max(row) for row in grid])

from utils import draw_path, draw_path_walls
from random import random

positions = {grid[r][c]: (r, c) for r in range(N) for c in range(N) if grid[r][c] != 0}

neighbors = {
    (r, c): [
        (nr, nc)
        for nr, nc in [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
        if 0 <= nr < N and 0 <= nc < N
    ]
    for r in range(N)
    for c in range(N)
}

for w in walls:
    for r, c in neighbors:
        neighbors[(r, c)] = [
            (nr, nc)
            for (nr, nc) in neighbors[(r, c)]
            if ((r, c), (nr, nc)) not in walls and ((nr, nc), (r, c)) not in walls
        ]


def solve():
    sr, sc = positions[start]

    # stack holds: (r, c, next_search, path, visited_set)
    stack = [(sr, sc, start, [], set())]

    while stack:
        r, c, next_search, path, visited = stack.pop()

        if (r, c) in visited:
            continue

        new_next = next_search
        if grid[r][c] == next_search:
            if next_search == end:
                if len(visited) == N * N - 1:  # all cells covered
                    sol = path + [(r, c)]
                    print("Found solution:", sol)
                    draw_path_walls(sol, grid, walls, "sol.png")
                    return True
                else:
                    continue
            else:
                new_next += 1
                if random() < TEMP_DRAW_RATE:
                    draw_path(path + [(r, c)], grid, "sol-temp.png")

        elif grid[r][c] != 0:
            continue

        new_path = path + [(r, c)]
        new_visited = visited | {(r, c)}

        # prune with manhattan distance
        tr, tc = positions[new_next]
        dist = abs(r - tr) + abs(c - tc)
        remaining = N * N - len(new_visited)
        if dist > remaining:
            continue

        for nr, nc in neighbors[(r, c)]:
            stack.append((nr, nc, new_next, new_path, new_visited))

    return False


solve()
