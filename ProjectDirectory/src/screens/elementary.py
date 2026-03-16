"""
screens/elementary.py
=====================
Grades 3–5 screens:

    ElementarySetupScreen  — sliders for rows/cols/players
    ElementaryPlaceScreen  — click-to-place starting positions
    ElementarySimScreen    — simulation + live stats panel
"""

from collections import defaultdict
import pygame

from screens.base import Screen
from engine.grid import Grid
from engine.player import Player
from engine.simulation import Simulation
from engine.stats import StatsTracker

from ui.widgets import Button, Slider
from ui.drawing import draw_text, draw_line_graph
from effects.balloons import Balloon

from music import play_celebration, stop_celebration
from constants import (
    C_BG, C_PANEL, C_BORDER, C_GRASS, C_GRID_LINE,
    C_ACCENT, C_GREEN_LT, C_TEXT, C_DIM,
    PLAYER_COLORS, PLAYER_NAMES, CELL_ELEM,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  SETUP
# ═══════════════════════════════════════════════════════════════════════════════

class ElementarySetupScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        W, H = 760, 520
        app.screen = pygame.display.set_mode((W, H))
        f  = app.fonts
        cx = W // 2

        self.sl_rows = Slider(cx-180, 160, 240, "Rows",    3, 12, 6,  f["sm"], f["md"])
        self.sl_cols = Slider(cx-180, 230, 240, "Columns", 3, 12, 6,  f["sm"], f["md"])
        self.sl_play = Slider(cx-180, 300, 240, "Players", 2,  4, 2,  f["sm"], f["md"])

        self.btn_start = Button((cx-120, 380, 240, 52), "▶  Place Players", font=f["md"])
        self.btn_menu  = Button((20, H-60, 110, 40),    "🏠 Menu",          font=f["sm"])

    def handle_events(self, events):
        for event in events:
            for sl in [self.sl_rows, self.sl_cols, self.sl_play]:
                sl.handle_event(event)
            if self.btn_start.clicked(event):
                self.app.goto("elem_place",
                              rows=self.sl_rows.value,
                              cols=self.sl_cols.value,
                              num_players=self.sl_play.value)
            if self.btn_menu.clicked(event):
                self.app.goto("menu")

    def draw(self, surface):
        surface.fill(C_BG)
        W, H = surface.get_size()
        cx   = W // 2

        draw_text(surface, self.app.fonts["xl"],
                  "🌿 Grades 3 – 5  Setup", C_GREEN_LT, cx, 60)

        panel = pygame.Rect(cx - 220, 130, 440, 230)
        pygame.draw.rect(surface, C_PANEL,  panel, border_radius=14)
        pygame.draw.rect(surface, C_BORDER, panel, 2, border_radius=14)

        for sl in [self.sl_rows, self.sl_cols, self.sl_play]:
            sl.draw(surface)

        hint = self.app.fonts["sm"].render(
            f"Grid: {self.sl_rows.value} × {self.sl_cols.value}  •  "
            f"{self.sl_play.value} players", True, C_DIM)
        surface.blit(hint, hint.get_rect(center=(cx, 360)))

        self.btn_start.draw(surface)
        self.btn_menu.draw(surface)


# ═══════════════════════════════════════════════════════════════════════════════
#  PLACE
# ═══════════════════════════════════════════════════════════════════════════════

class ElementaryPlaceScreen(Screen):
    def __init__(self, app, rows: int, cols: int, num_players: int):
        super().__init__(app)
        self.rows        = rows
        self.cols        = cols
        self.num_players = num_players
        self.positions   = []   # list of (row, col)

        W = cols * CELL_ELEM + 20
        H = rows * CELL_ELEM + 60
        app.screen = pygame.display.set_mode((W, H))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                c = mx // CELL_ELEM
                r = my // CELL_ELEM
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    if (not any(pr == r and pc == c for pr, pc in self.positions)
                            and len(self.positions) < self.num_players):
                        self.positions.append((r, c))
                    if len(self.positions) == self.num_players:
                        self.app.goto("elem_sim",
                                      rows=self.rows, cols=self.cols,
                                      num_players=self.num_players,
                                      positions=list(self.positions))
            if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
                if self.positions:
                    self.positions.pop()

    def draw(self, surface):
        surface.fill(C_GRASS)
        W, H = surface.get_size()

        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(c * CELL_ELEM, r * CELL_ELEM, CELL_ELEM, CELL_ELEM)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

        # Placed players
        for i, (r, c) in enumerate(self.positions):
            cx_ = c * CELL_ELEM + CELL_ELEM // 2
            cy_ = r * CELL_ELEM + CELL_ELEM // 2
            pygame.draw.circle(surface, PLAYER_COLORS[i], (cx_, cy_), CELL_ELEM // 3)
            lbl = self.app.fonts["md"].render(PLAYER_NAMES[i][0], True, (255, 255, 255))
            surface.blit(lbl, lbl.get_rect(center=(cx_, cy_)))

        # Hover ghost
        placed = len(self.positions)
        mx, my = pygame.mouse.get_pos()
        hc, hr = mx // CELL_ELEM, my // CELL_ELEM
        if (0 <= hr < self.rows and 0 <= hc < self.cols
                and placed < self.num_players):
            ghost = pygame.Surface((CELL_ELEM, CELL_ELEM), pygame.SRCALPHA)
            ghost.fill((*PLAYER_COLORS[placed], 80))
            surface.blit(ghost, (hc * CELL_ELEM, hr * CELL_ELEM))

        # Bottom banner
        banner = pygame.Surface((W, 50), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 160))
        surface.blit(banner, (0, H - 50))
        remaining = self.num_players - placed
        msg = (f"Click to place {PLAYER_NAMES[placed]}  ({remaining} left)"
               if remaining > 0 else "Starting…")
        draw_text(surface, self.app.fonts["md"], msg, (230, 230, 230), W // 2, H - 25)


# ═══════════════════════════════════════════════════════════════════════════════
#  SIMULATION + STATS
# ═══════════════════════════════════════════════════════════════════════════════

class ElementarySimScreen(Screen):
    UI_W = 260

    def __init__(self, app, rows: int, cols: int,
                 num_players: int, positions: list):
        super().__init__(app)
        self.rows        = rows
        self.cols        = cols
        self.num_players = num_players
        self.positions   = positions
        self.stats       = StatsTracker()

        W = cols * CELL_ELEM + self.UI_W
        H = max(rows * CELL_ELEM, 480)
        app.screen  = pygame.display.set_mode((W, H))
        self.grid_w = cols * CELL_ELEM
        self.grid_h = rows * CELL_ELEM

        f  = app.fonts
        bx = self.grid_w + 12
        bw = self.UI_W - 24
        self.btn_replay = Button((bx, H-120, bw, 44), "▶ Replay",    font=f["md"])
        self.btn_setup  = Button((bx, H- 66, bw, 44), "⚙ New Setup", font=f["md"],
                                 color=(80,40,120), hover_color=(130,80,180))
        self.btn_menu   = Button((bx, H-180, bw, 44), "🏠 Menu",     font=f["sm"],
                                 color=(60,40,40),   hover_color=(100,60,60))

        self._balloons  = []
        self._bal_timer = 0
        self._music_on  = False
        self._build()

    # ── Build / reset simulation ──────────────────────────────────────────────

    def _build(self):
        stop_celebration()
        self._music_on  = False
        self._balloons  = []
        self._bal_timer = 0
        grid    = Grid(self.rows, self.cols)
        players = [Player(i + 1, r, c, PLAYER_COLORS[i])
                   for i, (r, c) in enumerate(self.positions)]
        self.sim   = Simulation(grid, players)
        self.steps = 0

    # ── Screen interface ──────────────────────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            if self.btn_replay.clicked(event):
                self._build()
            if self.btn_setup.clicked(event):
                self.app.goto("elem_setup")
            if self.btn_menu.clicked(event):
                self.app.goto("menu")

    def update(self):
        if not self.sim.finished:
            self.sim.step()
            self.steps += 1
            self.stats.record_step(self.sim.players)
        else:
            # Record exactly once per run
            hist = self.stats.history()
            if not hist or hist[-1] != self.steps:
                self.stats.record_run(self.steps)
            if not self._music_on:
                play_celebration()
                self._music_on = True

    def draw(self, surface):
        W, H = surface.get_size()
        surface.fill(C_GRASS)

        # Grid
        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(c * CELL_ELEM, r * CELL_ELEM, CELL_ELEM, CELL_ELEM)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

        # Players
        cell_map = defaultdict(list)
        for p in self.sim.players:
            cell_map[(p.row, p.col)].append(p)

        for (r, c), grp in cell_map.items():
            cx_ = c * CELL_ELEM + CELL_ELEM // 2
            cy_ = r * CELL_ELEM + CELL_ELEM // 2
            offs = _group_offsets(len(grp), CELL_ELEM)
            for i, p in enumerate(grp):
                ox, oy = offs[i]
                pygame.draw.circle(surface, p.color,
                                   (cx_ + ox, cy_ + oy), CELL_ELEM // 3)
                lbl = self.app.fonts["sm"].render(
                    PLAYER_NAMES[p.id - 1][0], True, (255, 255, 255))
                surface.blit(lbl, lbl.get_rect(center=(cx_ + ox, cy_ + oy)))

        # Stats panel
        self._draw_panel(surface, W, H)

        # Finished overlay + balloons
        if self.sim.finished:
            ovl = pygame.Surface((self.grid_w, 60), pygame.SRCALPHA)
            ovl.fill((0, 0, 0, 160))
            surface.blit(ovl, (0, self.grid_h // 2 - 30))
            draw_text(surface, self.app.fonts["xl"], "🎉 They Met!",
                      (255, 230, 60), self.grid_w // 2, self.grid_h // 2)
            self._bal_timer += 1
            if self._bal_timer % 6 == 0:
                self._balloons.append(Balloon(self.grid_w, self.grid_h))
            self._balloons = [b for b in self._balloons if b.y > -60]
            for b in self._balloons:
                b.update(); b.draw(surface)

    def _draw_panel(self, surface, W, H):
        px = self.grid_w
        pygame.draw.rect(surface, C_PANEL,  pygame.Rect(px, 0, self.UI_W, H))
        pygame.draw.line(surface, C_BORDER, (px, 0), (px, H), 2)

        bx = px + 12
        f  = self.app.fonts

        draw_text(surface, f["lg"], "📊 Stats",
                  C_GREEN_LT, px + self.UI_W // 2, 28)

        y = 55
        draw_text(surface, f["md"], f"Step: {self.steps}",
                  C_TEXT, px + self.UI_W // 2, y);  y += 30
        n = self.stats.run_count()
        draw_text(surface, f["md"], f"Runs: {n}",
                  C_TEXT, px + self.UI_W // 2, y);  y += 36

        if n > 0:
            pygame.draw.line(surface, C_BORDER,
                             (bx, y), (bx + self.UI_W - 30, y), 1);  y += 12

            for label, val, col in [
                ("Min", str(self.stats.shortest()),      (100, 220, 120)),
                ("Max", str(self.stats.longest()),       (220, 100, 100)),
                ("Avg", f"{self.stats.average():.1f}",  (180, 180, 255)),
            ]:
                surface.blit(f["sm"].render(label, True, C_DIM), (bx, y))
                surface.blit(f["md"].render(val,   True, col),   (bx + 50, y))
                y += 26

            y += 8
            # Grouping bars
            for pair, pct in self.stats.grouping_summary():
                bw2 = int((self.UI_W - 34) * pct)
                pygame.draw.rect(surface, (50, 80, 50),
                                 pygame.Rect(bx, y + 8, self.UI_W - 34, 10))
                pygame.draw.rect(surface, C_GREEN_LT,
                                 pygame.Rect(bx, y + 8, bw2, 10))
                surface.blit(f["sm"].render(f"{pair}  {pct*100:.0f}%", True, C_TEXT),
                             (bx, y))
                y += 26

            # Sparkline
            hist = self.stats.history()
            if len(hist) > 1:
                pygame.draw.line(surface, C_BORDER,
                                 (bx, y), (bx + self.UI_W - 30, y), 1);  y += 10
                draw_line_graph(surface, f["sm"], bx, y,
                                self.UI_W - 30, 55,
                                [("runs", C_GREEN_LT, hist)])
                y += 60

        self.btn_replay.draw(surface)
        self.btn_setup.draw(surface)
        self.btn_menu.draw(surface)


# ── Utility ───────────────────────────────────────────────────────────────────

def _group_offsets(n: int, cell: int) -> list[tuple[int, int]]:
    r = cell // 5
    if n == 1: return [(0, 0)]
    if n == 2: return [(-r, 0), (r, 0)]
    if n == 3: return [(0, -r), (-r, r), (r, r)]
    return [(-r, -r), (r, -r), (-r, r), (r, r)]
