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
from entities.Wall import create_level_walls

from ui.UI_utils import Button, load_font


def game(dm):
    """Partie en cours"""
    print("--- JEU SOLO ---")
    
    # pos player when game starts
    player = Player(50, 50, player_id=1, name="P1")

    # player profile
    profile_img_orig = None
    try:
        profile_img_orig = pygame.image.load("assets/ui/profile-p1.png").convert_alpha()
    except Exception:
        profile_img_orig = None

    # profile img
    profile_img = None
    profile_size = (0, 0)
    if profile_img_orig is not None:
        ratio = profile_img_orig.get_width() / profile_img_orig.get_height()
        profile_size = (int(192 * ratio), 192)
        profile_img = pygame.transform.smoothscale(profile_img_orig, profile_size)

    MONSTER_TYPES = ["tumor", "bacteria", "virus", "caillot"]

    # murs et grille de pathfinding
    walls = create_level_walls()

    def _is_spawn_position_free(x, y):
        candidate = pygame.Rect(int(x), int(y), 24, 24)
        return not any(candidate.colliderect(w.rect) for w in walls)

    def _random_spawn_position():
        for _ in range(30):
            spawn_x = random.randint(50, 1230)
            spawn_y = random.randint(50, 670)
            if _is_spawn_position_free(spawn_x, spawn_y):
                return spawn_x, spawn_y
        return 1000, 500

    spawn_x, spawn_y = _random_spawn_position()
    enemies = [Enemy(spawn_x, spawn_y, monster_type=random.choice(MONSTER_TYPES))]
    max_enemies = 12
    spawn_timer_ms = random.randint(2000, 5000)
    # stats : score & timer
    score = 0
    time_elapsed_ms = 0
    # "+1"
    popups = []  # liste de {'text', 'pos', 'ttl', 'vy'}

    from entities.Pathfinding import NavGrid
    nav_grid = NavGrid(1280, 720, 32)
    nav_grid.add_walls(walls)
    
    # fonts
    font = load_font(32)
    font_big = load_font(56)
    font_small = load_font(18)

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

    clock = pygame.time.Clock()
    
    while True:
        dt = clock.tick(60)

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

                if event.key == pygame.K_SPACE and not game_over and not paused: # game: player atk
                    player.try_attack()

                if event.key == pygame.K_p and not game_over: # game: btn 'Pause' pressed
                    paused = not paused 

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        # --- LOGIQUE ---
        mouse_pos = dm.get_mouse()
        btn_pause.update(mouse_pos)

        if mouse_clicked and btn_pause.is_clicked(mouse_pos, True) and not game_over:
            paused = not paused

        if not game_over and not paused:
            time_elapsed_ms += dt

            # Generation d'ennemis supplémentaires (jusqu'à max_enemies)
            if len(enemies) < max_enemies:
                spawn_timer_ms -= dt
                if spawn_timer_ms <= 0:
                    spawn_timer_ms = random.randint(2000, 5000)
                    spawn_x, spawn_y = _random_spawn_position()
                    enemies.append(Enemy(spawn_x, spawn_y, monster_type=random.choice(MONSTER_TYPES)))

            # Mouvement du joueur
            keys = pygame.key.get_pressed()
            player.handle_input(keys, walls, dt)
            player.update(dt)

            spawned_enemies = []
            for enemy in enemies[:]:
                if enemy.is_alive():
                    spawned_enemies.extend(enemy.update(player.rect, walls, dt, nav_grid, enemies))

                    if enemy.attack_can_hit(player.rect):
                        player.health = enemy.deal_damage_to_player(player.health)
                        if not player.is_alive():
                            game_over = True

                    if player.check_attack_hit(enemy.rect, walls):
                        enemy.take_damage(player.attack_damage)
                else:
                    enemies.remove(enemy)
                    score += 1
                    popups.append({
                        "text": "+1",
                        "pos": list(enemy.rect.center),
                        "ttl": 800,
                        "vy": -0.03,
                    })

            enemies.extend(spawned_enemies)

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

        # --- AFFICHAGE ---
        if play_bg is not None:
            dm.canvas.blit(play_bg, (0, 0))
        else:
            dm.canvas.fill((30, 30, 30))
        
        # Murs
        for wall in walls:
            wall.draw(dm.canvas)
        
        # Ennemi
        for enemy in enemies:
            if enemy.is_alive():
                enemy.draw(dm.canvas)
        
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
            dm.canvas.blit(profile_img, (profile_x, profile_y))

        hp_text = font.render(f"{t('hp_label')} {player.health}/{player.max_health}", False, (255, 255, 255))
        hp_pos = (profile_x + 8, profile_y + ((profile_size[1] if profile_size[1] > 0 else 24) // 2) - (hp_text.get_height() // 2))
        dm.canvas.blit(hp_text, hp_pos)

        score_text = font.render(f"{t('score_label')} {score}", False, (255, 255, 255))
        score_pos = (profile_x + (profile_size[0] if profile_size[0] > 0 else 0) + 48, hp_pos[1])
        dm.canvas.blit(score_text, score_pos)

        # Temps écoulé (ne s'incrémente plus après game over)
        seconds = int(time_elapsed_ms / 1000)
        minutes = seconds // 60
        seconds = seconds % 60
        time_text = font.render(f"{t('time_label')} {minutes:02d}:{seconds:02d}", False, (255, 255, 255))
        dm.canvas.blit(time_text, (dm.virtual_res[0] - time_text.get_width() - 12, 12))

        # Bouton pause
        btn_pause.draw(dm.canvas)

        controls = font.render(t("controls_hint"), False, (150, 150, 150))
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

            score_text = font.render(f"{t('score_label')}: {score}", False, (255, 255, 255))
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

        dm.render()
        clock.tick(60)
    
    return "menu"
