class Player:
    def __init__(self, player_id, row, col, color):
        self.player_id = player_id
        self.row = row
        self.col = col
        self.start_row = row # Store starting position for reset
        self.start_col = col
        self.color = color
        self.moves = 0

    def position(self):
        return (self.row, self.col)

    def move_to(self, row, col):
        self.row = row
        self.col = col
        self.moves += 1

    # Reset player to starting position and reset move count
    def reset(self):
        self.row = self.start_row
        self.col = self.start_col
        self.moves = 0
