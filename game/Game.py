"""
=============================================================================
                        JEU SOLO AVEC MURS
=============================================================================
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
from common.music_manager import music_manager


def game(dm):
    """Partie en cours"""
    print("--- JEU SOLO ---")
    
    # pos player when game starts
    player = Player(50, 50, player_id=1, name="P1")

    # player profile
    profile_img_orig = None
    try:
        profile_img_orig = pygame.image.load("assets/ui/profil-p1.png").convert_alpha()
    except Exception:
        profile_img_orig = None

    # profile img
    profile_img = None
    profile_size = (0, 0)
    if profile_img_orig is not None:
        ratio = profile_img_orig.get_width() / profile_img_orig.get_height()
        profile_size = (int(192 * ratio), 192)
        profile_img = pygame.transform.smoothscale(profile_img_orig, profile_size)

    # Map generation
    game_map = Map(3, 3)
    game_map.create_map()
    # stats : score & timer
    score = 0
    time_elapsed_ms = 0
    # "+1"
    popups = []  # liste de {'text', 'pos', 'ttl', 'vy'}

    from entities.Pathfinding import NavGrid
    
    def get_nav_grid(current_room):
        ng = NavGrid(1280, 720, 32)
        active_obstacles = current_room.walls + [d for d in current_room.doors if d.is_locked]
        ng.add_walls(active_obstacles)
        return ng

    nav_grid = get_nav_grid(game_map.get_current_room())
    show_controls_hint = True
    
    # fonts
    font = load_font(32)
    font_big = load_font(56)
    font_small = load_font(18)
    font_body = load_body_font(18)

    # background image
    play_bg = None
    try:
        play_bg_orig = pygame.image.load("assets/ui/play_bg.png").convert_alpha()
        play_bg = pygame.transform.smoothscale(play_bg_orig, dm.virtual_res)
    except Exception:
        play_bg = None

    # buttons
    btn_width = 240
    btn_height = 50
    btn_spacing = 20
    btn_menu = Button(0, 0, btn_width, btn_height, t("button_menu"), font)
    btn_retry = Button(0, 0, btn_width, btn_height, t("button_retry"), font)
    btn_resume = Button(0, 0, btn_width, btn_height, t("button_resume"), font)

    btn_pause = Button(12, 12, 120, 40, t("pause_title"), font)

    # bool 'game over', 'pause'
    game_over = False
    paused = False

    shop_menu = ShopMenu(dm.virtual_res)

    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(60)
        music_manager.update()

        # scaling btn text
        btn_menu.font = font
        btn_retry.font = font
        btn_resume.font = font
        btn_pause.font = font

        # scaling img
        profile_img = None
        profile_size = (0, 0)
        if profile_img_orig is not None:
            ratio = profile_img_orig.get_width() / profile_img_orig.get_height()
            profile_size = (int(192 * ratio), 192)
            profile_img = pygame.transform.smoothscale(profile_img_orig, profile_size)

        # --- EVENTS ---
        mouse_clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # -> close game
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: # -> title screen
                    return "menu"

                if event.key == pygame.K_SPACE and not game_over and not paused and not shop_menu.is_open: # game: player atk
                    player.try_attack()

                if event.key == pygame.K_p and not game_over and not shop_menu.is_open: # game: btn 'Pause' pressed
                    paused = not paused 

                if event.key == pygame.K_e and not game_over and not paused:
                    current_room = game_map.get_current_room()
                    if current_room.is_shop and current_room.npc and current_room.npc.is_near(player.rect):
                        shop_menu.is_open = not shop_menu.is_open

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        # --- LOGIQUE ---
        mouse_pos = dm.get_mouse()
        btn_pause.update(mouse_pos)

        keys = pygame.key.get_pressed()

        if mouse_clicked and btn_pause.is_clicked(mouse_pos, True) and not game_over and not shop_menu.is_open:
            paused = not paused

        if shop_menu.is_open and not game_over and not paused:
            music_manager.play_shop()
            score = shop_menu.update(mouse_pos, mouse_clicked, keys, player, score)
        else:
            if not game_over and not paused:
                music_manager.play_game()

        # Control footsteps running loop sound
        if player.moving and not game_over and not paused and not shop_menu.is_open:
            music_manager.start_run()
        else:
            music_manager.stop_run()

        if not game_over and not paused and not shop_menu.is_open:
            time_elapsed_ms += dt

            current_room = game_map.get_current_room()
            current_room.update_room()
            
            # Vérifier les collisions avec les portes
            for door in current_room.doors:
                if door.check_collision(player):
                    game_map.change_room(door, player, dm.virtual_res[0], dm.virtual_res[1])
                    current_room = game_map.get_current_room()
                    nav_grid = get_nav_grid(current_room)
                    show_controls_hint = False
                    break

            # Mouvement du joueur (attention aux murs + portes verrouillées)
            active_obstacles = current_room.walls + [d for d in current_room.doors if d.is_locked]
            player.handle_input(keys, active_obstacles, dt)
            player.update(dt)

            spawned_enemies = []
            for enemy in current_room.enemies[:]:
                if enemy.is_alive() or not enemy.is_faint_animation_complete():
                    spawned_enemies.extend(enemy.update(player.rect, active_obstacles, dt, nav_grid, current_room.enemies))

                    if enemy.attack_can_hit(player.rect) and not player.dashing:
                        player.health = enemy.deal_damage_to_player(player.health)
                        if not player.is_alive():
                            game_over = True

                    if player.check_attack_hit(enemy.rect, active_obstacles):
                        enemy.take_damage(player.attack_damage)
                else:
                    current_room.enemies.remove(enemy)
                    score += 1
                    popups.append({
                        "text": "+1",
                        "pos": list(enemy.rect.center),
                        "ttl": 800,
                        "vy": -0.03,
                    })

            current_room.enemies.extend(spawned_enemies)

            # Mise à jour des popups (animation et durée)
            for popup in popups[:]:
                popup["ttl"] -= dt
                popup["pos"][1] += popup["vy"] * dt
                if popup["ttl"] <= 0:
                    popups.remove(popup)

        # Afficher les boutons de fin de partie / pause et gérer les clics
        if game_over:
            center_x = dm.virtual_res[0] // 2
            title_y = dm.virtual_res[1] // 2 - 120
            button_y = title_y + 160
            total_w = btn_width * 2 + btn_spacing
            start_x = center_x - total_w // 2

            btn_menu.rect.topleft = (start_x, button_y)
            btn_retry.rect.topleft = (start_x + btn_width + btn_spacing, button_y)

            btn_menu.update(mouse_pos)
            btn_retry.update(mouse_pos)

            if mouse_clicked:
                if btn_menu.is_clicked(mouse_pos, True):
                    return "menu"
                if btn_retry.is_clicked(mouse_pos, True):
                    return "game"

        elif paused:
            center_x = dm.virtual_res[0] // 2
            title_y = dm.virtual_res[1] // 2 - 120
            button_y = title_y + 110
            total_w = btn_width * 3 + btn_spacing * 2
            start_x = center_x - total_w // 2

            btn_menu.rect.topleft = (start_x, button_y)
            btn_resume.rect.topleft = (start_x + btn_width + btn_spacing, button_y)
            btn_retry.rect.topleft = (start_x + (btn_width + btn_spacing) * 2, button_y)

            btn_menu.update(mouse_pos)
            btn_resume.update(mouse_pos)
            btn_retry.update(mouse_pos)

            if mouse_clicked:
                if btn_menu.is_clicked(mouse_pos, True):
                    return "menu"
                if btn_resume.is_clicked(mouse_pos, True):
                    paused = False
                if btn_retry.is_clicked(mouse_pos, True):
                    return "game"

        # (removed inline shop logic)

        # --- AFFICHAGE ---
        if play_bg is not None:
            dm.canvas.blit(play_bg, (0, 0))
        else:
            dm.canvas.fill((30, 30, 30))
        
        current_room = game_map.get_current_room()
        # Murs
        for wall in current_room.walls:
            wall.draw(dm.canvas)
            
        # Portes
        for door in current_room.doors:
            door.draw(dm.canvas)
        
        # Ennemi
        for enemy in current_room.enemies:
            if enemy.is_alive():
                enemy.draw(dm.canvas)
                
        # NPC Shop
        if current_room.is_shop and current_room.npc:
            current_room.npc.draw(dm.canvas)
            if current_room.npc.is_near(player.rect):
                current_room.npc.draw_interaction_hint(dm.canvas)
        
        # Joueur
        player.draw(dm.canvas)
        player.draw_name(dm.canvas, font_small)

        # Popups (+1)
        for popup in popups:
            alpha = max(0, min(255, int(255 * (popup["ttl"] / 800))))
            txt_surf = font.render(popup["text"], False, (255, 255, 255))
            txt_surf.set_alpha(alpha)
            dm.canvas.blit(txt_surf, txt_surf.get_rect(center=popup["pos"]))

        # HUD
        profile_x = 2
        profile_y = dm.virtual_res[1] - (profile_size[1] if profile_size[1] > 0 else 24) - 2
        if profile_img is not None:
            # Profil à 30% d'opacité
            profile_with_alpha = profile_img.copy()
            profile_with_alpha.set_alpha(77)  # 30% de 255
            dm.canvas.blit(profile_with_alpha, (profile_x, profile_y))

        # Barre de PV superposée sur le profil
        bar_width = 120
        bar_height = 14
        bar_x = profile_x + 3
        bar_y = profile_y + (profile_size[1] if profile_size[1] > 0 else 24) - bar_height - 3
        health_ratio = (player.health / player.max_health) if player.max_health else 0
        health_ratio = max(0.0, min(1.0, health_ratio))

        bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        fg_rect = pygame.Rect(bar_x, bar_y, int(bar_width * health_ratio), bar_height)

        pygame.draw.rect(dm.canvas, (255, 0, 0), bg_rect, border_radius=6)
        if fg_rect.width > 0:
            pygame.draw.rect(dm.canvas, (0, 220, 0), fg_rect, border_radius=6)
        pygame.draw.rect(dm.canvas, (80, 80, 80), bg_rect, 2, border_radius=6)

        # Texte HP au-dessus du profil
        hp_text = font.render(f"{t('hp_label')} {player.health}/{player.max_health}", False, (255, 255, 255))
        hp_pos = (profile_x, profile_y - hp_text.get_height() - 5)
        dm.canvas.blit(hp_text, hp_pos)

        # Indicateur de dash en carré à droite de la barre de PV
        dash_size = 14
        dash_x = bar_x + bar_width + 8
        dash_y = bar_y
        dash_box = pygame.Rect(dash_x, dash_y, dash_size, dash_size)
        pygame.draw.rect(dm.canvas, (60, 60, 60), dash_box, border_radius=4)
        if player.dash_cooldown_ms:
            fill_ratio = 1.0 - (player.dash_cooldown_remaining_ms / player.dash_cooldown_ms)
        else:
            fill_ratio = 1.0
        fill_ratio = max(0.0, min(1.0, fill_ratio))
        fill_h = int(dash_size * fill_ratio)
        fill_rect = pygame.Rect(dash_x, dash_y + dash_size - fill_h, dash_size, fill_h)
        if fill_h > 0:
            pygame.draw.rect(dm.canvas, (120, 180, 255), fill_rect, border_radius=4)
        pygame.draw.rect(dm.canvas, (80, 80, 80), dash_box, 2, border_radius=4)

        # Score en bas à droite du profil
        score_text = font.render(f"* {score}", False, (255, 255, 255))
        score_pos = (profile_x + (profile_size[0] if profile_size[0] > 0 else 0) + 10, dm.virtual_res[1] - score_text.get_height() - 2)
        dm.canvas.blit(score_text, score_pos)

        # Temps écoulé (ne s'incrémente plus après game over)
        seconds = int(time_elapsed_ms / 500)
        minutes = seconds // 60
        seconds = seconds % 60
        time_text = font.render(f"{t('time_label')} {minutes:02d}:{seconds:02d}", False, (255, 255, 255))
        dm.canvas.blit(time_text, (dm.virtual_res[0] - time_text.get_width() - 12, 12))

        # Bouton pause
        btn_pause.draw(dm.canvas)

        if show_controls_hint:
            layout = settings.get("keyboard_layout", "azerty")
            controls_key = t("controls_hint_qwerty") if layout == "qwerty" else t("controls_hint_azerty")
            controls = font_body.render(controls_key, False, (150, 150, 150))
            dm.canvas.blit(controls, (150, 160))

        # Game Over
        if game_over:
            overlay = pygame.Surface(dm.canvas.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(180)
            dm.canvas.blit(overlay, (0, 0))

            center = dm.canvas.get_rect().center
            title_y = center[1] - 120

            go_text = font_big.render(t("game_over"), False, (255, 50, 50))
            dm.canvas.blit(go_text, go_text.get_rect(center=(center[0], title_y)))

            score_text = font.render(f"* {score}", False, (255, 255, 255))
            dm.canvas.blit(score_text, score_text.get_rect(center=(center[0], title_y + 70)))

            time_text = font.render(
                f"{t('time_label')} {minutes:02d}:{seconds:02d}", False, (255, 255, 255)
            )
            dm.canvas.blit(time_text, time_text.get_rect(center=(center[0], title_y + 110)))

            button_y = title_y + 160
            total_w = btn_width * 2 + btn_spacing
            start_x = center[0] - total_w // 2
            btn_menu.rect.topleft = (start_x, button_y)
            btn_retry.rect.topleft = (start_x + btn_width + btn_spacing, button_y)

            btn_menu.draw(dm.canvas)
            btn_retry.draw(dm.canvas)

        # Pause
        if paused and not game_over:
            overlay = pygame.Surface(dm.canvas.get_size())
            overlay.fill((0, 0, 0))
            overlay.set_alpha(150)
            dm.canvas.blit(overlay, (0, 0))

            center = dm.canvas.get_rect().center
            title_y = center[1] - 120

            pause_text = font_big.render(t("pause_title"), False, (255, 255, 255))
            dm.canvas.blit(pause_text, pause_text.get_rect(center=(center[0], title_y)))

            button_y = title_y + 110
            total_w = btn_width * 3 + btn_spacing * 2
            start_x = center[0] - total_w // 2
            btn_menu.rect.topleft = (start_x, button_y)
            btn_resume.rect.topleft = (start_x + btn_width + btn_spacing, button_y)
            btn_retry.rect.topleft = (start_x + (btn_width + btn_spacing) * 2, button_y)

            btn_menu.draw(dm.canvas)
            btn_resume.draw(dm.canvas)
            btn_retry.draw(dm.canvas)

        # Shop UI
        if shop_menu.is_open and not game_over:
            shop_menu.draw(dm.canvas)

        dm.render()
        clock.tick(60)
    
    return "menu"
