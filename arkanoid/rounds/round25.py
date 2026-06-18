import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round26 import Round26
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    [None]*13, [None]*13, [None]*13, [None]*13,
    ['red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red', 'red'],
    ['green', 'green', 'green', 'green', 'green', 'green', 'green', 'green', 'green', 'green', 'green', 'green', 'green'],
    ['blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue'],
    ['gold', 'gold', 'gold', 'gold', 'gold', None, None, None, 'gold', 'gold', 'gold', 'gold', 'gold'],
    ['gold', 'red', 'red', 'red', 'gold', None, None, None, 'gold', 'blue', 'blue', 'blue', 'gold'],
    ['gold', 'red', 'red', 'red', 'gold', None, None, None, 'gold', 'blue', 'blue', 'blue', 'gold'],
    ['gold', None, None, None, None, None, None, None, None, None, None, None, 'gold'],
    ['gold', None, None, None, None, None, None, None, None, None, None, None, 'gold'],
    ['gold', None, None, None, 'gold', 'green', 'green', 'green', 'gold', None, None, None, 'gold'],
    ['gold', None, None, None, 'gold', 'green', 'green', 'green', 'gold', None, None, None, 'gold'],
    ['gold', 'silver', 'silver', 'silver', 'gold', 'gold', 'gold', 'gold', 'gold', 'silver', 'silver', 'silver', 'gold'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (0, 4): LaserPowerUp, (12, 4): ExpandPowerUp,
    (1, 8): CatchPowerUp, (9, 8): DuplicatePowerUp,
    (4, 12): ExtraLifePowerUp, (8, 12): SlowBallPowerUp,
}


class Round25(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 25'
        self.next_round = Round26
        self.enemy_type = EnemyType.cube
        self.num_enemies = 3

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_hex_background
        return create_hex_background(self.screen, self.edges)

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
