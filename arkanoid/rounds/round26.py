import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round27 import Round27
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    [None]*13, [None]*13, [None]*13, [None]*13,
    [None, None, 'gold', 'silver', 'silver', 'silver', 'gold', None, None, None, None, None, None],
    [None, 'gold', None, None, None, None, None, 'gold', None, None, None, None, None],
    ['gold', None, None, 'teal', 'teal', 'teal', None, None, 'gold', None, None, None, None],
    ['gold', None, 'green', 'green', 'green', 'green', 'green', None, 'gold', None, None, None, None],
    ['gold', None, 'blue', 'blue', 'blue', 'blue', 'blue', None, 'gold', None, None, None, None],
    ['gold', None, None, 'pink', 'pink', 'pink', None, None, 'gold', None, None, None, None],
    [None, 'gold', None, None, None, None, None, 'gold', None, None, None, None, None],
    [None, None, 'gold', 'gold', 'gold', 'gold', 'gold', None, None, None, None, None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (3, 0): LaserPowerUp, (5, 0): ExpandPowerUp,
    (2, 3): CatchPowerUp, (6, 3): DuplicatePowerUp,
    (0, 2): ExtraLifePowerUp, (8, 1): SlowBallPowerUp,
}


class Round26(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 26'
        self.next_round = Round27
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
