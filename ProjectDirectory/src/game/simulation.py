from .movement import random_move
from .stats import Stats

class Simulation:

    def __init__(self, grid, players):
        self.grid = grid
        self.players = players
        self.stats = Stats()
        self.finished = False
        self.message = ""

    def step(self):

        if self.finished:
            return

        for p in self.players:
            random_move(p, self.grid)

        self.stats.step()

        self.check_meeting()

    def check_meeting(self):

        p1, p2 = self.players

        if p1.position() == p2.position():
            self.finished = True
            self.message = "They met!"

            print("\n Players met!")
            print(f"Total simulation steps: {self.stats.steps}")
            print(f"Player 1 moves: {p1.moves}")
            print(f"Player 2 moves: {p2.moves}")

    def reset(self):
        for p in self.players:
            p.reset()
        self.stats.reset()
        self.finished = False
        self.message = ""
