# operations_page.py
import pygame
from ui_elements import (
    draw_title_text,
    draw_header_text,
    draw_body_text,
    draw_primary_button,
    draw_secondary_button,
    BODY_FONT,
    COLOR,
)

def draw_operations_page(surface, operations, selected_index, x, top_offset=0):
    """
    Super simple mission selection screen.

    - Top row: buttons for each operation.
    - Below: details for the selected operation.
    - Bottom-left: 'Launch Operation' button.

    Returns:
        (op_button_rects, launch_button_rect)
    """
    # --- top mission tabs ---
    menu_y = top_offset + 8
    button_width = 160
    button_height = 28
    spacing = 8

    op_button_rects = {}
    button_x = x

    for idx, op in enumerate(operations):
        # use .codename if it exists, fallback to generic
        label = getattr(op, "codename", f"Op {idx+1}")
        if len(label) > 18:
            label = label[:15] + "..."

        if idx == selected_index:
            rect = draw_primary_button(surface, label, button_x, menu_y,
                                       button_width, button_height)
        else:
            rect = draw_secondary_button(surface, label, button_x, menu_y,
                                         button_width, button_height)

        op_button_rects[idx] = rect
        button_x += button_width + spacing

    # --- selected operation details ---
    selected = operations[selected_index]

    y = menu_y + button_height + 24

    codename = getattr(selected, "codename", "Unknown Operation")
    y = draw_title_text(surface, codename, x, y)
    y += 6

    # Basic info line (location, risk, priority if present)
    city    = getattr(selected, "city", "Unknown City")
    country = getattr(selected, "country", "Unknown Country")
    risk    = getattr(selected, "risk", "Unknown Risk")
    priority = getattr(selected, "priority", "Unknown Priority")

    y = draw_body_text(surface, f"Location: {city}, {country}", x, y)
    y = draw_body_text(surface, f"Risk: {risk} | Priority: {priority}", x, y)
    y += 10

    # Briefing
    y = draw_header_text(surface, "Briefing:", x, y)
    desc = getattr(selected, "description", "No briefing available.")
    y = draw_body_text(surface, desc, x, y)

    # --- Launch button at bottom-left of content area ---
    btn_w, btn_h = 180, 32
    btn_x = x
    btn_y = surface.get_height() - btn_h - 40  # 40px up from bottom

    launch_button_rect = draw_primary_button(
        surface, "Launch Operation", btn_x, btn_y, btn_w, btn_h
    )

    return op_button_rects, launch_button_rect
