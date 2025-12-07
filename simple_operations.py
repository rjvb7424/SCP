# simple_operations.py

class SimpleOperation:
    def __init__(self, codename, city, country, risk, priority, description):
        self.codename = codename
        self.city = city
        self.country = country
        self.risk = risk
        self.priority = priority
        self.description = description


operations = [
    SimpleOperation(
        "Op BLACK ICE",
        "Lisbon",
        "Portugal",
        "Medium",
        "High",
        "Investigate anomalous activity in the old docks district."
    ),
    SimpleOperation(
        "Op GLASS VEIL",
        "Tokyo",
        "Japan",
        "High",
        "Very High",
        "Suppress public knowledge of a mass hallucination event."
    ),
    SimpleOperation(
        "Op SILENT DAWN",
        "Reykjavík",
        "Iceland",
        "Low",
        "Low",
        "Routine inspection of a dormant anomaly beneath the city."
    ),
]
