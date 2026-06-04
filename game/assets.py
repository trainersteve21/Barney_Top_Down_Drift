"""Procedural assets: fonts, car sprites and small drawing helpers.

No files are loaded from disk. Car sprites are drawn once per paint colour and
cached, then rotated on demand. Fonts use pygame's built-in default font.
"""

import math
import pygame

from . import config

# --------------------------------------------------------------------------
# Fonts (cached by size).  Uses the bundled default font so nothing extra is
# needed on disk.
# --------------------------------------------------------------------------
_font_cache = {}


def font(size, bold=False):
    key = (size, bold)
    f = _font_cache.get(key)
    if f is None:
        try:
            f = pygame.font.SysFont("consolas,menlo,monospace", size, bold=bold)
        except Exception:
            f = None
        if f is None:
            # web / minimal environments may have no system fonts; the bundled
            # default font is always available.
            f = pygame.font.Font(None, int(size * 1.2))
        _font_cache[key] = f
    return f


_text_cache = {}


def text(string, size, colour, bold=False):
    """Render text to a surface (cached). Good for static labels."""
    key = (string, size, colour, bold)
    surf = _text_cache.get(key)
    if surf is None:
        surf = font(size, bold).render(string, True, colour)
        if len(_text_cache) > 800:
            _text_cache.clear()
        _text_cache[key] = surf
    return surf


def draw_text(surface, string, size, colour, center=None, topleft=None,
              midleft=None, midright=None, bold=False):
    surf = text(string, size, colour, bold)
    rect = surf.get_rect()
    if center is not None:
        rect.center = center
    elif topleft is not None:
        rect.topleft = topleft
    elif midleft is not None:
        rect.midleft = midleft
    elif midright is not None:
        rect.midright = midright
    surface.blit(surf, rect)
    return rect


# --------------------------------------------------------------------------
# Generic drawing helpers
# --------------------------------------------------------------------------
def round_rect(surface, rect, colour, radius=10, width=0):
    pygame.draw.rect(surface, colour, rect, width=width, border_radius=radius)


def vgradient(width, height, top, bottom):
    """Vertical gradient surface."""
    surf = pygame.Surface((width, height)).convert()
    for y in range(height):
        t = y / max(1, height - 1)
        col = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
        pygame.draw.line(surf, col, (0, y), (width, y))
    return surf


def _shade(colour, factor):
    return tuple(max(0, min(255, int(c * factor))) for c in colour)


# --------------------------------------------------------------------------
# Car sprite generation
# --------------------------------------------------------------------------
# The car is drawn pointing RIGHT (heading 0 == +x) so it lines up with the
# physics convention (cos/sin of heading).  Length runs along x, width along y.
CAR_LEN = 64
CAR_WID = 32

_car_cache = {}


def car_sprite(colour):
    """Return a cached top-down car sprite for the given paint colour."""
    key = tuple(colour)
    surf = _car_cache.get(key)
    if surf is not None:
        return surf

    pad = 8
    w = CAR_LEN + pad * 2
    h = CAR_WID + pad * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)

    body = pygame.Rect(pad, pad, CAR_LEN, CAR_WID)

    # soft drop shadow
    shadow = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 70), body.move(3, 4), border_radius=10)
    surf.blit(shadow, (0, 0))

    # wheels (dark) poking out slightly
    wheel = (24, 24, 28)
    for wx in (pad + 8, pad + CAR_LEN - 20):
        pygame.draw.rect(surf, wheel, (wx, pad - 4, 12, 6), border_radius=3)
        pygame.draw.rect(surf, wheel, (wx, pad + CAR_WID - 2, 12, 6),
                         border_radius=3)

    # main body
    pygame.draw.rect(surf, colour, body, border_radius=11)
    pygame.draw.rect(surf, _shade(colour, 1.18), body, width=2,
                     border_radius=11)

    # bonnet / colour shading stripe down the centre for a 3D feel
    hi = pygame.Rect(body.x + 4, body.y + 5, body.w - 8, body.h // 2 - 4)
    pygame.draw.rect(surf, _shade(colour, 1.12), hi, border_radius=8)

    # windscreen + rear window (tinted glass), nearer the front
    glass = (40, 48, 60)
    front_glass = pygame.Rect(body.x + CAR_LEN * 0.52, body.y + 5,
                              CAR_LEN * 0.18, CAR_WID - 10)
    rear_glass = pygame.Rect(body.x + CAR_LEN * 0.20, body.y + 5,
                             CAR_LEN * 0.16, CAR_WID - 10)
    pygame.draw.rect(surf, glass, front_glass, border_radius=4)
    pygame.draw.rect(surf, glass, rear_glass, border_radius=4)
    pygame.draw.rect(surf, (70, 84, 100), front_glass, width=1, border_radius=4)

    # cabin roof between the windows
    roof = pygame.Rect(rear_glass.right, body.y + 6,
                       front_glass.left - rear_glass.right, CAR_WID - 12)
    pygame.draw.rect(surf, _shade(colour, 0.82), roof, border_radius=3)

    # headlights (front = right) and tail lights (rear = left)
    pygame.draw.rect(surf, (255, 240, 190),
                     (body.right - 5, body.y + 4, 4, 6), border_radius=2)
    pygame.draw.rect(surf, (255, 240, 190),
                     (body.right - 5, body.bottom - 10, 4, 6), border_radius=2)
    pygame.draw.rect(surf, (220, 60, 50),
                     (body.x + 1, body.y + 4, 3, 6), border_radius=2)
    pygame.draw.rect(surf, (220, 60, 50),
                     (body.x + 1, body.bottom - 10, 3, 6), border_radius=2)

    surf = surf.convert_alpha()
    _car_cache[key] = surf
    return surf


def rotated_car(colour, heading_rad):
    """Return (surface, rect_offset) for a car rotated to the given heading.

    pygame rotates counter-clockwise for positive angles, and our screen y axis
    points down, so we negate the heading (in degrees) to match.
    """
    base = car_sprite(colour)
    deg = -math.degrees(heading_rad)
    return pygame.transform.rotozoom(base, deg, 1.0)
