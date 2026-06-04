"""Global configuration: window, colours, controls and tuning constants.

Everything that might want tweaking lives here so the rest of the code reads
cleanly. Colours are plain (r, g, b) tuples.
"""

import pygame

# --------------------------------------------------------------------------
# Window / timing
# --------------------------------------------------------------------------
SCREEN_W = 1280
SCREEN_H = 720
FPS = 60
TITLE = "TOP-DOWN DRIFT"

# --------------------------------------------------------------------------
# Colour palette
# --------------------------------------------------------------------------
BLACK = (0, 0, 0)
WHITE = (245, 245, 245)
GREY = (130, 130, 138)
DARK = (22, 24, 30)
DARKER = (14, 15, 19)
PANEL = (32, 35, 44)
PANEL_LIGHT = (46, 50, 62)
ACCENT = (255, 92, 66)        # warm orange-red used for highlights
ACCENT_2 = (66, 200, 255)     # cyan secondary highlight
GOOD = (96, 220, 120)
WARN = (255, 196, 64)
BAD = (240, 84, 84)
GOLD = (255, 206, 84)

# Track / world
GRASS = (38, 70, 46)
GRASS_2 = (44, 80, 52)
ASPHALT = (54, 56, 62)
ASPHALT_2 = (60, 62, 70)
KERB_A = (210, 70, 60)
KERB_B = (235, 235, 235)
WALL = (66, 70, 82)
WALL_EDGE = (200, 60, 60)
START_LINE = (240, 240, 240)

# Car paint options: name -> base colour. Sprites are generated per colour.
CAR_COLOURS = {
    "Crimson": (210, 52, 52),
    "Azure": (52, 120, 220),
    "Lime": (110, 200, 70),
    "Sunset": (240, 150, 50),
    "Violet": (150, 90, 210),
    "Gold": (224, 184, 70),
    "Snow": (228, 230, 236),
    "Carbon": (52, 56, 64),
}

# --------------------------------------------------------------------------
# Controls
# --------------------------------------------------------------------------
KEY_THROTTLE = (pygame.K_w, pygame.K_UP)
KEY_BRAKE = (pygame.K_s, pygame.K_DOWN)
KEY_LEFT = (pygame.K_a, pygame.K_LEFT)
KEY_RIGHT = (pygame.K_d, pygame.K_RIGHT)
KEY_HANDBRAKE = (pygame.K_SPACE,)
KEY_CLUTCH = (pygame.K_LSHIFT, pygame.K_RSHIFT)
KEY_PAUSE = (pygame.K_ESCAPE, pygame.K_p)
KEY_RESET = (pygame.K_r,)
KEY_MUTE = (pygame.K_m,)

# --------------------------------------------------------------------------
# Car physics base values (before upgrades).  Units are pixels / seconds.
# These are deliberately "arcade" rather than strictly realistic.
# --------------------------------------------------------------------------
BASE_STATS = {
    "engine": 620.0,     # forward acceleration force (px/s^2 at full throttle)
    "top_speed": 560.0,  # natural top speed (px/s)
    "grip": 7.2,         # how strongly lateral slip is killed (higher = grippy)
    "handling": 3.0,     # steering rate (radians/s at speed)
    "braking": 900.0,    # braking deceleration (px/s^2)
    "mass": 1.0,         # multiplier; higher mass = slower accel + more slide
}

HANDBRAKE_GRIP = 1.6     # grip while handbrake held (much slippier -> drift)
DRIFT_SLIP_THRESHOLD = 70.0   # lateral speed (px/s) above which we count a drift
DRIFT_MIN_SPEED = 80.0        # need some forward speed to count as drifting

# Save file (created automatically next to main.py)
SAVE_FILE = "savegame.json"
