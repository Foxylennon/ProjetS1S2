import pygame
import ProjetS1S2.main_menu.Main_menu



# 1. base resolution
game_with,game_height = 1920,1080
target_ratio = game_with/game_height


pygame.init()

screen_x = 1920
screen_y = 1080

# 2. real window ( what the player sees)
screen = pygame.display.set_mode((screen_x, screen_y))

# 3. creating canvas ( the surface we're going to draw on )
canvas = pygame.Surface((game_with, game_height))

clock = pygame.time.Clock()
running = True

while running:
    screen.fill((0,0,0))

    #adjusting the canvas scale
    window_w, window_h = screen.get_size()
    scaled_canvas = pygame.transform.scale(canvas, (window_w, window_h))
    screen.blit(scaled_canvas, (0,0))

    # flip() the display to put your work on screen
    pygame.display.flip()

    clock.tick(60)  # limits FPS to 60

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.VIDEORESIZE:
            pass

pygame.quit()