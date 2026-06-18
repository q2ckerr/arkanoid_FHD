import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round23 import Round23
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    ['yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow'],
    ['yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow'],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    ['red', 'red', 'gold', None, 'gold', 'red', 'red', 'red', 'gold', None, 'gold', 'red', 'red'],
    ['red', 'red', 'gold', None, 'gold', 'red', 'red', 'red', 'gold', None, 'gold', 'red', 'red'],
    ['red', 'red', 'gold', None, 'gold', 'red', 'red', 'red', 'gold', None, 'gold', 'red', 'red'],
    ['red', 'red', 'gold', None, 'gold', 'red', 'red', 'red', 'gold', None, 'gold', 'red', 'red'],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    ['white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white'],
    ['white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white', 'white'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (0, 0): LaserPowerUp, (12, 0): ExpandPowerUp,
    (6, 3): CatchPowerUp, (6, 6): DuplicatePowerUp,
    (0, 8): ExtraLifePowerUp, (12, 8): SlowBallPowerUp,
}


class Round22(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 22'
        self.next_round = Round23
        self.enemy_type = EnemyType.cone
        self.num_enemies = 3

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_circles_background
        return create_circles_background(self.screen, self.edges)

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
