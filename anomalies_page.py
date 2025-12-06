# external imports
from ui_elements import draw_title_text, draw_header_text, draw_body_text, draw_primary_button, draw_secondary_button

def draw_anomalies_page(surface, anomalies, selected_index, x):
    """Draws the anomaly detail page and returns a dict of anomaly menu button rects."""
    # initialise positions
    menu_y = 16
    button_width = 140
    button_height = 28
    spacing = 8

    button_rects = {}

    button_x = x
    # for each anomaly, draw a button in the menu
    for idx, anomaly in enumerate(anomalies):
        label = anomaly.get_name()
        # truncate long names so buttons stay neat
        if len(label) > 18:
            label = label[:15] + "..."
        if idx == selected_index:
            # highlight selected anomaly
            rect = draw_primary_button(surface, label, button_x, menu_y, button_width, button_height)
        else:
            rect = draw_secondary_button(surface, label, button_x, menu_y, button_width, button_height)
        # store button rect for event handling
        button_rects[idx] = rect
        # increment x for next button
        button_x += button_width + spacing

    # draw selected anomaly details
    selected = anomalies[selected_index]
    # gap before details
    y = menu_y + button_height + 24 

    # anomaly name as title
    y = draw_title_text(surface, selected.get_name(), x, y)
    y += 10

    # containment procedures
    y = draw_header_text(surface, "Special Containment Procedures:", x, y)
    y = draw_body_text(surface, selected.get_containment_procedures(), x, y)

    # anomaly attributes
    y += 12
    y = draw_header_text(surface, "Statistics:", x, y)
    y = draw_body_text(surface, "• [add anomaly stats here]", x, y)

    return button_rects
