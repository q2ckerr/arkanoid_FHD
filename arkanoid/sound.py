"""Sound effects manager for Arkanoid.

Loads all sound effects on first access and exposes simple play()
helpers. Sounds are loaded lazily so the game can start even if a
file is missing — a warning is logged instead of crashing.
"""

import logging
import os

import pygame

LOG = logging.getLogger(__name__)

_sound_dir = os.path.join(os.path.dirname(__file__), 'data', 'sound')

# Cache: filename -> pygame.mixer.Sound (or None on failure).
_cache = {}


def _load(name):
    """Return a pygame.mixer.Sound for *name*, loading once."""
    if name in _cache:
        return _cache[name]
    path = os.path.join(_sound_dir, name)
    try:
        sound = pygame.mixer.Sound(path)
        _cache[name] = sound
    except Exception:
        LOG.warning('Could not load sound: %s', path)
        _cache[name] = None
    return _cache[name]


def _play(name, volume=1.0):
    """Play *name* at *volume* (0.0–1.0), if available.

    Stops any currently-playing instance of the same sound first,
    so rapid re-triggers (e.g. ball hitting multiple blocks) don't
    overlap.
    """
    sound = _load(name)
    if sound is not None:
        sound.set_volume(volume)
        sound.stop()
        sound.play()


def play_block_hit():
    """Ball hits a normal brick (or second hit on silver)."""
    _play('block_touch.mp3')


def play_gold_block_hit():
    """Ball hits a gold brick or first hit on a silver brick."""
    _play('gold_block touch.mp3')


def play_paddle_hit():
    """Ball bounces off the paddle."""
    _play('paddle_touch.mp3')


def play_enemy_explode():
    """Enemy is destroyed."""
    _play('enemy_explode.mp3')


def play_powerup():
    """Powerup collected."""
    _play('extend powerup.mp3')


def play_laser():
    """Laser bullet fired."""
    _play('laser_shoot.mp3', volume=0.6)


def play_level_start():
    """New round begins."""
    _play('level_start.mp3')


def play_intro():
    """Start screen background music (loops forever)."""
    if pygame.mixer.music.get_busy():
        return
    path = os.path.join(_sound_dir, 'intro.mp3')
    try:
        pygame.mixer.music.load(path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
    except Exception:
        LOG.warning('Could not load music: %s', path)


def stop_music():
    """Stop any currently-playing music."""
    pygame.mixer.music.stop()


def play_boss_hit():
    """Boss brick hit by ball."""
    _play('boss_hit.mp3')


def play_extra_life():
    """Extra life gained."""
    _play('extra_life.mp3')
