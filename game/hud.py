"""The in-game heads-up display: a Pixel-Car-Racer style tachometer and
speedometer with sweeping needles, three working pedals (clutch / brake /
accelerator) that depress as you drive, a gear indicator, lap & timer panel,
live drift score, points counter, a minimap and a pause button.
"""

import math
import pygame

from . import config, assets


def _dial(surface, center, radius, frac, label, value_str,
          redline_frac=None, accent=None):
    """Draw a circular gauge with a sweeping needle. frac in 0..1."""
    accent = accent or config.ACCENT
    cx, cy = center
    frac = max(0.0, min(1.0, frac))

    # face
    pygame.draw.circle(surface, (18, 19, 24), center, radius)
    pygame.draw.circle(surface, (60, 64, 76), center, radius, 3)
    pygame.draw.circle(surface, (30, 32, 40), center, int(radius * 0.82))

    start_deg = 135
    sweep = 270
    ticks = 10
    for i in range(ticks + 1):
        t = i / ticks
        ang = math.radians(start_deg + t * sweep)
        dx, dy = math.cos(ang), math.sin(ang)
        in_red = redline_frac is not None and t >= redline_frac
        col = config.BAD if in_red else (170, 175, 185)
        long_tick = (i % 1 == 0)
        r1 = radius * 0.82
        r2 = radius * (0.66 if long_tick else 0.74)
        pygame.draw.line(surface, col,
                         (cx + dx * r1, cy + dy * r1),
                         (cx + dx * r2, cy + dy * r2),
                         3 if long_tick else 2)

    # needle
    ang = math.radians(start_deg + frac * sweep)
    dx, dy = math.cos(ang), math.sin(ang)
    tip = (cx + dx * radius * 0.78, cy + dy * radius * 0.78)
    tail = (cx - dx * radius * 0.18, cy - dy * radius * 0.18)
    pygame.draw.line(surface, accent, tail, tip, 4)
    pygame.draw.circle(surface, accent, center, 7)
    pygame.draw.circle(surface, (20, 20, 24), center, 3)

    assets.draw_text(surface, label, 16, config.GREY,
                     center=(cx, cy + radius * 0.42), bold=True)
    assets.draw_text(surface, value_str, 30, config.WHITE,
                     center=(cx, cy - radius * 0.34), bold=True)


class HUD:
    def __init__(self):
        self.pause_rect = pygame.Rect(config.SCREEN_W - 64, 20, 44, 44)

    # ------------------------------------------------------------------
    def draw(self, surface, car, info):
        """info: dict with keys time, best, lap, laps, drift, combo, points,
        name, endless(bool)."""
        self._top_bar(surface, info)
        self._dials(surface, car)
        self._pedals(surface, car)
        self._minimap(surface, info)
        self._drift(surface, info)
        self._pause_button(surface)

    # ------------------------------------------------------------------
    def _top_bar(self, surface, info):
        # left panel: track + timer + lap
        panel = pygame.Rect(16, 16, 290, 92)
        s = pygame.Surface(panel.size, pygame.SRCALPHA)
        s.fill((20, 22, 28, 200))
        surface.blit(s, panel)
        assets.round_rect(surface, panel, config.PANEL, radius=12, width=2)

        assets.draw_text(surface, info["name"], 20, config.ACCENT_2,
                         topleft=(panel.x + 14, panel.y + 8), bold=True)
        assets.draw_text(surface, _fmt_time(info["time"]), 34, config.WHITE,
                         topleft=(panel.x + 14, panel.y + 32), bold=True)
        if info.get("endless"):
            assets.draw_text(surface, "ENDLESS", 18, config.GREY,
                             topleft=(panel.x + 180, panel.y + 44))
        else:
            assets.draw_text(surface,
                             f"LAP {info['lap']}/{info['laps']}", 20,
                             config.GREY,
                             topleft=(panel.x + 180, panel.y + 40), bold=True)
            best = info.get("best")
            if best:
                assets.draw_text(surface, f"best {_fmt_time(best)}", 15,
                                 config.GOLD,
                                 topleft=(panel.x + 180, panel.y + 66))

        # points (top-right, left of pause)
        pts = pygame.Rect(config.SCREEN_W - 250, 16, 170, 40)
        assets.round_rect(surface, pts, config.PANEL, radius=10)
        assets.round_rect(surface, pts, config.PANEL, radius=10, width=2)
        assets.draw_text(surface, f"{info['points']:,} pts", 22, config.GOLD,
                         center=pts.center, bold=True)

    # ------------------------------------------------------------------
    def _dials(self, surface, car):
        base_y = config.SCREEN_H - 96
        # tachometer
        tach_frac = car.rpm / car.redline
        _dial(surface, (110, base_y), 84, tach_frac, "RPM x1000",
              str(int(car.rpm / 1000)), redline_frac=0.86, accent=config.ACCENT)
        # gear box in the centre-bottom of the tach
        assets.draw_text(surface, f"G{car.gear + 1}", 22, config.GOOD,
                         center=(110, base_y + 18), bold=True)

        # speedometer
        spd_frac = car.speed_kmh / 200.0
        _dial(surface, (300, base_y), 84, spd_frac, "KM/H",
              str(int(car.speed_kmh)), accent=config.ACCENT_2)

    # ------------------------------------------------------------------
    def _pedals(self, surface, car):
        labels = [("C", car.clutch_vis, config.ACCENT_2),
                  ("B", car.brake_vis, config.BAD),
                  ("A", car.throttle_vis, config.GOOD)]
        pw, ph = 46, 96
        gap = 14
        total = len(labels) * pw + (len(labels) - 1) * gap
        x0 = config.SCREEN_W - total - 28
        y0 = config.SCREEN_H - ph - 28
        for i, (lab, depress, col) in enumerate(labels):
            x = x0 + i * (pw + gap)
            well = pygame.Rect(x, y0, pw, ph)
            assets.round_rect(surface, well, (24, 26, 32), radius=8)
            assets.round_rect(surface, well, (60, 64, 76), radius=8, width=2)
            travel = int((ph - 34) * depress)
            face = pygame.Rect(x + 5, y0 + 6 + travel, pw - 10, 28)
            face_col = col if depress > 0.05 else (70, 74, 86)
            assets.round_rect(surface, face, face_col, radius=6)
            assets.draw_text(surface, lab, 18, config.DARKER if depress > 0.05
                             else config.WHITE, center=face.center, bold=True)

    # ------------------------------------------------------------------
    def _minimap(self, surface, info):
        track = info.get("track")
        car = info.get("car")
        if track is None:
            return
        size = 150
        box = pygame.Rect(config.SCREEN_W - size - 28, 70, size, size)
        s = pygame.Surface(box.size, pygame.SRCALPHA)
        s.fill((16, 18, 22, 190))
        surface.blit(s, box)
        assets.round_rect(surface, box, config.PANEL, radius=10, width=2)

        minx, miny, maxx, maxy = track.bounds
        span = max(maxx - minx, maxy - miny) or 1
        pad = 14

        def to_map(p):
            mx = box.x + pad + (p.x - minx) / span * (size - 2 * pad)
            my = box.y + pad + (p.y - miny) / span * (size - 2 * pad)
            return (mx, my)

        if hasattr(track, "center"):
            pts = [to_map(p) for p in track.center]
            pygame.draw.polygon(surface, (90, 94, 108), pts, 3)
        else:
            # arena: outline box
            corners = [type("P", (), {"x": minx, "y": miny}),
                       type("P", (), {"x": maxx, "y": miny}),
                       type("P", (), {"x": maxx, "y": maxy}),
                       type("P", (), {"x": minx, "y": maxy})]
            pygame.draw.polygon(surface, (90, 94, 108),
                                [to_map(c) for c in corners], 3)
        if car is not None:
            pygame.draw.circle(surface, config.ACCENT,
                               [int(v) for v in to_map(car.pos)], 4)

    # ------------------------------------------------------------------
    def _drift(self, surface, info):
        if info.get("drifting") and info.get("combo", 0) > 0:
            cx = config.SCREEN_W // 2
            assets.draw_text(surface, f"{int(info['drift'])}", 44,
                             config.GOLD, center=(cx, 60), bold=True)
            assets.draw_text(surface, f"DRIFT  x{info['combo']:.1f}", 22,
                             config.ACCENT, center=(cx, 96), bold=True)

    # ------------------------------------------------------------------
    def _pause_button(self, surface):
        r = self.pause_rect
        assets.round_rect(surface, r, config.PANEL, radius=10)
        assets.round_rect(surface, r, config.PANEL_LIGHT, radius=10, width=2)
        bar_w = 6
        pygame.draw.rect(surface, config.WHITE,
                         (r.centerx - 9, r.y + 12, bar_w, r.h - 24),
                         border_radius=2)
        pygame.draw.rect(surface, config.WHITE,
                         (r.centerx + 3, r.y + 12, bar_w, r.h - 24),
                         border_radius=2)


def _fmt_time(t):
    if t is None:
        return "--:--"
    m = int(t // 60)
    s = t - m * 60
    return f"{m:02d}:{s:05.2f}"
