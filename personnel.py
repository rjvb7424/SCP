import random
import json

class Personnel:
    """Class representing a Foundation personnel member."""

    with open("countries.json", "r") as f:
        _countries = json.load(f)

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
    def _generate_gauss(mu: int, sigma: int, lo: int, hi: int) -> int:
        """Return an integer from a normal distribution."""
        value = random.gauss(mu, sigma)
        value = round(value)
        value = max(lo, min(hi, value))
        return int(value)

    def __init__(self, position=None):
        # basic flags
        self.isAlive = True
        self.isInjured = False

        # task management
        self.current_task = None
        self.busy_until_day = 0

        # personnel identity
        self.gender = random.choice(["male", "female"])
        self.age = self._generate_gauss(mu=27, sigma=4, lo=22, hi=35)

        # select a random country of origin
        country_name = random.choice(list(self._countries.keys()))
        country_data = self._countries[country_name]

        self.country = country_name                      # if you want to store it
        self.nationality = country_data["nationality"]

        # pick a birth city (dict with city/lat/lon)
        city_data = random.choice(country_data["cities"])
        self.city_of_birth = city_data["city"]
        self.city_lat = city_data["lat"]
        self.city_lon = city_data["lon"]

        # pick first language used for name generation
        self.first_language = random.choice(country_data["languages"])

        # generate first and last names based on the first language
        self.fname = random.choice(
            self._names["first_names"][self.first_language][self.gender]
        )
        self.lname = random.choice(
            self._names["last_names"][self.first_language]
        )

        # a postion will be generated if none is provided or if the provided one is invalid
        if position is not None and position in self._positions:
            self.position = position
        else:
            self.position = random.choice(list(self._positions.keys()))

        # fetch primary and secondary attributes for this position
        self.primary_attrs = set(self._positions[self.position].get("primary", []))
        self.secondary_attrs = set(self._positions[self.position].get("secondary", []))

        PRIMARY_MU = 12
        SECONDARY_MU = 10
        OTHER_MU = 8

        # generate attributes
        self.attributes = {}
        for attr in self._all_attributes:
            # if primary attribute, use higher mean
            if attr in self.primary_attrs:
                mu = PRIMARY_MU
            # if secondary attribute, use lower mean
            elif attr in self.secondary_attrs:
                mu = SECONDARY_MU
            # otherwise, use base mean
            else:
                mu = OTHER_MU
            self.attributes[attr] = self._generate_gauss(mu=mu, sigma=3, lo=0, hi=20)

        self.known_attributes = set() # subset of attr names we actually know

        for attr in self._all_attributes:
            value = self._generate_gauss(mu=10, sigma=3, lo=0, hi=20)
            self.attributes[attr] = value

            # 70% chance Foundation has solid data on this attribute
            if random.random() < 0.7:
                self.known_attributes.add(attr)

    def __repr__(self):
        return f"{self.fname.capitalize()} {self.lname.capitalize()}"
    
    def get_full_name(self) -> str:
        return f"{self.fname.capitalize()} {self.lname.capitalize()}"
    
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

