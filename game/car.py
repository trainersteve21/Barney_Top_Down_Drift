"""The drivable car: arcade drift physics, an auto gearbox and rendering.

Physics model (top-down, world space):
  * velocity is decomposed into a *forward* component (along the car heading)
    and a *lateral* component (sideways).
  * the engine pushes the forward component; braking pulls it toward zero.
  * lateral velocity is bled off by grip every frame -- high grip kills slides
    quickly (planted), low grip (or the handbrake) lets the back step out and
    the car drifts.
  * steering rotates the heading; because the velocity keeps its old direction
    for a moment, rotating the heading naturally produces oversteer / drift.

This gives a responsive, controllable arcade-drift feel that reacts to the
player's inputs, exactly as described in the analysis.
"""

import math
import pygame
from pygame.math import Vector2

from . import config, assets

RADIUS = 24  # collision radius (px)


class Inputs:
    """Lightweight container for a frame's control state."""

    __slots__ = ("throttle", "brake", "steer", "handbrake", "clutch")

    def __init__(self):
        self.throttle = 0.0   # 0..1
        self.brake = 0.0      # 0..1
        self.steer = 0.0      # -1 (left) .. +1 (right)
        self.handbrake = False
        self.clutch = 0.0     # 0..1


class Car:
    def __init__(self, stats, colour):
        self.stats = stats          # dict (already includes upgrades)
        self.colour = colour
        self.pos = Vector2(0, 0)
        self.vel = Vector2(0, 0)
        self.heading = 0.0          # radians, 0 == facing +x

        # gearbox / engine display values
        self.gear_ratios = [3.6, 2.4, 1.7, 1.3, 1.0, 0.82]
        self.final_drive = 14.2
        self.idle_rpm = 900
        self.redline = 7000
        self.gear = 0
        self.rpm = self.idle_rpm
        self._shift_cooldown = 0.0

        # telemetry exposed to HUD / scoring
        self.speed = 0.0            # px/s
        self.slip = 0.0             # |lateral speed| px/s
        self.is_drifting = False
        self.throttle_vis = 0.0     # smoothed pedal positions for the HUD
        self.brake_vis = 0.0
        self.clutch_vis = 0.0

    # ------------------------------------------------------------------
    def reset(self, pos, heading):
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.heading = heading
        self.gear = 0
        self.rpm = self.idle_rpm
        self.speed = 0.0
        self.slip = 0.0
        self.is_drifting = False

    # ------------------------------------------------------------------
    @property
    def speed_kmh(self):
        # purely cosmetic conversion for the speedometer dial
        return self.speed * 0.32

    # ------------------------------------------------------------------
    def update(self, dt, inp):
        s = self.stats
        fwd = Vector2(math.cos(self.heading), math.sin(self.heading))
        side = Vector2(-math.sin(self.heading), math.cos(self.heading))

        vf = self.vel.dot(fwd)
        vs = self.vel.dot(side)

        # --- engine drive (reduced by mass and the clutch) ---------------
        drive_throttle = inp.throttle * (1.0 - inp.clutch)
        accel = s["engine"] * drive_throttle / s["mass"]
        vf += accel * dt

        # --- braking ------------------------------------------------------
        if inp.brake > 0:
            if vf > 0:
                vf = max(0.0, vf - s["braking"] * inp.brake * dt)
            else:
                # already stopped / moving back -> drive in reverse (slowly)
                vf -= s["engine"] * 0.45 * inp.brake / s["mass"] * dt

        # --- drag / rolling resistance -> natural top speed --------------
        drag = 0.0016 + 0.0011  # quadratic-ish folded into a simple linear bleed
        vf -= vf * abs(vf) * 1.0 / (s["top_speed"] ** 2) * s["engine"] * dt
        vf -= vf * 0.6 * dt
        # hard clamp a touch above the rated top speed
        max_v = s["top_speed"] * 1.05
        vf = max(-max_v * 0.4, min(max_v, vf))

        # --- steering -----------------------------------------------------
        speed_now = math.hypot(vf, vs)
        # need some speed to turn; ramps in smoothly so parking feels natural
        turn_authority = min(1.0, speed_now / 90.0)
        direction = 1.0 if vf >= 0 else -1.0
        # tighten steering response a little as speed climbs for stability
        high_speed_damp = 1.0 - 0.35 * min(1.0, speed_now / max_v)
        self.heading += (inp.steer * s["handling"] * turn_authority
                         * direction * high_speed_damp * dt)

        # --- grip: bleed off lateral velocity ----------------------------
        grip = config.HANDBRAKE_GRIP if inp.handbrake else s["grip"]
        # heavier cars hold a slide longer
        grip /= (0.85 + 0.25 * s["mass"])
        retain = max(0.0, 1.0 - grip * dt)
        vs *= retain

        # --- recombine & integrate ---------------------------------------
        self.vel = fwd * vf + side * vs
        self.pos += self.vel * dt

        # --- telemetry & drift detection ---------------------------------
        self.speed = self.vel.length()
        self.slip = abs(vs)
        self.is_drifting = (self.slip > config.DRIFT_SLIP_THRESHOLD
                            and self.speed > config.DRIFT_MIN_SPEED)

        self._update_gearbox(dt, drive_throttle)
        self._update_pedal_visuals(dt, inp)

    # ------------------------------------------------------------------
    def _update_gearbox(self, dt, throttle):
        ratio = self.gear_ratios[self.gear]
        target_rpm = self.idle_rpm + abs(self.speed) * ratio * self.final_drive
        target_rpm = min(self.redline + 200, target_rpm)
        # smooth the needle
        self.rpm += (target_rpm - self.rpm) * min(1.0, 9.0 * dt)

        self._shift_cooldown = max(0.0, self._shift_cooldown - dt)
        if self._shift_cooldown == 0:
            if self.rpm > 6200 and self.gear < len(self.gear_ratios) - 1:
                self.gear += 1
                self._shift_cooldown = 0.35
            elif self.rpm < 2500 and self.gear > 0:
                self.gear -= 1
                self._shift_cooldown = 0.35

    def _update_pedal_visuals(self, dt, inp):
        k = min(1.0, 12.0 * dt)
        self.throttle_vis += (inp.throttle - self.throttle_vis) * k
        self.brake_vis += (inp.brake - self.brake_vis) * k
        self.clutch_vis += (inp.clutch - self.clutch_vis) * k

    # ------------------------------------------------------------------
    def tyre_world_points(self):
        """World positions of the two rear tyres (where smoke/marks spawn)."""
        fwd = Vector2(math.cos(self.heading), math.sin(self.heading))
        side = Vector2(-math.sin(self.heading), math.cos(self.heading))
        back = self.pos - fwd * (assets.CAR_LEN * 0.32)
        return (back + side * (assets.CAR_WID * 0.42),
                back - side * (assets.CAR_WID * 0.42))

    # ------------------------------------------------------------------
    def draw(self, surface, camera):
        sprite = assets.rotated_car(self.colour, self.heading)
        rect = sprite.get_rect()
        rect.center = (int(self.pos.x - camera[0]), int(self.pos.y - camera[1]))
        surface.blit(sprite, rect)
