import collections

import pygame

from arkanoid.sprites.edge import (TopEdge,
                                   SideEdge)
from arkanoid.sprites.brick import BrickColour

# RGB sequences for background colours.
BLUE = (0, 0, 128)
GREEN = (0, 128, 0)
RED = (128, 0, 0)


class BaseRound:
    """Abstract base class for all Arkanoid rounds.

    Subclasses must implement the abstract hook methods defined here.
    """

    def __init__(self, top_offset):
        """Initialise the BaseRound.

        Args:
            top_offset:
                The number of pixels from the top of the screen before the
                top edge can be displayed.
        """
        self.top_offset = top_offset
        self.screen = pygame.display.get_surface()

        # The name of the round displayed on the screen when the round starts.
        self.name = 'Round name not set!'

        # The edges used as the sides of the game area.
        # A named tuple referencing the 3 game edge sprites with the
        # attributes: 'left', 'right', 'top'.
        self.edges = self._create_edges()

        # The background for this round.
        self.background = self._create_background()

        # NOTE: the background is NOT blitted to the screen here.
        # The main loop clears the screen to black every frame and
        # the Game class blits the background (play-area only) and
        # the side-area starfield each frame, so a one-shot blit at
        # init time would be immediately overwritten anyway.

        # Create the bricks that the ball can collide with, positioning
        # them on the screen.
        self.bricks = self._create_bricks()

        # Concrete subclasses can override this setting to modify the
        # base speed of the ball for the round, if they want the ball to move
        # more quickly/slowly for that particular round.
        self.ball_base_speed_adjust = 0

        # Concreate subclasses can override this setting to modify the speed
        # of the paddle for the round, if they want the paddle to move
        # more quickly/slowly for that partucular round.
        self.paddle_speed_adjust = 0

        # Concrete subclasses can override this setting to modify the
        # ball speed normalisation rate, if the rate should be slower/quicker
        # for that particular round.
        self.ball_speed_normalisation_rate_adjust = 0

        # The class of the enemy to release in this round. Subclasses to
        # override with the specific class.
        self.enemy_type = None

        # The number of enemies to release. Subclasses to override with a
        # specific number.
        self.num_enemies = 0

        # Reference to the next round, to be overriden by subclasses.
        self.next_round = None

        # Keep track of the number of destroyed bricks.
        self._bricks_destroyed = 0

    @property
    def complete(self):
        """Whether the rounds has been completed (all bricks destroyed).
        
        Returns:
            True if the round has been completed. False otherwise.
        """
        return self._bricks_destroyed >= len([brick for brick in self.bricks
                                              if brick.colour !=
                                              BrickColour.gold])

    def brick_destroyed(self):
        """Conveys to the round that a brick has been destroyed in the game."""
        self._bricks_destroyed += 1

    def can_release_enemies(self):
        """Whether the enemies can be released into the game.

        This is round specific, so concrete round subclasses should implement
        this method.
        """
        raise NotImplementedError('Subclasses must implement '
                                  'can_release_enemies()')

    def _blit_brick(self, brick, x, y):
        """Blits the specified brick onto the game area by using a
        relative coordinate for the position of the brick.

        This is a convenience method that concrete subclasses can use when
        setting up bricks. It assumes that the game area (area within the
        edges) is split into a grid where each grid square corresponds to one
        brick. The top left most brick is considered position (0, 0). This
        allows clients to avoid having to work with actual screen positions.

        Bricks are placed flush against the *left* wall of the play area
        (matching the original Arkanoid game, where the first column of
        bricks is hard up against the left side wall). The brick grid is
        *not* centred — the right side of the play area simply has
        whatever empty space is left over.

        Note that this method will modify the brick's rect attribute once
        the brick has been set.

        Args:
            brick:
                The brick instance to position on the grid.
            x:
                The x position on the grid.
            y:
                The y position on the grid.
        Returns:
            The blitted brick.
        """
        brick_width = brick.rect.width
        brick_height = brick.rect.height

        target_x = (self.edges.left.rect.x + self.edges.left.rect.width
                    + x * brick_width)
        target_y = (self.edges.top.rect.y + self.edges.top.rect.height
                    + y * brick_height)

        rect = self.screen.blit(brick.image, (target_x, target_y))
        brick.rect = rect
        return brick

    def _create_background(self):
        """Create the background surface for the round.

        The surface is screen-sized but only the play area (the
        region between the side walls and below the top edge) is
        filled with the round colour — the rest stays black so the
        side-area starfield drawn by :class:`Game` shows through.

        Subclasses may override this if they wish to provide a
        more elaborate background (e.g. textured) for a round.

        Returns:
            The background surface.
        """
        from arkanoid.game import LAYOUT

        background = pygame.Surface(self.screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))

        # Fill only the play area bounded by the side walls and top edge.
        left = self.edges.left.rect.right
        right = self.edges.right.rect.left
        top = self.edges.top.rect.bottom
        play_rect = pygame.Rect(left, top,
                                right - left,
                                self.screen.get_height() - top)
        background.fill(self._get_background_colour(), play_rect)
        return background

    def _get_background_colour(self):
        """Abstract method to obtain the background method for a round.

        Subclasses must implement this to return the colour, or alternatively,
        override _create_background() completely to create a more elaborate
        background.

        Returns:
            The background colour.
        """
        raise NotImplementedError(
            'Subclasses must implement _get_background_colour()')

    def _create_edges(self):
        """Create the edge sprites and position them at the edges of the
        screen.

        This implementation creates static edges. Subclasses may override
        if they wish to provide some special animation within an edge.

        Returns:
            A named tuple with attributes 'left', 'right', and 'top' that
            reference the corresponding edge sprites.
        """
        from arkanoid.game import LAYOUT
        
        edges = collections.namedtuple('edge', 'left right top')
        left_edge = SideEdge('left')
        right_edge = SideEdge('right')
        top_edge = TopEdge()
        
        # Use the layout offset for proper positioning
        left_edge.rect.topleft = (LAYOUT.offset_x, self.top_offset)
        right_edge.rect.topright = (
            self.screen.get_width() - LAYOUT.offset_x, self.top_offset)
        top_edge.rect.topleft = (
            LAYOUT.offset_x + left_edge.rect.width, self.top_offset)
        return edges(left_edge, right_edge, top_edge)

    def _create_bricks(self):
        """Create the bricks and position them on the screen.

        Subclasses must override this abstract method to create and position
        the bricks.

        Returns:
            A pygame.sprite.Group of bricks.
        """
        raise NotImplementedError('Subclasses must implement _create_bricks()')

