import pygame
import sys

from personnel import Personnel

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
MENU_HEIGHT = 40

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

person = Personnel()

# Fonts
body_font = pygame.font.Font(None, 26)
menu_font = pygame.font.Font(None, 24)

# Simple “tabs” at the top
menu_items = [
    {"name": "Personnel File", "page": "personnel", "rect": pygame.Rect(20, 5, 150, 30)},
    {"name": "Anomalies",      "page": "anomalies", "rect": pygame.Rect(190, 5, 150, 30)},
]

current_page = "personnel"   # which page is currently active


def draw_text(surface, text, x, y, font, color=(220, 220, 220)):
    """Draw a line of text and return the next y position."""
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + 4


def draw_menu(surface, current_page):
    """Draw the top menu bar with tabs."""
    # background bar
    pygame.draw.rect(surface, (20, 20, 20), (0, 0, WIDTH, MENU_HEIGHT))

    for item in menu_items:
        is_active = (item["page"] == current_page)
        rect = item["rect"]

        # Different color if this tab is selected
        bg = (60, 60, 60) if is_active else (40, 40, 40)
        border = (120, 120, 120)

        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, border, rect, width=1, border_radius=4)

        text_surf = menu_font.render(item["name"], True, (230, 230, 230))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)


def draw_personnel_page(surface):
    x = 40
    y = MENU_HEIGHT + 20  # start below the menu

    y = draw_text(surface, "Personnel File", x, y, body_font, (255, 255, 255))
    y = draw_text(surface, f"Name: {person.fname} {person.lname}", x, y, body_font)
    y = draw_text(surface, f"Gender: {person.gender}", x, y, body_font)
    y += 10

    y = draw_text(surface, "Attributes:", x, y, body_font, (255, 255, 255))

    for attr_name in sorted(person.attributes.keys()):
        value = person.attributes[attr_name]
        line = f" - {attr_name.replace('_', ' ').title()}: {value}"
        y = draw_text(surface, line, x, y, body_font)


def draw_anomalies_page(surface):
    x = 40
    y = MENU_HEIGHT + 20

    y = draw_text(surface, "Contained Anomalies", x, y, body_font, (255, 255, 255))
    y += 10
    # placeholder content
    y = draw_text(surface, "- SCP-173: Euclid", x, y, body_font)
    y = draw_text(surface, "- SCP-049: Euclid", x, y, body_font)
    y = draw_text(surface, "- SCP-682: Keter", x, y, body_font)
    # later you can turn this into a proper list from your own classes


running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # check if you clicked any of the menu items
            for item in menu_items:
                if item["rect"].collidepoint(mx, my):
                    current_page = item["page"]

    screen.fill((30, 30, 30))

    # draw menu bar
    draw_menu(screen, current_page)

    # draw current page content
    if current_page == "personnel":
        draw_personnel_page(screen)
    elif current_page == "anomalies":
        draw_anomalies_page(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
