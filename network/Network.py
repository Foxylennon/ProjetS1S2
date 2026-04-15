import socket
import threading
import struct

PORT = 5555

class Network:
    """
    Classe réseau multijoueur améliorée utilisant un protocole binaire (struct)
    au lieu de JSON sur TCP, pour des performances et empreinte mémoire optimales.
    """
    def __init__(self):
        self.socket = None
        self.client_socket = None
        self.is_host = False
        self.connected = False
        
        # Position reconstruite de l'autre joueur
        self.other_player_pos = {"x": 100, "y": 100}
        
        self.receive_thread = None
        self._recv_buffer = b""  # Tampon binaire
        self.running = False
    
    # =========================================================================
    #                           MODE HOST (SERVEUR)
    # =========================================================================
    def start_host(self):
        print("[HOST] Démarrage du serveur binaire...")
        self.is_host = True
        self.running = True
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", PORT))
        self.socket.listen(1)
        
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"[HOST] Serveur démarré sur {local_ip}:{PORT}")
        print("[HOST] En attente d'un joueur...")
        
        self.client_socket, client_address = self.socket.accept()
        print(f"[HOST] Joueur connecté depuis {client_address}")
        self.connected = True
        
        self.receive_thread = threading.Thread(target=self._receive_loop_host)
        self.receive_thread.daemon = True
        self.receive_thread.start()
        
        return True
        
    def _receive_loop_host(self):
        while self.running and self.connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    print("[HOST] Client déconnecté")
                    self.connected = False
                    break
                self._recv_buffer += data
                self._process_buffer()
            except Exception as e:
                print(f"[HOST] Erreur réception: {e}")
                self.connected = False
                break

    # =========================================================================
    #                           MODE CLIENT
    # =========================================================================
    def connect_to_host(self, host_ip):
        print(f"[CLIENT] Connexion à {host_ip}:{PORT}...")
        self.is_host = False
        self.running = True
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        
        try:
            self.socket.connect((host_ip, PORT))
            print("[CLIENT] Connecté au serveur!")
            self.connected = True
            self.socket.settimeout(None)
            
            self.receive_thread = threading.Thread(target=self._receive_loop_client)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            return True
        except socket.timeout:
            print("[CLIENT] Timeout")
            return False
        except ConnectionRefusedError:
            print("[CLIENT] Connexion refusée")
            return False
        except Exception as e:
            print(f"[CLIENT] Erreur: {e}")
            return False

    def _receive_loop_client(self):
        while self.running and self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    print("[CLIENT] Déconnecté du serveur")
                    self.connected = False
                    break
                self._recv_buffer += data
                self._process_buffer()
            except Exception as e:
                print(f"[CLIENT] Erreur réception: {e}")
                self.connected = False
                break

    # =========================================================================
    #                 PROCESSING BINAIRE DES PAQUETS
    # =========================================================================
    def _process_buffer(self):
        """Découpe le flux TCP en paquets en utilisant la taille (2 bytes) d'en-tête."""
        while len(self._recv_buffer) >= 2:
            packet_len = struct.unpack('!H', self._recv_buffer[:2])[0]
            if len(self._recv_buffer) < 2 + packet_len:
                break # Le paquet n'est pas complètement arrivé, on attend
            
            payload = self._recv_buffer[2:2+packet_len]
            self._recv_buffer = self._recv_buffer[2+packet_len:]
            self._handle_payload(payload)

    def _handle_payload(self, payload):
        """Traduit la donnée binaire en dictionnaire (reconstruction performante)."""
        if not payload:
            return
            
        packet_type = payload[0]
        try:
            if packet_type == 1:
                # [Client -> Host] format: header(1) + x(f) + y(f) + hp(f) + a_attaque(?) = 14 bytes
                _, x, y, hp, attack = struct.unpack('!Bfff?', payload)
                self.other_player_pos = {
                    "x": x, "y": y,
                    "player_health": hp,
                    "player_attack": attack
                }
            elif packet_type == 2:
                # [Host -> Client] format: header(1) + x(f) + y(f) + hp(f) + other_hp(f) + vic(?) + num_enemies(B) = 19 bytes
                _, x, y, hp, other_hp, vic, num_enemies = struct.unpack('!Bffff?B', payload[:19])
                
                enemies = []
                offset = 19
                for _ in range(num_enemies):
                    ex, ey, ehp = struct.unpack('!fff', payload[offset:offset+12])
                    enemies.append({"x": ex, "y": ey, "health": ehp})
                    offset += 12
                    
                self.other_player_pos = {
                    "x": x, "y": y,
                    "player_health": hp,
                    "other_player_health": other_hp,
                    "victory": vic,
                    "enemies": enemies
                }
        except Exception as e:
            print(f"[NETWORK] Payload parse error: {e}")

    # =========================================================================
    #                       ENVOI DE DONNÉES
    # =========================================================================
    def send_position(self, x, y, player_health=100.0, enemies=None, other_player_health=100.0, player_attack=False, victory=False):
        if not self.connected:
            return
            
        try:
            if self.is_host:
                # Packet Type 2
                victory = bool(victory) if victory is not None else False
                num_e = len(enemies) if enemies else 0
                payload = struct.pack('!Bffff?B', 2, float(x), float(y), float(player_health), float(other_player_health), victory, num_e)
                
                if enemies:
                    for e in enemies:
                        payload += struct.pack('!fff', float(e['x']), float(e['y']), float(e['health']))
                
                packet_len = len(payload)
                message = struct.pack('!H', packet_len) + payload
                self.client_socket.send(message)
                
            else:
                # Packet Type 1
                payload = struct.pack('!Bfff?', 1, float(x), float(y), float(player_health), bool(player_attack))
                packet_len = len(payload)
                message = struct.pack('!H', packet_len) + payload
                self.socket.send(message)
                
        except Exception as e:
            print(f"[NETWORK] Erreur envoi: {e}")
            self.connected = False
            
    def get_other_player_pos(self):
        return self.other_player_pos
        
    def close(self):
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
