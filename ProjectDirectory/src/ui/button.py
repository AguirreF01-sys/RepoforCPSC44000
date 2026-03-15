import pygame

class Button:
    def __init__(self, rect, text, font, bg_color, text_color, border_color=(255, 255, 255)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.border_color = border_color

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, self.border_color, self.rect, width=2, border_radius=10)

        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def is_clicked(self, event):
        return (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and self.rect.collidepoint(event.pos)
        )
    
    def set_text(self, text):
        self.text = text
