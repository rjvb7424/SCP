# personnel.py
import random
import json


class Personnel:
    with open("nationalities.json", "r") as f:
        _nationalities = json.load(f)

    with open("names.json", "r") as f:
        _names = json.load(f)

    with open("positions.json", "r") as f:
        _positions = json.load(f)

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
    def _generate_attribute(mu, sigma=3, lo=0, hi=20):
        """Return an int drawn from a normal distribution."""
        value = random.gauss(mu, sigma)
        value = round(value)
        value = max(lo, min(hi, value))
        return int(value)

    def __init__(self, position=None):
        # personnel identity
        self.gender = random.choice(["male", "female"])

        # personnel nationality
        self.nationality = random.choice(list(self._nationalities.keys()))
        # pick a first language from the nationality's language list
        self.first_language = random.choice(
            self._nationalities[self.nationality]["languages"]
        )

        # generate first and last names based on the personnel's first language
        self.fname = random.choice(
            self._names["first_names"][self.first_language][self.gender]
        )
        self.lname = random.choice(self._names["last_names"][self.first_language])

        # build the flag path from the country field
        country = self._nationalities[self.nationality]["country"]
        country_for_file = country.replace(" ", "_")
        self.flag_path = f"flags/Flag_of_{country_for_file}.png"

        # personnel position and attributes
        if position is not None and position in self._positions:
            self.position = position
        else:
            self.position = random.choice(list(self._positions.keys()))

        # get the primary and secondary attributes for this position
        primary_attrs = set(self._positions[self.position].get("primary", []))
        secondary_attrs = set(self._positions[self.position].get("secondary", []))

        # attribute means (tweak these to change “role weight”)
        PRIMARY_MU = 12   # primary stats tend to be higher
        SECONDARY_MU = 10 # secondary stats are slightly above average
        OTHER_MU = 8      # everything else is baseline

        self.attributes = {}

        for attr in self._all_attributes:
            if attr in primary_attrs:
                mu = PRIMARY_MU
            elif attr in secondary_attrs:
                mu = SECONDARY_MU
            else:
                mu = OTHER_MU
            self.attributes[attr] = self._generate_attribute(mu=mu)

        # --- Mission / health state ---
        # "Active" staff can be sent on operations.
        # "Injured" or "KIA" staff are not selectable.
        self.status = "Active"   # Active / Injured / KIA
        self.alive = True
        self.on_mission = False  # future use if you add multi-step missions

    def __repr__(self):
        return f"{self.fname} {self.lname}"
