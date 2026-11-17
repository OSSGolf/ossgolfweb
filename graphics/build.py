#!/usr/bin/env python3
"""Build the open source golf landscape graphics.

    python3 graphics/build.py

Reads graphics/landscape.json and renders, with headless Chrome at 2x:

    _site/images/open-source-golf-landscape.png        the full reference table
    _site/images/open-source-golf-landscape-card.png   1200x675 share card
    _site/images/open-source-golf-landscape-map-v3.png    market-map style overview
    _site/images/open-source-golf-landscape-map-v3-1920.png   lighter copy of the map for posts

The intermediate HTML is written next to this script. Standard library only.
Fonts are macOS system fonts; the outputs are images, so readers do not need them.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = HERE / "landscape.json"
IMAGES = ROOT / "_site" / "images"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# key -> (legend label, examples)
FAMILIES = {
    "permissive": ("Permissive", "MIT, Apache, ISC"),
    "copyleft": ("Copyleft", "GPL, AGPL, LGPL"),
    "public": ("Public domain", "CC0"),
    "restricted": ("Source available", "no commercial use"),
    "unknown": ("License unclear", ""),
}


def family(lic: str) -> str:
    l = lic.lower()
    if "not verified" in l or "unclear" in l:
        return "unknown"
    if "polyform" in l:
        return "restricted"
    if "gpl" in l:
        return "copyleft"
    if l.startswith("cc0") or "public domain" in l:
        return "public"
    return "permissive"


def e(s) -> str:
    return html.escape(str(s))


def mark(fam: str) -> str:
    return f'<span class="mark {fam}" aria-hidden="true">{"?" if fam == "unknown" else ""}</span>'


def items_of(node: dict) -> list:
    if "items" in node:
        return node["items"]
    key = "groups" if "groups" in node else "segments"
    return [i for child in node[key] for i in items_of(child)]


def tier(stars) -> str:
    if stars is None:
        return "none"
    return "lead" if stars >= 100 else "mid" if stars >= 10 else "low"


def item_html(it: dict) -> str:
    stars = it.get("stars")
    owner = f'<span class="owner">{e(it["owner"])}/</span>' if it.get("owner") else ""
    star_txt = f"{stars:,}" if stars is not None else "–"
    out = [
        f'<div class="row {tier(stars)}">'
        f'<span class="name">{owner}{e(it["name"])}</span>'
        f'<span class="note">{e(it.get("note", ""))}</span>'
        f'<span class="lic">{mark(family(it["license"]))}{e(it["license"])}</span>'
        f'<span class="stars">{star_txt}</span></div>'
    ]
    kids = it.get("with", [])
    if kids:
        out.append('<div class="kids">')
        for k in kids:
            out.append(
                f'<div class="row kid"><span class="name">{e(k["name"])}</span>'
                f'<span class="note">{e(k.get("note", ""))}</span>'
                f'<span class="lic">{mark(family(k["license"]))}{e(k["license"])}</span>'
                f'<span class="stars"></span></div>'
            )
        out.append("</div>")
    return "".join(out)


def plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def overview_html(d: dict) -> str:
    cols = []
    for side in d["sides"]:
        rows = "".join(
            f'<div class="ov-row"><span class="ov-name">{e(seg["name"])}</span>'
            f'<span class="ov-marks">{"".join(mark(f) for f in sorted((family(i["license"]) for i in items_of(seg)), key=list(FAMILIES).index))}</span>'
            f'<span class="ov-n">{len(items_of(seg))}</span></div>'
            for seg in side["segments"]
        )
        cols.append(
            f'<div class="ov-col"><div class="ov-head"><span>{e(side["name"])}</span>'
            f'<span>{len(items_of(side))}</span></div>{rows}</div>'
        )
    return f'<div class="overview">{"".join(cols)}</div>'


def legend_html(d: dict) -> str:
    counts = {k: 0 for k in FAMILIES}
    for side in d["sides"]:
        for i in items_of(side):
            counts[family(i["license"])] += 1
    return '<ul class="legend">' + "".join(
        f'<li>{mark(k)}<b>{e(v[0])}</b><span class="n">{counts[k]}</span>'
        f'{f"<span class=eg>{e(v[1])}</span>" if v[1] else ""}</li>'
        for k, v in FAMILIES.items() if counts[k]
    ) + "</ul>"


def finding(d: dict) -> str:
    everything = [i for side in d["sides"] for i in items_of(side)]
    total = sum(i.get("stars") or 0 for i in everything)
    top = sorted(everything, key=lambda i: -(i.get("stars") or 0))[:2]
    share = sum(i["stars"] for i in top) / total
    if not 0.58 <= share <= 0.70:
        sys.exit(f"finding copy says 'almost two thirds' but the top-two share is {share:.0%}; rewrite it")
    soft = next(s for s in d["sides"] if s["name"] == "Software")
    sims = sum(len(items_of(seg)) for seg in soft["segments"]
               if seg["name"] in ("Simulators", "Launch monitor connectivity"))
    if sims * 2 <= len(items_of(soft)):
        sys.exit("finding copy says simulators and connectivity are most of the software; no longer true")
    return (f"Two DIY launch monitors, {e(top[0]['name'])} and {e(top[1]['name'])}, hold almost two thirds "
            f"of all the GitHub stars. Most of the software is simulators and the bridges that feed them.")


CSS = """
:root {
  --paper: #FFFFF0; --ink: #17241c; --fairway: #1d5637; --green: #2f8f57; --rough: #4c5b50;
  --tint: #eef1dc; --rule: #aeb696; --hair: #e3e7cf; --flag: #c2311f; --water: #2a55b0;
  --label: "Avenir Next Condensed", "Avenir Next", system-ui, sans-serif;
  --text: "Avenir Next", system-ui, sans-serif;
  --display: Charter, "Bitstream Charter", Georgia, serif;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html { background: var(--paper); }
body { background: var(--paper); color: var(--ink); font-family: var(--text); font-size: 19px;
  line-height: 1.25; -webkit-font-smoothing: antialiased; font-variant-numeric: tabular-nums lining-nums; }

.masthead { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; }
h1 { font-family: var(--display); font-weight: 900; letter-spacing: -0.02em; line-height: 0.98; }
.stamp { font-family: var(--label); font-weight: 600; font-size: 19px; color: var(--rough);
  text-align: right; white-space: nowrap; line-height: 1.3; padding-top: 10px; }
.stamp b { display: block; color: var(--ink); font-size: 22px; }
.dek, .finding { font-family: var(--display); line-height: 1.34; }
.finding { font-weight: 700; }

.mark { display: inline-block; width: 15px; height: 15px; flex: none; }
.mark.permissive { background: var(--green); border-radius: 50%; }
.mark.copyleft { background: var(--ink); }
.mark.public { background: var(--water); transform: rotate(45deg) scale(0.82); }
.mark.restricted { background: var(--flag); clip-path: polygon(50% 4%, 100% 96%, 0 96%); }
.mark.unknown { color: var(--rough); font-family: var(--text); font-weight: 700; font-size: 19px;
  line-height: 15px; text-align: center; }

.legend { list-style: none; display: flex; flex-wrap: wrap; gap: 10px 30px; font-size: 19px; }
.legend li { display: flex; align-items: center; gap: 8px; white-space: nowrap; }
.legend b { font-weight: 600; }
.legend .n { font-weight: 700; }
.legend .eg { color: var(--rough); font-weight: 500; }

.overview { display: grid; grid-template-columns: 4fr 6fr; column-gap: 40px; }
.ov-head { display: flex; justify-content: space-between; align-items: baseline;
  font-family: var(--display); font-weight: 900; font-size: 30px; letter-spacing: -0.01em;
  border-bottom: 3px solid var(--ink); padding-bottom: 6px; margin-bottom: 4px; }
.ov-row { display: grid; grid-template-columns: 222px minmax(0, 1fr) 30px; align-items: center;
  column-gap: 10px; padding: 8px 0; border-bottom: 1px solid var(--hair); }
.ov-name { font-family: var(--label); font-weight: 600; font-size: 20px; color: var(--fairway);
  white-space: nowrap; }
.ov-marks { display: flex; flex-wrap: wrap; gap: 5px; }
.ov-n { font-weight: 600; text-align: right; }

/* ---------- full reference table ---------- */
body.full { width: 1080px; padding: 56px 40px 40px; }
.full h1 { font-size: 80px; }
.full .dek { font-size: 27px; margin-top: 22px; max-width: 30em; }
.full .finding { font-size: 25px; margin: 40px 0 22px; max-width: 34em; }
.full .legend { margin-top: 26px; padding-top: 18px; border-top: 1px solid var(--rule); }

.side { margin-top: 64px; }
.side-head { display: flex; align-items: baseline; gap: 22px; border-bottom: 3px solid var(--ink);
  padding-bottom: 8px; }
.side-head h2 { font-family: var(--display); font-weight: 900; font-size: 60px;
  letter-spacing: -0.015em; line-height: 1; }
.side-head p { font-family: var(--display); font-size: 22px; color: var(--rough); flex: 1; }
.side-head .total { font-family: var(--label); font-weight: 600; font-size: 20px; text-align: right;
  white-space: nowrap; }
.colheads { display: flex; justify-content: flex-end; font-family: var(--label); font-weight: 500;
  font-size: 18px; color: var(--rough); padding: 8px 16px 0; }

.segment { margin-top: 30px; }
.band { display: flex; justify-content: space-between; align-items: baseline;
  border-top: 3px solid var(--fairway); border-bottom: 1px solid var(--rule); padding: 9px 16px 8px; }
.band h3 { font-family: var(--label); font-weight: 600; font-size: 28px; color: var(--fairway);
  letter-spacing: 0.005em; }
.band span { font-family: var(--label); font-weight: 500; font-size: 18px; color: var(--rough); }

.group { display: grid; grid-template-columns: 156px 1fr; border-bottom: 1px solid var(--rule); }
.glabel { font-family: var(--label); font-weight: 600; font-size: 20px; color: var(--fairway);
  background: var(--tint); padding: 14px 10px 12px 16px; line-height: 1.2; }
.glabel small { display: block; font-weight: 500; font-size: 16px; color: var(--rough); margin-top: 3px; }
.group.has-lead .glabel { padding-top: 18px; }
.items { padding: 4px 16px; }
.row { display: grid; grid-template-columns: minmax(0, 1fr) 226px 156px 70px; column-gap: 16px;
  align-items: baseline; padding: 8px 0; }
.items > .row + .row, .items > .kids + .row { border-top: 1px solid var(--hair); }
.name { font-weight: 600; font-size: 21px; white-space: nowrap; }
.owner { font-weight: 400; color: var(--rough); }
.note { font-size: 19px; font-weight: 500; color: var(--rough); white-space: nowrap; }
.lic { font-size: 19px; white-space: nowrap; display: flex; align-items: center; gap: 9px; }
.stars { text-align: right; font-size: 20px; }
.row.lead .name { font-size: 24px; font-weight: 700; letter-spacing: -0.01em; }
.row.lead .stars { font-weight: 700; font-size: 22px; }
.row.mid .stars { font-weight: 500; }
.row.low .stars, .row.none .stars { font-weight: 400; color: var(--rough); }

.kids { margin: -2px 0 10px 8px; border-left: 1.5px solid var(--rule); }
.row.kid { padding: 4px 0; }
.row.kid .name { font-weight: 400; font-size: 18px; padding-left: 26px; position: relative; }
.row.kid .name::before { content: ""; position: absolute; left: 0; top: 50%; width: 18px;
  border-top: 1.5px solid var(--rule); }
.row.kid .note, .row.kid .lic { font-size: 18px; }

.ground .band { border-top-style: dashed; }
.ground .lede { font-family: var(--display); font-size: 21px; color: var(--rough); padding: 14px 16px 6px; }
.ground .row { grid-template-columns: minmax(0, 1fr) 70px; padding: 8px 16px;
  border-bottom: 1px solid var(--hair); }
.ground .row .name { color: var(--rough); }
.ground .row .stars { color: var(--rough); }

footer { margin-top: 48px; padding-top: 14px; border-top: 3px solid var(--ink); display: flex;
  justify-content: space-between; align-items: baseline; gap: 24px; font-size: 18px;
  font-weight: 500; color: var(--rough); }
footer b { font-family: var(--display); font-weight: 900; font-size: 24px; color: var(--ink); }

/* ---------- market map ---------- */
body.map { width: 2560px; padding: 30px 30px 34px; }
.map-head { display: flex; align-items: baseline; gap: 28px; padding: 0 6px 22px; }
.map-head h1 { font-family: var(--text); font-weight: 800; font-size: 76px; line-height: 1;
  letter-spacing: -0.03em; white-space: nowrap; }
.map-head .sub-line { font-family: var(--text); font-weight: 600; font-size: 27px; flex: 1; }
.map-head .keys { display: flex; gap: 20px; font-family: var(--label); font-weight: 600; font-size: 19px;
  color: var(--rough); }
.map-head .keys span { display: inline-flex; align-items: center; gap: 6px; }
.map-head .keys .ico { width: 16px; height: 16px; }
.map-head .site { font-family: var(--label); font-weight: 600; font-size: 19px; color: var(--rough);
  text-align: right; white-space: nowrap; }
.map-head .site b { font-family: var(--text); font-weight: 800; font-size: 26px; color: var(--ink);
  margin-right: 14px; }
.zones { display: flex; gap: 22px; align-items: stretch; }
.zone { border-radius: 30px; padding: 0 18px 20px; display: flex; flex-direction: column; min-width: 0; }
.zone.hardware { background: #f3dfc4; }
.zone.software { background: #cfe0ea; }
.zone-head { display: flex; align-items: baseline; justify-content: space-between; gap: 16px;
  padding: 16px 8px 6px; }
.zone-head h2 { font-family: var(--text); font-weight: 800; font-size: 50px; letter-spacing: -0.025em;
  line-height: 1; }
.zone.hardware .zone-head h2 { color: #7a3410; }
.zone.software .zone-head h2 { color: #12406b; }
.zone-n { font-family: var(--text); font-weight: 700; font-size: 20px; white-space: nowrap; }
.zone-row { display: flex; gap: 16px; margin-top: 16px; flex: 1 1 auto; }
.cell { flex: 1 0 0; min-width: 0; display: flex; flex-direction: column; gap: 16px; }
.cell > .box { flex: 1 1 auto; }
.box { border: 3.5px solid var(--hue); border-radius: 22px; padding: 10px 12px 14px; min-width: 0;
  background: #fffffa; display: flex; flex-direction: column; }
.box-head { display: flex; flex-wrap: wrap; align-items: baseline; justify-content: space-between;
  gap: 2px 14px; padding: 2px 6px 10px; }
.box-head h3 { font-family: var(--text); font-weight: 700; font-size: 25px; line-height: 1.15;
  letter-spacing: -0.005em; color: var(--hue); }
.box-head span { font-family: var(--text); font-weight: 600; font-size: 16px; color: var(--rough);
  white-space: nowrap; }
.subs { flex: 1 1 auto; display: flex; flex-flow: row wrap; gap: 10px; align-content: stretch; }
.sub { display: flex; flex-direction: column;
  background: color-mix(in srgb, var(--hue) 12%, #fff);
  border: 1.5px solid color-mix(in srgb, var(--hue) 45%, #fff); border-radius: 13px;
  padding: 0 8px 12px; min-width: 0; }
.sub-name { align-self: flex-start; margin-left: 4px; font-family: var(--text); font-weight: 600;
  font-size: 15px; letter-spacing: 0.015em; line-height: 1.2; color: #fff; background: var(--hue);
  border-radius: 0 0 8px 8px; padding: 5px 13px 6px; margin-bottom: 11px; white-space: nowrap; }
.chips { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(214px, 100%), 1fr));
  gap: 9px 10px; align-content: start; }
.chip { display: flex; align-items: center; gap: 9px; min-width: 0; background: #fff; border: 1.5px solid var(--hair);
  border-radius: 10px; padding: 6px 10px 6px 7px; line-height: 1.15;
  box-shadow: 0 1px 0 var(--rule); text-align: left; }
.chip .logo { width: 44px; height: 44px; object-fit: contain; flex: none; border-radius: 7px; }
.chip .logo.avatar { border-radius: 50%; object-fit: cover; }
.chip .logo.page { object-fit: cover; }
.chip .txt { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.chip .by { font-family: var(--text); font-weight: 500; font-size: 13px; color: var(--rough);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center;
  gap: 5px; }
.gh { width: 13px; height: 13px; fill: var(--ink); flex: none; }
.chip .host { display: flex; align-items: center; gap: 5px; font-family: var(--text); font-weight: 600;
  font-size: 14px; color: var(--ink); white-space: nowrap; }
.chip .host img { width: 14px; height: 14px; border-radius: 3px; flex: none; }
.chip .nm { font-family: var(--text); font-weight: 700; font-size: 16px; letter-spacing: -0.015em; }
.chip .meta { display: flex; gap: 9px; white-space: nowrap; font-family: var(--text); font-weight: 600; font-size: 14px;
  color: var(--rough); }
.chip .meta > span { display: inline-flex; align-items: center; gap: 4px; }
.chip .st { color: var(--ink); }
.ico { width: 13px; height: 13px; fill: #c98a00; flex: none; }
.ico.line { fill: none; stroke: currentColor; stroke-width: 1.4; stroke-linecap: round; stroke-linejoin: round; }
.chip .plus { font-family: var(--label); font-weight: 600; font-size: 13px; color: var(--rough);
  white-space: nowrap; display: inline-block;
  margin-left: 7px; letter-spacing: 0; }

/* The map is dark, to sit on the dark site ("Night fairway"). Segment hues stay as they are (they
   carry the white tab text); headings and borders use lightened mixes of them, and logos sit on
   a light plate because many are dark marks on a transparent background. */
html:has(body.map), body.map { --paper: #0e1712; --ink: #e6ead9; --rough: #a3b3a7; --hair: #33443a;
  --rule: #060a08; }
body.map .map-head { align-items: center; padding-bottom: 20px; }
body.map .map-head .mark { height: 112px; flex: none; margin-right: 12px; }
body.map .map-head h1 { padding-left: 40px; border-left: 3px solid var(--hair); line-height: 112px;
  font-size: 0; }
body.map .map-head h1 svg { height: 96px; display: block; margin: 8px 0; }
body.map .map-head .sub-line { white-space: nowrap; }
body.map .zone.hardware { background: #2b1f14; }
body.map .zone.software { background: #13232f; }
body.map .zone.hardware .zone-head h2 { color: #f2b98c; }
body.map .zone.software .zone-head h2 { color: #9fcff2; }
body.map .box { background: #0f1814; border-color: color-mix(in srgb, var(--hue) 78%, #fff); }
body.map .box-head h3 { color: color-mix(in srgb, var(--hue) 48%, #fff); }
body.map .sub { background: color-mix(in srgb, var(--hue) 20%, #0f1814);
  border-color: color-mix(in srgb, var(--hue) 60%, #0f1814); }
body.map .chip { background: #1c2822; }
body.map .chip .logo { background: #f4f5ea; }
body.map .ico { fill: #f0b429; }
body.map .ico.line { fill: none; }

/* ---------- share card ---------- */
body.card { width: 1200px; height: 675px; padding: 40px 48px 0; overflow: hidden; }
.card h1 { font-size: 62px; }
.card .finding { font-size: 23px; margin: 16px 0 20px; max-width: 46em; }
.card .ov-head { font-size: 26px; padding-bottom: 4px; }
.card .ov-row { padding: 6px 0; }
.card .legend { margin-top: 16px; font-size: 18px; }
"""


def page(body_class: str, body: str) -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f"<title>The open source golf landscape</title><style>{CSS}</style></head>"
            f'<body class="{body_class}">{body}'
            "<script>const r = document.documentElement;"
            "r.dataset.h = Math.ceil(document.body.getBoundingClientRect().height);"
            "r.dataset.ih = window.innerHeight;"
            "r.dataset.overflow = [...document.querySelectorAll('.row > span, .ov-name, .legend li, .box-head h3, .box .chips')]"
            ".filter(s => s.scrollWidth > s.clientWidth + 1).map(s => s.textContent).join('|');"
            "</script></body></html>")


def masthead(d: dict) -> str:
    return (f'<div class="masthead"><h1>The open source golf landscape</h1>'
            f'<p class="stamp"><b>ossgolf.com</b>Snapshot {e(d["asOf"])}</p></div>')


def full_html(d: dict) -> str:
    total = sum(len(items_of(s)) for s in d["sides"])
    attached = sum(len(i.get("with", [])) for s in d["sides"] for i in items_of(s))
    parts = [
        masthead(d),
        f'<p class="dek">{total} projects you can build and fork, plus {attached} companion repos, '
        f"sorted by what they are and how they work.</p>",
        f'<p class="finding">{finding(d)}</p>',
        overview_html(d),
        legend_html(d),
    ]
    for side in d["sides"]:
        its = items_of(side)
        stars = sum(i.get("stars") or 0 for i in its)
        parts.append(
            f'<section class="side"><header class="side-head"><h2>{e(side["name"])}</h2>'
            f'<p>{e(side["blurb"])}</p>'
            f'<span class="total">{plural(len(its), "project")}, {stars:,} stars</span></header>'
            f'<div class="colheads">GitHub stars</div>'
        )
        for seg in side["segments"]:
            parts.append(
                f'<div class="segment"><div class="band"><h3>{e(seg["name"])}</h3>'
                f'<span>{plural(len(items_of(seg)), "project")}</span></div>'
            )
            for g in seg["groups"]:
                n = len(g["items"])
                lead = " has-lead" if tier(g["items"][0].get("stars")) == "lead" else ""
                count = f"<small>{n} projects</small>" if n >= 3 else ""
                parts.append(
                    f'<div class="group{lead}"><div class="glabel">{e(g["name"])}{count}</div>'
                    f'<div class="items">{"".join(item_html(i) for i in g["items"])}</div></div>'
                )
            parts.append("</div>")
        parts.append("</section>")
    ground = "".join(
        f'<div class="row"><span class="name">{e(x)}</span><span class="stars">0</span></div>'
        for x in d["openGround"]
    )
    parts.append(
        '<section class="side ground"><div class="segment"><div class="band"><h3>Open ground</h3>'
        "<span>0 projects</span></div>"
        '<p class="lede">We have not found an openly licensed one of these yet.</p>'
        f"{ground}</div></section>"
        f'<footer><b>ossgolf.com</b><span>Stars and licenses from each project’s page, '
        f'{e(d["asOf"])}. Stars measure attention, not quality.</span></footer>'
    )
    return page("full", "".join(parts))


def card_html(d: dict) -> str:
    return page("card", masthead(d) + f'<p class="finding">{finding(d)}</p>'
                + overview_html(d) + legend_html(d))


# The map is two zones side by side. Each zone is a list of rows; a row is a list of
# (segment or stack of segments, relative width).
MAP_ROWS = {
    "Hardware": [
        [("Launch monitors", 1)],
        [("On-course trackers", 1), ("Training aids", 1)],
        [("Biomechanics", 1), ("3D printable", 1)],
    ],
    "Software": [
        [("Simulators", 1.5), ("Launch monitor connectivity", 1.1)],
        [("Swing analysis", 1.05), ("Stats and scoring", 1.25), ("Course data", 0.8), ("Camera ball tracking", 0.62)],
    ],
}
MAP_ZONE_WIDTH = {"Hardware": 25, "Software": 75}  # percent
MAP_WIDTH = 2560


STAR_ICON = ('<svg class="ico" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 1.2l2.1 4.3 4.7.7-3.4 3.3.8 4.7'
             'L8 12l-4.2 2.2.8-4.7L1.2 6.2l4.7-.7z"/></svg>')
# A simple balance scale, drawn for this graphic.
LICENSE_ICON = ('<svg class="ico line" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2v11.5M4.5 13.5h7'
                'M2.5 4h11M4 4L2 9.2a2.1 2.1 0 004 0zM12 4l-2 5.2a2.1 2.1 0 004 0z"/></svg>')


# One hue per segment on the map, never repeated, spread around the colour wheel and assigned so
# neighbouring boxes are far apart. Sub-boxes use tints of their segment's hue. All are dark
# enough for white tab text.
SEGMENT_HUES = {
    "Launch monitors": "#c1272d",              # red
    "On-course trackers": "#00857c",           # teal
    "Training aids": "#9c7a00",                # gold
    "Biomechanics": "#8a5a2b",                 # brown
    "3D printable": "#4a5560",                 # slate
    "Simulators": "#1b7f3b",                   # green
    "Launch monitor connectivity": "#2456c9",  # blue
    "Swing analysis": "#0a7fb5",               # sky
    "Stats and scoring": "#cf5a00",            # orange
    "Course data": "#6b3fc0",                  # violet
    "Camera ball tracking": "#5a8f00",         # lime
}
assert len(set(SEGMENT_HUES.values())) == len(SEGMENT_HUES), "segment hues must be unique"


# GitHub's mark, from the MIT-licensed Octicons set; shown only on projects hosted on GitHub.
GITHUB_ICON = ('<svg class="gh" viewBox="0 0 16 16" aria-hidden="true"><path d="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1'
               '-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95'
               ' 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2'
               ' .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64'
               ' 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9'
               '.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42'
               ' 3.58-8 8-8Z"/></svg>')


def owner_of(it: dict) -> str:
    """The GitHub account a project lives under, or the designer for models hosted elsewhere."""
    if it.get("by"):
        return it["by"]
    m = re.match(r"https://github\.com/([^/]+)", it["url"])
    return m.group(1) if m else ""


def chip_html(it: dict) -> str:
    """One project tile: its logo or avatar, name, star count, and license when there is one."""
    kids = it.get("with", [])
    plus = f'<span class="plus">+{len(kids)} repo{"s" if len(kids) != 1 else ""}</span>' if kids else ""
    logo = ""
    if it.get("logo"):
        logo = f'<img class="logo {e(it.get("logoSource", ""))}" src="logos/{e(it["logo"])}" alt="">'
    host = ""
    if it.get("host"):  # projects that live somewhere other than GitHub say where, on their own line
        host = (f'<span class="host"><img src="logos/{e(it["host"]["icon"])}" alt="">'
                f'{e(it["host"]["name"])}</span>')
    stars = it.get("stars")
    meta = []
    if stars is not None:
        meta.append(f'<span class="st">{STAR_ICON}{stars:,}</span>')
    fam = family(it["license"])
    if fam != "unknown":
        meta.append(f'<span class="lc {fam}">{LICENSE_ICON}{e(it["license"])}</span>')
    return (f'<span class="chip">{logo}<span class="txt">'
            f'<span class="by">{GITHUB_ICON if it["url"].startswith("https://github.com/") else ""}'
            f'{e(owner_of(it))}</span>'
            f'<span class="nm">{e(it["name"])}{plus}</span>{host}'
            f'<span class="meta">{"".join(meta)}</span></span></span>')


def box_html(seg: dict) -> str:
    subs = "".join(
        f'<div class="sub" style="flex: {min(len(g["items"]), 3)} 1 {min(len(g["items"]), 3) * 232}px">'
        f'<div class="sub-name">{e(g["name"])}</div>'
        f'<div class="chips">{"".join(chip_html(i) for i in g["items"])}</div></div>'
        for g in seg["groups"]
    )
    return (f'<div class="box" style="--hue: {SEGMENT_HUES[seg["name"]]}">'
            f'<div class="box-head"><h3>{e(seg["name"])}</h3>'
            f'<span>{plural(len(items_of(seg)), "project")}</span></div>'
            f'<div class="subs">{subs}</div></div>')


def map_html(d: dict) -> str:
    total = sum(len(items_of(s)) for s in d["sides"])
    zones = []
    for side in d["sides"]:
        segs = {seg["name"]: seg for seg in side["segments"]}
        placed, rows = set(), []
        for row in MAP_ROWS[side["name"]]:
            cells = []
            for names, weight in row:
                names = (names,) if isinstance(names, str) else names
                placed.update(names)
                cells.append(f'<div class="cell" style="flex-grow: {weight}">'
                             f'{"".join(box_html(segs[n]) for n in names)}</div>')
            rows.append(f'<div class="zone-row">{"".join(cells)}</div>')
        if placed != set(segs):
            sys.exit(f"MAP_ROWS for {side['name']} does not match the data: {placed ^ set(segs)}")
        n = len(items_of(side))
        zones.append(
            f'<section class="zone {side["name"].lower()}" style="width: {MAP_ZONE_WIDTH[side["name"]]}%">'
            f'<header class="zone-head"><h2>{e(side["name"])}</h2>'
            f'<span class="zone-n">{plural(n, "project")}</span></header>'
            f'{"".join(rows)}</section>'
        )
    # The site's wordmark leads the title. Imported here because logo.py itself imports this module.
    from logo import FONT, Glyphs, wordmark
    glyphs = Glyphs(FONT)
    mark, mw, mh = wordmark(glyphs)
    logo = (f'<svg class="mark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {mw:g} {mh:g}" '
            f'shape-rendering="crispEdges" role="img" aria-label="oss/golf, for the hackers" '
            f'style="width: {112 * mw / mh:.0f}px">{mark}</svg>')
    # The title is drawn as outlines too, in the wordmark's font, so it gets the same repairs.
    name = "Open Source Golf Landscape"
    title, tw = glyphs.text(name, 0, "currentColor")
    title = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {tw:g} 1000" role="img" '
             f'aria-label="{name}" style="width: {96 * tw / 1000:.0f}px">{title}</svg>')
    head = (
        f'<header class="map-head">{logo}<h1>{title}</h1>'
        f'<p class="sub-line">{total} projects you can build and fork</p>'
        f'<p class="keys"><span>{STAR_ICON} GitHub stars</span><span>{LICENSE_ICON} License</span></p>'
        f'<p class="site"><b>ossgolf.com</b>Snapshot {e(d["asOf"])}</p></header>'
    )
    return page("map", f'{head}<div class="zones">{"".join(zones)}</div>')


def chrome(profile: Path, *args: str) -> str:
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
           f"--user-data-dir={profile}", "--virtual-time-budget=2000", *args]
    for attempt in (1, 2):  # headless Chrome occasionally exits early on a cold start; once more is enough
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if run.returncode == 0:
            return run.stdout
    run.check_returncode()


def render(src: Path, out: Path, width: int, fixed_height=None) -> int:
    profile = Path(tempfile.mkdtemp(prefix="landscape-chrome-"))
    try:
        dom = chrome(profile, f"--window-size={width},2000", "--dump-dom", src.as_uri())
        attr = lambda k: re.search(rf'data-{k}="([^"]*)"', dom).group(1)
        height = fixed_height or int(attr("h"))
        if attr("overflow"):
            print(f"WARNING {src.name}: text overflows its column:", html.unescape(attr("overflow")),
                  file=sys.stderr)
        if fixed_height and int(attr("h")) > fixed_height:
            print(f"WARNING {src.name}: content is {attr('h')}px tall, card is {fixed_height}px",
                  file=sys.stderr)
        # Headless Chrome's viewport is shorter than --window-size, and the screenshot is
        # window-sized: pad the window by the gap, then trim the padding back off.
        gap = 2000 - int(attr("ih"))
        out.parent.mkdir(parents=True, exist_ok=True)
        chrome(profile, f"--window-size={width},{height + gap}", "--force-device-scale-factor=2",
               f"--screenshot={out}", src.as_uri())
        # sips crops from the centre unless the offset is non-zero.
        subprocess.run(["sips", "--cropOffset", "1", "1", "-c", str(height * 2), str(width * 2), str(out)],
                       capture_output=True, check=True)
        return height
    finally:
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    data = json.loads(DATA.read_text())
    jobs = [
        ("landscape.html", full_html, "open-source-golf-landscape.png", 1080, None),
        ("landscape-card.html", card_html, "open-source-golf-landscape-card.png", 1200, 675),
        # /images is cached by browsers for a year as immutable (_site/_headers), so a redrawn map
        # must ship under a new name: bump the -vN here and in posts.json whenever its look changes.
        ("landscape-map.html", map_html, "open-source-golf-landscape-map-v3.png", MAP_WIDTH, None),
    ]
    for page_name, build, image_name, width, fixed in jobs:
        src = HERE / page_name
        src.write_text(build(data))
        h = render(src, IMAGES / image_name, width, fixed)
        print(f"wrote {(IMAGES / image_name).relative_to(ROOT)} ({width}x{h} @2x)")
    # A lighter copy of the map for embedding in posts; it links through to the full-size one.
    preview = IMAGES / "open-source-golf-landscape-map-v3-1920.png"
    subprocess.run(["sips", "-Z", "1920", str(IMAGES / "open-source-golf-landscape-map-v3.png"), "--out", str(preview)],
                   capture_output=True, check=True)
    print(f"wrote {preview.relative_to(ROOT)}")
