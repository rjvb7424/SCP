# sidebar_menu.py
import pygame
from ui_elements import draw_title_text, draw_secondary_button, draw_primary_button

def draw_sidebar(surface, sidebar_width, current_page, pages, top_offset=0):
    """
    pages: list of (page_id, label)
    """
    height = surface.get_height()

    # sidebar background starts below the top bar
    rect = pygame.Rect(0, top_offset, sidebar_width, height - top_offset)
    pygame.draw.rect(surface, (15, 15, 22), rect)

    # vertical separator
    pygame.draw.line(surface, (60, 60, 80),
                     (sidebar_width, top_offset),
                     (sidebar_width, height))

    x = 16
    y = top_offset + 18

    y = draw_title_text(surface, "Navigation", x, y)

    button_width = sidebar_width - 2 * x
    button_height = 32
    spacing = 8

    rects = {}

    for page_id, label in pages:
        is_current = (page_id == current_page)
        if is_current:
            r = draw_primary_button(surface, label, x, y, button_width, button_height)
        else:
            r = draw_secondary_button(surface, label, x, y, button_width, button_height)

        rects[page_id] = r
        y += button_height + spacing

    return rects
