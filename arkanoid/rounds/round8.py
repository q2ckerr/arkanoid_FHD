import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round9 import Round9
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 8, 13 columns wide, taken directly from the
# supplied ``stage 8.txt`` reference file (11 rows of data). The
# reference file is a vertically-symmetric emblem / hourglass: two
# diamond-shaped gold clusters at the very top and bottom, joined by
# a single central column at x=6 of mixed-colour highlight bricks
# (pink, green, orange, blue, red, green, orange).
#
# With ``_TOP_ROW_START = 4`` (set on the Round8 class below) the
# first row of bricks lands at game y=4, leaving the four rows
# above (y=0..3) clear for the enemy spawn zone - matching the rest
# of the game (round 3, round 6, round 7).
#
# Each cell is either ``None`` (no brick) or a colour name. The
# colour name maps to the corresponding ``BrickColour`` enum value
# via ``_COLOUR_MAP`` further down. The reference file's row labels
# start at "Row 0"; below they are translated to game y by adding
# ``_TOP_ROW_START``.
LAYOUT = [
    # Row 0 (game y=4) - top of the upper diamond cluster.
    [None, None, 'gold', None, None, 'gold', None, 'gold', None,
     None, 'gold', None, None],
    # Row 1 (game y=5) - second row of the upper cluster.
    [None, None, 'gold', 'gold', None, None, None, None, None,
     'gold', 'gold', None, None],
    # Row 2 (game y=6) - single pink highlight brick, the apex of
    # the central column.
    [None, None, None, None, None, None, 'pink', None, None,
     None, None, None, None],
    # Row 3 (game y=7) - first three-brick row of the central
    # cluster (gold / green / gold).
    [None, None, None, None, None, 'gold', 'green', 'gold', None,
     None, None, None, None],
    # Row 4 (game y=8) - the outer gold shoulders of the central
    # cluster and the upper orange highlight.
    [None, None, None, 'gold', None, None, 'orange', None, None,
     'gold', None, None, None],
    # Row 5 (game y=9) - the single blue highlight brick, the
    # visual centre of the level.
    [None, None, None, None, None, None, 'blue', None, None,
     None, None, None, None],
    # Row 6 (game y=10) - mirror of row 4 with the red highlight
    # instead of orange.
    [None, None, None, 'gold', None, None, 'red', None, None,
     'gold', None, None, None],
    # Row 7 (game y=11) - mirror of row 3 (gold / green / gold).
    [None, None, None, None, None, 'gold', 'green', 'gold', None,
     None, None, None, None],
    # Row 8 (game y=12) - mirror of row 2, with the lower orange
    # highlight.
    [None, None, None, None, None, None, 'orange', None, None,
     None, None, None, None],
    # Row 9 (game y=13) - mirror of row 1, the second row of the
    # lower diamond cluster.
    [None, None, 'gold', 'gold', None, None, None, None, None,
     'gold', 'gold', None, None],
    # Row 10 (game y=14) - mirror of row 0, the bottom of the
    # lower diamond cluster.
    [None, None, 'gold', None, None, 'gold', None, 'gold', None,
     None, 'gold', None, None],
]


# Maps the colour names used in LAYOUT to the BrickColour enum.
_COLOUR_MAP = {
    'blue': BrickColour.blue,
    'gold': BrickColour.gold,
    'green': BrickColour.green,
    'orange': BrickColour.orange,
    'pink': BrickColour.pink,
    'red': BrickColour.red,
}


# Powerups for the level, keyed by (x, y) of the brick they fall
# from. The four outer gold corners of the upper and lower diamond
# clusters (x=2 and x=10 on rows 0 and 10) are the hardest to
# reach, so they hold the more situational powerups (Laser /
# Expand at the top, ExtraLife / SlowBall at the bottom). The
# pink and blue highlight bricks in the central column hold the
# catch / duplicate combo, since they're the easiest to reach
# from a centred paddle.
POWERUPS = {
    # Top outer corners of the upper diamond cluster (hardest).
    (2, 4): LaserPowerUp,
    (10, 4): ExpandPowerUp,
    # Central column - easiest to reach.
    (6, 6): CatchPowerUp,
    (6, 10): DuplicatePowerUp,
    # Bottom outer corners of the lower diamond cluster (mirror).
    (2, 14): ExtraLifePowerUp,
    (10, 14): SlowBallPowerUp,
}


class Round8(BaseRound):
    """Initialises the background, brick layout and powerups for round 8.

    The brick layout is taken directly from the supplied
    ``stage 8.txt`` reference file: 13 columns wide, 11 rows of
    data, with the first row of bricks at game y=4 (matching the
    top of round 3, round 6 and round 7) so the four rows above
    remain clear for the enemy spawn zone. The structure is a
    vertically-symmetric emblem: two diamond-shaped gold clusters
    at the top and bottom of the play area, joined by a single
    central column at x=6 of mixed-colour highlight bricks
    (pink at the top, then green, orange, blue, red, green,
    orange descending).

    This is the final round in the game, so ``self.next_round``
    stays at the base-class default of ``None`` and the
    ``RoundEndState`` will display the "you completed the game"
    flow when the last brick is destroyed.
    """

    # Top of the brick grid. With the LAYOUT above the first row
    # of bricks lands at this y; the four rows above (y=0, 1, 2,
    # 3) remain clear for enemy spawn - the same pattern used by
    # round 3, round 6 and round 7.
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        """Initialise round 8.

        Args:
            top_offset:
                The number of pixels from the top of the screen before
                the top edge can be displayed.
        """
        super().__init__(top_offset)

        self.name = 'Round 8'
        self.next_round = Round9
        # Re-use the round 3 enemy type: ``molecule`` is the third
        # enemy in the existing per-level rotation (see rounds 1-5)
        # and continues the "round 6 -> enemy from round 1, round 7
        # -> enemy from round 2, round 8 -> enemy from round 3, ..."
        # pattern. ``EnemyType.molecule`` has a full set of
        # ``enemy_molecule_*.png`` assets, so the animation
        # iterator is populated and the enemy spawns and animates
        # without raising ``StopIteration`` on the first
        # ``update()`` call.
        self.enemy_type = EnemyType.molecule
        self.num_enemies = 3

    def can_release_enemies(self):
        """Release the enemies right at the start."""
        return True

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_chevron_background
        return create_chevron_background(self.screen, self.edges)

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
                brick = Brick(colour, 8, powerup_cls=powerup_cls)
                bricks.append(self._blit_brick(brick, x, y))
        return pygame.sprite.Group(*bricks)
