import pygame
from config import settings

FONT_PATH = "assets/fonts/PressStart2P-Regular.ttf"

def load_font(size):
    """
    Charge une police en appliquant l'échelle de texte choisie dans Settings.
    Utilise une taille minimale de 6.
    """
    scale = settings.get("text_scale", 1.0)
    scaled_size = max(6, int(size * scale))
    try:
        return pygame.font.Font(FONT_PATH, scaled_size)
    except Exception:
        return pygame.font.SysFont(None, scaled_size)

class Button:
    """
    Bouton générique pour l'interface de jeu.
    """
    def __init__(self, x, y, width, height, text, font, color=(70, 70, 70), hover_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        
        # Rend le texte avec la police définie
        text_surf = self.font.render(self.text, False, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        """Met à jour l'état de survol du bouton."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        """Retourne vrai si le bouton est survolé et qu'un clic gauche a lieu."""
        return self.rect.collidepoint(mouse_pos) and mouse_pressed
