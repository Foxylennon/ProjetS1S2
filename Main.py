import pygame
import sys
from main_menu.Main_menu import main_menu
from game.Game import game

# --- CONFIGURATION ---
GAME_W, GAME_H = 320, 180  # Résolution
DEFAULT_SCREEN_W, DEFAULT_SCREEN_H = 1280, 720  # Taille fenêtre de départ


class DisplayManager:
    def __init__(self):
        self.virtual_res = (GAME_W, GAME_H)
        # La surface sur laquelle on vas dessiner tout le jeu
        self.canvas = pygame.Surface(self.virtual_res)

        # État de la fenêtre réelle
        self.window_w = DEFAULT_SCREEN_W
        self.window_h = DEFAULT_SCREEN_H
        self.fullscreen = False
        self.screen = None

        # Création de la fenêtre
        self.set_window_mode()

    def set_window_mode(self):
        """Crée ou recrée la fenêtre selon les paramètres actuels"""
        flags = pygame.RESIZABLE
        if self.fullscreen:
            flags = pygame.FULLSCREEN | pygame.SCALED

        self.screen = pygame.display.set_mode((self.window_w, self.window_h), flags)
        self.calc_scale()  # Important : recalculer les ratios tout de suite

    def change_resolution(self, width, height, fullscreen=False):
        """Appelle cette fonction depuis tes menus pour changer la taille"""
        self.window_w = width
        self.window_h = height
        self.fullscreen = fullscreen
        self.set_window_mode()

    def calc_scale(self):
        """Calcule le zoom et les bandes noires"""
        scr_w, scr_h = self.screen.get_size()

        # Calcul du facteur de zoom (on garde le ratio)
        self.scale = min(scr_w / GAME_W, scr_h / GAME_H)

        # Nouvelle taille du canvas étiré
        self.new_w = int(GAME_W * self.scale)
        self.new_h = int(GAME_H * self.scale)

        # Calcul du centrage (offset)
        self.dx = (scr_w - self.new_w) // 2
        self.dy = (scr_h - self.new_h) // 2

    def render(self):
        """Affiche le canvas sur l'écran final"""
        # 1. Fond noir (bandes noires)
        self.screen.fill((0, 0, 0))

        # 2. Upscaling (redimensionnement propre)
        scaled_surf = pygame.transform.scale(self.canvas, (self.new_w, self.new_h))

        # 3. Blit centré
        self.screen.blit(scaled_surf, (self.dx, self.dy))

        # 4. Flip
        pygame.display.flip()

    def get_mouse(self):
        """Traduit la souris 'Fenêtre' vers la souris 'Jeu'"""
        mx, my = pygame.mouse.get_pos()

        # On enlève les bandes noires et on divise par le zoom
        mx_virt = int((mx - self.dx) / self.scale)
        my_virt = int((my - self.dy) / self.scale)

        # On s'assure qu'on ne sort pas du cadre du jeu
        return mx_virt, my_virt


def main():
    pygame.init()

    # UNE SEULE FOIS
    display_manager = DisplayManager()

    state = "menu"

    while state != "quit":
        if state == "menu":
            state = main_menu(display_manager)
        elif state == "game":
            state = game(display_manager)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()