import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round13 import Round13
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 12, 13 columns wide, taken from ``stage 12.txt``.
# 14 rows (0-13).  First row at game y=4 (``_TOP_ROW_START = 4``)
# so four rows above remain clear for the enemy spawn zone.
#
# The layout is two gold frame rectangles (a larger outer one and a
# smaller inner one) with scattered coloured bricks inside.
LAYOUT = [
    # Row 0 (game y=4) – full gold top bar
    ['gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold',
     'gold', 'gold', 'gold', 'gold', 'gold', 'gold'],
    # Row 1 (game y=5)
    [None, None, None, None, 'gold', None, None, None, None, None,
     'gold', 'pink', None],
    # Row 2 (game y=6)
    [None, 'gold', 'white', None, 'gold', None, None, None, None, None,
     'gold', None, None],
    # Row 3 (game y=7)
    [None, 'gold', None, None, 'gold', None, None, 'gold', None, None,
     'gold', None, None],
    # Row 4 (game y=8)
    [None, 'gold', None, None, 'gold', 'green', None, 'gold', None, None,
     'gold', None, None],
    # Row 5 (game y=9)
    [None, 'gold', None, None, 'gold', None, None, 'gold', None, None,
     'gold', None, None],
    # Row 6 (game y=10)
    [None, 'gold', None, 'orange', 'gold', None, None, 'gold', None,
     'blue', 'gold', None, None],
    # Row 7 (game y=11)
    [None, 'gold', None, None, 'gold', None, None, 'gold', None, None,
     'gold', None, None],
    # Row 8 (game y=12)
    [None, 'gold', None, None, 'gold', None, None, 'gold', None, None,
     'gold', None, None],
    # Row 9 (game y=13)
    [None, 'gold', None, None, 'gold', None, 'red', 'gold', None, None,
     'gold', None, None],
    # Row 10 (game y=14)
    [None, 'gold', None, None, 'gold', None, None, 'gold', None, None,
     'gold', None, None],
    # Row 11 (game y=15)
    [None, 'gold', 'cyan', None, None, None, None, 'gold', None, None,
     None, None, None],
    # Row 12 (game y=16)
    [None, 'gold', None, None, None, None, None, 'gold', None, None,
     None, None, 'yellow'],
    # Row 13 (game y=17) – full gold bottom bar (leftmost removed for passability)
    [None, 'gold', 'gold', 'gold', 'gold', 'gold', 'gold',
     'gold', 'gold', 'gold', 'gold', 'gold', 'gold'],
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
    (4, 4): LaserPowerUp,
    (10, 4): ExpandPowerUp,
    (2, 6): CatchPowerUp,
    (8, 3): DuplicatePowerUp,
    (2, 13): ExtraLifePowerUp,
    (10, 13): SlowBallPowerUp,
}


class Round12(BaseRound):
    """Round 12: gold frames with scattered coloured bricks.

    First row at game y=4 so the enemy spawn zone above is clear.
    Enemy type: molecule (next after pyramid in the rotation).
    Background: chevrons (next after rects in the rotation).
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 12'
        self.next_round = Round13
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
