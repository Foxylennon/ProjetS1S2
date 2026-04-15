"""
JEU MULTIJOUEUR AVEC MURS
"""

import pygame
from config import settings
from lang import t
from entities.Player import Player
from entities.Enemy import Enemy
from entities.Wall import create_level_walls

from ui.UI_utils import Button, load_font


def game_multiplayer(dm, network):
    """Boucle de jeu multijoueur."""
    print("--- JEU MULTIJOUEUR ---")
    
    # Position de spawn selon Host/Client
    if network.is_host:
        player = Player(200, 200)
    else:
        player = Player(280, 140)
    
    spawn_positions = [
        (160, 90),
        (320, 90),
        (160, 250),
        (320, 250),
        (240, 170),
    ]
    enemies = [Enemy(x, y) for x, y in spawn_positions]
    walls = create_level_walls()
    
    from entities.Pathfinding import NavGrid
    nav_grid = NavGrid(1280, 720, 32)
    nav_grid.add_walls(walls)
    
    other_player_rect = pygame.Rect(0, 0, 16, 16)
    other_player_color = (0, 150, 255)
    other_player_health = 100
    
    client_attack_flag = False
    
    def get_closest_target(player_rect, other_pos, enemy_rect):
        if "x" in other_pos and "y" in other_pos:
            other_rect = pygame.Rect(other_pos["x"], other_pos["y"], 16, 16)
            local_dx = player_rect.centerx - enemy_rect.centerx
            local_dy = player_rect.centery - enemy_rect.centery
            other_dx = other_rect.centerx - enemy_rect.centerx
            other_dy = other_rect.centery - enemy_rect.centery
            local_dist = local_dx * local_dx + local_dy * local_dy
            other_dist = other_dx * other_dx + other_dy * other_dy
            return other_rect if other_dist < local_dist else player_rect
        return player_rect
    
    # Polices (recalculées si l'utilisateur change la taille du texte)
    last_text_scale = settings.get("text_scale", 1.0)
    font = load_font(32)
    font_big = load_font(56)

    # Boutons de fin de partie
    btn_width = 240
    btn_height = 50
    btn_spacing = 20
    btn_menu = Button(0, 0, btn_width, btn_height, t("button_menu"), font)
    btn_retry = Button(0, 0, btn_width, btn_height, t("button_retry"), font)

    game_over = False
    victory = False
    
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(60)

        # Recharger les polices si l'utilisateur change la taille du texte
        current_scale = settings.get("text_scale", 1.0)
        if current_scale != last_text_scale:
            last_text_scale = current_scale
            font = load_font(32)
            font_big = load_font(56)

        # Mettre à jour les polices des boutons
        btn_menu.font = font
        btn_retry.font = font

        mouse_clicked = False
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
                    if not network.is_host:
                        client_attack_flag = True

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        other_pos = network.get_other_player_pos()

        if not game_over and not victory:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, walls, dt)
            player.update(dt)

            if network.is_host:
                alive_enemies = [enemy for enemy in enemies if enemy.is_alive()]
                if alive_enemies:
                    for enemy in alive_enemies:
                        target_rect = get_closest_target(player.rect, other_pos, enemy.rect)
                        enemy.update(target_rect, walls, dt, nav_grid)

                        if enemy.is_in_attack_range(player.rect, 10):
                            player.health = enemy.deal_damage_to_player(player.health)
                            if not player.is_alive():
                                game_over = True

                        if "x" in other_pos and "y" in other_pos:
                            other_rect = pygame.Rect(other_pos["x"], other_pos["y"], 16, 16)
                            if enemy.is_in_attack_range(other_rect, 10):
                                other_player_health = enemy.deal_damage_to_player(other_player_health)

                        if player.check_attack_hit(enemy.rect, walls):
                            enemy.take_damage(player.attack_damage)

                    if "player_attack" in other_pos and other_pos["player_attack"]:
                        for enemy in alive_enemies:
                            if "x" in other_pos and "y" in other_pos:
                                other_rect = pygame.Rect(other_pos["x"], other_pos["y"], 16, 16)
                                # On utilise une distance pour la hitbox d'attaque du client 
                                dx = enemy.rect.centerx - other_rect.centerx
                                dy = enemy.rect.centery - other_rect.centery
                                if (dx*dx) + (dy*dy) < 3000:
                                    enemy.take_damage(player.attack_damage)

                    victory = all(not enemy.is_alive() for enemy in enemies)
                else:
                    victory = True
            else:
                # Le client ne calcule pas l'ennemi, il affiche simplement la position reçue
                if "enemies" in other_pos:
                    enemy_list = other_pos["enemies"]
                    for idx, enemy_data in enumerate(enemy_list):
                        if idx < len(enemies):
                            enemies[idx].x = float(enemy_data.get("x", enemies[idx].x))
                            enemies[idx].y = float(enemy_data.get("y", enemies[idx].y))
                            enemies[idx].rect.x = int(enemies[idx].x)
                            enemies[idx].rect.y = int(enemies[idx].y)
                            enemies[idx].health = enemy_data.get("health", enemies[idx].health)
                        else:
                            new_enemy = Enemy(enemy_data.get("x", 0), enemy_data.get("y", 0))
                            new_enemy.health = enemy_data.get("health", new_enemy.health)
                            enemies.append(new_enemy)
                if "other_player_health" in other_pos:
                    player.health = other_pos["other_player_health"]
                if "victory" in other_pos:
                    victory = other_pos["victory"]

        # Boutons de fin de partie
        mouse_pos = dm.get_mouse()
        if game_over or victory:
            center_x = dm.virtual_res[0] // 2
            buttons_y = dm.virtual_res[1] // 2 + 80
            total_w = btn_width * 2 + btn_spacing
            start_x = center_x - total_w // 2

            btn_menu.rect.topleft = (start_x, buttons_y)
            btn_retry.rect.topleft = (start_x + btn_width + btn_spacing, buttons_y)

            btn_menu.update(mouse_pos)
            btn_retry.update(mouse_pos)

            if mouse_clicked:
                if btn_menu.is_clicked(mouse_pos, True):
                    network.close()
                    return "menu"
                if btn_retry.is_clicked(mouse_pos, True):
                    return "game_multi"

        if network.is_host:
            enemy_data = [
                {"x": enemy.x, "y": enemy.y, "health": enemy.health}
                for enemy in enemies
            ]
            network.send_position(
                player.rect.x,
                player.rect.y,
                player_health=player.health,
                enemies=enemy_data,
                other_player_health=other_player_health,
                victory=victory,
            )
        else:
            network.send_position(
                player.rect.x,
                player.rect.y,
                player_health=player.health,
                player_attack=client_attack_flag,
            )
            client_attack_flag = False

        other_pos = network.get_other_player_pos()
        if "x" in other_pos and "y" in other_pos:
            other_player_rect.x = other_pos["x"]
            other_player_rect.y = other_pos["y"]
        if "player_health" in other_pos:
            if not network.is_host:
                other_player_health = other_pos["player_health"]
        
        # Affichage
        dm.canvas.fill((30, 30, 30))
        
        for wall in walls:
            wall.draw(dm.canvas)
        
        pygame.draw.rect(dm.canvas, other_player_color, other_player_rect)
        
        for enemy in enemies:
            if enemy.is_alive():
                enemy.draw(dm.canvas)
        
        player.draw(dm.canvas)
        
        # HUD
        role_label = t("host_label") if network.is_host else t("client_label")
        dm.canvas.blit(font.render(role_label, False, (255, 255, 255)), (12, 12))
        dm.canvas.blit(font.render(f"{t('hp_label')} {player.health}", False, (255, 255, 255)), (12, 25))
        if network.is_host:
            dm.canvas.blit(font.render(f"Client: {other_player_health}", False, (100, 150, 255)), (12, 38))
        else:
            dm.canvas.blit(font.render(f"Host: {other_player_health}", False, (150, 100, 100)), (12, 38))

        if game_over:
            overlay = pygame.Surface(dm.canvas.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))
            go_surf = font_big.render(t("game_over"), False, (255, 50, 50))
            dm.canvas.blit(go_surf, go_surf.get_rect(center=dm.canvas.get_rect().center))

            btn_menu.draw(dm.canvas)
            btn_retry.draw(dm.canvas)

        if victory:
            overlay = pygame.Surface(dm.canvas.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))
            victory_surf = font_big.render(t("victory"), False, (50, 255, 50))
            dm.canvas.blit(victory_surf, victory_surf.get_rect(center=dm.canvas.get_rect().center))

            btn_menu.draw(dm.canvas)
            btn_retry.draw(dm.canvas)
        
        dm.render()
        
        if not network.connected:
            return "menu"
        
        if not player.is_alive():
            game_over = True
        
        if network.is_host and other_player_health <= 0:
            victory = True
        
        clock.tick(60)
    
    return "menu"
