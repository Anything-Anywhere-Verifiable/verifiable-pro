#!/usr/bin/env python3
"""Screenshot a preview build with headless Chrome.

    python3 tools/shoot.py SITE_DIR OUT_DIR [--pages home,article,...] [--reduced]

Produces PNGs such as home-desktop.png, home-mobile.png, home-dark.png and
zh-home-desktop.png. Dark shots inject data-theme="dark" into a temporary
copy of the page next to the original so relative links keep working.
--reduced asks Chrome for prefers-reduced-motion: reduce, so the home hero
shows its still frame, and the file names end in -reduced.

Page names: home, tee (the TEE hub), latest, topics (the Stack page), topic (the
first other topic), learn, resources, vision, glossary, about, search, article
(--article, or the alphabetically first), brief (a news brief that is not about
TEEs), tee-brief (the DDRop brief) and longform (an explainer), each with a zh-
twin such as zh-tee.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SIZES = {"desktop": (1440, 2600), "mobile": (390, 2400), "tablet": (820, 2000)}
TEE_HUB = "topics/confidential-computing/index.html"
BRIEF = "articles/nist-nsa-cisa-agent-incident-practices/index.html"
TEE_BRIEF = "articles/ddrop-ddr5-interposer-attack/index.html"
LONGFORM = "articles/remote-attestation-for-ai-workloads-explained/index.html"


def first_article(site):
    arts = sorted((site / "articles").glob("*/index.html"))
    return arts[0].relative_to(site).as_posix() if arts else "index.html"


def page_map(site, article=None):
    article = article or first_article(site)
    topics = [p.relative_to(site).as_posix() for p in sorted((site / "topics").glob("*/index.html"))
              if p.parent.name != "confidential-computing"]
    en = {
        "home": "index.html",
        "tee": TEE_HUB,
        "latest": "latest/index.html",
        "topics": "topics/index.html",
        "topic": topics[0] if topics else "topics/index.html",
        "learn": "learn/index.html",
        "resources": "resources/index.html",
        "vision": "vision/index.html",
        "glossary": "glossary/index.html",
        "about": "about/index.html",
        "search": "search/index.html",
        "article": article,
        "brief": BRIEF,
        "tee-brief": TEE_BRIEF,
        "longform": LONGFORM,
    }
    return {**en, **{f"zh-{name}": f"zh/{path}" for name, path in en.items()}}


def shoot(url, out, size, reduced=False):
    w, h = size
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--virtual-time-budget=6000",
           f"--window-size={w},{h}", f"--screenshot={out}"]
    if reduced:
        cmd.append("--force-prefers-reduced-motion")
    subprocess.run(cmd + [url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)


def dark_copy(path):
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<html([^>]*)>", r'<html\1 data-theme="dark">', text, count=1)
    copy = path.with_name(path.stem + ".dark-shot.html")
    copy.write_text(text, encoding="utf-8")
    return copy


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("out")
    ap.add_argument("--pages", default="home,article,latest,resources,zh-home")
    ap.add_argument("--sizes", default="desktop,mobile")
    ap.add_argument("--dark", default="home,article", help="pages to also shoot in dark mode (desktop and mobile)")
    ap.add_argument("--article", default=None, help="article path relative to the site, e.g. articles/<slug>/index.html")
    ap.add_argument("--reduced", action="store_true", help="emulate prefers-reduced-motion: reduce")
    args = ap.parse_args()
    site, out = Path(args.site).resolve(), Path(args.out).resolve()
    pages = page_map(site, args.article)
    names = [p for p in args.pages.split(",") if p]
    darks = [p for p in args.dark.split(",") if p]
    unknown = [n for n in names + darks if n not in pages]
    if unknown:
        ap.error(f"unknown page {unknown[0]!r}; use one of: {', '.join(pages)}")
    unknown = [s for s in args.sizes.split(",") if s not in SIZES]
    if unknown:
        ap.error(f"unknown size {unknown[0]!r}; use one of: {', '.join(SIZES)}")
    out.mkdir(parents=True, exist_ok=True)
    tag = "-reduced" if args.reduced else ""
    made = []
    for name in names:
        target = site / pages[name]
        if not target.exists():
            made.append(f"{name}: skipped, {pages[name]} is not in this build")
            continue
        for size in args.sizes.split(","):
            png = out / f"{name}{tag}-{size}.png"
            shoot(target.as_uri(), png, SIZES[size], args.reduced)
            made.append(png.name)
    for name in darks:
        target = site / pages[name]
        if not target.exists():
            made.append(f"{name}: skipped, {pages[name]} is not in this build")
            continue
        copy = dark_copy(target)
        try:
            for size in ("desktop", "mobile"):
                png = out / f"{name}-dark{tag}-{size}.png"
                shoot(copy.as_uri(), png, SIZES[size], args.reduced)
                made.append(png.name)
        finally:
            copy.unlink(missing_ok=True)
    print("\n".join(made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
