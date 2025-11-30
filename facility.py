# facility.py
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class FacilityRoom:
    room_type: str
    row: int
    col: int
    level: int = 1  # future-proofing for upgrades


class Facility:
    """Simple Fallout-Shelter-style 2D facility grid."""

    def __init__(self, rows: int = 3, cols: int = 8):
        self.rows = rows
        self.cols = cols
        # grid[row][col] -> FacilityRoom or None
        self.grid: List[List[Optional[FacilityRoom]]] = [
            [None for _ in range(cols)] for _ in range(rows)
        ]

        # The room types the player can build
        self.room_types = [
            "Command Center",
            "Research Lab",
            "Infirmary",
            "Security Station",
            "Dormitory",
            "Common Room",
        ]

        self._build_initial_layout()

    # --- Setup helpers ---

    def _build_initial_layout(self):
        """Start with a few core rooms in the middle row."""
        mid_row = self.rows // 2
        core_types = ["Command Center", "Research Lab", "Infirmary", "Security Station"]
        for col, rtype in enumerate(core_types):
            if col < self.cols:
                self.grid[mid_row][col] = FacilityRoom(rtype, mid_row, col)

    # --- Grid helpers ---

    def in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_room(self, row: int, col: int) -> Optional[FacilityRoom]:
        if not self.in_bounds(row, col):
            return None
        return self.grid[row][col]

    def build_room(self, row: int, col: int, room_type: str) -> bool:
        """Attempt to build a room. Returns True on success."""
        if not self.in_bounds(row, col):
            return False
        if room_type not in self.room_types:
            return False
        if self.grid[row][col] is not None:
            # already a room here
            return False

        self.grid[row][col] = FacilityRoom(room_type, row, col)
        return True
