# anomaly_page.py

from ui_elements import (
    draw_title_text,
    draw_header_text,
    draw_body_text,
    draw_primary_button,
    draw_secondary_button,
)

def draw_anomaly_page(surface, anomalies, selected_index, x):
    """
    Draw the anomalies page:
      - A top menu with buttons for each anomaly.
      - Detail section for the currently selected anomaly.

    Returns:
      dict[int, pygame.Rect]: mapping anomaly index -> button rect
    """
    # --- top anomaly menu ---
    menu_y = 16
    button_width = 140
    button_height = 28
    spacing = 8

    button_rects = {}

    current_x = x
    for idx, anomaly in enumerate(anomalies):
        label = anomaly.get_name()

        # truncate long names so buttons stay neat
        if len(label) > 18:
            label = label[:15] + "..."

        if idx == selected_index:
            # highlight selected anomaly
            rect = draw_primary_button(
                surface, label, current_x, menu_y, button_width, button_height
            )
        else:
            rect = draw_secondary_button(
                surface, label, current_x, menu_y, button_width, button_height
            )

        button_rects[idx] = rect
        current_x += button_width + spacing

    # --- selected anomaly details ---
    selected = anomalies[selected_index]

    content_x = x
    y = menu_y + button_height + 24  # some gap below the menu

    # Name
    y = draw_title_text(surface, selected.get_name(), content_x, y)
    y += 10

    # Containment
    y = draw_header_text(surface, "Special Containment Procedures:", content_x, y)
    y = draw_body_text(surface, selected.get_containment_procedures(), content_x, y)

    # Stats (placeholder – plug in your real fields here)
    y += 12
    y = draw_header_text(surface, "Statistics:", content_x, y)
    y = draw_body_text(surface, "• [add anomaly stats here]", content_x, y)

    return button_rects
