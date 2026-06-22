import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round11 import Round11
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 10, 13 columns wide, taken from ``stage 10.txt``.
# 18 rows (0-17).  Row 0 is flush against the top wall
# (``_TOP_ROW_START = 0``).
#
# The layout is a gold left-column border (x=1) with a diamond of
# blue/cyan/white/silver bricks in the centre, and a full gold bar
# across the bottom row.
LAYOUT = [
    # Row 0 – flush with top wall
    [None, 'gold', None, None, None, None, None, None, None, None, None, None, None],
    # Row 1
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    # Row 2
    [None, None, None, None, None, None, None, None, None, None, None, None, None],
    # Row 3
    [None, 'gold', None, None, None, None, None, None, None, None, None, None, None],
    # Row 4
    [None, 'gold', None, None, None, None, None, None, None, None, None, None, None],
    # Row 5
    [None, 'gold', None, None, None, None, None, 'blue', None, None, None, None, None],
    # Row 6
    [None, 'gold', None, None, None, None, 'blue', 'cyan', 'blue', None, None, None, None],
    # Row 7
    [None, 'gold', None, None, None, 'blue', 'cyan', 'white', 'cyan', 'blue', None, None, None],
    # Row 8
    [None, 'gold', None, None, 'blue', 'cyan', 'white', 'cyan', 'white', 'cyan', 'blue', None, None],
    # Row 9
    [None, 'gold', None, 'blue', 'cyan', 'white', 'cyan', 'silver', 'cyan', 'white', 'cyan', 'blue', None],
    # Row 10
    [None, 'gold', None, None, 'blue', 'cyan', 'white', 'cyan', 'white', 'cyan', 'blue', None, None],
    # Row 11
    [None, 'gold', None, None, None, 'blue', 'cyan', 'white', 'cyan', 'blue', None, None, None],
    # Row 12
    [None, 'gold', None, None, None, None, 'blue', 'cyan', 'blue', None, None, None, None],
    # Row 13
    [None, 'gold', None, None, None, None, None, 'blue', None, None, None, None, None],
    # Row 14
    [None, 'gold', None, None, None, None, None, None, None, None, None, None, None],
    # Row 15
    [None, 'gold', None, None, None, None, None, None, None, None, None, None, None],
    # Row 16
    [None, 'gold', None, None, None, None, None, None, None, None, None, None, None],
    # Row 17 – full gold bar
    [None, 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold', 'gold'],
]


# Maps colour names to BrickColour enum values.
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
# Spread across the diamond and the gold bar so the player has
# incentive to clear the whole formation.
POWERUPS = {
    # Diamond centre – easiest to reach.
    (7, 9): CatchPowerUp,
    (7, 7): DuplicatePowerUp,
    # Gold column – requires aimed shots.
    (1, 2): LaserPowerUp,
    (1, 5): ExpandPowerUp,
    # Gold bar at the bottom.
    (6, 17): ExtraLifePowerUp,
    (10, 17): SlowBallPowerUp,
}


class Round10(BaseRound):
    """Round 10: gold left border with a central diamond and gold bar.

    Bricks start flush against the top wall (``_TOP_ROW_START = 0``).
    Enemy type cycles back to ``cone`` (same as round 1).
    Background uses the circles pattern (same as round 2).
    """

    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 10'
        self.next_round = Round11
        self.enemy_type = EnemyType.cone
        self.num_enemies = 3

    def can_release_enemies(self):
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_circles_background
        return create_circles_background(self.screen, self.edges)

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
