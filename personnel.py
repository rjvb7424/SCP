import random
import json

class Personnel:
    with open("names.json", "r") as f:
        _data = json.load(f)

    def __init__(self):
        self.gender = random.choice(["male", "female"])
        self.fname = random.choice(self._data["first_names"][self.gender])
        self.lname = random.choice(self._data["last_names"])

    def __repr__(self):
        return f"{self.fname} {self.lname} ({self.gender})"
