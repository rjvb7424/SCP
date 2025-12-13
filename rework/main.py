import math
import random
import heapq
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import pygame

from ui_elements import draw_title_text, draw_header_text, draw_body_text, draw_primary_button, draw_secondary_button, draw_deny_button, get_attribute_color
from ui_elements import TITLE_FONT, FOOTER_FONT

pygame.font.init()

# ==========================
# Utils
# ==========================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def bresenham_line(x0, y0, x1, y1):
    points = []
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy
    return points


# ==========================
# Pathfinding (A*)
# ==========================
def astar(grid, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
    # grid: 1=wall, 0=floor, 2=door (passable)
    w, h = len(grid[0]), len(grid)

    def in_bounds(p):
        return 0 <= p[0] < w and 0 <= p[1] < h

    def passable(p):
        return grid[p[1]][p[0]] != 1

    if start == goal:
        return [start]
    if not in_bounds(goal) or not passable(goal):
        return []

    open_heap = []
    heapq.heappush(open_heap, (0, start))
    came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    gscore = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            break

        x, y = current
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nxt = (nx, ny)
            if not in_bounds(nxt) or not passable(nxt):
                continue
            tentative = gscore[current] + 1
            if nxt not in gscore or tentative < gscore[nxt]:
                gscore[nxt] = tentative
                priority = tentative + manhattan(nxt, goal)
                heapq.heappush(open_heap, (priority, nxt))
                came_from[nxt] = current

    if goal not in came_from:
        return []

    path = []
    cur = goal
    while cur is not None:
        path.append(cur)
        cur = came_from[cur]
    path.reverse()
    return path


# ==========================
# Facility / Building Generation
# ==========================
@dataclass
class Building:
    bid: int
    rect: pygame.Rect  # in grid coords
    door: Tuple[int, int]
    interior_cells: List[Tuple[int, int]]


def _rects_overlap(a: pygame.Rect, b: pygame.Rect, pad: int = 1) -> bool:
    aa = pygame.Rect(a.x - pad, a.y - pad, a.w + pad * 2, a.h + pad * 2)
    bb = pygame.Rect(b.x - pad, b.y - pad, b.w + pad * 2, b.h + pad * 2)
    return aa.colliderect(bb)


def _dig_corridor(grid, a: Tuple[int, int], b: Tuple[int, int]):
    x, y = a
    tx, ty = b
    w, h = len(grid[0]), len(grid)
    for _ in range(2000):
        grid[y][x] = 0
        if (x, y) == (tx, ty):
            break
        if random.random() < 0.5:
            if x < tx:
                x += 1
            elif x > tx:
                x -= 1
        else:
            if y < ty:
                y += 1
            elif y > ty:
                y -= 1
        x = clamp(x, 1, w - 2)
        y = clamp(y, 1, h - 2)


def generate_facility(map_w: int, map_h: int, num_buildings: int = 6) -> Tuple[List[List[int]], List[List[int]], List[Building]]:
    # grid: 0 floor (outdoor), 1 wall, 2 door (passable)
    grid = [[0 for _ in range(map_w)] for _ in range(map_h)]
    building_id = [[-1 for _ in range(map_w)] for _ in range(map_h)]
    buildings: List[Building] = []

    # boundary
    for x in range(map_w):
        grid[0][x] = 1
        grid[map_h - 1][x] = 1
    for y in range(map_h):
        grid[y][0] = 1
        grid[y][map_w - 1] = 1

    # scatter some outdoor cover/obstacles
    for _ in range(10):
        rw = random.randint(2, 5)
        rh = random.randint(2, 4)
        cx = random.randint(2, map_w - rw - 3)
        cy = random.randint(2, map_h - rh - 3)
        for yy in range(cy, cy + rh):
            for xx in range(cx, cx + rw):
                if random.random() < 0.55:
                    grid[yy][xx] = 1

    # buildings
    placed_rects: List[pygame.Rect] = []
    attempts = 0
    bid = 0
    while bid < num_buildings and attempts < 800:
        attempts += 1
        bw = random.randint(9, 15)
        bh = random.randint(7, 12)
        bx = random.randint(2, map_w - bw - 3)
        by = random.randint(2, map_h - bh - 3)
        rect = pygame.Rect(bx, by, bw, bh)

        if any(_rects_overlap(rect, r, pad=2) for r in placed_rects):
            continue

        # build perimeter walls + interior floor
        interior_cells = []
        for y in range(by, by + bh):
            for x in range(bx, bx + bw):
                on_edge = (x == bx or y == by or x == bx + bw - 1 or y == by + bh - 1)
                if on_edge:
                    grid[y][x] = 1
                else:
                    grid[y][x] = 0
                    building_id[y][x] = bid
                    interior_cells.append((x, y))

        # internal partition(s)
        if bw >= 12 and random.random() < 0.9:
            px = bx + random.randint(3, bw - 4)
            for y in range(by + 1, by + bh - 1):
                grid[y][px] = 1
            # doorway in partition
            dy = by + random.randint(2, bh - 3)
            grid[dy][px] = 0

        if bh >= 10 and random.random() < 0.8:
            py = by + random.randint(3, bh - 4)
            for x in range(bx + 1, bx + bw - 1):
                grid[py][x] = 1
            dx = bx + random.randint(2, bw - 3)
            grid[py][dx] = 0

        # add a door on perimeter
        side = random.choice(["N", "S", "W", "E"])
        if side == "N":
            door = (bx + random.randint(2, bw - 3), by)
            outside = (door[0], door[1] - 1)
        elif side == "S":
            door = (bx + random.randint(2, bw - 3), by + bh - 1)
            outside = (door[0], door[1] + 1)
        elif side == "W":
            door = (bx, by + random.randint(2, bh - 3))
            outside = (door[0] - 1, door[1])
        else:
            door = (bx + bw - 1, by + random.randint(2, bh - 3))
            outside = (door[0] + 1, door[1])

        # door tile passable
        grid[door[1]][door[0]] = 2

        # ensure door connects to outdoors (dig 1-3 tiles)
        if 0 <= outside[0] < map_w and 0 <= outside[1] < map_h:
            _dig_corridor(grid, outside, (clamp(outside[0] + random.randint(-2, 2), 1, map_w - 2),
                                          clamp(outside[1] + random.randint(-2, 2), 1, map_h - 2)))

        buildings.append(Building(bid=bid, rect=rect, door=door, interior_cells=interior_cells))
        placed_rects.append(rect)
        bid += 1

    return grid, building_id, buildings


def random_floor_cell(grid, avoid: Optional[List[Tuple[int, int]]] = None, tries=5000) -> Tuple[int, int]:
    avoid = avoid or []
    h = len(grid)
    w = len(grid[0])
    for _ in range(tries):
        x = random.randint(1, w - 2)
        y = random.randint(1, h - 2)
        if grid[y][x] != 1 and all(manhattan((x, y), a) > 6 for a in avoid):
            return (x, y)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if grid[y][x] != 1:
                return (x, y)
    return (1, 1)


# ==========================
# Simulation Data
# ==========================
ATTR_KEYS = ["speed", "perception", "tactics", "aim", "endurance", "courage", "medical", "containment"]

ROLE_TEMPLATES = {
    "Leader":   {"speed": 10, "perception": 12, "tactics": 16, "aim": 12, "endurance": 12, "courage": 16, "medical": 6, "containment": 12},
    "Scout":    {"speed": 16, "perception": 17, "tactics": 10, "aim": 10, "endurance": 10, "courage": 12, "medical": 5, "containment": 10},
    "Medic":    {"speed": 10, "perception": 12, "tactics": 10, "aim": 8,  "endurance": 12, "courage": 12, "medical": 18, "containment": 10},
    "Breacher": {"speed": 11, "perception": 10, "tactics": 12, "aim": 12, "endurance": 17, "courage": 13, "medical": 6, "containment": 14},
    "Sniper":   {"speed": 10, "perception": 16, "tactics": 10, "aim": 18, "endurance": 9,  "courage": 11, "medical": 4, "containment": 9},
    "Tech":     {"speed": 9,  "perception": 11, "tactics": 14, "aim": 10, "endurance": 10, "courage": 10, "medical": 8, "containment": 16},
}


def jitter_base(v, spread=4):
    return clamp(v + random.randint(-spread, spread), 0, 20)


@dataclass
class DamageOverTime:
    dps: float
    duration: float


@dataclass
class Tracer:
    x0: float
    y0: float
    x1: float
    y1: float
    ttl: float
    color: Tuple[int, int, int]


@dataclass
class Weapon:
    name: str
    damage_min: float
    damage_max: float
    range_tiles: int
    fire_rate: float      # shots per second
    accuracy: float       # base 0..1
    mag_size: int
    reload_time: float


WEAPONS = {
    "Rifle":   Weapon("Rifle", damage_min=10, damage_max=16, range_tiles=9,  fire_rate=3.0, accuracy=0.62, mag_size=30, reload_time=1.9),
    "SMG":     Weapon("SMG",   damage_min=7,  damage_max=12, range_tiles=7,  fire_rate=5.2, accuracy=0.50, mag_size=28, reload_time=1.7),
    "Shotgun": Weapon("Shotgun", damage_min=14, damage_max=24, range_tiles=4, fire_rate=1.4, accuracy=0.56, mag_size=6, reload_time=2.3),
    "Sniper":  Weapon("Sniper", damage_min=18, damage_max=32, range_tiles=13, fire_rate=0.9, accuracy=0.78, mag_size=5, reload_time=2.5),
    "Carbine": Weapon("Carbine", damage_min=9, damage_max=14, range_tiles=8,  fire_rate=3.6, accuracy=0.58, mag_size=25, reload_time=1.8),
    "Pistol":  Weapon("Pistol", damage_min=6, damage_max=10, range_tiles=6,  fire_rate=2.2, accuracy=0.46, mag_size=12, reload_time=1.5),
}

ROLE_WEAPON = {
    "Leader": "Rifle",
    "Scout": "SMG",
    "Medic": "Pistol",
    "Breacher": "Shotgun",
    "Sniper": "Sniper",
    "Tech": "Carbine",
}


class EventLog:
    def __init__(self, max_lines=400):
        self.lines: List[str] = []
        self.max_lines = max_lines
        self.scroll = 0

    def add(self, msg: str):
        self.lines.append(msg)
        if len(self.lines) > self.max_lines:
            self.lines = self.lines[-self.max_lines:]
        self.scroll = 0

    def scroll_by(self, dy: int):
        self.scroll = clamp(self.scroll + dy, 0, max(0, len(self.lines) - 1))


class Entity:
    def __init__(self, gx: int, gy: int):
        self.gx = gx
        self.gy = gy
        self.px = float(gx)
        self.py = float(gy)
        self.path: List[Tuple[int, int]] = []
        self.manual_target: Optional[Tuple[int, int]] = None

    def set_grid_pos(self, gx, gy):
        self.gx, self.gy = gx, gy
        self.px, self.py = float(gx), float(gy)


# ==========================
# Combat helpers
# ==========================
def los_clear(grid, a: Tuple[int, int], b: Tuple[int, int]) -> bool:
    for (x, y) in bresenham_line(a[0], a[1], b[0], b[1]):
        if (x, y) == a or (x, y) == b:
            continue
        if grid[y][x] == 1:
            return False
    return True


def target_has_cover(grid, target: Tuple[int, int]) -> float:
    # simple cover heuristic: walls adjacent -> some cover
    x, y = target
    h = len(grid)
    w = len(grid[0])
    cover = 0
    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
        if 0 <= nx < w and 0 <= ny < h and grid[ny][nx] == 1:
            cover += 1
    # 0..4 -> 0..0.22ish reduction later
    return min(0.22, cover * 0.06)


# ==========================
# Operative
# ==========================
class Operative(Entity):
    def __init__(self, name: str, role: str, gx: int, gy: int, attrs: Dict[str, int]):
        super().__init__(gx, gy)
        self.name = name
        self.role = role
        self.attrs = attrs

        self.hp_max = 60 + int(self.attrs["endurance"] * 4)
        self.hp = float(self.hp_max)
        self.alive = True

        self.injured = False
        self.bleeds: List[DamageOverTime] = []
        self.panic = 0.0  # 0..100
        self.fleeing = False
        self.incapacitated = False

        self.state = "inserting"  # search/chase/capture/extract/flee/manual
        self.cooldown = 0.0

        self.kit_integrity = 100.0  # affects containment odds
        self.last_seen_anomaly: Optional[Tuple[int, int]] = None
        self.detected_anomaly = False

        # weapon
        self.weapon = WEAPONS[ROLE_WEAPON.get(role, "Rifle")]
        self.ammo = self.weapon.mag_size
        self.reloading = 0.0

        # fire control (separate from other cooldown)
        self.fire_cd = 0.0

    def speed_tiles_per_sec(self):
        base = 1.4 + (self.attrs["speed"] / 20.0) * 2.0
        if self.injured:
            base *= 0.65
        if self.fleeing:
            base *= 1.15
        if self.incapacitated:
            base *= 0.0
        return base

    def perception_radius(self):
        return 3 + int(self.attrs["perception"] / 3)  # 3..9

    def aim_quality(self):
        return self.attrs["aim"] / 20.0

    def courage_resist(self):
        return self.attrs["courage"] / 20.0

    def tactics_bonus(self):
        return self.attrs["tactics"] / 20.0

    def containment_skill(self):
        return (self.attrs["containment"] / 20.0) * (0.55 + 0.45 * (self.kit_integrity / 100.0))

    def medical_skill(self):
        return self.attrs["medical"] / 20.0

    def apply_damage(self, sim, amount: float, cause: str = "unknown"):
        if not self.alive or self.incapacitated:
            return

        self.hp -= amount
        sim.log.add(f"{self.name} took {amount:.0f} damage ({cause}).")

        if amount >= 10 and random.random() < 0.25:
            self.bleeds.append(DamageOverTime(dps=1.2 + random.random() * 1.2, duration=8 + random.random() * 6))
            sim.log.add(f"{self.name} is bleeding!")

        if self.hp <= self.hp_max * 0.45 and not self.injured and self.hp > 0:
            self.injured = True
            sim.log.add(f"{self.name} is injured (movement & actions slower).")

        panic_gain = amount * (1.2 - self.courage_resist())
        self.panic = clamp(self.panic + panic_gain, 0, 100)

        if not self.fleeing and self.panic > 65 and random.random() < (0.15 + (self.panic - 65) / 100.0) * (1.0 - self.courage_resist()):
            self.fleeing = True
            self.state = "flee"
            sim.log.add(f"{self.name} panics and flees!")

        if self.hp <= 0:
            self.alive = False
            self.incapacitated = True
            self.state = "dead"
            sim.log.add(f"{self.name} is KIA.")

    def update_bleeding(self, sim, dt):
        if not self.bleeds or not self.alive or self.incapacitated:
            return
        remaining = []
        for b in self.bleeds:
            self.hp -= b.dps * dt
            b.duration -= dt
            if b.duration > 0:
                remaining.append(b)
        self.bleeds = remaining
        if self.hp <= 0 and self.alive:
            self.alive = False
            self.incapacitated = True
            self.state = "dead"
            sim.log.add(f"{self.name} bled out.")

    def heal_nearby(self, sim, dt):
        if self.medical_skill() < 0.25 or not self.alive or self.incapacitated:
            return
        if self.state in ("chase", "capture") and random.random() < 0.6:
            return
        if self.panic > 70:
            return

        for other in sim.operatives:
            if other is self or not other.alive:
                continue
            if manhattan((self.gx, self.gy), (other.gx, other.gy)) <= 1:
                if other.hp < other.hp_max and (other.injured or other.bleeds):
                    heal_rate = 2.0 + 8.0 * self.medical_skill()
                    other.hp = min(other.hp_max, other.hp + heal_rate * dt)
                    if other.bleeds and random.random() < 0.2 * self.medical_skill():
                        other.bleeds.pop(0)
                        sim.log.add(f"{self.name} stabilizes {other.name}'s bleeding.")
                    if other.hp > other.hp_max * 0.55:
                        other.injured = False
                    if random.random() < 0.08:
                        sim.log.add(f"{self.name} treats {other.name}.")
                break

    def can_see(self, sim, target: Tuple[int, int]) -> bool:
        if manhattan((self.gx, self.gy), target) > self.perception_radius():
            return False
        return los_clear(sim.grid, (self.gx, self.gy), target)

    def choose_explore_target(self, sim) -> Optional[Tuple[int, int]]:
        # Prefer unexplored building interiors first (facility sweep vibe)
        candidates = []

        # If we haven't entered many buildings, bias towards building cells
        for _ in range(160):
            if random.random() < 0.75 and sim.buildings:
                b = random.choice(sim.buildings)
                if not b.interior_cells:
                    continue
                x, y = random.choice(b.interior_cells)
            else:
                x = random.randint(1, sim.map_w - 2)
                y = random.randint(1, sim.map_h - 2)

            if sim.grid[y][x] == 1:
                continue

            score = 0.0
            score += 2.2 if not sim.visited[y][x] else 0.0

            # frontier preference
            unknown = 0
            for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if 0 <= nx < sim.map_w and 0 <= ny < sim.map_h and not sim.revealed[ny][nx]:
                    unknown += 1
            score += unknown * 0.85

            # building bias (sweep)
            if sim.building_id[y][x] != -1:
                score += 1.2

            score -= manhattan((self.gx, self.gy), (x, y)) * 0.06
            crowd = sum(1 for op in sim.operatives if op.alive and manhattan((x, y), (op.gx, op.gy)) <= 2)
            score -= crowd * 0.6

            candidates.append((score, (x, y)))

        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1]

    def decide(self, sim):
        if not self.alive or self.incapacitated:
            return

        if sim.retreat_order or self.fleeing or sim.phase == "extraction":
            self.state = "extract"
            self.manual_target = sim.extraction
            return

        if self.manual_target is not None:
            self.state = "manual"
            return

        if sim.team_last_known_anomaly is not None:
            # flanking a bit if tactics good
            tx, ty = sim.team_last_known_anomaly
            if random.random() < 0.35 + 0.35 * self.tactics_bonus():
                ox = random.randint(-2, 2)
                oy = random.randint(-2, 2)
                tgt = (clamp(tx + ox, 1, sim.map_w - 2), clamp(ty + oy, 1, sim.map_h - 2))
                if sim.is_passable(tgt):
                    self.state = "chase"
                    self.manual_target = tgt
                    return
            self.state = "chase"
            self.manual_target = sim.team_last_known_anomaly
            return

        self.state = "search"
        tgt = self.choose_explore_target(sim)
        if tgt:
            self.manual_target = tgt

    def try_reload(self, sim):
        if self.reloading <= 0 and self.ammo <= 0:
            self.reloading = self.weapon.reload_time
            sim.log.add(f"{self.name} reloads ({self.weapon.name}).")

    def try_shoot_anomaly(self, sim, dt):
        if not self.alive or self.incapacitated:
            return
        if not sim.anomaly or sim.anomaly.contained:
            return
        if self.reloading > 0:
            return

        ax, ay = sim.anomaly.gx, sim.anomaly.gy
        if manhattan((self.gx, self.gy), (ax, ay)) > self.weapon.range_tiles:
            return
        if not los_clear(sim.grid, (self.gx, self.gy), (ax, ay)):
            return

        # cadence
        if self.fire_cd > 0:
            return

        self.try_reload(sim)
        if self.reloading > 0:
            return
        if self.ammo <= 0:
            return

        # fire
        self.fire_cd = 1.0 / max(0.2, self.weapon.fire_rate)
        self.ammo -= 1

        # visual tracer
        sim.tracers.append(Tracer(
            x0=self.px + 0.5, y0=self.py + 0.5,
            x1=sim.anomaly.px + 0.5, y1=sim.anomaly.py + 0.5,
            ttl=0.10, color=(230, 220, 120)
        ))

        # hit chance
        d = max(1, manhattan((self.gx, self.gy), (ax, ay)))
        falloff = clamp(1.0 - (d / (self.weapon.range_tiles + 2)) * 0.35, 0.55, 1.0)
        cover = target_has_cover(sim.grid, (ax, ay))
        base = self.weapon.accuracy * (0.55 + 0.45 * self.aim_quality())
        if self.injured:
            base *= 0.78
        # anomaly stealth makes it harder to hit a bit (especially at range)
        stealth_pen = (sim.anomaly.stealth / 20.0) * (0.06 + 0.02 * d)
        chance = clamp(base * falloff - cover - stealth_pen, 0.05, 0.88)

        if random.random() < chance:
            dmg = random.uniform(self.weapon.damage_min, self.weapon.damage_max)
            # tactical bonus slightly increases effectiveness
            dmg *= (0.92 + 0.16 * self.tactics_bonus())
            sim.anomaly.apply_damage(sim, dmg, cause=f"{self.weapon.name} hit by {self.name}")
            # gunfire pressure reduces stability (easier containment)
            sim.anomaly.stability = clamp(sim.anomaly.stability - (3.0 + dmg * 0.15), 0, 100)
            # aggro rises
            sim.anomaly.aggro = clamp(sim.anomaly.aggro + 5.0, 0, 100)
        else:
            # near miss raises aggro a bit
            sim.anomaly.aggro = clamp(sim.anomaly.aggro + 1.5, 0, 100)

    def attempt_capture(self, sim):
        if not self.alive or self.incapacitated:
            return False
        if sim.anomaly is None or sim.anomaly.contained:
            return False
        if manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) > 1:
            return False

        stability_factor = 1.0 - (sim.anomaly.stability / 100.0)
        skill = self.containment_skill()

        adjacent = sum(
            1 for op in sim.operatives
            if op.alive and not op.incapacitated and manhattan((op.gx, op.gy), (sim.anomaly.gx, sim.anomaly.gy)) <= 1
        )
        team_factor = 1.0 + (adjacent - 1) * 0.35

        # immobilized anomaly is easier
        imm = 1.25 if sim.anomaly.immobilized else 1.0

        res = sim.anomaly.resilience / 20.0
        base = 0.05 + 0.35 * skill
        chance = base * (0.35 + 0.65 * stability_factor) * team_factor * imm * (1.0 - 0.45 * res)
        chance = clamp(chance, 0.03, 0.82)

        self.kit_integrity = clamp(self.kit_integrity - (6 + random.random() * 8), 0, 100)
        sim.anomaly.aggro = clamp(sim.anomaly.aggro + 10, 0, 100)

        if random.random() < chance:
            sim.anomaly.contained = True
            sim.phase = "extraction"
            sim.log.add(f"CONTAINMENT SUCCESS by {self.name}! Begin extraction.")
            return True
        else:
            sim.log.add(f"{self.name} containment attempt failed.")
            if random.random() < 0.20 + 0.35 * (sim.anomaly.threat / 20.0):
                self.apply_damage(sim, 8 + random.random() * 16, cause="containment backlash")
            return False

    def update(self, sim, dt):
        if not self.alive:
            return

        self.cooldown = max(0.0, self.cooldown - dt)
        self.fire_cd = max(0.0, self.fire_cd - dt)

        if self.reloading > 0:
            self.reloading -= dt
            if self.reloading <= 0:
                self.ammo = self.weapon.mag_size
                sim.log.add(f"{self.name} finished reloading.")

        # panic recovery if not in immediate contact
        near_threat = False
        if sim.anomaly and not sim.anomaly.contained:
            near_threat = manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) <= 7
        if not near_threat:
            self.panic = max(0.0, self.panic - dt * (8.0 + 12.0 * self.courage_resist()))

        self.update_bleeding(sim, dt)
        if not self.alive:
            return

        self.heal_nearby(sim, dt)

        # detect anomaly
        self.detected_anomaly = False
        if sim.anomaly and not sim.anomaly.contained:
            if self.can_see(sim, (sim.anomaly.gx, sim.anomaly.gy)):
                self.detected_anomaly = True
                self.last_seen_anomaly = (sim.anomaly.gx, sim.anomaly.gy)
                sim.team_last_known_anomaly = (sim.anomaly.gx, sim.anomaly.gy)

        # shooting if possible (this is the “match view” action!)
        if sim.anomaly and not sim.anomaly.contained:
            self.try_shoot_anomaly(sim, dt)

        # containment attempt if adjacent (cadenced)
        if sim.anomaly and not sim.anomaly.contained and manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) <= 1:
            if self.cooldown <= 0:
                self.cooldown = 0.8 + random.random() * 0.7
                self.attempt_capture(sim)

        # planning / path
        if self.cooldown <= 0 and (not self.path or random.random() < 0.03):
            self.decide(sim)
            if self.manual_target is not None:
                p = astar(sim.grid, (self.gx, self.gy), self.manual_target)
                if p:
                    self.path = p[1:]
                else:
                    self.manual_target = None
                    self.path = []

        # movement
        spd = self.speed_tiles_per_sec()
        if spd > 0 and self.path:
            tx, ty = self.path[0]
            vx = tx - self.px
            vy = ty - self.py
            d = math.hypot(vx, vy)
            if d < 1e-6:
                self.px, self.py = float(tx), float(ty)
                self.gx, self.gy = tx, ty
                self.path.pop(0)
                sim.visited[self.gy][self.gx] = True
                if self.manual_target == (self.gx, self.gy):
                    self.manual_target = None
            else:
                step = spd * dt
                if step >= d:
                    self.px, self.py = float(tx), float(ty)
                    self.gx, self.gy = tx, ty
                    self.path.pop(0)
                    sim.visited[self.gy][self.gx] = True
                    if self.manual_target == (self.gx, self.gy):
                        self.manual_target = None
                else:
                    self.px += (vx / d) * step
                    self.py += (vy / d) * step

        self.try_reload(sim)


# ==========================
# Anomaly
# ==========================
class Anomaly(Entity):
    def __init__(self, code: str, gx: int, gy: int, threat: int, speed: int, stealth: int, aggression: int, resilience: int):
        super().__init__(gx, gy)
        self.code = code
        self.threat = threat
        self.speed = speed
        self.stealth = stealth
        self.aggression = aggression
        self.resilience = resilience

        self.contained = False
        self.stability = 100.0
        self.aggro = float(aggression) * 3.0
        self.escape_timer = 0.0

        self.hp_max = 80 + threat * 6 + resilience * 5
        self.hp = float(self.hp_max)
        self.immobilized = False

        self.attack_cd = 0.0

    def speed_tiles_per_sec(self):
        base = 1.6 + (self.speed / 20.0) * 2.2
        if self.immobilized:
            base *= 0.15
        # low stability can make it “erratic” (small speed boost)
        base *= (0.95 + (1.0 - self.stability / 100.0) * 0.25)
        return base

    def apply_damage(self, sim, amount: float, cause: str):
        if self.contained:
            return
        self.hp -= amount
        sim.log.add(f"{self.code} took {amount:.0f} damage ({cause}).")
        if self.hp <= self.hp_max * 0.22 and not self.immobilized:
            self.immobilized = True
            sim.log.add(f"{self.code} destabilizes and slows (immobilized).")
        if self.hp <= 0:
            self.hp = 0
            self.immobilized = True
            sim.log.add(f"{self.code} manifestation collapses. Containment is now much easier.")

    def choose_target(self, sim) -> Optional[Operative]:
        # prefer closest visible operative
        best = None
        best_d = 9999
        for op in sim.operatives:
            if not op.alive or op.incapacitated:
                continue
            d = manhattan((self.gx, self.gy), (op.gx, op.gy))
            if d < best_d:
                best_d = d
                best = op
        return best

    def try_attack(self, sim, dt):
        if self.contained:
            return
        if self.attack_cd > 0:
            return

        target = self.choose_target(sim)
        if not target:
            return

        d = manhattan((self.gx, self.gy), (target.gx, target.gy))
        can_see = los_clear(sim.grid, (self.gx, self.gy), (target.gx, target.gy))

        # aggression gate
        aggro_gate = 0.35 + (self.aggro / 100.0) * 0.55
        if random.random() > aggro_gate:
            return

        # melee if close
        if d <= 1:
            lethality = 9 + (self.threat / 20.0) * 20
            lethality *= (0.85 + 0.15 * (self.stability / 100.0))
            target.apply_damage(sim, lethality + random.random() * 6, cause=f"{self.code} melee")
            self.attack_cd = 0.9 + random.random() * 0.6
            return

        # ranged if line of sight + within range
        ranged_range = 6 + int(self.threat / 4) + int(self.aggression / 5)  # ~6..12
        if can_see and d <= ranged_range:
            # tracer
            sim.tracers.append(Tracer(
                x0=self.px + 0.5, y0=self.py + 0.5,
                x1=target.px + 0.5, y1=target.py + 0.5,
                ttl=0.10, color=(220, 70, 70)
            ))
            # hit chance
            cover = target_has_cover(sim.grid, (target.gx, target.gy))
            base = 0.35 + (self.threat / 20.0) * 0.35
            base -= cover
            # target courage reduces effective hit a bit (keeps composure)
            base *= (0.85 + 0.15 * (1.0 - target.courage_resist()))
            base = clamp(base, 0.08, 0.75)
            if random.random() < base:
                dmg = 7 + (self.threat / 20.0) * 16 + random.random() * 6
                target.apply_damage(sim, dmg, cause=f"{self.code} ranged")
            else:
                # near miss adds panic
                target.panic = clamp(target.panic + 6 * (1.1 - target.courage_resist()), 0, 100)
            self.attack_cd = 1.1 + random.random() * 0.7

    def update(self, sim, dt):
        if self.contained:
            return

        self.attack_cd = max(0.0, self.attack_cd - dt)

        # seen by team?
        visible_by = []
        for op in sim.operatives:
            if not op.alive:
                continue
            if manhattan((op.gx, op.gy), (self.gx, self.gy)) <= op.perception_radius() and op.can_see(sim, (self.gx, self.gy)):
                # stealth makes it easier to “lose”
                if random.random() < (0.90 - (self.stealth / 20.0) * 0.20):
                    visible_by.append(op)

        if not visible_by:
            self.stability = clamp(self.stability + dt * (2.0 + 5.0 * (self.resilience / 20.0)), 0, 100)
            self.escape_timer += dt
        else:
            self.escape_timer = 0.0

        # fight back if aggressive
        self.try_attack(sim, dt)

        # movement: if seen, evade; else roam within facility
        spd = self.speed_tiles_per_sec()
        if not self.path or random.random() < 0.06:
            if visible_by:
                ax = sum(op.gx for op in visible_by) / len(visible_by)
                ay = sum(op.gy for op in visible_by) / len(visible_by)
                dx = self.gx - ax
                dy = self.gy - ay
                mag = math.hypot(dx, dy) + 1e-6
                dx /= mag
                dy /= mag
                step = 9 + int(self.stealth / 2)
                tx = int(clamp(self.gx + dx * step, 1, sim.map_w - 2))
                ty = int(clamp(self.gy + dy * step, 1, sim.map_h - 2))
                tx = clamp(tx + random.randint(-3, 3), 1, sim.map_w - 2)
                ty = clamp(ty + random.randint(-3, 3), 1, sim.map_h - 2)
                target = (tx, ty)
                if not sim.is_passable(target):
                    target = random_floor_cell(sim.grid, avoid=[(op.gx, op.gy) for op in sim.operatives if op.alive])
            else:
                # roam: bias into buildings to feel like "inside containment zone"
                if sim.buildings and random.random() < 0.65:
                    b = random.choice(sim.buildings)
                    target = random.choice(b.interior_cells) if b.interior_cells else random_floor_cell(sim.grid)
                else:
                    target = random_floor_cell(sim.grid)

            p = astar(sim.grid, (self.gx, self.gy), target)
            self.path = p[1:] if p else []

        if spd > 0 and self.path:
            tx, ty = self.path[0]
            vx = tx - self.px
            vy = ty - self.py
            d = math.hypot(vx, vy)
            if d < 1e-6:
                self.px, self.py = float(tx), float(ty)
                self.gx, self.gy = tx, ty
                self.path.pop(0)
            else:
                step = spd * dt
                if step >= d:
                    self.px, self.py = float(tx), float(ty)
                    self.gx, self.gy = tx, ty
                    self.path.pop(0)
                else:
                    self.px += (vx / d) * step
                    self.py += (vy / d) * step


# ==========================
# Operation Simulation
# ==========================
class OperationSim:
    def __init__(self, map_w=52, map_h=34, tile=20, screen=None):
        self.map_w = map_w
        self.map_h = map_h
        self.tile = tile
        self.panel_w = 380

        self.screen_w = self.map_w * self.tile + self.panel_w
        self.screen_h = self.map_h * self.tile

        self.screen = screen or pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Operation Simulation - Facility Containment")

        self.clock = pygame.time.Clock()
        self.running = True

        self.debug_show_anomaly = False
        self.fog_enabled = True

        self.log = EventLog()
        self.selected: Optional[Operative] = None

        self.paused = False
        self.retreat_order = False

        self.phase = "operation"  # operation/extraction/failure/success
        self.elapsed = 0.0
        self.deadline = 480.0

        # world
        self.grid: List[List[int]] = []
        self.building_id: List[List[int]] = []
        self.buildings: List[Building] = []
        self.revealed: List[List[bool]] = []
        self.visited: List[List[bool]] = []
        self.entry = (2, 2)
        self.extraction = (2, 2)

        self.operatives: List[Operative] = []
        self.anomaly: Optional[Anomaly] = None

        self.team_last_known_anomaly: Optional[Tuple[int, int]] = None

        # FX
        self.tracers: List[Tracer] = []

        # UI button rects
        self.btn_pause = pygame.Rect(0, 0, 0, 0)
        self.btn_retreat = pygame.Rect(0, 0, 0, 0)
        self.btn_new = pygame.Rect(0, 0, 0, 0)
        self.btn_fog = pygame.Rect(0, 0, 0, 0)
        self.btn_debug = pygame.Rect(0, 0, 0, 0)

        self.reset_operation()

    def is_passable(self, cell: Tuple[int, int]) -> bool:
        x, y = cell
        return 0 <= x < self.map_w and 0 <= y < self.map_h and self.grid[y][x] != 1

    def reset_operation(self):
        self.elapsed = 0.0
        self.phase = "operation"
        self.paused = False
        self.retreat_order = False
        self.team_last_known_anomaly = None
        self.tracers = []

        self.grid, self.building_id, self.buildings = generate_facility(self.map_w, self.map_h, num_buildings=6)

        # entry/extraction points (outdoor)
        self.entry = (2, self.map_h // 2)
        self.extraction = (self.map_w - 3, self.map_h // 2)
        self.grid[self.entry[1]][self.entry[0]] = 0
        self.grid[self.extraction[1]][self.extraction[0]] = 0

        # ensure a corridor-ish passable strip between entry & extraction
        if not astar(self.grid, self.entry, self.extraction):
            _dig_corridor(self.grid, self.entry, self.extraction)

        self.revealed = [[False for _ in range(self.map_w)] for _ in range(self.map_h)]
        self.visited = [[False for _ in range(self.map_w)] for _ in range(self.map_h)]

        self.log = EventLog()
        self.log.add("New operation initialized.")
        self.log.add("Objective: contain the anomaly and extract survivors.")
        self.log.add("Facility: multiple structures detected. Sweep & contain.")

        self.operatives = self.build_team()
        self.selected = self.operatives[0] if self.operatives else None

        # spawn anomaly: preferably inside a random building
        if self.buildings:
            b = random.choice(self.buildings)
            spawn = random.choice(b.interior_cells) if b.interior_cells else random_floor_cell(self.grid, avoid=[self.entry, self.extraction])
        else:
            spawn = random_floor_cell(self.grid, avoid=[self.entry, self.extraction])

        self.anomaly = self.build_anomaly(spawn)

        self.log.add(f"Anomaly registered: {self.anomaly.code}.")
        self.log.add("Rules of engagement: survive, stabilize, contain (lethal force may not fully stop it).")

        self.update_fog()

    def build_team(self) -> List[Operative]:
        names = ["Vega", "Kline", "Mori", "Ash", "Rook", "Silva"]
        roles = ["Leader", "Scout", "Medic", "Breacher", "Sniper", "Tech"]
        team = []

        spawn_cells = []
        for _ in range(80):
            c = random_floor_cell(self.grid, avoid=[self.extraction])
            if manhattan(c, self.entry) <= 5:
                spawn_cells.append(c)
        if not spawn_cells:
            spawn_cells = [self.entry]

        for i, role in enumerate(roles):
            base = ROLE_TEMPLATES[role]
            attrs = {k: jitter_base(base[k], spread=4) for k in ATTR_KEYS}
            gx, gy = random.choice(spawn_cells)
            op = Operative(names[i % len(names)], role, gx, gy, attrs)
            team.append(op)

        self.log.add("Operatives inserted: " + ", ".join([f"{op.name} ({op.role}/{op.weapon.name})" for op in team]) + ".")
        return team

    def build_anomaly(self, spawn: Tuple[int, int]) -> Anomaly:
        codes = ["SCP-███", "SCP-Δ13", "SCP-2470", "SCP-Ω9", "SCP-██-K"]
        code = random.choice(codes)

        threat = random.randint(8, 18)
        speed = random.randint(8, 18)
        stealth = random.randint(6, 18)
        aggression = random.randint(8, 18)
        resilience = random.randint(8, 18)

        return Anomaly(code, spawn[0], spawn[1], threat, speed, stealth, aggression, resilience)

    def update_fog(self):
        if not self.fog_enabled:
            for y in range(self.map_h):
                for x in range(self.map_w):
                    self.revealed[y][x] = True
            return

        for op in self.operatives:
            if not op.alive:
                continue
            r = op.perception_radius()
            for yy in range(op.gy - r, op.gy + r + 1):
                for xx in range(op.gx - r, op.gx + r + 1):
                    if 0 <= xx < self.map_w and 0 <= yy < self.map_h:
                        if manhattan((op.gx, op.gy), (xx, yy)) <= r:
                            if los_clear(self.grid, (op.gx, op.gy), (xx, yy)):
                                self.revealed[yy][xx] = True

    def any_alive(self) -> bool:
        return any(op.alive for op in self.operatives)

    def update_phase_outcomes(self):
        if self.phase in ("success", "failure"):
            return

        if self.elapsed >= self.deadline:
            self.phase = "failure"
            self.log.add("OPERATION FAILED: Time limit exceeded. Anomaly activity lost.")
            return

        if self.anomaly and not self.anomaly.contained:
            at_edge = self.anomaly.gx <= 1 or self.anomaly.gx >= self.map_w - 2 or self.anomaly.gy <= 1 or self.anomaly.gy >= self.map_h - 2
            if at_edge and self.anomaly.escape_timer > 12:
                self.phase = "failure"
                self.log.add("OPERATION FAILED: Anomaly escaped containment zone.")
                return

        if not self.any_alive():
            self.phase = "failure"
            self.log.add("OPERATION FAILED: All operatives lost.")
            return

        if self.anomaly and self.anomaly.contained:
            survivors = [op for op in self.operatives if op.alive]
            if survivors and all(manhattan((op.gx, op.gy), self.extraction) <= 3 for op in survivors):
                self.phase = "success"
                self.log.add("MISSION SUCCESS: Survivors extracted with contained anomaly.")
                return

    def handle_click_map(self, mx, my, button):
        map_rect = pygame.Rect(0, 0, self.map_w * self.tile, self.map_h * self.tile)
        if not map_rect.collidepoint(mx, my):
            return

        gx = mx // self.tile
        gy = my // self.tile

        if button == 1:
            for op in self.operatives:
                if not op.alive:
                    continue
                if (op.gx, op.gy) == (gx, gy):
                    self.selected = op
                    self.log.add(f"Selected: {op.name} ({op.role}/{op.weapon.name}).")
                    return

        if button == 3 and self.selected and self.selected.alive and self.is_passable((gx, gy)):
            self.selected.manual_target = (gx, gy)
            self.selected.path = astar(self.grid, (self.selected.gx, self.selected.gy), (gx, gy))[1:]
            self.log.add(f"{self.selected.name} manual move -> ({gx}, {gy}).")

    def handle_buttons(self, mx, my):
        if self.btn_pause.collidepoint(mx, my):
            self.paused = not self.paused
            self.log.add("Paused." if self.paused else "Resumed.")
        elif self.btn_retreat.collidepoint(mx, my):
            self.retreat_order = True
            self.phase = "extraction"
            self.log.add("RETREAT ORDER: All operatives extract immediately!")
        elif self.btn_new.collidepoint(mx, my):
            self.reset_operation()
        elif self.btn_fog.collidepoint(mx, my):
            self.fog_enabled = not self.fog_enabled
            self.log.add("Fog of war enabled." if self.fog_enabled else "Fog of war disabled.")
        elif self.btn_debug.collidepoint(mx, my):
            self.debug_show_anomaly = not self.debug_show_anomaly
            self.log.add("Debug: anomaly visibility ON." if self.debug_show_anomaly else "Debug: anomaly visibility OFF.")

    def update_fx(self, dt):
        keep = []
        for t in self.tracers:
            t.ttl -= dt
            if t.ttl > 0:
                keep.append(t)
        self.tracers = keep

    def update(self, dt):
        if self.paused or self.phase in ("success", "failure"):
            self.update_fx(dt)
            return

        self.elapsed += dt

        for op in self.operatives:
            op.update(self, dt)

        if self.anomaly:
            self.anomaly.update(self, dt)

        self.update_fog()
        self.update_fx(dt)
        self.update_phase_outcomes()

    # ==========================
    # Rendering
    # ==========================
    def draw_map(self):
        # outdoor / indoor palette
        outdoor_floor = (28, 28, 34)
        indoor_floor = (24, 24, 30)
        wall = (12, 12, 16)
        door = (90, 72, 40)
        fog = (0, 0, 0)

        for y in range(self.map_h):
            for x in range(self.map_w):
                rect = pygame.Rect(x * self.tile, y * self.tile, self.tile, self.tile)

                if self.fog_enabled and not self.revealed[y][x]:
                    pygame.draw.rect(self.screen, fog, rect)
                    continue

                v = self.grid[y][x]
                if v == 1:
                    pygame.draw.rect(self.screen, wall, rect)
                elif v == 2:
                    # door sits “on wall line”
                    pygame.draw.rect(self.screen, door, rect)
                else:
                    # indoor vs outdoor
                    if self.building_id[y][x] != -1:
                        pygame.draw.rect(self.screen, indoor_floor, rect)
                    else:
                        pygame.draw.rect(self.screen, outdoor_floor, rect)

        # highlight entry/extraction
        exx, exy = self.extraction
        enx, eny = self.entry
        pygame.draw.rect(self.screen, (40, 90, 40), pygame.Rect(exx * self.tile, exy * self.tile, self.tile, self.tile), width=2)
        pygame.draw.rect(self.screen, (80, 80, 120), pygame.Rect(enx * self.tile, eny * self.tile, self.tile, self.tile), width=2)

    def draw_paths(self):
        for op in self.operatives:
            if not op.alive or not op.path:
                continue
            if self.fog_enabled and not self.revealed[op.gy][op.gx]:
                continue
            points = [(int((op.px + 0.5) * self.tile), int((op.py + 0.5) * self.tile))]
            for (gx, gy) in op.path[:18]:
                if self.fog_enabled and not self.revealed[gy][gx]:
                    break
                points.append((gx * self.tile + self.tile // 2, gy * self.tile + self.tile // 2))
            if len(points) >= 2:
                pygame.draw.lines(self.screen, (60, 60, 85), False, points, 2)

    def draw_tracers(self):
        for t in self.tracers:
            # convert tile coords -> pixels
            x0 = int(t.x0 * self.tile)
            y0 = int(t.y0 * self.tile)
            x1 = int(t.x1 * self.tile)
            y1 = int(t.y1 * self.tile)
            pygame.draw.line(self.screen, t.color, (x0, y0), (x1, y1), 2)

    def draw_entities(self):
        # operatives
        for op in self.operatives:
            if not op.alive:
                continue
            gx, gy = op.gx, op.gy
            if self.fog_enabled and not self.revealed[gy][gx]:
                continue

            cx = int((op.px + 0.5) * self.tile)
            cy = int((op.py + 0.5) * self.tile)

            col = (220, 220, 220)
            if op.injured:
                col = (230, 150, 50)
            if op.fleeing:
                col = (210, 140, 140)
            if op.detected_anomaly:
                col = (180, 230, 100)

            pygame.draw.circle(self.screen, col, (cx, cy), self.tile // 3)
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), self.tile // 3, width=2)

            if op == self.selected:
                pygame.draw.circle(self.screen, (200, 200, 120), (cx, cy), self.tile // 2, width=2)

        # anomaly
        if self.anomaly and not self.anomaly.contained:
            ax, ay = self.anomaly.gx, self.anomaly.gy
            visible = self.debug_show_anomaly
            if not visible:
                if (not self.fog_enabled or self.revealed[ay][ax]):
                    visible = any(op.alive and op.can_see(self, (ax, ay)) for op in self.operatives)

            if visible:
                cx = int((self.anomaly.px + 0.5) * self.tile)
                cy = int((self.anomaly.py + 0.5) * self.tile)
                r = self.tile // 3
                pts = [(cx, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
                col = (220, 50, 50) if not self.anomaly.immobilized else (180, 120, 120)
                pygame.draw.polygon(self.screen, col, pts)
                pygame.draw.polygon(self.screen, (0, 0, 0), pts, width=2)

    def draw_side_panel(self):
        x0 = self.map_w * self.tile
        pygame.draw.rect(self.screen, (18, 18, 22), pygame.Rect(x0, 0, self.panel_w, self.screen_h))
        pygame.draw.line(self.screen, (60, 60, 70), (x0, 0), (x0, self.screen_h), 2)

        y = 12
        y = draw_title_text(self.screen, "OPERATION VIEW", x0 + 14, y)

        phase = self.phase.upper()
        t_left = max(0, int(self.deadline - self.elapsed))
        y = draw_body_text(self.screen, f"Phase: {phase}", x0 + 14, y)
        y = draw_body_text(self.screen, f"Time Left: {t_left}s", x0 + 14, y)

        if self.anomaly:
            a = self.anomaly
            status = "CONTAINED" if a.contained else "ACTIVE"
            y = draw_body_text(self.screen, f"Anomaly: {a.code} [{status}]", x0 + 14, y)
            y = draw_body_text(self.screen, f"HP: {int(a.hp)}/{a.hp_max}", x0 + 14, y)
            y = draw_body_text(self.screen, f"Stability: {int(a.stability)}/100", x0 + 14, y)
            y = draw_body_text(self.screen, f"Aggro: {int(a.aggro)}/100", x0 + 14, y)
            if a.immobilized:
                y = draw_body_text(self.screen, "State: Immobilized", x0 + 14, y, color=(230, 150, 50))
            y += 6

        bw, bh = self.panel_w - 28, 32
        self.btn_pause = draw_primary_button(self.screen, "Resume" if self.paused else "Pause", x0 + 14, y, bw, bh)
        y += bh + 10
        self.btn_retreat = draw_deny_button(self.screen, "Retreat", x0 + 14, y, bw, bh)
        y += bh + 10
        self.btn_new = draw_secondary_button(self.screen, "New Operation", x0 + 14, y, bw, bh)
        y += bh + 10
        self.btn_fog = draw_secondary_button(self.screen, "Toggle Fog", x0 + 14, y, bw, bh)
        y += bh + 10
        self.btn_debug = draw_secondary_button(self.screen, "Toggle Debug", x0 + 14, y, bw, bh)
        y += bh + 14

        y = draw_header_text(self.screen, "Selected Operative", x0 + 14, y)
        if self.selected:
            op = self.selected
            y = draw_body_text(self.screen, f"{op.name} ({op.role})", x0 + 14, y)
            y = draw_body_text(self.screen, f"Weapon: {op.weapon.name}", x0 + 14, y)
            if op.reloading > 0:
                y = draw_body_text(self.screen, f"Reloading: {op.reloading:.1f}s", x0 + 14, y, color=(230, 150, 50))
            y = draw_body_text(self.screen, f"Ammo: {op.ammo}/{op.weapon.mag_size}", x0 + 14, y)
            y = draw_body_text(self.screen, f"HP: {max(0, int(op.hp))}/{op.hp_max}", x0 + 14, y)
            y = draw_body_text(self.screen, f"Panic: {int(op.panic)}", x0 + 14, y)
            y = draw_body_text(self.screen, f"Kit: {int(op.kit_integrity)}%", x0 + 14, y)
            y = draw_body_text(self.screen, f"State: {op.state}", x0 + 14, y)
            y += 6
            for k in ATTR_KEYS:
                v = op.attrs[k]
                col = get_attribute_color(v)
                y = draw_body_text(self.screen, f"{k.capitalize():<11} {v:>2}", x0 + 14, y, color=col)
        else:
            y = draw_body_text(self.screen, "None", x0 + 14, y)

        y += 10
        y = draw_header_text(self.screen, "Event Log", x0 + 14, y)
        log_top = y
        log_h = self.screen_h - log_top - 16
        log_rect = pygame.Rect(x0 + 14, log_top, self.panel_w - 28, log_h)
        pygame.draw.rect(self.screen, (12, 12, 16), log_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 70, 80), log_rect, width=1, border_radius=6)

        pad = 10
        lx = log_rect.x + pad
        ly = log_rect.y + pad
        max_lines = (log_rect.h - 2 * pad) // 18
        total = len(self.log.lines)

        start_index = max(0, total - max_lines - self.log.scroll)
        end_index = min(total, start_index + max_lines)

        for i in range(start_index, end_index):
            msg = self.log.lines[i]
            if len(msg) > 52:
                msg = msg[:52] + "…"
            text = FOOTER_FONT.render(msg, True, (200, 200, 200))
            self.screen.blit(text, (lx, ly))
            ly += 18

    def render(self):
        self.screen.fill((0, 0, 0))
        self.draw_map()
        self.draw_paths()
        self.draw_tracers()
        self.draw_entities()
        self.draw_side_panel()

        if self.phase in ("success", "failure"):
            overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            msg = "MISSION SUCCESS" if self.phase == "success" else "MISSION FAILED"
            text = TITLE_FONT.render(msg, True, (240, 240, 240))
            rect = text.get_rect(center=(self.screen_w // 2 - self.panel_w // 2, self.screen_h // 2))
            self.screen.blit(text, rect)

        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    map_rect = pygame.Rect(0, 0, self.map_w * self.tile, self.map_h * self.tile)

                    if event.button == 4:
                        self.log.scroll_by(3)
                    elif event.button == 5:
                        self.log.scroll_by(-3)
                    else:
                        if map_rect.collidepoint(mx, my):
                            self.handle_click_map(mx, my, event.button)
                        else:
                            self.handle_buttons(mx, my)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        self.log.add("Paused." if self.paused else "Resumed.")
                    elif event.key == pygame.K_r:
                        self.retreat_order = True
                        self.phase = "extraction"
                        self.log.add("RETREAT ORDER: All operatives extract immediately!")
                    elif event.key == pygame.K_n:
                        self.reset_operation()
                    elif event.key == pygame.K_f:
                        self.fog_enabled = not self.fog_enabled
                        self.log.add("Fog of war enabled." if self.fog_enabled else "Fog of war disabled.")
                    elif event.key == pygame.K_d:
                        self.debug_show_anomaly = not self.debug_show_anomaly
                        self.log.add("Debug: anomaly visibility ON." if self.debug_show_anomaly else "Debug: anomaly visibility OFF.")
                    elif event.key == pygame.K_ESCAPE:
                        if self.selected:
                            self.selected.manual_target = None
                            self.selected.path = []
                            self.log.add(f"{self.selected.name} manual orders cleared.")

            self.update(dt)
            self.render()


def main():
    pygame.init()
    info = pygame.display.Info()
    WIDTH, HEIGHT = info.current_w, info.current_h

    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("UI Button Test")

    sim = OperationSim(map_w=52, map_h=34, tile=20, screen=screen)
    sim.run()
    pygame.quit()

if __name__ == "__main__":
    main()
