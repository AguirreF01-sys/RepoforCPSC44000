import pygame
import sys
import math
import random

from game.grid import Grid
from game.player import Player
from game.simulation import Simulation
from game.stats import StatsTracker
from music import init_music

# ── Constants ────────────────────────────────────────────────────────────────
CELL_SIZE   = 80
UI_WIDTH    = 260          # right-side panel
FPS         = 30

PLAYER_COLORS = [
    (220, 50,  50),   # Red
    (50,  80,  220),  # Blue
    (40,  180, 80),   # Green
    (220, 160, 30),   # Yellow
]
PLAYER_NAMES = ["Red", "Blue", "Green", "Yellow"]


# ── Balloon helper ────────────────────────────────────────────────────────────
class Balloon:
    def __init__(self, screen_w, screen_h):
        self.x      = random.randint(20, screen_w - 20)
        self.y      = screen_h + random.randint(0, 120)
        self.speed  = random.uniform(1.5, 3.5)
        self.wo     = random.uniform(0, 2 * math.pi)
        self.ws     = random.uniform(0.05, 0.1)
        self.color  = random.choice(PLAYER_COLORS + [(200, 80, 255)])
        self.r      = random.randint(14, 22)
        self.tick   = 0

    def update(self):
        self.y    -= self.speed
        self.tick += self.ws
        self.x    += math.sin(self.tick + self.wo) * 1.5

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(surface, self.color, (ix, iy), self.r)
        pygame.draw.circle(surface, (255, 255, 255),
                           (ix - self.r // 3, iy - self.r // 3), self.r // 4)
        pygame.draw.line(surface, (180, 180, 180),
                         (ix, iy + self.r), (ix + 5, iy + self.r + 18), 1)


# ── App state machine ─────────────────────────────────────────────────────────
class App:
    STATE_SETUP    = "setup"
    STATE_PLACE    = "place"
    STATE_RUNNING  = "running"
    STATE_FINISHED = "finished"

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Wandering in the Woods")

        # Start with a small window — resized after setup
        self.screen = pygame.display.set_mode((700, 500))
        self.clock  = pygame.time.Clock()
        self.font_sm  = pygame.font.SysFont("Arial", 14)
        self.font_md  = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_lg  = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_xl  = pygame.font.SysFont("Arial", 36, bold=True)

        self.song          = None
        self.music_started = False

        self.stats         = StatsTracker()
        self.state         = self.STATE_SETUP
        self.setup_screen  = SetupScreen(self.screen, self.font_sm,
                                         self.font_md, self.font_lg)

        # Set after setup
        self.rows = self.cols = self.num_players = None
        self.start_positions = []   # list of (row, col) chosen by user
        self.grid = self.simulation = None

        self.balloons      = []
        self.balloon_timer = 0
        self.step_count    = 0

    # ── resize window for game ────────────────────────────────────────────────
    def _resize_for_game(self):
        W = self.cols * CELL_SIZE + UI_WIDTH
        H = max(self.rows * CELL_SIZE, 420)
        self.screen = pygame.display.set_mode((W, H))
        self.grid_w = self.cols * CELL_SIZE
        self.grid_h = self.rows * CELL_SIZE

    # ── build / rebuild simulation from stored positions ──────────────────────
    def _build_simulation(self):
        self.grid = Grid(self.rows, self.cols)
        players = []
        for i, (r, c) in enumerate(self.start_positions):
            players.append(Player(i + 1, r, c, PLAYER_COLORS[i]))
        self.simulation    = Simulation(self.grid, players)
        self.step_count    = 0
        self.balloons      = []
        self.balloon_timer = 0
        self.music_started = False
        if self.song:
            self.song.stop()

    # ── drawing helpers ───────────────────────────────────────────────────────
    def _draw_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE,
                                   CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)

    def _draw_players(self):
        # Draw grouped players with merged circles
        occupied = {}
        for p in self.simulation.players:
            key = (p.row, p.col)
            occupied.setdefault(key, []).append(p)

        for (r, c), group in occupied.items():
            cx = c * CELL_SIZE + CELL_SIZE // 2
            cy = r * CELL_SIZE + CELL_SIZE // 2
            n  = len(group)
            if n == 1:
                p = group[0]
                pygame.draw.circle(self.screen, p.color, (cx, cy), CELL_SIZE // 3)
                # player number
                lbl = self.font_sm.render(PLAYER_NAMES[p.id - 1][0], True, (255, 255, 255))
                self.screen.blit(lbl, lbl.get_rect(center=(cx, cy)))
            else:
                # Draw overlapping circles for grouped players
                offsets = self._group_offsets(n)
                rad     = CELL_SIZE // 4
                for i, p in enumerate(group):
                    ox, oy = offsets[i]
                    pygame.draw.circle(self.screen, p.color,
                                       (cx + ox, cy + oy), rad)
                    lbl = self.font_sm.render(PLAYER_NAMES[p.id - 1][0],
                                              True, (255, 255, 255))
                    self.screen.blit(lbl, lbl.get_rect(center=(cx + ox, cy + oy)))

    def _group_offsets(self, n):
        r = CELL_SIZE // 5
        if n == 2:
            return [(-r, 0), (r, 0)]
        if n == 3:
            return [(0, -r), (-r, r), (r, r)]
        return [(-r, -r), (r, -r), (-r, r), (r, r)]

    def _draw_ui_panel(self):
        W, H    = self.screen.get_size()
        px      = self.grid_w + 10
        panel_w = UI_WIDTH - 10

        # Background
        pygame.draw.rect(self.screen, (25, 25, 35),
                         pygame.Rect(self.grid_w, 0, UI_WIDTH, H))
        pygame.draw.line(self.screen, (80, 80, 100),
                         (self.grid_w, 0), (self.grid_w, H), 2)

        y = 14
        title = self.font_lg.render("🌲 Stats", True, (200, 230, 200))
        self.screen.blit(title, (px, y));  y += 38

        # Current run
        step_lbl = self.font_md.render(f"Step: {self.step_count}", True, (180, 220, 180))
        self.screen.blit(step_lbl, (px, y));  y += 28

        runs = self.stats.run_count()
        run_lbl = self.font_md.render(f"Runs: {runs}", True, (180, 220, 180))
        self.screen.blit(run_lbl, (px, y));  y += 36

        # Divider
        pygame.draw.line(self.screen, (70, 90, 70),
                         (px, y), (px + panel_w - 20, y), 1);  y += 14

        # History stats
        if runs > 0:
            headers = ["Min", "Max", "Avg"]
            vals    = [str(self.stats.shortest()),
                       str(self.stats.longest()),
                       f"{self.stats.average():.1f}"]
            colors  = [(100, 220, 120), (220, 100, 100), (180, 180, 255)]
            for h, v, col in zip(headers, vals, colors):
                hl = self.font_sm.render(h, True, (140, 140, 160))
                vl = self.font_md.render(v, True, col)
                self.screen.blit(hl, (px, y))
                self.screen.blit(vl, (px + 50, y))
                y += 26
            y += 10

            # Grouping behaviour
            pygame.draw.line(self.screen, (70, 90, 70),
                             (px, y), (px + panel_w - 20, y), 1);  y += 14
            gl = self.font_md.render("Grouping", True, (200, 200, 120))
            self.screen.blit(gl, (px, y));  y += 24
            for name, pct in self.stats.grouping_summary():
                bar_w = int((panel_w - 30) * pct)
                pygame.draw.rect(self.screen, (60, 100, 60),
                                 pygame.Rect(px, y + 8, panel_w - 30, 10))
                pygame.draw.rect(self.screen, (100, 200, 100),
                                 pygame.Rect(px, y + 8, bar_w, 10))
                nl = self.font_sm.render(f"{name}  {pct*100:.0f}%",
                                         True, (180, 200, 180))
                self.screen.blit(nl, (px, y));  y += 28

        # Last-run history sparkline
        history = self.stats.history()
        if len(history) > 1:
            y += 8
            pygame.draw.line(self.screen, (70, 90, 70),
                             (px, y), (px + panel_w - 20, y), 1);  y += 12
            hl2 = self.font_sm.render("Run history", True, (140, 140, 160))
            self.screen.blit(hl2, (px, y));  y += 18
            self._draw_sparkline(px, y, panel_w - 30, 40, history)
            y += 50

        # Buttons
        btn_y = H - 110
        self._draw_button("▶  Replay", px, btn_y, panel_w - 20,
                          (40, 140, 60), (80, 200, 100), "replay")
        self._draw_button("⚙  New Setup", px, btn_y + 50, panel_w - 20,
                          (100, 60, 140), (160, 100, 200), "setup")

    def _draw_sparkline(self, x, y, w, h, data):
        lo, hi = min(data), max(data)
        if lo == hi:
            hi = lo + 1
        pts = []
        for i, v in enumerate(data[-20:]):   # show last 20
            nx = x + int(i / (len(data[-20:]) - 1) * w) if len(data) > 1 else x
            ny = y + h - int((v - lo) / (hi - lo) * h)
            pts.append((nx, ny))
        if len(pts) >= 2:
            pygame.draw.lines(self.screen, (100, 200, 120), False, pts, 2)
        for pt in pts:
            pygame.draw.circle(self.screen, (160, 240, 160), pt, 3)

    def _draw_button(self, text, x, y, w, col_base, col_hover, tag):
        rect  = pygame.Rect(x, y, w, 38)
        mx, my = pygame.mouse.get_pos()
        hover  = rect.collidepoint(mx, my)
        col    = col_hover if hover else col_base
        pygame.draw.rect(self.screen, col, rect, border_radius=8)
        lbl = self.font_md.render(text, True, (240, 240, 240))
        self.screen.blit(lbl, lbl.get_rect(center=rect.center))
        # store for click detection
        if not hasattr(self, "_buttons"):
            self._buttons = {}
        self._buttons[tag] = rect

    def _draw_place_screen(self):
        self.screen.fill((20, 60, 30))
        self._draw_grid()

        placed = len(self.start_positions)
        remaining = self.num_players - placed

        # Already-placed markers
        for i, (r, c) in enumerate(self.start_positions):
            cx = c * CELL_SIZE + CELL_SIZE // 2
            cy = r * CELL_SIZE + CELL_SIZE // 2
            pygame.draw.circle(self.screen, PLAYER_COLORS[i], (cx, cy), CELL_SIZE // 3)
            lbl = self.font_md.render(PLAYER_NAMES[i][0], True, (255, 255, 255))
            self.screen.blit(lbl, lbl.get_rect(center=(cx, cy)))

        # Hover highlight
        mx, my = pygame.mouse.get_pos()
        hc, hr = mx // CELL_SIZE, my // CELL_SIZE
        if 0 <= hr < self.rows and 0 <= hc < self.cols:
            pos_taken = any(r == hr and c == hc for r, c in self.start_positions)
            if not pos_taken and remaining > 0:
                s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                s.fill((*PLAYER_COLORS[placed], 80))
                self.screen.blit(s, (hc * CELL_SIZE, hr * CELL_SIZE))

        # Instructions banner
        W, H = self.screen.get_size()
        banner = pygame.Surface((W, 44), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 160))
        self.screen.blit(banner, (0, H - 44))
        if remaining > 0:
            msg = f"Click to place {PLAYER_NAMES[placed]} player  ({remaining} left)"
        else:
            msg = "All placed! Click anywhere to start."
        txt = self.font_md.render(msg, True, (230, 230, 230))
        self.screen.blit(txt, txt.get_rect(center=(W // 2, H - 22)))

    def _draw_finished_overlay(self):
        W, H = self.screen.get_size()
        s = pygame.Surface((self.grid_w, 60), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        self.screen.blit(s, (0, self.grid_h // 2 - 30))
        msg = self.font_xl.render("🎉 Players Met!", True, (255, 230, 80))
        self.screen.blit(msg, msg.get_rect(center=(self.grid_w // 2, self.grid_h // 2)))

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        self.song = init_music()

        while True:
            self._buttons = {}

            # ── SETUP screen ──
            if self.state == self.STATE_SETUP:
                result = self.setup_screen.handle_events()
                if result:
                    self.rows, self.cols, self.num_players = result
                    self._resize_for_game()
                    self.start_positions = []
                    self.state = self.STATE_PLACE
                self.setup_screen.draw()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            # ── PLACE screen ──
            if self.state == self.STATE_PLACE:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        c, r = mx // CELL_SIZE, my // CELL_SIZE
                        if 0 <= r < self.rows and 0 <= c < self.cols:
                            pos_taken = any(pr == r and pc == c
                                            for pr, pc in self.start_positions)
                            if not pos_taken:
                                if len(self.start_positions) < self.num_players:
                                    self.start_positions.append((r, c))
                                if len(self.start_positions) == self.num_players:
                                    self._build_simulation()
                                    self.state = self.STATE_RUNNING

                self._draw_place_screen()
                pygame.display.flip()
                self.clock.tick(FPS)
                continue

            # ── RUNNING / FINISHED ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if "replay" in self._buttons and \
                            self._buttons["replay"].collidepoint(event.pos):
                        self._build_simulation()
                        self.state = self.STATE_RUNNING
                    if "setup" in self._buttons and \
                            self._buttons["setup"].collidepoint(event.pos):
                        self.state = self.STATE_SETUP
                        self.setup_screen = SetupScreen(
                            self.screen, self.font_sm, self.font_md, self.font_lg)

            if self.state == self.STATE_RUNNING:
                if not self.simulation.finished:
                    self.simulation.step()
                    self.step_count += 1
                    # record grouping events
                    self.stats.record_grouping(self.simulation.players)
                else:
                    self.stats.record_run(self.step_count)
                    if not self.music_started:
                        self.song.play(loops=-1)
                        self.music_started = True
                    self.state = self.STATE_FINISHED

            # Draw game
            self.screen.fill((30, 120, 30))
            self._draw_grid()
            self._draw_players()
            self._draw_ui_panel()

            if self.state == self.STATE_FINISHED:
                self._draw_finished_overlay()
                self.balloon_timer += 1
                if self.balloon_timer % 6 == 0:
                    self.balloons.append(
                        Balloon(self.grid_w, self.grid_h))
                self.balloons = [b for b in self.balloons if b.y > -60]
                for b in self.balloons:
                    b.update()
                    b.draw(self.screen)

            pygame.display.flip()
            self.clock.tick(FPS)


def run_grade35_mode():
    App().run()


if __name__ == "__main__":
    run_grade35_mode()