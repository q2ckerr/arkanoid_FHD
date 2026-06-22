import itertools
import logging
import math

import pygame

from arkanoid.event import receiver
from arkanoid.sound import play_laser, play_paddle_hit
from arkanoid.utils.util import (load_png,
                                 load_png_sequence)

LOG = logging.getLogger(__name__)


class Paddle(pygame.sprite.Sprite):
    """The movable paddle (a.k.a the "Vaus") used to control the ball to
    prevent it from dropping off the bottom of the screen."""

    def __init__(self, left_offset=0, right_offset=0, bottom_offset=0,
                 speed=10):
        """
        Create a new Paddle instance.

        The paddle will travel the entire width of the screen, unless the
        left and right offsets are specified which can restrict its travel.
        A bottom offset can also be supplied which defines how far from the
        bottom of the screen the paddle floats.

        Args:
            left_offset:
                Optional offset in pixels from the left of the screen that
                will restrict the maximum travel of the paddle.
            right_offset:
                Optional offset in pixels from the right of the screen that
                will restrict the maximum travel of the paddle.
            bottom_offset:
                The distance the paddle sits above the bottom of the screen.
            speed:
                Optional speed of the paddle in pixels per frame.
        """
        super().__init__()

        # The speed of the paddle movement in pixels per frame.
        self.speed = speed

        # The current movement in pixels. A negative value will trigger the
        # paddle to move left, a positive value to move right.
        self._move = 0

        # This toggles visibility of the paddle.
        self.visible = True

        # Load the default paddle image.
        self.image, self.rect = load_png('paddle')

        # Create the area the paddle can move laterally in.
        screen = pygame.display.get_surface().get_rect()
        self.area = pygame.Rect(screen.left + left_offset,
                                screen.height - bottom_offset,
                                screen.width - left_offset - right_offset,
                                self.rect.height)
        # Position the paddle.
        self.rect.center = self.area.center

        # A list of no-args callables that will be called on ball collision.
        self.ball_collide_callbacks = []

        # Whether the gamepad is currently the *active* input source.
        # The gamepad is a polled device, so there is no analogue of
        # the keyboard's KEYUP event to tell us "the player has
        # released the stick". We treat the stick going from
        # deflected back to centred as a single "release" event,
        # flipping this flag back to False so the keyboard can take
        # over again. Without this, just plugging a controller in
        # would cause the keyboard to stop working the next time
        # the stick returned to its centre position.
        self._gamepad_active = False

        # The current paddle state.
        self._state = NormalState(self)

    def update(self):
        """Update the state of the paddle."""

        # Delegate to our active state for specific animation/behaviour.
        self._state.update()

        # === Gamepad analog-stick movement =============================
        # The left stick of the connected gamepad (axis 0) can move
        # the paddle left/right. Unlike the keyboard, the gamepad
        # is a polled device, so we cannot rely on a KEYUP-equivalent
        # event to clear ``self._move`` when the player releases the
        # stick. Instead we track whether the gamepad is currently
        # the *active* input source with ``self._gamepad_active``:
        #
        #   * stick deflected -> the gamepad takes over, set
        #     ``self._move`` to the stick's direction and remember
        #     that the gamepad is active;
        #   * stick centred while the gamepad was active -> the
        #     player has released the stick, stop the paddle and
        #     mark the gamepad as inactive so the keyboard can take
        #     over again;
        #   * stick centred while the gamepad was NOT active ->
        #     leave ``self._move`` alone so the keyboard's last
        #     value (set by KEYDOWN/KEYUP handlers) is preserved
        #     and a player using the keyboard on a machine with a
        #     controller plugged in is not clobbered every frame.
        #
        # Importing here (rather than at module load) avoids a
        # circular import between the gamepad wrapper and the
        # paddle sprite.
        from arkanoid.game import get_gamepad
        gamepad = get_gamepad()
        if gamepad.connected:
            axis_x = gamepad.axis_x
            if axis_x < -0.1 or axis_x > 0.1:
                # Stick deflected - the gamepad is now the active
                # source of paddle motion. Set ``self._move`` to the
                # stick's direction at the paddle's full speed.
                self._gamepad_active = True
                if axis_x < -0.1:
                    self._move = -self.speed
                else:
                    self._move = self.speed
            elif self._gamepad_active:
                # The stick was deflected last frame but is centred
                # now - that's the player's "release". Stop the
                # paddle and mark the gamepad as inactive so the
                # keyboard (if any) regains control.
                self._gamepad_active = False
                self._move = 0
            # else: stick centred and the gamepad was never
            # active - leave ``self._move`` alone so the
            # keyboard's last setting is preserved.
        # else: no gamepad connected, the keyboard KEYDOWN/KEYUP
        # event handlers in this module are the only thing that
        # mutates ``self._move``.

        if self._move:
            # Continuously move the paddle when the offset is non-zero.
            newpos = self.rect.move(self._move, 0)

            if self._area_contains(newpos):
                # But only update the position of the paddle if it's
                # within the movable area.
                self.rect = newpos
            else:
                # The new position is not within the screen area based on
                # current speed, which might leave a small gap. Adjust the
                # speed until we match the paddle up with the edge of the
                # game area exactly.
                while self._move != 0:
                    if self._move < 0:
                        self._move += 1
                    else:
                        self._move -= 1

                    newpos = self.rect.move(self._move, 0)
                    if self._area_contains(newpos):
                        self.rect = newpos
                        break

    def _area_contains(self, newpos):
        return self.area.collidepoint(newpos.midleft) and \
               self.area.collidepoint(newpos.midright)

    def transition(self, state):
        """Transition to the specified state.

        Note that this is a request to transition, notifying an existing state
        to exit, before switching to the new state. There therefore may be a
        delay before the supplied state becomes active.

        Args:
            state:
                The state to transition to.
        """
        def on_exit():
            # Switch the state on state exit.
            self._state = state
            state.enter()
            LOG.debug('Entered {}'.format(type(state).__name__))

        self._state.exit(on_exit)

    def move_left(self):
        """Tell the paddle to move to the left by the speed set when the
        paddle was initialised."""
        # Set the offset to negative to move left.
        self._move = -self.speed

    def move_right(self):
        """Tell the paddle to move to the right by the speed set when the
        paddle was initialised."""
        # A positive offset to move right.
        self._move = self.speed

    def stop(self):
        """Tell the paddle to stop moving."""
        self._move = 0

    def reset(self):
        """Reset the position of the paddle to its start position."""
        self.rect.center = self.area.center

    def on_ball_collide(self, paddle, ball):
        """Called when the ball collides with the paddle.

        This implementation delegates to the instance level
        ball_collide_callbacks list. To monitor for ball collisions, add
        a callback to that list. A callback will be passed the ball instance
        that collided.

        Args:
            paddle:
                The paddle that was struck.
            ball:
                The ball that struck the paddle.
        """
        for callback in self.ball_collide_callbacks:
            callback(ball)
        play_paddle_hit()

    @property
    def exploding(self):
        return isinstance(self._state, ExplodingState)

    @staticmethod
    def bounce_strategy(paddle_rect, ball_rect):
        """Implementation of a ball bounce strategy used to calculate
        the angle that the ball bounces off the paddle. The angle
        of bounce is dependent upon where the ball strikes the paddle.

        The centre of the paddle sends the ball straight up. The further
        from the centre, the stronger the horizontal deflection. The
        maximum side angle is reached at 1/5 of the paddle width from
        each edge.

        Note: this function is not tied to the Paddle class but we house it
        here as it seems a reasonable place to keep it.

        Args:
            paddle_rect:
                The Rect of the paddle.
            ball_rect:
                The Rect of the ball.

        Returns:
            The angle of bounce in radians.
        """
        # Minimum angle offset (degrees) to ensure the ball never
        # bounces strictly vertically — even from the paddle centre.
        MIN_OFFSET_DEG = 5

        # Ball offset from paddle centre, normalised to -1..1.
        paddle_cx = paddle_rect.centerx
        half_w = paddle_rect.width / 2.0
        offset = (ball_rect.centerx - paddle_cx) / half_w

        # The outer 25 % on each side produces the maximum deflection.
        # Map |offset| from [0 .. 0.5] → [0 .. 1], clamped.
        t = max(0.0, min(1.0, (abs(offset) - 0.2) / 0.3)) if abs(offset) > 0.2 else 0.0

        # Straight up is 270°. Maximum deflection is ±60° (30° from
        # horizontal) on the left and right quarters of the paddle.
        MAX_DEFLECT = 60  # degrees
        angle_deg = 270 + (MAX_DEFLECT * t * (1 if offset >= 0 else -1))

        # Ensure the ball never bounces strictly vertically.
        # If the angle is within MIN_OFFSET_DEG of 270°, push it away.
        deviation = abs(angle_deg - 270)
        if deviation < MIN_OFFSET_DEG:
            # Nudge toward the side the ball came from (or right by default).
            direction = -1 if offset < 0 else 1
            angle_deg = 270 + direction * MIN_OFFSET_DEG

        return math.radians(angle_deg)


class PaddleState:
    """A PaddleState represents a particular state of the paddle, in terms
    of its graphics and behaviour.

    This base class is abstract and concrete sub-states should implement
    the update() abstract method. The update() method is called repeatedly
    by the game and is where much of the state specific logic should reside,
    such as animation.

    The enter() and exit() methods are called when the state is entered and
    exited respectively.

    When the enter() method is called, any previous paddle state is
    guaranteed to have exited. The enter() method can therefore be used to
    access any paddle attributes required for sub-state initialisation. Do
    not use __init__() for this, because a previous paddle state may still
    be in play and you may end up with attribute values you weren't expecting.

    The exit() method is called before a transition to a new state. States
    should perform any exit behaviour here, such as triggering an animation 
    to return to normal, before calling the no-args on_exit callback passed
    to the exit() method.
    """

    def __init__(self, paddle):
        """Initialise the PaddleState with the paddle instance.

        The paddle instance is made available as an instance level attribute
        and can be accessed by concrete sub-states to change paddle attriubtes.

        Args:
            paddle:
                The Paddle instance.
        """
        self.paddle = paddle
        LOG.debug('Initialised {}'.format(type(self).__name__))

    def enter(self):
        """Perform any initialisation when the state is first entered."""
        pass

    def update(self):
        """Update the state of the paddle.

        Sub-states must implement this to perform state specific behaviour.
        This method is designed to be called repeatedly.
        """
        raise NotImplementedError('Subclasses must implement update()')

    def exit(self, on_exit):
        """Trigger any state specific exit behaviour before calling the no-args
        on_exit callable.

        Args:
            on_exit:
                A no-args callable that will be called when the exit behaviour
                has completed.
        """
        on_exit()

    def __repr__(self):
        class_name = type(self).__name__
        return '{}({!r})'.format(class_name, self.paddle)


class NormalState(PaddleState):
    """This represents the default appearance of the paddle."""

    def __init__(self, paddle):
        super().__init__(paddle)

        self._pulsator = _PaddlePulsator(paddle, 'paddle_pulsate')

    def enter(self):
        """Set the default paddle graphic."""
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = load_png('paddle')
        self.paddle.rect.center = pos

    def update(self):
        """Pulsate the paddle lights."""
        self._pulsator.update()


class _PaddlePulsator:
    """Helper class for pulsating the lights at the end of the paddle."""

    def __init__(self, paddle, image_sequence_name):
        """Initialise with the name of the image sequence corresponding to
        each pulsating paddle frame.

        Args:
            paddle:
                The paddle.
            image_sequence_name:
                The name of theimage sequence representing each pulsating
                frame.
        """
        self._paddle = paddle
        self._image_sequence = load_png_sequence(image_sequence_name)
        self._animation = None
        self._update_count = 0

    def update(self):
        """Update the paddle and pulsate the lights."""
        if self._update_count % 80 == 0:
            self._animation = itertools.chain(self._image_sequence,
                                              reversed(self._image_sequence))
            self._update_count = 0
        elif self._animation:
            try:
                if self._update_count % 4 == 0:
                    self._paddle.image, _ = next(self._animation)
            except StopIteration:
                self._animation = None

        self._update_count += 1


class MaterializeState(PaddleState):
    """This special state animates the paddle as it first appears on the 
    screen.

    After the paddle has materialized, this state automatically transitions
    to NormalState.
    """

    def __init__(self, paddle):
        super().__init__(paddle)

        self._animation = iter(load_png_sequence('paddle_materialize'))
        self._update_count = 0

    def update(self):
        """Display the materialization effect, then transition to NormalState.
        """
        if self._update_count % 2 == 0:
            try:
                pos = self.paddle.rect.center
                self.paddle.image, self.paddle.rect = next(self._animation)
                self.paddle.rect.center = pos
            except StopIteration:
                # Transition to NormalState now we're done.
                self.paddle.transition(NormalState(self.paddle))

        self._update_count += 1


class WideState(PaddleState):
    """This state represents the wide state of the paddle.

    Animation is used to increase the width when the state is created, and
    also to decrease it when the state exits.
    """

    def __init__(self, paddle):
        super().__init__(paddle)

        # Load the images/rects required for the expanding animation.
        self._image_sequence = load_png_sequence('paddle_wide')
        self._animation = iter(self._image_sequence)

        # The pulsating animation.
        self._pulsator = _PaddlePulsator(paddle, 'paddle_wide_pulsate')

        # Whether we're to expand or to shrink.
        self._expand, self._shrink = True, False

        # Exit callback.
        self._on_exit = None

    def update(self):
        """Animate the paddle expanding from normal to wide or shrinking
        from wide to normal."""
        if not self._expand and not self._shrink:
            self._pulsator.update()

        if self._expand:
            self._expand_paddle()
        elif self._shrink:
            self._shrink_paddle()

    def _expand_paddle(self):
        try:
            self._convert()
            while (not self.paddle.area.collidepoint(
                    self.paddle.rect.midleft)):
                # Nudge the paddle back inside the game area.
                self.paddle.rect = self.paddle.rect.move(1, 0)
            while (not self.paddle.area.collidepoint(
                    self.paddle.rect.midright)):
                # Nudge the paddle back inside the game area.
                self.paddle.rect = self.paddle.rect.move(-1, 0)
        except StopIteration:
            self._expand = False

    def _shrink_paddle(self):
        try:
            self._convert()
        except StopIteration:
            # State ends.
            self._shrink = False
            self._on_exit()

    def _convert(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = next(self._animation)
        self.paddle.rect.center = pos

    def exit(self, on_exit):
        """Trigger the animation to shrink the paddle and exit the state.

        Args:
            on_exit:
                No-args callable invoked when the shrinking paddle animation
                has completed.
        """
        self._shrink = True
        self._on_exit = on_exit
        self._animation = iter(reversed(self._image_sequence))


class LaserState(PaddleState):
    """This state represents a laser paddle which is able to fire bullets
    upwards at the bricks.

    Animation is used to convert from the normal paddle to the laser paddle
    and vice-versa.
    """

    def __init__(self, paddle, game):
        super().__init__(paddle)
        self._game = game

        # Load the images/rects for converting to a laser paddle.
        self._image_sequence = load_png_sequence('paddle_laser')
        self._laser_anim = iter(self._image_sequence)

        # Whether we're converting to or from a laser paddle.
        self._to_laser, self._from_laser = True, False

        # The pulsating animation.
        self._pulsator = _PaddlePulsator(paddle, 'paddle_laser_pulsate')

        # Track the number of laser bullets currently in the air.
        self._bullets = []

        # Cooldown between consecutive shots (in frames).
        self._fire_cooldown = 0
        self._FIRE_RATE = 8  # frames between shots

        # Exit callback.
        self._on_exit = None

    def update(self):
        """Animate the paddle from normal to laser, or from laser to normal.

        Once converted to laser, monitor for fire input every frame:
          * the keyboard's Space key, polled via :func:`pygame.key.get_pressed`;
          * the gamepad's A / Cross button (button 0), which is
            *polled* each frame here rather than via an event,
            because pygame does not dispatch KEYUP events for
            gamepad buttons - so the KEYUP path on its own would
            never see a pure-gamepad fire press.
        """
        if not self._to_laser and not self._from_laser:
            self._pulsator.update()
            if self._fire_cooldown > 0:
                self._fire_cooldown -= 1
            # === Gamepad fire (hold to fire continuously) ===========
            from arkanoid.game import get_gamepad
            if get_gamepad().fire_held:
                self._spawn_bullets()
            # === Keyboard fire (hold Space to fire continuously) ====
            if pygame.key.get_pressed()[pygame.K_SPACE]:
                self._spawn_bullets()

        if self._to_laser:
            self._convert_to_laser()
        elif self._from_laser:
            self._convert_from_laser()

    def _convert_to_laser(self):
        try:
            self._convert()
        except StopIteration:
            # Conversion finished.
            self._to_laser = False

    def _convert_from_laser(self):
        try:
            self._convert()
        except StopIteration:
            # State ends.
            self._from_laser = False
            self._on_exit()

    def _convert(self):
        pos = self.paddle.rect.center
        self.paddle.image, self.paddle.rect = next(self._laser_anim)
        self.paddle.rect.center = pos
        while (not self.paddle.area.collidepoint(
                self.paddle.rect.midleft)):
            # Nudge the paddle back inside the game area.
            self.paddle.rect = self.paddle.rect.move(1, 0)
        while (not self.paddle.area.collidepoint(
                self.paddle.rect.midright)):
            # Nudge the paddle back inside the game area.
            self.paddle.rect = self.paddle.rect.move(-1, 0)

    def exit(self, on_exit):
        """Trigger the animation to return to normal state.

        Args:
            on_exit:
                No-args callable invoked when the laser has converted back
                to a normal paddle.
        """
        self._to_laser = False
        self._from_laser = True
        self._on_exit = on_exit
        self._laser_anim = iter(reversed(self._image_sequence))

    def _spawn_bullets(self):
        """Release a pair of laser bullets from the paddle."""
        if self._fire_cooldown > 0:
            return
        self._bullets = [bullet for bullet in self._bullets if
                         bullet.visible]
        # Fire the bullets, only allowing max 4 in the air at once.
        if len(self._bullets) < 3:
            # Create the bullet sprites. We fire two bullets at once.
            left, top = self.paddle.rect.bottomleft
            bullet1 = LaserBullet(self._game, position=(left + 10, top))
            bullet2 = LaserBullet(self._game, position=(
                left + self.paddle.rect.width - 10, top))

            # Keep track of the bullets we're fired.
            self._bullets.append(bullet1)
            self._bullets.append(bullet2)

            # Allow the bullets to be displayed.
            self._game.sprites.append(bullet1)
            self._game.sprites.append(bullet2)

            # Release them.
            bullet1.release()
            bullet2.release()
            play_laser()
            self._fire_cooldown = self._FIRE_RATE


class LaserBullet(pygame.sprite.Sprite):
    """A bullet fired from the laser paddle."""

    def __init__(self, game, position, speed=15):
        """Initialise the laser bullets.

        Args:
            game:
                The running Game instance.
            position:
                The position the bullet starts from.
            speed:
                Optional speed at which the bullet travels. Default is 15
                pixels per frame.
        """
        super().__init__()
        # Load the bullet and its rect.
        self.image, self.rect = load_png('laser_bullet')

        self._game = game
        self._position = position
        self._speed = speed

        # The area within which the bullet is travelling.
        screen = pygame.display.get_surface()
        self._area = screen.get_rect()

        # Whether the bullet is visible.
        # It may not be visible if it went off screen without hitting a brick,
        # or if it hit a brick and was destroyed as a result.
        self.visible = False

    def release(self):
        """Set the bullet in motion from its start point."""
        self.rect.midbottom = self._position
        self.visible = True

    def update(self):
        """Animate the laser bullet moving upwards, and handle any collisions
        with bricks.
        """
        # Only update if we're still visible.
        if self.visible:
            # Calculate the new position.
            self.rect = self.rect.move(0, -self._speed)
            top_edge_collision = pygame.sprite.spritecollide(
                self,
                [self._game.round.edges.top],
                False)

            if not top_edge_collision:
                # We haven't collided with the top of the game area, so
                # check whether we've collided with anything.
                visible_bricks = (brick for brick in self._game.round.bricks
                                  if brick.visible)
                brick_collide = pygame.sprite.spritecollide(self,
                                                            visible_bricks,
                                                            False)

                if brick_collide:
                    brick = brick_collide[0]
                    # The game's score is not increased when a laser destroys
                    # a brick.
                    brick.value = 0
                    # Powerups aren't released when laser destroys a brick.
                    brick.powerup_cls = None
                    self._game.on_brick_collide(brick, self)
                    self.visible = False
                else:
                    visible_enemies = (
                        enemy for enemy in self._game.enemies if enemy.visible)
                    enemy_collide = pygame.sprite.spritecollide(
                        self,
                        visible_enemies,
                        False)
                    if enemy_collide:
                        self._game.on_enemy_collide(enemy_collide[0], self)
                        self.visible = False
            else:
                # We've collided with the top edge of the game area.
                self.visible = False


class ExplodingState(PaddleState):
    """This state animates the paddle exploding when the ball goes offscreen.

    This state notifies the caller when the explosion animation has completed
    via the on_exploded no-args callback passed to the initialiser.

    Note that this state leaves the paddle invisible when it has completed
    (when on_exploded is called).
    """

    def __init__(self, paddle, on_exploded):
        """Initialise a new ExplodingState with the paddle and a no-args
        callback which gets called once the exploding animation is complete.

        Args:
            paddle:
                The paddle instance.
            on_exploded:
                The no-args callback used to notify the caller when the
                animation is complete.
        """
        super().__init__(paddle)

        # Set up the exploding images.
        self._exploding_animation = iter(load_png_sequence('paddle_explode'))
        # The notification callback.
        self._on_explode_complete = on_exploded
        self._rect_orig = None

        # Keep track of update cycles for animation purposes.
        self._update_count = 0

    def enter(self):
        """Record the original position of the paddle."""
        self._rect_orig = self.paddle.rect

    def update(self):
        """Run the exploding animation."""
        # Run the animation after a short delay.
        if 10 < self._update_count:
            if self._update_count % 4 == 0:
                try:
                    self.paddle.image, self.paddle.rect = next(
                        self._exploding_animation)
                    self.paddle.rect.center = self._rect_orig.center
                except StopIteration:
                    # Animation finished, notify the client that we're done.
                    self._on_explode_complete()
                    # We leave the paddle invisible, since it exploded.
                    self.paddle.visible = False

        self.paddle.stop()  # Prevent the paddle from moving when exploding.
        self._update_count += 1

