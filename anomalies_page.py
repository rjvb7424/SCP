# anomalies_page.py
from ui_common import draw_text

def draw_anomalies_page(surface, body_font, menu_height, anomalies):
    x = 40
    y = menu_height + 20

    y = draw_text(surface, "Contained Anomalies", x, y, body_font, (255, 255, 255))
    y += 10
    
    for anomaly in anomalies:
        y += 20
        y = draw_text(
            surface,
            f"Anomaly Name: {anomaly.name}",
            x,
            y,
            body_font,
            (200, 200, 255),
        )
        for attr, value in anomaly.attributes.items():
            y = draw_text(
                surface,
                f"  {attr.capitalize()}: {value}",
                x + 20,
                y,
                body_font,
            )
