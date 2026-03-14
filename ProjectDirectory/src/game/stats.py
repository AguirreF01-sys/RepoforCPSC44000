class Stats:

    def __init__(self):
        self.steps = 0

    def step(self):
        self.steps += 1

    def reset(self):
        self.steps = 0
