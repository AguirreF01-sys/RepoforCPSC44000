"""
app.py
======
App — the top-level controller.

Responsibilities
----------------
- Initialise pygame and shared fonts
- Own the display surface and clock
- Route between screens via goto(name, **kwargs)
- Run the main event/update/draw loop
"""

import sys
import pygame

from constants import FPS
from music     import init_music, stop_celebration

from screens.menu import MainMenuScreen
from screens.menu import InstructionsScreen
from screens.k2 import K2GameScreen
from screens.elementary import (
    ElementarySetupScreen,
    ElementaryPlaceScreen,
    ElementarySimScreen,
)
from screens.middle import MiddleSchoolExperimentScreen


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Wandering in the Woods")

        self.screen = pygame.display.set_mode((800, 600))
        self.clock  = pygame.time.Clock()

        self.fonts = {
            "sm": pygame.font.SysFont("Arial", 13),
            "md": pygame.font.SysFont("Arial", 17, bold=True),
            "lg": pygame.font.SysFont("Arial", 24, bold=True),
            "xl": pygame.font.SysFont("Arial", 34, bold=True),
        }

        init_music()
        self.current_screen = MainMenuScreen(self)

    # ── Screen router ─────────────────────────────────────────────────────────

    def goto(self, name: str, **kwargs) -> None:
        """
        Navigate to a named screen.

        Supported names
        ---------------
        "menu"          — MainMenuScreen
        "instructions"  — InstructionsScreen
        "k2"            — K2GameScreen
        "elem" /
        "elem_setup"    — ElementarySetupScreen
        "elem_place"    — ElementaryPlaceScreen   (requires rows, cols, num_players)
        "elem_sim"      — ElementarySimScreen     (requires rows, cols, num_players, positions)
        "middle"        — MiddleSchoolExperimentScreen
        """
        stop_celebration()

        if name == "menu":
            self.current_screen = MainMenuScreen(self)

        elif name == "instructions":
            self.current_screen = InstructionsScreen(self)

        elif name == "k2":
            self.current_screen = K2GameScreen(self)

        elif name in ("elem", "elem_setup"):
            self.current_screen = ElementarySetupScreen(self)

        elif name == "elem_place":
            self.current_screen = ElementaryPlaceScreen(
                self,
                rows=kwargs["rows"],
                cols=kwargs["cols"],
                num_players=kwargs["num_players"],
            )

        elif name == "elem_sim":
            self.current_screen = ElementarySimScreen(
                self,
                rows=kwargs["rows"],
                cols=kwargs["cols"],
                num_players=kwargs["num_players"],
                positions=kwargs["positions"],
            )

        elif name == "middle":
            self.current_screen = MiddleSchoolExperimentScreen(self)

        else:
            raise ValueError(f"Unknown screen name: {name!r}")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> None:
        while True:
            events = pygame.event.get()

            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            self.current_screen.handle_events(events)
            self.current_screen.update()
            self.current_screen.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
