#!/usr/bin/env python3
"""Apply the OSSGolf header to RSS Lobster's generated pages.

    python3 graphics/postbuild.py        (./build.sh runs it after every regenerate)

RSS Lobster gives the homepage a title, tagline and RSS link, and post pages only a small site
link and RSS. This makes them the same everywhere: it adds a GitHub icon link beside RSS on every
page, puts the "for the hackers" tagline under the site name, makes the name and tagline one
link to the homepage, and gives post pages the description line the homepage has.

It also removes the causes of layout shift: every image and video gets explicit width and height
(so the browser reserves its space before it loads), and the header font is embedded in the page
itself, cut down to the dozen letters the wordmark uses, so the header never renders in a
stand-in font first. Safe to run twice. Needs fontTools with brotli.
"""
import base64
import html
import io
import json
import re
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CONFIG = json.loads((ROOT / "rsslobster.json").read_text())
TAGLINE = "for the hackers"  # the wordmark's tagline; graphics/logo.py draws the same text

# GitHub's mark, from the MIT-licensed Octicons set.
GITHUB_ICON = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 16 16" fill="currentColor" '
    'aria-hidden="true"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 '
    "0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36"
    "-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 "
    "1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61"
    ".55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 "
    '1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg>'
)

RSS_LINK = re.compile(r'<a href="/feed\.xml" class="header-rss".*?</a>', re.S)
HEADER = re.compile(r"(<body>.*?<header>)(.*?)(</header>)", re.S)


def patch(page: str) -> str:
    m = HEADER.search(page)
    if not m or "header-links" in m.group(2):
        return page
    inner = m.group(2)
    github = (f'<a href="{html.escape(CONFIG["authorUrl"])}" class="header-gh" '
              f'aria-label="{html.escape(CONFIG["author"])} on GitHub">{GITHUB_ICON}</a>')
    inner, n = RSS_LINK.subn(lambda r: f'<span class="header-links">{github}{r.group(0)}</span>', inner, count=1)
    if n != 1:
        raise SystemExit("could not find the RSS link in a page header; has RSS Lobster's markup changed?")
    if "<p>" not in inner:  # post pages have no description line of their own
        inner = inner.rstrip() + f'\n    <p>{html.escape(CONFIG["description"])}</p>\n  '
    # Wrap the site name and the tagline in one link to the homepage. The homepage has the name
    # as an <h1>, post pages as a small link inside <nav>.
    tagline = f'<span class="site-tagline">{html.escape(TAGLINE)}</span>'
    label = f'aria-label="{html.escape(CONFIG["title"])}, {html.escape(TAGLINE)}: home"'
    inner, home = re.subn(
        r"<h1>(.*?)</h1>",
        rf'<a class="site-mark" href="/" {label}><h1 class="site-name">\1</h1>{tagline}</a>', inner, count=1)
    inner, post = re.subn(
        r'<nav><a href="/">(.*?)</a></nav>',
        rf'<nav><a class="site-mark" href="/" {label}><span class="site-name">\1</span>{tagline}</a></nav>',
        inner, count=1)
    if home + post != 1:
        raise SystemExit("could not find the site name in a page header; has RSS Lobster's markup changed?")
    return page[:m.start(2)] + inner + page[m.end(2):]


FONT_FILE = SITE / "fonts" / "vt323-latin.woff2"
FONT_URL = 'url("/fonts/vt323-latin.woff2")'  # as written in custom.css
WORDMARK_TEXT = "> oss/golf " + TAGLINE       # every character the header sets in VT323
MEDIA_TAG = re.compile(r"<(img|video)\b([^>]*)>")


@lru_cache(maxsize=None)
def pixel_size(src: str):
    """Width and height of a local image, or None if it is not a file in the site."""
    path = SITE / src.lstrip("/")
    if not src.startswith("/") or not path.is_file():
        return None
    out = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)],
                         capture_output=True, text=True).stdout
    w, h = re.search(r"pixelWidth: (\d+)", out), re.search(r"pixelHeight: (\d+)", out)
    return (int(w.group(1)), int(h.group(1))) if w and h else None


def size_media(page: str) -> str:
    """Give images and videos width/height attributes so their space is reserved before load."""
    def fix(m: re.Match) -> str:
        tag, attrs = m.group(1), m.group(2)
        if re.search(r'\bwidth="', attrs):
            return m.group(0)
        src = re.search(r'\b(?:poster|src)="([^"]+)"' if tag == "video" else r'\bsrc="([^"]+)"', attrs)
        size = pixel_size(src.group(1)) if src else None
        return f'<{tag}{attrs} width="{size[0]}" height="{size[1]}">' if size else m.group(0)
    return MEDIA_TAG.sub(fix, page)


@lru_cache(maxsize=None)
def font_data_uri() -> str:
    """VT323 reduced to the wordmark's characters, as a data: URI (about 3 KB)."""
    from fontTools import subset
    from fontTools.ttLib import TTFont

    font = TTFont(FONT_FILE)
    options = subset.Options(flavor="woff2", layout_features=[])
    subsetter = subset.Subsetter(options)
    subsetter.populate(text=WORDMARK_TEXT)
    subsetter.subset(font)
    out = io.BytesIO()
    font.flavor = "woff2"
    font.save(out)
    return "data:font/woff2;base64," + base64.b64encode(out.getvalue()).decode()


def inline_font(page: str) -> str:
    """Swap the font file reference for the embedded font, so there is no request to wait on."""
    return page.replace(FONT_URL, f'url("{font_data_uri()}")')


if __name__ == "__main__":
    changed = 0
    for path in sorted(SITE.rglob("*.html")):
        before = path.read_text()
        after = inline_font(size_media(patch(before)))
        if after != before:
            path.write_text(after)
            changed += 1
    print(f"applied the site header and layout-shift fixes to {changed} pages")
