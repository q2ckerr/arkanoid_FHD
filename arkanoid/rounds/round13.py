import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round14 import Round14
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 13, 13 columns wide, taken from ``stage 13.txt``.
# 8 rows (0-7).  First row at game y=4 (``_TOP_ROW_START = 4``)
# so four rows above remain clear for the enemy spawn zone.
#
# The layout is three vertical colour-block columns separated by
# empty gaps, with colours alternating between columns and rows.
LAYOUT = [
    # Row 0 (game y=4)
    [None, 'yellow', 'yellow', 'yellow', None, 'white', 'white',
     'white', None, 'yellow', 'yellow', 'yellow', None],
    # Row 1 (game y=5)
    [None, 'pink', 'pink', 'pink', None, 'orange', 'orange',
     'orange', None, 'pink', 'pink', 'pink', None],
    # Row 2 (game y=6)
    [None, 'blue', 'blue', 'blue', None, 'cyan', 'cyan', 'cyan',
     None, 'blue', 'blue', 'blue', None],
    # Row 3 (game y=7)
    [None, 'red', 'red', 'red', None, 'green', 'green', 'green',
     None, 'red', 'red', 'red', None],
    # Row 4 (game y=8)
    [None, 'green', 'green', 'green', None, 'red', 'red', 'red',
     None, 'green', 'green', 'green', None],
    # Row 5 (game y=9)
    [None, 'cyan', 'cyan', 'cyan', None, 'blue', 'blue', 'blue',
     None, 'cyan', 'cyan', 'cyan', None],
    # Row 6 (game y=10)
    [None, 'orange', 'orange', 'orange', None, 'pink', 'pink',
     'pink', None, 'orange', 'orange', 'orange', None],
    # Row 7 (game y=11)
    [None, 'white', 'white', 'white', None, 'yellow', 'yellow',
     'yellow', None, 'white', 'white', 'white', None],
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
    (2, 4): LaserPowerUp,
    (10, 4): ExpandPowerUp,
    (6, 5): CatchPowerUp,
    (2, 7): DuplicatePowerUp,
    (6, 9): ExtraLifePowerUp,
    (10, 11): SlowBallPowerUp,
}


class Round13(BaseRound):
    """Round 13: three vertical colour-block columns.

    First row at game y=4 so the enemy spawn zone above is clear.
    Enemy type: cube (next after molecule in the rotation).
    Background: hex (next after chevrons in the rotation).
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 13'
        self.next_round = Round14
        self.enemy_type = EnemyType.cube
        self.num_enemies = 3

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_hex_background
        return create_hex_background(self.screen, self.edges)

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
