import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round19 import Round19
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

# stage_18.txt — 5 empty rows trimmed, first brick at row 0.
LAYOUT = [
    ['orange', None, 'gold', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'gold', None, 'orange'],
    ['orange', None, 'gold', 'gold', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'gold', 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'yellow', 'yellow', 'yellow', 'gold', None, 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'pink', 'yellow', 'teal', 'gold', None, 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'pink', 'silver', 'teal', 'gold', None, 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'pink', 'green', 'teal', 'gold', None, 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'pink', 'green', 'teal', 'gold', None, 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'pink', 'green', 'teal', 'gold', None, 'gold', None, 'orange'],
    ['orange', None, 'gold', None, 'gold', 'pink', 'green', 'teal', 'gold', None, 'gold', None, 'orange'],
    ['orange', 'gold', 'gold', 'gold', 'gold', 'pink', 'green', 'teal', 'gold', 'gold', 'gold', 'gold', 'orange'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (2, 0): LaserPowerUp, (10, 0): ExpandPowerUp,
    (5, 4): CatchPowerUp, (7, 4): DuplicatePowerUp,
    (0, 1): ExtraLifePowerUp, (12, 1): SlowBallPowerUp,
}


class Round18(BaseRound):
    _TOP_ROW_START = 4

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 18'
        self.next_round = Round19
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
