"""Gamepad / joystick support for Arkanoid.

This module wraps ``pygame.joystick`` and exposes a small object
that the rest of the game can talk to without needing to know about
pygame events directly. The wrapper:

* enumerates connected joysticks on startup and picks the first one;
* polls the joystick every frame and reports a normalised
  horizontal axis (``-1.0`` = fully left, ``0.0`` = centred,
  ``+1.0`` = fully right) with a small deadzone;
* detects button presses (rising edges only) and dispatches them
  as named "actions" the rest of the game can listen for;
* supports the standard XInput / DirectInput mapping used by most
  USB / Bluetooth controllers (Xbox, PlayStation, generic pads):

  - Left stick X axis / D-pad: paddle left/right
  - A / Cross button (button 0): fire (when the laser powerup
    is active) or "press" (start screen / accept level /
    start the game - the analog of the keyboard's Space key)
  - Start button (button 7): start the game (alternative to A
    on controllers that expose a dedicated Start button)
  - B / Circle button (button 1): release the ball (press once to
    launch it from the paddle at the start of a round)
  - Back / View / Select button (button 6): toggle pause while a
    round is in progress (the analog of pressing P on the keyboard)

If no joystick is connected the wrapper is a no-op: the rest of
the game can keep calling its methods and reading its attributes
without checking for a controller first.
"""

import logging
import math

import pygame

LOG = logging.getLogger(__name__)


# The index of the "A / Cross" button on a standard gamepad. This
# is button 0 on every common mapping (Xbox 360, Xbox One, PS3,
# PS4, generic DirectInput/XInput pads).
FIRE_BUTTON = 0
# The index of the "B / Circle" button. This is button 1 on a
# standard gamepad. We use it to release the ball from the
# paddle at the start of a round.
RELEASE_BUTTON = 1
# The index of the "Start" button. This is button 7 on the
# XInput layout, which is what most modern controllers expose.
START_BUTTON = 7
# The index of the "Back / View / Select" button. This is
# button 6 on the XInput layout. On Xbox controllers this is the
# View button (the one with two overlapping rectangles), on
# PlayStation 4 this is the Share button and on PlayStation 5
# it is the Create button. We use it as the dedicated
# "menu" / "pause" button - the analog of pressing P on the
# keyboard. Picking button 6 keeps it separate from the
# already-used Start button (button 7) on the start screen.
MENU_BUTTON = 6

# The horizontal axis of the left analog stick (axis 0 on every
# standard layout). The D-pad is exposed as a "hat" on most
# platforms - see ``_read_hat`` below.
LEFT_STICK_X_AXIS = 0

# Stick movement smaller than this (in the -1.0..+1.0 normalised
# range) is treated as "centred" - this prevents the paddle from
# drifting when the player takes their finger off the stick.
DEADZONE = 0.25

# A horizontal D-pad "hat" press is reported as ``(x, y)`` with
# each component in ``{-1, 0, +1}``. We only care about the X
# component (left/right).
DPAD_LEFT = -1
DPAD_RIGHT = +1


class Gamepad:
    """A thin wrapper around a single pygame joystick.

    The wrapper hides the difference between "no joystick is
    plugged in" and "joystick is plugged in but idle". All of its
    methods are safe to call when no joystick is connected; in
    that case they return neutral values (axis = 0, no buttons
    pressed this frame).
    """

    def __init__(self):
        # The active pygame joystick, or ``None`` if no controller
        # is currently connected. This is updated by
        # ``refresh`` whenever the connection state changes.
        self._joystick = None
        # Whether a button was pressed on the *previous* frame -
        # used to detect rising edges (button just went down).
        self._prev_buttons = set()
        # Whether the A/Cross button was pressed on the previous
        # frame. Kept as a flag for the "fire" action so the
        # paddle only fires once per button press (not on every
        # frame the button is held).
        self._prev_fire = False
        self._prev_start = False
        self._prev_release = False
        # Initialise the joystick subsystem and look for any
        # currently connected pads.
        pygame.joystick.init()
        self._init_joystick()

    def _init_joystick(self):
        """Find and initialise the first connected joystick.

        Called on construction and whenever the controller list
        changes (e.g. the player plugs in a pad after the game
        has already started). If no joysticks are connected this
        is a no-op.
        """
        count = pygame.joystick.get_count()
        if count == 0:
            self._joystick = None
            return
        # Use the first joystick. Arkanoid only needs one player,
        # so there is no need to manage multiple pads.
        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()
        LOG.info('Gamepad connected: %s (axes=%d, buttons=%d, hats=%d)',
                 self._joystick.get_name(),
                 self._joystick.get_numaxes(),
                 self._joystick.get_numbuttons(),
                 self._joystick.get_numhats())

    def refresh(self):
        """Re-scan for newly connected joysticks.

        Should be called once per frame from the main loop so
        that a controller plugged in after the game started is
        picked up automatically. If the previously-active pad
        has been disconnected, the wrapper reverts to the
        "no joystick" state.
        """
        if self._joystick is not None:
            # The active joystick may have been unplugged. The
            # easiest reliable check is to ask pygame how many
            # joysticks are still attached: if the count has
            # changed, re-init from scratch.
            if pygame.joystick.get_count() == 0:
                LOG.info('Gamepad disconnected')
                self._joystick = None
                self._prev_buttons.clear()
                self._prev_fire = self._prev_start = self._prev_release = False
                return
        if self._joystick is None and pygame.joystick.get_count() > 0:
            self._init_joystick()

    def _apply_deadzone(self, value):
        """Return ``value`` with the deadzone applied.

        Any value in ``[-DEADZONE, +DEADZONE]`` is snapped to 0
        so the paddle does not drift when the player releases
        the stick. Values outside that range are rescaled to
        fill the full ``[-1.0, +1.0]`` range so that, for
        example, a stick at half deflection gives an axis of
        0.5 rather than ~0.25.
        """
        if abs(value) < DEADZONE:
            return 0.0
        # Rescale: strip the deadzone and divide by the
        # remaining range.
        sign = 1 if value > 0 else -1
        return sign * (abs(value) - DEADZONE) / (1.0 - DEADZONE)

    @property
    def connected(self):
        """Whether a gamepad is currently connected."""
        return self._joystick is not None

    @property
    def axis_x(self):
        """The normalised horizontal axis of the left stick.

        Returns a value in the range ``-1.0..+1.0`` (after the
        deadzone is applied). Negative is left, positive is
        right. The D-pad is mixed in so that pressing left or
        right on the D-pad gives the same result as pushing
        the stick fully left or right.
        """
        if self._joystick is None:
            return 0.0
        try:
            raw = self._joystick.get_axis(LEFT_STICK_X_AXIS)
        except pygame.error:
            return 0.0
        axis = self._apply_deadzone(raw)
        # Mix in the D-pad (exposed as a "hat" on most
        # platforms). Pressing the D-pad left/right gives a
        # full deflection in that direction.
        try:
            hat_x, _ = self._joystick.get_hat(0)
        except (pygame.error, IndexError):
            hat_x = 0
        if hat_x != 0:
            axis = float(hat_x)
        return axis

    def _button_pressed(self, button_index):
        """Return whether ``button_index`` was JUST pressed this frame.

        A "just pressed" event is the rising edge of a button
        press: the button is currently down, but it was up on
        the previous frame. This is what we need for one-shot
        actions like "start the game" and "fire a bullet" - we
        do not want the action to repeat while the button is
        held.
        """
        if self._joystick is None:
            return False
        try:
            current = bool(self._joystick.get_button(button_index))
        except pygame.error:
            return False
        # ``prev_buttons`` tracks the rising-edge state per
        # button. We update it as we go so the next call sees
        # this frame's state as the previous one.
        was_down = button_index in self._prev_buttons
        if current and not was_down:
            self._prev_buttons.add(button_index)
            return True
        if not current:
            self._prev_buttons.discard(button_index)
        return False

    @property
    def fire_pressed(self):
        """Whether the fire button (A/Cross) was just pressed this frame.

        The paddle reads this in the laser state to decide
        whether to release a bullet.
        """
        return self._button_pressed(FIRE_BUTTON)

    @property
    def start_pressed(self):
        """Whether a start-equivalent button was just pressed this frame.

        The start screen reads this to begin a new game. We treat
        *two* buttons as "start":

        * the standard A / Cross button (button 0), which is the
          universal "primary action" button on every common
          controller layout (Xbox 360/One, PS3/4, generic
          XInput/DirectInput pads) and is the most natural
          counterpart to the Space key on a keyboard;
        * the Start button (button 7) on the XInput layout, used
          by most controllers that do expose a dedicated Start
          button.

        Accepting both means the game starts correctly on
        controllers that lack a Start button (or where the Start
        button is wired to a different index) - the user can
        always just press A to begin, the same way they'd press
        Space on a keyboard.
        """
        if self._button_pressed(START_BUTTON):
            return True
        if self._button_pressed(FIRE_BUTTON):
            return True
        return False

    @property
    def release_pressed(self):
        """Whether the release button (B/Circle) was just pressed this frame.

        The game uses this to launch the ball from the paddle
        at the start of a round (the same action as pressing
        space on the keyboard).
        """
        return self._button_pressed(RELEASE_BUTTON)

    @property
    def menu_pressed(self):
        """Whether the menu / pause button (Back / View / Select)
        was just pressed this frame.

        The game uses this to toggle the in-game pause overlay -
        the analog of pressing P on the keyboard. Reads button
        6 (Back / View / Select on the XInput layout) so the
        dedicated menu-style button on most controllers can be
        used for pause without conflicting with the Start button
        (button 7), which is wired to the start-screen "begin
        game" action.
        """
        return self._button_pressed(MENU_BUTTON)
