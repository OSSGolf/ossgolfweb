#!/usr/bin/env python3
"""Apply the OSSGolf header to RSS Lobster's generated pages.

    python3 graphics/postbuild.py        (./build.sh runs it after every regenerate)

RSS Lobster gives the homepage a title, tagline and RSS link, and post pages only a small site
link and RSS. This makes them the same everywhere: it adds a GitHub icon link beside RSS on every
page and puts the tagline under the site name on post pages too. Safe to run twice.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"
CONFIG = json.loads((ROOT / "rsslobster.json").read_text())

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
    if "<p>" not in inner:  # post pages have no tagline of their own
        inner = inner.rstrip() + f'\n    <p>{html.escape(CONFIG["description"])}</p>\n  '
    return page[:m.start(2)] + inner + page[m.end(2):]


if __name__ == "__main__":
    changed = 0
    for path in sorted(SITE.rglob("*.html")):
        before = path.read_text()
        after = patch(before)
        if after != before:
            path.write_text(after)
            changed += 1
    print(f"applied the site header to {changed} pages")
