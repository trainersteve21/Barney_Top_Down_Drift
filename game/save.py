"""Tiny JSON save system. The file is created automatically on first run, so
no external files are needed to start playing.

Stores: the player's points (currency), purchased upgrade levels, chosen paint
colour, best lap/level times and the best endless drift score.

On the desktop this is a JSON file next to main.py. In the browser (pygbag /
Emscripten) there is no persistent disk, so we use the page's localStorage
instead, which keeps progress between visits.
"""

import json
import os
import sys

from . import config

DEFAULT = {
    "points": 0,
    "colour": "Crimson",
    "upgrades": {},          # category -> level (int)
    "best_times": {},        # str(level_index) -> seconds (float)
    "best_drift": 0,         # endless mode high score
    "total_points_earned": 0,
}

_WEB = sys.platform == "emscripten"
_LS_KEY = "topdowndrift_save"


def _path():
    return os.path.join(os.getcwd(), config.SAVE_FILE)


def _web_storage():
    """Return the browser localStorage object, or None if unavailable."""
    try:
        import platform
        return platform.window.localStorage
    except Exception:
        return None


def _read_raw():
    if _WEB:
        ls = _web_storage()
        if ls is not None:
            value = ls.getItem(_LS_KEY)
            return value if value else None
        return None
    try:
        with open(_path(), "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None


def _write_raw(text):
    if _WEB:
        ls = _web_storage()
        if ls is not None:
            ls.setItem(_LS_KEY, text)
        return
    try:
        with open(_path(), "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError:
        pass  # saving is a nicety; never crash the game over it


def load():
    data = dict(DEFAULT)
    raw = _read_raw()
    if raw:
        try:
            data.update(json.loads(raw))
        except ValueError:
            pass
    for key in ("upgrades", "best_times"):
        if not isinstance(data.get(key), dict):
            data[key] = {}
    return data


def save(data):
    try:
        _write_raw(json.dumps(data, indent=2))
    except Exception:
        pass
