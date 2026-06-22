import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round18 import Round18
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

# stage_17.txt — 5 empty rows trimmed, first brick at row 0.
LAYOUT = [
    [None, None, None, None, None, None, 'silver', None, None, None, None, None, None],
    [None, None, None, 'blue', 'blue', 'blue', 'silver', 'green', 'green', 'green', None, None, None],
    [None, None, 'blue', 'blue', 'blue', 'white', 'white', 'white', 'green', 'green', 'green', None, None],
    [None, None, 'blue', 'blue', 'white', 'white', 'white', 'white', 'white', 'green', 'green', None, None],
    [None, 'blue', 'blue', 'blue', 'white', 'white', 'white', 'white', 'white', 'green', 'green', 'green', None],
    [None, 'blue', 'blue', 'blue', 'white', 'white', 'white', 'white', 'white', 'green', 'green', 'green', None],
    [None, 'blue', 'blue', 'blue', 'white', 'white', 'white', 'white', 'white', 'green', 'green', 'green', None],
    [None, 'silver', None, None, 'silver', None, 'silver', None, 'silver', None, None, 'white', None],
    [None, None, None, None, None, None, 'silver', None, None, None, None, None, None],
    [None, None, None, None, None, None, 'silver', None, None, None, None, None, None],
    [None, None, None, None, None, None, 'silver', None, None, None, None, None, None],
    [None, None, None, None, 'yellow', None, 'yellow', None, None, None, None, None, None],
    [None, None, None, None, 'yellow', 'yellow', 'yellow', None, None, None, None, None, None],
    [None, None, None, None, None, 'yellow', None, None, None, None, None, None, None],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (6, 0): LaserPowerUp, (6, 7): ExpandPowerUp,
    (1, 4): CatchPowerUp, (11, 7): DuplicatePowerUp,
    (4, 11): ExtraLifePowerUp, (6, 13): SlowBallPowerUp,
}


class Round17(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 17'
        self.next_round = Round18
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
