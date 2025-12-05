# external imports
import pygame
# internal imports
from anomalies_page import draw_anomalies_page
from anomaly_page import draw_anomaly_page
from anomaly import Anomaly

def main():
    pygame.init()

    # constants
    WIDTH, HEIGHT = 900, 600

    # pygame setup
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("UI Button Test")
    clock = pygame.time.Clock()

    # test data
    anomalies = [Anomaly() for _ in range(3)]

    # main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # check for button clicks
                # if (add_anomaly_button_rect.collidepoint(mx, my)):
                    # anomalies[1].name = "New Anomaly"
                # if (secure_anomalies_button_rect.collidepoint(mx, my)):
                    # print("Secure Anomalies clicked!")

        screen.fill((20, 20, 25))  # background

        draw_anomaly_page(screen, anomalies[0])

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

# run the main function
if __name__ == "__main__":
    main()
