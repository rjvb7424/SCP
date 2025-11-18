import random

def generate_description():
    with open("anomaly_descriptions.txt", "r", encoding="utf-8") as f:
        descriptions = [line.strip() for line in f if line.strip()]
    return random.choice(descriptions)

class Anomaly:
    def __init__(self):
        self.description = generate_description()
    
    def get_description(self):
        return self.description

