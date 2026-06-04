"""Reusable UI widgets: buttons and small panel helpers used by the menus."""

import pygame

from . import config, assets


class Button:
    def __init__(self, rect, label, font_size=26, colour=None, text_colour=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font_size = font_size
        self.colour = colour or config.PANEL_LIGHT
        self.text_colour = text_colour or config.WHITE
        self.hover = False
        self.enabled = True

    def update(self, mouse_pos):
        self.hover = self.enabled and self.rect.collidepoint(mouse_pos)

    def clicked(self, event):
        return (self.enabled and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1 and self.rect.collidepoint(event.pos))

    def draw(self, surface):
        if not self.enabled:
            base = (40, 42, 50)
            tcol = (90, 92, 100)
        elif self.hover:
            base = config.ACCENT
            tcol = config.DARKER
        else:
            base = self.colour
            tcol = self.text_colour
        shadow = self.rect.move(0, 4)
        assets.round_rect(surface, shadow, (0, 0, 0), radius=12)
        assets.round_rect(surface, self.rect, base, radius=12)
        if self.enabled and not self.hover:
            assets.round_rect(surface, self.rect, config.PANEL, radius=12,
                              width=2)
        assets.draw_text(surface, self.label, self.font_size, tcol,
                         center=self.rect.center, bold=True)


def panel(surface, rect, radius=16, fill=None, border=None):
    rect = pygame.Rect(rect)
    assets.round_rect(surface, rect, fill or config.PANEL, radius=radius)
    if border:
        assets.round_rect(surface, rect, border, radius=radius, width=2)
    return rect


def stat_bar(surface, x, y, w, h, value, label, colour=None):
    """Draw a labelled 0..100 stat bar."""
    colour = colour or config.ACCENT_2
    assets.draw_text(surface, label, 18, config.GREY, midleft=(x, y + h // 2))
    bx = x + 130
    bw = w - 130
    assets.round_rect(surface, (bx, y, bw, h), (24, 26, 32), radius=h // 2)
    fill_w = max(h, int(bw * value / 100))
    assets.round_rect(surface, (bx, y, fill_w, h), colour, radius=h // 2)
    assets.draw_text(surface, str(value), 16, config.WHITE,
                     midright=(bx + bw - 8, y + h // 2), bold=True)
