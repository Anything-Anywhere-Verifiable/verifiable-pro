"""What search engines, AI answer engines and agents read: machine-readable files
and the metadata in each page's head.

build.py writes robots.txt, llms.txt, llms-full.txt and /zh/llms-full.txt, the
JSON Feeds (/feed.json, /zh/feed.json) and the web app manifests
(/site.webmanifest, /zh/site.webmanifest) with the functions here, and
render.Site.layout() takes each page's social tags and structured data (JSON-LD)
from them. Everything is generated from the content model, so drafts stay out.

The social cards (static/og/) and the icons (static/icons/) are PNG files that
tools/og_images.py draws with headless Chrome and that are committed. The build
reads only their headers and static/og/cards.json, which records the text on
each card and its alt text: check_images() stops the build when a file is
missing or has the wrong size, so the build never needs a browser.
"""

import html
import json
import re
import struct
import urllib.parse
from pathlib import Path

from . import content

SCHEMA = "https://schema.org"
HREFLANG = {"en": "en", "zh": "zh-CN"}
OG_LOCALE = {"en": "en_US", "zh": "zh_CN"}
# The social cards: one for the site and one for each topic, in each language
CARD_SIZE = (1200, 630)
CARD_DIR = Path("static") / "og"
CARD_INDEX = CARD_DIR / "cards.json"
# The icons, by file name and size in pixels; the 512px icon is also the logo in the structured data
ICON_DIR = Path("static") / "icons"
ICONS = {"apple-touch-icon.png": 180, "icon-192.png": 192, "icon-512.png": 512}
LOGO = "icon-512.png"
CARD_TOOL = "python3 tools/og_images.py"
# The feeds carry the newest articles, as the Atom feeds do
FEED_ITEMS = 20
# The fill behind the icons and the browser chrome colour: the page's paper
THEME_COLOR = "#ffffff"

# robots.txt. A crawler obeys only the most specific group that names it, so every
# group repeats ROBOTS_RULES: a rule meant for all crawlers goes there. A group may
# carry its own rules as a third item, such as ("Disallow: /",). Each token is the one
# its operator documents (see docs/MAINTAINING.md).
ROBOTS_RULES = ("Allow: /",)
ROBOTS_GROUPS = (
    ("Search engines", ("Googlebot", "Bingbot", "Applebot", "Baiduspider")),
    ("AI search and answer engines, which link the pages they cite",
     ("OAI-SearchBot", "Claude-SearchBot", "PerplexityBot", "DuckAssistBot", "Amzn-SearchBot", "Meta-WebIndexer")),
    ("Assistants that fetch a page when a person asks them to", ("ChatGPT-User", "Claude-User", "Perplexity-User")),
    ("AI model training and open web datasets",
     ("GPTBot", "ClaudeBot", "Google-Extended", "Applebot-Extended", "CCBot", "Amazonbot", "Meta-ExternalAgent")),
)

# llms-full.txt: the boxes a Markdown body opens with :::kind
CALLOUTS = ("facts", "analysis", "checked", "limits", "example", "note")
# A site-absolute Markdown link target: "](/articles/x/)" or "](/manifest.json)"
SITE_LINK_RE = re.compile(r"(\]\()(/(?!/)[^)\s]*)")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
INCLUDE_RE = re.compile(r'^\s*<div\s+data-include="([^"]*)"\s*>\s*</div>\s*$')
HREF_RE = re.compile(r'(\s(?:href|src)=")([^"]*)(")')
SOURCE_DATE_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")


# ----- the site's own words ----------------------------------------------------

def site_name(model):
    return model["site"]["domain"]


def describe(model, lang):
    """The site's description in LANG: "description" in content/site.json (a text or
    {"en": ..., "zh": ...}), else the site_description interface string."""
    value = model["site"].get("description")
    if isinstance(value, dict):
        value = value.get(lang) or value.get("en")
    return value or model["strings"][lang].get("site_description", "")


def link(site, path):
    """A link from the file being written (site.current) to a site path: the full URL in a
    production build, a relative link in preview and artifact builds."""
    return site.base_url + path if site.mode == "prod" else site.href(path)


def one_line(text):
    return " ".join(str(text or "").split())


def count_word(n, lang="en"):
    """A small count as a word in running text: in English up to ten ("seven layers"), else
    digits; in Chinese a numeral before its measure word up to 99 ("五步", "两篇", "十二篇"),
    which sets no space before the measure word as digits would."""
    if lang == "zh":
        digits = "零一二三四五六七八九"
        if n == 2:
            return "两"
        if 0 <= n < 10:
            return digits[n]
        if 10 <= n < 100:
            tens, ones = divmod(n, 10)
            return ("" if tens == 1 else digits[tens]) + "十" + (digits[ones] if ones else "")
        return str(n)
    words = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten")
    return words[n] if 0 <= n < len(words) else str(n)


def md_label(text):
    """Text for the label of a Markdown link."""
    return one_line(text).replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def article_source(a_obj):
    return f"/articles/{a_obj.slug}/{a_obj.lang}.md"


def page_source(page):
    return f"/pages/{page.name}.{page.lang}.md"


# ----- social cards and icons ---------------------------------------------------

def card_file(topic, lang):
    """The file name of a social card: "site-en.png" or "<topic id>-zh.png"."""
    return f"{topic or 'site'}-{lang}.png"


def card_text(model, topic, lang):
    """The words on a card: the kicker and the title, from the content model.
    tools/og_images.py draws them; check_images() compares them with cards.json."""
    strings = model["strings"][lang]
    if topic is None:
        return {"kicker": strings.get("home_kicker", ""), "title": strings.get("tagline", "")}
    found = next(t for t in model["topics"]["topics"] if t["id"] == topic)
    name = found["name"]
    return {"kicker": strings.get("topic_kicker", ""), "title": name.get(lang) or name.get("en", "")}


def png_size(path):
    """(width, height) from a PNG file's header, or None when the file is not a PNG."""
    with open(path, "rb") as fh:
        head = fh.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def check_images(root, model):
    """The social cards and icons that the pages link, checked without a browser.

    Returns ({card file name: {"alt": ...}}, warnings). Stops the build with a
    ContentError when static/og/cards.json, a card or an icon is missing, or a PNG
    has the wrong size. A card whose words differ from what the content now says
    only warns, since the page text is still right: redraw the cards."""
    root = Path(root)
    redraw = f"run {CARD_TOOL} to draw them (it needs Google Chrome)"
    try:
        index = json.loads((root / CARD_INDEX).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise content.ContentError(f"{CARD_INDEX.as_posix()} is missing: the social cards and their alt text "
                                   f"need it; {redraw}") from exc
    except ValueError as exc:
        raise content.ContentError(f"{CARD_INDEX.as_posix()}: not valid JSON ({exc}); {redraw}") from exc
    listed = index.get("cards") if isinstance(index, dict) else None
    if not isinstance(listed, dict):
        raise content.ContentError(f'{CARD_INDEX.as_posix()} has no "cards" object; {redraw}')
    cards, warnings = {}, []
    for lang in content.LANGS:
        for topic in [None] + [t["id"] for t in model["topics"]["topics"]]:
            name = card_file(topic, lang)
            rel = (CARD_DIR / name).as_posix()
            what = "the site's" if topic is None else f"the {topic} topic's"
            info = listed.get(name)
            path = root / CARD_DIR / name
            if not path.is_file() or not isinstance(info, dict) or not info.get("alt"):
                missing = rel if not path.is_file() else f"the entry for {name} in {CARD_INDEX.as_posix()}"
                raise content.ContentError(f"{missing} is missing: {what} social card in {lang}; {redraw}")
            size = png_size(path)
            if size != CARD_SIZE:
                shown = f"{size[0]}x{size[1]}" if size else "not a PNG"
                raise content.ContentError(f"{rel} is {shown}, not {CARD_SIZE[0]}x{CARD_SIZE[1]}; {redraw}")
            words = card_text(model, topic, lang)
            if any(info.get(key) != value for key, value in words.items()):
                warnings.append(f"{rel} shows {info.get('title')!r} under {info.get('kicker')!r}, but the content now "
                                f"says {words['title']!r} under {words['kicker']!r}; {redraw}")
            cards[name] = {"alt": one_line(info["alt"])}
    for name, px in ICONS.items():
        rel = (ICON_DIR / name).as_posix()
        path = root / ICON_DIR / name
        if not path.is_file():
            raise content.ContentError(f"{rel} is missing: the {px}px icon; {redraw}")
        size = png_size(path)
        if size != (px, px):
            shown = f"{size[0]}x{size[1]}" if size else "not a PNG"
            raise content.ContentError(f"{rel} is {shown}, not {px}x{px}; {redraw}")
    return cards, warnings


def card(site, topic=None):
    """The social card of TOPIC (or the site's) in the page's language, as {"url",
    "width", "height", "alt"}, or None while the build has loaded no cards."""
    cards = getattr(site, "cards", None) or {}
    name = card_file(topic if topic in site.topics else None, site.lang)
    info = cards.get(name)
    if not info:
        return None
    return {"url": f"{site.base_url}/assets/og/{name}", "width": CARD_SIZE[0], "height": CARD_SIZE[1],
            "alt": info["alt"]}


def photo_card(site, a_obj):
    """An article's own picture for link previews and the structured data: its photo's
    social copy (variants.social in its illustration.json, at the cards' size), as card()
    gives a social card, with the photo's alt text and, for the structured data, its credit
    and license address. None for an article without a photo, which keeps its primary
    topic's card."""
    image = getattr(a_obj, "lead_image", None)
    social = getattr(image, "variants", {}).get("social") if image is not None else None
    if social is None:
        return None
    return {"url": site.base_url + social.src, "width": social.width, "height": social.height,
            "alt": one_line(site.t(image.alt)), "credit": one_line(site.t(image.credit)), "license": image.license_url}


def icon_url(site, name):
    return f"{site.base_url}/assets/icons/{name}"


# ----- the head --------------------------------------------------------------

def head_links(site, source=None):
    """<link> elements for agents and devices: the JSON Feed, the page's Markdown
    source, the site's llms.txt, the touch icon and the web app manifest."""
    loc = site.loc
    out = [f'<link rel="alternate" type="application/feed+json" title="{html.escape(site_name(site.m))}" '
           f'href="{html.escape(site.href(loc("/feed.json")))}">']
    if source:
        # no hreflang: search engines read rel="alternate" with hreflang as a page in another language
        out.append(f'<link rel="alternate" type="text/markdown" href="{html.escape(site.href(source))}">')
    out.append(f'<link rel="describedby" href="{html.escape(site.href("/llms.txt"))}">')
    out.append(f'<link rel="apple-touch-icon" href="{html.escape(site.href("/assets/icons/apple-touch-icon.png"))}">')
    out.append(f'<link rel="manifest" href="{html.escape(site.href(loc("/site.webmanifest")))}">')
    return "\n".join(out)


def social_meta(site, *, image_topic=None, alternate=True, article=None):
    """Open Graph and card tags beyond the title and description: the locales, the
    social card and, on articles, the dates, section and tags. IMAGE_TOPIC is the topic
    whose card the page shows, or an article's own picture as photo_card() gives it.
    ARTICLE is a dict with "published", "modified" (dates), "section" and "tags"."""
    def meta(prop, value, attr="property"):
        return f'<meta {attr}="{prop}" content="{html.escape(str(value))}">'
    out = [meta("og:locale", OG_LOCALE[site.lang])]
    if alternate:
        out.append(meta("og:locale:alternate", OG_LOCALE[site.other()]))
    image = image_topic if isinstance(image_topic, dict) else card(site, image_topic)
    if image:
        out += [meta("og:image", image["url"]), meta("og:image:width", image["width"]),
                meta("og:image:height", image["height"]), meta("og:image:alt", image["alt"])]
    if article:
        out += [meta("article:published_time", article["published"].isoformat()),
                meta("article:modified_time", article["modified"].isoformat()),
                meta("article:section", article["section"])]
        out += [meta("article:tag", tag) for tag in article["tags"]]
    out.append(meta("twitter:card", "summary_large_image" if image else "summary", "name"))
    if image:
        out += [meta("twitter:image", image["url"], "name"), meta("twitter:image:alt", image["alt"], "name")]
    return "\n".join(out)


# ----- structured data (JSON-LD) -------------------------------------------------

def org_id(site):
    return site.base_url + "/#organization"


def website_id(site):
    return site.base_url + "/#website"


def logo(site):
    px = ICONS[LOGO]
    return {"@type": "ImageObject", "url": icon_url(site, LOGO), "width": px, "height": px}


def organization(site):
    """The publisher, with its logo, repository and editorial address (content/site.json)."""
    settings = site.m["site"]
    node = {"@context": SCHEMA, "@type": "Organization", "@id": org_id(site), "name": site_name(site.m)}
    if settings.get("alternate_name"):  # Google asks for the same names as the WebSite's
        node["alternateName"] = settings["alternate_name"]
    node.update({"url": site.base_url + "/", "logo": logo(site), "description": site.s("footer_about"),
                 "publishingPrinciples": site.base_url + site.loc("/about/")})
    if site.repo():
        node["sameAs"] = [site.repo()]
    if settings.get("contact_email"):
        node["email"] = settings["contact_email"]
    return node


def publisher(site):
    """The organization as an article's publisher, inline so that it carries its logo."""
    return {"@type": "Organization", "@id": org_id(site), "name": site_name(site.m), "url": site.base_url + "/",
            "logo": logo(site)}


def website(site):
    node = {"@context": SCHEMA, "@type": "WebSite", "@id": website_id(site), "name": site_name(site.m)}
    alternate = site.m["site"].get("alternate_name")
    if alternate:
        node["alternateName"] = alternate
    node.update({"url": site.base_url + "/", "inLanguage": [HREFLANG[lang] for lang in content.LANGS],
                 "description": site.s("site_description"), "publisher": {"@id": org_id(site)}})
    return node


def breadcrumbs(site, crumbs, title):
    """The trail a page shows above its title, ending with the page itself. Google asks
    for at least two items, so the home pages, which have no trail, carry none."""
    items = [{"@type": "ListItem", "position": n, "name": name, "item": site.base_url + path}
             for n, (path, name) in enumerate(crumbs, 1)]
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": title})
    return {"@context": SCHEMA, "@type": "BreadcrumbList", "itemListElement": items}


def author(site, a_obj):
    """The article's author in the structured data: a Person for an article a person wrote
    (author), and the publication itself, as an Organization, for an automated article, which
    the site's drafting software wrote under one of its automated bylines (agent). Search
    engines take only a Person or an Organization as an author, so the automated byline, such
    as "verifiable.pro Wire", is named in the visible byline and in the feeds, never as a
    person."""
    name = one_line(getattr(a_obj, "author", ""))
    if name and not getattr(a_obj, "agent", ""):
        return {"@type": "Person", "name": name}
    return {"@type": "Organization", "@id": org_id(site), "name": site_name(site.m), "url": site.base_url + "/"}


def submitter(a_obj):
    """The person who submitted the story (submitted_by), as the article's contributor, or None."""
    name = one_line(getattr(a_obj, "submitted_by", ""))
    return {"@type": "Person", "name": name} if name else None


def byline(site, a_obj, lang):
    """The byline of a feed entry or an llms-full.txt header in LANG, as {"name", "url"}: an
    automated byline's name marked as automated ("verifiable.pro Wire (automated)"), with the
    address of About's section on how the site uses AI tools; a person's name, with no
    address; or, for an article that names neither, which content.load() refuses, the
    publication."""
    agent = site.m["site"].get("agents", {}).get(getattr(a_obj, "agent", "") or "")
    if agent:
        name = agent["name"]
        name = (name.get(lang) or name.get("en", "")) if isinstance(name, dict) else name
        return {"name": site.m["strings"][lang]["byline_agent_named"].format(name=one_line(name)),
                "url": site.base_url + site.loc("/about/", lang) + "#ai"}
    name = one_line(getattr(a_obj, "author", ""))
    return {"name": name} if name else {"name": site_name(site.m), "url": site.base_url + "/"}


def citation(source):
    """A numbered source as a CreativeWork, with its publication date when it gives one.
    Source labels may combine authors and venues ("Brundage et al., arXiv"). Keep
    those labels in the visible sources instead of inventing a publisher entity:
    Schema.org's publisher property requires a Person or Organization."""
    work = {"@type": "CreativeWork", "name": source["title"], "url": source["url"]}
    if SOURCE_DATE_RE.match(source.get("date", "")):
        work["datePublished"] = source["date"]
    return work


def article_ld(site, a_obj, has_other):
    """NewsArticle or Article: the headline, dek, card, dates, language, author (and the
    person who submitted the story as contributor), publisher, topics as keywords, the kind
    as its section, the numbered sources as citations, and the other edition as its
    translation or original."""
    url = site.base_url + site.article_url(a_obj)
    node = {"@context": SCHEMA, "@type": "NewsArticle" if a_obj.kind == "news" else "Article", "@id": url + "#article",
            "headline": a_obj.title, "description": a_obj.dek}
    # a photo's social copy, with the photo's credit and license, else the primary topic's card
    image = photo_card(site, a_obj) or card(site, a_obj.primary_topic)
    if image:
        node["image"] = {"@type": "ImageObject", "url": image["url"], "width": image["width"], "height": image["height"]}
        if image.get("credit"):
            node["image"].update({"creditText": image["credit"], "license": image["license"]})
    node.update({
        "datePublished": a_obj.published.isoformat(),
        "dateModified": (a_obj.updated or a_obj.published).isoformat(),
        "inLanguage": HREFLANG[a_obj.lang], "isAccessibleForFree": True,
        "author": author(site, a_obj), "publisher": publisher(site),
        "mainEntityOfPage": url, "isPartOf": {"@id": website_id(site)},
        "articleSection": site.kind_label(a_obj.kind, "kind_plural"),
        "keywords": [site.topic_name(t) for t in a_obj.topics],
    })
    if submitter(a_obj):
        node["contributor"] = submitter(a_obj)
    if a_obj.sources:
        node["citation"] = [citation(s) for s in a_obj.sources]
    if has_other:
        other = site.base_url + site.article_url(a_obj, site.other()) + "#article"
        node["translationOfWork" if a_obj.lang == "zh" else "workTranslation"] = {"@id": other}
    return node


def collection(site, path, title, description, items):
    """A page that lists other pages or documents, with its ItemList: ITEMS are
    (url, name) pairs in the page's order."""
    url = site.base_url + path
    return {"@context": SCHEMA, "@type": "CollectionPage", "@id": url, "url": url, "name": title,
            "description": description, "inLanguage": HREFLANG[site.lang], "isPartOf": {"@id": website_id(site)},
            "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": [
                {"@type": "ListItem", "position": n, "url": item_url, "name": name}
                for n, (item_url, name) in enumerate(items, 1)]}}


def article_items(site, articles):
    return [(site.base_url + site.article_url(a_obj), a_obj.title) for a_obj in articles]


def glossary_ld(site, path, title, description, terms):
    """The glossary as a DefinedTermSet: each term in the page's language, with the
    other language's term as its alternate name."""
    url = site.base_url + path
    other = site.other()
    return {"@context": SCHEMA, "@type": "DefinedTermSet", "@id": url + "#terms", "url": url, "name": title,
            "description": description, "inLanguage": HREFLANG[site.lang], "hasDefinedTerm": [
                {"@type": "DefinedTerm", "name": site.t(g["term"]), "alternateName": g["term"][other],
                 "description": site.t(g["definition"]), "url": f"{url}#{g['id']}"} for g in terms]}


def about_ld(site, page):
    """The About page, which says who publishes the site, with the publisher itself."""
    url = site.base_url + site.loc(f"/{page.name}/")
    node = {"@context": SCHEMA, "@type": "AboutPage", "@id": url, "url": url, "name": page.title,
            "description": page.dek, "inLanguage": HREFLANG[site.lang], "isPartOf": {"@id": website_id(site)},
            "about": {"@id": org_id(site)}}
    if page.published:
        node["datePublished"] = page.published.isoformat()
    if page.updated:
        node["dateModified"] = page.updated.isoformat()
    return [node, organization(site)]


# ----- robots.txt --------------------------------------------------------------

def robots_txt(base):
    lines = [
        "# verifiable.pro reports on verifiable AI systems, in English and Simplified Chinese.",
        "# Every page is open to search engines, AI answer engines and agents.",
        f"# Language models and agents: start with {base}/llms.txt. The full text is in",
        f"# {base}/llms-full.txt (English) and {base}/zh/llms-full.txt (Chinese).",
        "",
        "User-agent: *",
        *ROBOTS_RULES,
        "",
    ]
    for title, agents, *rules in ROBOTS_GROUPS:
        lines.append(f"# {title}")
        lines += [f"User-agent: {agent}" for agent in agents]
        lines += [*(rules[0] if rules else ROBOTS_RULES), ""]
    lines.append(f"Sitemap: {base}/sitemap.xml")
    return "\n".join(lines) + "\n"


# ----- llms.txt ------------------------------------------------------------------

def _entry(label, url, note=""):
    note = one_line(note)
    return f"- [{md_label(label)}]({url})" + (f": {note}" if note else "")


def _pages(model, lang):
    """The pages of LANG, Vision and About first."""
    order = {"vision": 0, "about": 1}
    pages = model["pages"][lang]
    return [pages[name] for name in sorted(pages, key=lambda n: (order.get(n, len(order)), n))]


def llms_txt(site, model):
    """The site's guide for language models, in the llmstxt.org format: a title, a
    summary, how the site works and how to check a page, then lists of links. Links
    point to Markdown sources where a page has one."""
    site.lang, site.current = "en", "/llms.txt"
    s, zh = model["strings"]["en"], model["strings"]["zh"]
    stack = model["topics"].get("stack", [])
    tiers = model.get("tiers", {}).get("tiers", [])
    articles = model["articles"]["en"]
    resources = model["resources"]
    terms = model["glossary"]["terms"]

    def kind(a_obj):
        return s.get(f"kind_{a_obj.kind}", a_obj.kind)

    # the automated bylines (content/site.json "agents"), by their English names, such as "verifiable.pro Wire"
    automated = [one_line(site.t(entry["name"])) for entry in model["site"].get("agents", {}).values()]
    bylines = "Each article's byline gives the name of the person who wrote it."
    if automated:
        names = (", ".join(automated[:-1]) + " or " if len(automated) > 1 else "") + automated[-1]
        which = "one of the site's automated bylines" if len(automated) > 1 else "the site's automated byline"
        bylines = (f"Each article's byline gives the name of the person who wrote it or, for an article that software "
                   f"drafted with AI models, {which} ({names}), marked as automated.")

    parts = [
        f"# {site_name(model)}",
        "",
        "> " + one_line(describe(model, "en")),
        "",
        # the summary above names the kinds of article; this adds the site's other sections
        one_line(f"""Besides the articles, the site keeps a hub on trusted execution environments (TEEs) and a map of
        the verification stack: {count_word(len(stack))} layers from
        {site.t(stack[-1]['name']) if stack else 'hardware'} (T1) to
        {site.t(stack[0]['name']) if stack else 'policy'} (T{len(stack)}), with {count_word(len(tiers))} trust tiers.
        Every piece says what a check establishes and what it still leaves to trust, and the site never calls a
        service verified."""),
        "",
        one_line(f"""Each factual claim in an article traces to a numbered source listed with it; in the Markdown,
        [^n] cites source n. Every news brief ends with a "What we checked" box that names the primary sources
        opened, the day they were opened and what could not be confirmed, and the site's interpretation sits apart
        in a "Why it matters" box. A vendor's security claim is reported as the vendor's claim. Corrections are
        listed with their dates at the end of the article they correct. {bylines} AI tools also translate, and an
        editor decides what is published and checks each claim against its source before publication."""),
        "",
        one_line("""Every article and page has a Markdown source beside it: `/articles/<slug>/en.md` and `zh.md` for
        the article at `/articles/<slug>/` and `/zh/articles/<slug>/`, and `/pages/<name>.en.md` or `.zh.md` for the
        page at `/<name>/` and `/zh/<name>/`. The site manifest lists the SHA-256 digest of every source and data
        file; its `digest` field is the SHA-256 of the manifest without its `digest` and `digest_note` fields,
        serialized with sorted keys, no whitespace and UTF-8. To check a page, download its source, compute its
        SHA-256 and compare it with the source's entry in the manifest; `tools/verify_manifest.py` in the source
        repository checks every entry. A match shows that the text is what the site recorded when it was built, not
        that the reporting is correct. To cite a page, give its title, its address (not the address of its Markdown
        source), verifiable.pro and its filing or update date."""),
        "",
    ]
    if any(getattr(a, "lead_image", None) for a in articles):
        # only once some article has a lead image, so the guide never describes files the site lacks
        parts += [one_line("""An article with a lead image also has `/articles/<slug>/illustration.json` beside
        its sources, with the picture's alt text and caption in both languages. For a photo, the file gives its
        credit, license and source, and how `tools/photos.py` in the source repository cropped it and adjusted its
        colors; the caption says what the photo shows, and says so when it does not show the story's own subject.
        For an illustration, the file holds the scene description that `tools/illustrate.py` draws the picture from;
        the illustrations are conceptual and depict no real event, person or product. The manifest lists that file
        and the pictures under `/assets/media/` with their digests."""), ""]

    def section(title, entries):
        parts.extend([f"## {title}", "", *entries, ""])

    start = [_entry(p.title, link(site, page_source(p)), p.dek) for p in _pages(model, "en")]
    path = [step["article"] for step in model.get("tee", {}).get("path", []) if "article" in step]
    by_slug = {a.slug: a for a in articles}
    on_path = [by_slug[slug] for slug in path if slug in by_slug]
    for n, a_obj in enumerate(on_path, 1):
        start.append(_entry(a_obj.title, link(site, article_source(a_obj)),
                            f"Step {n} of the TEE path ({kind(a_obj).lower()}). {a_obj.dek}"))
    for a_obj in articles:
        if a_obj.kind in ("explainer", "guide") and a_obj not in on_path:
            start.append(_entry(a_obj.title, link(site, article_source(a_obj)), f"{kind(a_obj)}. {a_obj.dek}"))
    section("Start here", start)

    topics = [_entry(s.get("topics_page_title", "Stack"), link(site, "/topics/"), s.get("topics_page_dek", ""))]
    for t in model["topics"]["topics"]:
        name = site.t(t["name"])
        if t["id"] == content.TEE_TOPIC:
            topics.append(_entry(f"{name}: {s.get('hub_title', '')}", link(site, f"/topics/{t['id']}/"),
                                 s.get("hub_dek", "")))
        else:
            topics.append(_entry(name, link(site, f"/topics/{t['id']}/"), site.t(t["one_liner"])))
    section("Topics", topics)

    section("Articles", [_entry(a_obj.title, link(site, article_source(a_obj)),
                                f"{kind(a_obj)}, filed {a_obj.published.isoformat()}. {a_obj.dek}")
                         for a_obj in articles])

    n_feed = min(FEED_ITEMS, len(articles))
    section("Data and verification", [
        _entry("Site manifest", link(site, "/manifest.json"),
               "the SHA-256 digest of every article, page and data source, and a digest over the whole list"),
        _entry("How to check a page against the manifest", link(site, "/about/") + "#integrity",
               "the About page's section on source digests"),
        _entry("Atom feed", link(site, "/feed.xml"), f"the {n_feed} newest English articles with their full text"),
        _entry("JSON Feed", link(site, "/feed.json"), "the same articles in JSON Feed 1.1, each with its sources"),
        _entry("Search index", link(site, "/search-index.json"),
               "titles, summaries and addresses of the English articles, topics, pages, trust tiers, resources and "
               "glossary terms"),
        _entry("Glossary data", link(site, "/data/glossary.json"),
               f"{len(terms)} terms with their English and Chinese names and definitions"),
        _entry("Resource library data", link(site, "/data/resources.json"),
               f"{len(resources['resources'])} papers, standards, tools and other documents with their links, topics "
               f"and the date each link was last checked, and {count_word(len(resources.get('paths', [])))} reading "
               "paths"),
        _entry("Topics and verification stack data", link(site, "/data/topics.json"),
               "the topics, and for each stack layer its claim, who checks it, what a TEE contributes and how its "
               "evidence binds to the layer below"),
        _entry("TEE hub data", link(site, "/data/tee.json"),
               "TEE platforms, AI services that publish attestation evidence, and attacks and limits, with dates and "
               "sources"),
        _entry("Trust tiers data", link(site, "/data/tiers.json"),
               "what a passing check rests on in each tier, and the combinations deployed today"),
        _entry("Full text in English", link(site, "/llms-full.txt"),
               "every English article and page as Markdown in one file, each with its metadata and sources"),
        _entry("Sitemap", link(site, "/sitemap.xml"), "every page with its language versions and last change"),
    ])

    site.lang = "zh"
    chinese = [_entry(f"{site_name(model)} 中文版", link(site, "/zh/"), zh.get("site_description", ""))]
    chinese += [_entry(p.title, link(site, page_source(p)), p.dek) for p in _pages(model, "zh")]
    chinese += [
        _entry(zh.get("latest_title", ""), link(site, "/zh/latest/"), zh.get("latest_dek", "")),
        _entry(zh.get("topics_page_title", ""), link(site, "/zh/topics/"), zh.get("topics_page_dek", "")),
        _entry(zh.get("hub_title", ""), link(site, f"/zh/topics/{content.TEE_TOPIC}/"), zh.get("hub_dek", "")),
        _entry(zh.get("learn_title", ""), link(site, "/zh/learn/"), zh.get("learn_dek", "")),
        _entry(zh.get("resources_page_title", ""), link(site, "/zh/resources/"), zh.get("resources_dek", "")),
        _entry(zh.get("glossary_title", ""), link(site, "/zh/glossary/"), zh.get("glossary_dek", "")),
        _entry(zh.get("footer_feed_zh", "Atom"), link(site, "/zh/feed.xml"),
               f"最新 {min(FEED_ITEMS, len(model['articles']['zh']))} 篇中文文章的全文"),
        _entry("JSON Feed（中文）", link(site, "/zh/feed.json"), "同样的文章，JSON Feed 1.1 格式，附各篇来源"),
        _entry("中文搜索索引", link(site, "/zh/search-index.json"), "中文文章、主题、页面、信任分档、资源与术语的标题、摘要和地址"),
        _entry("中文全文", link(site, "/zh/llms-full.txt"), "全部中文文章与页面的 Markdown 全文，每篇附元数据和来源"),
    ]
    site.lang = "en"
    section("中文", chinese)

    optional = [
        _entry(s.get("latest_title", ""), link(site, "/latest/"), s.get("latest_dek", "")),
        _entry(s.get("learn_title", ""), link(site, "/learn/"), s.get("learn_dek", "")),
        _entry(s.get("resources_page_title", ""), link(site, "/resources/"), s.get("resources_dek", "")),
        _entry(s.get("glossary_title", ""), link(site, "/glossary/"), s.get("glossary_dek", "")),
    ]
    if site.repo():
        optional.append(_entry("Source repository", site.repo(),
                               "the site's Markdown content, data files, generator and tests"))
    if site.mode == "prod":  # deploy.yml adds these to the production build only
        optional += [
            _entry("Build record", link(site, "/build.json"),
                   "written by each deploy: the manifest digest and the commit that built the site"),
            _entry("Checksums of every published file", link(site, "/SHA256SUMS"),
                   "written by each deploy, with a Sigstore build provenance bundle at /SHA256SUMS.sigstore.json"),
        ]
    section("Optional", optional)
    return "\n".join(parts).rstrip("\n") + "\n"


# ----- llms-full.txt ---------------------------------------------------------------

def _site_links(site, body, lang):
    """A Markdown body with its site-absolute links as full URLs (relative links in
    preview builds), resolved as build.resolver does: in Chinese, a page path points to
    the Chinese page. Code blocks are left alone."""
    def resolve(m):
        target = m.group(2)
        path = target.split("#", 1)[0]
        if lang == "zh" and (path.endswith("/") or path == "") and not target.startswith("/zh/"):
            target = "/zh" + target
        return m.group(1) + link(site, target)
    out, fence = [], None
    for line in body.split("\n"):
        opened = FENCE_RE.match(line.strip())
        if fence:
            if opened and line.strip().startswith(fence) and not line.strip().strip(fence[0]):
                fence = None
        elif opened:
            fence = opened.group(1)
        else:
            line = SITE_LINK_RE.sub(resolve, line)
        out.append(line)
    return "\n".join(out)


def _includes(site, body):
    """A page body with its include lines written out as Markdown, as the page shows them."""
    def table_cell(text):
        return one_line(text).replace("|", "\\|")

    def fill(name):
        if name == "positioning":
            return site.s("home_positioning")
        if name == "tiers-summary":
            rows = [site.t(site.m["tiers"]["order_note"]), "",
                    f"| {site.s('tier_col')} | {site.s('tier_trust')} | {site.s('tier_vs_tee')} |", "| --- | --- | --- |"]
            for tier in site.tiers():
                label = site.s("tier_n", n=tier["n"]) + " · " + site.t(tier["mechanism"])
                rows.append(f"| [{md_label(label)}]({link(site, site.loc('/topics/') + '#tier-' + tier['id'])}) | "
                            f"{table_cell(site.t(tier['trust_name']))} | {table_cell(site.t(tier['summary']))} |")
            return "\n".join(rows)
        return ""
    return "\n".join((fill(m.group(1)) if m else line) for line in body.split("\n") for m in [INCLUDE_RE.match(line)])


def _metadata(rows):
    return [f"- {key}: {value}" for key, value in rows if value]


def llms_full(site, model, lang):
    """Every published article (newest first) and page of LANG as Markdown in one
    file, each under a header with its title, address, kind, byline, dates, topics and
    sources."""
    prefix = "/zh" if lang == "zh" else ""
    site.lang, site.current = lang, f"{prefix}/llms-full.txt"
    other = "zh" if lang == "en" else "en"
    other_slugs = {a.slug for a in model["articles"][other]}
    name = site_name(model)
    marks = ("、" if lang == "zh" else ", ").join(f":::{kind}" for kind in CALLOUTS)
    about_ai = link(site, site.loc("/about/")) + "#ai"
    # what follows an automated byline's name in the headers: "(automated)", "（自动采编）"
    auto_mark = model["strings"][lang]["byline_agent_named"].replace("{name}", "").strip()
    if lang == "zh":
        intro = (f"本文件按 Markdown 收录 {name} 已发布的全部中文文章（从新到旧）和页面。每一篇以一级标题和一份元数据列表开头，"
                 f"随后是其源文件去掉前置元数据后的正文，站内链接已写成完整地址。正文中的 [^n] 引用该篇来源列表中的第 n 条；"
                 f"{marks} 开启带标签的说明框，以 ::: 结束。元数据中的 Byline 写明撰写文章的人；由程序起草的文章写明其自动署名，"
                 f"名称后注明“{auto_mark}”，各自动署名的介绍见[本站如何使用 AI 工具]({about_ai})。"
                 f"各源文件的 SHA-256 摘要列在[站点清单]({link(site, '/manifest.json')})"
                 f"中。另见[索引]({link(site, '/llms.txt')})和[英文全文]({link(site, '/llms-full.txt')})。")
        title = f"# {name}：中文全文"
    else:
        intro = (f"This file holds every published English article (newest first) and page of {name} as Markdown. Each "
                 f"entry starts with a level-1 heading and a list of its metadata, followed by the body of its source "
                 f"file without the front matter, with site links written as full addresses. In a body, [^n] cites "
                 f"source n of the entry's list, and {marks} open labeled boxes that close at :::. An article's Byline "
                 f"names the person who wrote it or, for an article that software drafted, its automated byline, with "
                 f"\"{auto_mark}\" after the name; [how the site uses AI tools]({about_ai}) describes each automated "
                 f"byline. The SHA-256 digest "
                 f"of each source file is listed in the [site manifest]({link(site, '/manifest.json')}). See also the "
                 f"[index]({link(site, '/llms.txt')}) and the [Chinese full text]({link(site, '/zh/llms-full.txt')}).")
        title = f"# {name}: full text in English"
    out = [title, "", "> " + one_line(describe(model, lang)), "", intro, ""]
    for a_obj in model["articles"][lang]:
        rows = [("URL", site.base_url + site.article_url(a_obj)),
                ("Markdown source", link(site, article_source(a_obj))),
                ("SHA-256", a_obj.sha256),
                ("Kind", a_obj.kind),
                ("Byline", byline(site, a_obj, lang)["name"]),
                ("Submitted by", one_line(getattr(a_obj, "submitted_by", ""))),
                ("Source date", a_obj.event_date.isoformat() if a_obj.kind == "news" and a_obj.event_date else ""),
                ("Published", a_obj.published.isoformat()),
                ("Updated", a_obj.updated.isoformat() if site.revised(a_obj) else ""),
                ("Topics", ", ".join(site.topic_name(t) for t in a_obj.topics))]
        if a_obj.slug in other_slugs:
            rows.append(("English original" if lang == "zh" else "Chinese edition",
                         site.base_url + site.article_url(a_obj, other)))
        sources = [f"  {s['n']}. {one_line(s['title'])}. {one_line(s['publisher'])}, {s['date']}. {s['url']}"
                   for s in a_obj.sources]
        out += ["---", "", f"# {one_line(a_obj.title)}", "", *_metadata(rows)]
        if sources:
            out += ["- Sources:", *sources]
        out += ["", _site_links(site, a_obj.body, lang).strip(), ""]
    for page in _pages(model, lang):
        rows = [("URL", site.base_url + site.loc(f"/{page.name}/")),
                ("Markdown source", link(site, page_source(page))),
                ("SHA-256", page.sha256),
                ("Kind", "page"),
                ("Published", page.published.isoformat() if page.published else ""),
                ("Updated", page.updated.isoformat() if site.revised(page) else "")]
        body = _site_links(site, _includes(site, page.body), lang).strip()
        out += ["---", "", f"# {one_line(page.title)}", "", *_metadata(rows), "", body, ""]
    return "\n".join(out).rstrip("\n") + "\n"


# ----- feeds and the web app manifest ---------------------------------------------

def _absolute_html(text, page_url, base):
    """HTML whose links and images point to full addresses, resolved against the page:
    a feed item has no base address. Site pages end in "/" rather than "index.html"."""
    def fix(m):
        value = html.unescape(m.group(2))
        if not value.startswith(("http://", "https://", "mailto:")):
            value = urllib.parse.urljoin(page_url, value)
            if value.startswith(base + "/"):
                value = re.sub(r"/index\.html(?=$|#)", "/", value)
        return m.group(1) + html.escape(value, quote=True) + m.group(3)
    return HREF_RE.sub(fix, text)


def json_feed(site, model, lang):
    """The newest articles of LANG in JSON Feed 1.1, with their full text and sources.
    Items keep the ids of the Atom feed's entries; the time of day is 00:00 UTC
    because the content records dates only."""
    from . import render  # render imports this module
    prefix = "/zh" if lang == "zh" else ""
    site.lang = lang
    base, name = site.base_url, site_name(model)
    items = []
    for a_obj in model["articles"][lang][:FEED_ITEMS]:
        url = base + site.article_url(a_obj)
        sources = ""
        if a_obj.sources:
            rows = "".join(
                f'<li id="source-{s["n"]}"><a href="{html.escape(s["url"], quote=True)}">{html.escape(s["title"])}</a>'
                f' · {html.escape(s["publisher"])} · {html.escape(render.source_date(s["date"], lang))}</li>'
                for s in a_obj.sources)
            sources = f'<h2>{html.escape(site.s("sources_title"))}</h2><ol>{rows}</ol>'
        items.append({
            "id": f"tag:{name},{a_obj.published.isoformat()}:{prefix}/articles/{a_obj.slug}/",
            "url": url,
            "title": a_obj.title,
            "summary": a_obj.dek,
            "content_html": _absolute_html(a_obj.html, url, base) + sources,
            "date_published": f"{a_obj.published.isoformat()}T00:00:00Z",
            "date_modified": f"{(a_obj.updated or a_obj.published).isoformat()}T00:00:00Z",
            # the byline: a person, or an automated byline marked as automated (JSON Feed has no field for a submitter)
            "authors": [byline(site, a_obj, lang)],
            "tags": [site.topic_name(t) for t in a_obj.topics],
            "language": HREFLANG[lang],
        })
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": name,
        "home_page_url": base + prefix + "/",
        "feed_url": base + prefix + "/feed.json",
        "description": site.s("footer_about"),
        "icon": icon_url(site, "icon-512.png"),
        "favicon": icon_url(site, "icon-192.png"),
        "language": HREFLANG[lang],
        "authors": [{"name": name, "url": base + "/"}],
        "items": items,
    }
    return json.dumps(feed, ensure_ascii=False, indent=1) + "\n"


def webmanifest(site, model, lang):
    """The web app manifest of LANG's edition. Its addresses are relative to the
    manifest, so the same file works in every build mode."""
    up = "../" if lang == "zh" else ""
    icons = [{"src": f"{up}assets/icons/{name}", "sizes": f"{px}x{px}", "type": "image/png"}
             for name, px in ICONS.items() if name != "apple-touch-icon.png"]
    icons.append(dict(icons[-1], purpose="maskable"))
    doc = {"name": site_name(model), "short_name": site_name(model), "description": one_line(describe(model, lang)),
           "lang": HREFLANG[lang], "dir": "ltr", "start_url": "./", "display": "browser",
           "background_color": THEME_COLOR, "theme_color": THEME_COLOR, "icons": icons}
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
