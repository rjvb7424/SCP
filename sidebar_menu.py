# external imports
import pygame
# internal imports
from ui_elements import draw_title_text, draw_primary_button, draw_secondary_button

def draw_sidebar(surface, sidebar_width, current_page, pages):
    """Draws a navigation sidebar on the left and returns a dict of button rects."""
    height = surface.get_height()

    # sidebar background
    pygame.draw.rect(surface, (15, 15, 22), (0, 0, sidebar_width, height))
    # vertical separator
    pygame.draw.line(surface, (60, 60, 80), (sidebar_width, 0), (sidebar_width, height))

    x = 16
    y = 18
    y = draw_title_text(surface, "Navigation", x, y)
    y+= 12

    button_width = sidebar_width - 2 * x
    button_height = 32
    spacing = 8

    rects = {}

    for page_id, label in pages:
        is_current = (page_id == current_page)
        # page is currently selected, draw primary button style
        if is_current:
            rect = draw_primary_button(surface, label, x, y, button_width, button_height)
        # page is not selected, draw secondary button style
        else:
            rect = draw_secondary_button(surface, label, x, y, button_width, button_height)
        # store the button rect for event handling
        rects[page_id] = rect
        y += button_height + spacing

    return rects
