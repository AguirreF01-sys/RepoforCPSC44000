"""
engine/player.py
================
Player model — position, colour, and group membership.
No pygame dependency.
"""


class Player:
    def __init__(self, pid: int, row: int, col: int, color: tuple):
        self.id       = pid
        self.row      = row
        self.col      = col
        self.color    = color
        self.group    = {pid}   # set of player ids currently in this group
        self.prev_row = row
        self.prev_col = col

    def move_to(self, r: int, c: int) -> None:
        """Move to a new cell, remembering the previous position."""
        self.prev_row, self.prev_col = self.row, self.col
        self.row, self.col = r, c

    def __repr__(self) -> str:
        return f"Player(id={self.id}, pos=({self.row},{self.col}), group={self.group})"
