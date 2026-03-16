"""
ui/drawing.py
=============
Stateless drawing helpers shared across all screens.

    draw_text(surface, font, text, color, cx, cy)
    draw_bar_graph(surface, font_sm, x, y, w, h, data, colors)
    draw_line_graph(surface, font_sm, x, y, w, h, series)
"""

import pygame
from constants import C_TEXT, C_ACCENT, C_GREEN_LT, C_BORDER, C_DIM
from typing import Optional


def draw_text(surface: pygame.Surface, font, text: str,
              color, cx: int, cy: int) -> None:
    """Blit centre-aligned text at (cx, cy)."""
    rendered = font.render(text, True, color)
    surface.blit(rendered, rendered.get_rect(center=(cx, cy)))


def draw_bar_graph(surface: pygame.Surface, font_sm,
                   x: int, y: int, w: int, h: int,
                   data: list[tuple[str, float]],
                   colors: Optional[list] = None) -> None:
    """
    Horizontal bar chart.

    Parameters
    ----------
    data   : list of (label_str, numeric_value)
    colors : optional list of RGB tuples — cycles if shorter than data
    """
    if not data:
        return

    max_val = max(v for _, v in data) or 1
    bar_h   = min(36, (h - 20) // max(1, len(data)) - 6)
    oy      = y + 10

    for i, (label, value) in enumerate(data):
        bw    = int((w - 120) * value / max_val)
        col   = colors[i % len(colors)] if colors else C_GREEN_LT
        bg    = pygame.Rect(x + 90, oy, w - 120, bar_h)
        bar   = pygame.Rect(x + 90, oy, bw, bar_h)
        pygame.draw.rect(surface, (40, 60, 40), bg,  border_radius=4)
        pygame.draw.rect(surface, col,           bar, border_radius=4)

        lbl = font_sm.render(label, True, C_TEXT)
        surface.blit(lbl, (x + 2, oy + bar_h // 2 - lbl.get_height() // 2))

        val = font_sm.render(f"{value:.1f}", True, C_ACCENT)
        surface.blit(val, (x + 94 + bw, oy + bar_h // 2 - val.get_height() // 2))

        oy += bar_h + 8


def draw_line_graph(surface: pygame.Surface, font_sm,
                    x: int, y: int, w: int, h: int,
                    series: list[tuple[str, tuple, list[float]]]) -> None:
    """
    Overlaid line graph.

    Parameters
    ----------
    series : list of (label, rgb_color, [float values])
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

    # Background + axes
    pygame.draw.rect(surface, (40, 60, 40), pygame.Rect(x, y, w, h))
    pygame.draw.line(surface, C_BORDER, (x, y),     (x, y + h), 1)
    pygame.draw.line(surface, C_BORDER, (x, y + h), (x + w, y + h), 1)

    # Series lines
    for _, color, vals in series:
        if len(vals) < 2:
            continue
        pts = [
            (x + int(i / (len(vals) - 1) * w),
             y + h - int((v - lo) / (hi - lo) * h))
            for i, v in enumerate(vals)
        ]
        pygame.draw.lines(surface, color, False, pts, 2)
        pygame.draw.circle(surface, color, pts[-1], 4)

    # Y-axis tick labels
    for tick in [lo, (lo + hi) // 2, hi]:
        ty  = y + h - int((tick - lo) / (hi - lo) * h)
        lbl = font_sm.render(str(int(tick)), True, C_DIM)
        surface.blit(lbl, (x - lbl.get_width() - 4,
                           ty - lbl.get_height() // 2))
