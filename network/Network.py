"""
=============================================================================
                        MODULE RÉSEAU - MULTIJOUEUR
=============================================================================

CE FICHIER CONTIENT TOUTE LA LOGIQUE RÉSEAU DU JEU.

VOCABULAIRE IMPORTANT :
-----------------------
- Socket : Une "prise" virtuelle qui permet à deux programmes de communiquer
- Host   : Le joueur qui CRÉE la partie (il fait office de serveur)
- Client : Le joueur qui REJOINT la partie
- TCP    : Protocole de communication fiable (les messages arrivent dans l'ordre)
- Port   : Un numéro (comme un numéro de porte) pour identifier la connexion

COMMENT ÇA MARCHE :
-------------------
1. Le Host crée un socket serveur et attend une connexion
2. Le Client crée un socket et se connecte au Host
3. Une fois connectés, ils s'envoient leurs positions en JSON
4. Un thread séparé reçoit les données pour ne pas bloquer le jeu

"""

import socket
import threading
import json

# Port utilisé pour la connexion (peut être n'importe quel nombre entre 1024 et 65535)
PORT = 5555


class Network:
    """
    Classe qui gère TOUTE la communication réseau.
    
    Elle peut fonctionner en mode HOST (serveur) ou CLIENT.
    """
    
    def __init__(self):
        # Le socket principal pour communiquer
        self.socket = None
        
        # Socket du client connecté (uniquement pour le Host)
        self.client_socket = None
        
        # Est-ce qu'on est le Host ?
        self.is_host = False
        
        # Est-ce qu'on est connecté ?
        self.connected = False
        
        # Position de l'autre joueur (reçue par le réseau)
        # On stocke ça ici pour que le jeu puisse y accéder
        self.other_player_pos = {"x": 100, "y": 100}
        
        # Thread pour recevoir les données en arrière-plan
        self.receive_thread = None
        
        # Tampon pour assembler les messages TCP reçus (par ligne)
        self._recv_buffer = ""
        
        # Variable pour arrêter proprement le thread
        self.running = False
    
    # =========================================================================
    #                           MODE HOST (SERVEUR)
    # =========================================================================
    
    def start_host(self):
        """
        Démarre le serveur et attend qu'un client se connecte.
        
        ÉTAPES :
        1. Créer un socket serveur
        2. Le lier (bind) à une adresse IP et un port
        3. Écouter (listen) les connexions entrantes
        4. Accepter (accept) la connexion d'un client
        """
        print("[HOST] Démarrage du serveur...")
        
        self.is_host = True
        self.running = True
        
        # --- ÉTAPE 1 : Créer le socket ---
        # AF_INET = On utilise IPv4 (adresses comme 192.168.1.1)
        # SOCK_STREAM = On utilise TCP (connexion fiable)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Option pour réutiliser l'adresse immédiatement après fermeture
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # --- ÉTAPE 2 : Lier le socket à une adresse ---
        # "" = Écouter sur toutes les interfaces réseau
        # PORT = Le numéro de port qu'on a choisi (5555)
        self.socket.bind(("", PORT))
        
        # --- ÉTAPE 3 : Écouter les connexions ---
        # Le "1" signifie qu'on accepte 1 connexion en attente maximum
        self.socket.listen(1)
        
        # Récupérer notre adresse IP pour l'afficher
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"[HOST] Serveur démarré sur {local_ip}:{PORT}")
        print("[HOST] En attente d'un joueur...")
        
        # --- ÉTAPE 4 : Attendre et accepter une connexion ---
        # Cette ligne BLOQUE jusqu'à ce qu'un client se connecte
        # Elle retourne : (socket_du_client, adresse_du_client)
        self.client_socket, client_address = self.socket.accept()
        
        print(f"[HOST] Joueur connecté depuis {client_address}")
        self.connected = True
        
        # --- ÉTAPE 5 : Démarrer le thread de réception ---
        self.receive_thread = threading.Thread(target=self._receive_loop_host)
        self.receive_thread.daemon = True  # Le thread s'arrête quand le programme principal s'arrête
        self.receive_thread.start()
        
        return True
    
    def _receive_loop_host(self):
        """
        Boucle qui tourne en arrière-plan pour recevoir les données du client.
        
        C'est un THREAD séparé pour ne pas bloquer le jeu pendant qu'on attend
        des données réseau.
        """
        while self.running and self.connected:
            try:
                # Recevoir jusqu'à 1024 octets de données
                data = self.client_socket.recv(1024)
                
                if not data:
                    # Si on reçoit des données vides, le client s'est déconnecté
                    print("[HOST] Client déconnecté")
                    self.connected = False
                    break
                
                # Décoder les données (bytes → string) et parser ligne par ligne
                message = data.decode('utf-8')
                self._recv_buffer += message
                while "\n" in self._recv_buffer:
                    line, self._recv_buffer = self._recv_buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        self.other_player_pos = json.loads(line)
                    except Exception as e:
                        print(f"[HOST] JSON parse error: {e} - line={line}")
                
            except Exception as e:
                print(f"[HOST] Erreur réception: {e}")
                self.connected = False
                break
    
    # =========================================================================
    #                           MODE CLIENT
    # =========================================================================
    
    def connect_to_host(self, host_ip):
        """
        Se connecte au serveur (Host).
        
        PARAMÈTRE :
        - host_ip : L'adresse IP du Host (ex: "192.168.1.42")
        
        ÉTAPES :
        1. Créer un socket client
        2. Se connecter (connect) au serveur
        """
        print(f"[CLIENT] Connexion à {host_ip}:{PORT}...")
        
        self.is_host = False
        self.running = True
        
        # --- ÉTAPE 1 : Créer le socket ---
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Timeout de 5 secondes pour la connexion
        self.socket.settimeout(5)
        
        try:
            # --- ÉTAPE 2 : Se connecter au serveur ---
            self.socket.connect((host_ip, PORT))
            
            print("[CLIENT] Connecté au serveur!")
            self.connected = True
            
            # Enlever le timeout pour les communications normales
            self.socket.settimeout(None)
            
            # --- ÉTAPE 3 : Démarrer le thread de réception ---
            self.receive_thread = threading.Thread(target=self._receive_loop_client)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
            
        except socket.timeout:
            print("[CLIENT] Timeout - Impossible de se connecter")
            return False
        except ConnectionRefusedError:
            print("[CLIENT] Connexion refusée - Vérifiez que le Host est lancé")
            return False
        except Exception as e:
            print(f"[CLIENT] Erreur: {e}")
            return False
    
    def _receive_loop_client(self):
        """
        Boucle de réception pour le client (même principe que pour le Host).
        """
        while self.running and self.connected:
            try:
                data = self.socket.recv(1024)
                
                if not data:
                    print("[CLIENT] Déconnecté du serveur")
                    self.connected = False
                    break
                
                message = data.decode('utf-8')
                self._recv_buffer += message
                while "\n" in self._recv_buffer:
                    line, self._recv_buffer = self._recv_buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        self.other_player_pos = json.loads(line)
                    except Exception as e:
                        print(f"[CLIENT] JSON parse error: {e} - line={line}")
                
            except Exception as e:
                print(f"[CLIENT] Erreur réception: {e}")
                self.connected = False
                break
    
    # =========================================================================
    #                       ENVOI DE DONNÉES
    # =========================================================================
    
    def send_position(self, x, y, player_health=None, enemies=None, other_player_health=None, player_attack=False, victory=None):
        """
        Envoie notre position, santé et données du jeu.
        """
        if not self.connected:
            return
        
        message_data = {"x": x, "y": y}
        if player_health is not None:
            message_data["player_health"] = player_health
        if enemies is not None:
            message_data["enemies"] = enemies
        if other_player_health is not None:
            message_data["other_player_health"] = other_player_health
        if player_attack:
            message_data["player_attack"] = True
        if victory is not None:
            message_data["victory"] = victory
        
        # Créer le message (JSON + délimiteur newline)
        message = json.dumps(message_data) + "\n"
        
        try:
            if self.is_host:
                # Le Host envoie au client_socket
                self.client_socket.send(message.encode('utf-8'))
            else:
                # Le Client envoie via son socket principal
                self.socket.send(message.encode('utf-8'))
                
        except Exception as e:
            print(f"[NETWORK] Erreur envoi: {e}")
            self.connected = False
    
    def get_other_player_pos(self):
        """
        Retourne la dernière position connue de l'autre joueur.
        
        Cette méthode est appelée par le jeu à chaque frame pour savoir
        où dessiner l'autre joueur.
        """
        return self.other_player_pos
    
    # =========================================================================
    #                       FERMETURE PROPRE
    # =========================================================================
    
    def close(self):
        """
        Ferme proprement toutes les connexions.
        
        IMPORTANT : Toujours appeler cette méthode quand on quitte !
        Sinon le port peut rester bloqué pendant quelques minutes.
        """
        print("[NETWORK] Fermeture des connexions...")
        
        self.running = False
        self.connected = False
        
        try:
            if self.client_socket:
                self.client_socket.close()
            if self.socket:
                self.socket.close()
        except:
            pass
        
        print("[NETWORK] Connexions fermées")
