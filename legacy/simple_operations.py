# external imports
import json
import random

with open("countries.json", "r") as f:
    _COUNTRY_DATA = json.load(f)

with open("code_names.json", "r") as f:
    _CN_DATA = json.load(f)

class Operation:
    def __init__(self):
        self.country = random.choice(list(_COUNTRY_DATA.keys()))
        self.city = random.choice(_COUNTRY_DATA[self.country]["cities"])["city"]
        self.codename = random.choice(_CN_DATA["adjectives"]) + " " + random.choice(_CN_DATA["nouns"])
        self.lat, self.lon = _COUNTRY_DATA[self.country]["cities"][0]["lat"], _COUNTRY_DATA[self.country]["cities"][0]["lon"]
        self.priority = random.choice(["Low", "Medium", "High"])

class Operations:
    def __init__(self, count: int):
        all_locations = []
        # for each country in the dataset, gather all cities
        for country, info in _COUNTRY_DATA.items():
            # for each city in that country add to the list
            for city in info["cities"]:
                all_locations.append((country, city))
        # randomly choose 'count' locations
        chosen_locations = random.sample(all_locations, count)
        self.operations = []
        # for each country and city, create an Operation
        for country, city in chosen_locations:
            lat = city["lat"]
            lon = city["lon"]

            codename = random.choice(_CN_DATA["adjectives"]) + " " + \
                       random.choice(_CN_DATA["nouns"])
            priority = random.choice(["Low", "Medium", "High"])

            op = Operation(country, city_name, lat, lon, codename, priority)
            self.operations.append(op)

    def __iter__(self):
        return iter(self.operations)

    def __len__(self):
        return len(self.operations)

