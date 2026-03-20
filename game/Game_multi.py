"""
JEU MULTIJOUEUR AVEC MURS
"""

import pygame
from config import settings
from lang import t
from entities.Player import Player
from entities.Enemy import Enemy
from entities.Wall import create_level_walls

FONT_PATH = "assets/fonts/PressStart2P-Regular.ttf"

def load_font(size):
    scale = settings.get("text_scale", 1.0)
    size = max(6, int(size * scale))
    try:
        return pygame.font.Font(FONT_PATH, size)
    except Exception:
        return pygame.font.SysFont(None, size)


class Button:
    """Bouton simple pour l'écran de fin de partie."""

    def __init__(self, x, y, width, height, text, font, color=(70, 70, 70), hover_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, (150, 150, 150), self.rect, 2, border_radius=5)
        text_surf = self.font.render(self.text, False, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed


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

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True

            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        other_pos = network.get_other_player_pos()

        if not game_over and not victory:
            keys = pygame.key.get_pressed()
            player.handle_input(keys, walls)
            player.update(dt)

            if network.is_host:
                if enemy.is_alive():
                    enemy.update(player.rect, walls, dt)

                    if enemy.is_in_attack_range(player.rect, 10):
                        player.health = enemy.deal_damage_to_player(player.health)
                        if not player.is_alive():
                            game_over = True

                    if player.check_attack_hit(enemy.rect, walls):
                        enemy.take_damage(player.attack_damage)
                else:
                    victory = True
            else:
                # Le client ne calcule pas l'ennemi, il affiche simplement la position reçue
                if "enemy_health" in other_pos and other_pos["enemy_health"] <= 0:
                    enemy.health = 0
                elif "enemy_health" in other_pos:
                    enemy.health = other_pos["enemy_health"]
                if "enemy_x" in other_pos and "enemy_y" in other_pos:
                    enemy.rect.x = other_pos["enemy_x"]
                    enemy.rect.y = other_pos["enemy_y"]
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

        # Réseau
        if network.is_host:
            network.send_position(
                player.rect.x,
                player.rect.y,
                #enemy_x=enemy.rect.x,
                #enemy_y=enemy.rect.y,
                #enemy_health=enemy.health,
                #victory=victory,
            )
        else:
            network.send_position(player.rect.x, player.rect.y)

        other_pos = network.get_other_player_pos()
        if "x" in other_pos and "y" in other_pos:
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
        role_label = t("host_label") if network.is_host else t("client_label")
        dm.canvas.blit(font.render(role_label, False, (255, 255, 255)), (12, 12))
        dm.canvas.blit(font.render(f"{t('hp_label')} {player.health}", False, (255, 255, 255)), (12, 25))

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
        
        clock.tick(60)
    
    return "menu"
