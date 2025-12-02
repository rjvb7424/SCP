import random
import json

class Personnel:
    """Class representing a Foundation personnel member."""

    with open("nationalities.json", "r") as f:
        _nationalities = json.load(f)

    with open("names.json", "r") as f:
        _names = json.load(f)

    with open("positions.json", "r") as f:
        _positions = json.load(f)

    with open("backstories.json", "r") as f:
        _backstories = json.load(f)

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
    def _generate_attribute(mu, sigma=4, lo=0, hi=20):
        """Return an int drawn from a normal distribution."""
        value = random.gauss(mu, sigma)
        value = round(value)
        value = max(lo, min(hi, value))
        return int(value)

    def _generate_biography(self, site_name: str = "Site-██") -> str:
        """
        Build a biography by stitching together a childhood and adulthood
        backstory template from backstories.json and filling in placeholders.
        """
        # pronouns
        if self.gender == "male":
            he_she = "he"
            him_her = "him"
            his_her = "his"
        else:
            he_she = "she"
            him_her = "her"
            his_her = "her"

        ctx = {
            "fname": self.fname,
            "lname": self.lname,
            "country": self.nationality,
            "first_language": self.first_language,
            "position": self.position,
            "position_lower": self.position.lower(),
            "site": site_name,
            "he_she": he_she,
            "him_her": him_her,
            "his_her": his_her,
        }

        def fill(template: str) -> str:
            for key, value in ctx.items():
                template = template.replace("{" + key + "}", value)
            return template

        child_tpl = random.choice(self._backstories["childhood"])
        adult_tpl = random.choice(self._backstories["adulthood"])

        return fill(child_tpl) + " " + fill(adult_tpl)

    # -------- Normal init --------

    def __init__(self, position=None):
        # --- Identity ---
        self.gender = random.choice(["male", "female"])

        # nationality + language
        self.nationality = random.choice(list(self._nationalities.keys()))
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

        # --- Demographic / physical info (FM-style profile numbers) ---

        # Age – centred around mid-30s, clamped to [22, 65]
        self.age = self._generate_attribute(mu=38, sigma=7, lo=22, hi=65)

        # Height (simple gendered Gaussian, in cm)
        if self.gender == "male":
            self.height_cm = self._generate_attribute(mu=180, sigma=7, lo=160, hi=200)
        else:
            self.height_cm = self._generate_attribute(mu=167, sigma=6, lo=150, hi=190)

        # Years of service – capped so it never exceeds (age - 18)
        raw_service_years = self._generate_attribute(mu=8, sigma=4, lo=0, hi=30)
        self.years_of_service = min(raw_service_years, max(0, self.age - 18))

        # Foundation-style clearance level
        self.clearance_level = random.choice(
            ["Level 1", "Level 2", "Level 3", "Level 4"]
        )

        # Simple morale “rating” (0–20). You can expand this later.
        self.morale = self._generate_attribute(mu=11, sigma=3, lo=0, hi=20)

        # --- Position & skill attributes ---

        if position is not None and position in self._positions:
            self.position = position
        else:
            self.position = random.choice(list(self._positions.keys()))

        self.primary_attrs = set(self._positions[self.position].get("primary", []))
        self.secondary_attrs = set(self._positions[self.position].get("secondary", []))

        PRIMARY_MU = 12
        SECONDARY_MU = 10
        OTHER_MU = 8

        self.attributes = {}
        for attr in self._all_attributes:
            if attr in self.primary_attrs:
                mu = PRIMARY_MU
            elif attr in self.secondary_attrs:
                mu = SECONDARY_MU
            else:
                mu = OTHER_MU
            self.attributes[attr] = self._generate_attribute(mu=mu)

        # --- Mission / health state ---
        self.status = "Active"   # Active / Injured / KIA / On Leave etc.
        self.alive = True
        self.on_mission = False

        # --- Task / calendar state ---
        self.current_task = None          # Task object or None
        self.busy_until_day = 0           # day index when this person becomes free

        # --- Biography / backstory ---
        self.biography = self._generate_biography()

    def __repr__(self):
        return f"{self.fname} {self.lname}"
