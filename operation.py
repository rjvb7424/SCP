# operations.py
import random

from dataclasses import dataclass
from operation_simulation import simulate

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

        self.simulate = simulate()

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
    
@dataclass
class OperationLogEvent:
    delay: float              # seconds until this event appears (from previous one)
    time_label: str           # "04:13", "05:36" etc
    text: str                 # log text
    color: tuple[int, int, int]  # (r, g, b)


class OperationRun:
    """
    Handles the "cinematic" execution of a single operation.
    It wraps Operation.simulate() and turns the result into a timed log.
    """

    def __init__(self, operation: Operation, team):
        self.operation = operation
        self.team = list(team)
        self.visible_events = 0   # how many log entries are currently revealed
        self.timer = 0.0          # counts up to reveal next entry
        self.finished = False

        # Run the actual simulation ONCE and keep the result
        sim_result = operation.simulate(team)
        self.sim_result = sim_result

        # Pre-build a list of narrative events from the outcome
        self.events = self._build_events(sim_result)

    def _build_events(self, sim_result):
        op = self.operation
        injured = sim_result["injured"]
        killed = sim_result["killed"]
        success = sim_result["success"]

        # Colors for the log
        NEUTRAL = (210, 210, 210)
        GOOD    = (140, 220, 140)
        BAD     = (230, 110, 110)
        WARN    = (230, 200, 140)

        # Random in-universe start time for flavor
        start_hour = random.randint(0, 23)
        start_minute = random.randint(0, 59)

        def hhmm(offset_min):
            total_min = start_hour * 60 + start_minute + offset_min
            h = (total_min // 60) % 24
            m = total_min % 60
            return f"{h:02d}:{m:02d}"

        events = []

        def add(delay_sec, offset_min, text, color):
            events.append(OperationLogEvent(
                delay=delay_sec,
                time_label=hhmm(offset_min),
                text=text,
                color=color,
            ))

        # --- Narrative beats (simple but atmospheric) ---

        # Departure / approach
        add(0.8, 0, f"{op.codename} initiated. Strike team departs for {op.city}, {op.country}.", NEUTRAL)
        add(1.0, 25, "Operatives arrive near target zone. Final equipment check.", NEUTRAL)
        add(1.0, 35, "Team advances towards the anomaly's last known location.", NEUTRAL)

        # First contact
        add(1.2, 48, f"Visual contact with {op.anomaly_name}. Behaviour classified as {op.anomaly_class}.", WARN)
        add(1.2, 52, "Operatives begin containment protocol. Civilians ordered to evacuate area.", WARN)

        # Combat / critical moment
        add(1.4, 60, "Hostile reaction from anomaly. Operatives open fire.", WARN)
        add(1.4, 72, "Radio traffic spikes. Heart rates elevated. Situation unstable.", WARN)

        # Casualties (if any)
        if injured:
            names = ", ".join(f"{m.fname} {m.lname}" for m in injured)
            add(1.4, 85, f"Medical report: {names} injured during engagement. Field treatment underway.", WARN)

        if killed:
            names = ", ".join(f"{m.fname} {m.lname}" for m in killed)
            add(1.6, 92, f"Critical update: KIA confirmed – {names}. Body recovery flagged as secondary objective.", BAD)

        # Outcome
        if success:
            add(1.6, 110, "Containment seals hold. Anomaly subdued and prepared for transport.", GOOD)
            add(1.8, 125, "Team withdraws from hot zone. Civilians cleared to return. Command reports mission success.", GOOD)
        else:
            add(1.6, 110, "Containment fails. Anomaly breaks perimeter. Team forced to withdraw.", BAD)
            add(1.8, 125, "Command declares operation failed. Emergency protocols initiated in surrounding sectors.", BAD)

        return events

    def update(self, dt: float):
        """
        Advance the mission timeline.
        dt: time in seconds since last frame.
        """
        if self.finished or not self.events:
            return

        self.timer += dt

        # Reveal events one-by-one as time passes
        while self.visible_events < len(self.events) and self.timer >= self.events[self.visible_events].delay:
            self.timer -= self.events[self.visible_events].delay
            self.visible_events += 1

            if self.visible_events == len(self.events):
                self.finished = True
                break

    @property
    def visible_log(self):
        """Return currently visible events."""
        return self.events[:self.visible_events]


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
