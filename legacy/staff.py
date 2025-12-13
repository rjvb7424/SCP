# staff.py
from personnel import Personnel


class Staff:
    """
    Holds all personnel for the site.
    Responsible for:
      - creating initial staff (key positions + randoms)
      - tracking which member is currently selected
    """

    def __init__(self, key_positions=None, num_random=5):
        # key_positions: list of position names that must always be present
        if key_positions is None:
            key_positions = []

        self.key_positions = key_positions
        self._members = []
        self._current_index = 0

        self._create_initial_roster(num_random)

    def _create_initial_roster(self, num_random):
        # Guarantee one member for each key position (if it exists)
        for pos in self.key_positions:
            if pos in Personnel._positions:
                p = Personnel(position=pos)
                p.is_key_position = True
                self._members.append(p)
            else:
                print(f"[StaffRoster] Key position '{pos}' not found in positions.json")

        # Add some extra random staff
        for _ in range(num_random):
            p = Personnel()
            p.is_key_position = False
            self._members.append(p)

    # --- Basic container helpers ---

    def __len__(self):
        return len(self._members)

    def __getitem__(self, index):
        return self._members[index]

    @property
    def members(self):
        return self._members

    @property
    def current_index(self):
        return self._current_index

    @property
    def current(self):
        if not self._members:
            return None
        return self._members[self._current_index]

    def next(self):
        """Select next staff member in the roster."""
        if not self._members:
            return
        self._current_index = (self._current_index + 1) % len(self._members)

    def previous(self):
        """Select previous staff member in the roster."""
        if not self._members:
            return
        self._current_index = (self._current_index - 1) % len(self._members)
