# external imports
import json
import os
import random

# Load country / city data once
COUNTRIES_PATH = os.path.join(os.path.dirname(__file__), "countries.json")

with open(COUNTRIES_PATH, "r") as f:
    _COUNTRY_DATA = json.load(f)

with open("code_names.json", "r") as f:
    _CODE_NAMES = json.load(f)

class Operation:
    def __init__(self):
        self.country = random.choice(list(_COUNTRY_DATA.keys()))
        self.city = random.choice(_COUNTRY_DATA[self.country]["cities"])["city"]
        self.codename = random.choice(_CODE_NAMES["adjectives"]) + " " + random.choice(_CODE_NAMES["nouns"])
        self.lat, self.lon = _COUNTRY_DATA[self.country]["cities"][0]["lat"], _COUNTRY_DATA[self.country]["cities"][0]["lon"]
        self.priority = random.choice(["Low", "Medium", "High"])
