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
        
        # --- PATHFINDING A* ---
        self.path = []
        self.last_path_update = 0
        self.path_update_interval = 500  # ms
        self.current_target_pos = None
        
        self.color = (255, 50, 50)
    
    def update(self, player_rect, walls=None, dt_ms: float = 0, nav_grid=None):
        """Se déplace vers le joueur en utilisant A*."""
        # Cooldown d'attaque (ms)
        if self.damage_cooldown_ms > 0:
            self.damage_cooldown_ms = max(0, self.damage_cooldown_ms - dt_ms)

        self.last_path_update += dt_ms
        stop_margin = 0
        dx, dy = 0, 0
        
        if self._edge_distance_to(player_rect) > stop_margin:
            if nav_grid:
                player_center = player_rect.center
                dist_to_target = 0
                if self.current_target_pos:
                    dist_to_target = math.hypot(player_center[0] - self.current_target_pos[0], player_center[1] - self.current_target_pos[1])
                else:
                    dist_to_target = 999
                    
                # Recalcule le chemin toutes les 500ms ou si le joueur a beaucoup bougé
                if self.last_path_update >= self.path_update_interval or dist_to_target > 100:
                    self.path = nav_grid.find_path(self.rect.center, player_center)
                    self.last_path_update = 0
                    self.current_target_pos = player_center
                    
                if self.path:
                    # Point de passage à atteindre
                    wpt = self.path[0]
                    diff_x = wpt[0] - self.rect.centerx
                    diff_y = wpt[1] - self.rect.centery
                    dist = math.hypot(diff_x, diff_y)
                    
                    if dist < 8:
                        self.path.pop(0) # Waypoint atteint
                    else:
                        angle = math.atan2(diff_y, diff_x)
                        dx = math.cos(angle) * self.speed
                        dy = math.sin(angle) * self.speed
                else:
                    # S'il n'y a pas de chemin (obstacle, même case), simple poursuite
                    diff_x = player_center[0] - self.rect.centerx
                    diff_y = player_center[1] - self.rect.centery
                    angle = math.atan2(diff_y, diff_x)
                    dx = math.cos(angle) * self.speed
                    dy = math.sin(angle) * self.speed
            else:
                # Direction centrale vers le joueur (fallback sans grid)
                diff_x = player_rect.centerx - (self.x + self.width / 2)
                diff_y = player_rect.centery - (self.y + self.height / 2)
    
                if abs(diff_x) >= 2 or abs(diff_y) >= 2:
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
