# operations.py
import random

CITY_LOCATIONS = [
    {"id": "rome",         "city": "Rome",         "country": "Italy",             "lat": 41.9,  "lon": 12.5},
    {"id": "london",       "city": "London",       "country": "United Kingdom",    "lat": 51.5,  "lon": -0.1},
    {"id": "paris",        "city": "Paris",        "country": "France",            "lat": 48.9,  "lon": 2.4},
    {"id": "berlin",       "city": "Berlin",       "country": "Germany",           "lat": 52.5,  "lon": 13.4},
    {"id": "madrid",       "city": "Madrid",       "country": "Spain",             "lat": 40.4,  "lon": -3.7},
    {"id": "lisbon",       "city": "Lisbon",       "country": "Portugal",          "lat": 38.7,  "lon": -9.1},
    {"id": "copenhagen",   "city": "Copenhagen",   "country": "Denmark",           "lat": 55.7,  "lon": 12.6},
    {"id": "stockholm",    "city": "Stockholm",    "country": "Sweden",            "lat": 59.3,  "lon": 18.1},
    {"id": "warsaw",       "city": "Warsaw",       "country": "Poland",            "lat": 52.2,  "lon": 21.0},
    {"id": "moscow",       "city": "Moscow",       "country": "Russia",            "lat": 55.8,  "lon": 37.6},
    {"id": "new_york",     "city": "New York",     "country": "United States",     "lat": 40.7,  "lon": -74.0},
    {"id": "los_angeles",  "city": "Los Angeles",  "country": "United States",     "lat": 34.1,  "lon": -118.2},
    {"id": "rio",          "city": "Rio de Janeiro","country": "Brazil",           "lat": -22.9, "lon": -43.2},
    {"id": "buenos_aires", "city": "Buenos Aires", "country": "Argentina",         "lat": -34.6, "lon": -58.4},
    {"id": "toronto",      "city": "Toronto",      "country": "Canada",            "lat": 43.7,  "lon": -79.4},
    {"id": "beijing",      "city": "Beijing",      "country": "China",             "lat": 39.9,  "lon": 116.4},
    {"id": "tokyo",        "city": "Tokyo",        "country": "Japan",             "lat": 35.7,  "lon": 139.7},
    {"id": "seoul",        "city": "Seoul",        "country": "South Korea",       "lat": 37.6,  "lon": 126.9},
    {"id": "sydney",       "city": "Sydney",       "country": "Australia",         "lat": -33.9, "lon": 151.2},
]

OPERATION_TYPES = [
    "Recover Anomalous Object",
    "Secure Intel Cache",
    "Containment Reinforcement",
    "Covert Field Interview",
    "Track Hostile Entity",
    "Escort Sensitive Shipment",
]

CODENAME_ADJECTIVES = [
    "Silent", "Crimson", "Iron", "Glass", "Pale",
    "Hidden", "Burning", "Frozen", "Black", "Echoing",
]

CODENAME_NOUNS = [
    "Oracle", "Vanguard", "Signal", "Citadel", "Serpent",
    "Archive", "Mirage", "Aegis", "Harbor", "Monolith",
]


class Operation:
    def __init__(self, location, op_type, priority, risk, status, description):
        self.location    = location
        self.op_type     = op_type
        self.priority    = priority
        self.risk        = risk
        self.status      = status
        self.description = description
        self.codename    = self._generate_codename()

        # Build a flag path like your Personnel class does
        country_for_file = self.country.replace(" ", "_")
        self.flag_path = f"flags/Flag_of_{country_for_file}.png"

    @property
    def city(self):
        return self.location["city"]

    @property
    def country(self):
        return self.location["country"]

    @property
    def lat(self):
        return self.location["lat"]

    @property
    def lon(self):
        return self.location["lon"]

    @staticmethod
    def _generate_codename():
        adj  = random.choice(CODENAME_ADJECTIVES)
        noun = random.choice(CODENAME_NOUNS)
        return f"Operation {adj} {noun}"


def _make_random_operation():
    loc     = random.choice(CITY_LOCATIONS)
    op_type = random.choice(OPERATION_TYPES)

    priority = random.randint(1, 3)
    risk     = random.choice(["Low", "Moderate", "High", "Critical"])
    status   = random.choice(["Pending", "Planning", "Deployed"])

    if "Recover Anomalous Object" in op_type:
        template = (
            "Recovered reports of an unregistered anomalous object in {city}, {country}. "
            "Local authorities have not been briefed. Foundation assets must locate, "
            "secure, and transport the item to the nearest Site."
        )
    elif "Secure Intel Cache" in op_type:
        template = (
            "Unknown group has established an intel cache in {city}, {country}. "
            "Operation team is to infiltrate, extract all relevant data, and sanitize "
            "the area before hostile elements can respond."
        )
    elif "Containment Reinforcement" in op_type:
        template = (
            "Existing containment protocols in {city}, {country} are at risk of "
            "compromise. Field team will assess the situation and reinforce the site "
            "before a public incident occurs."
        )
    elif "Covert Field Interview" in op_type:
        template = (
            "Civilian witness in {city}, {country} has observed anomalous activity. "
            "Agents must perform a covert interview, evaluate credibility, and apply "
            "amnestics if required."
        )
    elif "Track Hostile Entity" in op_type:
        template = (
            "Hostile anomalous entity was last sighted near {city}, {country}. "
            "Track and pin down the target while minimizing civilian exposure."
        )
    else:  # Escort Sensitive Shipment
        template = (
            "A high-value anomalous shipment is transiting through {city}, {country}. "
            "Operation team will escort and protect the cargo until it reaches its "
            "secured destination."
        )

    description = template.format(city=loc["city"], country=loc["country"])

    return Operation(loc, op_type, priority, risk, status, description)


class Operations:
    def __init__(self, num_operations=10):
        self.operations = [_make_random_operation() for _ in range(num_operations)]
        self.current_index = 0 if self.operations else None

    def __len__(self):
        return len(self.operations)

    @property
    def current(self):
        if self.current_index is None or not self.operations:
            return None
        return self.operations[self.current_index]

    def select(self, index: int):
        if 0 <= index < len(self.operations):
            self.current_index = index

    def next(self):
        if self.operations:
            self.current_index = (self.current_index + 1) % len(self.operations)

    def previous(self):
        if self.operations:
            self.current_index = (self.current_index - 1) % len(self.operations)
