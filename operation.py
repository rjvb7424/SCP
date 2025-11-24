import random
import json

class Operation:
    with open("code_names.json", "r") as f:
        data = json.load(f)

    def __init__(self):
        self.code_name = random.choice(self.data["adjectives"]) + " " + random.choice(self.data["nouns"])

    def __repr__(self):
        return f"{self.code_name}"
