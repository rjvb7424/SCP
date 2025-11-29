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
    staff_roster,
    mode,                # "view" or "assign"
    selected_indices,    # set of staff indices selected for mission
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

        map_surface = pygame.Surface(map_rect.size)
        map_surface.fill((25, 25, 25))
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

            if not map_rect.collidepoint(x, y):
                continue

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

    # --- Info panel (two modes: view vs assign) ---
    padding = 14
    top_y = info_rect.y + padding
    text_x = info_rect.x + padding

    op = operations_manager.current

    execute_button_rect = None
    cancel_button_rect = None
    confirm_button_rect = None
    staff_item_rects = []

    if op is None:
        msg = "No active operations."
        msg_surf = body_font.render(msg, True, (220, 220, 220))
        surface.blit(msg_surf, (text_x, top_y))
        return marker_hitboxes, execute_button_rect, cancel_button_rect, confirm_button_rect, staff_item_rects

    # --- ASSIGN MODE: choose personnel to send ---
    if mode == "assign":
        header = title_font.render("Assign Personnel", True, (255, 255, 255))
        surface.blit(header, (text_x, top_y))
        y = top_y + header.get_height() + 6

        sub = body_font.render(op.codename, True, (200, 200, 200))
        surface.blit(sub, (text_x, y))
        y += sub.get_height() + 10

        # Each staff member as a selectable row
        for idx, person in enumerate(staff_roster.members):
            status = getattr(person, "status", "Active")
            is_available = (status == "Active")
            is_selected = (idx in selected_indices)

            row_rect = pygame.Rect(
                info_rect.x + padding,
                y,
                info_rect.width - 2 * padding,
                28,
            )

            if not is_available:
                bg = (45, 45, 45)
                text_color = (140, 140, 140)
            elif is_selected:
                bg = (70, 110, 70)
                text_color = (255, 255, 255)
            else:
                bg = (60, 60, 60)
                text_color = (220, 220, 220)

            pygame.draw.rect(surface, bg, row_rect, border_radius=4)
            pygame.draw.rect(surface, (90, 90, 90), row_rect, width=1, border_radius=4)

            label = f"{person.fname} {person.lname} - {person.position} ({status})"
            label_surf = body_font.render(label, True, text_color)
            surface.blit(label_surf, (row_rect.x + 6, row_rect.y + 4))

            staff_item_rects.append((idx, row_rect))
            y += row_rect.height + 4

        # Buttons at bottom
        btn_w, btn_h = 150, 32

        cancel_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        cancel_button_rect.left = info_rect.x + padding
        cancel_button_rect.bottom = info_rect.bottom - padding

        confirm_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
        confirm_button_rect.right = info_rect.right - padding
        confirm_button_rect.bottom = info_rect.bottom - padding

        # Cancel button
        pygame.draw.rect(surface, (100, 60, 60), cancel_button_rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), cancel_button_rect, width=1, border_radius=4)
        cancel_text = body_font.render("Cancel", True, (230, 230, 230))
        surface.blit(cancel_text, cancel_text.get_rect(center=cancel_button_rect.center))

        # Confirm / Launch button (disabled if no selection)
        if selected_indices:
            conf_bg = (70, 120, 70)
            conf_text_color = (255, 255, 255)
        else:
            conf_bg = (45, 70, 45)
            conf_text_color = (160, 160, 160)

        pygame.draw.rect(surface, conf_bg, confirm_button_rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), confirm_button_rect, width=1, border_radius=4)
        conf_text = body_font.render("Launch Operation", True, conf_text_color)
        surface.blit(conf_text, conf_text.get_rect(center=confirm_button_rect.center))

        return marker_hitboxes, execute_button_rect, cancel_button_rect, confirm_button_rect, staff_item_rects

    # --- VIEW MODE: show op info + execute button ---

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

    title_height = title_font.get_height()
    code_y = top_y
    code_surf = title_font.render(op.codename, True, (255, 255, 255))
    surface.blit(code_surf, (text_x, code_y))

    block_start_y = top_y + max(title_height, flag_h) + 10
    text_y = block_start_y

    lines = [
        f"Location: {op.city}, {op.country}",
        f"Type: {op.op_type}",
        f"Anomaly: {op.anomaly_name} ({op.anomaly_class})",
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

    # Briefing text (wrapped)
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
        text_y += line_surf.get_height() + 6

    # Outcome text if the operation has been run
    if getattr(op, "result_text", ""):
        text_y += 6
        outcome_header = body_font.render("Outcome:", True, (235, 235, 235))
        surface.blit(outcome_header, (text_x, text_y))
        text_y += outcome_header.get_height() + 3

        words = op.result_text.split()
        current_line = ""
        while words:
            word = words.pop(0)
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

    # Execute button (bottom of panel)
    btn_w, btn_h = 180, 32
    execute_button_rect = pygame.Rect(0, 0, btn_w, btn_h)
    execute_button_rect.centerx = info_rect.centerx
    execute_button_rect.bottom = info_rect.bottom - padding

    # Enabled only if operation is still available and at least one Active staff
    any_active = any(getattr(p, "status", "Active") == "Active" for p in staff_roster.members)
    enabled = (op.status == "Available") and any_active

    if enabled:
        bg = (70, 120, 70)
        text_color = (255, 255, 255)
    else:
        bg = (45, 70, 45)
        text_color = (160, 160, 160)

    pygame.draw.rect(surface, bg, execute_button_rect, border_radius=4)
    pygame.draw.rect(surface, (90, 90, 90), execute_button_rect, width=1, border_radius=4)
    txt = body_font.render("Execute Operation", True, text_color)
    surface.blit(txt, txt.get_rect(center=execute_button_rect.center))

    return marker_hitboxes, execute_button_rect, cancel_button_rect, confirm_button_rect, staff_item_rects
