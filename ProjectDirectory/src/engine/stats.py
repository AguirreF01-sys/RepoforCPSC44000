"""
engine/stats.py
===============
Statistics tracking.

StatsTracker       – single-protocol run history + grouping events (3-5 mode)
MultiProtocolStats – per-protocol run lists for comparison (6-8 mode)
"""

from collections import defaultdict
from itertools import combinations


class StatsTracker:
    """Tracks run lengths and pairwise grouping frequency across replays."""

    def __init__(self):
        self._history   = []               # step count per completed run
        self._grouping  = defaultdict(int) # "P1&P2" -> co-location count
        self._total_obs = 0                # total steps observed

    # ── Feed data ─────────────────────────────────────────────────────────────

    def record_step(self, players) -> None:
        """Call once per simulation step to track grouping events."""
        cell_map = defaultdict(list)
        for p in players:
            cell_map[(p.row, p.col)].append(p)
        for group in cell_map.values():
            if len(group) >= 2:
                for a, b in combinations(group, 2):
                    self._grouping[f"P{a.id}&P{b.id}"] += 1
        self._total_obs += 1

    def record_run(self, steps: int) -> None:
        """Call once when a run finishes."""
        self._history.append(steps)

    # ── Query ─────────────────────────────────────────────────────────────────

    def run_count(self) -> int:
        return len(self._history)

    def history(self) -> list[int]:
        return list(self._history)

    def shortest(self) -> int:
        return min(self._history) if self._history else 0

    def longest(self) -> int:
        return max(self._history) if self._history else 0

    def average(self) -> float:
        return sum(self._history) / len(self._history) if self._history else 0.0

    def grouping_summary(self) -> list[tuple[str, float]]:
        """Returns [(pair_label, fraction_of_steps_co-located), ...] sorted desc."""
        if not self._grouping or not self._total_obs:
            return []
        items = [(lbl, cnt / self._total_obs)
                 for lbl, cnt in self._grouping.items()]
        items.sort(key=lambda x: -x[1])
        return items


class MultiProtocolStats:
    """Tracks separate run lists per protocol for side-by-side comparison."""

    def __init__(self):
        self._data = defaultdict(list)   # protocol_name -> [step_count, ...]

    def record(self, protocol_name: str, steps: int) -> None:
        self._data[protocol_name].append(steps)

    def protocols(self) -> list[str]:
        return list(self._data.keys())

    def runs_for(self, name: str) -> list[int]:
        return list(self._data[name])

    def summary(self) -> list[dict]:
        """
        Returns a list of dicts (sorted by avg ascending):
          { name, n, min, max, avg, runs }
        """
        out = []
        for name, runs in self._data.items():
            if runs:
                out.append({
                    "name": name,
                    "n":    len(runs),
                    "min":  min(runs),
                    "max":  max(runs),
                    "avg":  sum(runs) / len(runs),
                    "runs": list(runs),
                })
        out.sort(key=lambda x: x["avg"])
        return out

    def clear(self) -> None:
        self._data.clear()
