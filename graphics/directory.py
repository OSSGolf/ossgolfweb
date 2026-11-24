#!/usr/bin/env python3
"""Write the project directory into the "Open Source Golf is Exploding" post.

The map in that post is an image, so its projects cannot be clicked, searched or read aloud. This
script turns the same data (graphics/landscape.json) into a text list: one heading per side
(Hardware, Software), one per segment, then every project as a link with its description, and its
companion repos nested underneath.

It replaces everything in the post body between the line after the map and the closing line, so
it is safe to run again after landscape.json changes:

    python3 graphics/directory.py && ./build.sh
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "graphics" / "landscape.json"
POSTS = ROOT / "posts.json"
SLUG = "open-source-golf-is-exploding"
START = "Tap the map to open it full size."     # the list goes after this line...
END = "We will keep adding to this list"        # ...and before the paragraph that starts with this


SMALL = {"a", "an", "and", "at", "for", "in", "is", "of", "on", "or", "the", "to", "with"}


def title_case(text: str) -> str:
    """Headings on the site are capitalized. Words that already carry a capital (APIs, GPS, 3D) stay."""
    def cap(word: str, first: bool) -> str:
        if word.lower() in SMALL and not first:
            return word.lower()
        return word if word != word.lower() else word[:1].upper() + word[1:]
    words = text.split(" ")
    return " ".join("-".join(cap(part, i == 0) for part in w.split("-")) for i, w in enumerate(words))


def entry(it: dict, indent: str = "") -> str:
    missing = [k for k in ("url", "description") if not it.get(k)]
    if missing:
        sys.exit(f'{it["name"]}: no {" or ".join(missing)} in {DATA.name}')
    return f'{indent}- **[{it["name"]}]({it["url"]})**: {it["description"]}'


def directory(d: dict) -> str:
    out = []
    for side in d["sides"]:
        out += [f'## {title_case(side["name"])}', ""]
        for seg in side["segments"]:
            out += [f'### {title_case(seg["name"])}', ""]
            for group in seg["groups"]:
                out += [f'#### {title_case(group["name"])}', ""]
                for it in group["items"]:
                    out.append(entry(it))
                    out += [entry(kid, "  ") for kid in it.get("with", [])]
                out.append("")
    return "\n".join(out).rstrip()


if __name__ == "__main__":
    data = json.loads(DATA.read_text())
    raw = POSTS.read_text()
    posts = json.loads(raw)
    post = next(p for p in (posts if isinstance(posts, list) else posts["posts"]) if p["slug"] == SLUG)
    key = "body" if "body" in post else "content"
    body = post[key]
    if body.count(START) != 1 or body.count(END) != 1:
        sys.exit(f"the post no longer has exactly one {START!r} and one {END!r} line")
    head, tail = body[:body.index(START) + len(START)], body[body.index(END):]
    post[key] = f"{head}\n\n{directory(data)}\n\n{tail}"
    POSTS.write_text(json.dumps(posts, indent=2 if raw.startswith(("[\n ", "{\n ")) else None,
                                ensure_ascii=False) + ("\n" if raw.endswith("\n") else ""))
    count = sum(1 + len(i.get("with", [])) for s in data["sides"] for seg in s["segments"]
                for g in seg["groups"] for i in g["items"])
    print(f"wrote {count} projects into the {SLUG} post")
