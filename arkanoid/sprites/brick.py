import enum
import logging

import pygame

from arkanoid.utils.util import (BRICK_WIDTH_ADJUSTMENT,
                                 load_png,
                                 load_png_sequence)

LOG = logging.getLogger(__name__)


class Brick(pygame.sprite.Sprite):
    """A Brick is hit and destroyed by the ball."""

    def __init__(self, brick_colour, round_no, powerup_cls=None):
        """Initialise a new Brick using the specified BrickColour enum.

        When a brick is initialised with the specified BrickColour, a file
        named 'brick_<colour>.png' will be loaded from the graphics folder -
        where <colour> corresponds to the name attribute of the BrickColour
        enum. That file must exist.

        In addition, the initialiser will also attempt to load an image
        sequence named 'brick_<colour>_N.png' from the graphics folder
        which will be used to animate the brick when  Brick.animate() is
        called. This image sequence is optional, and if the files do not
        exist, then triggering Brick.animate() will have no effect.

        The round number must also be supplied which is used to generate the
        score value for certain brcks.

        Lastly, optionally specify the class of a powerup which will fall
        from the brick when the brick is struck by the ball - via the
        powerup_cls attribute.

        Args:
            brick_colour:
                A BrickColour enum instance. A png file named
                'brick_<colour>.png' must exist in the graphics folder where
                <colour> corresponds to the enum name attribute.
            round_no:
                The current round number used to generate the brick score
                value.
            powerup_cls:
                Optional class of a PowerUp that will be used when the ball
                strikes this brick (default None).
        """
        super().__init__()
        self.colour = brick_colour
        # Load the brick graphic.
        self.image, self.rect = load_png('brick_{}'.format(brick_colour.name))

        # Scale the brick *horizontally* so that BRICK_PLAY_AREA_COLUMNS
        # bricks fit exactly into the play area width. At 1920x1080 the
        # play area is 750 px wide and a freshly loaded brick is 58 px,
        # so 13 * 58 = 754 px overflows by 4 px; the scale factor
        # (BRICK_WIDTH_ADJUSTMENT) corrects that. The height is left
        # unchanged so bricks stay proportional. The factor is
        # resolution-independent because both the play area and the
        # brick scale by the same GAME_SCALE.
        target_width = int(round(
            self.image.get_width() * BRICK_WIDTH_ADJUSTMENT))
        if target_width != self.image.get_width():
            self.image = pygame.transform.scale(
                self.image, (target_width, self.image.get_height()))
            self.rect = self.image.get_rect()

        # Keep the original image so the brick can revert after
        # an animation finishes.
        self._original_image = self.image

        # Load the images/rects required for any animation. Animation
        # frames are also re-scaled to the same width so the destruction
        # animation matches the static brick.
        self._image_sequence = []
        for anim_image, _ in load_png_sequence(
                'brick_{}'.format(brick_colour.name)):
            if (target_width != anim_image.get_width()
                    and anim_image.get_height() > 0):
                anim_image = pygame.transform.scale(
                    anim_image,
                    (target_width, anim_image.get_height()))
            self._image_sequence.append(anim_image)
        self._animation = None

        # The number of ball collisions with this brick.
        self.collision_count = 0

        # The class of the powerup.
        self.powerup_cls = powerup_cls

        # The score value for this brick.
        if brick_colour == BrickColour.silver:
            # The score for silver bricks is a product of the brick value
            # and round number.
            self.value = brick_colour.value * round_no
        else:
            self.value = brick_colour.value

        # The number of collisions before the brick gets destroyed.
        if brick_colour == BrickColour.silver:
            self._destroy_after = 2 + (round_no - 1) // 8
        elif brick_colour == BrickColour.gold:
            # Gold bricks are never destroyed.
            self._destroy_after = -1
        else:
            self._destroy_after = 1

    def update(self):
        if self._animation:
            try:
                self.image = next(self._animation)
            except StopIteration:
                self._animation = None
                self.image = self._original_image

    @property
    def visible(self):
        """Whether the brick is still visible based on its collision count,
        or whether it is destroyed and no longer visible.

        Returns:
            True if the brick is visible. False otherwise.
        """
        if self._destroy_after > 0:
            return self.collision_count < self._destroy_after
        return True

    def animate(self):
        """Trigger animation of this brick."""
        self._animation = iter(self._image_sequence)


class BrickColour(enum.Enum):

    """Enumeration of brick colours to their corresponding score value."""

    blue = 100
    cyan = 70
    # Gold bricks have no score because they are indestructable.
    gold = 0
    green = 80
    orange = 60
    pink = 110
    red = 90
    # The score for a silver brick is the value multiplied by the Round number.
    silver = 50
    white = 40
    yellow = 120


class BossBrick(pygame.sprite.Sprite):
    """The DOH boss brick — a large sprite that takes many hits to destroy."""

    def __init__(self, width, height, hits_to_kill=50):
        super().__init__()
        self.colour = 'boss'
        self.image, _ = load_png('bossBrick')

        # Scale to the requested dimensions.
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()

        self._original_image = self.image
        self._image_sequence = []
        self._animation = None
        self.collision_count = 0
        self._destroy_after = hits_to_kill
        self.value = 10000
        self.powerup_cls = None

        # Shooting state.
        self._shoot_timer = 0
        self._shoot_burst = 3  # start with burst complete → first pause
        self._shoot_burst_size = 3
        self._shoot_burst_pause = 90    # frames between bursts (1.5 s)
        self._shoot_burst_delay = 40    # frames between shots in a burst
        self._projectiles = pygame.sprite.Group()
        # Reference to the paddle (set by the round or game).
        self._paddle = None

        # Colour flash state (yellow → cyan → green → red).
        self._flash_colors = [
            (255, 255, 0),    # yellow
            (0, 255, 255),    # cyan
            (0, 255, 0),      # green
            (255, 0, 0),      # red
        ]
        self._flash_frames_per_color = 5
        self._flash_index = 0
        self._flash_timer = 0
        self._flashing = False

    @property
    def visible(self):
        return self.collision_count < self._destroy_after

    @property
    def projectiles(self):
        return self._projectiles

    def set_paddle(self, paddle):
        self._paddle = paddle

    def update(self):
        if self._animation:
            try:
                self.image = next(self._animation)
            except StopIteration:
                self._animation = None
                self.image = self._original_image

        # Colour flash effect after being hit.
        if self._flashing:
            self._flash_timer += 1
            ci = self._flash_index
            w, h = self._original_image.get_size()
            # Build a white mask that carries only the original alpha.
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            mask.fill((255, 255, 255, 255))
            # Multiply with the original so RGB=white, A=original A.
            mask.blit(self._original_image, (0, 0),
                      special_flags=pygame.BLEND_RGBA_MULT)
            # Coloured overlay, masked to non-transparent pixels only.
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((*self._flash_colors[ci], 120))
            overlay.blit(mask, (0, 0),
                         special_flags=pygame.BLEND_RGBA_MULT)
            # Composite: original + coloured glow.
            self.image = self._original_image.copy()
            self.image.blit(overlay, (0, 0),
                            special_flags=pygame.BLEND_RGBA_ADD)
            if self._flash_timer >= self._flash_frames_per_color:
                self._flash_timer = 0
                self._flash_index += 1
                if self._flash_index >= len(self._flash_colors):
                    self._flashing = False
                    self.image = self._original_image

        # Burst shooting logic.
        self._shoot_timer += 1
        if self._shoot_burst < self._shoot_burst_size:
            # Still firing within a burst.
            if self._shoot_timer >= self._shoot_burst_delay:
                self._shoot_timer = 0
                self._shoot_burst += 1
                self._fire()
        else:
            # Burst complete — wait for pause then reset.
            if self._shoot_timer >= self._shoot_burst_pause:
                self._shoot_timer = 0
                self._shoot_burst = 0

        # Update active projectiles.
        self._projectiles.update()
        # Remove dead projectiles.
        for p in list(self._projectiles):
            if not p.visible:
                self._projectiles.remove(p)

    def flash(self):
        """Trigger the colour flash effect."""
        self._flashing = True
        self._flash_index = 0
        self._flash_timer = 0

    def _fire(self):
        """Create a projectile aimed at the paddle."""
        if self._paddle is None:
            return
        target_x, target_y = self._paddle.rect.center
        proj = Projectile(self.rect.centerx, self.rect.bottom,
                          target_x, target_y)
        self._projectiles.add(proj)

    def animate(self):
        self._animation = iter(self._image_sequence)


class Projectile(pygame.sprite.Sprite):
    """A projectile fired by the DOH boss toward the paddle."""

    SPEED = 2

    def __init__(self, x, y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((12, 24))
        self.image.fill((255, 50, 50))
        self.rect = self.image.get_rect(center=(x, y))

        # Direction toward the target (paddle centre).
        dx = target_x - x
        dy = target_y - y
        length = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        self._vx = dx / length * self.SPEED
        self._vy = dy / length * self.SPEED

        self.visible = True

    def update(self):
        self.rect.x += self._vx
        self.rect.y += self._vy
        # Deactivate if it leaves the screen.
        screen = pygame.display.get_surface()
        if not screen.get_rect().inflate(20, 20).colliderect(self.rect):
            self.visible = False
