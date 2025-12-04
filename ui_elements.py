import pygame

# constants
FONT = "arial"
COLOR = (220, 220, 220)
GAP = 4

def draw_title_text(surface, text, x, y, color=COLOR):
    """Draws title text on the given surface and returns the new y position."""
    font = pygame.font.SysFont(FONT, 24)
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + GAP

def draw_body_text(surface, text, x, y, color=COLOR):
    """Draws body text on the given surface and returns the new y position."""
    font = pygame.font.SysFont(FONT, 16)
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + GAP

def draw_footer_text(surface, text, x, y, color=COLOR):
    """Draws footer text on the given surface and returns the new y position."""
    font = pygame.font.SysFont(FONT, 14)
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + GAP