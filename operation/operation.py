import random
import json
import os

class Operation:
    def __init__(self):
        self.code_name = self.generate_code_name()

    def generate_code_name(self):
        base_dir = os.path.dirname(__file__)  # folder where operation.py lives
        json_path = os.path.join(base_dir, "code_names.json")

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        adjective = random.choice(data["adjectives"])
        noun = random.choice(data["nouns"])
        return f"{adjective} {noun}"

    def get_code_name(self):
        return self.code_name
