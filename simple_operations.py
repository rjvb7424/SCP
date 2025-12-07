# simple_operations.py
import json
import os

# Load country / city data once
COUNTRIES_PATH = os.path.join(os.path.dirname(__file__), "countries.json")

with open(COUNTRIES_PATH, "r", encoding="utf-8") as f:
    COUNTRY_DATA = json.load(f)


def get_city_coords(country_name: str, city_name: str):
    """Look up (lat, lon) for a given city in a given country."""
    try:
        country = COUNTRY_DATA[country_name]
    except KeyError:
        raise ValueError(f"Unknown country in countries.json: {country_name!r}")

    for city in country["cities"]:
        if city["city"] == city_name:
            return float(city["lat"]), float(city["lon"])

    raise ValueError(f"City {city_name!r} not found in {country_name!r} in countries.json")


class SimpleOperation:
    def __init__(self, codename, country, city, risk, priority, description):
        self.codename = codename
        self.country = country
        self.city = city
        self.risk = risk
        self.priority = priority
        self.description = description

        # lat/lon taken from countries.json
        self.lat, self.lon = get_city_coords(country, city)


# A few sample operations
operations = [
    SimpleOperation(
        "Op BLACK ICE",
        "Portugal",
        "Lisbon",
        "Medium",
        "High",
        "Investigate anomalous activity in the old docks district."
    ),
    SimpleOperation(
        "Op GLASS VEIL",
        "Japan",
        "Tokyo",
        "High",
        "Very High",
        "Suppress public knowledge of a mass hallucination event."
    ),
    SimpleOperation(
        "Op SILENT DAWN",
        "United States of America",
        "New York City",
        "Low",
        "Low",
        "Routine inspection of a dormant anomaly beneath a metropolitan subway line."
    ),
]
