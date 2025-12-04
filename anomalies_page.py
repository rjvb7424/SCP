# anomalies_page.py
from ui_elements import draw_title_text, draw_body_text

def draw_anomalies_page(surface, menu_height, anomalies):
    x = 40
    y = menu_height + 20

    y = draw_title_text(surface, "Contained Anomalies", x, y)
    y += 10
    
    for anomaly in anomalies:
        y += 20
        y = draw_body_text(
            surface,
            f"Anomaly Name: {anomaly.name}",
            x,
            y,
            (200, 200, 255),
        )
        for attr, value in anomaly.attributes.items():
            y = draw_body_text(
                surface,
                f"  {attr.capitalize()}: {value}",
                x + 20,
                y,
            )
