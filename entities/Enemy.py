"""
CLASSE ENNEMI - SIMPLIFIÉ
"""

import pygame
import math
import random
from entities.Wall import check_wall_collision


class Enemy:
    def __init__(self, x, y, width=24, height=24):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)
        
        self.speed = 150
        self.health = 100
        self.max_health = 100
        self.damage = 10
        self.damage_cooldown_ms = 0
        self.damage_cooldown_ms_default = 500  # 0.5s
        
        self.color = (255, 50, 50)
    
    def update(self, player_rect, walls=None, dt_ms: float = 0):
        """Se déplace vers le joueur avec du bruit, puis rebond anti-blocage.

        L'ennemi s'arrête à 10px du joueur.
        """
        # Cooldown d'attaque (ms)
        if self.damage_cooldown_ms > 0:
            self.damage_cooldown_ms = max(0, self.damage_cooldown_ms - dt_ms)

        # Si l'ennemi est déjà proche, on ne se déplace pas
        stop_margin = 0
        if self._edge_distance_to(player_rect) <= stop_margin:
            dx, dy = 0, 0
        else:
            # Direction centrale vers le joueur
            diff_x = player_rect.centerx - (self.x + self.width / 2)
            diff_y = player_rect.centery - (self.y + self.height / 2)

            if abs(diff_x) < 2 and abs(diff_y) < 2:
                dx, dy = 0, 0
            else:
                angle = math.atan2(diff_y, diff_x)
                dx = math.cos(angle) * self.speed
                dy = math.sin(angle) * self.speed

        if dt_ms > 0:
            dx *= (dt_ms / 1000.0)
            dy *= (dt_ms / 1000.0)

        if walls is not None and (dx != 0 or dy != 0):
            dx, dy = check_wall_collision(self.rect, walls, dx, dy)

        self.x += dx
        self.y += dy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def _edge_distance_to(self, player_rect):
        """Distance entre le bord de l'ennemi et le bord du joueur (en pixels)."""
        dx = max(player_rect.left - self.rect.right, self.rect.left - player_rect.right, 0)
        dy = max(player_rect.top - self.rect.bottom, self.rect.top - player_rect.bottom, 0)
        return math.hypot(dx, dy)

    def check_collision_with_player(self, player_rect):
        return self.rect.colliderect(player_rect)

    def is_in_attack_range(self, player_rect, range_px: float = 10):
        """Renvoie True si l'ennemi est suffisamment proche pour infliger des dégâts."""
        return self._edge_distance_to(player_rect) <= range_px

    def deal_damage_to_player(self, player_health):
        if self.damage_cooldown_ms <= 0:
            player_health -= self.damage
            self.damage_cooldown_ms = self.damage_cooldown_ms_default
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
