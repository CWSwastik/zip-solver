import matplotlib.pyplot as plt


def draw_path(path, grid, filename="solution.png"):
    N = len(grid)
    fig, ax = plt.subplots()

    # Draw grid lines
    for i in range(N + 1):
        ax.plot([0, N], [i, i], color="black", linewidth=1)
        ax.plot([i, i], [0, N], color="black", linewidth=1)

    # Place non-zero numbers in grid cells
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                x, y = c + 0.5, N - r - 0.5
                ax.text(
                    x,
                    y,
                    str(grid[r][c]),
                    color="blue",
                    weight="bold",
                    ha="center",
                    va="center",
                    fontsize=12,
                )

    # Convert cell indices to cell-center coordinates.
    centers = [(c + 0.5, N - r - 0.5) for r, c in path]

    # Draw arrows for the path
    if len(centers) > 0:
        prev = centers[0]
        ax.plot(prev[0], prev[1], marker="o", color="red", markersize=5)
        for curr in centers[1:]:
            ax.annotate(
                "",
                xy=curr,
                xycoords="data",
                xytext=prev,
                textcoords="data",
                arrowprops=dict(arrowstyle="->", color="red", lw=2),
            )
            ax.plot(curr[0], curr[1], marker="o", color="red", markersize=5)
            prev = curr

    ax.set_aspect("equal")
    ax.axis("off")
    plt.savefig(filename, bbox_inches="tight")
    plt.close()


def draw_path_walls(path, grid, walls, filename="solution_walls.png"):
    N = len(grid)
    fig, ax = plt.subplots()

    # Draw grid lines
    for i in range(N + 1):
        ax.plot([0, N], [i, i], color="black", linewidth=1)
        ax.plot([i, i], [0, N], color="black", linewidth=1)

    # Draw walls as thick lines between cells
    for wall in walls:
        (r1, c1), (r2, c2) = wall

        if r1 == r2:  # Same row → vertical neighbors → draw vertical wall
            x = max(c1, c2)  # right edge of the left cell
            y1, y2 = N - r1 - 1, N - r1
            ax.plot([x, x], [y1, y2], color="black", linewidth=5)

        elif c1 == c2:  # Same column → horizontal neighbors → draw horizontal wall
            y = N - max(r1, r2)  # top edge of the bottom cell
            x1, x2 = c1, c1 + 1
            ax.plot([x1, x2], [y, y], color="black", linewidth=5)

    # Place non-zero numbers in grid cells
    for r in range(N):
        for c in range(N):
            if grid[r][c] != 0:
                x, y = c + 0.5, N - r - 0.5
                ax.text(
                    x,
                    y,
                    str(grid[r][c]),
                    color="blue",
                    weight="bold",
                    ha="center",
                    va="center",
                    fontsize=12,
                )

    # Convert cell indices to cell-center coordinates.
    centers = [(c + 0.5, N - r - 0.5) for r, c in path]

    # Draw arrows for the path
    if len(centers) > 0:
        prev = centers[0]
        ax.plot(prev[0], prev[1], marker="o", color="red", markersize=5)
        for curr in centers[1:]:
            ax.annotate(
                "",
                xy=curr,
                xycoords="data",
                xytext=prev,
                textcoords="data",
                arrowprops=dict(arrowstyle="->", color="red", lw=2),
            )
            ax.plot(curr[0], curr[1], marker="o", color="red", markersize=5)
            prev = curr

    ax.set_aspect("equal")
    ax.axis("off")
    plt.savefig(filename, bbox_inches="tight")
    plt.close()


if __name__ == "__main__":
    from solvers.grids import grid_4, path_4

    draw_path(path_4, grid_4, "solution.png")
