import pygame


class Door:
    """Un mur simple qui bloque le passage."""

    def __init__(self, x, y, width, height, direction:str, color=(120, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.direction = direction

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)

    def check_collision(self, player):
        """Si collision alors appeller change_room"""
        pass
