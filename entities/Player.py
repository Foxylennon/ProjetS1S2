"""
CLASSE JOUEUR - SIMPLIFIÉ
"""

import os

import pygame
from config import settings
from entities.Wall import check_wall_collision


def _load_gif_frames(path: str, return_durations: bool = False):
    """Charge les frames d'un GIF en tant que surfaces Pygame.

    Pygame ne gère pas nativement les GIF animés, donc on passe par Pillow
    si disponible. Si Pillow n'est pas installé, on se contente de charger
    l'image statique avec pygame.image.load.

    Si `return_durations` est vrai, la fonction renvoie (frames, durations_ms).
    """

    def _safe_convert(surf: pygame.Surface):
        try:
            return surf.convert_alpha()
        except pygame.error:
            return surf

    try:
        from PIL import Image
    except ImportError:
        # Pas de Pillow disponible : on charge juste l'image statique
        img = pygame.image.load(path)
        frames = [_safe_convert(img)]
        durations = [0]
        return (frames, durations) if return_durations else frames

    frames = []
    durations = []
    try:
        pil_img = Image.open(path)
    except Exception:
        # Fallback to pygame loader if Pillow ne peut pas ouvrir le fichier
        img = pygame.image.load(path)
        frames = [_safe_convert(img)]
        durations = [0]
        return (frames, durations) if return_durations else frames

    try:
        while True:
            pil_frame = pil_img.convert("RGBA")
            data = pil_frame.tobytes()
            size = pil_frame.size
            surf = pygame.image.fromstring(data, size, "RGBA")
            frames.append(_safe_convert(surf))
            durations.append(pil_img.info.get("duration", 50))
            pil_img.seek(pil_img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        # En dernier recours on charge une image statique
        img = pygame.image.load(path)
        frames = [_safe_convert(img)]
        durations = [0]

    return (frames, durations) if return_durations else frames


def _scale_preserve_aspect(surf: pygame.Surface, target_size: tuple[int, int]) -> pygame.Surface:
    """Redimensionne une surface tout en conservant son ratio d'aspect."""
    sw, sh = surf.get_size()
    tw, th = target_size
    if sw == 0 or sh == 0 or tw == 0 or th == 0:
        return surf

    scale = min(tw / sw, th / sh)
    new_size = (max(1, int(sw * scale)), max(1, int(sh * scale)))
    return pygame.transform.smoothscale(surf, new_size)


def _zoom_crop(surf: pygame.Surface, target_size: tuple[int, int], zoom: float) -> pygame.Surface:
    """Scale le sprite puis croppe pour garder un cadre carré (taille target_size)."""
    if zoom == 1.0:
        return _scale_preserve_aspect(surf, target_size)

    zoom_size = (int(target_size[0] * zoom), int(target_size[1] * zoom))
    zoomed = _scale_preserve_aspect(surf, zoom_size)

    out = pygame.Surface(target_size, pygame.SRCALPHA)
    ox = (target_size[0] - zoomed.get_width()) // 2
    oy = (target_size[1] - zoomed.get_height()) // 2
    out.blit(zoomed, (ox, oy))
    return out


class Player:
    def __init__(
        self,
        x,
        y,
        width=40,  # Hitbox rétrécie
        height=40, # Hitbox rétrécie
        *,
        player_id: int = 1,
        name: str | None = None,
        sprite_scale: float = 1.0,
        animation_speed: float = 2.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

        self.speed = 300
        self.health = 100
        self.max_health = 100

        # Attaque
        self.attack_damage = 34
        self.attack_range = 40
        self.attacking = False
        self.attack_rect = None
        self.attack_cooldown_ms = 0
        self.attack_cooldown_ms_default = 100  # 0.2s
        self.attack_time_elapsed_ms = 0
        self.attack_total_duration_ms = 0
        self.attack_frame_durations: list[int] = []
        self.attack_frame_index = 0
        self.attack_has_hit = False
        self.attack_speed = 1.5  # Multiplie la vitesse de l'animation d'attaque

        # Système de combo
        self.combo_level = 0  # 0, 1, 2 pour les 3 attaques
        self.combo_attack_pressed = False  # Si espace est pressé pendant l'animation
        self.attack_hit_frame = 1  # 2e frame (index 1)

        self.direction = 0  # 0=droite, 1=gauche, 2=bas, 3=haut
        self.previous_horizontal = 0  # 0=droite, 1=gauche, conservé selon dernier déplacement horizontal

        # Identité du joueur
        self.player_id = max(1, min(player_id, 4))
        self.display_name = name.strip() if name and name.strip() else f"P{self.player_id}"

        # Échelle d'affichage du sprite
        self.sprite_scale = sprite_scale
        self.sprite_size = (82, 56)  # sprite visuel, décorellé de self.width/height (hitbox)

        # Animation
        self.animation_speed = max(0.05, animation_speed)
        self.moving = False
        self.animation_frame = 0
        self.animation_timer_ms = 0
        self.animation_frame_duration_ms = 100.0 / self.animation_speed  # ms par frame

        # Chargement des sprites
        assets_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "player", f"p{self.player_id}")
        )
        idle_path = os.path.join(assets_dir, f"p{self.player_id}-idle.png")
        run_gif_path = os.path.join(assets_dir, f"p{self.player_id}-wasd.gif")

        try:
            self.idle_image = pygame.image.load(idle_path)
        except Exception:
            # Fallback en cas d'erreur
            self.idle_image = pygame.Surface(self.sprite_size, pygame.SRCALPHA)
            self.idle_image.fill((255, 255, 0))

        # Mettre à l'échelle sans déformer le sprite (conserver le ratio)
        self.idle_image = _zoom_crop(self.idle_image, self.sprite_size, self.sprite_scale)
        self.idle_image_left = pygame.transform.flip(self.idle_image, True, False)

        # Animation de course
        run_frames = _load_gif_frames(run_gif_path)
        if not run_frames:
            run_frames = [self.idle_image]
        self.run_frames_right = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in run_frames]
        self.run_frames_left = [pygame.transform.flip(f, True, False) for f in self.run_frames_right]

        # Animation d'attaque (système de combo avec 3 attaques)
        self.attack_animations = []
        for combo in range(1, 4):
            atk_path = os.path.join(assets_dir, "atk-ciseaux", f"p{self.player_id}-atk-ciseaux-{combo*4-3}-{combo*4}.gif")
            atk_frames, atk_durations = _load_gif_frames(atk_path, return_durations=True)
            if not atk_frames:
                atk_frames = [self.idle_image]
                atk_durations = [0]
            # On accélère l'animation d'attaque sans toucher à la vitesse de marche
            frame_durations = [
                max(1, int(d / (self.animation_speed * self.attack_speed))) for d in atk_durations
            ]
            total_duration = sum(frame_durations) or (len(atk_frames) * self.animation_frame_duration_ms)
            frames_right = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in atk_frames]
            frames_left = [pygame.transform.flip(f, True, False) for f in frames_right]
            self.attack_animations.append({
                'frames_right': frames_right,
                'frames_left': frames_left,
                'frame_durations': frame_durations,
                'total_duration': total_duration
            })

        # Utiliser la première attaque par défaut
        self.attack_frames_right = self.attack_animations[0]['frames_right']
        self.attack_frames_left = self.attack_animations[0]['frames_left']
        self.attack_frame_durations = self.attack_animations[0]['frame_durations']
        self.attack_total_duration_ms = self.attack_animations[0]['total_duration']

        # Dash / esquive
        self.dashing = False
        self.dash_time_remaining_ms = 0
        self.dash_cooldown_ms = 1000
        self.dash_cooldown_remaining_ms = 0
        self.dash_duration_ms = 100
        self.dash_speed = 700
        self.dash_vector = pygame.Vector2(0, 0)

        dash_path = os.path.join(assets_dir, f"p{self.player_id}-dash.png")
        try:
            dash_image = pygame.image.load(dash_path)
        except Exception:
            dash_image = pygame.Surface(self.sprite_size, pygame.SRCALPHA)
            dash_image.fill((255, 255, 255, 90))

        self.dash_image = _zoom_crop(dash_image, self.sprite_size, self.sprite_scale)
        self.dash_image_left = pygame.transform.flip(self.dash_image, True, False)

        self.color = (255, 255, 0)
    
    def handle_input(self, keys, walls=None, dt_ms=0):
        """Gère le déplacement du joueur."""
        dx = 0
        dy = 0

        layout = settings.get("keyboard_layout", "azerty")
        qwerty = layout == "qwerty"

        right_pressed = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        left_pressed = keys[pygame.K_LEFT] or (keys[pygame.K_a] if qwerty else keys[pygame.K_q])
        down_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s]
        up_pressed = keys[pygame.K_UP] or (keys[pygame.K_w] if qwerty else keys[pygame.K_z])
        dash_pressed = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        if dash_pressed and self.dash_cooldown_remaining_ms <= 0 and not self.dashing:
            dash_x = 0
            dash_y = 0
            if right_pressed:
                dash_x += 1
            if left_pressed:
                dash_x -= 1
            if down_pressed:
                dash_y += 1
            if up_pressed:
                dash_y -= 1

            if dash_x == 0 and dash_y == 0:
                if self.direction == 0:
                    dash_x = 1
                elif self.direction == 1:
                    dash_x = -1
                elif self.direction == 2:
                    dash_y = 1
                else:
                    dash_y = -1

            self.dash_vector = pygame.Vector2(dash_x, dash_y)
            if self.dash_vector.length_squared() == 0:
                self.dash_vector = pygame.Vector2(1, 0)
            self.dash_vector = self.dash_vector.normalize()
            self.dashing = True
            self.dash_time_remaining_ms = self.dash_duration_ms
            self.dash_cooldown_remaining_ms = self.dash_cooldown_ms

        if self.dashing:
            self.moving = True
            distance = self.dash_speed * (dt_ms / 1000.0) if dt_ms > 0 else 0
            dx = self.dash_vector.x * distance
            dy = self.dash_vector.y * distance
        else:
            if right_pressed:
                dx = self.speed
                self.direction = 0
                self.previous_horizontal = 0
            if left_pressed:
                dx = -self.speed
                self.direction = 1
                self.previous_horizontal = 1
            if down_pressed:
                dy = self.speed
                self.direction = 2
            if up_pressed:
                dy = -self.speed
                self.direction = 3

            self.moving = any([right_pressed, left_pressed, down_pressed, up_pressed])

            if dt_ms > 0:
                dx *= (dt_ms / 1000.0)
                dy *= (dt_ms / 1000.0)

        # Collision avec les murs
        if walls is not None and (dx != 0 or dy != 0):
            dx, dy = check_wall_collision(self.rect, walls, dx, dy)

        # Appliquer le déplacement
        self.x += dx
        self.y += dy

        # Limites de l'écran
        self.x = max(0, min(self.x, 1280 - self.width))
        self.y = max(0, min(self.y, 720 - self.height))

        # Mettre à jour le rectangle
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)
    
    def try_attack(self):
        """Lance une attaque en jouant l'animation GIF."""
        if self.attack_cooldown_ms > 0:
            return False

        # Si on est en train d'attaquer et que l'espace est pressé, préparer le combo suivant
        if self.attacking:
            self.combo_attack_pressed = True
            return False

        self.attacking = True
        self.attack_time_elapsed_ms = 0
        self.attack_cooldown_ms = self.attack_cooldown_ms_default
        self.attack_has_hit = False
        self.attack_frame_index = 0
        self.combo_attack_pressed = False

        # Utiliser l'animation du combo actuel
        anim = self.attack_animations[self.combo_level]
        self.attack_frames_right = anim['frames_right']
        self.attack_frames_left = anim['frames_left']
        self.attack_frame_durations = anim['frame_durations']
        self.attack_total_duration_ms = anim['total_duration']

        size = self.attack_range
        offset = 10

        if self.direction == 0:  # Droite
            self.attack_rect = pygame.Rect(self.rect.right - offset, self.rect.centery - size // 4, size + offset, size)
        elif self.direction == 1:  # Gauche
            self.attack_rect = pygame.Rect(self.rect.left - size, self.rect.centery - size // 4, size + offset, size)
        elif self.direction == 2:  # Bas
            self.attack_rect = pygame.Rect(self.rect.centerx - size // 4, self.rect.bottom - offset, size, size + offset)
        else:  # Haut
            self.attack_rect = pygame.Rect(self.rect.centerx - size // 4, self.rect.top - size, size, size + offset)

        return True
    
    def update(self, dt_ms: float = 0):
        """Met à jour les cooldowns et l'animation."""
        # Cooldown d'attaque (ms)
        if self.attack_cooldown_ms > 0:
            self.attack_cooldown_ms = max(0, self.attack_cooldown_ms - dt_ms)

        # Cooldown et durée du dash
        if self.dash_cooldown_remaining_ms > 0:
            self.dash_cooldown_remaining_ms = max(0, self.dash_cooldown_remaining_ms - dt_ms)
        if self.dashing:
            self.dash_time_remaining_ms = max(0, self.dash_time_remaining_ms - dt_ms)
            if self.dash_time_remaining_ms <= 0:
                self.dashing = False

        # Animation d'attaque (durée liée au gif)
        if self.attacking:
            self.attack_time_elapsed_ms += dt_ms

            # Déterminer l'index de la frame d'attaque actuelle
            self.attack_frame_index = 0
            if self.attack_frame_durations and self.attack_total_duration_ms > 0:
                accumulated = 0
                elapsed = min(self.attack_time_elapsed_ms, self.attack_total_duration_ms - 1)
                for i, duration in enumerate(self.attack_frame_durations):
                    accumulated += duration
                    if elapsed < accumulated:
                        self.attack_frame_index = i
                        break

            if self.attack_time_elapsed_ms >= self.attack_total_duration_ms:
                self.attacking = False
                self.attack_time_elapsed_ms = 0
                self.attack_rect = None
                self.attack_frame_index = 0
                # Gérer le combo
                if self.combo_attack_pressed and self.combo_level < 2:
                    self.combo_level += 1
                    self.try_attack()  # Lancer l'attaque suivante immédiatement
                else:
                    self.combo_level = 0  # Reset combo

        # Animation du joueur (idle vs marche)
        if self.moving and self.run_frames_right:
            self.animation_timer_ms += dt_ms
            if self.animation_timer_ms >= self.animation_frame_duration_ms:
                self.animation_timer_ms -= self.animation_frame_duration_ms
                self.animation_frame = (self.animation_frame + 1) % len(self.run_frames_right)
        else:
            self.animation_frame = 0
            self.animation_timer_ms = 0
    
    def check_attack_hit(self, enemy_rect, Walls):
        """Vérifie si l'attaque touche.

        - L'attaque ne peut toucher qu'une seule fois par coup.
        - La hitbox n'est active qu'à la 2e frame d'animation.
        """
        if not self.attacking or not self.attack_rect:
            return False

        # Les dégâts sont infligés seulement à la 2e frame (index 1)
        if self.attack_frame_index != self.attack_hit_frame:
            return False

        # Empêche plusieurs touches sur la même attaque
        if self.attack_has_hit:
            return False

        point_depart = self.rect.center
        point_arrivee = enemy_rect.center

        for wall in Walls:
            if wall.rect.clipline(point_depart, point_arrivee):
                return False

        if self.attack_rect.colliderect(enemy_rect):
            self.attack_has_hit = True
            return True

        return False
    
    def take_damage(self, amount):
        self.health -= amount
        return self.health <= 0
    
    def is_alive(self):
        return self.health > 0
    
    def draw(self, surface):
        # Sprite du joueur (idle / marche / attaque)
        if self.dashing:
            image = self.dash_image_left if self.previous_horizontal == 1 else self.dash_image
        elif self.attacking and (self.attack_frames_right or self.attack_frames_left):
            frames = self.attack_frames_left if self.previous_horizontal == 1 else self.attack_frames_right
            elapsed = min(self.attack_time_elapsed_ms, self.attack_total_duration_ms)

            frame_index = 0
            if self.attack_frame_durations and self.attack_total_duration_ms > 0:
                accumulated = 0
                for i, d in enumerate(self.attack_frame_durations):
                    accumulated += d
                    if elapsed < accumulated:
                        frame_index = i
                        break
                frame_index = frame_index % len(frames)

            image = frames[frame_index]
        elif self.moving and self.run_frames_right:
            frames = self.run_frames_left if self.previous_horizontal == 1 else self.run_frames_right
            image = frames[self.animation_frame % len(frames)]
        else:
            image = self.idle_image_left if self.previous_horizontal == 1 else self.idle_image

        image_rect = image.get_rect(center=self.rect.center)
        surface.blit(image, image_rect.topleft)

        # Zone d'attaque (visible seulement à partir de la 2ᵉ frame)
        if self.attacking and self.attack_rect and self.attack_frame_index >= 1:
            # Transparent + bordure blanche
            overlay = pygame.Surface((self.attack_rect.width, self.attack_rect.height), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 50))
            pygame.draw.rect(overlay, (255, 255, 255), overlay.get_rect(), 2)
            surface.blit(overlay, self.attack_rect.topleft)
        
        # Barre de vie
        bar_w, bar_h = 30, 4
        bar_x = self.rect.centerx - bar_w // 2
        bar_y = self.rect.y - 8
        
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        
        ratio = self.health / self.max_health
        fill_w = int(bar_w * ratio)
        color = (50, 255, 50) if ratio > 0.5 else (255, 255, 50) if ratio > 0.25 else (255, 50, 50)
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))

    def draw_name(self, surface, font):
        name_text = font.render(self.display_name, False, (255, 255, 255))
        text_rect = name_text.get_rect(center=(self.rect.centerx, self.rect.top - 18))
        surface.blit(name_text, text_rect)
