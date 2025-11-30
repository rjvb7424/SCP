import pygame
import sys

from staff import Staff
from personnel_profile import draw_personnel_page
from operations import Operations
from operations_page import draw_operations_page
from tasks import TaskManager
from calendar_page import draw_calendar_page

pygame.init()

FPS = 60
MENU_HEIGHT = 40

# --- START "FULLSCREEN-SIZED" BUT RESIZABLE ---
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h  # start at monitor size
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("SCP")

clock = pygame.time.Clock()

# --- GAME TIME (Football Manager style) ---
current_day = 0   # Day 0 corresponds to BASE_DATE in tasks.py / calendar_page.py

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
    num_random=5,
)

# Preload flag images for each member
flag_images = [load_flag_image(p.flag_path) for p in staff_roster.members]

# --- Operations setup ---
operations_manager = Operations(num_operations=10)
operation_flag_images = [load_flag_image(op.flag_path) for op in operations_manager.operations]

# Load world map image
try:
    world_map_image = pygame.image.load("world_map.jpg").convert()
except pygame.error as e:
    print(f"Could not load world_map.jpg: {e}")
    world_map_image = None

# --- Task manager (calendar) ---
task_manager = TaskManager()

# Fonts
title_font = pygame.font.Font(None, 32)
body_font = pygame.font.Font(None, 26)
menu_font = pygame.font.Font(None, 24)

# Menu tabs
menu_items = [
    {"name": "Personnel File", "page": "personnel", "rect": pygame.Rect(20, 5, 150, 30)},
    {"name": "Anomalies",      "page": "anomalies", "rect": pygame.Rect(190, 5, 150, 30)},
    {"name": "Operations",     "page": "operations", "rect": pygame.Rect(360, 5, 150, 30)},
    {"name": "Calendar",       "page": "calendar",  "rect": pygame.Rect(530, 5, 150, 30)},
]

current_page = "personnel"

# Operations UI state
operation_mode = "view"         # "view" or "assign"
selected_team_indices = set()

# Calendar UI state
calendar_selected_staff_index = None

# Clickable zones
staff_menu_rects = []
operation_marker_rects = []
op_execute_rect = None
op_cancel_rect = None
op_confirm_rect = None
op_staff_item_rects = []
cal_staff_rows = []
cal_task_buttons = []
cal_continue_rect = None


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
                    if current_page != "calendar":
                        calendar_selected_staff_index = None

            # PERSONNEL PAGE
            if current_page == "personnel":
                for idx, rect in staff_menu_rects:
                    if rect.collidepoint(mx, my):
                        staff_roster._current_index = idx
                        break

            # OPERATIONS PAGE
            elif current_page == "operations":
                # select operation from map
                for idx, rect in operation_marker_rects:
                    if rect.collidepoint(mx, my):
                        operations_manager.select(idx)
                        operation_mode = "view"
                        selected_team_indices.clear()
                        break

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

                elif operation_mode == "assign":
                    for s_idx, rect in op_staff_item_rects:
                        if rect.collidepoint(mx, my):
                            person = staff_roster.members[s_idx]
                            if getattr(person, "status", "Active") == "Active":
                                if s_idx in selected_team_indices:
                                    selected_team_indices.remove(s_idx)
                                else:
                                    selected_team_indices.add(s_idx)
                            break

                    if op_cancel_rect and op_cancel_rect.collidepoint(mx, my):
                        operation_mode = "view"
                        selected_team_indices.clear()

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

            # CALENDAR PAGE
            elif current_page == "calendar":
                # select staff
                for s_idx, rect in cal_staff_rows:
                    if rect.collidepoint(mx, my):
                        calendar_selected_staff_index = s_idx
                        break

                # click task buttons (role-specific)
                if (
                    calendar_selected_staff_index is not None
                    and 0 <= calendar_selected_staff_index < len(staff_roster.members)
                ):
                    person = staff_roster.members[calendar_selected_staff_index]
                    for task_def, rect in cal_task_buttons:
                        if rect.collidepoint(mx, my):
                            if (
                                person.status == "Active"
                                and person.current_task is None
                            ):
                                task_manager.create_task(
                                    task_def["name"],
                                    person,
                                    current_day,
                                    task_def["duration"],
                                    task_def["description"],
                                )
                            break

                # Continue button
                if cal_continue_rect and cal_continue_rect.collidepoint(mx, my):
                    current_day, finished_tasks = task_manager.advance_to_next_event(current_day)
                    # (Optional) you could later surface finished_tasks in a popup / log

    screen.fill((30, 30, 30))
    draw_menu(screen, current_page)

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

    elif current_page == "calendar":
        (
            cal_staff_rows,
            cal_task_buttons,
            cal_continue_rect,
        ) = draw_calendar_page(
            screen,
            task_manager,
            staff_roster,
            current_day,
            calendar_selected_staff_index,
            title_font,
            body_font,
            WIDTH,
            HEIGHT,
            MENU_HEIGHT,
        )

    pygame.display.flip()

pygame.quit()
sys.exit()
