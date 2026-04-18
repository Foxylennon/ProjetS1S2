"""
CLASSE ENNEMI - SIMPLIFIÉ
"""

import os
import pygame
import math
import random
from entities.Wall import check_wall_collision


def _load_gif_frames(path: str, return_durations: bool = False):
    def _safe_convert(surf: pygame.Surface):
        try:
            return surf.convert_alpha()
        except pygame.error:
            return surf

    try:
        from PIL import Image
    except ImportError:
        img = pygame.image.load(path)
        frames = [_safe_convert(img)]
        durations = [0]
        return (frames, durations) if return_durations else frames

    frames = []
    durations = []
    try:
        pil_img = Image.open(path)
    except Exception:
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
            durations.append(pil_img.info.get("duration", 100))
            pil_img.seek(pil_img.tell() + 1)
    except EOFError:
        pass

    if not frames:
        img = pygame.image.load(path)
        frames = [_safe_convert(img)]
        durations = [0]

    return (frames, durations) if return_durations else frames


def _scale_preserve_aspect(surf: pygame.Surface, target_size: tuple[int, int]) -> pygame.Surface:
    sw, sh = surf.get_size()
    tw, th = target_size
    if sw == 0 or sh == 0 or tw == 0 or th == 0:
        return surf

    scale = min(tw / sw, th / sh)
    new_size = (max(1, int(sw * scale)), max(1, int(sh * scale)))
    return pygame.transform.smoothscale(surf, new_size)


def _zoom_crop(surf: pygame.Surface, target_size: tuple[int, int], zoom: float) -> pygame.Surface:
    if zoom == 1.0:
        return _scale_preserve_aspect(surf, target_size)

    zoom_size = (int(target_size[0] * zoom), int(target_size[1] * zoom))
    zoomed = _scale_preserve_aspect(surf, zoom_size)

    out = pygame.Surface(target_size, pygame.SRCALPHA)
    ox = (target_size[0] - zoomed.get_width()) // 2
    oy = (target_size[1] - zoomed.get_height()) // 2
    out.blit(zoomed, (ox, oy))
    return out


class Enemy:
    TYPE_IDS = {
        "tumor": 1,
        "bacteria": 2,
        "virus": 3,
        "caillot": 4,
    }

    def __init__(self, x, y, width=24, height=24, monster_type="tumor", *, clone=False):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

        self.monster_type = monster_type if monster_type in self.TYPE_IDS else "tumor"
        self.clone = clone

        self.speed = 150
        self.max_health = 300 if self.monster_type == "caillot" else 100
        self.health = self.max_health
        self.damage = 10 if self.monster_type in ("tumor", "bacteria") else 0
        self.attack_range = 40 if self.monster_type in ("tumor", "bacteria") else 0
        self.detection_radius = 260 if self.monster_type in ("tumor", "bacteria") else 0

        if self.monster_type == "tumor":
            width = 26
            height = 26
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, self.width, self.height)

        self.animation_speed = 2.0
        self.pending_clone = False

        self.damage_cooldown_ms = 0
        self.damage_cooldown_ms_default = 800

        self.state = "idle"
        self.moving = False
        self.facing_left = False
        self.previous_horizontal = False

        self.sprite_scale = 1.0
        self.sprite_size = (103, 103) if self.monster_type == "tumor" else (110, 110)

        self.animation_frame = 0
        self.animation_timer_ms = 0
        self.animation_frame_durations = []

        self.attack_frames = []
        self.attack_frame_durations = []
        self.attack_frame_index = 0
        self.attack_hit_frame = 3
        self.attacking = False
        self.attack_has_hit = False
        self.attack_rect = None
        self.attack_variant_index = 0
        self.spawn_clone = False
        self.spawned_clone = False

        self.hit_time_ms = 0
        self.hit_duration_ms = 180

        self.faint_frames = []
        self.faint_durations = []

        self.skill_a_frames = []
        self.skill_a_durations = []
        self.skill_b_frames = []
        self.skill_b_durations = []
        self.skill_b_timer = 0

        self.heal_frames = []
        self.heal_durations = []
        self.heal_b4loop = None
        self.heal_timer = 0
        self.heal_tick_ms = 1200
        self.healing_target = None
        self.heal_phase = "idle"

        self.caillot_phase = "moving"
        self.caillot_phase_timer = 0
        self.caillot_velocity = (0, 0)

        self.path = []
        self.last_path_update = 0
        self.path_update_interval = 500
        self.current_target_pos = None

        self.immobility_timer = 0

        self._load_assets()

    def _get_attack_hit_frame(self, variant_index=None):
        if self.monster_type == "tumor":
            return min(5, len(self.attack_frames) - 1)
        if self.monster_type == "bacteria":
            if variant_index is None:
                variant_index = self.attack_variant_index
            return 7 if variant_index == 0 else 5
        return 0

    def _trigger_bacteria_skill(self):
        if self.monster_type != "bacteria":
            return
        self.attacking = False
        self.attack_rect = None
        self.attack_has_hit = True
        self.pending_clone = False
        self._set_state("skill_a")
        self.skill_b_timer = 1000

    def _load_assets(self):
        assets_dir = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "assets", "sprites", "monster", f"mob-{self.monster_type}")
        )

        def _load_static(path):
            try:
                img = pygame.image.load(path)
                return img.convert_alpha()
            except Exception:
                return pygame.Surface(self.sprite_size, pygame.SRCALPHA)

        def _load_frames(path):
            frames, durations = _load_gif_frames(path, return_durations=True)
            if not frames:
                frames = [_load_static(path)]
                durations = [100]
            return frames, durations

        if self.monster_type == "caillot":
            self.idle_frames, self.idle_durations = _load_frames(os.path.join(assets_dir, "mob-caillot-idle.gif"))
        elif self.monster_type == "virus":
            self.idle_frames, self.idle_durations = _load_frames(os.path.join(assets_dir, "mob-virus-idle.gif"))
        else:
            self.idle_frames = [_load_static(os.path.join(assets_dir, f"mob-{self.monster_type}-idle.png"))]
            self.idle_durations = [0]

        self.idle_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.idle_frames]
        self.idle_frames_left = [pygame.transform.flip(f, True, False) for f in self.idle_frames]

        if self.monster_type in ("tumor", "bacteria"):
            run_path = os.path.join(assets_dir, f"mob-{self.monster_type}-wasd-front.gif")
            self.run_frames, self.run_durations = _load_frames(run_path)
            self.run_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.run_frames]
            self.run_frames_left = [pygame.transform.flip(f, True, False) for f in self.run_frames]
        else:
            self.run_frames = self.idle_frames
            self.run_frames_left = self.idle_frames_left
            self.run_durations = self.idle_durations

        if self.monster_type == "tumor":
            self.attack_frames, self.attack_frame_durations = _load_frames(os.path.join(assets_dir, "mob-tumor-atk.gif"))
            self.attack_variant_frames = [self.attack_frames]
            self.attack_hit_frames = [self._get_attack_hit_frame(0)]
        elif self.monster_type == "bacteria":
            atk1, atk1_d = _load_frames(os.path.join(assets_dir, "mob-bacteria-atk1.gif"))
            atk2, atk2_d = _load_frames(os.path.join(assets_dir, "mob-bacteria-atk2.gif"))
            self.attack_variant_frames = [atk1, atk2]
            self.attack_variant_durations = [atk1_d, atk2_d]
            self.attack_frames = self.attack_variant_frames[self.attack_variant_index]
            self.attack_frame_durations = self.attack_variant_durations[self.attack_variant_index]
            self.attack_hit_frames = [self._get_attack_hit_frame(0), self._get_attack_hit_frame(1)]
        else:
            self.attack_frames = [self.idle_frames[0]]
            self.attack_frame_durations = [100]
            self.attack_variant_frames = [self.attack_frames]
            self.attack_variant_durations = [self.attack_frame_durations]
            self.attack_hit_frames = [0]

        if self.monster_type == "bacteria":
            self.skill_a_frames, self.skill_a_durations = _load_frames(os.path.join(assets_dir, "mob-bacteria-skill-a.gif"))
            self.skill_b_frames, self.skill_b_durations = _load_frames(os.path.join(assets_dir, "mob-bacteria-skill-b.gif"))
            self.skill_a_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.skill_a_frames]
            self.skill_a_frames_left = [pygame.transform.flip(f, True, False) for f in self.skill_a_frames]
            self.skill_b_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.skill_b_frames]
            self.skill_b_frames_left = [pygame.transform.flip(f, True, False) for f in self.skill_b_frames]
        else:
            self.skill_a_frames = []
            self.skill_a_frames_left = []
            self.skill_b_frames = []
            self.skill_b_frames_left = []

        if self.monster_type == "virus":
            self.heal_b4loop = _zoom_crop(_load_static(os.path.join(assets_dir, "mob-virus-heal-b4loop.png")), self.sprite_size, self.sprite_scale)
            self.heal_frames, self.heal_durations = _load_frames(os.path.join(assets_dir, "mob-virus-heal.gif"))
            self.heal_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.heal_frames]
            self.heal_frames_left = [pygame.transform.flip(f, True, False) for f in self.heal_frames]
        else:
            self.heal_b4loop = None
            self.heal_frames = []
            self.heal_frames_left = []
            self.heal_durations = []

        faint_path = os.path.join(assets_dir, f"mob-{self.monster_type}-faint.gif")
        self.faint_frames, self.faint_durations = _load_frames(faint_path)
        self.faint_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.faint_frames]
        self.faint_frames_left = [pygame.transform.flip(f, True, False) for f in self.faint_frames]

        hit_path = os.path.join(assets_dir, f"mob-{self.monster_type}-hit.png")
        self.hit_image = _zoom_crop(_load_static(hit_path), self.sprite_size, self.sprite_scale)
        self.hit_image_left = pygame.transform.flip(self.hit_image, True, False)

        self.attack_frames = [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.attack_frames]
        self.attack_frames_left = [pygame.transform.flip(f, True, False) for f in self.attack_frames]
        if self.monster_type == "bacteria":
            self.attack_variant_frames = [
                [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.attack_variant_frames[0]],
                [_zoom_crop(f, self.sprite_size, self.sprite_scale) for f in self.attack_variant_frames[1]],
            ]
            self.attack_frames = self.attack_variant_frames[self.attack_variant_index]
            self.attack_frames_left = [pygame.transform.flip(f, True, False) for f in self.attack_frames]

    def _set_state(self, state_name: str):
        self.state = state_name
        self.animation_frame = 0
        self.animation_timer_ms = 0
        self.attack_has_hit = False
        self.spawn_clone = False
        if state_name == "idle":
            self.attacking = False
            self.attack_rect = None

    def _update_facing(self, dx: float, dy: float):
        if abs(dx) > abs(dy) and dx != 0:
            self.facing_left = dx < 0
            self.previous_horizontal = self.facing_left
        elif dy != 0:
            self.facing_left = self.previous_horizontal

    def _open_attack(self):
        self.attacking = True
        self.attack_has_hit = False
        self.attack_rect = pygame.Rect(
            self.rect.centerx - 30,
            self.rect.centery - 30,
            60,
            60,
        )
        self._set_state("attacking")
        if self.monster_type == "bacteria":
            current_variant = self.attack_variant_index
            self.attack_frames = self.attack_variant_frames[current_variant]
            self.attack_frame_durations = self.attack_variant_durations[current_variant]
            self.attack_frames_left = [pygame.transform.flip(f, True, False) for f in self.attack_frames]
            self.attack_hit_frame = self.attack_hit_frames[current_variant]
            self.attack_variant_index ^= 1
        else:
            self.attack_hit_frame = self._get_attack_hit_frame(0)

    def _start_faint(self):
        self._set_state("faint")
        self.attacking = False
        self.attack_rect = None

    def _start_hit(self):
        self.hit_time_ms = self.hit_duration_ms
        self._set_state("hit")

    def _move_towards(self, target_rect, walls, dt_ms: float, stop_distance: float = 2.0):
        diff_x = target_rect.centerx - self.rect.centerx
        diff_y = target_rect.centery - self.rect.centery
        dist = math.hypot(diff_x, diff_y)
        if dist <= stop_distance:
            self.moving = False
            return

        vx = diff_x / dist * self.speed
        vy = diff_y / dist * self.speed
        if dt_ms > 0:
            vx *= dt_ms / 1000.0
            vy *= dt_ms / 1000.0

        self._update_facing(vx, vy)
        self.moving = True

        if walls is not None and (vx != 0 or vy != 0):
            vx, vy = check_wall_collision(self.rect, walls, vx, vy)

        self.x += vx
        self.y += vy
        self.rect.x = int(self.x)
        self.rect.y = int(self.y)

    def _update_caillot(self, dt_ms: float, walls):
        if self.caillot_phase_timer <= 0:
            if self.caillot_phase == "moving":
                self.caillot_phase = "waiting"
                self.caillot_phase_timer = random.randint(2000, 5000)
                self.caillot_velocity = (0, 0)
                self.moving = False
            else:
                self.caillot_phase = "moving"
                self.caillot_phase_timer = random.randint(5000, 10000)
                angle = random.random() * math.pi * 2
                self.caillot_velocity = (math.cos(angle) * self.speed, math.sin(angle) * self.speed)
                self._update_facing(self.caillot_velocity[0], self.caillot_velocity[1])
                self.moving = True

        self.caillot_phase_timer -= dt_ms
        if self.caillot_phase == "moving":
            vx, vy = self.caillot_velocity
            if dt_ms > 0:
                vx *= dt_ms / 1000.0
                vy *= dt_ms / 1000.0
            if walls is not None and (vx != 0 or vy != 0):
                vx, vy = check_wall_collision(self.rect, walls, vx, vy)
            self.x += vx
            self.y += vy
            self.rect.x = int(self.x)
            self.rect.y = int(self.y)
        else:
            self.moving = False

    def is_alive(self):
        return self.health > 0

    def _choose_heal_target(self, allies):
        if not allies:
            return None
        wounded = [ally for ally in allies if ally is not self and ally.health < ally.max_health and ally.is_alive()]
        if not wounded:
            return None
        wounded.sort(key=lambda m: (m.health, m.rect.centerx, m.rect.centery))
        return wounded[0]

    def _update_virus(self, allies, dt_ms: float, walls):
        target = self._choose_heal_target(allies)
        if target:
            self.healing_target = target
            if self.state != "healing":
                self._set_state("healing")
                self.heal_phase = "b4loop"
            self._move_towards(target.rect, walls, dt_ms, stop_distance=10.0)
            self.heal_timer += dt_ms
            if self.heal_timer >= self.heal_tick_ms:
                self.heal_timer -= self.heal_tick_ms
                target.health = min(target.max_health, target.health + 1)
                if target.health >= target.max_health:
                    self.healing_target = None
            return

        self.heal_timer = 0
        self.healing_target = None
        self.moving = False
        self._set_state("idle")

    def _player_in_range(self, player_rect):
        if self.detection_radius <= 0:
            return True
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        return math.hypot(dx, dy) <= self.detection_radius

    def _advance_animation(self, dt_ms: float):
        spawned = []
        if self.state == "hit":
            if self.hit_time_ms > 0:
                self.hit_time_ms -= dt_ms * self.animation_speed
                if self.hit_time_ms <= 0:
                    self._set_state("idle")
            return spawned

        frames, durations = self._get_current_animation()
        if not frames:
            return spawned

        if self.state == "attacking":
            self.attack_frame_index = self.animation_frame

        duration = durations[self.animation_frame] if self.animation_frame < len(durations) else durations[-1]
        self.animation_timer_ms += dt_ms * self.animation_speed
        if self.animation_timer_ms >= duration:
            self.animation_timer_ms -= duration
            self.animation_frame += 1
            if self.monster_type == "bacteria" and self.state == "skill_a":
                if self.animation_frame == 10:  # 11th frame (0-based)
                    clone = Enemy(self.x + 10, self.y, monster_type="bacteria", clone=True)
                    clone.x += 6
                    clone.rect.x = int(clone.x)
                    clone._set_state("skill_b")
                    clone.facing_left = self.facing_left
                    spawned.append(clone)
                elif self.animation_frame == 11:  # 12th frame
                    self.x -= 3
                    self.rect.x = int(self.x)
            if self.animation_frame >= len(frames):
                if self.state == "healing" and self.heal_phase == "b4loop":
                    self.heal_phase = "heal"
                    self.animation_frame = 0
                elif self.state in ("attacking", "skill_a", "skill_b", "healing", "faint"):
                    spawned.extend(self._on_action_complete())
                    return spawned
                else:
                    self.animation_frame = 0

        if self.state == "attacking":
            self.attack_frame_index = self.animation_frame
        return spawned

    def _get_current_animation(self):
        if self.state == "faint":
            return self.faint_frames, self.faint_durations
        if self.state == "hit":
            return [self.hit_image], [self.hit_duration_ms]
        if self.state == "attacking":
            return self.attack_frames, self.attack_frame_durations
        if self.state == "skill_a":
            return self.skill_a_frames, self.skill_a_durations
        if self.state == "skill_b":
            return self.skill_b_frames, self.skill_b_durations
        if self.state == "healing":
            if self.heal_phase == "b4loop":
                return [self.heal_b4loop], [100]
            elif self.heal_frames:
                return self.heal_frames, self.heal_durations
            elif self.heal_b4loop:
                return [self.heal_b4loop], [100]
            return self.idle_frames, self.idle_durations
        if self.moving:
            return self.run_frames, self.run_durations
        return self.idle_frames, self.idle_durations

    def _on_action_complete(self):
        spawned = []
        if self.state == "attacking":
            self.attacking = False
            self.attack_rect = None
            if self.monster_type == "bacteria" and not self.pending_clone and not self.spawned_clone:
                self._trigger_bacteria_skill()
            else:
                self._set_state("idle")
        elif self.state == "skill_a":
            self.immobility_timer = 1000
            self._set_state("idle")
        elif self.state == "skill_b":
            self.immobility_timer = 1000
            self._set_state("idle")
        elif self.state == "healing":
            self._set_state("idle")
        elif self.state == "faint":
            self.animation_frame = len(self.faint_frames) - 1
        return spawned

    def _update_attack_rect(self):
        self.attack_rect = pygame.Rect(self.rect.centerx - 30, self.rect.centery - 30, 60, 60)

    def update(self, player_rect, walls=None, dt_ms: float = 0, nav_grid=None, allies=None):
        spawned = []
        if self.health <= 0:
            if self.state != "faint":
                self._start_faint()
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.monster_type == "caillot":
            if self.state != "faint":
                if self.state != "waiting" and self.state != "moving":
                    self._set_state("idle")
                self._update_caillot(dt_ms, walls)
                spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.monster_type == "virus":
            self._update_virus(allies, dt_ms, walls)
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.hit_time_ms > 0:
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.immobility_timer > 0:
            self.immobility_timer -= dt_ms
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.state in ("skill_a", "skill_b"):
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.state == "attacking":
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if not self._player_in_range(player_rect):
            self.moving = False
            self._set_state("idle")
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        if self.is_in_attack_range(player_rect, self.attack_range):
            self._open_attack()
            self._update_attack_rect()
            spawned.extend(self._advance_animation(dt_ms))
            return spawned

        self._move_towards(player_rect, walls, dt_ms)
        if self.state != "attacking":
            self._set_state("moving")
        spawned.extend(self._advance_animation(dt_ms))
        return spawned

    def attack_can_hit(self, target_rect):
        if not self.attacking or self.attack_has_hit:
            return False
        if self.attack_frame_index == self.attack_hit_frame and self.attack_rect and self.attack_rect.colliderect(target_rect):
            self.attack_has_hit = True
            return True
        return False

    def is_in_attack_range(self, player_rect, range_px: float = 10):
        if self.monster_type not in ("tumor", "bacteria"):
            return False
        dx = player_rect.centerx - self.rect.centerx
        dy = player_rect.centery - self.rect.centery
        return math.hypot(dx, dy) <= range_px

    def deal_damage_to_player(self, player_health):
        if self.damage > 0 and self.attack_has_hit:
            self.attack_has_hit = True
            player_health -= self.damage
        return player_health

    def take_damage(self, amount):
        self.health -= amount
        if self.health > 0:
            self._start_hit()
        else:
            self._start_faint()
        return self.health <= 0

    def is_faint_animation_complete(self):
        return self.state == "faint" and self.animation_frame >= len(self.faint_frames) - 1

    def _select_image(self):
        if self.state == "hit":
            return self.hit_image
        frames, _ = self._get_current_animation()
        if not frames:
            return self.hit_image
        frame = min(self.animation_frame, len(frames) - 1)
        return frames[frame]

    def draw(self, surface):
        image = self._select_image()
        if self.facing_left and image is not None:
            image = pygame.transform.flip(image, True, False)

        if image is not None:
            rect = image.get_rect(center=self.rect.center)
            surface.blit(image, rect.topleft)

        bar_w, bar_h = self.width, 4
        bar_x, bar_y = self.rect.x, self.rect.y - 8
        pygame.draw.rect(surface, (60, 60, 60), (bar_x, bar_y, bar_w, bar_h))
        ratio = max(0.0, min(1.0, self.health / self.max_health))
        fill_w = int(bar_w * ratio)
        color = (50, 255, 50) if ratio > 0.5 else (255, 255, 50) if ratio > 0.25 else (255, 50, 50)
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_w, bar_h))
