"""
screens/k2.py
=============
K2GameScreen — large colourful grid, cartoon face characters,
step counter, balloons on meeting, restart/menu buttons.
"""

import math
from collections import defaultdict
import pygame

from screens.base import Screen
from engine.grid import Grid
from engine.player import Player
from engine.simulation import Simulation

from ui.widgets import Button
from ui.drawing import draw_text
from effects.balloons import Balloon

from music import play_celebration, stop_celebration
from constants import (
    C_GRASS, C_PANEL, C_BORDER, C_GRID_LINE,
    C_ACCENT, C_GREEN_LT,
    PLAYER_COLORS, CELL_K2,
)


class K2GameScreen(Screen):
    ROWS = 5
    COLS = 5

    def __init__(self, app):
        super().__init__(app)
        W = self.COLS * CELL_K2 + 200
        H = max(self.ROWS * CELL_K2 + 100, 560)
        app.screen = pygame.display.set_mode((W, H))
        f = app.fonts

        gw = self.COLS * CELL_K2
        self.btn_restart = Button(
            (gw + 20, H - 80,  160, 48), "↺ Restart", font=f["md"])
        self.btn_menu = Button(
            (gw + 20, H - 140, 160, 48), "🏠 Menu",   font=f["md"])

        self._balloons  = []
        self._bal_timer = 0
        self._music_on  = False
        self._reset()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _reset(self):
        stop_celebration()
        self._music_on  = False
        self._balloons  = []
        self._bal_timer = 0
        grid = Grid(self.ROWS, self.COLS)
        p1   = Player(1, 0,            0,            PLAYER_COLORS[0])
        p2   = Player(2, self.ROWS - 1, self.COLS - 1, PLAYER_COLORS[1])
        self.sim   = Simulation(grid, [p1, p2])
        self.steps = 0

    # ── Screen interface ──────────────────────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            if self.btn_restart.clicked(event):
                self._reset()
            if self.btn_menu.clicked(event):
                self.app.goto("menu")

    def update(self):
        if not self.sim.finished:
            self.sim.step()
            self.steps += 1
        elif not self._music_on:
            play_celebration()
            self._music_on = True

    def draw(self, surface):
        surface.fill(C_GRASS)
        W, H = surface.get_size()
        gw   = self.COLS * CELL_K2

        # Checkerboard grid
        for r in range(self.ROWS):
            for c in range(self.COLS):
                rect = pygame.Rect(c * CELL_K2, r * CELL_K2, CELL_K2, CELL_K2)
                col  = (40, 130, 40) if (r + c) % 2 == 0 else (35, 120, 35)
                pygame.draw.rect(surface, col, rect)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

        # Characters (grouped)
        cell_map = defaultdict(list)
        for p in self.sim.players:
            cell_map[(p.row, p.col)].append(p)

        for (r, c), group in cell_map.items():
            cx_ = c * CELL_K2 + CELL_K2 // 2
            cy_ = r * CELL_K2 + CELL_K2 // 2
            for i, p in enumerate(group):
                ox = (i - len(group) // 2) * 18
                self._draw_character(surface, cx_ + ox, cy_, p.color)

        # Side panel
        pygame.draw.rect(surface, C_PANEL,  pygame.Rect(gw, 0, 200, H))
        pygame.draw.line(surface, C_BORDER, (gw, 0), (gw, H), 2)
        draw_text(surface, self.app.fonts["lg"], "Steps",
                  C_ACCENT, gw + 100, 60)
        draw_text(surface, self.app.fonts["xl"], str(self.steps),
                  C_GREEN_LT, gw + 100, 110)
        if self.sim.finished:
            draw_text(surface, self.app.fonts["md"], "They Met! 🎉",
                      (255, 230, 60), gw + 100, 160)

        self.btn_restart.draw(surface)
        self.btn_menu.draw(surface)

        # Balloons on celebration
        if self.sim.finished:
            self._bal_timer += 1
            if self._bal_timer % 5 == 0:
                self._balloons.append(Balloon(gw, H))
            self._balloons = [b for b in self._balloons if b.y > -60]
            for b in self._balloons:
                b.update()
                b.draw(surface)

    # ── Character renderer ────────────────────────────────────────────────────

    def _draw_character(self, surface, cx: int, cy: int, color) -> None:
        r = CELL_K2 // 3
        pygame.draw.circle(surface, color, (cx, cy), r)
        pygame.draw.circle(surface, (255, 255, 255),
                           (cx - r // 3, cy - r // 3), r // 4)
        for ex in [-r // 3, r // 3]:
            pygame.draw.circle(surface, (255, 255, 255),
                               (cx + ex, cy - r // 5), r // 6)
            pygame.draw.circle(surface, (30, 30, 30),
                               (cx + ex, cy - r // 5), r // 9)
        sm_rect = pygame.Rect(cx - r // 2, cy, r, r // 2)
        pygame.draw.arc(surface, (255, 255, 255), sm_rect,
                        math.pi, 2 * math.pi, 2)
