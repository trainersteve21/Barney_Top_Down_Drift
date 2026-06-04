"""Car modification / upgrade system.

As described in the analysis, each upgrade mirrors a real car part and affects
*multiple* statistics at once, so there are genuine trade-offs (grippier tyres
add drag and shave a little top speed; a bigger engine adds weight). Upgrades
are bought with points earned by driving.

Each effect is a per-level multiplier applied `level` times to the base stat.
"""

from . import config

UPGRADES = [
    {
        "key": "engine",
        "name": "Engine",
        "desc": "Bigger engine: stronger acceleration, a little more weight.",
        "levels": 5,
        "cost": [220, 360, 560, 820, 1200],
        "effects": {"engine": 1.10, "top_speed": 1.02, "mass": 1.03},
    },
    {
        "key": "turbo",
        "name": "Turbo",
        "desc": "Forced induction: big top-speed gains, slight weight cost.",
        "levels": 5,
        "cost": [260, 420, 640, 900, 1300],
        "effects": {"top_speed": 1.08, "engine": 1.03, "mass": 1.015},
    },
    {
        "key": "tyres",
        "name": "Tyres",
        "desc": "Stickier rubber: much more grip & turn-in, tiny speed drag.",
        "levels": 5,
        "cost": [200, 340, 520, 760, 1100],
        "effects": {"grip": 1.10, "handling": 1.04, "top_speed": 0.99},
    },
    {
        "key": "suspension",
        "name": "Suspension",
        "desc": "Sharper handling and a slightly more planted rear end.",
        "levels": 5,
        "cost": [200, 330, 500, 740, 1080],
        "effects": {"handling": 1.09, "grip": 1.03},
    },
    {
        "key": "brakes",
        "name": "Brakes",
        "desc": "Big discs: shorter stopping distances into the corners.",
        "levels": 5,
        "cost": [160, 260, 400, 600, 900],
        "effects": {"braking": 1.12},
    },
    {
        "key": "weight",
        "name": "Weight Reduction",
        "desc": "Strip weight: better acceleration & handling everywhere.",
        "levels": 5,
        "cost": [240, 400, 620, 880, 1250],
        "effects": {"mass": 0.95, "top_speed": 0.995},
    },
]

UPGRADE_BY_KEY = {u["key"]: u for u in UPGRADES}


def cost_to_next(upgrade, current_level):
    """Point cost to buy the next level, or None if maxed."""
    if current_level >= upgrade["levels"]:
        return None
    return upgrade["cost"][current_level]


def compute_stats(upgrades):
    """Return a fresh stats dict from base stats + purchased upgrade levels."""
    stats = dict(config.BASE_STATS)
    for u in UPGRADES:
        level = int(upgrades.get(u["key"], 0))
        if level <= 0:
            continue
        for stat, mult in u["effects"].items():
            stats[stat] *= mult ** level
    return stats


def ratings(stats):
    """Map raw stats to friendly 0-100 bars for the garage display."""
    def norm(value, lo, hi):
        return max(2, min(100, int((value - lo) / (hi - lo) * 100)))
    return {
        "Speed": norm(stats["top_speed"], 480, 900),
        "Accel": norm(stats["engine"] / stats["mass"], 480, 1100),
        "Grip": norm(stats["grip"], 6.5, 13.0),
        "Handling": norm(stats["handling"], 2.6, 5.0),
        "Braking": norm(stats["braking"], 800, 1700),
    }
