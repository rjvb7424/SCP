from ui_elements import draw_title_text, draw_header_text, draw_body_text, draw_primary_button, draw_accept_button

def draw_anomaly_page(surface, anomaly):
    X = 20
    y = 0
    y = draw_title_text(surface, f"{anomaly.get_name()}", X, y)
    y += 10
    y = draw_header_text(surface, f"Special Containment Procedures:", X, y)
    y = draw_body_text(surface, anomaly.get_containment_procedures(), X, y)