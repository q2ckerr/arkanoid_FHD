import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.rounds.round30 import Round30
from arkanoid.sprites.brick import (Brick, BrickColour)
from arkanoid.sprites.enemy import EnemyType
from arkanoid.sprites.powerup import (CatchPowerUp, DuplicatePowerUp,
                                      ExpandPowerUp, ExtraLifePowerUp,
                                      LaserPowerUp, SlowBallPowerUp)

LAYOUT = [
    [None]*13, [None]*13, [None]*13, [None]*13,
    ['yellow', 'yellow', 'yellow', 'yellow', 'yellow', 'gold', None, 'gold', 'yellow', 'yellow', 'yellow', 'yellow', 'yellow'],
    ['pink', 'pink', 'pink', 'pink', 'pink', 'gold', None, 'gold', 'pink', 'pink', 'pink', 'pink', 'pink'],
    ['gold', 'gold', 'white', 'gold', 'gold', 'gold', None, 'gold', 'gold', 'gold', 'white', 'gold', 'gold'],
    ['blue', 'blue', 'blue', 'blue', 'blue', 'gold', None, 'gold', 'blue', 'blue', 'blue', 'blue', 'blue'],
    ['red', 'red', 'red', 'red', 'red', 'gold', None, 'gold', 'red', 'red', 'red', 'red', 'red'],
    ['green', 'green', 'green', 'green', 'green', 'gold', None, 'gold', 'green', 'green', 'green', 'green', 'green'],
    ['silver', 'silver', 'white', 'silver', 'silver', 'gold', None, 'gold', 'silver', 'silver', 'white', 'silver', 'silver'],
    ['teal', 'teal', 'teal', 'teal', 'teal', 'gold', None, 'gold', 'teal', 'teal', 'teal', 'teal', 'teal'],
    ['orange', 'orange', 'orange', 'orange', 'orange', 'gold', None, 'gold', 'orange', 'orange', 'orange', 'orange', 'orange'],
    ['white', 'white', 'white', 'white', 'white', 'gold', None, 'gold', 'white', 'white', 'white', 'white', 'white'],
]

_COLOUR_MAP = {
    'blue': BrickColour.blue, 'cyan': BrickColour.cyan, 'gold': BrickColour.gold,
    'green': BrickColour.green, 'orange': BrickColour.orange, 'pink': BrickColour.pink,
    'red': BrickColour.red, 'silver': BrickColour.silver, 'teal': BrickColour.cyan,
    'white': BrickColour.white, 'yellow': BrickColour.yellow,
}

POWERUPS = {
    (0, 0): LaserPowerUp, (12, 0): ExpandPowerUp,
    (5, 0): CatchPowerUp, (7, 0): DuplicatePowerUp,
    (5, 5): ExtraLifePowerUp, (7, 5): SlowBallPowerUp,
}


class Round29(BaseRound):
    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)
        self.name = 'Round 29'
        self.next_round = Round30
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
