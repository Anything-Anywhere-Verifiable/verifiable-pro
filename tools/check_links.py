#!/usr/bin/env python3
"""Check internal links and anchors in a preview build (relative links)."""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if key in a and a[key]:
                self.links.append((tag, a[key]))


def main(root):
    root = Path(root).resolve()
    pages, problems = {}, []
    for f in root.rglob("*.html"):
        c = Collector()
        c.feed(f.read_text(encoding="utf-8"))
        pages[f] = c
    for f, c in pages.items():
        for tag, link in c.links:
            if re.match(r"^(https?:|mailto:|data:|tel:)", link) or link.startswith("//"):
                continue
            if link.startswith("/"):
                problems.append(f"{f.relative_to(root)}: absolute link {link}")
                continue
            path, _, frag = link.partition("#")
            target = (f.parent / unquote(path)).resolve() if path else f
            if target.is_dir():
                problems.append(f"{f.relative_to(root)}: directory link {link}")
                continue
            if not target.exists():
                problems.append(f"{f.relative_to(root)}: missing {link}")
                continue
            if frag and target.suffix == ".html":
                ids = pages[target].ids if target in pages else set()
                if frag not in ids:
                    problems.append(f"{f.relative_to(root)}: missing anchor {link}")
    print(f"checked {len(pages)} pages; {len(problems)} problems")
    for p in problems[:200]:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
