"""Track geometry: builds a closed circuit from a centre-line, with walls you
cannot drive through, kerbs, a start/finish line, ordered checkpoints and
collectible pickups.

Walls are stored as line segments and collide against the car's circle, which
is far more robust (and smoother) than a grid of rectangles. The map is drawn
in world space and offset by the camera so the car can sit still in the centre
while the world slides around it.
"""

import math
import random
import pygame
from pygame.math import Vector2

from . import config

WALL_THICKNESS = 10


def _normals(center):
    """Average vertex normals for a closed poly-line of points."""
    n = len(center)
    norms = []
    for i in range(n):
        a = center[i]
        prv = center[(i - 1) % n]
        nxt = center[(i + 1) % n]
        d1 = (a - prv)
        d2 = (nxt - a)
        if d1.length() > 0:
            d1 = d1.normalize()
        if d2.length() > 0:
            d2 = d2.normalize()
        d = d1 + d2
        if d.length() == 0:
            d = d2 if d2.length() else Vector2(1, 0)
        d = d.normalize()
        norms.append(Vector2(-d.y, d.x))  # rotate 90 deg
    return norms


class Pickup:
    __slots__ = ("pos", "collected", "phase")

    def __init__(self, pos, phase):
        self.pos = pos
        self.collected = False
        self.phase = phase


class Track:
    def __init__(self, level):
        self.name = level["name"]
        self.half_width = level["width"] / 2.0
        self.laps = level.get("laps", 2)
        self.par_time = level.get("par_time", 60.0)

        # scale & translate the raw centre-line into world space
        scale = level.get("scale", 1.0)
        ox, oy = level.get("offset", (0, 0))
        self.center = [Vector2(px * scale + ox, py * scale + oy)
                       for px, py in level["center"]]

        norms = _normals(self.center)
        hw = self.half_width
        self.left = [self.center[i] + norms[i] * hw for i in range(len(norms))]
        self.right = [self.center[i] - norms[i] * hw for i in range(len(norms))]

        # wall segments (both boundaries, looped)
        self.walls = []
        n = len(self.center)
        for i in range(n):
            j = (i + 1) % n
            self.walls.append((self.left[i], self.left[j]))
            self.walls.append((self.right[i], self.right[j]))

        # ordered checkpoint gates (centre indices). gate 0 == start/finish.
        gate_count = max(4, n // 6)
        step = max(1, n // gate_count)
        self.gate_indices = list(range(0, n, step))
        if self.gate_indices[0] != 0:
            self.gate_indices.insert(0, 0)

        # pickups: a coin near a selection of centre points, nudged sideways
        self.pickups = []
        rng = random.Random(level.get("seed", 1))
        for i in range(2, n, max(2, n // 14)):
            off = norms[i] * rng.uniform(-hw * 0.5, hw * 0.5)
            self.pickups.append(Pickup(self.center[i] + off, rng.random() * 6))

        # starting pose: at gate 0 facing toward the next centre point
        self.start_pos = Vector2(self.center[0])
        d = (self.center[1] - self.center[0])
        self.start_heading = math.atan2(d.y, d.x)

        # cache a tiled grass background
        self._grass = self._make_grass()

        # world bounds (for the minimap)
        xs = [p.x for p in self.left + self.right]
        ys = [p.y for p in self.left + self.right]
        self.bounds = (min(xs), min(ys), max(xs), max(ys))

    # ------------------------------------------------------------------
    @staticmethod
    def _make_grass():
        tile = pygame.Surface((128, 128)).convert()
        tile.fill(config.GRASS)
        rng = random.Random(7)
        for _ in range(60):
            x = rng.randint(0, 127)
            y = rng.randint(0, 127)
            shade = rng.choice([config.GRASS_2, (32, 62, 40)])
            pygame.draw.circle(tile, shade, (x, y), rng.randint(2, 5))
        return tile

    # ------------------------------------------------------------------
    def draw_background(self, surface, camera):
        tw, th = self._grass.get_size()
        ox = -int(camera[0]) % tw
        oy = -int(camera[1]) % th
        for x in range(ox - tw, surface.get_width() + tw, tw):
            for y in range(oy - th, surface.get_height() + th, th):
                surface.blit(self._grass, (x, y))

    def draw_road(self, surface, camera):
        cx, cy = camera
        n = len(self.center)
        # asphalt quads
        for i in range(n):
            j = (i + 1) % n
            quad = [
                (self.left[i].x - cx, self.left[i].y - cy),
                (self.right[i].x - cx, self.right[i].y - cy),
                (self.right[j].x - cx, self.right[j].y - cy),
                (self.left[j].x - cx, self.left[j].y - cy),
            ]
            # cheap viewport cull
            if all(p[0] < -80 for p in quad) or all(p[0] > surface.get_width() + 80 for p in quad):
                continue
            if all(p[1] < -80 for p in quad) or all(p[1] > surface.get_height() + 80 for p in quad):
                continue
            col = config.ASPHALT if i % 2 == 0 else config.ASPHALT_2
            pygame.draw.polygon(surface, col, quad)

        self._draw_kerbs(surface, camera)
        self._draw_start_line(surface, camera)
        self._draw_walls(surface, camera)

    def _draw_kerbs(self, surface, camera):
        cx, cy = camera
        for boundary in (self.left, self.right):
            n = len(boundary)
            for i in range(n):
                j = (i + 1) % n
                col = config.KERB_A if i % 2 == 0 else config.KERB_B
                a = (boundary[i].x - cx, boundary[i].y - cy)
                b = (boundary[j].x - cx, boundary[j].y - cy)
                pygame.draw.line(surface, col, a, b, 6)

    def _draw_walls(self, surface, camera):
        cx, cy = camera
        w = surface.get_width()
        h = surface.get_height()
        for (a, b) in self.walls:
            ax, ay = a.x - cx, a.y - cy
            bx, by = b.x - cx, b.y - cy
            if (max(ax, bx) < -40 or min(ax, bx) > w + 40
                    or max(ay, by) < -40 or min(ay, by) > h + 40):
                continue
            pygame.draw.line(surface, config.WALL, (ax, ay), (bx, by),
                             WALL_THICKNESS)
            pygame.draw.line(surface, config.WALL_EDGE, (ax, ay), (bx, by), 2)

    def _draw_start_line(self, surface, camera):
        cx, cy = camera
        a = self.left[0]
        b = self.right[0]
        squares = 8
        for s in range(squares):
            t0 = s / squares
            t1 = (s + 1) / squares
            p0 = a.lerp(b, t0)
            p1 = a.lerp(b, t1)
            col = config.START_LINE if s % 2 == 0 else (40, 40, 46)
            mid = p0.lerp(p1, 0.5)
            pygame.draw.line(surface, col,
                             (p0.x - cx, p0.y - cy), (p1.x - cx, p1.y - cy), 10)

    def draw_pickups(self, surface, camera, t):
        cx, cy = camera
        for p in self.pickups:
            if p.collected:
                continue
            sx = p.pos.x - cx
            sy = p.pos.y - cy
            if not (-30 <= sx <= surface.get_width() + 30
                    and -30 <= sy <= surface.get_height() + 30):
                continue
            bob = math.sin(t * 3 + p.phase) * 3
            r = 9 + math.sin(t * 4 + p.phase) * 1.5
            cy2 = sy + bob
            pygame.draw.circle(surface, (180, 150, 40), (int(sx), int(cy2)),
                               int(r) + 2)
            pygame.draw.circle(surface, config.GOLD, (int(sx), int(cy2)),
                               int(r))
            pygame.draw.circle(surface, (255, 240, 180),
                               (int(sx - 2), int(cy2 - 2)), 3)

    # ------------------------------------------------------------------
    def collide(self, car):
        """Resolve car-vs-wall collisions. Returns the impact speed (px/s) if a
        collision happened this frame, else 0.0."""
        return resolve_walls(car, self.walls)

    # ------------------------------------------------------------------
    def gate_pos(self, gate_idx):
        i = self.gate_indices[gate_idx]
        return self.center[i]

    def gate_radius(self):
        return self.half_width


def _closest_point(p, a, b):
    ab = b - a
    length_sq = ab.length_squared()
    if length_sq == 0:
        return Vector2(a)
    t = max(0.0, min(1.0, (p - a).dot(ab) / length_sq))
    return a + ab * t


def resolve_walls(car, walls):
    """Shared circle-vs-segment collision resolution used by tracks & arena."""
    from .car import RADIUS
    r = RADIUS
    impact = 0.0
    px, py = car.pos.x, car.pos.y
    min_dist = r + WALL_THICKNESS / 2
    for (a, b) in walls:
        if (px < min(a.x, b.x) - min_dist or px > max(a.x, b.x) + min_dist):
            if (py < min(a.y, b.y) - min_dist or py > max(a.y, b.y) + min_dist):
                continue
        cp = _closest_point(car.pos, a, b)
        d = car.pos - cp
        dist = d.length()
        if dist < min_dist:
            if dist == 0:
                seg = (b - a)
                d = Vector2(-seg.y, seg.x)
                dist = d.length() or 1.0
            normal = d / dist
            car.pos += normal * (min_dist - dist)
            vn = car.vel.dot(normal)
            if vn < 0:
                impact = max(impact, -vn)
                car.vel -= normal * vn * 1.4
                car.vel *= 0.55
    return impact


class Arena:
    """An open square play-space for endless / free-drive drifting.

    Shares the same interface the Play scene relies on (draw_background,
    draw_road, draw_pickups, collide, start pose, bounds), but there are no
    laps -- you just drift for points until you choose to stop.
    """

    def __init__(self, size=2600):
        self.name = "Drift Arena"
        self.laps = None
        self.half_width = size / 2.0
        h = size / 2.0
        self.bounds = (-h, -h, h, h)
        self.start_pos = Vector2(0, 0)
        self.start_heading = 0.0
        self.par_time = None

        # outer boundary walls (a big box)
        c = [Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)]
        self.walls = [(c[i], c[(i + 1) % 4]) for i in range(4)]

        # a handful of pillar obstacles to drift around
        self.obstacles = []
        rng = random.Random(99)
        for _ in range(7):
            ox = rng.uniform(-h * 0.7, h * 0.7)
            oy = rng.uniform(-h * 0.7, h * 0.7)
            if math.hypot(ox, oy) < 350:
                continue
            half = rng.uniform(50, 110)
            r = pygame.Rect(ox - half, oy - half, half * 2, half * 2)
            self.obstacles.append(r)
            corners = [Vector2(r.left, r.top), Vector2(r.right, r.top),
                       Vector2(r.right, r.bottom), Vector2(r.left, r.bottom)]
            for i in range(4):
                self.walls.append((corners[i], corners[(i + 1) % 4]))

        self.pickups = []
        self._grass = Track._make_grass()

    def draw_background(self, surface, camera):
        Track.draw_background(self, surface, camera)

    def draw_road(self, surface, camera):
        cx, cy = camera
        h = self.half_width
        rect = pygame.Rect(-h - cx, -h - cy, h * 2, h * 2)
        pygame.draw.rect(surface, config.ASPHALT, rect)
        pygame.draw.rect(surface, config.WALL, rect, WALL_THICKNESS)
        pygame.draw.rect(surface, config.WALL_EDGE, rect, 2)
        for ob in self.obstacles:
            r = pygame.Rect(ob.x - cx, ob.y - cy, ob.w, ob.h)
            pygame.draw.rect(surface, config.WALL, r, border_radius=6)
            pygame.draw.rect(surface, config.WALL_EDGE, r, 3, border_radius=6)

    def draw_pickups(self, surface, camera, t):
        pass

    def collide(self, car):
        return resolve_walls(car, self.walls)
