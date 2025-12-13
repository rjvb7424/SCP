# operation_simulation.py
# ------------------------------------------------------------
# SCP-inspired Operation Simulation (Football Manager-style view)
# ------------------------------------------------------------
# Controls
# - Left click an operative to select them
# - Right click the map to set a manual waypoint for the selected operative
# - Mouse wheel over the log panel to scroll
#
# Buttons (right panel)
# - Pause/Resume
# - Retreat (order extraction / flee)
# - New Operation (regenerate map + new anomaly + new team)
# - Toggle Fog
# - Toggle Debug (shows anomaly even if not detected)
#
# Notes
# - Operatives have attributes that affect movement, detection, combat pressure,
#   capture chance, panic/flee chance, healing, etc.
# - The anomaly may attack, flee, and “slip away” if not contained in time.
# ------------------------------------------------------------

import math
import random
import heapq
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

import pygame

# ==========================
# Reusable UI Components (self-contained)
# ==========================
pygame.font.init()

FONT = "arial"
COLOR = (220, 220, 220)
TITLE_FONT = pygame.font.SysFont(FONT, 24)
HEADER_FONT = pygame.font.SysFont(FONT, 20)
BODY_FONT = pygame.font.SysFont(FONT, 16)
FOOTER_FONT = pygame.font.SysFont(FONT, 14)

BUTTON_BORDER_RADIUS = 4

BUTTON_BG = (50, 50, 70)
BUTTON_BG_HOVER = (80, 80, 120)
BUTTON_TEXT_COLOR = (240, 240, 240)
BUTTON_BORDER_COLOR = (180, 180, 200)

SECONDARY_BG = (40, 40, 40)
SECONDARY_BG_HOVER = (70, 70, 70)
SECONDARY_TEXT_COLOR = (230, 230, 230)
SECONDARY_BORDER_COLOR = (160, 160, 160)

ACCEPT_BG = (40, 90, 40)
ACCEPT_BG_HOVER = (60, 130, 60)
ACCEPT_TEXT_COLOR = (230, 255, 230)
ACCEPT_BORDER_COLOR = (120, 200, 120)

DENY_BG = (110, 40, 40)
DENY_BG_HOVER = (150, 60, 60)
DENY_TEXT_COLOR = (255, 230, 230)
DENY_BORDER_COLOR = (210, 140, 140)


def _draw_text(surface, text, x, y, font, color):
    text_surf = font.render(text, True, color)
    surface.blit(text_surf, (x, y))
    return y + text_surf.get_height() + 4


def draw_title_text(surface, text, x, y, color=COLOR):
    return _draw_text(surface, text, x, y, TITLE_FONT, color)


def draw_header_text(surface, text, x, y, color=COLOR):
    return _draw_text(surface, text, x, y, HEADER_FONT, color)


def draw_body_text(surface, text, x, y, color=COLOR):
    return _draw_text(surface, text, x, y, BODY_FONT, color)


def draw_footer_text(surface, text, x, y, color=COLOR):
    return _draw_text(surface, text, x, y, FOOTER_FONT, color)


def _draw_button(surface, text, x, y, width, height, bg_color, hover_color, text_color, border_color):
    rect = pygame.Rect(x, y, width, height)
    mx, my = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mx, my)
    current_bg = hover_color if is_hovered else bg_color

    pygame.draw.rect(surface, current_bg, rect, border_radius=BUTTON_BORDER_RADIUS)
    pygame.draw.rect(surface, border_color, rect, width=1, border_radius=BUTTON_BORDER_RADIUS)

    text_surf = BODY_FONT.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)
    return rect


def draw_primary_button(surface, text, x, y, width, height):
    return _draw_button(surface, text, x, y, width, height,
                        BUTTON_BG, BUTTON_BG_HOVER, BUTTON_TEXT_COLOR, BUTTON_BORDER_COLOR)


def draw_secondary_button(surface, text, x, y, width, height):
    return _draw_button(surface, text, x, y, width, height,
                        SECONDARY_BG, SECONDARY_BG_HOVER, SECONDARY_TEXT_COLOR, SECONDARY_BORDER_COLOR)


def draw_accept_button(surface, text, x, y, width, height):
    return _draw_button(surface, text, x, y, width, height,
                        ACCEPT_BG, ACCEPT_BG_HOVER, ACCEPT_TEXT_COLOR, ACCEPT_BORDER_COLOR)


def draw_deny_button(surface, text, x, y, width, height):
    return _draw_button(surface, text, x, y, width, height,
                        DENY_BG, DENY_BG_HOVER, DENY_TEXT_COLOR, DENY_BORDER_COLOR)


def _lerp_color(c1, c2, t: float):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def get_attribute_color(value, lo=0, hi=20):
    v = max(lo, min(hi, value))
    norm = (v - lo) / (hi - lo)

    red = (220, 50, 50)
    orange = (230, 150, 50)
    light_green = (180, 230, 100)
    dark_green = (20, 180, 80)

    if norm < 1 / 3:
        t = norm / (1 / 3)
        return _lerp_color(red, orange, t)
    elif norm < 2 / 3:
        t = (norm - 1 / 3) / (1 / 3)
        return _lerp_color(orange, light_green, t)
    else:
        t = (norm - 2 / 3) / (1 / 3)
        return _lerp_color(light_green, dark_green, t)


# ==========================
# Utils
# ==========================
def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def manhattan(a: Tuple[int, int], b: Tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def bresenham_line(x0, y0, x1, y1):
    """Integer grid line points."""
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
    w, h = len(grid[0]), len(grid)

    def in_bounds(p):
        return 0 <= p[0] < w and 0 <= p[1] < h

    def passable(p):
        return grid[p[1]][p[0]] == 0

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
# Map Generation (Cave-like)
# ==========================
def generate_cave(width: int, height: int, fill_prob: float = 0.42, steps: int = 5) -> List[List[int]]:
    # 1 = wall, 0 = floor
    grid = [[1 for _ in range(width)] for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                grid[y][x] = 1
            else:
                grid[y][x] = 1 if random.random() < fill_prob else 0

    def count_walls_around(cx, cy):
        c = 0
        for yy in range(cy - 1, cy + 2):
            for xx in range(cx - 1, cx + 2):
                if xx == cx and yy == cy:
                    continue
                if xx < 0 or yy < 0 or xx >= width or yy >= height:
                    c += 1
                elif grid[yy][xx] == 1:
                    c += 1
        return c

    for _ in range(steps):
        newg = [[grid[y][x] for x in range(width)] for y in range(height)]
        for y in range(1, height - 1):
            for x in range(1, width - 1):
                walls = count_walls_around(x, y)
                if walls >= 5:
                    newg[y][x] = 1
                else:
                    newg[y][x] = 0
        grid = newg

    return grid


def flood_fill_floor(grid, start: Tuple[int, int]) -> set:
    w, h = len(grid[0]), len(grid)
    stack = [start]
    visited = set()
    while stack:
        x, y = stack.pop()
        if (x, y) in visited:
            continue
        if not (0 <= x < w and 0 <= y < h):
            continue
        if grid[y][x] == 1:
            continue
        visited.add((x, y))
        stack.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])
    return visited


def ensure_connectivity(grid) -> List[List[int]]:
    """Keep the largest connected floor region; convert other floors to walls."""
    w, h = len(grid[0]), len(grid)
    seen = set()
    regions = []

    for y in range(h):
        for x in range(w):
            if grid[y][x] == 0 and (x, y) not in seen:
                reg = flood_fill_floor(grid, (x, y))
                seen |= reg
                regions.append(reg)

    if not regions:
        return grid

    regions.sort(key=len, reverse=True)
    main = regions[0]
    for y in range(h):
        for x in range(w):
            if grid[y][x] == 0 and (x, y) not in main:
                grid[y][x] = 1
    return grid


def carve_room(grid, cx, cy, rw, rh):
    h = len(grid)
    w = len(grid[0])
    x0 = clamp(cx - rw // 2, 1, w - 2)
    x1 = clamp(cx + rw // 2, 1, w - 2)
    y0 = clamp(cy - rh // 2, 1, h - 2)
    y1 = clamp(cy + rh // 2, 1, h - 2)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = 0


def random_floor_cell(grid, avoid: Optional[List[Tuple[int, int]]] = None, tries=5000) -> Tuple[int, int]:
    avoid = avoid or []
    h = len(grid)
    w = len(grid[0])
    for _ in range(tries):
        x = random.randint(1, w - 2)
        y = random.randint(1, h - 2)
        if grid[y][x] == 0 and all(manhattan((x, y), a) > 6 for a in avoid):
            return (x, y)
    # fallback: brute find any floor
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if grid[y][x] == 0:
                return (x, y)
    return (1, 1)


# ==========================
# Simulation Data
# ==========================
ATTR_KEYS = ["speed", "perception", "tactics", "aim", "endurance", "courage", "medical", "containment"]

ROLE_TEMPLATES = {
    "Leader":   {"speed": 10, "perception": 12, "tactics": 16, "aim": 11, "endurance": 12, "courage": 16, "medical": 6, "containment": 12},
    "Scout":    {"speed": 16, "perception": 17, "tactics": 10, "aim": 9,  "endurance": 10, "courage": 12, "medical": 5, "containment": 10},
    "Medic":    {"speed": 10, "perception": 12, "tactics": 10, "aim": 8,  "endurance": 12, "courage": 12, "medical": 18, "containment": 10},
    "Breacher": {"speed": 11, "perception": 10, "tactics": 12, "aim": 12, "endurance": 17, "courage": 13, "medical": 6, "containment": 14},
    "Sniper":   {"speed": 10, "perception": 16, "tactics": 10, "aim": 18, "endurance": 9,  "courage": 11, "medical": 4, "containment": 9},
    "Tech":     {"speed": 9,  "perception": 11, "tactics": 14, "aim": 9,  "endurance": 10, "courage": 10, "medical": 8, "containment": 16},
}


def jitter_base(v, spread=4):
    return clamp(v + random.randint(-spread, spread), 0, 20)


@dataclass
class DamageOverTime:
    dps: float
    duration: float


class EventLog:
    def __init__(self, max_lines=300):
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

        self.state = "inserting"  # inserting/search/chase/capture/extract/flee
        self.cooldown = 0.0

        # team gear abstractions
        self.kit_integrity = 100.0  # impacts containment attempts
        self.suppression = 0.0  # temporary "pressure" applied to anomaly

        self.last_seen_anomaly: Optional[Tuple[int, int]] = None
        self.detected_anomaly = False

    def speed_tiles_per_sec(self):
        base = 1.4 + (self.attrs["speed"] / 20.0) * 2.0  # 1.4..3.4
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
        # also affected by kit integrity
        return (self.attrs["containment"] / 20.0) * (0.55 + 0.45 * (self.kit_integrity / 100.0))

    def medical_skill(self):
        return self.attrs["medical"] / 20.0

    def apply_damage(self, sim, amount: float, cause: str = "unknown"):
        if not self.alive or self.incapacitated:
            return

        self.hp -= amount
        sim.log.add(f"{self.name} took {amount:.0f} damage ({cause}).")

        # bleeding chance depends on severity
        if amount >= 10 and random.random() < 0.25:
            self.bleeds.append(DamageOverTime(dps=1.2 + random.random() * 1.2, duration=8 + random.random() * 6))
            sim.log.add(f"{self.name} is bleeding!")

        # injury threshold
        if self.hp <= self.hp_max * 0.45 and not self.injured and self.hp > 0:
            self.injured = True
            sim.log.add(f"{self.name} is injured (movement & actions slower).")

        # panic spike (lower courage => more panic)
        panic_gain = amount * (1.2 - self.courage_resist())
        self.panic = clamp(self.panic + panic_gain, 0, 100)

        # chance to flee when panic high
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
        # medics heal adjacent operatives if calm enough and not in direct chase
        if self.medical_skill() < 0.25 or not self.alive or self.incapacitated:
            return
        if self.state in ("chase", "capture") and random.random() < 0.6:
            return
        if self.panic > 70:
            return

        radius = 1
        for other in sim.operatives:
            if other is self or not other.alive:
                continue
            if manhattan((self.gx, self.gy), (other.gx, other.gy)) <= radius:
                if other.hp < other.hp_max and (other.injured or other.bleeds):
                    heal_rate = 2.0 + 8.0 * self.medical_skill()  # 2..10 hp/s
                    other.hp = min(other.hp_max, other.hp + heal_rate * dt)
                    # reduce bleeding duration
                    if other.bleeds and random.random() < 0.2 * self.medical_skill():
                        other.bleeds.pop(0)
                        sim.log.add(f"{self.name} stabilizes {other.name}'s bleeding.")
                    if other.hp > other.hp_max * 0.55:
                        other.injured = False
                    if random.random() < 0.08:
                        sim.log.add(f"{self.name} treats {other.name}.")
                break

    def can_see(self, sim, target: Tuple[int, int]) -> bool:
        x0, y0 = self.gx, self.gy
        x1, y1 = target
        # quick radius check
        if manhattan((x0, y0), (x1, y1)) > self.perception_radius():
            return False
        # LoS check
        for (x, y) in bresenham_line(x0, y0, x1, y1):
            if (x, y) == (x0, y0) or (x, y) == (x1, y1):
                continue
            if sim.grid[y][x] == 1:
                return False
        return True

    def choose_explore_target(self, sim) -> Optional[Tuple[int, int]]:
        # favor unvisited, revealed frontier tiles
        candidates = []
        pr = self.perception_radius() + 2
        for _ in range(120):
            x = clamp(self.gx + random.randint(-pr * 2, pr * 2), 1, sim.map_w - 2)
            y = clamp(self.gy + random.randint(-pr * 2, pr * 2), 1, sim.map_h - 2)
            if sim.grid[y][x] == 0:
                score = 0.0
                # prefer not recently visited
                score += 2.0 if not sim.visited[y][x] else 0.0
                # prefer unknown around (frontier)
                unknown = 0
                for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                    if 0 <= nx < sim.map_w and 0 <= ny < sim.map_h and not sim.revealed[ny][nx]:
                        unknown += 1
                score += unknown * 0.9
                # less crowded
                crowd = sum(1 for op in sim.operatives if op.alive and manhattan((x,y),(op.gx,op.gy)) <= 2)
                score -= crowd * 0.6
                # distance penalty
                score -= manhattan((self.gx, self.gy), (x, y)) * 0.06
                candidates.append((score, (x, y)))
        if not candidates:
            return None
        candidates.sort(key=lambda t: t[0], reverse=True)
        return candidates[0][1]

    def decide(self, sim):
        if not self.alive or self.incapacitated:
            return

        # if retreat ordered or fleeing -> go to extraction
        if sim.retreat_order or self.fleeing or sim.phase == "extraction":
            self.state = "extract"
            self.manual_target = sim.extraction
            return

        # manual waypoint overrides
        if self.manual_target is not None:
            self.state = "manual"
            return

        # if anomaly was seen by team, head there depending on tactics
        if sim.team_last_known_anomaly is not None:
            # split behavior: higher tactics -> better flanking (approach from offset)
            if random.random() < 0.35 + 0.35 * self.tactics_bonus():
                tx, ty = sim.team_last_known_anomaly
                ox = random.randint(-2, 2)
                oy = random.randint(-2, 2)
                tgt = (clamp(tx + ox, 1, sim.map_w - 2), clamp(ty + oy, 1, sim.map_h - 2))
                if sim.is_floor(tgt):
                    self.state = "chase"
                    self.manual_target = tgt
                    return
            self.state = "chase"
            self.manual_target = sim.team_last_known_anomaly
            return

        # otherwise explore
        self.state = "search"
        tgt = self.choose_explore_target(sim)
        if tgt:
            self.manual_target = tgt

    def attempt_suppress(self, sim, dt):
        """If anomaly in LoS and range, apply suppression/pressure."""
        if not self.alive or self.incapacitated:
            return
        if sim.anomaly is None or sim.anomaly.contained:
            return
        if not self.can_see(sim, (sim.anomaly.gx, sim.anomaly.gy)):
            return

        rng = 6 + int(self.attrs["aim"] / 5)  # 6..10
        if manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) > rng:
            return

        if self.cooldown > 0:
            return

        # chance to "hit" and apply pressure
        hit_chance = 0.25 + 0.55 * self.aim_quality()
        if self.injured:
            hit_chance *= 0.75
        if random.random() < hit_chance:
            pressure = 4.0 + 10.0 * self.aim_quality()
            sim.anomaly.stability = clamp(sim.anomaly.stability - pressure, 0, 100)
            sim.log.add(f"{self.name} applies pressure: anomaly stability -{pressure:.0f}.")
            # make anomaly more aggressive if pressured
            sim.anomaly.aggro = clamp(sim.anomaly.aggro + 6.0, 0, 100)
            self.cooldown = 0.6 + random.random() * 0.5

    def attempt_capture(self, sim):
        if not self.alive or self.incapacitated:
            return False
        if sim.anomaly is None or sim.anomaly.contained:
            return False
        if manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) > 1:
            return False

        # capture is harder when stability is high
        stability_factor = 1.0 - (sim.anomaly.stability / 100.0)  # 0..1
        skill = self.containment_skill()

        # teamwork: more adjacent operatives improves odds
        adjacent = sum(
            1 for op in sim.operatives
            if op.alive and not op.incapacitated and manhattan((op.gx, op.gy), (sim.anomaly.gx, sim.anomaly.gy)) <= 1
        )
        team_factor = 1.0 + (adjacent - 1) * 0.35

        # anomaly resilience reduces odds
        res = sim.anomaly.resilience / 20.0

        base = 0.05 + 0.35 * skill
        chance = base * (0.35 + 0.65 * stability_factor) * team_factor * (1.0 - 0.45 * res)
        chance = clamp(chance, 0.02, 0.72)

        # capture attempt damages kit and spikes anomaly aggro
        self.kit_integrity = clamp(self.kit_integrity - (6 + random.random() * 8), 0, 100)
        sim.anomaly.aggro = clamp(sim.anomaly.aggro + 10, 0, 100)

        if random.random() < chance:
            sim.anomaly.contained = True
            sim.phase = "extraction"
            sim.log.add(f"CONTAINMENT SUCCESS by {self.name}! Begin extraction.")
            return True
        else:
            sim.log.add(f"{self.name} containment attempt failed.")
            # failed attempt can cause backlash
            if random.random() < 0.20 + 0.35 * (sim.anomaly.threat / 20.0):
                self.apply_damage(sim, 8 + random.random() * 16, cause="containment backlash")
            return False

    def update(self, sim, dt):
        if not self.alive:
            return

        # cooldown timers
        self.cooldown = max(0.0, self.cooldown - dt)

        # passive panic recovery if not under immediate threat
        if sim.anomaly and not sim.anomaly.contained:
            near = manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) <= 6
        else:
            near = False
        if not near:
            self.panic = max(0.0, self.panic - dt * (8.0 + 12.0 * self.courage_resist()))

        self.update_bleeding(sim, dt)
        if not self.alive:
            return

        # heal allies
        self.heal_nearby(sim, dt)

        # detect anomaly
        self.detected_anomaly = False
        if sim.anomaly and not sim.anomaly.contained:
            if self.can_see(sim, (sim.anomaly.gx, sim.anomaly.gy)):
                self.detected_anomaly = True
                self.last_seen_anomaly = (sim.anomaly.gx, sim.anomaly.gy)
                sim.team_last_known_anomaly = (sim.anomaly.gx, sim.anomaly.gy)

        # behavior planning
        if self.cooldown <= 0 and (not self.path or random.random() < 0.03):
            self.decide(sim)
            # set path to manual_target if exists
            if self.manual_target is not None:
                p = astar(sim.grid, (self.gx, self.gy), self.manual_target)
                if p:
                    self.path = p[1:]  # exclude current
                else:
                    # can't reach; drop target
                    self.manual_target = None
                    self.path = []

        # combat pressure if we can see anomaly
        self.attempt_suppress(sim, dt)

        # if adjacent, attempt capture (with some cadence)
        if sim.anomaly and not sim.anomaly.contained and manhattan((self.gx, self.gy), (sim.anomaly.gx, sim.anomaly.gy)) <= 1:
            if self.cooldown <= 0:
                self.cooldown = 0.8 + random.random() * 0.7
                self.attempt_capture(sim)

        # movement along path (smooth)
        spd = self.speed_tiles_per_sec()
        if spd > 0 and self.path:
            tx, ty = self.path[0]
            # move toward target node
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
        self.stability = 100.0  # reduced by suppression; low stability => easier capture
        self.aggro = float(aggression) * 3.0  # 0..100-ish
        self.cooldown = 0.0

        self.escape_timer = 0.0  # time spent with no operative contact
        self.last_target: Optional[Tuple[int, int]] = None
        self.path = []

    def speed_tiles_per_sec(self):
        return 1.6 + (self.speed / 20.0) * 2.2  # 1.6..3.8

    def update(self, sim, dt):
        if self.contained:
            return

        self.cooldown = max(0.0, self.cooldown - dt)

        # decide if detected by any operative (LoS)
        visible_by = []
        for op in sim.operatives:
            if not op.alive:
                continue
            # anomaly stealth reduces detection
            stealth_factor = 1.0 - (self.stealth / 30.0)  # 1..~0.33
            if manhattan((op.gx, op.gy), (self.gx, self.gy)) <= op.perception_radius():
                if op.can_see(sim, (self.gx, self.gy)) and random.random() < (0.85 * stealth_factor + 0.15):
                    visible_by.append(op)

        # if not seen, stability slowly recovers
        if not visible_by:
            self.stability = clamp(self.stability + dt * (3.0 + 5.0 * (self.resilience / 20.0)), 0, 100)
            self.escape_timer += dt
        else:
            self.escape_timer = 0.0

        # target logic: if close to an operative, maybe attack; else evade from last known
        closest_op = None
        best_d = 9999
        for op in sim.operatives:
            if not op.alive or op.incapacitated:
                continue
            d = manhattan((op.gx, op.gy), (self.gx, self.gy))
            if d < best_d:
                best_d = d
                closest_op = op

        # attack if adjacent and aggressive enough
        if closest_op and best_d <= 1 and self.cooldown <= 0:
            lethality = 6 + (self.threat / 20.0) * 16  # 6..22
            # pressure low stability => anomaly "less coherent" => slightly reduced lethality
            lethality *= (0.85 + 0.15 * (self.stability / 100.0))
            # aggression influences multi-hit chance
            if random.random() < 0.85:
                closest_op.apply_damage(sim, lethality + random.random() * 6, cause=f"{self.code} attack")
            if random.random() < 0.25 + 0.35 * (self.aggro / 100.0):
                # second swipe
                closest_op.apply_damage(sim, (lethality * 0.6) + random.random() * 5, cause=f"{self.code} follow-up")
            self.cooldown = 1.0 + random.random() * 0.6

        # movement target selection
        if not self.path or random.random() < 0.06:
            if visible_by:
                # evade: move away from centroid of observers
                ax = sum(op.gx for op in visible_by) / len(visible_by)
                ay = sum(op.gy for op in visible_by) / len(visible_by)
                dx = self.gx - ax
                dy = self.gy - ay
                mag = math.hypot(dx, dy) + 1e-6
                dx /= mag
                dy /= mag

                # pick a point in that direction
                step = 10 + int(self.stealth / 2)
                tx = int(clamp(self.gx + dx * step, 1, sim.map_w - 2))
                ty = int(clamp(self.gy + dy * step, 1, sim.map_h - 2))
                # jitter
                tx = clamp(tx + random.randint(-3, 3), 1, sim.map_w - 2)
                ty = clamp(ty + random.randint(-3, 3), 1, sim.map_h - 2)
                target = (tx, ty)
                if not sim.is_floor(target):
                    target = random_floor_cell(sim.grid, avoid=[(op.gx, op.gy) for op in sim.operatives if op.alive])
                self.last_target = target
            else:
                # roam: prefer unknown (to escape) if fog on; else random
                if sim.fog_enabled and random.random() < 0.75:
                    target = sim.find_far_unrevealed_from((self.gx, self.gy))
                    if target is None:
                        target = random_floor_cell(sim.grid, avoid=[sim.extraction, sim.entry])
                else:
                    target = random_floor_cell(sim.grid, avoid=[sim.extraction, sim.entry])
                self.last_target = target

            if self.last_target:
                p = astar(sim.grid, (self.gx, self.gy), self.last_target)
                self.path = p[1:] if p else []

        # movement
        spd = self.speed_tiles_per_sec()
        if self.path:
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
    def __init__(self, map_w=52, map_h=34, tile=20):
        self.map_w = map_w
        self.map_h = map_h
        self.tile = tile

        self.panel_w = 360
        self.screen_w = self.map_w * self.tile + self.panel_w
        self.screen_h = self.map_h * self.tile

        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption("Operation Simulation - Containment")

        self.clock = pygame.time.Clock()
        self.running = True

        self.debug_show_anomaly = False
        self.fog_enabled = True

        self.log = EventLog()
        self.selected: Optional[Operative] = None

        self.paused = False
        self.retreat_order = False

        self.phase = "insertion"  # insertion/operation/extraction/failure/success
        self.elapsed = 0.0
        self.deadline = 420.0  # operation time limit (seconds)

        # world
        self.grid: List[List[int]] = []
        self.revealed: List[List[bool]] = []
        self.visited: List[List[bool]] = []
        self.entry = (2, 2)
        self.extraction = (2, 2)

        self.operatives: List[Operative] = []
        self.anomaly: Optional[Anomaly] = None

        self.team_last_known_anomaly: Optional[Tuple[int, int]] = None

        # UI button rects
        self.btn_pause = pygame.Rect(0, 0, 0, 0)
        self.btn_retreat = pygame.Rect(0, 0, 0, 0)
        self.btn_new = pygame.Rect(0, 0, 0, 0)
        self.btn_fog = pygame.Rect(0, 0, 0, 0)
        self.btn_debug = pygame.Rect(0, 0, 0, 0)

        self.reset_operation()

    def is_floor(self, cell: Tuple[int, int]) -> bool:
        x, y = cell
        return 0 <= x < self.map_w and 0 <= y < self.map_h and self.grid[y][x] == 0

    def reset_operation(self):
        self.elapsed = 0.0
        self.phase = "insertion"
        self.paused = False
        self.retreat_order = False
        self.team_last_known_anomaly = None

        # generate map
        self.grid = generate_cave(self.map_w, self.map_h, fill_prob=0.44, steps=5)
        self.grid = ensure_connectivity(self.grid)

        # carve entry + extraction rooms
        self.entry = (3, self.map_h // 2)
        self.extraction = (self.map_w - 4, self.map_h // 2)

        carve_room(self.grid, self.entry[0], self.entry[1], 7, 7)
        carve_room(self.grid, self.extraction[0], self.extraction[1], 7, 7)

        # open corridor-ish connection attempt by ensuring both are in same region
        # If not connected, soften walls by carving a noisy tunnel
        if self.is_floor(self.entry) and self.is_floor(self.extraction):
            p = astar(self.grid, self.entry, self.extraction)
            if not p:
                # carve a rough tunnel
                x, y = self.entry
                for _ in range(800):
                    if (x, y) == self.extraction:
                        break
                    self.grid[y][x] = 0
                    dx = 1 if x < self.extraction[0] else -1 if x > self.extraction[0] else 0
                    dy = 1 if y < self.extraction[1] else -1 if y > self.extraction[1] else 0
                    if random.random() < 0.65:
                        x = clamp(x + dx + random.randint(-1, 1), 1, self.map_w - 2)
                    else:
                        y = clamp(y + dy + random.randint(-1, 1), 1, self.map_h - 2)
                self.grid = ensure_connectivity(self.grid)

        self.revealed = [[False for _ in range(self.map_w)] for _ in range(self.map_h)]
        self.visited = [[False for _ in range(self.map_w)] for _ in range(self.map_h)]

        self.log = EventLog()
        self.log.add("New operation initialized.")
        self.log.add("Objective: contain the anomaly and extract survivors.")

        # create team
        self.operatives = self.build_team()

        self.selected = self.operatives[0] if self.operatives else None

        # anomaly spawn far from entry/extraction
        spawn = random_floor_cell(self.grid, avoid=[self.entry, self.extraction])
        self.anomaly = self.build_anomaly(spawn)

        self.phase = "operation"
        self.log.add(f"Anomaly registered: {self.anomaly.code}. Threat level unknown.")

        # initial reveal around entry
        self.update_fog()

    def build_team(self) -> List[Operative]:
        names = ["Vega", "Kline", "Mori", "Ash", "Rook", "Silva"]
        roles = ["Leader", "Scout", "Medic", "Breacher", "Sniper", "Tech"]
        team = []
        # spawn around entry room
        spawn_cells = []
        for _ in range(30):
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

        self.log.add(f"Operatives inserted: {', '.join([op.name + ' (' + op.role + ')' for op in team])}.")
        return team

    def build_anomaly(self, spawn: Tuple[int, int]) -> Anomaly:
        codes = ["SCP-███", "SCP-Δ13", "SCP-2470", "SCP-Ω9", "SCP-██-K"]
        code = random.choice(codes)

        threat = random.randint(8, 18)
        speed = random.randint(8, 18)
        stealth = random.randint(6, 18)
        aggression = random.randint(6, 18)
        resilience = random.randint(8, 18)

        return Anomaly(code, spawn[0], spawn[1], threat, speed, stealth, aggression, resilience)

    def update_fog(self):
        if not self.fog_enabled:
            for y in range(self.map_h):
                for x in range(self.map_w):
                    self.revealed[y][x] = True
            return

        # reveal within radius around each alive operative
        for op in self.operatives:
            if not op.alive:
                continue
            r = op.perception_radius()
            for yy in range(op.gy - r, op.gy + r + 1):
                for xx in range(op.gx - r, op.gx + r + 1):
                    if 0 <= xx < self.map_w and 0 <= yy < self.map_h:
                        if manhattan((op.gx, op.gy), (xx, yy)) <= r:
                            # line of sight-ish reveal
                            visible = True
                            for (lx, ly) in bresenham_line(op.gx, op.gy, xx, yy):
                                if (lx, ly) == (op.gx, op.gy) or (lx, ly) == (xx, yy):
                                    continue
                                if self.grid[ly][lx] == 1:
                                    visible = False
                                    break
                            if visible:
                                self.revealed[yy][xx] = True

    def find_far_unrevealed_from(self, start: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        # pick random unrevealed floors far away
        best = None
        best_score = -1
        for _ in range(250):
            x = random.randint(1, self.map_w - 2)
            y = random.randint(1, self.map_h - 2)
            if self.grid[y][x] == 0 and not self.revealed[y][x]:
                score = manhattan(start, (x, y))
                if score > best_score:
                    best_score = score
                    best = (x, y)
        return best

    def any_alive(self) -> bool:
        return any(op.alive for op in self.operatives)

    def update_phase_outcomes(self):
        # success condition: anomaly contained and at least one operative extracts to extraction room
        if self.phase in ("success", "failure"):
            return

        if self.elapsed >= self.deadline and self.phase != "success":
            self.phase = "failure"
            self.log.add("OPERATION FAILED: Time limit exceeded. Anomaly activity lost.")
            return

        if self.anomaly and not self.anomaly.contained:
            # anomaly escapes if it reaches map border-ish while unseen for a bit
            at_edge = self.anomaly.gx <= 1 or self.anomaly.gx >= self.map_w - 2 or self.anomaly.gy <= 1 or self.anomaly.gy >= self.map_h - 2
            if at_edge and self.anomaly.escape_timer > 10:
                self.phase = "failure"
                self.log.add("OPERATION FAILED: Anomaly escaped containment zone.")
                return

        if not self.any_alive():
            self.phase = "failure"
            self.log.add("OPERATION FAILED: All operatives lost.")
            return

        if self.anomaly and self.anomaly.contained:
            # if all surviving operatives reach extraction room area -> success
            ex = self.extraction
            survivors = [op for op in self.operatives if op.alive]
            if survivors and all(manhattan((op.gx, op.gy), ex) <= 3 for op in survivors):
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
            # select operative if clicked near
            for op in self.operatives:
                if not op.alive:
                    continue
                if manhattan((op.gx, op.gy), (gx, gy)) == 0:
                    self.selected = op
                    self.log.add(f"Selected: {op.name} ({op.role}).")
                    return

        if button == 3 and self.selected and self.selected.alive and self.is_floor((gx, gy)):
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

    def update(self, dt):
        if self.paused or self.phase in ("success", "failure"):
            return

        self.elapsed += dt

        # update operatives + anomaly
        for op in self.operatives:
            op.update(self, dt)

        if self.anomaly:
            self.anomaly.update(self, dt)

        # update fog after movement
        self.update_fog()

        # update phase outcomes
        self.update_phase_outcomes()

    # ==========================
    # Rendering
    # ==========================
    def draw_map(self):
        # colors
        floor = (28, 28, 34)
        wall = (12, 12, 16)
        fog = (0, 0, 0)

        for y in range(self.map_h):
            for x in range(self.map_w):
                rect = pygame.Rect(x * self.tile, y * self.tile, self.tile, self.tile)
                if self.fog_enabled and not self.revealed[y][x]:
                    pygame.draw.rect(self.screen, fog, rect)
                    continue

                if self.grid[y][x] == 1:
                    pygame.draw.rect(self.screen, wall, rect)
                else:
                    pygame.draw.rect(self.screen, floor, rect)

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

            # status color
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
                # visible if revealed and at least one operative sees it (rough)
                if (not self.fog_enabled or self.revealed[ay][ax]):
                    visible = any(op.alive and op.can_see(self, (ax, ay)) for op in self.operatives)

            if visible:
                cx = int((self.anomaly.px + 0.5) * self.tile)
                cy = int((self.anomaly.py + 0.5) * self.tile)
                r = self.tile // 3
                pts = [(cx, cy - r), (cx + r, cy + r), (cx - r, cy + r)]
                pygame.draw.polygon(self.screen, (220, 50, 50), pts)
                pygame.draw.polygon(self.screen, (0, 0, 0), pts, width=2)

    def draw_side_panel(self):
        x0 = self.map_w * self.tile
        pygame.draw.rect(self.screen, (18, 18, 22), pygame.Rect(x0, 0, self.panel_w, self.screen_h))
        pygame.draw.line(self.screen, (60, 60, 70), (x0, 0), (x0, self.screen_h), 2)

        y = 12
        y = draw_title_text(self.screen, "OPERATION VIEW", x0 + 14, y)

        # phase/time
        phase = self.phase.upper()
        t_left = max(0, int(self.deadline - self.elapsed))
        y = draw_body_text(self.screen, f"Phase: {phase}", x0 + 14, y)
        y = draw_body_text(self.screen, f"Time Left: {t_left}s", x0 + 14, y)

        # anomaly status
        if self.anomaly:
            a = self.anomaly
            status = "CONTAINED" if a.contained else "ACTIVE"
            y = draw_body_text(self.screen, f"Anomaly: {a.code} [{status}]", x0 + 14, y)
            y = draw_body_text(self.screen, f"Stability: {int(a.stability)} / 100", x0 + 14, y)
            y += 6

        # buttons
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

        # selected operative
        y = draw_header_text(self.screen, "Selected Operative", x0 + 14, y)
        if self.selected:
            op = self.selected
            y = draw_body_text(self.screen, f"{op.name} ({op.role})", x0 + 14, y)
            hp = max(0, int(op.hp))
            y = draw_body_text(self.screen, f"HP: {hp}/{op.hp_max}", x0 + 14, y)
            y = draw_body_text(self.screen, f"Panic: {int(op.panic)}", x0 + 14, y)
            y = draw_body_text(self.screen, f"Kit: {int(op.kit_integrity)}%", x0 + 14, y)
            y = draw_body_text(self.screen, f"State: {op.state}", x0 + 14, y)
            y += 6

            # attributes
            for k in ATTR_KEYS:
                v = op.attrs[k]
                col = get_attribute_color(v)
                label = f"{k.capitalize():<11} {v:>2}"
                y = draw_body_text(self.screen, label, x0 + 14, y, color=col)
        else:
            y = draw_body_text(self.screen, "None", x0 + 14, y)

        # log
        y += 10
        y = draw_header_text(self.screen, "Event Log", x0 + 14, y)
        log_top = y
        log_h = self.screen_h - log_top - 16
        log_rect = pygame.Rect(x0 + 14, log_top, self.panel_w - 28, log_h)
        pygame.draw.rect(self.screen, (12, 12, 16), log_rect, border_radius=6)
        pygame.draw.rect(self.screen, (70, 70, 80), log_rect, width=1, border_radius=6)

        # render last lines with scroll
        pad = 10
        lx = log_rect.x + pad
        ly = log_rect.y + pad
        max_lines = (log_rect.h - 2 * pad) // 18
        total = len(self.log.lines)

        start_index = max(0, total - max_lines - self.log.scroll)
        end_index = min(total, start_index + max_lines)

        for i in range(start_index, end_index):
            msg = self.log.lines[i]
            # clip long messages
            if len(msg) > 46:
                msg = msg[:46] + "…"
            text = FOOTER_FONT.render(msg, True, (200, 200, 200))
            self.screen.blit(text, (lx, ly))
            ly += 18

    def render(self):
        self.screen.fill((0, 0, 0))
        self.draw_map()
        self.draw_paths()
        self.draw_entities()
        self.draw_side_panel()

        # end banners
        if self.phase in ("success", "failure"):
            overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
            msg = "MISSION SUCCESS" if self.phase == "success" else "MISSION FAILED"
            text = TITLE_FONT.render(msg, True, (240, 240, 240))
            rect = text.get_rect(center=(self.screen_w // 2 - self.panel_w // 2, self.screen_h // 2))
            self.screen.blit(text, rect)

        pygame.display.flip()

    # ==========================
    # Main Loop
    # ==========================
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    map_rect = pygame.Rect(0, 0, self.map_w * self.tile, self.map_h * self.tile)

                    # mouse wheel: log scroll (button 4/5)
                    if event.button == 4:
                        self.log.scroll_by(3)
                    elif event.button == 5:
                        self.log.scroll_by(-3)
                    else:
                        if map_rect.collidepoint(mx, my):
                            self.handle_click_map(mx, my, event.button)
                        else:
                            # UI buttons
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
                        # clear manual target
                        if self.selected:
                            self.selected.manual_target = None
                            self.selected.path = []
                            self.log.add(f"{self.selected.name} manual orders cleared.")

            self.update(dt)
            self.render()


def main():
    pygame.init()
    random.seed()  # random operation each run
    sim = OperationSim(map_w=52, map_h=34, tile=20)
    sim.run()
    pygame.quit()


if __name__ == "__main__":
    main()
