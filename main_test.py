# external imports
import pygame
# internal imports
from anomalies_page import draw_anomalies_page
from anomaly import Anomaly
from ui_elements import draw_title_text, draw_body_text, draw_primary_button, draw_secondary_button
from sidebar_menu import draw_sidebar
from top_bar import draw_top_bar, TOP_BAR_HEIGHT
from staff_page import draw_staff_page
from personnel import Personnel


def main():
    pygame.init()

    display_info = pygame.display.Info()
    WIDTH, HEIGHT = display_info.current_w, display_info.current_h

    PAGES = [
        ("staff", "Staff"),
        ("anomalies", "Anomalies"),
    ]
    SIDEBAR_WIDTH = 200
    CONTENT_X = SIDEBAR_WIDTH + 30

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("UI Button Test")
    clock = pygame.time.Clock()

    anomalies = [Anomaly() for _ in range(3)]
    staff = [Personnel() for _ in range(5)]

    # dummy facility resources (swap later with real game state)
    resources = {
        "site_name": "Site-13",
        "funds": 125000,
        "staff": 23,
        "date": "12 Mar 2031",
    }

    current_page = "anomalies"
    sidebar_button_rects = {}

    selected_anomaly_index = 0
    anomaly_menu_rects = {}

    selected_staff_index = 0
    staff_menu_rects = {}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                new_width, new_height = event.w, event.h
                screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                for page_id, rect in sidebar_button_rects.items():
                    if rect.collidepoint(mx, my):
                        current_page = page_id
                        break

                if current_page == "anomalies":
                    for idx, rect in anomaly_menu_rects.items():
                        if rect.collidepoint(mx, my):
                            selected_anomaly_index = idx
                            break

                elif current_page == "staff":
                    for idx, rect in staff_menu_rects.items():
                        if rect.collidepoint(mx, my):
                            selected_staff_index = idx
                            break

        # --- drawing ---
        screen.fill((20, 20, 25))

        # global top bar (always visible)
        draw_top_bar(screen, resources)

        # main content
        if current_page == "anomalies":
            anomaly_menu_rects = draw_anomalies_page(screen, anomalies, selected_anomaly_index, CONTENT_X, top_offset=TOP_BAR_HEIGHT)
        elif current_page == "staff":
            staff_menu_rects = draw_staff_page(screen, staff, selected_staff_index, CONTENT_X,top_offset=TOP_BAR_HEIGHT)
        else:
            anomaly_menu_rects = {}

        # sidebar sits under the top bar
        sidebar_button_rects = draw_sidebar(
            screen,
            SIDEBAR_WIDTH,
            current_page,
            PAGES,
            top_offset=TOP_BAR_HEIGHT,
        )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
