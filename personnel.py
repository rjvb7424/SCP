import random
import json

class Personnel:
    with open("names.json", "r") as f:
        _data = json.load(f)

    with open("positions.json", "r") as f:
        _positions = json.load(f)

    _all_attributes = [
        # administrative attributes
        "leadership", "logistics", "planning",
        # combat attributes
        "marksmanship", "situational_awareness", "physical_fitness",
        # research attributes
        "data_collection", "anomaly_knowledge", "analytical_thinking",
        # medical attributes
        "surgery", "psychology", "first_aid",
        # mental attributes
        "adaptability", "determination", "negotiation",
    ]

    @staticmethod
    def _generate_attribute(mu, sigma=3, lo=0, hi=20):
        """Return an int drawn from a normal distribution."""
        value = random.gauss(mu, sigma)
        value = round(value)
        value = max(lo, min(hi, value))
        return int(value)

    def __init__(self):
        # personnel identity
        self.gender = random.choice(["male", "female"])
        self.fname = random.choice(self._data["first_names"][self.gender])
        self.lname = random.choice(self._data["last_names"])

        # personnel position
        self.position = random.choice(list(self._positions.keys()))
        # get the primary and secondary attributes for this position
        primary_attrs = set(self._positions[self.position].get("primary", []))
        secondary_attrs = set(self._positions[self.position].get("secondary", []))
        # attribute means (tweak these to change “role weight”)
        # primary stats tend to be higher
        PRIMARY_MU = 12
        # secondary stats are slightly above average
        SECONDARY_MU = 10 
        # everything else is baseline
        OTHER_MU = 8     

        self.attributes = {}

        for attr in self._all_attributes:
            if attr in primary_attrs:
                mu = PRIMARY_MU
            elif attr in secondary_attrs:
                mu = SECONDARY_MU
            else:
                mu = OTHER_MU

            self.attributes[attr] = self._generate_attribute(mu=mu)

    def __repr__(self):
        return f"{self.fname} {self.lname} ({self.gender}, {self.position})"
