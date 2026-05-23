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
        
        # Position reconstruite de l'autre joueur et informations de lobby
        self.other_player_pos = {
            "x": 100,
            "y": 100,
            "lobby_ready": False,
            "lobby_name": "",
            "start_game": False,
        }
        
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
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.bind(("", PORT))
        self.socket.listen(1)
        
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"[HOST] Serveur démarré sur {local_ip}:{PORT}")
        print("[HOST] En attente d'un joueur...")
        
        self.client_socket, client_address = self.socket.accept()
        self.client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
                self.other_player_pos.update({
                    "x": x,
                    "y": y,
                    "player_health": hp,
                    "player_attack": attack,
                })
            elif packet_type == 2:
                # [Host -> Client] format: header(1) + x(f) + y(f) + hp(f) + other_hp(f) + vic(?) + num_enemies(B) + room_x(B) + room_y(B) = 21 bytes
                _, x, y, hp, other_hp, vic, num_enemies, room_x, room_y = struct.unpack('!Bffff?BBB', payload[:21])
                
                enemies = []
                offset = 21
                for _ in range(num_enemies):
                    ex, ey, ehp, etype_id = struct.unpack('!fffB', payload[offset:offset+13])
                    enemy_type = {1: "tumor", 2: "bacteria", 3: "virus", 4: "caillot"}.get(etype_id, "tumor")
                    enemies.append({"x": ex, "y": ey, "health": ehp, "type": enemy_type})
                    offset += 13
                    
                self.other_player_pos.update({
                    "x": x,
                    "y": y,
                    "player_health": hp,
                    "other_player_health": other_hp,
                    "victory": vic,
                    "enemies": enemies,
                    "room_x": room_x,
                    "room_y": room_y,
                })
            elif packet_type == 3:
                # [Lobby] header(1) + ready(?) + name_len(B) + name bytes
                if len(payload) >= 3:
                    _, ready, name_len = struct.unpack('!B?B', payload[:3])
                    name_bytes = payload[3:3+name_len]
                    name = name_bytes.decode('utf-8', errors='ignore') if name_bytes else ""
                    self.other_player_pos.update({
                        "lobby_ready": ready,
                        "lobby_name": name,
                    })
            elif packet_type == 5:
                # [Lobby] Host démarre la partie
                self.other_player_pos["start_game"] = True
        except Exception as e:
            print(f"[NETWORK] Payload parse error: {e}")

    # =========================================================================
    #                       ENVOI DE DONNÉES
    # =========================================================================
    def send_position(self, x, y, player_health=100.0, enemies=None, other_player_health=100.0, player_attack=False, victory=False, room_x=0, room_y=0):
        if not self.connected:
            return
            
        try:
            if self.is_host:
                # Packet Type 2
                victory = bool(victory) if victory is not None else False
                num_e = len(enemies) if enemies else 0
                payload = struct.pack('!Bffff?BBB', 2, float(x), float(y), float(player_health), float(other_player_health), victory, num_e, int(room_x), int(room_y))
                
                if enemies:
                    for e in enemies:
                        type_id = {"tumor": 1, "bacteria": 2, "virus": 3, "caillot": 4}.get(e.get('type', 'tumor'), 1)
                        payload += struct.pack('!fffB', float(e['x']), float(e['y']), float(e['health']), type_id)
                
                packet_len = len(payload)
                message = struct.pack('!H', packet_len) + payload
                self.client_socket.sendall(message)
                
            else:
                # Packet Type 1
                payload = struct.pack('!Bfff?', 1, float(x), float(y), float(player_health), bool(player_attack))
                packet_len = len(payload)
                message = struct.pack('!H', packet_len) + payload
                self.socket.sendall(message)
                
        except Exception as e:
            print(f"[NETWORK] Erreur envoi: {e}")
            self.connected = False

    def send_lobby_status(self, ready: bool, name: str = ""):
        if not self.connected:
            return
        if name is None:
            name = ""
        name_bytes = name.encode('utf-8')[:255]
        payload = struct.pack('!B?B', 3, bool(ready), len(name_bytes)) + name_bytes
        packet_len = len(payload)
        message = struct.pack('!H', packet_len) + payload
        try:
            if self.is_host and self.client_socket:
                self.client_socket.sendall(message)
            elif not self.is_host and self.socket:
                self.socket.sendall(message)
        except Exception as e:
            print(f"[NETWORK] Erreur envoi lobby status: {e}")
            self.connected = False

    def send_start_game(self):
        if not self.connected:
            return
        payload = struct.pack('!B', 5)
        packet_len = len(payload)
        message = struct.pack('!H', packet_len) + payload
        try:
            if self.is_host and self.client_socket:
                self.client_socket.sendall(message)
            elif not self.is_host and self.socket:
                self.socket.sendall(message)
        except Exception as e:
            print(f"[NETWORK] Erreur envoi start game: {e}")
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
