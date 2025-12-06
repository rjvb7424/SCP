import pygame
from ui_elements import draw_title_text, draw_primary_button, draw_secondary_button

SIDEBAR_WIDTH = 200

# (internal ID, label)
PAGES = [
    ("anomalies", "Anomalies"),
    ("anomaly",   "Anomaly Detail"),
    ("research",  "Research"),
    ("facility",  "Facility"),
]

def draw_sidebar(surface, current_page):
    """Draws the left navigation sidebar and returns a dict of button rects."""
    height = surface.get_height()

    # sidebar background
    pygame.draw.rect(surface, (15, 15, 22), (0, 0, SIDEBAR_WIDTH, height))
    # vertical separator
    pygame.draw.line(surface, (60, 60, 80), (SIDEBAR_WIDTH, 0), (SIDEBAR_WIDTH, height))

    x = 16
    y = 18

    # "Navigation" title
    y = draw_title_text(surface, "Navigation", x, y)

    button_width = SIDEBAR_WIDTH - 2 * x
    button_height = 32
    spacing = 8

    rects = {}

    for page_id, label in PAGES:
        is_current = (page_id == current_page)

        if is_current:
            rect = draw_primary_button(surface, label, x, y, button_width, button_height)
        else:
            rect = draw_secondary_button(surface, label, x, y, button_width, button_height)

        rects[page_id] = rect
        y += button_height + spacing

    return rects
