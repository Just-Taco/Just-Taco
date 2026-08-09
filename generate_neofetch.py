#!/usr/bin/env python3
"""
Renders a neofetch-style "about me" panel as an SVG (dark + light variants)
for use in a GitHub profile README.

Edit CONFIG below, then run:

    python generate_neofetch.py

Uptime is derived from BIRTHDAY, and the GitHub Stats block is read from
assets/stats.json (refreshed by fetch_stats.py), so both stay
current on their own once the workflow is running.

Output: assets/neofetch-dark.svg, assets/neofetch-light.svg
"""

import datetime
import json
import os

# --------------------------------------------------------------------------
# CONFIG  --  everything you'd want to change lives here.
# --------------------------------------------------------------------------

HEADER = "just@taco"          # the "user@host" line at the top
BIRTHDAY = (2007, 3, 9)       # year, month, day -> drives the Uptime row


def uptime():
    """Age as neofetch would print it: 'N years, N months, N days'."""
    born = datetime.date(*BIRTHDAY)
    today = datetime.date.today()

    years = today.year - born.year
    months = today.month - born.month
    days = today.day - born.day

    if days < 0:
        months -= 1
        # days in the month that just ended
        first = today.replace(day=1)
        days += (first - datetime.timedelta(days=1)).day
    if months < 0:
        years -= 1
        months += 12

    parts = [f"{years} year{'s' * (years != 1)}",
             f"{months} month{'s' * (months != 1)}",
             f"{days} day{'s' * (days != 1)}"]
    return ", ".join(parts)


def stats():
    """Cached GitHub numbers, or em dashes when nothing has been fetched."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "stats.json")
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, ValueError):
        raw = {}

    def num(key):
        value = raw.get(key)
        return f"{value:,}" if isinstance(value, int) else "—"

    return {key: num(key) for key in
            ("repos", "stars", "commits", "followers",
             "loc_added", "loc_deleted", "loc_total")}


S = stats()

# Section title -> list of (label, value) rows.
# A value is a plain string, or a list of (text, color_key) pairs where
# color_key is one of: value, dim, green, red, yellow, purple, cyan.
SECTIONS = [
    (None, [  # first block has no section title
        ("OS",                    "Windows 11"),
        ("Uptime",                uptime()),
        ("Host",                  "School"),
        ("Kernel",                "Student / Developer"),
        ("Shell",                 "PowerShell"),
        ("IDE",                   "VS Code, Visual Studio"),
    ]),
    (None, [
        ("Languages.Programming", "Python, C#, C++, TypeScript, Lua, JavaScript"),
        ("Languages.Markup",      "HTML, CSS, JSON, YAML, SQL"),
        ("Languages.Spoken",      "English, Danish, German"),
    ]),
    (None, [
        ("Stack.Frontend",        "React, Next.js, Vite, Tailwind, shadcn/ui"),
        ("Stack.Backend",         "Node.js, PostgreSQL, Prisma"),
        ("Stack.Tools",           "Git, Docker, Linux, Claude"),
    ]),
    (None, [
        ("Hobbies.Software",      "FiveM Modding, Tooling"),
        ("Hobbies.Hardware",      "Home Automation"),
    ]),
    ("Contact", [
        ("Email",                 "hermansenian01@gmail.com"),
        ("GitHub",                "Just-Taco"),
        ("Discord",               "tacothedev"),
    ]),
    ("GitHub Stats", [
        ("Repos",                 [(S["repos"], "value"), ("  |  Stars: ", "dim"),
                                   (S["stars"], "value")]),
        ("Commits",               [(S["commits"], "value"), ("  |  Followers: ", "dim"),
                                   (S["followers"], "value")]),
        ("Lines of Code",         [(S["loc_total"], "value"), ("  ( ", "dim"),
                                   (S["loc_added"] + "++", "green"), (", ", "dim"),
                                   (S["loc_deleted"] + "--", "red"), (" )", "dim")]),
    ]),
]

# --------------------------------------------------------------------------
# ASCII art (left panel).  (text, default color key, {char: color key})
# --------------------------------------------------------------------------

SHELL, MEAT, CHEESE, SALSA, LETTUCE = "shell", "meat", "cheese", "salsa", "lettuce"

ART = [
    ("",                                              SHELL, {}),
    ("                ___     ___     ___",         LETTUCE, {}),
    ("               (   )   (   )   (   )",        LETTUCE, {}),
    ("            .---`-'-----`-'-----`-'---.",       SHELL, {}),
    ("           /   * . * . * . * . * . *   \\",     SHELL, {"*": SALSA, ".": LETTUCE}),
    ("          |  ~~~~~~~~~~~~~~~~~~~~~~~~~  |",     SHELL, {"~": CHEESE}),
    ("          |  #########################  |",     SHELL, {"#": MEAT}),
    ("           \\  #######################  /",      SHELL, {"#": MEAT}),
    ("            \\                         /",       SHELL, {}),
    ("             \\                       /",        SHELL, {}),
    ("              \\_____________________/",         SHELL, {}),
    ("               `-------------------'",          SHELL, {}),
    ("",                                              SHELL, {}),
    ("",                                              SHELL, {}),
    ("       ████████  █████   ██████   ██████",     CHEESE, {}),
    ("          ██    ██   ██ ██       ██    ██",    CHEESE, {}),
    ("          ██    ███████ ██       ██    ██",    CHEESE, {}),
    ("          ██    ██   ██ ██       ██    ██",    CHEESE, {}),
    ("          ██    ██   ██  ██████   ██████",     CHEESE, {}),
    ("",                                              SHELL, {}),
    ("           J  U  S  T   ·   T  A  C  O",        SHELL, {}),
]

# --------------------------------------------------------------------------
# Themes
# --------------------------------------------------------------------------

THEMES = {
    "dark": {
        "is_light": False,
        "bg": "#0d1117", "border": "#30363d",
        "label": "#e3b341", "value": "#c9d1d9", "dim": "#484f58",
        "rule": "#30363d", "header": "#e3b341", "section": "#8b949e",
        "green": "#3fb950", "red": "#f85149", "yellow": "#e3b341",
        "purple": "#d2a8ff", "cyan": "#56d4dd",
        "shell": "#e3b341", "meat": "#b06a3b", "cheese": "#f0c674",
        "salsa": "#f85149", "lettuce": "#3fb950",
        "dot1": "#f85149", "dot2": "#e3b341", "dot3": "#3fb950",
    },
    "light": {
        "is_light": True,
        "bg": "#ffffff", "border": "#d0d7de",
        "label": "#9a6700", "value": "#1f2328", "dim": "#afb8c1",
        "rule": "#d0d7de", "header": "#9a6700", "section": "#57606a",
        "green": "#1a7f37", "red": "#cf222e", "yellow": "#9a6700",
        "purple": "#8250df", "cyan": "#1b7c83",
        "shell": "#bf8700", "meat": "#8c4a1f", "cheese": "#bf8700",
        "salsa": "#cf222e", "lettuce": "#1a7f37",
        "dot1": "#cf222e", "dot2": "#bf8700", "dot3": "#1a7f37",
    },
}

# --------------------------------------------------------------------------
# Layout constants
# --------------------------------------------------------------------------

FONT_SIZE = 14
CHAR_W = FONT_SIZE * 0.6          # monospace advance width
LINE_H = 19
PAD_X, PAD_Y = 22, 26
TITLEBAR_H = 34                   # fake terminal title bar
INFO_W = 66                       # min info panel width, in characters
MIN_DOTS = 3                      # shortest run of leader dots
GAP = 4                           # columns between art and info
FONT_STACK = ("'JetBrains Mono','Fira Code','Cascadia Mono','DejaVu Sans Mono',"
              "Menlo,Consolas,monospace")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fit_luma(colour, floor, ceiling):
    """
    Pull a colour's brightness into a legible band, keeping its hue.

    Sampled art colours are whatever the source image had, so the dark
    jacket would come out near-black on the dark card and the blonde hair
    near-white on the light one. Mixing toward white or black fixes the
    contrast without turning the portrait grey.
    """
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    luma = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255

    if luma < floor:
        t = (floor - luma) / max(1e-6, 1 - luma)     # mix toward white
        r, g, b = (round(c + (255 - c) * t) for c in (r, g, b))
    elif luma > ceiling:
        s = ceiling / max(1e-6, luma)                # scale toward black
        r, g, b = (round(c * s) for c in (r, g, b))

    return "#%02x%02x%02x" % (r, g, b)


def resolve(key, theme):
    """A theme colour name, or a literal #rrggbb sampled from the art."""
    if not key.startswith("#"):
        return theme[key]
    return (fit_luma(key, 0.0, 0.55) if theme["is_light"]
            else fit_luma(key, 0.42, 1.0))


def load_art():
    """Art rendered from an image by ascii_art.py, else the built-in taco."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "art.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return [[tuple(seg) for seg in row]
                    for row in json.load(fh)["rows"]]
    except (OSError, ValueError, KeyError):
        return None


# --------------------------------------------------------------------------
# Info panel -> list of lines, each line a list of (text, color_key) segments
# --------------------------------------------------------------------------

def build_info_lines():
    """Lay the info panel out, widening it if a row would otherwise overflow."""
    rows = [(title, label, value if isinstance(value, list) else [(value, "value")])
            for title, block in SECTIONS for label, value in block]

    width = max([INFO_W] + [
        len("  " + label + ":") + sum(len(t) for t, _ in segs) + MIN_DOTS + 2
        for _, label, segs in rows])

    lines = [[(HEADER, "header"),
              (" " + "-" * max(3, width - len(HEADER) - 1), "rule")]]

    for title, block in SECTIONS:
        lines.append([])
        if title:
            left = "- " + title + " "
            lines.append([(left, "section"),
                          ("-" * max(3, width - len(left)), "rule")])
        for label, value in block:
            segs = value if isinstance(value, list) else [(value, "value")]
            left = "  " + label + ":"
            dots = width - len(left) - sum(len(t) for t, _ in segs) - 2
            lines.append([(left, "label"),
                          (" " + "." * dots + " ", "dim")] + segs)

    return lines, width


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_segments(out, segments, col0, row, theme):
    """Emit one line of coloured text, starting at character column col0."""
    col = col0
    y = PAD_Y + TITLEBAR_H + row * LINE_H + FONT_SIZE
    for text, key in segments:
        if text.strip():
            x = PAD_X + col * CHAR_W
            out.append(
                f'<text x="{x:.1f}" y="{y:.1f}" fill="{resolve(key, theme)}" '
                f'textLength="{len(text) * CHAR_W:.1f}" lengthAdjust="spacing"'
                f'>{esc(text)}</text>'
            )
        col += len(text)


def build_art_lines():
    """Either the image-derived art, or the taco expanded into segments."""
    art = load_art()
    if art is not None:
        return art

    rows = []
    for line, default, overrides in ART:
        segs, buf, cur = [], "", None
        for ch in line:
            key = overrides.get(ch, default)
            if key != cur and buf:
                segs.append((buf, cur))
                buf = ""
            cur, buf = key, buf + ch
        if buf:
            segs.append((buf, cur))
        rows.append(segs)
    return rows


def build_svg(theme_name):
    theme = THEMES[theme_name]
    info, info_w = build_info_lines()
    art = build_art_lines()

    art_w = max((sum(len(t) for t, _ in row) for row in art), default=0)
    info_col0 = art_w + GAP
    cols = info_col0 + info_w
    rows = max(len(art), len(info))

    width = round(PAD_X * 2 + cols * CHAR_W)
    height = round(PAD_Y * 2 + TITLEBAR_H + rows * LINE_H)

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" '
        f'font-family="{FONT_STACK}" font-size="{FONT_SIZE}" '
        f'xml:space="preserve" role="img" '
        f'aria-label="About {HEADER}">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" '
        f'rx="10" fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        # fake terminal title bar
        f'<circle cx="26" cy="24" r="6" fill="{theme["dot1"]}"/>',
        f'<circle cx="46" cy="24" r="6" fill="{theme["dot2"]}"/>',
        f'<circle cx="66" cy="24" r="6" fill="{theme["dot3"]}"/>',
        f'<text x="{width / 2:.0f}" y="29" fill="{theme["section"]}" '
        f'font-size="12" text-anchor="middle">{esc(HEADER)} — neofetch</text>',
        f'<line x1="0" y1="{TITLEBAR_H + 8}" x2="{width}" '
        f'y2="{TITLEBAR_H + 8}" stroke="{theme["border"]}"/>',
    ]

    for row, segs in enumerate(art):
        render_segments(out, segs, 0, row, theme)
    for row, segs in enumerate(info):
        render_segments(out, segs, info_col0, row, theme)

    out.append("</svg>")
    return "\n".join(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    dest = os.path.join(here, "assets")
    os.makedirs(dest, exist_ok=True)
    for name in THEMES:
        path = os.path.join(dest, f"neofetch-{name}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(build_svg(name))
        print("wrote", path)


if __name__ == "__main__":
    main()
