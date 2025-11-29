# operations_page.py
import pygame
from operations import Operations


def project_lat_lon_on_image(lat, lon, img_x, img_y, img_w, img_h):
    """
    Map latitude/longitude onto the *scaled image* that starts at (img_x, img_y)
    and has size img_w x img_h.
    lat:  -90 .. +90
    lon: -180 .. +180
    """
    x = img_x + (lon + 180.0) / 360.0 * img_w
    y = img_y + (90.0 - lat) / 180.0 * img_h
    return int(x), int(y)


def draw_operations_page(
    surface,
    world_map_image,
    operations_manager: Operations,
    op_flag_images,      # list of flag surfaces aligned with operations_manager.operations
    title_font,
    body_font,
    width,
    height,
    menu_height,
):
    margin = 20
    top = menu_height + 20

    right_panel_width = max(320, int(width * 0.28))

    # Left map area and right info panel
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

    # Backgrounds / borders
    pygame.draw.rect(surface, (25, 25, 25), map_rect)
    pygame.draw.rect(surface, (40, 40, 40), info_rect)
    pygame.draw.rect(surface, (90, 90, 90), map_rect, width=1)
    pygame.draw.rect(surface, (90, 90, 90), info_rect, width=1)

    # Title above map
    title_surf = title_font.render("Operations", True, (255, 255, 255))
    surface.blit(title_surf, (margin, top - title_surf.get_height() - 6))

    # --- Draw world map with aspect kept, no cropping (letterbox if needed) ---
    img_x = map_rect.x
    img_y = map_rect.y
    img_w = map_rect.width
    img_h = map_rect.height

    if world_map_image is not None and map_rect.width > 0 and map_rect.height > 0:
        orig_w, orig_h = world_map_image.get_size()
        img_aspect = orig_w / orig_h
        rect_aspect = map_rect.width / map_rect.height

        # Scale so the entire image fits inside map_rect, keeping aspect ratio
        if img_aspect > rect_aspect:
            # Image is proportionally wider -> match width, letterbox top/bottom
            scaled_w = map_rect.width
            scaled_h = int(scaled_w / img_aspect)
            offset_x_local = 0
            offset_y_local = (map_rect.height - scaled_h) // 2
        else:
            # Image is proportionally taller -> match height, letterbox left/right
            scaled_h = map_rect.height
            scaled_w = int(scaled_h * img_aspect)
            offset_y_local = 0
            offset_x_local = (map_rect.width - scaled_w) // 2

        scaled_map = pygame.transform.smoothscale(world_map_image, (scaled_w, scaled_h))

        # Draw onto a surface the size of map_rect so we never go outside the card
        map_surface = pygame.Surface(map_rect.size)
        map_surface.fill((25, 25, 25))  # background for letterbox bars
        map_surface.blit(scaled_map, (offset_x_local, offset_y_local))
        surface.blit(map_surface, map_rect.topleft)

        # Global position of the scaled image
        img_x = map_rect.x + offset_x_local
        img_y = map_rect.y + offset_y_local
        img_w = scaled_w
        img_h = scaled_h

    marker_hitboxes = []

    # --- Draw operation markers ---
    if len(operations_manager) > 0:
        for idx, op in enumerate(operations_manager.operations):
            if world_map_image is None:
                # Fallback: map directly into map_rect if image missing
                x = map_rect.left + (op.lon + 180.0) / 360.0 * map_rect.width
                y = map_rect.top + (90.0 - op.lat) / 180.0 * map_rect.height
                x, y = int(x), int(y)
            else:
                x, y = project_lat_lon_on_image(op.lat, op.lon, img_x, img_y, img_w, img_h)

            # Only draw if inside the visible map rect
            if not map_rect.collidepoint(x, y):
                continue

            # Color based on priority
            if op.priority == 3:
                color = (210, 70, 70)
            elif op.priority == 2:
                color = (230, 170, 60)
            else:
                color = (110, 200, 120)

            radius = 7 if idx == operations_manager.current_index else 5

            pygame.draw.circle(surface, color, (x, y), radius)
            pygame.draw.circle(surface, (0, 0, 0), (x, y), radius, width=1)

            hit_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
            marker_hitboxes.append((idx, hit_rect))

    # --- Info panel with flag + text (fixed vertical anchor) ---
    padding = 14
    top_y = info_rect.y + padding
    text_x = info_rect.x + padding

    op = operations_manager.current

    if op is None:
        msg = "Click a marker on the map to view operation details."
        msg_surf = body_font.render(msg, True, (220, 220, 220))
        surface.blit(msg_surf, (text_x, top_y))
    else:
        # Flag (if available)
        flag_img = None
        if op_flag_images and 0 <= operations_manager.current_index < len(op_flag_images):
            flag_img = op_flag_images[operations_manager.current_index]

        flag_h = 0
        if flag_img is not None:
            flag_rect = flag_img.get_rect()
            flag_rect.top = top_y
            flag_rect.right = info_rect.right - padding
            surface.blit(flag_img, flag_rect)
            flag_h = flag_rect.height

        # Codename: fixed Y, independent of flag height
        title_height = title_font.get_height()
        code_y = top_y
        code_surf = title_font.render(op.codename, True, (255, 255, 255))
        surface.blit(code_surf, (text_x, code_y))

        # Block of info lines starts at a fixed distance below the top,
        # based on max(title_height, flag_height) so it never moves per operation.
        block_start_y = top_y + max(title_height, flag_h) + 10
        text_y = block_start_y

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

        # Simple word-wrapped description
        desc = op.description
        words = desc.split()
        current_line = ""
        max_width = info_rect.width - 2 * padding

        for word in words:
            test = current_line + (" " if current_line else "") + word
            test_surf = body_font.render(test, True, (200, 200, 200))
            if test_surf.get_width() > max_width:
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
