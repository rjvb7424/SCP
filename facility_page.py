# facility_page.py
import pygame
from typing import List, Tuple, Optional

from facility import Facility, FacilityRoom
from tasks import _classify_position  # reuse the role classification from tasks.py

# Map role -> room type
ROLE_ROOM_MAP = {
    "research": "Research Lab",
    "medical": "Infirmary",
    "security": "Security Station",
    "administration": "Command Center",
    "general": "Common Room",
}

# Basic colors per room type
ROOM_COLORS = {
    "Command Center": (90, 90, 130),
    "Research Lab": (80, 120, 150),
    "Infirmary": (90, 140, 110),
    "Security Station": (120, 90, 90),
    "Dormitory": (120, 100, 80),
    "Common Room": (100, 110, 100),
}


def draw_facility_page(
    surface,
    facility: Facility,
    staff_roster,
    current_day: int,
    title_font,
    body_font,
    width: int,
    height: int,
    menu_height: int,
    mode: str,
    selected_room_type: Optional[str],
):
    """Draw the Facility page.

    Returns:
        cell_rects: [(row, col, rect), ...]
        roomtype_button_rects: [(room_type, rect), ...]
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
    grid_rect = pygame.Rect(
        margin,
        top,
        int(card_width * 0.65),
        height - top - margin,
    )
    side_rect = pygame.Rect(
        grid_rect.right + 10,
        top,
        card_width - grid_rect.width - 10,
        height - top - margin,
    )

    pygame.draw.rect(surface, (40, 40, 40), grid_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), grid_rect, width=1, border_radius=8)

    pygame.draw.rect(surface, (40, 40, 40), side_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), side_rect, width=1, border_radius=8)

    # --- Which personnel are "in" each room type? ---
    occupants_by_roomtype = {}

    for person in staff_roster.members:
        status = getattr(person, "status", "Active")
        if status != "Active":
            continue
        if getattr(person, "current_task", None) is None:
            continue  # idle personnel not shown in rooms (for now)

        role = _classify_position(getattr(person, "position", ""))
        room_type = ROLE_ROOM_MAP.get(role)
        if not room_type:
            continue

        occupants_by_roomtype.setdefault(room_type, []).append(person)

    # --- Draw grid cells (rooms) ---
    rows = facility.rows
    cols = facility.cols

    padding = 10
    cell_width = (grid_rect.width - padding * 2) // cols
    cell_height = (grid_rect.height - padding * 2) // rows

    cell_rects: List[Tuple[int, int, pygame.Rect]] = []

    for r in range(rows):
        for c in range(cols):
            x = grid_rect.x + padding + c * cell_width
            y = grid_rect.y + padding + r * cell_height
            rect = pygame.Rect(x, y, cell_width - 4, cell_height - 4)

            room = facility.get_room(r, c)

            if room is None:
                # empty / buildable
                if mode == "build" and selected_room_type:
                    bg = (50, 60, 50)
                    border = (120, 180, 120)
                else:
                    bg = (35, 35, 35)
                    border = (70, 70, 70)
                pygame.draw.rect(surface, bg, rect, border_radius=4)
                pygame.draw.rect(surface, border, rect, width=1, border_radius=4)

                label = "Empty"
                label_surf = body_font.render(label, True, (130, 130, 130))
                surface.blit(
                    label_surf,
                    label_surf.get_rect(center=(rect.centerx, rect.centery)),
                )
            else:
                base_col = ROOM_COLORS.get(room.room_type, (80, 80, 80))
                pygame.draw.rect(surface, base_col, rect, border_radius=4)
                pygame.draw.rect(surface, (30, 30, 30), rect, width=1, border_radius=4)

                # room name
                label_surf = body_font.render(room.room_type, True, (240, 240, 240))
                surface.blit(label_surf, (rect.x + 4, rect.y + 4))

                # occupants (small circles at bottom)
                occs = occupants_by_roomtype.get(room.room_type, [])
                for i, person in enumerate(occs[:4]):
                    cx = rect.x + 10 + i * 14
                    cy = rect.bottom - 10
                    pygame.draw.circle(surface, (230, 230, 230), (cx, cy), 4)

            cell_rects.append((r, c, rect))

    # --- Right panel: room types to build ---
    roomtype_button_rects: List[Tuple[str, pygame.Rect]] = []
    cancel_build_rect: Optional[pygame.Rect] = None

    x_r = side_rect.x + 10
    y_r = side_rect.y + 10

    header = body_font.render("Build Rooms", True, (255, 255, 255))
    surface.blit(header, (x_r, y_r))
    y_r += header.get_height() + 4

    info_lines = [
        "Select a room type below,",
        "then click on an empty",
        "space in the grid to build.",
        "",
        "Personnel on tasks will",
        "appear in relevant rooms.",
    ]
    for line in info_lines:
        s = body_font.render(line, True, (190, 190, 190))
        surface.blit(s, (x_r, y_r))
        y_r += s.get_height() + 1

    y_r += 6

    btn_w = side_rect.width - 20
    btn_h = 30
    gap = 6

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

    # Cancel build button (only in build mode)
    if mode == "build":
        cancel_build_rect = pygame.Rect(
            x_r,
            side_rect.bottom - btn_h - 10,
            btn_w,
            btn_h,
        )
        pygame.draw.rect(surface, (120, 70, 70), cancel_build_rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), cancel_build_rect, width=1, border_radius=4)
        cancel_surf = body_font.render("Cancel Build", True, (255, 255, 255))
        surface.blit(cancel_surf, cancel_surf.get_rect(center=cancel_build_rect.center))

    return cell_rects, roomtype_button_rects, cancel_build_rect
