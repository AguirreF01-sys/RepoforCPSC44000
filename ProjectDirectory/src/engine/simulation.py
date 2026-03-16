"""
engine/simulation.py
====================
Simulation engine.

Features
--------
- Pluggable movement protocol (any Protocol subclass)
- Group merging: players on the same cell join into one group
  and move as a unit from then on
- finished == True when all players share one cell/group
"""

from collections import defaultdict
from .protocols import PureRandom


class Simulation:
    def __init__(self, grid, players, protocol_cls=None):
        """
        Parameters
        ----------
        grid         : Grid
        players      : list[Player]
        protocol_cls : Protocol subclass (default: PureRandom)
        """
        self.grid     = grid
        self.players  = list(players)
        self.protocol = (protocol_cls or PureRandom)()
        self.finished = False
        self.steps    = 0
        self._rebuild_groups()

    # ── Public API ────────────────────────────────────────────────────────────

    def step(self) -> None:
        """Advance the simulation by one step."""
        if self.finished:
            return
        self.steps += 1
        self._move_groups()
        self._merge_collisions()
        if len(self._groups) == 1:
            self.finished = True

    def snapshot_positions(self) -> list[tuple[int, int]]:
        """Return current (row, col) for every player."""
        return [(p.row, p.col) for p in self.players]

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _rebuild_groups(self) -> None:
        """Reindex _groups: leader_id (min id in group) -> [Player, ...]"""
        self._groups = defaultdict(list)
        for p in self.players:
            self._groups[min(p.group)].append(p)

    def _move_groups(self) -> None:
        """Each group picks a move via the protocol and all members follow."""
        self._cell_map = defaultdict(list)   # cell -> players after moving
        for members in list(self._groups.values()):
            rep = members[0]   # group representative chooses
            nr, nc = self.protocol.choose_move(rep, self.grid, self.players)
            for m in members:
                m.move_to(nr, nc)
            self._cell_map[(nr, nc)].extend(members)

    def _merge_collisions(self) -> None:
        """Merge any groups that landed on the same cell."""
        merged = False
        for occupants in self._cell_map.values():
            if len(occupants) > 1:
                merged    = True
                all_ids   = set()
                for p in occupants:
                    all_ids |= p.group
                for p in occupants:
                    p.group = all_ids
        if merged:
            self._rebuild_groups()
