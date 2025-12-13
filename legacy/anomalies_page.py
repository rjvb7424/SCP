# external imports
import pygame
# internal imports
from rework.ui_elements import draw_title_text, draw_header_text, draw_body_text, draw_primary_button, draw_secondary_button, get_attribute_color
from rework.ui_elements import COLOR, BODY_FONT

def _draw_attributes(surface, anomaly, x, y_start):
    """Draws the anomaly attributes table and returns the new y position."""
    table_width  = surface.get_width() - x - 40
    row_height   = 26
    bar_width    = 220
    bar_height   = 10

    y = y_start

    for row_index, (attr_name, value, is_known) in enumerate(anomaly.get_attribute_items()):
        # Human-readable label
        label = attr_name.replace("_", " ").title()

        # alternating row background
        row_rect = pygame.Rect(x, y, table_width, row_height)
        if row_index % 2 == 0:
            row_bg = (24, 24, 32)
        else:
            row_bg = (28, 28, 38)
        pygame.draw.rect(surface, row_bg, row_rect, border_radius=4)

        # attribute name
        name_surf = BODY_FONT.render(label, True, COLOR)
        name_y = y + (row_height - name_surf.get_height()) // 2
        surface.blit(name_surf, (x + 10, name_y))

        # bar background
        bar_x = x + 170
        bar_y = y + (row_height - bar_height) // 2
        bar_bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        pygame.draw.rect(surface, (18, 18, 24), bar_bg_rect, border_radius=3)
        pygame.draw.rect(surface, (70, 70, 90), bar_bg_rect, width=1, border_radius=3)

        # fill only if known
        if is_known:
            ratio = value / 20.0  # since lo=0, hi=20
            fill_width = int(bar_width * ratio)
            fill_color = get_attribute_color(value)
            fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
            pygame.draw.rect(surface, fill_color, fill_rect, border_radius=3)
            value_text = f"{value:2d}"
        else:
            # unknown – show a greyed-out overlay and '?'
            value_text = "?"
            unknown_overlay = pygame.Surface((bar_width, bar_height), pygame.SRCALPHA)
            unknown_overlay.fill((0, 0, 0, 90))
            surface.blit(unknown_overlay, (bar_x, bar_y))

        # numeric / '?' text to the right of the bar
        value_surf = BODY_FONT.render(value_text, True, COLOR)
        value_rect = value_surf.get_rect()
        value_rect.midleft = (bar_x + bar_width + 12, y + row_height // 2)
        surface.blit(value_surf, value_rect)

        y += row_height + 4

    return y


def draw_anomalies_page(surface, anomalies, selected_index, x, top_offset=0):
    """Draws the anomaly page and returns a dict of anomaly menu button rects."""
    # menu starts a bit below the top bar
    menu_y = top_offset + 8
    button_width = 140
    button_height = 28
    spacing = 8

    button_rects = {}

    button_x = x
    # --- top anomaly menu (tabs) ---
    for idx, anomaly in enumerate(anomalies):
        label = anomaly.get_name()
        if len(label) > 18:
            label = label[:15] + "..."

        if idx == selected_index:
            rect = draw_primary_button(surface, label, button_x, menu_y,
                                       button_width, button_height)
        else:
            rect = draw_secondary_button(surface, label, button_x, menu_y,
                                         button_width, button_height)

        button_rects[idx] = rect
        button_x += button_width + spacing

    # --- selected anomaly details ---
    selected = anomalies[selected_index]

    y = menu_y + button_height + 24

    # anomaly name as title
    y = draw_title_text(surface, selected.get_name(), x, y)
    y += 10

    # containment procedures
    y = draw_header_text(surface, "Special Containment Procedures:", x, y)
    y = draw_body_text(surface, selected.get_containment_procedures(), x, y)

    # attributes
    y += 12
    y = draw_header_text(surface, "Statistics:", x, y)
    y += 4
    y = _draw_attributes(surface, selected, x, y)

    return button_rects