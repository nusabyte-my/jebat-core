"""Draw the JEBAT "Pendekar" mascot: a chibi Malay warrior head in a tengkolok.

Generates the two 3x3 sprite sheets that page-mascot consumes:

    characters/pendekar/directions.png   nine head directions
    characters/pendekar/reactions.png    nine expressions

Drawn programmatically rather than with an image model. That is deliberate: the
page-mascot pipeline exists to enforce two properties that generated art keeps
breaking -- an identical body in every cell, and nothing touching a cell edge.
Drawing to a grid enforces both by construction, and it lets the character use
JEBAT's exact brand palette.

Geometry follows skills/page-mascot/reference/design-rules.md:
  * head dominates; shoulders ~= 0.65 x head width
  * body identical across all 9 cells, clear space below it
  * tengkolok folded close to the skull -- wide headdresses clip at cell edges
  * no loose hair over the shoulders (the most common alignment failure)

Rebuild the atlases afterwards with:

    python ../../scripts/mascot.py pendekar --skip-generate --dest ../../../assets/mascots

from this directory, or from the repo root:

    python skills/page-mascot/scripts/mascot.py pendekar --skip-generate \
        --dest assets/mascots
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

CELL = 418          # final cell size (sheet 1254 = 3 x 418)
SS = 4              # supersample factor for smooth edges
S = CELL * SS

# ── JEBAT brand palette (Malam / Besi / Tembaga / Bara / Pucuk) ────────────
SKIN = (193, 138, 91, 255)
SKIN_SHADE = (168, 114, 70, 255)
SKIN_LINE = (120, 78, 44, 255)
HAT = (110, 42, 42, 255)           # maroon cloth
HAT_DARK = (84, 30, 30, 255)
HAT_LIGHT = (133, 55, 52, 255)
GOLD = (201, 122, 64, 255)         # tembaga
GOLD_BRIGHT = (213, 138, 74, 255)  # bara
BODY = (92, 34, 36, 255)
BODY_DARK = (70, 25, 27, 255)
INK = (24, 20, 18, 255)
WHITE = (240, 234, 223, 255)
BLUSH = (214, 120, 96, 130)
EMERALD = (47, 111, 85, 255)

DIRECTIONS = [
    (-1, -1), (0, -1), (1, -1),
    (-1, 0), (0, 0), (1, 0),
    (-1, 1), (0, 1), (1, 1),
]

REACTIONS = [
    "blink", "heart", "sparkle", "surprised", "wink",
    "bashful", "sleepy", "dizzy", "delighted",
]


def px(f: float) -> int:
    return round(f * S)


def ell(d, cx, cy, rx, ry, fill=None, outline=None, width=1):
    d.ellipse([px(cx - rx), px(cy - ry), px(cx + rx), px(cy + ry)],
              fill=fill, outline=outline, width=max(1, px(width)))


def poly(d, pts, fill):
    d.polygon([(px(x), px(y)) for x, y in pts], fill=fill)


# ── body: drawn identically in every cell ─────────────────────────────────
def draw_body(d):
    cx = 0.5
    top = 0.715
    # rounded shoulders, width ~= 0.34 (head width ~= 0.51) -> ratio ~0.66
    d.rounded_rectangle([px(cx - 0.17), px(top), px(cx + 0.17), px(0.905)],
                        radius=px(0.075), fill=BODY)
    # songket collar
    d.rounded_rectangle([px(cx - 0.115), px(top - 0.012), px(cx + 0.115), px(0.775)],
                        radius=px(0.03), fill=BODY_DARK)
    # gold trim line
    d.arc([px(cx - 0.115), px(top - 0.02), px(cx + 0.115), px(0.80)],
          200, 340, fill=GOLD, width=px(0.006))
    # gold songket diamonds (kept well inside the body)
    for i, fx in enumerate((-0.115, -0.038, 0.038, 0.115)):
        fy = 0.845 + (0.012 if i % 2 else 0.0)
        r = 0.016
        poly(d, [(cx + fx, fy - r), (cx + fx + r, fy),
                 (cx + fx, fy + r), (cx + fx - r, fy)], GOLD_BRIGHT)


# ── tengkolok: the folded headdress ────────────────────────────────────────
def draw_tengkolok(d, cx, cy, rx, ry):
    """Three broad pleats rising from a wrapped forehead band, plus a tail.

    Compact by design: total width stays under the head width and the crown
    adds little height, so nothing clips at a cell edge and the head still
    dominates. Wide fabric triangles with flat crests read as cloth; many thin
    spikes read as a crown.
    """
    base_y = cy - ry * 0.50          # where the band sits on the forehead
    band_bot = base_y + 0.086
    crown_top = cy - ry - 0.050      # tallest fold apex
    hw = rx * 0.94

    # back dome of the wrap (behind the pleats)
    d.pieslice([px(cx - rx), px(cy - ry - 0.01), px(cx + rx), px(cy + ry * 0.55)],
               180, 360, fill=HAT_DARK)

    peaks = [(-0.95, -0.30, crown_top + 0.030),
             (-0.36, 0.36, crown_top - 0.014),
             (0.30, 0.95, crown_top + 0.028)]

    pts = [(cx - hw, band_bot)]
    for left, right, apex in peaks:
        pts.append((cx + hw * left, base_y + 0.026))
        pts.append((cx + hw * (left + (right - left) * 0.30), apex))          # crest start
        pts.append((cx + hw * (left + (right - left) * 0.70), apex + 0.010))  # crest end
        pts.append((cx + hw * right, base_y + 0.026))
    pts.append((cx + hw, band_bot))
    poly(d, pts, HAT)

    # fold shading: dark on the rising edge, light on the falling edge
    for left, right, apex in peaks:
        d.line([px(cx + hw * (left + (right - left) * 0.30)), px(apex),
                px(cx + hw * left), px(base_y + 0.026)],
               fill=HAT_DARK, width=px(0.011))
        d.line([px(cx + hw * (left + (right - left) * 0.70)), px(apex + 0.010),
                px(cx + hw * right), px(base_y + 0.026)],
               fill=HAT_LIGHT, width=px(0.008))

    # forehead wrap band
    d.rounded_rectangle([px(cx - hw), px(base_y + 0.016),
                         px(cx + hw), px(band_bot)],
                        radius=px(0.016), fill=HAT)
    # woven texture on the band
    for i in range(-3, 4):
        fx = cx + hw * (i / 3.6)
        d.line([px(fx), px(base_y + 0.020), px(fx), px(base_y + 0.050)],
               fill=HAT_DARK, width=px(0.005))
    # gold trim along the band's lower edge
    d.rectangle([px(cx - hw), px(band_bot - 0.020),
                 px(cx + hw), px(band_bot - 0.008)], fill=GOLD)

    # The "tail": the loose folded end tucked over the band at the side --
    # the cue that reads as a real destar rather than a crown.
    tx = cx + hw * 0.66
    poly(d, [(tx, base_y + 0.020), (tx + 0.034, base_y - 0.042),
             (tx + 0.052, base_y - 0.004), (tx + 0.022, base_y + 0.060)],
         HAT_LIGHT)
    poly(d, [(tx, base_y + 0.020), (tx + 0.034, base_y - 0.042),
             (tx + 0.028, base_y + 0.014)], HAT_DARK)

    # central gold emblem (tumpal motif) at the tallest fold
    em = (cx, base_y + 0.036)
    poly(d, [(em[0], em[1] - 0.021), (em[0] + 0.017, em[1]),
             (em[0], em[1] + 0.021), (em[0] - 0.017, em[1])], GOLD_BRIGHT)


# ── head group: translated per direction ──────────────────────────────────
def draw_head(d, ox, oy, expr, gaze):
    """ox/oy: head offset in cell units. gaze: (gx, gy) pupil offset."""
    cx, cy = 0.5 + ox, 0.455 + oy
    rx, ry = 0.255, 0.235
    gx, gy = gaze

    # ears (behind head)
    for side in (-1, 1):
        ell(d, cx + side * (rx - 0.012) + gx * 0.4, cy + 0.035,
            0.042, 0.055, fill=SKIN_SHADE)

    # neck
    d.rounded_rectangle([px(cx - 0.055), px(cy + ry - 0.06),
                         px(cx + 0.055), px(0.76)],
                        radius=px(0.03), fill=SKIN_SHADE)

    # face
    ell(d, cx, cy, rx, ry, fill=SKIN)
    d.chord([px(cx - rx), px(cy - ry), px(cx + rx), px(cy + ry)],
            20, 160, fill=SKIN_SHADE)
    ell(d, cx, cy - 0.02, rx * 0.97, ry * 0.9, fill=SKIN)

    draw_tengkolok(d, cx, cy, rx, ry)

    # ── eyes ────────────────────────────────────────────────────────────
    eye_y = cy + 0.030
    eye_dx = 0.098
    eye_r = 0.043

    def eye(side, kind):
        ex = cx + side * eye_dx + gx
        ey = eye_y + gy * 0.6
        if kind in ("blink", "bashful"):
            d.arc([px(ex - eye_r), px(ey - eye_r * 0.9),
                   px(ex + eye_r), px(ey + eye_r * 0.9)],
                  200, 340, fill=INK, width=px(0.014))
            return
        if kind == "delighted":
            d.arc([px(ex - eye_r), px(ey - eye_r * 0.7),
                   px(ex + eye_r), px(ey + eye_r * 1.1)],
                  20, 160, fill=INK, width=px(0.014))
            return
        if kind == "wink" and side == 1:
            d.line([px(ex - eye_r * 0.85), px(ey), px(ex + eye_r * 0.85), px(ey)],
                   fill=INK, width=px(0.014))
            return
        if kind == "heart":
            r = eye_r * 0.95
            for s2 in (-1, 1):
                ell(d, ex + s2 * r * 0.42, ey - r * 0.32, r * 0.5, r * 0.5,
                    fill=(206, 92, 96, 255))
            poly(d, [(ex - r * 0.9, ey - r * 0.1), (ex + r * 0.9, ey - r * 0.1),
                     (ex, ey + r)], (206, 92, 96, 255))
            return
        if kind == "sparkle":
            r = eye_r * 1.05
            poly(d, [(ex, ey - r), (ex + r * 0.3, ey - r * 0.3), (ex + r, ey),
                     (ex + r * 0.3, ey + r * 0.3), (ex, ey + r),
                     (ex - r * 0.3, ey + r * 0.3), (ex - r, ey),
                     (ex - r * 0.3, ey - r * 0.3)], INK)
            ell(d, ex - r * 0.25, ey - r * 0.25, r * 0.16, r * 0.16, fill=WHITE)
            return
        if kind == "dizzy":
            r = eye_r * 0.95
            spiral = []
            for deg in range(0, 720, 24):
                a = math.radians(deg)
                rr = r * (deg / 720)
                spiral.append((ex + rr * math.cos(a), ey + rr * math.sin(a)))
            d.line([(px(a), px(b)) for a, b in spiral],
                   fill=INK, width=px(0.011), joint="curve")
            return
        if kind == "sleepy":
            d.arc([px(ex - eye_r), px(ey - eye_r * 0.5),
                   px(ex + eye_r), px(ey + eye_r)],
                  20, 160, fill=INK, width=px(0.013))
            return
        # open eye
        rr = eye_r * (1.28 if kind == "surprised" else 1.0)
        ell(d, ex, ey, rr * 0.86, rr, fill=INK)
        ell(d, ex - rr * 0.26, ey - rr * 0.3, rr * 0.3, rr * 0.3, fill=WHITE)
        ell(d, ex + rr * 0.24, ey + rr * 0.26, rr * 0.14, rr * 0.14,
            fill=(255, 255, 255, 150))

    eye(-1, "wink" if expr == "wink" else expr)
    eye(1, expr)

    # brows for surprised
    if expr == "surprised":
        for side in (-1, 1):
            bx = cx + side * eye_dx + gx
            d.arc([px(bx - 0.05), px(eye_y - 0.115),
                   px(bx + 0.05), px(eye_y - 0.055)],
                  200, 340, fill=SKIN_LINE, width=px(0.011))

    # blush
    if expr in ("bashful", "delighted", "heart"):
        for side in (-1, 1):
            ell(d, cx + side * 0.152 + gx * 0.5, cy + 0.092,
                0.045, 0.026, fill=BLUSH)

    # nose
    d.arc([px(cx + gx - 0.022), px(cy + 0.054),
           px(cx + gx + 0.022), px(cy + 0.094)],
          30, 130, fill=SKIN_LINE, width=px(0.008))

    # ── mustache: thin, tucked under the nose, ends flicked out ──────────
    my = cy + 0.112 + gy * 0.2
    mx = cx + gx
    for side in (-1, 1):
        x0, x1 = sorted((mx, mx + side * 0.084))
        box = [px(x0), px(my - 0.030), px(x1), px(my + 0.034)]
        d.arc(box, 250, 340 if side < 0 else 110,
              fill=(46, 34, 26, 255), width=px(0.014))
        d.line([px(mx + side * 0.078), px(my + 0.004),
                px(mx + side * 0.092), px(my - 0.010)],
               fill=(46, 34, 26, 255), width=px(0.012))

    # ── mouth ───────────────────────────────────────────────────────────
    mo_y = cy + 0.158 + gy * 0.2
    if expr in ("surprised", "dizzy"):
        ell(d, cx + gx, mo_y + 0.008, 0.026, 0.032, fill=(96, 44, 44, 255))
    elif expr in ("blink", "sleepy", "bashful"):
        d.arc([px(cx + gx - 0.038), px(mo_y - 0.03),
               px(cx + gx + 0.038), px(mo_y + 0.032)],
              20, 160, fill=(96, 44, 44, 255), width=px(0.011))
    elif expr in ("delighted", "sparkle"):
        d.pieslice([px(cx + gx - 0.052), px(mo_y - 0.042),
                    px(cx + gx + 0.052), px(mo_y + 0.046)],
                   15, 165, fill=(120, 52, 52, 255))
        d.pieslice([px(cx + gx - 0.03), px(mo_y + 0.006),
                    px(cx + gx + 0.03), px(mo_y + 0.05)],
                   0, 180, fill=(206, 106, 106, 255))
    else:
        d.arc([px(cx + gx - 0.044), px(mo_y - 0.032),
               px(cx + gx + 0.044), px(mo_y + 0.034)],
              25, 155, fill=(96, 44, 44, 255), width=px(0.012))

    # sleepy "z z" -- kept clear of every cell edge
    if expr == "sleepy":
        for zx, zy, zr in ((0.70, 0.30, 0.030), (0.755, 0.225, 0.022)):
            d.line([px(zx - zr), px(zy - zr), px(zx + zr), px(zy - zr)],
                   fill=EMERALD, width=px(0.010))
            d.line([px(zx + zr), px(zy - zr), px(zx - zr), px(zy + zr)],
                   fill=EMERALD, width=px(0.010))
            d.line([px(zx - zr), px(zy + zr), px(zx + zr), px(zy + zr)],
                   fill=EMERALD, width=px(0.010))


def render_cell(ox, oy, gaze, expr) -> Image.Image:
    tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(tile)
    draw_body(d)
    draw_head(d, ox, oy, expr, gaze)
    return tile.resize((CELL, CELL), Image.LANCZOS)


def build_sheet(cells) -> Image.Image:
    sheet = Image.new("RGBA", (CELL * 3, CELL * 3), (0, 0, 0, 0))
    for i, tile in enumerate(cells):
        sheet.paste(tile, ((i % 3) * CELL, (i // 3) * CELL))
    return sheet


def main():
    out = Path(__file__).resolve().parent
    out.mkdir(parents=True, exist_ok=True)

    # directions: head translates toward the pointer; pupils lead slightly
    HEAD_OFF, GAZE_OFF = 0.052, 0.020
    dirs = []
    for sx, sy in DIRECTIONS:
        dirs.append(render_cell(sx * HEAD_OFF, sy * HEAD_OFF * 0.72,
                                (sx * GAZE_OFF, sy * GAZE_OFF * 0.8), "neutral"))
    build_sheet(dirs).save(out / "directions.png")

    # reactions: head centred, expression changes
    reac = [render_cell(0.0, 0.0, (0.0, 0.0), e) for e in REACTIONS]
    build_sheet(reac).save(out / "reactions.png")

    print("wrote", out / "directions.png", "|", out / "reactions.png")


if __name__ == "__main__":
    main()
