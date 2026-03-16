"""
screens/base.py
===============
Base Screen class — every screen inherits from this.
The App calls handle_events → update → draw each frame.
"""


class Screen:
    def __init__(self, app):
        self.app = app   # back-reference so screens can call app.goto()

    def handle_events(self, events: list) -> None:
        """Process a list of pygame events."""

    def update(self) -> None:
        """Advance game state by one frame."""

    def draw(self, surface) -> None:
        """Render the screen onto surface."""
