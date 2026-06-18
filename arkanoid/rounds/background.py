"""Shared background generators for the game rounds.

Each ``create_*`` function builds a full-screen :class:`pygame.Surface`
with the decorative play-area background for one visual theme.  The
round classes call these instead of implementing their own
``_create_background`` so the same ornament can be reused across
multiple levels without duplicating code.
"""

import math

import pygame


# ---------------------------------------------------------------------------
#  Helper – play-area rect
# ---------------------------------------------------------------------------

def _play_rect(edges, screen_size):
    """Return ``(play_rect, play_w, play_h)`` for the current edges."""
    left = edges.left.rect.right
    right = edges.right.rect.left
    top = edges.top.rect.bottom
    play_w = right - left
    play_h = screen_size[1] - top
    return pygame.Rect(left, top, play_w, play_h), play_w, play_h


def _radial_glow(play_w, play_h, colour_fn):
    """Return an SRCALPHA surface with a radial glow.

    *colour_fn* is called with ``(t,)`` where *t* ∈ [0, 1] (1 = centre)
    and must return an ``(r, g, b)`` tuple.
    """
    cx = play_w // 2
    cy = int(play_h * 0.45)
    radius = int(min(play_w, play_h) * 0.55)
    surf = pygame.Surface((play_w, play_h), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        t = 1.0 - (r / radius)
        r_, g_, b_ = colour_fn(t)
        alpha = int(20 * t * t)
        pygame.draw.circle(surf, (r_, g_, b_, alpha), (cx, cy), r)
    return surf


# ---------------------------------------------------------------------------
#  1. Hexagonal honeycomb (rounds 1, 5, …)
# ---------------------------------------------------------------------------

def create_hex_background(screen, edges):
    """Deep navy with two offset layers of outlined hexagons."""
    from arkanoid.game import LAYOUT

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    play_rect, pw, ph = _play_rect(edges, screen.get_size())
    background.fill((10, 22, 40), play_rect)

    hex_r = LAYOUT.s(36)
    hex_h = int(math.sqrt(3) * hex_r)
    h_sp = hex_r * 3 // 2
    v_sp = hex_h

    def verts(cx, cy, r):
        return [(cx + r * math.cos(math.radians(60 * i)),
                 cy + r * math.sin(math.radians(60 * i)))
                for i in range(6)]

    back_col = (20, 40, 70)
    front_col = (30, 70, 130)
    lw = max(1, LAYOUT.s(1))

    hex_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    for layer in (0, 1):
        col = back_col if layer == 0 else front_col
        x_off = layer * h_sp // 2
        row = 0
        y = -hex_h // 2
        while y < ph + hex_h:
            x = -hex_r + (x_off if row % 2 else 0)
            while x < pw + hex_r:
                v = verts(x, y, hex_r)
                v.append(v[0])
                pygame.draw.lines(hex_surf, col, False, v, lw)
                x += h_sp
            y += v_sp
            row += 1

    glow = _radial_glow(pw, ph, lambda t: (0, int(120 * t), int(200 * t)))
    background.blit(hex_surf, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    background.blit(glow, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    return background


# ---------------------------------------------------------------------------
#  2. Overlapping concentric circles (rounds 2, 6, …)
# ---------------------------------------------------------------------------

def create_circles_background(screen, edges):
    """Dark green with overlapping bullseye targets."""
    from arkanoid.game import LAYOUT

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    play_rect, pw, ph = _play_rect(edges, screen.get_size())
    background.fill((5, 18, 10), play_rect)

    cr = LAYOUT.s(30)
    rings = 5
    h_sp = int(cr * 1.85)
    v_sp = int(cr * 1.60)
    ring_dk = (12, 38, 18)
    ring_br = (20, 60, 30)
    fill_dk = (8, 24, 12)
    fill_br = (15, 45, 22)
    lw = max(1, LAYOUT.s(1))

    cs = pygame.Surface((pw, ph), pygame.SRCALPHA)
    row = 0
    y = 0
    while y - cr < ph + cr:
        x_off = (h_sp // 2) if row % 2 else 0
        x = x_off
        while x - cr < pw + cr:
            bright = (row + (x // h_sp)) % 2 == 0
            for i in range(rings, 0, -1):
                r = cr * i // rings
                if r < 1:
                    continue
                t = i / rings
                fc = fill_br if bright else fill_dk
                pygame.draw.circle(cs, (int(fc[0] * t), int(fc[1] * t),
                                        int(fc[2] * t), 255), (x, y), r)
            for i in range(1, rings + 1):
                r = cr * i // rings
                if r < 1:
                    continue
                oc = ring_br if bright else ring_dk
                pygame.draw.circle(cs, oc, (x, y), r, lw)
            x += h_sp
        y += v_sp
        row += 1

    glow = _radial_glow(pw, ph, lambda t: (0, int(80 * t), int(30 * t)))
    background.blit(cs, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    background.blit(glow, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    return background


# ---------------------------------------------------------------------------
#  3. Overlapping rounded rectangles (rounds 3, 7, …)
# ---------------------------------------------------------------------------

def create_rects_background(screen, edges):
    """Dark purple with two layers of overlapping rounded rectangles."""
    from arkanoid.game import LAYOUT

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    play_rect, pw, ph = _play_rect(edges, screen.get_size())
    background.fill((14, 6, 22), play_rect)

    fw = LAYOUT.s(80)
    fh = LAYOUT.s(55)
    bw = LAYOUT.s(42)
    bh = LAYOUT.s(30)
    sx = fw + bw
    sy = fh + bh
    lw = max(1, LAYOUT.s(1))

    rs = pygame.Surface((pw, ph), pygame.SRCALPHA)

    # Back layer – small rects
    bk_c = (30, 12, 50)
    bk_r = min(LAYOUT.s(6), bw // 4, bh // 4)
    ox = fw - bw // 2
    oy = -(bh + bh // 2)
    y = oy
    while y - bh < ph:
        x = ox
        while x - bw < pw:
            pygame.draw.rect(rs, bk_c, pygame.Rect(x, y, bw, bh),
                             width=lw, border_radius=bk_r)
            x += sx
        y += sy

    # Front layer – large rects + inner concentric
    fr_c = (55, 22, 90)
    fr_i = (40, 16, 65)
    fr_r = min(LAYOUT.s(8), fw // 4, fh // 4)
    iw = fw * 3 // 4
    ih = fh * 3 // 4
    ir = min(fr_r, iw // 4, ih // 4)
    y = 0
    while y - fh < ph:
        x = 0
        while x - fw < pw:
            pygame.draw.rect(rs, fr_c, pygame.Rect(x, y, fw, fh),
                             width=lw, border_radius=fr_r)
            ix = x + (fw - iw) // 2
            iy = y + (fh - ih) // 2
            pygame.draw.rect(rs, fr_i, pygame.Rect(ix, iy, iw, ih),
                             width=lw, border_radius=ir)
            x += sx
        y += sy

    glow = _radial_glow(pw, ph, lambda t: (int(60 * t), 0, int(90 * t)))
    background.blit(rs, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    background.blit(glow, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    return background


# ---------------------------------------------------------------------------
#  4. Chevron / V-shape ornament (rounds 4, 8, …)
# ---------------------------------------------------------------------------

def create_chevron_background(screen, edges):
    """Dark red with a diagonal grid of nested V-shapes."""
    from arkanoid.game import LAYOUT

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    play_rect, pw, ph = _play_rect(edges, screen.get_size())
    background.fill((20, 5, 5), play_rect)

    cw = LAYOUT.s(52)
    ch = LAYOUT.s(44)
    layers = 4
    lw = max(1, LAYOUT.s(2))
    dk = (50, 10, 10)
    br = (80, 20, 20)

    cs = pygame.Surface((pw, ph), pygame.SRCALPHA)
    row = 0
    y = 0
    while y - ch < ph + ch:
        x_off = cw // 2 if row % 2 else 0
        x = -cw + x_off
        while x - cw < pw + cw:
            col = br if (row + (x // cw)) % 2 == 0 else dk
            cx_ = x + cw // 2
            cy_ = y + ch // 2
            for i in range(1, layers + 1):
                t = i / layers
                hw = int(cw * 0.45 * t)
                vd = int(ch * 0.40 * t)
                pts = [(cx_ - hw, cy_ - vd), (cx_, cy_ + vd // 2),
                       (cx_ + hw, cy_ - vd)]
                pygame.draw.lines(cs, col, False, pts, lw)
            x += cw
        y += ch
        row += 1

    glow = _radial_glow(pw, ph, lambda t: (int(80 * t), 0, 0))
    background.blit(cs, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    background.blit(glow, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    return background


# ---------------------------------------------------------------------------
#  5. Perspective grid room – boss background (red / purple)
# ---------------------------------------------------------------------------

def create_boss_background(screen, edges):
    """Red-purple perspective grid room with a vanishing point in the centre."""
    from arkanoid.game import LAYOUT

    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((0, 0, 0))

    play_rect, pw, ph = _play_rect(edges, screen.get_size())
    # Dark red-purple base.
    background.fill((30, 5, 20), play_rect)

    lw = max(1, LAYOUT.s(1))
    cx = pw // 2
    cy = int(ph * 0.42)          # vanishing point slightly above centre
    line_col = (100, 20, 80)     # purple grid lines
    bright = (160, 40, 120)      # brighter accent

    grid = pygame.Surface((pw, ph), pygame.SRCALPHA)

    # --- Floor grid (below the vanishing point) ---
    # Horizontal lines spread wider as they approach the bottom.
    num_h = 20
    for i in range(num_h + 1):
        t = i / num_h                         # 0 = vanishing point, 1 = bottom
        y = int(cy + t * (ph - cy))
        spread = int(t * pw * 0.6)
        col = bright if i % 4 == 0 else line_col
        pygame.draw.line(grid, col, (cx - spread, y), (cx + spread, y), lw)

    # Vertical lines radiate from the vanishing point to the bottom edge.
    num_v_floor = 14
    for i in range(num_v_floor):
        angle = math.radians(60 + i * (60 / (num_v_floor - 1)))
        ex = cx + int(math.cos(angle) * pw)
        ey = cy + int(math.sin(angle) * ph)
        col = bright if i % 3 == 0 else line_col
        pygame.draw.line(grid, col, (cx, cy), (ex, ey), lw)

    # --- Ceiling grid (above the vanishing point) ---
    num_hc = 12
    for i in range(num_hc + 1):
        t = i / num_hc
        y = int(cy - t * cy)
        spread = int(t * pw * 0.6)
        col = bright if i % 4 == 0 else line_col
        pygame.draw.line(grid, col, (cx - spread, y), (cx + spread, y), lw)

    # Vertical lines radiate upward from the vanishing point.
    num_v_ceil = 14
    for i in range(num_v_ceil):
        angle = math.radians(240 + i * (60 / (num_v_ceil - 1)))
        ex = cx + int(math.cos(angle) * pw)
        ey = cy + int(math.sin(angle) * ph)
        col = bright if i % 3 == 0 else line_col
        pygame.draw.line(grid, col, (cx, cy), (ex, ey), lw)

    # --- Left wall vertical lines ---
    left_x = int(pw * 0.08)
    num_left = 8
    for i in range(num_left):
        t = i / (num_left - 1)
        y_top = int(cy - t * cy * 0.6)
        y_bot = int(cy + t * (ph - cy) * 0.6)
        x = int(left_x * (1 - t * 0.3))
        col = bright if i % 2 == 0 else line_col
        pygame.draw.line(grid, col, (x, y_top), (x, y_bot), lw)

    # --- Right wall vertical lines ---
    right_x = int(pw * 0.92)
    num_right = 8
    for i in range(num_right):
        t = i / (num_right - 1)
        y_top = int(cy - t * cy * 0.6)
        y_bot = int(cy + t * (ph - cy) * 0.6)
        x = int(right_x + (pw - right_x) * t * 0.3)
        col = bright if i % 2 == 0 else line_col
        pygame.draw.line(grid, col, (x, y_top), (x, y_bot), lw)

    background.blit(grid, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)

    # Radial glow in red-purple.
    glow = _radial_glow(pw, ph,
                        lambda t: (int(100 * t), 0, int(60 * t)))
    background.blit(glow, play_rect.topleft,
                    special_flags=pygame.BLEND_RGBA_ADD)
    return background
