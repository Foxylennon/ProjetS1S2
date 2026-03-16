"""
=============================================================================
                        POINT D'ENTRÉE DU JEU
=============================================================================

Ce fichier contient :
1. La configuration globale (résolution, taille fenêtre)
2. Le DisplayManager (gestion de l'affichage avec upscaling)
3. La boucle principale avec la MACHINE À ÉTATS

MACHINE À ÉTATS :
-----------------
Le jeu fonctionne avec différents "états" :
- "menu"       : Menu principal
- "game"       : Jeu solo
- "multi_menu" : Menu multijoueur (choix Host/Client)
- "game_multi" : Jeu en multijoueur
- "quit"       : Quitter le jeu

Chaque état est une fonction qui retourne le prochain état.

"""

import pygame
import sys
from main_menu.Main_menu import main_menu
from main_menu.Multiplayer_menu import multiplayer_menu
from game.Game import game
from game.Game_multi import game_multiplayer
from network.Network import Network

# --- CONFIGURATION ---
GAME_W, GAME_H = 320, 180  # Résolution virtuelle du jeu
DEFAULT_SCREEN_W, DEFAULT_SCREEN_H = 1280, 720  # Taille fenêtre de départ


class DisplayManager:
    """
    Gère l'affichage avec une résolution virtuelle.
    
    POURQUOI ?
    ----------
    On dessine tout sur une petite surface (320x180) puis on l'agrandit.
    Avantages :
    - Le jeu a le même rendu quelle que soit la taille de la fenêtre
    - Style "pixel art" automatique
    - Performances optimales
    """
    
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

        # On garde un zoom entier pour éviter le flou du pixel art.
        # Si la fenêtre n'est pas un multiple entier, on ajoute des bandes noires.
        scale_w = scr_w // GAME_W
        scale_h = scr_h // GAME_H
        self.scale = max(1, min(scale_w, scale_h))

        # Nouvelle taille du canvas étiré (entier)
        self.new_w = GAME_W * self.scale
        self.new_h = GAME_H * self.scale

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
    """
    FONCTION PRINCIPALE - MACHINE À ÉTATS
    
    Le jeu est organisé en "états". Chaque état est une fonction
    qui gère sa propre boucle et retourne le nom du prochain état.
    
    SCHÉMA :
    
        ┌──────────────────────────────────────────┐
        │                                          │
        ▼                                          │
      menu ──────► game ─────────────────────────► │
        │                                          │
        └──────► multi_menu ──► game_multi ──────► │
                     │                             │
                     └─────────────────────────────┘
        
    """
    pygame.init()
    pygame.display.set_caption("ProjetS1S2 - Multijoueur")

    # Création du gestionnaire d'affichage (UNE SEULE FOIS)
    display_manager = DisplayManager()
    
    # Création de l'objet réseau (UNE SEULE FOIS)
    # On le crée ici pour pouvoir le réutiliser entre les états
    network = Network()

    # État initial
    state = "menu"

    # =========================================================================
    #                       BOUCLE DE LA MACHINE À ÉTATS
    # =========================================================================
    
    while state != "quit":
        
        if state == "menu":
            # Menu principal
            state = main_menu(display_manager)
        
        elif state == "game":
            # Jeu solo
            state = game(display_manager)
        
        elif state == "multi_menu":
            # Menu multijoueur (choix Host/Client)
            # On recrée l'objet network pour une nouvelle connexion
            network = Network()
            state = multiplayer_menu(display_manager, network)
        
        elif state == "game_multi":
            # Jeu multijoueur
            state = game_multiplayer(display_manager, network)
        
        else:
            # État inconnu → retour au menu
            print(f"[MAIN] État inconnu : {state}")
            state = "menu"
    
    # Fermeture propre
    network.close()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
