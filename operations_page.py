# operations_page.py
import pygame

from operations import Operation, Operations  # only for type hints / clarity


def project_lat_lon(lat, lon, map_rect: pygame.Rect):
    """
    Convert latitude/longitude to x,y in the given map_rect assuming
    an equirectangular projection (common flat world map).
    lat:  -90 (south) .. +90 (north)
    lon: -180 (west)  .. +180 (east)
    """
    x = map_rect.left + (lon + 180.0) / 360.0 * map_rect.width
    y = map_rect.top + (90.0 - lat) / 180.0 * map_rect.height
    return int(x), int(y)


def draw_operations_page(
    surface,
    world_map_image,
    operations_manager: Operations,
    title_font,
    body_font,
    width,
    height,
    menu_height,
):
    """
    Draws the Operations screen:
      - world map with markers
      - info panel on the right for selected operation

    Returns:
      marker_hitboxes: list[(index, pygame.Rect)] so the caller can detect clicks.
    """
    margin = 20
    top = menu_height + 20

    # Right-hand info panel width (responsive-ish)
    right_panel_width = max(320, int(width * 0.28))

    map_rect = pygame.Rect(
        margin,
        top,
        width - 3 * margin - right_panel_width,
        height - top - margin,
    )
    info_rect = pygame.Rect(
        map_rect.right + margin,
        top,
        right_panel_width,
        height - top - margin,
    )

    # --- Draw backgrounds / borders ---
    pygame.draw.rect(surface, (25, 25, 25), map_rect)
    pygame.draw.rect(surface, (40, 40, 40), info_rect)
    pygame.draw.rect(surface, (90, 90, 90), map_rect, width=1)
    pygame.draw.rect(surface, (90, 90, 90), info_rect, width=1)

    # --- Title above map ---
    title_surf = title_font.render("Operations", True, (255, 255, 255))
    surface.blit(title_surf, (margin, top - title_surf.get_height() - 6))

    # --- Draw the map ---
    if world_map_image is not None and map_rect.width > 0 and map_rect.height > 0:
        map_scaled = pygame.transform.smoothscale(
            world_map_image, (map_rect.width, map_rect.height)
        )
        surface.blit(map_scaled, map_rect.topleft)

    marker_hitboxes = []

    # --- Draw operation markers ---
    if len(operations_manager) > 0:
        for idx, op in enumerate(operations_manager.operations):
            x, y = project_lat_lon(op.lat, op.lon, map_rect)

            # Color based on priority
            if op.priority == 3:
                color = (210, 70, 70)      # high priority = red-ish
            elif op.priority == 2:
                color = (230, 170, 60)     # medium = amber
            else:
                color = (110, 200, 120)    # low = green-ish

            radius = 7 if idx == operations_manager.current_index else 5

            pygame.draw.circle(surface, color, (x, y), radius)
            pygame.draw.circle(surface, (0, 0, 0), (x, y), radius, width=1)

            hit_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
            marker_hitboxes.append((idx, hit_rect))

    # --- Draw info panel for selected operation ---
    padding = 14
    text_x = info_rect.x + padding
    text_y = info_rect.y + padding

    if operations_manager.current is None:
        msg = "Click a marker on the map to view operation details."
        msg_surf = body_font.render(msg, True, (220, 220, 220))
        msg_rect = msg_surf.get_rect()
        msg_rect.topleft = (text_x, text_y)
        surface.blit(msg_surf, msg_rect)
    else:
        op = operations_manager.current

        # Codename as title
        code_surf = title_font.render(op.codename, True, (255, 255, 255))
        surface.blit(code_surf, (text_x, text_y))
        text_y += code_surf.get_height() + 8

        # Basic fields
        lines = [
            f"Location: {op.city}, {op.country}",
            f"Type: {op.op_type}",
            f"Priority: {op.priority}",
            f"Risk: {op.risk}",
            f"Status: {op.status}",
            "",
            "Briefing:",
        ]

        for line in lines:
            line_surf = body_font.render(line, True, (220, 220, 220))
            surface.blit(line_surf, (text_x, text_y))
            text_y += line_surf.get_height() + 3

        # Wrap description roughly to the panel width
        desc = op.description
        words = desc.split()
        current_line = ""
        max_width = info_rect.width - 2 * padding

        for word in words:
            test = current_line + (" " if current_line else "") + word
            test_surf = body_font.render(test, True, (200, 200, 200))
            if test_surf.get_width() > max_width:
                # render current_line, start new
                line_surf = body_font.render(current_line, True, (200, 200, 200))
                surface.blit(line_surf, (text_x, text_y))
                text_y += line_surf.get_height() + 2
                current_line = word
            else:
                current_line = test

        if current_line:
            line_surf = body_font.render(current_line, True, (200, 200, 200))
            surface.blit(line_surf, (text_x, text_y))

    return marker_hitboxes
