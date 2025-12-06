from ui_elements import draw_title_text, draw_header_text, draw_body_text, draw_primary_button, draw_accept_button

def draw_anomaly_page(surface, anomaly, x):
    y = 0
    y = draw_title_text(surface, f"{anomaly.get_name()}", x, y)
    y += 10
    y = draw_header_text(surface, f"Special Containment Procedures:", x, y)
    y = draw_body_text(surface, anomaly.get_containment_procedures(), x, y)