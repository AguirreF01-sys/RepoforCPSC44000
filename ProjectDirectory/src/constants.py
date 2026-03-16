"""
constants.py
============
All shared constants: FPS, colours, player palette, cell sizes.
Import everything from here so nothing is hardcoded in multiple places.
"""

# ── Timing ────────────────────────────────────────────────────────────────────
FPS = 30

# ── Players ───────────────────────────────────────────────────────────────────
PLAYER_COLORS = [
    (220,  50,  50),   # Red
    ( 50,  80, 220),   # Blue
    ( 40, 180,  80),   # Green
    (220, 160,  30),   # Yellow
]
PLAYER_NAMES = ["Red", "Blue", "Green", "Yellow"]

# ── Dark forest colour palette ────────────────────────────────────────────────
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

# ── Cell sizes per grade mode ─────────────────────────────────────────────────
CELL_K2   = 90    # K-2: large cells
CELL_ELEM = 72    # 3-5: medium cells
CELL_MID  = 40    # 6-8: small cells (fits larger grids)

# ── 6-8 lab layout ────────────────────────────────────────────────────────────
MS_GRID_W  = 420  # pixel width reserved for the live-preview grid
MS_PANEL_W = 420  # pixel width of the controls/graph panel
