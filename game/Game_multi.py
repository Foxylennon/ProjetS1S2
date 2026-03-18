"""
JEU MULTIJOUEUR AVEC MURS
"""

import pygame
from entities.Player import Player
from entities.Enemy import Enemy
from entities.Wall import create_level_walls

FONT_PATH = "assets/fonts/PressStart2P-Regular.ttf"

def load_font(size):
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont(None, size)


def game_multiplayer(dm, network):
    """Boucle de jeu multijoueur."""
    print("--- JEU MULTIJOUEUR ---")
    
    # Position de spawn selon Host/Client
    if network.is_host:
        player = Player(200, 200)
    else:
        player = Player(280, 140)
    
    enemy = Enemy(160, 90)
    walls = create_level_walls()
    
    other_player_rect = pygame.Rect(0, 0, 16, 16)
    other_player_color = (0, 150, 255)
    
    font = load_font(32)
    font_big = load_font(56)
    
    game_over = False
    victory = False
    
    clock = pygame.time.Clock()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                network.close()
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    network.close()
                    return "menu"
                
                if event.key == pygame.K_SPACE and not game_over:
                    player.try_attack()
            
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()
        
        if not game_over and not victory:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, walls)
            player.update()
            
            if enemy.is_alive():
                enemy.update(player.rect, walls)
                
                if enemy.check_collision_with_player(player.rect):
                    player.health = enemy.deal_damage_to_player(player.health)
                    if not player.is_alive():
                        game_over = True
                
                if player.check_attack_hit(enemy.rect,walls):
                    enemy.take_damage(player.attack_damage)
            else:
                victory = True
        
                        
        # Réseau
        network.send_position(player.rect.x, player.rect.y)
        other_pos = network.get_other_player_pos()
        other_player_rect.x = other_pos["x"]
        other_player_rect.y = other_pos["y"]
        
        # Affichage
        dm.canvas.fill((30, 30, 30))
        
        for wall in walls:
            wall.draw(dm.canvas)
        
        pygame.draw.rect(dm.canvas, other_player_color, other_player_rect)
        
        if enemy.is_alive():
            enemy.draw(dm.canvas)
        
        player.draw(dm.canvas)
        
        # HUD
        role = "HOST" if network.is_host else "CLIENT"
        dm.canvas.blit(font.render(role, False, (255, 255, 255)), (12, 12))
        dm.canvas.blit(font.render(f"PV: {player.health}", False, (255, 255, 255)), (12, 25))
        
        if game_over:
            overlay = pygame.Surface(dm.canvas.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))
            dm.canvas.blit(font_big.render("GAME OVER", False, (255, 50, 50)), font_big.render("GAME OVER", False, (255, 50, 50)).get_rect(center=(640, 360)))
        
        if victory:
            overlay = pygame.Surface(dm.canvas.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))
            dm.canvas.blit(font_big.render("VICTOIRE !", False, (50, 255, 50)), font_big.render("VICTOIRE !", False, (50, 255, 50)).get_rect(center=(640, 360)))
        
        dm.render()
        
        if not network.connected:
            return "menu"
        
        clock.tick(60)
    
    return "menu"
