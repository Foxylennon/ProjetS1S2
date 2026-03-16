"""
CLASSE JOUEUR - SIMPLIFIÉ
"""

import pygame
from entities.Wall import check_wall_collision


class Player:
    def __init__(self, x, y, width=16, height=16):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        
        self.speed = 2
        self.health = 100
        self.max_health = 100
        
        # Attaque
        self.attack_damage = 34
        self.attack_range = 20
        self.attacking = False
        self.attack_cooldown = 0
        self.attack_duration = 0
        self.attack_rect = None
        self.direction = 0  # 0=droite, 1=gauche, 2=bas, 3=haut
        
        self.color = (255, 255, 0)
    
    def handle_input(self, keys, walls=None):
        """Gère le déplacement du joueur."""
        dx = 0
        dy = 0
        
        # DROITE (flèche droite OU D OU touche D azerty)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = self.speed
            self.direction = 0
        
        # GAUCHE (flèche gauche OU A OU Q azerty)
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]:
            dx = -self.speed
            self.direction = 1
        
        # BAS (flèche bas OU S)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = self.speed
            self.direction = 2
        
        # HAUT (flèche haut OU W OU Z azerty)
        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_z]:
            dy = -self.speed
            self.direction = 3
        
        # Collision avec les murs
        if walls is not None and (dx != 0 or dy != 0):
            dx, dy = check_wall_collision(self.rect, walls, dx, dy)
        
        # Appliquer le déplacement
        self.x += dx
        self.y += dy
        
        # Limites de l'écran
        self.x = max(0, min(self.x, 320 - self.width))
        self.y = max(0, min(self.y, 180 - self.height))
        
        # Mettre à jour le rectangle
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def try_attack(self):
        """Lance une attaque."""
        if self.attack_cooldown > 0:
            return False
        
        self.attacking = True
        self.attack_duration = 1
        self.attack_cooldown = 30
        
        size = self.attack_range

        offset = 10
        
        if self.direction == 0:  # Droite
            self.attack_rect = pygame.Rect(self.rect.right - offset , self.rect.centery - size//2, size + offset, size)
        elif self.direction == 1:  # Gauche
            self.attack_rect = pygame.Rect(self.rect.left - size , self.rect.centery - size//2, size +offset , size)
        elif self.direction == 2:  # Bas
            self.attack_rect = pygame.Rect(self.rect.centerx - size//2, self.rect.bottom - offset, size, size + offset)
        else:  # Haut
            self.attack_rect = pygame.Rect(self.rect.centerx - size//2, self.rect.top - size, size, size +offset)
        
        return True
    
    def update(self):
        """Met à jour les cooldowns."""
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        if self.attack_duration > 0:
            self.attack_duration -= 1
        else:
            self.attacking = False
            self.attack_rect = None
    
    def check_attack_hit(self, enemy_rect,Walls):
        """Vérifie si l'attaque touche."""
        if self.attacking and self.attack_rect:

            point_depart = self.rect.center
            point_arrivee = enemy_rect.center

            for wall in Walls:
                if wall.rect.clipline(point_depart,point_arrivee):
                    return False
            return self.attack_rect.colliderect(enemy_rect)
        return False
    
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0
    
    def is_alive(self):
        return self.health > 0
    
    def draw(self, surface):
        # Joueur
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Zone d'attaque
        if self.attacking and self.attack_rect:
            pygame.draw.rect(surface, (255, 255, 255), self.attack_rect)
        
        # Barre de vie
        bar_w, bar_h = 30, 4
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.y - 8
        
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        
        ratio = self.health / self.max_health
        fill_w = int(bar_w * ratio)
        color = (50, 255, 50) if ratio > 0.5 else (255, 255, 50) if ratio > 0.25 else (255, 50, 50)
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))
