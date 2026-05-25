import pygame
from lang import t
from ui.UI_utils import load_font

class NPC:
    """PNJ qui permet d'ouvrir le shop."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 40
        self.rect = pygame.Rect(self.x - self.width//2, self.y - self.height//2, self.width, self.height)
        self.color = (50, 200, 255)  # Couleur bleue claire pour se distinguer
        self.font = load_font(18)
        
        try:
            # Le joueur a demandé "crim_idle.png" mais le fichier est "chrom_idle.png"
            raw_img = pygame.image.load("assets/sprites/npc/chrom/chrom_idle.png").convert_alpha()
            # L'image originale fait 400x270. On la redimensionne proportionnellement.
            target_h = 70
            target_w = int(target_h * (raw_img.get_width() / raw_img.get_height()))
            self.image = pygame.transform.smoothscale(raw_img, (target_w, target_h))
        except Exception as e:
            print(f"Erreur chargement image NPC: {e}")
            self.image = None
        
    def draw(self, surface):
        if hasattr(self, 'image') and self.image:
            img_rect = self.image.get_rect(center=self.rect.center)
            surface.blit(self.image, img_rect)
        else:
            # Dessiner le PNJ en placeholder
            pygame.draw.rect(surface, self.color, self.rect)
            
            # Yeux pour lui donner une orientation "vers le bas" (simple détail visuel)
            pygame.draw.rect(surface, (0, 0, 0), (self.rect.x + 8, self.rect.y + 10, 6, 6))
            pygame.draw.rect(surface, (0, 0, 0), (self.rect.x + 26, self.rect.y + 10, 6, 6))

    def draw_interaction_hint(self, surface):
        """Dessine l'indication d'interaction au-dessus du PNJ."""
        text = self.font.render("E : Shop", False, (255, 255, 255))
        bg_rect = text.get_rect(center=(self.x, self.rect.top - 20))
        
        # Fond sombre pour lisibilité
        bg_surface = pygame.Surface((bg_rect.width + 10, bg_rect.height + 6))
        bg_surface.fill((0, 0, 0))
        bg_surface.set_alpha(150)
        surface.blit(bg_surface, (bg_rect.x - 5, bg_rect.y - 3))
        
        surface.blit(text, bg_rect)
        
    def is_near(self, player_rect, max_distance=100):
        """Vérifie si le joueur est assez proche pour interagir."""
        dx = self.x - player_rect.centerx
        dy = self.y - player_rect.centery
        distance_sq = dx*dx + dy*dy
        return distance_sq <= max_distance * max_distance
