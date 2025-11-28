import pygame
import sys

from personnel import Personnel

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

person = Personnel()

font = pygame.font.Font(None, 26)

def draw_text(surface, text, x, y, font, color=(220, 220, 220)):
    """Draw a line of text and return the next y position."""
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + 4


running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Game logic / updates go here

    screen.fill((30, 30, 30))

    x = 40
    y = 40

    # header / name
    y = draw_text(screen, "Personnel File", x, y, font, (255, 255, 255))
    y = draw_text(screen, f"Name: {person.fname} {person.lname}", x, y, font)
    y = draw_text(screen, f"Gender: {person.gender}", x, y, font)
    y += 10  # extra gap

    y = draw_text(screen, "Attributes:", x, y, font, (255, 255, 255))

    for attr_name in sorted(person.attributes.keys()):
        value = person.attributes[attr_name]
        line = f" - {attr_name.replace('_', ' ').title()}: {value}"
        y = draw_text(screen, line, x, y, font)

    pygame.display.flip()

pygame.quit()
sys.exit()
