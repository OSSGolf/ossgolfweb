#!/usr/bin/env python3
"""Build the oss/golf wordmark and everything derived from it.

    python3 graphics/logo.py

The wordmark is the site header drawn as vector outlines: a green prompt, "oss/golf" in VT323,
and a block cursor holding a pixel golf flag. Outputs:

    logo/ossgolf-wordmark.svg   the wordmark on the site's cream background (used in the README)
    logo/ossgolf-wordmark.png   the same, as a PNG
    logo/ossgolf-avatar.svg     square mark (prompt + flag cursor) for profile pictures
    logo/ossgolf-avatar.png     the same, 1024x1024
    _site/og-image.png          1200x630 social preview for the site

`rsslobster regenerate` rewrites _site/og-image.png with its own default, so run this after it
(./build.sh does both). Needs fontTools (with brotli) and, for the PNGs, Chrome on macOS.
"""
import subprocess
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from build import page, render  # shared headless-Chrome renderer

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT = ROOT / "_site" / "fonts" / "vt323-latin.woff2"
LOGO = ROOT / "logo"
OG = ROOT / "_site" / "og-image.png"

PAPER, INK, GREEN, RED, WHITE = "#FFFFF0", "#222222", "#1d7a3e", "#e0281e", "#FFFFFF"

# Everything below is in font units (1000 per em), matching the header CSS in custom.css.
ASCENT = 800          # baseline sits this far below the top of the line
PROMPT_GAP = 400      # margin-right: 0.4em after ">"
CURSOR_GAP = 120      # space between the last letter and the cursor
CELL = 60             # one cursor pixel; the block is 9 x 13 cells = 0.54em x 0.78em
CURSOR_TOP = 100      # the block runs from just under the ascender line to just below the baseline
CURSOR = """
#########
#########
##.rr####
##.rrrr##
##.rrrr##
##.rr####
##.######
##.######
##.######
##.######
##.######
#########
#########
""".split()


class Glyphs:
    def __init__(self, path: Path):
        self.font = TTFont(path)
        self.set = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()

    def text(self, s: str, x: float, fill: str):
        """Return (svg path element, x after the text) for `s` starting at x on the baseline."""
        d = []
        for ch in s:
            name = self.cmap[ord(ch)]
            pen = SVGPathPen(self.set)
            self.set[name].draw(TransformPen(pen, (1, 0, 0, -1, x, ASCENT)))  # flip y, move to x
            d.append(pen.getCommands())
            x += self.font["hmtx"][name][0]
        return f'<path fill="{fill}" d="{" ".join(d)}"/>', x


def cursor(x: float) -> str:
    w, h = len(CURSOR[0]) * CELL, len(CURSOR) * CELL
    cells = {".": [], "r": []}
    for row, line in enumerate(CURSOR):
        for col, ch in enumerate(line):
            if ch in cells:
                cells[ch].append(f'<rect x="{x + col * CELL}" y="{CURSOR_TOP + row * CELL}" '
                                 f'width="{CELL}" height="{CELL}"/>')
    return (f'<rect x="{x}" y="{CURSOR_TOP}" width="{w}" height="{h}" fill="{INK}"/>'
            f'<g fill="{WHITE}">{"".join(cells["."])}</g><g fill="{RED}">{"".join(cells["r"])}</g>')


def wordmark(g: Glyphs):
    """Return (svg content, width, height) of the full wordmark with no background or padding."""
    prompt, x = g.text(">", 0, GREEN)
    name, x = g.text("oss/golf", x + PROMPT_GAP, INK)
    x += CURSOR_GAP
    return prompt + name + cursor(x), x + len(CURSOR[0]) * CELL, 1000


def avatar_mark(g: Glyphs):
    """The prompt and the flag cursor on their own: what still reads in a small circle."""
    prompt, x = g.text(">", 0, GREEN)
    x += 300
    return prompt + cursor(x), x + len(CURSOR[0]) * CELL, 1000


def svg(content: str, w: float, h: float, pad_x: float, pad_y: float, radius: float, title: str) -> str:
    W, H = w + 2 * pad_x, h + 2 * pad_y
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{title}"><title>{title}</title>'
            f'<rect width="{W:g}" height="{H:g}" rx="{radius:g}" fill="{PAPER}"/>'
            f'<g transform="translate({pad_x:g} {pad_y:g})">{content}</g></svg>\n')


def rasterize(svg_text: str, out: Path, width: int, height: int, body: str = "") -> None:
    """Render an SVG (or an HTML body containing it) to a PNG of exactly width x height."""
    src = HERE / f"_{out.stem}.html"
    box = body or f'<div style="width:{width}px;height:{height}px;line-height:0">{svg_text}</div>'
    src.write_text(page("logo", box))
    try:
        render(src, out, width, height)  # writes at 2x
        subprocess.run(["sips", "-z", str(height), str(width), str(out)], capture_output=True, check=True)
    finally:
        src.unlink()
    print(f"wrote {out.relative_to(ROOT)} ({width}x{height})")


if __name__ == "__main__":
    g = Glyphs(FONT)
    LOGO.mkdir(exist_ok=True)

    content, w, h = wordmark(g)
    mark = svg(content, w, h, pad_x=520, pad_y=380, radius=260, title="oss/golf")
    (LOGO / "ossgolf-wordmark.svg").write_text(mark)
    print("wrote logo/ossgolf-wordmark.svg")
    W, H = w + 1040, h + 760
    rasterize(mark, LOGO / "ossgolf-wordmark.png", 1200, round(1200 * H / W))

    content, w, h = avatar_mark(g)
    side = 2200
    square = svg(content, w, h, pad_x=(side - w) / 2, pad_y=(side - h) / 2 + 10, radius=0, title="oss/golf")
    (LOGO / "ossgolf-avatar.svg").write_text(square)
    print("wrote logo/ossgolf-avatar.svg")
    rasterize(square, LOGO / "ossgolf-avatar.png", 1024, 1024)

    content, w, h = wordmark(g)
    bare = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" shape-rendering="crispEdges" '
            f'style="width:860px;display:block">{content}</svg>')
    og = (f'<div style="width:1200px;height:630px;background:{PAPER};display:flex;flex-direction:column;'
          f'align-items:center;justify-content:center;gap:34px">{bare}'
          f'<p style="font-family:Charter,Georgia,serif;font-size:38px;line-height:1.3;color:#555;'
          f'text-align:center;max-width:900px">Open source golf hardware and software<br>'
          f'you can build and own.</p>'
          f'<p style="font-family:Charter,Georgia,serif;font-weight:700;font-size:30px;color:{INK}">'
          f'ossgolf.com</p></div>')
    rasterize("", OG, 1200, 630, body=og)
