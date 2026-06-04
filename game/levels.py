"""Level definitions.

Each race track centre-line is generated from a smooth periodic curve so the
loop is guaranteed to close on itself without self-intersecting:

    r(theta) = R + sum( amp * sin(k*theta + phase) )
    x = r*cos(theta),  y = r*sin(theta)

Different harmonics give noticeably different circuit shapes (ovals, triangular
hairpins, flowing esses) while staying drivable.
"""

import math

from .track import Track, Arena


def _loop(R, harmonics, samples=120):
    pts = []
    for i in range(samples):
        th = 2 * math.pi * i / samples
        r = R
        for (k, amp, phase) in harmonics:
            r += amp * math.sin(k * th + phase)
        pts.append((math.cos(th) * r, math.sin(th) * r))
    return pts


# Each entry feeds Track(). "center" is in local units, scaled into the world.
# Tracks are large and open so there's plenty of room to drift; a radial
# r(theta) > 0 curve is always a simple, non-self-intersecting loop.
LEVELS = [
    {
        "name": "1. Coastal Oval",
        "center": _loop(390, [(2, 95, 0.0)]),
        "width": 300, "laps": 2, "par_time": 52.0, "seed": 11,
    },
    {
        "name": "2. Hairpin Heights",
        "center": _loop(420, [(3, 125, 0.4), (1, 60, 1.0)]),
        "width": 270, "laps": 2, "par_time": 72.0, "seed": 22,
    },
    {
        "name": "3. Serpentine",
        "center": _loop(440, [(5, 105, 0.0), (2, 80, 1.2)]),
        "width": 250, "laps": 2, "par_time": 88.0, "seed": 33,
    },
    {
        "name": "4. Twin Apex",
        "center": _loop(430, [(2, 180, 0.0), (3, 70, 1.4)]),
        "width": 280, "laps": 2, "par_time": 80.0, "seed": 55,
    },
    {
        "name": "5. Clover Leaf",
        "center": _loop(470, [(3, 180, 0.2), (6, 55, 1.0)]),
        "width": 250, "laps": 2, "par_time": 92.0, "seed": 66,
    },
    {
        "name": "6. Ribbon",
        "center": _loop(480, [(4, 110, 0.0), (2, 90, 2.4), (6, 45, 0.5)]),
        "width": 235, "laps": 2, "par_time": 98.0, "seed": 77,
    },
    {
        "name": "7. Grand Circuit",
        "center": _loop(500, [(4, 95, 0.6), (7, 60, 0.0), (2, 72, 2.0)]),
        "width": 240, "laps": 3, "par_time": 140.0, "seed": 44,
    },
    {
        "name": "8. Maelstrom",
        "center": _loop(540, [(5, 125, 0.3), (7, 55, 1.0), (2, 85, 1.8)]),
        "width": 230, "laps": 3, "par_time": 165.0, "seed": 88,
    },
]


def build_track(index):
    return Track(LEVELS[index])


def build_arena():
    return Arena()
