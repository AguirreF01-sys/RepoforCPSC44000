import pygame
import sys

from game.grid import Grid
from game.player import Player
from game.simulation import Simulation

# 6 by 6 grid, each cell is 60 pixels
CELL_SIZE = 60
GRID_SIZE = 6

TOP_BAR_HEIGHT = 140 # space for counters and messages
SIDE_PADDING = 40

GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE

WIDTH = GRID_WIDTH + SIDE_PADDING * 2
HEIGHT = GRID_HEIGHT + TOP_BAR_HEIGHT

BG_COLOR = (34, 139, 34)
GRID_COLOR = (200, 200, 200)
TEXT_COLOR = (255, 255, 255)
MESSAGE_COLOR = (255, 215, 0)


pygame.init()

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wandering in the Woods")

clock = pygame.time.Clock()

# Create the simulation
font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 48)

grid = Grid(GRID_SIZE, GRID_SIZE)

# Create two players at opposite corners
# Red player starts at top-left, Blue player starts at bottom-right
p1 = Player(1, 0, 0, (255, 0, 0))
p2 = Player(2, GRID_SIZE - 1, GRID_SIZE - 1, (0, 0, 255))

simulation = Simulation(grid, [p1,p2])

running_simulation = True

def draw_grid():

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):

            rect = pygame.Rect(
                SIDE_PADDING + c*CELL_SIZE,
                TOP_BAR_HEIGHT + r * CELL_SIZE, # Adjust for top bar
                CELL_SIZE,
                CELL_SIZE
            )

            pygame.draw.rect(screen,GRID_COLOR,rect,1)


def draw_players():

    for p in simulation.players:

        x = SIDE_PADDING + p.col*CELL_SIZE + CELL_SIZE//2
        y = TOP_BAR_HEIGHT + p.row*CELL_SIZE + CELL_SIZE//2

        pygame.draw.circle(screen,p.color,(x,y),CELL_SIZE//3)

def draw_ui():
    p1, p2 = simulation.players

    p1_text = font.render(f"Player 1 Moves: {p1.moves}", True, TEXT_COLOR)
    p2_text = font.render(f"Player 2 Moves: {p2.moves}", True, TEXT_COLOR)
    step_text = font.render(f"Total Steps: {simulation.stats.steps}", True, TEXT_COLOR)
    help_text = font.render("SPACE = pause/resume   R = reset", True, TEXT_COLOR)

    screen.blit(p1_text, (20, 10))
    screen.blit(p2_text, (20, 35))
    screen.blit(step_text, (20, 60))
    screen.blit(help_text, (20, 85))


def draw_meeting_message():
    if simulation.finished:
        msg_surface = big_font.render(simulation.message, True, MESSAGE_COLOR)
        msg_rect = msg_surface.get_rect(center=(WIDTH // 2, TOP_BAR_HEIGHT//2))
        screen.blit(msg_surface, msg_rect)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                simulation.reset()
                running_simulation = True

            if event.key == pygame.K_SPACE and not simulation.finished:
                running_simulation = not running_simulation

    if running_simulation and not simulation.finished:
        simulation.step()

    screen.fill(BG_COLOR)

    draw_grid()
    draw_players()
    draw_ui()
    draw_meeting_message()

    pygame.display.flip()
    clock.tick(5)
