"""
engine/grid.py
==============
Grid model — knows its size and can compute valid neighbours.
No pygame dependency.
"""


class Grid:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols

    def neighbors(self, row: int, col: int) -> list[tuple[int, int]]:
        """Return all valid orthogonal neighbours of (row, col)."""
        out = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                out.append((nr, nc))
        return out

    def center(self) -> tuple[int, int]:
        return (self.rows // 2, self.cols // 2)

    def all_cells(self) -> list[tuple[int, int]]:
        return [(r, c) for r in range(self.rows) for c in range(self.cols)]
