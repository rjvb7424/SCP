# external imports
import pygame
# internal imports
from ui_elements import draw_title_text, draw_header_text, draw_body_text, draw_primary_button

# cached world map image
_world_map_image = None
def _get_world_map():
    """Load the image for the world map once. Safe even if called before set_mode."""
    global _world_map_image
    # if already loaded, return cached version
    if _world_map_image is None:
        try:
            img = pygame.image.load("world_map.jpg")
            # Only convert if a display surface exists
            if pygame.display.get_surface() is not None:
                img = img.convert()
            _world_map_image = img
        except Exception as e:
            print("Warning: could not load world_map.jpg:", e)
            _world_map_image = None
    return _world_map_image


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


def _priority_color(priority):
    """Very simple color mapping based on priority string or number."""
    if isinstance(priority, str):
        p = priority.lower()
        if "very" in p or "high" in p:
            return (210, 70, 70)       # red-ish
        if "med" in p:
            return (230, 170, 60)      # orange
        return (110, 200, 120)         # green-ish
    else:
        # numeric style: 3 = high, 2 = medium, 1 = low
        if priority >= 3:
            return (210, 70, 70)
        elif priority == 2:
            return (230, 170, 60)
        else:
            return (110, 200, 120)


def draw_operations_page(surface, operations, selected_index, x, top_offset=0):
    """
    Mission selection screen with a world map on the left and details on the right.

    - World map with one dot per operation (click dots to change selection).
    - Right-hand panel shows details for the selected operation.
    - 'Launch Operation' button at bottom of the info panel.

    Returns:
        (marker_rects, launch_button_rect)
        where marker_rects is {op_index: pygame.Rect}
    """
    width, height = surface.get_size()
    margin = 20
    top = top_offset + 20

    # --- Layout: map area & info panel (to the right) ---
    available_width = width - x - margin
    right_panel_width = max(320, int(available_width * 0.35))

    map_rect = pygame.Rect(
        x,
        top,
        available_width - right_panel_width - margin,
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
    draw_title_text(surface, "Operations", x, top_offset + 4)

    # --- Draw world map with aspect kept, no cropping (letterbox if needed) ---
    map_img = _get_world_map()

    img_x = map_rect.x
    img_y = map_rect.y
    img_w = map_rect.width
    img_h = map_rect.height

    if map_img is not None and map_rect.width > 0 and map_rect.height > 0:
        orig_w, orig_h = map_img.get_size()
        img_aspect = orig_w / orig_h
        rect_aspect = map_rect.width / map_rect.height

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

        scaled_map = pygame.transform.smoothscale(map_img, (scaled_w, scaled_h))

        map_surface = pygame.Surface(map_rect.size)
        map_surface.fill((25, 25, 25))
        map_surface.blit(scaled_map, (offset_x_local, offset_y_local))
        surface.blit(map_surface, map_rect.topleft)

        # Global position of the scaled image
        img_x = map_rect.x + offset_x_local
        img_y = map_rect.y + offset_y_local
        img_w = scaled_w
        img_h = scaled_h

    # --- Draw operation markers ---
    marker_rects = {}

    for idx, op in enumerate(operations):
        lat = getattr(op, "lat", 0.0)
        lon = getattr(op, "lon", 0.0)

        if map_img is None:
            # Fallback: map directly into map_rect if image missing
            mx = map_rect.left + (lon + 180.0) / 360.0 * map_rect.width
            my = map_rect.top + (90.0 - lat) / 180.0 * map_rect.height
            mx, my = int(mx), int(my)
        else:
            mx, my = project_lat_lon_on_image(lat, lon, img_x, img_y, img_w, img_h)

        if not map_rect.collidepoint(mx, my):
            continue

        color = _priority_color(getattr(op, "priority", "Low"))
        radius = 7 if idx == selected_index else 5

        pygame.draw.circle(surface, color, (mx, my), radius)
        pygame.draw.circle(surface, (0, 0, 0), (mx, my), radius, width=1)

        marker_rects[idx] = pygame.Rect(mx - radius, my - radius, radius * 2, radius * 2)

    # --- Info panel for selected operation ---
    if not operations:
        return marker_rects, None

    selected = operations[selected_index]

    padding = 14
    text_x = info_rect.x + padding
    y = info_rect.y + padding

    codename = getattr(selected, "codename", "Unknown Operation")
    y = draw_title_text(surface, codename, text_x, y)
    y += 6

    city    = getattr(selected, "city", "Unknown City")
    country = getattr(selected, "country", "Unknown Country")
    risk    = getattr(selected, "risk", "Unknown Risk")
    priority = getattr(selected, "priority", "Unknown Priority")

    y = draw_body_text(surface, f"Location: {city}, {country}", text_x, y)
    y = draw_body_text(surface, f"Risk: {risk} | Priority: {priority}", text_x, y)
    y += 10

    y = draw_header_text(surface, "Briefing:", text_x, y)
    desc = getattr(selected, "description", "No briefing available.")
    y = draw_body_text(surface, desc, text_x, y)

    # --- Launch button at bottom of info panel ---
    btn_w, btn_h = 180, 32
    btn_x = info_rect.x + padding
    btn_y = info_rect.bottom - padding - btn_h

    launch_button_rect = draw_primary_button(
        surface, "Launch Operation", btn_x, btn_y, btn_w, btn_h
    )

    return marker_rects, launch_button_rect
