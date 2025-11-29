# main.py
import pygame
import sys

from staff import Staff
from personnel_profile import draw_personnel_page

pygame.init()

WIDTH, HEIGHT = 800, 600
FPS = 60
MENU_HEIGHT = 40

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

# --- Positions that must always exist at game start ---
# Make sure these match keys in positions.json
KEY_POSITIONS = [
    "Site Director",
    "Chief of Security",
    "Chief Researcher",
]


def load_flag_image(path, size=(64, 40)):
    if not path:
        return None
    try:
        flag_img = pygame.image.load(path).convert_alpha()
        flag_img = pygame.transform.smoothscale(flag_img, size)
        return flag_img
    except pygame.error as e:
        print(f"Could not load flag image {path}: {e}")
        return None


# --- Generate starting staff roster ---
staff_roster = Staff(
    key_positions=KEY_POSITIONS,
    num_random=5,   # number of extra random staff
)

# Preload flag images for each member (index-aligned with roster.members)
flag_images = [load_flag_image(p.flag_path) for p in staff_roster.members]

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

        elif event.type == pygame.KEYDOWN:
            # Use left/right to cycle through available personnel
            if event.key == pygame.K_RIGHT:
                staff_roster.next()
            elif event.key == pygame.K_LEFT:
                staff_roster.previous()

    screen.fill((30, 30, 30))

    # draw menu bar
    draw_menu(screen, current_page)

    # draw current page content
    if current_page == "personnel":
        if len(staff_roster) > 0:
            person = staff_roster.current
            idx = staff_roster.current_index
            flag_image = flag_images[idx] if 0 <= idx < len(flag_images) else None

            draw_personnel_page(
                screen,
                person,
                flag_image,
                title_font,
                body_font,
                WIDTH,
                HEIGHT,
                MENU_HEIGHT,
                idx,
                len(staff_roster),
            )
    elif current_page == "anomalies":
        draw_anomalies_page(screen)

    pygame.display.flip()

pygame.quit()
sys.exit()
