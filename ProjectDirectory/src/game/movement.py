import random

def random_move(player, grid):

    # Get valid neighboring positions
    neighbors = grid.neighbors(player.row, player.col)

    # choose a random valid move
    new_row, new_col = random.choice(neighbors)

    # Move the player to the new position
    player.move_to(new_row, new_col)
