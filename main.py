import pygame
import sys

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Game logic / updates go here

    screen.fill((30, 30, 30))

    pygame.display.flip()

pygame.quit()
sys.exit()
