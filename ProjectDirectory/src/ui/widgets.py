"""
ui/widgets.py
=============
Reusable pygame UI widgets:
    Button   — clickable labelled rectangle
    Slider   — integer drag slider
    Balloon  — floating celebration balloon particle
"""

import math
import random
import pygame

from constants import (
    C_GREEN_MID, C_GREEN_LT, C_ACCENT, C_DIM, C_TEXT,
    PLAYER_COLORS,
)


# ── Button ────────────────────────────────────────────────────────────────────

class Button:
    """Clickable labelled rectangle with hover highlight."""

    def __init__(self, rect, label: str, color=None, hover_color=None,
                 text_color=(240, 240, 240), font=None, tag=None, radius=8):
        self.rect        = pygame.Rect(rect)
        self.label       = label
        self.color       = color       or C_GREEN_MID
        self.hover_color = hover_color or C_GREEN_LT
        self.text_color  = text_color
        self.font        = font
        self.tag         = tag or label
        self.radius      = radius

    def draw(self, surface: pygame.Surface) -> None:
        mx, my = pygame.mouse.get_pos()
        col    = self.hover_color if self.rect.collidepoint(mx, my) else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=self.radius)
        if self.font:
            lbl = self.font.render(self.label, True, self.text_color)
            surface.blit(lbl, lbl.get_rect(center=self.rect.center))

    def clicked(self, event) -> bool:
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ── Slider ────────────────────────────────────────────────────────────────────

class Slider:
    """Draggable integer slider with label and live value display."""

    def __init__(self, x: int, y: int, w: int, label: str,
                 lo: int, hi: int, value: int,
                 font_sm, font_md):
        self.rect    = pygame.Rect(x, y, w, 28)
        self.label   = label
        self.lo      = lo
        self.hi      = hi
        self.value   = value
        self.drag    = False
        self.font_sm = font_sm
        self.font_md = font_md

    def handle_event(self, event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.drag = True
                self._set_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.drag = False
        elif event.type == pygame.MOUSEMOTION and self.drag:
            self._set_from_x(event.pos[0])

    def _set_from_x(self, mx: int) -> None:
        frac       = max(0.0, min(1.0, (mx - self.rect.x) / self.rect.w))
        self.value = round(self.lo + frac * (self.hi - self.lo))

    def draw(self, surface: pygame.Surface) -> None:
        frac = (self.value - self.lo) / max(1, self.hi - self.lo)

        # Track background
        track = pygame.Rect(self.rect.x, self.rect.centery - 3, self.rect.w, 6)
        pygame.draw.rect(surface, (50, 70, 50), track, border_radius=3)

        # Filled portion
        fill = pygame.Rect(self.rect.x, self.rect.centery - 3,
                           int(self.rect.w * frac), 6)
        pygame.draw.rect(surface, C_GREEN_LT, fill, border_radius=3)

        # Thumb
        tx = self.rect.x + int(self.rect.w * frac)
        pygame.draw.circle(surface, C_ACCENT, (tx, self.rect.centery), 10)
        pygame.draw.circle(surface, (255, 255, 255), (tx, self.rect.centery), 4)

        # Text
        lbl = self.font_sm.render(self.label, True, C_DIM)
        val = self.font_md.render(str(self.value), True, C_ACCENT)
        surface.blit(lbl, (self.rect.x, self.rect.y - 20))
        surface.blit(val, (self.rect.right + 12,
                           self.rect.centery - val.get_height() // 2))


# ── Balloon ───────────────────────────────────────────────────────────────────

class Balloon:
    """Floating celebration balloon particle."""

    def __init__(self, screen_w: int, screen_h: int):
        self.x     = random.randint(20, screen_w - 20)
        self.y     = screen_h + random.randint(0, 120)
        self.speed = random.uniform(1.5, 3.5)
        self.wo    = random.uniform(0, 2 * math.pi)   # wobble offset
        self.ws    = random.uniform(0.05, 0.1)         # wobble speed
        self.color = random.choice(PLAYER_COLORS + [(200, 80, 255)])
        self.r     = random.randint(14, 22)
        self.tick  = 0.0

    def update(self) -> None:
        self.y    -= self.speed
        self.tick += self.ws
        self.x    += math.sin(self.tick + self.wo) * 1.5

    def draw(self, surface: pygame.Surface) -> None:
        ix, iy = int(self.x), int(self.y)
        pygame.draw.circle(surface, self.color, (ix, iy), self.r)
        pygame.draw.circle(surface, (255, 255, 255),
                           (ix - self.r // 3, iy - self.r // 3), self.r // 4)
        pygame.draw.line(surface, (180, 180, 180),
                         (ix, iy + self.r), (ix + 5, iy + self.r + 18), 1)
