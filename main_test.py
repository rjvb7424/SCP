# external imports
import pygame
# internal imports
from anomalies_page import draw_anomalies_page
from anomaly_page import draw_anomaly_page
from anomaly import Anomaly
from ui_elements import draw_title_text, draw_body_text, draw_primary_button, draw_secondary_button
from sidebar_menu import draw_sidebar

def main():
    pygame.init()

    # get the current display resolution
    display_info = pygame.display.Info()
    WIDTH, HEIGHT = display_info.current_w, display_info.current_h

    # pages in the sidebar
    PAGES = [
        ("anomalies", "Anomalies"),
        ("anomaly",   "Anomaly Detail"),
        ("research",  "Research"),
        ("facility",  "Facility"),
    ]
    SIDEBAR_WIDTH = 200

    # create a window that starts "fullscreen" but is resizable
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("UI Button Test")
    clock = pygame.time.Clock()

    # test data
    anomalies = [Anomaly() for _ in range(3)]

    # which page are we on?
    current_page = "anomaly"   # default page when game starts

    # store rects for sidebar buttons so we can detect clicks
    sidebar_button_rects = {}

    running = True
    while running:
        # --- event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                # when the window is resized, update the screen surface
                new_width, new_height = event.w, event.h
                screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # check sidebar button clicks
                for page_id, rect in sidebar_button_rects.items():
                    if rect.collidepoint(mx, my):
                        current_page = page_id
                        break

        # --- drawing ---
        screen.fill((20, 20, 25))  # background

        # main content (drawn behind the sidebar)
        if current_page == "anomalies":
            draw_anomalies_page(screen, anomalies)
        elif current_page == "anomaly":
            draw_anomaly_page(screen, anomalies[0], SIDEBAR_WIDTH + 20)
        elif current_page == "research":
            draw_anomaly_page(screen, anomalies[1], SIDEBAR_WIDTH + 20)
        elif current_page == "facility":
            draw_anomaly_page(screen, anomalies[2], SIDEBAR_WIDTH + 20)

        # draw sidebar last so it sits on top of the content
        sidebar_button_rects = draw_sidebar(screen, SIDEBAR_WIDTH, current_page, PAGES)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
