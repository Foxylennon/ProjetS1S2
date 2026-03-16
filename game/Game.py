"""
=============================================================================
                        JEU SOLO AVEC MURS
=============================================================================
"""

import pygame
from entities.Player import Player
from entities.Enemy import Enemy
from entities.Wall import create_level_walls


def game(dm):
    """Boucle de jeu solo."""
    print("--- JEU SOLO ---")
    
    # Joueur - spawn en haut à gauche (LOIN des murs et obstacles)
    player = Player(20, 20)
    
    # Ennemi - spawn en bas à droite
    enemy = Enemy(200, 140)
    
    # Murs
    walls = create_level_walls()
    
    # Polices
    font = pygame.font.SysFont(None, 16)
    font_big = pygame.font.SysFont(None, 24)
    
    # État
    game_over = False
    victory = False
    
    clock = pygame.time.Clock()
    
    while True:
        # --- ÉVÉNEMENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
                
                if event.key == pygame.K_SPACE and not game_over and not victory:
                    player.try_attack()
            
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()
        
        # --- LOGIQUE ---
        if not game_over and not victory:
            # Mouvement du joueur
            keys = pygame.key.get_pressed()
            player.handle_input(keys, walls)
            player.update()
            
            # Ennemi
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
                        
        
        # --- AFFICHAGE ---
        dm.canvas.fill((30, 30, 30))
        
        # Murs
        for wall in walls:
            wall.draw(dm.canvas)
        
        # Ennemi
        if enemy.is_alive():
            enemy.draw(dm.canvas)
        
        # Joueur
        player.draw(dm.canvas)
        
        # HUD
        pv_text = font.render(f"PV: {player.health}/{player.max_health}", True, (255, 255, 255))
        dm.canvas.blit(pv_text, (12, 12))
        
        controls = font.render("ESPACE=Attaque  ESC=Menu", True, (150, 150, 150))
        dm.canvas.blit(controls, (150, 160))
        
        # Game Over
        if game_over:
            overlay = pygame.Surface((320, 180))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))
            
            go_text = font_big.render("GAME OVER", True, (255, 50, 50))
            dm.canvas.blit(go_text, go_text.get_rect(center=(160, 80)))
        
        # Victoire
        if victory:
            overlay = pygame.Surface((320, 180))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))
            
            win_text = font_big.render("VICTOIRE !", True, (50, 255, 50))
            dm.canvas.blit(win_text, win_text.get_rect(center=(160, 80)))
        
        dm.render()
        clock.tick(60)
    
    return "menu"
