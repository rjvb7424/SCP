# anomaly.py
import random
import json

class Anomaly:
    with open("anomaly_names.json", "r") as f:
        _names = json.load(f)

    _all_attributes = [
        # administrative attributes
        "leadership", "logistics", "planning",
        # combat attributes
        "marksmanship", "situational_awareness", "physical_fitness",
        # research attributes
        "data_collection", "anomaly_knowledge", "analytical_thinking",
        # mental attributes
        "adaptability", "determination", "negotiation",
        # medical attributes
        "surgery", "psychology", "first_aid",
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
        self.name = (
            "The "
            + random.choice(self._names["adjectives"])
            + " "
            + random.choice(self._names["nouns"])
        )

        # attributes + knowledge
        self.attributes = {}          # attr -> value
        self.known_attributes = set() # subset of attr names we actually know

        for attr in self._all_attributes:
            value = self._generate_gauss(mu=10, sigma=3, lo=0, hi=20)
            self.attributes[attr] = value

            # 70% chance Foundation has solid data on this attribute
            if random.random() < 0.7:
                self.known_attributes.add(attr)

        # special containment procedures
        self.containment_procedures = "Standard containment procedures apply."

    def __repr__(self):
        return f"{self.name}"
    
    def get_name(self) -> str:
        return self.name

    def get_containment_procedures(self) -> str:
        return self.containment_procedures

    def get_attribute_items(self):
        """
        Returns a list of (attribute_name, value, is_known) in a fixed order.
        """
        items = []
        for attr in self._all_attributes:
            value = self.attributes[attr]
            known = attr in self.known_attributes
            items.append((attr, value, known))
        return items
