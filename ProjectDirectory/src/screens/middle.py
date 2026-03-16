"""
screens/middle.py
=================
MiddleSchoolExperimentScreen — Grades 6–8 science lab.

Features
--------
- Live animated grid preview
- Protocol multi-select checkboxes (5 protocols)
- Grid size + trial count sliders
- "Run Experiment" — silent batch runner with progress bar
- Three graph views: Bar (avg), Line (run history), Table
- Student judgment text box
"""

import random
from collections import defaultdict
import pygame

from screens.base import Screen

from engine.grid import Grid
from engine.player import Player
from engine.simulation import Simulation
from engine.stats import MultiProtocolStats
from engine.protocols import ALL_PROTOCOLS, PureRandom

from ui.widgets import Button, Slider
from ui.drawing import draw_text, draw_bar_graph, draw_line_graph
from music import stop_celebration
from constants import (
    C_BG, C_PANEL, C_BORDER, C_GRID_LINE,
    C_ACCENT, C_GREEN_LT, C_GREEN_MID, C_TEXT, C_DIM,
    PLAYER_COLORS, CELL_MID, MS_GRID_W, MS_PANEL_W,
)


class MiddleSchoolExperimentScreen(Screen):

    def __init__(self, app):
        super().__init__(app)
        W = MS_GRID_W + MS_PANEL_W + 20
        H = 700
        app.screen = pygame.display.set_mode((W, H))
        f = app.fonts

        self.mp_stats = MultiProtocolStats()

        # ── Sliders ──────────────────────────────────────────────────────────
        bx = MS_GRID_W + 14
        self.sl_rows    = Slider(bx, 55,  160, "Rows",    3, 15, 6,  f["sm"], f["md"])
        self.sl_cols    = Slider(bx, 115, 160, "Cols",    3, 15, 6,  f["sm"], f["md"])
        self.sl_trials  = Slider(bx, 175, 160, "Trials",  5, 200, 30, f["sm"], f["md"])
        self.sl_players = Slider(bx, 235, 160, "Players", 2,  4,  2,  f["sm"], f["md"])

        # ── Protocol checkboxes ───────────────────────────────────────────────
        self._proto_instances  = [cls() for cls in ALL_PROTOCOLS]
        self._proto_selected   = {p.name: True for p in self._proto_instances}
        self._proto_rects      = {}
        py = 300
        for p in self._proto_instances:
            self._proto_rects[p.name] = pygame.Rect(bx, py, 16, 16)
            py += 28

        # ── Buttons ───────────────────────────────────────────────────────────
        self.btn_run   = Button((bx, py + 10, 160, 46), "▶ Run Experiment",
                                font=f["md"], color=(40,100,40), hover_color=(60,160,60))
        self.btn_clear = Button((bx, py + 66, 160, 36), "🗑 Clear Results",
                                font=f["sm"], color=(80,30,30), hover_color=(140,50,50))
        self.btn_menu  = Button((bx, H - 54, 160, 40), "🏠 Menu",
                                font=f["sm"], color=(40,40,60), hover_color=(70,70,100))

        # ── Experiment runner state ───────────────────────────────────────────
        self._running    = False
        self._exp_queue  = []   # [(proto_name, proto_instance), ...]
        self._exp_total  = 0

        # ── Graph view ────────────────────────────────────────────────────────
        self._graph_mode = "bar"   # "bar",   "line",  "table"
        gy = H - 220
        self._tab_rects = {
            "bar":   pygame.Rect(bx,       gy - 30, 65, 26),
            "line":  pygame.Rect(bx + 70,  gy - 30, 65, 26),
            "table": pygame.Rect(bx + 140, gy - 30, 65, 26),
        }
        self._graph_rect = pygame.Rect(bx, gy, MS_PANEL_W - 28, 200)

        # ── Student judgment box ──────────────────────────────────────────────
        self._judgment_text   = ""
        self._judgment_active = False
        self._judgment_box    = pygame.Rect(bx, H - 46, MS_PANEL_W - 28, 34)

        # ── Live preview sim ──────────────────────────────────────────────────
        self._live_sim   = None
        self._live_steps = 0
        self._init_live()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _init_live(self):
        rows = self.sl_rows.value
        cols = self.sl_cols.value
        n    = self.sl_players.value
        grid = Grid(rows, cols)
        players = _random_players(rows, cols, n)
        self._live_sim   = Simulation(grid, players)
        self._live_steps = 0

    def _start_experiment(self):
        selected = [p for p in self._proto_instances
                    if self._proto_selected[p.name]]
        if not selected:
            return
        trials = self.sl_trials.value
        queue  = [(p.name, type(p)) for p in selected] * trials
        random.shuffle(queue)
        self._exp_queue = queue
        self._exp_total = len(queue)
        self._running   = True
        self._init_live()

    def _run_silent(self, proto_cls) -> int:
        rows = self.sl_rows.value
        cols = self.sl_cols.value
        n    = self.sl_players.value
        grid = Grid(rows, cols)
        sim  = Simulation(grid, _random_players(rows, cols, n), proto_cls)
        while not sim.finished and sim.steps < 10_000:
            sim.step()
        return sim.steps

    # ── Screen interface ──────────────────────────────────────────────────────

    def handle_events(self, events):
        for event in events:
            # Sliders
            for sl in [self.sl_rows, self.sl_cols,
                       self.sl_trials, self.sl_players]:
                sl.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Protocol checkboxes
                for name, rect in self._proto_rects.items():
                    if rect.collidepoint(event.pos):
                        self._proto_selected[name] = not self._proto_selected[name]
                # Graph tabs
                for mode, rect in self._tab_rects.items():
                    if rect.collidepoint(event.pos):
                        self._graph_mode = mode
                # Judgment box focus
                self._judgment_active = self._judgment_box.collidepoint(event.pos)

            if self.btn_run.clicked(event):
                self._start_experiment()
            if self.btn_clear.clicked(event):
                self.mp_stats.clear()
                self._running = False
                self._exp_queue.clear()
            if self.btn_menu.clicked(event):
                stop_celebration()
                self.app.goto("menu")

            # Typing in judgment box
            if event.type == pygame.KEYDOWN and self._judgment_active:
                if event.key == pygame.K_BACKSPACE:
                    self._judgment_text = self._judgment_text[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self._judgment_active = False
                elif len(self._judgment_text) < 80:
                    self._judgment_text += event.unicode

    def update(self):
        if self._running and self._exp_queue:
            # Run a batch silently each frame so UI stays responsive
            batch = max(1, self._exp_total // 60)
            for _ in range(min(batch, len(self._exp_queue))):
                name, cls = self._exp_queue.pop(0)
                self.mp_stats.record(name, self._run_silent(cls))
            if not self._exp_queue:
                self._running = False
        else:
            # Keep the live preview animated
            if self._live_sim and not self._live_sim.finished:
                self._live_sim.step()
                self._live_steps += 1
            elif self._live_sim and self._live_sim.finished:
                self._init_live()

    def draw(self, surface):
        W, H = surface.get_size()
        surface.fill(C_BG)
        self._draw_live_grid(surface, W, H)
        self._draw_panel(surface, W, H)

    # ── Draw sections ─────────────────────────────────────────────────────────

    def _draw_live_grid(self, surface, W, H):
        rows = self.sl_rows.value
        cols = self.sl_cols.value
        cs   = min(CELL_MID,
                   MS_GRID_W // max(cols, 1),
                   (H - 80)  // max(rows, 1))
        gw   = cols * cs
        gh   = rows * cs
        gox  = (MS_GRID_W - gw) // 2
        goy  = (H - gh) // 2

        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(gox + c * cs, goy + r * cs, cs, cs)
                col  = (30, 90, 30) if (r + c) % 2 == 0 else (25, 80, 25)
                pygame.draw.rect(surface, col, rect)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

        if self._live_sim:
            cell_map = defaultdict(list)
            for p in self._live_sim.players:
                cell_map[(p.row, p.col)].append(p)
            for (r, c), grp in cell_map.items():
                cx_ = gox + c * cs + cs // 2
                cy_ = goy + r * cs + cs // 2
                for i, p in enumerate(grp):
                    ox  = (i - len(grp) // 2) * (cs // 4)
                    rad = max(4, cs // 3)
                    pygame.draw.circle(surface, p.color, (cx_ + ox, cy_), rad)

        draw_text(surface, self.app.fonts["sm"],
                  f"Live preview – step {self._live_steps}",
                  C_DIM, MS_GRID_W // 2, H - 30)

    def _draw_panel(self, surface, W, H):
        px = MS_GRID_W + 10
        bx = MS_GRID_W + 14
        pygame.draw.rect(surface, C_PANEL,  pygame.Rect(px, 0, MS_PANEL_W, H))
        pygame.draw.line(surface, C_BORDER, (px, 0), (px, H), 2)
        f = self.app.fonts

        draw_text(surface, f["lg"], "🌲 Grades 6–8 Lab",
                  C_GREEN_LT, px + MS_PANEL_W // 2, 24)

        for sl in [self.sl_rows, self.sl_cols, self.sl_trials, self.sl_players]:
            sl.draw(surface)

        # Protocol checkboxes
        y = 285
        surface.blit(f["sm"].render("Movement Protocols:", True, C_DIM), (bx, y))
        y += 22
        for name, rect in self._proto_rects.items():
            sel = self._proto_selected[name]
            pygame.draw.rect(surface,
                             (255, 255, 255) if sel else (60, 80, 60),
                             rect, border_radius=3)
            if sel:
                pygame.draw.line(surface, (30, 30, 30),
                                 (rect.x + 3, rect.centery),
                                 (rect.x + 6, rect.bottom - 3), 2)
                pygame.draw.line(surface, (30, 30, 30),
                                 (rect.x + 6, rect.bottom - 3),
                                 (rect.right - 3, rect.y + 3), 2)
            surface.blit(f["sm"].render(name[:24], True, C_TEXT),
                         (rect.right + 6, rect.y - 1))

        self.btn_run.draw(surface)
        self.btn_clear.draw(surface)

        # Progress bar
        if self._running and self._exp_total > 0:
            done = 1 - len(self._exp_queue) / self._exp_total
            bg   = pygame.Rect(bx, self.btn_run.rect.bottom + 4, 160, 10)
            fill = pygame.Rect(bx, self.btn_run.rect.bottom + 4, int(160 * done), 10)
            pygame.draw.rect(surface, (40, 60, 40), bg,   border_radius=5)
            pygame.draw.rect(surface, C_GREEN_LT,   fill, border_radius=5)
            surface.blit(f["sm"].render(f"{int(done*100)}%", True, C_ACCENT),
                         (bx + 168, self.btn_run.rect.bottom + 1))

        self._draw_graphs(surface, f)
        self._draw_judgment(surface, f, H)
        self.btn_menu.draw(surface)

    def _draw_graphs(self, surface, f):
        summary = self.mp_stats.summary()

        # Tab buttons
        for mode, rect in self._tab_rects.items():
            active = (self._graph_mode == mode)
            pygame.draw.rect(surface,
                             (40, 55, 40) if active else C_PANEL,
                             rect, border_radius=5)
            pygame.draw.rect(surface,
                             C_ACCENT if active else C_BORDER,
                             rect, 1, border_radius=5)
            draw_text(surface, f["sm"],
                      {"bar": "Bar", "line": "Line", "table": "Table"}[mode],
                      C_TEXT, rect.centerx, rect.centery)

        gr = self._graph_rect
        pygame.draw.rect(surface, (20, 35, 20), gr, border_radius=6)
        pygame.draw.rect(surface, C_BORDER,     gr, 1, border_radius=6)

        if not summary:
            draw_text(surface, f["sm"], "No data yet — run an experiment!",
                      C_DIM, gr.centerx, gr.centery)
            return

        if self._graph_mode == "bar":
            data   = [(s["name"][:14], s["avg"]) for s in summary]
            colors = [PLAYER_COLORS[i % len(PLAYER_COLORS)]
                      for i in range(len(data))]
            draw_bar_graph(surface, f["sm"],
                           gr.x + 4, gr.y + 4, gr.w - 8, gr.h - 8,
                           data, colors)
            draw_text(surface, f["sm"], "Average steps per protocol",
                      C_DIM, gr.centerx, gr.y - 10)

        elif self._graph_mode == "line":
            colors = [PLAYER_COLORS[i % len(PLAYER_COLORS)]
                      for i in range(len(summary))]
            series = [(s["name"][:10], colors[i], s["runs"])
                      for i, s in enumerate(summary)]
            draw_line_graph(surface, f["sm"],
                            gr.x + 30, gr.y + 4, gr.w - 34, gr.h - 8, series)
            # Mini legend below graph
            lx = gr.x + 4
            for i, s in enumerate(summary):
                pygame.draw.line(surface, colors[i],
                                 (lx, gr.bottom + 12), (lx + 18, gr.bottom + 12), 2)
                ll = f["sm"].render(s["name"][:10], True, colors[i])
                surface.blit(ll, (lx + 22, gr.bottom + 4))
                lx += ll.get_width() + 40

        elif self._graph_mode == "table":
            self._draw_table(surface, f, gr, summary)

    def _draw_table(self, surface, f, rect, summary):
        cols_def = ["Protocol", "Runs", "Min", "Max", "Avg"]
        col_frac = [42, 12, 12, 12, 16]   # percent widths
        cw       = [rect.w * p // 100 for p in col_frac]
        x0       = rect.x + 4
        y        = rect.y + 6

        # Header
        x = x0
        for label, w in zip(cols_def, cw):
            surface.blit(f["sm"].render(label, True, C_ACCENT), (x, y))
            x += w
        y += 20
        pygame.draw.line(surface, C_BORDER, (rect.x, y), (rect.right, y), 1)
        y += 4

        for i, s in enumerate(summary):
            if y > rect.bottom - 18:
                break
            row_col = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            x       = x0
            for val, w in zip([s["name"][:18], str(s["n"]),
                                str(s["min"]), str(s["max"]),
                                f"{s['avg']:.1f}"], cw):
                surface.blit(f["sm"].render(val, True, row_col), (x, y))
                x += w
            y += 22

    def _draw_judgment(self, surface, f, H):
        px = MS_GRID_W + 10
        bx = MS_GRID_W + 14
        draw_text(surface, f["sm"], "Which protocol is best? Why?",
                  C_DIM, px + MS_PANEL_W // 2, H - 90)
        border = C_ACCENT if self._judgment_active else C_BORDER
        pygame.draw.rect(surface, (20, 30, 20), self._judgment_box, border_radius=5)
        pygame.draw.rect(surface, border,       self._judgment_box, 1, border_radius=5)
        txt = self._judgment_text + ("|" if self._judgment_active else "")
        surface.blit(f["sm"].render(txt, True, C_TEXT),
                     (self._judgment_box.x + 6, self._judgment_box.y + 8))


# ── Utility ───────────────────────────────────────────────────────────────────

def _random_players(rows: int, cols: int, n: int) -> list:
    positions = random.sample(
        [(r, c) for r in range(rows) for c in range(cols)], k=n)
    return [Player(i + 1, r, c, PLAYER_COLORS[i])
            for i, (r, c) in enumerate(positions)]
