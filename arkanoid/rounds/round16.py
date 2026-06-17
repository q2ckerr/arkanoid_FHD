import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round17 import Round17
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

# stage_16.txt — 3 empty rows trimmed, first brick at row 0.
LAYOUT = [
    [None, None, None, None, None, None, 'gold', None, None, None, None, None, None],
    [None, None, None, None, 'white', 'white', None, 'white', 'white', None, None, None, None],
    [None, None, 'white', 'white', None, None, 'gold', None, None, 'white', 'white', None, None],
    ['white', 'white', None, None, 'orange', 'orange', None, 'orange', 'orange', None, None, 'white', 'white'],
    [None, None, 'orange', 'orange', None, None, 'gold', None, None, 'orange', 'orange', None, None],
    ['orange', 'orange', None, None, 'yellow', 'yellow', None, 'yellow', 'yellow', None, None, 'orange', 'orange'],
    [None, None, 'yellow', 'yellow', None, None, 'gold', None, None, 'yellow', 'yellow', None, None],
    ['yellow', 'yellow', None, None, 'green', 'green', None, 'green', 'green', None, None, 'yellow', 'yellow'],
    [None, None, 'green', 'green', None, None, 'gold', None, None, 'green', 'green', None, None],
    ['green', 'green', None, None, 'red', 'red', None, 'red', 'red', None, None, 'green', 'green'],
    [None, None, 'red', 'red', None, None, 'gold', None, None, 'red', 'red', None, None],
    ['red', 'red', None, None, 'blue', 'blue', None, 'blue', 'blue', None, None, 'red', 'red'],
    [None, None, 'blue', 'blue', None, None, None, None, None, 'blue', 'blue', None, None],
    ['blue', 'blue', None, None, None, None, None, None, None, None, None, 'blue', 'blue'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (6, 0): LaserPowerUp, (6, 10): ExpandPowerUp,
    (0, 3): CatchPowerUp, (12, 3): DuplicatePowerUp,
    (0, 5): ExtraLifePowerUp, (12, 5): SlowBallPowerUp,
}


class Round16(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 16'
        self.next_round = None
        self.enemy_type = EnemyType.molecule
        self.num_enemies = 3

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_chevron_background
        return create_chevron_background(self.screen, self.edges)

    def _create_bricks(self):
        bricks = []
        for row_offset, row in enumerate(LAYOUT):
            y = self._TOP_ROW_START + row_offset
            for x, colour_name in enumerate(row):
                if colour_name is None:
                    continue
                colour = _COLOUR_MAP[colour_name]
                powerup_cls = POWERUPS.get((x, y))
                brick = Brick(colour, 9, powerup_cls=powerup_cls)
                bricks.append(self._blit_brick(brick, x, y))
        return pygame.sprite.Group(*bricks)
