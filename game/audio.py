"""Procedurally synthesised engine + tyre-screech sound.

No audio files are used. The engine note is generated in real time as a stream
of short, phase-continuous chunks whose pitch tracks the RPM, so the sound
glides smoothly as the engine revs. Tyre screech is a looping filtered-noise
bed whose volume follows how much the car is sliding.

Everything is wrapped in try/except: if numpy or an audio device is missing
(or audio simply isn't allowed yet in a browser) the game carries on silently.
"""

import math
import pygame


class EngineSound:
    def __init__(self):
        self.ok = False
        self.muted = False
        self.np = None
        try:
            import numpy as np
            self.np = np
        except Exception:
            return
        try:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(frequency=22050, size=-16, channels=2,
                              buffer=1024)
        except Exception:
            return
        init = pygame.mixer.get_init()
        if not init:
            return
        self.sr = init[0]
        self.out_channels = init[2]
        try:
            pygame.mixer.set_num_channels(8)
            self.engine_ch = pygame.mixer.Channel(5)
            self.skid_ch = pygame.mixer.Channel(6)
        except Exception:
            return

        self.rng = np.random.default_rng(7)
        self.phase = 0.0
        self.chunk = 0.05  # seconds per generated engine chunk

        try:
            self._skid = self._make_skid_loop()
            self.skid_ch.play(self._skid, loops=-1)
            self.skid_ch.set_volume(0.0)
        except Exception:
            return
        self.ok = True

    # ------------------------------------------------------------------
    def _to_sound(self, mono):
        np = self.np
        data = (np.clip(mono, -1.0, 1.0) * 30000).astype(np.int16)
        if self.out_channels == 2:
            data = np.repeat(data.reshape(-1, 1), 2, axis=1)
        return pygame.sndarray.make_sound(np.ascontiguousarray(data))

    def _make_skid_loop(self):
        np = self.np
        n = int(self.sr * 0.5)
        noise = self.rng.uniform(-1.0, 1.0, n)
        # crude low-pass so it sounds like a screech rather than white hiss
        k = 6
        noise = np.convolve(noise, np.ones(k) / k, mode="same")
        # taper the ends so the loop point is seamless
        fade = np.linspace(0, 1, n // 20)
        noise[:fade.size] *= fade
        noise[-fade.size:] *= fade[::-1]
        return self._to_sound(noise * 0.5)

    def _engine_chunk(self, rpm, throttle):
        np = self.np
        n = int(self.sr * self.chunk)
        freq = 30.0 + (rpm / 7000.0) * 150.0   # fundamental in Hz
        inc = 2 * math.pi * freq / self.sr
        phases = self.phase + inc * np.arange(1, n + 1)
        self.phase = float(phases[-1] % (2 * math.pi))
        wave = (0.60 * np.sin(phases)
                + 0.30 * np.sin(2 * phases)
                + 0.18 * np.sin(3 * phases)
                + 0.10 * np.sin(4 * phases + 0.5))
        wave += (0.05 + 0.10 * throttle) * self.rng.uniform(-1.0, 1.0, n)
        amp = 0.14 + 0.42 * throttle + 0.10 * (rpm / 7000.0)
        return self._to_sound(wave * amp)

    # ------------------------------------------------------------------
    def pump(self, rpm, throttle, slip):
        """Call once per frame while driving."""
        if not self.ok or self.muted:
            return
        try:
            if self.engine_ch.get_queue() is None:
                snd = self._engine_chunk(rpm, throttle)
                if self.engine_ch.get_busy():
                    self.engine_ch.queue(snd)
                else:
                    self.engine_ch.play(snd)
            self.skid_ch.set_volume(max(0.0, min(0.7, slip / 320.0)))
        except Exception:
            self.ok = False

    def silence(self):
        if not self.ok:
            return
        try:
            self.engine_ch.stop()
            self.skid_ch.set_volume(0.0)
            self.phase = 0.0
        except Exception:
            pass

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.silence()
