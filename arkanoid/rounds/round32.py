import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round33 import Round33
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    [None]*13, [None]*13, [None]*13, [None]*13,
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', 'green', 'green', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', 'red', 'red', 'red', 'red', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, 'gold', None, 'gold', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, 'gold', 'pink', 'pink', 'pink', 'pink', 'pink', 'pink', 'pink', 'pink', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', None, None],
    [None, None, 'silver', 'silver', 'silver', 'silver', 'silver', 'silver', 'silver', 'silver', 'silver', None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (2, 0): LaserPowerUp, (10, 2): ExpandPowerUp,
    (5, 6): CatchPowerUp, (7, 6): DuplicatePowerUp,
    (4, 8): ExtraLifePowerUp, (9, 8): SlowBallPowerUp,
}


class Round32(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 32'
        self.next_round = Round33
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
