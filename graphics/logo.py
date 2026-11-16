#!/usr/bin/env python3
"""Build the oss/golf wordmark and everything derived from it.

    python3 graphics/logo.py

The wordmark is the site header drawn as vector outlines: a green prompt, "oss/golf" in VT323,
and a block cursor holding a pixel golf flag, with the tagline "for the hackers" spaced to the
same width underneath. Outputs:

    logo/ossgolf-wordmark.svg   wordmark and tagline on the site's cream background (in the README)
    logo/ossgolf-wordmark.png   the same, as a PNG
    logo/ossgolf-avatar.svg     square mark (prompt + flag cursor) for profile pictures
    logo/ossgolf-avatar.png     the same, 1024x1024
    _site/og-image.png          1200x630 social preview for the site
    logo/ossgolf-favicon.svg    16x16 pixel favicon: green prompt and flag on black
    _site/favicon.svg, favicon.ico, icon.png, and the inline icon in every page

`rsslobster regenerate` rewrites the preview image and the favicons with its own defaults, so run
this after it (./build.sh does both). Needs fontTools (with brotli) and, for the PNGs, Chrome on macOS.
"""
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from build import page, render  # shared headless-Chrome renderer
from postbuild import TAGLINE  # the same tagline the site header shows

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT = ROOT / "_site" / "fonts" / "vt323-latin.woff2"
LOGO = ROOT / "logo"
OG = ROOT / "_site" / "og-image.png"

PAPER, INK, GREEN, RED, WHITE = "#FFFFF0", "#222222", "#1d7a3e", "#e0281e", "#FFFFFF"
BRIGHT_GREEN = "#35c46a"  # the prompt on black, where the header green is too dark to read

# The favicon, drawn on a 16x16 grid so it stays crisp in a browser tab.
# K block, g prompt, w flagstick, r flag, . transparent corner
FAVICON = """
.KKKKKKKKKKKKKK.
KKKKKKKKKKKKKKKK
KKKKKKKKKKKKKKKK
KKKKKKKKKKKKKKKK
KKggKKKKKKwrrKKK
KKKggKKKKKwrrrrK
KKKKggKKKKwrrrrK
KKKKKggKKKwrrKKK
KKKKKggKKKwKKKKK
KKKKggKKKKwKKKKK
KKKggKKKKKwKKKKK
KKggKKKKKKwKKKKK
KKKKKKKKKKKKKKKK
KKKKKKKKKKKKKKKK
KKKKKKKKKKKKKKKK
.KKKKKKKKKKKKKK.
""".split()
FAVICON_COLORS = {"K": INK, "g": BRIGHT_GREEN, "w": WHITE, "r": RED}

# Everything below is in font units (1000 per em), matching the header CSS in custom.css.
ASCENT = 800          # baseline sits this far below the top of the line
PROMPT_GAP = 400      # margin-right: 0.4em after ">"
CURSOR_GAP = 120      # space between the last letter and the cursor
CELL = 60             # one cursor pixel; the block is 9 x 13 cells = 0.54em x 0.78em
CURSOR_TOP = 100      # the block runs from just under the ascender line to just below the baseline
TAGLINE_SCALE = 0.64  # tagline letter size relative to the name
TAGLINE_BASELINE = 1684
NAME_STROKE = 20       # 0.02em outline on the prompt and the name, as in the header CSS
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

    def text(self, s: str, x: float, fill: str, scale: float = 1, spacing: float = 0,
             baseline: float = ASCENT, stroke: float = 0):
        """Return (svg path element, x after the text) for `s` starting at x on `baseline`.

        `scale` sizes the text relative to the wordmark; `spacing` is extra space after each letter;
        `stroke` outlines the letters to make them heavier.
        """
        d = []
        for ch in s:
            name = self.cmap[ord(ch)]
            pen = SVGPathPen(self.set)
            self.set[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x, baseline)))  # flip y
            d.append(pen.getCommands())
            x += self.font["hmtx"][name][0] * scale + spacing
        outline = f' stroke="{fill}" stroke-width="{stroke:g}"' if stroke else ""
        return f'<path fill="{fill}"{outline} d="{" ".join(d)}"/>', x

    def ink(self, ch: str):
        """Left and right edges of a glyph's outline, in font units."""
        pen = BoundsPen(self.set)
        self.set[self.cmap[ord(ch)]].draw(pen)
        return pen.bounds[0], pen.bounds[2]


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
    """Return (svg content, width, height) of the wordmark and its tagline, with no background."""
    prompt, x = g.text(">", 0, GREEN, stroke=NAME_STROKE)
    name, x = g.text("oss/golf", x + PROMPT_GAP, INK, stroke=NAME_STROKE)
    x += CURSOR_GAP
    width = x + len(CURSOR[0]) * CELL
    return prompt + name + cursor(x) + tagline(g, width), width, TAGLINE_BASELINE + 100


def tagline(g: Glyphs, width: float) -> str:
    """The tagline, letter-spaced so its ink runs exactly from the prompt's left edge to the
    cursor's right edge."""
    left = g.ink(">")[0]
    first, last = g.ink(TAGLINE[0])[0], g.ink(TAGLINE[-1])[1]
    advance = g.font["hmtx"][g.cmap[ord(TAGLINE[0])]][0] * TAGLINE_SCALE  # VT323 is monospaced
    gaps = len(TAGLINE) - 1
    spacing = (width - left - (last - first) * TAGLINE_SCALE - gaps * advance) / gaps
    path, _ = g.text(TAGLINE, left - first * TAGLINE_SCALE, INK, TAGLINE_SCALE, spacing, TAGLINE_BASELINE)
    return path


def avatar_mark(g: Glyphs):
    """The prompt and the flag cursor on their own: what still reads in a small circle."""
    prompt, x = g.text(">", 0, GREEN, stroke=NAME_STROKE)
    x += 300
    return prompt + cursor(x), x + len(CURSOR[0]) * CELL, 1000


def svg(content: str, w: float, h: float, pad_x: float, pad_y: float, radius: float, title: str) -> str:
    W, H = w + 2 * pad_x, h + 2 * pad_y
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:g} {H:g}" '
            f'shape-rendering="crispEdges" role="img" aria-label="{title}"><title>{title}</title>'
            f'<rect width="{W:g}" height="{H:g}" rx="{radius:g}" fill="{PAPER}"/>'
            f'<g transform="translate({pad_x:g} {pad_y:g})">{content}</g></svg>\n')


def favicon_svg(square: bool = False) -> str:
    """The favicon as SVG. `square` fills the clipped corners, for icons the OS masks itself."""
    rects = "".join(
        f'<rect x="{x}" y="{y}" width="1.02" height="1.02" fill="{FAVICON_COLORS.get(ch, INK)}"/>'
        for y, line in enumerate(FAVICON) for x, ch in enumerate(line) if ch != "." or square
    )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" '
            f'shape-rendering="crispEdges">{rects}</svg>')


def install_favicon() -> None:
    icon = favicon_svg()
    (LOGO / "ossgolf-favicon.svg").write_text(icon + "\n")
    site = ROOT / "_site"
    (site / "favicon.svg").write_text(icon + "\n")
    print("wrote logo/ossgolf-favicon.svg and _site/favicon.svg")
    rasterize(favicon_svg(square=True), site / "icon.png", 512, 512)
    rasterize(icon, site / "favicon.ico", 32, 32)  # RSS Lobster also serves a PNG under this name
    # Every page also carries the icon inline as a data URI; swap RSS Lobster's default for ours.
    inline = re.compile(r'<link rel="icon" type="image/svg\+xml" href="data:image/svg\+xml,[^"]*">')
    tag = f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{quote(icon)}">'
    pages = [p for p in site.rglob("*.html") if inline.search(p.read_text())]
    for p in pages:
        p.write_text(inline.sub(tag, p.read_text()))
    print(f"updated the inline icon in {len(pages)} pages")


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
            f'style="width:820px;display:block">{content}</svg>')
    og = (f'<div style="width:1200px;height:630px;background:{PAPER};display:flex;flex-direction:column;'
          f'align-items:center;justify-content:center;gap:30px">{bare}'
          f'<p style="font-family:Charter,Georgia,serif;font-size:38px;line-height:1.3;color:#555;'
          f'text-align:center;max-width:900px">Open source golf hardware and software.</p>'
          f'<p style="font-family:Charter,Georgia,serif;font-weight:700;font-size:30px;color:{INK}">'
          f'ossgolf.com</p></div>')
    rasterize("", OG, 1200, 630, body=og)

    install_favicon()
