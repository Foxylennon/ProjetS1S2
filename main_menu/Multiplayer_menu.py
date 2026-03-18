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
from main_menu.Main_menu import Button

FONT_PATH = "assets/fonts/PressStart2P-Regular.ttf"

def load_font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont(None, size)


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
    
    # Récupérer notre IP pour l'afficher
    try:
        hostname = socket.gethostname()
        my_ip = socket.gethostbyname(hostname)
    except:
        my_ip = "???.???.???.???"
    
    # Champ de saisie pour l'IP (pour le client)
    ip_input = "192.168.1."  # Valeur par défaut
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
    btn_host = Button(btn_x, 240, btn_width, btn_height, "Créer partie", color=(70, 130, 70), hover_color=(90, 170, 90))
    btn_join = Button(btn_x, 480, btn_width, btn_height, "Rejoindre", color=(70, 70, 130), hover_color=(100, 100, 170))
    btn_back = Button(50, 600, btn_width // 2, int(btn_height // 1.5), "Retour", color=(60, 60, 60), hover_color=(90, 90, 90))
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
                
                # Saisie de l'IP
                if ip_active and not waiting_for_client and not connecting:
                    if event.key == pygame.K_BACKSPACE:
                        ip_input = ip_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        # Lancer la connexion
                        pass
                    else:
                        char = event.unicode
                        if len(char) == 1 and (char.isdigit() or char == '.'):
                            ip_input += char

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
                    
                    # Lancer le thread
                    network_thread = threading.Thread(target=host_thread_func)
                    network_thread.daemon = True
                    network_thread.start()
                
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
                        error_message = "Entrez une IP valide!"
                
                # Clic sur "Retour"
                if btn_back.is_clicked(mouse_pos, True):
                    network.close()
                    return "menu"
        
        # ---------------------------------------------------------------------
        #                    VÉRIFICATION DU THREAD RÉSEAU
        # ---------------------------------------------------------------------
        
        if connection_result["done"]:
            if connection_result["success"]:
                # Connexion réussie ! Lancer le jeu
                return "game_multi"
            else:
                # Échec
                if waiting_for_client:
                    error_message = "Erreur serveur"
                else:
                    error_message = "Connexion échouée"
                waiting_for_client = False
                connecting = False
            connection_result["done"] = False
        
        # ---------------------------------------------------------------------
        #                    AFFICHAGE
        # ---------------------------------------------------------------------
        
        dm.canvas.fill((40, 40, 40))
        
        # --- Titre ---
        title = font_big.render("MULTIJOUEUR", False, (255, 255, 255))
        dm.canvas.blit(title, (btn_x, 60))
        
        # --- Section HOST ---
        
        # Bouton Host
        btn_host.text = "En attente..." if waiting_for_client else "Créer partie"
        btn_host.color = (80, 80, 80) if waiting_for_client else (70, 130, 70)
        btn_host.hover_color = (120, 120, 120) if waiting_for_client else (90, 170, 90)
        btn_host.draw(dm.canvas, font_small)
        
        # Afficher notre IP
        ip_label = font_small.render(f"Votre IP : {my_ip}", False, (150, 150, 150))
        dm.canvas.blit(ip_label, (btn_x + 480, 250))
        
        # --- Section CLIENT ---
        
        # Champ de saisie IP
        input_color = (60, 60, 80) if ip_active else (50, 50, 50)
        pygame.draw.rect(dm.canvas, input_color, input_rect, border_radius=3)
        pygame.draw.rect(dm.canvas, (100, 100, 100) if ip_active else (70, 70, 70), input_rect, 1, border_radius=3)
        
        ip_text = font_small.render(ip_input, False, (255, 255, 255))
        dm.canvas.blit(ip_text, (input_rect.x + 5, input_rect.y + 4))
        
        ip_hint = font_small.render("IP du Host :", False, (150, 150, 150))
        dm.canvas.blit(ip_hint, (btn_x - 245, 365))
        
        # Bouton Rejoindre
        btn_join.text = "Connexion..." if connecting else "Rejoindre"
        btn_join.color = (80, 80, 80) if connecting else (70, 70, 130)
        btn_join.hover_color = (120, 120, 120) if connecting else (100, 100, 170)
        btn_join.draw(dm.canvas, font_small)
        
        # --- Message d'erreur ---
        if error_message:
            err_text = font_small.render(error_message, False, (255, 100, 100))
            dm.canvas.blit(err_text, (btn_x, 365))
        
        # --- Bouton Retour ---
        btn_back.draw(dm.canvas, font_small)
        
        # --- Instructions ---
        instr = font_small.render("ESC = Annuler/Retour", False, (100, 100, 100))
        dm.canvas.blit(instr, (600, 1000))
        
        # --- Rendu ---
        dm.render()
        clock.tick(60)
    
    return "menu"
