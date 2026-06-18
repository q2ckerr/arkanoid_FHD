import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round24 import Round24
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    ['teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal', 'teal'],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver'],
    [None, None, 'silver', 'green', 'silver', None, 'silver', 'green', 'silver', None, 'silver', 'green', 'silver'],
    [None, None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver'],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None],
    [None, 'silver', 'red', 'silver', None, 'silver', 'red', 'silver', None, 'silver', 'red', 'silver', None],
    [None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    ['silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, None],
    ['silver', 'blue', 'silver', None, 'silver', 'blue', 'silver', None, 'silver', 'blue', 'silver', None, None],
    ['silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, 'silver', 'silver', 'silver', None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (0, 0): LaserPowerUp, (12, 0): ExpandPowerUp,
    (7, 3): CatchPowerUp, (1, 7): DuplicatePowerUp,
    (0, 10): ExtraLifePowerUp, (5, 11): SlowBallPowerUp,
}


class Round23(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 23'
        self.next_round = Round24
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
