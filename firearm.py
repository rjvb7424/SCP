class Firearm:
    def __init__(self, name, caliber, rounds_per_minute, effective_range, magazine_capacity):
        self.name = name
        self.caliber = caliber
        self.rounds_per_minute = rounds_per_minute
        self.effective_range = effective_range
        self.magazine_capacity = magazine_capacity
        self.current_ammo = magazine_capacity
