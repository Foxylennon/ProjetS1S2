import pygame
from Player import Player



class Map:
    def __init__(self,x,y):
        self.x = x
        self.y = y
        self.matrice = []
        self.current_room_coords = (0,0)

    def create_map(self):
        map_matrice = []
        (x, y) = self.current_room_coords
        for i in range (self.y):
            row = []
            for j in range (self.x):
                row.append(0)
            map_matrice.append(row)
        map_matrice[y][x] = "X"
        self.matrice = map_matrice
        return map_matrice

    def print_map(self):
        for row in self.matrice:
            print(row)

    def change_room(self, door, player, game_width, game_height):
        """
        Change le joueur de salle, le repositionne et met à jour la map.
        directions : "haut", "bas", "gauche", "droite".
        """
        # 1. On efface l'ancienne position du joueur sur la mini-map
        old_x, old_y = self.current_room_coords
        self.matrice[old_y][old_x] = 0

        # 2. Mettre à jour les coordonnées de la salle (Map)
        new_x, new_y = old_x, old_y
        offset = 60  # Distance pour s'éloigner de la porte et éviter la boucle infinie

        if door.direction == "haut":
            new_y -= 1  # On monte dans la matrice
            # Le joueur apparaît en bas de l'écran
            player.y = game_height - player.height - offset

        elif door.direction == "bas":
            new_y += 1  # On descend dans la matrice
            # Le joueur apparaît en haut de l'écran
            player.y = offset

        elif door.direction == "gauche":
            new_x -= 1  # On va à gauche dans la matrice
            # Le joueur apparaît à droite de l'écran
            player.x = game_width - player.width - offset

        elif door.direction == "droite":
            new_x += 1  # On va à droite dans la matrice
            # Le joueur apparaît à gauche de l'écran
            player.x = offset

            # 3. Synchroniser les coordonnées réelles du joueur et son rect
        player.rect.x = int(player.x)
        player.rect.y = int(player.y)

        # 4. Enregistrer la nouvelle salle et mettre à jour la matrice
        self.current_room_coords = (new_x, new_y)
        self.matrice[new_y][new_x] = "X"

        print(f"Transition vers la salle : {self.current_room_coords}")


Map = Map(3,3)
Map.create_map()
Map.print_map()

