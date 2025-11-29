# operations.py
import random

# Real-world cities so operations land on actual countries
CITY_LOCATIONS = [
    {"id": "rome",         "city": "Rome",         "country": "Italy",             "lat": 41.9,  "lon": 12.5},
    {"id": "london",       "city": "London",       "country": "United Kingdom",    "lat": 51.5,  "lon": -0.1},
    {"id": "paris",        "city": "Paris",        "country": "France",            "lat": 48.9,  "lon": 2.4},
    {"id": "berlin",       "city": "Berlin",       "country": "Germany",           "lat": 52.5,  "lon": 13.4},
    {"id": "madrid",       "city": "Madrid",       "country": "Spain",             "lat": 40.4,  "lon": -3.7},
    {"id": "lisbon",       "city": "Lisbon",       "country": "Portugal",          "lat": 38.7,  "lon": -9.1},
    {"id": "copenhagen",   "city": "Copenhagen",   "country": "Denmark",           "lat": 55.7,  "lon": 12.6},
    {"id": "stockholm",    "city": "Stockholm",    "country": "Sweden",           "lat": 59.3,  "lon": 18.1},
    {"id": "warsaw",       "city": "Warsaw",       "country": "Poland",            "lat": 52.2,  "lon": 21.0},
    {"id": "moscow",       "city": "Moscow",       "country": "Russia",           "lat": 55.8,  "lon": 37.6},
    {"id": "new_york",     "city": "New York",     "country": "United States",    "lat": 40.7,  "lon": -74.0},
    {"id": "los_angeles",  "city": "Los Angeles",  "country": "United States",    "lat": 34.1,  "lon": -118.2},
    {"id": "rio",          "city": "Rio de Janeiro","country": "Brazil",          "lat": -22.9, "lon": -43.2},
    {"id": "buenos_aires", "city": "Buenos Aires", "country": "Argentina",        "lat": -34.6, "lon": -58.4},
    {"id": "toronto",      "city": "Toronto",      "country": "Canada",           "lat": 43.7,  "lon": -79.4},
    {"id": "beijing",      "city": "Beijing",      "country": "China",            "lat": 39.9,  "lon": 116.4},
    {"id": "tokyo",        "city": "Tokyo",        "country": "Japan",            "lat": 35.7,  "lon": 139.7},
    {"id": "seoul",        "city": "Seoul",        "country": "South Korea",      "lat": 37.6,  "lon": 126.9},  
    {"id": "sydney",       "city": "Sydney",       "country": "Australia",        "lat": -33.9, "lon": 151.2},
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
    """
    A single anomaly containment operation.
    """

    def __init__(
        self,
        location,
        anomaly_name,
        anomaly_class,
        anomaly_difficulty,  # 0–20
        priority,
        risk,
        description,
    ):
        self.location = location
        self.anomaly_name = anomaly_name
        self.anomaly_class = anomaly_class
        self.anomaly_difficulty = anomaly_difficulty  # 0–20
        self.priority = priority         # 1..3 (1 = low, 3 = high)
        self.risk = risk                 # Low / Moderate / High
        self.description = description

        self.op_type = "Anomaly Containment"
        self.status = "Available"        # Available / Completed / Failed

        self.codename = self._generate_codename()

        # Team + result state
        self.assigned_team = []          # list[Personnel]
        self.result_text = ""            # summary of outcome

        # Country flag path (same convention as Personnel)
        country_for_file = self.country.replace(" ", "_")
        self.flag_path = f"flags/Flag_of_{country_for_file}.png"

    # --- Convenience properties ---

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

    # --- Helpers ---

    @staticmethod
    def _generate_codename():
        adj = random.choice(CODENAME_ADJECTIVES)
        noun = random.choice(CODENAME_NOUNS)
        return f"Operation {adj} {noun}"

    def _team_effective_score(self, team):
        """
        Compute a single numeric score from team attributes.

        We look at combat + anomaly knowledge + determination + first aid,
        average them across the team, and map to roughly 0–100.
        """
        relevant_attrs = [
            "marksmanship",
            "situational_awareness",
            "physical_fitness",
            "anomaly_knowledge",
            "analytical_thinking",
            "determination",
            "first_aid",
        ]

        if not team:
            return 0.0

        total = 0
        count = 0
        for member in team:
            for attr in relevant_attrs:
                total += member.attributes.get(attr, 0)
            count += len(relevant_attrs)

        if count == 0:
            return 0.0

        avg_attr = total / count          # 0–20-ish
        return avg_attr * 5.0             # 0–100-ish

    def simulate(self, team):
        """
        Run the operation with the given team of Personnel.

        Updates:
          - self.status
          - self.assigned_team
          - self.result_text
          - each member.status / member.alive may change

        Returns a dict with success flag and casualty lists.
        """
        # Store team (for later display)
        self.assigned_team = list(team)

        # Scores
        team_score = self._team_effective_score(team)             # 0–100
        diff_score = self.anomaly_difficulty * 5.0                # 0–100

        # Success chance: 50% base, +/- based on score difference
        success_chance = 0.5 + (team_score - diff_score) / 100.0
        success_chance = max(0.1, min(0.9, success_chance))       # clamp

        roll = random.random()
        success = roll < success_chance

        # Casualty risk: higher when anomaly is "stronger" than team
        hazard_margin = diff_score - team_score  # positive = dangerous

        if hazard_margin <= 0:
            casualty_prob = 0.1
            death_prob = 0.0
        else:
            casualty_prob = min(0.8, 0.15 + hazard_margin / 120.0)
            death_prob = max(0.0, casualty_prob - 0.35)

        injured = []
        killed = []

        for member in team:
            r = random.random()
            if r < death_prob:
                member.status = "KIA"
                member.alive = False
                killed.append(member)
            elif r < casualty_prob:
                if getattr(member, "status", "Active") != "KIA":
                    member.status = "Injured"
                    injured.append(member)
            else:
                # stays Active
                pass

        if success:
            self.status = "Completed"
            outcome = "SUCCESS"
        else:
            self.status = "Failed"
            outcome = "FAILURE"

        # Build a human-readable summary
        lines = []
        lines.append(f"{outcome}: {self.anomaly_name} containment in {self.city}, {self.country}.")
        lines.append(
            f"Team score {team_score:.1f} vs anomaly difficulty {diff_score:.1f}."
        )

        if killed or injured:
            if killed:
                names = ", ".join(f"{m.fname} {m.lname}" for m in killed)
                lines.append(f"KIA: {names}.")
            if injured:
                names = ", ".join(f"{m.fname} {m.lname}" for m in injured)
                lines.append(f"Injured: {names}.")
        else:
            lines.append("No casualties reported.")

        self.result_text = " ".join(lines)

        return {
            "success": success,
            "team_score": team_score,
            "difficulty_score": diff_score,
            "injured": injured,
            "killed": killed,
            "outcome_text": self.result_text,
        }


def _make_random_operation():
    """
    Create a random anomaly containment operation.
    """
    loc = random.choice(CITY_LOCATIONS)

    anomaly_name = f"SCP-{random.randint(100, 999)}"
    anomaly_class = random.choice(["Safe", "Euclid", "Keter"])

    if anomaly_class == "Safe":
        difficulty = random.randint(6, 10)
    elif anomaly_class == "Euclid":
        difficulty = random.randint(10, 14)
    else:  # Keter
        difficulty = random.randint(14, 18)

    priority = {"Safe": 1, "Euclid": 2, "Keter": 3}[anomaly_class]
    risk = {"Safe": "Low", "Euclid": "Moderate", "Keter": "High"}[anomaly_class]

    description = (
        f"Containment operation targeting {anomaly_name} ({anomaly_class}) in "
        f"{loc['city']}, {loc['country']}. Field team must locate, secure, and "
        "transport the entity to an appropriate Foundation facility while "
        "minimizing civilian exposure."
    )

    return Operation(loc, anomaly_name, anomaly_class, difficulty, priority, risk, description)


class Operations:
    """
    Manages the list of active operations and which one is currently selected.
    """

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
