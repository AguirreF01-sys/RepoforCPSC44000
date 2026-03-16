"""
screens/menu.py
===============
MainMenuScreen  — animated starfield + grade-level navigation buttons
InstructionsScreen — 4-page illustrated guide with prev/next navigation
"""

import math
import random
import sys
import pygame

from screens.base import Screen
from ui.widgets import Button
from ui.drawing import draw_text
from constants import (
    C_BG, C_BORDER, C_ACCENT, C_GREEN_LT, C_GREEN_MID,
    C_DIM, C_TEXT,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

class MainMenuScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        app.screen = pygame.display.set_mode((800, 600))
        W, H = app.screen.get_size()
        cx   = W // 2
        f    = app.fonts

        bw, bh, gap = 260, 52, 14
        sy = H // 2 - 80

        menu_items = [
            ("🌱  K – 2",         "k2",           C_GREEN_MID,    C_GREEN_LT),
            ("🌿  Grades 3 – 5",  "elem",          (40,100, 60),   (70,160, 80)),
            ("🌲  Grades 6 – 8",  "middle",        (30, 80,100),   (60,130,160)),
            ("📖  Instructions",  "instructions",  (80, 60,100),   (130,100,160)),
            ("✕   Quit",          "quit",          (100, 40, 40),  (160, 70, 70)),
        ]

        self.buttons = [
            Button(pygame.Rect(cx - bw // 2, sy + i * (bh + gap), bw, bh),
                   label, col, hcol, font=f["lg"], tag=tag)
            for i, (label, tag, col, hcol) in enumerate(menu_items)
        ]

        self._stars = [
            (random.randint(0, W), random.randint(0, H), random.uniform(0.3, 1.5))
            for _ in range(60)
        ]

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
        t    = pygame.time.get_ticks() / 1000

        # Animated twinkle stars
        for sx, sy, sp in self._stars:
            a = int(120 + 80 * math.sin(t * sp + sx))
            r = max(1, int(sp * 1.5))
            pygame.draw.circle(surface, (a, min(255, int(a * 1.1)), a), (sx, sy), r)

        draw_text(surface, self.app.fonts["xl"],
                  "🌲 Wandering in the Woods", C_GREEN_LT, W // 2, 90)
        draw_text(surface, self.app.fonts["sm"],
                  "Choose your grade level", C_DIM, W // 2, 130)

        for btn in self.buttons:
            btn.draw(surface)


# ═══════════════════════════════════════════════════════════════════════════════
#  INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class InstructionsScreen(Screen):
    PAGES = [
        ("How the Game Works", [
            "Two or more players are placed on a grid of cells.",
            "Each step, every player moves to a random neighbouring cell.",
            "The game ends when two (or more) players land on the same cell.",
            "We call that moment: they've MET in the woods!",
            "",
            "Try different grid sizes and starting positions.",
            "Does size change how long it takes to meet?",
        ]),
        ("For K–2 Students", [
            "Big colourful grid, two cartoon characters.",
            "Watch them wander until they meet.",
            "Count the steps together as a class.",
            "Press Restart to try again!",
        ]),
        ("For Grades 3–5", [
            "You choose the grid size and number of players.",
            "Click to place each player's starting position.",
            "Run it many times and see the statistics:",
            "  • Shortest run   • Longest run   • Average",
            "Does starting closer together help?",
            "What happens with more players?",
        ]),
        ("For Grades 6–8", [
            "Run hundreds of trials automatically.",
            "Compare five different movement protocols:",
            "  Pure Random, Biased, Zig-Zag, Edge-Follower, Center-Seeker.",
            "Graphs update live as experiments run.",
            "A results table lets you rank which protocol is fastest.",
            "Think like a scientist — form a hypothesis first!",
        ]),
    ]

    def __init__(self, app):
        super().__init__(app)
        app.screen = pygame.display.set_mode((700, 520))
        self.page = 0
        W, H = app.screen.get_size()
        f    = app.fonts
        self.btn_back = Button((40,      H-70, 120, 44), "◀ Back", font=f["md"])
        self.btn_prev = Button((W//2-150, H-70, 120, 44), "◀ Prev", font=f["md"])
        self.btn_next = Button((W//2+30,  H-70, 120, 44), "Next ▶", font=f["md"])

    def handle_events(self, events):
        for event in events:
            if self.btn_back.clicked(event):
                self.app.goto("menu")
            if self.btn_prev.clicked(event):
                self.page = max(0, self.page - 1)
            if self.btn_next.clicked(event):
                self.page = min(len(self.PAGES) - 1, self.page + 1)

    def draw(self, surface):
        surface.fill(C_BG)
        W, H = surface.get_size()
        title, lines = self.PAGES[self.page]

        draw_text(surface, self.app.fonts["lg"], title, C_ACCENT, W // 2, 80)

        y = 140
        for line in lines:
            lbl = self.app.fonts["md"].render(line, True, C_TEXT)
            surface.blit(lbl, (W // 2 - lbl.get_width() // 2, y))
            y += 32

        # Page dot indicators
        dot_y = H - 110
        for i in range(len(self.PAGES)):
            col = C_ACCENT if i == self.page else C_BORDER
            pygame.draw.circle(surface, col, (W // 2 + (i - 1) * 24, dot_y), 6)

        self.btn_back.draw(surface)
        self.btn_prev.draw(surface)
        self.btn_next.draw(surface)
