import pygame

# Attribute groups for display
# ui_personnel.py (or wherever draw_personnel_page lives)

ATTRIBUTE_GROUPS = {
    "Administrative": ["leadership", "logistics", "planning"],
    "Combat": ["marksmanship", "situational_awareness", "physical_fitness"],
    "Research": ["data_collection", "anomaly_knowledge", "analytical_thinking"],
    "Mental": ["adaptability", "determination", "negotiation"],
    "Medical": ["surgery", "psychology", "first_aid"],
    "Personal": ["discipline", "loyalty", "stress_resilience"],
}

def draw_badge(surface, text, x, y, font,
               bg=(60, 60, 90), fg=(230, 230, 230),
               border=(140, 140, 200)):
    padding_x, padding_y = 8, 3
    text_surf = font.render(text, True, fg)
    rect = text_surf.get_rect()
    rect.topleft = (x, y)
    rect.inflate_ip(padding_x * 2, padding_y * 2)

    pygame.draw.rect(surface, bg, rect, border_radius=8)
    pygame.draw.rect(surface, border, rect, width=1, border_radius=8)

    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)
    return rect

def draw_text(surface, text, x, y, font, color=(220, 220, 220)):
    """Draw a line of text and return the next y position."""
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + 4


def lerp_color(c1, c2, t: float):
    """Linearly interpolate between two RGB colors c1 -> c2 with t in [0, 1]."""
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def get_attribute_color(value, lo=0, hi=20):
    """Map each attribute value to a corresponding color"""
    v = max(lo, min(hi, value))
    norm = (v - lo) / (hi - lo)

    red         = (220, 50, 50)
    orange      = (230, 150, 50)
    light_green = (180, 230, 100)
    dark_green  = (20, 180, 80)

    if norm < 1/3:
        t = norm / (1/3)
        return lerp_color(red, orange, t)
    elif norm < 2/3:
        t = (norm - 1/3) / (1/3)
        return lerp_color(orange, light_green, t)
    else:
        t = (norm - 2/3) / (1/3)
        return lerp_color(light_green, dark_green, t)


def draw_personnel_page(
    surface,
    person,
    flag_image,
    title_font,
    body_font,
    width,
    height,
    menu_height,
    index,        # current index in roster
    total,        # total personnel
    staff_list,   # list of all Personnel objects
):
    """
    Draw the personnel page and return a list of (i, rect) for each staff
    'button' so the caller can detect clicks.
    """
    margin = 30
    top = menu_height + 20
    card_width = width - margin * 2

    staff_menu_rects = []

    # --- Page title ---
    title_text = "Personnel Profile"
    title_surf = title_font.render(title_text, True, (255, 255, 255))
    surface.blit(title_surf, (margin, top))
    top += title_surf.get_height() + 4

    # --- Counter + hint line ---
    if total > 1:
        hint_text = f"{index + 1} / {total}   (Click a position or use \u2190 / \u2192)"
        hint_surf = body_font.render(hint_text, True, (180, 180, 180))
        surface.blit(hint_surf, (margin, top))
        top += hint_surf.get_height() + 8
    else:
        top += 6

    # --- Staff selector menu (horizontal chips) ---
    chip_y = top
    x = margin
    chip_padding_x = 10
    chip_padding_y = 4
    gap_x = 8
    max_row_height = 0

    for i, member in enumerate(staff_list):
        label = member.position
        text_color = (230, 230, 230)

        text_surf = body_font.render(label, True, text_color)
        text_rect = text_surf.get_rect()

        chip_rect = pygame.Rect(
            0, 0,
            text_rect.width + chip_padding_x * 2,
            text_rect.height + chip_padding_y * 2
        )

        # Wrap to next line if too wide
        if x + chip_rect.width > width - margin:
            x = margin
            chip_y += max_row_height + 6
            max_row_height = 0

        chip_rect.topleft = (x, chip_y)

        # colors for selected vs normal
        if i == index:
            bg = (80, 80, 120)
            border = (160, 160, 220)
        else:
            bg = (40, 40, 40)
            border = (90, 90, 90)

        pygame.draw.rect(surface, bg, chip_rect, border_radius=6)
        pygame.draw.rect(surface, border, chip_rect, width=1, border_radius=6)

        text_rect.center = chip_rect.center
        surface.blit(text_surf, text_rect)

        staff_menu_rects.append((i, chip_rect))

        x += chip_rect.width + gap_x
        max_row_height = max(max_row_height, chip_rect.height)

    if max_row_height == 0:
        max_row_height = body_font.get_linesize()

    selector_bottom = chip_y + max_row_height
    top = selector_bottom + 12

    # --- Profile card ---
    profile_height = 190
    profile_rect = pygame.Rect(margin, top, card_width, profile_height)

    pygame.draw.rect(surface, (40, 40, 40), profile_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), profile_rect, width=1, border_radius=8)

    # Fixed positions for name + info text
    text_x = profile_rect.x + 20
    name_y = profile_rect.y + 15

    # personnel name
    name_text = f"{person.fname} {person.lname}"
    name_surf = title_font.render(name_text, True, (255, 255, 255))
    surface.blit(name_surf, (text_x, name_y))

    # Status & mission badges beside name (FM-style chips)
    status_color_bg = (70, 110, 70) if person.status == "Active" else (130, 80, 80)
    status_text = f"STATUS: {person.status.upper()}"
    status_rect = draw_badge(
        surface,
        status_text,
        text_x + name_surf.get_width() + 20,
        name_y + 4,
        body_font,
        bg=status_color_bg,
        fg=(235, 235, 235),
        border=(140, 200, 140) if person.status == "Active" else (200, 140, 140),
    )

    mission_label = "ON MISSION" if person.on_mission else "ON SITE"
    mission_rect = draw_badge(
        surface,
        mission_label,
        status_rect.right + 10,
        name_y + 4,
        body_font,
        bg=(60, 60, 60),
        fg=(220, 220, 220),
        border=(120, 120, 120),
    )

    # Base line for the info block (two columns)
    base_info_y = name_y + title_font.get_height() + 10
    line_height = body_font.get_linesize()

    left_info = [
        f"Gender: {person.gender.capitalize()}",
        f"Age: {person.age}",
        f"Height: {person.height_cm} cm",
    ]

    right_info = [
        f"Nationality: {person.nationality}",
        f"Position: {person.position}",
        f"Clearance: {person.clearance_level}",
    ]

    # Left column
    for i, line in enumerate(left_info):
        info_y = base_info_y + i * line_height
        info_surf = body_font.render(line, True, (220, 220, 220))
        surface.blit(info_surf, (text_x, info_y))

    # Right column
    right_x = text_x + 260  # tweak spacing if needed
    for i, line in enumerate(right_info):
        info_y = base_info_y + i * line_height
        info_surf = body_font.render(line, True, (220, 220, 220))
        surface.blit(info_surf, (right_x, info_y))

    # Bottom line: years of service + language + morale summary
    bottom_y = profile_rect.bottom - body_font.get_linesize() - 12
    service_text = f"Years of Service: {person.years_of_service}"
    language_text = f"Primary Language: {person.first_language}"
    # Simple morale descriptor based on 0–20 scale
    if person.morale >= 15:
        morale_label = "Morale: Excellent"
    elif person.morale >= 10:
        morale_label = "Morale: Stable"
    elif person.morale >= 5:
        morale_label = "Morale: Low"
    else:
        morale_label = "Morale: Critical"

    footer_line = f"{service_text}   |   {language_text}   |   {morale_label}"
    footer_surf = body_font.render(footer_line, True, (190, 190, 190))
    surface.blit(footer_surf, (text_x, bottom_y))

    # Flag on the RIGHT
    if flag_image is not None:
        flag_rect = flag_image.get_rect()
        flag_rect.right = profile_rect.right - 20
        flag_rect.centery = profile_rect.centery
        surface.blit(flag_image, flag_rect)

    # --- Attributes panel (grouped, with bars) ---
    attrs_top = profile_rect.bottom + 20
    attrs_rect = pygame.Rect(margin, attrs_top, card_width, height - attrs_top - margin)

    pygame.draw.rect(surface, (40, 40, 40), attrs_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), attrs_rect, width=1, border_radius=8)

    header_surf = body_font.render("Attributes", True, (255, 255, 255))
    surface.blit(header_surf, (attrs_rect.x + 20, attrs_rect.y + 10))

    group_items = list(ATTRIBUTE_GROUPS.items())
    left_groups = group_items[:3]
    right_groups = group_items[3:]

    line_height = body_font.get_linesize() + 4
    left_x = attrs_rect.x + 20
    right_x = attrs_rect.x + attrs_rect.width // 2 + 10
    start_y = attrs_rect.y + 40

    def draw_group_column(groups, col_x):
        y = start_y
        for group_name, attrs in groups:
            # group header
            group_surf = body_font.render(group_name, True, (240, 240, 240))
            surface.blit(group_surf, (col_x, y))
            y += group_surf.get_height() + 2

            for attr in attrs:
                if attr not in person.attributes:
                    continue

                pretty_name = attr.replace("_", " ").title()
                label = f"{pretty_name}: "
                label_surf = body_font.render(label, True, (210, 210, 210))
                surface.blit(label_surf, (col_x, y))

                value = person.attributes[attr]
                value_color = get_attribute_color(value)

                # numeric value
                value_surf = body_font.render(str(value), True, value_color)
                value_x = col_x + label_surf.get_width() + 4
                surface.blit(value_surf, (value_x, y))

                # small bar representing the value (0–20)
                bar_width = 80
                bar_height = 4
                bar_x = value_x + value_surf.get_width() + 10
                bar_y = y + (value_surf.get_height() - bar_height) // 2

                # background bar
                pygame.draw.rect(
                    surface, (25, 25, 25),
                    pygame.Rect(bar_x, bar_y, bar_width, bar_height),
                    border_radius=2
                )
                # filled portion
                fill_w = int(bar_width * (value / 20.0))
                pygame.draw.rect(
                    surface, value_color,
                    pygame.Rect(bar_x, bar_y, fill_w, bar_height),
                    border_radius=2
                )

                y += line_height

            y += 8  # gap between groups

    draw_group_column(left_groups, left_x)
    draw_group_column(right_groups, right_x)

    # Return clickable rects for the staff selector
    return staff_menu_rects
