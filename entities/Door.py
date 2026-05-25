import pygame


class Door:
    """Une porte qui permet de changer de salle, mais bloque si elle est verrouillée."""

    def __init__(self, x, y, width, height, direction:str, color=(120, 0, 0)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.direction = direction
        self.is_locked = False
        self.open_color = (0, 120, 0) # Vert quand c'est ouvert
        
        try:
            img = pygame.image.load("assets/ui/play_bg_door.png").convert_alpha()
            # Pivoter l'image pour les portes horizontales (haut/bas)
            if self.direction in ["haut", "bas"]:
                img = pygame.transform.rotate(img, 90)
            self.image = pygame.transform.scale(img, (width, height))
        except Exception as e:
            print(f"Erreur de chargement de l'image de porte: {e}")
            self.image = None

    def draw(self, surface):
        if self.image:
            surface.blit(self.image, self.rect)
            if self.is_locked:
                # Ajoute une teinte rouge semi-transparente si verrouillée
                tint = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                tint.fill((255, 0, 0, 100))
                surface.blit(tint, self.rect.topleft)
        else:
            color = self.color if self.is_locked else self.open_color
            pygame.draw.rect(surface, color, self.rect)

    def check_collision(self, player):
        """Vérifie la collision. Retourne True si le joueur touche une porte ouverte."""
        if not self.is_locked and self.rect.colliderect(player.rect):
            return True
        return False
