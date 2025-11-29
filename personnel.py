import random
import json

class Personnel:
    with open("names.json", "r") as f:
        _data = json.load(f)

    @staticmethod
    def _generate_attribute(mu=10, sigma=4, lo=0, hi=20):
        """Return an int drawn from a normal distribution"""
        value = random.gauss(mu, sigma)
        value = round(value)
        value = max(lo, min(hi, value))
        return int(value)

    def __init__(self):
        # personnel identity
        self.gender = random.choice(["male", "female"])
        self.fname = random.choice(self._data["first_names"][self.gender])
        self.lname = random.choice(self._data["last_names"])

        self.attributes = {}

        # administrative attributes
        self.attributes["leadership"] = self._generate_attribute()
        self.attributes["logistics"] = self._generate_attribute()
        self.attributes["planning"] = self._generate_attribute()

        # combat attributes
        self.attributes["marksmanship"] = self._generate_attribute()
        self.attributes["situational_awareness"] = self._generate_attribute()
        self.attributes["physical_fitness"] = self._generate_attribute()

        # research attributes
        self.attributes["data_collection"] = self._generate_attribute()
        self.attributes["anomaly_knowledge"] = self._generate_attribute()
        self.attributes["analytical_thinking"] = self._generate_attribute()

        # mental attributes
        self.attributes["adaptability"] = self._generate_attribute()
        self.attributes["determination"] = self._generate_attribute()
        self.attributes["negotiation"] = self._generate_attribute()

        # medical attributes
        self.attributes["surgery"] = self._generate_attribute()
        self.attributes["psychology"] = self._generate_attribute()
        self.attributes["first_aid"] = self._generate_attribute()

    def __repr__(self):
        return f"{self.fname} {self.lname} ({self.gender})"
