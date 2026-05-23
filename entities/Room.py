import pygame
import random
from entities.Wall import Wall
from entities.Door import Door
from entities.Enemy import Enemy
from entities.NPC import NPC

class Room:
    def __init__(self, room_x, room_y, door_flags, is_start_room=False, is_shop=False):
        self.room_x = room_x
        self.room_y = room_y
        self.is_shop = is_shop
        self.is_cleared = is_start_room or is_shop
        self.doors = []
        self.walls = []
        self.enemies = []
        self.npc = None
        self.has_entered = False
        
        self.build_room(door_flags)
        
        if not is_start_room and not is_shop:
            self.spawn_enemies()
            
        if self.is_shop:
            self.npc = NPC(640, 360)

    def build_room(self, door_flags):
        # Dimensions
        screen_w, screen_h = 1280, 720
        wall_thick = 32
        door_size = 120 # Largeur ou hauteur de la porte
        
        # Murs HAUT
        if door_flags.get("top"):
            self.walls.append(Wall(0, 0, (screen_w - door_size) // 2, wall_thick, visible=False))
            self.walls.append(Wall((screen_w + door_size) // 2, 0, (screen_w - door_size) // 2, wall_thick, visible=False))
            self.doors.append(Door((screen_w - door_size) // 2, 0, door_size, wall_thick, "haut"))
        else:
            self.walls.append(Wall(0, 0, screen_w, wall_thick, visible=False))

        # Murs BAS
        if door_flags.get("bottom"):
            self.walls.append(Wall(0, screen_h - wall_thick, (screen_w - door_size) // 2, wall_thick, visible=False))
            self.walls.append(Wall((screen_w + door_size) // 2, screen_h - wall_thick, (screen_w - door_size) // 2, wall_thick, visible=False))
            self.doors.append(Door((screen_w - door_size) // 2, screen_h - wall_thick, door_size, wall_thick, "bas"))
        else:
            self.walls.append(Wall(0, screen_h - wall_thick, screen_w, wall_thick, visible=False))

        # Murs GAUCHE
        if door_flags.get("left"):
            self.walls.append(Wall(0, 0, wall_thick, (screen_h - door_size) // 2, visible=False))
            self.walls.append(Wall(0, (screen_h + door_size) // 2, wall_thick, (screen_h - door_size) // 2, visible=False))
            self.doors.append(Door(0, (screen_h - door_size) // 2, wall_thick, door_size, "gauche"))
        else:
            self.walls.append(Wall(0, 0, wall_thick, screen_h, visible=False))

        # Murs DROITE
        if door_flags.get("right"):
            self.walls.append(Wall(screen_w - wall_thick, 0, wall_thick, (screen_h - door_size) // 2, visible=False))
            self.walls.append(Wall(screen_w - wall_thick, (screen_h + door_size) // 2, wall_thick, (screen_h - door_size) // 2, visible=False))
            self.doors.append(Door(screen_w - wall_thick, (screen_h - door_size) // 2, wall_thick, door_size, "droite"))
        else:
            self.walls.append(Wall(screen_w - wall_thick, 0, wall_thick, screen_h, visible=False))

        # Ajouter des obstacles aléatoires uniquement si ce n'est pas un shop
        if not self.is_shop:
            # Obstacle central
            if random.random() > 0.5:
                self.walls.append(Wall(440, 300, 200, 60, color=(100, 70, 70)))
            if random.random() > 0.5:
                self.walls.append(Wall(1100, 550, 70, 70, color=(100, 70, 70)))
            if random.random() > 0.5:
                self.walls.append(Wall(200, 200, 80, 80, color=(100, 70, 70)))
            
    def spawn_enemies(self):
        MONSTER_TYPES = ["tumor", "bacteria", "virus", "caillot"]
        num_enemies = random.randint(3, 8)
        
        for _ in range(num_enemies):
            spawn_x, spawn_y = self.random_spawn_position()
            self.enemies.append(Enemy(spawn_x, spawn_y, monster_type=random.choice(MONSTER_TYPES)))

    def is_spawn_position_free(self, x, y):
        candidate = pygame.Rect(int(x), int(y), 24, 24)
        return not any(candidate.colliderect(w.rect) for w in self.walls)

    def random_spawn_position(self):
        for _ in range(30):
            spawn_x = random.randint(100, 1180)
            spawn_y = random.randint(100, 620)
            if self.is_spawn_position_free(spawn_x, spawn_y):
                return spawn_x, spawn_y
        return 600, 360

    def update_room(self):
        # Nettoyer les ennemis morts (la suppression est gérée par Game.py généralement, 
        # mais on peut au moins vérifier si tous sont morts)
        alive_enemies = [e for e in self.enemies if e.is_alive() or not e.is_faint_animation_complete()]
        if not alive_enemies and not self.is_cleared:
            self.is_cleared = True
            for door in self.doors:
                door.is_locked = False

    def on_enter(self):
        if not self.has_entered:
            self.has_entered = True
            if self.enemies:
                for door in self.doors:
                    door.is_locked = True
