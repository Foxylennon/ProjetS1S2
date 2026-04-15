"""
=============================================================================
                        MENU PRINCIPAL (PYGAME PUR)
=============================================================================

Menu simple sans pygame_gui - que du pygame de base.

"""

import pygame

from config import settings
from lang import t

from ui.UI_utils import Button, load_font

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
    btn_play = Button(btn_x, 300, btn_width, btn_height, t("button_play"), font, color=(70, 100, 70))
    btn_multi = Button(btn_x, 380, btn_width, btn_height, t("button_multi"), font, color=(70, 70, 100))
    btn_settings = Button(btn_x, 460, btn_width, btn_height, t("button_settings"), font, color=(70, 100, 100))
    btn_quit = Button(btn_x, 540, btn_width, btn_height, t("button_quit"), font, color=(100, 70, 70))
    
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
            btn.font = font
            btn.draw(dm.canvas)
        
        dm.render()
        clock.tick(60)
