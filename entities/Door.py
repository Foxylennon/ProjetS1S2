import pygame


class Door:
    """Une porte qui permet de changer de salle, mais bloque si elle est verrouillée."""

    def __init__(self, x, y, width, height, direction:str, color=(120, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.direction = direction
        self.is_locked = False
        self.open_color = (0, 120, 0) # Vert quand c'est ouvert

    def draw(self, surface):
        color = self.color if self.is_locked else self.open_color
        pygame.draw.rect(surface, color, self.rect)

    def check_collision(self, player):
        """Vérifie la collision. Retourne True si le joueur touche une porte ouverte."""
        if not self.is_locked and self.rect.colliderect(player.rect):
            return True
        return False
