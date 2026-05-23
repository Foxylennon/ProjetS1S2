import pygame
from entities.Player import Player
from entities.Room import Room


class Map:
    def __init__(self, width_rooms, height_rooms):
        self.width_rooms = width_rooms
        self.height_rooms = height_rooms
        self.grid = []
        self.current_room_coords = (0, 0)

    def create_map(self):
        self.grid = [[None for _ in range(self.width_rooms)] for _ in range(self.height_rooms)]
        
        for y in range(self.height_rooms):
            for x in range(self.width_rooms):
                door_flags = {
                    "top": y > 0,
                    "bottom": y < self.height_rooms - 1,
                    "left": x > 0,
                    "right": x < self.width_rooms - 1
                }
                is_start = (x == 0 and y == 0)
                is_shop = (x == 1 and y == 1)
                self.grid[y][x] = Room(x, y, door_flags, is_start_room=is_start, is_shop=is_shop)
                
        self.current_room_coords = (0, 0)
        # On entre dans la première salle
        self.get_current_room().on_enter()
        return self.grid

    def get_current_room(self):
        cx, cy = self.current_room_coords
        return self.grid[cy][cx]

    def change_room(self, door, player, game_width, game_height):
        """
        Change le joueur de salle, le repositionne et met à jour la map.
        directions : "haut", "bas", "gauche", "droite".
        """
        old_x, old_y = self.current_room_coords
        new_x, new_y = old_x, old_y
        offset = 60  # Distance pour s'éloigner de la porte et éviter la boucle infinie

        if door.direction == "haut":
            new_y -= 1
            player.y = game_height - player.rect.height - offset
        elif door.direction == "bas":
            new_y += 1
            player.y = offset
        elif door.direction == "gauche":
            new_x -= 1
            player.x = game_width - player.rect.width - offset
        elif door.direction == "droite":
            new_x += 1
            player.x = offset

        player.rect.x = int(player.x)
        player.rect.y = int(player.y)

        self.current_room_coords = (new_x, new_y)
        new_room = self.get_current_room()
        new_room.on_enter()

        print(f"Transition vers la salle : {self.current_room_coords}")

