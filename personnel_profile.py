import pygame

# Attribute groups for display
ATTRIBUTE_GROUPS = {
    "Administrative": ["leadership", "logistics", "planning"],
    "Combat": ["marksmanship", "situational_awareness", "physical_fitness"],
    "Research": ["data_collection", "anomaly_knowledge", "analytical_thinking"],
    "Mental": ["adaptability", "determination", "negotiation"],
    "Medical": ["surgery", "psychology", "first_aid"],
}


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
        # You can change this to show names instead, e.g. f"{member.fname} {member.lname}"
        label = member.position
        text_color = (230, 230, 230)

        text_surf = body_font.render(label, True, text_color)
        text_rect = text_surf.get_rect()

        chip_rect = pygame.Rect(0, 0,
                                text_rect.width + chip_padding_x * 2,
                                text_rect.height + chip_padding_y * 2)

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
    profile_height = 160
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

    # Base line for the info block (fixed below the name)
    base_info_y = name_y + title_font.get_height() + 8
    line_spacing = body_font.get_linesize()

    info_lines = [
        f"Gender: {person.gender}.",
        f"Nationality: {person.nationality}",
        f"Position: {person.position}",
    ]

    # Draw each info line at a fixed slot
    for i, line in enumerate(info_lines):
        info_y = base_info_y + i * line_spacing
        info_surf = body_font.render(line, True, (220, 220, 220))
        surface.blit(info_surf, (text_x, info_y))

    # Flag on the RIGHT
    if flag_image is not None:
        flag_rect = flag_image.get_rect()
        flag_rect.right = profile_rect.right - 20
        flag_rect.centery = profile_rect.centery
        surface.blit(flag_image, flag_rect)

    # --- Attributes panel (grouped) ---
    attrs_top = profile_rect.bottom + 20
    attrs_rect = pygame.Rect(margin, attrs_top, card_width, height - attrs_top - margin)

    pygame.draw.rect(surface, (40, 40, 40), attrs_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), attrs_rect, width=1, border_radius=8)

    header_surf = body_font.render("Attributes", True, (255, 255, 255))
    surface.blit(header_surf, (attrs_rect.x + 20, attrs_rect.y + 10))

    group_items = list(ATTRIBUTE_GROUPS.items())
    left_groups = group_items[:3]
    right_groups = group_items[3:]

    line_height = body_font.get_linesize() + 2
    left_x = attrs_rect.x + 20
    right_x = attrs_rect.x + attrs_rect.width // 2 + 10
    start_y = attrs_rect.y + 40

    def draw_group_column(groups, col_x):
        y = start_y
        for group_name, attrs in groups:
            group_surf = body_font.render(group_name, True, (255, 255, 255))
            surface.blit(group_surf, (col_x, y))
            y += group_surf.get_height() + 2

            for attr in attrs:
                if attr not in person.attributes:
                    continue
                label = f"{attr.replace('_', ' ').title()}: "
                label_surf = body_font.render(label, True, (220, 220, 220))
                surface.blit(label_surf, (col_x, y))

                value = person.attributes[attr]
                value_color = get_attribute_color(value)
                value_surf = body_font.render(str(value), True, value_color)
                surface.blit(value_surf, (col_x + label_surf.get_width(), y))

                y += line_height

            y += 8  # gap between groups

    draw_group_column(left_groups, left_x)
    draw_group_column(right_groups, right_x)

    # Return clickable rects for the staff selector
    return staff_menu_rects
