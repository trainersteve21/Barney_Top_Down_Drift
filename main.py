"""TOP-DOWN DRIFT  -  entry point.

A top-down drifting / racing simulator built with pygame, as described in the
Computer Science coursework analysis.

  * Drive, steer, brake and DRIFT a car with reactive arcade physics.
  * Race 8 procedurally-shaped tracks (with walls you can't pass through) or
    free-drive an endless drift arena.
  * The map slides around the car, which stays centred -- the illusion of
    driving.
  * Earn points from your time, coins, clean runs and big drifts, then spend
    them in the GARAGE on upgrades that each affect several car stats, plus a
    choice of paint colours.
  * A Pixel-Car-Racer style GUI: sweeping tacho & speedo dials, working
    clutch/brake/accelerator pedals, gear indicator, minimap and pause.
  * A synthesised engine note that revs with the RPM, plus tyre screech.

RUN ON YOUR COMPUTER
--------------------
1. Install the dependency (either works):
       pip install pygame-ce numpy
   (numpy is only needed for engine sound; the game still runs without it.)
2. Run this file:   python main.py
   In VS Code you can simply press the Run button on this file.

RUN IT IN A WEB BROWSER (optional)
----------------------------------
The main loop is async, so the game is also ready to compile to WebAssembly
with pygbag if you ever want to share a link (free static hosting works):
       pip install pygbag
       pygbag main.py            # test locally at http://localhost:8000
       pygbag --build main.py    # static site appears in  build/web

CONTROLS
--------
  W / Up .......... accelerate          S / Down ........ brake / reverse
  A / Left ........ steer left          D / Right ....... steer right
  Space ........... handbrake (drift)   Shift ........... clutch
  R ............... respawn on track    M ............... mute / unmute
  Esc / P ......... pause
"""

import asyncio
import sys


async def _amain():
    try:
        import pygame  # noqa: F401
    except ImportError:
        print("=" * 64)
        print("pygame is not installed.")
        print("Install it with:  pip install pygame-ce numpy")
        print("=" * 64)
        sys.exit(1)

    from game.app import main as run_game
    await run_game()


# asyncio.run is what pygbag hooks into for the web build, and it works
# perfectly well on the desktop too.
if __name__ == "__main__":
    asyncio.run(_amain())
