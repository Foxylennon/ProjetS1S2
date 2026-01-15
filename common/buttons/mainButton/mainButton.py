import pygame


class Button:
    def __init__(self, width, height, text="", background_color=(0, 0, 0),
                 text_color=(255, 255, 255), text_size=20, text_font=None,
                 background="None", border=False, rounded_border=False,
                 border_radius=0, border_color=(0, 0, 0), border_width=0):

        # --- 1. Stockage des données de base ---
        self.rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.text_content = text
        self.background_color = background_color
        self.text_color = text_color
        self.background_image_path = background

        # Gestion des bordures
        self.border = border
        self.rounded_border = rounded_border
        self.border_color = border_color
        self.border_width = border_width

        if self.rounded_border and border_radius == 0:
            self.border_radius = 15
        else:
            self.border_radius = border_radius

        # --- 2. Chargement de la Police (Font) ---
        self.font = pygame.font.SysFont(text_font, text_size)
        self.text_surf = self.font.render(self.text_content, True, self.text_color)

        # --- 3. Chargement de l'image de fond (optionnel) ---
        self.bg_image = None
        if self.background_image_path != "None":
            try:
                loaded_img = pygame.image.load(self.background_image_path).convert_alpha()
                # On redimensionne l'image pour qu'elle rentre exactement dans le bouton
                self.bg_image = pygame.transform.scale(loaded_img, (width, height))
            except Exception as e:
                print(f"Erreur chargement image bouton: {e}")

    def draw(self, surface,x,y):
        # --- ÉTAPE 1 : DESSINER LE FOND ---
        self.rect = pygame.Rect(x, y, self.width, self.height)
        if self.bg_image:
            surface.blit(self.bg_image, self.rect)
        else:

            pygame.draw.rect(surface, self.background_color, self.rect, border_radius=self.border_radius)

        # --- ÉTAPE 2 : DESSINER LA BORDURE ---
        if self.border:

            pygame.draw.rect(surface, self.border_color, self.rect, self.border_width, border_radius=self.border_radius)

        # --- ÉTAPE 3 : DESSINER LE TEXTE ---
        if self.text_content != "":



            text_rect = self.text_surf.get_rect(center=self.rect.center)
            surface.blit(self.text_surf, text_rect)

    def is_hovered(self, mouse_pos):
        """Retourne True si la souris est sur le bouton"""
        return self.rect.collidepoint(mouse_pos)