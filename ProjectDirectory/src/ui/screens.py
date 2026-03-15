import pygame

def draw_title_screen(screen, width, height, title_font, text_font, start_button):
    screen.fill((34, 139, 34))

    title_text = title_font.render("Wandering in the Woods", True, (255, 255, 255))
    subtitle_text = text_font.render("Can the two friends find each other?", True, (255, 255, 255))

    title_rect = title_text.get_rect(center=(width // 2, height // 3))
    subtitle_rect = subtitle_text.get_rect(center=(width // 2, height // 3 + 60))

    screen.blit(title_text, title_rect)
    screen.blit(subtitle_text, subtitle_rect)

    start_button.draw(screen)


def draw_game_screen(
    screen,
    simulation,
    width,
    top_bar_height,
    side_padding,
    grid_size,
    cell_size,
    font,
    pause_button,
    reset_button,
    player1_img,
    player2_img,
):
    screen.fill((34, 139, 34))

    p1, p2 = simulation.players

    p1_text = font.render(f"Player 1 Moves: {p1.moves}", True, (255, 255, 255))
    p2_text = font.render(f"Player 2 Moves: {p2.moves}", True, (255, 255, 255))
    step_text = font.render(f"Total Steps: {simulation.stats.steps}", True, (255, 255, 255))

    screen.blit(p1_text, (20, 15))
    screen.blit(p2_text, (20, 45))
    screen.blit(step_text, (20, 75))

    pause_button.draw(screen)
    reset_button.draw(screen)

    for r in range(grid_size):
        for c in range(grid_size):
            rect = pygame.Rect(
                side_padding + c * cell_size,
                top_bar_height + r * cell_size,
                cell_size,
                cell_size
            )
            pygame.draw.rect(screen, (200, 200, 200), rect, 1)

    for p in simulation.players:
        x = side_padding + p.col * cell_size + cell_size // 2
        y = top_bar_height + p.row * cell_size + cell_size // 2
        if p.player_id == 1:
            img = player1_img
        else:
            img = player2_img

        rect = img.get_rect(center=(x, y))
        screen.blit(img, rect)


def draw_celebration_screen(screen, width, height, title_font, text_font, simulation, play_again_button, exit_button):
    screen.fill((34, 139, 34))

    title_text = title_font.render("They found each other!", True, (255, 215, 0))

    p1, p2 = simulation.players
    line1 = text_font.render(f"Player 1 Moves: {p1.moves}", True, (255, 255, 255))
    line2 = text_font.render(f"Player 2 Moves: {p2.moves}", True, (255, 255, 255))
    line3 = text_font.render(f"Total Steps: {simulation.stats.steps}", True, (255, 255, 255))

    title_rect = title_text.get_rect(center=(width // 2, height // 3))
    line1_rect = line1.get_rect(center=(width // 2, height // 3 + 60))
    line2_rect = line2.get_rect(center=(width // 2, height // 3 + 95))
    line3_rect = line3.get_rect(center=(width // 2, height // 3 + 130))

    screen.blit(title_text, title_rect)
    screen.blit(line1, line1_rect)
    screen.blit(line2, line2_rect)
    screen.blit(line3, line3_rect)

    play_again_button.draw(screen)
    exit_button.draw(screen)
