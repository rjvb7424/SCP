# top_bar.py
import pygame
from ui_elements import BODY_FONT, HEADER_FONT, COLOR

TOP_BAR_HEIGHT = 40  # pixels


def draw_top_bar(surface, resources):
    """
    Draws a global top bar across the whole window.

    resources: dict with keys like:
      - "site_name"
      - "funds"
      - "staff"
      - "date"
    """
    width = surface.get_width()

    # background
    bar_rect = pygame.Rect(0, 0, width, TOP_BAR_HEIGHT)
    pygame.draw.rect(surface, (15, 15, 22), bar_rect)
    # bottom border
    pygame.draw.line(surface, (70, 70, 90), (0, TOP_BAR_HEIGHT), (width, TOP_BAR_HEIGHT))

    padding_x = 16
    center_y = TOP_BAR_HEIGHT // 2

    # left side: site name / title
    title_text = resources.get("site_name", "Site-13 Control")
    title_surf = HEADER_FONT.render(title_text, True, COLOR)
    title_rect = title_surf.get_rect(midleft=(padding_x, center_y))
    surface.blit(title_surf, title_rect)

    # right side: funds, staff, date
    info_strings = []
    if "funds" in resources:
        info_strings.append(f"Funds: ${resources['funds']:,}")
    if "staff" in resources:
        info_strings.append(f"Staff: {resources['staff']}")
    if "date" in resources:
        info_strings.append(f"Date: {resources['date']}")

    x = width - padding_x
    for text in reversed(info_strings):  # draw from right to left
        surf = BODY_FONT.render(text, True, COLOR)
        rect = surf.get_rect(midright=(x, center_y))
        surface.blit(surf, rect)
        x -= rect.width + 24  # gap between items
