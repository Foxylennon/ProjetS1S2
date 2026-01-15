"""
CLASSE ENNEMI - SIMPLIFIÉ
"""

import pygame
from entities.Wall import check_wall_collision


class Enemy:
    def __init__(self, x, y, width=14, height=14):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        
        self.speed = 0.8
        self.health = 50
        self.max_health = 50
        self.damage = 10
        self.damage_cooldown = 0
        
        self.color = (255, 50, 50)
    
    def update(self, player_rect, walls=None):
        """Se déplace vers le joueur."""
        # Direction vers le joueur
        diff_x = player_rect.centerx - (self.x + self.width // 2)
        diff_y = player_rect.centery - (self.y + self.height // 2)
        
        dx = 0
        dy = 0
        
        if diff_x > 5:
            dx = self.speed
        elif diff_x < -5:
            dx = -self.speed
        
        if diff_y > 5:
            dy = self.speed
        elif diff_y < -5:
            dy = -self.speed
        
        # Collision avec les murs
        if walls is not None and (dx != 0 or dy != 0):
            dx, dy = check_wall_collision(self.rect, walls, dx, dy)
        
        self.x += dx
        self.y += dy
        
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
        
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1
    
    def check_collision_with_player(self, player_rect):
        return self.rect.colliderect(player_rect)
    
    def deal_damage_to_player(self, player_health):
        if self.damage_cooldown <= 0:
            player_health -= self.damage
            self.damage_cooldown = 60
        return player_health
    
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0
    
    def is_alive(self):
        return self.health > 0
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Barre de vie
        bar_w, bar_h = self.width, 3
        bar_x, bar_y = self.rect.x, self.rect.y - 5
        
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        
        ratio = self.health / self.max_health
        fill_w = int(bar_w * ratio)
        color = (50, 255, 50) if ratio > 0.5 else (255, 255, 50) if ratio > 0.25 else (255, 50, 50)
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))
