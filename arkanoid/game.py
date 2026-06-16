import functools
import importlib
import itertools
import logging
import math
import os
import random
import ctypes

import pygame

from arkanoid.event import receiver
from arkanoid.rounds.round1 import Round1
from arkanoid.sound import (play_block_hit, play_enemy_explode,
                            play_gold_block_hit, play_level_start)
from arkanoid.sprites.ball import Ball
from arkanoid.sprites.brick import Brick, BrickColour
from arkanoid.sprites.edge import SideEdge, TopEdge
from arkanoid.sprites.enemy import Enemy
from arkanoid.sprites.paddle import (ExplodingState,
                                     Paddle,
                                     MaterializeState)
from arkanoid.utils.util import (load_high_score,
                                 load_png,
                                 load_png_sequence,
                                 save_high_score)
from arkanoid.utils import ptext

LOG = logging.getLogger(__name__)

# A module-level gamepad wrapper. This is the single source of
# truth for the connected controller - both the start screen and
# the in-game paddle read from it. It is created lazily (on first
# import) so pygame.joystick.init() only runs once.
GAMEPAD = None


def get_gamepad():
    """Return the process-wide :class:`Gamepad` instance, creating
    it on the first call. The wrapper is safe to use whether or not
    a controller is actually connected - in that case it reports a
    centred axis and no button presses.
    """
    global GAMEPAD
    if GAMEPAD is None:
        from arkanoid.gamepad import Gamepad
        GAMEPAD = Gamepad()
    return GAMEPAD

# === Resolution-independent game tuning =====================================
# The speed the game runs at in FPS.
GAME_SPEED = 60
# The angle the ball initially moves off the paddle, in radians.
BALL_START_ANGLE_RAD = 5.0  # Value must be no smaller than -3.14
# The speed that the ball will always try to arrive at.
# This is based on a game running at 60fps. You might need to increment it by
# a couple of notches if you find the ball moves too slowly.
BALL_BASE_SPEED = 8  # pixels per frame
# The max speed of the ball, prevents a runaway speed when lots of rapid
# collisions.
BALL_TOP_SPEED = 15  # pixels per frame
# Per-frame rate at which ball is brought back to base speed.
BALL_SPEED_NORMALISATION_RATE = 0.02
# Increase in speed caused by colliding with a brick.
BRICK_SPEED_ADJUST = 0.5
# Increase in speed caused by colliding with a wall.
WALL_SPEED_ADJUST = 0.2
# The speed the paddle moves.
PADDLE_SPEED = 10
# The fonts.
MAIN_FONT = os.path.join(os.path.dirname(__file__), 'data', 'fonts',
                         'generation.ttf')
ALT_FONT = os.path.join(os.path.dirname(__file__), 'data', 'fonts',
                        'optimus.otf')

# === Display configuration ==================================================
# The dimensions of the main game window in pixels. Change this to whatever
# resolution you'd like the game to run at. All UI offsets/positions/sizes
# below are computed relative to the reference resolution defined in
# :class:`Layout`, so they will scale automatically.
DISPLAY_SIZE = 1920, 1080
# The title of the main window.
DISPLAY_CAPTION = 'Arkanoid'

# The game was originally laid out for a 600x800 display. To support
# arbitrary display resolutions we treat every on-screen value as authored
# against this reference resolution and scale it to the actual display
# resolution at runtime.
REFERENCE_SIZE = (600, 800)


class Layout:
    """Resolution-aware scale + centring calculator.

    The game was originally designed for 600x800. To make every on-screen
    value work at any other resolution we scale it uniformly by
    ``min(scale_x, scale_y)`` and centre the resulting game area on the
    screen (per-axis ``offset_x`` / ``offset_y``). Per-axis scales
    (``scale_x`` / ``scale_y``) are also exposed for the (rare) cases
    where an element should stretch with the screen rather than scale
    uniformly (for example UI widgets anchored to the right edge of the
    screen).

    Using this class means every hardcoded offset, font size, surface
    size, gap and position in :mod:`arkanoid.game` is written against the
    reference resolution and converted to the actual resolution at
    runtime — so changing :data:`DISPLAY_SIZE` is the only thing required
    to retarget the game at a new resolution.
    """

    def __init__(self, display_size, reference_size=REFERENCE_SIZE):
        """Initialise the Layout for the given display size.

        Args:
            display_size:
                The actual display resolution as a ``(width, height)`` tuple.
            reference_size:
                The reference resolution that all on-screen values are
                authored against. Defaults to :data:`REFERENCE_SIZE`.
        """
        self.display_size = tuple(display_size)
        self.reference_size = tuple(reference_size)

        # Per-axis scales — how much each axis is stretched when going
        # from the reference resolution to the actual display.
        self.scale_x = self.display_size[0] / self.reference_size[0]
        self.scale_y = self.display_size[1] / self.reference_size[1]

        # Uniform scale — preserves the original aspect ratio. We pick
        # the smaller of the two axis scales so the scaled game area
        # always fits inside the actual screen.
        self.scale = min(self.scale_x, self.scale_y)

        # Centring offsets — the scaled game area is placed in the middle
        # of the screen, so on a wider screen the extra horizontal space
        # is split evenly as a left/right border.
        self.offset_x = int(
            (self.display_size[0] - self.reference_size[0] * self.scale) / 2)
        self.offset_y = int(
            (self.display_size[1] - self.reference_size[1] * self.scale) / 2)

    def s(self, value):
        """Scale ``value`` uniformly (use for square elements such as font
        sizes, padding and surface sizes).

        Returns:
            The integer pixel value at the new resolution.
        """
        return int(value * self.scale)

    def sx(self, value):
        """Scale ``value`` along the x-axis and add the horizontal centring
        offset. Use for in-game x positions — i.e. positions that are
        anchored to the left edge of the (centred) game area.

        Returns:
            The integer pixel value at the new resolution.
        """
        return self.offset_x + int(value * self.scale)

    def sy(self, value):
        """Scale ``value`` along the y-axis and add the vertical centring
        offset. Use for in-game y positions.

        Returns:
            The integer pixel value at the new resolution.
        """
        return self.offset_y + int(value * self.scale)


# A single shared layout instance used throughout the module. Recompute
# this if you change :data:`DISPLAY_SIZE` at runtime.
LAYOUT = Layout(DISPLAY_SIZE)

# Set global scale for sprite loading
from arkanoid.utils.util import set_game_scale
set_game_scale(LAYOUT.scale)


def s(v):
    """Shorthand: scale ``v`` uniformly."""
    return LAYOUT.s(v)


def sx(v):
    """Shorthand: scale ``v`` along the x-axis with the centring offset."""
    return LAYOUT.sx(v)


def sy(v):
    """Shorthand: scale ``v`` along the y-axis with the centring offset."""
    return LAYOUT.sy(v)


# The number of pixels from the top of the screen before the top edge
# starts. Expressed in the reference resolution and scaled via the
# Layout so it tracks the display resolution.
TOP_OFFSET = s(150)

import sys

# === Disable Windows DPI scaling ============================================
# When Windows has UI scaling (e.g. 125%/150%) enabled, the pygame window
# is stretched by the OS, which makes every sprite, font and offset appear
# larger than authored. Tell Windows that this process handles its own DPI
# so the game renders at its true resolution. No-op on non-Windows.
if sys.platform == 'win32':
    try:
        # Windows 8.1+: per-monitor DPI awareness (best)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except (AttributeError, OSError):
        try:
            # Windows Vista+: system DPI awareness (fallback)
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


# Initialise the pygame modules.
pygame.init()


class Arkanoid:
    """Manages the overall program. This will start and end new games."""

    def __init__(self):
        # Initialise the clock.
        self._clock = pygame.time.Clock()

        # Create the main screen (the window) and default background.
        self._screen = self._create_screen()
        self._background = self._create_background()
        self._display_logo()
        self._display_score_titles()
        self._high_score = load_high_score()

        # The start screen displayed before the game is started.
        self._start_screen = StartScreen(self._start_game)

        # Reference to a running game, when one is in play.
        self._game = None

        # Whether we're running.
        self._running = True

        # Set up the top level event handlers.
        def quit_handler(event):
            self._running = False
        receiver.register_handler(pygame.QUIT, quit_handler)

        # Initialise the scores. The y coordinates place the 1UP
        # score value on the same line as the 1UP label (drawn by
        # ``_display_score_titles`` at sy(20)) and the high score
        # value on the line below the HIGH SCORE label, so the three
        # top-right elements (1UP, HIGH SCORE, high score value)
        # are stacked with equal margins between them.
        self._display_player_score = functools.partial(self._display_score,
                                                       y=sy(20))
        self._display_high_score = functools.partial(self._display_score,
                                                     y=sy(80))
        self._display_player_score(0)
        self._display_high_score(self._high_score)

    def main_loop(self):
        """Starts the main loop of the program which manages the screen
        interactions and game play.

        Pretty much everything takes place within this loop.
        """
        while self._running:
            # Game runs at 60 fps.
            self._clock.tick(GAME_SPEED)

            # Receive and dispatch events.
            receiver.receive()

            # Pick up gamepads that were plugged in after the game
            # started. This is a no-op if no controller is
            # connected, so it is safe to call on every frame.
            get_gamepad().refresh()

            # Always clear the screen to black so the side-area
            # starfield and the play-area background are drawn on
            # a clean base every frame.
            self._screen.fill((0, 0, 0))

            # Draw the logo every frame (visible in both states).
            self._display_logo()

            if not self._game:
                self._start_screen.show()
            else:
                # Draw score titles and scores only during gameplay.
                self._display_score_titles()
                self._display_high_score(self._high_score)
                self._display_player_score(self._game.score)
                self._display_level()

                self._game.update()

                if self._game.over:
                    if self._game.score > self._high_score:
                        self._high_score = self._game.score
                        save_high_score(self._high_score)
                    self._game = None

            # Display all updates.
            pygame.display.flip()

        LOG.debug('Exiting')

    def _start_game(self, round_no):
        """Callback invoked by the start screen when a user begins a game,
        either by hitting the spacebar, or by entering a specific round number
        to start at.

        Args:
            round_no:
                The round number the user entered.

        """
        module_name = 'arkanoid.rounds.round{}'.format(round_no)
        try:
            module = importlib.import_module(module_name)
            round_cls = getattr(module, 'Round{}'.format(round_no))
        except (ImportError, AttributeError):
            LOG.exception('Unable to import round')
        else:
            self._game = Game(round_class=round_cls)
            self._start_screen.hide()

    def _create_screen(self):
        pygame.display.set_mode(DISPLAY_SIZE)
        pygame.display.set_caption(DISPLAY_CAPTION)
        pygame.mouse.set_visible(False)
        screen = pygame.display.get_surface()
        return screen

    def _create_background(self):
        background = pygame.Surface(self._screen.get_size())
        background = background.convert()
        background.fill((0, 0, 0))
        return background

    def _display_logo(self):
        image, _ = load_png('logo.png')
        # The logo is centred horizontally on the *screen* (not the
        # play area) so it sits above the centre of the game field.
        # This is balanced by the score panel (top-right) and works
        # equally well during gameplay and on the start screen, where
        # the powerups grid sits to the left and the controls to the
        # right.
        screen_w = self._screen.get_width()
        logo_w = image.get_width()
        self._screen.blit(image, (screen_w // 2 - logo_w // 2, sy(0)))

    def _display_score_titles(self):
        """Display the 1UP label, HIGH SCORE label and the high score
        value stacked vertically in the top-right of the screen.

        UI elements use the *full screen width* (not just the play
        area) and are right-aligned to the screen's right edge with
        equal margins between the three elements. The score panel
        lives in the top-right of the screen, clear of the (now
        horizontally centred) logo.
        """
        screen_w = self._screen.get_width()
        right_edge = screen_w - s(20)

        # 1UP label sits on the *same line* as the 1UP score (drawn
        # by ``_display_score`` at the same y) but offset to the
        # left so the label and value are side-by-side, like the
        # original Arkanoid game. The label is right-aligned to a
        # point s(150) px in from the screen's right edge so the
        # score value (right-aligned to the edge) has space to its
        # right.
        ptext.draw('1UP', topright=(right_edge - s(150), sy(20)),
                   fontname=MAIN_FONT,
                   fontsize=s(24),
                   color=(230, 0, 0))
        # HIGH SCORE label (below 1UP, equal spacing).
        ptext.draw('HIGH SCORE', topright=(right_edge, sy(50)),
                   fontname=MAIN_FONT,
                   fontsize=s(24),
                   color=(230, 0, 0))

    def _display_score(self, value, y):
        """Draw ``value`` right-aligned to the *screen* edge at ``y``.

        The score panel is right-aligned to the screen's right edge
        (not the play area's) so the score value is visible even on
        wider displays where the play area does not reach the screen
        edge.
        """
        score_surf = pygame.Surface((s(150), s(20))).convert_alpha()
        ptext.draw(str(value),
                   topright=(s(150), 0),
                   fontname=MAIN_FONT,
                   fontsize=s(24),
                   color=(255, 255, 255),
                   surf=score_surf)
        right_edge = self._screen.get_width() - s(20)
        position = (right_edge - s(150), y)
        self._screen.blit(self._background, position, score_surf.get_rect())
        self._screen.blit(score_surf, position)

    def _display_level(self):
        """Draw 'Level X' to the left of the logo, using the same font
        and style as the score panel."""
        level_text = 'Level {}'.format(self._game.round.name.split()[-1])
        ptext.draw(level_text,
                   topleft=(s(20), sy(20)),
                   fontname=MAIN_FONT,
                   fontsize=s(24),
                   color=(230, 0, 0))


class StartScreen:
    """Used to display the screen shown when the program is first run, and
    before a game is started.

    Apart from displaying some general information about the game, the start
    screen is also responsible for capturing user input to decide when to
    start a game, and which level to start on.
    """

    def __init__(self, on_start):
        """Initialise the start screen.

        Args:
            on_start:
                Callback invoked when a player starts a new game. The callback
                should accept a single argument: the round number that the
                game will start at.
        """
        self._on_start = on_start
        self._screen = pygame.display.get_surface()

        # The key for the powerups - their images with names and descriptions.
        # Each entry is stored as [image, name, description, animation_cycle],
        # so we can keep the most recently rendered image around between
        # frames. Without this, the icon and text would only be re-blitted
        # every 4 frames (when the animation cycle advances), causing the
        # whole powerup grid to visibly flicker on the cleared start screen.
        self._powerups = [
            # (animation, name, description)
            (itertools.cycle(load_png_sequence('powerup_laser')),
             'laser',
             'enables the vaus\nto fire a laser'),
            (itertools.cycle(load_png_sequence('powerup_slow')),
             'slow',
             'slow down the\nenergy ball'),
            (itertools.cycle(load_png_sequence('powerup_life')),
             'extra life',
             'gain an additional\nvaus'),
            (itertools.cycle(load_png_sequence('powerup_expand')),
             'expand',
             'expands the vaus'),
            (itertools.cycle(load_png_sequence('powerup_catch')),
             'catch',
             'catches the energy\nball'),
            (itertools.cycle(load_png_sequence('powerup_duplicate')),
             'duplicate',
             'duplicates the energy\nball'),
        ]
        # Pre-render the first image for every powerup so the grid has
        # something to draw on the very first frame.
        self._powerup_images = []
        for anim, _name, _desc in self._powerups:
            image, _ = next(anim)
            self._powerup_images.append(image)

        # Whether the event listeners have been registered.
        self._registered = False

        self._text_colors_1 = itertools.cycle([(255, 255, 255),
                                               (255, 255, 0)])
        self._text_color_1 = None

        self._text_colors_2 = itertools.cycle([(255, 255, 0),
                                               (255, 0, 0)])
        self._text_color_2 = None

        # The text entered by the user.
        self._user_input = ''
        self._user_input_pos = None

        # Keep track of display count for animation purposes.
        self._display_count = 0

        # === Starfield animation ==========================================
        # A simple field of white dots scattered randomly across the
        # whole screen, each drifting slowly outward from the centre.
        # Each star is a [x, y, dir_x, dir_y, speed, visible] list so
        # the structure stays trivially readable. The direction is
        # computed once at spawn time from the vector between the
        # star's random position and the screen centre - this is
        # what produces the "galaxy expanding outward" feel without
        # the need for any actual line drawing.
        #
        # A small per-frame chance toggles each star's visibility
        # (twinkling) and off-screen stars are respawned at a new
        # random position with a fresh outward direction, so the
        # field looks alive indefinitely.
        self._stars = []
        self._star_center_x = self._screen.get_width() // 2
        self._star_center_y = self._screen.get_height() // 2
        # Random speed buckets chosen to match the reference
        # stars.py: a slow pair (the "distant" stars) and a fast
        # pair (the "close" stars) so the field has a hint of
        # parallax without resorting to two separate layers.
        self._star_speed_choices = [0.1, 0.15, 0.4, 0.6]
        self._star_count = 200
        self._star_flicker_chance = 0.01

    def show(self):
        """Display the start screen and register event listeners for
        capturing keyboard input.

        This method is designed to be called repeatedly by the main game loop.

        The start screen is laid out in two columns plus a centred footer,
        drawn on top of an animated starfield:
        - BACKGROUND: two layers of stars moving outward from the screen
          centre, creating a parallax "warp / hyperspace" effect.
        - LEFT: the powerups grid (2 columns x 3 rows) with the POWERUPS
          header centred above it. The grid is positioned in the free
          space *left* of the play area (between the screen's left edge
          and the play area's left wall), so it never overlaps the game
          field.
        - RIGHT: the game-start controls (SPACEBAR / A TO START, OR
          ENTER LEVEL, and the level-number entry), right-aligned
          to the screen edge.
        - BOTTOM: the "Based on original Arkanoid game" credit, centred
          horizontally on the screen.
        """
        if not self._registered:
            receiver.register_handler(pygame.KEYUP, self._on_keyup)
            self._registered = True

        # The main loop clears the screen to black before calling
        # ``show``, so we no longer need a one-shot clear here -
        # the starfield just adds dots on top of that black
        # background each frame.

        screen_w = self._screen.get_width()

        # === GAMEPAD: refresh + Start button ===============================
        # Pick up controllers that were plugged in after the game
        # started, then check whether the player has just pressed
        # a start-equivalent button. ``start_pressed`` returns True
        # for both the A / Cross button (button 0) and the Start
        # button (button 7), so the player can use whichever feels
        # natural on their controller. We do this BEFORE the
        # starfield update so the start-screen logic always sees
        # the freshest input.
        get_gamepad().refresh()
        if get_gamepad().start_pressed:
            self._on_start(1)
            return

        # === BACKGROUND: Animated starfield ===============================
        # Stars are drawn directly on the main screen this frame
        # (the caller has already cleared the screen to black in
        # the main loop), so the only thing left to do here is
        # to draw the white dots. The outward motion is supplied
        # by a per-star direction vector computed at spawn time
        # from the vector between the star and the screen centre,
        # and ``pygame.draw.circle`` with radius 1 is the
        # smallest possible filled circle - so the stars read as
        # points, not streaks.
        if not self._stars:
            self._init_stars()
        self._update_and_draw_stars()

        # === LEFT SIDE: Powerups grid (2 columns x 3 rows) =================
        # The powerups live in the free space to the LEFT of the play
        # area (i.e. between the screen's left edge and the play area's
        # left wall). At 1920x1080 this free space is LAYOUT.offset_x
        # pixels wide, so the grid is sized to fit comfortably inside
        # it with a small uniform margin from the screen edge.
        grid_left = s(20)
        col_width = s(195)
        col_count = 2
        grid_width = col_count * col_width
        grid_right = grid_left + grid_width
        grid_center_x = (grid_left + grid_right) // 2
        row_height = s(110)

        # POWERUPS label, centred horizontally over the 2-column grid
        # and placed just above the grid's top row.
        ptext.draw('POWERUPS', center=(grid_center_x, sy(180)),
                   fontname=ALT_FONT,
                   fontsize=s(32),
                   color=(255, 255, 255))

        # Lay out the 2x3 powerups grid. Each cell is col_width wide
        # and row_height tall; after 2 cells (one per column) we wrap
        # to the next row.
        left, top = grid_left, sy(230)

        for index, (anim, name, desc) in enumerate(self._powerups):
            # Advance the animation cycle every 4 frames so the icon
            # "pulses" - but the icon and label must be re-blitted
            # every single frame, otherwise the powerup grid flashes
            # on a black background when the start screen is cleared.
            if self._display_count % 4 == 0:
                self._powerup_images[index], _ = next(anim)
            image = self._powerup_images[index]
            self._screen.blit(image, (left, top))
            # Name and description are placed to the right of the
            # icon (not below it) so each cell stays compact and the
            # description doesn't overlap the icon.
            text_x = left + image.get_width() + s(15)
            ptext.draw(name.upper(), (text_x, top),
                       fontname=ALT_FONT,
                       fontsize=s(18),
                       color=(255, 255, 255))
            ptext.draw(desc.upper(), (text_x, top + s(25)),
                       fontname=ALT_FONT,
                       fontsize=s(12),
                       color=(255, 255, 255))
            left += col_width
            if left >= grid_left + grid_width:
                left = grid_left
                top += row_height

        # === RIGHT SIDE: Controls (right-aligned to screen edge) =========
        if self._display_count % 15 == 0:
            self._text_color_1 = next(self._text_colors_1)
            self._text_color_2 = next(self._text_colors_2)

        # Right edge of the screen with a small uniform margin. The
        # controls are right-aligned here so they sit clearly on the
        # right side of the screen, independent of the play area.
        right_x = screen_w - s(40)

        # SPACEBAR (OR A / START) TO START - the main call to action.
        # The text shows the keyboard shortcut by default and the
        # gamepad's A / Cross button (and, as a fallback, the
        # dedicated Start button) as an alternative - so the prompt
        # reads correctly whether or not a controller is plugged in.
        # The A button is the primary gamepad option because it is
        # the universal "primary action" button on every common
        # controller layout and is the most natural counterpart to
        # the Space key on a keyboard.
        gamepad = get_gamepad()
        if gamepad.connected:
            start_label = 'SPACEBAR / A TO START'
        else:
            start_label = 'SPACEBAR TO START'
        ptext.draw(start_label, topright=(right_x, sy(360)),
                   fontname=ALT_FONT,
                   fontsize=s(40),
                   color=self._text_color_1,
                   shadow=(1.0, 1.0),
                   scolor="grey")

        # OR ENTER LEVEL - secondary action.
        ptext.draw('OR ENTER LEVEL', topright=(right_x, sy(470)),
                   fontname=ALT_FONT,
                   fontsize=s(28),
                   color=self._text_color_2)

        # User input (level number) - on the line below OR ENTER LEVEL
        # so there's room to type a 1-2 digit number without overlapping
        # the label.
        self._user_input_pos = ptext.draw(self._user_input,
                                          topright=(right_x, sy(530)),
                                          fontname=ALT_FONT,
                                          fontsize=s(32),
                                          color=(255, 255, 255))[1]

        # === BOTTOM: "Based on..." credit, centred horizontally =========
        # The previous version used pos=(screen_w//2, sy(700)) with
        # align='center', but align='center' only centres the LINES
        # within the rendered text surface - it does not centre the
        # surface itself relative to the screen. Use
        # midtop=(screen_w//2, y) so the rendered text is horizontally
        # centred on the screen with its top edge at sy(700).
        ptext.draw('Based on original Arkanoid game\n'
                   'by Taito Corporation 1986',
                   midtop=(screen_w // 2, sy(700)),
                   fontname=ALT_FONT,
                   fontsize=s(18),
                   color=(128, 128, 128))

        self._display_count += 1

    def hide(self):
        """Hide the start screen and unregister event listeners."""
        receiver.unregister_handler(self._on_keyup)
        self._registered = False

    def _on_keyup(self, event):
        """Event handler for capturing user input.

        Args:
            event:
                The pygame event.

        """
        numeric_keys = {pygame.K_0: '0', pygame.K_1: '1', pygame.K_2: '2',
                        pygame.K_3: '3', pygame.K_4: '4', pygame.K_5: '5',
                        pygame.K_6: '6', pygame.K_7: '7', pygame.K_8: '8',
                        pygame.K_9: '9'}
        if event.key == pygame.K_SPACE:
            self._on_start(1)
        elif event.key in numeric_keys and len(self._user_input) < 2:
            self._user_input += numeric_keys[event.key]
        elif event.key == pygame.K_BACKSPACE:
            self._user_input = ''
            # Clear the user input area. The clear surface is scaled
            # from the reference size so it covers the rendered input
            # text at any resolution.
            self._screen.blit(pygame.Surface((s(100), s(60))),
                              self._user_input_pos)
        elif event.key == pygame.K_RETURN and self._user_input:
            self._screen.blit(pygame.Surface((s(100), s(60))),
                              self._user_input_pos)
            self._on_start(int(self._user_input))
            self._user_input = ''

    def _init_stars(self):
        """Populate ``self._stars`` with the initial star field.

        Each star is a 6-element list ``[x, y, dir_x, dir_y, speed,
        visible]``:

        * ``x, y``         - current screen position;
        * ``dir_x, dir_y`` - unit vector pointing *outward* from the
          screen centre. This is what makes the field look like a
          galaxy expanding away from the viewer;
        * ``speed``        - scalar drift speed, picked from
          ``self._star_speed_choices`` for a stepped, deliberately
          non-uniform feel;
        * ``visible``      - whether the star is currently drawn
          (toggled by the per-frame flicker in
          :meth:`_update_and_draw_stars`).

        The list-of-lists layout mirrors the reference stars.py
        file: it's small, easy to read, and has no per-star
        metadata to keep in sync.
        """
        screen_w, screen_h = self._screen.get_size()
        self._star_center_x = screen_w // 2
        self._star_center_y = screen_h // 2
        for _ in range(self._star_count):
            star = [0, 0, 0, 0, 0, True]
            self._reset_star(star)
            self._stars.append(star)

    def _reset_star(self, star):
        """Re-seed a star with a fresh random position and direction.

        Used both at field initialisation and whenever a star has
        drifted off any edge of the screen, so the field never
        empties out. The new position is uniform across the whole
        screen, and the direction is the unit vector from the
        centre to the new position - so the star always heads
        outward regardless of where it spawned.
        """
        screen_w, screen_h = self._screen.get_size()
        star[0] = random.uniform(0, screen_w)
        star[1] = random.uniform(0, screen_h)
        dx = star[0] - self._star_center_x
        dy = star[1] - self._star_center_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            # Star happened to land on the centre: push it in a
            # deterministic direction so it still moves outward.
            star[2], star[3] = 1.0, 0.0
        else:
            star[2], star[3] = dx / dist, dy / dist
        # Random speed picked from the discrete speed buckets so
        # the field has a hint of parallax without the visual
        # weight of a true two-layer system.
        star[4] = random.choice(self._star_speed_choices)
        # Always reset to visible - if a star was flickering
        # invisible when it left the screen we still want it to
        # appear on its new position.
        star[5] = True

    def _update_and_draw_stars(self):
        """Advance every star and draw it on the main screen.

        For each star we:
          1. Move it along its outward direction by its speed.
          2. Possibly toggle its visibility (the twinkle).
          3. If it has drifted off any edge of the screen, respawn
             it at a new random position with a fresh direction.
          4. If it is currently visible, draw a single 1-pixel
             white dot at its position.

        Stars are drawn directly on ``self._screen`` (which the
        caller has already cleared to black this frame) - there is
        no dedicated alpha surface, no streaks, and no parallax
        layer. The end result is a clean starfield of dots that
        drift slowly outward from the centre, matching the
        reference stars.py file.
        """
        screen_w, screen_h = self._screen.get_size()
        for star in self._stars:
            # 1. Advance the star outward from the centre.
            star[0] += star[2] * star[4]
            star[1] += star[3] * star[4]

            # 2. Twinkle: a small per-frame chance of flipping the
            # star's visibility. This is what gives the field its
            # "twinkling" look.
            if random.random() < self._star_flicker_chance:
                star[5] = not star[5]

            # 3. If the star has left the screen, respawn it at a
            # new random position with a fresh direction. A small
            # margin is used so a star whose edge has just touched
            # the side of the screen is not immediately redrawn at
            # a new position one pixel away from the edge.
            if (star[0] < -2 or star[0] > screen_w + 2 or
                    star[1] < -2 or star[1] > screen_h + 2):
                self._reset_star(star)
                continue

            # 4. Draw a single white 1-pixel dot (if currently
            # visible). ``pygame.draw.circle`` with radius 1 is
            # the smallest possible filled circle, so the star
            # reads as a point rather than a streak.
            if star[5]:
                pygame.draw.circle(self._screen, (255, 255, 255),
                                   (int(star[0]), int(star[1])), 1)


class Game:
    """Represents a running Arkanoid game.

    An instance of a Game comes into being when a player starts a new game.
    """

    def __init__(self, round_class=Round1, lives=3):
        """Initialise a new Game.

        Args:
            round_class:
                The class of the round to start, default Round1.
            lives:
                Optional number of lives for the player, default 3.
                One extra life is added at the start and consumed when
                the paddle materialises, so the player sees the
                "extra life spent" animation before gameplay begins.
        """
        # Keep track of the score and lives throughout the game.
        self.lives = lives + 1
        self.score = 0
        # Extra life thresholds: first at 20K, then every 60K.
        self._next_extra_life = 20000

        # Reference to the main screen.
        self._screen = pygame.display.get_surface()

        # The life graphic.
        self._life_img, _ = load_png('paddle_life.png')
        # The life graphic positions.
        self._life_rects = []

        # The current round. TOP_OFFSET is already scaled against the
        # active display resolution, so the round's top edge is
        # positioned consistently regardless of resolution.
        self.round = round_class(TOP_OFFSET)

        # The sprites in the game.
        # Calculate proper offsets for paddle movement area
        left_boundary = self.round.edges.left.rect.right
        right_boundary = self.round.edges.right.rect.left
        left_offset = left_boundary
        right_offset = self._screen.get_width() - right_boundary
        
        self.paddle = Paddle(left_offset=left_offset,
                             right_offset=right_offset,
                             bottom_offset=s(60),
                             speed=PADDLE_SPEED)

        ball = Ball(start_pos=self.paddle.rect.midtop,
                    start_angle=BALL_START_ANGLE_RAD,
                    base_speed=BALL_BASE_SPEED,
                    top_speed=BALL_TOP_SPEED,
                    normalisation_rate=BALL_SPEED_NORMALISATION_RATE,
                    off_screen_callback=self._off_screen)

        # The game starts with a single ball in play initially.
        self.balls = [ball]

        # The currently applied powerup, if any.
        self.active_powerup = None

        # The current enemies in the game.
        self.enemies = []

        # Hold a reference to all the sprites for redrawing purposes.
        self.sprites = []

        # Create event handlers required by the game.
        self._create_event_handlers()

        # Whether the game is finished.
        self.over = False

        # Whether the game is currently paused. While paused, the
        # state machine and sprite updates are frozen and a
        # translucent overlay is drawn on top of the last frame.
        # The flag is toggled by the ``K_p`` KEYUP handler and by
        # the gamepad's menu / view button (polled in
        # :meth:`update`).
        self.paused = False
        # Whether the game was paused on the previous frame.
        # Used by :meth:`update` to detect the paused ->
        # unpaused transition so it can repaint the play area
        # with the round background and clear the pause overlay
        # (translucent dim layer + PAUSED text) that was drawn
        # on top of it - otherwise the overlay would persist as
        # artifacts (faded text, dimmed bricks) until something
        # else happened to overwrite that part of the screen.
        self._was_paused = False

        # Whether the quit-prompt overlay is active.  When True the
        # pause overlay shows "Quit game?  Y / N" instead of the
        # usual "PAUSED" caption.  Y ends the game and returns to the
        # start screen; N or a second ESC press resumes play.
        self._quit_prompt = False

        # Pre-created shadow surfaces (lazily initialized)
        self._brick_shadow = None
        self._ball_shadows = {}
        self._enemy_shadows = {}
        self._left_wall_shadow = None
        self._right_wall_shadow = None
        self._top_wall_shadow = None

        # The current game state which handles the behaviour for the
        # current stage of the game.
        self.state = GameStartState(self)

        # === Side-area starfield ========================================
        # The same outward-drifting starfield used on the start screen,
        # restricted to the left and right side areas outside the play
        # area.  The stars are drawn directly on the main screen surface
        # before the play-area background is blitted, so they appear
        # behind the game field.
        self._stars = []
        self._star_center_x = self._screen.get_width() // 2
        self._star_center_y = self._screen.get_height() // 2
        self._star_speed_choices = [0.1, 0.15, 0.4, 0.6]
        self._star_count = 100
        self._star_flicker_chance = 0.01
        self._init_stars()

    def update(self):
        """Update the state of the running game."""
        # === Side-area starfield ========================================
        # Draw the outward-drifting stars in the left and right side
        # areas BEFORE anything else so they appear behind the play
        # area background, the pause overlay and all sprites.
        self._update_and_draw_stars()

        # === Gamepad menu / view button (pause toggle) =================
        # Polled here rather than wired as a KEYUP handler because
        # pygame does not dispatch KEYUP-equivalent events for
        # gamepad buttons - the wrapper tracks button rising edges
        # internally and reports them once per frame through
        # :attr:`Gamepad.menu_pressed`. Doing this BEFORE the
        # ``self.paused`` check means a second press of the menu
        # button while the overlay is shown immediately resumes
        # the game, matching the keyboard P-key behaviour.
        if get_gamepad().menu_pressed:
            self.paused = not self.paused

        if self.paused:
            # While paused, freeze the state machine and the
            # sprite updates.  Restore the clean round background
            # first so the translucent dim layer is always drawn on
            # top of the same base image — otherwise each frame
            # stacks another semi-transparent layer, making the
            # screen progressively darker and leaving artifacts
            # when the player resumes.
            self._screen.blit(self.round.background, self._play_area_rect(),
                              self._play_area_rect())
            self._draw_pause_overlay()
            self._was_paused = True
            return

        # === Resume from pause =======================================
        # The pause overlay was drawn directly on the screen on
        # top of the play area: a translucent dim layer plus the
        # "PAUSED" caption and the resume hint. None of that is
        # part of the sprite erase-redraw cycle, so without
        # intervention the overlay would remain as visual
        # artifacts (faded text, dimmed bricks, ball-trail-like
        # smudges) until something else happened to overwrite
        # those pixels. Detect the paused -> unpaused transition
        # via ``self._was_paused`` and repaint the play area
        # with the clean round background before the regular
        # update runs. The blit is restricted to the play area
        # so the header (logo + score titles) drawn by the main
        # loop above the game is left untouched.
        if self._was_paused:
            self._screen.blit(self.round.background, self._play_area_rect(),
                              self._play_area_rect())
            self._was_paused = False

        # Delegate to the active state. This determines the behaviour
        # for the current stage of the game.
        self.state.update()

        # Paint only the play area of the round background before the
        # sprites are redrawn. Without this, only the sprite rects
        # get repainted (via the per-sprite erase in
        # :meth:`_update_sprites`), so the play area stays black
        # everywhere a sprite has not just been - most visibly where a
        # brick was destroyed or a powerup has moved on. The blit is
        # restricted to the play area (between the side walls and
        # below the top edge) so the logo and 1UP / HIGH SCORE
        # header drawn by the main loop above the game is left
        # untouched.
        play_area = self._play_area_rect()
        self._screen.blit(self.round.background, play_area, play_area)

        # Re-render the sprites.
        self._update_sprites()
        self._update_lives()

    def _draw_pause_overlay(self):
        """Draw the in-game pause overlay.

        A semi-transparent dark layer is blitted over the *play
        area only* (not the header with the logo and score
        titles), and a centred "PAUSED" caption plus a smaller
        hint about how to resume is drawn on top. The hint text
        mentions whichever input devices are actually available
        (keyboard P, gamepad menu button) so the player is never
        told to press a button they do not have.

        Limiting the dim to the play area keeps the header
        untouched by the overlay - the logo and score labels
        stay fully visible (so the player keeps seeing their
        score while paused) and, more importantly, the header
        pixels do not need to be restored on resume.
        """
        screen = self._screen
        screen_w, screen_h = screen.get_size()

        # === Dim layer (play area only) ===============================
        # The dim covers the play area (from the top edge down to
        # the bottom of the screen, between the side walls).
        # The header (the strip at the top of the screen, where
        # the logo and score titles sit) is deliberately left
        # untouched, for two reasons:
        #
        #   1. it keeps the logo and the 1UP / HIGH SCORE
        #      labels fully visible while the game is paused,
        #      so the player can still see their score;
        #   2. on resume we blit ``self.round.background`` over
        #      the play area to clear the dim and the PAUSED
        #      text, and that blit does not cover the header
        #      anyway. Leaving the dim out of the header in the
        #      first place avoids having to remember to restore
        #      it as a separate step.
        play_area = pygame.Rect(
            LAYOUT.offset_x, self.round.top_offset,
            screen_w - 2 * LAYOUT.offset_x,
            screen_h - self.round.top_offset)
        dim = pygame.Surface(play_area.size, pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        screen.blit(dim, play_area.topleft)

        # Big "PAUSED" caption, centred horizontally on the screen
        # and placed just above the screen midpoint so there is
        # room for the resume hint below it. The screen midpoint
        # is well within the play area for every round (the
        # ``top_offset`` keeps the bricks below the header), so
        # the text is always drawn on top of the dim layer.
        if self._quit_prompt:
            ptext.draw('QUIT GAME?',
                       center=(screen_w // 2, screen_h // 2 - s(40)),
                       fontname=MAIN_FONT,
                       fontsize=s(96),
                       color=(255, 255, 255),
                       shadow=(1.0, 1.0),
                       scolor='grey')
            hint = 'Y = quit    N / ESC = resume'
        else:
            ptext.draw('PAUSED',
                       center=(screen_w // 2, screen_h // 2 - s(40)),
                       fontname=MAIN_FONT,
                       fontsize=s(96),
                       color=(255, 255, 255),
                       shadow=(1.0, 1.0),
                       scolor='grey')
            if get_gamepad().connected:
                hint = 'press P or the menu button to resume'
            else:
                hint = 'press P to resume'
        ptext.draw(hint, center=(screen_w // 2, screen_h // 2 + s(50)),
                   fontname=ALT_FONT,
                   fontsize=s(24),
                   color=(200, 200, 200))

    def _init_stars(self):
        """Populate the side-area starfield with initial stars."""
        screen_w, screen_h = self._screen.get_size()
        self._star_center_x = screen_w // 2
        self._star_center_y = screen_h // 2
        for _ in range(self._star_count):
            star = [0, 0, 0, 0, 0, True]
            self._reset_star(star)
            self._stars.append(star)

    def _reset_star(self, star):
        """Re-seed a star with a fresh random position and direction,
        confined to the left or right side area outside the play field."""
        screen_w, screen_h = self._screen.get_size()
        left_edge = self.round.edges.left.rect.right
        right_edge = self.round.edges.right.rect.left
        side_w = left_edge  # width of each side strip

        # Decide which side: 0 = left, 1 = right
        side = random.randint(0, 1)
        if side == 0:
            star[0] = random.uniform(0, side_w)
        else:
            star[0] = random.uniform(right_edge, screen_w)
        star[1] = random.uniform(0, screen_h)

        dx = star[0] - self._star_center_x
        dy = star[1] - self._star_center_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            star[2], star[3] = 1.0, 0.0
        else:
            star[2], star[3] = dx / dist, dy / dist
        star[4] = random.choice(self._star_speed_choices)
        star[5] = True

    def _update_and_draw_stars(self):
        """Advance every side-area star and draw it on the screen.

        Stars that drift into the play area are simply not drawn
        (they will be respawned once they leave the screen bounds).
        """
        screen_w, screen_h = self._screen.get_size()
        left_edge = self.round.edges.left.rect.right
        right_edge = self.round.edges.right.rect.left

        for star in self._stars:
            star[0] += star[2] * star[4]
            star[1] += star[3] * star[4]

            if random.random() < self._star_flicker_chance:
                star[5] = not star[5]

            if (star[0] < -2 or star[0] > screen_w + 2 or
                    star[1] < -2 or star[1] > screen_h + 2):
                self._reset_star(star)
                continue

            # Only draw if the star is in a side area (outside the
            # play-area walls) so it doesn't overlap the game field.
            in_left = star[0] < left_edge
            in_right = star[0] > right_edge
            if star[5] and (in_left or in_right):
                pygame.draw.circle(self._screen, (255, 255, 255),
                                   (int(star[0]), int(star[1])), 1)

    def _update_sprites(self):
        """Erase the sprites, update their state, and then redraw them
        on the screen.
        """
        # Erase.
        for sprite in self.sprites:
            self._screen.blit(self.round.background, sprite.rect, sprite.rect)

        # Update all sprites first so positions are current.
        for sprite in self.sprites:
            sprite.update()

        # Redraw wall shadows (erased sprites may have removed parts of them).
        self._draw_wall_shadows()

        # Draw gradient shadows for bricks, ball and enemies.
        for sprite in self.sprites:
            if sprite.visible:
                if isinstance(sprite, Brick):
                    if self._brick_shadow is None:
                        bw, bh = sprite.rect.width, sprite.rect.height
                        sw = bw + bw // 2
                        sh = bh + bh
                        self._brick_shadow = pygame.Surface(
                            (sw, sh), pygame.SRCALPHA)
                        for py in range(sh):
                            ay = int(255 * (1 - py / sh))
                            for px in range(sw):
                                ax = int(255 * (1 - px / sw))
                                a = ax * ay // 255
                                if a > 0:
                                    pygame.draw.line(
                                        self._brick_shadow,
                                        (0, 0, 0, a), (px, py), (px, py))
                    self._screen.blit(self._brick_shadow,
                                      (sprite.rect.x, sprite.rect.y))
                elif isinstance(sprite, Ball):
                    shadow_key = id(sprite.image)
                    if shadow_key not in self._ball_shadows:
                        self._ball_shadows[shadow_key] = \
                            self._make_sprite_shadow(sprite.image)
                    self._screen.blit(self._ball_shadows[shadow_key],
                                      (sprite.rect.x, sprite.rect.y))
                elif isinstance(sprite, Enemy):
                    if sprite.image is not None:
                        shadow_key = id(sprite.image)
                        if shadow_key not in self._enemy_shadows:
                            self._enemy_shadows[shadow_key] = \
                                self._make_sprite_shadow(sprite.image)
                        self._screen.blit(self._enemy_shadows[shadow_key],
                                          (sprite.rect.x, sprite.rect.y))

        # Draw sprites on top of shadows.
        for sprite in self.sprites:
            if sprite.visible:
                self._screen.blit(sprite.image, sprite.rect)

    def _make_sprite_shadow(self, image):
        """Create a gradient shadow surface from a sprite image.

        The shadow preserves the alpha mask of the source image and
        applies a 2D linear gradient (dark at top-left, transparent
        at bottom-right).
        """
        w, h = image.get_size()
        img_data = pygame.image.tostring(image.convert_alpha(), 'RGBA')
        shadow_data = bytearray(w * h * 4)
        for py in range(h):
            row_off = py * w * 4
            for px in range(w):
                idx = row_off + px * 4
                alpha = img_data[idx + 3]
                if alpha > 0:
                    ax = int(255 * (1 - px / w))
                    ay = int(255 * (1 - py / h))
                    a = alpha * ax * ay // (255 * 255)
                    shadow_data[idx] = 0
                    shadow_data[idx + 1] = 0
                    shadow_data[idx + 2] = 0
                    shadow_data[idx + 3] = a
        return pygame.image.fromstring(bytes(shadow_data), (w, h), 'RGBA')

    def _draw_wall_shadows(self):
        """Draw shadows cast by the walls into the play area."""
        edges = self.round.edges
        play_area = self._play_area_rect()

        # Left wall shadow - gradient fading from dark near wall to transparent
        if self._left_wall_shadow is None:
            shadow_w = s(20)
            shadow_h = play_area.height
            self._left_wall_shadow = pygame.Surface(
                (shadow_w, shadow_h), pygame.SRCALPHA)
            for i in range(shadow_w):
                alpha = int(100 * (1 - i / shadow_w))
                pygame.draw.line(self._left_wall_shadow,
                                 (0, 0, 0, alpha),
                                 (i, 0), (i, shadow_h))
        self._screen.blit(self._left_wall_shadow,
                          (edges.left.rect.right, play_area.top))

        # Right wall shadow - gradient fading from dark near wall to transparent
        if self._right_wall_shadow is None:
            shadow_w = s(20)
            shadow_h = play_area.height
            self._right_wall_shadow = pygame.Surface(
                (shadow_w, shadow_h), pygame.SRCALPHA)
            for i in range(shadow_w):
                alpha = int(100 * (i / shadow_w))
                pygame.draw.line(self._right_wall_shadow,
                                 (0, 0, 0, alpha),
                                 (i, 0), (i, shadow_h))
        self._screen.blit(self._right_wall_shadow,
                          (edges.right.rect.left - s(20), play_area.top))

        # Top wall shadow - gradient fading from dark near wall to transparent
        if self._top_wall_shadow is None:
            shadow_w = play_area.width
            shadow_h = s(40)
            self._top_wall_shadow = pygame.Surface(
                (shadow_w, shadow_h), pygame.SRCALPHA)
            for j in range(shadow_h):
                alpha = int(100 * (1 - j / shadow_h))
                pygame.draw.line(self._top_wall_shadow,
                                 (0, 0, 0, alpha),
                                 (0, j), (shadow_w, j))
        self._screen.blit(self._top_wall_shadow,
                          (play_area.left, edges.top.rect.bottom))

    def _play_area_rect(self):
        """Return the screen-space rectangle of the play area.

        The play area is the region bounded by the side walls and
        below the top edge - i.e. the rectangle the round's
        background is filled with. Used by the per-frame background
        blit in :meth:`update` and by the pause overlay in
        :meth:`_draw_pause_overlay` to make sure neither of those
        operations touches the header (logo + 1UP / HIGH SCORE)
        drawn by the main loop above the game.
        """
        edges = self.round.edges
        return pygame.Rect(
            edges.left.rect.right,
            edges.top.rect.bottom,
            edges.right.rect.left - edges.left.rect.right,
            self._screen.get_height() - edges.top.rect.bottom)

    def _update_lives(self):
        """Update the number of remaining lives displayed on the screen."""
        # Erase the existing lives.
        for rect in self._life_rects:
            self._screen.blit(self.round.background, rect, rect)
        self._life_rects.clear()
        # Display the remaining lives. The padding between/around the
        # life icons is scaled from the reference resolution so the
        # icons look correctly spaced at any display size.
        left = self.round.edges.left.rect.right
        top = self._screen.get_height() - self._life_img.get_height() - s(5)

        for life in range(self.lives - 1):
            self._life_rects.append(
                self._screen.blit(self._life_img, (left, top)))
            left += self._life_img.get_width() + s(5)

    def _check_extra_life(self):
        """Grant an extra life when the score crosses a threshold.

        The first extra life is awarded at 20,000 points, then every
        60,000 points after that (80K, 140K, 200K, ...).
        """
        if self.score >= self._next_extra_life:
            self.lives += 1
            self._next_extra_life += 60000
            self._draw_lives()

    def on_brick_collide(self, brick, sprite):
        """Called by a sprite when it collides with a brick.

        In this case a sprite might be the ball, or a laser beam from the
        laser paddle.

        Args:
            brick:
                The Brick instance the sprite collided with.
            sprite:
                The sprite instance that struck the brick.
        """
        # Increment the collision count.
        brick.collision_count += 1

        # Play the appropriate brick-hit sound.
        if brick.colour == BrickColour.gold or \
                (brick.colour == BrickColour.silver and
                 brick.collision_count == 1):
            play_gold_block_hit()
        else:
            play_block_hit()

        # Has the brick been destroyed, based on the collision count?
        if brick.visible:
            # Still visible, so animate to indicate strike.
            brick.animate()
        else:
            # Brick has been destroyed.
            if brick.value:
                # Add this brick's value to the score.
                self.score += brick.value
                self._check_extra_life()

            # Tell the round that a brick has gone, so that it can decide
            # whether the round is completed.
            self.round.brick_destroyed()

        if brick.powerup_cls:
            # There is a powerup in the brick.
            # Figure out whether we should release it.
            release = not brick.visible  # Always release on brick destruction

            if not release:
                # Brick hasn't been destroyed, so randomly decide whether
                # to release or not.
                release = random.choice((True, False))

            if release:
                powerup = brick.powerup_cls(self, brick)
                brick.powerup_cls = None

                # Display the powerup.
                self.sprites.append(powerup)

        if not self.enemies and self.round.can_release_enemies():
            # Setup the enemy sprites.
            self._setup_enemies()

            # Release them into the game.
            # Note that once an enemy is destroyed, it will call
            # Game.release_enemy() itself to respawn itself.
            for enemy in self.enemies:
                self.release_enemy(enemy)

    def on_enemy_collide(self, enemy, sprite):
        """Called by a sprite when it collides with an enemy.

        In this case a sprite might be the ball, or a laser beam from the
        laser paddle.

        Args:
            enemy:
                The Enemy instance the sprite collided with.
            sprite:
                The sprite instance that struck the enemy.
        """
        enemy.explode()
        play_enemy_explode()
        self.score += 500
        self._check_extra_life()
        # Temporarily remove the enemy sprites from the balls to prevent
        # the balls from colliding with the explosion. The enemy sprites
        # are re-added to the balls when they are re-released.
        for ball in self.balls:
            ball.remove_collidable_sprite(enemy)

    def _setup_enemies(self):
        """Set up the enemy sprites ready for release into the game."""
        collidable_sprites = []
        collidable_sprites += self.round.edges
        collidable_sprites += self.round.bricks

        for _ in range(self.round.num_enemies):
            # Create the sprite.
            enemy_sprite = Enemy(self.round.enemy_type,
                                 self.paddle,
                                 self.on_enemy_collide,
                                 collidable_sprites,
                                 on_destroyed=self.release_enemy)

            # Keep track of the enemy sprites currently in the game.
            self.enemies.append(enemy_sprite)

            # Allow the sprite to be displayed.
            self.sprites.append(enemy_sprite)

    def release_enemy(self, enemy):
        """Release an enemy through one of the top doors.

        Note that this method runs asynchronously and the enemy is not
        necessarily released immediately, but after a short random delay.
        The door from which the enemy is released is selected at random.

        Args:
            enemy:
                The enemy sprite to release through one of the doors.
        """
        # Conceal the enemy until the door opens.
        enemy.freeze = True
        enemy.visible = False

        # Callback called when the door is opened.
        def door_open(coords):
            enemy.reset()  # Show the enemy and re-init its movement.
            enemy.rect.topleft = coords
            # Tell the ball(s) about it.
            for ball in self.balls:
                ball.add_collidable_sprite(enemy,
                                           on_collide=self.on_enemy_collide)

        # Trigger opening the door.
        self.round.edges.top.open_door(door_open)

    def _off_screen(self, ball):
        """Callback called by a ball when it goes offscreen.

        Args:
            ball:
                The ball that left the screen.
        """
        if len(self.balls) > 1:
            # There are multiple balls in play, so just take this ball
            # out of play.
            self.balls.remove(ball)
            self.sprites.remove(ball)
            ball.visible = False
        else:
            # This ball is the last in play, so transition to the
            # BallOffScreenState which handles end of life.
            if not isinstance(self.state, BallOffScreenState):
                self.state = BallOffScreenState(self)

    def _create_event_handlers(self):
        """Create the event handlers for paddle movement."""
        keys_down = 0

        def move_left(event):
            nonlocal keys_down
            if event.key in (pygame.K_LEFT, pygame.K_a):
                self.paddle.move_left()
                keys_down += 1
        self.handler_move_left = move_left

        def move_right(event):
            nonlocal keys_down
            if event.key in (pygame.K_RIGHT, pygame.K_d):
                self.paddle.move_right()
                keys_down += 1
        self.handler_move_right = move_right

        def stop(event):
            nonlocal keys_down
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT,
                              pygame.K_a, pygame.K_d):
                if keys_down > 0:
                    keys_down -= 1
                if keys_down == 0:
                    self.paddle.stop()
        self.handler_stop = stop

        def toggle_pause(event):
            """Toggle the in-game pause overlay on P key release.

            ``K_p`` (and the gamepad's menu / view button, polled
            separately each frame in :meth:`Game.update`) flips
            :attr:`Game.paused`; the main loop freezes the
            state-machine and sprite updates while that flag is
            set, and the pause overlay is drawn on top of the
            frozen frame.
            """
            if event.key == pygame.K_p:
                self.paused = not self.paused
                self._quit_prompt = False
        self.handler_toggle_pause = toggle_pause

        def handle_esc(event):
            """ESC opens the quit-prompt overlay; a second ESC dismisses it."""
            if event.key == pygame.K_ESCAPE:
                if not self._quit_prompt:
                    self._quit_prompt = True
                    self.paused = True
                else:
                    self._quit_prompt = False
                    self.paused = False
        self.handler_esc = handle_esc

        def handle_quit_response(event):
            """Y / N responses while the quit-prompt overlay is shown."""
            if not self._quit_prompt:
                return
            if event.key == pygame.K_y:
                self._quit_prompt = False
                self.paused = False
                for b in self.balls:
                    b.speed = 0
                    b.visible = False
                self.paddle.visible = False
                self.over = True
            elif event.key == pygame.K_n:
                self._quit_prompt = False
                self.paused = False
        self.handler_quit_response = handle_quit_response

    @property
    def ball(self):
        """A convenience attribute for accessing the primary ball in the game.

        This is really just an convenient alias so client code doesn't have to
        do game.balls[0] everywhere.

        Returns:
            The priamry ball in the game, or None if no balls currently in
            play.
        """
        try:
            return self.balls[0]
        except IndexError:
            return None

    def __repr__(self):
        class_name = type(self).__name__
        return '{}(round_class={}, lives={})'.format(
            class_name,
            type(self.round).__name__,
            self.lives)


class BaseState:
    """Abstract base class holding behaviour common to all states."""

    def __init__(self, game):
        self.game = game

        LOG.debug('Entered {}'.format(type(self).__name__))

    def update(self):
        """Update the state.

        Sub-states must implement this to perform their state specific
        behaviour. This method is called repeatedly by the main game loop.
        """
        raise NotImplementedError('Subclasses must implement update()')

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r})'.format(class_name, self.game)


class GameStartState(BaseState):
    """This state handles the behaviour after the user has begun a new game,
    but before they actually start playing it, e.g. showing an animation
    sequence.
    """

    def __init__(self, game):
        super().__init__(game)

        # The ball and paddle are kept invisible at the very start.
        self.game.paddle.visible = False
        self.game.ball.visible = False

        # Register the event handlers for paddle control.
        receiver.register_handler(pygame.KEYDOWN,
                                  self.game.handler_move_left,
                                  self.game.handler_move_right)
        receiver.register_handler(pygame.KEYUP, self.game.handler_stop)
        # Register the in-game pause toggle (P key). The gamepad's
        # menu / view button is polled in :meth:`Game.update`
        # rather than wired as an event handler, because pygame
        # does not dispatch KEYUP events for gamepad buttons.
        receiver.register_handler(pygame.KEYUP,
                                  self.game.handler_toggle_pause)
        receiver.register_handler(pygame.KEYUP,
                                  self.game.handler_esc)
        receiver.register_handler(pygame.KEYUP,
                                  self.game.handler_quit_response)

    def update(self):
        # TODO: implement the game intro sequence (animation).
        self.game.state = RoundStartState(self.game)


class RoundStartState(BaseState):
    """This state handles the behaviour that happens at the very beginning of
    a round and just before the real gameplay begins.

    This state initialises the sprites so they are set up ready for a new
    round to begin.
    """

    def __init__(self, game, consume_startup_life=True):
        super().__init__(game)

        # Set up the sprites for the round.
        self._setup_sprites()

        # Set up the ball and paddle.
        self._configure_ball()
        self._configure_paddle()

        # Initialise the sprites' display state.
        self._screen = pygame.display.get_surface()
        self.game.ball.reset()
        self.game.paddle.visible = False
        self.game.ball.visible = False
        # Anchor the ball whilst it's invisible. The vertical position is
        # scaled from the reference resolution so the ball sits the
        # same proportional distance above the bottom of the screen
        # regardless of resolution.
        anchor_x = self._screen.get_width() / 2
        anchor_y = self._screen.get_height() - s(100)
        self.game.ball.anchor((anchor_x, anchor_y))

        # Whether we've reset the paddle
        self._paddle_reset = False

        # Keep track of the number of update cycles.
        self._update_count = 0

        # === Manual ball release =========================================
        # The ball sits on the paddle from frame 200 onwards and is
        # normally released automatically at frame 340. To match the
        # behaviour of the catch powerup (and what players expect
        # from Arkanoid), we also let the player release the ball
        # manually by pressing Space (keyboard) or A / Cross
        # (gamepad). The release handlers are registered here and
        # torn down in :meth:`_release_ball` once the ball is
        # released - whether by the player or by the automatic
        # timeout - so they don't leak across state transitions.
        self._released = False
        # The ball is not yet on the paddle (it is anchored to a
        # fixed off-paddle position), so the manual release is
        # disabled until the ball is anchored to the paddle in
        # :meth:`update`. Pressing Space before then is a no-op.
        self._can_release = False
        # Whether the extra startup life should be consumed when the
        # paddle materialises.  True for the initial round start,
        # False for RoundRestartState and subsequent rounds.
        self._consume_startup_life = consume_startup_life
        receiver.register_handler(pygame.KEYUP, self._on_release_keyup)
        self._gamepad_listener = _RoundStartGamepadListener(self)
        self.game.sprites.append(self._gamepad_listener)

    def _setup_sprites(self):
        """Make all the sprites available for rendering."""
        self.game.sprites.clear()
        self.game.sprites.append(self.game.paddle)
        self.game.sprites.append(self.game.ball)
        self.game.sprites += self.game.round.edges
        self.game.sprites += self.game.round.bricks

    def _configure_ball(self):
        self.game.ball.remove_all_collidable_sprites()

        for edge in self.game.round.edges:
            # Every collision with a wall momentarily increases the speed
            # of the ball.
            self.game.ball.add_collidable_sprite(
                edge,
                speed_adjust=WALL_SPEED_ADJUST)

        self.game.ball.add_collidable_sprite(
            self.game.paddle,
            bounce_strategy=self.game.paddle.bounce_strategy,
            on_collide=self.game.paddle.on_ball_collide)

        for brick in self.game.round.bricks:
            # Make the ball aware of the bricks it might collide with.
            # Every brick collision momentarily increases the speed of
            # the ball.
            self.game.ball.add_collidable_sprite(
                brick,
                speed_adjust=BRICK_SPEED_ADJUST,
                on_collide=self.game.on_brick_collide)

        # Make any round-specific adjustments to the ball.
        self.game.ball.base_speed += self.game.round.ball_base_speed_adjust
        self.game.ball.normalisation_rate += \
            self.game.round.ball_speed_normalisation_rate_adjust

    def _configure_paddle(self):
        # Make any round-specific adjustments to the paddle.
        self.game.paddle.speed += self.game.round.paddle_speed_adjust

    def update(self):
        """Handle the sequence of events that happen at the beginning of a
        round just before gameplay starts.
        """
        caption, ready = None, None

        if self._update_count > 100:
            # Display the caption after a short delay. Both the x
            # position of the caption and its vertical offset from the
            # paddle centre are scaled from the reference resolution.
            caption = ptext.draw(self.game.round.name,
                                 (sx(235),
                                  self.game.paddle.rect.center[1] - s(150)),
                                 fontname=MAIN_FONT,
                                 fontsize=s(24),
                                 color=(255, 255, 255))
            if self._update_count == 101:
                play_level_start()
        if self._update_count > 200:
            # Display the "Ready" message.
            ready = ptext.draw('ready',
                               (sx(250), caption[1][1] + s(50)),
                               fontname=MAIN_FONT,
                               fontsize=s(24),
                               color=(255, 255, 255))
            # Anchor the ball to the paddle.
            self.game.ball.anchor(self.game.paddle,
                                  (self.game.paddle.rect.width // 2,
                                   -self.game.ball.rect.height))
            # Display the sprites.
            if not self._paddle_reset:
                self.game.paddle.reset()
                self._paddle_reset = True
            self.game.paddle.visible = True
            self.game.ball.visible = True
            # The ball is now sitting on the visible paddle, so the
            # player can release it manually with Space / A.
            self._can_release = True
        if self._update_count == 201:
            # Consume the extra startup life — the player saw one
            # more life icon on screen before this point; now the
            # paddle materialises and that life is "spent".
            if self._consume_startup_life:
                self.game.lives -= 1
            # Animate the paddle materializing onto the screen.
            self.game.paddle.transition(MaterializeState(self.game.paddle))
            # Animate the bricks
            for brick in self.game.round.bricks:
                brick.animate()
        if self._update_count > 310:
            # Erase the text.
            self._screen.blit(self.game.round.background, caption[1])
            self._screen.blit(self.game.round.background, ready[1])
        if self._update_count > 340:
            # Release the anchor. Uses the same code path as the
            # manual release so the handlers are torn down either
            # way.
            self._release_ball()

        self._update_count += 1

        # Don't let the paddle move when it's not displayed.
        if not self.game.paddle.visible:
            self.game.paddle.stop()

    def _on_release_keyup(self, event):
        """KEYUP handler that releases the ball on Space.

        Only active once the ball is anchored to the paddle (see
        ``_can_release`` in :meth:`update`).
        """
        if event.key == pygame.K_SPACE:
            self._release_ball()

    def _release_ball(self):
        """Release the anchored ball and transition to gameplay.

        Idempotent: subsequent calls (e.g. the player pressing
        Space a second time after the automatic release has
        already fired) are no-ops. Tearing down the KEYUP handler
        and the gamepad polling sprite here means the release
        mechanism never leaks beyond the round-start state,
        regardless of whether the release was triggered manually
        or by the automatic timeout in :meth:`update`.
        """
        if self._released:
            return
        if not self._can_release:
            return
        self._released = True
        # Drop the release listeners before we hand control over to
        # RoundPlayState, so the next state doesn't inherit stale
        # handlers.
        receiver.unregister_handler(self._on_release_keyup)
        if (self._gamepad_listener is not None
                and self._gamepad_listener in self.game.sprites):
            self.game.sprites.remove(self._gamepad_listener)
        self._gamepad_listener = None
        # Release the ball at the configured start angle and switch
        # to the live-play state.
        self.game.ball.release(BALL_START_ANGLE_RAD)
        self.game.state = RoundPlayState(self.game)


class _RoundStartGamepadListener(pygame.sprite.Sprite):
    """Per-frame polling sprite that releases the ball on the
    A / Cross gamepad button.

    Mirrors :class:`_GamepadCatchReleaseListener` from the catch
    powerup: pygame does not generate KEYUP events for gamepad
    buttons, so the round-start state adds one of these listeners
    to ``self.game.sprites`` on entry and removes it in
    :meth:`RoundStartState._release_ball`. The listener's
    ``update()`` is invoked by ``Game._update_sprites()`` every
    frame while the round-start state is active, giving us a
    reliable per-frame poll of the A button.
    """

    def __init__(self, state):
        super().__init__()
        self._state = state
        # 1x1 placeholder surface. The sprite is never visible
        # so this is purely cosmetic.
        self.image = pygame.Surface((1, 1))
        self.image.set_alpha(0)
        self.rect = pygame.Rect(0, 0, 1, 1)
        self.visible = False

    def update(self):
        # Local import to avoid a circular import between the
        # gamepad wrapper and the round-start state.
        from arkanoid.game import get_gamepad
        if get_gamepad().fire_pressed:
            self._state._release_ball()


class RoundPlayState(BaseState):
    """This state is active when the game is running and the user is
    controlling the paddle and ball.
    """

    def __init__(self, game):
        super().__init__(game)

    def update(self):
        if self.game.round.complete:
            self.game.state = RoundEndState(self.game)


class BallOffScreenState(BaseState):
    """This state handles what happens when gameplay stops due to the
    ball going offscreen.
    """

    def __init__(self, game):
        super().__init__(game)

        # Deactivate the active powerup if set.
        if self.game.active_powerup:
            self.game.active_powerup.deactivate()
            self.game.active_powerup = None

        # Tell the paddle to explode.
        self.game.paddle.transition(
            ExplodingState(self.game.paddle, self._exploded))
        self._explode_complete = False

    def update(self):
        # Wait for the explosion animation to complete.
        if self._explode_complete:
            if self.game.lives - 1 > 0:
                self.game.state = RoundRestartState(self.game)
            else:
                self.game.state = GameEndState(self.game)

    def _exploded(self):
        self._explode_complete = True


class RoundRestartState(RoundStartState):
    """Specialisation of RoundStartState that handles the behaviour when a
    round is restarted due to the ball going off screen.
    """

    def __init__(self, game):
        super().__init__(game, consume_startup_life=False)

        # The new number of lives since restarting.
        self._lives = game.lives - 1

        # Conceal any enemy sprites.
        for enemy in self.game.enemies:
            enemy.freeze = True
            enemy.visible = False

        # Cancel any existing open door requests.
        self.game.round.edges.top.cancel_open_door()

        # Whether the enemies have been re-released for this round restart.
        self._enemies_rereleased = False

    def _setup_sprites(self):
        # No need to setup the sprites again on round restart.
        pass

    def _configure_ball(self):
        # No need to configure the ball again on round restart.
        pass

    def _configure_paddle(self):
        # No need to configure the paddle again on round restart.
        pass

    def update(self):
        # Run the logic in the RoundStartState first.
        super().update()

        if self._update_count > 100:
            # Update the number of lives when we display the caption.
            self.game.lives = self._lives
        if self._update_count > 340:
            # Re-release any enemies that were previously active.
            if not self._enemies_rereleased:
                for enemy in self.game.enemies:
                    self.game.release_enemy(enemy)
                self._enemies_rereleased = True


class RoundEndState(BaseState):
    """Transition effect between rounds.

    Phases:
      1. Fade the play area to black.                          (30 frames)
      2. Show a full-screen starfield with "Level X" text.    (120 frames)
      3. Fade from black to the new play area.                 (30 frames)
    """

    FADE_OUT_FRAMES = 30
    ANNOUNCE_FRAMES = 120
    FADE_IN_FRAMES = 30
    TOTAL_FRAMES = FADE_OUT_FRAMES + ANNOUNCE_FRAMES + FADE_IN_FRAMES

    def __init__(self, game):
        super().__init__(game)

        # Deactivate any active powerup.
        if self.game.active_powerup:
            self.game.active_powerup.deactivate()
            self.game.active_powerup = None

        # Determine the next round number for the announcement text.
        self._next_round_name = None
        if self.game.round.next_round is not None:
            self._next_round_name = self.game.round.next_round.__name__
            # e.g. 'Round2' -> 'Level 2'
            num = ''.join(c for c in self._next_round_name if c.isdigit())
            self._next_round_name = 'Level {}'.format(num)

        self._update_count = 0

        # Cache the screen surface (BaseState does not provide one).
        self._screen = self.game._screen

        # Full-screen starfield for the transition.
        self._stars = []
        self._star_center_x = self._screen.get_width() // 2
        self._star_center_y = self._screen.get_height() // 2
        self._star_speed_choices = [0.1, 0.15, 0.4, 0.6]
        self._star_count = 200
        self._star_flicker_chance = 0.01

        # Create a black overlay surface for fading.
        self._fade_surface = pygame.Surface(self._screen.get_size())
        self._fade_surface.fill((0, 0, 0))

    def _init_stars(self):
        """Populate the full-screen starfield."""
        screen_w, screen_h = self._screen.get_size()
        self._star_center_x = screen_w // 2
        self._star_center_y = screen_h // 2
        for _ in range(self._star_count):
            star = [0, 0, 0, 0, 0, True]
            self._reset_star(star)
            self._stars.append(star)

    def _reset_star(self, star):
        """Re-seed a star with a fresh random position and direction."""
        screen_w, screen_h = self._screen.get_size()
        star[0] = random.uniform(0, screen_w)
        star[1] = random.uniform(0, screen_h)
        dx = star[0] - self._star_center_x
        dy = star[1] - self._star_center_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            star[2], star[3] = 1.0, 0.0
        else:
            star[2], star[3] = dx / dist, dy / dist
        star[4] = random.choice(self._star_speed_choices)
        star[5] = True

    def _update_and_draw_stars(self):
        """Advance and draw the full-screen starfield."""
        screen_w, screen_h = self._screen.get_size()
        for star in self._stars:
            star[0] += star[2] * star[4]
            star[1] += star[3] * star[4]
            if random.random() < self._star_flicker_chance:
                star[5] = not star[5]
            if (star[0] < -2 or star[0] > screen_w + 2 or
                    star[1] < -2 or star[1] > screen_h + 2):
                self._reset_star(star)
                continue
            if star[5]:
                pygame.draw.circle(self._screen, (255, 255, 255),
                                   (int(star[0]), int(star[1])), 1)

    def update(self):
        count = self._update_count

        # Phase 1: fade out — darken the play area.
        if count < self.FADE_OUT_FRAMES:
            # Hide all gameplay sprites during the fade.
            for ball in self.game.balls:
                ball.speed = 0
                ball.visible = False
            self.game.paddle.visible = False
            for enemy in self.game.enemies:
                enemy.visible = False
            self.game.enemies.clear()
            self.game.round.edges.top.cancel_open_door()

            alpha = int(255 * count / self.FADE_OUT_FRAMES)
            self._fade_surface.set_alpha(alpha)
            self._screen.blit(self._fade_surface, (0, 0))

        # Phase 2: starfield + announcement text.
        elif count < self.FADE_OUT_FRAMES + self.ANNOUNCE_FRAMES:
            self._screen.fill((0, 0, 0))
            if not self._stars:
                self._init_stars()
            self._update_and_draw_stars()
            if self._next_round_name:
                ptext.draw(self._next_round_name,
                           center=(self._screen.get_width() // 2,
                                   self._screen.get_height() // 2),
                           fontname=ALT_FONT,
                           fontsize=s(72),
                           color=(255, 255, 255),
                           shadow=(2.0, 2.0),
                           scolor=(80, 80, 80))

        # Phase 3: fade in from black.
        elif count < self.TOTAL_FRAMES:
            progress = count - self.FADE_OUT_FRAMES - self.ANNOUNCE_FRAMES
            alpha = int(255 * (1.0 - progress / self.FADE_IN_FRAMES))
            self._fade_surface.set_alpha(alpha)
            self._screen.blit(self._fade_surface, (0, 0))

        # Transition complete — move to the next round.
        if count >= self.TOTAL_FRAMES:
            self.game.balls = self.game.balls[:1]
            if self.game.round.next_round is not None:
                self.game.round = self.game.round.next_round(TOP_OFFSET)
                self.game.state = RoundStartState(
                    self.game, consume_startup_life=False)
            else:
                self.game.state = GameEndState(self.game)

        self._update_count += 1

        self._update_count += 1


class GameEndState(BaseState):
    """This state handles the behaviour when the game ends, either due to all
    lives being lost, or when the player successfully reaches the very end.
    """

    def __init__(self, game):
        super().__init__(game)

        # Bring the ball back onto the screen, but hide it.
        # This prevents the offscreen callback from being called again.
        game.ball.anchor(game.paddle.rect.midtop)
        game.ball.visible = False

        # Indicate that the game is over.
        game.over = True

        # Unregister the event handlers.
        receiver.unregister_handler(self.game.handler_move_left,
                                    self.game.handler_move_right,
                                    self.game.handler_stop,
                                    self.game.handler_toggle_pause,
                                    self.game.handler_esc,
                                    self.game.handler_quit_response)

    def update(self):
        pass
