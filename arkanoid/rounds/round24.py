import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round25 import Round25
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, 'white', 'white', 'white', None, None, None, None, None],
    [None, None, None, None, None, 'white', 'white', 'white', None, None, None, None, None],
    [None, None, None, None, None, 'white', 'white', 'white', None, None, None, None, None],
    [None, None, None, None, 'white', 'white', 'white', 'white', 'white', None, None, None, None],
    [None, None, None, None, 'white', 'blue', 'white', 'blue', 'white', None, None, None, None],
    [None, None, None, 'white', 'blue', 'blue', 'white', 'blue', 'blue', 'white', None, None, None],
    [None, None, None, 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', None, None, None],
    [None, None, 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', None, None],
    [None, None, 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', None, None],
    [None, 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', None],
    ['blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (5, 7): LaserPowerUp, (7, 7): ExpandPowerUp,
    (6, 11): CatchPowerUp, (3, 13): DuplicatePowerUp,
    (0, 17): ExtraLifePowerUp, (12, 17): SlowBallPowerUp,
}


class Round24(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 24'
        self.next_round = Round25
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
