import pygame


def game(dm):
    print("--- JEU LANCÉ ---")

    player_rect = pygame.Rect(10, 10, 16, 16)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu" # Retour au menu
            if event.type == pygame.VIDEORESIZE:
                dm.calc_scale()

        # Logique simple de mouvement
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]: player_rect.x += 1
        if keys[pygame.K_LEFT]: player_rect.x -= 1
        if keys[pygame.K_DOWN]: player_rect.y += 1
        if keys[pygame.K_UP]: player_rect.y -= 1

        # Dessin
        dm.canvas.fill((20, 20, 20)) # Fond gris sombre
        pygame.draw.rect(dm.canvas, (255, 255, 0), player_rect) # Joueur jaune

        dm.render()