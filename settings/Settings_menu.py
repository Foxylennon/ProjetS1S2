"""Page des paramètres (Settings)."""

import pygame

from lang import t
from config import settings


class Dropdown:
    """Menu déroulant simple."""

    def __init__(self, x, y, width, height, options, selected_index=0, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options  # list of (label, value)
        self.selected_index = selected_index
        self.is_open = False
        self.font = font

    @property
    def selected(self):
        return self.options[self.selected_index]

    def draw(self, surface):
        # Base
        color = (70, 70, 70)
        hover_color = (100, 100, 100)
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), self.rect, 2, border_radius=6)

        # Texte du choix actuel
        label = self.selected[0]
        text_surf = self.font.render(label, False, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(midleft=(self.rect.x + 12, self.rect.centery)))

        # Flèche
        arrow = "▼" if not self.is_open else "▲"
        arrow_surf = self.font.render(arrow, False, (255, 255, 255))
        surface.blit(arrow_surf, arrow_surf.get_rect(midright=(self.rect.right - 12, self.rect.centery)))

        # Liste des options ouvertes
        if self.is_open:
            for i, (label, _) in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                pygame.draw.rect(surface, hover_color if i == self.selected_index else color, option_rect, border_radius=6)
                pygame.draw.rect(surface, (180, 180, 180), option_rect, 2, border_radius=6)
                text_surf = self.font.render(label, False, (255, 255, 255))
                surface.blit(text_surf, text_surf.get_rect(midleft=(option_rect.x + 12, option_rect.centery)))

    def handle_click(self, mouse_pos):
        if self.rect.collidepoint(mouse_pos):
            self.is_open = not self.is_open
            return True

        if self.is_open:
            for i, _ in enumerate(self.options):
                option_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                if option_rect.collidepoint(mouse_pos):
                    self.selected_index = i
                    self.is_open = False
                    return True

        return False


class Button:
    def __init__(self, x, y, width, height, text, font, color=(70, 70, 70), hover_color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), self.rect, 2, border_radius=6)
        text_surf = self.font.render(self.text, False, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed


class Slider:
    """Barre horizontale pour ajuster une valeur continue."""

    def __init__(self, x, y, width, height, min_value, max_value, value, font, color=(70, 70, 70)):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.font = font
        self.color = color
        self.dragging = False

    def _value_to_pos(self):
        fraction = (self.value - self.min_value) / (self.max_value - self.min_value)
        return int(self.rect.x + fraction * self.rect.width)

    def _pos_to_value(self, x):
        fraction = (x - self.rect.x) / self.rect.width
        fraction = max(0.0, min(1.0, fraction))
        return self.min_value + fraction * (self.max_value - self.min_value)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=6)
        pygame.draw.rect(surface, (180, 180, 180), self.rect, 2, border_radius=6)

        handle_x = self._value_to_pos()
        handle_r = self.rect.height // 2
        pygame.draw.circle(surface, (220, 220, 220), (handle_x, self.rect.centery), handle_r)
        pygame.draw.circle(surface, (120, 120, 120), (handle_x, self.rect.centery), handle_r, 2)

        # Affiche la valeur (par exemple 1.0x)
        label = f"{self.value:.2f}x"
        text_surf = self.font.render(label, False, (255, 255, 255))
        surface.blit(text_surf, text_surf.get_rect(midleft=(self.rect.right + 12, self.rect.centery)))

    def handle_event(self, mouse_pos, mouse_pressed):
        if mouse_pressed:
            if self.rect.collidepoint(mouse_pos):
                self.dragging = True
                self.value = self._pos_to_value(mouse_pos[0])
                return True
        else:
            self.dragging = False

        if self.dragging:
            self.value = self._pos_to_value(mouse_pos[0])
            return True

        return False


def settings_menu(dm):
    """Page de paramètres."""
    print("--- SETTINGS ---")

    # --- Valeurs modifiables ---
    resolution_values = [
        ("resolution_1920x1080", (1920, 1080)),
        ("resolution_1366x768", (1366, 768)),
        ("resolution_1536x864", (1536, 864)),
        ("resolution_1280x720", (1280, 720)),
    ]
    language_values = [
        ("lang_english", "en"),
        ("lang_french", "fr"),
    ]

    # Indices sélectionnés
    current_res = settings.get("resolution", (1280, 720))
    res_index = next((i for i, (_, v) in enumerate(resolution_values) if v == current_res), 3)

    current_lang = settings.get("language", "en")
    lang_index = next((i for i, (_, v) in enumerate(language_values) if v == current_lang), 0)

    # UI
    dropdown_w = 360
    dropdown_h = 50
    spacing_y = 90
    column_gap = 80

    res_dropdown = Dropdown(0, 0, dropdown_w, dropdown_h, [], selected_index=res_index, font=None)
    lang_dropdown = Dropdown(0, 0, dropdown_w, dropdown_h, [], selected_index=lang_index, font=None)

    slider_width = 640
    text_slider = Slider(0, 0, slider_width, 28, min_value=0.5, max_value=2.0, value=settings.get("text_scale", 1.0), font=None)

    btn_back = Button(0, 0, 240, 50, t("button_back"), None)

    clock = pygame.time.Clock()

    while True:
        mouse_clicked = False
        mouse_pos = dm.get_mouse()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        # --- Fonts (recalculées selon la taille de texte) ---
        text_scale = settings.get("text_scale", 1.0)
        font_title = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", max(12, int(56 * text_scale)))
        font = pygame.font.Font("assets/fonts/PressStart2P-Regular.ttf", max(10, int(28 * text_scale)))

        # Mise à jour des labels (en cas de changement de langue)
        resolutions = [(t(key), value) for key, value in resolution_values]
        languages = [(t(key), value) for key, value in language_values]
        res_dropdown.options = resolutions
        lang_dropdown.options = languages

        # Mise à jour du layout (colonne gauche / colonne droite)
        center_x = dm.virtual_res[0] // 2
        left_x = center_x - dropdown_w - column_gap // 2
        right_x = center_x + column_gap // 2
        top_y = 220

        res_dropdown.rect.topleft = (left_x, top_y)
        lang_dropdown.rect.topleft = (right_x, top_y)

        # Calculer la hauteur nécessaire pour afficher les options du menu déroulant
        max_options = max(len(resolution_values), len(language_values))
        dropdown_area_height = (max_options + 1) * dropdown_h

        slider_x = center_x - slider_width // 2
        slider_y = top_y + dropdown_area_height + 40
        text_slider.rect.topleft = (slider_x, slider_y)
        text_slider.font = font

        btn_back.rect.topleft = (center_x - btn_back.rect.width // 2, slider_y + 90)
        btn_back.font = font

        res_dropdown.font = font
        lang_dropdown.font = font

        # --- MISE À JOUR DES ÉTATS ---
        btn_back.update(mouse_pos)

        if text_slider.handle_event(mouse_pos, mouse_clicked):
            settings["text_scale"] = text_slider.value

        if mouse_clicked:
            if res_dropdown.handle_click(mouse_pos):
                lang_dropdown.is_open = False
                selected_res = resolution_values[res_dropdown.selected_index][1]
                settings["resolution"] = selected_res
                dm.change_resolution(*selected_res)
            elif lang_dropdown.handle_click(mouse_pos):
                res_dropdown.is_open = False
                selected_lang = language_values[lang_dropdown.selected_index][1]
                settings["language"] = selected_lang
                from lang import set_language
                set_language(selected_lang)
            elif btn_back.is_clicked(mouse_pos, True):
                return "menu"
            else:
                # Clic hors des menus déroulants : fermer les listes
                res_dropdown.is_open = False
                lang_dropdown.is_open = False

        # --- AFFICHAGE ---
        dm.canvas.fill((40, 40, 40))

        title = font_title.render(t("settings_title"), False, (255, 255, 255))
        dm.canvas.blit(title, title.get_rect(center=(center_x, 120)))

        # Labels en colonnes
        label_ws = font.render(t("window_size_label"), False, (220, 220, 220))
        dm.canvas.blit(label_ws, (left_x, top_y - 40))

        label_lang = font.render(t("language_label"), False, (220, 220, 220))
        dm.canvas.blit(label_lang, (right_x, top_y - 40))

        # Slider (taille du texte)
        label_slider = font.render(t("text_size_label"), False, (220, 220, 220))
        dm.canvas.blit(label_slider, (slider_x, slider_y - 40))
        text_slider.draw(dm.canvas)

        # Dropdowns + bouton
        res_dropdown.draw(dm.canvas)
        lang_dropdown.draw(dm.canvas)
        btn_back.draw(dm.canvas)

        dm.render()
        clock.tick(60)
