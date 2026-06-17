import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round20 import Round20
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

# stage_19.txt — 5 empty rows trimmed, first brick at row 0.
LAYOUT = [
    [None, None, 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'gold', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'gold', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'gold', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'yellow', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'gold', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'gold', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'green', 'red', 'blue', 'pink', 'gold', 'pink', 'blue', 'red', 'green', None, None],
    [None, None, 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (2, 0): LaserPowerUp, (10, 0): ExpandPowerUp,
    (6, 1): CatchPowerUp, (6, 4): DuplicatePowerUp,
    (2, 8): ExtraLifePowerUp, (10, 8): SlowBallPowerUp,
}


class Round19(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 19'
        self.next_round = None
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
