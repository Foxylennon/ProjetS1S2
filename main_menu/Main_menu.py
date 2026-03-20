"""
=============================================================================
                        MENU PRINCIPAL (PYGAME PUR)
=============================================================================

Menu simple sans pygame_gui - que du pygame de base.

"""

import pygame

from config import settings
from lang import t

FONT_PATH = "assets/fonts/PressStart2P-Regular.ttf"


def load_font(size):
    scale = settings.get("text_scale", 1.0)
    size = max(6, int(size * scale))
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont(None, size)


class Button:
    """Bouton simple fait maison."""
    
    def __init__(self, x, y, width, height, text, color=(70, 70, 70), hover_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
    
    def draw(self, surface, font):
        # Couleur selon hover
        color = self.hover_color if self.is_hovered else self.color
        
        # Fond du bouton
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        
        # Bordure
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        
        # Texte centré
        text_surf = font.render(self.text, False, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
    
    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed


def main_menu(dm):
    """Menu principal."""
    print("--- MENU PRINCIPAL ---")
    
    # Police (recalculée en fonction du scale texte)
    font_big = load_font(56)
    font = load_font(32)
    
    # Créer les boutons
    GAME_W  = 1280
    btn_width = 400
    btn_height = 60
    btn_x = (GAME_W -btn_width)//2
    btn_play = Button(btn_x, 300, btn_width, btn_height, t("button_play"), color=(70, 100, 70))
    btn_multi = Button(btn_x, 380, btn_width, btn_height, t("button_multi"), color=(70, 70, 100))
    btn_settings = Button(btn_x, 460, btn_width, btn_height, t("button_settings"), color=(70, 100, 100))
    btn_quit = Button(btn_x, 540, btn_width, btn_height, t("button_quit"), color=(100, 70, 70))
    
    buttons = [btn_play, btn_multi, btn_settings, btn_quit]
    
    clock = pygame.time.Clock()
    
    while True:
        # --- ÉVÉNEMENTS ---
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Clic gauche
                    mouse_clicked = True
            
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()
        
        # --- MISE À JOUR ---
        mouse_pos = dm.get_mouse()
        
        for btn in buttons:
            btn.update(mouse_pos)
        
        # --- CLICS ---
        if mouse_clicked:
            if btn_play.is_clicked(mouse_pos, True):
                return "game"
            if btn_multi.is_clicked(mouse_pos, True):
                return "multi_menu"
            if btn_settings.is_clicked(mouse_pos, True):
                return "settings"
            if btn_quit.is_clicked(mouse_pos, True):
                return "quit"
        
        # --- AFFICHAGE ---
        dm.canvas.fill((40, 40, 40))
        
        # Titre
        title = font_big.render(t("game_title"), False, (255, 255, 255))
        title_rect = title.get_rect(center=(640, 180))
        dm.canvas.blit(title, title_rect)
        
        # Boutons
        for btn in buttons:
            btn.draw(dm.canvas, font)
        
        dm.render()
        clock.tick(60)
