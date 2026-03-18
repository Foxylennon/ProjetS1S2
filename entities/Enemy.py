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
        
        self.speed = 4.5
        self.health = 100
        self.max_health = 100
        self.damage = 10
        self.damage_cooldown = 0
        
        self.color = (255, 50, 50)
    
    def update(self, player_rect, walls=None):
        """Se déplace vers le joueur avec du bruit, puis rebond anti-blocage."""
        # Direction centrale vers le joueur
        diff_x = player_rect.centerx - (self.x + self.width / 2)
        diff_y = player_rect.centery - (self.y + self.height / 2)

        if abs(diff_x) < 2 and abs(diff_y) < 2:
            dx, dy = 0, 0
        else:
            base_angle = math.atan2(diff_y, diff_x)
            jitter = random.uniform(-math.pi / 9, math.pi / 9)  # +/- 20°
            angle = base_angle + jitter
            dx = math.cos(angle) * self.speed 
            dy = math.sin(angle) * self.speed 

        if walls is not None and (dx != 0 or dy != 0):
            dx_try, dy_try = check_wall_collision(self.rect, walls, dx, dy)

            if dx_try == 0 and dy_try == 0:
                # Bloqué, on tente plusieurs directions alternatives
                alternatives = [
                    (dx, 0),
                    (0, dy),
                    (math.cos(base_angle + math.pi / 2) * self.speed, math.sin(base_angle + math.pi / 2) * self.speed),
                    (math.cos(base_angle - math.pi / 2) * self.speed, math.sin(base_angle - math.pi / 2) * self.speed),
                    (math.cos(base_angle + math.pi) * self.speed, math.sin(base_angle + math.pi) * self.speed),
                ]

                found = False
                for alt_dx, alt_dy in alternatives:
                    cand_dx, cand_dy = check_wall_collision(self.rect, walls, alt_dx, alt_dy)
                    if cand_dx != 0 or cand_dy != 0:
                        dx, dy = cand_dx, cand_dy
                        found = True
                        break

                if not found:
                    # Rebond aléatoire pour sortir du coin
                    for _ in range(8):
                        rand_angle = random.uniform(0, math.pi * 2)
                        rand_dx = math.cos(rand_angle) * self.speed
                        rand_dy = math.sin(rand_angle) * self.speed
                        cand_dx, cand_dy = check_wall_collision(self.rect, walls, rand_dx, rand_dy)
                        if cand_dx != 0 or cand_dy != 0:
                            dx, dy = cand_dx, cand_dy
                            found = True
                            break

                    if not found:
                        dx, dy = 0, 0
            else:
                dx, dy = dx_try, dy_try

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
