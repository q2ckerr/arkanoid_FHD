import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round32 import Round32
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    [None]*13, [None]*13, [None]*13, [None]*13,
    ['green', None, 'red', None, 'blue', None, 'pink', None, 'yellow', None, 'white', None, 'orange'],
    ['silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver'],
    [None, 'blue', None, 'red', None, 'green', None, 'teal', None, 'orange', None, 'white', None],
    [None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None],
    ['teal', None, 'green', None, 'red', None, 'blue', None, 'pink', None, 'yellow', None, 'white'],
    ['silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver'],
    [None, 'pink', None, 'blue', None, 'red', None, 'green', None, 'teal', None, 'orange', None],
    [None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None],
    ['orange', None, 'teal', None, 'green', None, 'red', None, 'blue', None, 'pink', None, 'yellow'],
    ['silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver'],
    [None, 'yellow', None, 'pink', None, 'blue', None, 'red', None, 'green', None, 'teal', None],
    [None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None],
    ['white', None, 'orange', None, 'teal', None, 'green', None, 'red', None, 'blue', None, 'pink'],
    ['silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver', None, 'silver'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (0, 0): LaserPowerUp, (12, 0): ExpandPowerUp,
    (6, 2): CatchPowerUp, (6, 6): DuplicatePowerUp,
    (0, 4): ExtraLifePowerUp, (12, 4): SlowBallPowerUp,
}


class Round31(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 31'
        self.next_round = Round32
        self.enemy_type = EnemyType.pyramid
        self.num_enemies = 3

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_rects_background
        return create_rects_background(self.screen, self.edges)

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
