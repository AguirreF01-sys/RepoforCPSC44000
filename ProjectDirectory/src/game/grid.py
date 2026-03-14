class Grid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def is_valid(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def neighbors(self, row, col):
        moves = [
            (row-1, col),  # Up
            (row+1, col),  # Down
            (row, col-1),  # Left
            (row, col+1)   # Right
        ]

        return [(r,c) for r,c in moves if self.is_valid(r,c)]
