# anomalies_page.py
from ui_elements import draw_title_text, draw_body_text, draw_primary_button, draw_accept_button

def draw_anomalies_page(surface, menu_height, anomalies):
    x = 40
    y = menu_height + 20

    y = draw_title_text(surface, "Contained Anomalies", x, y)
    y += 10
    
    for anomaly in anomalies:
        y += 20
        y = draw_body_text(surface, f"Anomaly Name: {anomaly.name}", x, y)
        for attr, value in anomaly.attributes.items():
            y = draw_body_text( surface, f"{attr.capitalize()}: {value}", x + 20, y,)

    primary_button_rect = draw_primary_button(surface, "Add Anomaly", x, y + 30, 150, 40)
    accept_button_rect = draw_accept_button(surface, "Secure Anomalies", x + 170, y, 200, 40)

    return primary_button_rect, accept_button_rect