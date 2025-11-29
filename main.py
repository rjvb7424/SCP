import pygame
import sys

from staff import Staff
from personnel_profile import draw_personnel_page
from operations import Operations
from operations_page import draw_operations_page

pygame.init()

FPS = 60
MENU_HEIGHT = 40

# --- START "FULLSCREEN-SIZED" BUT RESIZABLE ---
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h  # start at monitor size
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

# --- Positions that must always exist at game start ---
KEY_POSITIONS = [
    "Site Director",
    "Chief of Security",
    "Chief Researcher",
]


def load_flag_image(path, size=(64, 40)):
    if not path:
        return None
    try:
        flag_img = pygame.image.load(path).convert_alpha()
        flag_img = pygame.transform.smoothscale(flag_img, size)
        return flag_img
    except pygame.error as e:
        print(f"Could not load flag image {path}: {e}")
        return None


# --- Generate starting staff roster ---
staff_roster = Staff(
    key_positions=KEY_POSITIONS,
    num_random=5,   # number of extra random staff
)

# Preload flag images for each member
flag_images = [load_flag_image(p.flag_path) for p in staff_roster.members]

# --- Operations setup ---
operations_manager = Operations(num_operations=10)

# Preload flag images for each operation (country flags)
operation_flag_images = [load_flag_image(op.flag_path) for op in operations_manager.operations]

# Load world map image (your file is world_map.jpg)
try:
    world_map_image = pygame.image.load("world_map.jpg").convert()
except pygame.error as e:
    print(f"Could not load world_map.jpg: {e}")
    world_map_image = None

# Fonts
title_font = pygame.font.Font(None, 32)
body_font = pygame.font.Font(None, 26)
menu_font = pygame.font.Font(None, 24)

# Simple “tabs” at the top
menu_items = [
    {"name": "Personnel File", "page": "personnel", "rect": pygame.Rect(20, 5, 150, 30)},
    {"name": "Anomalies",      "page": "anomalies", "rect": pygame.Rect(190, 5, 150, 30)},
    {"name": "Operations",     "page": "operations", "rect": pygame.Rect(360, 5, 150, 30)},
]

current_page = "personnel"

# Operations UI state
operation_mode = "view"         # "view" or "assign"
selected_team_indices = set()   # indices into staff_roster.members

# Clickable zones
staff_menu_rects = []           # for personnel chips
operation_marker_rects = []     # for operation markers on the map
op_execute_rect = None
op_cancel_rect = None
op_confirm_rect = None
op_staff_item_rects = []


def draw_text(surface, text, x, y, font, color=(220, 220, 220)):
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + 4


def draw_menu(surface, current_page):
    pygame.draw.rect(surface, (20, 20, 20), (0, 0, WIDTH, MENU_HEIGHT))

    for item in menu_items:
        is_active = (item["page"] == current_page)
        rect = item["rect"]

        bg = (60, 60, 60) if is_active else (40, 40, 40)
        border = (120, 120, 120)

        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, border, rect, width=1, border_radius=4)

        text_surf = menu_font.render(item["name"], True, (230, 230, 230))
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)


def draw_anomalies_page(surface):
    x = 40
    y = MENU_HEIGHT + 20

    y = draw_text(surface, "Contained Anomalies", x, y, body_font, (255, 255, 255))
    y += 10
    y = draw_text(surface, "- SCP-173: Euclid", x, y, body_font)
    y = draw_text(surface, "- SCP-049: Euclid", x, y, body_font)
    y = draw_text(surface, "- SCP-682: Keter", x, y, body_font)
    # later: replace with real anomaly list


running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.VIDEORESIZE:
            WIDTH, HEIGHT = event.w, event.h
            screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

        elif event.type == pygame.KEYDOWN:
            # ESC to quit
            if event.key == pygame.K_ESCAPE:
                running = False

            elif event.key == pygame.K_RIGHT:
                if current_page == "personnel":
                    staff_roster.next()
                elif current_page == "operations":
                    operations_manager.next()
                    operation_mode = "view"
                    selected_team_indices.clear()

            elif event.key == pygame.K_LEFT:
                if current_page == "personnel":
                    staff_roster.previous()
                elif current_page == "operations":
                    operations_manager.previous()
                    operation_mode = "view"
                    selected_team_indices.clear()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Top menu tabs
            for item in menu_items:
                if item["rect"].collidepoint(mx, my):
                    current_page = item["page"]
                    if current_page != "operations":
                        operation_mode = "view"
                        selected_team_indices.clear()

            # Staff selector (personnel page)
            if current_page == "personnel":
                for idx, rect in staff_menu_rects:
                    if rect.collidepoint(mx, my):
                        staff_roster._current_index = idx
                        break

            # Operations page interactions
            elif current_page == "operations":
                # Click markers on the map (select operation)
                for idx, rect in operation_marker_rects:
                    if rect.collidepoint(mx, my):
                        operations_manager.select(idx)
                        operation_mode = "view"
                        selected_team_indices.clear()
                        break

                # VIEW MODE: click Execute
                if operation_mode == "view":
                    if op_execute_rect and op_execute_rect.collidepoint(mx, my):
                        op = operations_manager.current
                        if op and op.status == "Available":
                            any_active = any(
                                getattr(p, "status", "Active") == "Active"
                                for p in staff_roster.members
                            )
                            if any_active:
                                operation_mode = "assign"
                                selected_team_indices.clear()

                # ASSIGN MODE: select staff / confirm / cancel
                elif operation_mode == "assign":
                    # Toggle staff selection
                    for s_idx, rect in op_staff_item_rects:
                        if rect.collidepoint(mx, my):
                            person = staff_roster.members[s_idx]
                            if getattr(person, "status", "Active") == "Active":
                                if s_idx in selected_team_indices:
                                    selected_team_indices.remove(s_idx)
                                else:
                                    selected_team_indices.add(s_idx)
                            break

                    # Cancel assignment
                    if op_cancel_rect and op_cancel_rect.collidepoint(mx, my):
                        operation_mode = "view"
                        selected_team_indices.clear()

                    # Confirm & launch mission
                    elif op_confirm_rect and op_confirm_rect.collidepoint(mx, my):
                        if selected_team_indices:
                            team = []
                            for s_idx in selected_team_indices:
                                if 0 <= s_idx < len(staff_roster.members):
                                    person = staff_roster.members[s_idx]
                                    if getattr(person, "status", "Active") == "Active":
                                        team.append(person)
                            if team:
                                op = operations_manager.current
                                if op:
                                    op.simulate(team)
                        operation_mode = "view"
                        selected_team_indices.clear()

    screen.fill((30, 30, 30))

    # draw menu bar
    draw_menu(screen, current_page)

    # draw current page content
    if current_page == "personnel":
        if len(staff_roster) > 0:
            person = staff_roster.current
            idx = staff_roster.current_index
            flag_image = flag_images[idx] if 0 <= idx < len(flag_images) else None

            staff_menu_rects = draw_personnel_page(
                screen,
                person,
                flag_image,
                title_font,
                body_font,
                WIDTH,
                HEIGHT,
                MENU_HEIGHT,
                idx,
                len(staff_roster),
                staff_roster.members,
            )
        else:
            staff_menu_rects = []

    elif current_page == "anomalies":
        draw_anomalies_page(screen)

    elif current_page == "operations":
        (
            operation_marker_rects,
            op_execute_rect,
            op_cancel_rect,
            op_confirm_rect,
            op_staff_item_rects,
        ) = draw_operations_page(
            screen,
            world_map_image,
            operations_manager,
            operation_flag_images,
            staff_roster,
            operation_mode,
            selected_team_indices,
            title_font,
            body_font,
            WIDTH,
            HEIGHT,
            MENU_HEIGHT,
        )

    pygame.display.flip()

pygame.quit()
sys.exit()
