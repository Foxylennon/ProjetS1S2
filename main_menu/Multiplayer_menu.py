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
    font_big = pygame.font.SysFont(None, 24)
    font_medium = pygame.font.SysFont(None, 18)
    font_small = pygame.font.SysFont(None, 14)
    
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
    btn_host = pygame.Rect(110, 50, 100, 25)
    btn_join = pygame.Rect(110, 120, 100, 25)
    btn_back = pygame.Rect(10, 155, 60, 20)
    input_rect = pygame.Rect(60, 95, 200, 18)
    
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
                        # Ajouter le caractère (seulement chiffres et points)
                        char = event.unicode
                        if char.isdigit() or char == '.':
                            ip_input += char
            
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()
            
            # Clics souris
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Convertir position souris
                mouse_pos = dm.get_mouse()
                
                # Clic sur le champ IP
                if input_rect.collidepoint(mouse_pos):
                    ip_active = True
                else:
                    ip_active = False
                
                # Clic sur "Créer partie" (HOST)
                if btn_host.collidepoint(mouse_pos) and not waiting_for_client and not connecting:
                    waiting_for_client = True
                    connection_result["done"] = False
                    connection_result["success"] = False
                    error_message = ""
                    
                    # Lancer le thread
                    network_thread = threading.Thread(target=host_thread_func)
                    network_thread.daemon = True
                    network_thread.start()
                
                # Clic sur "Rejoindre" (CLIENT)
                if btn_join.collidepoint(mouse_pos) and not waiting_for_client and not connecting:
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
                if btn_back.collidepoint(mouse_pos):
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
        dm.canvas.blit(title, (110, 10))
        
        # --- Section HOST ---
        host_label = font_medium.render("Créer une partie :", False, (200, 200, 200))
        dm.canvas.blit(host_label, (10, 38))
        
        # Bouton Host
        btn_host_color = (80, 80, 80) if waiting_for_client else (70, 130, 70)
        pygame.draw.rect(dm.canvas, btn_host_color, btn_host, border_radius=5)
        pygame.draw.rect(dm.canvas, (100, 100, 100), btn_host, 1, border_radius=5)
        
        if waiting_for_client:
            btn_text = font_small.render("En attente...", False, (255, 255, 255))
        else:
            btn_text = font_small.render("Créer partie", False, (255, 255, 255))
        dm.canvas.blit(btn_text, (btn_host.x + 15, btn_host.y + 6))
        
        # Afficher notre IP
        ip_label = font_small.render(f"Votre IP : {my_ip}", False, (150, 150, 150))
        dm.canvas.blit(ip_label, (220, 55))
        
        # --- Section CLIENT ---
        client_label = font_medium.render("Rejoindre :", False, (200, 200, 200))
        dm.canvas.blit(client_label, (10, 80))
        
        # Champ de saisie IP
        input_color = (60, 60, 80) if ip_active else (50, 50, 50)
        pygame.draw.rect(dm.canvas, input_color, input_rect, border_radius=3)
        pygame.draw.rect(dm.canvas, (100, 100, 100) if ip_active else (70, 70, 70), input_rect, 1, border_radius=3)
        
        ip_text = font_small.render(ip_input, False, (255, 255, 255))
        dm.canvas.blit(ip_text, (input_rect.x + 5, input_rect.y + 4))
        
        ip_hint = font_small.render("IP du Host :", False, (150, 150, 150))
        dm.canvas.blit(ip_hint, (10, 98))
        
        # Bouton Rejoindre
        btn_join_color = (80, 80, 80) if connecting else (70, 70, 130)
        pygame.draw.rect(dm.canvas, btn_join_color, btn_join, border_radius=5)
        pygame.draw.rect(dm.canvas, (100, 100, 100), btn_join, 1, border_radius=5)
        
        if connecting:
            join_text = font_small.render("Connexion...", False, (255, 255, 255))
        else:
            join_text = font_small.render("Rejoindre", False, (255, 255, 255))
        dm.canvas.blit(join_text, (btn_join.x + 20, btn_join.y + 6))
        
        # --- Message d'erreur ---
        if error_message:
            err_text = font_small.render(error_message, False, (255, 100, 100))
            dm.canvas.blit(err_text, (110, 145))
        
        # --- Bouton Retour ---
        pygame.draw.rect(dm.canvas, (60, 60, 60), btn_back, border_radius=3)
        back_text = font_small.render("Retour", False, (200, 200, 200))
        dm.canvas.blit(back_text, (btn_back.x + 10, btn_back.y + 5))
        
        # --- Instructions ---
        instr = font_small.render("ESC = Annuler/Retour", False, (100, 100, 100))
        dm.canvas.blit(instr, (200, 165))
        
        # --- Rendu ---
        dm.render()
        clock.tick(60)
    
    return "menu"
