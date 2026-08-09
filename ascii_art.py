#!/usr/bin/env python3
"""
Turns an image into coloured ASCII art for the left panel of the neofetch card.

    pip install pillow
    python ascii_art.py path\\to\\image.png

Writes assets/art.json, which generate_neofetch.py picks up
automatically (it falls back to the built-in taco if the file is missing).

Useful flags:
    --width 46      characters across (default 46)
    --gamma 1.0     <1 darkens / adds detail, >1 lightens
    --invert        dense characters on light pixels instead of dark
    --mono "#c9d1d9"  one flat colour instead of sampling the image
    --preview       print the art to the terminal instead of writing JSON
"""

import argparse
import json
import os
import sys

try:
    from PIL import Image, ImageFilter, ImageOps
except ImportError:
    sys.exit("Pillow is required:  pip install pillow")

# Standard density ramp, lightest -> densest.
RAMP = (" .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "assets", "art.json")

# A character cell is about twice as tall as it is wide.
CELL_ASPECT = 0.5


def autocrop(img, tolerance=8):
    """Trim uniform borders (the white background around the subject)."""
    grey = img.convert("L")
    w, h = grey.size
    px = grey.load()
    corner = px[0, 0]

    def blank_row(y):
        return all(abs(px[x, y] - corner) <= tolerance for x in range(w))

    def blank_col(x):
        return all(abs(px[x, y] - corner) <= tolerance for y in range(h))

    top, bottom, left, right = 0, h - 1, 0, w - 1
    while top < bottom and blank_row(top):
        top += 1
    while bottom > top and blank_row(bottom):
        bottom -= 1
    while left < right and blank_col(left):
        left += 1
    while right > left and blank_col(right):
        right -= 1

    pad = 2
    return img.crop((max(0, left - pad), max(0, top - pad),
                     min(w, right + 1 + pad), min(h, bottom + 1 + pad)))


def edge_map(img, width, height, supersample=4):
    """
    Strength of the line work in each character cell, 0..1.

    Line art is only a pixel or two wide, so it disappears if we look for
    edges after shrinking to character size. Instead we find edges at several
    times the target resolution and average them down — a thin line then
    survives as a grey cell rather than vanishing.
    """
    big = img.convert("L").resize(
        (width * supersample, height * supersample), Image.LANCZOS)

    # FIND_EDGES lights up the outermost pixels, which would draw a frame
    # around the art. Pad first, then cut the padding back off.
    pad = 2
    edges = ImageOps.expand(big, pad, fill=255).filter(ImageFilter.FIND_EDGES)
    edges = edges.crop((pad, pad, pad + big.width, pad + big.height))

    edges = edges.filter(ImageFilter.MaxFilter(3))
    small = ImageOps.autocontrast(edges.resize((width, height), Image.BOX))
    return [[small.getpixel((x, y)) / 255 for x in range(width)]
            for y in range(height)]


def quantise(rgb, step=24):
    """Round colours to a coarse grid so neighbouring cells merge into runs."""
    return tuple(min(255, (c + step // 2) // step * step) for c in rgb)


def build(path, width, gamma, invert, mono, edges):
    img = Image.open(path)

    # Flatten transparency onto white, matching the source background.
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        flat = Image.new("RGB", img.size, (255, 255, 255))
        flat.paste(img, mask=img.split()[-1])
        img = flat
    else:
        img = img.convert("RGB")

    img = autocrop(img)
    w, h = img.size
    height = max(1, round(width * (h / w) * CELL_ASPECT))
    small = img.resize((width, height), Image.LANCZOS)
    grey = small.convert("L")

    # Stretch the used luminance range across the whole ramp so a mostly
    # pale image still produces contrast.
    lo, hi = grey.getextrema()
    span = max(1, hi - lo)

    lines = edge_map(img, width, height) if edges else None

    rows = []
    for y in range(height):
        cells = []
        for x in range(width):
            value = (grey.getpixel((x, y)) - lo) / span    # 0 = dark, 1 = light
            if not invert:
                value = 1.0 - value                        # dark -> dense
            value = max(0.0, min(1.0, value)) ** gamma

            # Let line work win wherever it is stronger than the flat tone.
            if lines:
                value = max(value, lines[y][x] * edges)

            char = RAMP[min(len(RAMP) - 1, int(value * len(RAMP)))]
            colour = mono or "#%02x%02x%02x" % quantise(small.getpixel((x, y)))
            cells.append((char, colour))
        rows.append(cells)

    return rows


def to_segments(rows):
    """Merge neighbouring cells that share a colour into one span each."""
    out = []
    for cells in rows:
        segments, text, current = [], "", None
        for char, colour in cells:
            if colour != current and text:
                segments.append([text, current])
                text = ""
            current, text = colour, text + char
        if text:
            segments.append([text, current])
        # Drop trailing blank runs; they only bloat the SVG.
        while segments and not segments[-1][0].strip():
            segments.pop()
        out.append(segments)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--width", type=int, default=46)
    ap.add_argument("--gamma", type=float, default=1.0)
    ap.add_argument("--invert", action="store_true")
    ap.add_argument("--mono", default=None,
                    help="flat colour, e.g. \"#c9d1d9\"")
    ap.add_argument("--edges", type=float, default=0.0, metavar="STRENGTH",
                    help="blend in line art, 0 = off, 0.6-1.0 works well")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    rows = build(args.image, args.width, args.gamma, args.invert, args.mono,
                 args.edges)

    if args.preview:
        for cells in rows:
            print("".join(char for char, _ in cells))
        return

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump({"rows": to_segments(rows)}, fh)
    print(f"wrote {OUT}  ({args.width}x{len(rows)} characters)")


if __name__ == "__main__":
    main()
