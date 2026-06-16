import pygame

from arkanoid.rounds.base import (BaseRound,
                                  RED)
from arkanoid.rounds.round7 import Round7
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 6, 13 columns wide, taken directly from the
# supplied ``stage 6.txt`` reference file (11 rows of data). The
# first row of bricks lands at game y=4 (see ``_TOP_ROW_START``
# below) so the four rows above it (y=0, 1, 2, 3) are kept clear for
# the enemy spawn zone, matching the rest of the game.
#
# Each cell is either ``None`` (no brick) or a colour name. The
# colour name maps to the corresponding ``BrickColour`` enum value
# via ``_COLOUR_MAP`` further down.
#
# The structure of the level is two pairs of tall inner columns
# (red at x=3, x=9 and green at x=5, x=7) with shorter blue columns
# at x=1, x=11, plus two horizontal cross-connections: row 4 (game
# y=7) is a gold bridge with pink highlight bricks filling the gaps,
# and row 10 (game y=13) is the same gold bridge but with the outer
# blue columns swapped for pink highlight bricks.
LAYOUT = [
    # Row 1 (file Row 1, game y=4) - top of the tall columns.
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 2 (game y=5)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 3 (game y=6)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 4 (game y=7) - first horizontal cross-connection
    # (gold bridge with pink highlight bricks between the gold pieces).
    [None, 'blue', None, 'gold', 'pink', 'gold', 'pink', 'gold',
     'pink', 'gold', None, 'blue', None],
    # Row 5 (game y=8)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 6 (game y=9)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 7 (game y=10)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 8 (game y=11)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 9 (game y=12)
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
    # Row 10 (game y=13) - second horizontal cross-connection
    # (outer blue columns replaced with pink highlight bricks).
    [None, 'pink', None, 'gold', None, 'gold', None, 'gold', None,
     'gold', None, 'pink', None],
    # Row 11 (game y=14) - bottom of the tall columns.
    [None, 'blue', None, 'red', None, 'green', None, 'green', None,
     'red', None, 'blue', None],
]


# Maps the colour names used in LAYOUT to the BrickColour enum.
_COLOUR_MAP = {
    'blue': BrickColour.blue,
    'red': BrickColour.red,
    'green': BrickColour.green,
    'gold': BrickColour.gold,
    'pink': BrickColour.pink,
}


# Powerups for the level, keyed by (x, y) of the brick they fall
# from. The top and bottom blue columns (x=1, x=11) are the
# hardest to reach, so they hold the more situational powerups
# (Laser / Expand at the top, ExtraLife / SlowBall at the bottom).
# The two pink highlight bricks in the middle cross-connection
# row hold the catch / duplicate combo, since they're the easiest
# to reach from a centred paddle.
POWERUPS = {
    # Top blue columns (hardest to reach).
    (1, 4): LaserPowerUp,
    (11, 4): ExpandPowerUp,
    # Middle pink highlight bricks in the upper cross-connection.
    (4, 7): CatchPowerUp,
    (8, 7): DuplicatePowerUp,
    # Bottom blue columns (mirror of the top).
    (1, 14): ExtraLifePowerUp,
    (11, 14): SlowBallPowerUp,
}


class Round6(BaseRound):
    """Initialises the background, brick layout and powerups for round 6.

    The brick layout is taken directly from the supplied
    ``stage 6.txt`` reference file: 13 columns wide, 11 rows of
    data, with the first row of bricks at game y=4 (matching the
    top of round 3) so the four rows above remain clear for the
    enemy spawn zone. The structure is two pairs of tall inner
    columns (red at x=3, x=9 and green at x=5, x=7) flanked by
    shorter outer blue columns at x=1, x=11, joined by two
    horizontal cross-connections: a gold bridge with pink
    highlights halfway down (row 4 of the file, game y=7) and a
    second gold bridge with pink outer columns near the bottom
    (row 10 of the file, game y=13).
    """

    # Top of the brick grid. With the LAYOUT above the first row of
    # bricks lands at this y; the four rows above (y=0, 1, 2, 3)
    # remain clear for enemy spawn - the same pattern used by
    # round 3.
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        """Initialise round 6.

        Args:
            top_offset:
                The number of pixels from the top of the screen before
                the top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 6'
        self.next_round = Round7
        # Re-use the round 1 enemy type: ``cone`` is the first
        # enemy in the existing per-level rotation (see rounds 1-5)
        # and continues the "round 6 -> enemy from round 1, round 7
        # -> enemy from round 2, ..." pattern requested for the
        # later rounds.
        self.enemy_type = EnemyType.cone
        self.num_enemies = 3

    def can_release_enemies(self):
        """Release the enemies right at the start."""
        return True

    def _get_background_colour(self):
        return RED

    def _create_background(self):
        from arkanoid.rounds.background import create_circles_background
        return create_circles_background(self.screen, self.edges)

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Walks the 2D ``LAYOUT`` table above and creates one brick
        for every non-empty cell, with the optional powerup class
        looked up from ``POWERUPS``. Each brick is blitted onto the
        play area at the row/column position from the table, with
        ``_TOP_ROW_START`` added to the row index so the first row
        of bricks sits at game y=4.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        bricks = []
        for row_offset, row in enumerate(LAYOUT):
            y = self._TOP_ROW_START + row_offset
            for x, colour_name in enumerate(row):
                if colour_name is None:
                    continue
                colour = _COLOUR_MAP[colour_name]
                powerup_cls = POWERUPS.get((x, y))
                brick = Brick(colour, 6, powerup_cls=powerup_cls)
                bricks.append(self._blit_brick(brick, x, y))
        return pygame.sprite.Group(*bricks)
