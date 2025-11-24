import random
import json

from anomaly import Anomaly

class Operation:
    with open("code_names.json", "r") as f:
        cn_data = json.load(f)

    def __init__(self):
        self.code_name = random.choice(self.cn_data["adjectives"]) + " " + random.choice(self.cn_data["nouns"])

    def __repr__(self):
        return f"{self.code_name}"
    
    def execute():
        anomaly = Anomaly()
