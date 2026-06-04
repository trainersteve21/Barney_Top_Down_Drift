"""All game screens (scenes) and the gameplay logic that ties the systems
together: main menu, level select, garage (upgrades + paint), the driving
scene with its pause overlay, and the results screen.

Each scene implements handle_event / update / draw. Scenes switch by calling
helper methods on the shared `app` object.
"""

import math
import random
import pygame
from pygame.math import Vector2

from . import config, assets, ui, shop, levels
from .car import Car
from .particles import SkidMarks, Smoke, Sparks
from .hud import HUD, _fmt_time


class Scene:
    def __init__(self, app):
        self.app = app

    def handle_event(self, event):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass


# ==========================================================================
# Main menu
# ==========================================================================
class MenuScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        cx = config.SCREEN_W // 2
        self.buttons = [
            ui.Button((cx - 150, 300, 300, 56), "RACE", 28, config.ACCENT,
                      config.DARKER),
            ui.Button((cx - 150, 368, 300, 56), "FREE DRIVE (ENDLESS)", 22),
            ui.Button((cx - 150, 436, 300, 56), "GARAGE", 26),
            ui.Button((cx - 150, 504, 300, 56), "QUIT", 26),
        ]
        self._bg = assets.vgradient(config.SCREEN_W, config.SCREEN_H,
                                    (28, 30, 40), (12, 13, 18))

    def handle_event(self, event):
        for b in self.buttons:
            if b.clicked(event):
                if b.label == "RACE":
                    self.app.go_level_select()
                elif b.label.startswith("FREE"):
                    self.app.go_play(None)
                elif b.label == "GARAGE":
                    self.app.go_garage()
                elif b.label == "QUIT":
                    self.app.running = False

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(mp)

    def draw(self, surface):
        surface.blit(self._bg, (0, 0))
        t = pygame.time.get_ticks() / 1000.0

        # rotating car preview behind the title
        colour = config.CAR_COLOURS[self.app.save["colour"]]
        sprite = assets.rotated_car(colour, t * 0.7)
        rect = sprite.get_rect(center=(config.SCREEN_W // 2, 200))
        surface.blit(sprite, rect)

        cx = config.SCREEN_W // 2
        assets.draw_text(surface, config.TITLE, 72, config.WHITE,
                         center=(cx, 110), bold=True)
        assets.draw_text(surface, "a top-down drifting simulator", 22,
                         config.ACCENT, center=(cx, 160))
        for b in self.buttons:
            b.draw(surface)
        assets.draw_text(surface,
                         f"Points: {self.app.save['points']:,}", 22,
                         config.GOLD, center=(cx, 596), bold=True)
        assets.draw_text(surface,
                         "WASD / Arrows to drive   -   SPACE handbrake   -   "
                         "SHIFT clutch   -   ESC pause",
                         16, config.GREY, center=(cx, 660))


# ==========================================================================
# Level select
# ==========================================================================
class LevelSelectScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.buttons = []
        cx = config.SCREEN_W // 2
        bw, bh, gap = 470, 84, 22
        cols = 2
        x0 = cx - (cols * bw + (cols - 1) * 40) // 2
        for i, lvl in enumerate(levels.LEVELS):
            col = i % cols
            row = i // cols
            x = x0 + col * (bw + 40)
            y = 160 + row * (bh + gap)
            self.buttons.append(ui.Button((x, y, bw, bh), lvl["name"], 26))
        self.back = ui.Button((40, 40, 120, 46), "BACK", 22)

    def handle_event(self, event):
        if self.back.clicked(event):
            self.app.go_menu()
        for i, b in enumerate(self.buttons):
            if b.clicked(event):
                self.app.go_play(i)

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.back.update(mp)
        for b in self.buttons:
            b.update(mp)

    def draw(self, surface):
        surface.fill(config.DARK)
        cx = config.SCREEN_W // 2
        assets.draw_text(surface, "SELECT A TRACK", 44, config.WHITE,
                         center=(cx, 90), bold=True)
        for i, b in enumerate(self.buttons):
            b.draw(surface)
            best = self.app.save["best_times"].get(str(i))
            label = ("best " + _fmt_time(best)) if best else "not set"
            col = config.GOLD if best else config.GREY
            assets.draw_text(surface, label, 18, col,
                             midright=(b.rect.right - 18, b.rect.centery))
            assets.draw_text(surface, f"{levels.LEVELS[i]['laps']} laps", 16,
                             config.GREY,
                             midleft=(b.rect.x + 16, b.rect.bottom - 12))
        self.back.draw(surface)


# ==========================================================================
# Garage: upgrades + paint
# ==========================================================================
class GarageScene(Scene):
    def __init__(self, app):
        super().__init__(app)
        self.back = ui.Button((40, 30, 120, 44), "BACK", 22)
        self.buy_buttons = []
        x = 470
        for i, up in enumerate(shop.UPGRADES):
            y = 150 + i * 78
            self.buy_buttons.append(
                (up, ui.Button((x + 560, y + 14, 120, 46), "BUY", 22,
                               config.GOOD, config.DARKER)))
        # colour swatch rects
        self.swatches = []
        names = list(config.CAR_COLOURS.keys())
        sx, sy = 70, 470
        for i, name in enumerate(names):
            r = pygame.Rect(sx + (i % 4) * 80, sy + (i // 4) * 80, 64, 64)
            self.swatches.append((name, r))

    def handle_event(self, event):
        if self.back.clicked(event):
            self.app.save_game()
            self.app.go_menu()
        for up, btn in self.buy_buttons:
            if btn.clicked(event):
                self._buy(up)
        for name, r in self.swatches:
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and r.collidepoint(event.pos)):
                self.app.save["colour"] = name
                self.app.save_game()

    def _buy(self, up):
        save = self.app.save
        level = int(save["upgrades"].get(up["key"], 0))
        cost = shop.cost_to_next(up, level)
        if cost is not None and save["points"] >= cost:
            save["points"] -= cost
            save["upgrades"][up["key"]] = level + 1
            self.app.save_game()

    def update(self, dt):
        mp = pygame.mouse.get_pos()
        self.back.update(mp)
        save = self.app.save
        for up, btn in self.buy_buttons:
            level = int(save["upgrades"].get(up["key"], 0))
            cost = shop.cost_to_next(up, level)
            btn.enabled = cost is not None and save["points"] >= cost
            btn.label = "MAX" if cost is None else f"{cost}"
            btn.update(mp)

    def draw(self, surface):
        surface.fill(config.DARK)
        save = self.app.save
        assets.draw_text(surface, "GARAGE", 44, config.WHITE,
                         center=(config.SCREEN_W // 2, 50), bold=True)
        assets.draw_text(surface, f"{save['points']:,} pts", 28, config.GOLD,
                         midright=(config.SCREEN_W - 50, 52), bold=True)
        self.back.draw(surface)

        self._draw_preview(surface)
        self._draw_upgrades(surface)
        self._draw_swatches(surface)

    def _draw_preview(self, surface):
        ui.panel(surface, (50, 110, 380, 320), border=config.PANEL_LIGHT)
        t = pygame.time.get_ticks() / 1000.0
        colour = config.CAR_COLOURS[self.app.save["colour"]]
        sprite = assets.rotated_car(colour, t * 0.6)
        rect = sprite.get_rect(center=(240, 230))
        surface.blit(sprite, rect)
        assets.draw_text(surface, "PAINT: " + self.app.save["colour"], 22,
                         config.WHITE, center=(240, 330), bold=True)
        assets.draw_text(surface, "Tap a swatch below to change colour", 14,
                         config.GREY, center=(240, 360))

    def _draw_upgrades(self, surface):
        save = self.app.save
        x = 470
        for up, btn in self.buy_buttons:
            y = btn.rect.y - 14
            row = pygame.Rect(x, y, 760, 66)
            ui.panel(surface, row, radius=10, fill=config.PANEL)
            level = int(save["upgrades"].get(up["key"], 0))
            assets.draw_text(surface, up["name"], 24, config.WHITE,
                             topleft=(row.x + 16, row.y + 8), bold=True)
            assets.draw_text(surface, up["desc"], 15, config.GREY,
                             topleft=(row.x + 16, row.y + 38))
            # level pips
            for p in range(up["levels"]):
                px = row.x + 470 + p * 18
                col = config.GOOD if p < level else (60, 64, 76)
                pygame.draw.rect(surface, col, (px, row.y + 12, 14, 14),
                                 border_radius=3)
            btn.draw(surface)

        # overall stat bars at the very bottom
        stats = shop.compute_stats(save["upgrades"])
        rt = shop.ratings(stats)
        bx = 50
        by = 638
        for i, (label, val) in enumerate(rt.items()):
            ui.stat_bar(surface, bx + (i % 2) * 380, by + (i // 2) * 26,
                        360, 16, val, label)

    def _draw_swatches(self, surface):
        assets.draw_text(surface, "PAINT", 22, config.ACCENT_2,
                         topleft=(70, 440), bold=True)
        for name, r in self.swatches:
            pygame.draw.rect(surface, config.CAR_COLOURS[name], r,
                             border_radius=8)
            if self.app.save["colour"] == name:
                pygame.draw.rect(surface, config.WHITE, r, 3, border_radius=8)
            else:
                pygame.draw.rect(surface, (60, 64, 76), r, 2, border_radius=8)


# ==========================================================================
# Driving
# ==========================================================================
class PlayScene(Scene):
    def __init__(self, app, level_index):
        super().__init__(app)
        self.level_index = level_index
        self.endless = level_index is None
        if self.endless:
            self.track = levels.build_arena()
        else:
            self.track = levels.build_track(level_index)

        stats = shop.compute_stats(app.save["upgrades"])
        colour = config.CAR_COLOURS[app.save["colour"]]
        self.car = Car(stats, colour)
        self.car.reset(self.track.start_pos, self.track.start_heading)

        self.skid = SkidMarks()
        self.smoke = Smoke()
        self.sparks = Sparks()
        self.hud = HUD()

        self.time = 0.0
        self.started = False           # timer starts on first throttle
        self.finished = False
        self.paused = False
        self.countdown = 3.0

        # lap / checkpoint state
        self.lap = 1
        self.next_gate = 1
        self.gate_count = len(getattr(self.track, "gate_indices", [])) or 1

        # scoring
        self.collisions = 0
        self.pickups_got = 0
        self.drift_score = 0.0
        self.combo = 1.0
        self._drift_timer = 0.0
        self._collide_cd = 0.0
        self.shake = 0.0
        self.cam = Vector2(self.track.start_pos)

        self.pause_buttons = self._make_pause_buttons()

    # ------------------------------------------------------------------
    def _make_pause_buttons(self):
        cx = config.SCREEN_W // 2
        return {
            "resume": ui.Button((cx - 130, 300, 260, 52), "RESUME", 24,
                                 config.ACCENT, config.DARKER),
            "restart": ui.Button((cx - 130, 364, 260, 52), "RESTART", 24),
            "garage": ui.Button((cx - 130, 428, 260, 52), "GARAGE", 24),
            "menu": ui.Button((cx - 130, 492, 260, 52),
                              "END & SAVE" if self.endless else "QUIT TO MENU",
                              24),
        }

    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in config.KEY_PAUSE:
                self.paused = not self.paused
                if self.paused:
                    self.app.audio.silence()
            elif event.key in config.KEY_MUTE:
                self.app.audio.toggle_mute()
            elif event.key in config.KEY_RESET and not self.paused:
                self._respawn()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hud.pause_rect.collidepoint(event.pos) and not self.finished:
                self.paused = not self.paused
                if self.paused:
                    self.app.audio.silence()

        if self.paused:
            for key, b in self.pause_buttons.items():
                if b.clicked(event):
                    if key == "resume":
                        self.paused = False
                    elif key == "restart":
                        self.app.go_play(self.level_index)
                    elif key == "garage":
                        self.app.go_garage()
                    elif key == "menu":
                        if self.endless:
                            self._end_endless()
                        else:
                            self.app.go_menu()

    # ------------------------------------------------------------------
    def _read_inputs(self):
        from .car import Inputs
        keys = pygame.key.get_pressed()
        inp = Inputs()
        inp.throttle = 1.0 if any(keys[k] for k in config.KEY_THROTTLE) else 0.0
        inp.brake = 1.0 if any(keys[k] for k in config.KEY_BRAKE) else 0.0
        steer = 0.0
        if any(keys[k] for k in config.KEY_LEFT):
            steer -= 1.0
        if any(keys[k] for k in config.KEY_RIGHT):
            steer += 1.0
        inp.steer = steer
        inp.handbrake = any(keys[k] for k in config.KEY_HANDBRAKE)
        inp.clutch = 1.0 if any(keys[k] for k in config.KEY_CLUTCH) else 0.0
        return inp

    # ------------------------------------------------------------------
    def update(self, dt):
        if self.paused or self.finished:
            mp = pygame.mouse.get_pos()
            if self.paused:
                for b in self.pause_buttons.values():
                    b.update(mp)
            return

        if self.countdown > 0:
            self.countdown -= dt
            # still let the camera settle, but no driving yet
            inp = self._read_inputs()
            inp.throttle = inp.brake = 0.0
            inp.steer = 0.0
        else:
            inp = self._read_inputs()
            if not self.started and (inp.throttle > 0 or self.endless):
                self.started = True

        self.car.update(dt, inp)
        impact = self.track.collide(self.car)
        self._handle_impact(impact)

        if self.started:
            self.time += dt

        self._update_drift(dt, inp)
        self._update_particles(dt, inp)
        self._update_pickups()
        if not self.endless:
            self._update_laps()
        self._update_camera(dt)

        self._collide_cd = max(0.0, self._collide_cd - dt)
        self.shake = max(0.0, self.shake - dt * 40)

        # engine note follows the rev counter; tyre screech follows the slide
        screech = self.car.slip if self.car.is_drifting else 0.0
        self.app.audio.pump(self.car.rpm, self.car.throttle_vis, screech)

    # ------------------------------------------------------------------
    def _handle_impact(self, impact):
        if impact > 60 and self._collide_cd == 0:
            self.collisions += 1
            self._collide_cd = 0.4
            self.shake = min(14, impact * 0.04)
            # spark burst roughly where the car is heading
            fwd = Vector2(math.cos(self.car.heading), math.sin(self.car.heading))
            p = self.car.pos + fwd * 22
            self.sparks.burst(p.x, p.y, (-fwd.x, -fwd.y), n=12)
            # crashing breaks the drift combo
            self.combo = 1.0

    # ------------------------------------------------------------------
    def _update_drift(self, dt, inp):
        if self.car.is_drifting:
            self._drift_timer = 0.0
            slip_factor = min(1.0, self.car.slip / 260.0)
            gain = slip_factor * self.car.speed * dt * 0.16
            self.drift_score += gain * self.combo
            self.combo = min(6.0, self.combo + dt * 0.7)
        else:
            self._drift_timer += dt
            if self._drift_timer > 0.5:
                self.combo = 1.0

    def _update_particles(self, dt, inp):
        if self.car.is_drifting or (inp.handbrake and self.car.speed > 40):
            intensity = min(1.0, self.car.slip / 220.0)
            for tp in self.car.tyre_world_points():
                self.skid.emit(tp.x, tp.y, intensity)
                self.smoke.emit(tp.x, tp.y, self.car.vel.x, self.car.vel.y,
                                intensity)
        self.smoke.update(dt)
        self.sparks.update(dt)

    def _update_pickups(self):
        for p in self.track.pickups:
            if not p.collected and (self.car.pos - p.pos).length() < 30:
                p.collected = True
                self.pickups_got += 1
                self.drift_score += 40  # coins feed the score pot

    def _update_laps(self):
        target = self.track.gate_pos(self.next_gate)
        radius = self.track.gate_radius() * 0.95
        if (self.car.pos - target).length() < radius:
            if self.next_gate == 0:
                # crossed the finish line
                self.lap += 1
                if self.lap > self.track.laps:
                    self._finish()
                    return
                self.next_gate = 1
            else:
                self.next_gate += 1
                if self.next_gate >= self.gate_count:
                    self.next_gate = 0

    def _update_camera(self, dt):
        look = self.car.vel * 0.18
        target = self.car.pos + look
        # smooth follow
        self.cam += (target - self.cam) * min(1.0, 8.0 * dt)

    # ------------------------------------------------------------------
    def _camera_offset(self):
        off_x = self.cam.x - config.SCREEN_W / 2
        off_y = self.cam.y - config.SCREEN_H / 2
        if self.shake > 0.5:
            off_x += random.uniform(-self.shake, self.shake)
            off_y += random.uniform(-self.shake, self.shake)
        return (off_x, off_y)

    # ------------------------------------------------------------------
    def _respawn(self):
        """Place the car back on the nearest bit of track, facing forwards."""
        if hasattr(self.track, "center"):
            best_i = min(range(len(self.track.center)),
                         key=lambda i: (self.car.pos
                                        - self.track.center[i]).length_squared())
            nxt = self.track.center[(best_i + 1) % len(self.track.center)]
            d = nxt - self.track.center[best_i]
            self.car.reset(self.track.center[best_i], math.atan2(d.y, d.x))
        else:
            self.car.reset(self.track.start_pos, self.track.start_heading)
        self.combo = 1.0

    # ------------------------------------------------------------------
    def _finish(self):
        self.finished = True
        save = self.app.save
        key = str(self.level_index)
        prev_best = save["best_times"].get(key)
        new_record = prev_best is None or self.time < prev_best
        if new_record:
            save["best_times"][key] = round(self.time, 2)

        par = self.track.par_time or 60.0
        breakdown = [
            ("Completion", 250),
            ("Time bonus", int(max(0, par - self.time) * 12)),
            ("Coins", self.pickups_got * 50),
            ("Drift score", int(self.drift_score * 0.5)),
            ("Collisions", -self.collisions * 40),
        ]
        if self.collisions == 0:
            breakdown.append(("Clean run!", 300))
        if new_record:
            breakdown.append(("New record!", 300))
        total = max(0, sum(v for _, v in breakdown))

        save["points"] += total
        save["total_points_earned"] += total
        self.app.save_game()
        self.app.go_results(ResultsData(
            title="LEVEL COMPLETE", time=self.time, best=save["best_times"][key],
            breakdown=breakdown, total=total, level_index=self.level_index,
            new_record=new_record))

    def _end_endless(self):
        save = self.app.save
        breakdown = [
            ("Drift score", int(self.drift_score * 0.5)),
            ("Survival", int(self.time * 2)),
        ]
        total = max(0, sum(v for _, v in breakdown))
        best_drift = max(save.get("best_drift", 0), int(self.drift_score))
        new_record = int(self.drift_score) >= best_drift and self.drift_score > 0
        save["best_drift"] = best_drift
        save["points"] += total
        save["total_points_earned"] += total
        self.app.save_game()
        self.app.go_results(ResultsData(
            title="DRIFT RUN OVER", time=self.time, best=None,
            breakdown=breakdown, total=total, level_index=None,
            new_record=new_record, extra=f"Best drift: {best_drift:,}"))

    # ------------------------------------------------------------------
    def draw(self, surface):
        cam = self._camera_offset()
        t = pygame.time.get_ticks() / 1000.0

        self.track.draw_background(surface, cam)
        self.skid.draw(surface, cam)
        self.track.draw_road(surface, cam)
        self.track.draw_pickups(surface, cam, t)
        self.smoke.draw(surface, cam)
        self.car.draw(surface, cam)
        self.sparks.draw(surface, cam)

        info = {
            "name": self.track.name,
            "time": self.time,
            "best": (self.app.save["best_times"].get(str(self.level_index))
                     if not self.endless else None),
            "lap": min(self.lap, getattr(self.track, "laps", 1) or 1),
            "laps": getattr(self.track, "laps", 1) or 1,
            "drift": self.drift_score,
            "combo": self.combo,
            "drifting": self.car.is_drifting,
            "points": self.app.save["points"],
            "endless": self.endless,
            "track": self.track,
            "car": self.car,
        }
        self.hud.draw(surface, self.car, info)

        if self.countdown > 0:
            self._draw_countdown(surface)
        if self.paused:
            self._draw_pause(surface)

    def _draw_countdown(self, surface):
        n = int(math.ceil(self.countdown))
        label = str(n) if n > 0 else "GO!"
        assets.draw_text(surface, label, 120, config.WHITE,
                         center=(config.SCREEN_W // 2, config.SCREEN_H // 2),
                         bold=True)

    def _draw_pause(self, surface):
        overlay = pygame.Surface((config.SCREEN_W, config.SCREEN_H),
                                 pygame.SRCALPHA)
        overlay.fill((10, 11, 15, 200))
        surface.blit(overlay, (0, 0))
        assets.draw_text(surface, "PAUSED", 56, config.WHITE,
                         center=(config.SCREEN_W // 2, 210), bold=True)
        for b in self.pause_buttons.values():
            b.draw(surface)


# ==========================================================================
# Results
# ==========================================================================
class ResultsData:
    def __init__(self, title, time, best, breakdown, total, level_index,
                 new_record, extra=None):
        self.title = title
        self.time = time
        self.best = best
        self.breakdown = breakdown
        self.total = total
        self.level_index = level_index
        self.new_record = new_record
        self.extra = extra


class ResultsScene(Scene):
    def __init__(self, app, data):
        super().__init__(app)
        self.data = data
        cx = config.SCREEN_W // 2
        self.buttons = []
        if data.level_index is not None:
            self.buttons.append(ui.Button((cx - 330, 600, 200, 52), "RETRY",
                                          24, config.ACCENT, config.DARKER))
            has_next = data.level_index + 1 < len(levels.LEVELS)
            nb = ui.Button((cx - 110, 600, 200, 52), "NEXT TRACK", 22)
            nb.enabled = has_next
            self.buttons.append(nb)
            self.buttons.append(ui.Button((cx + 130, 600, 200, 52), "GARAGE",
                                          24))
        else:
            self.buttons.append(ui.Button((cx - 220, 600, 200, 52),
                                          "DRIFT AGAIN", 22, config.ACCENT,
                                          config.DARKER))
            self.buttons.append(ui.Button((cx + 20, 600, 200, 52), "MENU", 24))
        self._anim = 0.0

    def handle_event(self, event):
        for b in self.buttons:
            if b.clicked(event):
                if b.label == "RETRY" or b.label == "DRIFT AGAIN":
                    self.app.go_play(self.data.level_index)
                elif b.label == "NEXT TRACK":
                    self.app.go_play(self.data.level_index + 1)
                elif b.label == "GARAGE":
                    self.app.go_garage()
                elif b.label == "MENU":
                    self.app.go_menu()

    def update(self, dt):
        self._anim = min(1.0, self._anim + dt * 1.5)
        mp = pygame.mouse.get_pos()
        for b in self.buttons:
            b.update(mp)

    def draw(self, surface):
        surface.fill(config.DARK)
        cx = config.SCREEN_W // 2
        assets.draw_text(surface, self.data.title, 52, config.WHITE,
                         center=(cx, 80), bold=True)
        if self.data.time is not None:
            assets.draw_text(surface, "Time  " + _fmt_time(self.data.time), 28,
                             config.ACCENT_2, center=(cx, 140))
        if self.data.best:
            assets.draw_text(surface, "Best  " + _fmt_time(self.data.best), 20,
                             config.GOLD, center=(cx, 174))
        if self.data.new_record:
            assets.draw_text(surface, "NEW RECORD!", 26, config.GOLD,
                             center=(cx, 206), bold=True)
        if self.data.extra:
            assets.draw_text(surface, self.data.extra, 22, config.GREY,
                             center=(cx, 206))

        # breakdown panel
        panel = pygame.Rect(cx - 260, 240, 520, 300)
        ui.panel(surface, panel, border=config.PANEL_LIGHT)
        y = panel.y + 26
        shown = int(len(self.data.breakdown) * self._anim) + 1
        for i, (label, val) in enumerate(self.data.breakdown[:shown]):
            col = config.GOOD if val >= 0 else config.BAD
            assets.draw_text(surface, label, 24, config.WHITE,
                             midleft=(panel.x + 30, y))
            assets.draw_text(surface, f"{val:+,}", 24, col,
                             midright=(panel.right - 30, y), bold=True)
            y += 40
        pygame.draw.line(surface, config.PANEL_LIGHT,
                         (panel.x + 20, panel.bottom - 56),
                         (panel.right - 20, panel.bottom - 56), 2)
        assets.draw_text(surface, "TOTAL", 28, config.WHITE,
                         midleft=(panel.x + 30, panel.bottom - 28), bold=True)
        assets.draw_text(surface, f"+{self.data.total:,} pts", 30, config.GOLD,
                         midright=(panel.right - 30, panel.bottom - 28),
                         bold=True)

        for b in self.buttons:
            b.draw(surface)
