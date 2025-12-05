import random
import json

class Anomaly:
    with open("anomaly_names.json", "r") as f:
        _names = json.load(f)

    _all_attributes = [
        # combat attributes
        "lethality", "deception", "physical_fitness",
    ]

    @staticmethod
    def _generate_gauss(mu: int, sigma: int, lo: int, hi: int) -> int:
        """Return an integer from a normal distribution."""
        value = random.gauss(mu, sigma)
        value = round(value)
        value = max(lo, min(hi, value))
        return int(value)

    def __init__(self):
        # identity
        self.name = "The " + random.choice(self._names["adjectives"]) + " " + random.choice(self._names["nouns"])

        # generate attributes
        self.attributes = {}
        for attr in self._all_attributes:
            self.attributes[attr] = self._generate_gauss(mu=10, sigma=3, lo=0, hi=20)

        # special containment procedures
        self.containment_procedures = "Standard containment procedures apply."

    def __repr__(self):
        return f"{self.name}"
    
    def get_name(self) -> str:
        return self.name

    def get_containment_procedures(self) -> str:
        return self.containment_procedures