import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round12 import Round12
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 11, 13 columns wide, taken from ``stage 11.txt``.
# 11 rows (0-10).  First row at game y=4 (``_TOP_ROW_START = 4``)
# so four rows above remain clear for the enemy spawn zone.
#
# The layout is two nested silver rectangles (a "castle" or "door"
# motif) with the centre left open.
LAYOUT = [
    # Row 0 (game y=4)
    [None, 'silver', 'silver', 'silver', 'silver', 'silver', 'silver',
     'silver', 'silver', 'silver', 'silver', 'silver', None],
    # Row 1 (game y=5)
    [None, 'silver', None, None, None, None, None, None, None, None,
     None, 'silver', None],
    # Row 2 (game y=6)
    [None, 'silver', None, 'silver', 'silver', 'silver', 'silver',
     'silver', 'silver', 'silver', None, 'silver', None],
    # Row 3 (game y=7)
    [None, 'silver', None, 'silver', None, None, None, None, None,
     'silver', None, 'silver', None],
    # Row 4 (game y=8)
    [None, 'silver', None, 'silver', None, 'silver', 'silver', 'silver',
     None, 'silver', None, 'silver', None],
    # Row 5 (game y=9)
    [None, 'silver', None, 'silver', None, 'silver', None, 'silver',
     None, 'silver', None, 'silver', None],
    # Row 6 (game y=10)
    [None, 'silver', None, 'silver', None, 'silver', 'silver', 'silver',
     None, 'silver', None, 'silver', None],
    # Row 7 (game y=11)
    [None, 'silver', None, 'silver', None, None, None, None, None,
     'silver', None, 'silver', None],
    # Row 8 (game y=12)
    [None, 'silver', None, 'silver', 'silver', 'silver', 'silver',
     'silver', 'silver', 'silver', None, 'silver', None],
    # Row 9 (game y=13)
    [None, 'silver', None, None, None, None, None, None, None, None,
     None, 'silver', None],
    # Row 10 (game y=14)
    [None, 'silver', 'silver', 'silver', 'silver', 'silver', 'silver',
     'silver', 'silver', 'silver', 'silver', 'silver', None],
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
}


# Powerups keyed by (column, game_y).
# Placed on the outer frame (harder to reach) and the inner ring.
POWERUPS = {
    # Top corners of outer frame.
    (1, 4): LaserPowerUp,
    (11, 4): ExpandPowerUp,
    # Inner rectangle.
    (6, 8): CatchPowerUp,
    (6, 10): DuplicatePowerUp,
    # Bottom corners.
    (1, 14): ExtraLifePowerUp,
    (11, 14): SlowBallPowerUp,
}


class Round11(BaseRound):
    """Round 11: nested silver rectangles.

    First row at game y=4 so the enemy spawn zone above is clear.
    Enemy type: pyramid (next after cone in the rotation).
    Background: rects (next after circles in the rotation).
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 11'
        self.next_round = Round12
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
