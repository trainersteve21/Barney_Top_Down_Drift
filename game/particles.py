"""Smoke puffs and tyre skid marks left behind while drifting.

Both systems work in WORLD coordinates so they stay glued to the track while
the camera moves. Off-screen items are culled when drawing for performance,
and both collections are length-capped so the game stays smooth.
"""

import math
import random
from collections import deque

import pygame


class SkidMarks:
    """Dark tyre marks painted on the road while the car slips."""

    def __init__(self, max_points=1300):
        self.marks = deque(maxlen=max_points)  # each: [x, y, radius, grey]

    def emit(self, x, y, intensity):
        # intensity 0..1 -> darkness/size of the mark. We bake a grey shade in
        # rather than per-pixel alpha so marks can be drawn directly (fast on
        # the web build) instead of via a transparent surface each frame.
        r = int(3 + 1.6 * intensity)
        grey = max(20, int(54 - 26 * intensity))
        self.marks.append([x, y, r, (grey, grey, grey + 4)])

    def draw(self, surface, camera):
        cx, cy = camera
        w, h = surface.get_size()
        for m in self.marks:
            sx = m[0] - cx
            sy = m[1] - cy
            if -20 <= sx <= w + 20 and -20 <= sy <= h + 20:
                pygame.draw.circle(surface, m[3], (int(sx), int(sy)), m[2])


class Smoke:
    """Soft expanding smoke puffs from the tyres while drifting."""

    def __init__(self, max_particles=240):
        self.parts = deque(maxlen=max_particles)
        # each: [x, y, vx, vy, radius, life, max_life, base_grey]

    def emit(self, x, y, vx, vy, intensity):
        spread = 22
        self.parts.append([
            x + random.uniform(-4, 4),
            y + random.uniform(-4, 4),
            vx * 0.05 + random.uniform(-spread, spread),
            vy * 0.05 + random.uniform(-spread, spread),
            random.uniform(5, 9) + intensity * 6,
            0.0,
            random.uniform(0.5, 0.95),
            random.randint(150, 200),
        ])

    def update(self, dt):
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[2] *= 0.92
            p[3] *= 0.92
            p[4] += 26 * dt          # grow
            p[5] += dt               # age
        # drop dead particles from the left of the deque
        while self.parts and self.parts[0][5] >= self.parts[0][6]:
            self.parts.popleft()

    def draw(self, surface, camera):
        cx, cy = camera
        w, h = surface.get_size()
        for p in self.parts:
            life_t = 1.0 - (p[5] / p[6])
            if life_t <= 0:
                continue
            sx = p[0] - cx
            sy = p[1] - cy
            r = p[4]
            if -r <= sx <= w + r and -r <= sy <= h + r:
                alpha = int(150 * life_t)
                grey = p[7]
                surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (grey, grey, grey, alpha),
                                   (int(r), int(r)), int(r))
                surface.blit(surf, (sx - r, sy - r))


class Sparks:
    """Short-lived bright sparks emitted on a wall collision."""

    def __init__(self):
        self.parts = []  # [x, y, vx, vy, life]

    def burst(self, x, y, normal, n=10):
        ang0 = math.atan2(normal[1], normal[0])
        for _ in range(n):
            a = ang0 + random.uniform(-1.1, 1.1)
            sp = random.uniform(120, 320)
            self.parts.append([x, y, math.cos(a) * sp, math.sin(a) * sp,
                               random.uniform(0.18, 0.4)])

    def update(self, dt):
        for p in self.parts:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[3] += 240 * dt
            p[4] -= dt
        self.parts = [p for p in self.parts if p[4] > 0]

    def draw(self, surface, camera):
        cx, cy = camera
        for p in self.parts:
            sx = int(p[0] - cx)
            sy = int(p[1] - cy)
            t = max(0.0, min(1.0, p[4] / 0.4))
            col = (255, int(180 + 60 * t), int(60 * t))
            pygame.draw.circle(surface, col, (sx, sy), max(1, int(3 * t)))
