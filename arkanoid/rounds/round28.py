import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round29 import Round29
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

# stage_28.txt — 3 empty rows, first brick at row 3.
LAYOUT = [
    [None]*13, [None]*13, [None]*13,
    ['blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue'],
    ['blue', 'gold', 'gold', 'gold', 'gold', 'pink', 'gold', 'pink', 'gold', 'gold', 'gold', 'gold', 'blue'],
    ['blue', 'gold', None, None, None, None, None, None, None, None, None, 'gold', 'blue'],
    ['blue', 'gold', 'pink', None, None, None, None, None, None, None, 'pink', 'gold', 'blue'],
    ['blue', 'gold', 'pink', 'pink', None, None, None, None, None, 'pink', 'pink', 'gold', 'blue'],
    ['blue', 'gold', 'pink', 'pink', 'pink', None, None, None, 'pink', 'pink', 'pink', 'gold', 'blue'],
    [None, 'blue', 'gold', 'pink', 'pink', 'pink', None, 'pink', 'pink', 'pink', 'gold', 'blue', None],
    [None, None, 'blue', 'gold', 'pink', 'pink', 'pink', 'pink', 'pink', 'gold', 'blue', None, None],
    [None, None, None, 'blue', 'gold', 'pink', 'pink', 'pink', 'gold', 'blue', None, None, None],
    [None, None, None, None, 'blue', 'gold', 'pink', 'gold', 'blue', None, None, None, None],
    [None, None, None, None, None, 'blue', 'pink', 'blue', None, None, None, None, None],
    [None, None, None, None, None, None, 'blue', None, None, None, None, None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (5, 4): LaserPowerUp, (7, 4): ExpandPowerUp,
    (6, 9): CatchPowerUp, (6, 11): DuplicatePowerUp,
    (1, 5): ExtraLifePowerUp, (11, 5): SlowBallPowerUp,
}


class Round28(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 28'
        self.next_round = Round29
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
