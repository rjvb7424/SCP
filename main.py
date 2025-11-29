import pygame
import sys

from personnel import Personnel
from personnel_profile import draw_personnel_page

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
MENU_HEIGHT = 40

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

person = Personnel()

# Load flag image once, based on the person's nationality
flag_image = None
if getattr(person, "flag_path", None):
    try:
        flag_image = pygame.image.load(person.flag_path).convert_alpha()
        flag_image = pygame.transform.smoothscale(flag_image, (64, 40))
    except pygame.error as e:
        print(f"Could not load flag image {person.flag_path}: {e}")
        flag_image = None

# Fonts
title_font = pygame.font.Font(None, 32)
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
    pygame.draw.rect(surface, (20, 20, 20), (0, 0, WIDTH, MENU_HEIGHT))

    for item in menu_items:
        is_active = (item["page"] == current_page)
        rect = item["rect"]

        bg = (60, 60, 60) if is_active else (40, 40, 40)
        border = (120, 120, 120)

        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, border, rect, width=1, border_radius=4)

        text_surf = menu_font.render(item["name"], True, (230, 230, 230))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)


def draw_anomalies_page(surface):
    x = 40
    y = MENU_HEIGHT + 20

    y = draw_text(surface, "Contained Anomalies", x, y, body_font, (255, 255, 255))
    y += 10
    y = draw_text(surface, "- SCP-173: Euclid", x, y, body_font)
    y = draw_text(surface, "- SCP-049: Euclid", x, y, body_font)
    y = draw_text(surface, "- SCP-682: Keter", x, y, body_font)
    # later: replace with real anomaly list


running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for item in menu_items:
                if item["rect"].collidepoint(mx, my):
                    current_page = item["page"]

    screen.fill((30, 30, 30))

    # draw menu bar
    draw_menu(screen, current_page)

    # draw current page content
    if current_page == "personnel":
        draw_personnel_page(
            screen,
            person,
            flag_image,
            title_font,
            body_font,
            WIDTH,
            HEIGHT,
            MENU_HEIGHT,
        )
    elif current_page == "anomalies":
        draw_anomalies_page(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
