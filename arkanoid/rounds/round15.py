import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round16 import Round16
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 15, 13 columns wide, taken from ``stage 15.txt``.
# 12 rows (0-11).  First row at game y=4 (``_TOP_ROW_START = 4``).
#
# A triangular / arrow-head pattern: cyan border with white and gold
# accents at the top, narrowing to a silver point at the bottom.
LAYOUT = [
    # Row 0 (game y=4)
    ['cyan', 'white', 'gold', 'cyan', 'cyan', 'cyan', 'cyan',
     'cyan', 'cyan', 'cyan', 'gold', 'white', 'cyan'],
    # Row 1 (game y=5)
    ['cyan', 'white', 'yellow', 'gold', 'cyan', 'cyan', 'cyan',
     'cyan', 'cyan', 'gold', 'green', 'white', 'cyan'],
    # Row 2 (game y=6)
    ['cyan', 'white', 'yellow', 'yellow', 'gold', 'cyan', 'cyan',
     'cyan', 'gold', 'green', 'green', 'white', 'cyan'],
    # Row 3 (game y=7)
    ['cyan', 'white', 'yellow', 'yellow', 'yellow', 'gold', 'white',
     'gold', 'green', 'green', 'green', 'white', 'cyan'],
    # Row 4 (game y=8)
    ['cyan', 'white', 'yellow', 'yellow', 'yellow', 'yellow', 'white',
     'green', 'green', 'green', 'green', 'white', 'cyan'],
    # Row 5 (game y=9)
    ['cyan', 'white', 'yellow', 'yellow', 'yellow', 'yellow', 'white',
     'green', 'green', 'green', 'green', 'white', 'cyan'],
    # Row 6 (game y=10)
    ['cyan', 'white', 'yellow', 'yellow', 'yellow', 'yellow', 'white',
     'green', 'green', 'green', 'green', 'white', 'cyan'],
    # Row 7 (game y=11)
    ['cyan', 'silver', 'yellow', 'yellow', 'yellow', 'yellow', 'white',
     'green', 'green', 'green', 'green', 'silver', 'cyan'],
    # Row 8 (game y=12)
    ['cyan', 'cyan', 'silver', 'yellow', 'yellow', 'yellow', 'white',
     'green', 'green', 'green', 'silver', 'cyan', 'cyan'],
    # Row 9 (game y=13)
    ['cyan', 'cyan', 'cyan', 'silver', 'yellow', 'yellow', 'white',
     'green', 'green', 'silver', 'cyan', 'cyan', 'cyan'],
    # Row 10 (game y=14)
    ['cyan', 'cyan', 'cyan', 'cyan', 'silver', 'yellow', 'white',
     'green', 'silver', 'cyan', 'cyan', 'cyan', 'cyan'],
    # Row 11 (game y=15)
    ['cyan', 'cyan', 'cyan', 'cyan', 'cyan', 'silver', 'white',
     'silver', 'cyan', 'cyan', 'cyan', 'cyan', 'cyan'],
]


_COLOUR_MAP = {
    'blue': BrickColour.blue,
    'cyan': BrickColour.cyan,
    'gold': BrickColour.gold,
    'green': BrickColour.green,
    'orange': BrickColour.orange,
    'pink': BrickColour.pink,
    'red': BrickColour.red,
    'silver': BrickColour.silver,
    'teal': BrickColour.cyan,
    'white': BrickColour.white,
    'yellow': BrickColour.yellow,
}


POWERUPS = {
    (2, 0): LaserPowerUp,
    (10, 0): ExpandPowerUp,
    (6, 3): CatchPowerUp,
    (2, 4): DuplicatePowerUp,
    (10, 4): ExtraLifePowerUp,
    (6, 11): SlowBallPowerUp,
}


class Round15(BaseRound):
    """Round 15: triangular arrow-head pattern.

    First row at game y=4 so the enemy spawn zone above is clear.
    Enemy type: pyramid (next after cone in the rotation).
    Background: rects (next after circles in the rotation).
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 15'
        self.next_round = Round16
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
