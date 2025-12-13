# calendar_page.py
import pygame
from tasks import TaskManager, day_to_date, get_tasks_for_person


def draw_calendar_page(
    surface,
    task_manager: TaskManager,
    staff_roster,
    current_day: int,
    selected_staff_index,
    title_font,
    body_font,
    width,
    height,
    menu_height,
):
    """
    Draw Football-Manager-style calendar:

    - Top: current date + 7-day strip with events.
    - Bottom-left: staff list.
    - Bottom-right: role-specific task buttons for selected staff.

    Returns:
        staff_row_rects: [(staff_index, rect), ...]
        task_button_rects: [(task_def, rect), ...]  # task_def is dict(name,duration,description)
        continue_rect: pygame.Rect for 'Continue'
    """
    margin = 30
    top = menu_height + 20
    card_width = width - margin * 2

    # --- HEADER: title + current date + Continue button ---
    date = day_to_date(current_day)
    title_text = "Calendar"
    title_surf = title_font.render(title_text, True, (255, 255, 255))
    surface.blit(title_surf, (margin, menu_height + 4))

    date_str = date.strftime("%d %b %Y")
    day_info = f"Day {current_day}  –  {date_str}"
    day_surf = body_font.render(day_info, True, (200, 200, 200))
    surface.blit(day_surf, (margin, menu_height + 4 + title_surf.get_height() + 2))

    # Continue button (top right, like FM)
    continue_rect = pygame.Rect(0, 0, 140, 32)
    continue_rect.top = menu_height + 8
    continue_rect.right = margin + card_width

    any_active_tasks = bool(task_manager.active_tasks(current_day))
    cont_bg = (70, 120, 70) if any_active_tasks else (55, 80, 55)
    cont_text_col = (255, 255, 255) if any_active_tasks else (180, 180, 180)

    pygame.draw.rect(surface, cont_bg, continue_rect, border_radius=4)
    pygame.draw.rect(surface, (90, 90, 90), continue_rect, width=1, border_radius=4)
    cont_text = body_font.render("Continue", True, cont_text_col)
    surface.blit(cont_text, cont_text.get_rect(center=continue_rect.center))

    # --- TOP: 7-day calendar strip ---
    strip_top = top
    strip_height = 140
    strip_rect = pygame.Rect(margin, strip_top, card_width, strip_height)

    pygame.draw.rect(surface, (40, 40, 40), strip_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), strip_rect, width=1, border_radius=8)

    days_to_show = 7
    gap = 6
    inner_w = strip_rect.width - (days_to_show + 1) * gap
    day_box_w = inner_w // days_to_show
    day_box_h = strip_rect.height - 2 * gap

    for i in range(days_to_show):
        day_index = current_day + i
        box_x = strip_rect.x + gap + i * (day_box_w + gap)
        box_y = strip_rect.y + gap
        box_rect = pygame.Rect(box_x, box_y, day_box_w, day_box_h)

        # Highlight current day
        if day_index == current_day:
            bg = (80, 80, 100)
            border = (180, 180, 220)
        else:
            bg = (50, 50, 50)
            border = (90, 90, 90)

        pygame.draw.rect(surface, bg, box_rect, border_radius=4)
        pygame.draw.rect(surface, border, box_rect, width=1, border_radius=4)

        this_date = day_to_date(day_index)
        date_label = this_date.strftime("%d %b")
        weekday_label = this_date.strftime("%a")

        date_surf = body_font.render(date_label, True, (240, 240, 240))
        weekday_surf = body_font.render(weekday_label, True, (200, 200, 200))

        surface.blit(date_surf, (box_rect.x + 6, box_rect.y + 4))
        surface.blit(weekday_surf, (box_rect.x + 6, box_rect.y + 4 + date_surf.get_height()))

        # Show tasks that END on this day
        tasks_today = task_manager.tasks_ending_on(day_index)
        y = box_rect.y + 4 + date_surf.get_height() + weekday_surf.get_height() + 4

        for t in tasks_today[:3]:
            label = f"{t.name} – {t.assignee.fname}"
            label_surf = body_font.render(label, True, (220, 220, 220))
            if label_surf.get_width() > box_rect.width - 8:
                # simple truncation
                while label and label_surf.get_width() > box_rect.width - 20:
                    label = label[:-1]
                    label_surf = body_font.render(label + "…", True, (220, 220, 220))
            surface.blit(label_surf, (box_rect.x + 4, y))
            y += label_surf.get_height() + 1

        if len(tasks_today) > 3:
            more = f"+{len(tasks_today) - 3} more"
            more_surf = body_font.render(more, True, (190, 190, 190))
            surface.blit(more_surf, (box_rect.x + 4, box_rect.bottom - more_surf.get_height() - 2))

    # --- BOTTOM SECTION: staff list + task buttons ---
    bottom_top = strip_rect.bottom + 10
    bottom_height = height - bottom_top - margin

    left_rect = pygame.Rect(margin, bottom_top, int(card_width * 0.55), bottom_height)
    right_rect = pygame.Rect(
        left_rect.right + 10, bottom_top, card_width - left_rect.width - 10, bottom_height
    )

    pygame.draw.rect(surface, (40, 40, 40), left_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), left_rect, width=1, border_radius=8)

    pygame.draw.rect(surface, (40, 40, 40), right_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), right_rect, width=1, border_radius=8)

    # --- Staff list (left) ---
    staff_row_rects = []
    padding = 10
    y = left_rect.y + padding

    for idx, person in enumerate(staff_roster.members):
        row_h = 44
        row_rect = pygame.Rect(
            left_rect.x + padding,
            y,
            left_rect.width - 2 * padding,
            row_h,
        )

        status = getattr(person, "status", "Active")
        has_task = getattr(person, "current_task", None) is not None

        if idx == selected_staff_index:
            bg = (80, 80, 110)
        else:
            bg = (55, 55, 55)

        if status.lower() == "kia":
            bg = (70, 40, 40)

        pygame.draw.rect(surface, bg, row_rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), row_rect, width=1, border_radius=4)

        # First line: name + position
        name = f"{person.fname} {person.lname}"
        line1 = f"{name} – {person.position}"
        line1_surf = body_font.render(line1, True, (230, 230, 230))
        surface.blit(line1_surf, (row_rect.x + 6, row_rect.y + 4))

        # Second line: status + task
        if status.lower() == "active":
            status_color = (160, 230, 160)
        elif status.lower() == "injured":
            status_color = (230, 200, 100)
        elif status.lower() == "kia":
            status_color = (230, 100, 100)
        else:
            status_color = (200, 200, 200)

        status_text = f"Status: {status}"
        status_surf = body_font.render(status_text, True, status_color)
        surface.blit(status_surf, (row_rect.x + 6, row_rect.y + 20))

        task_text = "Idle"
        if has_task and person.current_task.status == "Active":
            rem = person.current_task.remaining_days(current_day)
            task_text = f"{person.current_task.name} ({rem}d left)"

        task_surf = body_font.render(task_text, True, (200, 200, 200))
        surface.blit(
            task_surf,
            (row_rect.right - task_surf.get_width() - 6, row_rect.y + 20),
        )

        staff_row_rects.append((idx, row_rect))
        y += row_h + 4

    # --- Right: role-specific task buttons for selected staff ---
    task_button_rects = []
    padding_r = 10
    x_r = right_rect.x + padding_r
    y_r = right_rect.y + padding_r

    header = body_font.render("Assign Task", True, (255, 255, 255))
    surface.blit(header, (x_r, y_r))
    y_r += header.get_height() + 6

    instructions = [
        "Select staff on the left.",
        "Choose a task below.",
        "Click 'Continue' to",
        "simulate time until",
        "the next event.",
    ]
    for line in instructions:
        s = body_font.render(line, True, (180, 180, 180))
        surface.blit(s, (x_r, y_r))
        y_r += s.get_height() + 1

    y_r += 6

    valid_selection = (
        selected_staff_index is not None
        and 0 <= selected_staff_index < len(staff_roster.members)
    )

    if valid_selection:
        person = staff_roster.members[selected_staff_index]
        status = getattr(person, "status", "Active")
        can_assign = (status == "Active") and (person.current_task is None)

        # Role-specific task definitions
        task_defs = get_tasks_for_person(person)
    else:
        person = None
        can_assign = False
        task_defs = []

    # Draw buttons for each available task
    btn_w = right_rect.width - 2 * padding_r
    btn_h = 32
    gap_btn = 6

    for tdef in task_defs:
        rect = pygame.Rect(x_r, y_r, btn_w, btn_h)

        if can_assign:
            bg = (70, 100, 140)
            text_col = (255, 255, 255)
        else:
            bg = (55, 65, 80)
            text_col = (160, 160, 160)

        pygame.draw.rect(surface, bg, rect, border_radius=4)
        pygame.draw.rect(surface, (90, 90, 90), rect, width=1, border_radius=4)

        label = f"{tdef['name']} ({tdef['duration']} days)"
        txt_surf = body_font.render(label, True, text_col)
        surface.blit(txt_surf, txt_surf.get_rect(midleft=(rect.x + 8, rect.centery)))

        task_button_rects.append((tdef, rect))
        y_r += btn_h + gap_btn

    # If the person is busy or not Active, show why
    if valid_selection and not can_assign:
        reason = "Personnel not available."
        if person.status != "Active":
            reason = "Personnel not fit for duty."
        elif person.current_task is not None:
            reason = "Personnel already assigned."

        reason_surf = body_font.render(reason, True, (220, 180, 120))
        surface.blit(reason_surf, (x_r, right_rect.bottom - reason_surf.get_height() - 8))

    return staff_row_rects, task_button_rects, continue_rect
