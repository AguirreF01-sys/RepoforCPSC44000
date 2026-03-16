"""
engine/protocols.py
===================
Movement protocols.  Each class implements:

    choose_move(player, grid, all_players) -> (row, col)

Add new protocols by subclassing Protocol and appending to ALL_PROTOCOLS.
No pygame dependency.
"""

import random


# ── Base ──────────────────────────────────────────────────────────────────────

class Protocol:
    name        = "Base"
    description = "Abstract base — do not use directly."

    def choose_move(self, player, grid, all_players):
        raise NotImplementedError


# ── Implementations ───────────────────────────────────────────────────────────

class PureRandom(Protocol):
    name        = "Pure Random Walk"
    description = "Each step picks a uniformly random valid neighbour — no bias."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        return random.choice(nbrs) if nbrs else (player.row, player.col)


class BiasedWalk(Protocol):
    name        = "Biased Walk"
    description = "Prefers moving right and down (southeast drift, weight ×2.5)."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)
        weights = []
        for (r, c) in nbrs:
            w = 1.0
            if r > player.row:  w += 1.5   # prefer down
            if c > player.col:  w += 1.5   # prefer right
            weights.append(w)
        return _weighted_choice(nbrs, weights)


class ZigZag(Protocol):
    name        = "Zig-Zag"
    description = "Alternates horizontal and vertical moves each step."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)
        dr = player.row - player.prev_row
        dc = player.col - player.prev_col
        # Prefer perpendicular direction to last move
        if abs(dc) > abs(dr):
            pref = [(r, c) for (r, c) in nbrs if c == player.col]  # go vertical
        else:
            pref = [(r, c) for (r, c) in nbrs if r == player.row]  # go horizontal
        return random.choice(pref) if pref else random.choice(nbrs)


class EdgeFollower(Protocol):
    name        = "Edge Follower"
    description = "Prefers cells on or near the grid boundary (weight ×4)."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)

        def edge_score(r, c):
            return 4 if (r == 0 or r == grid.rows - 1 or
                         c == 0 or c == grid.cols - 1) else 1

        weights = [edge_score(r, c) for r, c in nbrs]
        return _weighted_choice(nbrs, weights)


class CenterSeeker(Protocol):
    name        = "Move to Center"
    description = "Drifts toward the grid centre (weight ×3 for closer cells)."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)
        cr, cc  = grid.center()
        cur_d   = abs(player.row - cr) + abs(player.col - cc)
        weights = [3.0 if abs(r - cr) + abs(c - cc) < cur_d else 1.0
                   for (r, c) in nbrs]
        return _weighted_choice(nbrs, weights)


# ── Registry ──────────────────────────────────────────────────────────────────

ALL_PROTOCOLS: list[type[Protocol]] = [
    PureRandom,
    BiasedWalk,
    ZigZag,
    EdgeFollower,
    CenterSeeker,
]


# ── Internal helper ───────────────────────────────────────────────────────────

def _weighted_choice(options, weights):
    total = sum(weights)
    pick  = random.uniform(0, total)
    cum   = 0
    for opt, w in zip(options, weights):
        cum += w
        if pick <= cum:
            return opt
    return options[-1]
