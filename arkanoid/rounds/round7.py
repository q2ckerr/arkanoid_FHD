import pygame

from arkanoid.rounds.base import (BaseRound,
                                  RED)
from arkanoid.rounds.round8 import Round8
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 7, 13 columns wide, taken from the supplied
# "stage 7.txt" reference file. The reference file is a centred
# diamond / oval: 3 bricks at the very top, 5 at the next two rows,
# 7 bricks across the wide middle, 5 at the next two rows, and 3
# at the very bottom.
#
# With ``_TOP_ROW_START = 4`` (set on the Round7 class below) the
# first row of bricks lands at game y=4, leaving the four rows
# above (y=0..3) clear for the enemy spawn zone - matching the
# rest of the game (round 3, round 6).
#
# Each cell is either None (no brick) or a colour name. The colour
# name maps to the corresponding BrickColour enum value via
# ``_COLOUR_MAP`` further down. The reference file's row labels
# start at "Row 0"; below they are translated to game y by adding
# ``_TOP_ROW_START``.
LAYOUT = [
    # Row 0 - верхушка ромба (game y=4)
    [None, None, None, None, None,
     'orange', 'cyan', 'blue', None, None, None, None, None],
    # Row 1 (game y=5)
    [None, None, None, None,
     'orange', 'green', 'blue', 'cyan', 'orange', None, None, None, None],
    # Row 2 (game y=6) - slightly left-shifted
    [None, None, None, None,
     'cyan', 'blue', 'green', 'orange', 'pink', None, None, None, None],
    # Row 3 (game y=7) - first of six full-width rows
    [None, None, None,
     'green', 'blue', 'cyan', 'orange', 'green', 'red', 'pink',
     None, None, None],
    # Row 4 (game y=8)
    [None, None, None,
     'blue', 'green', 'orange', 'pink', 'red', 'green', 'orange',
     None, None, None],
    # Row 5 (game y=9) - centre of the diamond
    [None, None, None,
     'cyan', 'orange', 'green', 'red', 'pink', 'orange', 'green',
     None, None, None],
    # Row 6 (game y=10)
    [None, None, None,
     'orange', 'pink', 'red', 'green', 'orange', 'cyan', 'blue',
     None, None, None],
    # Row 7 (game y=11)
    [None, None, None,
     'green', 'red', 'pink', 'orange', 'green', 'blue', 'cyan',
     None, None, None],
    # Row 8 (game y=12) - last of the full-width rows
    [None, None, None,
     'red', 'green', 'orange', 'cyan', 'blue', 'green', 'orange',
     None, None, None],
    # Row 9 (game y=13)
    [None, None, None, None,
     'orange', 'green', 'blue', 'cyan', 'orange', None, None, None, None],
    # Row 10 (game y=14) - left-shifted to mirror row 2
    [None, None, None, None,
     'cyan', 'blue', 'green', 'orange', 'pink', None, None, None, None],
    # Row 11 - низ ромба (game y=15)
    [None, None, None, None, None,
     'cyan', 'orange', 'green', None, None, None, None, None],
]


# Maps the colour names used in LAYOUT to the BrickColour enum.
_COLOUR_MAP = {
    'blue': BrickColour.blue,
    'cyan': BrickColour.cyan,
    'green': BrickColour.green,
    'orange': BrickColour.orange,
    'pink': BrickColour.pink,
    'red': BrickColour.red,
}


# Powerups for the level, keyed by (x, y) of the brick they fall
# from. The four "tips" of the diamond (top and bottom rows, plus
# the leftmost/rightmost bricks in the widest row) are the
# hardest to reach, so they hold the more situational powerups.
# The remaining two powerups go on the centre row, where they're
# the easiest to pick up.
POWERUPS = {
    # Top tip of the diamond.
    (5, 4): LaserPowerUp,
    (7, 4): ExpandPowerUp,
    # Centre row - easiest to reach.
    (4, 9): CatchPowerUp,
    (8, 9): DuplicatePowerUp,
    # Bottom tip of the diamond (mirror of the top).
    (5, 15): ExtraLifePowerUp,
    (7, 15): SlowBallPowerUp,
}


class Round7(BaseRound):
    """Initialises the background, brick layout and powerups for round 7.

    The brick layout is taken directly from the supplied
    ``stage 7.txt`` reference file: 13 columns wide, a centred
    diamond / oval (3 bricks at the top, growing to 7 in the wide
    middle, and shrinking back to 3 at the bottom) with the first
    row of bricks at game y=4 (matching round 3 and round 6) so
    the four rows above remain clear for the enemy spawn zone.

    On completion, round 7 chains into ``Round8`` (the layout
    from ``stage 8.txt``), which is the final round in the
    game. ``Round8.next_round`` is ``None``, so completing round
    8 will display the "you completed the game" flow via the
    ``RoundEndState``.
    """

    # Top of the brick grid. With the LAYOUT above the first row
    # of bricks lands at this y; the four rows above (y=0, 1, 2,
    # 3) remain clear for enemy spawn - the same pattern used by
    # round 3 and round 6.
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        """Initialise round 7.

        Args:
            top_offset:
                The number of pixels from the top of the screen before
                the top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 7'
        # Chain into round 8 on completion (see the module
        # docstring for the full progression).
        self.next_round = Round8
        # Re-use the round 2 enemy type: ``pyramid`` is the second
        # enemy in the existing per-level rotation (see rounds 1-5)
        # and continues the "round 6 -> enemy from round 1, round 7
        # -> enemy from round 2, round 8 -> enemy from round 3, ..."
        # pattern.
        self.enemy_type = EnemyType.pyramid
        self.num_enemies = 3

    def can_release_enemies(self):
        """Release the enemies right at the start."""
        return True

    def _get_background_colour(self):
        return RED

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
                brick = Brick(colour, 7, powerup_cls=powerup_cls)
                bricks.append(self._blit_brick(brick, x, y))
        return pygame.sprite.Group(*bricks)
