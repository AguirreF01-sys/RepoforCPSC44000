import pygame
import sys

from game.grid import Grid
from game.player import Player
from game.simulation import Simulation

# 6 by 6 grid, each cell is 60 pixels
CELL_SIZE = 60
GRID_SIZE = 6

WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE


pygame.init()

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wandering in the Woods")

clock = pygame.time.Clock()


grid = Grid(GRID_SIZE, GRID_SIZE)

# Create two players at opposite corners
# Red player starts at top-left, Blue player starts at bottom-right
p1 = Player(1, 0, 0, (255,0,0))
p2 = Player(2, GRID_SIZE-1, GRID_SIZE-1, (0,0,255))

simulation = Simulation(grid, [p1,p2])


def draw_grid():

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):

            rect = pygame.Rect(
                c*CELL_SIZE,
                r*CELL_SIZE,
                CELL_SIZE,
                CELL_SIZE
            )

            pygame.draw.rect(screen,(200,200,200),rect,1)


def draw_players():

    for p in simulation.players:

        x = p.col*CELL_SIZE + CELL_SIZE//2
        y = p.row*CELL_SIZE + CELL_SIZE//2

        pygame.draw.circle(screen,p.color,(x,y),CELL_SIZE//3)


while True:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if not simulation.finished:
        simulation.step()

    screen.fill((30,120,30))

    draw_grid()
    draw_players()

    pygame.display.flip()

    clock.tick(5)
