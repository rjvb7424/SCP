# facility_page.py
import pygame
from typing import List, Tuple, Optional, Dict

from facility import Facility
from tasks import _classify_position

# Map role -> default room type
ROLE_ROOM_MAP = {
    "research": "Research Lab",
    "medical": "Infirmary",
    "security": "Security Station",
    "administration": "Command Center",
    "general": "Common Room",
}

# Basic colors per room type
ROOM_COLORS = {
    "Entrance": (70, 70, 90),
    "Command Center": (90, 90, 130),
    "Research Lab": (80, 120, 150),
    "Infirmary": (90, 140, 110),
    "Security Station": (120, 90, 90),
    "Dormitory": (120, 100, 80),
    "Common Room": (100, 110, 100),
}


def _build_occupant_map(
    facility: Facility,
    staff_roster,
    build_orders,
    current_day: int,
) -> Dict[tuple, list]:
    """
    Decide which personnel appear in which room cell.

    Returns: dict[(row, col)] -> [personnel...]
    """
    rows = facility.rows
    cols = facility.cols

    # Rooms by type for distributing staff
    rooms_by_type: Dict[str, List[tuple]] = {}
    for r in range(rows):
        for c in range(cols):
            room = facility.get_room(r, c)
            if room is not None:
                rooms_by_type.setdefault(room.room_type, []).append((r, c, room))

    existing_room_types = set(rooms_by_type.keys())

    # Which cell is each builder working in?
    builder_cells = {}
    for order in build_orders:
        if order.task.status == "Active":
            builder_cells[order.builder] = (order.row, order.col)

    # Where do idle staff chill?
    idle_room_type = None
    for candidate in ("Common Room", "Dormitory", "Command Center"):
        if candidate in existing_room_types:
            idle_room_type = candidate
            break

    occupants_by_cell: Dict[tuple, list] = {}
    type_assign_counter: Dict[str, int] = {}

    def assign_to_cell(cell_key, person):
        occupants_by_cell.setdefault(cell_key, []).append(person)

    for person in staff_roster.members:
        status = getattr(person, "status", "Active")
        if status != "Active":
            continue

        # If they're building a room, show them in that construction cell
        if person in builder_cells:
            cell = builder_cells[person]
            assign_to_cell(cell, person)
            continue

        task = getattr(person, "current_task", None)

        # If they're on a task, send them to a role-specific room
        if task is not None and task.status == "Active":
            role = _classify_position(getattr(person, "position", ""))
            room_type = ROLE_ROOM_MAP.get(role)
            if room_type and room_type in rooms_by_type:
                index = type_assign_counter.get(room_type, 0)
                room_list = rooms_by_type[room_type]
                cell = room_list[index % len(room_list)][:2]
                type_assign_counter[room_type] = index + 1
                assign_to_cell(cell, person)
                continue

        # Otherwise they are idle; send to chill room
        if idle_room_type and idle_room_type in rooms_by_type:
            index = type_assign_counter.get(idle_room_type, 0)
            room_list = rooms_by_type[idle_room_type]
            cell = room_list[index % len(room_list)][:2]
            type_assign_counter[idle_room_type] = index + 1
            assign_to_cell(cell, person)

    return occupants_by_cell


def draw_facility_page(
    surface,
    facility: Facility,
    staff_roster,
    build_orders,
    current_day: int,
    title_font,
    body_font,
    width: int,
    height: int,
    menu_height: int,
    mode: str,
    selected_room_type: Optional[str],
    selected_cell: Optional[tuple],
    selected_builder_index: Optional[int],
):
    """
    Draw the Facility page.

    Returns:
        cell_rects: [(row, col, rect), ...]
        roomtype_button_rects: [(room_type, rect), ...]
        builder_button_rects: [(staff_index, rect), ...]
        cancel_build_rect: pygame.Rect or None
    """
    margin = 30
    top = menu_height + 20
    card_width = width - margin * 2

    # Title + mode
    title_text = "Facility"
    title_surf = title_font.render(title_text, True, (255, 255, 255))
    surface.blit(title_surf, (margin, top))
    top += title_surf.get_height() + 4

    mode_text = "Mode: Build" if mode == "build" else "Mode: View"
    mode_surf = body_font.render(mode_text, True, (200, 200, 220))
    surface.blit(mode_surf, (margin, top))
    top += mode_surf.get_height() + 8

    # Layout: left grid, right control panel
    grid_width = int(card_width * 0.68)
    grid_x = margin
    grid_y = top
    padding = 10

    # --- Horizontal rooms: make each room wider than tall ---
    rows = facility.rows
    cols = facility.cols

    inner_w = grid_width - padding * 2
    cell_width = inner_w // cols
    cell_height = max(40, cell_width // 2)  # ~2:1 aspect ratio (wide rooms)
    inner_h = rows * cell_height
    grid_height = inner_h + padding * 2

    grid_rect = pygame.Rect(grid_x, grid_y, grid_width, grid_height)

    side_rect = pygame.Rect(
        grid_rect.right + 10,
        grid_y,
        card_width - grid_rect.width - 10,
        grid_height,
    )

    pygame.draw.rect(surface, (40, 40, 40), grid_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), grid_rect, width=1, border_radius=8)

    pygame.draw.rect(surface, (40, 40, 40), side_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), side_rect, width=1, border_radius=8)

    # Where is everyone?
    occupants_by_cell = _build_occupant_map(facility, staff_roster, build_orders, current_day)

    # Build orders by cell, for quick lookup
    build_orders_by_cell = {
        (order.row, order.col): order for order in build_orders
    }

    # --- Grid drawing ---
    cell_rects: List[Tuple[int, int, pygame.Rect]] = []

    for r in range(rows):
        for c in range(cols):
            x = grid_rect.x + padding + c * cell_width
            y = grid_rect.y + padding + r * cell_height
            rect = pygame.Rect(x, y, cell_width - 4, cell_height - 4)

            room = facility.get_room(r, c)
            order = build_orders_by_cell.get((r, c))
            occupants = occupants_by_cell.get((r, c), [])

            # Highlight selected cell
            is_selected = selected_cell == (r, c)

            if order is not None:
                # Under construction
                bg = (100, 100, 60)
                border = (220, 220, 130) if is_selected else (40, 40, 20)
                pygame.draw.rect(surface, bg, rect, border_radius=4)
                pygame.draw.rect(surface, border, rect, width=2, border_radius=4)

                title = f"Building: {order.room_type}"
                title_surf = body_font.render(title, True, (250, 250, 210))
                surface.blit(title_surf, (rect.x + 4, rect.y + 4))

                remaining = order.task.remaining_days(current_day)
                rem_text = f"{remaining} day(s) remaining"
                rem_surf = body_font.render(rem_text, True, (240, 240, 200))
                surface.blit(rem_surf, (rect.x + 4, rect.y + 4 + title_surf.get_height()))
            else:
                if room is None:
                    # Empty tile
                    bg = (35, 35, 35)
                    border = (130, 160, 130) if (mode == "build" and selected_room_type) else (70, 70, 70)
                    if is_selected:
                        border = (200, 200, 200)
                    pygame.draw.rect(surface, bg, rect, border_radius=4)
                    pygame.draw.rect(surface, border, rect, width=1, border_radius=4)

                    label_surf = body_font.render("Empty", True, (130, 130, 130))
                    surface.blit(
                        label_surf,
                        label_surf.get_rect(center=(rect.centerx, rect.centery)),
                    )
                else:
                    base_col = ROOM_COLORS.get(room.room_type, (80, 80, 80))
                    pygame.draw.rect(surface, base_col, rect, border_radius=4)

                    border_col = (255, 255, 255) if is_selected else (30, 30, 30)
                    pygame.draw.rect(surface, border_col, rect, width=2 if is_selected else 1, border_radius=4)

                    # room name
                    label_surf = body_font.render(room.room_type, True, (240, 240, 240))
                    surface.blit(label_surf, (rect.x + 4, rect.y + 4))

            # Occupants list (names)
            if occupants:
                y_occ = rect.bottom - 4
                max_lines = 3
                for person in occupants[:max_lines][::-1]:
                    name = f"{person.fname} {person.lname}"
                    name_surf = body_font.render(name, True, (250, 250, 250))
                    y_occ -= name_surf.get_height()
                    surface.blit(name_surf, (rect.x + 6, y_occ))

                if len(occupants) > max_lines:
                    more = f"+{len(occupants) - max_lines} more"
                    more_surf = body_font.render(more, True, (230, 230, 230))
                    y_occ -= more_surf.get_height()
                    surface.blit(more_surf, (rect.x + 6, y_occ))

            cell_rects.append((r, c, rect))

    # --- Side panel: room info + build controls + builder selection ---

    # 1) Selected room info
    info_height = 120
    info_rect = pygame.Rect(
        side_rect.x + 8,
        side_rect.y + 8,
        side_rect.width - 16,
        info_height,
    )
    pygame.draw.rect(surface, (30, 30, 30), info_rect, border_radius=4)
    pygame.draw.rect(surface, (70, 70, 70), info_rect, width=1, border_radius=4)

    y_info = info_rect.y + 6
    header = body_font.render("Room Info", True, (255, 255, 255))
    surface.blit(header, (info_rect.x + 6, y_info))
    y_info += header.get_height() + 3

    if selected_cell is None:
        msg = "Click a room in the facility to view details."
        msg_surf = body_font.render(msg, True, (200, 200, 200))
        surface.blit(msg_surf, (info_rect.x + 6, y_info))
    else:
        r, c = selected_cell
        room = facility.get_room(r, c)
        order = build_orders_by_cell.get((r, c))
        occs = occupants_by_cell.get((r, c), [])

        loc_text = f"Location: Row {r+1}, Col {c+1}"
        loc_surf = body_font.render(loc_text, True, (200, 200, 200))
        surface.blit(loc_surf, (info_rect.x + 6, y_info))
        y_info += loc_surf.get_height() + 2

        if room is not None:
            room_text = f"Room: {room.room_type}"
        elif order is not None:
            room_text = f"Planned: {order.room_type}"
        else:
            room_text = "Room: Empty"
        room_surf = body_font.render(room_text, True, (210, 210, 210))
        surface.blit(room_surf, (info_rect.x + 6, y_info))
        y_info += room_surf.get_height() + 2

        if order is not None:
            rem = order.task.remaining_days(current_day)
            status_text = f"Status: Under construction ({rem} day(s) left)"
        elif room is not None:
            status_text = "Status: Operational"
        else:
            status_text = "Status: Unused space"
        status_surf = body_font.render(status_text, True, (210, 210, 210))
        surface.blit(status_surf, (info_rect.x + 6, y_info))
        y_info += status_surf.get_height() + 2

        occ_text = f"Occupants: {len(occs)} personnel"
        occ_surf = body_font.render(occ_text, True, (200, 200, 200))
        surface.blit(occ_surf, (info_rect.x + 6, y_info))

    # 2) Build Rooms section
    roomtype_button_rects: List[Tuple[str, pygame.Rect]] = []
    builder_button_rects: List[Tuple[int, pygame.Rect]] = []
    cancel_build_rect: Optional[pygame.Rect] = None

    x_r = side_rect.x + 10
    y_r = info_rect.bottom + 10

    build_header = body_font.render("Build Rooms", True, (255, 255, 255))
    surface.blit(build_header, (x_r, y_r))
    y_r += build_header.get_height() + 4

    info_lines = [
        "1. Pick a room type.",
        "2. Select a builder.",
        "3. Click an empty tile.",
    ]
    for line in info_lines:
        s = body_font.render(line, True, (190, 190, 190))
        surface.blit(s, (x_r, y_r))
        y_r += s.get_height() + 1

    y_r += 4

    btn_w = side_rect.width - 20
    btn_h = 26
    gap = 4

    for room_type in facility.room_types:
        rect = pygame.Rect(x_r, y_r, btn_w, btn_h)

        if mode == "build" and selected_room_type == room_type:
            bg = (90, 130, 90)
            text_col = (255, 255, 255)
        else:
            bg = (65, 65, 65)
            text_col = (220, 220, 220)

        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), rect, width=1, border_radius=4)

        label_surf = body_font.render(room_type, True, text_col)
        surface.blit(label_surf, label_surf.get_rect(center=rect.center))

        roomtype_button_rects.append((room_type, rect))
        y_r += btn_h + gap

    # 3) Builder selection
    y_r += 6
    builder_header = body_font.render("Builder", True, (255, 255, 255))
    surface.blit(builder_header, (x_r, y_r))
    y_r += builder_header.get_height() + 4

    builder_list_height = 110
    builder_area_rect = pygame.Rect(
        x_r,
        y_r,
        btn_w,
        builder_list_height,
    )
    pygame.draw.rect(surface, (32, 32, 32), builder_area_rect, border_radius=4)
    pygame.draw.rect(surface, (70, 70, 70), builder_area_rect, width=1, border_radius=4)

    y_b = builder_area_rect.y + 4
    for idx, person in enumerate(staff_roster.members):
        status = getattr(person, "status", "Active")
        if status != "Active":
            continue

        row_rect = pygame.Rect(
            builder_area_rect.x + 2,
            y_b,
            builder_area_rect.width - 4,
            22,
        )

        is_selected = selected_builder_index == idx
        bg = (85, 95, 125) if is_selected else (55, 55, 55)
        pygame.draw.rect(surface, bg, row_rect, border_radius=3)
        pygame.draw.rect(surface, (90, 90, 90), row_rect, width=1, border_radius=3)

        name = f"{person.fname} {person.lname}"
        task = getattr(person, "current_task", None)
        if task is None or task.status != "Active":
            status_text = "Idle"
            st_color = (190, 230, 190)
        else:
            status_text = "Busy"
            st_color = (230, 210, 160)

        name_surf = body_font.render(name, True, (240, 240, 240))
        surface.blit(name_surf, (row_rect.x + 4, row_rect.y + 2))

        status_surf = body_font.render(status_text, True, st_color)
        surface.blit(
            status_surf,
            (row_rect.right - status_surf.get_width() - 4, row_rect.y + 2),
        )

        builder_button_rects.append((idx, row_rect))
        y_b += row_rect.height + 2
        if y_b > builder_area_rect.bottom - 24:
            break  # don't overflow

    # 4) Cancel build button (only in build mode)
    if mode == "build":
        cancel_build_rect = pygame.Rect(
            x_r,
            side_rect.bottom - btn_h - 10,
            btn_w,
            btn_h,
        )
        pygame.draw.rect(surface, (120, 70, 70), cancel_build_rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), cancel_build_rect, width=1, border_radius=4)
        cancel_surf = body_font.render("Cancel Build Mode", True, (255, 255, 255))
        surface.blit(cancel_surf, cancel_surf.get_rect(center=cancel_build_rect.center))

    return cell_rects, roomtype_button_rects, builder_button_rects, cancel_build_rect
