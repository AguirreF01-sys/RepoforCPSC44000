import pygame
import sys

from game.grid import Grid
from game.player import Player
from game.simulation import Simulation
from ui.button import Button
from ui.screens import draw_title_screen, draw_game_screen, draw_celebration_screen

# 6 by 6 grid, each cell is 60 pixels
CELL_SIZE = 60
GRID_SIZE = 6
ICON_SIZE = int(CELL_SIZE * 0.8) # Player icons will be 80% of cell size for better fit

TOP_BAR_HEIGHT = 140 # space for counters and messages
SIDE_PADDING = 40

GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE

WIDTH = GRID_WIDTH + SIDE_PADDING * 2
HEIGHT = GRID_HEIGHT + TOP_BAR_HEIGHT

BG_COLOR = (34, 139, 34)
BUTTON_COLOR = (60, 160, 60)
TEXT_COLOR = (255, 255, 255)


pygame.init()
player1_img = pygame.image.load("assets/player1.jpg")
player2_img = pygame.image.load("assets/player2.jpg")
player1_img = pygame.transform.smoothscale(player1_img, (ICON_SIZE, ICON_SIZE))
player2_img = pygame.transform.smoothscale(player2_img, (ICON_SIZE, ICON_SIZE))
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Wandering in the Woods")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 30)
big_font = pygame.font.SysFont(None, 48)

grid = Grid(GRID_SIZE, GRID_SIZE)

# Create two players at opposite corners
# Red player starts at top-left, Blue player starts at bottom-right
p1 = Player(1, 0, 0, (255, 0, 0))
p2 = Player(2, GRID_SIZE - 1, GRID_SIZE - 1, (0, 0, 255))

simulation = Simulation(grid, [p1,p2])

current_screen = "title"
running_simulation = False

start_button = Button((WIDTH // 2 - 80, HEIGHT // 2, 160, 50), "Start", font, BUTTON_COLOR, TEXT_COLOR)
pause_button = Button((WIDTH - 180, 20, 140, 40), "Pause", font, BUTTON_COLOR, TEXT_COLOR)
reset_button = Button((WIDTH - 180, 70, 140, 40), "Reset", font, BUTTON_COLOR, TEXT_COLOR)
play_again_button = Button((WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50), "Play Again", font, BUTTON_COLOR, TEXT_COLOR)
exit_button = Button((WIDTH // 2 - 100, HEIGHT // 2 + 170, 200, 50), "Exit", font, BUTTON_COLOR, TEXT_COLOR)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if current_screen == "title":
            if start_button.is_clicked(event):
                simulation.reset()
                running_simulation = True
                current_screen = "game"

        elif current_screen == "game":
            if pause_button.is_clicked(event): # Toggle simulation running state on pause button click
                running_simulation = not running_simulation
                if running_simulation:
                    pause_button.set_text("Pause")
                else:
                    pause_button.set_text("Run")

            if reset_button.is_clicked(event):
                simulation.reset()
                running_simulation = False

        elif current_screen == "celebration":
            if play_again_button.is_clicked(event):
                simulation.reset()
                running_simulation = True
                current_screen = "game"
            if exit_button.is_clicked(event):
                pygame.quit()
                sys.exit()

    if current_screen == "game" and running_simulation and not simulation.finished:
        simulation.step()

    if current_screen == "game" and simulation.finished:
        current_screen = "celebration"

    if current_screen == "title":
        draw_title_screen(screen, WIDTH, HEIGHT, big_font, font, start_button)

    elif current_screen == "game":
        draw_game_screen(
            screen,
            simulation,
            WIDTH,
            TOP_BAR_HEIGHT,
            SIDE_PADDING,
            GRID_SIZE,
            CELL_SIZE,
            font,
            pause_button,
            reset_button,
            player1_img,
            player2_img,
        )

    elif current_screen == "celebration":
        draw_celebration_screen(screen, WIDTH, HEIGHT, big_font, font, simulation, play_again_button, exit_button)

    pygame.display.flip()
    clock.tick(5)