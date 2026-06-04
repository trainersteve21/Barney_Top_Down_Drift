# TOP-DOWN DRIFT

A top-down drifting / racing simulator built with **Python + pygame**, created
for the Computer Science coursework. All artwork and sound are generated in
code at runtime, so no external image, font or audio files are required.

## Run it

```bash
pip install pygame-ce numpy
python main.py
```

In VS Code you can just open `main.py` and press **Run**.
(`numpy` is only used for the engine sound — the game still runs without it.)

## Features

- **Drifting physics** — velocity is split into forward and sideways parts;
  grip bleeds off the slide, and the handbrake lets the back step out so you
  can drift. Smoke and tyre marks are left behind.
- **8 tracks** with walls you can't drive through, plus an endless **Drift
  Arena**. The map slides around the car, which stays centred.
- **Garage** — 6 upgrades (engine, turbo, tyres, suspension, brakes, weight)
  that each affect several stats, plus 8 paint colours.
- **Points system** — earned from your time, coins, clean runs and big drifts,
  then spent on upgrades. Best times and points are saved automatically.
- **Pixel-Car-Racer style GUI** — sweeping tacho & speedo dials, working
  clutch / brake / accelerator pedals, gear indicator, minimap and pause.
- **Synthesised engine sound** that revs with the RPM, plus tyre screech.

## Controls

| Key | Action | Key | Action |
|-----|--------|-----|--------|
| W / ↑ | accelerate | S / ↓ | brake / reverse |
| A / ← | steer left | D / → | steer right |
| Space | handbrake (drift) | Shift | clutch |
| R | respawn on track | M | mute / unmute |
| Esc / P | pause | | |

## Project layout

```
main.py            entry point
game/
  app.py           main loop + scene management
  config.py        tuning, colours, controls
  assets.py        procedural car sprites, fonts, drawing helpers
  car.py           drift physics + gearbox
  track.py         track geometry, walls, collision, drift arena
  levels.py        the 8 track definitions
  particles.py     smoke, skid marks, sparks
  hud.py           dials, pedals, minimap
  ui.py            buttons + widgets
  shop.py          upgrade definitions + stat maths
  scenes.py        menu, level select, garage, gameplay, results
  audio.py         synthesised engine + tyre sound
  save.py          JSON / browser save system
```
