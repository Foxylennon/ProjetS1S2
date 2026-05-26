import pygame
from ui.UI_utils import Button, load_font
from lang import t

class ShopCard:
    def __init__(self, x, y, width, height, bg_color, item_data, font, font_small):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.item_data = item_data
        self.font = font
        self.font_small = font_small
        self.is_hovered = False
        self.purchased = False
        
        # Load image
        self.image = None
        try:
            img = pygame.image.load(item_data["img_path"]).convert_alpha()
            # Scale image to fit inside card
            self.image = pygame.transform.smoothscale(img, (120, 120))
        except Exception as e:
            print(f"Error loading image {item_data['img_path']}: {e}")

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.is_hovered and mouse_pressed

    def draw(self, surface):
        # Hover effect et couleur si acheté
        if self.purchased:
            color = (150, 150, 150)
        else:
            color = (min(255, self.bg_color[0] + 30), min(255, self.bg_color[1] + 30), min(255, self.bg_color[2] + 30)) if self.is_hovered else self.bg_color
        
        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 5
        shadow_rect.x += 5
        pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=10)

        # Card Background
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        
        # Card Border
        pygame.draw.rect(surface, (20, 20, 20), self.rect, 4, border_radius=10)

        # Draw cost (top left)
        if self.purchased:
            cost_text = self.font_small.render("VENDU", True, (20, 20, 20))
        else:
            cost_text = self.font_small.render(f"* {self.item_data['cost']}", True, (20, 20, 20))
        surface.blit(cost_text, (self.rect.x + 15, self.rect.y + 15))

        # Draw image (center top)
        if self.image:
            img_x = self.rect.x + (self.rect.width - self.image.get_width()) // 2
            surface.blit(self.image, (img_x, self.rect.y + 40))

        # Draw title line
        pygame.draw.line(surface, (20, 20, 20), (self.rect.x + 15, self.rect.y + 175), (self.rect.x + self.rect.width - 15, self.rect.y + 175), 2)
        
        title_text = self.font.render(t(self.item_data["name_key"]), True, (20, 20, 20))
        # Scale title if it's too big
        if title_text.get_width() > self.rect.width - 30:
            scale = (self.rect.width - 30) / title_text.get_width()
            title_text = pygame.transform.smoothscale(title_text, (int(title_text.get_width() * scale), int(title_text.get_height() * scale)))
        
        surface.blit(title_text, (self.rect.x + 15, self.rect.y + 185))

        # Draw stats box
        stats_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 225, self.rect.width - 30, 80)
        pygame.draw.rect(surface, (240, 240, 240), stats_rect, border_radius=5)
        pygame.draw.rect(surface, (20, 20, 20), stats_rect, 2, border_radius=5)

        # Draw stat lines
        y_offset = stats_rect.y + 10
        for stat in self.item_data["stats"]:
            stat_text = self.font_small.render(f"- {stat}", True, (20, 20, 20))
            surface.blit(stat_text, (stats_rect.x + 10, y_offset))
            y_offset += 25


class ShopMenu:
    def __init__(self, virtual_res):
        self.is_open = False
        self.virtual_res = virtual_res
        self.font_big = load_font(48)
        self.font = load_font(20)
        self.font_small = load_font(14)
        
        # Colors from the image: purple, green, light green, light grey
        self.colors = [(210, 180, 240), (160, 240, 160), (200, 255, 180), (230, 230, 230)]
        
        self.available_items = [
            {
                "id": "anticorps", "name_key": "item_damage", "cost": 10,
                "img_path": "assets/ui/item_protein/item-protein-anticorps.png",
                "stats": ["ATK +1", "CRIT +5%"],
                "effect": lambda p: setattr(p, 'attack_damage', p.attack_damage + 1)
            },
            {
                "id": "collagene", "name_key": "item_max_hp", "cost": 10,
                "img_path": "assets/ui/item_protein/item-protein-collagene.png",
                "stats": ["MAX HP +10"],
                "effect": lambda p: (setattr(p, 'max_health', p.max_health + 10), setattr(p, 'health', p.health + 10))
            },
            {
                "id": "hemoglobine", "name_key": "item_heal", "cost": 5,
                "img_path": "assets/ui/item_protein/item-protein-hemoglobine.png",
                "stats": ["HP +20"],
                "effect": lambda p: setattr(p, 'health', min(p.health + 20, p.max_health))
            },
            {
                "id": "lactase", "name_key": "item_speed", "cost": 10,
                "img_path": "assets/ui/item_protein/item-protein-lactase.png",
                "stats": ["SPEED +50"],
                "effect": lambda p: setattr(p, 'speed', p.speed + 50)
            }
        ]

        self.cards = []
        self.leave_button = Button(self.virtual_res[0] - 160, self.virtual_res[1] - 60, 140, 44, t("button_leave"), self.font_small, color=(100, 70, 70), hover_color=(130, 90, 90))
        
        # Setup layout
        card_w, card_h = 240, 340
        spacing = 30
        total_w = 4 * card_w + 3 * spacing
        start_x = (self.virtual_res[0] - total_w) // 2
        start_y = (self.virtual_res[1] - card_h) // 2 + 20

        for i, item in enumerate(self.available_items):
            x = start_x + i * (card_w + spacing)
            card = ShopCard(x, start_y, card_w, card_h, self.colors[i % len(self.colors)], item, self.font, self.font_small)
            self.cards.append(card)

        # Bottom text for prompt
        self.prompt_text = "CLICK POUR ACHETER"

    def update(self, mouse_pos, mouse_clicked, keys, player, current_score):
        """Update logic, returns new score if an item was bought."""
        if not self.is_open:
            return current_score

        hovered_card = None
        for card in self.cards:
            card.update(mouse_pos)
            if card.is_hovered:
                hovered_card = card

        self.leave_button.update(mouse_pos)
        if mouse_clicked and self.leave_button.is_clicked(mouse_pos, True):
            self.is_open = False
            return current_score

        buy_attempted = mouse_clicked and hovered_card is not None and not hovered_card.purchased

        if buy_attempted:
            cost = hovered_card.item_data["cost"]
            if current_score >= cost: # We use score as currency
                new_score = current_score - cost
                
                # Apply effect
                if hovered_card.item_data["effect"] is not None:
                    hovered_card.item_data["effect"](player)
                
                hovered_card.purchased = True
                
                self.is_open = False # Close shop after buy
                return new_score
                
        return current_score

    def draw(self, surface):
        if not self.is_open:
            return

        # Overlay
        overlay = pygame.Surface(self.virtual_res)
        overlay.fill((100, 90, 100))
        overlay.set_alpha(200)
        surface.blit(overlay, (0, 0))

        # Title
        title_surf = self.font_big.render(t("shop_title"), True, (255, 255, 255))
        surface.blit(title_surf, ((self.virtual_res[0] - title_surf.get_width()) // 2, 40))
        
        prompt_surf = self.font.render(self.prompt_text, True, (255, 255, 255))
        surface.blit(prompt_surf, ((self.virtual_res[0] - prompt_surf.get_width()) // 2, 110))

        # Cards
        for card in self.cards:
            card.draw(surface)

        self.leave_button.draw(surface)
