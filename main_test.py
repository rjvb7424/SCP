# main.py
import pygame
from anomalies_page import draw_anomalies_page
from anomaly import Anomaly


def main():
    pygame.init()

    WIDTH, HEIGHT = 900, 600
    MENU_HEIGHT = 40

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("UI Button Test")
    clock = pygame.time.Clock()

    anomalies = [Anomaly() for _ in range(3)]

    secure_anomalies_button_rect = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                if (add_anomaly_button_rect.collidepoint(mx, my)):
                    anomalies[1].name = "New Anomaly"
                if (
                    secure_anomalies_button_rect
                    and secure_anomalies_button_rect.collidepoint(mx, my)
                ):
                    print("Secure Anomalies clicked!")

        # ---- DRAW ----
        screen.fill((20, 20, 25))  # background

        # (Optional) fake menu bar so you can see MENU_HEIGHT
        pygame.draw.rect(
            screen, (30, 30, 40), pygame.Rect(0, 0, WIDTH, MENU_HEIGHT)
        )

        (
            add_anomaly_button_rect,
            secure_anomalies_button_rect,
        ) = draw_anomalies_page(screen, MENU_HEIGHT, anomalies)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
