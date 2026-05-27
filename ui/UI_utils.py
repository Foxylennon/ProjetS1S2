import pygame
from config import settings
from common.music_manager import music_manager

FONT_PATH = "assets/fonts/PressStart2P.ttf"
BODY_FONT_PATH = "assets/fonts/PixelOperator.ttf"


def load_font(size):
    """
    Charge une police de type UI / titres.
    """
    scaled_size = max(6, int(size))
    try:
        return pygame.font.Font(FONT_PATH, scaled_size)
    except Exception:
        return pygame.font.SysFont(None, scaled_size)


def load_body_font(size):
    """
    Charge la police pour les textes corps (indicateurs, notes, labels secondaires).
    """
    scaled_size = max(6, int(size))
    try:
        return pygame.font.Font(BODY_FONT_PATH, scaled_size)
    except Exception:
        return pygame.font.SysFont(None, scaled_size)


class Dropdown:
    """Menu déroulant avec support des flèches clavier."""
    def __init__(self, x, y, width, height, options, selected_index=0, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_index = selected_index
        self.is_open = False
        self.font = font

    @property
    def selected(self):
        return self.options[self.selected_index]

    def draw(self, surface):
        color = (70, 70, 70)
        hover_color = (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), self.rect, 2, border_radius=6)

        label = self.selected[0]
        text_surf = self.font.render(label, False, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(midleft=(self.rect.x + 12, self.rect.centery)))

        arrow = "▼" if not self.is_open else "▲"
        arrow_surf = self.font.render(arrow, False, (255, 255, 255))
        surface.blit(arrow_surf, arrow_surf.get_rect(midright=(self.rect.right - 12, self.rect.centery)))

        if self.is_open:
            for i, (label, _) in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(surface, hover_color if i == self.selected_index else color, option_rect, border_radius=6)
                pygame.draw.rect(surface, (180, 180, 180), option_rect, 2, border_radius=6)
                text_surf = self.font.render(label, False, (255, 255, 255))
                surface.blit(text_surf, text_surf.get_rect(midleft=(option_rect.x + 12, option_rect.centery)))

    def handle_click(self, mouse_pos):
        """Retourne 'toggle' si clic sur header, 'select' si clic sur option, sinon None."""
        if self.rect.collidepoint(mouse_pos):
            self.is_open = not self.is_open
            return 'toggle'

        if self.is_open:
            for i, _ in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                if option_rect.collidepoint(mouse_pos):
                    self.selected_index = i
                    self.is_open = False
                    return 'select'
        return None

    def navigate_keyboard(self, key):
        """Navigue dans le dropdown avec les flèches clavier."""
        if not self.is_open:
            return
        if key == pygame.K_UP:
            self.selected_index = max(0, self.selected_index - 1)
        elif key == pygame.K_DOWN:
            self.selected_index = min(len(self.options) - 1, self.selected_index + 1)


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
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered and not was_hovered:
            music_manager.play_hover()

    def is_clicked(self, mouse_pos, mouse_pressed):
        """Retourne vrai si le bouton est survolé et qu'un clic gauche a lieu."""
        clicked = self.rect.collidepoint(mouse_pos) and mouse_pressed
        if clicked:
            music_manager.play_click()
        return clicked
