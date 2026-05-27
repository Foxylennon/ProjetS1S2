"""Page des paramètres (Settings)."""

import pygame

from lang import t
from config import settings


from ui.UI_utils import Button, load_font, load_body_font, Dropdown


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
    keyboard_layout_values = [
        ("layout_azerty", "azerty"),
        ("layout_qwerty", "qwerty"),
    ]

    # Indices sélectionnés
    current_res = settings.get("resolution", (1280, 720))
    res_index = next((i for i, (_, v) in enumerate(resolution_values) if v == current_res), 3)

    current_lang = settings.get("language", "en")
    lang_index = next((i for i, (_, v) in enumerate(language_values) if v == current_lang), 0)

    current_layout = settings.get("keyboard_layout", "azerty")
    layout_index = next((i for i, (_, v) in enumerate(keyboard_layout_values) if v == current_layout), 0)

    # UI
    dropdown_w = 360
    dropdown_h = 50
    spacing_y = 90
    column_gap = 80

    res_dropdown = Dropdown(0, 0, dropdown_w, dropdown_h, [], selected_index=res_index, font=None)
    lang_dropdown = Dropdown(0, 0, dropdown_w, dropdown_h, [], selected_index=lang_index, font=None)
    layout_dropdown = Dropdown(0, 0, dropdown_w, dropdown_h, [], selected_index=layout_index, font=None)

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
                # Navigation clavier dans les dropdowns ouverts
                if event.key in [pygame.K_UP, pygame.K_DOWN]:
                    if res_dropdown.is_open:
                        res_dropdown.navigate_keyboard(event.key)
                    elif lang_dropdown.is_open:
                        lang_dropdown.navigate_keyboard(event.key)
                    elif layout_dropdown.is_open:
                        layout_dropdown.navigate_keyboard(event.key)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        # --- Fonts ---
        font_title = pygame.font.Font("assets/fonts/PressStart2P.ttf", 56)
        font = load_font(28)
        font_body = load_body_font(24)

        # Mise à jour des labels (en cas de changement de langue)
        resolutions = [(t(key), value) for key, value in resolution_values]
        languages = [(t(key), value) for key, value in language_values]
        layouts = [(t(key), value) for key, value in keyboard_layout_values]
        res_dropdown.options = resolutions
        lang_dropdown.options = languages
        layout_dropdown.options = layouts

        # Mise à jour du layout (colonnes)
        center_x = dm.virtual_res[0] // 2
        left_x = center_x - dropdown_w - column_gap // 2
        right_x = center_x + column_gap // 2
        top_y = 220

        res_dropdown.rect.topleft = (left_x, top_y)
        lang_dropdown.rect.topleft = (right_x, top_y)
        layout_dropdown.rect.topleft = (left_x, top_y + dropdown_h + 45)

        # Calculer la hauteur minimale nécessaire pour afficher les dropdowns et leurs options
        dropdown_area_height = 4 * dropdown_h

        btn_back.rect.topleft = (center_x - btn_back.rect.width // 2, top_y + dropdown_area_height + 60)
        btn_back.font = font_body

        res_dropdown.font = font_body
        lang_dropdown.font = font_body
        layout_dropdown.font = font_body

        # --- MISE À JOUR DES ÉTATS ---
        btn_back.update(mouse_pos)

        if mouse_clicked:
            res_action = res_dropdown.handle_click(mouse_pos)
            if res_action == 'select':
                lang_dropdown.is_open = False
                layout_dropdown.is_open = False
                selected_res = resolution_values[res_dropdown.selected_index][1]
                settings["resolution"] = selected_res
                dm.change_resolution(*selected_res)
            elif res_action == 'toggle':
                lang_dropdown.is_open = False
                layout_dropdown.is_open = False
            else:
                lang_action = lang_dropdown.handle_click(mouse_pos)
                if lang_action == 'select':
                    res_dropdown.is_open = False
                    layout_dropdown.is_open = False
                    selected_lang = language_values[lang_dropdown.selected_index][1]
                    settings["language"] = selected_lang
                    from lang import set_language
                    set_language(selected_lang)
                elif lang_action == 'toggle':
                    res_dropdown.is_open = False
                    layout_dropdown.is_open = False
                else:
                    layout_action = layout_dropdown.handle_click(mouse_pos)
                    if layout_action == 'select':
                        res_dropdown.is_open = False
                        lang_dropdown.is_open = False
                        selected_layout = keyboard_layout_values[layout_dropdown.selected_index][1]
                        settings["keyboard_layout"] = selected_layout
                    elif layout_action == 'toggle':
                        res_dropdown.is_open = False
                        lang_dropdown.is_open = False
                    elif btn_back.is_clicked(mouse_pos, True):
                        return "menu"
                    else:
                        # Clic hors des menus déroulants : fermer les listes
                        res_dropdown.is_open = False
                        lang_dropdown.is_open = False
                        layout_dropdown.is_open = False

        # --- AFFICHAGE ---
        dm.canvas.fill((40, 40, 40))

        title_text = t("settings_title")
        title_font = font_title
        # if any(ord(c) > 127 for c in title_text):  # change pas de police stp
        #    title_font = font_body
        title = title_font.render(title_text, False, (255, 255, 255))
        dm.canvas.blit(title, title.get_rect(center=(center_x, 120)))

        # Labels en colonnes
        label_ws = font_body.render(t("window_size_label"), False, (220, 220, 220))
        dm.canvas.blit(label_ws, (left_x, top_y - 30))

        label_layout = font_body.render(t("layout_label"), False, (220, 220, 220))
        dm.canvas.blit(label_layout, (left_x, top_y + 10 + dropdown_h))

        label_lang = font_body.render(t("language_label"), False, (220, 220, 220))
        dm.canvas.blit(label_lang, (right_x, top_y - 30))

        # Dropdowns + bouton
        btn_back.draw(dm.canvas)
        for dropdown in sorted([res_dropdown, layout_dropdown, lang_dropdown], key=lambda d: d.rect.y, reverse=True):
            dropdown.draw(dm.canvas)

        dm.render()
        clock.tick(60)
