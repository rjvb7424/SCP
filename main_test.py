# external imports
import pygame
# internal imports
from anomalies_page import draw_anomalies_page
from anomaly_page import draw_anomaly_page
from anomaly import Anomaly
from ui_elements import draw_title_text, draw_body_text, draw_primary_button, draw_secondary_button
from sidebar import draw_sidebar

# constants
WIDTH, HEIGHT = 800, 600

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
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

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # check sidebar button clicks
                for page_id, rect in sidebar_button_rects.items():
                    if rect.collidepoint(mx, my):
                        current_page = page_id
                        break

                # you can keep your other click logic here (for page-specific buttons)
                # e.g. add anomaly buttons, etc.

        # --- drawing ---
        screen.fill((20, 20, 25))  # background

        # main content (drawn behind the sidebar)
        if current_page == "anomalies":
            # your anomalies list page
            draw_anomalies_page(screen, anomalies)
        elif current_page == "anomaly":
            # your single anomaly page
            draw_anomaly_page(screen, anomalies[0])
        elif current_page == "research":
            draw_anomaly_page(screen, anomalies[1])
        elif current_page == "facility":
            draw_anomaly_page(screen, anomalies[2])

        # draw sidebar last so it sits on top of the content
        sidebar_button_rects = draw_sidebar(screen, current_page)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
