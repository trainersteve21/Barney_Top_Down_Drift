"""Application shell: window setup, the main loop, and scene management.

The main loop is async so the exact same code runs on the desktop *and* in a
web browser via pygbag (which compiles pygame to WebAssembly). On the desktop
``await asyncio.sleep(0)`` is essentially free; in the browser it hands control
back so the page stays responsive.
"""

import asyncio
import pygame

from . import config, save
from . import scenes
from .audio import EngineSound


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.audio = EngineSound()   # synthesised engine + tyre sound
        self.save = save.load()
        self.scene = scenes.MenuScene(self)
        self._next_scene = None

    # ------------------------------------------------------------------
    # scene transitions (deferred to the end of the frame so we never swap a
    # scene out from under its own event handler)
    # ------------------------------------------------------------------
    def _transition(self, scene):
        self.audio.silence()
        self._next_scene = scene

    def go_menu(self):
        self._transition(scenes.MenuScene(self))

    def go_level_select(self):
        self._transition(scenes.LevelSelectScene(self))

    def go_garage(self):
        self._transition(scenes.GarageScene(self))

    def go_play(self, level_index):
        self._transition(scenes.PlayScene(self, level_index))

    def go_results(self, data):
        self._transition(scenes.ResultsScene(self, data))

    def save_game(self):
        save.save(self.save)

    # ------------------------------------------------------------------
    async def run(self):
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            dt = min(dt, 1 / 20)  # clamp big hitches so physics stays stable

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()

            if self._next_scene is not None:
                self.scene = self._next_scene
                self._next_scene = None

            await asyncio.sleep(0)

        self.save_game()
        pygame.quit()


async def main():
    await App().run()
