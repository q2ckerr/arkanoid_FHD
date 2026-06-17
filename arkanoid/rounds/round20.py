import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

# stage_20.txt — 5 empty rows trimmed, first brick at row 0.
LAYOUT = [
    ['gold', 'white', 'gold', 'orange', 'gold', 'teal', 'gold', 'green', 'gold', 'red', 'gold', 'blue', 'gold'],
    ['gold', 'pink', 'gold', 'silver', 'gold', 'silver', 'gold', 'silver', 'gold', 'silver', 'gold', 'yellow', 'gold'],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    ['gold', 'pink', 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold'],
    ['gold', None, 'gold', 'pink', 'gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold'],
    ['gold', None, 'gold', None, 'gold', 'pink', 'gold', None, 'gold', None, 'gold', None, 'gold'],
    ['gold', None, 'gold', None, 'gold', None, 'gold', 'pink', 'gold', None, 'gold', None, 'gold'],
    ['gold', None, 'gold', None, 'gold', None, 'gold', None, 'gold', 'pink', 'gold', None, 'gold'],
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', None, 'gold', 'pink', 'gold', None, None],
    [None, None, 'gold', None, 'gold', None, 'gold', 'pink', 'gold', None, 'gold', None, None],
    [None, None, 'gold', None, 'gold', 'pink', 'gold', None, 'gold', None, 'gold', None, None],
    [None, None, None, 'pink', 'gold', None, 'gold', None, 'gold', None, None, None, None],
    [None, 'pink', None, None, None, None, 'gold', None, None, None, None, None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (0, 0): LaserPowerUp, (12, 0): ExpandPowerUp,
    (3, 4): CatchPowerUp, (7, 6): DuplicatePowerUp,
    (0, 1): ExtraLifePowerUp, (12, 1): SlowBallPowerUp,
}


class Round20(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 20'
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
