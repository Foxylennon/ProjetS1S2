"""
=============================================================================
                        CLASSE MUR (WALL)
=============================================================================

Un mur = un rectangle qui bloque le passage.

"""

import pygame


class Wall:
    """Un mur simple qui bloque le passage."""
    
    def __init__(self, x, y, width, height, color=(80, 80, 80)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)


def create_level_walls():
    """Crée les murs du niveau."""
    walls = []
    
    # --- BORDURES DE L'ÉCRAN ---
    # Mur du HAUT
    walls.append(Wall(0, 0, 320, 8))
    
    # Mur du BAS
    walls.append(Wall(0, 172, 320, 8))
    
    # Mur de GAUCHE
    walls.append(Wall(0, 0, 8, 180))
    
    # Mur de DROITE
    walls.append(Wall(312, 0, 8, 180))
    
    # --- OBSTACLES AU MILIEU ---
    # Obstacle horizontal au centre
    walls.append(Wall(100, 85, 120, 10, color=(100, 70, 70)))
    
    # Petit bloc en bas à droite (PAS en haut à gauche pour pas bloquer le spawn)
    walls.append(Wall(250, 130, 30, 30, color=(100, 70, 70)))
    
    return walls


def check_wall_collision(entity_rect, walls, dx, dy):
    """
    Vérifie si un déplacement cause une collision.
    Retourne le déplacement corrigé.
    """
    new_dx = dx
    new_dy = dy
    
    # Test horizontal (X)
    if dx != 0:
        test_rect = entity_rect.copy()
        test_rect.x += dx
        for wall in walls:
            if test_rect.colliderect(wall.rect):
                new_dx = 0
                break
    
    # Test vertical (Y)
    if dy != 0:
        test_rect = entity_rect.copy()
        test_rect.y += dy
        for wall in walls:
            if test_rect.colliderect(wall.rect):
                new_dy = 0
                break
    
    return new_dx, new_dy
