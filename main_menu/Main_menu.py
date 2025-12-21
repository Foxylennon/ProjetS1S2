import pygame
import pygame_gui


def main_menu(dm):
    print("--- MENU AVEC PYGAME_GUI ---")

    # 1. Création du Manager UI
    # IMPORTANT : On lui donne la taille VIRTUELLE (320, 180), pas celle de la fenêtre
    manager = pygame_gui.UIManager(dm.virtual_res)

    # 2. Création des éléments (Boutons, Sliders, etc.)
    # On les place en coordonnées 320x180

    # Titre (Label)
    rect_titre = pygame.Rect(0, 20, 320, 30)
    label_title = pygame_gui.elements.UILabel(
        relative_rect=rect_titre,
        text="MON SUPER JEU",
        manager=manager
    )

    # Bouton 1 : Petite Résolution
    rect_btn_1 = pygame.Rect(110, 60, 100, 30)
    btn_res_small = pygame_gui.elements.UIButton(
        relative_rect=rect_btn_1,
        text='2560x1440',
        manager=manager
    )

    # Bouton 2 : Grande Résolution
    rect_btn_2 = pygame.Rect(110, 100, 100, 30)
    btn_res_big = pygame_gui.elements.UIButton(
        relative_rect=rect_btn_2,
        text='1280x720',
        manager=manager
    )

    # Bouton 3 : Jouer
    rect_btn_play = pygame.Rect(110, 140, 100, 30)
    btn_play = pygame_gui.elements.UIButton(
        relative_rect=rect_btn_play,
        text='JOUER',
        manager=manager
    )

    clock = pygame.time.Clock()
    running = True

    while running:
        time_delta = clock.tick(60) / 1000.0

        # --- GESTION DES ÉVÉNEMENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

            # --- MOUSE FIX ---
            # On intercepte les événements souris pour corriger les coordonnées
            if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                # On utilise la fonction de calcul existante
                virtual_xy = dm.get_mouse()

                # On remplace les coordonnées réelles par les virtuelles dans l'événement
                event.pos = virtual_xy

                # Si c'est un mouvement, il faut aussi corriger le mouvement relatif (rel)
                if event.type == pygame.MOUSEMOTION:
                    # Approximation : on divise le mouvement par le scale
                    event.rel = (int(event.rel[0] / dm.scale), int(event.rel[1] / dm.scale))

            # Maintenant que l'événement est "corrigé", on le donne à pygame_gui
            manager.process_events(event)

            # --- GESTION DES CLICS UI ---
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == btn_res_small:
                    dm.change_resolution(2560, 1440)
                elif event.ui_element == btn_res_big:
                    dm.change_resolution(1280, 720)
                elif event.ui_element == btn_play:
                    return "game"

        # --- MISE À JOUR ---
        manager.update(time_delta)

        # --- DESSIN ---
        dm.canvas.fill((40, 40, 40))  # Fond

        # On demande au manager de dessiner sur le CANVAS virtuel
        manager.draw_ui(dm.canvas)

        # On render le tout à l'écran
        dm.render()
