"""
=============================================================================
                        CLASSE MUR (WALL)
=============================================================================

Un mur = un rectangle qui bloque le passage.

"""

import pygame


class Wall:
    """Un mur simple qui bloque le passage."""
    
    def __init__(self, x, y, width, height, color=(80, 80, 80), visible=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.visible = visible
    
    def draw(self, surface):
        if not self.visible:
            return
        pygame.draw.rect(surface, self.color, self.rect)


def create_level_walls():
    """Crée les murs du niveau."""
    walls = []
    
    # --- BORDURES DE L'ÉCRAN ---
    # Mur du HAUT
    walls.append(Wall(0, 0, 1280, 32, visible=False))
    
    # Mur du BAS
    walls.append(Wall(0, 688, 1280, 32, visible=False))
    
    # Mur de GAUCHE
    walls.append(Wall(0, 0, 32, 720, visible=False))
    
    # Mur de DROITE
    walls.append(Wall(1248, 0, 32, 720, visible=False))
    
    # --- OBSTACLES AU MILIEU ---
    # Obstacle horizontal au centre
    walls.append(Wall(440, 300, 200, 60, color=(100, 70, 70)))
    
    # Petit bloc en bas à droite (PAS en haut à gauche pour pas bloquer le spawn)
    walls.append(Wall(1100, 550, 70, 70, color=(100, 70, 70)))
    
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
