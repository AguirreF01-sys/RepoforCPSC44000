"""
wandering_woods_full.py
=======================
Wandering in the Woods  –  Full Edition
Grades K-2  |  3-5  |  6-8

Run with:  python wandering_woods_full.py
Requires:  pygame   numpy
"""

import pygame
import sys
import math
import random
import time
from collections import defaultdict
from itertools import combinations

# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS & SHARED PALETTE
# ═══════════════════════════════════════════════════════════════════════════════

FPS = 30

PLAYER_COLORS = [
    (220,  50,  50),  # Red
    ( 50,  80, 220),  # Blue
    ( 40, 180,  80),  # Green
    (220, 160,  30),  # Yellow
]
PLAYER_NAMES = ["Red", "Blue", "Green", "Yellow"]

# Dark forest palette
C_BG        = ( 14,  22,  14)
C_PANEL     = ( 22,  38,  22)
C_BORDER    = ( 60, 100,  60)
C_GRID_LINE = (180, 200, 180)
C_GRASS     = ( 30, 110,  30)
C_TEXT      = (210, 240, 210)
C_DIM       = (130, 160, 130)
C_ACCENT    = (255, 210,  60)
C_GREEN_LT  = (100, 200, 100)
C_GREEN_MID = ( 60, 130,  60)


# ═══════════════════════════════════════════════════════════════════════════════
#  MUSIC  (synthesised, no external files)
# ═══════════════════════════════════════════════════════════════════════════════

def _make_tone(freq, duration, volume=0.18):
    import numpy as np
    sr = 44100
    frames = int(sr * duration)
    t = (freq * 2 * math.pi / sr * (
        __import__('numpy').arange(frames))).tolist()
    raw = [math.copysign(1, math.sin(v)) for v in t]
    env = [1.0] * frames
    fade = max(1, int(frames * 0.15))
    for i in range(fade):
        env[frames - fade + i] = 1 - i / fade
    for i in range(min(int(frames * 0.02), frames)):
        env[i] = i / max(1, int(frames * 0.02))
    samples = [int(raw[i] * env[i] * volume * 32767) for i in range(frames)]
    import numpy as np
    arr = np.array(samples, dtype=np.int16)
    stereo = np.ascontiguousarray(np.column_stack([arr, arr]))
    return stereo

def _make_silence(duration):
    import numpy as np
    return np.zeros((int(44100 * duration), 2), dtype=np.int16)

_NOTES = {
    "C4":261.63,"D4":293.66,"E4":329.63,"F4":349.23,
    "G4":392.00,"A4":440.00,"B4":493.88,
    "C5":523.25,"D5":587.33,"E5":659.25,"REST":0,
}
_BEAT = 0.21
_SONG = [
    ("G4",1),("G4",1),("G4",1),("E4",1.5),("G4",0.5),
    ("G4",1),("E4",1.5),("G4",0.5),("G4",1),("G4",1),
    ("B4",1),("B4",1),("A4",1),("G4",1),("A4",1),("G4",2),("REST",.5),
    ("D5",1),("D5",1),("D5",1),("D5",1.5),("B4",.5),
    ("C5",1),("C5",1),("C5",1),("C5",1.5),("A4",.5),
    ("G4",1),("G4",.5),("G4",.5),("B4",1),("B4",.5),("B4",.5),
    ("A4",1),("G4",1),("A4",1),("G4",2),
]

_celebration_sound = None

def init_music():
    global _celebration_sound
    try:
        import numpy as np
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        parts = []
        for note, beats in _SONG:
            dur = beats * _BEAT
            if note == "REST":
                parts.append(_make_silence(dur))
            else:
                parts.append(_make_tone(_NOTES[note], dur))
            parts.append(_make_silence(0.02))
        full = np.concatenate(parts, axis=0)
        _celebration_sound = pygame.sndarray.make_sound(
            np.ascontiguousarray(full))
    except Exception:
        _celebration_sound = None

def play_celebration():
    if _celebration_sound:
        _celebration_sound.play(loops=-1)

def stop_celebration():
    if _celebration_sound:
        _celebration_sound.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  CORE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class Grid:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols

    def neighbors(self, row, col):
        out = []
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = row+dr, col+dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                out.append((nr, nc))
        return out

    def center(self):
        return (self.rows // 2, self.cols // 2)


class Player:
    def __init__(self, pid, row, col, color):
        self.id    = pid
        self.row   = row
        self.col   = col
        self.color = color
        self.group = {pid}   # set of player ids in this group
        self.prev_row = row
        self.prev_col = col

    def move_to(self, r, c):
        self.prev_row, self.prev_col = self.row, self.col
        self.row, self.col = r, c


# ── Movement Protocols ────────────────────────────────────────────────────────

class Protocol:
    name = "Base"
    description = "Abstract base"

    def choose_move(self, player, grid, all_players):
        raise NotImplementedError


class PureRandom(Protocol):
    name = "Pure Random Walk"
    description = "Each step picks a random valid neighbor — no bias at all."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        return random.choice(nbrs) if nbrs else (player.row, player.col)


class BiasedWalk(Protocol):
    name = "Biased Walk"
    description = "Slightly prefers moving right and down (southeast drift)."

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
        total = sum(weights)
        pick  = random.uniform(0, total)
        cum   = 0
        for (r, c), w in zip(nbrs, weights):
            cum += w
            if pick <= cum:
                return (r, c)
        return nbrs[-1]


class ZigZag(Protocol):
    name = "Zig-Zag"
    description = "Alternates horizontal and vertical moves each step."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)
        dr = player.row - player.prev_row
        dc = player.col - player.prev_col
        # If last move was horizontal, prefer vertical, and vice versa
        if abs(dc) > abs(dr):
            pref = [(r, c) for (r, c) in nbrs if c == player.col]   # vertical
        else:
            pref = [(r, c) for (r, c) in nbrs if r == player.row]   # horizontal
        return random.choice(pref) if pref else random.choice(nbrs)


class EdgeFollower(Protocol):
    name = "Edge Follower"
    description = "Prefers cells on or near the grid boundary."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)
        def edge_score(r, c):
            return int(r == 0 or r == grid.rows-1 or
                       c == 0 or c == grid.cols-1) * 3 + 1
        weights = [edge_score(r, c) for r, c in nbrs]
        total   = sum(weights)
        pick    = random.uniform(0, total)
        cum     = 0
        for (r, c), w in zip(nbrs, weights):
            cum += w
            if pick <= cum:
                return (r, c)
        return nbrs[-1]


class CenterSeeker(Protocol):
    name = "Move to Center"
    description = "Tends to drift toward the center of the grid."

    def choose_move(self, player, grid, all_players):
        nbrs = grid.neighbors(player.row, player.col)
        if not nbrs:
            return (player.row, player.col)
        cr, cc = grid.center()
        def dist(r, c):
            return abs(r - cr) + abs(c - cc)
        cur_d   = dist(player.row, player.col)
        weights = []
        for (r, c) in nbrs:
            d = dist(r, c)
            w = 3.0 if d < cur_d else 1.0
            weights.append(w)
        total = sum(weights)
        pick  = random.uniform(0, total)
        cum   = 0
        for (r, c), w in zip(nbrs, weights):
            cum += w
            if pick <= cum:
                return (r, c)
        return nbrs[-1]


ALL_PROTOCOLS = [PureRandom, BiasedWalk, ZigZag, EdgeFollower, CenterSeeker]


# ── Simulation Engine ─────────────────────────────────────────────────────────

class Simulation:
    """
    Supports:
    - Pluggable movement protocols per player
    - Group merging: once two players meet they move as one
    - finished when all players are in one group
    """

    def __init__(self, grid, players, protocol_cls=None):
        self.grid     = grid
        self.players  = list(players)
        self.protocol = (protocol_cls or PureRandom)()
        self.finished = False
        self.steps    = 0
        # groups: map group_leader_id -> list of Player objects
        self._rebuild_groups()

    def _rebuild_groups(self):
        self._groups = defaultdict(list)
        for p in self.players:
            self._groups[min(p.group)].append(p)

    def step(self):
        if self.finished:
            return
        self.steps += 1

        # Move each group as a unit (leader decides, all follow)
        cell_to_players = defaultdict(list)
        for leader_id, members in list(self._groups.items()):
            rep = members[0]
            new_r, new_c = self.protocol.choose_move(
                rep, self.grid, self.players)
            for m in members:
                m.move_to(new_r, new_c)
            cell_to_players[(new_r, new_c)].extend(members)

        # Merge groups that land on same cell
        merged = False
        for cell, occupants in cell_to_players.items():
            if len(occupants) > 1:
                merged = True
                all_ids = set()
                for p in occupants:
                    all_ids |= p.group
                for p in occupants:
                    p.group = all_ids

        if merged:
            self._rebuild_groups()

        # Check finished: all players in one group
        if len(self._groups) == 1:
            self.finished = True

    def snapshot_positions(self):
        return [(p.row, p.col) for p in self.players]


# ── Stats Tracker ─────────────────────────────────────────────────────────────

class StatsTracker:
    def __init__(self):
        self._history    = []
        self._grouping   = defaultdict(int)
        self._total_obs  = 0

    def record_step(self, players):
        cell_map = defaultdict(list)
        for p in players:
            cell_map[(p.row, p.col)].append(p)
        for group in cell_map.values():
            if len(group) >= 2:
                for a, b in combinations(group, 2):
                    key = f"P{a.id}&P{b.id}"
                    self._grouping[key] += 1
        self._total_obs += 1

    def record_run(self, steps):
        self._history.append(steps)

    def run_count(self):   return len(self._history)
    def history(self):     return list(self._history)
    def shortest(self):    return min(self._history) if self._history else 0
    def longest(self):     return max(self._history) if self._history else 0
    def average(self):
        return sum(self._history)/len(self._history) if self._history else 0.0

    def grouping_summary(self):
        if not self._grouping or not self._total_obs:
            return []
        items = [(lbl, cnt/self._total_obs)
                 for lbl, cnt in self._grouping.items()]
        items.sort(key=lambda x: -x[1])
        return items

    def protocol_compare(self):
        """Returns dict protocol_name -> list of run lengths"""
        return dict(self._by_protocol) if hasattr(self,'_by_protocol') else {}


class MultiProtocolStats:
    """Tracks separate run lists per protocol for 6-8 comparison."""
    def __init__(self):
        self._data = defaultdict(list)   # protocol_name -> [steps, ...]

    def record(self, protocol_name, steps):
        self._data[protocol_name].append(steps)

    def protocols(self):
        return list(self._data.keys())

    def runs_for(self, name):
        return list(self._data[name])

    def summary(self):
        """Returns list of dicts with min/max/avg per protocol."""
        out = []
        for name, runs in self._data.items():
            if runs:
                out.append({
                    "name":  name,
                    "n":     len(runs),
                    "min":   min(runs),
                    "max":   max(runs),
                    "avg":   sum(runs)/len(runs),
                    "runs":  list(runs),
                })
        out.sort(key=lambda x: x["avg"])
        return out


# ═══════════════════════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

class Button:
    def __init__(self, rect, label, color=None, hover_color=None,
                 text_color=(240,240,240), font=None, tag=None, radius=8):
        self.rect        = pygame.Rect(rect)
        self.label       = label
        self.color       = color       or C_GREEN_MID
        self.hover_color = hover_color or C_GREEN_LT
        self.text_color  = text_color
        self.font        = font
        self.tag         = tag or label
        self.radius      = radius

    def draw(self, surface):
        mx, my = pygame.mouse.get_pos()
        col    = self.hover_color if self.rect.collidepoint(mx, my) else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=self.radius)
        if self.font:
            lbl = self.font.render(self.label, True, self.text_color)
            surface.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


class Slider:
    def __init__(self, x, y, w, label, lo, hi, value, font_sm, font_md):
        self.rect    = pygame.Rect(x, y, w, 28)
        self.label   = label
        self.lo, self.hi = lo, hi
        self.value   = value
        self.drag    = False
        self.font_sm = font_sm
        self.font_md = font_md

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.drag = True
                self._set(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self._set(event.pos[0])

    def _set(self, mx):
        frac = max(0., min(1., (mx - self.rect.x) / self.rect.w))
        self.value = round(self.lo + frac * (self.hi - self.lo))

    def draw(self, surface):
        frac = (self.value - self.lo) / max(1, self.hi - self.lo)
        track = pygame.Rect(self.rect.x, self.rect.centery-3, self.rect.w, 6)
        pygame.draw.rect(surface, (50,70,50), track, border_radius=3)
        fill  = pygame.Rect(self.rect.x, self.rect.centery-3,
                            int(self.rect.w*frac), 6)
        pygame.draw.rect(surface, C_GREEN_LT, fill, border_radius=3)
        tx = self.rect.x + int(self.rect.w * frac)
        pygame.draw.circle(surface, C_ACCENT, (tx, self.rect.centery), 10)
        pygame.draw.circle(surface, (255,255,255), (tx, self.rect.centery), 4)
        lbl = self.font_sm.render(self.label, True, C_DIM)
        val = self.font_md.render(str(self.value), True, C_ACCENT)
        surface.blit(lbl, (self.rect.x, self.rect.y - 20))
        surface.blit(val, (self.rect.right + 12,
                           self.rect.centery - val.get_height()//2))


class Balloon:
    def __init__(self, sw, sh):
        self.x     = random.randint(20, sw-20)
        self.y     = sh + random.randint(0, 120)
        self.speed = random.uniform(1.5, 3.5)
        self.wo    = random.uniform(0, 2*math.pi)
        self.ws    = random.uniform(0.05, 0.1)
        self.color = random.choice(PLAYER_COLORS + [(200,80,255)])
        self.r     = random.randint(14, 22)
        self.tick  = 0

    def update(self):
        self.y    -= self.speed
        self.tick += self.ws
        self.x    += math.sin(self.tick + self.wo) * 1.5

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(surface, self.color, (ix,iy), self.r)
        pygame.draw.circle(surface, (255,255,255),
                           (ix-self.r//3, iy-self.r//3), self.r//4)
        pygame.draw.line(surface, (180,180,180),
                         (ix, iy+self.r), (ix+5, iy+self.r+18), 1)


def draw_text(surface, font, text, color, cx, cy):
    s = font.render(text, True, color)
    surface.blit(s, s.get_rect(center=(cx, cy)))


def draw_bar_graph(surface, font_sm, x, y, w, h, data, colors=None):
    """
    data: list of (label, value)
    Draws a horizontal bar chart inside rect(x,y,w,h).
    """
    if not data:
        return
    max_val = max(v for _, v in data) or 1
    bar_h   = min(36, (h - 20) // max(1, len(data)) - 6)
    oy      = y + 10
    for i, (label, value) in enumerate(data):
        bw     = int((w - 120) * value / max_val)
        col    = colors[i % len(colors)] if colors else C_GREEN_LT
        rect   = pygame.Rect(x + 90, oy, bw, bar_h)
        bg     = pygame.Rect(x + 90, oy, w - 120, bar_h)
        pygame.draw.rect(surface, (40,60,40), bg, border_radius=4)
        pygame.draw.rect(surface, col, rect, border_radius=4)
        lbl = font_sm.render(label, True, C_TEXT)
        surface.blit(lbl, (x+2, oy + bar_h//2 - lbl.get_height()//2))
        val = font_sm.render(f"{value:.1f}", True, C_ACCENT)
        surface.blit(val, (x+92+bw+4, oy + bar_h//2 - val.get_height()//2))
        oy += bar_h + 8


def draw_line_graph(surface, font_sm, x, y, w, h, series):
    """
    series: list of (label, color, [values])
    Draws overlaid line plots inside rect(x,y,w,h).
    """
    if not series:
        return
    all_vals = [v for _, _, vals in series for v in vals]
    if not all_vals:
        return
    lo = min(all_vals)
    hi = max(all_vals) or 1
    if lo == hi:
        hi = lo + 1
    # Axes
    pygame.draw.rect(surface, (40,60,40), pygame.Rect(x,y,w,h))
    pygame.draw.line(surface, C_BORDER, (x, y), (x, y+h), 1)
    pygame.draw.line(surface, C_BORDER, (x, y+h), (x+w, y+h), 1)
    for label, col, vals in series:
        if len(vals) < 2:
            continue
        pts = []
        for i, v in enumerate(vals):
            px_ = x + int(i / (len(vals)-1) * w)
            py_ = y + h - int((v - lo) / (hi - lo) * h)
            pts.append((px_, py_))
        pygame.draw.lines(surface, col, False, pts, 2)
        for pt in pts[-1:]:
            pygame.draw.circle(surface, col, pt, 4)
    # y-axis labels
    for tick in [lo, (lo+hi)//2, hi]:
        ty = y + h - int((tick - lo) / (hi - lo) * h)
        t  = font_sm.render(str(int(tick)), True, C_DIM)
        surface.blit(t, (x - t.get_width() - 4, ty - t.get_height()//2))


# ═══════════════════════════════════════════════════════════════════════════════
#  SCREEN BASE
# ═══════════════════════════════════════════════════════════════════════════════

class Screen:
    """Base class – each screen gets handle_events+update+draw."""

    def __init__(self, app):
        self.app = app

    def handle_events(self, events):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

class MainMenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        W, H = app.screen.get_size()
        cx   = W // 2
        f    = app.fonts
        bw, bh, gap = 260, 52, 14
        sy = H // 2 - 60
        labels = [("🌱  K – 2", "k2"),
                  ("🌿  Grades 3 – 5", "elem"),
                  ("🌲  Grades 6 – 8", "middle"),
                  ("📖  Instructions", "instructions"),
                  ("✕   Quit", "quit")]
        cols   = [C_GREEN_MID, (40,100,60), (30,80,100),
                  (80,60,100), (100,40,40)]
        hcols  = [C_GREEN_LT, (70,160,80), (60,130,160),
                  (130,100,160), (160,70,70)]
        self.buttons = []
        for i, (lbl, tag) in enumerate(labels):
            r = pygame.Rect(cx-bw//2, sy + i*(bh+gap), bw, bh)
            self.buttons.append(
                Button(r, lbl, cols[i], hcols[i], font=f["lg"], tag=tag))
        self._stars = [(random.randint(0,W), random.randint(0,H),
                        random.uniform(0.3,1.5)) for _ in range(60)]

    def handle_events(self, events):
        for event in events:
            for btn in self.buttons:
                if btn.clicked(event):
                    if btn.tag == "quit":
                        pygame.quit(); sys.exit()
                    self.app.goto(btn.tag)

    def draw(self, surface):
        surface.fill(C_BG)
        W, H = surface.get_size()
        # stars
        t = pygame.time.get_ticks() / 1000
        for sx, sy, sp in self._stars:
            a = int(120 + 80 * math.sin(t * sp + sx))
            r = max(1, int(sp * 1.5))
            pygame.draw.circle(surface, (a, int(a*1.1), a), (sx, sy), r)
        # title
        draw_text(surface, self.app.fonts["xl"],
                  "🌲 Wandering in the Woods", C_GREEN_LT, W//2, 90)
        draw_text(surface, self.app.fonts["sm"],
                  "Choose your grade level", C_DIM, W//2, 130)
        for btn in self.buttons:
            btn.draw(surface)


# ═══════════════════════════════════════════════════════════════════════════════
#  INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class InstructionsScreen(Screen):
    PAGES = [
        ("How the Game Works",
         ["Two or more players are placed on a grid of cells.",
          "Each step, every player moves to a random neighboring cell.",
          "The game ends when two (or more) players land on the same cell.",
          "We call that moment: they've MET in the woods!",
          "",
          "Try different grid sizes and starting positions.",
          "Does size change how long it takes to meet?"]),
        ("For K–2 Students",
         ["Big colourful grid, two cartoon characters.",
          "Watch them wander until they meet.",
          "Count the steps together as a class.",
          "Press Restart to try again!"]),
        ("For Grades 3–5",
         ["You choose the grid size and number of players.",
          "Click to place each player's starting position.",
          "Run it many times and see the statistics:",
          "  • Shortest run   • Longest run   • Average",
          "Does starting closer together help?",
          "What happens with more players?"]),
        ("For Grades 6–8",
         ["Run hundreds of trials automatically.",
          "Compare five different movement protocols:",
          "  Pure Random, Biased, Zig-Zag, Edge-Follower, Center-Seeker.",
          "Graphs update live as experiments run.",
          "A results table lets you rank which protocol is fastest.",
          "Think like a scientist — form a hypothesis first!"]),
    ]

    def __init__(self, app):
        super().__init__(app)
        self.page = 0
        W, H = app.screen.get_size()
        f    = app.fonts
        self.btn_back = Button(
            (40, H-70, 120, 44), "◀ Back", font=f["md"], tag="back")
        self.btn_prev = Button(
            (W//2-150, H-70, 120, 44), "◀ Prev", font=f["md"])
        self.btn_next = Button(
            (W//2+30,  H-70, 120, 44), "Next ▶", font=f["md"])

    def handle_events(self, events):
        for event in events:
            if self.btn_back.clicked(event):
                self.app.goto("menu")
            if self.btn_prev.clicked(event):
                self.page = max(0, self.page - 1)
            if self.btn_next.clicked(event):
                self.page = min(len(self.PAGES)-1, self.page + 1)

    def draw(self, surface):
        surface.fill(C_BG)
        W, H = surface.get_size()
        title, lines = self.PAGES[self.page]
        draw_text(surface, self.app.fonts["lg"], title, C_ACCENT, W//2, 80)
        y = 140
        for line in lines:
            lbl = self.app.fonts["md"].render(line, True, C_TEXT)
            surface.blit(lbl, (W//2 - lbl.get_width()//2, y))
            y += 32
        # page indicator
        dot_y = H - 110
        for i in range(len(self.PAGES)):
            col = C_ACCENT if i == self.page else C_BORDER
            pygame.draw.circle(surface, col, (W//2 + (i-1)*24, dot_y), 6)
        self.btn_back.draw(surface)
        self.btn_prev.draw(surface)
        self.btn_next.draw(surface)


# ═══════════════════════════════════════════════════════════════════════════════
#  K-2  GAME SCREEN
# ═══════════════════════════════════════════════════════════════════════════════

CELL_K2 = 90

class K2GameScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.ROWS = 5
        self.COLS = 5
        W = self.COLS * CELL_K2 + 200
        H = max(self.ROWS * CELL_K2 + 100, 560)
        app.screen = pygame.display.set_mode((W, H))
        self._reset()
        f = app.fonts
        self.btn_restart = Button(
            (self.COLS*CELL_K2+20, H-80, 160, 48),
            "↺ Restart", font=f["md"], tag="restart")
        self.btn_menu = Button(
            (self.COLS*CELL_K2+20, H-140, 160, 48),
            "🏠 Menu", font=f["md"], tag="menu")
        self._balloons   = []
        self._bal_timer  = 0
        self._music_on   = False

    def _reset(self):
        stop_celebration()
        self._music_on = False
        self.grid = Grid(self.ROWS, self.COLS)
        p1 = Player(1, 0, 0, PLAYER_COLORS[0])
        p2 = Player(2, self.ROWS-1, self.COLS-1, PLAYER_COLORS[1])
        self.sim   = Simulation(self.grid, [p1, p2])
        self.steps = 0
        self._balloons  = []
        self._bal_timer = 0

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

        # Grid
        for r in range(self.ROWS):
            for c in range(self.COLS):
                rect = pygame.Rect(c*CELL_K2, r*CELL_K2, CELL_K2, CELL_K2)
                col  = (40, 130, 40) if (r+c)%2==0 else (35, 120, 35)
                pygame.draw.rect(surface, col, rect)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

        # Players — big cartoon circles with face
        cell_map = defaultdict(list)
        for p in self.sim.players:
            cell_map[(p.row, p.col)].append(p)

        for (r, c), group in cell_map.items():
            cx_ = c*CELL_K2 + CELL_K2//2
            cy_ = r*CELL_K2 + CELL_K2//2
            for i, p in enumerate(group):
                ox = (i - len(group)//2) * 18
                self._draw_character(surface, cx_+ox, cy_, p.color)

        # Side panel
        px = gw + 10
        pygame.draw.rect(surface, C_PANEL, pygame.Rect(gw, 0, 200, H))
        pygame.draw.line(surface, C_BORDER, (gw,0), (gw,H), 2)
        draw_text(surface, self.app.fonts["lg"], "Steps", C_ACCENT, gw+100, 60)
        draw_text(surface, self.app.fonts["xl"], str(self.steps),
                  C_GREEN_LT, gw+100, 110)
        if self.sim.finished:
            draw_text(surface, self.app.fonts["md"], "They Met! 🎉",
                      (255, 230, 60), gw+100, 160)
        self.btn_restart.draw(surface)
        self.btn_menu.draw(surface)

        # Balloons
        if self.sim.finished:
            self._bal_timer += 1
            if self._bal_timer % 5 == 0:
                self._balloons.append(Balloon(gw, H))
            self._balloons = [b for b in self._balloons if b.y > -60]
            for b in self._balloons:
                b.update(); b.draw(surface)

    def _draw_character(self, surface, cx, cy, color):
        r = CELL_K2 // 3
        pygame.draw.circle(surface, color, (cx, cy), r)
        # highlight
        pygame.draw.circle(surface, (255,255,255),
                           (cx - r//3, cy - r//3), r//4)
        # eyes
        for ex in [-r//3, r//3]:
            pygame.draw.circle(surface, (255,255,255), (cx+ex, cy-r//5), r//6)
            pygame.draw.circle(surface, (30,30,30),    (cx+ex, cy-r//5), r//9)
        # smile
        sm_rect = pygame.Rect(cx-r//2, cy, r, r//2)
        pygame.draw.arc(surface, (255,255,255), sm_rect, math.pi, 2*math.pi, 2)


# ═══════════════════════════════════════════════════════════════════════════════
#  GRADES 3-5  SETUP + SIMULATION + RESULTS
# ═══════════════════════════════════════════════════════════════════════════════

CELL_ELEM = 72

class ElementarySetupScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        W, H = 760, 520
        app.screen = pygame.display.set_mode((W, H))
        f = app.fonts
        cx = W // 2
        self.sl_rows = Slider(cx-180, 160, 240, "Rows",    3, 12, 6,
                               f["sm"], f["md"])
        self.sl_cols = Slider(cx-180, 230, 240, "Columns", 3, 12, 6,
                               f["sm"], f["md"])
        self.sl_play = Slider(cx-180, 300, 240, "Players", 2,  4, 2,
                               f["sm"], f["md"])
        self.btn_start = Button((cx-120, 380, 240, 52),
                                "▶  Place Players", font=f["md"])
        self.btn_menu  = Button((20, H-60, 110, 40),
                                "🏠 Menu", font=f["sm"], tag="menu")

    def handle_events(self, events):
        for event in events:
            for sl in [self.sl_rows, self.sl_cols, self.sl_play]:
                sl.handle_event(event)
            if self.btn_start.clicked(event):
                r = self.sl_rows.value
                c = self.sl_cols.value
                n = self.sl_play.value
                self.app.goto("elem_place",
                              rows=r, cols=c, num_players=n)
            if self.btn_menu.clicked(event):
                self.app.goto("menu")

    def draw(self, surface):
        surface.fill(C_BG)
        W, H = surface.get_size()
        cx   = W // 2
        draw_text(surface, self.app.fonts["xl"],
                  "🌿 Grades 3 – 5  Setup", C_GREEN_LT, cx, 60)
        panel = pygame.Rect(cx-220, 130, 440, 230)
        pygame.draw.rect(surface, C_PANEL, panel, border_radius=14)
        pygame.draw.rect(surface, C_BORDER, panel, 2, border_radius=14)
        for sl in [self.sl_rows, self.sl_cols, self.sl_play]:
            sl.draw(surface)
        hint = self.app.fonts["sm"].render(
            f"Grid: {self.sl_rows.value} × {self.sl_cols.value}  •"
            f"  {self.sl_play.value} players", True, C_DIM)
        surface.blit(hint, hint.get_rect(center=(cx, 360)))
        self.btn_start.draw(surface)
        self.btn_menu.draw(surface)


class ElementaryPlaceScreen(Screen):
    def __init__(self, app, rows, cols, num_players):
        super().__init__(app)
        self.rows = rows
        self.cols = cols
        self.num_players = num_players
        self.positions = []
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
                    taken = any(pr==r and pc==c for pr,pc in self.positions)
                    if not taken and len(self.positions) < self.num_players:
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
                rect = pygame.Rect(c*CELL_ELEM, r*CELL_ELEM, CELL_ELEM, CELL_ELEM)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)
        for i, (r, c) in enumerate(self.positions):
            cx_ = c*CELL_ELEM + CELL_ELEM//2
            cy_ = r*CELL_ELEM + CELL_ELEM//2
            pygame.draw.circle(surface, PLAYER_COLORS[i], (cx_, cy_), CELL_ELEM//3)
            lbl = self.app.fonts["md"].render(
                PLAYER_NAMES[i][0], True, (255,255,255))
            surface.blit(lbl, lbl.get_rect(center=(cx_, cy_)))
        # hover
        mx, my = pygame.mouse.get_pos()
        hc, hr = mx//CELL_ELEM, my//CELL_ELEM
        placed = len(self.positions)
        if (0<=hr<self.rows and 0<=hc<self.cols and
                placed < self.num_players):
            s = pygame.Surface((CELL_ELEM, CELL_ELEM), pygame.SRCALPHA)
            s.fill((*PLAYER_COLORS[placed], 80))
            surface.blit(s, (hc*CELL_ELEM, hr*CELL_ELEM))
        # banner
        banner = pygame.Surface((W, 50), pygame.SRCALPHA)
        banner.fill((0,0,0,160))
        surface.blit(banner, (0, H-50))
        remaining = self.num_players - placed
        if remaining > 0:
            msg = f"Click to place {PLAYER_NAMES[placed]}  ({remaining} left)"
        else:
            msg = "Starting..."
        draw_text(surface, self.app.fonts["md"], msg, (230,230,230), W//2, H-25)


class ElementarySimScreen(Screen):
    CELL = CELL_ELEM
    UI_W = 260

    def __init__(self, app, rows, cols, num_players, positions):
        super().__init__(app)
        self.rows        = rows
        self.cols        = cols
        self.num_players = num_players
        self.positions   = positions
        self.stats       = StatsTracker()
        W = cols * self.CELL + self.UI_W
        H = max(rows * self.CELL, 480)
        app.screen = pygame.display.set_mode((W, H))
        self.grid_w = cols * self.CELL
        self.grid_h = rows * self.CELL
        f = app.fonts
        bx = self.grid_w + 12
        bw = self.UI_W - 24
        self.btn_replay = Button((bx, H-120, bw, 44),
                                 "▶ Replay", font=f["md"])
        self.btn_setup  = Button((bx, H-66,  bw, 44),
                                 "⚙ New Setup", font=f["md"],
                                 color=(80,40,120), hover_color=(130,80,180))
        self.btn_menu   = Button((bx, H-180, bw, 44),
                                 "🏠 Menu", font=f["sm"],
                                 color=(60,40,40), hover_color=(100,60,60))
        self._balloons   = []
        self._bal_timer  = 0
        self._music_on   = False
        self._build()

    def _build(self):
        stop_celebration()
        self._music_on = False
        self._balloons = []
        self._bal_timer= 0
        grid = Grid(self.rows, self.cols)
        players = [Player(i+1, r, c, PLAYER_COLORS[i])
                   for i, (r,c) in enumerate(self.positions)]
        self.sim   = Simulation(grid, players)
        self.steps = 0

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
            if self.stats.run_count() == 0 or \
                    self.stats.history()[-1] != self.steps:
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
                rect = pygame.Rect(c*self.CELL, r*self.CELL,
                                   self.CELL, self.CELL)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)
        # Players
        cell_map = defaultdict(list)
        for p in self.sim.players:
            cell_map[(p.row, p.col)].append(p)
        for (r, c), grp in cell_map.items():
            cx_ = c*self.CELL + self.CELL//2
            cy_ = r*self.CELL + self.CELL//2
            offs = self._offsets(len(grp))
            for i, p in enumerate(grp):
                ox, oy = offs[i]
                pygame.draw.circle(surface, p.color,
                                   (cx_+ox, cy_+oy), self.CELL//3)
                lbl = self.app.fonts["sm"].render(
                    PLAYER_NAMES[p.id-1][0], True, (255,255,255))
                surface.blit(lbl, lbl.get_rect(center=(cx_+ox, cy_+oy)))
        # Panel
        px = self.grid_w
        pygame.draw.rect(surface, C_PANEL,
                         pygame.Rect(px, 0, self.UI_W, H))
        pygame.draw.line(surface, C_BORDER, (px,0), (px,H), 2)
        bx = px + 12
        y  = 16
        f  = self.app.fonts
        draw_text(surface, f["lg"], "📊 Stats", C_GREEN_LT, px+self.UI_W//2, y+12)
        y += 42
        draw_text(surface, f["md"],
                  f"Step: {self.steps}", C_TEXT, px+self.UI_W//2, y); y += 30
        n = self.stats.run_count()
        draw_text(surface, f["md"],
                  f"Runs: {n}", C_TEXT, px+self.UI_W//2, y); y += 36
        if n > 0:
            pygame.draw.line(surface, C_BORDER, (bx,y), (bx+self.UI_W-30,y),1)
            y += 12
            for label, val, col in [
                ("Min", str(self.stats.shortest()), (100,220,120)),
                ("Max", str(self.stats.longest()),  (220,100,100)),
                ("Avg", f"{self.stats.average():.1f}", (180,180,255))]:
                hl = f["sm"].render(label, True, C_DIM)
                vl = f["md"].render(val,   True, col)
                surface.blit(hl, (bx, y))
                surface.blit(vl, (bx+50, y))
                y += 26
            y += 10
            # grouping bars
            for lbl2, pct in self.stats.grouping_summary():
                pygame.draw.rect(surface, (50,80,50),
                                 pygame.Rect(bx, y+8, self.UI_W-34, 10))
                bw2 = int((self.UI_W-34)*pct)
                pygame.draw.rect(surface, C_GREEN_LT,
                                 pygame.Rect(bx, y+8, bw2, 10))
                tl = f["sm"].render(f"{lbl2}  {pct*100:.0f}%",True,C_TEXT)
                surface.blit(tl, (bx, y)); y += 26
            # sparkline
            hist = self.stats.history()
            if len(hist) > 1:
                pygame.draw.line(surface, C_BORDER, (bx,y),
                                 (bx+self.UI_W-30,y), 1); y += 10
                draw_line_graph(surface, f["sm"], bx, y,
                                self.UI_W-30, 55, [("runs", C_GREEN_LT, hist)])
                y += 60
        self.btn_replay.draw(surface)
        self.btn_setup.draw(surface)
        self.btn_menu.draw(surface)
        # Finished overlay
        if self.sim.finished:
            s = pygame.Surface((self.grid_w, 60), pygame.SRCALPHA)
            s.fill((0,0,0,160))
            surface.blit(s, (0, self.grid_h//2-30))
            draw_text(surface, f["xl"], "🎉 They Met!",
                      (255,230,60), self.grid_w//2, self.grid_h//2)
            self._bal_timer += 1
            if self._bal_timer % 6 == 0:
                self._balloons.append(Balloon(self.grid_w, self.grid_h))
            self._balloons = [b for b in self._balloons if b.y > -60]
            for b in self._balloons:
                b.update(); b.draw(surface)

    def _offsets(self, n):
        r = self.CELL // 5
        if n == 1: return [(0,0)]
        if n == 2: return [(-r,0),(r,0)]
        if n == 3: return [(0,-r),(-r,r),(r,r)]
        return [(-r,-r),(r,-r),(-r,r),(r,r)]


# ═══════════════════════════════════════════════════════════════════════════════
#  GRADES 6-8  EXPERIMENT SCREEN
# ═══════════════════════════════════════════════════════════════════════════════

CELL_MID = 40
MS_GRID_W = 420
MS_PANEL_W = 420

class MiddleSchoolExperimentScreen(Screen):
    """
    Full experiment screen:
    - Protocol selector (5 protocols)
    - Grid shape/size controls
    - Trials slider
    - Run Experiment button (runs silently, fast)
    - Live updating bar chart (avg steps) + line graph (run history per protocol)
    - Results table
    - Student judgment: "Which is best?" with reasoning input
    """

    def __init__(self, app):
        super().__init__(app)
        W = MS_GRID_W + MS_PANEL_W + 20
        H = 700
        app.screen = pygame.display.set_mode((W, H))
        f = app.fonts

        self.mp_stats = MultiProtocolStats()

        # Controls
        self.sl_rows   = Slider(MS_GRID_W+20, 60,  160, "Rows",    3, 15, 6, f["sm"], f["md"])
        self.sl_cols   = Slider(MS_GRID_W+20, 120, 160, "Cols",    3, 15, 6, f["sm"], f["md"])
        self.sl_trials = Slider(MS_GRID_W+20, 180, 160, "Trials",  5, 200, 30, f["sm"], f["md"])
        self.sl_players= Slider(MS_GRID_W+20, 240, 160, "Players", 2, 4,  2,  f["sm"], f["md"])

        # Protocol checkboxes (multi-select)
        self._proto_selected = {p.name: True for p in
                                [PureRandom(), BiasedWalk(), ZigZag(),
                                 EdgeFollower(), CenterSeeker()]}
        self._proto_objs = {p.name: p for p in
                            [PureRandom(), BiasedWalk(), ZigZag(),
                             EdgeFollower(), CenterSeeker()]}
        proto_names = list(self._proto_selected.keys())
        self._proto_rects = {}
        py = 310
        for name in proto_names:
            self._proto_rects[name] = pygame.Rect(MS_GRID_W+14, py, 16, 16)
            py += 28

        self.btn_run   = Button((MS_GRID_W+14, py+10, 160, 46),
                                "▶ Run Experiment", font=f["md"],
                                color=(40,100,40), hover_color=(60,160,60))
        self.btn_clear = Button((MS_GRID_W+14, py+66, 160, 36),
                                "🗑 Clear Results", font=f["sm"],
                                color=(80,30,30), hover_color=(140,50,50))
        self.btn_menu  = Button((MS_GRID_W+14, H-54, 160, 40),
                                "🏠 Menu", font=f["sm"],
                                color=(40,40,60), hover_color=(70,70,100))

        # Live sim for visualization
        self._live_grid = None
        self._live_sim  = None
        self._live_steps= 0
        self._running_experiment = False
        self._exp_queue  = []   # list of (protocol_name, Protocol instance) to run
        self._exp_trial  = 0
        self._exp_total  = 0

        # Graph view toggle
        self._graph_mode = "bar"   # "bar" | "line" | "table"
        gx = MS_GRID_W + 14
        gw = MS_PANEL_W - 28
        gy = H - 220
        self._tab_rects = {
            "bar":   pygame.Rect(gx,       gy-30, 65, 26),
            "line":  pygame.Rect(gx+70,    gy-30, 65, 26),
            "table": pygame.Rect(gx+140,   gy-30, 65, 26),
        }
        self._graph_rect = pygame.Rect(gx, gy, gw, 200)

        # Student judgment
        self._judgment_text = ""
        self._judgment_active = False

        self._init_live_sim()

    def _init_live_sim(self):
        rows = self.sl_rows.value
        cols = self.sl_cols.value
        n    = self.sl_players.value
        self._live_grid = Grid(rows, cols)
        players = self._random_players(rows, cols, n)
        self._live_sim   = Simulation(self._live_grid, players)
        self._live_steps = 0

    def _random_players(self, rows, cols, n):
        positions = random.sample(
            [(r, c) for r in range(rows) for c in range(cols)], k=n)
        return [Player(i+1, r, c, PLAYER_COLORS[i])
                for i, (r, c) in enumerate(positions)]

    def handle_events(self, events):
        for event in events:
            for sl in [self.sl_rows, self.sl_cols,
                       self.sl_trials, self.sl_players]:
                sl.handle_event(event)

            # Protocol checkboxes
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for name, rect in self._proto_rects.items():
                    if rect.collidepoint(event.pos):
                        self._proto_selected[name] = \
                            not self._proto_selected[name]

            if self.btn_run.clicked(event):
                self._start_experiment()
            if self.btn_clear.clicked(event):
                self.mp_stats = MultiProtocolStats()
                self._running_experiment = False
                self._exp_queue = []
            if self.btn_menu.clicked(event):
                stop_celebration()
                self.app.goto("menu")

            # Graph tabs
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for mode, rect in self._tab_rects.items():
                    if rect.collidepoint(event.pos):
                        self._graph_mode = mode

            # Judgment text box
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                W, H = self.app.screen.get_size()
                jbox = pygame.Rect(MS_GRID_W+14, H-46, MS_PANEL_W-28, 34)
                self._judgment_active = jbox.collidepoint(event.pos)
            if event.type == pygame.KEYDOWN and self._judgment_active:
                if event.key == pygame.K_BACKSPACE:
                    self._judgment_text = self._judgment_text[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self._judgment_active = False
                elif len(self._judgment_text) < 80:
                    self._judgment_text += event.unicode

    def _start_experiment(self):
        selected = [name for name, on in self._proto_selected.items() if on]
        if not selected:
            return
        trials = self.sl_trials.value
        self._exp_queue = [(name, self._proto_objs[name])
                           for name in selected] * trials
        random.shuffle(self._exp_queue)
        self._exp_trial   = 0
        self._exp_total   = len(self._exp_queue)
        self._running_experiment = True
        self._init_live_sim()

    def update(self):
        if self._running_experiment and self._exp_queue:
            # Run a batch of trials silently per frame (fast)
            batch = max(1, self._exp_total // 60)
            for _ in range(min(batch, len(self._exp_queue))):
                name, proto = self._exp_queue.pop(0)
                steps = self._run_silent_trial(proto)
                self.mp_stats.record(name, steps)
                self._exp_trial += 1
            if not self._exp_queue:
                self._running_experiment = False
        else:
            # Animate the live preview sim
            if self._live_sim and not self._live_sim.finished:
                self._live_sim.step()
                self._live_steps += 1
            elif self._live_sim and self._live_sim.finished:
                self._init_live_sim()

    def _run_silent_trial(self, proto):
        rows = self.sl_rows.value
        cols = self.sl_cols.value
        n    = self.sl_players.value
        grid = Grid(rows, cols)
        players = self._random_players(rows, cols, n)
        sim  = Simulation(grid, players, type(proto))
        while not sim.finished and sim.steps < 10000:
            sim.step()
        return sim.steps

    def draw(self, surface):
        W, H = surface.get_size()
        surface.fill(C_BG)
        f = self.app.fonts

        # ── Live grid preview ──────────────────────────────────────────────
        rows = self.sl_rows.value
        cols = self.sl_cols.value
        cs   = min(CELL_MID, MS_GRID_W // max(cols, 1),
                   (H - 80) // max(rows, 1))
        gw_px= cols * cs
        gh_px= rows * cs
        gox  = (MS_GRID_W - gw_px) // 2
        goy  = (H - gh_px) // 2

        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(gox+c*cs, goy+r*cs, cs, cs)
                col  = (30,90,30) if (r+c)%2==0 else (25,80,25)
                pygame.draw.rect(surface, col, rect)
                pygame.draw.rect(surface, C_GRID_LINE, rect, 1)

        if self._live_sim:
            cell_map = defaultdict(list)
            for p in self._live_sim.players:
                cell_map[(p.row, p.col)].append(p)
            for (r, c), grp in cell_map.items():
                cx_ = gox + c*cs + cs//2
                cy_ = goy + r*cs + cs//2
                for i, p in enumerate(grp):
                    ox = (i - len(grp)//2) * (cs//4)
                    rad = max(4, cs//3)
                    pygame.draw.circle(surface, p.color, (cx_+ox, cy_), rad)

        # Step counter under grid
        draw_text(surface, f["sm"], f"Live preview – step {self._live_steps}",
                  C_DIM, MS_GRID_W//2, H-30)

        # ── Right panel ────────────────────────────────────────────────────
        px = MS_GRID_W + 10
        pygame.draw.rect(surface, C_PANEL,
                         pygame.Rect(px, 0, MS_PANEL_W, H))
        pygame.draw.line(surface, C_BORDER, (px,0), (px,H), 2)

        draw_text(surface, f["lg"], "🌲 Grades 6–8 Lab",
                  C_GREEN_LT, px + MS_PANEL_W//2, 24)

        for sl in [self.sl_rows, self.sl_cols,
                   self.sl_trials, self.sl_players]:
            sl.draw(surface)

        # Protocol checkboxes
        bx = MS_GRID_W + 14
        y  = 295
        lbl_hdr = f["sm"].render("Movement Protocols:", True, C_DIM)
        surface.blit(lbl_hdr, (bx, y)); y += 22
        for name, rect in self._proto_rects.items():
            selected = self._proto_selected[name]
            pygame.draw.rect(surface, (255,255,255) if selected else (60,80,60),
                             rect, border_radius=3)
            if selected:
                pygame.draw.line(surface, (30,30,30),
                                 (rect.x+3, rect.centery),
                                 (rect.x+6, rect.bottom-3), 2)
                pygame.draw.line(surface, (30,30,30),
                                 (rect.x+6, rect.bottom-3),
                                 (rect.right-3, rect.y+3), 2)
            short = name[:22]
            nl = f["sm"].render(short, True, C_TEXT)
            surface.blit(nl, (rect.right+6, rect.y-1))

        self.btn_run.draw(surface)
        self.btn_clear.draw(surface)

        # Progress bar
        if self._running_experiment and self._exp_total > 0:
            progress_rect = pygame.Rect(bx, self.btn_run.rect.bottom+4,
                                        160, 10)
            pygame.draw.rect(surface, (40,60,40), progress_rect, border_radius=5)
            done = 1 - len(self._exp_queue)/self._exp_total
            pygame.draw.rect(surface, C_GREEN_LT,
                             pygame.Rect(bx, self.btn_run.rect.bottom+4,
                                         int(160*done), 10),
                             border_radius=5)
            pct_lbl = f["sm"].render(f"{int(done*100)}%", True, C_ACCENT)
            surface.blit(pct_lbl, (bx+168, self.btn_run.rect.bottom+1))

        # ── Graph area ─────────────────────────────────────────────────────
        summary = self.mp_stats.summary()

        # Tabs
        for mode, rect in self._tab_rects.items():
            active = (self._graph_mode == mode)
            col    = C_ACCENT if active else C_BORDER
            pygame.draw.rect(surface, C_PANEL if not active else (40,55,40),
                             rect, border_radius=5)
            pygame.draw.rect(surface, col, rect, 1, border_radius=5)
            draw_text(surface, f["sm"],
                      {"bar":"Bar","line":"Line","table":"Table"}[mode],
                      C_TEXT, rect.centerx, rect.centery)

        gr = self._graph_rect
        pygame.draw.rect(surface, (20,35,20), gr, border_radius=6)
        pygame.draw.rect(surface, C_BORDER, gr, 1, border_radius=6)

        if not summary:
            draw_text(surface, f["sm"], "No data yet — run an experiment!",
                      C_DIM, gr.centerx, gr.centery)
        elif self._graph_mode == "bar":
            data   = [(s["name"][:12], s["avg"]) for s in summary]
            colors = [PLAYER_COLORS[i % len(PLAYER_COLORS)]
                      for i in range(len(data))]
            draw_bar_graph(surface, f["sm"], gr.x+4, gr.y+4,
                           gr.w-8, gr.h-8, data, colors)
            draw_text(surface, f["sm"], "Average steps per protocol",
                      C_DIM, gr.centerx, gr.y-10)

        elif self._graph_mode == "line":
            cols_c = [PLAYER_COLORS[i % len(PLAYER_COLORS)]
                      for i in range(len(summary))]
            series = [(s["name"][:10], cols_c[i], s["runs"])
                      for i, s in enumerate(summary)]
            draw_line_graph(surface, f["sm"],
                            gr.x+30, gr.y+4, gr.w-34, gr.h-8, series)
            # legend
            lx = gr.x + 4
            for i, s in enumerate(summary):
                pygame.draw.line(surface, cols_c[i],
                                 (lx, gr.bottom+12), (lx+18, gr.bottom+12), 2)
                ll = f["sm"].render(s["name"][:10], True, cols_c[i])
                surface.blit(ll, (lx+22, gr.bottom+4))
                lx += ll.get_width() + 40

        elif self._graph_mode == "table":
            self._draw_table(surface, f, gr, summary)

        # ── Student judgment ───────────────────────────────────────────────
        jy = H - 90
        draw_text(surface, f["sm"], "Which protocol is best? Why?",
                  C_DIM, px + MS_PANEL_W//2, jy)
        jbox = pygame.Rect(bx, jy+14, MS_PANEL_W-28, 34)
        border_col = C_ACCENT if self._judgment_active else C_BORDER
        pygame.draw.rect(surface, (20,30,20), jbox, border_radius=5)
        pygame.draw.rect(surface, border_col, jbox, 1, border_radius=5)
        jtext = self._judgment_text + ("|" if self._judgment_active else "")
        jlbl  = f["sm"].render(jtext, True, C_TEXT)
        surface.blit(jlbl, (jbox.x+6, jbox.y+8))

        self.btn_menu.draw(surface)

    def _draw_table(self, surface, f, rect, summary):
        if not summary:
            return
        cols_def = ["Protocol", "Runs", "Min", "Max", "Avg"]
        cw       = [rect.w*c//100 for c in [42,12,12,12,16]]
        x0       = rect.x + 4
        y        = rect.y + 6
        # header
        x = x0
        for label, w in zip(cols_def, cw):
            h_lbl = f["sm"].render(label, True, C_ACCENT)
            surface.blit(h_lbl, (x, y))
            x += w
        y += 20
        pygame.draw.line(surface, C_BORDER,
                         (rect.x, y), (rect.right, y), 1)
        y += 4
        for i, s in enumerate(summary):
            if y > rect.bottom - 18:
                break
            row_col = PLAYER_COLORS[i % len(PLAYER_COLORS)]
            x = x0
            vals = [s["name"][:18], str(s["n"]),
                    str(s["min"]), str(s["max"]), f"{s['avg']:.1f}"]
            for val, w in zip(vals, cw):
                lbl = f["sm"].render(val, True, row_col)
                surface.blit(lbl, (x, y))
                x += w
            y += 22


# ═══════════════════════════════════════════════════════════════════════════════
#  APP  (router + window manager)
# ═══════════════════════════════════════════════════════════════════════════════

class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Wandering in the Woods")
        self.clock  = pygame.time.Clock()
        self.fonts  = {
            "sm": pygame.font.SysFont("Arial", 13),
            "md": pygame.font.SysFont("Arial", 17, bold=True),
            "lg": pygame.font.SysFont("Arial", 24, bold=True),
            "xl": pygame.font.SysFont("Arial", 34, bold=True),
        }
        init_music()
        self.current_screen = MainMenuScreen(self)

    def goto(self, name, **kwargs):
        stop_celebration()
        if name == "menu":
            self.screen = pygame.display.set_mode((800, 600))
            self.current_screen = MainMenuScreen(self)
        elif name == "instructions":
            self.screen = pygame.display.set_mode((700, 520))
            self.current_screen = InstructionsScreen(self)
        elif name == "k2":
            self.current_screen = K2GameScreen(self)
        elif name == "elem_setup" or name == "elem":
            self.current_screen = ElementarySetupScreen(self)
        elif name == "elem_place":
            self.current_screen = ElementaryPlaceScreen(
                self, kwargs["rows"], kwargs["cols"], kwargs["num_players"])
        elif name == "elem_sim":
            self.current_screen = ElementarySimScreen(
                self, kwargs["rows"], kwargs["cols"],
                kwargs["num_players"], kwargs["positions"])
        elif name == "middle":
            self.current_screen = MiddleSchoolExperimentScreen(self)

    def run(self):
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

            self.current_screen.handle_events(events)
            self.current_screen.update()
            self.current_screen.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    App().run()
