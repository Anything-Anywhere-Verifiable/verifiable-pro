#!/usr/bin/env python3
"""Build the verifiable.pro static site (standard library only).

    python3 build.py                  # production build into public/
    python3 build.py --mode preview   # relative links for local file preview
    python3 build.py --mode artifact --out dist-artifact
    python3 build.py --mode preview --chat off            # without the Ask assistant
    python3 build.py --mode preview --chat live --chat-api http://127.0.0.1:8787

--chat and --chat-api override "chat.mode" and "chat.api_base" in
content/site.json for one build.

sitegen/discover.py writes what search engines and agents read: robots.txt,
llms.txt, llms-full.txt, the JSON Feeds and the web app manifests, and the
structured data and social tags in each page's head. The social cards and icons
are committed PNG files that tools/og_images.py draws; the build only checks and
links them.

The home page hero is the inline SVG scene in sitegen/templates/hero-scene.svg,
with the seven layer labels beside it; sitegen/templates/hero-anchors.json says
where each label's leader line starts on the scene. hero_scene_check stops a build
whose scene has lost a group, hit area or the person that the page addresses, or
whose person carries a transform; tools/hero/person.py draws the person and
tools/hero/flow.py the data that flows from their phone.

An article's lead image is described by content/articles/<slug>/illustration.json,
which sitegen/content.py checks against the pictures in static/media/: a photo
and its three copies (two for lists, one for link previews), which tools/photos.py writes,
or an illustration, which tools/illustrate.py draws. The build publishes the spec
beside the article's sources and the pictures under /assets/media/, lists them
all in the manifest (lead_images()), and warns about files in static/media/ that
no spec names, which it does not publish.
"""

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

from sitegen import art, content, discover, md
from sitegen import render
from sitegen.render import Site

ROOT = Path(__file__).resolve().parent

# Pages in content/pages/ whose header item they mark as current
PAGE_SECTIONS = ("about", "vision")
# Placeholders that a production build reports until the owner replaces them
PLACEHOLDER_PAGES = ("about", "vision")
PLACEHOLDERS = {"[editor": "the editor line", "[to be confirmed": "an owner decision",
                "[待网站所有者确认": "an owner decision"}
# The hero scene; the templates fill its title and description in the page language, and the
# description's data-hv-live, the sentences that static/hero.js adds once it runs
HERO_TEMPLATE = Path("sitegen") / "templates" / "hero-scene.svg"
HERO_SLOTS = ("{{SCENE_TITLE}}", "{{SCENE_DESC}}", "{{SCENE_DESC_LIVE}}")
# Where each layer's leader line starts on the scene, in its viewBox units
HERO_ANCHORS = Path("sitegen") / "templates" / "hero-anchors.json"
VIEWBOX_RE = re.compile(r'<svg\b[^>]*\sviewBox="([^"]+)"')


def callout_titles(strings):
    return {
        "facts": strings.get("callout_facts", ""),
        "analysis": strings.get("callout_analysis", ""),
        "checked": strings.get("callout_checked", ""),
        "example": strings.get("callout_example", ""),
        "note": strings.get("callout_note", ""),
        "limits": strings.get("callout_limits", ""),
    }


def resolver(site, lang, page_path):
    """Resolve site-absolute links written in Markdown for the page being rendered."""
    def resolve(target):
        path = target.split("#", 1)[0]
        is_page = path.endswith("/") or path == ""
        if lang == "zh" and is_page and not target.startswith("/zh/"):
            target = "/zh" + target
        site.current = page_path
        return site.href(target)
    return resolve


def render_markdown(doc, ctx):
    try:
        return md.render(doc.body, ctx)
    except ValueError as exc:  # e.g. two headings with the same {#id}
        raise content.ContentError(f"{doc.path}: {exc}") from exc


def render_docs(model, mode):
    site = Site(model, mode)
    for lang in content.LANGS:
        titles = callout_titles(model["strings"][lang])
        prefix = "/zh" if lang == "zh" else ""
        for a in model["articles"][lang]:
            reserved = render.PAGE_IDS + tuple(f"source-{s['n']}" for s in a.sources)
            ctx = md.Context(doc_id=f"{a.slug}-{lang}", source_count=len(a.sources), callout_titles=titles,
                             resolve=resolver(site, lang, f"{prefix}/articles/{a.slug}/"), reserved=reserved)
            a.html, ctx = render_markdown(a, ctx)
            a.headings = ctx.headings
            missing = [n for n in ctx.cited if not 1 <= int(n) <= len(a.sources)]
            if missing:
                raise content.ContentError(f"{a.path}: citation [^{missing[0]}] has no matching source")
        for page in model["pages"][lang].values():
            ctx = md.Context(doc_id=f"page-{page.name}-{lang}", callout_titles=titles,
                             resolve=resolver(site, lang, f"{prefix}/{page.name}/"), reserved=render.PAGE_IDS)
            page.html, ctx = render_markdown(page, ctx)
            page.headings = ctx.headings


def attach_art(model):
    by_slug = {a.slug: a for a in model["articles"]["en"]}
    for lang in content.LANGS:
        strings = model["strings"][lang]
        for a in model["articles"][lang]:
            en = by_slug[a.slug]
            # the drawing comes from the English source; the label names the page's own title
            label = strings.get("art_label", render.FALLBACK_STRINGS[lang]["art_label"]).format(title=a.title)
            svg, digest = art.illustration(en.raw.decode("utf-8"), en.primary_topic, label, show_hash=False)
            if digest != en.sha256:
                raise content.ContentError(f"{en.path}: illustration digest does not match the source digest")
            a.art, a.art_hash = svg, digest


def data_bytes(model, name):
    """The bytes of content/<name>.json as loaded, so the digest, the published copy
    and the pages built from it agree even if the file changes during the build."""
    raw = model.get("raw", {}).get(name)
    return raw if raw is not None else (ROOT / "content" / f"{name}.json").read_bytes()


def lead_images(model):
    """The lead images of the published articles, one per article, in slug order. A
    Chinese edition shares its English original's image, which is published with it."""
    found = {}
    for lang in content.LANGS:
        for a in model["articles"][lang]:
            if getattr(a, "lead_image", None) is not None:
                found.setdefault(a.slug, a.lead_image)
    return [found[slug] for slug in sorted(found)]


def manifest(model):
    entries = []
    for lang in content.LANGS:
        for a in model["articles"][lang]:
            entries.append({
                "source": f"/articles/{a.slug}/{lang}.md",
                "page": ("/zh" if lang == "zh" else "") + f"/articles/{a.slug}/",
                "lang": lang, "kind": a.kind, "title": a.title,
                "published": a.published.isoformat(),
                "updated": a.updated.isoformat() if a.updated else None,
                "bytes": len(a.raw), "sha256": a.sha256,
            })
        for page in model["pages"][lang].values():
            entries.append({
                "source": f"/pages/{page.name}.{lang}.md",
                "page": ("/zh" if lang == "zh" else "") + f"/{page.name}/",
                "lang": lang, "kind": "page", "title": page.title,
                "published": page.published.isoformat() if page.published else None,
                "updated": page.updated.isoformat() if page.updated else None,
                "bytes": len(page.raw), "sha256": page.sha256,
            })
    for name in content.DATA_FILES:
        raw = data_bytes(model, name)
        entries.append({"source": f"/data/{name}.json", "page": None, "lang": None, "kind": "data", "title": name,
                        "published": None, "updated": None, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    # each lead image: its illustration.json (kind "illustration") and the image file it names
    # (kind "image"), listed once for both editions. Like the data files they name no page,
    # so "page" still leads to exactly one entry, the page's own Markdown source; the spec's
    # path names its article, and its title is the article's slug
    for image in lead_images(model):
        entries.append({"source": image.spec_path, "page": None, "lang": None, "kind": "illustration",
                        "title": image.slug, "published": None, "updated": None,
                        "bytes": len(image.spec_raw), "sha256": image.spec_sha256})
        # the picture, then a photo's copies for lists and link previews, each its own "image"
        for picture in image.published():
            entries.append({"source": picture.src, "page": None, "lang": None, "kind": "image", "title": image.slug,
                            "published": None, "updated": None, "bytes": len(picture.raw), "sha256": picture.sha256})
    entries.sort(key=lambda e: e["source"])
    body = {"site": model["site"]["domain"], "hash": "sha256", "entries": entries}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    doc = dict(body)
    doc["digest_note"] = "digest = sha256 of this object without 'digest' and 'digest_note', serialized with sorted keys, no whitespace, UTF-8"
    doc["digest"] = digest
    return doc, digest


XML_INVALID_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")


def xml_text(value):
    """Escape element text; drop characters XML 1.0 forbids, which would void the whole feed."""
    return xml_escape(XML_INVALID_RE.sub("", str(value)))


def xml_attr(value):
    """Escape a double-quoted attribute value."""
    return xml_escape(XML_INVALID_RE.sub("", str(value)), {'"': "&quot;"})


def atom(site, model, lang, base):
    s = model["strings"][lang]
    items = model["articles"][lang][:20]
    prefix = "/zh" if lang == "zh" else ""
    updated = max((a.updated or a.published) for a in items) if items else dt.date.today()
    out = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="{xml_attr(s["html_lang"])}" xml:base="{xml_attr(base + "/")}">',
        f"<title>verifiable.pro</title><subtitle>{xml_text(s['footer_about'])}</subtitle>",
        f'<link href="{xml_attr(base + prefix + "/feed.xml")}" rel="self"/><link href="{xml_attr(base + prefix + "/")}"/>',
        f"<id>{xml_text(base + prefix)}/</id><updated>{updated.isoformat()}T00:00:00Z</updated>",
    ]
    domain = model["site"]["domain"]
    for a in items:
        url = f"{base}{prefix}/articles/{a.slug}/"
        tag = f"tag:{domain},{a.published.isoformat()}:{prefix}/articles/{a.slug}/"
        # the byline: a person, or an automated byline marked as automated, with About's #ai as its address;
        # the person who submitted the story, when someone did, is the entry's contributor
        who = discover.byline(site, a, lang)
        uri = f"<uri>{xml_text(who['url'])}</uri>" if who.get("url") else ""
        submitted = " ".join(str(getattr(a, "submitted_by", "") or "").split())
        contributor = f"<contributor><name>{xml_text(submitted)}</name></contributor>" if submitted else ""
        # xml:base on <content> resolves the body's "#source-1" and relative links against the article
        out.append(
            f"<entry><title>{xml_text(a.title)}</title><link href=\"{xml_attr(url)}\"/>"
            f"<id>{xml_text(tag)}</id>"
            f"<published>{a.published.isoformat()}T00:00:00Z</published>"
            f"<updated>{(a.updated or a.published).isoformat()}T00:00:00Z</updated>"
            f"<summary>{xml_text(a.dek)}</summary><content type=\"html\" xml:base=\"{xml_attr(url)}\">{xml_text(a.html)}</content>"
            f"<category term=\"{xml_attr(a.kind)}\"/>" + "".join(f"<category term=\"{xml_attr(t)}\"/>" for t in a.topics) +
            f"<author><name>{xml_text(who['name'])}</name>{uri}</author>{contributor}</entry>"
        )
    out.append("</feed>")
    return "\n".join(out) + "\n"


def sitemap(pages, base, lastmod=None):
    """Every indexable page: not the 404 pages, nor a page whose head asks search engines
    not to index it (render.ROBOTS_NOINDEX), such as the search pages. A page in both
    languages lists both versions and the English one as x-default, as its head does, and a
    page in one language lists none. PAGES maps each path to its HTML; LASTMOD maps a page's
    path to the date of its last revision (its updated, else its published date), where the
    content gives one."""
    lastmod = lastmod or {}
    pairs = {}
    for path, text in pages.items():
        if path.endswith(".html") or render.ROBOTS_NOINDEX in text:
            continue
        key = path[3:] if path.startswith("/zh/") else path
        pairs.setdefault(key, {})["zh" if path.startswith("/zh/") else "en"] = path
    out = ['<?xml version="1.0" encoding="utf-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for key in sorted(pairs):
        langs = pairs[key]
        links = [("zh-CN" if l == "zh" else "en", p) for l, p in sorted(langs.items())] if len(langs) > 1 else []
        if links and "en" in langs:
            links.append(("x-default", langs["en"]))
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{xml_attr(base + p)}"/>' for code, p in links)
        for lang, path in sorted(langs.items()):
            when = f"<lastmod>{lastmod[path].isoformat()}</lastmod>" if lastmod.get(path) else ""
            out.append(f"<url><loc>{xml_text(base + path)}</loc>{when}{alts}</url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def last_revised(model):
    """The date each article and page last changed, by path: updated, else published."""
    dates = {}
    for lang in content.LANGS:
        prefix = "/zh" if lang == "zh" else ""
        for a in model["articles"][lang]:
            dates[f"{prefix}/articles/{a.slug}/"] = a.updated or a.published
        for page in model["pages"][lang].values():
            if page.updated or page.published:
                dates[f"{prefix}/{page.name}/"] = page.updated or page.published
    return dates


def nav_label(site, section):
    """The header or footer label of a section ("Vision", "愿景"), or "" when it has none."""
    key = f"nav_{section}"
    known = key in site.m["strings"][site.lang] or key in render.FALLBACK_STRINGS[site.lang]
    return site.s(key) if known else ""


def search_index(site, model, lang):
    """The entries site.js searches (title, text and meta) for one language. An entry for a
    page that the header or footer names carries that label in its meta, so typing "Vision"
    finds "What verifiable.pro is for" and typing "TEEs" finds the TEE hub."""
    site.lang = lang
    entries = []
    for a in model["articles"][lang]:
        entries.append({"type": "article", "title": a.title, "text": a.dek, "meta": site.kind_label(a.kind),
                        "path": site.article_url(a)})
    for t in model["topics"]["topics"]:
        # the TEE topic's page is the TEE hub, the header's first item
        meta = nav_label(site, "tee") if t["id"] == content.TEE_TOPIC else ""
        entries.append({"type": "topic", "title": site.t(t["name"]), "text": site.t(t["one_liner"]), "meta": meta,
                        "path": site.loc(f"/topics/{t['id']}/")})
    for r in model["resources"]["resources"]:
        entries.append({"type": "resource", "title": r["title"], "text": site.t(r.get("note", "")),
                        "meta": " · ".join(x for x in [r.get("org", ""), str(r.get("year", ""))] if x), "url": r["url"]})
    # pages: Vision and About first, then the trust tiers, which live on the Stack page
    order = {name: n for n, name in enumerate(("vision", "about"))}
    for name in sorted(model["pages"][lang], key=lambda n: (order.get(n, len(order)), n)):
        page = model["pages"][lang][name]
        entries.append({"type": "page", "title": page.title, "text": page.dek, "meta": nav_label(site, name),
                        "path": site.loc(f"/{name}/")})
    stack = nav_label(site, "stack")
    for tier in model.get("tiers", {}).get("tiers", []):
        entries.append({"type": "page", "title": f"{site.s('tier_n', n=tier['n'])} · {site.t(tier['trust_name'])}",
                        "text": site.t(tier["summary"]), "meta": " · ".join(x for x in (stack, site.t(tier["mechanism"])) if x),
                        "path": site.loc("/topics/") + "#tier-" + tier["id"]})
    for g in model["glossary"]["terms"]:
        entries.append({"type": "term", "title": site.t(g["term"]), "text": site.t(g["definition"]),
                        "meta": g["term"]["zh"] if lang == "en" else g["term"]["en"],
                        "path": site.loc("/glossary/") + "#" + g["id"]})
    return entries


def write(out, path, text):
    target = out / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


SOURCE_DIRS = ("content", "sitegen", "static", "tools", "tests", "brand", "design", "research", "api", "backend",
               "docs", ".git", ".github")


def check_out_dir(out):
    """Refuse an output folder whose replacement would delete sources: the build
    empties --out first, so "--out ." or "--out content" must not get that far."""
    out = Path(out).resolve()
    protected = [ROOT / name for name in SOURCE_DIRS]
    if (out == ROOT or out in ROOT.parents or out == Path.home() or out in protected
            or any(p in out.parents for p in protected)):
        raise content.ContentError(f"refusing to build into {out}: it holds the project or its sources")
    if out.is_dir() and any(out.iterdir()) and not ((out / "index.html").exists() or (out / "manifest.json").exists()):
        raise content.ContentError(f"refusing to build into {out}: it is not empty and does not look like a build")


LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")

# Sentences in content/pages/about.*.md that are true only while the assistant runs
# in demo mode. Rewrite "The assistant" section (and update this list) before
# switching content/site.json to another mode.
DEMO_ONLY_CLAIMS = {
    "en": "nothing you type is sent anywhere",
    "zh": "你输入的内容也不会发送到任何地方",
}


def stale_about(model):
    """The languages whose About page still describes the assistant as demo-only."""
    pages = model.get("pages") or {}
    return [lang for lang, claim in DEMO_ONLY_CLAIMS.items()
            if claim in (getattr(pages.get(lang, {}).get("about"), "body", "") or "")]


def apply_chat(model, mode, chat=None, chat_api=None):
    """Check content/site.json "chat" with the command-line overrides applied.

    A production build made from content/site.json alone (what deploy.yml
    publishes) must not point the assistant at this machine, and must not go
    live while the About page still says nothing typed leaves the page.
    Command-line overrides are for local test builds and only warn.
    """
    try:
        settings = render.chat_settings(model["site"], chat, chat_api)
    except ValueError as exc:
        raise content.ContentError(str(exc)) from exc
    api = settings["api_base"]
    host = urllib.parse.urlsplit(api).hostname or ""
    if mode == "prod" and settings["mode"] == "live" and api.startswith("http://") and host not in LOCAL_HOSTS:
        raise content.ContentError(f"chat.api_base must use https:// in a production build, not {api}")
    if mode == "prod" and settings["mode"] != "demo":
        override = chat is not None or chat_api is not None
        problems = []
        if settings["mode"] == "live" and host in LOCAL_HOSTS:
            problems.append(f"chat.api_base {api} is this machine, so every reader's browser would call its own computer")
        stale = stale_about(model)
        if stale:
            files = " and ".join(f"content/pages/about.{lang}.md" for lang in stale)
            verb = "describe" if len(stale) > 1 else "describes"
            problems.append(f'{files} still {verb} the assistant as demo-only (chat mode is "{settings["mode"]}"); '
                            'rewrite the "The assistant" section and build.DEMO_ONLY_CLAIMS')
        for problem in problems:
            if settings["mode"] == "live" and not override:
                raise content.ContentError(problem)
            print(f"warning: {problem}", file=sys.stderr)
    missing = [f"{lang}: {key}" for lang in content.LANGS for key in model["strings"]["en"]
               if key.startswith("chat_") and key not in model["strings"][lang]]
    if settings["mode"] != "off" and missing:
        raise content.ContentError(f"content/strings.json lacks chat strings ({', '.join(missing[:3])})")
    model["site"]["chat"] = settings
    return settings


def static_ignore(chat_off=False, static=ROOT / "static"):
    """The ignore function for copying static/ to assets/: it leaves out chat.js and
    chat.css when the assistant is off, and always static/media/, whose files the build
    writes itself, only those that a published article's illustration.json names
    (lead_images()), so a draft's picture or a stray file is never published unlisted."""
    def ignore(folder, names):
        top = Path(folder) == Path(static)
        return [n for n in names if (chat_off and n in ("chat.js", "chat.css")) or (top and n == content.MEDIA_DIR.name)]
    return ignore


def hero_svg(root=ROOT):
    """The hero scene template. The templates fill its title and description in the
    page language (HERO_SLOTS), and the sentences that static/hero.js adds to the
    description once it runs."""
    path = root / HERO_TEMPLATE
    if not path.is_file():
        raise content.ContentError(f"{HERO_TEMPLATE.as_posix()} is missing: the home page hero needs it")
    svg = path.read_text(encoding="utf-8")
    missing = [slot for slot in HERO_SLOTS if slot not in svg]
    if missing:
        raise content.ContentError(f"{HERO_TEMPLATE.as_posix()} lacks {' and '.join(missing)}, which carry its title "
                                   "and description in the page language")
    return svg


def hero_scene_check(svg):
    """The parts of the hero scene that the page and static/hero.js address: one
    <g class="hv-hits"> as the scene's last element, holding the seven plates' hit
    areas (path.hv-hit, data-hv-n 1 to 7 in that order, and no hit area elsewhere); a
    g.hv-layer for each of hv-ly1 to hv-ly7, a g.hv-seg for each of hv-seg2 to hv-seg7
    with two stubs (hv-stub) per segment, and a g.hv-ring for each of hv-ring1 to
    hv-ring6, which the figure's data-hv-chain and data-hv-active rules reach; and one
    g.hv-person whose phone carries one hv-ph-ring, with no transform on the group or
    inside it (as an attribute or in a style): tools/hero/person.py bakes the person's
    size and place into its path data, which is where the tests check its bounds (the
    scene's stylesheet may still animate it: its hop ends where it starts); and the
    person's own hit area, one path.hv-you-hit outside g.hv-hits, which static/hero.js
    listens to for a click or a tap on the person."""
    name = HERO_TEMPLATE.as_posix()
    try:
        root = ET.fromstring(svg)
    except ET.ParseError as exc:
        raise content.ContentError(f"{name}: not well-formed XML ({exc})") from exc

    def tag(el):
        return el.tag.rsplit("}", 1)[-1]

    def classes(el):
        return set(el.get("class", "").split())
    groups = [el for el in root.iter() if tag(el) == "g"]

    def having(*names):
        return [g for g in groups if classes(g) >= set(names)]
    hits = having("hv-hits")
    if len(hits) != 1 or list(root)[-1] is not hits[0]:
        raise content.ContentError(f'{name}: needs exactly one <g class="hv-hits">, as the scene\'s last element')
    inside = [el for el in hits[0].iter() if "hv-hit" in classes(el)]
    if ([(tag(el), el.get("data-hv-n")) for el in inside] != [("path", str(n)) for n in range(1, 8)]
            or sum("hv-hit" in classes(el) for el in root.iter()) != len(inside)):
        raise content.ContentError(f'{name}: g.hv-hits must hold the seven plates\' <path class="hv-hit">, '
                                   'data-hv-n "1" to "7" in that order, and no hit area may stand elsewhere')
    for kind, codes in (("hv-layer", [f"hv-ly{n}" for n in range(1, 8)]),
                        ("hv-seg", [f"hv-seg{k}" for k in range(2, 8)]),
                        ("hv-ring", [f"hv-ring{n}" for n in range(1, 7)])):
        for code in codes:
            if not having(kind, code):
                raise content.ContentError(f'{name}: no <g class="{kind} {code}">; the page\'s data-hv-* rules need one')
    for k in range(2, 8):
        stubs = {id(el) for g in having("hv-seg", f"hv-seg{k}") for el in g.iter() if "hv-stub" in classes(el)}
        if len(stubs) != 2:
            raise content.ContentError(f"{name}: segment {k} needs two stubs (hv-stub in g.hv-seg{k}), drawn where "
                                       f"its binding is missing; it has {len(stubs)}")
    people = having("hv-person")
    rings = [el for g in people for el in g.iter() if "hv-ph-ring" in classes(el)]
    if len(people) != 1 or len(rings) != 1:
        raise content.ContentError(f"{name}: needs one g.hv-person whose phone carries one hv-ph-ring "
                                   f"(found {len(people)} and {len(rings)})")
    moved = [el for el in people[0].iter()
             if el.get("transform") is not None or re.search(r"(?:^|;)\s*transform\s*:", el.get("style", ""))]
    if moved:
        where = "g.hv-person" if moved[0] is people[0] else f"g.hv-person's {tag(moved[0])}"
        raise content.ContentError(f"{name}: {where} has a transform; the person's geometry must be baked into its "
                                   "path data by tools/hero/person.py")
    you = [el for el in root.iter() if "hv-you-hit" in classes(el)]
    if len(you) != 1 or tag(you[0]) != "path" or any(el is you[0] for el in hits[0].iter()):
        raise content.ContentError(f'{name}: needs one <path class="hv-you-hit">, the person\'s hit area, outside '
                                   f"g.hv-hits (found {len(you)})")


def hero_anchors(svg, layers, root=ROOT):
    """Where each layer's leader line starts on the hero scene SVG, from HERO_ANCHORS:
    {"viewBox": [x, y, width, height], "anchors": [{"layer": n, "x": .., "y": ..}, ...]}
    with one anchor for each layer code from 1 to LAYERS, inside the scene's viewBox,
    which must match the SVG's. An anchor's optional label_y sets its label higher
    or lower than the anchor."""
    name = HERO_ANCHORS.as_posix()
    try:
        doc = json.loads((root / HERO_ANCHORS).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise content.ContentError(f"{name} is missing: the hero's layer labels need it") from exc
    except ValueError as exc:
        raise content.ContentError(f"{name}: not valid JSON ({exc})") from exc
    box = doc.get("viewBox") if isinstance(doc, dict) else None
    m = VIEWBOX_RE.search(svg)
    if not m or [float(v) for v in re.split(r"[\s,]+", m.group(1).strip())] != box:
        raise content.ContentError(f"{name}: viewBox {box} does not match the scene's "
                                   f"({m.group(1) if m else 'none'}) in {HERO_TEMPLATE.as_posix()}")
    anchors = doc.get("anchors")
    # an anchor without an integer layer (a missing one, "7", or true) counts for no layer
    codes = (sorted(a["layer"] for a in anchors if isinstance(a, dict) and type(a.get("layer")) is int)
             if isinstance(anchors, list) else None)
    if codes != list(range(1, layers + 1)) or len(anchors) != layers:
        raise content.ContentError(f"{name}: needs one anchor for each layer from 1 to {layers}")
    x0, y0, width, height = box
    for a in anchors:
        for key in ("x", "y", "label_y"):
            value = a.get(key, a["y"] if key == "label_y" else None)
            low, high = (x0, x0 + width) if key == "x" else (y0, y0 + height)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not low <= value <= high:
                raise content.ContentError(f"{name}: layer {a['layer']}'s {key} must be a number inside the viewBox")
    return doc


def placeholders(model):
    """Text the owner still has to fill in before the site goes live: the editor line and
    owner decisions in About and Vision."""
    found = []
    for lang in content.LANGS:
        for name in PLACEHOLDER_PAGES:
            page = model["pages"][lang].get(name)
            text = page.raw.decode("utf-8", "replace") if page else ""
            for marker, what in PLACEHOLDERS.items():
                if marker in text:
                    found.append(f"content/pages/{name}.{lang}.md still has a placeholder for {what} ({marker} ...])")
    return found


def build(mode, out, css=None, mark=None, drafts=False, chat=None, chat_api=None):
    model = content.load(ROOT, drafts=drafts)
    chat_mode = apply_chat(model, mode, chat, chat_api)["mode"]
    scene = hero_svg()
    hero_scene_check(scene)
    anchors = hero_anchors(scene, len(model["topics"]["stack"]))
    # the committed social cards and icons (tools/og_images.py draws them); no browser runs here
    cards, card_warnings = discover.check_images(ROOT, model)
    for problem in card_warnings:
        print(f"warning: {problem}", file=sys.stderr)
    # a picture left behind when its spec changed or went: never published, so only a warning
    for name in model.get("unused_media", []):
        print(f"warning: {(content.MEDIA_DIR / name).as_posix()} is named by no illustration.json, so the build "
              "does not publish it; delete it (tools/photos.py --check reports it too)", file=sys.stderr)
    if mode == "prod":
        for problem in placeholders(model):
            print(f"warning: {problem}", file=sys.stderr)
    mark_file = Path(mark) if mark else ROOT / "static" / "mark.svg"
    if mark_file.exists():
        render.set_mark(mark_file.read_text(encoding="utf-8"))
    render_docs(model, mode)
    attach_art(model)
    manifest_doc, digest = manifest(model)
    base = model["site"]["base_url"].rstrip("/")
    try:
        indexnow = discover.indexnow_config(ROOT / "indexnow.json")
    except (ValueError, OSError) as exc:
        raise content.ContentError(f"indexnow.json: {exc}") from exc
    if base != f"https://{indexnow['host']}":
        raise content.ContentError("indexnow.json host must match the canonical HTTPS site base_url")

    check_out_dir(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    site = Site(model, mode)
    site.build_digest = digest
    site.hero_svg = scene  # with {{SCENE_TITLE}}, {{SCENE_DESC}} and {{SCENE_DESC_LIVE}} still to fill
    site.hero_anchors = anchors
    site.cards = cards
    pages = {}
    for lang in content.LANGS:
        site.lang = lang
        arts = model["articles"][lang]
        other = {a.slug for a in model["articles"]["zh" if lang == "en" else "en"]}
        renders = [site.home(arts), site.latest(arts), site.topics_index(arts), site.learn(arts),
                   site.resources(), site.glossary(), site.search(), site.not_found()]
        # the TEE topic's page is the TEE hub, at the same address
        renders += [site.tee_hub(arts) if tid == content.TEE_TOPIC else site.topic_page(tid, arts)
                    for tid in site.topic_order]
        renders += [site.article(a, arts, a.slug in other) for a in arts]
        for name, page in model["pages"][lang].items():
            renders.append(site.static_page(page, name if name in PAGE_SECTIONS else ""))
        for path, text in renders:
            if path in pages:
                raise content.ContentError(f"two pages render to {path}")
            pages[path] = text

    for path, text in pages.items():
        write(out, path, text)

    for lang in content.LANGS:
        for a in model["articles"][lang]:
            target = out / "articles" / a.slug / f"{lang}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(a.raw)
        for page in model["pages"][lang].values():
            target = out / "pages" / f"{page.name}.{lang}.md"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(page.raw)
    (out / "data").mkdir(exist_ok=True)
    for name in content.DATA_FILES:
        (out / "data" / f"{name}.json").write_bytes(data_bytes(model, name))

    # with the assistant off, its script and stylesheet are not published either
    shutil.copytree(ROOT / "static", out / "assets", ignore=static_ignore(chat_off=chat_mode == "off"))
    if css:
        shutil.copyfile(css, out / "assets" / "site.css")
    # each lead image's spec beside the article's sources, and the image as loaded and hashed,
    # so the manifest's digests match the published files even if a file changed during the build
    for image in lead_images(model):
        for path, raw in [(image.spec_path, image.spec_raw)] + [(p.src, p.raw) for p in image.published()]:
            target = out / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    (out / "manifest.json").write_text(json.dumps(manifest_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for lang in content.LANGS:
        prefix = "zh/" if lang == "zh" else ""
        (out / prefix).mkdir(parents=True, exist_ok=True)
        (out / f"{prefix}feed.xml").write_text(atom(site, model, lang, base), encoding="utf-8")
        (out / f"{prefix}search-index.json").write_text(
            json.dumps(search_index(site, model, lang), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        # for agents and devices: the JSON Feed, the full text and the web app manifest
        (out / f"{prefix}feed.json").write_text(discover.json_feed(site, model, lang), encoding="utf-8")
        (out / f"{prefix}llms-full.txt").write_text(discover.llms_full(site, model, lang), encoding="utf-8")
        (out / f"{prefix}site.webmanifest").write_text(discover.webmanifest(site, model, lang), encoding="utf-8")
    (out / "llms.txt").write_text(discover.llms_txt(site, model), encoding="utf-8")
    (out / "sitemap.xml").write_text(sitemap(pages, base, last_revised(model)), encoding="utf-8")
    (out / "robots.txt").write_text(discover.robots_txt(base), encoding="utf-8")
    # Exactly the key, with no newline: search engines compare the file with the key they are sent
    (out / f"{indexnow['key']}.txt").write_text(indexnow["key"], encoding="utf-8")
    if mode == "prod":
        (out / "CNAME").write_text(model["site"]["domain"] + "\n", encoding="utf-8")
    return len(pages), digest


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=("prod", "preview", "artifact"), default="prod")
    parser.add_argument("--out", default=None, help="output directory (default: public, or dist-<mode>)")
    parser.add_argument("--css", default=None, help="use this stylesheet instead of static/site.css")
    parser.add_argument("--mark", default=None, help="use this 48x48 mark SVG instead of static/mark.svg")
    parser.add_argument("--drafts", action="store_true", help="include articles marked draft: true")
    parser.add_argument("--chat", choices=render.CHAT_MODES, default=None,
                        help="Ask assistant mode for this build (default: chat.mode in content/site.json)")
    parser.add_argument("--chat-api", default=None, metavar="URL",
                        help="chat API base URL for --chat live (default: chat.api_base in content/site.json)")
    args = parser.parse_args()
    out = Path(args.out) if args.out else ROOT / ("public" if args.mode == "prod" else f"dist-{args.mode}")
    try:
        count, digest = build(args.mode, out.resolve(), args.css, args.mark, args.drafts, args.chat, args.chat_api)
    except content.ContentError as exc:
        print(f"content error: {exc}", file=sys.stderr)
        return 1
    print(f"built {count} pages into {out} (manifest digest {digest[:16]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
