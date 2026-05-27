import pygame
import os
import random

class MusicManager:
    STATE_NONE = 0
    STATE_MENU = 1
    STATE_GAME = 2
    STATE_SHOP = 3

    def __init__(self):
        self.current_state = self.STATE_NONE
        self.current_track = None
        
        # Audio paths
        self.menu_track = "assets/music/Project_8.mp3"
        self.shop_track = "assets/music/Project_22.mp3"
        self.game_tracks = [
            "assets/music/Project_12_best_ver_2.mp3",
            "assets/music/Project_19.mp3",
            "assets/music/Project_20.mp3"
        ]
        
        # SFX paths
        self.sword_path = "assets/effects/musicholder-sword-sound-260274.mp3"
        self.dash_path = "assets/effects/freesound_community-kung-fu-punch-4-105262.mp3"
        self.buy_path = "assets/effects/u_byub5wd934-cashier-quotka-chingquot-sound-effect-129698.mp3"
        self.hover_path = "assets/effects/universfield-happy-message-ping-351298_firstpingonly.mp3"
        self.click_path = "assets/effects/universfield-happy-message-ping-351298.mp3"
        self.run_path = "assets/effects/blendertimer-person-running-loop-245173.mp3"
        
        self.game_playlist = []
        self.playlist_index = 0
        
        # Sound objects
        self.sound_sword = None
        self.sound_dash = None
        self.sound_buy = None
        self.sound_hover = None
        self.sound_click = None
        self.sound_run = None
        
        # Channels
        self.run_channel = None
        
        # Check if pygame mixer is initialized
        if not pygame.mixer.get_init():
            try:
                # Initialize with standard settings (44100Hz, 16-bit, stereo, 2048 buffer)
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
            except Exception as e:
                print(f"[MusicManager] Failed to initialize mixer: {e}")
                
        self._load_sounds()

    def _load_sounds(self):
        if not pygame.mixer.get_init():
            return
            
        try:
            self.sound_sword = pygame.mixer.Sound(os.path.normpath(self.sword_path))
            self.sound_dash = pygame.mixer.Sound(os.path.normpath(self.dash_path))
            self.sound_buy = pygame.mixer.Sound(os.path.normpath(self.buy_path))
            self.sound_hover = pygame.mixer.Sound(os.path.normpath(self.hover_path))
            self.sound_click = pygame.mixer.Sound(os.path.normpath(self.click_path))
            self.sound_run = pygame.mixer.Sound(os.path.normpath(self.run_path))
            
            # Adjust volume levels for comfortable balance
            self.sound_sword.set_volume(0.5)
            self.sound_dash.set_volume(0.6)
            self.sound_buy.set_volume(0.6)
            self.sound_hover.set_volume(0.4)
            self.sound_click.set_volume(0.5)
            self.sound_run.set_volume(0.3)
        except Exception as e:
            print(f"[MusicManager] Error loading sound effects: {e}")

    def play_menu(self):
        """Starts playing the menu music if not already playing."""
        self.stop_run()
        if self.current_state == self.STATE_MENU:
            return
            
        print("[MusicManager] Switching to menu music")
        self.current_state = self.STATE_MENU
        self.current_track = self.menu_track
        self._play_track(self.menu_track, loops=-1, fade_ms=1000)

    def play_shop(self):
        """Starts playing the shop music if not already playing."""
        self.stop_run()
        if self.current_state == self.STATE_SHOP:
            return
            
        print("[MusicManager] Switching to shop music")
        self.current_state = self.STATE_SHOP
        self.current_track = self.shop_track
        self._play_track(self.shop_track, loops=-1, fade_ms=500)

    def play_game(self, force_restart=False):
        """Starts playing the gameplay music playlist."""
        if self.current_state == self.STATE_GAME and not force_restart:
            return
            
        self.stop_run()
        print("[MusicManager] Switching to game music")
        self.current_state = self.STATE_GAME
        
        if not self.game_playlist or force_restart:
            self.game_playlist = self.game_tracks.copy()
            random.shuffle(self.game_playlist)
            self.playlist_index = 0
            
        self._play_next_game_track(fade_ms=1000)

    def _play_next_game_track(self, fade_ms=1000):
        if not self.game_playlist:
            return
            
        track = self.game_playlist[self.playlist_index]
        print(f"[MusicManager] Playing game track: {track}")
        self.current_track = track
        self._play_track(track, loops=0, fade_ms=fade_ms)
        
        # Advance index for the next song
        self.playlist_index = (self.playlist_index + 1) % len(self.game_playlist)

    def _play_track(self, track_path, loops=0, fade_ms=0):
        if not pygame.mixer.get_init():
            return
            
        # Standardize path slashes for Windows/cross-platform safety
        normalized_path = os.path.normpath(track_path)
        if not os.path.exists(normalized_path):
            print(f"[MusicManager] Error: File not found at {normalized_path}")
            return
            
        try:
            pygame.mixer.music.fadeout(fade_ms) if fade_ms > 0 else pygame.mixer.music.stop()
            pygame.mixer.music.load(normalized_path)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
        except Exception as e:
            print(f"[MusicManager] Error playing track {normalized_path}: {e}")

    # --- Sound Effects API ---
    
    def play_sword(self):
        if not pygame.mixer.get_init():
            return
        if self.sound_sword:
            try:
                self.sound_sword.play()
            except Exception as e:
                print(f"[MusicManager] Error playing sword sound: {e}")

    def play_dash(self):
        if not pygame.mixer.get_init():
            return
        if self.sound_dash:
            try:
                self.sound_dash.play()
            except Exception as e:
                print(f"[MusicManager] Error playing dash sound: {e}")

    def play_buy(self):
        if not pygame.mixer.get_init():
            return
        if self.sound_buy:
            try:
                self.sound_buy.play()
            except Exception as e:
                print(f"[MusicManager] Error playing purchase sound: {e}")

    def play_hover(self):
        if not pygame.mixer.get_init():
            return
        if self.sound_hover:
            try:
                self.sound_hover.play()
            except Exception as e:
                print(f"[MusicManager] Error playing hover sound: {e}")

    def play_click(self):
        if not pygame.mixer.get_init():
            return
        if self.sound_click:
            try:
                self.sound_click.play()
            except Exception as e:
                print(f"[MusicManager] Error playing click sound: {e}")

    def start_run(self):
        if not pygame.mixer.get_init():
            return
        if not self.sound_run:
            return
            
        # Already playing running sound
        if self.run_channel is not None and self.run_channel.get_busy():
            return
            
        try:
            # Play loop infinitely
            self.run_channel = self.sound_run.play(loops=-1)
        except Exception as e:
            print(f"[MusicManager] Error starting running loop: {e}")

    def stop_run(self):
        if not pygame.mixer.get_init():
            return
        if self.run_channel is not None:
            try:
                self.run_channel.stop()
            except Exception as e:
                print(f"[MusicManager] Error stopping running loop: {e}")
            self.run_channel = None

    def update(self):
        """Checks if a track has finished and advances gameplay playlist if needed."""
        if not pygame.mixer.get_init():
            return
            
        # In STATE_GAME, check if the music has stopped playing to load the next track
        if self.current_state == self.STATE_GAME:
            if not pygame.mixer.music.get_busy():
                print("[MusicManager] Track finished. Playing next game track.")
                self._play_next_game_track(fade_ms=1000)

    def stop(self, fade_ms=500):
        if not pygame.mixer.get_init():
            return
        self.stop_run()
        pygame.mixer.music.fadeout(fade_ms)
        self.current_state = self.STATE_NONE
        self.current_track = None

# Global singleton instance
music_manager = MusicManager()
