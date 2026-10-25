"""HTML templates for verifiable.pro.

Every page is rendered for a canonical path such as ``/latest/`` or
``/zh/articles/<slug>/``. ``Site.href`` turns canonical paths into links:
absolute clean URLs in production, relative ``index.html`` links in preview
builds (which also serve the Artifact preview).

Trusted execution environments (TEEs) are the site's main subject. The
shared pieces follow the component contract in DESIGN.md and site.css
sections 19 and 21: story tags (layer codes and a TEE label), the Stack
page's seven-layer table with its TEE line, the trust tiers, path lists and
the TEE hub at the confidential-computing topic's address. The pictures on the
pages are the home page hero, the drawn stack and you, the person talking with
it, with the seven layer labels and their layer cards, and each article's lead
image (its illustration.json): a captioned figure under the article's head, and
decorative copies beside the story in lists (Site.thumb). The social cards in
static/og/ appear only in link previews; long field lists fold into <details>.
"""

import datetime as dt
import html
import json
import posixpath
import re
import urllib.parse

from . import content, discover, md
from .logos import LAYER_ICONS, LOGOS, PERSON_ICON

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]
KIND_ORDER = ("news", "analysis", "explainer", "guide")
FONTS = (
    "https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;"
    "0,6..72,600;1,6..72,400&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap"
)
# The body of an article's ":::checked" callout ("What we checked")
CHECKED_RE = re.compile(r"^:::checked[^\n]*\n(.*?)\n:::[ \t]*$", re.S | re.M)
# A sentence end: ". " after a lowercase letter, digit or bracket (so "U.S. " and
# "version 1.0" do not split), or a Chinese full stop, question or exclamation mark
SENTENCE_END_RE = re.compile(r"(?<=[a-z0-9)\]][.!?])\s+(?=[A-Z\"“‘(])|(?<=[。！？])")
# Ids that article and page templates (and chat.js) place around a Markdown
# body; build.py reserves them so a heading such as "## Main" gets "main-2".
# Sources add "source-1" ... per article.
PAGE_IDS = (
    "main", "f-read", "chat-config", "details-title", "record-title", "chat-aside-title", "disclosure-title",
    "toc-title", "sources-title", "changes-title", "check-title", "related-title",
    "chat-panel", "chat-title", "chat-input", "chat-status", "chat-disclosure", "chat-att-line", "chat-att-panel",
    "analytics-config", "analytics-choice", "analytics-title",
)
# Interface strings that content/strings.json may not define yet; a key there
# takes precedence. Move these into strings.json when it is next edited.
FALLBACK_STRINGS = {
    "en": {"breadcrumb": "Breadcrumb", "art_label": "Generated illustration for: {title}",
           "search_count": "{n} results", "search_count_one": "1 result",
           "layer_more": "More on this layer", "res_more": "Summary", "footer_llms": "Guide for AI agents (llms.txt)"},
    "zh": {"breadcrumb": "面包屑导航", "art_label": "生成插图：{title}", "search_count": "{n} 个结果",
           "layer_more": "本层详情", "res_more": "简介", "footer_llms": "AI 智能体指南（llms.txt）"},
}
# The TEE hub's coverage list shows this many of the newest TEE stories not on its path
HUB_COVERAGE = 5
# The head of a page that search engines should not index (Site.layout's indexable=False);
# build.sitemap() leaves out every page that carries it
ROBOTS_NOINDEX = '<meta name="robots" content="noindex">'
# The head of every other page: search results may show a large preview of its images,
# such as its social card, up to the width of the screen (Google's max-image-preview)
ROBOTS_INDEX = '<meta name="robots" content="max-image-preview:large">'
# A hint that only the Claude artifact viewer reads, so only artifact builds carry it
ARTIFACT_VIEWER_HINT = '<meta name="claude:viewport-fit-sides" content="cover">'

# The TEE hub is the confidential-computing topic's page
TEE_TOPIC = content.TEE_TOPIC
HUB_PATH = f"/topics/{TEE_TOPIC}/"
ARROW = ' <span aria-hidden="true">→</span>'
# A guide's numbered steps: "## Step 3: ..." or "## 3. ..." headings in the English body
STEP_RE = re.compile(r"^##\s+(?:Step\s+\d+\b|\d+\.\s)", re.I)
FENCE_RE = re.compile(r"^(`{3,}|~{3,})")
# Resources groups whose "You trust" line names every tier of the topic, joined with
# "or"; the other groups name their first tier (the two tiers of verifiable
# inference are alternatives that check the same claim)
TRUST_ALL_TIERS = ("verifiable-inference",)
# Vision and other pages fill these placeholders: <div data-include="name"></div>
INCLUDE_RE = re.compile(r'<div\s+data-include="([^"]*)"\s*>\s*</div>')
# Data-file dates: YYYY-MM-DD, YYYY-MM or YYYY
WHEN_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
# English trust names start with an article; mid-sentence it is lowercase
LEADING_ARTICLE_RE = re.compile(r"^(The|An|A) ")
# The width a photo takes on the page, for srcset's choice among its 400 and 800 px copies
# (variants.thumb and variants.list) and its 1600 px file: each list copy's widest width at
# each of static/site.css's breakpoints (section 22.3), by its class, and the article's
# figure, as wide as the reading column (--measure). The rail's and the TEE rows' copies stay
# under 140 CSS px, so they load the 400 px file on most screens. Latest's river widens its
# picture column with the list (13.5rem from a 64rem window, 18rem from 72rem)
THUMB_SIZES = {
    "news-lead-media": "(min-width: 80rem) 32rem, (min-width: 60rem) 28rem, (min-width: 34rem) 32rem, "
                       "calc(100vw - 2rem)",
    "ledger-thumb": "(min-width: 80rem) 7.5rem, (min-width: 60rem) 5.5rem, (min-width: 30rem) 6.5rem, 5.5rem",
    "brief-thumb": "(min-width: 47.5rem) 8.5rem, (min-width: 30rem) 6.5rem, 5.5rem",
    "river-thumb": "(min-width: 72rem) 18rem, (min-width: 64rem) 13.5rem, (min-width: 32rem) 11rem, 15rem",
    "card-thumb": "(min-width: 60rem) 23rem, (min-width: 37.5rem) 46vw, calc(100vw - 2rem)",
}
# A topic page's river shares the page with the record column from 64rem, so its pictures
# keep to the 11rem column there, where Latest's widen
TOPIC_RIVER_SIZES = "(min-width: 32rem) 11rem, 15rem"
FIGURE_SIZES = "(min-width: 45rem) 40.5rem, calc(100vw - 2rem)"


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


CJK_TEXT_RE = re.compile(r"[　-〿㐀-鿿豈-﫿＀-￯]")
LATIN_TEXT_RE = re.compile(r"[A-Za-z]")


def island_lang(text, page_lang):
    """The lang value for text in the other language than the page, else "".

    Source titles, publishers and resource titles stay in their original
    language, so most are English on Chinese pages. Mixed text keeps the page
    language rather than risk a wrong voice."""
    text = text or ""
    if page_lang == "zh" and LATIN_TEXT_RE.search(text) and not CJK_TEXT_RE.search(text):
        return "en"
    if page_lang == "en" and CJK_TEXT_RE.search(text) and not LATIN_TEXT_RE.search(text):
        return "zh-CN"
    return ""


def json_script(data):
    """JSON for a <script> element: "<" is escaped, so no "</script>" or "<!--" in the data can end or upset it."""
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def fmt_date(d, lang):
    if not d:
        return ""
    if lang == "zh":
        return f"{d.year}年{d.month}月{d.day}日"
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def fmt_month(d, lang):
    return f"{d.year}年{d.month}月" if lang == "zh" else f"{MONTHS_LONG[d.month - 1]} {d.year}"


def fmt_when(value, lang):
    """A data-file date (YYYY-MM-DD, YYYY-MM or YYYY) as (datetime attribute, label);
    ("", "") for an empty value."""
    value = (value or "").strip()
    m = WHEN_RE.match(value)
    if not m:
        return "", value
    year, month, day = m.groups()
    if day:
        return value, fmt_date(dt.date(int(year), int(month), int(day)), lang)
    if month:
        return value, (f"{year}年{int(month)}月" if lang == "zh" else f"{MONTHS[int(month) - 1]} {year}")
    return value, (f"{year}年" if lang == "zh" else year)


def plain(text):
    """Strip inline Markdown markers, citations and link targets for plain-text labels."""
    text = md.LINK_RE.sub(r"\1", re.sub(r"\[\^\d+(?:\s*,\s*\d+)*\]", "", text))
    return re.sub(r"`|\*\*|\*|(?<!\w)_|_(?!\w)", "", text)


def source_date(value, lang):
    """Format a source date: YYYY-MM-DD, YYYY-MM, YYYY or 'accessed YYYY-MM-DD'."""
    value = (value or "").strip()
    accessed = re.match(r"^accessed (\d{4}-\d{2}-\d{2})$", value)
    if accessed:
        d = dt.date.fromisoformat(accessed.group(1))
        return ("访问于 " if lang == "zh" else "accessed ") + fmt_date(d, lang)
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return fmt_date(dt.date.fromisoformat(value), lang)
    month = re.match(r"^(\d{4})-(\d{2})$", value)
    if month:
        y, m = int(month.group(1)), int(month.group(2))
        return f"{y}年{m}月" if lang == "zh" else f"{MONTHS[m - 1]} {y}"
    return value


def time_tag(d, lang):
    return f'<time datetime="{d.isoformat()}">{fmt_date(d, lang)}</time>' if d else ""


def guide_steps(body):
    """The number of numbered steps in a guide's Markdown body (outside code blocks)."""
    n, fence = 0, None
    for line in body.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        opened = FENCE_RE.match(s)
        if fence:
            if opened and s.startswith(fence) and not s.strip(fence[0]):
                fence = None
            continue
        if opened:
            fence = opened.group(1)
            continue
        if STEP_RE.match(s):
            n += 1
    return n


# The light/dark toggle: a moon (offers dark) and a sun (offers light); the stylesheet
# shows the one for the theme the page is not in
ICON_THEME = (
    '<svg class="icon-moon" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">'
    '<path d="M15.5 12.3A6.5 6.5 0 0 1 7.7 4.5a6.5 6.5 0 1 0 7.8 7.8z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/></svg>'
    '<svg class="icon-sun" viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">'
    '<circle cx="10" cy="10" r="3.6" fill="none" stroke="currentColor" stroke-width="1.6"/>'
    '<path d="M10 1.8v2.4M10 15.8v2.4M1.8 10h2.4M15.8 10h2.4M4.2 4.2l1.7 1.7M14.1 14.1l1.7 1.7M4.2 15.8l1.7-1.7M14.1 5.9l1.7-1.7" '
    'stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>'
)
ICON_SEARCH = (
    '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">'
    '<circle cx="8.5" cy="8.5" r="5.5" fill="none" stroke="currentColor" stroke-width="1.6"/>'
    '<path d="M12.6 12.6 17 17" stroke="currentColor" stroke-width="1.6" stroke-linecap="square"/></svg>'
)


ICON_ASK = (
    '<svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">'
    '<path d="M3 3.5h14v10H8.5L5 16.8V13.5H3z" fill="none" stroke="currentColor" stroke-width="1.5"/>'
    '<rect class="chat-icon-seal" x="11.5" y="8" width="3.5" height="3.5"/></svg>'
)

# The hero's layout from 45em (720px at the default text size): the scene takes HERO_ART
# percent of the stage, the label column starts at HERO_LABELS, and a layer card runs from
# HERO_CARD (just right of every plate's right corner, so it never covers a plate) to the
# stage's right edge. The leader lines are drawn in the same percentages, and the figure
# hands them to the stylesheet.
HERO_ART = 60
HERO_LABELS = 63
HERO_CARD = 58.5
# The chain at rest: "status" draws each binding as it holds today; "whole" draws it unbroken
# and shows the statuses only while a layer is open (owner decision; see DESIGN.md).
HERO_CHAIN_REST = "status"
# The hero legend's samples of the chain in a 28 x 4 box, by binding status: solid where a
# binding is in use, dashed where one is emerging, broken where there is none
HERO_CHAIN_SAMPLES = {
    "deployed": '<path d="M1 2h26"/>',
    "emerging": '<path d="M1 2h26" stroke-dasharray="4 3"/>',
    "missing": '<path d="M1 2h6M21 2h6"/>',
}

# The hero's pause control (static/hero.js swaps the icons and labels)
ICON_PAUSE = ('<svg class="verification-pause-icon" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true" '
              'focusable="false"><path d="M4 2v8M8 2v8"/></svg>')
ICON_PLAY = ('<svg class="verification-play-icon" viewBox="0 0 12 12" width="12" height="12" aria-hidden="true" '
             'focusable="false"><path d="m4 2 6 4-6 4Z"/></svg>')
# The chevron that opens a layer row's card on touch screens and phones (static/hero.js shows it)
ICON_MORE = ('<svg class="hero-more-icon" viewBox="0 0 12 12" aria-hidden="true" focusable="false">'
             '<path d="M3 4.5l3 3 3-3"/></svg>')
# The check mark beside a layer's name once the reader has checked the layer (static/hero.js)
ICON_TICK = ('<svg class="hero-tick-icon" viewBox="0 0 16 16" aria-hidden="true" focusable="false">'
             '<path d="M3.2 8.6l3.1 3.1 6.5-7"/></svg>')
# The hero's guard, inline after static/hero.js on the home pages. Where scripts run the scene grays
# you from the first paint while the figure has data-hv-wait, which the build writes; hero.js writes
# data-hv-checked once it has set the figure up. At the window's load, when hero.js has not (it
# failed to load, or threw first), the guard removes data-hv-wait, so you are not left gray.
HERO_GUARD = ('(function(){function f(){document.querySelectorAll("[data-verification-visual][data-hv-wait]")'
              '.forEach(function(g){if(!g.hasAttribute("data-hv-checked"))g.removeAttribute("data-hv-wait")})}'
              'if(document.readyState==="complete")f();else addEventListener("load",f)})()')
# The hero's hint, one line for each way of opening a layer: pointing or Tab from 45em with a mouse or
# a pen, a tap on a layer's arrow on touch screens, a click on it in the list below 45em with a mouse
# (site.css 21.2 shows the one that fits); then the same once every layer is checked, without the
# promise of colour
HERO_HINTS = (("pointer", "hero_hint"), ("touch", "hero_hint_touch"), ("click", "hero_hint_click"))

# The site assistant ("Ask"): static/chat.js and chat.css, configured per page
# by an inline JSON block. See api/chat-v1.md and DESIGN.md.
CHAT_MODES = ("off", "demo", "live")
CHAT_LAUNCHERS = ("header", "float")
API_BASE_RE = re.compile(r"^https?://[^\s/?#]+(/[^\s?#]*)?$")


def chat_settings(site, mode=None, api_base=None):
    """The "chat" block of content/site.json, with build overrides applied and checked.

    A site.json without a "chat" block builds without the assistant; a block
    without "mode" means "demo". Raises ValueError on a value chat.js cannot use.
    """
    raw = site.get("chat")
    if raw is None:
        raw = {"mode": "off"}
    if not isinstance(raw, dict):
        raise ValueError('content/site.json: "chat" must be an object')
    out = {
        "mode": mode or raw.get("mode", "demo"),
        "api_base": raw.get("api_base", "") if api_base is None else api_base,
        "launcher": raw.get("launcher", "header"),
        "allow_demo_fallback": raw.get("allow_demo_fallback", True),
        "suggestions": raw.get("suggestions") or {},
    }
    if out["mode"] not in CHAT_MODES:
        raise ValueError(f"chat.mode must be one of {', '.join(CHAT_MODES)}, not {out['mode']!r}")
    if out["launcher"] not in CHAT_LAUNCHERS:
        raise ValueError(f"chat.launcher must be one of {', '.join(CHAT_LAUNCHERS)}, not {out['launcher']!r}")
    if not isinstance(out["allow_demo_fallback"], bool):
        raise ValueError("chat.allow_demo_fallback must be true or false")
    api = out["api_base"]
    if not isinstance(api, str) or (api and not API_BASE_RE.match(api)):
        raise ValueError(f"chat.api_base must be an http(s) URL without query or fragment, not {api!r}")
    out["api_base"] = api.rstrip("/")
    if out["mode"] == "live" and not out["api_base"]:
        raise ValueError('chat.mode "live" needs chat.api_base (or build.py --chat-api URL)')
    sg = out["suggestions"]
    if not isinstance(sg, dict) or not all(
            isinstance(v, list) and all(isinstance(q, str) and q.strip() for q in v) for v in sg.values()):
        raise ValueError('chat.suggestions must map a language to a list of questions: {"en": [...], "zh": [...]}')
    return out


MARK_INNER = (
    '<rect class="mark-bg" width="48" height="48"/>'
    '<path class="mark-fg-stroke" d="M10.5 24.5 18.5 32.5 33 15" fill="none" stroke-width="2.6" stroke-linecap="square"/>'
    '<rect class="mark-fg" x="33" y="28" width="5.5" height="5.5"/>'
)


def set_mark(svg_text):
    """Use the inner markup of a 48x48 mark SVG whose shapes carry mark-* classes."""
    global MARK_INNER
    start, end = svg_text.index(">", svg_text.index("<svg")) + 1, svg_text.rindex("</svg>")
    MARK_INNER = svg_text[start:end].strip()


def mark_svg(size=36, cls="mark"):
    """The verifiable.pro mark, themed through CSS classes."""
    return (
        f'<svg class="{cls}" viewBox="0 0 48 48" width="{size}" height="{size}" aria-hidden="true" focusable="false">'
        f"{MARK_INNER}</svg>"
    )


class Site:
    def __init__(self, model, mode="prod"):
        self.m = model
        self.mode = mode
        self.base_url = model["site"]["base_url"].rstrip("/")
        self.topics = {t["id"]: t for t in model["topics"]["topics"]}
        self.topic_order = [t["id"] for t in model["topics"]["topics"]]
        self.lang = "en"
        self.current = "/"
        self.build_digest = ""
        self.year = dt.date.today().year
        self.chat = chat_settings(model["site"])
        self.analytics_id = content.analytics_id(model["site"]) if mode == "prod" else ""
        # The home hero; build.py sets these. hero_svg is the scene template with
        # {{SCENE_TITLE}}, {{SCENE_DESC}} and {{SCENE_DESC_LIVE}} still to fill, and hero_anchors
        # says where each layer's leader line starts (sitegen/templates/hero-anchors.json).
        self.hero_svg = ""
        self.hero_anchors = {}
        self._slugs = {}

    # ----- language and links -------------------------------------------------
    def s(self, key, **kw):
        strings = self.m["strings"][self.lang]
        text = strings[key] if key in strings or key not in FALLBACK_STRINGS[self.lang] else FALLBACK_STRINGS[self.lang][key]
        return text.format(**kw) if kw else text

    def t(self, value):
        """Pick the current language from a {"en": .., "zh": ..} value."""
        if isinstance(value, dict):
            return value.get(self.lang) or value.get("en", "")
        return value or ""

    def lang_attr(self, text):
        """' lang="en"' on English text in a Chinese page (and the reverse), for screen reader voices."""
        lang = island_lang(text, self.lang)
        return f' lang="{lang}"' if lang else ""

    def island(self, text):
        """Escaped text, wrapped in a span with its own lang when it is in the other language."""
        attr = self.lang_attr(text)
        return f"<span{attr}>{esc(text)}</span>" if attr else esc(text)

    def md_link(self, target):
        """Resolve a site-absolute Markdown link in a front-matter field, as build.resolver does for bodies."""
        path = target.split("#", 1)[0]
        if self.lang == "zh" and (path.endswith("/") or path == "") and not target.startswith("/zh/"):
            target = "/zh" + target
        return self.href(target)

    def loc(self, path, lang=None):
        lang = lang or self.lang
        return ("/zh" + path) if lang == "zh" else path

    def href(self, target):
        if self.mode == "prod" or target.startswith(("http://", "https://", "mailto:", "#")):
            return target
        path, _, frag = target.partition("#")
        if path.endswith("/"):
            path += "index.html"
        here = self.current if self.current.endswith("/") else posixpath.dirname(self.current) + "/"
        rel = posixpath.relpath(path, here)
        return rel + ("#" + frag if frag else "")

    def a(self, target, label, cls="", extra=""):
        c = f' class="{cls}"' if cls else ""
        return f'<a href="{esc(self.href(target))}"{c}{extra}>{label}</a>'

    def ext(self, url, title, cls="ext"):
        """An outside link: the title keeps its own language and ends with the ↗ mark."""
        return (f'<a href="{esc(url)}" rel="noopener" class="{cls}"{self.lang_attr(title)}>{esc(title)}'
                f'<span class="ext-mark" aria-hidden="true">↗</span></a>')

    def root_rel(self):
        if self.mode == "prod":
            return "/"
        here = self.current if self.current.endswith("/") else posixpath.dirname(self.current) + "/"
        depth = here.strip("/").count("/") + (1 if here.strip("/") else 0)
        return "../" * depth or "./"

    def count(self, key, n):
        one = f"{key}_one"
        if n == 1 and (one in self.m["strings"][self.lang] or one in FALLBACK_STRINGS[self.lang]):
            return self.s(one, n=n)
        return self.s(key, n=n)

    def colon(self, key):
        """An escaped interface label followed by the language's colon ("Sources: ", "来源：")."""
        return esc(self.s(key) + self.s("label_colon"))

    def join_sentences(self, parts):
        """Sentences in a row: a space between them in English, none in Chinese."""
        return ("" if self.lang == "zh" else " ").join(p for p in parts if p)

    def kind_label(self, kind, form="kind"):
        return self.s(f"{form}_{kind}")

    def topic_name(self, tid):
        topic = self.topics.get(tid)
        return self.t(topic["name"]) if topic else tid

    def article_url(self, art_obj, lang=None):
        return self.loc(f"/articles/{art_obj.slug}/", lang or art_obj.lang)

    def other(self):
        return "zh" if self.lang == "en" else "en"

    # ----- the stack, tiers and story tags ---------------------------------------
    def stack(self):
        return self.m["topics"].get("stack", [])

    def layer(self, lid):
        return next((layer for layer in self.stack() if layer["id"] == lid), None)

    def layer_code(self, lid):
        """"T7" for the top layer down to "T1", from the stack's order."""
        ids = [layer["id"] for layer in self.stack()]
        return f"T{len(ids) - ids.index(lid)}"

    def layers_of(self, a_obj):
        """The article's stack layers, T7 first: the front-matter layers, or without
        that field the layers that list its primary topic. [] names none."""
        stack = self.stack()
        explicit = getattr(a_obj, "layers", None)
        if explicit is not None:
            order = {layer["id"]: n for n, layer in enumerate(stack)}
            return sorted((lid for lid in explicit if lid in order), key=order.get)
        return [layer["id"] for layer in stack if a_obj.primary_topic in layer.get("topics", [])]

    def is_tee(self, a_obj):
        """True for a story about trusted execution environments."""
        return TEE_TOPIC in a_obj.topics

    def tags(self, a_obj):
        """The story tags of a list row. The layer codes link to the first layer on the
        Stack page, and site.js shows the whole stack with the story's layers marked
        when they are hovered or focused (#stack-data); the link names the layers in
        full for screen readers. The TEE label adds no tab stop."""
        ids = self.layers_of(a_obj)
        tee = self.is_tee(a_obj)
        if not ids and not tee:
            return ""
        parts = []
        if ids:
            names = [self.t(self.layer(lid)["name"]) for lid in ids]
            codes = [self.layer_code(lid) for lid in ids]
            target = self.href(self.loc("/topics/") + "#layer-" + ids[0])
            parts.append(f'<a class="tag-layers" href="{esc(target)}" data-layers="{esc(" ".join(ids))}">'
                         f'<span aria-hidden="true">{esc(" ".join(codes))}</span>'
                         f'<span class="vh">{esc(self.s("tag_layers_vh", names=self.s("list_comma").join(names)))}</span></a>')
        if tee:
            name = self.s("tag_tee_name")
            parts.append(f'<span class="tag tag-tee" aria-hidden="true" title="{esc(name)}">{esc(self.s("tag_tee"))}</span>'
                         f'<span class="vh">{esc(name + ("。" if self.lang == "zh" else "."))}</span>')
        return f'<span class="tags">{"".join(parts)}</span>'

    def stack_data(self):
        """The stack as JSON for the stack card that site.js opens on a story's layer codes."""
        return json_script({
            "title": self.s("pop_title"), "note": self.s("pop_note"),
            "layers": [{"id": layer["id"], "code": self.layer_code(layer["id"]), "name": self.t(layer["name"]),
                        "reach": layer["tee"]["reach"], "bind": (layer.get("bind") or {}).get("status", "")}
                       for layer in self.stack()],
        })

    def layer_stories(self, articles, lid):
        """The stories at a stack layer, in the order given, and how many of them are about
        TEEs. The Stack page's table and the hero's layer cards count with it, so they agree."""
        stories = [a for a in articles if lid in self.layers_of(a)]
        return stories, sum(1 for a in stories if self.is_tee(a))

    def cover_label(self, stories, n_tee):
        """"15 stories · 2 about TEEs": a layer's story count, with its TEE stories when it has any."""
        label = self.count("stack_cover", len(stories))
        return label + " · " + self.s("stack_cover_tee", n=n_tee) if n_tee else label

    def tiers(self):
        return self.m.get("tiers", {}).get("tiers", [])

    def tier(self, tid):
        return next((t for t in self.tiers() if t["id"] == tid), None)

    def tier_link(self, tid, label=None):
        """A tier's short name (or another label), linked to its row on the Stack page."""
        tier = self.tier(tid)
        text = label if label is not None else self.t(tier["short"])
        return self.a(self.loc("/topics/") + f"#tier-{tid}", self.island(text))

    def trust_text(self, text):
        """A tier's trust name inside a sentence ("You trust: the signer and its keys")."""
        return LEADING_ARTICLE_RE.sub(lambda m: m.group(1).lower() + " ", text) if self.lang == "en" else text

    # ----- articles and resources by id ------------------------------------------
    def find_article(self, slug):
        """The article with this slug in the page language, else in English, else None."""
        for lang in (self.lang, "en"):
            if lang not in self._slugs:
                self._slugs[lang] = {a.slug: a for a in self.m.get("articles", {}).get(lang, [])}
            if slug in self._slugs[lang]:
                return self._slugs[lang][slug]
        return None

    def article_link(self, slug, label=None, suffix="", cls=""):
        """A link to an article by slug, titled in the page language when it has that
        edition; an English fallback on a Chinese page says so with hreflang. label
        replaces the title; suffix (HTML, such as the arrow) ends the link text."""
        a_obj = self.find_article(slug)
        if a_obj is None:
            return ""
        fallback = a_obj.lang != self.lang
        text = esc(label) if label is not None else (f'<span lang="en">{esc(a_obj.title)}</span>' if fallback
                                                     else self.island(a_obj.title))
        return self.a(self.article_url(a_obj), text + suffix, cls, ' hreflang="en"' if fallback else "")

    def resource(self, rid):
        return next((r for r in self.m["resources"]["resources"] if r["id"] == rid), None)

    def source_links(self, refs):
        """Links for data-file sources: "article:<slug>" to the article, "resource:<id>" to the document."""
        out = []
        for ref in refs or []:
            kind, _, ident = ref.partition(":")
            if kind == "article":
                link = self.article_link(ident)
            else:
                r = self.resource(ident)
                link = self.ext(r["url"], r["title"]) if r else ""
            if link:
                out.append(link)
        return out

    def sources_line(self, refs, cls, tag="p"):
        links = " · ".join(self.source_links(refs))
        return f'<{tag} class="{cls}">{self.colon("sources_title")}{links}</{tag}>' if links else ""

    def sources_fold(self, refs, cls, inline=False):
        """Sources folded under "3 sources", where a run of long titles would outweigh
        what they support: one per line in a table cell, or inline as one line."""
        links = self.source_links(refs)
        if not links:
            return ""
        if inline:  # the line carries the class, so it reads like the other sources lines
            inner, cls = f'<p class="{cls}">{" · ".join(links)}</p>', "sources-fold"
        else:
            inner = f'<ul>{"".join(f"<li>{link}</li>" for link in links)}</ul>'
        return (f'<details class="{cls}"><summary>{esc(self.count("sources_count", len(links)))}</summary>'
                f'{inner}</details>')

    def field_list(self, rows, cls, pending=False):
        """A dl of (label key, {en, zh} text) rows. Empty texts are left out, or with
        pending=True read "Not yet covered here"."""
        items = []
        for key, value in rows:
            text = self.t(value)
            if not text and not pending:
                continue
            dd = esc(text) if text else f'<span class="plat-pending">{esc(self.s("plat_pending"))}</span>'
            items.append(f'<div><dt>{esc(self.s(key))}</dt><dd>{dd}</dd></div>')
        return f'<dl class="{cls}">{"".join(items)}</dl>' if items else ""

    def hub_trackers(self):
        """Tracker rows of the TEE hub as (anchor, name, sources): services, limits and responses."""
        tee = self.m.get("tee", {})
        rows = [(f"svc-{r['id']}", r) for r in tee.get("services", [])]
        rows += [(f"limit-{r['id']}", r) for r in tee.get("limits", [])]
        rows += [(f"resp-{r['id']}", r) for r in tee.get("responses", [])]
        return [(anchor, self.t(r["name"]), r.get("sources", [])) for anchor, r in rows]

    # ----- page frame ---------------------------------------------------------
    def nav_items(self):
        return [
            ("vision", "/vision/", self.s("nav_vision")),
            ("tee", HUB_PATH, self.s("nav_tee")),
            ("latest", "/latest/", self.s("nav_latest")),
            ("topics", "/topics/", self.s("nav_stack")),
            ("learn", "/learn/", self.s("nav_learn")),
            ("resources", "/resources/", self.s("nav_resources")),
        ]

    def header(self, section, alt_path):
        links = []
        for key, path, label in self.nav_items():
            current = ' aria-current="page"' if key == section else ""
            links.append(self.a(self.loc(path), esc(label), extra=current))
        switch_label = self.s("switch_to")
        switch_lang = self.s("switch_to_lang")
        current_label = self.s("lang_name")
        # The Ask launcher ships hidden; chat.js shows it (and leaves it hidden
        # when chat.launcher is "float", which draws its own bottom-right tab)
        ask = ""
        if self.chat_on():
            ask = (f'<button type="button" class="chat-launch" data-chat-open hidden aria-haspopup="dialog" '
                   f'aria-label="{esc(self.s("chat_launch_aria"))}">{ICON_ASK}'
                   f'<span class="chat-launch-label" aria-hidden="true">{esc(self.s("chat_launch"))}</span></button>\n      ')
        return f"""<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="{esc(self.href(self.loc('/')))}" aria-label="verifiable.pro {esc(self.s('home'))}">
      {mark_svg(36)}
      <span class="brand-name">verifiable<span class="brand-tld">.pro</span></span>
    </a>
    <nav class="site-nav" aria-label="{esc(self.s('nav_main'))}">{''.join(links)}</nav>
    <div class="header-tools">
      {ask}<a class="search-link" href="{esc(self.href(self.loc('/search/')))}" aria-label="{esc(self.s('nav_search'))}"{' aria-current="page"' if section == 'search' else ''}>{ICON_SEARCH}</a>
      <button type="button" class="theme-toggle" data-theme-toggle hidden data-label-dark="{esc(self.s('theme_to_dark'))}" data-label-light="{esc(self.s('theme_to_light'))}" aria-label="{esc(self.s('theme_to_dark'))}">{ICON_THEME}</button>
      <nav class="lang-switch" aria-label="{esc(self.s('nav_lang'))}">
        <span class="lang-current" aria-current="true">{esc(current_label)}</span>
        <a href="{esc(self.href(alt_path))}" hreflang="{esc(switch_lang)}" lang="{esc(switch_lang)}">{esc(switch_label)}</a>
      </nav>
    </div>
  </div>
</header>"""

    def chat_on(self):
        return self.chat["mode"] != "off"

    def chat_config(self, path, page=None):
        """The inline #chat-config block that static/chat.js reads.

        Paths stay canonical ("/articles/x/", "/manifest.json"); chat.js resolves
        them against the page's data-root, as site.js does, so the same block
        works with absolute production links and relative preview links.
        """
        chat = self.chat
        strings = self.m["strings"][self.lang]
        cfg = {
            "mode": chat["mode"],
            "api": chat["api_base"] if chat["mode"] == "live" else "",
            "launcher": chat["launcher"],
            "lang": self.lang,
            "index": self.loc("/search-index.json"),
            "manifest": "/manifest.json",
            "build": self.build_digest,
            "about": self.loc("/about/") + "#assistant",
            "page": page or {"kind": "page", "url": path},
            "suggestions": chat["suggestions"].get(self.lang, []),
            "allow_demo_fallback": chat["allow_demo_fallback"],
            "strings": {k: v for k, v in strings.items() if k.startswith("chat_")},
        }
        # "<" as <, so no "</script>" or "<!--" can end or upset the script element
        blob = json.dumps(cfg, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
        return f'<script type="application/json" id="chat-config">{blob}</script>'

    def repo(self):
        """The public source repository, or "" while content/site.json has no repo_url."""
        return (self.m["site"].get("repo_url") or "").rstrip("/")

    def footer(self):
        L = self.loc
        email = esc(self.m["site"].get("contact_email", ""))
        repo = self.repo()
        ext = '<span class="ext-mark" aria-hidden="true">↗</span>'
        sections = [(L(path), label) for _, path, label in self.nav_items()]
        sections += [(L("/glossary/"), self.s("nav_glossary")), (L("/about/"), self.s("nav_about"))]
        read = "".join(f"<li>{self.a(p, esc(t))}</li>" for p, t in sections)
        read += (f'<li class="footer-labelled"><span class="footer-label">{esc(self.s("related_pub"))}</span>'
                 f'<a href="https://auditcommons.org/" rel="noopener">Audit Commons{ext}</a></li>')
        contribute = []
        if repo:
            contribute.append(f'<li><a href="{esc(repo)}" rel="noopener">{esc(self.s("footer_repo"))}{ext}</a></li>')
            contribute.append(f'<li><a href="{esc(repo)}/issues/new/choose" rel="noopener">{esc(self.s("footer_suggest"))}{ext}</a></li>')
        contribute.append(f"<li>{self.a(L('/about/') + '#contribute', esc(self.s('footer_contribute')))}</li>")
        contribute.append(f"<li>{self.a(L('/about/') + '#corrections', esc(self.s('footer_corrections')))}</li>")
        contribute.append(f"<li>{self.a(L('/privacy/'), esc(self.s('footer_privacy')))}</li>")
        if self.analytics_id:
            contribute.append(f'<li><button type="button" class="footer-analytics" data-analytics-open hidden>{esc(self.s("analytics_choices"))}</button></li>')
        contribute.append(f'<li class="footer-labelled"><span class="footer-label">{esc(self.s("footer_email"))}</span><span class="email">{email}</span></li>')
        machine = [
            (self.loc("/feed.xml", "en"), self.s("footer_feed_en"), ' hreflang="en"'),
            (self.loc("/feed.xml", "zh"), self.s("footer_feed_zh"), ' hreflang="zh-CN"'),
            ("/manifest.json", self.s("footer_manifest"), ""),
            ("/sitemap.xml", self.s("footer_sitemap"), ""),
            ("/llms.txt", self.s("footer_llms"), ""),  # the site's guide for language models (sitegen/discover.py)
        ]
        machine_links = "".join(f"<li>{self.a(p, esc(t), extra=x)}</li>" for p, t, x in machine)
        wordmark = f'<a class="sept-wordmark" href="https://septlab.com/"{self.lang_attr("SEPT Lab")}><span class="sept-brand">SEPT</span> Lab</a>'
        maintainer = esc(self.s("home_maintainer")).replace("{name}", wordmark)
        return f"""<footer class="site-footer">
  <div class="wrap"><div class="footer-band">
    <div class="footer-brand">
      <a class="brand brand-footer" href="{esc(self.href(L('/')))}">{mark_svg(32)}<span class="brand-name">verifiable<span class="brand-tld">.pro</span></span></a>
      <p>{esc(self.s('footer_about'))}</p>
      <p class="footer-credits">{maintainer}&nbsp;<span aria-hidden="true">·</span> {self.a(L('/contributors/'), esc(self.s('home_contributors')))}</p>
    </div>
  </div></div>
  <div class="wrap footer-grid">
    <nav class="footer-col" aria-labelledby="f-read"><h2 id="f-read">{esc(self.s('footer_sections'))}</h2><ul>{read}</ul></nav>
    <div class="footer-col"><h2>{esc(self.s('footer_contact'))}</h2><ul>{''.join(contribute)}</ul></div>
    <div class="footer-col"><h2>{esc(self.s('footer_machine'))}</h2><ul class="footer-machine">{machine_links}</ul></div>
  </div>
  <div class="wrap footer-bottom"><p>{esc(self.s('copyright', year=self.year))} · {self.a(self.loc("/vision/") + "#editor", esc(self.s("home_editor")), cls="footer-editor")}</p></div>
</footer>"""

    def analytics_block(self):
        """Local consent UI only; analytics.js loads Google solely after Allow."""
        if not self.analytics_id:
            return ""
        config = {"id": self.analytics_id, "origin": self.base_url,
                  "on": self.s("analytics_on"), "off": self.s("analytics_off"),
                  "unsaved": self.s("analytics_unsaved")}
        return f'''<script type="application/json" id="analytics-config">{json_script(config)}</script>
<section class="analytics-choice" id="analytics-choice" aria-labelledby="analytics-title" hidden>
  <h2 id="analytics-title">{esc(self.s("analytics_title"))}</h2>
  <p>{esc(self.s("analytics_text"))} {self.a(self.loc('/privacy/'), esc(self.s('footer_privacy')))}</p>
  <p class="analytics-status" data-analytics-status role="status" hidden></p>
  <div class="analytics-actions"><button type="button" data-analytics-allow>{esc(self.s("analytics_allow"))}</button><button type="button" data-analytics-decline>{esc(self.s("analytics_decline"))}</button></div>
</section>'''

    def layout(self, *, path, title, description, section, body, alt_path, page_class, og_type="website", head_extra="", jsonld=None,
               chat_page=None, alternate=True, indexable=True, hero_script=False, image=None, source=None, article=None,
               crumbs=None):
        """alternate: alt_path is this page in the other language (not a fallback such
        as Latest for an untranslated article). indexable: False for pages that search
        engines should not index: the 404 pages, which hosts serve at any missing
        address, and the search pages, which list no results without JavaScript. Such a
        page carries ROBOTS_NOINDEX and no canonical URL, language alternates or trail,
        and build.sitemap() leaves it out; every other page carries ROBOTS_INDEX.
        hero_script: the page carries the animated hero, so static/hero.js is
        linked (with defer); only the two home pages may.
        image: the topic whose social card the page shows (a topic page's own, an
        article's primary topic), else the site's card; or an article's own picture for
        link previews, as discover.photo_card() gives it. source: the page's Markdown
        source, linked as its text/markdown alternate. article: dates, section and
        tags for the article:* tags (sitegen/discover.py). crumbs: the trail above
        the title, which page_head() records, for the BreadcrumbList."""
        self.current = path
        crumbs = crumbs if crumbs is not None else self.__dict__.pop("crumbs", None)
        self.__dict__.pop("crumbs", None)
        if crumbs and indexable:
            trail = discover.breadcrumbs(self, crumbs, title)
            jsonld = ([jsonld] if isinstance(jsonld, dict) else list(jsonld or [])) + [trail]
        chat_assets = chat_block = ""
        if self.chat_on():
            chat_assets = (f'\n<link rel="stylesheet" href="{esc(self.href("/assets/chat.css"))}">'
                           f'\n<script src="{esc(self.href("/assets/chat.js"))}" defer></script>')
            chat_block = "\n" + self.chat_config(path, chat_page)
        if hero_script and path in ("/", "/zh/"):
            # defer: the script looks for the hero figure, which follows it in the page; the guard
            # gives you your colour back at the window's load if the script never set the figure up
            chat_assets += (f'\n<script src="{esc(self.href("/assets/hero.js"))}" defer></script>'
                            f'\n<script>{HERO_GUARD}</script>')
        head_extra = chat_assets + head_extra
        if self.analytics_id:
            head_extra += f'\n<script src="{esc(self.href("/assets/analytics.js"))}" defer></script>'
        if jsonld:
            head_extra += f'\n<script type="application/ld+json">{json_script(jsonld)}</script>'
        lang_attr = self.s("html_lang")
        # the site's name follows the page's title, unless the title names the site already: the
        # home pages' title starts with it (home_title), and About is "About verifiable.pro"
        name = discover.site_name(self.m)
        full_title = title if path in ("/", "/zh/") or name.lower() in title.lower() else f"{title} | {name}"
        canonical = self.base_url + path
        alt_lang = "zh-CN" if self.lang == "en" else "en"
        if not indexable:
            urls = ROBOTS_NOINDEX
        else:
            urls = f'{ROBOTS_INDEX}\n<link rel="canonical" href="{esc(canonical)}">'
            if alternate:
                # x-default: the English page, for readers in neither language
                english = canonical if self.lang == "en" else self.base_url + alt_path
                urls += (f'\n<link rel="alternate" hreflang="{esc(lang_attr)}" href="{esc(canonical)}">'
                         f'\n<link rel="alternate" hreflang="{alt_lang}" href="{esc(self.base_url + alt_path)}">'
                         f'\n<link rel="alternate" hreflang="x-default" href="{esc(english)}">')
        og_url = f'\n<meta property="og:url" content="{esc(canonical)}">' if indexable else ""
        social = discover.social_meta(self, image_topic=image, alternate=alternate and indexable, article=article)
        viewer = f"\n{ARTIFACT_VIEWER_HINT}" if self.mode == "artifact" else ""
        head = f"""<title>{esc(full_title)}</title>{viewer}
<meta name="description" content="{esc(description)}">
{urls}
<link rel="alternate" type="application/atom+xml" title="verifiable.pro" href="{esc(self.href(self.loc('/feed.xml')))}">
{discover.head_links(self, source)}
<link rel="icon" href="{esc(self.href('/assets/favicon.svg'))}" type="image/svg+xml">
<meta property="og:site_name" content="verifiable.pro">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:type" content="{og_type}">{og_url}
{social}
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#111416" media="(prefers-color-scheme: dark)">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{FONTS}" data-font-css>
<noscript><link rel="stylesheet" href="{FONTS}"></noscript>
<script>try{{var t=localStorage.getItem("vp-theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}}catch(e){{}}</script>
<link rel="stylesheet" href="{esc(self.href('/assets/site.css'))}">
<script src="{esc(self.href('/assets/site.js'))}" defer></script>{head_extra}"""
        stack_data = f'\n<script type="application/json" id="stack-data">{self.stack_data()}</script>' if self.stack() else ""
        page = f"""<div class="site {esc(page_class)}" lang="{esc(lang_attr)}" data-root="{esc(self.root_rel())}" data-lang="{self.lang}">
<a class="skip-link" href="#main">{esc(self.s('skip'))}</a>
{self.header(section, alt_path)}
<main id="main">
{body}
</main>
{self.footer()}{chat_block}{stack_data}{self.analytics_block()}
</div>"""
        if self.mode == "artifact" and path == "/":
            return head + "\n" + page + "\n"
        return (
            f'<!doctype html>\n<html lang="{esc(lang_attr)}">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f"{head}\n</head>\n<body>\n{page}\n</body>\n</html>\n"
        )

    # ----- shared fragments ---------------------------------------------------
    def kicker(self, a_obj, with_topic=True, link_kind=True):
        kind = esc(self.kind_label(a_obj.kind))
        kind_html = self.a(self.loc("/latest/") + f"#{a_obj.kind}", kind, "kind") if link_kind else f'<span class="kind">{kind}</span>'
        topic = ""
        if with_topic and a_obj.primary_topic:
            topic = self.a(self.loc(f"/topics/{a_obj.primary_topic}/"), esc(self.topic_name(a_obj.primary_topic)), "topic",
                           extra=f' data-topic="{a_obj.primary_topic}"')
        return f'<p class="kicker">{kind_html}{topic}</p>'

    @staticmethod
    def revised(obj):
        """The updated date of an article or page, or None when there is none or it is
        the filing date: an equal second date would only repeat the first."""
        updated = getattr(obj, "updated", None)
        return updated if updated and updated != obj.published else None

    def dates_line(self, a_obj, compact=False, tags="", byline=""):
        parts = []
        if a_obj.event_date and a_obj.kind == "news":
            parts.append(f'<span class="date-item"><span class="date-label">{esc(self.s("announced"))}</span> {time_tag(a_obj.event_date, self.lang)}</span>')
        parts.append(f'<span class="date-item"><span class="date-label">{esc(self.s("published"))}</span> {time_tag(a_obj.published, self.lang)}</span>')
        if self.revised(a_obj) and not compact:
            parts.append(f'<span class="date-item"><span class="date-label">{esc(self.s("updated"))}</span> {time_tag(a_obj.updated, self.lang)}</span>')
        return f'<p class="dates">{"".join(parts)}{byline}{tags}</p>'

    # ----- bylines --------------------------------------------------------------------
    # Every article names who drafted it (sitegen/content.py): a person (author), or, for an
    # article the site's drafting software wrote, its automated byline (agent, an id from
    # content/site.json "agents", such as "daily" for verifiable.pro Wire), and maybe the
    # person who submitted the story (submitted_by). Bylines follow wire-service style: an
    # automated byline gives its name without "By" and an "Automated" tag, and a person's
    # reads "By <name>". The article page gives the whole byline; a list row, a short mark.
    def agent_of(self, a_obj):
        """The registry entry of the article's automated byline, or None when a person wrote
        it."""
        return self.m["site"].get("agents", {}).get(getattr(a_obj, "agent", "") or "")

    def byline_name(self, a_obj):
        """The name a byline gives: the automated byline's, in the page's language, or the
        author's."""
        agent = self.agent_of(a_obj)
        return self.t(agent["name"]) if agent else " ".join(str(getattr(a_obj, "author", "") or "").split())

    def name_in(self, key, name):
        """The interface string KEY with its {name} filled in: escaped, and the name in its
        own language, so an English name on a Chinese page is read in an English voice."""
        before, _, after = self.s(key).partition("{name}")
        return f"{esc(before)}{self.island(name)}{esc(after)}"

    def byline(self, a_obj):
        """The article page's byline. An automated article: the byline's name, such as
        "verifiable.pro Wire", then a dot and the "Automated" tag, which links to About's #ai
        and carries the byline's description as its tooltip (and as its description for
        screen readers). A person's: "By <name>". Either way "Submitted by <name>" follows,
        after a dot, when someone submitted the story."""
        agent = self.agent_of(a_obj)
        name = self.byline_name(a_obj)
        # a no-break space keeps each dot at the end of a line, never at the start of the next
        sep = '&nbsp;<span class="byline-sep" aria-hidden="true">·</span> '
        if agent:
            parts = [f'<span class="byline-by">{self.island(name)}</span>', sep,
                     self.a(self.loc("/about/") + "#ai", esc(self.s("byline_agent")), "byline-tag",
                            extra=f' title="{esc(self.t(agent["description"]))}"')]
        else:
            parts = [f'<span class="byline-by">{self.name_in("byline_by", name)}</span>']
        submitted = " ".join(str(getattr(a_obj, "submitted_by", "") or "").split())
        if submitted:
            parts.append(f'{sep}<span class="byline-submitted">{self.name_in("byline_submitted", submitted)}</span>')
        return f'<p class="byline">{"".join(parts)}</p>'

    def byline_mark(self, a_obj):
        """A list row's byline, omitted on the home page. An automated article: the byline's
        name, such as "verifiable.pro Wire", whose tooltip gives its description; it adds no tab
        stop, and screen readers hear a sentence that also says the byline is automated. A
        person's: "By <name>"."""
        if self.current == self.loc("/"):
            return ""
        agent = self.agent_of(a_obj)
        name = self.byline_name(a_obj)
        if agent is None:
            return f'<span class="byline-mark">{self.name_in("byline_by", name)}</span>' if name else ""
        return (f'<span class="byline-mark is-agent" aria-hidden="true" title="{esc(self.t(agent["description"]))}">'
                f'{self.island(name)}</span>'
                f'<span class="vh">{esc(self.s("byline_agent_vh", name=name))}</span>')

    def topic_chips(self, ids):
        return "".join(self.a(self.loc(f"/topics/{t}/"), esc(self.topic_name(t)), "chip", extra=f' data-topic="{t}"')
                       for t in ids if t in self.topics)

    def evidence_label(self, kind):
        key = "evidence_" + kind
        return self.s(key) if key in self.m["strings"][self.lang] else kind

    def evidence_chips(self, a_obj):
        return "".join(f'<span class="chip chip-evidence">{esc(self.evidence_label(e))}</span>' for e in a_obj.evidence)

    def checked_line(self, a_obj, limit=200):
        """The first sentence of the article's "What we checked" callout, as plain text."""
        m = CHECKED_RE.search(a_obj.body)
        if not m:
            return ""
        text = re.sub(r"\[\^[^\]]*\]", "", m.group(1))  # citations link to #source-n, which exists only on the article page
        text = re.sub(r"(?<=[　-鿿＀-￯])[ \t]*\n[ \t]*(?=[　-鿿＀-￯])", "", text)
        text = " ".join(plain(text).split())
        first = SENTENCE_END_RE.split(text, maxsplit=1)[0].strip()
        if len(first) <= limit:
            return first
        cut = first[:limit]
        if " " in cut[-40:]:  # end on a word boundary when there is one nearby
            cut = cut.rsplit(" ", 1)[0]
        return cut.rstrip(" ,;:，；：") + "…"

    def block_head(self, title, link=None, link_label="", hid=None, tag="h2"):
        hid_attr = f' id="{hid}"' if hid else ""
        more = self.a(link, f'{esc(link_label)}{ARROW}', "block-more") if link else ""
        return f'<div class="block-head"><{tag} class="block-title"{hid_attr}>{esc(title)}</{tag}>{more}</div>'

    def story_card(self, a_obj, dek=True, cls="card", thumb=False):
        """A text card: kicker, title, dek and byline mark. With thumb, a story that has a
        lead image shows it on top of the card (a decorative copy: see thumb())."""
        dek_html = f'<p class="card-dek">{esc(a_obj.dek)}</p>' if dek else ""
        mark = self.byline_mark(a_obj)
        mark_html = f'<p class="card-meta">{mark}</p>' if mark else ""
        pic = self.thumb(a_obj, "card-thumb") if thumb else ""
        cls += " has-thumb" if pic else ""
        return (
            f'<article class="{cls}" data-kind="{a_obj.kind}">{pic}<div class="card-body">'
            f'{self.kicker(a_obj, with_topic=False)}'
            f'<h3 class="card-title">{self.a(self.article_url(a_obj), esc(a_obj.title))}</h3>{dek_html}{mark_html}</div></article>'
        )

    # ----- lead images ----------------------------------------------------------------
    # An article's lead image comes from its illustration.json (sitegen/content.py). The
    # article page shows it as a captioned figure under the head, with its real alt text;
    # the home page's lead brief, the rail, Latest, the topic pages, the TEE hub and the
    # related cards show a copy beside or above the story's title link, which already
    # names the story, so the copy is decorative there: alt="", inside a link that is
    # hidden from screen readers and takes no tab stop.
    def lead_img(self, image, cls, alt="", eager=False, sizes=FIGURE_SIZES):
        """An <img> of a lead image that reserves its box before it loads. eager: the article
        page's figure, which is near the top of the page; lists load their copies lazily
        (below the fold, as on the home page, under its hero). A photo also offers its 400 and
        800 px copies and its full-size file in srcset, smallest first, with SIZES, the width it
        takes on the page, so a browser loads the smallest file that is wide enough for that
        width on its screen. src, for a browser without srcset, is the 800 px copy in a list and
        the full-size file in the figure."""
        loading = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
        shown, srcset = image, ""
        variants = getattr(image, "variants", {})
        copies = [variants[name] for name in reversed(content.PHOTO_SRCSET) if name in variants]
        if copies:
            shown = image if eager else variants.get("list", copies[-1])
            candidates = ", ".join(f"{self.href(f.src)} {f.width}w" for f in copies + [image])
            srcset = f' srcset="{esc(candidates)}" sizes="{esc(sizes)}"'
        return (f'<img class="{cls}" src="{esc(self.href(shown.src))}"{srcset} width="{shown.width}" '
                f'height="{shown.height}" alt="{esc(alt)}" {loading} decoding="async">')

    def thumb(self, a_obj, cls, sizes=None):
        """A story's lead image as a decorative link to the story, or "" without one. SIZES
        overrides the class's width (THUMB_SIZES) where the same list is narrower."""
        image = getattr(a_obj, "lead_image", None)
        if image is None:
            return ""
        img = self.lead_img(image, "story-thumb-img", sizes=sizes or THUMB_SIZES.get(cls, FIGURE_SIZES))
        return (f'<a class="story-thumb {cls}" href="{esc(self.href(self.article_url(a_obj)))}" tabindex="-1" '
                f'aria-hidden="true" data-image-kind="{esc(image.kind)}">{img}</a>')

    def lead_credit(self, image):
        """The figure's credit line. An illustration: drawn by code from its published scene
        description (linked), then a link to About's section on how the site makes them. A
        photo: its credit, its license (linked) and its source (linked), then, where the
        license asks that changes be indicated (CC BY and CC BY-SA), how tools/photos.py
        changed it: cropped (unless its crop is the whole source) and colour-adjusted."""
        if image.kind == "photo":
            # the credit names a person or an agency, so it keeps its own language (lang)
            before, _, after = self.s("lead_photo_credit").partition("{credit}")
            parts = [f"{esc(before)}{self.island(self.t(image.credit))}{esc(after)}"]
            # a license's name stays as written ("CC BY 4.0"); "Public domain" describes a status
            # rather than naming a license, so it takes the page's language (公有领域)
            license_name = self.t(image.license)
            if license_name.strip().lower() == "public domain":
                license_name = self.s("lead_photo_public_domain")
            parts.append(self.ext(image.license_url, license_name, cls="lead-credit-link"))
            parts.append(self.ext(image.source_url, self.s("lead_photo_source"), cls="lead-credit-link"))
            if getattr(image, "note_changes", False):
                parts.append(esc(self.s("lead_photo_edited" if image.cropped else "lead_photo_graded")))
            return " · ".join(parts)
        before, _, after = self.s("lead_credit").partition("{spec}")
        spec = (f'<a class="lead-credit-link" href="{esc(self.href(image.spec_path))}" type="application/json">'
                f'{esc(self.s("lead_credit_spec"))}</a>')
        how = self.a(self.loc("/about/") + "#illustrations", esc(self.s("lead_credit_how")), "lead-credit-link")
        return self.join_sentences([f"{esc(before)}{spec}{esc(after)}", how])

    def lead_figure(self, a_obj):
        """The article page's lead figure, right after the head: the image, linked to the
        full-size file, with its alt text; then the caption and the credit line."""
        image = getattr(a_obj, "lead_image", None)
        if image is None:
            return ""
        img = self.lead_img(image, "lead-figure-img", alt=self.t(image.alt), eager=True, sizes=FIGURE_SIZES)
        return (f'<figure class="lead-figure" data-image-kind="{esc(image.kind)}">'
                f'<a class="lead-figure-link" href="{esc(self.href(image.src))}">{img}</a>'
                f'<figcaption><span class="lead-caption">{esc(self.t(image.caption))}</span> '
                f'<span class="lead-credit">{self.lead_credit(image)}</span></figcaption></figure>')

    def brief_meta(self, a_obj):
        """A list row's meta line, then the story tags. A news brief shows the date on its
        primary source and the first publisher; any other story its filing date and kind,
        since its sources are not its publisher. The byline mark follows."""
        if a_obj.kind == "news":
            when = a_obj.event_date or a_obj.published
            pub = a_obj.sources[0]["publisher"] if a_obj.sources else ""
            label = f' · <span{self.lang_attr(pub)}>{esc(pub)}</span>' if pub else ""
        else:
            when, label = a_obj.published, " · " + esc(self.kind_label(a_obj.kind))
        tags = self.tags(a_obj)
        mark = self.byline_mark(a_obj)
        return time_tag(when, self.lang) + label + (" · " + mark if mark else "") + (" " + tags if tags else "")

    def brief_rows(self, stories, level=3, thumbs=False):
        """Compact text rows: the title, then the meta line with date, source and tags.
        With thumbs, a story with a lead image shows a small copy of it beside the text."""
        rows = []
        for a_obj in stories:
            pic = self.thumb(a_obj, "brief-thumb") if thumbs else ""
            cls = "brief-row has-thumb" if pic else "brief-row"
            rows.append(f'<li class="{cls}">{pic}<h{level}>{self.a(self.article_url(a_obj), esc(a_obj.title))}</h{level}>'
                        f'<p>{self.brief_meta(a_obj)}</p></li>')
        return "".join(rows)

    def river_row(self, a_obj, with_topic=True, dates=False, sizes=None):
        """A row of a dated river (Latest, the TEE hub, topic pages). News rows on
        Latest carry their dates line with the tags; other rows put the tags in a
        line under the dek. The byline mark comes before the tags. A story with a lead
        image shows a copy of it in a column beside the text (above it on phones); other
        rows keep to text. SIZES: the picture's width in a narrower river (thumb())."""
        tags = self.tags(a_obj)
        mark = self.byline_mark(a_obj)
        if dates and a_obj.kind == "news":
            meta = self.dates_line(a_obj, compact=True, tags=tags, byline=mark and f'<span class="date-item">{mark}</span>')
        else:
            meta = f'<p class="river-meta">{" ".join(x for x in (mark, tags) if x)}</p>' if mark or tags else ""
        layers = " ".join(self.layers_of(a_obj))
        pic = self.thumb(a_obj, "river-thumb", sizes)
        cls = "river-item has-thumb" if pic else "river-item"
        return (
            f'<li class="{cls}" data-kind="{a_obj.kind}" data-tee="{1 if self.is_tee(a_obj) else 0}" data-layers="{esc(layers)}">'
            f'<div class="river-date">{time_tag(a_obj.published, self.lang)}</div>'
            f'<div class="river-body">{self.kicker(a_obj, with_topic=with_topic)}'
            f'<h3 class="river-title">{self.a(self.article_url(a_obj), esc(a_obj.title))}</h3>'
            f'<p class="river-dek">{esc(a_obj.dek)}</p>{meta}</div>{pic}</li>'
        )

    def page_head(self, kicker, title, dek, crumbs, cls="page-head", extra=""):
        self.crumbs = list(crumbs)  # layout() turns the trail into the page's BreadcrumbList
        crumb_html = "".join(f"<li>{self.a(p, esc(t))}</li>" for p, t in crumbs)
        kick = f'<p class="kicker"><span class="kind">{esc(kicker)}</span></p>' if kicker else ""
        return f"""<nav class="breadcrumb" aria-label="{esc(self.s('breadcrumb'))}"><ol>{crumb_html}<li aria-current="page">{esc(title)}</li></ol></nav>
<header class="{cls}">{kick}<h1 class="page-title">{esc(title)}</h1><p class="page-dek">{esc(dek)}</p>{extra}</header>"""

    # ----- the hero -----------------------------------------------------------
    def hero(self, articles=()):
        """The home page hero, in the order a phone reads it: the pause control that
        static/hero.js runs and the "Check all layers" button that takes its place until
        every layer is checked, first so that they come first in the tab order; the
        stage, with the inline SVG scene titled in the page language, the leader lines,
        the label of the person in the scene with the count of layers checked, the hint
        on how to open a layer card, the note that the logos and names are examples (for
        screen readers only), the seven layer rows with their cards (hero_layers) and the
        legend of the chain; then the two links to the Stack page, and the tooltip in
        which hero.js shows a vendor mark's name. The figure has no caption: what the
        scene shows is in its description, and the layers' scheme is on the Stack page.
        The button, the count and the hint ship hidden until hero.js runs. The hint is
        the stage's own child, after the person's label rather than in it, so that from
        45em the stylesheet can stand it under the label column, beside that label; it
        holds a line for each way of opening a layer, twice: as it reads until every layer
        is checked, and after. The
        figure tells the scene how each binding holds (data-hv-chain) and whether to draw
        that at rest (data-hv-rest), and hands the layout's percentages to the
        stylesheet; it ships with data-hv-wait, under which the scene grays you from the
        first paint where scripts run, until hero.js counts (or the page's guard finds
        that it never will). The scene's description says what the still scene shows,
        which is all a page without the script has; its data-hv-live holds the sentences
        on the gray and the data, which hero.js adds once it has set the figure up.
        ARTICLES gives the cards' story counts. "" when build.py set no scene."""
        if not self.hero_svg:
            return ""
        L = self.loc
        gap = "" if self.lang == "zh" else " "  # Chinese sets no space after a full stop
        svg = (self.hero_svg.strip().replace("{{SCENE_TITLE}}", esc(self.s("hero_scene_title")))
               .replace("{{SCENE_DESC}}", esc(self.s("hero_scene_desc")))
               .replace("{{SCENE_DESC_LIVE}}", esc(gap + self.s("hero_scene_desc_live"))))
        leaders, labels = self.hero_layers(articles)
        segments, runs = self.hero_chain()
        chain = " ".join(f"{k}:{status}" for k, status in segments)
        # --hero-shift: how far a card starts left of the label column, in percent of the stage
        style = (f"--hero-art:{HERO_ART:g}%;--hero-labels:{HERO_LABELS:g}%;--hero-card:{HERO_CARD:g}%;"
                 f"--hero-shift:{HERO_LABELS - HERO_CARD:g}")
        if self.hero_anchors:  # the scene's height per unit of stage width, for the viewport-height cap
            _, _, width, height = self.hero_anchors["viewBox"]
            style += f";--hero-ratio:{round(HERO_ART / 100 * height / width, 4):g}"
        pause, play = esc(self.s("motion_pause")), esc(self.s("motion_play"))
        icon = f'<svg class="hero-person-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{PERSON_ICON}</svg>'
        # the reader's progress through the layers, on the person's name line: hero.js shows it and
        # counts in its text from data-progress ({n} is the count) and data-done, announced politely;
        # it can take focus from the script (tabindex -1), for when "Check all layers" goes
        total = len(self.stack())
        counted = self.s("hero_progress", n="{n}", total=total)
        status = (f'<p class="hero-progress" role="status" tabindex="-1" hidden data-progress="{esc(counted)}" '
                  f'data-done="{esc(self.s("hero_progress_done", total=total))}">{esc(counted.replace("{n}", "0"))}</p>')
        # A visual celebration, revealed only on completion. The progress status already
        # announces all layers checked, so this repeats no announcement for screen readers.
        complete = f'<span class="hero-complete" aria-hidden="true" hidden>{esc(self.s("hero_complete"))}</span>'
        person = (f'<div class="hero-person"><div class="hero-person-head"><p class="hero-person-name">{icon}'
                  f'{esc(self.s("hero_person"))}</p>{status}</div>'
                  f'<p class="hero-person-who">{esc(self.s("hero_person_who"))}{gap}{complete}</p></div>')
        # the button that checks every layer at once, in the pause control's place at the figure's
        # top right until every layer is checked (hero.js shows it)
        check_all = f'<button class="hero-all" type="button" hidden>{esc(self.s("hero_check_all"))}</button>'
        # the hint says how to open a card, so it ships hidden until hero.js can open one: a line for
        # each input, until every layer is checked (hero-hint-todo) and after (hero-hint-done)
        def hint_lines(suffix):
            return "".join(f'<span class="hero-hint-{mode}">{esc(self.s(key + suffix))}</span>' for mode, key in HERO_HINTS)
        hint = (f'<p class="hero-hint" hidden><span class="hero-hint-todo">{hint_lines("")}</span>'
                f'<span class="hero-hint-done">{hint_lines("_done")}</span></p>')
        # the labels show real companies' and bodies' marks and names: screen readers hear that they
        # are examples, not endorsements, right before the list (About says so for everyone)
        note = f'<p class="vh" id="hero-layers-note">{esc(self.s("hero_layers_note"))}</p>' if labels else ""
        links = (self.a(L("/topics/"), esc(self.s("stack_more")) + ARROW) + " "
                 + self.a(L("/topics/") + "#tiers", esc(self.s("stack_compare")) + ARROW))
        # the name of the vendor mark that a mouse or pen rests on, or a tap touches: one tooltip for
        # the figure, which hero.js fills, shows and places; aria-hidden, since every mark it names is
        # named for screen readers already (hero_examples)
        tip = '<span class="hero-tip" aria-hidden="true" hidden></span>' if labels else ""
        return f"""<figure class="hero-visual" data-verification-visual data-hv-wait data-hv-chain="{esc(chain)}" data-hv-rest="{esc(HERO_CHAIN_REST)}" style="{style}">
  <button class="verification-motion" type="button" data-motion-toggle data-label-pause="{pause}" data-label-play="{play}" aria-label="{pause}" hidden>{ICON_PAUSE}{ICON_PLAY}<span data-motion-label>{pause}</span></button>
  <span class="verification-static-label">{esc(self.s("motion_static"))}</span>
  {check_all}
  <div class="hero-stage">
    <div class="hero-art">{svg}</div>
    {leaders}
    {person}
    {hint}
    {note}
    {labels}
    {self.hero_chain_legend(runs)}
  </div>
  <p class="hero-links">{links}</p>
  {tip}
</figure>"""

    def hero_layers(self, articles=()):
        """The hero's layer labels as (leader lines, list). One row per stack layer, T7
        first, set at the height of its plate: the layer's icon, its code and short name
        ("T7 Policy", read as "T7, Policy") linked to the layer on the Stack page, the TEE
        label where a TEE gives direct evidence, the mark that the reader has checked the
        layer (shown once hero.js marks the row .is-checked) and the chevron that opens
        the row's card on touch screens and phones (hidden until hero.js runs); then the
        examples from the layer's "hero" block, the "Who checks" line that phones show
        at rest, and the layer card (hero_card). The head line, whose width the name
        link's target spans, is the name area that opens the layer for a pointer; the
        examples open nothing (static/hero.js). The name
        link is described by the card's claim and "Who checks" line, so screen readers
        hear them wherever the card is not shown. A leader line runs from each plate's
        anchor to its row; the anchors are in the scene's units, counted from its
        viewBox's corner. From 45em the rows stand in a column beside the scene, and a
        card opens below its label in the upper half of the stage (data-place="down")
        and above it in the lower half; below 45em the rows are a plain list. ("", "")
        without anchors."""
        anchors = self.hero_anchors
        if not anchors:
            return "", ""
        x0, y0, width, height = anchors["viewBox"]
        at = {a["layer"]: a for a in anchors["anchors"]}
        stack = self.stack()
        end, bend = HERO_LABELS - 0.9, HERO_LABELS - 2.6
        lines, rows = [], []
        for i, layer in enumerate(stack):
            n = len(stack) - i  # the layer's code: T7 first
            lid = esc(layer["id"])
            anchor = at[n]
            ax, ay = (anchor["x"] - x0) / width * HERO_ART, (anchor["y"] - y0) / height * 100
            ly = (anchor.get("label_y", anchor["y"]) - y0) / height * 100
            # the board sits below the plates' rhythm, so its leader elbows up to its label
            points = [(ax, ay), (end, ay)] if ly == ay else [(ax, ay), (bend, ay), (bend, ly), (end, ly)]
            tee = layer["tee"]["reach"] == "direct"
            cls = " is-tee" if tee else ""
            lines.append(f'<g class="hero-leader{cls}"><polyline points="{" ".join(f"{x:.2f},{y:.2f}" for x, y in points)}"/>'
                         f'<path class="hero-leader-dot" d="M{ax:.2f} {ay:.2f}h0"/></g>')
            hero = layer["hero"]
            short = self.t(hero["short"])
            icon = (f'<svg class="hero-layer-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">'
                    f'{LAYER_ICONS[hero["icon"]]}</svg>')
            link = self.a(self.loc("/topics/") + "#layer-" + layer["id"], self.hero_code(n, "hero-layer-code") + esc(short),
                          cls="hero-layer-link", extra=f' aria-describedby="hero-card-{lid}-claim hero-card-{lid}-who"')
            tag = ""
            if tee:
                what = self.s("hero_tee_vh")
                tag = (f'<span class="tag tag-tee" aria-hidden="true" title="{esc(what)}">{esc(self.s("tag_tee"))}</span>'
                       f'<span class="vh"> {esc(what)}</span>')
            more = (f'<button class="hero-more" type="button" aria-expanded="false" aria-controls="hero-card-{lid}" hidden>'
                    f'{ICON_MORE}<span class="vh">{esc(self.s("hero_more", name=short))}</span></button>')
            # the mark that a layer has been checked, shown once hero.js marks the row .is-checked
            tick = (f'<span class="hero-tick">{ICON_TICK}<span class="vh">{esc(self.s("hero_checked"))}</span></span>')
            who = (f'<p class="hero-who-line"><span class="hero-who-label">{self.colon("checkers_label")}</span>'
                   f'{self.island(self.t(layer["checkers"]))}</p>')
            rows.append(f'<li class="hero-layer{cls}" id="hero-layer-{lid}" data-n="{n}" data-layer="{lid}" '
                        f'data-place="{"up" if ly >= 50 else "down"}" style="--ly:{ly:.2f}%">'
                        f'<span class="hero-layer-head">{icon}{link}{tag}{tick}{more}</span>'
                        f'<span class="hero-examples">{self.hero_examples(hero["examples"])}</span>'
                        f'{who}{self.hero_card(layer, n, articles)}</li>')
        leaders = ('<svg class="hero-leaders" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true" '
                   f'focusable="false">{"".join(lines)}</svg>')
        return leaders, f'<ol class="hero-layers" aria-label="{esc(self.s("hero_layers_label"))}">{"".join(rows)}</ol>'

    def hero_code(self, n, cls):
        """Layer N's code in a span of class CLS, followed by the separator that screen readers
        hear before the name and that the page does not show (hero_code_sep): "T5" and the name
        read as "T5, Agents" (T5，智能体). The stylesheet sets the code a little apart from the name."""
        return f'<span class="{cls}">T{n}</span><span class="vh">{esc(self.s("hero_code_sep"))}</span>'

    def hero_card(self, layer, n, articles):
        """The layer card of layer N, inside its row, kept to what a reader takes in at a
        glance: the code and full name, the claim, who outside the provider checks it,
        and, on the layers where a TEE gives direct evidence, what it shows there; on
        touch screens only, the names of the examples in the label (the stylesheet shows
        them where no pointer can rest on a mark to see its name; screen readers hear
        each mark's own name, so the line is aria-hidden); then the layer's stories,
        linked to that view of Latest (the card's one link). The binding to the layer
        below and the other kinds of evidence stay on the Stack page. The cue "To the
        Stack page" is for sighted readers: hero.js follows the row's name link when the
        card is clicked. No heading, so the page outline stays the h1, then "Latest news"."""
        lid = esc(layer["id"])
        tee = layer["tee"]
        who_icon = f'<svg class="hc-who-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">{PERSON_ICON}</svg>'
        parts = [
            f'<p class="hc-head">{self.hero_code(n, "hc-code")}'
            f'<span class="hc-name">{self.island(self.t(layer["name"]))}</span></p>',
            f'<p class="hc-claim" id="hero-card-{lid}-claim"><span class="vh">{self.colon("stack_claim")}</span>'
            f'{self.island(self.t(layer["claim"]))}</p>',
            f'<p class="hc-who" id="hero-card-{lid}-who">{who_icon}<span class="hc-label">{self.colon("checkers_label")}</span>'
            f'{self.island(self.t(layer["checkers"]))}</p>',
        ]
        if tee["reach"] == "direct":
            parts.append(f'<p class="hc-tee" data-reach="direct"><span class="hc-label">{self.colon("stack_with_tee")}</span>'
                         f'{self.island(self.t(tee["short"]))}</p>')
        names = self.s("list_comma").join(self.island(self.hero_example_name(e)) for e in layer["hero"]["examples"])
        parts.append(f'<p class="hc-names" aria-hidden="true"><span class="hc-label">{self.colon("hero_card_examples")}</span>'
                     f'{names}</p>')
        stories, n_tee = self.layer_stories(articles, layer["id"])
        count = (self.a(self.loc("/latest/") + f"#t{n}", esc(self.cover_label(stories, n_tee)), "hc-count") if stories
                 else f'<span class="hc-count">{esc(self.s("hero_card_none"))}</span>')
        cue = f'<span class="hc-open" aria-hidden="true">{esc(self.s("hero_card_open"))} →</span>'
        parts.append(f'<p class="hc-foot">{count}{cue}</p>')
        return f'<div class="hero-card" id="hero-card-{lid}">{"".join(parts)}</div>'

    def hero_chain(self):
        """The evidence chain as the hero draws it, from the stack's bind.status, as
        (segments, runs). Segment k is layer k's binding to layer k - 1, the chain from
        ring k - 1 up to ring k, so the segments run bottom up from 2: [(2, "deployed"),
        ..., (7, "missing")]. The runs merge consecutive segments of one status into
        (status, lo, hi), the chain from layer lo up to layer hi, such as ("emerging", 2, 6)."""
        stack = self.stack()
        segments = [(len(stack) - i, layer["bind"]["status"]) for i, layer in enumerate(stack) if layer.get("bind")][::-1]
        runs = []
        for k, status in segments:
            if runs and runs[-1][0] == status and runs[-1][2] == k - 1:
                runs[-1] = (status, runs[-1][1], k)
            else:
                runs.append((status, k - 1, k))
        return segments, runs

    def hero_chain_legend(self, runs):
        """The legend beside the board, always in view: the chain of evidence today, one
        line per run of one status (a sample of the line, the status and the layers the
        run spans). What a break means is on the Stack page, under its table."""
        if not runs:
            return ""
        items = "".join(
            f'<li data-bind="{esc(status)}"><svg class="hero-chain-sample" viewBox="0 0 28 4" aria-hidden="true" '
            f'focusable="false">{HERO_CHAIN_SAMPLES[status]}</svg>'
            f'<span class="hero-chain-status">{esc(self.s("bind_" + status))}</span>'
            f'<span class="hero-sep" aria-hidden="true"> · </span><span class="vh">{esc(self.s("label_colon"))}</span>'
            f'{esc(self.s("hero_chain_run", lo=f"T{lo}", hi=f"T{hi}"))}</li>'
            for status, lo, hi in runs
        )
        return (f'<div class="hero-chain"><p class="hero-chain-title">{esc(self.s("hero_chain_title"))}</p>'
                f'<ul class="hero-chain-runs">{items}</ul></div>')

    def hero_examples(self, examples):
        """A label's examples, separated by middle dots: a vendor mark (sitegen/logos.py),
        a name, or a mark followed by a name. A mark is named for screen readers (role
        "img" and aria-label) unless the name beside it already says it, as "Hugging Face"
        does; static/hero.js shows that name in a tooltip over the mark that a mouse or pen
        rests on, or a tap touches. The mark carries no <title>, whose own tooltip from the
        browser would show beside it."""
        parts = []
        for example in examples:
            text = self.t(example.get("text"))
            mark = ""
            if example.get("logo"):
                logo = LOGOS[example["logo"]]
                title = self.hero_mark_name(example)
                x, y, w, h = logo["box"]
                size = logo["height"]
                if text.startswith(title):
                    named = 'aria-hidden="true"'
                else:
                    named = f'role="img" aria-label="{esc(title)}"{self.lang_attr(title)}'
                light, dark = logo["color"]
                # a Simple Icons mark is one path; a Lobe Icons mark is several, even-odd filled
                if "paths" in logo:
                    shape = "".join(f'<path d="{d}"' + (f' fill-opacity="{o:g}"' if o is not None else "") + "/>"
                                    for d, o in logo["paths"])
                else:
                    shape = f'<path d="{logo["path"]}"/>'
                rule = f' fill-rule="{logo["rule"]}"' if logo.get("rule") else ""
                mark = (f'<svg class="hero-logo" viewBox="{x:g} {y:g} {w:g} {h:g}" {named} focusable="false"{rule} '
                        f'style="height:{size:g}rem;width:{size * w / h:.2f}rem;--logo:{light};--logo-dark:{dark}">'
                        f'{shape}</svg>')
            parts.append(f'<span class="hero-ex">{mark}{self.island(text) if text else ""}</span>')
        return '<span class="hero-sep" aria-hidden="true">·</span>'.join(parts)

    def hero_example_name(self, example):
        """What one example in a layer's label names, as a screen reader hears it there: its
        text, its mark's name, or the mark's name followed by the text ("European Union AI
        Act", 欧盟 AI Act); a mark whose text starts with its name gives the text alone."""
        text = self.t(example.get("text"))
        if not example.get("logo"):
            return text
        title = self.hero_mark_name(example)
        return text if text and text.startswith(title) else " ".join(part for part in (title, text) if part)

    def hero_mark_name(self, example):
        """The name of an example's vendor mark in the page language: the example's "name", else
        the mark's own title in sitegen/logos.py, one string for both languages or an {en, zh}
        pair (the European Union's mark is 欧盟 on Chinese pages)."""
        return self.t(example.get("name")) or self.t(LOGOS[example["logo"]]["title"])

    # ----- the verification stack -----------------------------------------------
    def stack_block(self, articles):
        """The Stack page's seven-layer table (#layers), T7 at the top. Every row shows its
        code, name, claim, who outside the provider can check that claim, the short TEE
        line, the binding to the layer below, the topic chips and the story count; the TEE
        line in full, the other evidence and the newest brief fold into a <details> per
        row, so the table stays short. The home page carries no table: the hero's layer
        cards show each layer there and link here."""
        L = self.loc
        rows = []
        above = ""
        for layer in self.stack():
            lid = layer["id"]
            code = self.layer_code(lid)
            tee = layer["tee"]
            reach = tee["reach"]
            at, n_tee = self.layer_stories(articles, lid)
            short = self.t(tee["short"])
            bind = layer.get("bind")
            status = bind["status"] if bind else ""
            body = (f'<p class="layer-claim"><span class="layer-claim-label">{esc(self.s("stack_claim"))}</span>'
                    f'{esc(self.t(layer["claim"]))}</p>'
                    f'<p class="layer-checkers"><span class="layer-checkers-label">{esc(self.s("checkers_label"))}</span>'
                    f'{esc(self.t(layer["checkers"]))}</p>'
                    f'<p class="layer-tee"><span class="layer-tee-label">{esc(self.s("stack_with_tee"))}</span>'
                    f'<span class="layer-reach">{esc(self.s("reach_" + reach))}</span>{esc(short)}</p>')
            if bind:
                body += (f'<p class="layer-bind"><span class="layer-bind-label">{esc(self.s("bind_label"))}</span>'
                         f'<span class="bind-status bind-{status}">{esc(self.s("bind_" + status))}</span>'
                         f'{esc(self.t(bind["text"]))}</p>')
            folded = []
            text = self.t(tee.get("text"))
            if text and text != short:
                folded.append(f'<p class="layer-tee-text">{self.colon("stack_with_tee")}{esc(text)}</p>')
            left, right = ("（", "）") if self.lang == "zh" else (" (", ")")
            others = " · ".join(f'{self.tier_link(o["tier"])}{left}{esc(self.t(o["examples"]))}{right}'
                                for o in layer.get("others", []) if self.tier(o["tier"]))
            if others:
                folded.append(f'<p class="layer-others">{self.colon("stack_other")}{others}</p>')
            newest = next((a for a in at if a.kind == "news"), None)
            if newest:  # the date the development was announced, then the brief
                folded.append(f'<p class="layer-newest">{self.colon("stack_newest")}'
                              f'{time_tag(newest.event_date or newest.published, self.lang)} · '
                              f'{self.a(self.article_url(newest), esc(newest.title))}</p>')
            if folded:
                body += (f'<details class="layer-more"><summary>{esc(self.s("layer_more"))}</summary>'
                         f'{"".join(folded)}</details>')
            topics = f'<div class="layer-topics">{self.topic_chips(layer.get("topics", []))}</div>'
            label = self.cover_label(at, n_tee)
            count = self.a(L("/latest/") + "#" + code.lower(), esc(label)) if at else esc(label)
            cover = f'<p class="layer-count">{count}</p>'
            rows.append(
                f'<li class="layer-row" id="layer-{esc(lid)}" data-reach="{esc(reach)}" '
                f'data-bind="{esc(status or "none")}" data-bind-above="{esc(above or "none")}">'
                f'<div class="layer-head"><span class="layer-code">{code}</span>'
                f'<h3 class="layer-name">{esc(self.t(layer["name"]))}</h3></div>'
                f'<div class="layer-body">{body}</div>{topics}<div class="layer-cover">{cover}</div></li>'
            )
            above = status
        table = f'<ol class="layer-table">{"".join(rows)}</ol>'
        note = (f'<p class="chain-legend">{esc(self.s("chain_legend"))}</p>'
                f'<p class="tags-note">{esc(self.s("tags_note"))}</p>')
        return (f'<section class="stack-block" id="layers" aria-labelledby="layers-title">'
                f'{self.block_head(self.s("layers_title"), hid="layers-title")}'
                f'<p class="block-dek">{esc(self.s("layers_dek"))}</p>{table}{note}</section>')

    # ----- trust tiers --------------------------------------------------------
    def tier_row(self, tier):
        """One trust tier: the trust name hangs left; what a passing check establishes
        and what it does not stay open, and the other fields fold away."""
        L = self.loc
        tid = tier["id"]
        main = tier.get("focus") is not None  # the TEE tier: the site's main subject
        head = f'<p class="tier-main-label">{esc(self.s("tier_main"))}</p>' if main else ""
        head += (f'<h3 class="tier-title"><span class="tier-n">{esc(self.s("tier_n", n=tier["n"]))}</span>'
                 f'<span class="vh"> · </span><span class="tier-name">{esc(self.t(tier["trust_name"]))}</span></h3>'
                 f'<p class="tier-mech">{esc(self.t(tier["mechanism"]))}</p>')
        shown = self.field_list([("tier_establishes", tier["establishes"]), ("tier_not", tier["not_established"])], "tier-fields")
        compare = ("tier_focus", tier["focus"]) if main else ("tier_vs_tee", tier.get("vs_tee"))
        folded = self.field_list([("tier_trust", tier["trust"]), ("tier_hidden", tier["hidden"]), ("tier_cost", tier["cost"]),
                                  compare, ("tier_combined", tier.get("combined"))], "tier-fields")
        includes = f'<p class="tier-includes">{self.colon("tier_includes")}{esc(self.t(tier["approaches"]))}</p>'
        details = f'<details><summary>{esc(self.s("tier_more"))}</summary>{folded}{includes}</details>'
        reads = "".join(f"<li>{link}</li>" for link in (self.article_link(slug) for slug in tier.get("read", [])) if link)
        read = (f'<div class="tier-read"><p class="tier-read-label">{esc(self.s("tier_read"))}</p>'
                f'<ul class="tier-read-list">{reads}</ul></div>') if reads else ""
        hub = f'<p class="tier-hub">{self.a(L(HUB_PATH), esc(self.s("tee_block_more")) + ARROW)}</p>' if main else ""
        return (f'<article class="tier" id="tier-{esc(tid)}" data-tier="{esc(tid)}"><div class="tier-body">'
                f'{head}{shown}{details}{read}{hub}</div></article>')

    def tiers_section(self):
        """The Stack page's #tiers: the order note, the provider's word as an unnumbered
        baseline, the five tiers and the note on encryption-based approaches."""
        L = self.loc
        data = self.m["tiers"]
        base = data["baseline"]
        baseline = (f'<div class="tier-baseline" id="tier-baseline"><p class="baseline-label">{esc(self.s("baseline_label"))}</p>'
                    f'<h3>{esc(self.t(base["trust_name"]))}</h3><p>{esc(self.t(base["text"]))}</p></div>')
        rows = "".join(self.tier_row(tier) for tier in self.tiers())
        why = f'<p class="read-more">{self.a(L("/vision/") + "#compare", esc(self.s("tiers_why_link")) + ARROW)}</p>'
        return (f'<section class="tiers" id="tiers" aria-labelledby="tiers-title">'
                f'{self.block_head(self.s("tiers_title"), hid="tiers-title")}'
                f'<p class="tiers-note">{esc(self.t(data["order_note"]))}</p>{baseline}{rows}'
                f'<p class="tiers-he-note">{esc(self.t(data["he_note"]))}</p>{why}</section>')

    def tier_summary(self):
        """The order note and a three-column summary of the tiers (Vision's include)."""
        L = self.loc
        trust, vs = esc(self.s("tier_trust")), esc(self.s("tier_vs_tee"))
        rows = "".join(
            f'<tr data-tier="{esc(tier["id"])}"><th scope="row">'
            f'{self.a(L("/topics/") + "#tier-" + tier["id"], esc(self.s("tier_n", n=tier["n"]) + " · " + self.t(tier["mechanism"])))}'
            f'</th><td data-label="{trust}">{esc(self.t(tier["trust_name"]))}</td>'
            f'<td data-label="{vs}">{esc(self.t(tier["summary"]))}</td></tr>'
            for tier in self.tiers()
        )
        return (f'<p class="tiers-note">{esc(self.t(self.m["tiers"]["order_note"]))}</p>'
                f'<table class="tier-summary"><thead><tr><th scope="col">{esc(self.s("tier_col"))}</th>'
                f'<th scope="col">{trust}</th><th scope="col">{vs}</th></tr></thead><tbody>{rows}</tbody></table>')

    # ----- reading paths ------------------------------------------------------
    def path_list(self, mini=False, planned=True, level=3, marks=False, outcomes=True):
        """The TEE path from content/tee.json: numbered steps with kind, reading time, byline
        mark and what the reader can do afterwards; planned steps show their title only.
        mini: the compact text variant (the hub and the home page). outcomes=False leaves
        out what the reader can do afterwards, as the home page does: Learn and the hub
        say it."""
        items, n = [], 0
        after = self.s("path_after")
        for step in self.m["tee"]["path"]:
            if "article" in step:
                a_obj = self.find_article(step["article"])
                if a_obj is None:
                    continue
                n += 1
                kind = esc(f'{self.kind_label(a_obj.kind)} · {self.s("min_read", n=a_obj.minutes)}')
                mark = self.byline_mark(a_obj)
                outcome = self.t(step.get("outcome")) if outcomes else ""
                outcome_html = f'<p class="path-outcome">{esc(self.join_sentences([after, outcome]))}</p>' if outcome else ""
                slug = f' data-slug="{esc(a_obj.slug)}"' if marks else ""
                items.append(
                    f'<li class="path-step"{slug}><span class="path-n">{n}</span><div class="path-body">'
                    f'<p class="path-kind">{kind}{" · " + mark if mark else ""}</p>'
                    f'<h{level} class="path-title">{self.article_link(a_obj.slug)}</h{level}>{outcome_html}</div></li>'
                )
            elif planned:
                outcome = self.t(step.get("outcome"))
                outcome_html = f'<p class="path-outcome">{esc(outcome)}</p>' if outcome else ""
                items.append(
                    f'<li class="path-step is-planned"><div class="path-body">'
                    f'<h{level} class="path-title"><span class="path-planned">{esc(self.s("path_planned"))}</span> '
                    f'{esc(self.t(step["planned"]))}</h{level}>{outcome_html}</div></li>'
                )
        return f'<ol class="path{" path-mini" if mini else ""}">{"".join(items)}</ol>'

    def path_slugs(self):
        return {step["article"] for step in self.m.get("tee", {}).get("path", []) if "article" in step}

    def path_counted(self, key):
        """The interface string KEY with {n}, the number of the TEE path's published steps (the
        steps path_list numbers), written as a word: "Learn TEEs in five steps", "五步读懂 TEE".
        Publishing a planned step changes it."""
        n = sum(1 for step in self.m.get("tee", {}).get("path", [])
                if "article" in step and self.find_article(step["article"]) is not None)
        return self.s(key, n=discover.count_word(n, self.lang))

    # ----- pages --------------------------------------------------------------
    def home(self, articles):
        path = self.loc("/")
        self.current = path
        L = self.loc
        news = [a for a in articles if a.kind == "news"]
        lead = next((a for a in news if a.lead), news[0] if news else None)
        # The lead brief, then five more: from 960px they stand beside it and end about level
        # with it; below 960px, under it, site.css (22.3) shows only four
        rail = ([lead] if lead else []) + [a for a in news if a is not lead][:5]
        in_rail = {a.slug for a in rail}
        tee_news = [a for a in news if self.is_tee(a) and a.slug not in in_rail][:4]
        on_path = self.path_slugs()
        guides = [a for a in articles if a.kind == "guide" and a.slug not in on_path][:3]

        # The band: the intro (kicker and tagline, then the one-sentence positioning and
        # two links, in two wrappers that wide layouts set apart), then the hero.
        hero = self.hero(articles)
        links = (self.a(L("/vision/") + "#why-tees", esc(self.s("home_link_vision")) + ARROW)
                 + self.a(L("/learn/") + "#tee-path", esc(self.s("home_link_path")) + ARROW))
        band = f"""<section class="home-hero" aria-labelledby="home-title">
  <div class="home-intro">
    <div class="home-head"><p class="home-kicker">{esc(self.s('home_kicker'))}</p><h1 class="home-tagline" id="home-title">{esc(self.s('tagline'))}</h1></div>
    <div class="home-lede">
      <p class="home-positioning">{esc(self.s('home_lead'))}</p>
      <p class="home-links">{links}</p>
    </div>
  </div>
  {hero}
</section>"""
        # the rail's rows and the lead brief show their lead images, as decorative links
        # beside or above the title link (thumb())
        rows = []
        for a_obj in rail[1:]:
            pic = self.thumb(a_obj, "ledger-thumb")
            rows.append(f'<li class="ledger-row{" has-thumb" if pic else ""}">{pic}'
                        f'<h3 class="ledger-title">{self.a(self.article_url(a_obj), esc(a_obj.title))}</h3>'
                        f'<p class="ledger-dates">{self.brief_meta(a_obj)}</p></li>')
        rows = "".join(rows)
        lead_html = ""
        if rail:
            first = rail[0]
            pic = self.thumb(first, "news-lead-media")
            lead_html = (f'<article class="news-lead{" has-thumb" if pic else ""}">{pic}{self.kicker(first)}'
                         f'<h3 class="news-lead-title">{self.a(self.article_url(first), esc(first.title))}</h3>'
                         f'<p class="news-lead-dek">{esc(first.dek)}</p>'
                         f'<p class="ledger-dates">{self.brief_meta(first)}</p></article>')
        rail_list = f'<ol class="ledger">{rows}</ol>' if rows else ""
        news = f"""<section class="ledger-rail home-news" aria-labelledby="rail-title">
  {self.block_head(self.s('on_record'), L('/latest/') + '#news', self.s('all_briefs'), 'rail-title')}
  <div class="home-news-grid">{lead_html or f'<p class="empty">{esc(self.s("no_coverage"))}</p>'}{rail_list}</div>
</section>"""

        tee_rows = self.brief_rows(tee_news, level=4, thumbs=True)
        # the path's steps by title, kind and reading time: what each step lets the reader do is
        # on Learn and the TEE hub, so the home page leaves it out
        path_steps = self.path_list(mini=True, planned=False, level=4, outcomes=False)
        tee_block = f"""<section class="tee-block" aria-labelledby="tee-title">
  {self.block_head(self.s('tee_block_title'), L(HUB_PATH), self.s('tee_block_more'), 'tee-title')}
  <div class="tee-col"><h3 class="mini-title">{esc(self.s('tee_block_latest'))}</h3><ol class="tee-latest">{tee_rows}</ol></div>
  <div class="tee-col"><h3 class="mini-title">{esc(self.path_counted('tee_block_path'))}</h3>{path_steps}</div>
</section>"""

        # each guide by its title, step count and reading time: its dek is on Learn's
        # worksheet card and on the guide, so the home page leaves it out
        cards = []
        for a_obj in guides:
            meta = [esc(self.s("min_read", n=a_obj.minutes))]
            steps = self.steps_of(a_obj)
            if steps:
                meta.insert(0, esc(self.count("guide_steps", steps)))
            cards.append(
                f'<article class="card check-card" data-kind="guide"><div class="card-body">'
                f'<h3 class="card-title">{self.a(self.article_url(a_obj), esc(a_obj.title))}</h3>'
                f'<p class="card-meta">{" · ".join(m for m in meta if m)}</p></div></article>'
            )
        checks = ""
        if cards:
            checks = f"""<section class="checks-block" aria-labelledby="checks-title">
  {self.block_head(self.s('checks_title'), L('/latest/') + '#guide', self.s('all_guides'), 'checks-title')}
  <div class="card-row">{''.join(cards)}</div>
</section>"""

        body = f"""<div class="wrap home">
{band}
{news}
{tee_block}
{checks}
</div>"""
        # WebSite and Organization (sitegen/discover.py), which name the site by its domain; the home
        # pages carry no trail. Their title, which search results and link previews show, starts with
        # that name and says what the site covers (home_title)
        ld = [discover.website(self), discover.organization(self)]
        return path, self.layout(
            path=path, title=self.s("home_title"), description=self.s("site_description"), section="home",
            body=body, alt_path=self.loc("/", self.other()), page_class="page-home", jsonld=ld,
            hero_script=bool(hero),
        )

    def steps_of(self, a_obj):
        """A guide's numbered steps, counted in the English body."""
        en = next((a for a in self.m.get("articles", {}).get("en", []) if a.slug == a_obj.slug), a_obj)
        return guide_steps(en.body)

    def check_strip(self, a_obj=None):
        """A receipt of actions only this site offers: on the home page the feed,
        a command that recomputes every digest and the correction route; at the
        end of an article its digest, its source and how to correct it. GitHub
        links appear once content/site.json names repo_url."""
        L = self.loc
        site = self.m["site"]
        repo = self.repo()
        branch = site.get("repo_branch") or "main"
        rows = []
        if a_obj is None:
            cmd = f"python3 tools/verify_manifest.py {self.base_url}"
            rows.append(("check_feed", self.a(L("/feed.xml"), esc(self.s("feed_atom")))))
            rows.append(("check_verify",
                         f'<span class="hash-row"><code class="hash">{esc(cmd)}</code>'
                         f'<button type="button" class="copy-btn" data-copy="{esc(cmd)}" data-copied="{esc(self.s("record_copied"))}">{esc(self.s("record_copy"))}</button></span>'
                         f'<span class="check-how">{self.a(L("/about/") + "#integrity", esc(self.s("footer_how")))}</span>'))
        else:
            src = f"/articles/{a_obj.slug}/{a_obj.lang}.md"
        if repo:
            # "template" and "page" prefill the correction issue form; "body" is
            # the fallback when the repository has no such form
            page = self.base_url + (self.article_url(a_obj) if a_obj else L("/"))
            query = urllib.parse.urlencode({
                "template": "correction.yml",
                "title": ("[Correction] " + (a_obj.title if a_obj else ""))[:120],
                "page": page,
                "digest": a_obj.sha256 if a_obj else "",
                "body": f"Page: {page}\nSource SHA-256: {a_obj.sha256 if a_obj else '-'}\n\nSentence to fix:\n\nPrimary source:\n",
            })
            links = f'<a href="{esc(repo)}/issues/new?{esc(query)}" rel="noopener">{esc(self.s("check_issue"))}</a>'
            if a_obj:
                edit = f"{repo}/edit/{branch}/content/articles/{a_obj.slug}/{a_obj.lang}.md"
                links += f' · <a href="{esc(edit)}" rel="noopener">{esc(self.s("check_edit"))}</a>'
            links += " · " + self.a(L("/about/") + "#corrections", esc(self.s("check_policy")))
        else:
            links = (self.a(L("/about/") + "#corrections", esc(self.s("check_policy")))
                     + f' · <span class="email">{esc(site.get("contact_email", ""))}</span>')
        rows.append(("check_correct", links))
        dl = "".join(f'<div class="{k.replace("_", "-")}"><dt>{esc(self.s(k))}</dt><dd>{v}</dd></div>' for k, v in rows)
        title = self.s("check_title_page" if a_obj else "check_title")
        verify = ""
        if a_obj is not None:
            verify = (f'<details class="verify"><summary>{esc(self.s("record_title"))}</summary>'
                      f'<p class="record-note">{esc(self.s("record_text"))}</p>'
                      f'<p class="hash-row"><code class="hash">{esc(a_obj.sha256)}</code>'
                      f'<button type="button" class="copy-btn" data-copy="{esc(a_obj.sha256)}" data-copied="{esc(self.s("record_copied"))}">{esc(self.s("record_copy"))}</button></p>'
                      f'<p class="record-links">{self.a(src, esc(self.s("record_source")))} · {self.a("/manifest.json", esc(self.s("record_manifest")))}</p></details>')
        return (f'<section class="check-strip" aria-labelledby="check-title">'
                f'<h2 id="check-title" class="aside-title">{esc(title)}</h2><dl>{dl}</dl>{verify}</section>')

    def latest(self, articles):
        self.current = self.loc("/latest/")
        L = self.loc
        counts = {k: sum(1 for a in articles if a.kind == k) for k in KIND_ORDER}
        buttons = [f'<button type="button" class="filter-btn" data-filter="all" aria-pressed="true">{esc(self.s("filter_all"))} <span class="count">{len(articles)}</span></button>']
        for k in KIND_ORDER:
            off = "" if counts[k] else " disabled"
            buttons.append(f'<button type="button" class="filter-btn" id="{k}" data-filter="{k}" aria-pressed="false"{off}>{esc(self.s("kind_plural_" + k))} <span class="count">{counts[k]}</span></button>')
        # The TEE toggle and the layer select combine with the kind buttons;
        # #tee and #t1 ... #t7 open those views (site.js reads the hash)
        n_tee = sum(1 for a in articles if self.is_tee(a))
        buttons.append(f'<button type="button" class="filter-btn filter-tee" id="tee" data-toggle="tee" aria-pressed="false" '
                       f'title="{esc(self.s("filter_tee_aria"))}"{"" if n_tee else " disabled"}>{esc(self.s("filter_tee"))} '
                       f'<span class="count">{n_tee}</span></button>')
        options = "".join(
            f'<option value="{esc(layer["id"])}" data-code="{self.layer_code(layer["id"]).lower()}" '
            f'id="{self.layer_code(layer["id"]).lower()}">{esc(self.layer_code(layer["id"]) + " " + self.t(layer["name"]))}</option>'
            for layer in self.stack()
        )
        buttons.append(f'<label class="filter-layer">{esc(self.s("filter_layer"))} <select id="layer-filter" name="layer">'
                       f'<option value="">{esc(self.s("any_layer"))}</option>{options}</select></label>')
        groups, current, items = [], None, []
        for a_obj in articles:
            month = (a_obj.published.year, a_obj.published.month)
            if month != current:
                if items:
                    groups.append((current, items))
                current, items = month, []
            items.append(a_obj)
        if items:
            groups.append((current, items))
        group_html = []
        for (y, m), group in groups:
            rows = "".join(self.river_row(a_obj, dates=True) for a_obj in group)
            group_html.append(
                f'<section class="river-group"><h2 class="river-month" id="m-{y}-{m:02d}">{esc(fmt_month(dt.date(y, m, 1), self.lang))}</h2>'
                f'<ol class="river">{rows}</ol></section>'
            )
        body = f"""<div class="wrap">
{self.page_head(None, self.s('latest_title'), self.s('latest_dek'), [(L('/'), self.s('home'))])}
<div class="filter-bar" role="group" aria-label="{esc(self.s('filter_label'))}" data-filter-group="latest" hidden>{''.join(buttons)}</div>
<p class="tags-note">{esc(self.s('tags_note'))}</p>
<div class="river-groups" data-filter-target="latest">{''.join(group_html)}</div>
</div>"""
        path = L("/latest/")
        ld = discover.collection(self, path, self.s("latest_title"), self.s("latest_dek"), discover.article_items(self, articles))
        return path, self.layout(path=path, title=self.s("latest_title"), description=self.s("latest_dek"), section="latest",
                                 body=body, alt_path=self.loc("/latest/", self.other()), page_class="page-latest", jsonld=ld)

    def article(self, a_obj, articles, has_other):
        self.current = self.article_url(a_obj)
        L = self.loc
        crumbs = [(L("/"), self.s("home")), (L("/latest/"), self.s("latest_title"))]
        crumb_html = "".join(f"<li>{self.a(p, esc(t))}</li>" for p, t in crumbs)
        crumb_html += f'<li>{self.a(L("/latest/") + "#" + a_obj.kind, esc(self.kind_label(a_obj.kind, "kind_plural")))}</li>'
        meta_dates = []
        if a_obj.event_date and a_obj.kind == "news":
            meta_dates.append(f'<div><dt>{esc(self.s("announced"))}</dt><dd>{time_tag(a_obj.event_date, self.lang)}</dd></div>')
        meta_dates.append(f'<div><dt>{esc(self.s("published"))}</dt><dd>{time_tag(a_obj.published, self.lang)}</dd></div>')
        if self.revised(a_obj):
            meta_dates.append(f'<div><dt>{esc(self.s("updated"))}</dt><dd>{time_tag(a_obj.updated, self.lang)}</dd></div>')

        sources = ""
        if a_obj.sources:
            # titles and publishers keep their own language (mostly English on Chinese pages)
            items = "".join(
                f'<li id="source-{s["n"]}"><a href="{esc(s["url"])}" rel="noopener" class="ext"{self.lang_attr(s["title"])}>{esc(s["title"])}</a>'
                f'<span class="source-meta">{self.island(s["publisher"])} · {esc(source_date(s["date"], self.lang))}</span></li>'
                for s in a_obj.sources
            )
            sources = f'<section class="sources" aria-labelledby="sources-title"><h2 id="sources-title">{esc(self.s("sources_title"))}</h2><ol>{items}</ol></section>'

        toc = ""
        h2s = [h for h in a_obj.headings if h[0] == 2]
        if len(h2s) >= 3:
            toc_items = "".join(f'<li><a href="#{hid}">{esc(plain(text))}</a></li>' for _, text, hid in h2s)
            toc = f'<nav class="toc" aria-labelledby="toc-title"><h2 id="toc-title" class="aside-title">{esc(self.s("on_this_page"))}</h2><ol>{toc_items}</ol></nav>'

        source_path = f"/articles/{a_obj.slug}/{a_obj.lang}.md"
        translation_note = ""
        if a_obj.lang == "zh" and has_other:
            # hreflang names the target's language; the link text itself is Chinese, so no lang="en"
            original = self.a(self.article_url(a_obj, "en"), esc(self.s("read_original")), extra=' hreflang="en"')
            translation_note = f'<p class="translation-note">{esc(self.s("translated_from"))} {original}</p>'
        disclosure_body = disclosure_aside = ""
        if a_obj.disclosure:
            # links resolve like the body's; an untranslated (English) disclosure is marked as such
            text = md.render_inline(a_obj.disclosure, md.Context(resolve=self.md_link))
            dlang = getattr(a_obj, "disclosure_lang", a_obj.lang)
            p = f'<p lang="en">{text}</p>' if dlang != a_obj.lang else f"<p>{text}</p>"
            disclosure_body = (f'<aside class="callout callout-disclosure"><p class="callout-label">{esc(self.s("disclosure_title"))}</p>'
                               f'<div class="callout-body">{p}</div></aside>')
            disclosure_aside = (f'<section class="disclosure" aria-labelledby="disclosure-title"><h2 id="disclosure-title" class="aside-title">'
                                f'{esc(self.s("disclosure_title"))}</h2>{p}</section>')
        changes = ""
        if a_obj.changes:
            rows = "".join(f'<li>{time_tag(c["date"], self.lang)} <span>{esc(c["note"])}</span></li>' for c in a_obj.changes)
            changes = f'<section class="changes" aria-labelledby="changes-title"><h2 id="changes-title">{esc(self.s("changes_title"))}</h2><ol>{rows}</ol></section>'
        chat_aside = ""
        if self.chat_on():
            # hidden until chat.js runs; its button opens the assistant on this article
            chat_aside = (f'\n  <section class="chat-aside" data-chat-wrap hidden aria-labelledby="chat-aside-title">'
                          f'<h2 id="chat-aside-title" class="aside-title">{esc(self.s("chat_ask_article"))}</h2>'
                          f'<p>{esc(self.s("chat_aside_text"))}</p>'
                          f'<button type="button" class="chat-aside-btn" data-chat-open="article">{esc(self.s("chat_aside_btn"))}'
                          f' <span aria-hidden="true">→</span></button></section>')
        # Filing: the stack layers with their full names, and the TEE hub rows that cite this article
        filing = [f'<div><dt>{esc(self.s("doc_sources"))}</dt><dd>{esc(self.count("doc_sources_n", len(a_obj.sources)))}</dd></div>']
        layer_links = " ".join(
            self.a(L("/topics/") + f"#layer-{lid}", esc(f'{self.layer_code(lid)} {self.t(self.layer(lid)["name"])}'))
            for lid in self.layers_of(a_obj)
        )
        if layer_links:
            filing.append(f'<div class="dd-layers"><dt>{esc(self.s("doc_layers"))}</dt><dd>{layer_links}</dd></div>')
        tracked = [self.a(L(HUB_PATH) + "#" + anchor, self.island(name))
                   for anchor, name, refs in self.hub_trackers() if f"article:{a_obj.slug}" in refs]
        if tracked:
            filing.append(f'<div class="dd-tracked"><dt>{esc(self.s("tracked_in"))}</dt><dd>{esc(self.s("list_sep")).join(tracked)}</dd></div>')
        filing.append(f'<div class="dd-chips"><dt>{esc(self.s("doc_topics"))}</dt><dd>{self.topic_chips(a_obj.topics)}</dd></div>')
        details = f"""<aside class="doc-aside">
  <section class="doc-details" aria-labelledby="details-title">
    <h2 id="details-title" class="aside-title">{esc(self.s('doc_details'))}</h2>
    <dl>
      {''.join(filing)}
    </dl>
  </section>
{chat_aside}
  {disclosure_aside}
  {toc}
</aside>"""

        by_slug = {o.slug: o for o in articles}
        related = [by_slug[x] for x in a_obj.related if x in by_slug and by_slug[x] is not a_obj][:3]
        related += [o for o in articles if o is not a_obj and o not in related and a_obj.primary_topic in o.topics][: 3 - len(related)]
        if len(related) < 3:
            related += [o for o in articles if o is not a_obj and o not in related][: 3 - len(related)]
        # the cards show their pictures only when every card has one, so the row keeps one shape
        pictures = bool(related) and all(getattr(o, "lead_image", None) for o in related)
        related_html = "".join(self.story_card(o, cls="card card-related", thumb=pictures) for o in related)
        lead_figure = self.lead_figure(a_obj)
        body = f"""<div class="wrap">
<nav class="breadcrumb" aria-label="{esc(self.s('breadcrumb'))}"><ol>{crumb_html}</ol></nav>
<article class="article{' has-lead' if lead_figure else ''}" data-kind="{a_obj.kind}">
  <header class="article-head">
    {self.kicker(a_obj)}
    <h1 class="article-title">{esc(a_obj.title)}</h1>
    <p class="article-dek">{esc(a_obj.dek)}</p>
    <div class="article-meta">
      {self.byline(a_obj)}
      <dl class="dateline">{''.join(meta_dates)}</dl>
      <p class="reading-time">{esc(self.s('min_read', n=a_obj.minutes))}</p>
      {translation_note}
    </div>
  </header>
  {lead_figure}
  <div class="article-grid">
    <div class="article-body prose">
      {a_obj.html}
      {disclosure_body}
      {sources}
      {changes}
      {self.check_strip(a_obj)}
    </div>
    {details}
  </div>
</article>
<section class="related" aria-labelledby="related-title">
  {self.block_head(self.s('related_title', topic=self.topic_name(a_obj.primary_topic)), None, '', 'related-title')}
  <div class="card-row">{related_html}</div>
</section>
</div>"""
        path = self.article_url(a_obj)
        alt = self.article_url(a_obj, self.other()) if has_other else self.loc("/latest/", self.other())
        # the structured data and the article:* tags (sitegen/discover.py); the trail is Home, Latest
        ld = discover.article_ld(self, a_obj, has_other)
        tags = {"published": a_obj.published, "modified": a_obj.updated or a_obj.published,
                "section": self.kind_label(a_obj.kind, "kind_plural"), "tags": [self.topic_name(t) for t in a_obj.topics]}
        section = "learn" if a_obj.kind in ("explainer", "guide") else "latest"
        chat_page = {"kind": "article", "slug": a_obj.slug, "url": path, "title": a_obj.title, "sha256": a_obj.sha256,
                     "source": source_path, "article_kind": a_obj.kind}
        return path, self.layout(path=path, title=a_obj.title, description=a_obj.dek, section=section, body=body,
                                 alt_path=alt, page_class=f"page-article kind-{a_obj.kind}", og_type="article", jsonld=ld,
                                 chat_page=chat_page, alternate=has_other,
                                 image=discover.photo_card(self, a_obj) or a_obj.primary_topic, source=source_path,
                                 article=tags, crumbs=crumbs)

    def topics_index(self, articles):
        """The Stack page: the seven layers, the trust tiers, the combinations deployed
        today and a compact index of the eight topics."""
        self.current = self.loc("/topics/")
        L = self.loc
        combos = []
        for combo in self.m["tiers"].get("combinations", []):
            name = self.t(combo["name"])
            tiers = " + ".join(self.tier_link(tid) for tid in combo["tiers"] if self.tier(tid))
            title = self.article_link(combo["article"], label=name) or esc(name)
            combos.append(f'<li class="combo"><h3>{title}</h3>'
                          f'<p class="combo-tiers">{self.colon("topic_tiers")}{tiers}</p><p>{esc(self.t(combo["text"]))}</p></li>')
        resources = self.m["resources"]["resources"]
        rows = []
        for tid in self.topic_order:
            topic = self.topics[tid]
            n = sum(1 for a in articles if tid in a.topics)
            r = sum(1 for res in resources if tid in res.get("topics", []))
            main = f' <span class="tier-main-label">{esc(self.s("tier_main"))}</span>' if tid == TEE_TOPIC else ""
            tiers = self.s("list_comma").join(self.tier_link(t) for t in topic.get("tiers", []) if self.tier(t))
            tier_line = f'<p class="topic-row-tiers">{self.colon("topic_tiers")}{tiers}</p>' if tiers else ""
            rows.append(
                f'<li class="topic-row" data-topic="{tid}"><h3>{self.a(L(f"/topics/{tid}/"), esc(self.t(topic["name"])))}{main}</h3>'
                f'<p>{esc(self.t(topic["one_liner"]))}</p>{tier_line}'
                f'<p class="topic-row-count">{esc(self.count("articles_count", n))} · {esc(self.count("resources_count", r))}</p></li>'
            )
        body = f"""<div class="wrap">
{self.page_head(None, self.s('topics_page_title'), self.s('topics_page_dek'), [(L('/'), self.s('home'))])}
{self.stack_block(articles)}
{self.tiers_section()}
<section id="combinations" aria-labelledby="combinations-title">
  {self.block_head(self.s('combos_title'), hid='combinations-title')}
  <ul class="combos">{''.join(combos)}</ul>
</section>
<section id="topic-index" aria-labelledby="topic-index-title">
  {self.block_head(self.s('topics_title'), hid='topic-index-title')}
  <ol class="topic-index">{''.join(rows)}</ol>
</section>
</div>"""
        path = L("/topics/")
        # the pages the Stack page lists: the topics of its index, in that order (the layers and the
        # tiers are sections of this page)
        ld = discover.collection(self, path, self.s("topics_page_title"), self.s("topics_page_dek"),
                                 [(self.base_url + L(f"/topics/{tid}/"), self.t(self.topics[tid]["name"]))
                                  for tid in self.topic_order])
        return path, self.layout(path=path, title=self.s("topics_page_title"), description=self.s("topics_page_dek"), section="topics",
                                 body=body, alt_path=self.loc("/topics/", self.other()), page_class="page-topics", jsonld=ld)

    def topic_page(self, tid, articles):
        self.current = self.loc(f"/topics/{tid}/")
        L = self.loc
        topic = self.topics[tid]
        coverage = [a for a in articles if tid in a.topics]
        cov_html = "".join(self.river_row(a, with_topic=False, dates=True, sizes=TOPIC_RIVER_SIZES)
                           for a in coverage) or f'<li class="empty">{esc(self.s("no_coverage"))}</li>'
        callout = ""
        if topic.get("tee_relation"):
            # role="note": a callout beside the description, not a second complementary landmark
            callout = (f'<aside class="callout callout-tee" role="note"><p class="callout-label">{esc(self.s("topic_vs_tee"))}</p>'
                       f'<div class="callout-body"><p>{esc(self.t(topic["tee_relation"]))}</p></div></aside>')
        questions = "".join(f"<li>{esc(q)}</li>" for q in self.t(topic["questions"]))
        techniques = "".join(
            f'<div><dt>{esc(self.t(tq["name"]))}</dt><dd>{esc(self.t(tq["description"]))}</dd></div>'
            for tq in topic["techniques"]
        )
        # The questions and techniques fold, as on the TEE hub, so the aside opens on short lists
        folds = "".join(
            f'<details><summary>{esc(self.s(key))}</summary>{inner}</details>'
            for key, inner in (("key_questions", f'<ol class="question-list">{questions}</ol>' if questions else ""),
                               ("techniques", f'<dl class="technique-list">{techniques}</dl>' if techniques else ""))
            if inner
        )
        more = (f'<section aria-labelledby="q-title"><h2 id="q-title" class="aside-title">{esc(self.s("hub_more_title"))}</h2>'
                f'{folds}</section>') if folds else ""
        res = [r for r in self.m["resources"]["resources"] if tid in r.get("topics", [])]
        res_html = "".join(self.resource_item(r, current=tid) for r in res)
        terms = [g for g in self.m["glossary"]["terms"] if g.get("topic") == tid]
        term_html = "".join(self.a(L("/glossary/") + "#" + g["id"], esc(self.t(g["term"])), "chip") for g in terms)
        tier_items = "".join(
            f'<li>{self.tier_link(t, self.s("tier_n", n=self.tier(t)["n"]) + " · " + self.t(self.tier(t)["trust_name"]))}</li>'
            for t in topic.get("tiers", []) if self.tier(t)
        )
        tiers = (f'<section aria-labelledby="tt-title"><h2 id="tt-title" class="aside-title">{esc(self.s("topic_tiers"))}</h2>'
                 f'<ul class="tier-list">{tier_items}</ul></section>') if tier_items else ""
        layer_html = "".join(
            f'<li><span class="layer-code">{self.layer_code(layer["id"])}</span>'
            f'{self.a(L("/topics/") + "#layer-" + layer["id"], esc(self.t(layer["name"])))}</li>'
            for layer in self.stack() if tid in layer.get("topics", [])
        )
        layers = (f'<section aria-labelledby="l-title"><h2 id="l-title" class="aside-title">{esc(self.s("doc_layers"))}</h2>'
                  f'<ul class="layer-list">{layer_html}</ul></section>') if layer_html else ""
        body = f"""<div class="wrap">
{self.page_head(self.s('topic_kicker'), self.t(topic['name']), self.t(topic['one_liner']), [(L('/'), self.s('home')), (L('/topics/'), self.s('nav_stack'))])}
<div class="topic-layout" data-topic="{tid}">
  <div class="topic-main">
    <p class="topic-desc">{esc(self.t(topic['description']))}</p>
    {callout}
    <section aria-labelledby="cov-title">{self.block_head(self.s('coverage'), None, '', 'cov-title')}<ol class="river">{cov_html}</ol></section>
    <section aria-labelledby="res-title">{self.block_head(self.s('topic_resources'), L('/resources/') + '#' + tid, self.s('full_catalog', n=len(self.m['resources']['resources'])), 'res-title')}<ul class="resource-list">{res_html}</ul></section>
  </div>
  <aside class="topic-aside">
    {tiers}
    {layers}
    {more}
    {f'<section aria-labelledby="g-title"><h2 id="g-title" class="aside-title">{esc(self.s("topic_terms"))}</h2><p class="chips">{term_html}</p></section>' if term_html else ''}
  </aside>
</div>
</div>"""
        path = L(f"/topics/{tid}/")
        ld = discover.collection(self, path, self.t(topic["name"]), self.t(topic["one_liner"]),
                                 discover.article_items(self, coverage))
        return path, self.layout(path=path, title=self.t(topic["name"]), description=self.t(topic["one_liner"]), section="topics",
                                 body=body, alt_path=self.loc(f"/topics/{tid}/", self.other()), page_class="page-topic",
                                 jsonld=ld, image=tid)

    def tee_hub(self, articles):
        """The TEE hub at /topics/confidential-computing/: what a checked attestation
        report establishes, the learning path, CPU and GPU platforms, dated trackers
        of attested services and of attacks, a short list of the newest TEE stories
        and the primary documents. Full width, with no aside."""
        path = self.loc(HUB_PATH)
        self.current = path
        L = self.loc
        tee = self.m["tee"]
        topic = self.topics.get(TEE_TOPIC, {})
        title = self.s("hub_title")
        why = f'<p class="hub-why">{self.a(L("/vision/") + "#why-tees", esc(self.s("hub_why")) + ARROW)}</p>'
        head = self.page_head(self.s("hub_kicker"), title, self.s("hub_dek"),
                              [(L("/"), self.s("home")), (L("/topics/"), self.s("nav_stack"))], cls="page-head tee-head", extra=why)

        # What a checked report establishes, and what it leaves to trust
        est = tee["establishes"]
        cols = "".join(
            f'<div><h3>{esc(self.s(key))}</h3><ul>{"".join(f"<li>{esc(self.t(item))}</li>" for item in est[field])}</ul></div>'
            for key, field in (("hub_shows", "shows"), ("hub_still", "still"))
        )
        # the explainer and the guide among the block's sources, then the comparison
        cited = [self.find_article(ref.partition(":")[2]) for ref in est.get("sources", []) if ref.startswith("article:")]
        more_links = [self.article_link(a_obj.slug, suffix=ARROW) for a_obj in cited
                      if a_obj is not None and a_obj.kind in ("explainer", "guide")]
        more_links.append(self.a(L("/topics/") + "#tiers", esc(self.s("stack_compare")) + ARROW))
        questions = "".join(f"<li>{esc(q)}</li>" for q in self.t(topic.get("questions", {})))
        techniques = "".join(f'<div><dt>{esc(self.t(tq["name"]))}</dt><dd>{esc(self.t(tq["description"]))}</dd></div>'
                             for tq in topic.get("techniques", []))
        more = ""
        if questions or techniques:
            more = (f'<details><summary>{esc(self.s("hub_more_title"))}</summary>'
                    + (f'<h3 class="mini-title">{esc(self.s("key_questions"))}</h3><ol class="question-list">{questions}</ol>' if questions else "")
                    + (f'<h3 class="mini-title">{esc(self.s("techniques"))}</h3><dl class="technique-list">{techniques}</dl>' if techniques else "")
                    + "</details>")
        establishes = f"""<section id="establishes" aria-labelledby="establishes-title">
  {self.block_head(self.s('hub_establishes_title'), hid='establishes-title')}
  <div class="hub-cols">{cols}</div>
  <p class="boundary">{esc(self.t(est['boundary']))}</p>
  <p class="hub-links">{''.join(more_links)}</p>
  {more}
</section>"""

        path_block = f"""<section id="path" aria-labelledby="path-title">
  {self.block_head(self.s('hub_path_title'), hid='path-title')}
  {self.path_list(mini=True)}
</section>"""

        # Platforms: what each isolates stays open; signing, reference values and scope fold
        groups = []
        for group, key in (("cpu", "area_cpu"), ("gpu", "area_gpu")):
            cards = "".join(self.platform_card(p) for p in tee["platforms"] if p["group"] == group)
            note = ""
            if group == "gpu" and tee.get("gpu_note"):
                gpu = tee["gpu_note"]
                text = gpu.get("text", gpu) if isinstance(gpu, dict) else gpu
                note = (f'<p class="platform-note">{esc(self.t(text))}</p>'
                        + self.sources_fold(gpu.get("sources") if isinstance(gpu, dict) else [], "platform-sources", inline=True))
            if cards:
                groups.append(f'<div class="platform-group"><h3>{esc(self.s(key))}</h3>{cards}{note}</div>')
        platforms = f"""<section id="platforms" aria-labelledby="platforms-title">
  {self.block_head(self.s('hub_platforms_title'), hid='platforms-title')}
  <div class="platform-groups">{''.join(groups)}</div>
</section>"""

        # Services that publish attestation evidence: a dated table
        cols_h = [("svc_record", "record"), ("svc_checker", "checker"), ("svc_inspect", "inspection")]
        svc_rows = "".join(
            f'<tr id="svc-{esc(svc["id"])}"><th scope="row">{self.island(self.t(svc["name"]))}'
            f'{self.sources_fold(svc.get("sources"), "tracker-sources")}</th>'
            + "".join(f'<td data-label="{esc(self.s(key))}">{esc(self.t(svc.get(field)))}</td>' for key, field in cols_h)
            + "</tr>"
            for svc in tee["services"]
        )
        svc_head = "".join(f'<th scope="col">{esc(self.s(key))}</th>' for key in ["svc_service"] + [k for k, _ in cols_h])
        services = f"""<section id="services" aria-labelledby="services-title">
  {self.block_head(self.s('hub_services_title'), hid='services-title')}
  <p class="hub-intro">{esc(self.s('hub_services_dek'))}</p>
  <table class="tracker"><thead><tr>{svc_head}</tr></thead><tbody>{svc_rows}</tbody></table>
  <p class="tracker-note">{esc(self.s('svc_note'))}</p>{self.as_of_line(tee['services'])}
</section>"""

        # Attacks and limits, newest first, then the responses
        responses = ""
        for resp in tee.get("responses", []):
            when, label = fmt_when(resp.get("date"), self.lang)
            date = f' · <time datetime="{when}">{esc(label)}</time>' if when else ""
            responses += (f'<h4 id="resp-{esc(resp["id"])}">{self.island(self.t(resp["name"]))}{date}</h4>'
                          f'<p>{esc(self.t(resp["text"]))}</p>{self.sources_line(resp.get("sources"), "limit-sources")}')
        if responses:
            responses = f'<div class="responses"><h3>{esc(self.s("lim_responses"))}</h3>{responses}</div>'
        limits = f"""<section id="limits" aria-labelledby="limits-title">
  {self.block_head(self.s('hub_limits_title'), hid='limits-title')}
  <p class="hub-intro">{esc(self.join_sentences([self.s('hub_limits_dek'), self.s('lim_note')]))}</p>
  <ol class="limits">{''.join(self.limit_row(lim) for lim in tee['limits'])}</ol>{self.as_of_line(tee['limits'])}
  {responses}
</section>"""

        # The newest TEE stories that the path above does not already list (or, if it
        # lists them all, the newest TEE stories), as compact rows; Latest#tee keeps them all
        on_path = self.path_slugs()
        tee_stories = [a for a in articles if self.is_tee(a)]
        recent = ([a for a in tee_stories if a.slug not in on_path] or tee_stories)[:HUB_COVERAGE]
        rows = self.brief_rows(recent, thumbs=True) or f'<li class="empty">{esc(self.s("no_coverage"))}</li>'
        coverage = f"""<section id="coverage" aria-labelledby="coverage-title">
  {self.block_head(self.s('hub_coverage_title'), L('/latest/') + '#tee', self.s('hub_coverage_all'), 'coverage-title')}
  <ol class="tee-latest">{rows}</ol>
</section>"""

        # Primary documents by TEE area, then the terms
        reading = []
        resources = self.m["resources"]["resources"]
        for area in content.TEE_AREAS:
            entries = [r for r in resources if r.get("tee_area") == area]
            if entries:
                items = "".join(
                    f'<li>{self.ext(r["url"], r["title"])}<span>{" · ".join(x for x in (self.island(r.get("org", "")), esc(r.get("year", ""))) if x)}</span></li>'
                    for r in entries
                )
                reading.append(f'<div><h3>{esc(self.s("area_" + area))}</h3><ul>{items}</ul></div>')
        # the terms close the grid as one more column, headed like the document groups
        glossary = {g["id"]: g for g in self.m["glossary"]["terms"]}
        chips = "".join(self.a(L("/glossary/") + "#" + gid, esc(self.t(glossary[gid]["term"])), "chip")
                        for gid in tee.get("terms", []) if gid in glossary)
        if chips:
            reading.append(f'<div class="reading-terms"><h3>{esc(self.s("hub_terms"))}</h3><p class="chips">{chips}</p></div>')
        reading_block = f"""<section id="reading" aria-labelledby="reading-title">
  {self.block_head(self.s('hub_reading_title'), hid='reading-title')}
  <div class="reading-grid">{''.join(reading)}</div>
</section>"""

        body = f"""<div class="wrap">
{head}
{establishes}
{path_block}
{platforms}
{services}
{limits}
{coverage}
{reading_block}
</div>"""
        # the stories the hub lists: its path, then the newest TEE stories
        listed = [a for a in (self.find_article(step["article"]) for step in tee["path"] if "article" in step) if a]
        listed += [a for a in recent if a not in listed]
        ld = discover.collection(self, path, title, self.s("hub_dek"), discover.article_items(self, listed))
        return path, self.layout(path=path, title=title, description=self.s("hub_dek"), section="tee", body=body,
                                 alt_path=self.loc(HUB_PATH, self.other()), page_class="page-topic page-tee",
                                 jsonld=ld, image=TEE_TOPIC)

    def platform_card(self, p):
        """A CPU or GPU platform: what it isolates stays open; signing, reference values,
        the vendor's scope and the sources fold away. A cell not yet researched reads
        "Not yet covered here"."""
        shown = self.field_list([("plat_isolates", p.get("isolates"))], "platform-fields", pending=True)
        folded = self.field_list([("plat_signs", p.get("signs")), ("plat_refs", p.get("reference_values")),
                                  ("plat_scope", p.get("out_of_scope"))], "platform-fields", pending=True)
        folded += self.sources_line(p.get("sources"), "platform-sources")
        details = f'<details><summary>{esc(self.s("plat_more"))}</summary>{folded}</details>' if folded else ""
        return (f'<article class="platform" id="plat-{esc(p["id"])}"><h4>{self.island(self.t(p["name"]))}</h4>'
                f'{shown}{details}</article>')

    def limit_row(self, lim):
        """An attack or limit: date, name, whether it needs physical access and what it
        defeated stay open; access, the vendor's position, status and the sources fold."""
        when, label = fmt_when(lim.get("date"), self.lang)
        date = f'<time datetime="{when}">{esc(label)}</time>' if when else esc(self.s("lim_undated"))
        physical = bool(lim.get("physical"))
        rest = [(key, lim.get(field)) for key, field in (("lim_access", "access"), ("lim_vendor", "vendor"), ("lim_status", "status"))]
        folded = self.field_list(rest, "limit-fields") + self.sources_line(lim.get("sources"), "limit-sources")
        details = f'<details><summary>{esc(self.s("lim_more"))}</summary>{folded}</details>' if folded else ""
        editor = f'<p class="limit-editor">{esc(self.s("editor_coauthor"))}</p>' if lim.get("editor") else ""
        return (f'<li class="limit" id="limit-{esc(lim["id"])}" data-kind="{"physical" if physical else "remote"}">'
                f'<p class="limit-date">{date}</p><h3>{self.island(self.t(lim["name"]))}</h3>'
                f'<p><span class="limit-kind">{esc(self.s("lim_physical" if physical else "lim_remote"))}</span></p>'
                f'{self.field_list([("lim_defeated", lim.get("defeated"))], "limit-fields")}{details}{editor}</li>')

    def as_of_line(self, rows):
        """"As of 20 Oct 2026" under a tracker whose rows were all reviewed that day."""
        dates = {row.get("as_of") for row in rows if row.get("as_of")}
        if len(dates) != 1:
            return ""
        when, label = fmt_when(dates.pop(), self.lang)
        stamp = f'<time datetime="{when}">{esc(label)}</time>'
        text = esc(self.s("as_of", date="\x00")).replace("\x00", stamp)
        return f'\n  <p class="as-of">{text}</p>'

    def learn(self, articles):
        """Learn: the TEE path, worksheet cards for the other guides, the terms to know
        first and a compact list of every explainer and guide."""
        self.current = self.loc("/learn/")
        L = self.loc
        on_path = self.path_slugs()
        cards = []
        for a_obj in [a for a in articles if a.kind == "guide" and a.slug not in on_path]:
            needs = (f'<p class="ws-needs">{self.colon("guide_needs")}{esc(a_obj.needs)}</p>'
                     if getattr(a_obj, "needs", "") else "")
            steps = self.steps_of(a_obj)
            steps_html = f'<p class="ws-steps">{esc(self.count("guide_steps", steps))}</p>' if steps else ""
            mark = self.byline_mark(a_obj)
            cards.append(
                f'<li class="worksheet-card"><p class="ws-kind">{esc(self.kind_label(a_obj.kind) + " · " + self.s("min_read", n=a_obj.minutes))}'
                f'{" · " + mark if mark else ""}</p>'
                f'<h3>{self.a(self.article_url(a_obj), esc(a_obj.title))}</h3><p>{esc(a_obj.dek)}</p>{needs}{steps_html}</li>'
            )
        glossary = {g["id"]: g for g in self.m["glossary"]["terms"]}
        alt_lang = "zh" if self.lang == "en" else "en"
        terms = "".join(
            f'<div><dt><span class="term-name">{self.a(L("/glossary/") + "#" + gid, esc(self.t(glossary[gid]["term"])))}</span>'
            f'<span class="term-alt" lang="{"zh-CN" if alt_lang == "zh" else "en"}">{esc(glossary[gid]["term"][alt_lang])}</span></dt>'
            f'<dd>{esc(self.t(glossary[gid]["definition"]))}</dd></div>'
            for gid in self.m["tee"].get("learn_terms", []) if gid in glossary
        )
        everything = "".join(
            f'<li>{time_tag(a.published, self.lang)}{self.a(self.article_url(a), esc(a.title))}</li>'
            for a in articles if a.kind in ("explainer", "guide")
        )
        sections = [f"""<section id="tee-path" aria-labelledby="tee-path-title">
  {self.block_head(self.s('learn_path_title'), hid='tee-path-title')}
  <p class="block-dek">{esc(self.path_counted('learn_path_dek'))}</p>
  {self.path_list(marks=True)}
</section>"""]
        if cards:
            sections.append(f"""<section id="checks" aria-labelledby="checks-title">
  {self.block_head(self.s('learn_checks_title'), hid='checks-title')}
  <ul class="worksheet-cards">{''.join(cards)}</ul>
</section>""")
        if terms:
            sections.append(f"""<section id="terms" aria-labelledby="terms-title">
  {self.block_head(self.s('learn_terms_title'), hid='terms-title')}
  <dl class="term-cards">{terms}</dl>
  <p class="all-terms">{self.a(L('/glossary/'), esc(self.s('all_terms')) + ARROW)}</p>
</section>""")
        if everything:
            sections.append(f"""<section id="all" aria-labelledby="all-title">
  {self.block_head(self.s('learn_all_title'), hid='all-title')}
  <ol class="compact-list">{everything}</ol>
</section>""")
        body = f"""<div class="wrap">
{self.page_head(None, self.s('learn_title'), self.s('learn_dek'), [(L('/'), self.s('home'))])}
{chr(10).join(sections)}
</div>"""
        path = L("/learn/")
        # the articles the page lists, each where it first appears: the TEE path in its order, the
        # worksheet guides, then the other explainers of the list of every explainer and guide
        listed = {}
        for a_obj in ([self.find_article(step["article"]) for step in self.m["tee"]["path"] if "article" in step]
                      + [a for a in articles if a.kind == "guide"] + [a for a in articles if a.kind in ("explainer", "guide")]):
            if a_obj is not None:
                listed.setdefault(a_obj.slug, a_obj)
        ld = discover.collection(self, path, self.s("learn_title"), self.s("learn_dek"),
                                 discover.article_items(self, listed.values()))
        return path, self.layout(path=path, title=self.s("learn_title"), description=self.s("learn_dek"), section="learn",
                                 body=body, alt_path=self.loc("/learn/", self.other()), page_class="page-learn", jsonld=ld)

    def resource_item(self, r, compact=False, group=None, level=3, current=None):
        """A resource entry: the title, then the publisher, year, type and "Link checked"
        date (beside the title from 760px). The note folds under "Summary", so a long
        list reads as titles. Chips name the entry's other topics: a topic page (current)
        leaves out its own, and in a catalog group the group's chip comes first, so the
        stylesheet can hide the chip that repeats the group heading. A compact entry
        has no anchor, date or chips, and its note stays open."""
        topics = r.get("topics", [])
        rtype = r.get("type", "")
        type_label = self.s(f"type_{rtype}") if f"type_{rtype}" in self.m["strings"][self.lang] else rtype
        meta = " · ".join(x for x in [self.island(r.get("org", "")), esc(r.get("year", "")), esc(type_label)] if x)
        if r.get("verified_on") and not compact:
            try:
                checked = fmt_date(dt.date.fromisoformat(r["verified_on"]), self.lang)
                meta += f' <span class="resource-checked">{esc(self.s("res_checked", date=checked))}</span>'
            except ValueError:
                pass
        note_text = self.t(r.get("note", ""))
        note = f'<p class="resource-note"{self.lang_attr(note_text)}>{esc(note_text)}</p>' if note_text else ""
        if note and not compact:
            note = f'<details class="resource-more"><summary>{esc(self.s("res_more"))}</summary>{note}</details>'
        others = [t for t in topics if t not in (group, current) and t in self.topics]
        chip_ids = ([group] + others) if group in topics else others
        chips = f'<p class="chips">{self.topic_chips(chip_ids)}</p>' if others and not compact else ""
        id_attr = "" if compact else ' id="res-' + esc(r.get("id", "")) + '"'
        area = f' data-area="{esc(r["tee_area"])}"' if r.get("tee_area") else ""
        haystack = " ".join([r.get("title", ""), r.get("org", ""), self.t(r.get("note", "")), r.get("note", {}).get("en", "") if isinstance(r.get("note"), dict) else ""]).lower()
        return (
            f'<li class="resource"{id_attr} data-type="{esc(rtype)}" data-topics="{esc(" ".join(topics))}"{area} data-text="{esc(haystack)}">'
            f'<h{level} class="resource-title">{self.ext(r["url"], r["title"])}</h{level}>'
            f'<p class="resource-meta">{meta}</p>{note}{chips}</li>'
        )

    def resources(self):
        """Resources: four reading paths, then the catalog with the TEE entries first,
        split by TEE area, and each group's "You trust" line."""
        self.current = self.loc("/resources/")
        L = self.loc
        data = self.m["resources"]
        items = data["resources"]
        by_id = {r["id"]: r for r in items}
        paths = []
        for rp in data.get("paths", []):
            entries = "".join(
                f'<li>{self.ext(by_id[e["id"]]["url"], by_id[e["id"]]["title"])}<span class="rpath-why">{esc(self.t(e["why"]))}</span></li>'
                for e in rp["entries"] if e["id"] in by_id
            )
            paths.append(f'<article class="rpath"><h3>{esc(self.t(rp["title"]))}</h3><p>{esc(self.t(rp["purpose"]))}</p>'
                         f'<ol>{entries}</ol></article>')
        types = sorted({r.get("type", "") for r in items})
        topic_opts = "".join(f'<option value="{tid}">{esc(self.topic_name(tid))}</option>' for tid in self.topic_order)
        area_opts = "".join(f'<option value="{area}">{esc(self.s("area_" + area))}</option>' for area in content.TEE_AREAS)
        type_opts = "".join(
            f'<option value="{esc(t)}">{esc(self.s("type_" + t) if ("type_" + t) in self.m["strings"][self.lang] else t)}</option>'
            for t in types if t
        )

        def trust_line(tid):
            tiers = [self.tier(t) for t in self.topics[tid].get("tiers", []) if self.tier(t)]
            if tid not in TRUST_ALL_TIERS:
                tiers = tiers[:1]
            names = self.s("list_or").join(self.trust_text(self.t(t["trust_name"])) for t in tiers)
            return f'<p class="catalog-trust">{esc(self.s("catalog_trust", text=names))}</p>' if names else ""

        # The TEE group holds every entry with a TEE area, including those whose first topic is another
        tee_items = [r for r in items if r.get("tee_area")]
        sections = []
        if tee_items and TEE_TOPIC in self.topics:
            subs = ""
            for area in content.TEE_AREAS:
                group = [r for r in tee_items if r["tee_area"] == area]
                if group:
                    subs += (f'<h3 class="catalog-sub" id="tee-{area}">{esc(self.s("area_" + area))} <span class="count">{len(group)}</span></h3>'
                             f'<ul class="resource-list" data-area="{area}">{"".join(self.resource_item(r, group=TEE_TOPIC, level=4) for r in group)}</ul>')
            sections.append(f'<section class="catalog-group" data-group="{TEE_TOPIC}">'
                            f'<h2 class="catalog-title" id="{TEE_TOPIC}">{esc(self.topic_name(TEE_TOPIC))} <span class="count">{len(tee_items)}</span></h2>'
                            f'{trust_line(TEE_TOPIC)}{subs}</section>')
        # The other topics follow in tier order: by the number of their first tier
        tier_n = {t["id"]: t["n"] for t in self.tiers()}
        others = [tid for tid in self.topic_order if tid != TEE_TOPIC]
        others.sort(key=lambda tid: tier_n.get((self.topics[tid].get("tiers") or [None])[0], len(tier_n) + 1))
        for tid in others:
            group = [r for r in items if (r.get("topics") or [""])[0] == tid and not r.get("tee_area")]
            if group:
                # unnamed, so the groups are headings rather than more landmarks
                sections.append(
                    f'<section class="catalog-group" data-group="{tid}">'
                    f'<h2 class="catalog-title" id="{tid}">{esc(self.topic_name(tid))} <span class="count">{len(group)}</span></h2>'
                    f'{trust_line(tid)}<ul class="resource-list">{"".join(self.resource_item(r, group=tid) for r in group)}</ul></section>'
                )
        total = len(items)
        rpaths = ""
        if paths:
            rpaths = f"""<section class="rpaths-section" id="paths" aria-labelledby="paths-title">
  {self.block_head(self.s('paths_title'), hid='paths-title')}
  <div class="rpaths">{''.join(paths)}</div>
</section>"""
        body = f"""<div class="wrap">
{self.page_head(None, self.s('resources_page_title'), self.s('resources_dek'), [(L('/'), self.s('home'))])}
{rpaths}
<form class="filters" role="search" data-resource-filters hidden>
  <div class="field field-search"><label for="res-q">{esc(self.s('search_resources'))}</label>
    <input id="res-q" name="q" type="search" placeholder="{esc(self.s('search_placeholder'))}" autocomplete="off"></div>
  <div class="field"><label for="res-topic">{esc(self.s('topics_title'))}</label>
    <select id="res-topic" name="topic"><option value="">{esc(self.s('any_topic'))}</option>{topic_opts}</select></div>
  <div class="field"><label for="res-area">{esc(self.s('res_area'))}</label>
    <select id="res-area" name="area" data-area><option value="">{esc(self.s('any_area'))}</option>{area_opts}</select></div>
  <div class="field"><label for="res-type">{esc(self.s('doc_type'))}</label>
    <select id="res-type" name="type"><option value="">{esc(self.s('any_type'))}</option>{type_opts}</select></div>
</form>
<p class="result-count" aria-live="polite" data-template="{esc(self.s('showing', shown='{shown}', total='{total}'))}">{esc(self.s('showing', shown=total, total=total))}</p>
<div class="resource-catalog">{''.join(sections)}</div>
<p class="empty" hidden data-empty>{esc(self.s('no_results'))}</p>
</div>"""
        path = L("/resources/")
        # the catalog in the order the page lists it: the TEE entries, then the other groups
        listed = [r for area in content.TEE_AREAS for r in tee_items if r["tee_area"] == area] if TEE_TOPIC in self.topics else []
        listed += [r for tid in others for r in items if (r.get("topics") or [""])[0] == tid and not r.get("tee_area")]
        ld = discover.collection(self, path, self.s("resources_page_title"), self.s("resources_dek"),
                                 [(r["url"], r["title"]) for r in listed])
        return path, self.layout(path=path, title=self.s("resources_page_title"), description=self.s("resources_dek"), section="resources",
                                 body=body, alt_path=self.loc("/resources/", self.other()), page_class="page-resources", jsonld=ld)

    def glossary(self):
        self.current = self.loc("/glossary/")
        L = self.loc
        terms = sorted(self.m["glossary"]["terms"], key=lambda g: g["term"]["en"].lower())
        letters, groups = [], {}
        for g in terms:
            letter = g["term"]["en"][0].upper()
            if letter not in groups:
                groups[letter] = []
                letters.append(letter)
            groups[letter].append(g)
        jump = "".join(f'<li><a href="#letter-{esc(l)}">{esc(l)}</a></li>' for l in letters)
        sections = []
        for letter in letters:
            entries = []
            for g in groups[letter]:
                topic = g.get("topic")
                topic_html = f'<p class="term-topic">{esc(self.s("related_topic"))}: {self.a(L(f"/topics/{topic}/"), esc(self.topic_name(topic)))}</p>' if topic in self.topics else ""
                alt = g["term"]["zh"] if self.lang == "en" else g["term"]["en"]
                primary = g["term"]["en"] if self.lang == "en" else g["term"]["zh"]
                entries.append(
                    f'<div class="term" id="{esc(g["id"])}"><dt><span class="term-name">{esc(primary)}</span>'
                    f'<span class="term-alt" lang="{"zh-CN" if self.lang == "en" else "en"}">{esc(alt)}</span></dt>'
                    f'<dd><p>{esc(self.t(g["definition"]))}</p>{topic_html}</dd></div>'
                )
            # unnamed: a letter is a heading to jump to, not a landmark (twenty of them crowd the landmark list)
            sections.append(f'<section class="term-group"><h2 class="term-letter" id="letter-{esc(letter)}">{esc(letter)}</h2><dl>{"".join(entries)}</dl></section>')
        body = f"""<div class="wrap">
{self.page_head(None, self.s('glossary_title'), self.s('glossary_dek'), [(L('/'), self.s('home'))])}
<nav class="letter-jump" aria-label="{esc(self.s('jump_to'))}"><ol>{jump}</ol></nav>
<div class="glossary">{''.join(sections)}</div>
</div>"""
        path = L("/glossary/")
        ld = discover.glossary_ld(self, path, self.s("glossary_title"), self.s("glossary_dek"), terms)
        return path, self.layout(path=path, title=self.s("glossary_title"), description=self.s("glossary_dek"), section="glossary",
                                 body=body, alt_path=self.loc("/glossary/", self.other()), page_class="page-glossary", jsonld=ld)

    def includes(self, page):
        """A page body with its <div data-include="..."></div> lines filled: "positioning"
        (the home positioning paragraph as the lead) and "tiers-summary" (the order
        note and the tier summary table). Any other name stops the build."""
        known = {"positioning": lambda: f'<p class="lead">{esc(self.s("home_positioning"))}</p>',
                 "tiers-summary": self.tier_summary}

        def fill(m):
            name = m.group(1)
            if name not in known:
                raise content.ContentError(f"{page.path}: unknown include {name!r}; use one of {', '.join(sorted(known))}")
            return known[name]()

        text = INCLUDE_RE.sub(fill, page.html)
        if "data-include=" in text:
            raise content.ContentError(f'{page.path}: write an include as a line of its own: <div data-include="name"></div>')
        return text

    def static_page(self, page, section):
        self.current = self.loc(f"/{page.name}/")
        L = self.loc
        dates = []
        if page.published:
            dates.append(f'<div><dt>{esc(self.s("published"))}</dt><dd>{time_tag(page.published, self.lang)}</dd></div>')
        if self.revised(page):  # "Updated" only when it differs from the filing date
            dates.append(f'<div><dt>{esc(self.s("updated"))}</dt><dd>{time_tag(page.updated, self.lang)}</dd></div>')
        toc_items = "".join(f'<li><a href="#{hid}">{esc(plain(text))}</a></li>' for lvl, text, hid in page.headings if lvl == 2)
        toc = (f'\n    <nav class="toc" aria-labelledby="toc-title"><h2 id="toc-title" class="aside-title">{esc(self.s("on_this_page"))}</h2>'
               f'<ol>{toc_items}</ol></nav>') if toc_items else ""
        # <article>: the body's callouts stay inside it rather than becoming complementary landmarks
        body = f"""<div class="wrap">
{self.page_head(None, page.title, page.dek, [(L('/'), self.s('home'))])}
<div class="article-grid">
  <article class="article-body prose">{self.includes(page)}</article>
  <aside class="doc-aside">
    <section class="doc-details" aria-labelledby="details-title"><h2 id="details-title" class="aside-title">{esc(self.s('doc_details'))}</h2><dl>{''.join(dates)}</dl></section>{toc}
  </aside>
</div>
</div>"""
        path = L(f"/{page.name}/")
        # About says who publishes the site, so it carries AboutPage and the Organization
        ld = discover.about_ld(self, page) if page.name == "about" else None
        return path, self.layout(path=path, title=page.title, description=page.dek, section=section, body=body,
                                 alt_path=self.loc(f"/{page.name}/", self.other()), page_class=f"page-{page.name}",
                                 jsonld=ld, source=f"/pages/{page.name}.{page.lang}.md")

    def search(self):
        self.current = self.loc("/search/")
        L = self.loc
        labels = {k: self.s(f"search_group_{k}") for k in ("article", "topic", "page", "term", "resource")}
        body = f"""<div class="wrap">
{self.page_head(None, self.s('search_title'), self.s('search_dek'), [(L('/'), self.s('home'))])}
<form class="search-form" role="search" data-site-search data-index="{esc(self.href(L('/search-index.json')))}" data-labels="{esc(json.dumps(labels, ensure_ascii=False))}" data-hint="{esc(self.s('search_hint'))}" data-none="{esc(self.s('search_none'))}" data-count="{esc(self.s('search_count'))}" data-count-one="{esc(self.count('search_count', 1))}">
  <label for="site-q">{esc(self.s('search_label'))}</label>
  <input id="site-q" name="q" type="search" autocomplete="off" placeholder="{esc(self.s('search_placeholder'))}">
</form>
<p class="vh" role="status" data-search-count></p>
<div class="search-results"><p class="search-status">{esc(self.s('search_hint'))}</p></div>
</div>"""
        path = L("/search/")
        # without JavaScript the page lists no results, so search engines are asked not to index it
        return path, self.layout(path=path, title=self.s("search_title"), description=self.s("search_dek"), section="search",
                                 body=body, alt_path=self.loc("/search/", self.other()), page_class="page-search",
                                 indexable=False)

    def not_found(self):
        self.current = "/404.html" if self.lang == "en" else "/zh/404.html"
        L = self.loc
        body = f"""<div class="wrap notfound">
<p class="kicker"><span class="kind">404</span></p>
<h1 class="page-title">{esc(self.s('notfound_title'))}</h1>
<p class="page-dek">{esc(self.s('notfound_text'))}</p>
<p class="read-more">{self.a(L('/'), esc(self.s('notfound_home')) + ARROW)}</p>
</div>"""
        path = "/404.html" if self.lang == "en" else "/zh/404.html"
        return path, self.layout(path=path, title=self.s("notfound_title"), description=self.s("notfound_text"), section="",
                                 body=body, alt_path="/zh/404.html" if self.lang == "en" else "/404.html", page_class="page-404",
                                 indexable=False)
