"""
=============================================================================
                        MENU MULTIJOUEUR
=============================================================================

Ce menu permet de :
1. Créer une partie (HOST)
2. Rejoindre une partie (CLIENT)

FONCTIONNEMENT :
----------------
- HOST   : Cliquez sur "Créer partie", le jeu attend qu'un joueur se connecte
- CLIENT : Entrez l'IP du Host, puis cliquez sur "Rejoindre"

COMMENT TROUVER SON IP ?
------------------------
- Windows : Ouvrir CMD, taper "ipconfig", chercher "Adresse IPv4"
- Mac/Linux : Ouvrir Terminal, taper "ifconfig" ou "ip addr"
- Généralement c'est quelque chose comme 192.168.1.XX

"""

import pygame
import socket
import threading
import random
from lang import t
from ui.UI_utils import Button, load_body_font, load_font


def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def multiplayer_menu(dm, network):
    """
    Menu pour choisir entre Host et Client.
    
    RETOURNE :
    - "game_multi" : Si la connexion est établie
    - "menu"       : Si on veut revenir au menu principal
    - "quit"       : Si on ferme la fenêtre
    """
    print("--- MENU MULTIJOUEUR ---")
    
    # =========================================================================
    #                       INITIALISATION
    # =========================================================================
    
    # Polices
    font_big = load_font(56)
    font_medium = load_font(32)
    font_small = load_font(26)
    font_body = load_body_font(24)
    
    def get_local_ip():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    # Récupérer notre IP locale pour l'afficher
    my_ip = get_local_ip()
    
    # Champ de saisie pour l'IP (pour le client)
    ip_input = my_ip
    ip_active = False        # Est-ce que le champ est sélectionné ?
    
    # États
    waiting_for_client = False  # Le Host attend un client
    connecting = False          # Le Client est en train de se connecter
    error_message = ""          # Message d'erreur à afficher
    
    # Thread pour les opérations réseau (pour ne pas bloquer l'interface)
    network_thread = None
    connection_result = {"success": False, "done": False}
    
    # Boutons (x, y, largeur, hauteur)
    GAME_W  = 1280
    btn_width = 400
    btn_height = 60
    btn_x = (GAME_W - btn_width) // 2
    btn_host = Button(btn_x, 240, btn_width, btn_height, t("button_create_game"), font_small, color=(70, 130, 70), hover_color=(90, 170, 90))
    btn_join = Button(btn_x, 480, btn_width, btn_height, t("button_join_game"), font_small, color=(70, 70, 130), hover_color=(100, 100, 170))
    btn_back = Button(50, 600, btn_width // 2, int(btn_height // 1.5), t("button_back"), font_small, color=(60, 60, 60), hover_color=(90, 90, 90))
    input_rect = pygame.Rect((GAME_W - btn_width * 1.5) // 2, 360, int(btn_width * 1.5), btn_height)
    
    clock = pygame.time.Clock()
    
    # =========================================================================
    #            FONCTIONS POUR LE RÉSEAU (exécutées dans un thread)
    # =========================================================================
    
    def host_thread_func():
        """Fonction exécutée dans un thread pour démarrer le host."""
        try:
            result = network.start_host()
            connection_result["success"] = result
        except Exception as e:
            print(f"Erreur host: {e}")
            connection_result["success"] = False
        connection_result["done"] = True
    
    def client_thread_func(ip):
        """Fonction exécutée dans un thread pour se connecter."""
        try:
            result = network.connect_to_host(ip)
            connection_result["success"] = result
        except Exception as e:
            print(f"Erreur client: {e}")
            connection_result["success"] = False
        connection_result["done"] = True
    
    # =========================================================================
    #                       BOUCLE PRINCIPALE
    # =========================================================================
    
    running = True
    while running:
        mouse_pos = dm.get_mouse()
        btn_host.update(mouse_pos)
        btn_join.update(mouse_pos)
        btn_back.update(mouse_pos)

        # ---------------------------------------------------------------------
        #                    GESTION DES ÉVÉNEMENTS
        # ---------------------------------------------------------------------
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if waiting_for_client or connecting:
                        # Annuler l'opération en cours
                        network.close()
                        waiting_for_client = False
                        connecting = False
                        connection_result["done"] = False
                    else:
                        return "menu"
                
                # Saisie de l'IP (BACKSPACE, RETOUR)
                if ip_active and not waiting_for_client and not connecting:
                    if event.key == pygame.K_BACKSPACE:
                        ip_input = ip_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        # Lancer la connexion
                        pass

            if event.type == pygame.TEXTINPUT:
                if ip_active and not waiting_for_client and not connecting:
                    char = event.text
                    if len(char) == 1 and (char.isdigit() or char == '.'):
                        ip_input += char
            
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()
            
            # Clics souris
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Convertir position souris
                mouse_pos = dm.get_mouse()
                
                # Clic sur le champ IP
                if input_rect.collidepoint(mouse_pos):
                    ip_active = True
                    pygame.key.start_text_input()
                else:
                    ip_active = False
                    pygame.key.stop_text_input()
                
                # Clic sur "Créer partie" (HOST)
                if btn_host.is_clicked(mouse_pos, True) and not waiting_for_client and not connecting:
                    waiting_for_client = True
                    connection_result["done"] = False
                    connection_result["success"] = False
                    error_message = ""

                    # Lancer le thread (démarre le serveur en arrière-plan)
                    network_thread = threading.Thread(target=host_thread_func)
                    network_thread.daemon = True
                    network_thread.start()

                    # Rediriger immédiatement vers le lobby où l'on affichera l'attente
                    return "lobby"
                
                # Clic sur "Rejoindre" (CLIENT)
                if btn_join.is_clicked(mouse_pos, True) and not waiting_for_client and not connecting:
                    if len(ip_input) > 7:  # IP minimale : "1.1.1.1"
                        connecting = True
                        connection_result["done"] = False
                        connection_result["success"] = False
                        error_message = ""
                        
                        # Lancer le thread
                        network_thread = threading.Thread(target=client_thread_func, args=(ip_input,))
                        network_thread.daemon = True
                        network_thread.start()
                    else:
                        error_message = t("error_invalid_ip")
                
                # Clic sur "Retour"
                if btn_back.is_clicked(mouse_pos, True):
                    network.close()
                    return "menu"
        
        # ---------------------------------------------------------------------
        #                    VÉRIFICATION DU THREAD RÉSEAU
        # ---------------------------------------------------------------------
        
        if connection_result["done"]:
            if connection_result["success"]:
                # Connexion réussie ! Lancer le lobby
                return "lobby"
            else:
                # Échec
                if waiting_for_client:
                    error_message = t("error_server")
                else:
                    error_message = t("error_connection_failed")
                waiting_for_client = False
                connecting = False
            connection_result["done"] = False
        
        dm.canvas.fill((40, 40, 40))
        
        # --- Titre ---
        title = font_big.render(t("multiplayer_title"), False, (255, 255, 255))
        dm.canvas.blit(title, (btn_x, 60))
        
        if waiting_for_client or connecting:
            loading_text = font_small.render(t("loading"), False, (200, 200, 200))
            dm.canvas.blit(loading_text, (btn_x + btn_width + 20, 68))
        
        # --- Section HOST ---
        
        # Bouton Host
        btn_host.text = t("button_waiting_host") if waiting_for_client else t("button_create_game")
        btn_host.color = (80, 80, 80) if waiting_for_client else (70, 130, 70)
        btn_host.hover_color = (120, 120, 120) if waiting_for_client else (90, 170, 90)
        btn_host.font = font_small
        btn_host.draw(dm.canvas)
        
        # Afficher notre IP
        ip_label = font_body.render(f"{t('your_ip_label')} {my_ip}", False, (150, 150, 150))
        dm.canvas.blit(ip_label, (btn_x + 480, 250))
        
        # --- Section CLIENT ---
        
        # Champ de saisie IP
        input_color = (60, 60, 80) if ip_active else (50, 50, 50)
        pygame.draw.rect(dm.canvas, input_color, input_rect, border_radius=3)
        pygame.draw.rect(dm.canvas, (100, 100, 100) if ip_active else (70, 70, 70), input_rect, 1, border_radius=3)
        
        ip_text = font_small.render(ip_input, False, (255, 255, 255))
        dm.canvas.blit(ip_text, (input_rect.x + 5, input_rect.y + 4))
        
        ip_hint = font_body.render(t("host_ip_label"), False, (150, 150, 150))
        dm.canvas.blit(ip_hint, (btn_x - 245, 365))
        
        # Bouton Rejoindre
        btn_join.text = t("button_connecting") if connecting else t("button_join_game")
        btn_join.color = (80, 80, 80) if connecting else (70, 70, 130)
        btn_join.hover_color = (120, 120, 120) if connecting else (100, 100, 170)
        btn_join.font = font_small
        btn_join.draw(dm.canvas)
        
        # --- Message d'erreur ---
        if error_message:
            err_text = font_small.render(error_message, False, (255, 100, 100))
            dm.canvas.blit(err_text, (btn_x, 365))
        
        # --- Bouton Retour ---
        btn_back.font = font_small
        btn_back.draw(dm.canvas)
        
        # --- Instructions ---
        instr = font_body.render(t("instruction_cancel_back"), False, (100, 100, 100))
        dm.canvas.blit(instr, (600, 1000))
        
        # --- Rendu ---
        dm.render()
        clock.tick(60)
    
    return "menu"


def _create_desaturated(surface: pygame.Surface) -> pygame.Surface:
    desat = surface.copy()
    overlay = pygame.Surface(desat.get_size(), pygame.SRCALPHA)
    overlay.fill((140, 140, 140, 120))
    desat.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    desat.set_alpha(150)
    return desat


def multiplayer_lobby(dm, network):
    """
    Lobby pour la partie multijoueur.
    - 4 emplacements de joueurs
    - P1 = hôte, toujours prêt
    - P2 = invité connecté
    - P3/P4 = slots vides
    """
    print("--- LOBBY MULTIJOUEUR ---")

    font_big = load_font(56)
    font_medium = load_font(32)
    font_small = load_font(26)
    font_body = load_body_font(26)
    font_input = load_body_font(22)

    # Chargement des avatars de profil (réduit)
    profile_imgs = []
    profile_desat = []
    for idx in range(1, 5):
        try:
            img = pygame.image.load(f"assets/ui/profil-p{idx}.png").convert_alpha()
        except Exception:
            img = pygame.Surface((160, 160), pygame.SRCALPHA)
            img.fill((120, 120, 120))
        scaled = pygame.transform.smoothscale(img, (160, 160))
        profile_imgs.append(scaled)
        profile_desat.append(_create_desaturated(scaled))

    names = [f"P{i}" for i in range(1, 5)]
    input_rects = []
    slot_rects = []
    start_x = 70
    start_y = 280
    slot_w = 220
    slot_h = 260
    gap_x = 30

    # Disposer les 4 emplacements sur une même ligne
    for col in range(4):
        x = start_x + (slot_w + gap_x) * col
        y = start_y
        slot_rects.append(pygame.Rect(x, y, slot_w, slot_h))
        input_rects.append(pygame.Rect(x + 10, y - 36, slot_w - 20, 34))

    btn_back = Button(50, 660, 140, 42, t("button_back"), font_small, color=(60, 60, 60), hover_color=(90, 90, 90))
    btn_start = Button(0, 0, 200, 50, t("button_start"), font_small, color=(70, 130, 70), hover_color=(90, 170, 90))
    btn_ready = Button(0, 0, 150, 44, t("button_ready"), font_small, color=(70, 130, 70), hover_color=(90, 170, 90))

    clock = pygame.time.Clock()
    active_input = None
    local_ready = network.is_host
    last_lobby_state = None

    while True:
        mouse_pos = dm.get_mouse()
        btn_back.update(mouse_pos)
        btn_start.update(mouse_pos)
        btn_ready.update(mouse_pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    network.close()
                    return "menu"

                if active_input is not None:
                    if event.key == pygame.K_BACKSPACE:
                        names[active_input] = names[active_input][:-1]
                    elif event.key == pygame.K_RETURN:
                        active_input = None
                        pygame.key.stop_text_input()

            if event.type == pygame.TEXTINPUT and active_input is not None:
                char = event.text
                if len(names[active_input]) < 16 and char.isprintable():
                    names[active_input] += char

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = False
                for idx, rect in enumerate(input_rects):
                    if rect.collidepoint(mouse_pos):
                        active_input = idx
                        pygame.key.start_text_input()
                        clicked = True
                        break
                if not clicked:
                    if active_input is not None:
                        active_input = None
                        pygame.key.stop_text_input()

                if btn_back.is_clicked(mouse_pos, True):
                    network.close()
                    return "menu"

                if network.is_host and btn_start.is_clicked(mouse_pos, True):
                    joined = network.connected
                    remote_ready = network.other_player_pos.get("lobby_ready", False)
                    if joined and remote_ready:
                        seed = random.randint(0, 1000000)
                        network.other_player_pos["map_seed"] = seed
                        network.send_start_game(seed)
                        return "game_multi"

                if not network.is_host and btn_ready.is_clicked(mouse_pos, True):
                    local_ready = not local_ready
                    network.send_lobby_status(local_ready, names[1])

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        if network.connected:
            if network.is_host:
                my_name = names[0]
                if last_lobby_state != (local_ready, my_name):
                    network.send_lobby_status(True, my_name)
                    last_lobby_state = (local_ready, my_name)
            else:
                my_name = names[1]
                if last_lobby_state != (local_ready, my_name):
                    network.send_lobby_status(local_ready, my_name)
                    last_lobby_state = (local_ready, my_name)

        if not network.is_host and network.other_player_pos.get("start_game"):
            return "game_multi"

        dm.canvas.fill((35, 35, 35))

        title = font_big.render(t("lobby_title"), False, (255, 255, 255))
        title_rect = title.get_rect(topleft=(start_x, 40))
        dm.canvas.blit(title, title_rect)

        ip_text = font_small.render(f"{t('your_ip_label')} {get_local_ip()}", False, (180, 180, 180))
        dm.canvas.blit(ip_text, (title_rect.right + 20, title_rect.y + 12))

        subtitle = font_body.render(t("lobby_subtitle"), False, (200, 200, 200))
        dm.canvas.blit(subtitle, (start_x, 110))

        for idx, slot_rect in enumerate(slot_rects):
            joined = False
            ready = False
            display_name = names[idx] or f"P{idx + 1}"

            if idx == 0:
                joined = True
                ready = True
                display_name = names[0] or "P1"
            elif idx == 1:
                joined = network.connected
                if network.is_host:
                    display_name = network.other_player_pos.get("lobby_name") or display_name
                    ready = network.other_player_pos.get("lobby_ready", False)
                else:
                    display_name = names[1] or "P2"
                    ready = local_ready
            else:
                joined = False
                ready = False

            # Slot
            pygame.draw.rect(dm.canvas, (45, 45, 55), slot_rect, border_radius=12)
            pygame.draw.rect(dm.canvas, (90, 90, 90), slot_rect, 2, border_radius=12)

            # Name field
            input_rect = input_rects[idx]
            pygame.draw.rect(dm.canvas, (30, 30, 35), input_rect, border_radius=6)
            pygame.draw.rect(dm.canvas, (150, 150, 150) if active_input == idx else (90, 90, 90), input_rect, 2, border_radius=6)
            name_text = font_input.render(display_name, False, (255, 255, 255))
            dm.canvas.blit(name_text, (input_rect.x + 8, input_rect.y + 6))

            # Profile image
            image = profile_imgs[idx] if joined else profile_desat[idx]
            image_rect = image.get_rect(center=(slot_rect.centerx, slot_rect.y + slot_h // 2 - 10))
            dm.canvas.blit(image, image_rect.topleft)

            # Prêt checkbox
            check_rect = pygame.Rect(slot_rect.right - 32, slot_rect.y + 12, 20, 20)
            pygame.draw.rect(dm.canvas, (60, 60, 60), check_rect, border_radius=4)
            if ready:
                pygame.draw.rect(dm.canvas, (80, 220, 100), check_rect, border_radius=4)
                pygame.draw.line(dm.canvas, (20, 20, 20), (check_rect.x + 5, check_rect.y + 11), (check_rect.x + 9, check_rect.y + 15), 3)
                pygame.draw.line(dm.canvas, (20, 20, 20), (check_rect.x + 9, check_rect.y + 15), (check_rect.x + 15, check_rect.y + 6), 3)

            # Slot label
            label = font_small.render(f"P{idx + 1}", False, (220, 220, 220))
            dm.canvas.blit(label, (slot_rect.x + 16, slot_rect.y + 14))

            # Boutons locaux
            if idx == 0 and network.is_host:
                btn_start.rect.topleft = (slot_rect.centerx - btn_start.rect.width // 2, slot_rect.bottom - 60)
                btn_start.text = t("button_start")
                if not joined or not ready or not network.connected or not network.other_player_pos.get("lobby_ready", False):
                    btn_start.color = (80, 80, 80)
                    btn_start.hover_color = (100, 100, 100)
                else:
                    btn_start.color = (70, 130, 70)
                    btn_start.hover_color = (90, 170, 90)
                btn_start.draw(dm.canvas)

            if idx == 1 and not network.is_host:
                btn_ready.rect.topleft = (slot_rect.centerx - btn_ready.rect.width // 2, slot_rect.bottom - 54)
                btn_ready.text = t("button_ready") if local_ready else t("button_wait")
                btn_ready.color = (70, 130, 70) if local_ready else (120, 120, 120)
                btn_ready.hover_color = (90, 170, 90) if local_ready else (140, 140, 140)
                btn_ready.draw(dm.canvas)

        status_text = t("status_host_waiting") if network.is_host and not network.other_player_pos.get("lobby_ready") else ""
        if status_text:
            dm.canvas.blit(font_body.render(status_text, False, (200, 200, 200)), (start_x, 160))

        btn_back.draw(dm.canvas)
        dm.canvas.blit(font_body.render(t("lobby_slot_note"), False, (180, 180, 180)), (start_x, 140))

        dm.render()
        clock.tick(60)
