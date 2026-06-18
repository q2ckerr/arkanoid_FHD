import pygame

from arkanoid.rounds.base import (BaseRound, BLUE)
from arkanoid.sprites.brick import BossBrick
from arkanoid.sprites.enemy import EnemyType


class Round33(BaseRound):
    """Round 33: DOH boss fight.

    A single large boss brick sits in the centre of the screen.
    Width = 1/3 play area, height = 1/2 play area.
    Top edge is 4 standard brick heights below the top wall.
    Destroy it (50 hits) to win the game.
    """

    _TOP_ROW_START = 0

    def __init__(self, top_offset):
        super().__init__(top_offset)

        self.name = 'Round 33'
        self.next_round = None
        self.enemy_type = EnemyType.cube
        self.num_enemies = 0

    def can_release_enemies(self):
        return False

    def _get_background_colour(self):
        return BLUE

    def _create_background(self):
        from arkanoid.rounds.background import create_boss_background
        return create_boss_background(self.screen, self.edges)

    def _create_bricks(self):
        play_left = self.edges.left.rect.right
        play_right = self.edges.right.rect.left
        play_top = self.edges.top.rect.bottom
        play_width = play_right - play_left
        play_height = self.screen.get_height() - play_top

        # Standard brick height (unscaled, same as regular bricks).
        brick_h = 21

        boss_w = play_width // 3
        boss_h = play_height // 2

        boss = BossBrick(width=boss_w, height=boss_h, hits_to_kill=50)
        boss.rect.midtop = ((play_left + play_right) // 2,
                            play_top + 4 * brick_h)

        return pygame.sprite.Group(boss)
