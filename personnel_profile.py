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


def draw_personnel_page(surface, person, flag_image, title_font, body_font, width, height, menu_height):
    margin = 30
    top = menu_height + 20
    card_width = width - margin * 2

    # --- Page title ---
    title_text = "Personnel Profile"
    title_surf = title_font.render(title_text, True, (255, 255, 255))
    surface.blit(title_surf, (margin, top))
    top += title_surf.get_height() + 10

    # --- Profile card ---
    profile_height = 160
    profile_rect = pygame.Rect(margin, top, card_width, profile_height)

    pygame.draw.rect(surface, (40, 40, 40), profile_rect, border_radius=8)
    pygame.draw.rect(surface, (90, 90, 90), profile_rect, width=1, border_radius=8)

    # Text on LEFT
    text_x = profile_rect.x + 20
    text_y = profile_rect.y + 15

    # personnel name
    name_text = f"{person.fname} {person.lname}"
    name_surf = title_font.render(name_text, True, (255, 255, 255))
    surface.blit(name_surf, (text_x, text_y))
    text_y += name_surf.get_height() + 8

    # personnel info
    info_lines = [
        f"Gender: {person.gender}.",
        f"Nationality: {person.nationality}",
        f"Position: {person.position}",
    ]

    for line in info_lines:
        info_surf = body_font.render(line, True, (220, 220, 220))
        surface.blit(info_surf, (text_x, text_y))
        text_y += info_surf.get_height() + 3

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

    # Grouped attributes: Administrative / Combat / Research / Mental / Medical
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
            # Group title
            group_surf = body_font.render(group_name, True, (255, 255, 255))
            surface.blit(group_surf, (col_x, y))
            y += group_surf.get_height() + 2

            # Attributes in that group
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
