#balloons

import pygame
import random
import math


class Balloon:
    def __init__(self, screen_width, screen_height):
        self.x = random.randint(20, screen_width - 20)
        self.y = screen_height + random.randint(0, 100)  # start below screen
        self.speed = random.uniform(4.5*2, 7.0*2)
        self.wobble_offset = random.uniform(0, 2 * math.pi)
        self.wobble_speed = random.uniform(0.05, 0.1)
        self.wobble_amount = random.uniform(12, 28)
        self.color = random.choice([
            (255, 80, 80),   # red
            (80, 80, 255),   # blue
            (255, 230, 50),  # yellow
            (80, 255, 120),  # green
            (255, 140, 0),   # orange
            (200, 80, 255),  # purple
        ])
        self.radius = random.randint(14, 22)
        self.tick = 0

    def update(self):
        self.y -= self.speed
        self.tick += self.wobble_speed
        self.x += math.sin(self.tick + self.wobble_offset) * 2.5

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        # Balloon body
        pygame.draw.circle(surface, self.color, (ix, iy), self.radius)
        # Highlight
        pygame.draw.circle(surface, (255, 255, 255), (ix - self.radius//3, iy - self.radius//3), self.radius//4)
        # String
        pygame.draw.line(surface, (180, 180, 180), (ix, iy + self.radius), (ix + 5, iy + self.radius + 18), 1)