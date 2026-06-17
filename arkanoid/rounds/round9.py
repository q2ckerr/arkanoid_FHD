import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round10 import Round10
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 9, 13 columns wide, taken from the supplied
# ``stage 9.txt`` reference file (11 rows of data).  The first row
# of bricks lands at game y=4 (``_TOP_ROW_START``) so the four rows
# above (y=0..3) remain clear for the enemy spawn zone.
#
# Each cell is either ``None`` (no brick) or a colour name.  The
# colour name maps to the corresponding ``BrickColour`` enum value
# via ``_COLOUR_MAP``.  ``teal`` from the reference is mapped to
# ``cyan`` (the closest available BrickColour).
#
# The structure is two symmetric gold clusters at the top (rows 0-3)
# and a central rectangular block (rows 5-10) with pink and orange
# borders and a green/teal interior, separated by an empty row 4.
LAYOUT = [
    # Row 0 (game y=4) - top of the gold clusters.
    [None, None, 'gold', None, 'gold', None, None, None,
     'gold', None, 'gold', None, None],
    # Row 1 (game y=5)
    [None, None, 'gold', 'green', 'gold', None, None, None,
     'gold', 'green', 'gold', None, None],
    # Row 2 (game y=6)
    [None, None, 'gold', 'blue', 'gold', None, None, None,
     'gold', 'blue', 'gold', None, None],
    # Row 3 (game y=7)
    [None, None, 'gold', 'gold', 'gold', None, None, None,
     'gold', 'gold', 'gold', None, None],
    # Row 4 (game y=8) - empty gap.
    [None, None, None, None, None, None, None, None,
     None, None, None, None, None],
    # Row 5 (game y=9) - top of the central block.
    [None, None, None, None, 'pink', 'blue', 'blue', 'blue',
     'orange', None, None, None, None],
    # Row 6 (game y=10)
    [None, None, None, None, 'pink', 'green', 'teal', 'green',
     'orange', None, None, None, None],
    # Row 7 (game y=11)
    [None, None, None, None, 'pink', 'teal', 'green', 'teal',
     'orange', None, None, None, None],
    # Row 8 (game y=12)
    [None, None, None, None, 'pink', 'green', 'teal', 'green',
     'orange', None, None, None, None],
    # Row 9 (game y=13)
    [None, None, None, None, 'pink', 'teal', 'green', 'teal',
     'orange', None, None, None, None],
    # Row 10 (game y=14) - bottom of the central block.
    [None, None, None, None, 'pink', 'blue', 'blue', 'blue',
     'orange', None, None, None, None],
]


# Maps the colour names used in LAYOUT to the BrickColour enum.
_COLOUR_MAP = {
    'blue': BrickColour.blue,
    'cyan': BrickColour.cyan,
    'gold': BrickColour.gold,
    'green': BrickColour.green,
    'orange': BrickColour.orange,
    'pink': BrickColour.pink,
    'red': BrickColour.red,
    'teal': BrickColour.cyan,
}


# Powerups for the level, keyed by (x, y) of the brick they fall
# from.  The four gold corners of the top clusters (x=2, x=10 on
# rows 0 and 3) are the hardest to reach, so they hold the more
# situational powerups.  The centre of the lower block is easiest
# to reach and holds the catch/duplicate combo.
POWERUPS = {
    # Top gold clusters (hardest to reach).
    (2, 4): LaserPowerUp,
    (10, 4): ExpandPowerUp,
    # Central block — easiest to reach.
    (6, 9): CatchPowerUp,
    (6, 11): DuplicatePowerUp,
    # Bottom of the central block (mirror).
    (2, 14): ExtraLifePowerUp,
    (10, 14): SlowBallPowerUp,
}


class Round9(BaseRound):
    """Initialises the background, brick layout and powerups for round 9.

    The brick layout is taken from the supplied ``stage 9.txt``
    reference file: 13 columns wide, 11 rows of data, with the first
    row of bricks at game y=4 so the four rows above remain clear
    for the enemy spawn zone.

    On completion advances to round 10.
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 9'
        self.next_round = Round10
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
