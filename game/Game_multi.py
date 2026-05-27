"""
JEU MULTIJOUEUR AVEC MURS
"""

import pygame
import random
from config import settings
from lang import t
from entities.Player import Player
from entities.Enemy import Enemy
from entities.Map import Map

from ui.UI_utils import Button, load_body_font, load_font
from game.Shop import ShopMenu


def game_multiplayer(dm, network):
    """Boucle de jeu multijoueur."""
    print("--- JEU MULTIJOUEUR ---")
    
    # Position de spawn selon Host/Client
    if network.is_host:
        player = Player(100, 100, player_id=1, name="P1")
        other_player = Player(0, 0, player_id=2, name="P2")
    else:
        player = Player(150, 100, player_id=2, name="P2")
        other_player = Player(0, 0, player_id=1, name="P1")

    map_seed = network.other_player_pos.get("map_seed", 42)
    random.seed(map_seed)
    game_map = Map(3, 3)
    game_map.create_map()
    random.seed()


    from entities.Pathfinding import NavGrid
    def get_nav_grid(current_room):
        ng = NavGrid(1280, 720, 32)
        active_obstacles = current_room.walls + [d for d in current_room.doors if d.is_locked]
        ng.add_walls(active_obstacles)
        return ng

    nav_grid = get_nav_grid(game_map.get_current_room())
    
    other_player_health = 100
    client_attack_flag = False
    host_attack_flag = False
    
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
    
    # Polices
    font = load_font(32)
    font_big = load_font(56)
    font_body = load_body_font(18)

    # background image
    play_bg = None
    try:
        play_bg_orig = pygame.image.load("assets/ui/play_bg.png").convert_alpha()
        play_bg = pygame.transform.smoothscale(play_bg_orig, dm.virtual_res)
    except Exception:
        play_bg = None

    # Boutons de fin de partie
    btn_width = 240
    btn_height = 50
    btn_spacing = 20
    btn_menu = Button(0, 0, btn_width, btn_height, t("button_menu"), font)
    btn_retry = Button(0, 0, btn_width, btn_height, t("button_retry"), font)

    game_over = False
    victory = False
    
    shop_menu = ShopMenu(dm.virtual_res)
    score = 0
    total_kills = 0
    
    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(60)

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

                if event.key == pygame.K_SPACE and not game_over and not shop_menu.is_open:
                    if player.try_attack():
                        if not network.is_host:
                            client_attack_flag = True
                        else:
                            host_attack_flag = True

                if event.key == pygame.K_e and not game_over and not victory:
                    current_room = game_map.get_current_room()
                    if current_room.is_shop and current_room.npc and current_room.npc.is_near(player.rect):
                        shop_menu.is_open = not shop_menu.is_open

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        other_pos = network.get_other_player_pos()

        mouse_pos = dm.get_mouse()

        keys = pygame.key.get_pressed()
        if shop_menu.is_open and not game_over and not victory:
            score = shop_menu.update(mouse_pos, mouse_clicked, keys, player, score)

        enemies_killed_this_tick = 0

        current_room = game_map.get_current_room()
        active_obstacles = current_room.walls + [d for d in current_room.doors if d.is_locked]

        if not game_over and not victory and not shop_menu.is_open:
            player.handle_input(keys, active_obstacles, dt)
            player.update(dt)

            if network.is_host:
                current_room.update_room()
                
                # Gestion des portes (Host)
                for door in current_room.doors:
                    if door.check_collision(player):
                        game_map.change_room(door, player, dm.virtual_res[0], dm.virtual_res[1])
                        # L'autre joueur change aussi et on le décale
                        if door.direction == "haut":
                            other_player.y = dm.virtual_res[1] - other_player.rect.height - 60
                        elif door.direction == "bas":
                            other_player.y = 60
                        elif door.direction == "gauche":
                            other_player.x = dm.virtual_res[0] - other_player.rect.width - 60
                        elif door.direction == "droite":
                            other_player.x = 60
                        other_player.rect.x = int(other_player.x)
                        other_player.rect.y = int(other_player.y)
                        
                        current_room = game_map.get_current_room()
                        nav_grid = get_nav_grid(current_room)
                        break
                spawned_enemies = []
                for enemy in current_room.enemies[:]:
                    if enemy.is_alive() or not enemy.is_faint_animation_complete():
                        target_rect = get_closest_target(player.rect, other_pos, enemy.rect)
                        spawned_enemies.extend(enemy.update(target_rect, active_obstacles, dt, nav_grid, current_room.enemies))

                        if enemy.attack_can_hit(player.rect) and not player.dashing:
                            player.health = enemy.deal_damage_to_player(player.health)
                            if not player.is_alive():
                                game_over = True

                        # Le client gère lui-même ses propres dégâts via l'animation synchronisée.

                        if player.check_attack_hit(enemy.rect, active_obstacles):
                            enemy.take_damage(player.attack_damage)
                    else:
                        current_room.enemies.remove(enemy)
                        enemies_killed_this_tick += 1

                current_room.enemies.extend(spawned_enemies)
                
                if enemies_killed_this_tick > 0:
                    score += enemies_killed_this_tick
                    total_kills += enemies_killed_this_tick

                if "player_attack" in other_pos and other_pos["player_attack"]:
                    for enemy in [e for e in current_room.enemies if e.is_alive()]:
                        if "x" in other_pos and "y" in other_pos:
                            other_rect = pygame.Rect(other_pos["x"], other_pos["y"], 16, 16)
                            # On utilise une distance pour la hitbox d'attaque du client 
                            dx = enemy.rect.centerx - other_rect.centerx
                            dy = enemy.rect.centery - other_rect.centery
                            if (dx*dx) + (dy*dy) < 3000:
                                enemy.take_damage(player.attack_damage)

                # Victoire non gérée simplement par la salle vide dans un Rogue-like
                # victory = ...
            else:
                # Le client vérifie si la salle a changé
                if "room_x" in other_pos and "room_y" in other_pos:
                    rx, ry = other_pos["room_x"], other_pos["room_y"]
                    if (rx, ry) != game_map.current_room_coords:
                        dx = rx - game_map.current_room_coords[0]
                        dy = ry - game_map.current_room_coords[1]
                        
                        game_map.current_room_coords = (rx, ry)
                        game_map.get_current_room().on_enter()
                        current_room = game_map.get_current_room()
                        
                        offset = 60
                        if dy == -1:
                            player.y = dm.virtual_res[1] - player.rect.height - offset
                        elif dy == 1:
                            player.y = offset
                        elif dx == -1:
                            player.x = dm.virtual_res[0] - player.rect.width - offset
                        elif dx == 1:
                            player.x = offset
                            
                        player.rect.x = int(player.x)
                        player.rect.y = int(player.y)

                # Le client met à jour les ennemis à partir des données
                if "enemies" in other_pos:
                    enemy_list = other_pos["enemies"]
                    new_enemies = []
                    for e_data in enemy_list:
                        e_type = e_data.get("type", "tumor")
                        existing = next((e for e in current_room.enemies if e.monster_type == e_type), None)
                        if existing:
                            current_room.enemies.remove(existing)
                            existing.x = e_data.get("x", existing.x)
                            existing.y = e_data.get("y", existing.y)
                            existing.rect.x = int(existing.x)
                            existing.rect.y = int(existing.y)
                            existing.health = e_data.get("health", existing.health)
                            existing.facing_left = e_data.get("facing_left", existing.facing_left)
                            existing.previous_horizontal = existing.facing_left
                            existing.moving = e_data.get("moving", existing.moving)
                            
                            is_attacking = e_data.get("attacking", False)
                            if is_attacking and existing.state != "attacking":
                                existing._open_attack()
                                existing._update_attack_rect()
                                
                            new_enemies.append(existing)
                        else:
                            new_enemy = Enemy(e_data.get("x", 0), e_data.get("y", 0), monster_type=e_type)
                            new_enemy.health = e_data.get("health", 100)
                            new_enemy.facing_left = e_data.get("facing_left", False)
                            new_enemy.previous_horizontal = new_enemy.facing_left
                            new_enemy.moving = e_data.get("moving", False)
                            
                            if e_data.get("attacking", False):
                                new_enemy._open_attack()
                                new_enemy._update_attack_rect()
                                
                            new_enemies.append(new_enemy)
                    
                    current_room.enemies = new_enemies
                    
                    # On anime les ennemis côté client pour voir l'effet du moving/facing
                    for e in current_room.enemies:
                        e._advance_animation(dt)
                        
                # On synchronise l'état de nettoyage de la salle pour le rendu des portes
                current_room.is_cleared = len(current_room.enemies) == 0
                for door in current_room.doors:
                    door.is_locked = not current_room.is_cleared
                
                # Le client gère ses propres dégâts
                for enemy in current_room.enemies:
                    if enemy.attack_can_hit(player.rect) and not player.dashing:
                        player.health = enemy.deal_damage_to_player(player.health)

                if "victory" in other_pos:
                    victory = other_pos["victory"]

        if "total_kills" in other_pos and not network.is_host:
            kills_received = other_pos["total_kills"]
            if kills_received > total_kills:
                diff = kills_received - total_kills
                score += diff
                total_kills = kills_received

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
                {"x": enemy.x, "y": enemy.y, "health": enemy.health, "type": enemy.monster_type, "facing_left": enemy.facing_left, "moving": enemy.moving, "attacking": enemy.attacking}
                for enemy in current_room.enemies
            ]
            network.send_position(
                player.rect.x,
                player.rect.y,
                player_health=player.health,
                enemies=enemy_data,
                other_player_health=other_player_health,
                victory=victory,
                room_x=game_map.current_room_coords[0],
                room_y=game_map.current_room_coords[1],
                facing_left=(player.previous_horizontal == 1),
                moving=player.moving,
                player_attack=host_attack_flag,
                total_kills=total_kills
            )
            host_attack_flag = False
        else:
            network.send_position(
                player.rect.x,
                player.rect.y,
                player_health=player.health,
                player_attack=client_attack_flag,
                facing_left=(player.previous_horizontal == 1),
                moving=player.moving
            )
            client_attack_flag = False

        other_pos = network.get_other_player_pos()
        if "x" in other_pos and "y" in other_pos:
            other_player.x = float(other_pos["x"])
            other_player.y = float(other_pos["y"])
            other_player.rect.x = int(other_player.x)
            other_player.rect.y = int(other_player.y)
            
        if "moving" in other_pos:
            other_player.moving = other_pos["moving"]
        if "facing_left" in other_pos:
            other_player.previous_horizontal = 1 if other_pos["facing_left"] else 0
            
        if "player_attack" in other_pos and other_pos["player_attack"]:
            if not other_player.attacking:
                other_player.try_attack()
                
        other_player.update(dt)
        if "player_health" in other_pos:
            if not network.is_host:
                other_player_health = other_pos["player_health"]
            else:
                other_player_health = other_pos.get("player_health", other_player_health)
            other_player.health = other_player_health
            
        if "lobby_name" in other_pos and other_pos["lobby_name"]:
            other_player.display_name = other_pos["lobby_name"]

        # Affichage
        if play_bg is not None:
            dm.canvas.blit(play_bg, (0, 0))
        else:
            dm.canvas.fill((30, 30, 30))
        
        for wall in current_room.walls:
            wall.draw(dm.canvas)
            
        for door in current_room.doors:
            door.draw(dm.canvas)
        
        for enemy in current_room.enemies:
            if enemy.is_alive():
                enemy.draw(dm.canvas)
                
        # NPC Shop
        if current_room.is_shop and current_room.npc:
            current_room.npc.draw(dm.canvas)
            if current_room.npc.is_near(player.rect):
                current_room.npc.draw_interaction_hint(dm.canvas)
        
        other_player.draw(dm.canvas)
        other_player.draw_name(dm.canvas, font)
        player.draw(dm.canvas)
        player.draw_name(dm.canvas, font)
        
        # HUD
        role_label = t("host_label") if network.is_host else t("client_label")
        dm.canvas.blit(font.render(role_label, False, (255, 255, 255)), (12, 12))
        dm.canvas.blit(font.render(f"{t('hp_label')} {player.health}", False, (255, 255, 255)), (12, 25))
        if network.is_host:
            dm.canvas.blit(font.render(f"Client: {other_player_health}", False, (100, 150, 255)), (12, 38))
        else:
            dm.canvas.blit(font.render(f"Host: {other_player_health}", False, (150, 100, 100)), (12, 38))

        dash_text = font_body.render(f"{t('dash_label')} [{int(player.dash_cooldown_remaining_ms/1000 + 0.9)}s]" if player.dash_cooldown_remaining_ms > 0 else t('dash_label'), False, (180, 180, 255))
        dm.canvas.blit(dash_text, (12, 60))

        score_text = font.render(f"* {score}", False, (255, 255, 255))
        dm.canvas.blit(score_text, (12, 84))

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
        
        if shop_menu.is_open and not game_over and not victory:
            shop_menu.draw(dm.canvas)

        dm.render()
        
        if not network.connected:
            return "menu"
        
        if not player.is_alive():
            game_over = True
        
        if network.is_host and other_player_health <= 0:
            victory = True
        
        clock.tick(60)
    
    return "menu"
