import pygame

from arkanoid.rounds.base import (BaseRound,
                                  BLUE)
from arkanoid.rounds.round15 import Round15
from arkanoid.sprites.brick import (Brick,
                                    BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp,
                                      DuplicatePowerUp,
                                      ExpandPowerUp,
                                      ExtraLifePowerUp,
                                      LaserPowerUp,
                                      SlowBallPowerUp)


# 2D layout for round 14, 13 columns wide, taken from ``stage 14.txt``.
# 14 rows (0-13).  First row at game y=4 (``_TOP_ROW_START = 4``)
# so four rows above remain clear for the enemy spawn zone.
#
# Alternating pattern of solid colour bars and gold-corner rows with
# silver bars in between.
LAYOUT = [
    # Row 0 (game y=4) — blue bar
    ['blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue',
     'blue', 'blue', 'blue', 'blue', 'blue', 'blue'],
    # Row 1 (game y=5) — gold corners
    ['gold', None, None, None, None, None, None, None, None,
     None, None, None, 'gold'],
    # Row 2 (game y=6) — blue bar
    ['blue', 'blue', 'blue', 'blue', 'blue', 'blue', 'blue',
     'blue', 'blue', 'blue', 'blue', 'blue', 'blue'],
    # Row 3 (game y=7) — empty
    [None, None, None, None, None, None, None, None, None,
     None, None, None, None],
    # Row 4 (game y=8) — orange + silver
    ['orange', 'silver', 'silver', 'silver', 'silver', 'silver',
     'silver', 'silver', 'silver', 'silver', 'silver', 'silver',
     'orange'],
    # Row 5 (game y=9) — gold corners
    ['gold', None, None, None, None, None, None, None, None,
     None, None, None, 'gold'],
    # Row 6 (game y=10) — white bar
    ['white', 'white', 'white', 'white', 'white', 'white', 'white',
     'white', 'white', 'white', 'white', 'white', 'white'],
    # Row 7 (game y=11) — empty
    [None, None, None, None, None, None, None, None, None,
     None, None, None, None],
    # Row 8 (game y=12) — cyan + silver
    ['cyan', 'silver', 'silver', 'silver', 'silver', 'silver',
     'silver', 'silver', 'silver', 'silver', 'silver', 'silver',
     'cyan'],
    # Row 9 (game y=13) — gold corners
    ['gold', None, None, None, None, None, None, None, None,
     None, None, None, 'gold'],
    # Row 10 (game y=14) — red bar
    ['red', 'red', 'red', 'red', 'red', 'red', 'red',
     'red', 'red', 'red', 'red', 'red', 'red'],
    # Row 11 (game y=15) — empty
    [None, None, None, None, None, None, None, None, None,
     None, None, None, None],
    # Row 12 (game y=16) — red bar
    ['red', 'red', 'red', 'red', 'red', 'red', 'red',
     'red', 'red', 'red', 'red', 'red', 'red'],
    # Row 13 (game y=17) — gold corners
    ['gold', None, None, None, None, None, None, None, None,
     None, None, None, 'gold'],
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
    (0, 4): LaserPowerUp,
    (12, 4): ExpandPowerUp,
    (6, 6): CatchPowerUp,
    (0, 10): DuplicatePowerUp,
    (0, 12): ExtraLifePowerUp,
    (12, 12): SlowBallPowerUp,
}


class Round14(BaseRound):
    """Round 14: alternating colour bars with gold corners.

    First row at game y=4 so the enemy spawn zone above is clear.
    Enemy type: cone (cycle restarts).
    Background: circles (next after hex in the rotation).
    """

    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 14'
        self.next_round = Round15
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
