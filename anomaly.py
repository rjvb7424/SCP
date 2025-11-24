import random
import json

def generate_description():
    with open("anomaly_descriptions.txt", "r") as f:
        descriptions = [line.strip() for line in f if line.strip()]
    return random.choice(descriptions)

class Anomaly:
    with open("anomaly_names.json", "r") as f:
        an_data = json.load(f)

    def __init__(self):
        # anomaly identity
        self.name = random.choice(self.an_data["adjectives"]) + " " + random.choice(self.an_data["nouns"])
        self.description = generate_description()
        # anomaly attributes
        self.attributes = {}
        # combat attributes
        self.attributes["resilience"] = random.randint(0, 20)
        self.attributes["deception"] = random.randint(0, 20)
        self.attributes["evasion"] = random.randint(0, 20)
    
    def get_description(self):
        return self.description

