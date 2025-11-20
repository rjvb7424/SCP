import random
import json

class Personnel:
    with open("names.json", "r") as f:
        _data = json.load(f)

    def __init__(self):
        # personnel identity
        self.gender = random.choice(["male", "female"])
        self.fname = random.choice(self._data["first_names"][self.gender])
        self.lname = random.choice(self._data["last_names"])
        # personnel attributes
        self.attributes = {}
        # administrative attributes
        self.attributes["leadership"] = random.randint(0, 20)
        self.attributes["logistics"] = random.randint(0, 20)
        self.attributes["planning"] = random.randint(0, 20)
        # combat attributes
        self.attributes["marksmanship"] = random.randint(0, 20)
        self.attributes["situational_awareness"] = random.randint(0, 20)
        self.attributes["physical_fitness"] = random.randint(0, 20)
        # research attributes
        self.attributes["data_collection"] = random.randint(0, 20)
        self.attributes["anomaly_knowledge"] = random.randint(0, 20)
        self.attributes["analytical_thinking"] = random.randint(0, 20)
        # mental attributes
        self.attributes["adaptability"] = random.randint(0, 20)
        self.attributes["determination"] = random.randint(0, 20)
        self.attributes["negotiation"] = random.randint(0, 20)
        # medical attributes
        self.attributes["surgery"] = random.randint(0, 20)
        self.attributes["psychology"] = random.randint(0, 20)
        self.attributes["first_aid"] = random.randint(0, 20)

    def __repr__(self):
        return f"{self.fname} {self.lname} ({self.gender})"
