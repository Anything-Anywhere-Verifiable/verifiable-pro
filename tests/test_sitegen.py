import colorsys
import copy
import datetime as dt
import hashlib
import html
import json
import math
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build  # noqa: E402
from sitegen import art, content, discover, logos, md, render  # noqa: E402
from sitegen.render import Site  # noqa: E402

CHAT_CONFIG_RE = re.compile(r'<script type="application/json" id="chat-config">(.*?)</script>', re.S)
# Markup that only the Ask assistant emits; none of it may appear with --chat off
CHAT_MARKERS = ('id="chat-config"', 'class="chat-launch"', 'class="chat-aside"', "data-chat-open", "assets/chat.css",
                "assets/chat.js")

def build_site(out, *extra, root=ROOT):
    """Build a preview into OUT with build.py, as CI does."""
    args = ["--mode", "preview", "--out", str(out), *extra]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(root / "build.py"), *args], cwd=root, capture_output=True, text=True,
                          env=env)

# Interface phrases retired so that verifiable.pro does not read as a copy of
# another publication's front page, footer or follow box. The build output
# must not contain them in either language. Add a phrase here when you retire it.
DENYLIST = [
    "News, analysis & learning",
    "News, analysis and learning",
    "Suggest a story or resource",
    "Follow via RSS / Atom",
    "Follow verifiable.pro",
    "News & releases",
    "Document details",
    "Contact & follow",
    "Editorial email",
    "Selected resources",
    "Full catalog",
    "新闻、分析与学习",
    "推荐报道或资源",
    "通过 RSS / Atom 关注",
    "新闻与发布",
    "联系与关注",
    "编辑邮箱",
    "精选资源",
    "完整目录",
]

# Wording that claims more than a check shows (spec section 2.1 and the lint in
# tools/lint_content.py): attestation establishes or shows and never proves, and
# Chinese keeps 远程证明 for attestation and 数学证明 for proofs.
WORDING = (
    r"\bproves the software", r"\bproves the model", r"\bguarantees privacy\b", r"\bverified services?\b",
    r"\bthe software that runs\b", "硬件证明", "能证明什么", "可证明审计",
)
# Known uses of that wording in article bodies that an editor has not yet rewritten.
# The six Chinese bodies that used it were reworded on 21 October 2026, so none is
# allowed now and any use in an article body fails. tools/lint_content.py keeps the
# same table.
LEGACY_BODY_WORDING = {}
# Quoted text reports someone else's words, such as a vendor's claim
QUOTED_RE = re.compile(r'"[^"\n]{1,200}"|“[^”\n]{1,200}”|「[^」\n]{1,200}」|『[^』\n]{1,200}』')

# Interface strings the redesign adds (spec section 19, the hero's layer labels, and the
# hero's person, layer cards and chain legend); each must be filled in both languages
NEW_STRINGS = (
    "nav_tee", "nav_vision", "home_positioning", "home_positioning_short", "home_link_vision", "home_link_path",
    "hero_scene_title", "hero_scene_desc", "hero_layers_label", "hero_layers_note", "hero_tee_vh",
    "motion_pause", "motion_play", "motion_static", "tag_tee", "tag_tee_name", "tag_layers_vh", "tags_note",
    "stack_with_tee", "reach_direct", "reach_via", "stack_other", "stack_cover", "stack_cover_tee", "stack_newest",
    "stack_compare", "stack_more", "layers_title", "layers_dek", "tiers_title", "tiers_why_link", "tier_n",
    "tier_trust", "tier_establishes", "tier_not", "tier_hidden", "tier_cost", "tier_vs_tee", "tier_focus",
    "tier_combined", "tier_includes", "tier_read", "tier_main", "baseline_label", "combos_title", "topic_tiers",
    "topic_vs_tee", "hub_kicker", "hub_title", "hub_dek", "hub_why", "hub_establishes_title", "hub_shows", "hub_still",
    "hub_more_title", "hub_path_title", "path_after", "path_planned", "hub_platforms_title", "plat_isolates",
    "plat_signs", "plat_refs", "plat_scope", "plat_pending", "hub_services_title", "svc_service", "svc_record",
    "svc_checker", "svc_inspect", "svc_note", "as_of", "hub_limits_title", "lim_defeated", "lim_access", "lim_vendor",
    "lim_status", "lim_physical", "lim_remote", "lim_responses", "lim_note", "hub_coverage_title", "hub_coverage_all",
    "hub_reading_title", "hub_terms", "area_standards", "area_cpu", "area_gpu", "area_services", "area_attacks",
    "area_performance", "area_uses", "tracked_in", "editor_coauthor", "tee_block_title", "tee_block_path",
    "tee_block_more", "checks_title", "guide_needs", "guide_steps", "learn_path_title", "learn_path_dek",
    "learn_checks_title", "learn_terms_title", "all_terms", "learn_all_title", "paths_title", "res_area", "any_area",
    "catalog_trust", "filter_tee", "filter_tee_aria", "filter_layer", "any_layer", "doc_layers", "search_group_page",
    "tagline", "site_description", "footer_about", "topics_page_title", "topics_page_dek", "learn_dek",
    "resources_dek", "filter_label", "hero_person", "hero_person_who", "hero_hint", "hero_hint_touch",
    "hero_chain_title", "hero_chain_run", "checkers_label", "hero_card_root", "hero_card_root_text",
    "hero_card_open", "hero_card_none", "hero_card_examples", "hero_more", "home_editor", "hero_progress", "hero_progress_done",
    "hero_check_all", "hero_checked", "hero_code_sep", "hero_complete", "home_maintainer", "home_contributors",
)

TEE = content.TEE_TOPIC
HUB = f"/topics/{TEE}/"
LANG_DIR = {"en": "", "zh": "zh/"}
# The header items in order: (section key, string key, address)
# Vision first, right beside the wordmark
NAV = (("vision", "nav_vision", "/vision/"), ("tee", "nav_tee", HUB), ("latest", "nav_latest", "/latest/"),
       ("topics", "nav_stack", "/topics/"), ("learn", "nav_learn", "/learn/"), ("resources", "nav_resources", "/resources/"))
# The home page's sections in order. The stack table is on the Stack page only: the hero's
# layer cards show each layer and link there.
HOME_BLOCKS = ("home-hero", "start-block", "home-news", "tee-block", "checks-block")
HUB_SECTIONS = ("establishes", "path", "platforms", "services", "limits", "coverage", "reading")
# The hub's #coverage lists this many of the newest TEE stories that its path does not
# list; Latest#tee keeps every TEE story
HUB_COVERAGE = 5
VISION_SECTIONS = ("problem", "verifiable", "why-tees", "compare", "goals", "non-goals", "editor", "readers",
                   "accountability")
# illustrations: the credit line under every lead figure links there
ABOUT_ANCHORS = ("integrity", "corrections", "contribute", "assistant", "contact", "ai", "editor", "illustrations")
# Files of the retired raster hero, which no page may link and the build must not publish
RASTER_HERO = ("hero.png", "hero-1200.png", "hero-800.webp", "hero-1400.webp", "hero-800.avif", "hero-1400.avif")
# Classes of the retired pictures: plates, the old square list thumbnails and the digest
# drawings (lead images use lead-figure and story-thumb instead)
RETIRED_CLASSES = {"plate", "plate-cap", "thumb", "art-figure", "article-art", "article-plate"}
HEX_DIGEST_RE = re.compile(r"\b[0-9a-f]{64}\b")
ARTICLE_PATH_RE = re.compile(r"^(?:/zh)?/articles/([a-z0-9]+(?:-[a-z0-9]+)*)/$")


# ----- reading built pages ---------------------------------------------------

VOID_TAGS = frozenset("area base br col embed hr img input link meta param source track wbr".split())


class Node:
    """An element of a parsed page: tag, attributes, parent and children (nodes and text)."""

    def __init__(self, tag, attrs=(), parent=None):
        self.tag = tag
        self.attrs = {key: "" if value is None else value for key, value in attrs}
        self.parent = parent
        self.children = []

    def __repr__(self):
        shown = " ".join(f'{k}="{v}"' for k, v in self.attrs.items() if k in ("id", "class", "href", "src"))
        return f"<{self.tag}{' ' + shown if shown else ''}>"

    @property
    def classes(self):
        return set(self.attrs.get("class", "").split())

    def iter(self):
        """This element and every element below it, in document order."""
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.iter()

    def matches(self, tag=None, cls=None, **attrs):
        if tag is not None and self.tag not in ((tag,) if isinstance(tag, str) else tag):
            return False
        if cls is not None and not set(cls.split()) <= self.classes:
            return False
        for key, value in attrs.items():
            key = key.replace("_", "-")
            if value is True:
                if key not in self.attrs:
                    return False
            elif self.attrs.get(key) != value:
                return False
        return True

    def find_all(self, tag=None, cls=None, **attrs):
        """Elements below this one that match, in document order."""
        return [n for n in self.iter() if n is not self and n.matches(tag, cls, **attrs)]

    def find(self, tag=None, cls=None, **attrs):
        return next((n for n in self.iter() if n is not self and n.matches(tag, cls, **attrs)), None)

    def kids(self, tag=None, cls=None, **attrs):
        """Child elements that match."""
        return [c for c in self.children if isinstance(c, Node) and c.matches(tag, cls, **attrs)]

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def within(self, other):
        return any(node is other for node in self.ancestors())

    def closest(self, tag):
        return next((node for node in self.ancestors() if node.tag == tag), None)

    def text(self, skip=None):
        """The text below this element with whitespace collapsed. Script and style
        content, and elements for which skip(element) is true, are left out."""
        parts = []

        def walk(node):
            for child in node.children:
                if isinstance(child, str):
                    parts.append(child)
                elif child.tag not in ("script", "style") and not (skip and skip(child)):
                    walk(child)

        walk(self)
        return norm("".join(parts))

    def raw(self):
        """The element's own text exactly as written, such as a script's JSON."""
        return "".join(c for c in self.children if isinstance(c, str))


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs, self.stack[-1]))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_html(text):
    builder = _Builder()
    builder.feed(text)
    builder.close()
    return builder.root


def site_stylesheet_href(doc):
    return next(link.attrs["href"] for link in doc.find_all("link", rel="stylesheet")
                if urlsplit(link.attrs["href"]).path.endswith("assets/site.css"))


def norm(text):
    return " ".join(str(text).split())


def loc(path, lang):
    """A canonical path in LANG: "/latest/" or "/zh/latest/"."""
    return ("/zh" + path) if lang == "zh" else path


def canonical(page, href):
    """The canonical path that a preview link on PAGE (such as "zh/learn/index.html")
    points to: "../latest/index.html#tee" there is "/zh/latest/#tee". Outside links
    are returned as they are."""
    if href.startswith(("http://", "https://", "mailto:", "//")):
        return href
    path, mark, frag = href.partition("#")
    target = posixpath.normpath(posixpath.join(posixpath.dirname(page), path)) if path else page
    if target == "index.html" or target.endswith("/index.html"):
        target = target[: -len("index.html")]
    elif target == ".":
        target = ""
    return "/" + target + mark + frag


def following_until(node, stop_tag):
    """The sibling elements after NODE, up to the next STOP_TAG sibling."""
    siblings = [c for c in node.parent.children if isinstance(c, Node)]
    out = []
    for sib in siblings[next(i for i, s in enumerate(siblings) if s is node) + 1:]:
        if sib.tag == stop_tag:
            break
        out.append(sib)
    return out


def kind_of(node, names):
    """The first of NAMES among NODE's classes, else its tag."""
    return next((name for name in names if name in node.classes), node.tag)


def images(doc):
    """The pictures a page shows: <img>, <video>, <canvas>, <object>, <embed>, <iframe>
    and any inline <svg> that is not aria-hidden (icons are aria-hidden; the vendor
    marks in the hero's layer labels are named, and hero_parts() sets them apart)."""
    found = []
    for node in doc.iter():
        if node.tag in ("img", "video", "canvas", "object", "embed", "iframe"):
            found.append(node)
        elif node.tag == "svg" and node.attrs.get("aria-hidden") != "true" and not any(
                a.tag == "svg" for a in node.ancestors()):
            found.append(node)
    return found


# The <img> classes of an article's lead image: the figure on its page, and the decorative
# copies that lists show beside the story
LEAD_PICTURES = {"lead-figure-img", "story-thumb-img"}


def is_lead_picture(node):
    return node.tag == "img" and bool(node.classes & LEAD_PICTURES)


def hero_parts(doc):
    """The home hero's (scene, vendor marks named for screen readers) among images(doc),
    leaving out the lead images of the news below it."""
    pictures = [p for p in images(doc) if not is_lead_picture(p)]
    marks = [p for p in pictures if "hero-logo" in p.classes]
    return [p for p in pictures if p not in marks], marks


def copy_content(root):
    """Copy content/ into the scratch project ROOT, with static/media/, which holds the lead
    images that content/articles/*/illustration.json name: content.load() checks them."""
    shutil.copytree(ROOT / "content", root / "content")
    media = ROOT / content.MEDIA_DIR
    if media.is_dir():
        shutil.copytree(media, root / content.MEDIA_DIR)


def path_points(d):
    """The points that an SVG path of straight segments passes through (M, L, H, V
    and Z, absolute or relative); any other command fails the calling test."""
    points, x, y, start = [], 0.0, 0.0, (0.0, 0.0)
    for cmd, args in re.findall(r"([A-Za-z])([^A-Za-z]*)", d):
        if cmd in "Zz":
            x, y = start
            continue
        if cmd not in "MmLlHhVv":
            raise AssertionError(f"path command {cmd} in {d[:40]}...")
        nums = [float(v) for v in re.findall(r"-?(?:\d+\.?\d*|\.\d+)", args)]
        step = 1 if cmd in "HhVv" else 2
        for i in range(0, len(nums), step):
            dx, dy = (x, y) if cmd.islower() else (0.0, 0.0)
            if cmd in "Hh":
                x = dx + nums[i]
            elif cmd in "Vv":
                y = dy + nums[i]
            else:
                x, y = dx + nums[i], dy + nums[i + 1]
                if cmd in "Mm" and i == 0:
                    start = (x, y)
            points.append((x, y))
    return points


def example_name(node):
    """What a screen reader reads for one example in a hero label: a named mark's
    aria-label, then the text beside it."""
    parts = [m.attrs["aria-label"] for m in node.kids("svg") if m.attrs.get("aria-label")]
    parts += [c if isinstance(c, str) else c.text() for c in node.children if isinstance(c, str) or c.tag != "svg"]
    return norm(" ".join(parts))


def date_span(value):
    """A YYYY-MM-DD, YYYY-MM or YYYY date as its (first day, last day)."""
    parts = [int(p) for p in value.split("-")]
    if len(parts) == 3:
        day = dt.date(*parts)
        return day, day
    if len(parts) == 2:
        first = dt.date(parts[0], parts[1], 1)
        return first, dt.date(parts[0] + parts[1] // 12, parts[1] % 12 + 1, 1) - dt.timedelta(days=1)
    return dt.date(parts[0], 1, 1), dt.date(parts[0], 12, 31)


def count_label(strings, key, n):
    """An interface count such as "{n} stories", with the "_one" form for one."""
    one = strings.get(key + "_one")
    return (one if n == 1 and one else strings[key]).format(n=n)


def is_vh(node):
    """A visually hidden element, which only screen readers announce."""
    return "vh" in node.classes


def byline_mark_text(model, a, lang):
    """What a list row shows of an article's byline (Site.byline_mark): the automated byline's
    name, such as "verifiable.pro Wire", for an article the site's software drafted, "By
    <name>" for one a person wrote."""
    if a.agent:
        name = model["site"]["agents"][a.agent]["name"]
        return (name.get(lang) or name.get("en", "")) if isinstance(name, dict) else name
    return model["strings"][lang]["byline_by"].format(name=" ".join(a.author.split()))


# ----- reading site.css ------------------------------------------------------

def css_rules(text):
    """The style rules of a stylesheet as (at-rule context, selector, {property: value}),
    with comments removed and @media blocks flattened."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules, stack, buf = [], [], ""
    for ch in text:
        if ch == "{":
            stack.append(norm(buf))
            buf = ""
        elif ch == "}":
            selector = stack.pop() if stack else ""
            if buf.strip():
                decls = {}
                for item in buf.split(";"):
                    prop, colon, value = item.partition(":")
                    if colon:
                        decls[prop.strip().lower()] = norm(value)
                rules.append((tuple(stack), selector, decls))
            buf = ""
        else:
            buf += ch
    return rules


def luminance(hex_colour):
    value = hex_colour.lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    channels = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    high, low = sorted((luminance(a), luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


def saturation(hex_colour):
    """The HSL saturation of a #rrggbb colour, from 0 to 1."""
    value = hex_colour.lstrip("#")
    r, g, b = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return colorsys.rgb_to_hls(r, g, b)[2]


def filtered(hex_colour, css_filter):
    """HEX_COLOUR through a CSS filter list of saturate() and brightness() functions, as #rrggbb,
    applied to the sRGB values in order, as browsers apply the shorthand filter functions."""
    rgb = [int(hex_colour.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    for name, arg in re.findall(r"(saturate|brightness)\(([\d.]+)\)", css_filter):
        s = float(arg)
        if name == "brightness":
            rgb = [c * s for c in rgb]
        else:
            m = [[0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s],
                 [0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s],
                 [0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s]]
            rgb = [sum(m[i][j] * rgb[j] for j in range(3)) for i in range(3)]
        rgb = [min(255.0, max(0.0, c)) for c in rgb]
    return "#" + "".join(f"{round(c):02x}" for c in rgb)


def mix(fg, bg, alpha):
    """The colour of FG drawn at ALPHA over BG, as #rrggbb."""
    f, b = [[int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)] for h in (fg, bg)]
    return "#" + "".join(f"{round(alpha * x + (1 - alpha) * y):02x}" for x, y in zip(f, b))


def js_const(code, name):
    """The source of the arrow function that CODE declares as `const NAME = ... => {`, up to
    the "};" that closes it at the same indentation."""
    start = re.search(r"^( *)const " + re.escape(name) + r" = [^\n]*=> \{$", code, re.M)
    if not start:
        raise AssertionError(f"no const {name} = ... => {{ in the script")
    end = code.index("\n" + start.group(1) + "};", start.end())
    return code[start.start():end + len(start.group(1)) + 3].strip()


def js_function(code, name):
    """The source of the function that CODE declares as `function NAME(...) {`, up to the "}" that
    closes it at the same indentation."""
    start = re.search(r"^( *)function " + re.escape(name) + r"\(", code, re.M)
    if not start:
        raise AssertionError(f"no function {name} in the script")
    end = code.index("\n" + start.group(1) + "}", start.end())
    return code[start.start():end + len(start.group(1)) + 2].strip()


def split_selectors(selector):
    """A selector list split at its top-level commas."""
    parts, depth, current = [], 0, ""
    for ch in selector:
        depth += (ch == "(") - (ch == ")")
        if ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    return parts + [current.strip()]


def expand_is(selector):
    """A selector list as single selectors, each :is() or :where() group written out, so that
    ":is(.a, .b).x" is ".a.x" and ".b.x"."""
    out = []
    for part in split_selectors(selector):
        group = re.search(r":(?:is|where)\(", part)
        if not group:
            out.append(part)
            continue
        depth, end = 1, group.end()
        while depth:
            depth += {"(": 1, ")": -1}.get(part[end], 0)
            end += 1
        for alternative in split_selectors(part[group.end():end - 1]):
            out += expand_is(part[:group.start()] + alternative + part[end:])
    return out


def subjects(selector):
    """The subject compound of each selector in a selector list, with :is() and :where() written
    out and the other parenthesised groups (:not(), :has(), :nth-child()) dropped."""
    found = []
    for part in expand_is(selector):
        while re.search(r"\([^()]*\)", part):
            part = re.sub(r"\([^()]*\)", "", part)
        found.append(re.split(r"[\s>+~]+", part.strip())[-1])
    return found


class MarkdownTests(unittest.TestCase):
    def render(self, text, **kw):
        html, ctx = md.render(text, md.Context(**kw))
        return html, ctx

    def test_front_matter_lists_and_colons(self):
        meta, body = md.parse_front_matter('---\ntitle: "A: B"\ntopics: [a, b]\nsources:\n  - x | y | 2026-01-01 | https://e.org\n---\nBody\n')
        self.assertEqual(meta["title"], "A: B")
        self.assertEqual(meta["topics"], ["a", "b"])
        self.assertEqual(len(meta["sources"]), 1)
        self.assertEqual(body, "Body\n")

    def test_citations_and_links(self):
        html, ctx = self.render("See [docs](https://e.org/a_b).[^1, 2]")
        self.assertIn('href="https://e.org/a_b"', html)
        self.assertIn('href="#source-2"', html)
        self.assertEqual(ctx.cited, ["1", "2"])

    def test_escaping(self):
        html, _ = self.render("<script>alert(1)</script> & `<b>`")
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;b&gt;", html)

    def test_explicit_heading_id_and_callout(self):
        html, ctx = self.render("## Corrections {#corrections}\n\n:::analysis\nText\n:::\n", callout_titles={"analysis": "Why it matters"})
        self.assertIn('<h2 id="corrections">Corrections</h2>', html)
        self.assertIn('class="callout callout-analysis"', html)
        self.assertIn("Why it matters", html)
        self.assertEqual(ctx.headings[0][2], "corrections")

    def test_lists_do_not_merge_across_types(self):
        html, _ = self.render("- [ ] a\n- [x] b\n\n1. one\n2. two\n")
        self.assertIn('<ul class="checklist">', html)
        self.assertIn("<ol>", html)
        self.assertIn("checked", html)

    def test_cjk_lines_join_without_space(self):
        html, _ = self.render("第一行\n第二行")
        self.assertIn("第一行第二行", html)

    def test_site_absolute_links_use_resolver(self):
        html, _ = self.render("[m](/manifest.json)", resolve=lambda t: "../" + t.lstrip("/"))
        self.assertIn('href="../manifest.json"', html)


class ArtTests(unittest.TestCase):
    def test_digest_matches_source_hash(self):
        text = "---\ntitle: x\n---\nbody"
        svg, digest = art.illustration(text, "confidential-computing", "label")
        self.assertEqual(digest, hashlib.sha256(text.encode("utf-8")).hexdigest())
        self.assertTrue(svg.startswith("<svg"))

    def test_deterministic(self):
        a = art.illustration("same", "agents-accountability", "l")[0]
        b = art.illustration("same", "agents-accountability", "l")[0]
        self.assertEqual(a, b)


class LinkTests(unittest.TestCase):
    def site(self, mode):
        model = {"site": {"base_url": "https://verifiable.pro"}, "topics": {"topics": []}, "strings": {}}
        return Site(model, mode)

    def test_preview_links_are_relative(self):
        s = self.site("preview")
        s.current = "/zh/articles/x/"
        self.assertEqual(s.href("/latest/"), "../../../latest/index.html")
        self.assertEqual(s.href("/zh/latest/#news"), "../../latest/index.html#news")
        self.assertEqual(s.root_rel(), "../../../")

    def test_prod_links_are_absolute(self):
        s = self.site("prod")
        s.current = "/articles/x/"
        self.assertEqual(s.href("/latest/"), "/latest/")


class Article:
    """The fields of sitegen.content.Article that the templates read."""

    def __init__(self, **kw):
        self.slug, self.lang, self.title, self.kind = "x", "en", "A title", "news"
        self.topics, self.sources, self.evidence, self.body = ["confidential-computing"], [], [], ""
        self.sha256 = "ab" * 32
        self.__dict__.update(kw)

    @property
    def primary_topic(self):
        return self.topics[0] if self.topics else ""


class TemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = content.load(ROOT)

    def site(self, lang="en", **site_overrides):
        model = dict(self.model)
        model["site"] = dict(self.model["site"], **site_overrides)
        s = Site(model, "preview")
        s.lang = lang
        s.current = "/zh/articles/x/" if lang == "zh" else "/articles/x/"
        return s

    def test_every_string_exists_in_both_languages(self):
        strings = self.model["strings"]
        en = {k for k in strings["en"] if not k.endswith("_one")}
        zh = {k for k in strings["zh"] if not k.endswith("_one")}
        self.assertEqual(sorted(en - zh), [])
        self.assertEqual(sorted(zh - en), [])

    def test_every_new_interface_string_is_filled_in_both_languages(self):
        for lang in content.LANGS:
            strings = self.model["strings"][lang]
            missing = [key for key in NEW_STRINGS if not str(strings.get(key, "")).strip()]
            self.assertEqual(missing, [], lang)
        zh = self.model["strings"]["zh"]
        # Chinese calls trust tiers 档 and stack layers 层
        self.assertIn("档", zh["tier_n"])
        self.assertIn("档", zh["topic_tiers"])
        self.assertIn("层", zh["layers_title"])
        self.assertNotIn("档", zh["layers_title"])

    def test_placeholders_survive_translation(self):
        """The templates fill each placeholder, such as {n}, {name} or {lo}, in both languages;
        a "_one" variant may spell its number out instead."""
        strings = self.model["strings"]

        def names(text):
            return set(re.findall(r"\{(\w+)\}", text))

        for key, en in strings["en"].items():
            if not key.endswith("_one"):
                with self.subTest(key=key):
                    self.assertEqual(names(strings["zh"][key]), names(en))
        for lang in content.LANGS:  # the hero's layer cards, chain legend and progress fill these
            self.assertEqual(names(strings[lang]["hero_more"]), {"name"}, lang)
            self.assertEqual(names(strings[lang]["hero_chain_run"]), {"lo", "hi"}, lang)
            self.assertEqual(names(strings[lang]["hero_progress"]), {"n", "total"}, lang)
            self.assertEqual(names(strings[lang]["hero_progress_done"]), {"total"}, lang)

    def test_hero_words_follow_how_the_chain_is_drawn(self):
        """The kicker and the scene's description never contradict the chain drawn at rest
        (owner decisions 1 and 2): drawn by binding status, nothing calls it unbroken."""
        en, zh = self.model["strings"]["en"], self.model["strings"]["zh"]
        if render.HERO_CHAIN_REST == "status":
            self.assertNotIn("unbroken", en["home_kicker"].lower())
            self.assertNotIn("不断", zh["home_kicker"])
            for words in ("solid where", "dashed where", "broken where"):
                self.assertIn(words, en["hero_scene_desc"])
            for words in ("实线", "虚线", "断开"):
                self.assertIn(words, zh["hero_scene_desc"])
        else:
            self.assertEqual(render.HERO_CHAIN_REST, "whole")
            self.assertIn("ends at the seal", en["hero_scene_desc"])
            self.assertIn("止于印章", zh["hero_scene_desc"])

    def test_tee_path_counts_follow_its_published_steps(self):
        """"Learn TEEs in five steps" on the home pages and "Read these five articles" on Learn
        count the path's published steps in words, so publishing a planned step changes both."""
        path = self.model["tee"]["path"]
        on_path = {step.get("article") for step in path}
        extra = next(a.slug for a in self.model["articles"]["en"] if a.slug not in on_path)
        first = next(i for i, step in enumerate(path) if "planned" in step)
        grown = path[:first] + [{"article": extra}] + path[first + 1:]
        published = sum(1 for step in path if "article" in step)
        for steps, n in ((path, published), (grown, published + 1)):
            model = dict(self.model, tee=dict(self.model["tee"], path=steps))
            for lang in content.LANGS:
                s, strings = Site(model, "preview"), self.model["strings"][lang]
                s.lang = lang
                arts = model["articles"][lang]
                block = parse_html(s.home(arts)[1]).find("section", cls="tee-block")
                self.assertEqual(block.find_all("h3", cls="mini-title")[-1].text(),
                                 norm(strings["tee_block_path"].format(n=discover.count_word(n, lang))), (lang, n))
                self.assertEqual(len(block.find("ol", cls="path-mini").kids("li")), n, (lang, n))
                dek = parse_html(s.learn(arts)[1]).find("section", id="tee-path").find("p", cls="block-dek")
                self.assertEqual(dek.text(), norm(strings["learn_path_dek"].format(n=discover.count_word(n, lang))),
                                 (lang, n))
        self.assertEqual([discover.count_word(n, "zh") for n in (1, 2, 5, 10, 12, 20, 21)],
                         ["一", "两", "五", "十", "十二", "二十", "二十一"])
        self.assertEqual([discover.count_word(n) for n in (5, 8, 11)], ["five", "eight", "11"])

    def test_checked_line_drops_citations_and_stops_at_the_first_sentence(self):
        body = ("Text.\n\n:::checked\nOn 20 October 2026 we read the U.S. agency's notice (version 1.0)[^1, 2] "
                "and the [standard](https://e.org).[^3] We did not test it.\n:::\n")
        line = self.site().checked_line(Article(body=body))
        self.assertEqual(line, "On 20 October 2026 we read the U.S. agency's notice (version 1.0) and the standard.")
        zh = Article(lang="zh", body=":::checked\n我们于 2026 年 10 月 20 日阅读了公告。[^1]我们没有测试系统。\n:::\n")
        self.assertEqual(self.site("zh").checked_line(zh), "我们于 2026 年 10 月 20 日阅读了公告。")
        self.assertEqual(self.site().checked_line(Article(body="No callout here.")), "")

    def test_check_strip_without_repository_falls_back_to_policy_and_email(self):
        out = self.site(repo_url="").check_strip(Article())
        self.assertNotIn("github.com", out)
        self.assertIn("#corrections", out)
        self.assertIn(self.model["site"]["contact_email"], out)

    def test_check_strip_with_repository_prefills_a_correction_issue(self):
        out = self.site(repo_url="https://github.com/o/r/", repo_branch="main").check_strip(Article(slug="s", lang="zh"))
        self.assertIn('href="https://github.com/o/r/issues/new?template=correction.yml&amp;', out)
        self.assertIn("page=https%3A%2F%2Fverifiable.pro%2Fzh%2Farticles%2Fs%2F", out)
        self.assertIn("&amp;digest=" + Article(slug="s", lang="zh").sha256 + "&amp;", out)  # fills the form's digest field
        self.assertIn('href="https://github.com/o/r/edit/main/content/articles/s/zh.md"', out)
        home = self.site(repo_url="https://github.com/o/r").check_strip()
        self.assertIn('data-copy="python3 tools/verify_manifest.py https://verifiable.pro"', home)

    def test_chat_config_cannot_end_its_script_element(self):
        model = dict(self.model)
        model["strings"] = dict(self.model["strings"], en=dict(self.model["strings"]["en"], chat_title="</script><!-- <b>"))
        model["site"] = dict(self.model["site"], chat={"mode": "demo"})
        s = Site(model, "preview")
        s.lang, s.current = "en", "/articles/x/"
        block = s.chat_config("/articles/x/")
        body = CHAT_CONFIG_RE.fullmatch(block).group(1)
        self.assertNotIn("<", body)
        self.assertEqual(json.loads(body)["strings"]["chat_title"], "</script><!-- <b>")

    def test_jsonld_cannot_end_or_upset_its_script_element(self):
        s = Site(self.model, "preview")
        s.lang, s.current = "en", "/articles/x/"
        title = "A </script> and <!--<script> title"
        page = s.layout(path="/articles/x/", title="x", description="x", section="latest", body="<p>BODY</p>",
                        alt_path="/zh/", page_class="page-article", jsonld={"headline": title})
        blob = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S).group(1)
        self.assertNotIn("<", blob)
        self.assertEqual(json.loads(blob)["headline"], title)

    def test_every_literal_chat_string_in_chat_js_exists(self):
        js = (ROOT / "static" / "chat.js").read_text(encoding="utf-8")
        keys = {k for k in re.findall(r"[\"'](chat_[a-z0-9_]+)[\"']", js) if not k.endswith("_")}
        self.assertTrue(keys)
        for lang in content.LANGS:
            self.assertEqual(sorted(keys - set(self.model["strings"][lang])), [], lang)

    # ----- the stack, tags and hero -------------------------------------------
    def test_tags_link_layers_to_the_stack_and_mark_tees(self):
        stack = [layer["id"] for layer in self.model["topics"]["stack"]]
        s = self.site()
        # front-matter layers come back in stack order, T7 first
        self.assertEqual(s.layers_of(Article(layers=["hardware", "runtime"])), ["runtime", "hardware"])
        # without the field, the layers that list the primary topic; [] names none
        cc = [layer["id"] for layer in self.model["topics"]["stack"] if TEE in layer.get("topics", [])]
        self.assertTrue(cc)
        self.assertEqual(s.layers_of(Article(topics=[TEE])), cc)
        self.assertEqual(s.layers_of(Article(layers=[])), [])
        self.assertEqual(s.tags(Article(layers=[], topics=["supply-chain"])), "")

        # the TEE topic may be a mechanism listed second, as on EigenAI's brief
        en = self.model["strings"]["en"]
        a = Article(layers=["hardware", "runtime"], topics=["verifiable-inference", TEE])
        tags = parse_html(s.tags(a)).find("span", cls="tags")
        codes = tags.find("a", cls="tag-layers")
        names = [s.t(s.layer(lid)["name"]) for lid in ("runtime", "hardware")]
        expected_codes = [f"T{len(stack) - stack.index(lid)}" for lid in ("runtime", "hardware")]
        shown = [n for n in codes.kids("span") if n.attrs.get("aria-hidden") == "true"]
        self.assertEqual([n.text() for n in shown], [" ".join(expected_codes)])
        # the codes link to the first layer on the Stack page and name the layers for the stack card
        self.assertTrue(codes.attrs["href"].endswith("#layer-runtime"), codes.attrs["href"])
        self.assertEqual(codes.attrs["data-layers"], "runtime hardware")
        self.assertEqual(codes.find("span", cls="vh").text(), norm(en["tag_layers_vh"].format(names=en["list_comma"].join(names))))
        label = tags.find("span", cls="tag-tee")
        self.assertEqual((label.text(), label.attrs["title"], label.attrs.get("aria-hidden")), (en["tag_tee"], en["tag_tee_name"], "true"))
        self.assertIn(en["tag_tee_name"] + ".", [n.text() for n in tags.find_all("span", cls="vh")])
        # the layer link is the tags' only tab stop
        self.assertEqual([n.tag for n in tags.iter() if n.tag in ("a", "button") or "tabindex" in n.attrs], ["a"])
        self.assertNotIn("tag-tee", s.tags(Article(layers=["outputs"], topics=["verifiable-inference"])))

        zh = parse_html(self.site("zh").tags(a)).find("span", cls="vh").text()
        self.assertTrue(zh.startswith("验证栈层级：") and zh.endswith("。"), zh)

    def hero_site(self, lang="en", model=None):
        """A Site on the home page in LANG with the hero scene and anchors that build.py reads."""
        s = Site(model or self.model, "preview")
        s.lang, s.current = lang, "/zh/" if lang == "zh" else "/"
        s.hero_svg = build.hero_svg()
        s.hero_anchors = build.hero_anchors(s.hero_svg, len(self.model["topics"]["stack"]))
        return s

    def test_hero_scene_carries_no_text_and_keeps_to_its_own_names(self):
        template = build.hero_svg()
        svg = parse_html(template).find("svg")
        self.assertEqual((svg.attrs.get("role"), svg.attrs.get("viewbox")), ("img", "-28 0 382 597"))
        self.assertEqual(svg.find_all(("text", "image", "script", "foreignobject")), [])
        self.assertNotIn("font-family", template)
        self.assertEqual([n.text() for n in svg.kids(("title", "desc"))], ["{{SCENE_TITLE}}", "{{SCENE_DESC}}"])
        # the description's sentences on the gray and the data, which hero.js adds once it runs
        self.assertEqual([n.attrs.get("data-hv-live") for n in svg.kids("desc")], ["{{SCENE_DESC_LIVE}}"])
        # named by its title and described by its description, so the name stays short
        title, desc = svg.kids("title"), svg.kids("desc")
        labelled = svg.attrs.get("aria-labelledby", "").split() + svg.attrs.get("aria-describedby", "").split()
        self.assertEqual(svg.attrs.get("aria-labelledby", "").split(), [n.attrs["id"] for n in title])
        self.assertEqual(svg.attrs.get("aria-describedby", "").split(), [n.attrs["id"] for n in desc])
        # inlined into the page, its classes, ids, keyframes and custom properties carry the
        # hv- prefix, so its own <style> cannot reach the page's elements
        self.assertEqual(sorted({c for n in svg.iter() for c in n.classes} - {"hero-scene"} - {
            c for n in svg.iter() for c in n.classes if c.startswith("hv-")}), [])
        ids = {n.attrs["id"] for n in svg.iter() if "id" in n.attrs} - set(labelled)
        self.assertEqual(sorted(i for i in ids if not i.startswith("hv-")), [])
        style = "".join(n.raw() for n in svg.find_all("style"))
        selectors = re.sub(r"/\*.*?\*/", "", style, flags=re.S)  # a comment may name a file, such as flow.py
        while "{" in selectors:
            selectors = re.sub(r"\{[^{}]*\}", ";", selectors)
        self.assertEqual(sorted({c for c in re.findall(r"\.(-?[A-Za-z_][\w-]*)", selectors) if not c.startswith("hv-")}), [])
        self.assertEqual(sorted({k for k in re.findall(r"@keyframes\s+([\w-]+)", style) if not k.startswith("hv-")}), [])
        # every custom property it sets is its own; the only page tokens it reads are your palette
        # (--you-*, from site.css's three theme blocks), each with the scene's own value after it, so
        # the scene still draws you when it stands alone
        self.assertEqual(sorted({v for v in re.findall(r"(?<![\w-])--([\w-]+)\s*:", style) if not v.startswith("hv-")}), [])
        read = set(re.findall(r"var\(--([\w-]+)", style))
        self.assertEqual(sorted(v for v in read if not v.startswith(("hv-", "you-"))), [])
        self.assertTrue({v for v in read if v.startswith("you-")})
        self.assertEqual(re.findall(r"var\(--you-[\w-]+\)", style), [])  # never without a fallback

    def test_hero_fills_its_slots_escaped(self):
        model = dict(self.model)
        model["strings"] = dict(self.model["strings"], en=dict(self.model["strings"]["en"], hero_scene_title='A <b> & "q"'))
        out = self.hero_site(model=model).hero()
        self.assertIn("A &lt;b&gt; &amp; &quot;q&quot;", out)
        self.assertNotIn("{{", out)
        self.assertEqual(parse_html(out).find("svg", cls="hero-scene").find("desc").text(), norm(self.model["strings"]["en"]["hero_scene_desc"]))
        self.assertEqual(Site(self.model, "preview").hero(), "")  # no scene, no hero
        # the description says what the still scene shows; its data-hv-live holds the sentences that
        # hero.js adds once it runs, after a space in English and none in Chinese
        for lang, gap in (("en", " "), ("zh", "")):
            desc = parse_html(self.hero_site(lang).hero()).find("svg", cls="hero-scene").find("desc")
            strings = self.model["strings"][lang]
            self.assertEqual((desc.text(), html.unescape(desc.attrs.get("data-hv-live", ""))),
                             (norm(strings["hero_scene_desc"]), gap + strings["hero_scene_desc_live"]), lang)

    def test_hero_labels_follow_the_stack_with_icons_marks_and_leaders(self):
        stack = self.model["topics"]["stack"]
        tee = [layer["id"] for layer in stack if layer["tee"]["reach"] == "direct"]
        # a mark's own name is one string, or an {en, zh} pair where the editions write it apart
        titles = {t for logo in logos.LOGOS.values()
                  for t in ([logo["title"]] if isinstance(logo["title"], str) else logo["title"].values())}
        # a mark shown alone may carry its product's name ("OpenAI Codex")
        named = {s_ for layer in self.model["topics"]["stack"] for e in layer["hero"]["examples"] if "name" in e
                 for s_ in ([e["name"]] if isinstance(e["name"], str) else e["name"].values())}
        for lang in content.LANGS:
            s = self.hero_site(lang)
            rel = LANG_DIR[lang] + "index.html"
            figure = parse_html(s.hero()).find("figure", cls="hero-visual")
            ol = figure.find("ol", cls="hero-layers")
            self.assertEqual(ol.attrs.get("aria-label"), self.model["strings"][lang]["hero_layers_label"], lang)
            rows = ol.kids("li")
            # seven rows, T7 first: the code and short name ("T7 Policy", which screen readers hear as
            # "T7, Policy") link to the layer on the Stack page, and the link is the row's first (the
            # card's stories link comes after it)
            sep = self.model["strings"][lang]["hero_code_sep"]
            self.assertEqual([r.find("a").text() for r in rows],
                             [norm(f"T{len(stack) - i}{sep}{layer['hero']['short'][lang]}") for i, layer in enumerate(stack)])
            self.assertTrue(all("hero-layer-link" in r.find("a").classes for r in rows), lang)
            self.assertEqual([canonical(rel, r.find("a").attrs["href"]) for r in rows],
                             [loc("/topics/", lang) + "#layer-" + layer["id"] for layer in stack])
            # set down the stage in that order, at the anchors' heights
            heights = [float(re.search(r"--ly:([\d.]+)%", r.attrs.get("style", "")).group(1)) for r in rows]
            self.assertEqual(heights, sorted(heights))
            self.assertTrue(all(0 < h < 100 for h in heights), heights)
            # only the layers where a TEE gives direct evidence carry the TEE label
            self.assertEqual([layer["id"] for layer, r in zip(stack, rows) if r.find("span", cls="tag-tee")], tee)
            self.assertEqual(["is-tee" in r.classes for r in rows], [layer["id"] in tee for layer in stack])
            for i, (layer, row) in enumerate(zip(stack, rows)):
                self.assertEqual(row.find("svg", cls="hero-layer-icon").attrs.get("aria-hidden"), "true")
                # the icon, then in the name link the layer's code as a prefix of its own, the separator
                # that only screen readers hear, and the short name; the layer card repeats the code
                link = row.find("a", cls="hero-layer-link")
                code, hidden = link.kids()[:2]
                self.assertEqual((kind_of(code, ("hero-layer-code",)), code.text()), ("hero-layer-code", f"T{len(stack) - i}"), layer["id"])
                self.assertEqual((hidden.classes, hidden.text()), ({"vh"}, norm(sep)), layer["id"])
                self.assertEqual(norm(link.children[-1]), norm(layer["hero"]["short"][lang]), layer["id"])
                self.assertEqual([kind_of(k, ("hero-layer-icon", "hero-layer-link")) for k in row.find("span", cls="hero-layer-head").kids()][:2],
                                 ["hero-layer-icon", "hero-layer-link"], layer["id"])
                # the examples in order: a named mark, a name, or a mark beside the name it shows
                expected = []
                for example in layer["hero"]["examples"]:
                    text = s.t(example.get("text"))
                    title = (s.t(example.get("name")) or s.t(logos.LOGOS[example["logo"]]["title"])) if example.get("logo") else ""
                    expected.append(norm(text if text.startswith(title) else f"{title} {text}"))
                self.assertEqual([example_name(n) for n in row.find_all("span", cls="hero-ex")], expected, layer["id"])
            for mark in ol.find_all("svg", cls="hero-logo"):
                if mark.attrs.get("aria-hidden") == "true":
                    self.assertTrue(mark.parent.text(), mark)
                else:
                    self.assertEqual(mark.attrs.get("role"), "img", mark)
                    self.assertIn(mark.attrs.get("aria-label"), titles | named)
                # no <title>: the browser's own tooltip would show beside the one hero.js shows, which
                # takes the mark's aria-label, and no mark takes a tab stop
                self.assertEqual(mark.find_all("title"), [], mark)
                self.assertNotIn("tabindex", mark.attrs, mark)
            # the note that the logos and names are examples, not endorsements, for screen readers only,
            # right before the list; nothing on the page says it in view (About does)
            stage = figure.find("div", cls="hero-stage")
            note = stage.find("p", id="hero-layers-note")
            self.assertEqual((note.classes, note.text()), ({"vh"}, norm(self.model["strings"][lang]["hero_layers_note"])), lang)
            self.assertIs(stage.kids()[stage.kids().index(ol) - 1], note, lang)
            # the one tooltip that names a mark: shipped hidden, empty and aria-hidden, after the links
            tips = figure.find_all(cls="hero-tip")
            self.assertEqual([(t.tag, t.attrs.get("aria-hidden"), "hidden" in t.attrs, t.text()) for t in tips],
                             [("span", "true", True, "")], lang)
            self.assertEqual(kind_of(figure.kids()[-1], ("hero-tip",)), "hero-tip", lang)
            # one leader line per row, hidden from screen readers. Each starts at its plate's right
            # corner at half the plate's thickness, where the plate's hit area in the scene has it,
            # counted from the viewBox's corner (the scene starts left of 0, where the person stands)
            # as a percentage of the stage (the scene is HERO_ART percent of its width), and left of
            # where the cards start, so a card never covers a plate
            leaders = figure.find("svg", cls="hero-leaders")
            self.assertEqual(leaders.attrs.get("aria-hidden"), "true")
            self.assertEqual(len(leaders.kids("g", cls="hero-leader")), len(stack))
            scene = figure.find("svg", cls="hero-scene")
            x0, y0, width, height = (float(v) for v in scene.attrs["viewbox"].split())
            plates = {int(p.attrs["data-hv-n"]): path_points(p.attrs["d"].split("Z")[0])
                      for p in scene.find_all("path", cls="hv-hit")}

            def corner(points):
                right = max(x for x, y in points)
                edge = [y for x, y in points if abs(x - right) < 1e-6]
                return right, (min(edge) + max(edge)) / 2
            dots = [g.find("path", cls="hero-leader-dot").attrs["d"] for g in leaders.kids("g", cls="hero-leader")]
            self.assertEqual(dots, [f"M{(x - x0) / width * render.HERO_ART:.2f} {(y - y0) / height * 100:.2f}h0"
                                    for x, y in (corner(plates[n]) for n in range(len(stack), 0, -1))])
            self.assertTrue(all(0 < float(d[1:].split()[0]) < render.HERO_CARD for d in dots), dots)

    def test_hero_marks_are_named_in_the_page_language(self):
        """Every vendor mark in the hero's labels is named in the page language: its aria-label, which
        screen readers hear and hero.js shows in the tooltip, and its name in the card's Examples line
        on touch screens. The Chinese edition keeps company and product names in their original form
        (NVIDIA, Apple, Model Context Protocol), each in a lang="en" island for screen reader voices,
        but writes the European Union as 欧盟, as its articles do, and a name that adds words to a
        mark in Chinese. So each of the marks on the Chinese page carries its English name but for
        these, which sitegen/logos.py ({en, zh} titles) and topics.json ({en, zh} names) give."""
        chinese = {"European Union": "欧盟", "Pi coding agent": "Pi 编程智能体",
                   "OpenAI (C2PA on generated images)": "OpenAI（生成的图像附带 C2PA 信息）",
                   "Meta (AI labels)": "Meta（AI 标签）", "TikTok (AI labels)": "TikTok（AI 标签）"}
        stack = self.model["topics"]["stack"]
        count = sum(1 for layer in stack for example in layer["hero"]["examples"] if "logo" in example)
        marks, cards = {}, {}
        for lang in content.LANGS:
            figure = parse_html(self.hero_site(lang).hero()).find("figure", cls="hero-visual")
            marks[lang] = [(m.attrs.get("aria-label"), m.attrs.get("lang")) for m in figure.find_all("svg", cls="hero-logo")]
            cards[lang] = figure.find("li", id="hero-layer-institutions").find("p", cls="hc-names").text()
        self.assertEqual(len(marks["en"]), count)
        self.assertEqual([lang for _, lang in marks["en"]], [None] * count)
        self.assertEqual(marks["zh"], [(chinese.get(name, name), None if name in chinese else "en") for name, _ in marks["en"]])
        self.assertLessEqual(set(chinese), {name for name, _ in marks["en"]})
        # the EU's mark beside its text: "European Union AI Act", 欧盟 AI Act
        self.assertIn("European Union AI Act", cards["en"])
        self.assertIn("欧盟 AI Act", cards["zh"])
        self.assertNotIn("European Union", cards["zh"])

    def test_hero_cards_carry_each_layer_in_both_languages(self):
        """Each layer row holds its layer card: what the Stack page's table says about the layer, who
        checks its claim and with what evidence, and the layer's stories, linked to that view of
        Latest (the card's one link). The name link is described by the card's claim and "Who checks".
        Each language is rendered again with no stories, when every card says it has none yet and has
        no link (today every layer has stories, so that branch runs only here)."""
        stack = self.model["topics"]["stack"]
        tiers = {t["id"]: t for t in self.model["tiers"]["tiers"]}
        parts = ("hero-layer-head", "hero-examples", "hero-who-line", "hero-card")
        for lang, arts in [(lang, arts) for lang in content.LANGS for arts in (self.model["articles"][lang], ())]:
            s, strings = self.hero_site(lang), self.model["strings"][lang]
            rel, colon = LANG_DIR[lang] + "index.html", strings["label_colon"]
            figure = parse_html(s.hero(arts)).find("figure", cls="hero-visual")
            rows = figure.find("ol", cls="hero-layers").kids("li", cls="hero-layer")
            self.assertEqual(len(rows), len(stack), lang)
            for i, (row, layer) in enumerate(zip(rows, stack)):
                n, lid = len(stack) - i, layer["id"]
                where = (lang, lid, f"{len(arts)} stories")
                tee, bind = layer["tee"], layer.get("bind")
                self.assertEqual((row.attrs.get("id"), row.attrs.get("data-n"), row.attrs.get("data-layer")),
                                 (f"hero-layer-{lid}", str(n), lid), where)
                # a card opens below the labels of T4 to T7 and above those of T1 to T3
                self.assertEqual(row.attrs.get("data-place"), "up" if n <= 3 else "down", where)
                # the label, the examples, "Who checks" (phones show it at rest), then the card
                self.assertEqual([kind_of(kid, parts) for kid in row.kids()], list(parts), where)
                self.assertEqual(row.find("p", cls="hero-who-line").text(),
                                 norm(strings["checkers_label"] + colon + s.t(layer["checkers"])), where)
                card = row.find("div", cls="hero-card")
                self.assertEqual(card.attrs.get("id"), f"hero-card-{lid}", where)
                # no heading, so the page outline stays the h1, then "Latest news"
                self.assertEqual(card.find_all(("h1", "h2", "h3", "h4", "h5", "h6")), [], where)
                # the code (an indigo chip where a TEE gives direct evidence: the row is .is-tee) and the full name,
                # read as "T4, Outputs & content", like the label's name
                head = card.find("p", cls="hc-head")
                self.assertEqual(head.find("span", cls="hc-code").text(), f"T{n}", where)
                self.assertEqual(head.find("span", cls="hc-name").text(), norm(s.t(layer["name"])), where)
                self.assertEqual(head.text(), norm(f"T{n}{strings['hero_code_sep']}{s.t(layer['name'])}"), where)
                self.assertEqual("is-tee" in row.classes, tee["reach"] == "direct", where)
                # the claim, labelled for screen readers only
                claim = card.find("p", cls="hc-claim")
                self.assertEqual(claim.find("span", cls="vh").text(), norm(strings["stack_claim"] + colon), where)
                self.assertEqual(claim.text(skip=lambda node: "vh" in node.classes), norm(s.t(layer["claim"])), where)
                # who checks, and with what evidence
                who = card.find("p", cls="hc-who")
                self.assertEqual(who.find("span", cls="hc-label").text(), norm(strings["checkers_label"] + colon), where)
                self.assertEqual(who.text(skip=lambda node: "hc-label" in node.classes), norm(s.t(layer["checkers"])), where)
                self.assertEqual([svg.attrs.get("aria-hidden") for svg in who.find_all("svg")], ["true"], where)
                # kept to a glance: what a TEE shows, on the TEE layers only; no binding, no other evidence
                line = card.find("p", cls="hc-tee")
                if tee["reach"] == "direct":
                    self.assertEqual(line.attrs.get("data-reach"), "direct", where)
                    self.assertEqual(line.find("span", cls="hc-label").text(), norm(strings["stack_with_tee"] + colon), where)
                    self.assertEqual(line.text(skip=lambda node: "hc-label" in node.classes), norm(s.t(tee["short"])), where)
                else:
                    self.assertIsNone(line, where)
                self.assertEqual(card.find_all("p", cls="hc-bind") + card.find_all("p", cls="hc-others"), [], where)
                # the examples' names, which the stylesheet shows on touch screens only: as a screen reader
                # hears them in the label (a mark's aria-label, then its text), hidden from screen readers here
                names = card.find("p", cls="hc-names")
                self.assertEqual(names.attrs.get("aria-hidden"), "true", where)
                self.assertEqual(names.find("span", cls="hc-label").text(), norm(strings["hero_card_examples"] + colon), where)
                self.assertEqual(names.text(skip=lambda node: "hc-label" in node.classes),
                                 norm(strings["list_comma"].join(example_name(x) for x in row.find_all("span", cls="hero-ex"))), where)
                self.assertEqual(names.find_all(("a", "button")), [], where)
                # the stories at the layer, the card's one link, to that view of Latest; or none yet
                at = [a for a in arts if lid in s.layers_of(a)]
                n_tee = sum(1 for a in at if s.is_tee(a))
                foot = card.find("p", cls="hc-foot")
                links = card.find_all("a")
                if at:
                    label = count_label(strings, "stack_cover", len(at))
                    label += " · " + strings["stack_cover_tee"].format(n=n_tee) if n_tee else ""
                    self.assertEqual([a.classes for a in links], [{"hc-count"}], where)
                    self.assertTrue(links[0].within(foot), where)
                    self.assertEqual(canonical(rel, links[0].attrs["href"]), loc("/latest/", lang) + f"#t{n}", where)
                    self.assertEqual(links[0].text(), norm(label), where)
                else:
                    self.assertEqual(links, [], where)
                    self.assertEqual(foot.find("span", cls="hc-count").text(), norm(strings["hero_card_none"]), where)
                # the cue that a click on the card opens the Stack page, for sighted readers only
                cue = foot.find("span", cls="hc-open")
                self.assertEqual((cue.attrs.get("aria-hidden"), cue.text()), ("true", norm(strings["hero_card_open"] + " →")), where)
                # the name link is described by the card's claim and "Who checks" line
                described = row.find("a", cls="hero-layer-link").attrs.get("aria-describedby", "").split()
                self.assertEqual(described, [f"hero-card-{lid}-claim", f"hero-card-{lid}-who"], where)
                self.assertEqual([card.find(id=ref) for ref in described], [claim, who], where)
            # the tab order: the pause control and "Check all layers" in its place (one of the two
            # shows), then each layer's name and (hidden until hero.js runs) chevron, then its stories
            # link if it has stories, then the two links under the stage; the vendor marks add none
            order = [kind_of(node, ("verification-motion", "hero-all", "hero-layer-link", "hero-more", "hc-count"))
                     for node in figure.iter() if node.tag in ("a", "button")]
            expected = ["verification-motion", "hero-all"]
            for layer in stack:
                expected += ["hero-layer-link", "hero-more"] + (["hc-count"] if any(layer["id"] in s.layers_of(a) for a in arts) else [])
            self.assertEqual(order, expected + ["a", "a"], (lang, len(arts)))

    def test_hero_person_legend_and_hint(self):
        """The stage reads as a phone shows it: the scene, the leader lines, the label of the person
        in the scene, the hint, the note on the logos (for screen readers), the layer rows and the
        legend of the chain. The hint is the stage's own child, after the person's label rather than
        in it, so that from 45em the stylesheet can stand it under the label column, beside that
        label; it ships hidden for hero.js to show. The icon and the legend's samples are hidden from
        screen readers. Each of the label, the hint and the legend keeps to a short line: the
        figure has no caption, and the legend no note."""
        for lang in content.LANGS:
            strings = self.model["strings"][lang]
            figure = parse_html(self.hero_site(lang).hero()).find("figure", cls="hero-visual")
            stage = figure.find("div", cls="hero-stage")
            parts = ("hero-art", "hero-leaders", "hero-person", "hero-hint", "vh", "hero-layers", "hero-chain")
            self.assertEqual([kind_of(kid, parts) for kid in stage.kids()], list(parts), lang)
            # the links follow the stage, and no caption: what the scene shows is in its description
            self.assertEqual([kind_of(kid, ("hero-stage", "hero-links", "hero-tip")) for kid in figure.kids()][-3:],
                             ["hero-stage", "hero-links", "hero-tip"], lang)
            self.assertEqual(figure.find_all("figcaption"), [], lang)
            # the person's label: who the figure stands for, with the reader's progress on its name line
            person = stage.find("div", cls="hero-person")
            self.assertEqual([kind_of(kid, ("hero-person-head", "hero-person-who")) for kid in person.kids()],
                             ["hero-person-head", "hero-person-who"], lang)
            head = person.kids()[0]
            self.assertEqual([kind_of(kid, ("hero-person-name", "hero-progress")) for kid in head.kids()],
                             ["hero-person-name", "hero-progress"], lang)
            name = person.find("p", cls="hero-person-name")
            self.assertEqual(name.text(), norm(strings["hero_person"]), lang)
            self.assertEqual([svg.attrs.get("aria-hidden") for svg in name.find_all("svg")], ["true"], lang)
            who = person.find("p", cls="hero-person-who")
            self.assertEqual(who.text(skip=lambda node: "hero-complete" in node.classes), norm(strings["hero_person_who"]), lang)
            complete = who.find("span", cls="hero-complete")
            self.assertEqual(complete.text(), norm(strings["hero_complete"]), lang)
            self.assertIn("hidden", complete.attrs, lang)
            self.assertEqual(complete.attrs.get("aria-hidden"), "true", lang)
            # the hint: the stage's own p.hero-hint, the only one in the figure. It holds two states,
            # until every layer is checked and after, each with a line for each way of opening a
            # layer: pointing or Tab, a tap on the arrow, a click on it
            hint = stage.kids()[parts.index("hero-hint")]
            self.assertTrue(hint.matches("p", "hero-hint"), lang)
            self.assertEqual(figure.find_all("p", cls="hero-hint"), [hint], lang)
            self.assertIn("hidden", hint.attrs, lang)
            self.assertEqual([kind_of(kid, ("hero-hint-todo", "hero-hint-done")) for kid in hint.kids()],
                             ["hero-hint-todo", "hero-hint-done"], lang)
            for state, suffix in zip(hint.kids(), ("", "_done")):
                modes = ("hero-hint-pointer", "hero-hint-touch", "hero-hint-click")
                self.assertEqual([kind_of(kid, modes) for kid in state.kids()], list(modes), (lang, suffix))
                self.assertEqual([kid.text() for kid in state.kids()],
                                 [norm(strings[k + suffix]) for k in ("hero_hint", "hero_hint_touch", "hero_hint_click")], (lang, suffix))
            # the legend: a title, then one line per run with a sample of the line in each; what a break
            # means is on the Stack page
            legend = stage.find("div", cls="hero-chain")
            self.assertEqual([kind_of(kid, ("hero-chain-title", "hero-chain-runs")) for kid in legend.kids()],
                             ["hero-chain-title", "hero-chain-runs"], lang)
            self.assertEqual(legend.find("p", cls="hero-chain-title").text(), norm(strings["hero_chain_title"]), lang)
            items = legend.find("ul", cls="hero-chain-runs").kids("li")
            self.assertTrue(items, lang)
            for li in items:
                samples = li.kids("svg", cls="hero-chain-sample")
                self.assertEqual([svg.attrs.get("aria-hidden") for svg in samples], ["true"], lang)
                self.assertEqual(li.find("span", cls="hero-sep").attrs.get("aria-hidden"), "true", lang)
                # read as "In use: T1 to T2"
                self.assertEqual(li.find("span", cls="vh").text(), norm(strings["label_colon"]), lang)
            # the figure has no heading; its pictures are the scene and the vendor marks
            self.assertEqual(figure.find_all(("h1", "h2", "h3", "h4", "h5", "h6")), [], lang)
            self.assertEqual([p.classes for p in images(figure) if "hero-logo" not in p.classes], [{"hero-scene", "hv-scene"}], lang)

    def test_hero_person_is_the_reader_talking_with_the_system(self):
        """The person in the scene is the reader, talking with an AI system: the label under the
        scene, the hint and the scene's title and description speak to "you" (你) in both
        languages, the label says in one short line that the reader's prompts and data pass
        through all seven layers (the dotted route), and no string calls the person a checker
        outside the provider any more. The cards' "Who checks" lines keep naming the real
        checkers."""
        you = {"en": r"\b[Yy]our?\b", "zh": "你"}
        keys = ("hero_person", "hero_person_who", "hero_hint", "hero_hint_touch", "hero_scene_title", "hero_scene_desc")
        for lang in content.LANGS:
            strings = self.model["strings"][lang]
            for key in keys:
                self.assertRegex(strings[key], you[lang], (lang, key))
            text = " ".join(strings[k] for k in keys)
            for retired in ("outside the provider who check", "Users, customers, developers", "a person who checks",
                            "服务商以外的核查者", "用户、客户、开发者", "一位核查它们的人"):
                self.assertNotIn(retired, text, lang)
        en, zh = self.model["strings"]["en"], self.model["strings"]["zh"]
        self.assertIn("prompts and data", en["hero_person_who"])
        self.assertIn("all seven layers", en["hero_person_who"])
        self.assertIn("提示词和数据", zh["hero_person_who"])
        self.assertIn("全部七层", zh["hero_person_who"])
        # one sentence, short enough for one line under the person on a phone
        self.assertLessEqual(len(en["hero_person_who"]), 60)
        self.assertLessEqual(len(zh["hero_person_who"]), 20)
        self.assertEqual((en["hero_person_who"].count(". "), zh["hero_person_who"].count("。")), (0, 1))
        # Chinese sets a space between Chinese and Latin letters (和 AI), and full-width punctuation
        for key in keys:
            self.assertIsNone(re.search(r"[\u4e00-\u9fff][A-Za-z]|[A-Za-z][\u4e00-\u9fff]", zh[key]), key)
            self.assertIsNone(re.search(r"[\u4e00-\u9fff][,.;:!?]", zh[key]), key)
        for layer in self.model["topics"]["stack"]:
            self.assertTrue(layer["checkers"]["en"] and layer["checkers"]["zh"], layer["id"])

    def test_hero_counts_the_layers_the_reader_checks(self):
        """The markup hero.js counts the reader's checks with: on the person's name line, the
        progress, a polite status (role="status") that ships hidden and counts from data-progress,
        where {n} is the count, to data-done, and can take focus (tabindex -1) for when "Check all
        layers" goes; that button, hidden until hero.js runs, in the pause control's place right after
        it and the still label, before the stage; and in each row's head, after the name and the TEE
        label, the check mark: an aria-hidden icon with "Checked" for screen readers, which the
        stylesheet shows once hero.js marks the row .is-checked."""
        n = len(self.model["topics"]["stack"])
        for lang in content.LANGS:
            strings = self.model["strings"][lang]
            figure = parse_html(self.hero_site(lang).hero()).find("figure", cls="hero-visual")
            status = figure.find("p", cls="hero-progress")
            self.assertEqual((status.attrs.get("role"), status.attrs.get("tabindex")), ("status", "-1"), lang)
            self.assertIn("hidden", status.attrs, lang)
            self.assertTrue(status.within(figure.find("div", cls="hero-person-head")), lang)
            counted = strings["hero_progress"].format(n="{n}", total=n)
            self.assertEqual(status.attrs.get("data-progress"), counted, lang)
            self.assertEqual(status.attrs.get("data-done"), strings["hero_progress_done"].format(total=n), lang)
            self.assertEqual(status.text(), norm(counted.replace("{n}", "0")), lang)
            kids = figure.kids()
            names = ("verification-motion", "verification-static-label", "hero-all", "hero-stage")
            self.assertEqual([kind_of(k, names) for k in kids[:4]], list(names), lang)
            button = kids[2]
            self.assertEqual((button.tag, button.attrs.get("type"), button.text()),
                             ("button", "button", norm(strings["hero_check_all"])), lang)
            self.assertIn("hidden", button.attrs, lang)
            for row in figure.find("ol", cls="hero-layers").kids("li", cls="hero-layer"):
                where = (lang, row.attrs.get("id"))
                head = row.find("span", cls="hero-layer-head")
                parts = [kind_of(k, ("hero-layer-icon", "hero-layer-link", "tag-tee", "vh", "hero-tick", "hero-more"))
                         for k in head.kids()]
                self.assertEqual([p for p in parts if p in ("hero-layer-link", "hero-tick", "hero-more")],
                                 ["hero-layer-link", "hero-tick", "hero-more"], where)
                self.assertTrue(all(i < parts.index("hero-tick") for i, p in enumerate(parts) if p in ("tag-tee", "vh")), where)
                tick = head.find("span", cls="hero-tick")
                self.assertEqual([svg.attrs.get("aria-hidden") for svg in tick.find_all("svg")], ["true"], where)
                self.assertEqual(tick.find("span", cls="vh").text(), norm(strings["hero_checked"]), where)

    def test_hero_words_describe_the_data_and_the_checks(self):
        """The scene's description and the hints follow what the hero does: the dotted path runs
        through every plate and carries the reader's prompts and data; each hint, one short line,
        asks the reader to open each layer until they turn colourful, the touch hint by tapping the
        arrow that opens a layer and the click hint, for a mouse in the list below 45em, by
        clicking it. Once every layer is checked each hint has a shorter line of its own that keeps
        the way to open a layer, for any layer, and drops the promise of colour. The description
        says what the still scene shows, which is all a page without the script has, so it names no
        gray; the sentences that hero.js adds once it runs (hero_scene_desc_live) say that the
        person starts in gray and that the data moves once all seven are checked, unless motion is
        reduced. The figure has no caption, so the description also carries what the caption said:
        a conceptual illustration, the chain of evidence, the TEE layers, the reader's data and the
        layers' scheme (positions, not security levels)."""
        en, zh = self.model["strings"]["en"], self.model["strings"]["zh"]
        for key in ("hero_hint", "hero_hint_touch", "hero_hint_click"):
            self.assertIn("each layer", en[key])
            self.assertIn("colorful", en[key])
            self.assertIn("每一层", zh[key])
            self.assertIn("彩色", zh[key])
            # one short sentence
            self.assertLessEqual(len(en[key]), 60, key)
            self.assertLessEqual(len(zh[key]), 25, key)
            self.assertEqual((en[key].count(". "), zh[key].count("。")), (0, 1), key)
        # on touch screens and phones a tap on a layer's name follows its link off the page, so the
        # touch hint sends the reader to the arrow (the chevron) that opens the layer; with a mouse
        # in the list below 45em the arrow opens it too, so the click hint names the click
        for word in ("Tap", "arrow"):
            self.assertIn(word, en["hero_hint_touch"])
            self.assertIn(word, en["hero_hint_touch_done"])
        for word in ("点按", "箭头"):
            self.assertIn(word, zh["hero_hint_touch"])
            self.assertIn(word, zh["hero_hint_touch_done"])
        for word in ("Click", "arrow"):
            self.assertIn(word, en["hero_hint_click"])
            self.assertIn(word, en["hero_hint_click_done"])
        for word in ("点击", "箭头"):
            self.assertIn(word, zh["hero_hint_click"])
            self.assertIn(word, zh["hero_hint_click_done"])
        self.assertNotIn("Tap", en["hero_hint_click"] + en["hero_hint_click_done"])
        self.assertNotIn("点按", zh["hero_hint_click"] + zh["hero_hint_click_done"])
        # the lines once every layer is checked: any layer, no promise of colour, and shorter
        for key in ("hero_hint", "hero_hint_touch", "hero_hint_click"):
            done = key + "_done"
            self.assertIn("any layer", en[done])
            self.assertIn("任意一层", zh[done])
            for lang, words in (("en", ("color", "all seven", "each")), ("zh", ("彩色", "七层", "每一层"))):
                strings = self.model["strings"][lang]
                self.assertTrue(strings[done].strip(), (lang, done))
                for word in words:
                    self.assertNotIn(word, strings[done], (lang, done))
                self.assertLess(len(strings[done]), len(strings[key]), (lang, done))
                # the same way of opening a layer as the hint before it: its verb comes first
                verb = strings[key].split()[0] if lang == "en" else strings[key][:2]
                self.assertTrue(strings[done].startswith(verb), (lang, done, verb))
        self.assertIn("every plate", en["hero_scene_desc"])
        self.assertIn("每块平板", zh["hero_scene_desc"])
        for word in ("gray", "grey", "color"):
            self.assertNotIn(word, en["hero_scene_desc"])
        for word in ("灰", "彩色", "颜色"):
            self.assertNotIn(word, zh["hero_scene_desc"])
        # what the caption said, for screen readers
        for words in ("conceptual illustration", "chain of evidence", "trusted execution environments (TEEs) give direct evidence",
                      "your prompts and data", "not security levels", "T1 to T7"):
            self.assertIn(words, en["hero_scene_desc"])
        for words in ("概念示意图", "证据链", "可信执行环境（TEE）在这两层提供直接证据", "你的提示词和数据", "不是安全等级", "T1–T7"):
            self.assertIn(words, zh["hero_scene_desc"])
        for words in ("gray", "all seven", "reduced motion"):
            self.assertIn(words, en["hero_scene_desc_live"])
        for words in ("灰色", "七层", "减少动态效果"):
            self.assertIn(words, zh["hero_scene_desc_live"])
        self.assertIn("data", en["hero_scene_title"])
        self.assertIn("数据", zh["hero_scene_title"])
        # the caption and the legend's note are gone, and the description names no checking
        for key in ("hero_caption", "hero_chain_note"):
            self.assertNotIn(key, en)
            self.assertNotIn(key, zh)
        self.assertNotIn("check", en["hero_scene_desc"].lower())
        self.assertNotIn("查看", zh["hero_scene_desc"])
        # every hero string these lines add is in both languages, Chinese with spaces around Latin
        # words and full-width punctuation
        for key in ("hero_scene_desc_live", "hero_hint_click", "hero_hint_done", "hero_hint_touch_done", "hero_hint_click_done"):
            self.assertTrue(en[key].strip() and zh[key].strip(), key)
            self.assertIsNone(re.search(r"[一-鿿][A-Za-z]|[A-Za-z][一-鿿]", zh[key]), key)
            self.assertIsNone(re.search(r"[一-鿿][,.;:!?]", zh[key]), key)

    def test_hero_chain_runs_follow_the_bindings(self):
        """The figure's chain and the legend's runs come from the stack's bindings: segment k is
        layer k's binding to layer k - 1, and neighbouring segments of one status make one run."""
        en = self.model["strings"]["en"]

        def figure(statuses):
            """The hero figure for a copy of the model whose bindings, T2 up to T7, have STATUSES."""
            stack = [dict(layer) for layer in self.model["topics"]["stack"]]
            for layer, status in zip(reversed(stack[:-1]), statuses):
                layer["bind"] = dict(layer["bind"], status=status)
            model = dict(self.model, topics=dict(self.model["topics"], stack=stack))
            s = self.hero_site(model=model)
            return s, parse_html(s.hero()).find("figure", cls="hero-visual")

        cases = [
            (["deployed"] * 6, [("deployed", 1, 7)]),
            (["deployed", "emerging"] * 3, [(st, k - 1, k) for k, st in zip(range(2, 8), ["deployed", "emerging"] * 3)]),
            (["emerging", "emerging", "missing", "missing", "deployed", "deployed"],
             [("emerging", 1, 3), ("missing", 3, 5), ("deployed", 5, 7)]),
        ]
        for statuses, runs in cases:
            with self.subTest(statuses=statuses):
                s, fig = figure(statuses)
                segments = list(zip(range(2, 8), statuses))
                self.assertEqual(s.hero_chain(), (segments, runs))
                self.assertEqual(fig.attrs.get("data-hv-chain"), " ".join(f"{k}:{st}" for k, st in segments))
                self.assertEqual(fig.attrs.get("data-hv-rest"), render.HERO_CHAIN_REST)
                items = fig.find("ul", cls="hero-chain-runs").kids("li")
                self.assertEqual([(li.attrs.get("data-bind"), li.find("span", cls="hero-chain-status").text(), norm(li.children[-1]))
                                  for li in items],
                                 [(st, en["bind_" + st], en["hero_chain_run"].format(lo=f"T{lo}", hi=f"T{hi}")) for st, lo, hi in runs])
                # the samples: one solid line in use, a dashed one where emerging, two stubs where missing
                for li in items:
                    paths = li.find("svg", cls="hero-chain-sample").find_all("path")
                    dashed = [p for p in paths if "stroke-dasharray" in p.attrs]
                    stubs = sum(p.attrs["d"].count("M") for p in paths)
                    self.assertEqual((len(dashed), stubs), {"deployed": (0, 1), "emerging": (1, 1), "missing": (0, 2)}[li.attrs["data-bind"]])
        # today's data, as the scene and the legend read it
        segments, runs = self.hero_site().hero_chain()
        stack = self.model["topics"]["stack"]
        self.assertEqual(segments, [(len(stack) - i, layer["bind"]["status"]) for i, layer in enumerate(stack) if layer.get("bind")][::-1])
        self.assertEqual([k for k, _ in segments], list(range(2, len(stack) + 1)))
        # the legend has a sample of the line for every status a binding may have, and only those
        self.assertEqual(set(render.HERO_CHAIN_SAMPLES), set(content.BIND_STATUSES))

    def test_a_lead_brief_pins_the_first_rail_row(self):
        """lead: true puts a news brief first in "Latest news"; on another kind it does nothing."""
        def rail(arts):
            s = self.site()
            s.hero_svg = build.hero_svg()
            s.hero_anchors = build.hero_anchors(s.hero_svg, len(self.model["topics"]["stack"]))
            doc = parse_html(s.home(arts)[1])
            titles = [doc.find("article", cls="news-lead").find("h3").find("a")]
            titles += [row.find("h3").find("a") for row in doc.find_all("li", cls="ledger-row")]
            return [ARTICLE_PATH_RE.match(canonical("index.html", a.attrs["href"])).group(1) for a in titles]

        arts = [copy.copy(a) for a in self.model["articles"]["en"]]
        for a in arts:
            a.lead = False
        news = [a for a in arts if a.kind == "news"]
        self.assertEqual(rail(arts), [a.slug for a in news[:6]])
        news[7].lead = True
        self.assertEqual(rail(arts), [news[7].slug] + [a.slug for a in news[:5]])
        news[7].lead = False
        next(a for a in arts if a.kind != "news").lead = True
        self.assertEqual(rail(arts), [a.slug for a in news[:6]])

    def test_unknown_include_stops_the_build(self):
        page = types.SimpleNamespace(path="content/pages/x.en.md", html='<p>a</p>\n<div data-include="nope"></div>')
        with self.assertRaises(content.ContentError):
            self.site().includes(page)
        page.html = '<div data-include="positioning"></div>\n<div data-include="tiers-summary"></div>'
        doc = parse_html(self.site().includes(page))
        self.assertEqual(doc.find("p", cls="lead").text(), norm(self.model["strings"]["en"]["home_positioning"]))
        self.assertEqual(len(doc.find("table", cls="tier-summary").find("tbody").kids("tr")), len(self.model["tiers"]["tiers"]))


class ChatSettingsTests(unittest.TestCase):
    """content/site.json "chat" and the build.py --chat / --chat-api overrides."""

    def test_defaults(self):
        self.assertEqual(render.chat_settings({})["mode"], "off")
        cfg = render.chat_settings({"chat": {}})
        self.assertEqual((cfg["mode"], cfg["launcher"], cfg["api_base"], cfg["allow_demo_fallback"]), ("demo", "header", "", True))

    def test_overrides_and_api_base(self):
        cfg = render.chat_settings({"chat": {"mode": "demo"}}, "live", "http://127.0.0.1:8787/")
        self.assertEqual((cfg["mode"], cfg["api_base"]), ("live", "http://127.0.0.1:8787"))
        self.assertEqual(render.chat_settings({"chat": {"mode": "live", "api_base": "https://x"}}, "off")["mode"], "off")

    def test_rejects_values_chat_js_cannot_use(self):
        bad = [
            {"mode": "mock"}, {"launcher": "bubble"}, {"allow_demo_fallback": "yes"},
            {"mode": "live"}, {"mode": "live", "api_base": "ftp://x"}, {"api_base": "https://x/?q=1"},
            {"suggestions": ["a"]}, {"suggestions": {"en": [""]}},
        ]
        for chat in bad:
            with self.assertRaises(ValueError, msg=chat):
                render.chat_settings({"chat": chat})

    def test_production_build_needs_https_for_a_remote_api(self):
        def model(api):
            return {"site": {"chat": {"mode": "live", "api_base": api}}, "strings": {"en": {}, "zh": {}}}
        with self.assertRaises(content.ContentError):
            build.apply_chat(model("http://api.example.org"), "prod")
        # a local API from content/site.json would make every reader's browser call its own machine
        with self.assertRaises(content.ContentError):
            build.apply_chat(model("http://127.0.0.1:8787"), "prod")
        # ... but a command-line override is a local test build, which may
        self.assertEqual(build.apply_chat(model("https://api.example.org"), "prod", "live", "http://127.0.0.1:8787")["mode"], "live")
        self.assertEqual(build.apply_chat(model("http://127.0.0.1:8787"), "preview")["mode"], "live")
        self.assertEqual(build.apply_chat(model("http://api.example.org"), "preview")["mode"], "live")
        with self.assertRaises(content.ContentError):
            build.apply_chat({"site": {"chat": {}}, "strings": {"en": {"chat_x": "x"}, "zh": {}}}, "preview")

    def test_live_production_build_needs_an_about_page_that_says_so(self):
        model = content.load(ROOT)
        self.assertEqual(build.stale_about(model), ["en", "zh"])  # the About text describes demo mode
        model["site"]["chat"] = {"mode": "live", "api_base": "https://api.example.org"}
        with self.assertRaises(content.ContentError):
            build.apply_chat(model, "prod")
        self.assertEqual(build.apply_chat(model, "preview")["mode"], "live")
        model["site"]["chat"] = {"mode": "demo"}
        self.assertEqual(build.apply_chat(model, "prod")["mode"], "demo")


class ContentModelTests(unittest.TestCase):
    """content.load() checks every id the data files name; a broken one stops the load."""

    @classmethod
    def setUpClass(cls):
        cls.model = content.load(ROOT)

    def test_data_references_resolve(self):
        """Every id the data files and front matter name exists, independently of the loader's own checks."""
        m = self.model
        slugs = {a.slug for a in m["articles"]["en"]}
        resources = {r["id"] for r in m["resources"]["resources"]}
        terms = {g["id"] for g in m["glossary"]["terms"]}
        layers = {layer["id"] for layer in m["topics"]["stack"]}
        topics = {t["id"] for t in m["topics"]["topics"]}
        tiers = {t["id"] for t in m["tiers"]["tiers"]}
        problems = []

        def need(values, known, where):
            problems.extend(f"{where}: {v!r}" for v in values if v not in known)

        def walk(node, where):
            """Every "article:<slug>" and "resource:<id>" source, and every {en, zh} text."""
            if isinstance(node, dict):
                if set(node) == {"en", "zh"} and all(isinstance(v, str) for v in node.values()):
                    if bool(node["en"].strip()) != bool(node["zh"].strip()):
                        problems.append(f"{where}: filled in one language only")
                for key, value in node.items():
                    walk(value, f"{where}.{key}")
            elif isinstance(node, list):
                for i, value in enumerate(node):
                    walk(value, f"{where}[{i}]")
            elif isinstance(node, str):
                ref = re.fullmatch(r"(article|resource):(\S+)", node)
                if ref:
                    need([ref.group(2)], slugs if ref.group(1) == "article" else resources, where)

        for name in ("tee", "tiers", "topics"):
            walk(m[name], name)
        walk(m["resources"].get("paths"), "resources.paths")
        tee = m["tee"]
        need([step["article"] for step in tee["path"] if "article" in step], slugs, "tee.path")
        need(tee["terms"] + tee["learn_terms"], terms, "tee.terms")
        for tier in m["tiers"]["tiers"]:
            need(tier["read"], slugs, f"tiers.{tier['id']}.read")
            need(tier["layers"], layers, f"tiers.{tier['id']}.layers")
            need(tier["topics"], topics, f"tiers.{tier['id']}.topics")
        for combo in m["tiers"]["combinations"]:
            need(combo["tiers"], tiers, f"tiers.combinations.{combo['id']}")
            need([combo["article"]], slugs, f"tiers.combinations.{combo['id']}.article")
        for topic in m["topics"]["topics"]:
            need(topic.get("tiers", []), tiers, f"topics.{topic['id']}.tiers")
        for layer in m["topics"]["stack"]:
            need([o["tier"] for o in layer.get("others", [])], tiers, f"stack.{layer['id']}.others")
            need(layer.get("topics", []), topics, f"stack.{layer['id']}.topics")
        for path in m["resources"]["paths"]:
            need([e["id"] for e in path["entries"]], resources, f"resources.paths.{path['id']}")
        for r in m["resources"]["resources"]:
            if (r.get("tee_area") in content.TEE_AREAS) != (TEE in r.get("topics", [])):
                problems.append(f"resources.{r['id']}: tee_area {r.get('tee_area')!r} with topics {r.get('topics')}")
        for lang in content.LANGS:
            for a in m["articles"][lang]:
                need(a.layers or [], layers, f"{a.path}: layers")
                need(a.topics, topics, f"{a.path}: topics")
        self.assertEqual(problems, [])

    def test_a_broken_reference_stops_the_load(self):
        cases = [
            ("tee", lambda d: d["services"][0]["sources"].append("article:no-such-article")),
            ("tee", lambda d: d["limits"][0]["sources"].append("resource:no-such-resource")),
            ("tee", lambda d: d["terms"].append("no-such-term")),
            ("tee", lambda d: d["limits"].reverse()),  # limits run newest first
            ("tee", lambda d: d["services"][0].update(record={"en": "Only in English", "zh": ""})),
            ("tiers", lambda d: d["tiers"][0]["read"].__setitem__(0, "no-such-article")),
            ("tiers", lambda d: d["tiers"][0]["layers"].append("no-such-layer")),
            ("tiers", lambda d: d["combinations"][0]["tiers"].append("no-such-tier")),
            ("topics", lambda d: d["topics"][0]["tiers"].append("no-such-tier")),
            ("topics", lambda d: d["stack"][0]["tee"].update(reach="direct")),  # direct evidence only at the bottom
            ("resources", lambda d: d["paths"][0]["entries"].append({"id": "no-such-resource", "why": {"en": "x", "zh": "x"}})),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_content(root)
            content.load(root)  # the copy loads as it is
            for n, (name, mutate) in enumerate(cases, 1):
                path = root / "content" / f"{name}.json"
                original = path.read_bytes()
                doc = json.loads(original)
                mutate(doc)
                path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
                try:
                    with self.subTest(case=n, file=name):
                        with self.assertRaises(content.ContentError) as caught:
                            content.load(root)
                        self.assertIn(f"content/{name}.json", str(caught.exception))  # the error names the file
                finally:
                    path.write_bytes(original)

    def test_retired_picture_fields_are_refused(self):
        """Plates and the front-matter illustration field are retired: an article's lead image
        comes from the illustration.json beside its editions (LeadImageTests)."""
        self.assertNotIn("illustrations", content.DATA_FILES)
        self.assertFalse((ROOT / "content" / "illustrations.json").exists())
        self.assertFalse((ROOT / "static" / "illustrations").exists())
        self.assertNotIn("plates", self.model["site"])

        def with_plate(text):
            doc = json.loads(text)
            doc["tiers"][0]["plate"] = "tier-signatures"
            return json.dumps(doc, ensure_ascii=False)

        def bad_layer(text):
            if re.search(r"^layers:", text, flags=re.M):
                return re.sub(r"^layers:.*$", "layers: [no-such-layer]", text, count=1, flags=re.M)
            return text.replace("---\n", "---\nlayers: [no-such-layer]\n", 1)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_content(root)
            slug = self.model["articles"]["en"][0].slug
            article = root / "content" / "articles" / slug / "en.md"
            page = root / "content" / "pages" / "vision.en.md"
            cases = [
                (article, lambda t: t.replace("---\n", "---\nillustration: tier-proof\n", 1)),
                (article, bad_layer),
                (page, lambda t: t.replace("---\n", "---\nplate: compare-methods\n", 1)),
                (root / "content" / "tiers.json", with_plate),
            ]
            for n, (path, edit) in enumerate(cases, 1):
                original = path.read_text(encoding="utf-8")
                path.write_text(edit(original), encoding="utf-8")
                try:
                    with self.subTest(case=n, file=path.name), self.assertRaises(content.ContentError):
                        content.load(root)
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_layer_7_is_policy_and_hero_blocks_name_known_icons_and_marks(self):
        stack = self.model["topics"]["stack"]
        self.assertEqual(stack[0]["id"], "institutions")  # the anchor stays, so old links keep working
        self.assertEqual(stack[0]["name"], {"en": "Policy", "zh": "政策"})
        self.assertEqual(stack[0]["hero"]["short"], {"en": "Policy", "zh": "政策"})
        self.assertEqual(sorted(layer["hero"]["icon"] for layer in stack), sorted(logos.LAYER_ICONS))
        cases = [
            lambda d: d["stack"][0]["hero"].update(icon="castle"),
            lambda d: d["stack"][0]["hero"]["examples"].append({"logo": "acme"}),
            lambda d: d["stack"][1]["hero"].update(examples=[]),
            lambda d: d["stack"][2]["hero"]["examples"].append({"name": "X"}),
            lambda d: d["stack"][3]["hero"].update(short={"en": "Outputs", "zh": ""}),
            lambda d: d["stack"][6]["hero"]["examples"].extend({"text": f"RISC-V {n}"} for n in range(7)),
            lambda d: d["stack"][5]["hero"]["examples"].append({"text": "vLLM", "name": "vLLM"}),
            lambda d: d["stack"][4].pop("hero"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_content(root)
            path = root / "content" / "topics.json"
            original = path.read_text(encoding="utf-8")
            for n, change in enumerate(cases, 1):
                doc = json.loads(original)
                change(doc)
                path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
                with self.subTest(case=n):
                    with self.assertRaises(content.ContentError) as caught:
                        content.load(root)
                    self.assertIn(".hero", str(caught.exception))
            # a mark's own title in sitegen/logos.py names it where the example gives no name: one
            # string, or an {en, zh} text with both filled in, as the European Union's (欧盟) is
            path.write_text(original, encoding="utf-8")
            eu = logos.LOGOS["europeanunion"]
            title = eu["title"]
            self.assertEqual(title, {"en": "European Union", "zh": "欧盟"})
            try:
                for bad in ({"en": "European Union"}, {"en": "European Union", "zh": " "}, "", None):
                    eu["title"] = bad
                    with self.subTest(title=bad):
                        with self.assertRaises(content.ContentError) as caught:
                            content.load(root)
                        self.assertIn("sitegen/logos.py", str(caught.exception))
            finally:
                eu["title"] = title
            content.load(root)

    def test_stack_layers_say_who_checks_in_both_languages(self):
        """Each stack layer's "checkers" names who outside the provider checks its claim: required,
        in both languages, on one line, and short enough for the layer card and the phone row."""
        stack = self.model["topics"]["stack"]
        cases = [
            (0, lambda layer: layer.pop("checkers")),
            (1, lambda layer: layer["checkers"].update(zh="")),
            (2, lambda layer: layer["checkers"].update(en="x" * 101)),
            (3, lambda layer: layer["checkers"].update(en=layer["checkers"]["en"] + " ")),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_content(root)
            path = root / "content" / "topics.json"
            original = path.read_text(encoding="utf-8")
            content.load(root)  # the copy loads as it is
            for n, (i, change) in enumerate(cases, 1):
                doc = json.loads(original)
                change(doc["stack"][i])
                path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
                with self.subTest(case=n):
                    with self.assertRaises(content.ContentError) as caught:
                        content.load(root)
                    self.assertIn(f"content/topics.json: stack.{stack[i]['id']}.checkers", str(caught.exception))
            doc = json.loads(original)
            doc["stack"][4]["checkers"] = {"en": "x" * 100, "zh": "核" * 45}  # the longest texts that fit
            path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
            content.load(root)


def set_byline(text, **fields):
    """Front matter TEXT with its byline replaced: author, submitted_by and agent are removed,
    then FIELDS (such as author="Ada Lovelace") are added after the opening ---."""
    head, sep, rest = text[4:].partition("\n---\n")
    lines = [ln for ln in head.split("\n") if not re.match(r"(author|submitted_by|agent):", ln)]
    lines = [f"{key}: {value}" for key, value in fields.items()] + lines
    return "---\n" + "\n".join(lines) + sep + rest


class BylineTests(unittest.TestCase):
    """Every article names the person who wrote it (author) or, for an article the site's
    software drafted, its automated byline (agent, an id from content/site.json "agents"),
    and may credit the person who submitted the story (submitted_by); zh.md takes the byline
    from en.md. Bylines follow wire-service style and never use the word "agent". The article
    page shows the whole byline (Site.byline) and a list row a short mark (Site.byline_mark)."""

    @classmethod
    def setUpClass(cls):
        cls.model = content.load(ROOT)
        cls.agents = cls.model["site"]["agents"]

    def site(self, lang):
        s = Site(self.model, "prod")
        s.lang = lang
        s.current = loc("/articles/x/", lang)
        return s

    def test_the_automated_bylines_have_wire_names_and_one_plain_sentence_in_both_languages(self):
        self.assertEqual(self.agents["daily"]["name"], {"en": "verifiable.pro Wire", "zh": "verifiable.pro 快讯"})
        self.assertEqual(self.agents["research"]["name"], {"en": "verifiable.pro Research", "zh": "verifiable.pro 研究"})
        for agent_id, entry in self.agents.items():
            self.assertEqual(set(entry), set(content.AGENT_KEYS), agent_id)
            en, zh = entry["description"]["en"], entry["description"]["zh"]
            # one sentence: what is automated, on which models, and that the editor decides what is published
            self.assertRegex(en, r"^Automated [^.]+\.$", agent_id)
            self.assertIn(": software built on Anthropic's Claude models ", en, agent_id)
            self.assertTrue(en.endswith("; the editor decides what is published."), agent_id)
            self.assertTrue(zh.startswith("自动") and zh.count("。") == 1 and zh.endswith("，由编辑决定是否发布。"), agent_id)
            self.assertIn("：基于 Anthropic Claude 模型的程序", zh, agent_id)

    def test_no_byline_text_uses_the_word_agent(self):
        """The owner's rule for bylines: they never say "AI agent" or use the word "agent", in
        the registry's names and descriptions or in the byline strings (only the keys and the
        front-matter field keep it)."""
        texts = [text for entry in self.agents.values() for field in content.AGENT_KEYS
                 for text in (entry[field].values() if isinstance(entry[field], dict) else [entry[field]])]
        texts += [text for lang in content.LANGS for key, text in self.model["strings"][lang].items()
                  if key.startswith("byline_")]
        self.assertGreaterEqual(len(texts), 18)  # 2 bylines × name and description × 2 languages, 5 strings × 2
        for text in texts:
            self.assertNotRegex(text.casefold(), r"agent|智能体", text)

    def test_every_article_names_its_author_or_agent_and_zh_takes_it_from_en(self):
        english = {a.slug: a for a in self.model["articles"]["en"]}
        for lang in content.LANGS:
            for a in self.model["articles"][lang]:
                self.assertEqual(bool(a.author) + bool(a.agent), 1, a.path)
                self.assertTrue(not a.agent or a.agent in self.agents, a.path)
                self.assertEqual(a.agent, english[a.slug].agent, a.path)
                self.assertEqual(bool(a.submitted_by), bool(english[a.slug].submitted_by), a.path)
        for path in sorted((ROOT / "content" / "articles").glob("*/zh.md")):
            meta, _ = md.parse_front_matter(path.read_text(encoding="utf-8"))
            self.assertNotIn("agent", meta, path)

    def test_a_broken_byline_stops_the_load(self):
        brief = next(a for a in self.model["articles"]["en"] if a.agent == "daily")

        def registry(edit):
            def change(text):
                doc = json.loads(text)
                edit(doc["agents"])
                return json.dumps(doc, ensure_ascii=False)
            return change

        def zh_field(line):
            return lambda text: text.replace("---\n", f"---\n{line}\n", 1)

        cases = [
            ("en", lambda t: set_byline(t), "the byline is missing"),
            ("en", lambda t: set_byline(t, author="Ada Lovelace", agent="daily"), "not both"),
            ("en", lambda t: set_byline(t, agent="nightly"), "unknown agent 'nightly'"),
            ("en", lambda t: set_byline(t, agent="[daily, research]"), "agent must be text"),
            ("en", lambda t: set_byline(t, author="verifiable.pro"), "not a person's name"),
            ("en", lambda t: set_byline(t, author="verifiable.pro Wire"), "not a person's name"),
            ("en", lambda t: set_byline(t, author="Verifiable.pro  research"), "not a person's name"),
            ("en", lambda t: set_byline(t, agent="daily", submitted_by="verifiable.pro 快讯"), "not a person's name"),
            ("en", lambda t: set_byline(t, author="Ada Lovelace", submitted_by="ada  lovelace"), "repeats author"),
            ("zh", zh_field("agent: research"), "agent differs from en.md"),
            ("zh", zh_field("submitted_by: Grace Hopper"), "one edition only"),
            ("zh", zh_field("author: Ada Lovelace"), "not both"),
            ("site", registry(lambda agents: agents["daily"].update(url="https://example.org/")), "unknown field 'url'"),
            ("site", registry(lambda agents: agents["daily"]["description"].update(zh="")), "the zh text is empty"),
            ("site", registry(lambda agents: agents.update(Daily=agents.pop("daily"))), "lowercase words"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_content(root)
            folder = root / "content" / "articles" / brief.slug
            files = {"en": folder / "en.md", "zh": folder / "zh.md", "site": root / "content" / "site.json"}
            content.load(root)  # the copy loads as it is
            for n, (name, edit, message) in enumerate(cases, 1):
                path = files[name]
                original = path.read_text(encoding="utf-8")
                path.write_text(edit(original), encoding="utf-8")
                try:
                    with self.subTest(case=n, file=name):
                        with self.assertRaises(content.ContentError) as caught:
                            content.load(root)
                        self.assertIn(message, str(caught.exception))
                        where = "content/site.json" if name == "site" else f"{brief.slug}/{name}.md"
                        self.assertIn(where, str(caught.exception))  # the error names the file
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_a_person_byline_may_give_a_chinese_form_of_the_names_in_zh(self):
        brief = next(a for a in self.model["articles"]["en"] if a.agent == "daily")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_content(root)
            folder = root / "content" / "articles" / brief.slug
            en, zh = folder / "en.md", folder / "zh.md"
            en.write_text(set_byline(en.read_text(encoding="utf-8"), author="Ada Lovelace", submitted_by="Grace Hopper"),
                          encoding="utf-8")
            loaded = {a.lang: a for lang in content.LANGS for a in content.load(root)["articles"][lang]
                      if a.slug == brief.slug}
            self.assertEqual([(a.author, a.submitted_by, a.agent) for a in loaded.values()],
                             [("Ada Lovelace", "Grace Hopper", "")] * 2)  # zh.md inherits the names
            zh.write_text(zh.read_text(encoding="utf-8").replace("---\n", "---\nauthor: 阿达·洛夫莱斯\n"
                                                                 "submitted_by: 格蕾丝·霍珀\n", 1), encoding="utf-8")
            chinese = next(a for a in content.load(root)["articles"]["zh"] if a.slug == brief.slug)
            self.assertEqual((chinese.author, chinese.submitted_by, chinese.agent), ("阿达·洛夫莱斯", "格蕾丝·霍珀", ""))

    def test_the_article_byline_gives_the_automated_name_a_dot_and_the_tag(self):
        """Wire-service style: "verifiable.pro Wire · Automated", the name without "By", and
        the tag links to About's #ai with the byline's description as its tooltip."""
        for lang in content.LANGS:
            site, s = self.site(lang), self.model["strings"][lang]
            for agent_id, entry in self.agents.items():
                with self.subTest(lang=lang, agent=agent_id):
                    html_text = site.byline(Article(agent=agent_id, author="", submitted_by=""))
                    p = parse_html(html_text).find("p")
                    self.assertEqual(p.classes, {"byline"})
                    self.assertEqual(p.text(), f'{entry["name"][lang]} · {s["byline_agent"]}')
                    self.assertEqual(p.find("span", cls="byline-by").text(), entry["name"][lang])
                    self.assertEqual(p.find("span", cls="byline-sep").attrs.get("aria-hidden"), "true")
                    tag = p.find("a", cls="byline-tag")
                    self.assertEqual((tag.text(), tag.attrs["href"]), (s["byline_agent"], loc("/about/", lang) + "#ai"))
                    self.assertEqual(tag.attrs["title"], entry["description"][lang])
                    self.assertIsNone(p.find("span", cls="byline-submitted"))
            # a story someone submitted, drafted by the software: another dot, then the credit;
            # a no-break space keeps every dot at the end of a line
            html_text = site.byline(Article(agent="daily", author="", submitted_by="Grace Hopper"))
            p = parse_html(html_text).find("p")
            self.assertEqual(p.find("span", cls="byline-submitted").text(),
                             norm(s["byline_submitted"].format(name="Grace Hopper")))
            self.assertEqual(p.text(), norm(f'{self.agents["daily"]["name"][lang]} · {s["byline_agent"]} · '
                                            + s["byline_submitted"].format(name="Grace Hopper")))
            self.assertEqual(html_text.count('&nbsp;<span class="byline-sep" aria-hidden="true">·</span> '), 2, lang)
            self.assertEqual(html_text.count("byline-sep"), 2, lang)

    def test_a_person_byline_gives_the_name_and_who_submitted_the_story(self):
        for lang in content.LANGS:
            site, s = self.site(lang), self.model["strings"][lang]
            p = parse_html(site.byline(Article(agent="", author="Ada Lovelace", submitted_by="Grace Hopper"))).find("p")
            self.assertEqual(p.find("span", cls="byline-by").text(), norm(s["byline_by"].format(name="Ada Lovelace")))
            self.assertEqual(p.text(), norm(s["byline_by"].format(name="Ada Lovelace") + " · "
                                            + s["byline_submitted"].format(name="Grace Hopper")))
            self.assertIsNone(p.find("a", cls="byline-tag"))
            self.assertEqual(p.find("span", cls="byline-submitted").text(),
                             norm(s["byline_submitted"].format(name="Grace Hopper")))
            # on a Chinese page the English names are marked as English, for screen reader voices
            names = [n.text() for n in p.find_all("span", lang="en")]
            self.assertEqual(names, ["Ada Lovelace", "Grace Hopper"] if lang == "zh" else [], lang)
            alone = parse_html(site.byline(Article(agent="", author="Ada Lovelace", submitted_by=""))).find("p")
            self.assertEqual([alone.find("span", cls="byline-sep"), alone.find("span", cls="byline-submitted")],
                             [None, None])

    def test_a_list_row_gives_the_automated_name_or_the_persons(self):
        """A list row shows the automated byline's name, such as "verifiable.pro Wire", with
        its description as the tooltip, and screen readers hear that it is automated; a
        person's row shows "By <name>"."""
        for lang in content.LANGS:
            site, s = self.site(lang), self.model["strings"][lang]
            for agent_id, entry in self.agents.items():
                with self.subTest(lang=lang, agent=agent_id):
                    doc = parse_html(site.byline_mark(Article(agent=agent_id, author="")))
                    shown = doc.find("span", cls="byline-mark")
                    self.assertEqual((shown.attrs.get("aria-hidden"), shown.text()), ("true", entry["name"][lang]))
                    self.assertIn("is-agent", shown.classes)
                    self.assertEqual(shown.attrs["title"], entry["description"][lang])
                    self.assertEqual(doc.find("span", cls="vh").text(),
                                     norm(s["byline_agent_vh"].format(name=entry["name"][lang])))
            doc = parse_html(site.byline_mark(Article(agent="", author="Ada Lovelace")))
            shown = doc.find("span", cls="byline-mark")
            self.assertEqual(shown.text(), norm(s["byline_by"].format(name="Ada Lovelace")))
            self.assertEqual({k for k in shown.attrs if k in ("aria-hidden", "title")}, set())
            self.assertIsNone(doc.find("span", cls="vh"))


class PersonBylineBuildTests(unittest.TestCase):
    """A production build of a copy of the project in which a person wrote one news brief and
    another person submitted it, with both names in Chinese form in zh.md: the article page,
    the list rows, the structured data, the Atom and JSON Feeds and the llms-full.txt headers
    name the people, while an automated article keeps its automated byline, such as
    "verifiable.pro Wire", and the publication as its author in the structured data."""
    NAMES = {"en": ("Ada Lovelace", "Grace Hopper"), "zh": ("阿达·洛夫莱斯", "格蕾丝·霍珀")}

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name) / "project"
        root.mkdir()
        for name in ("build.py", "indexnow.json"):
            shutil.copy2(ROOT / name, root / name)
        for name in ("sitegen", "static", "content"):
            shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
        newest = content.load(ROOT)["articles"]["en"][:discover.FEED_ITEMS]  # the feeds carry these
        briefs = [a for a in newest if a.kind == "news" and a.agent]
        cls.person, cls.agent = briefs[0].slug, briefs[1].slug
        folder = root / "content" / "articles" / cls.person
        (author, submitter), (author_zh, submitter_zh) = cls.NAMES["en"], cls.NAMES["zh"]
        en, zh = folder / "en.md", folder / "zh.md"
        en.write_text(set_byline(en.read_text(encoding="utf-8"), author=author, submitted_by=submitter), encoding="utf-8")
        zh.write_text(zh.read_text(encoding="utf-8").replace("---\n", f"---\nauthor: {author_zh}\nsubmitted_by: "
                                                             f"{submitter_zh}\n", 1), encoding="utf-8")
        cls.out = Path(cls.tmp.name) / "public"
        result = subprocess.run([sys.executable, "build.py", "--out", str(cls.out)], cwd=root, capture_output=True,
                                text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.model = content.load(root)
        cls.base = cls.model["site"]["base_url"].rstrip("/")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, rel):
        return (self.out / rel).read_text(encoding="utf-8")

    def agent_name(self, slug, lang):
        agents = self.model["site"]["agents"]
        agent = next(a for a in self.model["articles"][lang] if a.slug == slug).agent
        return agents[agent]["name"][lang]

    def test_the_page_and_the_lists_name_the_people(self):
        for lang in content.LANGS:
            s, (author, submitter) = self.model["strings"][lang], self.NAMES[lang]
            doc = parse_html(self.read(f"{LANG_DIR[lang]}articles/{self.person}/index.html"))
            byline = doc.find("p", cls="byline")
            self.assertEqual(byline.find("span", cls="byline-by").text(), norm(s["byline_by"].format(name=author)), lang)
            self.assertEqual(byline.find("span", cls="byline-submitted").text(),
                             norm(s["byline_submitted"].format(name=submitter)), lang)
            self.assertIsNone(byline.find("a", cls="byline-tag"), lang)
            latest = parse_html(self.read(f"{LANG_DIR[lang]}latest/index.html"))
            marks = {}
            for row in latest.find_all("li", cls="river-item"):
                href = row.find("h3", cls="river-title").find("a").attrs["href"]
                marks[href.strip("/").split("/")[-1]] = row.find("span", cls="byline-mark")
            self.assertEqual(marks[self.person].text(), norm(s["byline_by"].format(name=author)), lang)
            self.assertNotIn("title", marks[self.person].attrs, lang)
            self.assertEqual(marks[self.agent].text(), self.agent_name(self.agent, lang), lang)

    def test_structured_data_names_a_person_or_the_publication(self):
        for lang in content.LANGS:
            author, submitter = self.NAMES[lang]
            for slug in (self.person, self.agent):
                doc = parse_html(self.read(f"{LANG_DIR[lang]}articles/{slug}/index.html"))
                nodes = []
                for script in doc.find_all("script", type="application/ld+json"):
                    data = json.loads(script.raw())
                    nodes += data if isinstance(data, list) else [data]
                art = next(n for n in nodes if n["@type"] in ("NewsArticle", "Article"))
                if slug == self.person:
                    self.assertEqual(art["author"], {"@type": "Person", "name": author}, lang)
                    self.assertEqual(art["contributor"], {"@type": "Person", "name": submitter}, lang)
                else:  # the site's software drafted it: the publication is the author, and no person is made up
                    self.assertEqual(art["author"], {"@type": "Organization", "@id": self.base + "/#organization",
                                                     "name": self.model["site"]["domain"], "url": self.base + "/"}, lang)
                    self.assertNotIn("contributor", art, lang)
                    self.assertNotIn("Person", json.dumps(art), lang)

    def test_feeds_name_the_people_or_the_automated_byline_marked_as_automated(self):
        import xml.etree.ElementTree as ET
        atom = "{http://www.w3.org/2005/Atom}"
        for lang in content.LANGS:
            s, (author, submitter) = self.model["strings"][lang], self.NAMES[lang]
            agent = s["byline_agent_named"].format(name=self.agent_name(self.agent, lang))
            self.assertEqual(agent, {"en": "verifiable.pro Wire (automated)", "zh": "verifiable.pro 快讯（自动采编）"}[lang])
            about = self.base + loc("/about/", lang) + "#ai"
            entries = {}
            for entry in ET.parse(self.out / LANG_DIR[lang] / "feed.xml").getroot().iter(atom + "entry"):
                entries[entry.find(atom + "link").get("href").rstrip("/").split("/")[-1]] = entry
            person = entries[self.person]
            self.assertEqual([(a.findtext(atom + "name"), a.findtext(atom + "uri")) for a in person.findall(atom + "author")],
                             [(author, None)], lang)
            self.assertEqual([c.findtext(atom + "name") for c in person.findall(atom + "contributor")], [submitter], lang)
            drafted = entries[self.agent]
            self.assertEqual([(a.findtext(atom + "name"), a.findtext(atom + "uri")) for a in drafted.findall(atom + "author")],
                             [(agent, about)], lang)
            self.assertEqual(drafted.findall(atom + "contributor"), [], lang)
            items = {i["url"].rstrip("/").split("/")[-1]: i for i in json.loads(self.read(f"{LANG_DIR[lang]}feed.json"))["items"]}
            self.assertEqual(items[self.person]["authors"], [{"name": author}], lang)
            self.assertEqual(items[self.agent]["authors"], [{"name": agent, "url": about}], lang)

    def test_llms_full_txt_gives_each_byline(self):
        for lang in content.LANGS:
            s, (author, submitter) = self.model["strings"][lang], self.NAMES[lang]
            text = self.read(f"{LANG_DIR[lang]}llms-full.txt")
            prefix = "/zh" if lang == "zh" else ""

            def header(slug):
                return text.split(f"- URL: {self.base}{prefix}/articles/{slug}/\n", 1)[1].split("\n\n", 1)[0]

            self.assertIn(f"- Byline: {author}\n- Submitted by: {submitter}\n", header(self.person), lang)
            agent = s["byline_agent_named"].format(name=self.agent_name(self.agent, lang))
            self.assertIn(f"- Byline: {agent}\n", header(self.agent), lang)
            self.assertNotIn("- Submitted by:", header(self.agent), lang)
            # the intro, after the title and the site's description (which names the topic of agent
            # accountability), says what marks an automated byline and where About describes them
            intro = text.split("\n---\n", 1)[0].strip().split("\n\n")[-1]
            self.assertTrue(intro.startswith({"en": "This file holds", "zh": "本文件"}[lang]), lang)
            self.assertIn(self.base + loc("/about/", lang) + "#ai", intro, lang)
            self.assertIn({"en": '"(automated)" after the name', "zh": "名称后注明“（自动采编）”"}[lang], intro, lang)
            self.assertNotRegex(intro.casefold(), r"ai agent|智能体", lang)


class HeroAssetTests(unittest.TestCase):
    """build.py reads the hero scene and the anchors of its leader lines, and stops when
    either is missing or does not fit the scene and the stack."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / build.HERO_TEMPLATE).parent.mkdir(parents=True)
        self.svg = build.hero_svg()
        self.anchors = json.loads((ROOT / build.HERO_ANCHORS).read_text(encoding="utf-8"))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, doc):
        (self.root / build.HERO_ANCHORS).write_text(json.dumps(doc), encoding="utf-8")

    def test_scene_template_is_required_and_keeps_its_slots(self):
        with self.assertRaises(content.ContentError):
            build.hero_svg(self.root)
        for slot in build.HERO_SLOTS:  # the title, the description and the sentences hero.js adds to it
            (self.root / build.HERO_TEMPLATE).write_text(self.svg.replace(slot, ""), encoding="utf-8")
            with self.assertRaises(content.ContentError, msg=slot):
                build.hero_svg(self.root)
        self.assertEqual(build.HERO_SLOTS, ("{{SCENE_TITLE}}", "{{SCENE_DESC}}", "{{SCENE_DESC_LIVE}}"))
        self.assertIn("{{SCENE_TITLE}}", build.hero_svg(ROOT))

    def test_anchors_cover_each_layer_inside_the_scene(self):
        self.assertEqual(sorted(a["layer"] for a in build.hero_anchors(self.svg, 7)["anchors"]), list(range(1, 8)))
        with self.assertRaises(content.ContentError):
            build.hero_anchors(self.svg, 7, root=self.root)  # the file is missing
        anchors = self.anchors["anchors"]
        bad = [
            dict(self.anchors, viewBox=[0, 0, 100, 100]),
            dict(self.anchors, anchors=anchors[:-1]),
            dict(self.anchors, anchors=anchors + [dict(anchors[0])]),
            dict(self.anchors, anchors=[dict(a, x=999) if a["layer"] == 3 else a for a in anchors]),
            # left of the viewBox, which starts at x = -28 to make room for the person
            dict(self.anchors, anchors=[dict(a, x=-40) if a["layer"] == 2 else a for a in anchors]),
            dict(self.anchors, anchors=[dict(a, label_y="top") if a["layer"] == 1 else a for a in anchors]),
            # a layer that is missing, a string or a boolean stops the build with a message
            dict(self.anchors, anchors=[{k: v for k, v in a.items() if k != "layer"} if a["layer"] == 7 else a for a in anchors]),
            dict(self.anchors, anchors=[dict(a, layer="7") if a["layer"] == 7 else a for a in anchors]),
            dict(self.anchors, anchors=[dict(a, layer=True) if a["layer"] == 1 else a for a in anchors]),
        ]
        for n, doc in enumerate(bad, 1):
            self.write(doc)
            with self.subTest(case=n), self.assertRaises(content.ContentError):
                build.hero_anchors(self.svg, 7, root=self.root)
        self.write(self.anchors)
        self.assertEqual(build.hero_anchors(self.svg, 7, root=self.root), self.anchors)

    def test_scene_check_accepts_the_scene_and_refuses_a_broken_interface(self):
        """hero_scene_check guards what the page addresses in the scene: the plates' hit
        areas, the stubs of each segment, the person with the ring on their phone, drawn
        without a transform, so that the bounds test below reads where the person stands,
        and the person's own hit area, outside the plates'. A transform elsewhere in the
        scene is the drawing's own business."""
        build.hero_scene_check(self.svg)
        hit = {n: re.search(rf'<path class="hv-hit" data-hv-n="{n}"[^>]*/>\n', self.svg).group(0) for n in range(1, 8)}
        broken = {
            "a hit removed": self.svg.replace(hit[4], ""),
            "hits reordered": self.svg.replace(hit[2] + hit[3], hit[3] + hit[2]),
            "a stub removed from segment 7": re.sub(r'(<g class="hv-seg hv-seg7"><path class="hv-stub" d="[^"]+"/>)'
                                                    r'<path class="hv-stub" d="[^"]+"/>', r"\1", self.svg),
            "no person": self.svg.replace('<g class="hv-person">', '<g class="hv-figure">'),
            "no ring on the phone": re.sub(r'<ellipse class="[^"]*\bhv-ph-ring\b[^"]*"[^>]*/>', "", self.svg),
            "the person scaled by a transform": self.svg.replace('<g class="hv-person">',
                                                                 '<g class="hv-person" transform="scale(1.2)">'),
            "a part of the person moved by a transform": self.svg.replace('<path class="hv-pphone" ',
                                                                          '<path class="hv-pphone" transform="translate(9 0)" '),
            "a part of the person moved in its style": self.svg.replace('style="--hv-d:0s"',
                                                                        'style="--hv-d:0s;transform:scale(2)"'),
            "no hit area on the person": re.sub(r'<path class="hv-you-hit"[^>]*/>\n', "", self.svg),
            "the person's hit area among the plates'": re.sub(
                r'(<path class="hv-you-hit"[^>]*/>\n)(.*?<g class="hv-hits">\n)', r"\2\1", self.svg, flags=re.S),
        }
        for case, svg in broken.items():
            with self.subTest(case=case):
                self.assertNotEqual(svg, self.svg)  # the edit found what it breaks
                with self.assertRaises(content.ContentError) as caught:
                    build.hero_scene_check(svg)
                self.assertIn(build.HERO_TEMPLATE.as_posix(), str(caught.exception))
        # outside the person a transform is allowed
        build.hero_scene_check(self.svg.replace('<g class="hv-hits">', '<g class="hv-hits" transform="translate(0 0)">'))

    def test_scene_person_is_what_the_generator_draws(self):
        """The person in the scene is the path data that tools/hero/person.py draws, with its size
        and place (SCALE and FEET there) baked into the points; after changing the figure,
        python3 tools/hero/person.py --write rewrites it. The check runs the generator (about 3s)."""
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "hero" / "person.py"), "--check"], cwd=ROOT,
                             capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)

    def test_scene_data_flow_is_what_the_generator_draws(self):
        """The data flow (the dotted route and the packets, and their keyframes in the scene's
        style) is what tools/hero/flow.py computes from the scene's geometry: the phone's ring,
        the glass's top and the server's top; python3 tools/hero/flow.py --write rewrites it."""
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        run = subprocess.run([sys.executable, str(ROOT / "tools" / "hero" / "flow.py"), "--check"], cwd=ROOT,
                             capture_output=True, text=True, env=env, timeout=120)
        self.assertEqual(run.returncode, 0, run.stderr + run.stdout)

    def scene_rules(self):
        style = re.search(r"<style>(.*?)</style>", self.svg, re.S).group(1)
        return css_rules(style)

    def test_scene_data_passes_every_layer_in_order_before_the_pulse(self):
        """The loop (tools/hero/flow.py): the request leaves the phone's ring and rests on one object
        of every layer in order, T1 to T7 (each rest lies on that layer's plate, the topmost hit area
        there), and the answer runs from T7's object back to the ring; then the pulse rises, so no
        packet shows while it moves, the trailing packet's delay included. Each plate's front edges
        light as the packet reaches it, T1 first. A request leaves in the reader's colour, turns
        indigo on the board (T1) and back where it leaves the top of the glass (T2), where the low
        group, under the glass's front faces, hands it to the high group at the same place and time;
        the answer stays in the reader's colour. The rings light as the pulse passes, ring 1 as it
        starts, and the phone's halo as the request leaves and as the answer arrives."""
        rules = self.scene_rules()
        svg = parse_html(self.svg).find("svg")

        def frames(name):
            out = [(float(part.strip().rstrip("%")), decls) for ctx, sel, decls in rules
                   if ctx == (f"@keyframes {name}",) for part in sel.split(",")]
            return sorted(out, key=lambda f: f[0])

        def xy(decls):
            m = re.match(r"translate\((-?[\d.]+)px,(-?[\d.]+)px\)", decls["transform"])
            return float(m.group(1)), float(m.group(2))

        def inside(poly, p):
            hit = False
            for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
                if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                    hit = not hit
            return hit
        anim = {sel: decls["animation"] for ctx, sel, decls in rules if "animation" in decls and not ctx}
        period = float(re.search(r"hv-q ([\d.]+)s", anim["[data-animated] .hv-pkq"]).group(1))
        self.assertTrue(10 <= period <= 12, period)
        # the pulse holds below the die, rises from P0 to P1 and holds past the top
        rise = frames("hv-rise")
        start = [at for at, d in rise if "+" in d["stroke-dashoffset"]]
        stop = [at for at, d in rise if "-" in d["stroke-dashoffset"].split("var(--hv-s)")[1]]
        p0, p1 = max(start), min(stop)
        self.assertLess(p0, p1)
        packets = svg.find_all("circle", cls="hv-pk")
        delay = max(float(re.search(r"--hv-d:([\d.]+)s", c.attrs.get("style", "--hv-d:0s")).group(1)) for c in packets)
        for name in ("hv-q", "hv-r", "hv-a"):
            shown = [at for at, d in frames(name) if d.get("opacity", "0") != "0"]
            self.assertTrue(shown, name)
            self.assertLess(max(shown) + delay / period * 100, p0, name)
        # the request's rests, from the low and the high groups together, lie on T1 to T7 in order
        q, r = frames("hv-q"), frames("hv-r")
        moves = sorted([(at, xy(d)) for at, d in q + r if "transform" in d and 0 < at < 100], key=lambda f: f[0])
        rests = [(a, pa) for (a, pa), (b, pb) in zip(moves, moves[1:]) if pa == pb and b - a > 1]
        hits = {int(p.attrs["data-hv-n"]): [path_points(sub + "Z") for sub in p.attrs["d"].split("Z") if sub.strip()]
                for p in svg.find_all("path", cls="hv-hit")}

        def layer_at(p):
            return max((n for n, polys in hits.items() if any(inside(poly, p) for poly in polys)), default=0)
        self.assertEqual([layer_at(p) for _, p in rests], list(range(1, 8)), rests)
        ring = svg.find("ellipse", cls="hv-ph-ring")
        phone = (float(ring.attrs["cx"]), float(ring.attrs["cy"]))
        self.assertLess(math.dist(xy(q[0][1]), phone), 0.2)
        answer = frames("hv-a")
        self.assertLess(math.dist(xy(answer[-1][1]), phone), 0.2)
        self.assertLess(math.dist(xy(answer[0][1]), rests[-1][1]), 0.2)
        # the colours, and the hand-over at the top of the glass
        for name, first, last in (("hv-q", "var(--hv-data)", "var(--hv-tee2)"), ("hv-r", "var(--hv-tee2)", "var(--hv-data)"),
                                  ("hv-a", "var(--hv-data)", "var(--hv-data)")):
            fills = [d["fill"] for at, d in frames(name) if "fill" in d]
            self.assertEqual((fills[0], fills[-1]), (first, last), name)
        low_last = max(at for at, d in q if d.get("opacity", "0") != "0")
        high_first = min(at for at, d in r if d.get("opacity", "0") != "0")
        self.assertLessEqual(abs(low_last - high_first), 0.2)
        handed = [d for at, d in q if at == low_last and "transform" in d]
        taken = [d for at, d in r if at == high_first and "transform" in d]
        self.assertTrue(handed and taken)
        self.assertLess(math.dist(xy(handed[0]), xy(taken[0])), 0.2)
        glass = path_points(re.search(r'<path class="hv-gt" d="([^"]+)"', self.svg).group(1))[:4]
        self.assertTrue(math.dist(xy(handed[0]), min(glass, key=lambda c: math.dist(c, xy(handed[0])))) < 60)
        # the lit edges: one per plate, each lit as the packet rests on its layer, T1 first
        reach = svg.find_all("path", cls="hv-reach")
        self.assertEqual([("hv-reach" + str(n)) in p.classes for n, p in zip(range(1, 8), reach)], [True] * 7)
        delays = [float(re.search(r"--hv-d:([\d.]+)s", p.attrs["style"]).group(1)) for p in reach]
        self.assertEqual(delays, sorted(delays))
        for d, (at, _) in zip(delays, rests):
            self.assertLess(abs(d - at / 100 * period), 0.15, (d, at))
        # the rings light as the pulse passes, ring 1 as it starts; the phone's halo twice
        ring_delays = [float(re.search(r"--hv-d:([\d.]+)s", svg.find("g", cls=f"hv-ring{n}").find("ellipse", cls="hv-nh").attrs["style"]).group(1))
                       for n in range(1, 7)]
        self.assertEqual(ring_delays, sorted(ring_delays))
        self.assertAlmostEqual(ring_delays[0], p0 / 100 * period, delta=0.05)
        self.assertLess(ring_delays[-1], p1 / 100 * period)
        peaks = [at for at, d in frames("hv-yping") if "2.6" in d.get("opacity", "")]
        self.assertEqual(len(peaks), 2)
        self.assertLess(peaks[0], min(at for at, d in q if d.get("opacity", "0") != "0") + 2)
        last = max(at for at, d in answer if d.get("opacity", "0") != "0")
        home = min(at for at, d in answer if at > last and d.get("opacity") == "0")   # the answer is in
        self.assertTrue(0 <= peaks[1] - home <= 0.5 / period * 100, (peaks[1], home))

    def test_scene_motion_honours_the_pause_and_reduced_motion(self):
        """Every looping animation in the scene (the pulse, the pings, the data packets and the lit
        edges) runs only under data-animated, which hero.js sets once every layer is checked; it
        holds while data-motion is paused or suspended and stops under data-motion="static";
        the one-off motions of the person's moment (hop, twinkle, ripples) play only while the
        reader has not paused the motion (for a click, hero.js says so in data-hv-cheer="move");
        every transition sits under prefers-reduced-motion: no-preference; and under reduced
        motion nothing animates and the pulse, the packets and the lit edges are not drawn. Both
        flow groups are hidden while a layer is open, like the pulse: the low one stands under the
        glass's front faces, the high one over the top plate and under the person."""
        rules = self.scene_rules()
        loops, once = set(), set()
        for ctx, sel, decls in rules:
            value = decls.get("animation", "") or decls.get("animation-name", "")
            if not value or value.startswith("none") or any(c.startswith("@keyframes") for c in ctx):
                continue
            for part in sel.split(","):
                subject = re.findall(r"\.(hv-[\w-]+)", part)[-1]
                (loops if "infinite" in value else once).add((subject, part.strip()))
        self.assertEqual({c for c, _ in loops}, {"hv-pulse", "hv-nh", "hv-pkq", "hv-pkr", "hv-pka", "hv-reach"})
        for cls, part in loops:
            self.assertTrue(part.startswith("[data-animated] "), part)
        held = {sel for ctx, sel, decls in rules if decls.get("animation-play-state") == "paused"}
        stopped = {sel for ctx, sel, decls in rules if decls.get("animation") == "none" and not ctx}
        for cls in ("hv-pulse", "hv-nh", "hv-pk", "hv-reach"):
            for state in ("paused", "suspended"):
                self.assertIn(f'[data-motion="{state}"] .hv-scene .{cls}', ",".join(held).replace(",", " , "), (cls, state))
            self.assertIn(f'[data-motion="static"] .hv-scene .{cls}', ",".join(stopped), cls)
        # the rules that hold or stop the loop come after every rule that runs it, so that a loop rule
        # as specific as they are (the phone's halo) cannot set the play state back to running
        running = [i for i, (ctx, sel, decls) in enumerate(rules) if not ctx and "infinite" in decls.get("animation", "")]
        holding = [i for i, (ctx, sel, decls) in enumerate(rules) if not ctx and (decls.get("animation-play-state") == "paused"
                   or (decls.get("animation") == "none" and "data-motion" in sel))]
        self.assertTrue(running and holding)
        self.assertLess(max(running), min(holding))
        self.assertTrue(once)
        for cls, part in once:
            self.assertTrue(':not([data-motion="paused"])' in part or part.startswith('[data-hv-cheer="move"] '), part)
        # the hop keys on data-hv-hop, which hero.js holds for the hop's length, never on the open
        # layer itself: a pointer that leaves T1 or T2 mid-hop would drop the person to the ground
        hops = [part.strip() for ctx, sel, decls in rules if not ctx and "hv-hop" in decls.get("animation", "") + decls.get("animation-name", "")
                for part in sel.split(",") if part.strip().endswith(".hv-person")]
        self.assertTrue(hops)
        for part in hops:
            self.assertNotIn("data-hv-active", part)
            self.assertTrue("[data-hv-hop]" in part or part.startswith('[data-hv-cheer="move"] '), part)
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        self.assertRegex(script, r"const HOP = 700\b")
        self.assertRegex(script, r"setAttribute\('data-hv-cheer', fig\.dataset\.motion === 'paused' \|\| "
                                 r"fig\.dataset\.motion === 'static' \? 'still' : 'move'\)")
        for ctx, sel, decls in rules:
            if "transition" in decls or "transition-duration" in decls:
                self.assertIn("@media (prefers-reduced-motion:no-preference)", ctx, sel)
        reduced = {sel: decls for ctx, sel, decls in rules if ctx == ("@media (prefers-reduced-motion:reduce)",)}
        self.assertEqual(reduced.get(".hv-scene *"), {"animation": "none!important"})
        self.assertEqual(reduced.get(".hv-pulse"), {"display": "none"})
        self.assertEqual(reduced.get(".hv-pk"), {"display": "none"})
        self.assertEqual(reduced.get(".hv-reach"), {"display": "none"})
        hidden = {sel for ctx, sel, decls in rules if decls.get("opacity") == "0" and not ctx}
        self.assertIn("[data-hv-active] .hv-flow", hidden)
        svg = parse_html(self.svg).find("svg")
        flows = svg.find_all("g", cls="hv-flow")
        self.assertEqual([("hv-flow-lo" in g.classes, "hv-flow-hi" in g.classes) for g in flows], [(True, False), (False, True)])
        order = [n for n in svg.iter()]
        glass = svg.find("path", cls="hv-gl")
        top = [g for g in svg.find_all("g", cls="hv-ly7")][-1]
        person = svg.find("g", cls="hv-person")
        self.assertLess(order.index(flows[0]), order.index(glass))
        self.assertLess(order.index(top), order.index(flows[1]))
        self.assertLess(order.index(flows[1]), order.index(person))

    def test_scene_draws_you_gray_until_every_layer_is_checked(self):
        """You are gray until the reader has checked every layer: hero.js counts the layers checked
        in data-hv-checked, 0 to 7, and the scene sets --hv-gray for each count, from 1 down to 0,
        a step of colour back with each layer, through one grayscale filter on g.hv-person, which
        the lit filter of an open layer or the person's moment keeps; at 7 there is no filter.
        Where scripts run you are gray from the first paint while the figure has data-hv-wait
        (scripting: enabled), so you never flash in colour before the deferred script counts; the
        count's rules come after, so they take over once it writes data-hv-checked, and when the
        page's guard removes data-hv-wait because hero.js never did, nothing grays you. Without
        scripts there is no gray at all. A step eases in under prefers-reduced-motion:
        no-preference only, and not the first count."""
        rules = self.scene_rules()
        gray = {}
        for ctx, sel, decls in rules:
            m = re.fullmatch(r'\[data-hv-checked="(\d)"\] \.hv-scene', sel)
            if m and "--hv-gray" in decls and not ctx:
                gray[int(m.group(1))] = float(decls["--hv-gray"])
        self.assertEqual(sorted(gray), list(range(8)))
        self.assertEqual((gray[0], gray[7]), (1.0, 0.0))
        self.assertEqual([gray[n] for n in range(8)], sorted(gray.values(), reverse=True))
        self.assertEqual(len(set(gray.values())), 8)
        top = {sel: decls for ctx, sel, decls in rules if not ctx}
        self.assertEqual(top["[data-hv-checked] .hv-person"], {"filter": "grayscale(var(--hv-gray))"})
        self.assertEqual(top['[data-hv-checked="7"] .hv-person'], {"filter": "none"})
        lit = top["[data-hv-active] .hv-person,[data-hv-cheer] .hv-person"]["filter"]
        self.assertTrue(lit.startswith("grayscale(var(--hv-gray,0)) ") and lit.endswith("var(--hv-lit)"), lit)
        early = {sel: decls for ctx, sel, decls in rules if ctx == ("@media (scripting:enabled)",)}
        self.assertEqual(early, {"[data-hv-wait] .hv-scene": {"--hv-gray": "1"},
                                 "[data-hv-wait] .hv-person": {"filter": "grayscale(var(--hv-gray))"}})
        # the count's rules, as specific as the early ones, come after them, so they win
        index = {sel: i for i, (ctx, sel, decls) in enumerate(rules)}
        self.assertLess(max(index[s] for s in early), min(index[s] for s in ('[data-hv-checked="0"] .hv-scene', "[data-hv-checked] .hv-person")))
        # no rule outside those grays you without the script's count or the scripting query
        for ctx, sel, decls in rules:
            if "grayscale" in decls.get("filter", "") and ctx != ("@media (scripting:enabled)",):
                self.assertTrue(sel.startswith(("[data-hv-checked]", "[data-hv-active]")), sel)
        eased = [(ctx, sel) for ctx, sel, decls in rules if "filter" in decls.get("transition", "")]
        self.assertEqual(eased, [(("@media (prefers-reduced-motion:no-preference)",),
                                  '[data-hv-checked]:not([data-hv-checked="0"]) .hv-person')])

    def test_scene_person_is_a_pointer_only_delight_inside_an_image(self):
        """The scene is an image: nothing in it takes focus or carries a role but its root's img.
        The person's hit area is transparent, lies left of every plate's (the board's corner is
        at x = 13.3), and takes pointer events only once hero.js has run (data-enhanced); the
        moment it plays (data-hv-cheer, and T1 or T2 open) has its parts in the scene: the glow,
        the indigo screen with its lock, the bubble with the shield and two sparkles, and two
        ripples. The bubble and the sparkles stay inside the viewBox, left of the board."""
        svg = parse_html(self.svg).find("svg")
        for node in svg.iter():
            self.assertNotIn("tabindex", node.attrs, node.tag)
            self.assertFalse(node is not svg and "role" in node.attrs, node.tag)
        self.assertEqual(svg.find_all(("a", "foreignobject")), [])
        hit = svg.find("path", cls="hv-you-hit")
        xs = [x for x, y in path_points(hit.attrs["d"])]
        self.assertGreaterEqual(min(xs), -28)
        self.assertLessEqual(max(xs), 13.3 - 5)
        rules = {sel: decls for ctx, sel, decls in self.scene_rules() if not ctx}
        self.assertEqual((rules[".hv-you-hit"]["fill"], rules[".hv-you-hit"]["pointer-events"]), ("transparent", "none"))
        self.assertEqual(rules["[data-enhanced] .hv-you-hit"]["pointer-events"], "all")
        for cls in ("hv-you-glow", "hv-ptee", "hv-pscreen-tee", "hv-plock", "hv-shield", "hv-shlock"):
            self.assertEqual(len(svg.find_all(cls=cls)), 1, cls)
        bubble = svg.find("g", cls="hv-bubble")
        sparkles = bubble.find_all("path", cls="hv-twinkle")
        self.assertEqual([p.attrs["d"].count("M") for p in sparkles], [2])  # two sparkles, one element
        self.assertEqual(len(svg.find_all("ellipse", cls="hv-ripple")), 2)
        for c in bubble.find_all("circle"):
            cx, r = float(c.attrs["cx"]), float(c.attrs["r"])
            self.assertGreaterEqual(cx - r, -28)
            self.assertLess(cx + r, 13.3)
        for spark in bubble.find_all("path", cls="hv-twinkle"):
            xs = [float(v) for v in re.findall(r"[MC ](-?[\d.]+),", spark.attrs["d"])]
            self.assertGreaterEqual(min(xs), -28)
            self.assertLess(max(xs), 13.3)
        # the protected look shows for T1 and T2 and for a click, never for T3 to T7
        shown = ",".join(sel for sel, decls in rules.items() if decls.get("opacity") == "1" and "hv-bubble" in sel)
        self.assertEqual(sorted(set(re.findall(r'\[data-hv-(active="\d"|cheer)\]', shown))), ['active="1"', 'active="2"', "cheer"])

    def test_scene_draws_the_person_outside_the_stack(self):
        """The person stands on the ground left of the board's left corner (x = 13.3),
        with the phone at least 6 units clear of it, inside the viewBox that grew 28
        units on the left for them; every plate's hit area starts at that corner."""
        svg = parse_html(self.svg).find("svg")
        person = svg.find("g", cls="hv-person")
        points = []
        for node in person.iter():
            if node.tag == "path":
                points += path_points(node.attrs["d"])
            elif node.tag == "ellipse":
                cx, cy, rx, ry = (float(node.attrs[k]) for k in ("cx", "cy", "rx", "ry"))
                points += [(cx - rx, cy - ry), (cx + rx, cy + ry)]
        xs, ys = [x for x, y in points], [y for x, y in points]
        self.assertGreater(len(points), 50)  # the figure is drawn, not a stub
        self.assertLessEqual(max(xs), 13.3 - 6)
        self.assertGreaterEqual(min(xs), -28)
        self.assertLessEqual(max(ys), 597)
        hits = [x for p in svg.find("g", cls="hv-hits").find_all("path", cls="hv-hit") for x, y in path_points(p.attrs["d"])]
        self.assertEqual(min(hits), 13.3)


class StylesheetTests(unittest.TestCase):
    """static/site.css: the TEE indigo marks TEE coverage only, and the hero's control stays plain."""

    @classmethod
    def setUpClass(cls):
        cls.rules = css_rules((ROOT / "static" / "site.css").read_text(encoding="utf-8"))
        cls.model = content.load(ROOT)

    def tokens(self, selector, media=None):
        """The custom properties that rules with SELECTOR set, inside MEDIA (or outside any at-rule)."""
        found = {}
        for context, sel, decls in self.rules:
            if sel == selector and (context == () if media is None else any(media in c for c in context)):
                found.update({k: v for k, v in decls.items() if k.startswith("--")})
        return found

    def test_tee_tokens_are_set_in_every_theme_with_7_to_1_text(self):
        blocks = {
            "light": self.tokens(":root"),
            "dark (system)": self.tokens(':root:not([data-theme="light"])', "prefers-color-scheme: dark"),
            "dark (chosen)": self.tokens(':root[data-theme="dark"]'),
        }
        for name, tokens in blocks.items():
            for token in ("--tee-ink", "--tee-wash", "--tee-rule"):
                self.assertRegex(tokens.get(token, ""), r"^#[0-9a-fA-F]{3,6}$", (name, token))
            self.assertGreaterEqual(contrast(tokens["--tee-ink"], tokens["--tee-wash"]), 7, name)

    def test_tee_colour_never_marks_links_buttons_or_focus(self):
        # element names, focus and hover states, attributes only links and buttons carry,
        # and the classes the templates put on links and buttons (the TEE toggle is a button)
        interactive = re.compile(
            r"(?:^|[\s>+~(,])(?:a|button|select|input|summary|textarea)(?=$|[\s.#:\[>+~),])"
            r"|:(?:focus|focus-visible|focus-within|hover|active)\b"
            r"|\[(?:href|aria-pressed|aria-current|data-filter|data-toggle|data-motion-toggle)\b"
            r"|\.(?:filter-btn|filter-tee|copy-btn|chat-launch|chat-aside-btn|search-link|skip-link|brand|ext|"
            r"block-more|chip|verification-motion)(?![\w-])")
        offenders = [sel for context, sel, decls in self.rules
                     if any("var(--tee-" in value for value in decls.values()) and interactive.search(sel)]
        self.assertEqual(offenders, [])

    def test_tee_spine_is_strong_only_on_direct_rows(self):
        def uses(rule, *tokens):
            return all(any(f"var({t})" in v for v in rule[2].values()) for t in tokens)
        base = [r for r in self.rules if r[1] == ".layer-tee" and not r[0]]
        self.assertTrue(base and uses(base[-1], "--tee-rule"), "the faded rule on rows reached only through measured code")
        direct = [r for r in self.rules if '[data-reach="direct"]' in r[1] and ".layer-tee" in r[1] and not r[0]]
        self.assertTrue(direct and uses(direct[-1], "--tee-ink", "--tee-wash"), "the strong rule and wash on T1 and T2")

    def test_hero_pause_control_is_square_and_unblurred(self):
        control = [(sel, decls) for context, sel, decls in self.rules
                   if "verification-motion" in sel or "data-motion-toggle" in sel]
        self.assertTrue(control)
        for sel, decls in control:
            self.assertFalse({"backdrop-filter", "-webkit-backdrop-filter"} & set(decls), sel)
            self.assertIn(decls.get("border-radius", "0"), ("0", "0px"), sel)

    def test_hero_rules_name_no_retired_pieces(self):
        """The raster hero, the dark-canvas scene and the home stack table are gone, and so are their
        rules and tokens."""
        retired = ("hero-canvas", "hero-image", "hero-core", "hero-check", ".verification-visual", "--plate-",
                   "--hero-control-", "stack-compact", "stack-compare")
        found = [sel for context, sel, decls in self.rules
                 if any(r in sel or any(r in k or r in v for k, v in decls.items()) for r in retired)]
        # .hero-who is now .hero-examples; .hero-who-line and .hero-who-label are the new "Who checks" line
        found += [sel for context, sel, decls in self.rules if re.search(r"\.hero-who(?![\w-])", sel)]
        self.assertEqual(found, [])
        # each of the seven labels lights its own leader line
        lit = [sel for context, sel, decls in self.rules if ".hero-leader:nth-child(" in sel]
        self.assertEqual(len(lit), 1)
        self.assertEqual(len(re.findall(r"\.hero-leader:nth-child\(\d\)", lit[0])), content.STACK_SIZE)

    def test_layer_cards_open_by_script_not_by_hover(self):
        """From 45em the layer cards stay hidden without hero.js, and no :hover or :focus rule opens
        one (WCAG 1.4.13). A card shows once hero.js places it (data-open-place), which for a layer
        that a mouse or pen points at waits until the pointer settles, so the open layer alone
        (.is-active) shows no card; a closed card is clipped, not removed, so screen readers keep it
        and its stories link stays in the tab order, and its entrance plays as it shows. An open card
        paints above the pause control."""
        wide = [(sel, decls) for context, sel, decls in self.rules if "@media (min-width: 45em)" in context]
        nojs = [decls for sel, decls in wide if sel == ".hero-visual:not([data-enhanced]) .hero-card"]
        self.assertTrue(nojs and nojs[-1].get("display") == "none")
        closed = [decls for sel, decls in wide if sel == ".hero-layer:not([data-open-place]) > .hero-card"]
        self.assertTrue(closed and closed[-1].get("clip-path") == "inset(50%)" and "display" not in closed[-1])
        self.assertEqual([sel for sel, decls in wide if "clip-path" in decls and ".is-active" in sel], [])
        entrance = [sel for context, sel, decls in self.rules if "hero-card-in" in decls.get("animation", "")]
        self.assertEqual(entrance, [".hero-visual:not([data-hv-instant]) .hero-layer[data-open-place] > .hero-card"])
        states = re.compile(r":(?:hover|focus|focus-visible|focus-within|active)\b")
        self.assertEqual([sel for context, sel, decls in self.rules if ".hero-card" in sel and states.search(sel)], [])
        active = [decls for sel, decls in wide if sel == ".hero-layer.is-active" and "z-index" in decls]
        control = [decls for context, sel, decls in self.rules
                   if sel == ":is(.verification-motion, [data-motion-toggle])" and "z-index" in decls]
        self.assertTrue(active and control)
        self.assertGreater(int(active[-1]["z-index"]), int(control[-1]["z-index"]))

    def test_inactive_hero_labels_step_back_without_losing_contrast(self):
        """While a card is open the other layer names turn --ink-3, which keeps 4.5:1 on the page in
        every theme. No rule fades a label, its head or its name with opacity. The one rule that takes
        a label's opacity down hides what an open card lies over (hero.js marks it .is-covered), so no
        slice of it shows at the card's edge; it steps no label back, and a hidden name stays in the
        tab order (no visibility or display), where focusing it opens its own card."""
        dim = [decls for context, sel, decls in self.rules
               if sel == "[data-hv-active] .hero-layer:not(.is-active) .hero-layer-link"]
        self.assertTrue(dim and dim[-1].get("color") == "var(--ink-3)")
        themes = {
            "light": self.tokens(":root"),
            "dark (system)": self.tokens(':root:not([data-theme="light"])', "prefers-color-scheme: dark"),
            "dark (chosen)": self.tokens(':root[data-theme="dark"]'),
        }
        for name, tokens in themes.items():
            self.assertGreaterEqual(contrast(tokens["--ink-3"], tokens["--paper"]), 4.5, name)

        def faded(value):
            try:
                return float(value) < 1
            except ValueError:
                return True   # a variable or calc() could be anything
        label = re.compile(r"^\.hero-layer(?:-link|-head)?(?![\w-])")

        def fades_a_label(rules):
            return [sel for context, sel, decls in rules
                    if "opacity" in decls and faded(decls["opacity"]) and any(label.match(s) for s in subjects(sel))]
        covered = ":is(.hero-layer, .hero-chain, .hero-hint).is-covered"
        self.assertEqual(fades_a_label(self.rules), [covered])
        self.assertEqual([(context, decls) for context, sel, decls in self.rules if sel == covered],
                         [(("@media (min-width: 45em)",), {"opacity": "0", "pointer-events": "none"})])
        # the check sees a label inside :is() and after a comma, as the covered rule writes it
        probe = css_rules(".a, :is(.x, .hero-layer).is-dim { opacity: 0.5 } .b, .hero-layer-link:hover { opacity: 0.9 }")
        self.assertEqual(fades_a_label(probe), [".a, :is(.x, .hero-layer).is-dim", ".b, .hero-layer-link:hover"])

    def test_hero_examples_named_in_chinese_keep_the_13px_floor(self):
        """On Chinese pages a label's example named in Chinese (网信办, the CAC, on T7) is set at 13px,
        the floor for Chinese text that tools/cdp.mjs check --small enforces, while a Latin name, which
        the build sets in a lang island of its own, stays at the English page's 12px, so the label
        column keeps its width. The Chinese name's line height keeps the examples' line as tall as the
        12px names at 1.25 and the marks (at most 0.95rem) make it, so no row grows."""
        top = {sel: decls for context, sel, decls in self.rules if not context}
        sizes = self.tokens(":root")
        self.assertEqual((sizes["--fs-1"], sizes["--fs-2"]), ("0.75rem", "0.8125rem"))   # 12px and 13px
        self.assertRegex(top[".hero-examples"]["font"], r"var\(--fs-1\)/1\.25 ")
        zh, latin = top['.site[lang="zh-CN"] .hero-ex'], top['.site[lang="zh-CN"] .hero-ex > [lang]']
        self.assertEqual((zh["font-size"], latin["font-size"], latin["line-height"]), ("var(--fs-2)", "var(--fs-1)", "1.25"))
        self.assertLessEqual(13 * float(zh["line-height"]), 12 * 1.25)
        self.assertLessEqual(max(logo["height"] for logo in logos.LOGOS.values()) * 16, 15.2)
        # a Latin name is an island on a Chinese page, and a Chinese name is in the page's language
        self.assertEqual((render.island_lang("ISO 42001", "zh"), render.island_lang("网信办", "zh")), ("en", ""))
        texts = [example["text"] for layer in self.model["topics"]["stack"] for example in layer["hero"]["examples"] if example.get("text")]
        langs = [render.island_lang(text["zh"] if isinstance(text, dict) else text, "zh") for text in texts]
        self.assertIn("", langs)   # at least one example is named in Chinese, which this rule is for

    def test_hero_phone_layout_switches_where_hero_js_does(self):
        """The stylesheet's phone layout for the hero and hero.js switch at the same width: below
        45em. Every width-in-em media query around a hero rule is that one switch."""
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        self.assertIn("matchMedia('(max-width: 44.999em)')", script)
        hero = [(context, sel) for context, sel, decls in self.rules if ".hero-" in sel]
        self.assertGreater(len(hero), 50)
        ems = {width for context, sel in hero for c in context if c.startswith("@media")
               for width in re.findall(r"\b(?:min|max)-width: ([\d.]+em)\b", c)}
        self.assertEqual(ems, {"45em", "44.999em"})

    def test_hero_hint_follows_the_input_and_the_checks(self):
        """The hint shows one line, chosen by input type through the hover and pointer media
        features, not by width alone: pointing (or Tab) from 45em where the pointer can hover; a tap
        on a layer's arrow from 45em where it cannot (touch tablets), and below 45em where it is coarse
        or cannot hover (phones); a click on the arrow below 45em with a mouse (a narrow desktop
        window). A line that names the arrow shows exactly where the chevrons do. Once every layer is
        checked (data-hv-checked="7") the lines without the promise of colour take the others' place
        in the same grid cell, by visibility, so the hint keeps its height and nothing below it moves."""
        def holds(query, state):
            terms = {"(max-width: 44.999em)": state["narrow"], "(min-width: 45em)": not state["narrow"],
                     "(hover: none)": not state["hover"], "(hover: hover)": state["hover"],
                     "(pointer: coarse)": state["coarse"], "(pointer: fine)": not state["coarse"], "screen": True}
            return any(all(terms[t.strip()] for t in alt.split(" and ")) for alt in query.split(","))

        def display(sel, state):
            value = None
            for context, selector, decls in self.rules:
                if "display" in decls and sel in split_selectors(selector) and not any(
                        "print" in c or "forced-colors" in c or "prefers-" in c for c in context) and all(
                        holds(c[len("@media "):], state) for c in context if c.startswith("@media")):
                    value = decls["display"]
            return value
        modes = ("pointer", "touch", "click")
        want = {(False, True, False): "pointer", (False, True, True): "pointer", (False, False, True): "touch",
                (False, False, False): "touch", (True, True, False): "click", (True, True, True): "touch",
                (True, False, True): "touch", (True, False, False): "touch"}
        for (narrow, hover, coarse), mode in want.items():
            state = {"narrow": narrow, "hover": hover, "coarse": coarse}
            shown = [m for m in modes if display(f".hero-hint-{m}", state) not in ("none", None)
                     or (m == "pointer" and display(".hero-hint-pointer", state) is None)]
            self.assertEqual(shown, [mode], state)
            chevrons = display("[data-enhanced] .hero-more", state) not in ("none", None)
            self.assertEqual(chevrons, mode != "pointer", state)
        top = {sel: decls for context, sel, decls in self.rules if not context}
        self.assertEqual(top[".hero-hint"].get("display"), "grid")
        self.assertEqual(top[".hero-hint-todo, .hero-hint-done"], {"grid-area": "1 / 1"})
        self.assertEqual(top['.hero-hint-done, [data-hv-checked="7"] .hero-hint-todo'], {"visibility": "hidden"})
        self.assertEqual(top['[data-hv-checked="7"] .hero-hint-done'], {"visibility": "visible"})
        # [hidden] still wins over the hint's grid, so it stays hidden until hero.js shows it
        hidden = [decls for context, sel, decls in self.rules if sel == "[hidden]" and not context]
        self.assertTrue(hidden and hidden[-1].get("display") == "none !important")

    def test_phone_chevrons_are_44px_targets(self):
        """On phones and touch tablets each row's chevron is a 44px square target (2.75rem at the
        default text size); before hero.js runs it is not shown at all. On touch tablets it lies
        above its own card, whose edge comes within it when the card opens upward."""
        phone = [decls for context, sel, decls in self.rules
                 if sel == "[data-enhanced] .hero-more" and context == ("@media (max-width: 44.999em)",)]
        self.assertTrue(phone)
        self.assertEqual((phone[-1].get("width"), phone[-1].get("height")), ("2.75rem", "2.75rem"))
        touch = [decls for context, sel, decls in self.rules
                 if sel == "[data-enhanced] .hero-more" and context == ("@media (max-width: 44.999em), (hover: none)",)]
        self.assertTrue(touch)
        self.assertEqual((touch[-1].get("width"), touch[-1].get("height")), ("2.75rem", "2.75rem"))
        tablet = [decls for context, sel, decls in self.rules
                  if sel == "[data-enhanced] .hero-more" and context == ("@media (min-width: 45em) and (hover: none)",)]
        card = [decls for context, sel, decls in self.rules if sel == ".hero-card" and "z-index" in decls]
        self.assertTrue(tablet and card)
        self.assertGreater(int(tablet[-1]["z-index"]), int(card[-1]["z-index"]))
        base = [decls for context, sel, decls in self.rules if sel == ".hero-more" and not context]
        self.assertTrue(base and base[-1].get("display") == "none")

    def test_card_bridge_is_for_a_mouse_only(self):
        """The bridge over the gap between a label and its card lets a mouse reach the card. Touch
        screens have none, since it would lie over the top of the label's chevron. A card fitted
        over its own label's head (data-open-place="fit") needs none, and one past the label that a sweep
        reaches next ("past") has that label between it and its own; both keep the top hero.js
        gives them."""
        bridges = [(context, sel, decls) for context, sel, decls in self.rules if ".hero-card::before" in sel]
        self.assertTrue(bridges)
        self.assertEqual({context for context, sel, decls in bridges}, {("@media (min-width: 45em) and (hover: hover)",)})
        own = ':is([data-open-place="fit"], [data-open-place="past"])'
        fit = [decls for context, sel, decls in bridges if sel == f".hero-layer{own} > .hero-card::before"]
        self.assertTrue(fit and fit[-1].get("display") == "none")
        card = [decls for context, sel, decls in self.rules if sel == f".hero-layer{own} > .hero-card"]
        self.assertTrue(card and card[-1].get("bottom") == "auto")

    def test_the_name_area_is_the_target_and_the_examples_are_not(self):
        """A label's name area, its head line with the code and short name ("T5 Agents"), is what a
        pointer opens a layer by, and its examples are not part of it. The name link's stretched target
        is placed on the head (position: relative) and spans the head line from the row's rule (its
        0.6rem padding and 2px rule) to the column's edge, rising 0.3rem above the line and reaching
        only 0.15rem below it, short of the examples 0.2rem down: so it is at least 24px tall (the head
        line is at least its 1.05rem icon) and a pointer on an example reaches the example. On phones
        the row places the target and the chevron, as before, and the target ends above the examples
        (at least 0.6rem padding, the 1.05rem line and their 0.3rem margin down). No mark needs a
        stacking order of its own to stay out of the target; the TEE label keeps its, for its title.
        The code is a quiet prefix, as the story tags write codes: medium weight in --ink-3 (4.5:1 in
        every theme), in the name's colour while the name is lit (hovered, focused or open)."""
        def rem(value):
            m = re.fullmatch(r"(-?[\d.]+)rem", value.strip())
            self.assertIsNotNone(m, value)
            return float(m.group(1))
        top = {sel: decls for context, sel, decls in self.rules if not context}
        phone = {sel: decls for context, sel, decls in self.rules if context == ("@media (max-width: 44.999em)",)}
        self.assertEqual(top[".hero-layer-head"].get("position"), "relative")
        t, r, b, l = top[".hero-layer-link::after"]["inset"].split(" ", 3)
        row = top[".hero-layer"]
        self.assertEqual((row["padding-left"], row["border-left"].split()[0]), ("0.6rem", "2px"))
        self.assertEqual((r, l), ("0", "calc(-0.6rem - 2px)"))
        icon = rem(top[".hero-layer-icon"]["height"])
        gap = rem(top[".hero-examples"]["margin-top"])
        self.assertLess(-rem(b), gap)   # short of the examples
        self.assertGreaterEqual((icon - rem(t) - rem(b)) * 16, 24)
        # phones: the row places the target and the chevron; the target ends above the examples
        self.assertEqual(phone[".hero-layer-head"].get("position"), "static")
        after = phone[".hero-layer-link::after"]
        self.assertEqual(after["inset"], "0 2.75rem auto 0")
        pad = rem(phone[".hero-layer"]["padding"].split()[0])
        phone_gap = rem(phone[".hero-examples"]["margin-top"])
        self.assertLess(rem(after["height"]), pad + icon + phone_gap)
        self.assertGreaterEqual(rem(after["height"]) * 16, 24)
        # no mark is stacked over the target any more; the TEE label is, so its title shows on hover
        self.assertEqual([sel for context, sel, decls in self.rules if "hero-logo" in sel and "z-index" in decls], [])
        self.assertEqual(top[".hero-layer-head .tag"].get("z-index"), "1")
        # the code: a quiet prefix that takes the name's colour while the name is lit
        code = top[".hero-layer-code"]
        self.assertEqual((code.get("color"), code.get("font-weight"), code.get("font-variant-numeric")),
                         ("var(--ink-3)", "500", "tabular-nums"))
        lit = top[".hero-layer-link:is(:hover, :focus-visible) .hero-layer-code, .hero-layer.is-active .hero-layer-code"]
        self.assertEqual(lit, {"color": "inherit"})

    def test_hero_labels_light_on_hover_only_without_the_script(self):
        """Without hero.js, hovering or focusing a label's link lights its rule and its leader; with
        it, only the open layer's label is lit, so a focused label and a hovered one never light at
        once."""
        lit = [sel for context, sel, decls in self.rules if ".hero-leader:nth-child(" in sel]
        self.assertEqual(len(lit), 1)
        self.assertEqual(len(split_selectors(lit[0])), content.STACK_SIZE)
        self.assertTrue(all(s.startswith(".hero-visual:not([data-enhanced]) ") for s in split_selectors(lit[0])), lit)
        rule = [sel for context, sel, decls in self.rules if ".hero-layer:has(.hero-layer-link:is(:hover, :focus-visible))" in sel]
        self.assertTrue(rule and all(sel.startswith(".hero-visual:not([data-enhanced]) ") for sel in rule), rule)

    def test_sticky_header_offset_is_scroll_padding(self):
        """Anchor targets and focus that scrolls the page stop below the sticky header: one
        scroll-padding-top on the root scroller, so no scroll-margin-top adds to it."""
        root = [decls for context, sel, decls in self.rules if sel == "html" and not context and "scroll-padding-top" in decls]
        self.assertTrue(root and root[-1]["scroll-padding-top"] == "var(--sticky-offset)")
        self.assertEqual([sel for context, sel, decls in self.rules if "scroll-margin-top" in decls], [])

    def test_home_band_tells_hero_js_where_the_intro_is(self):
        """--hero-band is "side" once the band (a query container measured in rem) puts the intro
        beside the figure, and "stacked" otherwise; hero.js reads it to place the cards. The figure's
        width is capped by the scene's height-to-width ratio, in 100svh, so that the stage (the scene
        and the row with the person's label, whose name line carries the reader's progress, and the
        hint) fits one screen: 11.25rem of the screen is left for the header, the band's padding and
        that row, and 9.75rem in the masthead. A declaration with var() is accepted when it is
        parsed, so a 100vh twin before it could never be used."""
        base = [decls for context, sel, decls in self.rules if sel == ".home-hero" and not context and "--hero-band" in decls]
        side = [(context, decls) for context, sel, decls in self.rules if sel == ".home-hero" and "--hero-band" in decls and context]
        self.assertTrue(base and base[-1]["--hero-band"] == "stacked")
        self.assertEqual([(c, d["--hero-band"]) for c, d in side], [(("@container home (min-width: 70rem)",), "side")])
        self.assertEqual(side[0][1].get("grid-template-columns"), "minmax(0, 21rem) minmax(0, 1fr)")
        masthead = [decls for context, sel, decls in self.rules
                    if sel == ".home-intro" and context == ("@container home (min-width: 56rem) and (max-width: 69.999rem)",)]
        self.assertTrue(masthead and masthead[-1].get("display") == "grid")
        caps = [(context, decls["max-width"]) for context, sel, decls in self.rules
                if sel == ".home-hero > .hero-visual" and "max-width" in decls]
        self.assertTrue(caps and all("100svh" in cap and "var(--hero-ratio)" in cap for context, cap in caps), caps)
        self.assertEqual([(context, re.search(r"100svh - ([\d.]+rem)", cap).group(1)) for context, cap in caps],
                         [((), "11.25rem"), (("@container home (min-width: 56rem) and (max-width: 69.999rem)",), "9.75rem")])
        text = re.sub(r"/\*.*?\*/", "", (ROOT / "static" / "site.css").read_text(encoding="utf-8"), flags=re.S)
        self.assertEqual(re.findall(r"max-width:[^;{}]*\b100vh\b", text), [])

    def test_hero_prints_as_a_list_of_layers(self):
        """In print the scene, leaders, cards, the tooltip and script-only controls go; the figure
        itself stays, so the person's label, the layers with "Who checks", the legend and the links
        print."""
        printed = [(sel, decls) for context, sel, decls in self.rules if "@media print" in context]
        hidden = [s.strip() for sel, decls in printed if decls.get("display", "").startswith("none") for s in sel.split(",")]
        for piece in (".hero-art", ".hero-leaders", ".hero-card", ".hero-more", ".hero-hint", ".hero-tip"):
            self.assertIn(piece, hidden)
        self.assertFalse([s for s in hidden if re.search(r"\.hero-visual(?![\w-])", s)], hidden)
        who = [decls for sel, decls in printed if sel == ".hero-who-line"]
        self.assertTrue(who and who[-1].get("display") == "block" and "padding-left" in who[-1])
        # each label keeps its code before its name, which the story tags refer to (print adds no second
        # one), and the legend stays on one page
        self.assertEqual([sel for sel, decls in printed if "::before" in sel and ".hero-layer" in sel], [])
        self.assertNotIn(".hero-layer-code", hidden)
        legend = [decls for sel, decls in printed if sel == ".hero-chain" and "break-inside" in decls]
        self.assertTrue(legend and legend[-1]["break-inside"] == "avoid")

    def test_phones_show_who_checks_at_rest_on_the_tee_rows_only(self):
        """On phones a row's "Who checks" shows at rest only on T1 and T2, the TEE rows, where it says
        that the reader's own device checks (owner decision 4); on T3 to T7 it shows once the row is
        open, with its card. One rule hides it, keyed to markup the build writes (.is-tee) and to the
        open row (.is-open), not to script that sets it, and only under [data-enhanced], so without
        hero.js, when every card is open in its row, every row keeps its line; and on screens only, so
        print keeps every row's line."""
        phone = ("@media (max-width: 44.999em)",)
        shown = [decls for context, sel, decls in self.rules if sel == ".hero-who-line" and context == phone]
        self.assertTrue(shown and shown[-1].get("display") == "block")
        hiding = [(context, sel) for context, sel, decls in self.rules
                  if decls.get("display") == "none" and ".hero-who-line" in subjects(sel)]
        rest = "[data-enhanced] .hero-layer:not(.is-tee):not(.is-open) > .hero-who-line"
        # hidden from 45em (the base rule), and at rest on phones, on screens only
        self.assertEqual(hiding, [((), ".hero-who-line"), (("@media screen and (max-width: 44.999em)",), rest)])
        printed = [decls for context, sel, decls in self.rules if sel == ".hero-who-line" and "@media print" in context]
        self.assertTrue(printed and printed[-1].get("display") == "block")
        # what the rule's row compound excludes: a row that is either keeps its line at rest
        row = re.search(r"\.hero-layer((?::not\(\.[\w-]+\))+) >", rest).group(1)
        keeps = set(re.findall(r":not\(\.([\w-]+)\)", row))
        self.assertEqual(keeps, {"is-tee", "is-open"})
        # the TEE rows' lines address the reader's device ("a user's device" is owner decision 4's
        # alternative); no other row's line names a device
        device = {"en": re.compile(r"\b(?:your|a user's) device\b", re.I), "zh": re.compile("(?:你的|用户的)设备")}
        stack = self.model["topics"]["stack"]
        for lang in content.LANGS:
            s = Site(self.model, "preview")
            s.lang, s.current = lang, "/zh/" if lang == "zh" else "/"
            s.hero_svg = build.hero_svg()
            s.hero_anchors = build.hero_anchors(s.hero_svg, len(stack))
            rows = parse_html(s.hero()).find("ol", cls="hero-layers").kids("li", cls="hero-layer")
            self.assertEqual(len(rows), len(stack), lang)
            # at rest no row is open, so the rows that keep the line are the TEE rows: T2 and T1
            at_rest = [r.attrs["data-n"] for r in rows if r.classes & (keeps - {"is-open"})]
            self.assertEqual(at_rest, ["2", "1"], lang)
            self.assertEqual(at_rest, [str(len(stack) - i) for i, layer in enumerate(stack) if layer["tee"]["reach"] == "direct"], lang)
            for r, layer in zip(rows, stack):
                text = r.find("p", cls="hero-who-line").text()
                self.assertTrue(text.endswith(norm(s.t(layer["checkers"]))), (lang, layer["id"], text))
                self.assertEqual(bool(device[lang].search(text)), r.attrs["data-n"] in at_rest, (lang, layer["id"], text))

    def test_legend_samples_are_drawn_in_the_chain_indigo(self):
        """The legend's samples of the line are drawn in the indigo the scene draws the chain in, so a
        reader can match them to the drawing: --tee-ink, which is the scene's --hv-tee, the stroke of the
        chain's TEE run, in light and in both dark blocks. The missing run's stubs step back to 0.6,
        which still keeps 3:1 against the page in every theme (WCAG 1.4.11), as do the others at full
        strength. The words stay in ink. In forced colours every sample is CanvasText, at full opacity,
        the missing run's stubs too (its gap says "missing")."""
        sample = [(context, sel, decls) for context, sel, decls in self.rules if ".hero-chain-sample" in subjects(sel)]
        screen = {sel: decls for context, sel, decls in sample if not context}
        missing = '.hero-chain-runs [data-bind="missing"] .hero-chain-sample'
        self.assertEqual(set(screen), {".hero-chain-sample", missing})
        self.assertEqual((screen[".hero-chain-sample"].get("color"), screen[".hero-chain-sample"].get("stroke")),
                         ("var(--tee-ink)", "currentColor"))
        self.assertEqual(screen[missing], {"opacity": "0.6"})
        forced = {sel: decls for context, sel, decls in sample if context == ("@media (forced-colors: active)",)}
        self.assertEqual(forced, {".hero-chain-runs .hero-chain-sample": {"color": "CanvasText"}, missing: {"opacity": "1"}})
        self.assertEqual({context for context, sel, decls in sample} - {(), ("@media (forced-colors: active)",)}, set())
        # the words: the runs in --ink-2, and no other part of the legend in a TEE colour
        runs = [decls for context, sel, decls in self.rules if sel == ".hero-chain-runs" and not context]
        self.assertTrue(runs and runs[-1].get("color") == "var(--ink-2)")
        self.assertEqual([sel for context, sel, decls in self.rules
                          if ".hero-chain" in sel and any("var(--tee-" in v for v in decls.values())], [".hero-chain-sample"])
        # --tee-ink is the scene's --hv-tee in every theme, and the scene strokes the chain's TEE run with it
        scene = css_rules(re.search(r"<style>(.*?)</style>", build.hero_svg(), re.S).group(1))
        hv = {
            "light": [d for c, sel, d in scene if sel == ".hv-scene" and not c and "--hv-tee" in d],
            "dark (system)": [d for c, sel, d in scene if any("prefers-color-scheme:dark" in x.replace(" ", "") for x in c) and "--hv-tee" in d],
            "dark (chosen)": [d for c, sel, d in scene if sel == '[data-theme="dark"] .hv-scene' and "--hv-tee" in d],
        }
        self.assertTrue(any(sel == ".hv-bm.hv-t" and d.get("stroke") == "var(--hv-tee)" for c, sel, d in scene))
        themes = {
            "light": self.tokens(":root"),
            "dark (system)": self.tokens(':root:not([data-theme="light"])', "prefers-color-scheme: dark"),
            "dark (chosen)": self.tokens(':root[data-theme="dark"]'),
        }
        alpha = float(screen[missing]["opacity"])
        for name, tokens in themes.items():
            self.assertEqual(len(hv[name]), 1, name)
            self.assertEqual(tokens["--tee-ink"].lower(), hv[name][0]["--hv-tee"].lower(), name)
            self.assertGreaterEqual(contrast(tokens["--tee-ink"], tokens["--paper"]), 3, name)
            self.assertGreaterEqual(contrast(mix(tokens["--tee-ink"], tokens["--paper"], alpha), tokens["--paper"]), 3, name)
        # the check above sees a sample that fades too far: 0.5 fails on the light page
        self.assertLess(contrast(mix(themes["light"]["--tee-ink"], themes["light"]["--paper"], 0.5), themes["light"]["--paper"]), 3)

    def test_a_tapped_card_ends_wholly_in_view(self):
        """From 45em a card that a tap opens ends wholly in view (static/hero.js runs here in Node with a
        stand-in page): bring() scrolls the page by the least that puts the card between the sticky
        header and the window's bottom, 8px clear of each, or, when the card is taller than that, puts its
        top just under the header; a card already in view scrolls nothing. The scroll is the page's own
        (behavior "auto", smooth) and instant under reduced motion. place() puts a touch card that fits
        neither side on the side with more room, but below its label when, above it, the page could not
        scroll the card's top clear of the header. Only a tap scrolls: set() calls bring() after place()
        for a touch, and a resize or a focus does not."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        bring, place, setter = js_const(code, "bring"), js_const(code, "place"), js_const(code, "set")
        shower = js_const(code, "show")
        self.assertRegex(shower, r"place\(row, by, [^;]*\);\s*opened = performance\.now\(\);\s*if \(by === 'touch'\) bring\(row\);")
        self.assertRegex(setter, r"else show\(row, by\);")   # a tap shows its card at once
        self.assertEqual(len(re.findall(r"\bbring\(", code)), 1)
        resize = code[code.index("addEventListener('resize'"):]
        self.assertNotIn("bring", resize[:resize.index("\n")])
        harness = """
const vm = require('node:vm');
const BRING = %s, PLACE = %s;
const rect = (top, bottom, left = 0, right = 100) => ({ top, bottom, left, right, width: right - left, height: bottom - top });
// bring(): the header's bottom HB, the window's height IH, the card from T to B
const bring = ({ hb, ih, t, b, reduced = false }) => {
  const calls = [];
  const fn = vm.runInNewContext(BRING + '\\n;bring', {
    header: { getBoundingClientRect: () => rect(0, hb) }, card: () => ({ getBoundingClientRect: () => rect(t, b) }),
    reduced: { matches: reduced }, window: { innerHeight: ih, scrollBy: o => calls.push(o) } });
  fn({});
  return calls;
};
// place(): for input BY, a row from RT to RB (its head the first 17px) that prefers PREF, a card H
// tall, the scene's top at LIST, the stage's bottom at STAGE, the bottom of the control shown at the
// top right (the pause control hidden, "Check all layers" in its place) at PAUSE, the page scrolled to Y
const place = ({ by, ih, hb, y, rt, rb, h, pref, list, stage, pause }) => {
  const row = { dataset: { place: pref }, classList: { toggle() {} }, removeAttribute(k) { if (k === 'data-open-place') delete this.dataset.openPlace; },
    getBoundingClientRect: () => rect(rt, rb, 60, 100), querySelector: () => ({ getBoundingClientRect: () => rect(rt, rt + 17, 60, 100) }) };
  const c = { style: { removeProperty() {} }, offsetHeight: h, getBoundingClientRect: () => rect(rt, rt + h, 55, 100) };
  vm.runInNewContext(PLACE + '\\n;place(row, by)', {
    row, by, card: () => c, rows: [row], covers: [], band: null, document: { documentElement: {} },
    list: { getBoundingClientRect: () => rect(list, stage) }, stage: { getBoundingClientRect: () => rect(list, stage) },
    header: { getBoundingClientRect: () => rect(0, hb) },
    controls: [{ hidden: true, getClientRects: () => [], getBoundingClientRect: () => rect(0, 0) },
      { hidden: false, getClientRects: () => [1], getBoundingClientRect: () => rect(pause - 36, pause, 80, 100) }],
    getComputedStyle: () => ({ fontSize: '16px', getPropertyValue: () => 'stacked' }),
    window: { innerHeight: ih, scrollY: y } });
  return row.dataset.openPlace + (c.style.top ? ' ' + c.style.top : '');
};
const tablet = { hb: 65, ih: 768 }, phone = { hb: 92, ih: 430 };
console.log(JSON.stringify({
  bring: [
    bring({ ...tablet, t: 100, b: 500 }),                  // in view
    bring({ ...tablet, t: 305, b: 985 }),                  // past the bottom: up to 760
    bring({ ...tablet, t: 20, b: 420 }),                   // under the header: down to 73
    bring({ ...tablet, t: 300, b: 1100 }),                 // taller than 73 to 760: its top to 73
    bring({ ...tablet, t: -200, b: 600 }),                 // taller, above: its top to 73
    bring({ ...tablet, t: 305, b: 985, reduced: true }),   // reduced motion
    bring({ ...tablet, t: 72.5, b: 500 }),                 // half a pixel: nothing
  ],
  place: [
    // a phone on its side, near the page's top: no room either side, more above, but the page
    // cannot scroll a card above its label clear of the header, so a touch card opens below
    place({ ...phone, by: 'touch', y: 0, rt: 300, rb: 340, h: 534, pref: 'down', list: 150, stage: 1000, pause: 140 }),
    // the same scrolled further down the page: above is reachable, and has more room
    place({ ...phone, by: 'touch', y: 900, rt: 300, rb: 340, h: 534, pref: 'down', list: 150, stage: 1000, pause: 140 }),
    // the keyboard opens it below, and so does the mouse, since the card fits neither beside the
    // label nor over its head, and below the label more than its head and first lines show
    place({ ...phone, by: 'mouse', y: 0, rt: 300, rb: 340, h: 534, pref: 'down', list: 150, stage: 1000, pause: 140 }),
    place({ ...phone, by: 'key', y: 0, rt: 300, rb: 340, h: 534, pref: 'down', list: 150, stage: 1000, pause: 140 }),
    // a tablet: the card fits above, its preferred side
    place({ ...tablet, by: 'touch', y: 0, rt: 600, rb: 640, h: 380, pref: 'up', list: 150, stage: 900, pause: 140 }),
    // a mouse in a window 768px tall: no room beside the label, so the card is fitted over its
    // head (ending at the head's bottom, 449), from 137, below the control's 125 and its 0.4rem
    place({ ...tablet, by: 'mouse', y: 0, rt: 432, rb: 468, h: 312, pref: 'up', list: 89, stage: 762, pause: 125 }),
  ],
}));
""" % (json.dumps(bring), json.dumps(place))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        self.assertEqual(got["bring"], [
            [],
            [{"top": 225, "behavior": "auto"}],
            [{"top": -53, "behavior": "auto"}],
            [{"top": 227, "behavior": "auto"}],
            [{"top": -273, "behavior": "auto"}],
            [{"top": 225, "behavior": "instant"}],
            [],
        ])
        self.assertEqual([p.split()[0] for p in got["place"]], ["down", "up", "down", "down", "up", "fit"])
        # the fitted card ends at its label's head's bottom: 449 - 312 - 432, from its row's top
        self.assertEqual(got["place"][5], "fit -295px")

    def test_a_swept_label_keeps_the_next_label_clear(self):
        """From 45em a layer that a mouse or pen points at opens at once and is checked, but its card
        shows only once the pointer settles (settle(): under 3px in the last 100ms, or no move for
        STILL ms), so a sweep down or up the labels or the plates meets no card on its way. When the
        card of a label that the pointer reached along the column shows, place() (run here in Node with
        a stand-in stage, its numbers those of 1440 x 900, 1366 x 768 and 1280 x 720) keeps it clear of
        the label the sweep reaches next, CLEAR px away, more than the 8px within which a label counts
        as covered: on the side the pointer came from when the card fits there (T4 going down opens
        above); else, going down, over its own label's head, ending at the head's bottom (a shorter T5
        card: fit); else past the next label (T7 and T5 going down: past, below T6 and T4; T1 going
        up: above T2); else, on a short window, with its head in view, running past the window's
        bottom: below its own label going up (T1 and T2 at 1366 x 768: down), just below the next
        label going down (T2 at 1280 x 720: past). The next label is never covered, and no card lies
        over its own label's examples, whose marks keep their names; without a way along the column (a
        plate) the card takes its preferred side as before, or, with room on neither side, its label's
        head (T2 at 1366 x 768) or the room below it (T2 at 1280 x 720). The next name opens as the
        pointer reaches it, or, when it lies between a card and its own label (past) and the pointer
        heads for that card, once the pointer stops on it or turns away (test_triggers_open_and_cards_
        stay_while_the_pointer_heads_for_them), so a sweep that rests on a name goes on from there and a
        straight path from the name reaches its card past the next label. A name that the pointer came
        onto from the side (or from its plate) takes the way to its neighbour not checked yet (toward(),
        run here in Node): T7 and T1 have one neighbour each; with both or neither left to check there is
        no way, and the card takes its preferred side. way() keeps the way along the column while a label
        lies ahead that way, and else, for the name the pointer came onto last, asks toward()."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        place, setter, point = js_const(code, "place"), js_const(code, "set"), js_const(code, "point")
        clear = int(re.search(r"const CLEAR = (\d+);", code).group(1))
        self.assertGreater(clear, 8)
        # pointing opens without a card (hover); the name a pointer comes onto, which aim() finds once a
        # frame, passes the way it came, measured where the pointer is (travelOf()); no listener on the
        # rows themselves, whose examples open nothing
        self.assertIn("set(row, 'mouse', true, dir)", point)
        self.assertRegex(setter, r"if \(hover\) \{[^}]*is-covered[^}]*\} else show\(row, by\);")
        self.assertNotIn("addEventListener('pointerenter'", code)
        aim = js_const(code, "aim")
        self.assertIn("const dir = head && entered ? travelOf() : null;", aim)
        self.assertIn("if (row && entered) onLabel = head ? row : null;", aim)
        for gone in ("hold", "release", "holdRest"):
            self.assertNotRegex(code, r"\bconst " + gone + r" = ", gone)
        self.assertIsNotNone(re.search(r"\bSTILL = \d+", code), "the wait for a pointer to stop (STILL)")
        self.assertRegex(js_const(code, "settle"), r"show\(active, 'mouse', true\)")
        # the card's way is worked out when it shows, from way(), so a label from the side has one too
        self.assertIn("if (by === 'mouse') travel = way(row);", js_const(code, "show"))
        # travel is measured from the pointer's positions over the last TRAIL ms, not from a rest before
        self.assertIn("trail.find(p => now - p.t <= TRAIL)", js_const(code, "travelOf"))
        harness = """
const vm = require('node:vm');
const PLACE = %s, CLEAR = %d;
const rect = (top, bottom, left, right) => ({ top, bottom, left, right, width: right - left, height: bottom - top });
// place() for the mouse on the row of layer N, its card H tall, coming DIR along the column, in a stage whose
// rows (T7 first, 35px tall: a head 17px tall, then the examples from 20px) start at TOPS, from the scene's
// top LIST to the stage's bottom STAGE, in a window IH tall under a header ending at HB, with "Check all
// layers" ending at PAUSE. The card's top is read where place() put it (placed), whatever its side
const run = ({ n, h, dir, tops, list, stage, ih, hb = 65, pause = 125 }) => {
  const covered = new Set();
  const rows = tops.map((t, i) => ({ n: 7 - i, dataset: { n: String(7 - i), place: t < (list + stage) / 2 ? 'down' : 'up' },
    classList: { toggle(c, on) { if (c === 'is-covered') on ? covered.add(7 - i) : covered.delete(7 - i); } },
    removeAttribute() {}, getBoundingClientRect: () => rect(t, t + 35, 1016, 1300),
    querySelector: sel => (sel === '.hero-layer-head' ? { getBoundingClientRect: () => rect(t, t + 17, 1016, 1300) } : null) }));
  const row = rows[7 - n];
  const c = { style: { top: '', removeProperty() { this.top = ''; } }, offsetHeight: h, getBoundingClientRect: () => rect(0, h, 981, 1300) };
  const ctx = {
    row, dir, CLEAR, card: () => c, rows, covers: [], band: null, placed: null, document: { documentElement: {} },
    list: { getBoundingClientRect: () => rect(list, stage, 1016, 1300) }, stage: { getBoundingClientRect: () => rect(list, stage, 532, 1300) },
    header: { getBoundingClientRect: () => rect(0, hb, 0, 1440) },
    controls: [{ hidden: false, getClientRects: () => [1], getBoundingClientRect: () => rect(pause - 36, pause, 1180, 1300) }],
    getComputedStyle: () => ({ fontSize: '16px', getPropertyValue: () => 'stacked' }), window: { innerHeight: ih, scrollY: 0 } };
  vm.runInNewContext(PLACE + '\\n;place(row, "mouse", dir)', ctx);
  const top = row.getBoundingClientRect().top + ctx.placed.dy;
  return { at: row.dataset.openPlace, top, bottom: top + h, styled: c.style.top !== '', covered: [...covered].sort().reverse() };
};
const wide = { tops: [176, 243, 311, 378, 446, 513, 581], list: 89, stage: 876, ih: 900 };
const mid = { tops: [157, 212, 267, 322, 377, 432, 487], list: 89, stage: 762, ih: 768 };
const low = { tops: [150, 200, 251, 302, 352, 403, 453], list: 89, stage: 714, ih: 720 };
console.log(JSON.stringify({
  t7: run({ ...wide, n: 7, h: 220, dir: 'down' }),
  t5: run({ ...wide, n: 5, h: 198, dir: 'down' }),
  t5fit: run({ ...wide, n: 5, h: 190, dir: 'down' }),
  t4: run({ ...wide, n: 4, h: 198, dir: 'down' }),
  t1: run({ ...wide, n: 1, h: 273, dir: 'up' }),
  t1short: run({ ...mid, n: 1, h: 312, dir: 'up' }),
  t2up: run({ ...mid, n: 2, h: 312, dir: 'up' }),
  t2plate: run({ ...mid, n: 2, h: 312, dir: null }),
  t2short: run({ ...low, n: 2, h: 330, dir: 'down' }),
  t2low: run({ ...low, n: 2, h: 330, dir: null }),
  plate: run({ ...wide, n: 7, h: 220, dir: null }),
}));
""" % (json.dumps(place), clear)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        tops = {"wide": [176, 243, 311, 378, 446, 513, 581], "mid": [157, 212, 267, 322, 377, 432, 487],
                "low": [150, 200, 251, 302, 352, 403, 453]}

        def box(kind, n):
            t = tops[kind][7 - n]
            return t, t + 35
        kinds = {"t7": "wide", "t5": "wide", "t5fit": "wide", "t4": "wide", "t1": "wide", "t1short": "mid", "t2up": "mid",
                 "t2plate": "mid", "t2short": "low", "t2low": "low", "plate": "wide"}
        # whatever its side, a card never lies over its own label's examples (from 20px into the row)
        for key, kind in kinds.items():
            n = int(key[1]) if key[1].isdigit() else 7
            examples = (box(kind, n)[0] + 20, box(kind, n)[1])
            self.assertFalse(got[key]["top"] < examples[1] and got[key]["bottom"] > examples[0], (key, got[key]))
            self.assertEqual(got[key]["styled"], got[key]["at"] in ("fit", "past"), key)
        # T7 going down: no room above, too tall for above its head, so past T6, CLEAR below it
        self.assertEqual((got["t7"]["at"], got["t7"]["top"]), ("past", box("wide", 6)[1] + clear))
        self.assertNotIn(6, got["t7"]["covered"])
        self.assertEqual(got["t7"]["covered"], [5, 4, 3, 2])
        # T5 going down, its card 198px tall: 2px short of room above its head, so past T4, CLEAR below it
        self.assertEqual((got["t5"]["at"], got["t5"]["top"], got["t5"]["covered"]), ("past", box("wide", 4)[1] + clear, [3, 2, 1]))
        # a card 190px tall fits over T5's head, ending at the head's bottom, over T6 and T7, whose turn
        # is over, and clear of T4
        self.assertEqual((got["t5fit"]["at"], got["t5fit"]["bottom"], got["t5fit"]["covered"]), ("fit", box("wide", 5)[0] + 17, [7, 6]))
        # T4 going down: above its label, the side the pointer came from
        self.assertEqual((got["t4"]["at"], got["t4"]["covered"]), ("up", [7, 6, 5]))
        # T1 going up: no room below, so past T2, ending CLEAR above it, over T3 to T6
        self.assertEqual((got["t1"]["at"], got["t1"]["bottom"], got["t1"]["covered"]), ("past", box("wide", 2)[0] - clear, [6, 5, 4, 3]))
        # short windows: going up, below its own label, with T2 (T3) clear, running past the window's
        # bottom; going down, just below the next label, also running past it
        self.assertEqual((got["t1short"]["at"], got["t1short"]["covered"]), ("down", []))
        self.assertGreater(got["t1short"]["bottom"], 768 - 8)
        self.assertEqual((got["t2up"]["at"], got["t2up"]["covered"]), ("down", [1]))
        self.assertEqual((got["t2short"]["at"], got["t2short"]["top"], got["t2short"]["covered"]), ("past", box("low", 1)[1] + clear, []))
        # from a plate: the preferred side, below T7, as before; with room on neither side, over the
        # label's head when the card fits there (1366 x 768), else below it, past the window's bottom
        self.assertEqual((got["plate"]["at"], got["plate"]["covered"]), ("down", [6, 5, 4]))
        self.assertEqual((got["t2plate"]["at"], got["t2plate"]["bottom"], got["t2plate"]["covered"]), ("fit", box("mid", 2)[0] + 17, [7, 6, 5, 4, 3]))
        self.assertEqual((got["t2low"]["at"], got["t2low"]["covered"]), ("down", [1]))
        self.assertGreater(got["t2low"]["bottom"], 720 - 8)
        # toward() and way(), with stand-in rows (T7 first) whose checked states are given
        ways = """
const vm = require('node:vm');
const TOWARD = %s, WAY = %s;
const run = (checked, n, travel, onLabel) => {
  const rows = [7, 6, 5, 4, 3, 2, 1].map(k => ({ n: k, classList: { contains: c => c === 'is-checked' && checked.includes(k) } }));
  const row = rows[7 - n];
  return vm.runInNewContext(TOWARD + '\\n' + WAY + '\\n;way(row)', { rows, row, travel, onLabel: onLabel ? row : null });
};
console.log(JSON.stringify({
  t7side: run([7], 7, null, true), t1side: run([1], 1, null, true), t7done: run([7, 6], 7, null, true),
  t4both: run([4], 4, null, true), t4down: run([7, 6, 5, 4], 4, null, true), t4up: run([4, 3, 2, 1], 4, null, true),
  t4none: run([7, 6, 5, 4, 3, 2, 1], 4, null, true), plate: run([7], 7, null, false),
  along: run([7, 6], 6, 'down', true), end: run([7], 7, 'up', true), endPlate: run([7], 7, 'up', false),
}));
""" % (json.dumps(js_const(code, "toward")), json.dumps(js_const(code, "way")))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ways.js"
            path.write_text(ways, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout), {
            # from the side: toward the one neighbour left to check; none with both or neither left
            "t7side": "down", "t1side": "up", "t7done": None, "t4both": None, "t4down": "down", "t4up": "up", "t4none": None,
            # a plate gives no way; the way along the column holds while a label lies ahead that way, and at
            # the end of the column the label the pointer came onto asks toward()
            "plate": None, "along": "down", "end": "down", "endPlate": None})

    def test_triggers_open_and_cards_stay_while_the_pointer_heads_for_them(self):
        """static/hero.js's aim(), with wait(), rest(), go(), between(), onWay(), keep(), linger(),
        settle() and stopped(), run here in Node with a stand-in label column, plates, cards and clock
        (each move is a frame in which aim() reads what the pointer is on). From 45em a layer's
        triggers are its plate and its label's name area (the head line); the examples under the name
        open, switch, close and check nothing. Moving onto a trigger opens its layer at once, with the
        way the pointer came onto a name, and its card shows once the pointer settles on one of the
        layer's triggers, not elsewhere. The open card stays while the pointer is on the layer's name,
        its plate or the card, and while the pointer heads for the card (the wait starts over each
        frame); GRACE ms after the pointer has left them all and stopped heading for the card, the card
        closes, unless keyboard focus is in its row. A name between the open layer's label and its card
        (a card past the next label) waits while the pointer heads for that card, once it has shown for
        AGE ms: a stop on it shorter than REST ms keeps the card, and it opens, with its card, once the
        pointer has not headed for the card for REST ms, or at once when the pointer turns away; a name
        beyond the card, or a trigger off the way, opens at once, and so does any trigger while the card
        is younger than AGE ms. A plate below the open layer waits as before, while its card lies below
        its label."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        layers = js_function(code, "layers")
        k = {name: int(re.search(rf"\b{name} = (\d+)", layers).group(1)) for name in ("GRACE", "STILL", "AGE", "REST")}
        # a short grace, longer than a card takes to show and than a pointer takes to cross a label's examples
        self.assertTrue(k["STILL"] < 250 <= k["GRACE"] <= 500, k)
        stopped = re.search(r"^ *const stopped = [^\n]*;$", layers, re.M).group(0).strip()
        # settle() shows the open layer's card and opens no trigger that waits: rest() does, after REST ms
        self.assertNotIn("pending", js_const(layers, "settle"))
        source = "\n".join([stopped] + [js_const(layers, name) for name in
                                        ("settle", "wait", "rest", "go", "between", "keep", "linger", "aim", "onWay")])
        # the stage's pointerleave lingers too, and every set() starts by keeping the card
        leave = layers[layers.index("addEventListener('pointerleave'"):]
        self.assertIn("linger(false);", leave[:leave.index("\n    });")])
        self.assertTrue(js_const(layers, "set").split("\n")[1].strip() == "keep();")
        harness = """
const vm = require('node:vm');
const SRC = %s, K = %s;
const run = (steps) => {
  let now = 1000, next = 1;
  const timers = new Map(), log = [];
  const tops = { 7: 100, 6: 167, 5: 234, 4: 301, 3: 368, 2: 435, 1: 502 };
  const rows = {};
  for (const n of [7, 6, 5, 4, 3, 2, 1]) {
    const row = { n, dataset: { n: String(n) }, contains: el => !!el && el.row === row,
      getBoundingClientRect: () => ({ top: tops[n], bottom: tops[n] + 35, left: 1016, right: 1300 }) };
    row.head = { row, closest: sel => (sel === '.hero-layer-head' ? row.head : null) };
    row.plate = { row, closest: sel => (sel === '.hv-hit[data-hv-n]' ? row.plate : null) };
    row.box = { row, closest: sel => (sel === '.hero-card' ? row.box : null) };
    row.examples = { row, closest: () => null };
    rows[n] = row;
  }
  const empty = { closest: () => null };
  const ctx = { ...K, EDGE: 8,
    over: null, under: null, onLabel: null, pending: null, pendingHit: false, pendingDir: null, aimed: 0, restT: 0, opened: 0,
    left: null, lx: 0, ly: 0, px: 0, py: 0, active: null, placed: null, closeT: 0, keyed: false, how: 'mouse', trail: [],
    narrow: { matches: false }, document: { activeElement: null }, performance: { now: () => now },
    plates: new Map(Object.values(rows).map(r => [r.plate, r])), heads: new Map(Object.values(rows).map(r => [r.head, r])),
    rowOf: el => (el && el.row) || null, towards: false, dir: null, at: 'down', dy: 39, h: 200,
    setTimeout: (fn, ms) => { const id = next++; timers.set(id, { fn, at: now + ms }); return id; },
    clearTimeout: id => { timers.delete(id); } };
  // heading(): the pointer heads for the open card when the step says so and the card shows
  ctx.heading = () => ctx.towards && !!ctx.active && !!ctx.active.dataset.openPlace;
  ctx.travelOf = () => ctx.dir;
  ctx.point = (row, dir = null) => ctx.set(row, 'mouse', true, dir);
  ctx.show = row => { row.dataset.openPlace = ctx.at; ctx.opened = now; ctx.placed = { row, dy: ctx.dy, h: ctx.h }; log.push('show ' + row.n); };
  vm.createContext(ctx);
  const api = vm.runInContext(SRC + '\\n;({ aim, settle, keep, wait })', ctx);
  // set() as hero.js starts it (keep the card, drop a wait), then the switch it makes
  ctx.set = (row, by, hover, dir) => {
    api.keep(); api.wait(null);
    if (row === ctx.active) { log.push('again ' + (row ? row.n : '-') + (dir ? ' ' + dir : '')); return; }
    if (ctx.active) delete ctx.active.dataset.openPlace;
    ctx.active = row; ctx.placed = null; ctx.left = null;
    log.push(row ? 'open ' + row.n + (dir ? ' ' + dir : '') : 'close');
  };
  const tick = ms => {
    const end = now + ms;
    for (;;) {
      const due = [...timers].filter(([, t]) => t.at <= end).sort((a, b) => a[1].at - b[1].at)[0];
      if (!due) break;
      timers.delete(due[0]); now = due[1].at; due[1].fn();
    }
    now = end;
  };
  // the pointer moves onto EL, heading for the open card (TOWARDS) or not, and the next frame reads it
  const move = (el, towards = false) => { tick(16); ctx.px += 5; ctx.trail = [{ t: now - 10 }, { t: now }]; ctx.towards = towards; ctx.over = el; api.aim(); };
  // the pointer stops: STILL ms later the page calls settle()
  const stop = () => { tick(K.STILL); api.settle(); };
  steps({ rows, empty, move, stop, tick, ctx, log });
  return { log, active: ctx.active ? ctx.active.n : null };
};
const past = ctx => { ctx.at = 'past'; ctx.dy = 167 + 35 + 9 - 100; ctx.h = 220; };   // T7's card past T6, 211 to 431
console.log(JSON.stringify({
  examples: run(({ rows, move, stop, tick }) => { move(rows[5].examples); move(rows[4].examples); stop(); tick(1000); }),
  name: run(({ rows, move, stop, ctx }) => { ctx.dir = 'down'; move(rows[5].head); ctx.dir = null; stop(); }),
  plate: run(({ rows, move, stop }) => { move(rows[3].plate); stop(); }),
  settleOff: run(({ rows, move, stop, tick, log }) => { move(rows[5].head); move(rows[5].examples); stop(); tick(K.GRACE - K.STILL - 1); log.push('-'); tick(1); }),
  stays: run(({ rows, move, stop, tick, log, empty }) => {
    move(rows[5].head); stop();
    move(rows[5].examples, true); tick(250); move(empty, true); tick(250);
    move(rows[5].box); tick(1000); move(rows[5].plate); tick(1000);
    move(empty); tick(K.GRACE - 1); log.push('-'); tick(1); }),
  heads: run(({ rows, move, stop, tick, log, empty }) => {
    move(rows[5].head); stop(); move(empty, true); tick(200); move(empty, true); tick(K.GRACE - 17); log.push('-'); tick(17); }),
  focus: run(({ rows, move, stop, tick, ctx, empty }) => { move(rows[5].head); stop(); ctx.keyed = true; ctx.document.activeElement = rows[5].head; move(empty); tick(1000); }),
  back: run(({ rows, move, tick, ctx }) => { move(rows[5].head); move(rows[5].examples); ctx.dir = 'up'; move(rows[5].head); tick(1000); }),
  waits: run(({ rows, move, stop, tick, ctx, log }) => { past(ctx); move(rows[7].head); stop(); tick(K.AGE);
    move(rows[7].examples, true); move(rows[6].head, true); move(rows[6].head, true); log.push('-'); stop(); log.push('still');
    tick(K.REST - K.STILL); }),
  turns: run(({ rows, move, stop, tick, ctx }) => { past(ctx); move(rows[7].head); stop(); tick(K.AGE); move(rows[6].head, true); move(rows[6].head, false); }),
  rests: run(({ rows, move, stop, tick, ctx, log }) => { past(ctx); move(rows[7].head); stop(); tick(K.AGE); move(rows[6].head, true); log.push('-'); tick(K.REST); }),
  intoCard: run(({ rows, move, stop, tick, ctx }) => { past(ctx); move(rows[7].head); stop(); tick(K.AGE);
    move(rows[6].head, true); move(rows[6].examples, true); move(rows[7].box, true); tick(1000); }),
  beyond: run(({ rows, move, stop, tick, ctx }) => { past(ctx); move(rows[7].head); stop(); tick(K.AGE); move(rows[1].head, true); }),
  young: run(({ rows, move, stop, ctx }) => { past(ctx); move(rows[7].head); stop(); move(rows[6].head, true); }),
  plates: run(({ rows, move, stop, tick, log }) => { move(rows[5].plate); stop(); tick(K.AGE); move(rows[4].plate, true); log.push('-'); move(rows[6].plate, true); }),
}));
""" % (json.dumps(source), json.dumps(k))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        self.assertEqual(got, {
            # the examples open nothing, also after a rest
            "examples": {"log": [], "active": None},
            # a name opens at once with the way the pointer came, and shows its card once the pointer stops there
            "name": {"log": ["open 5 down", "show 5"], "active": 5},
            "plate": {"log": ["open 3", "show 3"], "active": 3},
            # a pointer that stops off the triggers shows no card, and the layer closes GRACE ms after it left
            "settleOff": {"log": ["open 5", "-", "close"], "active": None},
            # the card stays while the pointer heads for it, on it and on the layer's plate; GRACE ms after the
            # pointer has left them all, it closes
            "stays": {"log": ["open 5", "show 5", "-", "close"], "active": None},
            # heading for the card starts the wait over: the card closes GRACE ms after the last frame that did
            "heads": {"log": ["open 5", "show 5", "-", "close"], "active": None},
            # keyboard focus in the row keeps the card
            "focus": {"log": ["open 5", "show 5"], "active": 5},
            # back on the open layer's name: it stays, with the way the pointer came
            "back": {"log": ["open 5", "again 5 up"], "active": 5},
            # T6, between T7's label and its card past T6, waits while the pointer heads for the card: a stop on
            # it keeps T7 for REST ms, then T6 opens with its card; it opens at once when the pointer turns
            # away; a pointer that goes on into the card keeps T7
            "waits": {"log": ["open 7", "show 7", "-", "still", "open 6", "show 6"], "active": 6},
            "turns": {"log": ["open 7", "show 7", "open 6"], "active": 6},
            "rests": {"log": ["open 7", "show 7", "-", "open 6", "show 6"], "active": 6},
            "intoCard": {"log": ["open 7", "show 7"], "active": 7},
            # T1 lies beyond the card, and a card younger than AGE ms gives way at once
            "beyond": {"log": ["open 7", "show 7", "open 1"], "active": 1},
            "young": {"log": ["open 7", "show 7", "open 6"], "active": 6},
            # a plate below the open layer, whose card lies below its label, waits; one above opens at once
            "plates": {"log": ["open 5", "show 5", "-", "open 6"], "active": 6},
        })

    def test_hero_script_writes_only_state_that_the_page_reads(self):
        """What static/hero.js writes to the DOM (spec 5.1) is what the stylesheet and the scene
        read: the figure's data-enhanced, data-hv-hits, data-hv-active, data-hv-instant (the open
        card shows without its entrance), data-hv-checked (how many layers the reader has checked),
        data-hv-cheer (the person's moment, after a click on them or once every layer is checked),
        data-hv-hop (their hop, which plays whole once T1 or T2 opens), data-animated and
        data-motion; the rows' is-active, is-checked,
        is-open and data-open-place (up, down, fit or past, with an inline top on the last two),
        which shows the card; is-covered on the rows, the legend and the hint that a shown card
        lies over; the leaders' is-active; the chevrons' aria-expanded; the pause control's label;
        the text of the progress and of the scene's description; and the tooltip that names a
        vendor mark: its text, hidden, and its top and left in the figure.
        Every attribute,
        class, data-* and inline style that the script writes is in that list, so a write that
        nothing reads fails here."""
        # comments may name anything, so only code counts as a write or a read
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        css = re.sub(r"/\*.*?\*/", "", (ROOT / "static" / "site.css").read_text(encoding="utf-8"), flags=re.S)
        scene = re.sub(r"<!--.*?-->|/\*.*?\*/", "", (ROOT / "sitegen" / "templates" / "hero-scene.svg").read_text(encoding="utf-8"),
                       flags=re.S)

        def kebab(name):
            return re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), name)

        # every write: setAttribute, removeAttribute and toggleAttribute; classList.add, remove,
        # toggle and replace; dataset.x = ...; style.x = ... and style.setProperty/removeProperty;
        # and the element properties that reflect markup
        writes = {("attr", m.group(1)) for m in re.finditer(r"\.(?:set|remove|toggle)Attribute\(\s*'([\w-]+)'", code)}
        writes |= {("class", name) for m in re.finditer(r"\.classList\.(?:add|remove|toggle|replace)\(([^)]*)\)", code)
                   for name in re.findall(r"'([\w-]+)'", m.group(1))}
        writes |= {("attr", "data-" + kebab(m.group(1))) for m in re.finditer(r"\.dataset\.(\w+)\s*=(?!=)", code)}
        writes |= {("style", kebab(m.group(1))) for m in re.finditer(r"\.style\.(\w+)\s*=(?!=)", code)}
        writes |= {("style", m.group(1)) for m in re.finditer(r"\.style\.(?:setProperty|removeProperty)\(\s*'([\w-]+)'", code)}
        writes |= {("prop", m.group(1)) for m in re.finditer(r"\.(hidden|textContent|innerText|className|id|title|tabIndex|style)\s*=(?!=)", code)}
        self.assertNotRegex(code, r"\.(?:setAttributeNS|attributes|classList\s*=|dataset\s*=|style\.cssText)")
        # each write, and where the page reads it
        readers = {
            ("attr", "data-enhanced"): css, ("attr", "data-hv-hits"): scene, ("attr", "data-hv-active"): scene,
            ("attr", "data-hv-instant"): css, ("attr", "data-hv-cheer"): scene, ("attr", "data-hv-hop"): scene,
            ("attr", "data-hv-checked"): scene, ("class", "is-checked"): css,
            ("attr", "data-animated"): scene, ("attr", "data-motion"): css, ("attr", "data-open-place"): css,
            ("attr", "aria-expanded"): css,
            ("class", "is-active"): css, ("class", "is-open"): css, ("class", "is-covered"): css,
        }
        for (kind, name), reader in readers.items():
            self.assertRegex(reader, r"[\[.]" + re.escape(name) + r"(?![\w-])", name)
        # read by the browser and screen readers rather than the page: the pause control's label
        # (its text and aria-label), the progress's text and the scene's description, [hidden] on the
        # chevrons, the hint, the progress, the pause control and "Check all layers", and the top of a
        # card that is fitted or past the next label; and the tooltip's text, [hidden], top and left
        others = {("attr", "aria-label"), ("prop", "textContent"), ("prop", "hidden"), ("style", "top"), ("style", "left")}
        # tips() writes only the tooltip's text, [hidden], top and left, and only it writes a left
        tips = js_function(code, "tips")
        self.assertRegex(tips, r"^function tips\(fig\) \{\s*const tip = fig\.querySelector\('\.hero-tip'\)")
        tip_writes = {("style", m.group(1)) for m in re.finditer(r"\.style\.(\w+)\s*=(?!=)", tips)}
        tip_writes |= {("prop", m.group(1)) for m in re.finditer(r"\.(hidden|textContent|innerText|className|id|title|tabIndex|style)\s*=(?!=)", tips)}
        self.assertEqual(tip_writes, {("prop", "textContent"), ("prop", "hidden"), ("style", "left"), ("style", "top")})
        self.assertNotRegex(tips, r"(?:set|remove|toggle)Attribute\(|classList\.|dataset\.\w+\s*=(?!=)")
        self.assertEqual(len(re.findall(r"\.style\.left\s*=(?!=)", code)), len(re.findall(r"\.style\.left\s*=(?!=)", tips)))
        self.assertEqual(writes, set(readers) | others)
        # the placements hero.js writes are the ones the stylesheet reads, fit and past included
        self.assertEqual(set(re.findall(r"\[data-open-place=\"(\w+)\"\]", css)), {"up", "down", "fit", "past"})
        for place in ("'up'", "'down'", "'fit'", "'past'"):
            self.assertIn(place, code)
        # an open card holds the pulse: motion() reads data-hv-active, which set() writes
        motion = code[code.index("function motion("):code.index("function layers(")]
        self.assertIn("hasAttribute('data-hv-active')", motion)
        # and the pulse watches the scene, not the whole figure, which on phones is about 1800px tall
        self.assertIn("observe(fig.querySelector('.hero-art')", motion)
        # focus on a name opens its card only after a key press: a tap or a click that focuses a name
        # or a chevron opens nothing through focus (focus on a card's stories link always opens it,
        # since the link must be seen). tools/cdp.mjs hero checks the same with real input
        focusin = code[code.index("addEventListener('focusin'"):code.index("addEventListener('focusout'")]
        self.assertRegex(focusin, r"if \(keyed && !dismissed\) \{\s*set\(row, 'key'\)")
        self.assertEqual(len(re.findall(r"\bset\(row\b", focusin)), 2, focusin)
        # 21.3 lights the active row and leader, and steps the other names back, under data-hv-active
        selectors = [sel for context, sel, decls in self.rules]
        for want in (".hero-layer.is-active", ".hero-leader.is-active", "[data-hv-active] .hero-layer:not(.is-active) .hero-layer-link"):
            self.assertIn(want, selectors)

    def test_your_palette_is_set_in_every_theme(self):
        """Your colours in the scene (the coat, its shade, the trousers, theirs, and your data) are
        tokens in site.css's three theme blocks, light, dark by system and dark by choice, so the
        theme toggle and the system setting both reach them; the scene reads each with its own value
        for that theme after it. The dark set is the one the scene had; the light one is brighter and
        more saturated than the scene's first light set, and the coat and the trousers keep 3:1 on
        white, also through the filter that lights you while a layer is open (--hv-lit)."""
        names = ("--you-coat", "--you-coat-2", "--you-legs", "--you-legs-2", "--you-data")
        themes = {
            "light": self.tokens(":root"),
            "dark (system)": self.tokens(':root:not([data-theme="light"])', "prefers-color-scheme: dark"),
            "dark (chosen)": self.tokens(':root[data-theme="dark"]'),
        }
        for name, tokens in themes.items():
            for token in names:
                self.assertRegex(tokens.get(token, ""), r"^#[0-9a-f]{6}$", (name, token))
        light, dark = themes["light"], themes["dark (system)"]
        self.assertEqual([dark[t] for t in names], ["#e09a45", "#c27f2e", "#7e9cc7", "#6a87b0", "#f0a24a"])
        self.assertEqual([themes["dark (chosen)"][t] for t in names], [dark[t] for t in names])
        for token in ("--you-coat", "--you-coat-2", "--you-legs", "--you-legs-2"):
            self.assertGreaterEqual(contrast(light[token], light["--paper"]), 3, token)
        for token, before in (("--you-coat", "#c97c22"), ("--you-legs", "#3d5a80")):
            self.assertGreater(saturation(light[token]), saturation(before) + 0.15, token)
            self.assertGreater(luminance(light[token]), luminance(before), token)
        scene = css_rules(re.search(r"<style>(.*?)</style>", build.hero_svg(), re.S).group(1))
        blocks = {
            "light": [d for c, sel, d in scene if sel == ".hv-scene" and not c and "--hv-coat" in d],
            "dark (system)": [d for c, sel, d in scene if any("prefers-color-scheme:dark" in x.replace(" ", "") for x in c) and "--hv-coat" in d],
            "dark (chosen)": [d for c, sel, d in scene if sel == '[data-theme="dark"] .hv-scene' and "--hv-coat" in d],
        }
        pairs = {"--hv-coat": "--you-coat", "--hv-coat2": "--you-coat-2", "--hv-legs": "--you-legs",
                 "--hv-legs2": "--you-legs-2", "--hv-data": "--you-data"}
        for name, found in blocks.items():
            self.assertEqual(len(found), 1, name)
            for hv, you in pairs.items():
                self.assertEqual(found[0][hv], f"var({you},{themes[name][you]})", (name, hv))
        lit = blocks["light"][0]["--hv-lit"]
        self.assertIn("saturate(", lit)
        for token in ("--you-coat", "--you-coat-2", "--you-legs", "--you-legs-2"):
            self.assertGreaterEqual(contrast(filtered(light[token], lit), light["--paper"]), 3, (token, lit))

    def test_tee_packets_keep_a_ring_that_shows_on_the_die(self):
        """On the TEE layers a data packet is indigo with a soft ring, and the packet rests on the
        GPU die, which is dark in both themes. On light pages an indigo dot in an indigo ring all but
        vanishes there, so the ring (--hv-pkring) is white in the scene's light palette and stays the
        TEE indigo in its two dark ones; every packet strokes with it."""
        scene = css_rules(re.search(r"<style>(.*?)</style>", build.hero_svg(), re.S).group(1))
        palettes = {
            "light": [d for c, sel, d in scene if sel == ".hv-scene" and not c and "--hv-coat" in d],
            "dark (system)": [d for c, sel, d in scene if any("prefers-color-scheme:dark" in x.replace(" ", "") for x in c)
                              and "--hv-coat" in d],
            "dark (chosen)": [d for c, sel, d in scene if sel == '[data-theme="dark"] .hv-scene' and "--hv-coat" in d],
        }
        self.assertEqual({name: [d.get("--hv-pkring") for d in found] for name, found in palettes.items()},
                         {"light": ["#ffffff"], "dark (system)": ["var(--hv-tee2)"], "dark (chosen)": ["var(--hv-tee2)"]})
        packet = [d for c, sel, d in scene if sel == ".hv-pk" and not c]
        self.assertEqual([d.get("stroke") for d in packet], ["var(--hv-pkring)"])
        self.assertEqual(packet[0].get("paint-order"), "stroke")

    def test_marks_and_progress_show_only_with_the_script(self):
        """A checked layer's mark is hidden until hero.js marks its row .is-checked, so never without
        the script, and draws in the layer's hue; it, the progress and "Check all layers" leave print.
        The button is drawn like the pause control, in its place at the figure's top right; under
        reduced motion "Still image" waits there until every layer is checked, so that the button has
        the corner to itself."""
        top = {sel: decls for context, sel, decls in self.rules if not context}
        self.assertEqual(top[".hero-tick"].get("display"), "none")
        self.assertTrue(top["[data-enhanced] .hero-layer.is-checked .hero-tick"].get("display", "").startswith("inline"))
        self.assertEqual(top[".hero-tick-icon"].get("stroke"), "var(--hl-icon, var(--ink-2))")
        printed = [s.strip() for context, sel, decls in self.rules if "@media print" in context
                   and decls.get("display", "").startswith("none") for s in sel.split(",")]
        for piece in (".hero-tick", ".hero-all", ".hero-progress"):
            self.assertIn(piece, printed)
        still = [(context, decls) for context, sel, decls in self.rules
                 if sel == '[data-hv-checked]:not([data-hv-checked="7"]) .verification-static-label']
        self.assertEqual(still, [(("@media (prefers-reduced-motion: reduce)",), {"display": "none"})])
        button = top[".hero-all"]
        self.assertEqual((button.get("position"), button.get("top"), button.get("right"), button.get("border-radius")),
                         ("absolute", "0", "0", "0"))
        self.assertFalse({"backdrop-filter", "-webkit-backdrop-filter"} & set(button))

    def test_progress_counts_the_checks_and_starts_the_loop_at_seven(self):
        """static/hero.js's progress(), run here in Node with a stand-in figure: each layer checked
        marks its row .is-checked, counts it in data-hv-checked and in the status's text, and a second
        check of the same layer changes nothing; the seventh hands layers() the layer open then
        (state.free, before the loop's update), starts the loop (state.done, then the loop's update),
        hides "Check all layers" and, once the scene is in view, plays your moment and starts the wait
        after which the loop runs beside that layer (what state.free returned).
        "Check all layers" checks the rest at once and writes the status once; if it had focus, focus
        moves to the pause control, or to the status when the control stays hidden (reduced motion).
        Once the button goes, the loop is told that the pause control stands in its place (settle), so
        that a double click on the button does not pause the loop it has just started."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        source = js_function(re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S), "progress")
        harness = """
const vm = require('node:vm');
const SRC = %s;
const run = ({ focusAll = false, pauseHidden = false } = {}) => {
  const log = [], attrs = {};
  const rows = [7, 6, 5, 4, 3, 2, 1].map(n => { const set = new Set();
    return { set, dataset: { n: String(n) }, classList: { toggle: (c, on) => { on ? set.add(c) : set.delete(c); } } }; });
  let text = '0 of 7 layers checked', listener = null;
  const status = { dataset: { progress: '{n} of 7 layers checked', done: 'All 7 layers checked' }, hidden: true,
    get textContent() { return text; }, set textContent(v) { text = v; log.push('say ' + v); }, focus: () => log.push('focus status') };
  const all = { hidden: true, addEventListener: (type, fn) => { listener = fn; }, focus: () => log.push('focus all') };
  const pause = { hidden: pauseHidden, focus: () => log.push('focus pause') };
  const complete = { hidden: true };
  const fig = {
    querySelectorAll: sel => (sel === '.hero-layer[data-n]' ? rows : []),
    querySelector: sel => ({ '.hero-progress': status, '.hero-all': all, '[data-motion-toggle]': pause, '.hero-complete': complete })[sel] || null,
    setAttribute: (k, v) => { attrs[k] = v; }, removeAttribute: k => { delete attrs[k]; },
  };
  const state = { done: false, show: [], free: () => { log.push('free'); return () => log.push('let go'); } };
  const loop = { update: () => log.push('update ' + state.done), whenShown: fn => { log.push('when shown'); fn(); },
    settle: () => log.push('settle') };
  const check = vm.runInNewContext(SRC + '\\n;progress(fig, state, loop, cheer)', {
    fig, state, loop, cheer: () => log.push('cheer'), document: { activeElement: focusAll ? all : null },
    narrow: { matches: false }, String, Set });
  const view = () => ({ checked: attrs['data-hv-checked'], text, done: state.done, marked: rows.filter(r => r.set.has('is-checked')).length,
    status: status.hidden, all: all.hidden, complete: complete.hidden,
    show: state.show.map(el => (el === status ? 'status' : el === all ? 'all' : '?')) });
  return { check, rows, log, view, click: () => listener() };
};
const one = run();
const start = one.view();
one.check(one.rows[0]); one.check(one.rows[0]); one.check(one.rows[1]);
const two = one.view();
one.log.length = 0;
one.rows.slice(2).forEach(r => one.check(r));
const seven = one.view(), sevenLog = one.log.slice();
const many = run({ focusAll: true });
many.check(many.rows[3]); many.check(many.rows[4]);
many.log.length = 0;
many.click();
const still = run({ focusAll: true, pauseHidden: true });
still.click();
console.log(JSON.stringify({ start, two, seven, sevenLog, all: many.view(), allLog: many.log, stillLog: still.log }));
""" % json.dumps(source)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        # the count's 0 waits until the figure is set up, and so do the status and the button, which
        # progress() only hands to the set-up (the forEach that calls progress() shows them)
        self.assertEqual(got["start"], {"text": "0 of 7 layers checked", "done": False, "marked": 0,
                                        "status": True, "all": True, "complete": True, "show": ["status", "all"]})
        self.assertEqual(got["two"], {"checked": "2", "text": "2 of 7 layers checked", "done": False, "marked": 2,
                                      "status": True, "all": True, "complete": True, "show": ["status", "all"]})
        self.assertEqual(got["seven"], {"checked": "7", "text": "All 7 layers checked", "done": True, "marked": 7,
                                        "status": True, "all": True, "complete": False, "show": ["status", "all"]})
        self.assertEqual(got["sevenLog"], [f"say {n} of 7 layers checked" for n in range(3, 7)]
                         + ["say All 7 layers checked", "free", "update true", "settle", "when shown", "cheer", "let go"])
        self.assertEqual(got["all"]["checked"], "7")
        self.assertFalse(got["all"]["complete"])
        self.assertEqual(got["allLog"], ["say All 7 layers checked", "free", "update true", "focus pause", "settle", "when shown",
                                         "cheer", "let go"])
        self.assertEqual(got["stillLog"], ["say All 7 layers checked", "free", "update true", "focus status", "settle", "when shown",
                                           "cheer", "let go"])

    def test_the_last_check_lets_the_loop_run_beside_its_layer(self):
        """Once every layer is checked the data moves within moments, also while a layer is still
        open and the pointer, the focus or the finger stays where it is. static/hero.js's free() and
        unfree() (run here in Node with a stand-in figure and clock): free(), which progress() calls as
        state.free at the seventh check, takes the layer open then and returns what starts the wait,
        which progress() runs as your moment plays; FREE ms later, if that layer is still the open
        one, the scene stops marking it (data-hv-active goes) and the loop's update runs, so motion(),
        which holds the loop while data-hv-active is set, lets it run; the row and its card are left
        open. A switch to another layer, a close (set() calls unfree() whenever the open layer
        changes, before it checks the new one) or a reset cancels the wait, also a close and a reopen
        of the same layer; with no layer open, or under reduced motion, nothing waits, and the wait
        starts once. FREE lets the moment's hop, sparkles and first ripple play (1.1s) and starts the
        loop early enough for the data, which leaves the phone 0.15s into it, to move within 1.5s of
        the check. The phones keep their own way: the scene stops marking the row opened last at the
        seventh check."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        free_ms = int(re.search(r"const FREE = (\d+);", code).group(1))
        self.assertTrue(1100 <= free_ms <= 1500 - 150, free_ms)
        layers, progress, motion = js_function(code, "layers"), js_function(code, "progress"), js_function(code, "motion")
        # progress() hands over the open layer at the seventh check and starts the wait with your moment
        finish = js_const(progress, "finish")
        self.assertRegex(finish, r"state\.done = true;[\s\S]*const free = state\.free\(\);\s*loop\.update\(\);")
        self.assertIn("loop.whenShown(() => { cheer(); free(); });", finish)
        self.assertIn("if (narrow.matches) fig.removeAttribute('data-hv-active');", finish)
        # layers() sets state.free; without the labels it stays a no-op
        self.assertIn("state.free = free;", layers)
        self.assertIn("free: () => () => {}", code[:code.index("function you(")])
        # set() cancels the wait whenever the open layer changes, before it checks the new one, and not
        # when the open layer comes again (a pointer onto its label or plate, focus on its card's link)
        setter = js_const(layers, "set")
        self.assertNotIn("unfree", setter[:setter.index("const from = active;")])
        self.assertRegex(setter, r"const from = active;[\s\S]*?active = row;[\s\S]*?unfree\(\);[\s\S]*?check\(row\);")
        self.assertIn("unfree();", js_const(layers, "reset"))
        self.assertIn("const held = fig.hasAttribute('data-hv-active');", motion)
        harness = """
const vm = require('node:vm');
const UNFREE = %s, FREE_FN = %s, FREE = %d;
// a stand-in clock and figure; ACTIVE is the layer open in layers()
const run = (steps, { reduced = false } = {}) => {
  let now = 0, next = 1;
  const timers = new Map(), attrs = { 'data-hv-active': '1' }, log = [];
  const ctx = { FREE, active: null, freeing: null, freeT: 0, reduced: { matches: reduced },
    fig: { removeAttribute: k => { delete attrs[k]; log.push('remove ' + k); } },
    update: () => log.push('update'),
    setTimeout: (fn, ms) => { const id = next++; timers.set(id, { fn, at: now + ms }); return id; },
    clearTimeout: id => { timers.delete(id); } };
  vm.createContext(ctx);
  const api = vm.runInContext(UNFREE + '\\n' + FREE_FN + '\\n;({ free, unfree })', ctx);
  const tick = ms => { now += ms; for (const [id, t] of [...timers]) if (t.at <= now) { timers.delete(id); t.fn(); } };
  steps({ api, ctx, tick, timers, at: () => now });
  return { marked: 'data-hv-active' in attrs, log, waiting: timers.size };
};
console.log(JSON.stringify({
  // T1 opened by the seventh check and still open: the scene lets go of it FREE ms later, not before
  early: run(({ api, ctx, tick }) => { ctx.active = 'T1'; api.free()(); tick(FREE - 1); }),
  free: run(({ api, ctx, tick }) => { ctx.active = 'T1'; api.free()(); tick(FREE); }),
  // a switch to T2 first, as set() does it (unfree, then the new layer)
  switched: run(({ api, ctx, tick }) => { ctx.active = 'T1'; api.free()(); tick(500); api.unfree(); ctx.active = 'T2'; tick(FREE); }),
  // a close, then the same layer opened again: the wait is gone, so the reopened layer holds the loop
  reopened: run(({ api, ctx, tick }) => { ctx.active = 'T1'; api.free()(); tick(300); api.unfree(); ctx.active = null; tick(100);
    api.unfree(); ctx.active = 'T1'; tick(FREE); }),
  // no layer open, as after "Check all layers" with no card open
  none: run(({ api, ctx, tick }) => { ctx.active = null; api.free()(); tick(FREE); }),
  // reduced motion: no loop to show
  reduced: run(({ api, ctx, tick }) => { ctx.active = 'T1'; api.free()(); tick(FREE); }, { reduced: true }),
  // the moment waited for the scene to come into view, and the layer closed meanwhile
  late: run(({ api, ctx, tick }) => { ctx.active = 'T1'; const go = api.free(); api.unfree(); ctx.active = null; go(); tick(FREE); }),
  // the wait starts once
  twice: run(({ api, ctx }) => { ctx.active = 'T1'; const go = api.free(); go(); go(); }),
}));
""" % (json.dumps(js_const(layers, "unfree")), json.dumps(js_const(layers, "free")), free_ms)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        held = {"marked": True, "log": [], "waiting": 0}
        self.assertEqual(got["early"], {"marked": True, "log": [], "waiting": 1})
        self.assertEqual(got["free"], {"marked": False, "log": ["remove data-hv-active", "update"], "waiting": 0})
        for case in ("switched", "reopened", "none", "reduced", "late"):
            self.assertEqual(got[case], held, case)
        self.assertEqual(got["twice"], {"marked": True, "log": [], "waiting": 1})

    def test_pause_control_ignores_the_double_click_that_checked_all(self):
        """static/hero.js's motion(), run here in Node with a stand-in figure and clock: the pause
        control takes the place of "Check all layers", so the second click of a double click on the
        button lands on it. For 600ms after settle() it ignores clicks, then a click pauses and the
        next one plays again; a repeated Enter keydown (a held key) is cancelled, so it toggles once."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        source = js_function(re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S), "motion")
        harness = """
const vm = require('node:vm');
const SRC = %s;
let now = 1000;
const on = {}, attrs = {};
const toggle = { hidden: true, dataset: { labelPause: 'Pause animation', labelPlay: 'Play animation' },
  getAttribute: k => attrs[k], setAttribute: (k, v) => { attrs[k] = v; },
  addEventListener: (type, fn) => { on[type] = fn; } };
const label = { textContent: 'Pause animation' };
const fig = { dataset: {}, querySelector: sel => ({ '[data-motion-toggle]': toggle, '[data-motion-label]': label })[sel] || null,
  hasAttribute: () => false, toggleAttribute: () => {} };
const state = { done: true };
const loop = vm.runInNewContext(SRC + '\\n;motion(fig, state)', {
  fig, state, performance: { now: () => now }, reduced: { matches: false, addEventListener: () => {} },
  document: { hidden: false, addEventListener: () => {} }, window: {} });
loop.update();
const seen = [fig.dataset.motion];
loop.settle();
now += 120; on.click(); seen.push(fig.dataset.motion);    // the second click of a double click
now += 400; on.click(); seen.push(fig.dataset.motion);    // still within 600ms of settle
now += 200; on.click(); seen.push(fig.dataset.motion);    // a click of its own: pauses
now += 300; on.click(); seen.push(fig.dataset.motion);    // and plays again
let held = 0, first = 0;
on.keydown({ key: 'Enter', repeat: true, preventDefault: () => { held++; } });
on.keydown({ key: 'Enter', repeat: false, preventDefault: () => { first++; } });
on.keydown({ key: ' ', repeat: true, preventDefault: () => { first++; } });
console.log(JSON.stringify({ seen, held, first, label: label.textContent }));
""" % json.dumps(source)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        self.assertEqual(got["seen"], ["running", "running", "running", "paused", "running"])
        self.assertEqual((got["held"], got["first"]), (1, 0))
        self.assertEqual(got["label"], "Pause animation")

    def test_hero_script_marks_the_figure_set_up_last(self):
        """static/hero.js shows what it adds and writes the figure's data-hv-checked, the count that
        the scene's gray follows, only once it has set the figure up: after progress(), layers() and
        the loop's first update it sets data-enhanced, shows the chevrons, the hint, the count and
        "Check all layers" (which progress() and layers() only collect), then writes the count. So a
        throw on the way leaves the figure as a page without the script has it, and the page's guard
        reads the count's absence at the window's load as hero.js never having run (it failed to
        load, or threw first) and removes data-hv-wait, so you are not left gray. The same step adds
        the description's sentences on the gray and the data (its data-hv-live), whatever the count
        is by then, so the description of a page where hero.js does not run says only what its still
        scene shows. The guard, run here in Node with a stand-in page, removes data-hv-wait at load
        only from a figure without data-hv-checked, and at once when the page has already loaded."""
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        init = code[code.index("document.querySelectorAll('[data-verification-visual]')"):code.index("function you(")]
        steps = [init.index(s) for s in ("progress(fig, state, loop, cheer)", "loop.update();", "fig.setAttribute('data-enhanced', '')",
                                         "state.show.forEach(el => { el.hidden = false; });",
                                         "fig.setAttribute('data-hv-checked', '0')", "desc.textContent +=")]
        self.assertEqual(steps, sorted(steps))
        self.assertIn("if (!fig.hasAttribute('data-hv-checked')) fig.setAttribute('data-hv-checked', '0');", init)
        self.assertIn("getAttribute('data-hv-live')", init)
        progress, layers = js_function(code, "progress"), js_function(code, "layers")
        self.assertNotIn("'data-hv-checked', '0'", progress)
        # The completion handler reveals its sentence only after interaction. Initial
        # set-up still collects the controls before showing them.
        progress_setup = progress.replace(js_const(progress, "finish"), "")
        for part in (progress_setup, layers):
            self.assertNotRegex(part, r"\.hidden = false|'data-enhanced'")
        self.assertIn("state.show.push(status)", progress)
        self.assertIn("state.show.push(...fig.querySelectorAll('.hero-more, .hero-hint'))", layers)
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        harness = """
const vm = require('node:vm');
const GUARD = %s;
const run = ({ ready, checked }) => {
  const attrs = new Set(['data-verification-visual', 'data-hv-wait'].concat(checked ? ['data-hv-checked'] : []));
  const fig = { hasAttribute: k => attrs.has(k), removeAttribute: k => { attrs.delete(k); } };
  let onload = null;
  const document = { readyState: ready,
    querySelectorAll: sel => (sel === '[data-verification-visual][data-hv-wait]' && attrs.has('data-hv-wait') ? [fig] : []) };
  vm.runInNewContext(GUARD, { document, addEventListener: (type, fn) => { if (type === 'load') onload = fn; } });
  const before = attrs.has('data-hv-wait');
  if (onload) onload();
  return [before, attrs.has('data-hv-wait'), !!onload];
};
console.log(JSON.stringify([run({ ready: 'loading', checked: false }), run({ ready: 'loading', checked: true }),
  run({ ready: 'interactive', checked: false }), run({ ready: 'complete', checked: false }), run({ ready: 'complete', checked: true })]));
""" % json.dumps(render.HERO_GUARD)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        # [wait before load, wait after load, waited for load]
        self.assertEqual(json.loads(run.stdout), [[True, False, True], [True, True, True], [True, False, True],
                                                  [False, False, False], [True, True, False]])

    def test_hero_script_reads_no_json_and_leaves_the_stack_cards_alone(self):
        """The layer cards are in the page (spec 5.3): hero.js fetches and parses nothing, writes
        no markup, and leaves site.js's stack cards on story tags (#stack-data, #stack-pop) alone."""
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        for banned in ("JSON.parse", "fetch(", "XMLHttpRequest", "innerHTML", "insertAdjacentHTML", "createElement",
                       "stack-data", "stack-pop", "tag-layers"):
            self.assertNotIn(banned, script)

    def test_mark_names_show_in_a_flat_tooltip_that_takes_no_pointer(self):
        """The tooltip that names a vendor mark (21.10) is drawn like the current language in the
        header's switch: --ink ground, --on-ink text, 13px, square and without a shadow; in forced
        colours it keeps a frame. hero.js places it in the figure (absolute, with a top and a left),
        it takes no pointer events, so it never comes between the pointer and a label, a card or a
        plate, and it paints above the open card and its row. No :hover or :focus rule shows it:
        hero.js alone does, after its wait, and [hidden] keeps it out until then."""
        top = [decls for context, sel, decls in self.rules if sel == ".hero-tip" and not context]
        self.assertTrue(top)
        tip = top[-1]
        self.assertEqual((tip.get("position"), tip.get("pointer-events")), ("absolute", "none"))
        self.assertEqual((tip.get("background"), tip.get("color")), ("var(--ink)", "var(--on-ink)"))
        self.assertRegex(tip.get("font", ""), r"var\(--fs-2\)")
        self.assertFalse({"box-shadow", "border-radius", "transition", "animation"} & set(tip), tip)
        card = [decls for context, sel, decls in self.rules if sel == ".hero-card" and "z-index" in decls]
        active = [decls for context, sel, decls in self.rules if sel == ".hero-layer.is-active" and "z-index" in decls]
        self.assertGreater(int(tip["z-index"]), max(int(card[-1]["z-index"]), int(active[-1]["z-index"])))
        forced = [decls for context, sel, decls in self.rules if sel == ".hero-tip" and "@media (forced-colors: active)" in context]
        self.assertTrue(forced and "CanvasText" in forced[-1].get("border", ""), forced)
        figure = [decls for context, sel, decls in self.rules if sel == ".hero-visual" and not context and "position" in decls]
        self.assertEqual(figure[-1]["position"], "relative")   # its containing block, from whose box hero.js places it
        self.assertEqual([sel for context, sel, decls in self.rules if ".hero-tip" in sel and re.search(r":(?:hover|focus)", sel)], [])
        # where no pointer can rest on a mark, the open card names the examples; elsewhere the line takes
        # no room, so a card keeps the size that hero.js places it by
        names = [(context, decls.get("display")) for context, sel, decls in self.rules if sel == ".hc-names" and "display" in decls]
        self.assertEqual(names, [((), "none"), (("@media (hover: none), (pointer: coarse)",), "block")])

    def test_a_mark_names_its_brand_in_a_tooltip_beside_it(self):
        """static/hero.js's tips(), run here in Node with a stand-in figure and clock. A mouse that
        rests on a named mark for TIP ms shows its aria-label in the tooltip; one that passes over it
        sooner shows nothing, so a sweep across the labels shows no name, and a name that follows
        within CHAIN ms of the last shows at once. The name stands GAP px above the mark, centred
        on it and SIDE px inside the window's sides, on every layer (pointing at a mark opens no
        card, so none comes to show above T1 to T3); below it when the open card lies above, or when
        the sticky header is in the way above; and not at all when the open card covers the mark.
        When a card shows beside a name shown, the name moves clear of it; once shown, it keeps its
        side while it fits there, so it stays below the mark when the card above it goes, and the
        next mark's name starts above again. Touch ignores hovering: a tap shows the name at once,
        until a second tap on the mark, a tap elsewhere or LINGER ms; each row's examples take that
        click themselves, not the list, so that a touch screen does not move a tap on a mark to the
        name link above it (touch adjustment prefers the innermost element that takes clicks). A
        press of the mouse, a key, a scroll and focus in the figure hide it."""
        node = shutil.which("node")
        if not node:
            self.skipTest("Node.js is not installed")
        script = (ROOT / "static" / "hero.js").read_text(encoding="utf-8")
        code = re.sub(r"/\*.*?\*/|//[^\n]*", "", script, flags=re.S)
        tips = js_function(code, "tips")
        k = {name: int(re.search(rf"\b{name} = (\d+)", tips).group(1)) for name in ("TIP", "CHAIN", "LINGER", "GAP", "SIDE")}
        # a sweep at 250px/s crosses a 15px mark in 60ms, and a card shows 120ms after the pointer stops
        self.assertTrue(60 < k["TIP"] <= 300 and k["CHAIN"] > k["TIP"] and k["LINGER"] >= 2000, k)
        # the click that a tap on a mark makes is taken by each row's examples, not by the list
        self.assertIn("list.querySelectorAll('.hero-examples').forEach(line => line.addEventListener('click',", tips)
        self.assertNotIn("list.addEventListener('click'", tips)
        harness = r"""
const vm = require('node:vm');
const SRC = __SRC__, TIP = __TIP__, CHAIN = __CHAIN__, LINGER = __LINGER__;
const rect = (left, top, w, h) => ({ left, top, right: left + w, bottom: top + h, width: w, height: h });
// tips() in a window VW x IH under a header ending at HB, its figure from (500, 100), a named mark at
// MARK (and a second at 1030) in a row whose card opens on PLACE, shown at OPEN with its box CARD;
// the tooltip measures 120 x 22
const setup = ({ vw = 1440, ih = 900, hb = 65, narrow = false, place = 'down', open = null, card = null,
                 mark = rect(1000, 300, 20, 14) } = {}) => {
  let now = 0, next = 1, observer = null, cardBox = card;
  const timers = new Map(), on = {};
  const listen = name => (type, fn) => { (on[name + ' ' + type] = on[name + ' ' + type] || []).push(fn); };
  const row = { dataset: { place } };
  if (open) row.dataset.openPlace = open;
  const named = (label, box) => { const el = { getAttribute: a => (a === 'aria-label' ? label : null), getBoundingClientRect: () => box,
    closest: sel => (sel.startsWith('svg.hero-logo') ? el : sel === '.hero-layer' ? row : null), contains: x => x === el }; return el; };
  const m = named('NVIDIA', mark), m2 = named('AMD', rect(1030, 300, 20, 14)), text = { closest: () => null };
  const tip = { hidden: true, textContent: '', style: { left: '', top: '' }, offsetWidth: 120, offsetHeight: 22 };
  const line = { addEventListener: listen('line') };
  const list = { addEventListener: listen('list'), querySelectorAll: sel => (sel === '.hero-examples' ? [line] : []) };
  const fig = { addEventListener: listen('fig'), getBoundingClientRect: () => rect(500, 100, 900, 800),
    querySelector: sel => ({ '.hero-tip': tip, '.hero-layers': list })[sel]
      || (sel === '.hero-layer[data-open-place] > .hero-card' && cardBox ? { getBoundingClientRect: () => cardBox } : null) };
  vm.runInNewContext(SRC + '\n;tips(fig)', {
    fig, narrow: { matches: narrow }, performance: { now: () => now },
    document: { querySelector: sel => (sel === '.site-header' ? { getBoundingClientRect: () => rect(0, 0, vw, hb) } : null),
      documentElement: { clientWidth: vw }, addEventListener: listen('document') },
    window: { innerHeight: ih, addEventListener: listen('window') },
    setTimeout: (fn, ms) => { const id = next++; timers.set(id, { fn, at: now + ms }); return id; },
    clearTimeout: id => { timers.delete(id); },
    MutationObserver: class { constructor(fn) { observer = fn; } observe() {} } });
  const fire = (name, type, e = {}) => (on[name + ' ' + type] || []).forEach(fn => fn(e));
  return {
    m, m2, text, fire,
    tick: ms => { now += ms; for (const [id, t] of [...timers]) if (t.at <= now) { timers.delete(id); t.fn(); } },
    view: () => (tip.hidden ? null : [tip.textContent, tip.style.left, tip.style.top]),
    mouse: (target, type = 'pointerover', related = null) => fire('list', type, { pointerType: 'mouse', target, relatedTarget: related }),
    tap: target => { fire('document', 'pointerdown', { pointerType: 'touch', target }); fire('line', 'click', { target }); },
    card: (at, box) => { row.dataset.openPlace = at; cardBox = box; observer([]); },
  };
};
const out = {};
{ const t = setup(); t.mouse(t.m); t.tick(TIP - 1); out.early = t.view(); t.tick(1); out.rest = t.view();
  t.mouse(t.m, 'pointerout', t.text); out.left = t.view(); t.tick(100); t.mouse(t.m2); out.chain = t.view();
  t.fire('document', 'pointerdown', { pointerType: 'mouse', target: t.m2 }); out.press = t.view(); }
{ const t = setup(); t.mouse(t.m); t.tick(60); t.mouse(t.m, 'pointerout', t.text); t.tick(CHAIN + 100); out.pass = t.view();
  t.mouse(t.m2); out.passNext = t.view(); }
for (const [key, name, type] of [['key', 'document', 'keydown'], ['scroll', 'window', 'scroll'], ['focus', 'fig', 'focusin']]) {
  const t = setup(); t.mouse(t.m); t.tick(TIP); t.fire(name, type); out[key] = t.view(); }
{ const t = setup({ place: 'up' }); t.mouse(t.m); t.tick(TIP); out.up = t.view();
  t.card('down', rect(980, 330, 400, 200)); out.moved = t.view(); }
{ const t = setup({ open: 'up', card: rect(980, 60, 400, 230) }); t.mouse(t.m); t.tick(TIP); out.cardAbove = t.view();
  t.card('', null); out.cardGone = t.view(); t.mouse(t.m2); out.nextAbove = t.view(); }
{ const t = setup({ open: 'fit', card: rect(980, 250, 400, 200) }); t.mouse(t.m); t.tick(TIP); out.covered = t.view(); }
{ const t = setup(); t.mouse(t.m); t.tick(TIP); t.card('fit', rect(980, 250, 400, 200)); out.coveredLater = t.view(); }
{ const t = setup({ mark: rect(1425, 300, 14, 14) }); t.mouse(t.m); t.tick(TIP); out.edge = t.view(); }
{ const t = setup({ mark: rect(1000, 80, 20, 14) }); t.mouse(t.m); t.tick(TIP); out.header = t.view(); }
{ const t = setup({ narrow: true, place: 'up' }); t.mouse(t.m); t.tick(TIP); out.phone = t.view(); }
{ const t = setup(); t.fire('list', 'pointerover', { pointerType: 'touch', target: t.m }); t.tick(TIP); out.touchHover = t.view();
  t.tap(t.m); out.tap = t.view(); t.tick(LINGER - 1); out.linger = t.view(); t.tick(1); out.lingered = t.view();
  t.tap(t.m); t.tap(t.m); out.again = t.view(); t.tap(t.m); t.tap(t.text); out.elsewhere = t.view(); }
console.log(JSON.stringify(out));
"""
        for name, value in (("__SRC__", json.dumps(tips)), ("__TIP__", str(k["TIP"])), ("__CHAIN__", str(k["CHAIN"])),
                            ("__LINGER__", str(k["LINGER"]))):
            harness = harness.replace(name, value)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "harness.js"
            path.write_text(harness, encoding="utf-8")
            run = subprocess.run([node, str(path)], capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 0, run.stderr)
        got = json.loads(run.stdout)
        gap, side = k["GAP"], k["SIDE"]
        # the mark's centre less half the tooltip, and above it, in the figure's box (from 500, 100)
        x, above, below = f"{1010 - 60 - 500}px", f"{300 - gap - 22 - 100}px", f"{314 + gap - 100}px"
        self.assertEqual(got, {
            "early": None, "rest": ["NVIDIA", x, above], "left": None, "chain": ["AMD", f"{1040 - 60 - 500}px", above],
            "press": None, "pass": None, "passNext": None, "key": None, "scroll": None, "focus": None,
            # T1 to T3 as any other layer: above, and still above once a card opens below the label
            "up": ["NVIDIA", x, above], "moved": ["NVIDIA", x, above],
            # below the mark while the card lies above; it stays there when the card goes, and the next
            # mark's name starts above again
            "cardAbove": ["NVIDIA", x, below], "cardGone": ["NVIDIA", x, below], "nextAbove": ["AMD", f"{1040 - 60 - 500}px", above],
            "covered": None, "coveredLater": None,
            # SIDE px inside the window's right edge; below the mark under the sticky header (ending at 65)
            "edge": ["NVIDIA", f"{1440 - side - 120 - 500}px", above], "header": ["NVIDIA", x, f"{94 + gap - 100}px"],
            "phone": ["NVIDIA", x, above],
            "touchHover": None, "tap": ["NVIDIA", x, above], "linger": ["NVIDIA", x, above], "lingered": None,
            "again": None, "elsewhere": None,
        })


class BuildOutputTests(unittest.TestCase):
    """Build a preview into a temporary folder once and inspect the pages.

    The build uses --chat demo, so the Ask assistant's markup is checked
    whatever mode content/site.json sets.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = cls.project(Path(cls.tmp.name))
        cls.out = Path(cls.tmp.name) / "site"
        result = build_site(cls.out, "--chat", "demo", root=cls.root)
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.model = content.load(cls.root)
        cls.manifest = json.loads((cls.out / "manifest.json").read_text(encoding="utf-8"))
        cls.pages = sorted(cls.out.rglob("*.html"))
        cls.parsed = {}
        cls.by_slug = {lang: {a.slug: a for a in cls.model["articles"][lang]} for lang in content.LANGS}
        cls.stack_ids = [layer["id"] for layer in cls.model["topics"]["stack"]]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def project(cls, tmp):
        """The project to build: this repository (IllustratedBuildTests builds a copy)."""
        return ROOT

    def read(self, rel):
        return (self.out / rel).read_text(encoding="utf-8")

    # ----- helpers --------------------------------------------------------------
    def dom(self, rel):
        if rel not in self.parsed:
            self.parsed[rel] = parse_html(self.read(rel))
        return self.parsed[rel]

    def rels(self):
        return [p.relative_to(self.out).as_posix() for p in self.pages]

    @staticmethod
    def lang_of(rel):
        return "zh" if rel.startswith("zh/") else "en"

    def s(self, lang):
        return self.model["strings"][lang]

    def label(self, lang, key):
        """An interface string as the pages show it: content/strings.json, else render's fallback."""
        strings = self.s(lang)
        return strings[key] if key in strings else render.FALLBACK_STRINGS[lang][key]

    @staticmethod
    def t(value, lang):
        if isinstance(value, dict):
            return value.get(lang) or value.get("en", "")
        return value or ""

    def articles(self, lang):
        return self.model["articles"][lang]

    def is_tee(self, a):
        return TEE in a.topics

    def layers_of(self, a):
        """Front-matter layers in stack order (T7 first), or the layers that list the primary topic."""
        if a.layers is not None:
            return [lid for lid in self.stack_ids if lid in a.layers]
        return [layer["id"] for layer in self.model["topics"]["stack"] if a.primary_topic in layer.get("topics", [])]

    def code(self, lid):
        return f"T{len(self.stack_ids) - self.stack_ids.index(lid)}"

    def layer_name(self, lid, lang):
        return self.t(next(layer for layer in self.model["topics"]["stack"] if layer["id"] == lid)["name"], lang)

    def article_path(self, slug, lang):
        """Where a LANG page links an article: its LANG edition, else the English one."""
        return loc(f"/articles/{slug}/", lang if slug in self.by_slug[lang] else "en")

    def linked_article(self, rel, node):
        """The article that the first article link inside NODE points to, or None."""
        self.assertIsNotNone(node, f"{rel}: no list row around the element")
        lang = self.lang_of(rel)
        for a in node.find_all("a"):
            found = ARTICLE_PATH_RE.match(canonical(rel, a.attrs.get("href", "")))
            if found:
                return self.by_slug[lang].get(found.group(1)) or self.by_slug["en"][found.group(1)]
        return None

    def links(self, rel, node):
        return [canonical(rel, a.attrs.get("href", "")) for a in node.find_all("a")]

    def source_links(self, refs, lang):
        """Where a data row's "article:<slug>" and "resource:<id>" sources link."""
        urls = {r["id"]: r["url"] for r in self.model["resources"]["resources"]}
        return [self.article_path(ident, lang) if kind == "article" else urls[ident]
                for kind, _, ident in (ref.partition(":") for ref in refs)]

    def section_of(self, rel):
        """The header item a page marks as current, or None."""
        path = canonical(rel, "")
        bare = path[3:] if path.startswith("/zh/") else path
        found = ARTICLE_PATH_RE.match(bare)
        if found:
            return "learn" if self.by_slug["en"][found.group(1)].kind in ("explainer", "guide") else "latest"
        if bare == HUB:
            return "tee"
        if bare.startswith("/topics/"):
            return "topics"
        return {"/latest/": "latest", "/learn/": "learn", "/resources/": "resources", "/vision/": "vision"}.get(bare)

    def news(self, lang):
        return [a for a in self.articles(lang) if a.kind == "news"]

    def rail(self, lang):
        """The home page's "Latest news": the lead brief (or the newest), then the five newest briefs."""
        news = self.news(lang)
        lead = next((a for a in news if a.lead), news[0])
        return [lead] + [a for a in news if a is not lead][:5]

    def path_steps(self):
        return self.model["tee"]["path"]

    def test_stylesheet_version_matches_the_published_bytes(self):
        css_bytes = (self.out / "assets" / "site.css").read_bytes()
        self.assertEqual(css_bytes, (self.root / "static" / "site.css").read_bytes())
        digest = hashlib.sha256(css_bytes).hexdigest()
        for lang in content.LANGS:
            article = self.articles(lang)[0]
            for rel in (LANG_DIR[lang] + "index.html", LANG_DIR[lang] + f"articles/{article.slug}/index.html"):
                with self.subTest(page=rel):
                    href = urlsplit(site_stylesheet_href(self.dom(rel)))
                    self.assertEqual(href.path, posixpath.relpath("assets/site.css", posixpath.dirname(rel) or "."))
                    self.assertEqual(parse_qs(href.query), {"v": [digest[:16]]})

    # ----- retired interface ------------------------------------------------------
    def test_denylisted_phrases_are_absent_in_both_languages(self):
        # .txt and .webmanifest: llms.txt, the llms-full.txt files, robots.txt and the web app manifests
        files = [p for p in self.out.rglob("*")
                 if p.suffix in (".html", ".xml", ".json", ".js", ".css", ".md", ".txt", ".webmanifest")]
        self.assertTrue(any(p.match("zh/index.html") for p in files))
        hits = []
        for path in files:
            text = path.read_text(encoding="utf-8")
            if path.suffix == ".json":  # parsed before unescaping: a feed's HTML may hold &quot;
                text += json.dumps(json.loads(text), ensure_ascii=False)
            text = html.unescape(text).casefold()
            hits += [f"{path.relative_to(self.out)}: {phrase}" for phrase in DENYLIST if phrase.casefold() in text]
        self.assertEqual(hits, [])

    def test_wording_rules(self):
        """No page claims that attestation proves things or that a service is verified.
        Titles of outside documents and quoted words keep their own wording."""
        def outside(node):
            return (node.tag == "a" and "ext" in node.classes) or (node.tag == "section" and "sources" in node.classes)

        def hits(text):
            text = QUOTED_RE.sub(" ", text)
            return {m.group(0) for pattern in WORDING for m in re.finditer(pattern, text, re.I)}

        found = []
        for rel in self.rels():
            doc = self.dom(rel)
            article = ARTICLE_PATH_RE.match(canonical(rel, ""))
            body = doc.find("div", cls="article-body") if article else None
            words = [doc.text(skip=lambda n: n is body or outside(n))]
            words += [n.attrs[k] for n in doc.iter() for k in ("alt", "title", "aria-label", "placeholder") if k in n.attrs]
            words += [n.attrs.get("content", "") for n in doc.find_all("meta")]
            found += [f"{rel}: {hit}" for hit in sorted(hits("\n".join(words)))]
            if body is not None:
                known = LEGACY_BODY_WORDING.get((self.lang_of(rel), article.group(1)), set())
                found += [f"{rel} (article body): {hit}" for hit in sorted(hits(body.text(skip=outside)) - known)]
        self.assertEqual(found, [])

    # ----- the home page ----------------------------------------------------------
    def test_home_pages_open_with_positioning_hero_and_news(self):
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "index.html", self.s(lang)
            doc = self.dom(rel)
            page = self.read(rel)
            # the tagline is the page's only h1, then the positioning and two links
            h1 = doc.find_all("h1")
            self.assertEqual([h.text() for h in h1], [norm(s["tagline"])], rel)
            intro = doc.find("div", cls="home-intro")
            self.assertTrue(h1[0].within(intro), rel)
            self.assertEqual(intro.find("p", cls="home-kicker").text(), norm(s["home_kicker"]), rel)
            self.assertEqual(intro.find("p", cls="home-positioning").text(), norm(s["home_lead"]), rel)
            self.assertEqual(self.links(rel, intro.find("p", cls="home-links")),
                             [loc("/vision/", lang) + "#problem", loc("/topics/", lang)], rel)
            # The maintainer and contributors link are in the footer, leaving the intro concise.
            head, lede = intro.kids("div")
            self.assertEqual((head.classes, lede.classes), ({"home-head"}, {"home-lede"}), rel)
            self.assertEqual([kind_of(n, ("home-kicker",)) for n in head.kids()], ["home-kicker", "h1"], rel)
            self.assertIsNone(intro.find(cls="home-credits"), rel)
            self.assertEqual([kind_of(n, ("home-positioning", "home-links")) for n in lede.kids()],
                             ["home-positioning", "home-links"], rel)

            # one hero, beside the intro in the band: the inline scene, titled in the page language
            heroes = doc.find_all(cls="hero-visual")
            self.assertEqual(len(heroes), 1, rel)
            hero = heroes[0]
            self.assertTrue(hero.within(doc.find("section", cls="home-hero")) and not hero.within(intro), rel)
            svg = hero.find("svg", cls="hero-scene")
            self.assertEqual(svg.attrs.get("role"), "img", rel)
            self.assertTrue(svg.within(hero.find("div", cls="hero-art")), rel)  # inline, not an <img>
            title, desc = svg.kids("title"), svg.kids("desc")
            self.assertEqual([n.text() for n in title + desc], [norm(s["hero_scene_title"]), norm(s["hero_scene_desc"])], rel)
            self.assertEqual(svg.attrs.get("aria-labelledby", "").split(), [title[0].attrs.get("id")], rel)
            self.assertEqual(svg.attrs.get("aria-describedby", "").split(), [desc[0].attrs.get("id")], rel)
            self.assertEqual(svg.find_all(("text", "image", "script", "foreignobject")), [], rel)
            self.assertEqual([n for n in svg.iter() if "font-family" in n.attrs], [], rel)
            self.assertNotIn("{{", page, rel)
            # no caption: the scene's description says what it shows, and the note about the logos is
            # for screen readers only; the two links to the Stack page follow the stage
            self.assertEqual(hero.find_all("figcaption"), [], rel)
            self.assertEqual(hero.find("p", id="hero-layers-note").classes, {"vh"}, rel)
            links = hero.find("p", cls="hero-links")
            self.assertIs(links.parent, hero, rel)
            self.assertEqual(self.links(rel, links), [loc("/topics/", lang), loc("/topics/", lang) + "#tiers"], rel)
            self.assertEqual([a.text() for a in links.find_all("a")], [norm(s["stack_more"] + " →"), norm(s["stack_compare"] + " →")], rel)
            self.assertEqual(hero_parts(doc)[0], [svg], rel)

            # "Latest news" follows the band: the lead brief (or the newest) with its dek, then the
            # five newest briefs, all with tags (the stylesheet hides the fifth below 960px)
            rail = doc.find("section", cls="home-news")
            self.assertFalse(rail.within(doc.find("section", cls="home-hero")), rel)
            self.assertEqual(rail.find("h2").text(), norm(s["on_record"]), rel)
            self.assertEqual(self.links(rel, rail.find("div", cls="block-head")), [loc("/latest/", lang) + "#news"], rel)
            lead = rail.find("article", cls="news-lead")
            self.assertEqual(lead.find("p", cls="news-lead-dek").text(), norm(self.rail(lang)[0].dek), rel)
            rows = [lead] + rail.find_all("li", cls="ledger-row")
            expected = self.rail(lang)
            self.assertEqual(len(rows), 6, rel)
            self.assertEqual([self.linked_article(rel, row).slug for row in rows], [a.slug for a in expected], rel)
            for row, a in zip(rows, expected):
                meta = row.find("p", cls="ledger-dates")
                self.assertEqual(meta.find("time").attrs["datetime"], (a.event_date or a.published).isoformat(), rel)
                self.assertEqual(meta.find("span", cls="tags") is not None, bool(self.layers_of(a)) or self.is_tee(a),
                                 (rel, a.slug))

            # no stack table: it is on the Stack page, where the hero's cards and links lead
            self.assertIsNone(doc.find("section", cls="stack-compact"), rel)
            self.assertIsNone(doc.find("ol", cls="layer-table"), rel)

            # no digest, citation anchor, retired picture or digest drawing
            shown = page.split('<script type="application/json" id="chat-config">', 1)[0]
            for gone in ("sha256", "art-figure", "lead-story"):
                self.assertNotIn(gone, shown, (rel, gone))
            self.assertNotRegex(shown, HEX_DIGEST_RE, rel)
            self.assertNotIn("#source-", page, rel)  # citations stay on the article page
            self.assertEqual([n for n in doc.iter() if n.classes & RETIRED_CLASSES], [], rel)

    def test_stack_tables_draw_the_evidence_chain(self):
        stack = self.model["topics"]["stack"]
        statuses = [(layer.get("bind") or {}).get("status", "none") for layer in stack]
        self.assertEqual(statuses[-1], "none")  # T1 has no layer below
        self.assertTrue(all(st in ("deployed", "emerging", "missing") for st in statuses[:-1]), statuses)
        # the hero draws the same chain: segment k is layer k's binding to layer k - 1, bottom up, and
        # its legend merges neighbouring segments of one status into a run from layer lo up to hi
        segments = [(len(stack) - i, st) for i, st in enumerate(statuses[:-1])][::-1]
        runs = []
        for k, st in segments:
            if runs and runs[-1][0] == st:
                runs[-1][2] = k
            else:
                runs.append([st, k - 1, k])
        for lang in content.LANGS:
            s = self.s(lang)
            rel = LANG_DIR[lang] + "topics/index.html"
            section = self.dom(rel).find("section", id="layers")
            rows = section.find_all("li", cls="layer-row")
            self.assertEqual([r.attrs.get("data-bind") for r in rows], statuses, rel)
            self.assertEqual([r.attrs.get("data-bind-above") for r in rows], ["none"] + statuses[:-1], rel)
            self.assertEqual(section.find("p", cls="chain-legend").text(), norm(s["chain_legend"]), rel)
            for row, layer in zip(rows, stack):
                bind = layer.get("bind")
                line = row.find("p", cls="layer-bind")
                if bind:
                    self.assertEqual(line.find("span", cls="bind-status").text(), norm(s["bind_" + bind["status"]]), rel)
                    self.assertIn(norm(self.t(bind["text"], lang)), line.text(), rel)
                else:
                    self.assertIsNone(line, (rel, layer["id"]))
            # the home figure: the chain by binding status, drawn so at rest (owner decision 1), and the
            # legend's runs, each with its status and the layers it spans
            home = LANG_DIR[lang] + "index.html"
            figure = self.dom(home).find("figure", cls="hero-visual")
            self.assertEqual(figure.attrs.get("data-hv-chain"), " ".join(f"{k}:{st}" for k, st in segments), home)
            self.assertEqual(figure.attrs.get("data-hv-rest"), "status", home)
            items = figure.find("div", cls="hero-chain").find("ul", cls="hero-chain-runs").kids("li")
            self.assertEqual([(li.attrs.get("data-bind"), li.find("span", cls="hero-chain-status").text(), norm(li.children[-1]))
                              for li in items],
                             [(st, norm(s["bind_" + st]), norm(s["hero_chain_run"].format(lo=f"T{lo}", hi=f"T{hi}")))
                              for st, lo, hi in runs], home)

    def test_every_page_carries_the_stack_for_the_stack_card(self):
        for path in self.pages:
            rel = path.relative_to(self.out).as_posix()
            found = re.findall(r'<script type="application/json" id="stack-data">(.*?)</script>', path.read_text(encoding="utf-8"), re.S)
            self.assertEqual(len(found), 1, rel)
            data = json.loads(found[0])
            self.assertEqual([layer["code"] for layer in data["layers"]], [f"T{n}" for n in range(7, 0, -1)], rel)
            self.assertEqual(data["note"], self.s(self.lang_of(rel))["pop_note"], rel)

    def test_home_pages_follow_with_the_stack_tees_and_checks(self):
        tee_path = [step["article"] for step in self.path_steps() if "article" in step]
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "index.html", self.s(lang)
            doc = self.dom(rel)
            home = doc.find("div", cls="home")
            # The hero, core reading routes, news, TEEs and practical checks.
            self.assertEqual([kind_of(sec, HOME_BLOCKS) for sec in home.kids("section")], list(HOME_BLOCKS), rel)

            # Trusted execution environments: the newest TEE briefs not in the rail, and the five steps
            block = home.find("section", cls="tee-block")
            self.assertEqual(self.links(rel, block.find("div", cls="block-head")), [loc(HUB, lang)], rel)
            rail = self.rail(lang)
            tee_news = [a for a in self.news(lang) if self.is_tee(a) and a not in rail][:4]
            latest = block.find("ol", cls="tee-latest").kids("li")
            self.assertEqual([self.linked_article(rel, li).slug for li in latest], [a.slug for a in tee_news], rel)
            self.assertTrue(all(li.find("span", cls="tag-tee") for li in latest), rel)
            steps = block.find("ol", cls="path-mini").kids("li")
            self.assertEqual([self.linked_article(rel, li).slug for li in steps], tee_path, rel)
            self.assertEqual([n.classes for n in steps if "is-planned" in n.classes], [], rel)
            # "Learn TEEs in five steps": the count of the steps listed, as a word
            self.assertEqual(block.find_all("h3", cls="mini-title")[-1].text(),
                             norm(s["tee_block_path"].format(n=discover.count_word(len(steps), lang))), rel)
            # each step by its kind, reading time and title; what it lets the reader do is on Learn
            # and the TEE hub, not here
            for li in steps:
                self.assertIsNone(li.find("p", cls="path-outcome"), rel)
                self.assertTrue(li.find("p", cls="path-kind") and li.find("h4", cls="path-title"), rel)

            # Checks you can run: the newest guides that are not on the TEE path, each by its title,
            # step count and reading time; the byline is on the article, and the dek is on Learn
            # and on the guide, not here
            guides = [a for a in self.articles(lang) if a.kind == "guide" and a.slug not in tee_path][:3]
            cards = home.find("section", cls="checks-block").find_all("article", cls="check-card")
            self.assertEqual([self.linked_article(rel, card).slug for card in cards], [a.slug for a in guides], rel)
            for card, a in zip(cards, guides):
                self.assertIsNone(card.find("p", cls="card-dek"), (rel, a.slug))
                steps_n = render.guide_steps(self.by_slug["en"][a.slug].body)
                meta = ([count_label(s, "guide_steps", steps_n)] if steps_n else []) + [s["min_read"].format(n=a.minutes)]
                self.assertEqual(card.find("p", cls="card-meta").text(skip=is_vh), norm(" · ".join(meta)), (rel, a.slug))

            # metadata: the meta and og descriptions, WebSite and Organization JSON-LD
            meta = {n.attrs.get("name") or n.attrs.get("property"): n.attrs.get("content") for n in doc.find_all("meta")}
            self.assertEqual((meta["description"], meta["og:description"]), (s["site_description"], s["site_description"]), rel)
            ld = json.loads(doc.find("script", type="application/ld+json").raw())
            by_type = {item["@type"]: item for item in ld}
            self.assertEqual(by_type["WebSite"]["description"], s["site_description"], rel)
            org = by_type["Organization"]
            base = self.model["site"]["base_url"].rstrip("/")
            self.assertEqual((org["description"], org["publishingPrinciples"]), (s["footer_about"], base + loc("/about/", lang)), rel)

    def test_home_drops_the_stack_table_and_links_to_the_stack_page(self):
        """The stack table left the home page: the hero's layer cards show each layer there, and
        the hero's nine links to the Stack page (the seven layer names and the two under the
        caption) land on its table and its tiers. The cards' stories links open a layer's view of
        Latest. Every page still carries #stack-data for the stack cards on story tags."""
        for lang in content.LANGS:
            rel = LANG_DIR[lang] + "index.html"
            doc = self.dom(rel)
            for gone in ("stack-block", "stack-compact", "layer-table", "chain-legend"):
                self.assertEqual(doc.find_all(cls=gone), [], (rel, gone))
            # each hero link resolves to its page, and to an id there when it names one
            targets = {loc("/topics/", lang): LANG_DIR[lang] + "topics/index.html",
                       loc("/latest/", lang): LANG_DIR[lang] + "latest/index.html"}
            links = [canonical(rel, a.attrs["href"]) for a in doc.find("figure", cls="hero-visual").find_all("a")]
            self.assertEqual(sorted({href.partition("#")[0] for href in links}), sorted(targets), rel)
            for href in links:
                page, _, frag = href.partition("#")
                if frag:
                    self.assertIsNotNone(self.dom(targets[page]).find(id=frag), (rel, href))
            stack = [href for href in links if href.partition("#")[0] == loc("/topics/", lang)]
            self.assertEqual(stack, [loc("/topics/", lang) + "#layer-" + lid for lid in self.stack_ids]
                             + [loc("/topics/", lang), loc("/topics/", lang) + "#tiers"], rel)
        for rel in self.rels():
            self.assertEqual(self.read(rel).count('<script type="application/json" id="stack-data">'), 1, rel)

    def check_thumb(self, rel, img):
        """A list's copy of a lead image: <img alt=""> loaded lazily at the image's own size, in an
        a.story-thumb that screen readers skip and Tab passes over, linking to the story whose
        image it shows; the row's title links to the same story, so the row keeps one tab stop.
        A photo's copy names its 800 px file (variants.list) in src and offers its 400 and 800 px
        copies and the full-size file in srcset, smallest first, with the width the copy takes in
        this list (render.THUMB_SIZES)."""
        link = img.parent
        self.assertEqual((link.tag, link.attrs.get("aria-hidden"), link.attrs.get("tabindex")), ("a", "true", "-1"),
                         (rel, img))
        self.assertIn("story-thumb", link.classes, rel)
        self.assertEqual([img.attrs.get(k) for k in ("alt", "loading", "decoding")], ["", "lazy", "async"], (rel, img))
        found = ARTICLE_PATH_RE.match(canonical(rel, link.attrs.get("href", "")))
        self.assertIsNotNone(found, (rel, link))
        slug = found.group(1)
        image = self.by_slug["en"][slug].lead_image
        self.assertIsNotNone(image, (rel, slug))
        shown = image.variants.get("list", image)
        self.assertEqual(canonical(rel, img.attrs["src"]), shown.src, rel)
        self.assertEqual((img.attrs.get("width"), img.attrs.get("height")), (str(shown.width), str(shown.height)), rel)
        if shown is image:
            self.assertEqual((img.attrs.get("srcset"), img.attrs.get("sizes")), (None, None), rel)
        else:
            candidates = [c.split() for c in img.attrs["srcset"].split(",")]
            files = [image.variants[name] for name in reversed(content.PHOTO_SRCSET)] + [image]
            self.assertEqual([(canonical(rel, url), width) for url, width in candidates],
                             [(f.src, f"{f.width}w") for f in files], rel)
            cls = next(c for c in link.classes if c in render.THUMB_SIZES)
            # a topic page's river is narrower than Latest's, beside the record column
            topic = cls == "river-thumb" and "/topics/" in "/" + rel
            self.assertEqual(img.attrs.get("sizes"), render.TOPIC_RIVER_SIZES if topic else render.THUMB_SIZES[cls], rel)
        href = canonical(rel, link.attrs["href"])
        others = [a for a in link.parent.find_all("a") if a is not link and canonical(rel, a.attrs.get("href", "")) == href]
        self.assertEqual(len(others), 1, (rel, slug))
        self.assertNotIn("tabindex", others[0].attrs, rel)
        self.assertFalse(any(n.attrs.get("aria-hidden") == "true" for n in [others[0], *others[0].ancestors()]), rel)

    def assert_lead_copies_only(self, rel, doc):
        """A list page shows no pictures but the decorative copies of lead images (check_thumb)."""
        for pic in images(doc):
            self.assertIn("story-thumb-img", pic.classes if pic.tag == "img" else set(), (rel, pic))
            self.check_thumb(rel, pic)

    def test_pictures_are_the_hero_and_the_lead_images(self):
        """The pages show the home hero, each illustrated article's lead figure and, in lists,
        decorative copies of the lead images; nothing else. An article's page shows its figure
        exactly when the article has an illustration.json."""
        problems = []
        for rel in self.rels():
            doc = self.dom(rel)
            pictures = images(doc)
            lead = [p for p in pictures if is_lead_picture(p)]
            rest = [p for p in pictures if p not in lead]
            if rel in ("index.html", "zh/index.html"):
                scene, marks = hero_parts(doc)
                labels = doc.find("ol", cls="hero-layers")
                if [p.classes for p in scene] != [{"hero-scene", "hv-scene"}] or not all(m.within(labels) for m in marks):
                    problems.append(f"{rel}: {rest}")
            elif rest:
                problems.append(f"{rel}: {rest}")
            for img in lead:
                if "story-thumb-img" in img.classes:
                    self.check_thumb(rel, img)
            figures = [p for p in lead if "lead-figure-img" in p.classes]
            found = ARTICLE_PATH_RE.match(canonical(rel, "index.html"))
            image = self.by_slug["en"][found.group(1)].lead_image if found else None
            if len(figures) != (1 if image else 0):
                problems.append(f"{rel}: {len(figures)} lead figures")
            retired = [n for n in doc.iter() if n.classes & RETIRED_CLASSES or any(c.startswith("plate-") for c in n.classes)]
            if retired:
                problems.append(f"{rel}: {retired[:3]}")
            if "/illustrations/" in self.read(rel):
                problems.append(f"{rel}: links an illustration")
        self.assertEqual(problems, [])
        self.assertFalse((self.out / "assets" / "illustrations").exists())
        self.assertFalse((self.out / "data" / "illustrations.json").exists())
        self.assertNotIn("/data/illustrations.json", {e["source"] for e in self.manifest["entries"]})

    def test_llms_txt_describes_lead_image_specs_once_there_are_some(self):
        illustrated = any(a.lead_image for a in self.model["articles"]["en"])
        self.assertEqual("/articles/<slug>/illustration.json" in self.read("llms.txt"), illustrated)

    def test_lead_images_are_published_and_hashed(self):
        """Each lead image's spec is published beside its article's sources and the image under
        /assets/media/, with a photo's three copies, all byte for byte as loaded, and the manifest
        lists each of them, with no page."""
        images_ = {a.slug: a.lead_image for a in self.model["articles"]["en"] if a.lead_image}
        entries = {e["source"]: e for e in self.manifest["entries"] if e["kind"] in ("illustration", "image")}
        expected = {}
        for slug, image in images_.items():
            expected[image.spec_path] = ("illustration", image.spec_raw)
            for picture in image.published():
                expected[picture.src] = ("image", picture.raw)
        self.assertEqual(sorted(entries), sorted(expected))
        for source, (kind, raw) in expected.items():
            entry = entries[source]
            self.assertEqual((entry["kind"], entry["page"], entry["lang"], entry["bytes"], entry["sha256"]),
                             (kind, None, None, len(raw), hashlib.sha256(raw).hexdigest()), source)
            self.assertEqual((self.out / source.lstrip("/")).read_bytes(), raw, source)
        # /assets/media/ holds exactly the pictures the manifest lists: no draft's or stray file
        media = self.out / "assets" / "media"
        published = sorted("/" + p.relative_to(self.out).as_posix() for p in media.rglob("*") if p.is_file()) \
            if media.is_dir() else []
        self.assertEqual(published, sorted(source for source, (kind, _) in expected.items() if kind == "image"))
        kinds = set(self.model["site"].get("lead_image_kinds", []))
        self.assertLessEqual(kinds, set(content.KINDS))
        self.assertEqual([a.slug for a in self.model["articles"]["en"] if a.kind in kinds and not a.lead_image], [])

    def test_no_raster_hero_is_published_or_linked(self):
        self.assertFalse((ROOT / "static" / "hero").exists(), "static/hero/ held the retired raster hero")
        self.assertFalse((self.out / "assets" / "hero").exists())
        found = [f"{rel}: {name}" for rel in self.rels() for name in RASTER_HERO + ("assets/hero/",)
                 if name in self.read(rel)]
        self.assertEqual(found, [])

    def test_hero_script_only_on_home_and_pause_button_hidden_by_default(self):
        """hero.js and its guard are on the two home pages only: the guard, inline right after the
        deferred script, gives you your colour back at the window's load when hero.js never set the
        figure up, which ships with data-hv-wait."""
        for rel in self.rels():
            every = self.dom(rel).find_all("script")
            scripts = [n for n in every if n.attrs.get("src", "").endswith("hero.js")]
            guards = [n for n in every if "data-hv-wait" in n.raw()]
            if rel in ("index.html", "zh/index.html"):
                self.assertEqual([canonical(rel, n.attrs["src"]) for n in scripts], ["/assets/hero.js"], rel)
                self.assertIn("defer", scripts[0].attrs, rel)
                self.assertEqual(guards, [every[every.index(scripts[0]) + 1]], rel)
                self.assertEqual(guards[0].raw(), render.HERO_GUARD, rel)
                self.assertNotIn("src", guards[0].attrs, rel)
                self.assertIn("data-hv-wait", self.dom(rel).find("figure", cls="hero-visual").attrs, rel)
            else:
                self.assertEqual((scripts, guards), ([], []), rel)
        self.assertTrue((self.out / "assets" / "hero.js").is_file())
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "index.html", self.s(lang)
            hero = self.dom(rel).find("figure", cls="hero-visual")
            self.assertIn("data-verification-visual", hero.attrs, rel)
            buttons = hero.find_all("button")
            button = buttons[0]
            # first in the figure, so it comes before the layer links in the tab order
            self.assertIs(hero.kids()[0], button, rel)
            self.assertIn("hidden", button.attrs, rel)  # hero.js shows it once motion is allowed
            self.assertIn("data-motion-toggle", button.attrs, rel)
            self.assertEqual(button.attrs.get("type"), "button", rel)
            self.assertEqual((button.attrs.get("aria-label"), button.attrs.get("data-label-pause"), button.attrs.get("data-label-play")),
                             (s["motion_pause"], s["motion_pause"], s["motion_play"]), rel)
            self.assertEqual(button.find("span", data_motion_label=True).text(), norm(s["motion_pause"]), rel)
            self.assertEqual(hero.find("span", cls="verification-static-label").text(), norm(s["motion_static"]), rel)
            # then "Check all layers", in the pause control's place until every layer is checked, also
            # hidden until hero.js runs
            check_all = buttons[1]
            self.assertEqual((check_all.classes, check_all.attrs.get("type"), check_all.text()),
                             ({"hero-all"}, "button", norm(s["hero_check_all"])), rel)
            self.assertIn("hidden", check_all.attrs, rel)
            # the other buttons are the rows' chevrons, one per layer and T7 first, hidden until hero.js
            # runs; each names its layer and controls the layer's card
            stack = self.model["topics"]["stack"]
            chevrons = buttons[2:]
            self.assertEqual([b.classes for b in chevrons], [{"hero-more"}] * len(stack), rel)
            for b, layer in zip(chevrons, stack):
                where = (rel, layer["id"])
                self.assertIn("hidden", b.attrs, where)
                self.assertEqual((b.attrs.get("type"), b.attrs.get("aria-expanded"), b.attrs.get("aria-controls")),
                                 ("button", "false", f"hero-card-{layer['id']}"), where)
                self.assertIsNotNone(hero.find("div", cls="hero-card", id=f"hero-card-{layer['id']}"), where)
                self.assertEqual(b.find("span", cls="vh").text(), norm(s["hero_more"].format(name=layer["hero"]["short"][lang])), where)
                self.assertEqual([svg.attrs.get("aria-hidden") for svg in b.find_all("svg")], ["true"], where)

    def test_home_hero_gives_its_script_what_it_addresses(self):
        """The markup static/hero.js works on (spec 5): one figure per home page, in the band and
        under the sticky header, with its pause control and label, and "Check all layers"; the stage
        with seven rows, T7 first, each with one name link and one check mark in its head, one chevron
        that controls the row's card, a preferred side, and the card as the row's last element; a
        leader per row; a plate per row in the scene, T1 first; and the hint and the reader's
        progress, hidden until the script runs."""
        n = content.STACK_SIZE
        for lang in content.LANGS:
            rel = LANG_DIR[lang] + "index.html"
            doc = self.dom(rel)
            figs = doc.find_all(data_verification_visual=True)
            self.assertEqual(len(figs), 1, rel)
            fig = figs[0]
            self.assertTrue(fig.matches("figure", "hero-visual"), rel)
            self.assertTrue(fig.within(doc.find("section", cls="home-hero")), rel)
            self.assertIsNotNone(doc.find("header", cls="site-header"), rel)
            toggle = fig.find("button", data_motion_toggle=True)
            self.assertIsNotNone(toggle, rel)
            self.assertIsNotNone(toggle.find(data_motion_label=True), rel)
            stage = fig.kids("div", cls="hero-stage")[0]
            rows = stage.kids("ol", cls="hero-layers")[0].kids("li", cls="hero-layer")
            self.assertEqual([r.attrs.get("data-n") for r in rows], [str(k) for k in range(n, 0, -1)], rel)
            for row in rows:
                where = (rel, row.attrs.get("id"))
                head = row.kids("span", cls="hero-layer-head")[0]
                links = row.find_all("a", cls="hero-layer-link")
                self.assertEqual(len(links), 1, where)
                self.assertTrue(links[0].within(head), where)
                chevrons = row.find_all("button", cls="hero-more")
                self.assertEqual(len(chevrons), 1, where)
                self.assertTrue(chevrons[0].within(head), where)
                ticks = row.find_all("span", cls="hero-tick")
                self.assertEqual(len(ticks), 1, where)
                self.assertTrue(ticks[0].within(head), where)
                card = row.kids()[-1]
                self.assertTrue(card.matches("div", "hero-card"), where)
                self.assertEqual(chevrons[0].attrs.get("aria-controls"), card.attrs.get("id"), where)
                self.assertIn(row.attrs.get("data-place"), ("up", "down"), where)
            self.assertEqual(len(stage.find_all("g", cls="hero-leader")), n, rel)
            hits = stage.find("svg", cls="hero-scene").find_all("path", cls="hv-hit")
            self.assertEqual([h.attrs.get("data-hv-n") for h in hits], [str(k) for k in range(1, n + 1)], rel)
            hints = fig.find_all("p", cls="hero-hint")
            self.assertEqual(len(hints), 1, rel)
            self.assertIn("hidden", hints[0].attrs, rel)
            progress = fig.find_all("p", cls="hero-progress")
            self.assertEqual(len(progress), 1, rel)
            self.assertIn("hidden", progress[0].attrs, rel)
            self.assertEqual(progress[0].attrs.get("role"), "status", rel)
            self.assertIn("{n}", progress[0].attrs.get("data-progress", ""), rel)
            self.assertTrue(progress[0].attrs.get("data-done"), rel)
            self.assertEqual(len(fig.find_all("button", cls="hero-all")), 1, rel)

    def test_home_hero_labels_name_the_seven_layers_in_both_languages(self):
        stack = self.model["topics"]["stack"]
        direct = sum(1 for layer in stack if layer["tee"]["reach"] == "direct")
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "index.html", self.s(lang)
            hero = self.dom(rel).find("figure", cls="hero-visual")
            ol = hero.find("ol", cls="hero-layers")
            self.assertEqual(ol.attrs.get("aria-label"), s["hero_layers_label"], rel)
            rows = ol.kids("li", cls="hero-layer")
            # each name carries its code before it: "T7 Policy" on the page, "T7, Policy" (T7，政策) to a
            # screen reader
            self.assertEqual([r.find("a").text() for r in rows],
                             [norm(f"T{len(stack) - i}{s['hero_code_sep']}{layer['hero']['short'][lang]}") for i, layer in enumerate(stack)], rel)
            self.assertEqual([r.find("span", cls="hero-layer-code").text() for r in rows], [f"T{k}" for k in range(len(stack), 0, -1)], rel)
            names = ol.find_all("a", cls="hero-layer-link")
            self.assertEqual([canonical(rel, a.attrs["href"]) for a in names],
                             [loc("/topics/", lang) + "#layer-" + layer["id"] for layer in stack], rel)
            stack_page = self.dom(LANG_DIR[lang] + "topics/index.html")
            for layer in stack:
                self.assertIsNotNone(stack_page.find(id=f"layer-{layer['id']}"), (rel, layer["id"]))
            # the TEE label's sentence for screen readers, where a TEE gives direct evidence
            self.assertEqual([n.text() for r in rows for n in r.find("span", cls="hero-layer-head").kids("span", cls="vh")],
                             [norm(s["hero_tee_vh"])] * direct, rel)
            # the logos and names are examples, not endorsements: said to screen readers before the list
            note = hero.find("p", id="hero-layers-note")
            self.assertEqual((note.classes, note.text()), ({"vh"}, norm(s["hero_layers_note"])), rel)
            marks = ol.find_all("svg", cls="hero-logo")
            self.assertTrue(marks, rel)
            for mark in marks:
                named = mark.attrs.get("role") == "img" and mark.attrs.get("aria-label")
                self.assertTrue(named or (mark.attrs.get("aria-hidden") == "true" and mark.parent.text()), (rel, mark))
            # hero.js shows a named mark's aria-label in the figure's one tooltip, which it fills
            self.assertEqual(len(hero.find_all("span", cls="hero-tip")), 1, rel)
        zh = self.dom("zh/index.html").find("ol", cls="hero-layers").text()
        for name in ("政策", "评测", "智能体", "输出", "模型与数据", "运行时", "硬件"):
            self.assertIn(name, zh)

    # ----- the frame ---------------------------------------------------------------
    def test_header_six_sections_and_footer(self):
        for rel in self.rels():
            lang, doc = self.lang_of(rel), self.dom(rel)
            s = self.s(lang)
            nav = doc.find("nav", cls="site-nav")
            items = nav.find_all("a")
            self.assertEqual([a.text() for a in items], [norm(s[key]) for _, key, _ in NAV], rel)
            self.assertEqual(self.links(rel, nav), [loc(path, lang) for _, _, path in NAV], rel)
            current = [section for (section, _, _), a in zip(NAV, items) if a.attrs.get("aria-current") == "page"]
            expected = self.section_of(rel)
            self.assertEqual(current, [expected] if expected else [], rel)
            # the light/dark toggle, after search: hidden until site.js names it for the theme the page is in
            toggle = doc.find("button", cls="theme-toggle")
            self.assertEqual((toggle.attrs.get("type"), "hidden" in toggle.attrs, toggle.attrs.get("aria-label")),
                             ("button", True, s["theme_to_dark"]), rel)
            self.assertEqual((toggle.attrs.get("data-label-dark"), toggle.attrs.get("data-label-light")),
                             (s["theme_to_dark"], s["theme_to_light"]), rel)

            footer = doc.find("footer", cls="site-footer")
            # The maintainer and contributors link belong in the dark footer only.
            credits = footer.find("p", cls="footer-credits")
            self.assertEqual(credits.find("span", cls="sept-brand").text(), "SEPT", rel)
            self.assertEqual(credits.find("a", cls="sept-wordmark").text(), "SEPT Lab", rel)
            self.assertEqual(self.links(rel, credits), ["https://septlab.com/", loc("/contributors/", lang)], rel)
            self.assertEqual(credits.text(), norm(s["home_maintainer"].format(name="SEPT Lab") + " · " + s["home_contributors"]), rel)
            # The last line: copyright and editor, linked to the editor on Vision.
            editor = footer.find("div", cls="footer-bottom").find("a", cls="footer-editor")
            self.assertEqual(editor.text(), norm(s["home_editor"]), rel)
            self.assertEqual(self.links(rel, footer.find("div", cls="footer-bottom")), [loc("/vision/", lang) + "#editor"], rel)
            self.assertTrue(footer.find("div", cls="footer-bottom").text().endswith(" · " + norm(s["home_editor"])), rel)
            self.assertEqual(footer.find("div", cls="footer-brand").find("p").text(), norm(s["footer_about"]), rel)
            read = footer.find("nav", aria_labelledby="f-read").find_all("li")
            targets = [loc(path, lang) for _, _, path in NAV] + [loc("/glossary/", lang), loc("/about/", lang)]
            labels = [norm(s[key]) for _, key, _ in NAV] + [norm(s["nav_glossary"]), norm(s["nav_about"])]
            self.assertEqual([self.links(rel, li)[0] for li in read[:-1]], targets, rel)
            self.assertEqual([li.find("a").text() for li in read[:-1]], labels, rel)
            # then the related publication, an outside link
            self.assertIn("footer-labelled", read[-1].classes, rel)
            self.assertTrue(read[-1].find("a").attrs["href"].startswith("https://"), rel)
            footer_text = footer.text()
            self.assertNotRegex(footer_text, HEX_DIGEST_RE, rel)
            self.assertNotIn("sha256", footer_text.lower(), rel)

    # ----- tags and the stack ---------------------------------------------------------
    def test_layer_tags_follow_layers_or_primary_topic(self):
        seen = 0
        for rel in self.rels():
            lang, doc = self.lang_of(rel), self.dom(rel)
            for tags in doc.find_all("span", cls="tags"):
                a = self.linked_article(rel, tags.closest("li") or tags.closest("article"))
                expected = self.layers_of(a)
                codes = tags.find("a", cls="tag-layers")
                if expected:
                    self.assertIsNotNone(codes, (rel, a.slug))
                    shown = [n for n in codes.kids("span") if n.attrs.get("aria-hidden") == "true"]
                    self.assertEqual([n.text() for n in shown], [" ".join(self.code(lid) for lid in expected)], (rel, a.slug))
                    self.assertEqual(codes.attrs.get("data-layers", "").split(), expected, (rel, a.slug))
                    self.assertEqual(self.links(rel, tags), [loc("/topics/", lang) + f"#layer-{expected[0]}"], (rel, a.slug))
                    hidden = codes.find("span", cls="vh").text()
                    for lid in expected:
                        self.assertIn(norm(self.layer_name(lid, lang)), hidden, (rel, a.slug))
                else:
                    self.assertIsNone(codes, (rel, a.slug))  # layers: [] shows no codes
                # the layer link is the only tab stop; the TEE label takes none
                self.assertEqual([n.tag for n in tags.iter() if n.tag in ("a", "button") or "tabindex" in n.attrs],
                                 ["a"] if expected else [], (rel, a.slug))
                seen += 1
        self.assertGreater(seen, 0)

        for lang in content.LANGS:
            rel = LANG_DIR[lang] + "latest/index.html"
            rows = {self.linked_article(rel, li).slug: li for li in self.dom(rel).find_all("li", cls="river-item")}
            self.assertEqual(sorted(rows), sorted(a.slug for a in self.articles(lang)), rel)
            for a in self.articles(lang):
                # the layer filter reads data-layers; Filing names the layers in full
                self.assertEqual(rows[a.slug].attrs.get("data-layers", "").split(), self.layers_of(a), (rel, a.slug))
                page = f"{LANG_DIR[lang]}articles/{a.slug}/index.html"
                filing = self.dom(page).find("div", cls="dd-layers")
                if not self.layers_of(a):
                    self.assertIsNone(filing, page)
                    continue
                self.assertEqual(self.links(page, filing), [loc("/topics/", lang) + f"#layer-{lid}" for lid in self.layers_of(a)], page)
                self.assertEqual([n.text() for n in filing.find_all("a")],
                                 [f"{self.code(lid)} {norm(self.layer_name(lid, lang))}" for lid in self.layers_of(a)], page)

    def test_tee_label_iff_confidential_computing_topic(self):
        for rel in self.rels():
            s = self.s(self.lang_of(rel))
            for tags in self.dom(rel).find_all("span", cls="tags"):
                a = self.linked_article(rel, tags.closest("li") or tags.closest("article"))
                label = tags.find("span", cls="tag-tee")
                self.assertEqual(label is not None, self.is_tee(a), (rel, a.slug))
                if label is not None:
                    self.assertEqual((label.text(), label.attrs.get("title"), label.attrs.get("aria-hidden")),
                                     (norm(s["tag_tee"]), s["tag_tee_name"], "true"), (rel, a.slug))
                    self.assertIn(norm(s["tag_tee_name"]), " ".join(v.text() for v in tags.find_all("span", cls="vh")), (rel, a.slug))
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "latest/index.html", self.s(lang)
            doc = self.dom(rel)
            tees = [a for a in self.articles(lang) if self.is_tee(a)]
            self.assertTrue(tees, rel)
            for li in doc.find_all("li", cls="river-item"):
                a = self.linked_article(rel, li)
                self.assertEqual(li.attrs.get("data-tee"), "1" if self.is_tee(a) else "0", (rel, a.slug))
                self.assertEqual(li.find("span", cls="tag-tee") is not None, self.is_tee(a), (rel, a.slug))
            # the filter bar: the TEE toggle with its count, and the layer select (#l7 ... #l1)
            bar = doc.find("div", cls="filter-bar")
            self.assertEqual(bar.attrs.get("aria-label"), s["filter_label"], rel)
            toggle = bar.find("button", id="tee")
            self.assertEqual((toggle.attrs.get("data-toggle"), toggle.attrs.get("aria-pressed")), ("tee", "false"), rel)
            self.assertIn("filter-btn", toggle.classes, rel)
            self.assertEqual(toggle.find("span", cls="count").text(), str(len(tees)), rel)
            options = bar.find("select", id="layer-filter").find_all("option")
            self.assertEqual([o.attrs.get("value") for o in options], [""] + self.stack_ids, rel)
            codes = [self.code(lid).lower() for lid in self.stack_ids]
            self.assertEqual([o.attrs.get("data-code") for o in options[1:]], codes, rel)
            self.assertEqual([o.attrs.get("id") for o in options[1:]], codes, rel)
            self.assertEqual(doc.find("p", cls="tags-note").text(), norm(s["tags_note"]), rel)

    def test_stack_reach_direct_only_at_l1_l2(self):
        stack = self.model["topics"]["stack"]
        reach = [layer["tee"]["reach"] for layer in stack]
        self.assertEqual(len(stack), 7)
        self.assertEqual(reach, ["via"] * 5 + ["direct"] * 2)
        for lang in content.LANGS:
            s = self.s(lang)
            # the table is on the Stack page only; the home page's hero cards link to it
            self.assertIsNone(self.dom(LANG_DIR[lang] + "index.html").find("section", cls="stack-block"), lang)
            rel = LANG_DIR[lang] + "topics/index.html"
            block = self.dom(rel).find("section", cls="stack-block")
            self.assertEqual(block.attrs.get("id"), "layers", rel)
            rows = block.find("ol", cls="layer-table").kids("li")
            self.assertEqual([row.attrs.get("id") for row in rows], [f"layer-{lid}" for lid in self.stack_ids], rel)
            self.assertEqual([row.find("span", cls="layer-code").text() for row in rows], [f"T{n}" for n in range(7, 0, -1)], rel)
            self.assertEqual([row.attrs.get("data-reach") for row in rows], reach, rel)
            columns = ["layer-head", "layer-body", "layer-topics", "layer-cover"]
            for row, layer in zip(rows, stack):
                where = (rel, layer["id"])
                self.assertEqual([kind_of(kid, columns) for kid in row.kids()], columns, where)
                self.assertEqual(row.find("h3", cls="layer-name").text(), norm(self.t(layer["name"], lang)), where)
                # who outside the provider can check the claim, right under it
                body = row.find("div", cls="layer-body")
                self.assertEqual([kind_of(kid, ("layer-claim", "layer-checkers", "layer-tee")) for kid in body.kids()][:3],
                                 ["layer-claim", "layer-checkers", "layer-tee"], where)
                checkers = body.find("p", cls="layer-checkers")
                self.assertEqual(checkers.find("span", cls="layer-checkers-label").text(), norm(s["checkers_label"]), where)
                self.assertEqual(checkers.text(skip=lambda node: "layer-checkers-label" in node.classes),
                                 norm(self.t(layer["checkers"], lang)), where)
                # the short TEE line, in view
                line = row.find("p", cls="layer-tee")
                self.assertEqual(line.find("span", cls="layer-reach").text(), norm(s["reach_" + layer["tee"]["reach"]]), where)
                short, text = (self.t(layer["tee"].get(key), lang) for key in ("short", "text"))
                self.assertTrue(line.text().endswith(norm(short)), where)
                self.assertIsNone(line.closest("details"), where)
                # the full TEE line, the other evidence and the newest brief at the layer fold into
                # one <details> in the body
                at = [a for a in self.articles(lang) if layer["id"] in self.layers_of(a)]
                brief = next((a for a in at if a.kind == "news"), None)
                parts = [row.find("p", cls=cls) for cls in ("layer-tee-text", "layer-others", "layer-newest")]
                wanted = [bool(text) and text != short, bool(layer.get("others")), brief is not None]
                self.assertEqual([p is not None for p in parts], wanted, where)
                folds = row.find_all("details", cls="layer-more")
                self.assertEqual(len(folds), int(any(p is not None for p in parts)), where)
                if folds:
                    self.assertTrue(folds[0].within(body), where)
                    self.assertEqual(folds[0].find("summary").text(), norm(self.label(lang, "layer_more")), where)
                    self.assertTrue(all(p.within(folds[0]) for p in parts if p is not None), where)
                full_line, others, newest = parts
                if full_line is not None:
                    self.assertTrue(full_line.text().endswith(norm(text)), where)
                if others is not None:
                    self.assertEqual(self.links(rel, others), [loc("/topics/", lang) + "#tier-" + o["tier"] for o in layer["others"]], where)
                if newest is not None:  # the brief, linked, with the date of the development
                    self.assertEqual(self.linked_article(rel, newest).slug, brief.slug, where)
                    self.assertEqual(newest.find("time").attrs.get("datetime"), (brief.event_date or brief.published).isoformat(), where)
                # the cover counts the stories at this layer and opens that view of Latest
                cover = row.find("p", cls="layer-count")
                self.assertTrue(cover.text().startswith(count_label(s, "stack_cover", len(at))), where)
                if at:
                    self.assertEqual(self.links(rel, cover), [loc("/latest/", lang) + "#" + self.code(layer["id"]).lower()], where)
            self.assertEqual(block.find("p", cls="tags-note").text(), norm(s["tags_note"]), rel)

    # ----- the TEE hub, the Stack page and Vision --------------------------------------------
    def test_tee_hub_renders_at_topic_url(self):
        tee = self.model["tee"]
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "topics/confidential-computing/index.html", self.s(lang)
            doc = self.dom(rel)
            main = doc.find("main")
            self.assertTrue({"page-topic", "page-tee"} <= doc.find("div", cls="site").classes, rel)
            self.assertEqual([h.text() for h in doc.find_all("h1")], [norm(s["hub_title"])], rel)
            head = main.find("header", cls="tee-head")
            self.assertEqual(head.find("p", cls="kicker").text(), norm(s["hub_kicker"]), rel)
            self.assertEqual(head.find("p", cls="page-dek").text(), norm(s["hub_dek"]), rel)
            self.assertIn(loc("/vision/", lang) + "#why-tees", self.links(rel, head), rel)
            self.assertEqual(self.links(rel, main.find("nav", cls="breadcrumb")), [loc("/", lang), loc("/topics/", lang)], rel)
            nav = doc.find("nav", cls="site-nav")
            self.assertEqual([a.text() for a in nav.find_all("a", aria_current="page")], [norm(s["nav_tee"])], rel)
            sections = main.find("div", cls="wrap").kids("section")
            self.assertEqual([sec.attrs.get("id") for sec in sections], list(HUB_SECTIONS), rel)
            # full width: no chat aside, no sidebar and no table of contents
            sidebars = [n for n in main.iter() if n.classes & {"chat-aside", "doc-aside", "topic-aside", "toc"}]
            self.assertEqual(sidebars, [], rel)
            by_id = {sec.attrs["id"]: sec for sec in sections}

            # what a checked report shows and what it leaves to trust
            est = by_id["establishes"]
            cols = est.find("div", cls="hub-cols").kids("div")
            self.assertEqual([c.find("h3").text() for c in cols], [norm(s["hub_shows"]), norm(s["hub_still"])], rel)
            self.assertEqual([[li.text() for li in c.find_all("li")] for c in cols],
                             [[norm(self.t(x, lang)) for x in tee["establishes"][k]] for k in ("shows", "still")], rel)
            self.assertEqual(est.find("p", cls="boundary").text(), norm(self.t(tee["establishes"]["boundary"], lang)), rel)
            self.assertIn(loc("/topics/", lang) + "#tiers", self.links(rel, est.find("p", cls="hub-links")), rel)

            # the path: published steps link their articles; planned ones are labelled and unlinked
            steps = by_id["path"].find("ol", cls="path-mini").kids("li")
            self.assertEqual(len(steps), len(tee["path"]), rel)
            for li, step in zip(steps, tee["path"]):
                if "article" in step:
                    self.assertEqual(self.linked_article(rel, li).slug, step["article"], rel)
                else:
                    self.assertIn("is-planned", li.classes, rel)
                    self.assertEqual(li.find("span", cls="path-planned").text(), norm(s["path_planned"]), rel)
                    self.assertIn(norm(self.t(step["planned"], lang)), li.text(), rel)
                    self.assertEqual(li.find_all("a"), [], rel)

            # platforms: CPU cards, then GPU cards; a blank cell reads "Not yet covered here"
            groups = by_id["platforms"].find_all("div", cls="platform-group")
            self.assertEqual([g.find("h3").text() for g in groups], [norm(s["area_cpu"]), norm(s["area_gpu"])], rel)
            for group, key in zip(groups, ("cpu", "gpu")):
                cards = group.find_all("article", cls="platform")
                rows = [p for p in tee["platforms"] if p["group"] == key]
                self.assertEqual([c.attrs.get("id") for c in cards], [f"plat-{p['id']}" for p in rows], rel)
                for card, p in zip(cards, rows):
                    blank = sum(1 for k in ("isolates", "signs", "reference_values", "out_of_scope") if not self.t(p.get(k), lang))
                    self.assertEqual(len(card.find_all("span", cls="plat-pending")), blank, (rel, p["id"]))
                    self.assertEqual(self.links(rel, card.find("p", cls="platform-sources")), self.source_links(p["sources"], lang), (rel, p["id"]))

            # AI services that publish attestation evidence: dated rows that list their sources
            services = by_id["services"]
            rows = services.find("table", cls="tracker").find("tbody").kids("tr")
            self.assertEqual([r.attrs.get("id") for r in rows], [f"svc-{svc['id']}" for svc in tee["services"]], rel)
            for row, svc in zip(rows, tee["services"]):
                cells = row.kids("td")
                self.assertEqual([c.text() for c in cells], [norm(self.t(svc[k], lang)) for k in ("record", "checker", "inspection")], rel)
                self.assertTrue(all(c.attrs.get("data-label") for c in cells), rel)  # headings for the stacked phone layout
                self.assertEqual(self.links(rel, row.find("th")), self.source_links(svc["sources"], lang), (rel, svc["id"]))
            self.assertEqual(services.find("p", cls="tracker-note").text(), norm(s["svc_note"]), rel)
            reviewed = {svc["as_of"] for svc in tee["services"]}
            self.assertEqual(len(reviewed), 1, "the services table shows one review date")
            stamp = render.fmt_date(dt.date.fromisoformat(reviewed.pop()), lang)
            self.assertEqual(services.find("p", cls="as-of").text(), norm(s["as_of"].format(date=stamp)), rel)

            # attacks and limits, newest first and undated last, labelled by the access they need
            limits = by_id["limits"]
            self.assertIn(norm(s["lim_note"]), limits.find("p", cls="hub-intro").text(), rel)
            items = limits.find("ol", cls="limits").kids("li")
            self.assertEqual([li.attrs.get("id") for li in items], [f"limit-{lim['id']}" for lim in tee["limits"]], rel)
            kinds = [li.attrs.get("data-kind") for li in items]
            self.assertEqual(kinds, ["physical" if lim["physical"] else "remote" for lim in tee["limits"]], rel)
            self.assertIn("remote", kinds, rel)
            bound, undated = None, False
            for li, lim in zip(items, tee["limits"]):
                where = (rel, lim["id"])
                self.assertEqual(li.find("span", cls="limit-kind").text(),
                                 norm(s["lim_physical" if lim["physical"] else "lim_remote"]), where)
                stamp = li.find("p", cls="limit-date").find("time")
                if stamp is None:
                    undated = True
                else:
                    self.assertFalse(undated, f"{where}: a dated row follows an undated one")
                    first, last = date_span(stamp.attrs["datetime"])
                    self.assertTrue(bound is None or first <= bound, f"{where}: rows must run newest first")
                    bound = last if bound is None else min(bound, last)
                self.assertEqual(self.links(rel, li.find("p", cls="limit-sources")), self.source_links(lim["sources"], lang), where)
                self.assertEqual(li.find("p", cls="limit-editor") is not None, bool(lim.get("editor")), where)
            for resp in tee.get("responses", []):
                heading = limits.find(id=f"resp-{resp['id']}")
                self.assertIsNotNone(heading, (rel, resp["id"]))
                self.assertEqual(self.links(rel, following_until(heading, "h4")[-1]), self.source_links(resp["sources"], lang), rel)

            # the newest TEE stories that the path above does not list (or, if it lists them all,
            # the newest TEE stories) as short tagged rows, then a link to every TEE story on Latest
            coverage = by_id["coverage"]
            on_path = {step["article"] for step in tee["path"] if "article" in step}
            tees = [a for a in self.articles(lang) if self.is_tee(a)]
            recent = ([a for a in tees if a.slug not in on_path] or tees)[:HUB_COVERAGE]
            self.assertTrue(recent, rel)
            rows = coverage.find("ol", cls="tee-latest").kids("li")
            self.assertEqual([self.linked_article(rel, li).slug for li in rows], [a.slug for a in recent], rel)
            self.assertTrue(all(li.find("span", cls="tag-tee") for li in rows), rel)
            self.assertIsNone(coverage.find("ol", cls="river"), rel)
            more = coverage.find("div", cls="block-head")
            self.assertEqual(more.find("h2").text(), norm(s["hub_coverage_title"]), rel)
            self.assertEqual(self.links(rel, more), [loc("/latest/", lang) + "#tee"], rel)
            self.assertTrue(more.find("a").text().startswith(norm(s["hub_coverage_all"])), rel)

            # documents by TEE area, then the terms
            resources = self.model["resources"]["resources"]
            areas = [area for area in content.TEE_AREAS if any(r.get("tee_area") == area for r in resources)]
            grid = by_id["reading"].find("div", cls="reading-grid").kids("div")
            self.assertEqual([g.find("h3").text() for g in grid], [norm(s["area_" + a]) for a in areas] + [norm(s["hub_terms"])], rel)
            self.assertEqual(self.links(rel, grid[-1]), [loc("/glossary/", lang) + "#" + gid for gid in tee["terms"]], rel)
            self.assert_lead_copies_only(rel, doc)

    def test_articles_name_the_tracker_rows_that_cite_them(self):
        tee = self.model["tee"]
        rows = [(f"svc-{r['id']}", r) for r in tee["services"]] + [(f"limit-{r['id']}", r) for r in tee["limits"]]
        rows += [(f"resp-{r['id']}", r) for r in tee.get("responses", [])]
        for lang in content.LANGS:
            hub = LANG_DIR[lang] + "topics/confidential-computing/index.html"
            anchors = {n.attrs["id"] for n in self.dom(hub).iter() if "id" in n.attrs}
            for a in self.articles(lang):
                rel = f"{LANG_DIR[lang]}articles/{a.slug}/index.html"
                cited = [anchor for anchor, row in rows if f"article:{a.slug}" in row.get("sources", [])]
                tracked = self.dom(rel).find("div", cls="dd-tracked")
                if not cited:
                    self.assertIsNone(tracked, rel)
                    continue
                self.assertEqual(self.links(rel, tracked), [loc(HUB, lang) + "#" + anchor for anchor in cited], rel)
                self.assertTrue(set(cited) <= anchors, rel)

    def test_tiers_section_order_baseline_and_not_a_ranking(self):
        tiers = self.model["tiers"]
        ids = [tier["id"] for tier in tiers["tiers"]]
        self.assertEqual(ids, ["signatures", "audits", "tee", "reexecution", "proofs"])
        parts = ("block-head", "tiers-note", "tier-baseline", "tier", "tiers-he-note", "read-more")
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "topics/index.html", self.s(lang)
            doc = self.dom(rel)
            self.assertEqual([h.text() for h in doc.find_all("h1")], [norm(s["topics_page_title"])], rel)
            section = doc.find("section", id="tiers")
            # the order note, the unnumbered baseline, the five tiers, the HE/MPC note
            self.assertEqual([kind_of(kid, parts) for kid in section.kids()],
                             ["block-head", "tiers-note", "tier-baseline"] + ["tier"] * len(ids) + ["tiers-he-note", "read-more"], rel)
            note = section.find("p", cls="tiers-note").text()
            self.assertEqual(note, norm(self.t(tiers["order_note"], lang)), rel)
            self.assertIn("not a ranking" if lang == "en" else "并不是优劣排名", note, rel)
            base = section.find("div", id="tier-baseline")
            self.assertEqual(base.find("p", cls="baseline-label").text(), norm(s["baseline_label"]), rel)
            self.assertEqual(base.find("h3").text(), norm(self.t(tiers["baseline"]["trust_name"], lang)), rel)
            self.assertIsNone(base.find(cls="tier-n"), rel)
            rows = section.kids("article")
            self.assertEqual([r.attrs.get("id") for r in rows], [f"tier-{i}" for i in ids], rel)
            numbers = [r.find("span", cls="tier-n").text() for r in rows]
            self.assertEqual(numbers, [norm(s["tier_n"].format(n=n)) for n in range(1, len(ids) + 1)], rel)
            if lang == "zh":
                self.assertTrue(all(re.fullmatch(r"第 \d 档", n) for n in numbers), numbers)
            for row, tier in zip(rows, tiers["tiers"]):
                where = (rel, tier["id"])
                self.assertIn(norm(self.t(tier["trust_name"], lang)), row.find("h3", cls="tier-title").text(), where)
                # every field is on the row; what a passing check establishes and what it does
                # not stay in view, and the rest may fold into <details>
                shown = row.text(skip=lambda n: n.tag == "details")
                for key in ("establishes", "not_established"):
                    self.assertIn(norm(self.t(tier[key], lang)), shown, where)
                fields = ("mechanism", "trust", "hidden", "cost", "approaches", "focus" if tier.get("focus") else "vs_tee")
                for key in fields + (("combined",) if tier.get("combined") else ()):
                    self.assertIn(norm(self.t(tier[key], lang)), row.text(), (where, key))
                main = tier.get("focus") is not None
                self.assertEqual(row.find("p", cls="tier-main-label") is not None, main, where)
                self.assertEqual(loc(HUB, lang) in self.links(rel, row), main, where)
                self.assertEqual(self.links(rel, row.find("div", cls="tier-read")), [self.article_path(slug, lang) for slug in tier["read"]], where)
            # the Hollow-LLM paper is cited in view, so its disclosure is too
            proofs = section.find("article", id="tier-proofs").text(skip=lambda n: n.tag == "details")
            self.assertIn("Hollow-LLM", proofs, rel)
            self.assertIn("co-authored" if lang == "en" else "合著者", proofs, rel)
            self.assertEqual(section.find("p", cls="tiers-he-note").text(), norm(self.t(tiers["he_note"], lang)), rel)
            self.assertEqual(self.links(rel, section.find("p", cls="read-more")), [loc("/vision/", lang) + "#compare"], rel)
            # combinations in practice name the tiers they combine and link their article
            combos = doc.find("section", id="combinations").find_all("li", cls="combo")
            self.assertEqual(len(combos), len(tiers["combinations"]), rel)
            for li, combo in zip(combos, tiers["combinations"]):
                links = self.links(rel, li)
                self.assertEqual(links[0], self.article_path(combo["article"], lang), rel)
                self.assertEqual(links[1:], [loc("/topics/", lang) + "#tier-" + tid for tid in combo["tiers"]], rel)

    def test_vision_page_both_languages(self):
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "vision/index.html", self.s(lang)
            doc = self.dom(rel)
            page = self.model["pages"][lang]["vision"]
            self.assertEqual([h.text() for h in doc.find_all("h1")], [norm(page.title)], rel)
            nav = doc.find("nav", cls="site-nav")
            self.assertEqual([a.text() for a in nav.find_all("a", aria_current="page")], [norm(s["nav_vision"])], rel)
            body = doc.find("article", cls="article-body")
            headings = [h for h in body.kids() if h.tag in ("h2", "h3")]
            self.assertEqual([h.attrs.get("id") for h in headings], list(VISION_SECTIONS), rel)
            self.assertEqual([h.attrs.get("id") for h in body.kids("h2")],
                             ["problem", "verifiable", "why-tees", "goals", "editor"], rel)
            # the positioning include opens the page
            first = body.kids()[0]
            self.assertEqual((first.tag, first.classes, first.text()), ("p", {"lead"}, norm(s["home_positioning"])), rel)
            self.assertNotIn("data-include", self.read(rel), rel)
            # Vision links to the full comparison on Stack instead of repeating its table.
            compare = following_until(body.find("h3", id="compare"), "h2")
            self.assertIn(loc("/topics/", lang) + "#tiers", [href for node in compare for href in self.links(rel, node)], rel)
            self.assertEqual(body.find_all("table"), [], rel)
            self.assertEqual(images(doc), [], rel)

            # the goals are listed on Vision only
            goals = [li.text() for n in following_until(body.find("h2", id="goals"), "h2") for li in n.find_all("li")]
            self.assertTrue(goals, rel)
            for other in self.rels():
                if other != rel and self.lang_of(other) == lang:
                    text = self.dom(other).find("main").text()
                    self.assertEqual([g for g in goals if g[:60] in text], [], other)

    def test_about_points_to_vision_and_keeps_its_anchors(self):
        for lang in content.LANGS:
            rel = LANG_DIR[lang] + "about/index.html"
            body = self.dom(rel).find("article", cls="article-body")
            ids = {n.attrs["id"] for n in body.iter() if "id" in n.attrs}
            self.assertEqual([anchor for anchor in ABOUT_ANCHORS if anchor not in ids], [], rel)
            self.assertIn(loc("/vision/", lang), self.links(rel, body.find("p")), rel)

    def test_topic_pages_compare_with_a_tee(self):
        for topic in [t for t in self.model["topics"]["topics"] if t["id"] != TEE]:
            for lang in content.LANGS:
                rel, s = f"{LANG_DIR[lang]}topics/{topic['id']}/index.html", self.s(lang)
                doc = self.dom(rel)
                callout = doc.find("aside", cls="callout-tee")
                self.assertEqual(callout.find("p", cls="callout-label").text(), norm(s["topic_vs_tee"]), rel)
                self.assertEqual(callout.find("div", cls="callout-body").text(), norm(self.t(topic["tee_relation"], lang)), rel)
                aside = doc.find("aside", cls="topic-aside")
                self.assertEqual(self.links(rel, aside.find("ul", cls="tier-list")),
                                 [loc("/topics/", lang) + "#tier-" + t for t in topic["tiers"]], rel)
                layers = [layer["id"] for layer in self.model["topics"]["stack"] if topic["id"] in layer.get("topics", [])]
                items = aside.find("ul", cls="layer-list").kids("li") if layers else []
                self.assertEqual([li.find("span", cls="layer-code").text() for li in items], [self.code(lid) for lid in layers], rel)
                self.assertEqual([self.links(rel, li) for li in items], [[loc("/topics/", lang) + "#layer-" + lid] for lid in layers], rel)
                river = doc.find("div", cls="topic-main").find("ol", cls="river").kids("li", cls="river-item")
                self.assertEqual([self.linked_article(rel, li).slug for li in river],
                                 [a.slug for a in self.articles(lang) if topic["id"] in a.topics], rel)
                self.assert_lead_copies_only(rel, doc)

    # ----- Learn, Resources and search ----------------------------------------------------------
    def test_learn_page_runs_the_tee_path_then_checks_and_terms(self):
        tee = self.model["tee"]
        on_path = [step["article"] for step in tee["path"] if "article" in step]
        glossary = {g["id"] for g in self.model["glossary"]["terms"]}
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "learn/index.html", self.s(lang)
            doc = self.dom(rel)
            sections = doc.find("main").find("div", cls="wrap").kids("section")
            self.assertEqual([sec.attrs.get("id") for sec in sections], ["start-here", "tee-path", "checks", "terms", "all"], rel)
            by_id = {sec.attrs["id"]: sec for sec in sections}
            steps = by_id["tee-path"].find("ol", cls="path").kids("li")
            published = [li for li in steps if "is-planned" not in li.classes]
            self.assertEqual([li.attrs.get("data-slug") for li in published], on_path, rel)
            self.assertEqual([self.linked_article(rel, li).slug for li in published], on_path, rel)
            # "Read these five articles": the count of published steps, as a word
            self.assertEqual(by_id["tee-path"].find("p", cls="block-dek").text(),
                             norm(s["learn_path_dek"].format(n=discover.count_word(len(published), lang))), rel)
            for li in published:
                self.assertTrue(li.find("p", cls="path-outcome").text().startswith(norm(s["path_after"])), rel)
            planned = [li for li in steps if "is-planned" in li.classes]
            self.assertEqual(len(planned), sum(1 for step in tee["path"] if "planned" in step), rel)
            self.assertTrue(all(li.find("span", cls="path-planned") and not li.find_all("a") for li in planned), rel)
            # worksheet cards for the guides not on the path
            guides = [a for a in self.articles(lang) if a.kind == "guide" and a.slug not in on_path]
            cards = by_id["checks"].find_all("li", cls="worksheet-card")
            self.assertEqual([self.linked_article(rel, card).slug for card in cards], [a.slug for a in guides], rel)
            for card, a in zip(cards, guides):
                needs = card.find("p", cls="ws-needs")
                self.assertEqual(needs.text() if needs else "", norm(s["guide_needs"] + s["label_colon"] + a.needs) if a.needs else "",
                                 (rel, a.slug))
                steps_n = render.guide_steps(self.by_slug["en"][a.slug].body)
                shown = card.find("p", cls="ws-steps")
                self.assertEqual(shown.text() if shown else "", count_label(s, "guide_steps", steps_n) if steps_n else "", (rel, a.slug))
            terms = [gid for gid in tee["learn_terms"] if gid in glossary]
            self.assertEqual([self.links(rel, term)[0] for term in by_id["terms"].find("dl", cls="term-cards").find_all("dt")],
                             [loc("/glossary/", lang) + "#" + gid for gid in terms], rel)
            everything = [a.slug for a in self.articles(lang) if a.kind in ("explainer", "guide")]
            self.assertEqual([self.linked_article(rel, li).slug for li in by_id["all"].find_all("li")], everything, rel)
            self.assertEqual(images(doc), [], rel)

    def test_resources_open_with_reading_paths_and_tee_entries(self):
        data = self.model["resources"]
        items = data["resources"]
        urls = {r["id"]: r["url"] for r in items}
        tier_n = {t["id"]: t["n"] for t in self.model["tiers"]["tiers"]}
        topics = self.model["topics"]["topics"]
        others = sorted((t for t in topics if t["id"] != TEE), key=lambda t: tier_n[t["tiers"][0]])
        groups = [TEE] + [t["id"] for t in others if any((r.get("topics") or [""])[0] == t["id"] and not r.get("tee_area") for r in items)]
        areas = [area for area in content.TEE_AREAS if any(r.get("tee_area") == area for r in items)]
        for lang in content.LANGS:
            rel, s = LANG_DIR[lang] + "resources/index.html", self.s(lang)
            doc = self.dom(rel)
            # reading paths, each entry with its "why" line
            cards = doc.find("section", id="paths").find_all("article", cls="rpath")
            self.assertEqual([c.find("h3").text() for c in cards], [norm(self.t(p["title"], lang)) for p in data["paths"]], rel)
            for card, path in zip(cards, data["paths"]):
                self.assertEqual(self.links(rel, card), [urls[e["id"]] for e in path["entries"]], rel)
                self.assertEqual([n.text() for n in card.find_all("span", cls="rpath-why")], [norm(self.t(e["why"], lang)) for e in path["entries"]], rel)
            # the catalog: TEE entries first, by TEE area, then the other topics in tier order
            catalog = doc.find("div", cls="resource-catalog")
            sections = catalog.kids("section", cls="catalog-group")
            self.assertEqual([sec.attrs.get("data-group") for sec in sections], groups, rel)
            self.assertTrue(all(sec.find("p", cls="catalog-trust") for sec in sections), rel)
            tee_group = sections[0]
            self.assertEqual([h.attrs.get("id") for h in tee_group.find_all("h3", cls="catalog-sub")], [f"tee-{a}" for a in areas], rel)
            self.assertEqual(sorted(li.attrs["id"] for li in tee_group.find_all("li", cls="resource")),
                             sorted(f"res-{r['id']}" for r in items if r.get("tee_area")), rel)
            self.assertEqual(sorted(li.attrs["id"] for li in catalog.find_all("li", cls="resource")),
                             sorted(f"res-{r['id']}" for r in items), rel)  # every entry once
            area = doc.find("select", id="res-area")
            self.assertEqual([o.attrs.get("value") for o in area.find_all("option")], [""] + list(content.TEE_AREAS), rel)
            self.assertEqual(doc.find("label", **{"for": "res-area"}).text(), norm(s["res_area"]), rel)
            self.assertEqual(images(doc), [], rel)

    def test_search_index_lists_vision_about_and_the_tiers(self):
        for lang in content.LANGS:
            index = json.loads((self.out / LANG_DIR[lang] / "search-index.json").read_text(encoding="utf-8"))
            pages = [e["path"] for e in index if e["type"] == "page"]
            self.assertIn(loc("/vision/", lang), pages)
            self.assertIn(loc("/about/", lang), pages)
            self.assertEqual([p for p in pages if "#tier-" in p],
                             [loc("/topics/", lang) + "#tier-" + t["id"] for t in self.model["tiers"]["tiers"]], lang)
            for path in pages:
                where, _, anchor = path.partition("#")
                rel = where.lstrip("/") + "index.html"
                self.assertTrue((self.out / rel).is_file(), path)
                if anchor:
                    self.assertIsNotNone(self.dom(rel).find(id=anchor), path)
            search = self.dom(LANG_DIR[lang] + "search/index.html").find("form", cls="search-form")
            self.assertEqual(json.loads(search.attrs["data-labels"]).get("page"), self.s(lang)["search_group_page"], lang)

    # ----- digests -------------------------------------------------------------------
    def test_digests_only_in_folded_record(self):
        """Digests stay in the folded Verification record at the end of each article (and
        in the assistant's config); the correction link may carry one in its address."""
        problems = []
        for rel in self.rels():
            text = self.read(rel)
            text = re.sub(r'<details class="verify">.*?</details>', "", text, flags=re.S)
            text = CHAT_CONFIG_RE.sub("", text)
            text = re.sub(r'href="[^"]*"', "", text)
            if "sha256" in text.lower() or HEX_DIGEST_RE.search(text):
                problems.append(rel)
        self.assertEqual(problems, [])
        for lang in content.LANGS:
            for a in self.articles(lang):
                rel = f"{LANG_DIR[lang]}articles/{a.slug}/index.html"
                body = self.dom(rel).find("div", cls="article-body")
                record = body.find("details", cls="verify")
                self.assertTrue(record.within(body.find("section", cls="check-strip")), rel)
                self.assertEqual(record.find("code", cls="hash").text(), a.sha256, rel)

    def test_articles_end_with_check_or_correct(self):
        page = self.read(next(p for p in sorted((self.out / "articles").glob("*/index.html"))).relative_to(self.out).as_posix())
        body = page.split('class="article-body prose"', 1)[1].split('<aside class="doc-aside">', 1)[0]
        self.assertIn('class="check-strip"', body)
        self.assertIn('<details class="verify">', body)  # the digest is folded away at the end
        self.assertNotIn('class="follow', page)

    def test_bylines_open_the_article_meta_and_mark_listed_stories_except_on_home(self):
        """An article's meta line opens with its byline: an automated byline's name, a dot and
        the "Automated" tag ("verifiable.pro Wire · Automated"), or "By" and the author's name,
        then who submitted the story. The home page omits bylines. Other list rows (Latest,
        the topic pages, the TEE hub, Learn and the related cards) carry one byline mark, the
        story's own. No byline or mark uses the word "agent"."""
        agents = self.model["site"]["agents"]
        rows = ("river-item", "ledger-row", "news-lead", "brief-row", "path-step", "check-card", "worksheet-card",
                "card-related")
        seen = set()
        for rel in self.rels():
            lang, doc = self.lang_of(rel), self.dom(rel)
            s = self.s(lang)
            found = ARTICLE_PATH_RE.match(canonical(rel, ""))
            if found:
                a = self.by_slug[lang][found.group(1)]
                byline = doc.find("div", cls="article-meta").kids("p")[0]
                self.assertEqual(byline.classes, {"byline"}, rel)
                shown = self.t(agents[a.agent]["name"], lang) if a.agent else norm(s["byline_by"].format(name=a.author))
                self.assertEqual(byline.find("span", cls="byline-by").text(), shown, rel)
                tag = byline.find("a", cls="byline-tag")
                if a.agent:
                    self.assertTrue(byline.text().startswith(f'{shown} · {s["byline_agent"]}'), rel)
                    self.assertEqual(canonical(rel, tag.attrs["href"]), loc("/about/", lang) + "#ai", rel)
                    self.assertEqual(tag.attrs["title"], self.t(agents[a.agent]["description"], lang), rel)
                else:
                    self.assertIsNone(tag, rel)
                submitted = byline.find("span", cls="byline-submitted")
                self.assertEqual(submitted.text() if submitted else "",
                                 norm(s["byline_submitted"].format(name=a.submitted_by)) if a.submitted_by else "", rel)
                self.assertNotRegex(byline.text().casefold() + (tag.attrs["title"].casefold() if tag else ""),
                                    r"agent|智能体", rel)
            for row in (n for n in doc.iter() if n.classes & set(rows) and "is-planned" not in n.classes):
                a = self.linked_article(rel, row)
                marks = row.find_all("span", cls="byline-mark")
                seen |= row.classes & set(rows)
                if rel == LANG_DIR[lang] + "index.html":
                    self.assertEqual(marks, [], (rel, a.slug))
                    continue
                self.assertEqual([m.text() for m in marks], [norm(byline_mark_text(self.model, a, lang))], (rel, a.slug))
                if a.agent:
                    self.assertEqual(marks[0].attrs["title"], self.t(agents[a.agent]["description"], lang), (rel, a.slug))
                    heard = norm(s["byline_agent_vh"].format(name=self.t(agents[a.agent]["name"], lang)))
                    self.assertIn(heard, [n.text() for n in row.find_all("span", cls="vh")], (rel, a.slug))
                    self.assertNotRegex((marks[0].attrs["title"] + heard).casefold(), r"agent|智能体", (rel, a.slug))
        self.assertEqual(seen, set(rows))

    # ----- the Ask assistant ------------------------------------------------
    def config(self, page_text):
        found = CHAT_CONFIG_RE.findall(page_text)
        self.assertEqual(len(found), 1)
        self.assertNotIn("</", found[0])
        return json.loads(found[0])

    def test_every_page_has_a_chat_config_that_parses(self):
        suggestions = self.model["site"].get("chat", {}).get("suggestions", {})
        self.assertTrue(self.pages)
        for path in self.pages:
            rel = path.relative_to(self.out).as_posix()
            text = path.read_text(encoding="utf-8")
            cfg = self.config(text)
            lang = re.search(r'<div class="site [^"]*" lang="[^"]+" data-root="[^"]*" data-lang="(\w+)"', text).group(1)
            self.assertEqual((cfg["mode"], cfg["api"], cfg["lang"]), ("demo", "", lang), rel)
            self.assertEqual(cfg["build"], self.manifest["digest"], rel)
            self.assertEqual(cfg["suggestions"], suggestions.get(lang, []), rel)
            chat_strings = {k: v for k, v in self.model["strings"][lang].items() if k.startswith("chat_")}
            self.assertEqual(cfg["strings"], chat_strings, rel)
            # canonical paths; chat.js resolves them against data-root
            for key in ("index", "manifest", "about"):
                self.assertTrue(cfg[key].startswith("/"), (rel, key))
            self.assertTrue(cfg["page"]["url"].startswith("/"), rel)
            self.assertTrue(cfg["about"].endswith("/about/#assistant"), rel)
            self.assertTrue((self.out / cfg["index"].lstrip("/")).is_file(), rel)

    def test_preview_links_to_the_chat_assets_are_relative(self):
        slug = self.model["articles"]["zh"][0].slug
        for rel, root, up in (("index.html", "./", ""), (f"articles/{slug}/index.html", "../../", "../../"),
                              (f"zh/articles/{slug}/index.html", "../../../", "../../../")):
            page = self.read(rel)
            self.assertIn(f'data-root="{root}"', page, rel)
            self.assertIn(f'<link rel="stylesheet" href="{up}assets/chat.css">', page, rel)
            self.assertIn(f'<script src="{up}assets/chat.js" defer></script>', page, rel)
            self.assertNotIn('href="/assets/', page, rel)
        for name in ("chat.js", "chat.css"):
            self.assertTrue((self.out / "assets" / name).is_file())

    def test_header_launcher_and_article_aside(self):
        articles = {f"{'zh/' if a.lang == 'zh' else ''}articles/{a.slug}/index.html"
                    for lang in content.LANGS for a in self.model["articles"][lang]}
        for path in self.pages:
            rel = path.relative_to(self.out).as_posix()
            text = path.read_text(encoding="utf-8")
            tools = text.split('<div class="header-tools">', 1)[1].split("</div>", 1)[0]
            self.assertEqual(tools.count('class="chat-launch"'), 1, rel)
            self.assertLess(tools.index('class="chat-launch"'), tools.index('class="search-link"'), rel)
            self.assertRegex(tools, r'<button type="button" class="chat-launch" data-chat-open hidden ', rel)
            if rel in articles:
                aside = text.split('<aside class="doc-aside">', 1)[1].split("</aside>", 1)[0]
                self.assertNotIn('<section class="record"', aside, rel)
                after_details = aside.split('<section class="doc-details"', 1)[1].split("</section>", 1)[1]
                self.assertTrue(after_details.lstrip().startswith('<section class="chat-aside" data-chat-wrap hidden'), rel)
                self.assertIn('data-chat-open="article"', after_details, rel)
            else:
                self.assertNotIn('class="chat-aside"', text, rel)

    def test_article_page_context_matches_the_manifest(self):
        by_page = {e["page"]: e for e in self.manifest["entries"] if e["page"]}
        for lang in content.LANGS:
            for a in self.model["articles"][lang]:
                rel = f"{'zh/' if lang == 'zh' else ''}articles/{a.slug}/index.html"
                page = self.config(self.read(rel))["page"]
                entry = by_page[page["url"]]
                self.assertEqual((page["kind"], page["slug"], page["title"]), ("article", a.slug, a.title), rel)
                self.assertEqual((page["sha256"], page["source"]), (entry["sha256"], entry["source"]), rel)
                self.assertTrue((self.out / page["source"].lstrip("/")).is_file(), rel)

    def test_chinese_pages_carry_chinese_chat_strings(self):
        zh = self.model["strings"]["zh"]
        for rel in ("zh/index.html", "zh/about/index.html", f"zh/articles/{self.model['articles']['zh'][0].slug}/index.html"):
            text = self.read(rel)
            cfg = self.config(text)
            self.assertEqual(cfg["strings"]["chat_launch"], zh["chat_launch"], rel)
            self.assertEqual(cfg["about"], "/zh/about/#assistant", rel)
            self.assertEqual(cfg["index"], "/zh/search-index.json", rel)
            self.assertIn(f'aria-label="{html.escape(zh["chat_launch_aria"])}"', text, rel)
            self.assertIn(f'<span class="chat-launch-label" aria-hidden="true">{html.escape(zh["chat_launch"])}</span>', text, rel)
        about = self.read("zh/about/index.html")
        self.assertIn('id="assistant"', about)
        self.assertIn('id="assistant"', self.read("about/index.html"))


class ChatModeBuildTests(unittest.TestCase):
    """--chat off is the kill switch; --chat live points the widget at a backend."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.off = Path(cls.tmp.name) / "off"
        cls.live = Path(cls.tmp.name) / "live"
        for out, extra in ((cls.off, ("--chat", "off")), (cls.live, ("--chat", "live", "--chat-api", "http://127.0.0.1:8787/"))):
            result = build_site(out, *extra)
            if result.returncode:
                raise AssertionError(result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_chat_off_emits_no_chat_markup_or_assets(self):
        pages = sorted(self.off.rglob("*.html"))
        self.assertTrue(pages)
        hits = [f"{p.relative_to(self.off)}: {m}" for p in pages for m in CHAT_MARKERS if m in p.read_text(encoding="utf-8")]
        self.assertEqual(hits, [])
        self.assertFalse((self.off / "assets" / "chat.js").exists())
        self.assertFalse((self.off / "assets" / "chat.css").exists())
        self.assertTrue((self.off / "assets" / "site.js").exists())

    def test_chat_live_points_at_the_api(self):
        for rel in ("index.html", "zh/about/index.html"):
            text = (self.live / rel).read_text(encoding="utf-8")
            cfg = json.loads(CHAT_CONFIG_RE.search(text).group(1))
            self.assertEqual((cfg["mode"], cfg["api"]), ("live", "http://127.0.0.1:8787"), rel)

    def test_same_stylesheet_keeps_its_version_across_builds(self):
        self.assertEqual((self.off / "assets" / "site.css").read_bytes(),
                         (self.live / "assets" / "site.css").read_bytes())
        for rel in ("index.html", "zh/index.html"):
            before = parse_html((self.off / rel).read_text(encoding="utf-8"))
            after = parse_html((self.live / rel).read_text(encoding="utf-8"))
            self.assertEqual(site_stylesheet_href(before), site_stylesheet_href(after), rel)

    def test_live_without_an_api_base_stops_the_build(self):
        result = build_site(Path(self.tmp.name) / "bad", "--chat", "live", "--chat-api", "")
        self.assertEqual(result.returncode, 1)
        self.assertIn("content error: chat.mode \"live\" needs chat.api_base", result.stderr)


class StylesheetOverrideBuildTests(unittest.TestCase):
    def test_css_override_publishes_and_versions_the_override_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            css = Path(tmp) / "alternate.css"
            css_bytes = b"/* alternate stylesheet */\r\nbody { color: #234567; }\r\n"
            css.write_bytes(css_bytes)
            out = Path(tmp) / "site"
            result = build_site(out, "--css", str(css))
            self.assertEqual(result.returncode, 0, result.stderr)
            published = (out / "assets" / "site.css").read_bytes()
            self.assertEqual(published, css_bytes)
            digest = hashlib.sha256(published).hexdigest()
            self.assertNotEqual(digest, hashlib.sha256((ROOT / "static" / "site.css").read_bytes()).hexdigest())
            for rel in ("index.html", "zh/index.html"):
                doc = parse_html((out / rel).read_text(encoding="utf-8"))
                self.assertEqual(parse_qs(urlsplit(site_stylesheet_href(doc)).query), {"v": [digest[:16]]}, rel)



# ----- lead images ------------------------------------------------------------------------------
# Placeholder pictures for the tests: the real ones come from python3 tools/illustrate.py --write

def placeholder_svg(n=0, extra=""):
    """A minimal illustration in the contract's shape: 1200x800 with a viewBox, no text."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" viewBox="0 0 1200 800">'
            f'<rect width="1200" height="800" fill="#f4f5f7"/><circle cx="{600 + n}" cy="400" r="80" fill="#3f4a8a"/>'
            f'{extra}</svg>\n').encode()


def tiny_png(width=3, height=2):
    """A small valid PNG, standing in for a photo."""
    import struct
    import zlib
    rows = b"".join(b"\x00" + bytes([200, 120, 40]) * width for _ in range(height))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


def jpeg_header(width, height, orientation=None, order="big", progressive=False):
    """The start of a JPEG up to its frame header (all the build reads): SOI, an optional
    EXIF block with an Orientation tag, a quantization table and SOF0 (or SOF2)."""
    import struct

    def segment(marker, body):
        return bytes([0xFF, marker]) + struct.pack(">H", len(body) + 2) + body
    out = b"\xff\xd8"
    if orientation is not None:
        e = ">" if order == "big" else "<"
        tiff = (b"MM\x00*" if order == "big" else b"II*\x00") + struct.pack(e + "I", 8)
        tiff += struct.pack(e + "H", 1) + struct.pack(e + "HHI", 0x0112, 3, 1) + struct.pack(e + "HH", orientation, 0)
        tiff += struct.pack(e + "I", 0)
        out += segment(0xE1, b"Exif\x00\x00" + tiff)
    out += segment(0xDB, b"\x00" + bytes(64))
    out += segment(0xC2 if progressive else 0xC0, struct.pack(">BHHB", 8, height, width, 1) + b"\x01\x11\x00")
    return out + segment(0xDA, b"\x01\x01\x00\x00\x3f\x00")


def webp_header(chunk, width, height):
    """The start of a WebP file with a lossy (VP8), lossless (VP8L) or extended (VP8X) first chunk."""
    import struct
    if chunk == b"VP8 ":
        body = b"\x00\x00\x00" + b"\x9d\x01\x2a" + struct.pack("<HH", width, height)
    elif chunk == b"VP8L":
        body = b"\x2f" + struct.pack("<I", (width - 1) | ((height - 1) << 14))
    else:
        body = b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
    body += bytes(8)
    return b"RIFF" + struct.pack("<I", 4 + 8 + len(body)) + b"WEBP" + chunk + struct.pack("<I", len(body)) + body


LEAD_TEXTS = {
    "alt": {"en": "A test scene: a dark circle on a light ground.", "zh": "测试场景：浅色底上的一个深色圆形。"},
    "caption": {"en": "Illustration: a test scene. It does not depict any real system.",
                "zh": "示意图：测试场景，不描绘任何真实系统。"},
}


def write_illustration(root, slug, svg=None, **fields):
    """Write static/media/<slug>.svg and the article's illustration.json (its digest included,
    unless FIELDS sets svg_sha256), and return the spec."""
    svg = placeholder_svg() if svg is None else svg
    media = Path(root) / content.MEDIA_DIR
    media.mkdir(parents=True, exist_ok=True)
    (media / f"{slug}.svg").write_bytes(svg)
    spec = {"kind": "illustration", **copy.deepcopy(LEAD_TEXTS), "scene": {"test": True},
            "svg_sha256": hashlib.sha256(svg).hexdigest()}
    spec.update(fields)
    path = Path(root) / "content" / "articles" / slug / content.LEAD_IMAGE_FILE
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return spec


def photo_files(slug):
    """Placeholder files for a photo, as tools/photos.py names its four: the photo (6 x 4), its two
    copies for lists (3 x 2 and 2 x 1, each narrower than the one before and within a pixel of the
    photo's proportions) and its copy for link previews (1200 x 630, a JPEG header, which is all
    the build reads)."""
    return {f"{slug}.png": tiny_png(6, 4), f"{slug}-list.png": tiny_png(3, 2), f"{slug}-thumb.png": tiny_png(2, 1),
            f"{slug}-og.jpg": jpeg_header(1200, 630)}


def write_photo(root, slug, **fields):
    """Write a placeholder photo and its three copies into static/media/ and the article's
    illustration.json for them, in the shape tools/photos.py writes, and return the spec. The
    photo is cut from part of a 3000 x 2000 source, so it counts as cropped; FIELDS replace
    top-level fields."""
    media = Path(root) / content.MEDIA_DIR
    media.mkdir(parents=True, exist_ok=True)
    sizes = {f"{slug}.png": (6, 4), f"{slug}-list.png": (3, 2), f"{slug}-thumb.png": (2, 1), f"{slug}-og.jpg": (1200, 630)}
    entries = {}
    for name, data in photo_files(slug).items():
        (media / name).write_bytes(data)
        size = sizes[name]
        entries[name] = {"file": name, "width": size[0], "height": size[1], "sha256": hashlib.sha256(data).hexdigest()}
    spec = {"kind": "photo", **entries[f"{slug}.png"],
            "variants": {"list": entries[f"{slug}-list.png"], "thumb": entries[f"{slug}-thumb.png"],
                         "social": entries[f"{slug}-og.jpg"]},
            "edits": {"source_sha256": "ab" * 32, "source_size": [3000, 2000], "crop": [300, 0, 2400, 1600],
                      "social_crop": [300, 170, 2400, 1260], "grade": content.PHOTO_GRADES[0]},
            **copy.deepcopy(LEAD_TEXTS), "credit": "Example Photographer", "license": "CC BY 4.0",
            "license_url": "https://creativecommons.org/licenses/by/4.0/", "source_url": "https://example.org/photo",
            "retrieved": "2026-10-23"}
    spec["caption"] = {"en": "A test photo.", "zh": "测试照片。"}
    spec.update(fields)
    path = Path(root) / "content" / "articles" / slug / content.LEAD_IMAGE_FILE
    path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return spec


def set_lead_image_kinds(root, kinds):
    path = Path(root) / "content" / "site.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["lead_image_kinds"] = kinds
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class LeadImageTests(unittest.TestCase):
    """content/articles/<slug>/illustration.json: sitegen/content.py checks each spec, the image it
    names and its digest, attaches the image to both editions, and enforces lead_image_kinds."""

    def setUp(self):
        """A copy of the content with no lead images at all, whatever the repository has."""
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(ROOT / "content", self.root / "content")
        for spec in (self.root / "content" / "articles").glob(f"*/{content.LEAD_IMAGE_FILE}"):
            spec.unlink()
        set_lead_image_kinds(self.root, [])
        model = content.load(self.root)
        self.news = [a.slug for a in model["articles"]["en"] if a.kind == "news"]
        self.explainer = next(a.slug for a in model["articles"]["en"] if a.kind == "explainer")
        self.slug = self.news[0]

    def tearDown(self):
        self.tmp.cleanup()

    def editions(self, model, slug):
        return [a for lang in content.LANGS for a in model["articles"][lang] if a.slug == slug]

    def test_a_spec_gives_both_editions_one_lead_image(self):
        svg = placeholder_svg(7)
        spec = write_illustration(self.root, self.slug, svg)
        model = content.load(self.root)
        en, zh = self.editions(model, self.slug)
        self.assertIs(en.lead_image, zh.lead_image)
        image = en.lead_image
        self.assertEqual((image.kind, image.width, image.height), ("illustration", 1200, 800))
        self.assertEqual((image.src, image.spec_path, image.file),
                         (f"/assets/media/{self.slug}.svg", f"/articles/{self.slug}/illustration.json", f"{self.slug}.svg"))
        self.assertEqual((image.raw, image.sha256), (svg, hashlib.sha256(svg).hexdigest()))
        raw = (self.root / "content" / "articles" / self.slug / "illustration.json").read_bytes()
        self.assertEqual((image.spec_raw, image.spec_sha256), (raw, hashlib.sha256(raw).hexdigest()))
        self.assertEqual((image.alt, image.caption), (spec["alt"], spec["caption"]))
        # the other articles have none, and lists without a spec keep to text
        self.assertEqual([a.slug for a in model["articles"]["en"] if a.lead_image], [self.slug])

    def test_a_broken_spec_or_picture_stops_the_load(self):
        svg = placeholder_svg()
        drawn = hashlib.sha256(svg).hexdigest()

        def with_svg(data):
            """A spec whose picture is DATA, with the matching digest, so only the picture is wrong."""
            return {"svg": data, "svg_sha256": hashlib.sha256(data).hexdigest()}

        cases = {
            "alt without Chinese": {"alt": {"en": "A scene."}},
            "empty English caption": {"caption": {"en": " ", "zh": "示意图：测试。"}},
            "caption as one string": {"caption": "Illustration: a scene."},
            "digest of other bytes": {"svg_sha256": "0" * 64},
            "digest in capitals": {"svg_sha256": drawn.upper()},
            "unknown kind": {"kind": "drawing"},
            "unknown field": {"captions": LEAD_TEXTS["caption"]},
            "no scene": {"scene": None},
            "scene as text": {"scene": "a stack of plates"},
            "wrong canvas": with_svg(placeholder_svg().replace(b'width="1200"', b'width="800"')),
            "no viewBox": with_svg(placeholder_svg().replace(b' viewBox="0 0 1200 800"', b"")),
            "a script": with_svg(placeholder_svg(extra="<script>alert(1)</script>")),
            "an event handler": with_svg(placeholder_svg(extra='<rect width="1" height="1" onload="alert(1)"/>')),
            "an outside reference": with_svg(placeholder_svg(extra='<use href="https://example.org/a.svg#x"/>')),
            "an outside url()": with_svg(placeholder_svg(extra='<rect width="1" height="1" fill="url(https://x/y#z)"/>')),
            "a quoted outside url()": with_svg(placeholder_svg(extra='<rect width="1" height="1" fill="url(\'//x/y#z\')"/>')),
            "an outside url() after a local one": with_svg(placeholder_svg(
                extra='<rect width="1" height="1" fill="url(#a) URL(https://x/y)"/>')),
            "a style attribute": with_svg(placeholder_svg(extra='<rect width="1" height="1" style="fill:#000"/>')),
            "an embedded document": with_svg(placeholder_svg(extra="<foreignObject/>")),
            "not SVG": with_svg(b"<html><body/></html>"),
            "not XML": with_svg(b"<svg"),
            "entities": with_svg(b'<!DOCTYPE svg [<!ENTITY a "b">]>' + placeholder_svg()),
            # ways around a search of the raw bytes: the check reads the parsed document instead
            "a stylesheet instruction": with_svg(b'<?xml-stylesheet href="https://x/a.css"?>' + placeholder_svg()),
            "an XSLT instruction after the declaration": with_svg(
                b'<?xml version="1.0" encoding="UTF-8"?>\n<?xml-stylesheet type="text/xsl" href="https://x/a.xsl"?>'
                + placeholder_svg()),
            "a url() spelt with a character reference": with_svg(placeholder_svg(
                extra='<rect width="1" height="1" filter="&#117;rl(https://x/f.svg#f)"/>')),
            "a cursor url() spelt with a character reference": with_svg(placeholder_svg(
                extra='<rect width="1" height="1" cursor="&#117;rl(https://x/c.png),auto"/>')),
            "a CSS escape in an attribute": with_svg(placeholder_svg(extra='<rect width="1" height="1" fill="u\\72l(https://x/y)"/>')),
            "a CSS escape in a style element": with_svg(placeholder_svg(extra="<style>rect{fill:u\\72l(https://x/y)}</style>")),
            "an escaped @import": with_svg(placeholder_svg(extra='<style>@\\69mport "https://x/a.css";</style>')),
            "another CSS function": with_svg(placeholder_svg(
                extra='<rect width="1" height="1" cursor="image-set(\'https://x/c.png\' 1x)"/>')),
            "entities in UTF-16": with_svg(('<!DOCTYPE svg [<!ENTITY a "b">]>' + placeholder_svg().decode()).encode("utf-16")),
            "UTF-16 without a byte-order mark": with_svg(placeholder_svg().decode().encode("utf-16-le")),
            "a byte-order mark": with_svg(b"\xef\xbb\xbf" + placeholder_svg()),
            "a comment": with_svg(placeholder_svg(extra="<!-- a note -->")),
            "an animation that rewrites a link": with_svg(placeholder_svg(extra='<set attributeName="href" to="https://x/"/>')),
            "an animation": with_svg(placeholder_svg(extra='<rect width="1" height="1"><animate attributeName="fill" '
                                                           'values="#000;#fff" dur="1s"/></rect>')),
            "an outside xlink:href": with_svg(placeholder_svg(
                extra='<linearGradient xmlns:xlink="http://www.w3.org/1999/xlink" id="g" xlink:href="https://x/a.svg#g"/>')),
            "an xml:base": with_svg(placeholder_svg(extra='<g xml:base="https://x/"/>')),
            "a filter image": with_svg(placeholder_svg(extra='<filter id="f"><feImage href="#a"/></filter>')),
            "an element in another namespace": with_svg(placeholder_svg(extra='<h:p xmlns:h="http://www.w3.org/1999/xhtml"/>')),
            "words": with_svg(placeholder_svg(extra='<text x="10" y="10">Meta</text>')),
            "a root outside the SVG namespace": with_svg(placeholder_svg().replace(b' xmlns="http://www.w3.org/2000/svg"', b"")),
            "another viewBox": with_svg(placeholder_svg().replace(b"0 0 1200 800", b"0 0 10 10")),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                change = dict(change)
                data = change.pop("svg", svg)
                spec = write_illustration(self.root, self.slug, data)
                spec.update(change)
                spec = {k: v for k, v in spec.items() if v is not None}
                path = self.root / "content" / "articles" / self.slug / "illustration.json"
                path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(content.ContentError) as caught:
                    content.load(self.root)
                self.assertIn(self.slug, str(caught.exception))
        with self.subTest(case="missing picture"):
            write_illustration(self.root, self.slug, svg)
            (self.root / content.MEDIA_DIR / f"{self.slug}.svg").unlink()
            with self.assertRaises(content.ContentError) as caught:
                content.load(self.root)
            self.assertIn(f"static/media/{self.slug}.svg is missing", str(caught.exception))
            self.assertIn("python3 tools/illustrate.py --write", str(caught.exception))
        with self.subTest(case="not JSON"):
            path = self.root / "content" / "articles" / self.slug / "illustration.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(content.ContentError):
                content.load(self.root)
        with self.subTest(case="a list"):
            path.write_text("[]", encoding="utf-8")
            with self.assertRaises(content.ContentError):
                content.load(self.root)

    def test_a_picture_may_use_gradients_filters_and_its_own_references(self):
        """What the allowlist keeps: an XML declaration, gradients, a blur filter, clip paths,
        url(#id) quoted or not, an xlink:href to an id, colours, transforms, a title."""
        extra = ('<defs><linearGradient id="g"><stop offset="0" stop-color="#fff"/></linearGradient>'
                 '<linearGradient xmlns:xlink="http://www.w3.org/1999/xlink" id="h" xlink:href="#g"/>'
                 '<filter id="f" filterUnits="userSpaceOnUse"><feGaussianBlur stdDeviation="3"/></filter>'
                 '<clipPath id="c"><rect width="10" height="10"/></clipPath></defs>'
                 '<g clip-path="url(#c)" transform="translate(4 5) rotate(3)"><rect width="9" height="9" '
                 'fill="url(&quot;#g&quot;)" filter="url(\'#f\')"/><circle r="2" fill="rgb(10, 20, 30)"/></g>'
                 '<title>A test scene</title>')
        svg = b'<?xml version="1.0" encoding="UTF-8"?>\n' + placeholder_svg(extra=extra)
        write_illustration(self.root, self.slug, svg)
        self.assertEqual(self.editions(content.load(self.root), self.slug)[0].lead_image.raw, svg)

    def test_every_prop_the_generator_draws_passes_the_picture_check(self):
        """The allowlist covers what tools/illustrate.py draws: every prop in every tint it
        takes, and each ground, as the generator's catalog lays them out."""
        try:
            sys.path.insert(0, str(ROOT / "tools"))
            from scene import draw
            from scene.kit import REGISTRY
        except ImportError:
            self.skipTest("tools/scene is not here")
        finally:
            sys.path.remove(str(ROOT / "tools"))
        grounds = ({"kind": "plate"}, {"kind": "plate", "tint": "tee"}, {"kind": "plate", "tint": "pcb"},
                   {"kind": "tiles", "size": [5, 4]}, {"kind": "desk"}, {"kind": "none"})
        drawn = 0
        for name, pdef in REGISTRY.items():
            for tint in pdef.tints:
                item = {"prop": name, "at": [0, 0], **(pdef.example or {}), "tint": tint}
                if pdef.container:
                    item.update({"w": 3, "d": 2.4, "h": 1.8,
                                 "items": [{"prop": "server", "at": [0, 0], "tint": "tee", "w": 2, "d": 1.2}]})
                for ground in grounds if tint == pdef.tint else grounds[:1]:
                    with self.subTest(prop=name, tint=tint, ground=ground):
                        svg = draw({"ground": ground, "items": [item]}).encode("utf-8")
                        self.assertEqual(content._svg_size(svg, f"{name} {tint}"), content.ILLUSTRATION_SIZE)
                        drawn += 1
        self.assertGreater(drawn, len(REGISTRY))

    def test_a_photo_names_its_file_credit_license_and_source(self):
        write_photo(self.root, self.explainer)
        image = self.editions(content.load(self.root), self.explainer)[0].lead_image
        self.assertEqual((image.kind, image.src, image.width, image.height),
                         ("photo", f"/assets/media/{self.explainer}.png", 6, 4))
        self.assertEqual((image.credit, image.license, image.source_url),
                         ("Example Photographer", "CC BY 4.0", "https://example.org/photo"))
        # its copies, published beside it (tests/test_photos.py checks them in depth)
        self.assertEqual([(p.src, p.width, p.height) for p in image.published()],
                         [(f"/assets/media/{self.explainer}{end}", w, h)
                          for end, w, h in ((".png", 6, 4), ("-list.png", 3, 2), ("-thumb.png", 2, 1),
                                            ("-og.jpg", 1200, 630))])
        cases = {
            "a folder in the file name": {"file": "../og/site-en.png"},
            "a file type browsers do not show": {"file": f"{self.explainer}.tiff"},
            "no license address": {"license_url": None},
            "a source that is not http(s)": {"source_url": "javascript:alert(1)"},
            "a retrieval date that is not a day": {"retrieved": "2026-10"},
            "an impossible date": {"retrieved": "2026-13-01"},
            "no width": {"width": 0},
            "a width as text": {"width": "6"},
            "a size that is not the file's": {"width": 1200, "height": 800},
            "the sides swapped": {"width": 4, "height": 6},
            "no copies": {"variants": None},
            "no edits": {"edits": None},
            "a license a photo may not carry": {"license": "CC BY-NC 4.0",
                                                "license_url": "https://creativecommons.org/licenses/by-nc/4.0/"},
            "a type the build cannot measure": {"file": f"{self.explainer}.avif"},
            "a credit in one language": {"credit": {"en": "A. Person", "zh": ""}},
            "an illustration's digest field": {"svg_sha256": "0" * 64},
            "a wrong digest": {"sha256": "0" * 64},
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                spec = write_photo(self.root, self.explainer)
                spec.update(change)
                spec = {k: v for k, v in spec.items() if v is not None}
                path = self.root / "content" / "articles" / self.explainer / "illustration.json"
                path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(content.ContentError):
                    content.load(self.root)

    def test_a_photo_is_the_type_its_name_says_and_the_size_its_spec_says(self):
        """The build publishes a photo under its extension and reserves its box from width and
        height, so it reads both from the bytes: a mismatch stops the build, digest or not."""
        write_photo(self.root, self.explainer, width=1200, height=800)
        with self.assertRaises(content.ContentError) as caught:
            content.load(self.root)
        self.assertIn("width and height say 1200 x 800 pixels, but static/media/", str(caught.exception))
        self.assertIn("is 6 x 4", str(caught.exception))
        fake = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        (self.root / content.MEDIA_DIR / "fake.png").write_bytes(fake)
        write_photo(self.root, self.explainer, file="fake.png", sha256=hashlib.sha256(fake).hexdigest())
        with self.assertRaises(content.ContentError) as caught:
            content.load(self.root)
        self.assertIn("static/media/fake.png is not a PNG file", str(caught.exception))
        # a JPEG named .webp is refused too
        jpeg = jpeg_header(6, 4)
        (self.root / content.MEDIA_DIR / "photo.webp").write_bytes(jpeg)
        write_photo(self.root, self.explainer, file="photo.webp", sha256=hashlib.sha256(jpeg).hexdigest())
        with self.assertRaises(content.ContentError) as caught:
            content.load(self.root)
        self.assertIn("is not a WebP file", str(caught.exception))
        for name, data in (("photo.jpg", jpeg), ("photo.jpeg", jpeg_header(4, 6, orientation=6)),
                           ("photo.webp", webp_header(b"VP8X", 6, 4))):
            with self.subTest(name):
                (self.root / content.MEDIA_DIR / name).write_bytes(data)
                write_photo(self.root, self.explainer, file=name, sha256=hashlib.sha256(data).hexdigest())
                image = self.editions(content.load(self.root), self.explainer)[0].lead_image
                self.assertEqual((image.src, image.width, image.height), (f"/assets/media/{name}", 6, 4))

    def test_photo_sizes_come_from_each_types_header(self):
        size = content._raster_size
        self.assertEqual(size(tiny_png(5, 4), "PNG"), (5, 4))
        self.assertEqual(size(jpeg_header(640, 480), "JPEG"), (640, 480))
        self.assertEqual(size(jpeg_header(640, 480, progressive=True), "JPEG"), (640, 480))
        for orientation, want in ((1, (640, 480)), (3, (640, 480)), (6, (480, 640)), (8, (480, 640))):
            for order in ("little", "big"):
                with self.subTest(orientation=orientation, order=order):
                    self.assertEqual(size(jpeg_header(640, 480, orientation=orientation, order=order), "JPEG"), want)
        for chunk in (b"VP8 ", b"VP8L", b"VP8X"):
            with self.subTest(chunk=chunk):
                self.assertEqual(size(webp_header(chunk, 1600, 1067), "WebP"), (1600, 1067))
        for raw, kind in ((b"", "PNG"), (tiny_png()[:20], "PNG"), (jpeg_header(3, 2), "PNG"), (tiny_png(), "JPEG"),
                          (b"\xff\xd8\xff\xd9", "JPEG"), (jpeg_header(3, 2)[:-14], "JPEG"), (tiny_png(), "WebP"),
                          (b"RIFF\x00\x00\x00\x00WEBPVP8 " + bytes(20), "WebP")):
            with self.subTest(raw=raw[:16], kind=kind):
                self.assertIsNone(size(raw, kind))

    def test_lead_image_kinds_needs_a_spec_for_every_story_of_those_kinds(self):
        self.assertIn("lead_image_kinds", json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8")))
        set_lead_image_kinds(self.root, ["news"])
        with self.assertRaises(content.ContentError) as caught:
            content.load(self.root)
        self.assertIn("illustration.json is missing", str(caught.exception))
        self.assertIn("lead_image_kinds", str(caught.exception))
        for n, slug in enumerate(self.news):
            write_illustration(self.root, slug, placeholder_svg(n))
        model = content.load(self.root)
        self.assertTrue(all(a.lead_image for lang in content.LANGS for a in model["articles"][lang] if a.kind == "news"))
        # a draft brief in review has no picture yet: a --drafts preview still builds
        draft = self.root / "content" / "articles" / "zz-draft-news"
        draft.mkdir()
        en = (self.root / "content" / "articles" / self.slug / "en.md").read_text(encoding="utf-8")
        (draft / "en.md").write_text(en.replace("---\n", "---\ndraft: true\n", 1), encoding="utf-8")
        model = content.load(self.root, drafts=True)
        found = next(a for a in model["articles"]["en"] if a.slug == "zz-draft-news")
        self.assertEqual((found.kind, found.draft, found.lead_image), ("news", True, None))
        self.assertNotIn("zz-draft-news", [a.slug for a in content.load(self.root)["articles"]["en"]])
        shutil.rmtree(draft)
        for bad in (["briefs"], ["news", "news"], "news", [None]):
            with self.subTest(kinds=bad):
                set_lead_image_kinds(self.root, bad)
                with self.assertRaises(content.ContentError) as caught:
                    content.load(self.root)
                self.assertIn("lead_image_kinds", str(caught.exception))
        set_lead_image_kinds(self.root, [])
        content.load(self.root)


class AboutIllustrationsTests(unittest.TestCase):
    """What About says of the lead images stays true of the build. (Whether each committed
    picture is what the generator draws is tests/test_illustrate.py's RepositoryTest, which
    runs python3 tools/illustrate.py --check as CI's Build and check job does.)"""

    # The sentence that promises a picture on every news brief, as each file words it.
    EVERY_BRIEF = (("content/pages/about.en.md", ("Every news brief opens with", "Each news brief opens with")),
                   ("content/pages/about.zh.md", ("每篇新闻简报开头都",)),
                   ("README.md", ("Every news brief opens with", "Each news brief opens with")))

    def test_about_says_every_brief_has_a_picture_exactly_when_the_build_requires_one(self):
        """About (both editions) and the README promise a picture on every news brief exactly
        while content/site.json lists news under lead_image_kinds, which makes the build stop on
        a brief without one: drop news from the setting and the promise must go too."""
        kinds = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8")).get("lead_image_kinds", [])
        for rel, phrases in self.EVERY_BRIEF:
            said = [p for p in phrases if p in (ROOT / rel).read_text(encoding="utf-8")]
            if "news" in kinds:
                self.assertTrue(said, f"lead_image_kinds lists news, so {rel} should say {phrases[0]!r}")
            else:
                self.assertEqual(said, [], f"{rel} says {said} but lead_image_kinds is {kinds}")

    def test_about_explains_the_illustrations_where_the_credit_line_links(self):
        """The credit line under each illustration links About's #illustrations, which says the
        pictures are drawn by code from their published scene descriptions; the same section says
        where the photos come from, under which licenses, and that every credit line names them."""
        needles = {"en": ("drawn by code from a published scene description", "Wikimedia Commons", "CC BY-SA",
                          "The credit line under every photo", "does not show"),
                   "zh": ("由代码根据公开的场景描述绘制", "Wikimedia Commons", "CC BY-SA", "署名行", "没有表现什么")}
        for lang, words in needles.items():
            text = (ROOT / "content" / "pages" / f"about.{lang}.md").read_text(encoding="utf-8")
            section = text.split("{#illustrations}", 1)[1].split("\n## ", 1)[0] if "{#illustrations}" in text else ""
            for needle in words:
                self.assertIn(needle, section, f"about.{lang}.md #illustrations")


def illustrated_project(root):
    """A copy of this project (build.py, indexnow.json, sitegen/, static/ and content/) in which every news
    brief has a placeholder illustration and one explainer, one analysis and one guide a
    placeholder photo, and content/site.json lists news under lead_image_kinds, as the site
    itself does. The explainer's photo is cropped under CC BY 4.0, the analysis's is in the
    public domain, and the guide's keeps its whole source under CC BY-SA 4.0, so the credit
    lines say "Cropped and color-adjusted", nothing and "Color-adjusted". static/media/ also
    holds a picture that no spec names, which the build must leave unpublished."""
    root.mkdir(parents=True)
    for name in ("build.py", "indexnow.json"):
        shutil.copy2(ROOT / name, root / name)
    shutil.copytree(ROOT / "sitegen", root / "sitegen", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "static", root / "static")
    shutil.copytree(ROOT / "content", root / "content")
    model = content.load(root)
    for n, a in enumerate(a for a in model["articles"]["en"] if a.kind == "news"):
        write_illustration(root, a.slug, placeholder_svg(n))
    first = {kind: next((a.slug for a in model["articles"]["en"] if a.kind == kind), None)
             for kind in ("explainer", "analysis", "guide")}
    write_photo(root, first["explainer"])
    if first["analysis"]:
        write_photo(root, first["analysis"], license="Public domain", credit="U.S. Department of Energy",
                    license_url="https://www.usa.gov/government-copyright", source_url="https://www.energy.gov/photos")
    if first["guide"]:
        write_photo(root, first["guide"], license="CC BY-SA 4.0",
                    license_url="https://creativecommons.org/licenses/by-sa/4.0/",
                    edits={"source_sha256": "cd" * 32, "source_size": [2400, 1600], "crop": [0, 0, 2400, 1600],
                           "social_crop": [0, 170, 2400, 1260], "grade": content.PHOTO_GRADES[0]})
    (root / content.MEDIA_DIR / "zz-orphan.svg").write_bytes(placeholder_svg(99))
    set_lead_image_kinds(root, ["news"])
    return root


class IllustratedBuildTests(BuildOutputTests):
    """Every BuildOutputTests check again, on a copy of the project whose news briefs carry lead
    illustrations, then the figure, the list copies, the manifest and two production builds."""

    @classmethod
    def project(cls, tmp):
        return illustrated_project(tmp / "project")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prod = []
        for n in (1, 2):
            out = Path(cls.tmp.name) / f"prod-{n}"
            result = subprocess.run([sys.executable, "build.py", "--out", str(out)], cwd=cls.root, capture_output=True,
                                    text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
            if result.returncode:
                raise AssertionError(result.stderr)
            cls.prod.append(out)

    def image_of(self, slug):
        return self.by_slug["en"][slug].lead_image

    def test_the_copy_illustrates_every_news_brief(self):
        news = [a for a in self.model["articles"]["en"] if a.kind == "news"]
        self.assertTrue(news and all(a.lead_image for a in news))
        self.assertEqual(self.model["site"]["lead_image_kinds"], ["news"])
        self.assertTrue(any(a.lead_image and a.lead_image.kind == "photo" for a in self.model["articles"]["en"]))

    def test_an_illustrated_article_opens_on_its_lead_figure(self):
        for lang in content.LANGS:
            s = self.s(lang)
            for a in self.articles(lang):
                rel = f"{LANG_DIR[lang]}articles/{a.slug}/index.html"
                art_el = self.dom(rel).find("article", cls="article")
                image = self.image_of(a.slug)
                figures = art_el.find_all("figure", cls="lead-figure")
                if image is None:
                    self.assertEqual((figures, "has-lead" in art_el.classes), ([], False), rel)
                    continue
                self.assertIn("has-lead", art_el.classes, rel)
                # right after the head, before the body and the record column
                self.assertEqual([kind_of(n, ("article-head", "lead-figure", "article-grid")) for n in art_el.kids()],
                                 ["article-head", "lead-figure", "article-grid"], rel)
                fig = figures[0]
                self.assertEqual(fig.attrs.get("data-image-kind"), image.kind, rel)
                link, caption = fig.kids()
                self.assertEqual((link.tag, canonical(rel, link.attrs["href"])), ("a", image.src), rel)
                img = link.kids("img")[0]
                self.assertEqual(canonical(rel, img.attrs["src"]), image.src, rel)
                self.assertEqual([img.attrs.get(k) for k in ("alt", "width", "height", "loading", "fetchpriority", "decoding")],
                                 [norm(self.t(image.alt, lang)), str(image.width), str(image.height), "eager", "high", "async"],
                                 rel)
                # a photo starts from its full-size file and offers its 400 and 800 px copies for narrow screens
                copies = [image.variants[name] for name in reversed(content.PHOTO_SRCSET) if name in image.variants]
                if not copies:
                    self.assertNotIn("srcset", img.attrs, rel)
                else:
                    self.assertEqual([(canonical(rel, url), w) for url, w in (c.split() for c in img.attrs["srcset"].split(","))],
                                     [(f.src, f"{f.width}w") for f in copies + [image]], rel)
                    self.assertEqual(img.attrs["sizes"], render.FIGURE_SIZES, rel)
                self.assertNotIn("tabindex", link.attrs, rel)  # the full-size link is the figure's one tab stop
                self.assertEqual(caption.tag, "figcaption", rel)
                self.assertEqual(caption.find("span", cls="lead-caption").text(), norm(self.t(image.caption, lang)), rel)
                credit = caption.find("span", cls="lead-credit")
                if image.kind == "illustration":
                    # drawn by code from the published scene description; how the site makes illustrations
                    self.assertEqual(self.links(rel, credit), [image.spec_path, loc("/about/", lang) + "#illustrations"], rel)
                    gap = "" if lang == "zh" else " "
                    self.assertEqual(credit.text(), norm(s["lead_credit"].replace("{spec}", s["lead_credit_spec"])
                                                         + gap + s["lead_credit_how"]), rel)
                    self.assertTrue((self.out / image.spec_path.lstrip("/")).is_file(), rel)
                else:
                    self.assertEqual(self.links(rel, credit), [image.license_url, image.source_url], rel)
                    # a credit is one name, or an {"en", "zh"} text when the name has a Chinese form
                    name = self.t(image.credit, lang)
                    self.assertTrue(credit.text().startswith(norm(s["lead_photo_credit"].format(credit=name))), rel)
                    # an English name on a Chinese page keeps its own language, as the license link does;
                    # a Chinese form is in the page's language
                    named = [n for n in credit.find_all("span") if n.text() == norm(name)]
                    english = not re.search(r"[㐀-鿿]", name)
                    self.assertEqual([n.attrs.get("lang") for n in named], ["en"] if lang == "zh" and english else [], rel)
                    # a license keeps its name ("CC BY 4.0", lang="en" on a Chinese page), but "Public
                    # domain" names no license, so it is in the page's language (公有领域)
                    lic = credit.find_all("a")[0]
                    public = self.t(image.license, "en").strip().lower() == "public domain"
                    self.assertEqual(lic.text(skip=lambda n: "ext-mark" in n.classes),
                                     norm(s["lead_photo_public_domain"] if public else self.t(image.license, lang)), rel)
                    self.assertEqual(lic.attrs.get("lang"), "en" if lang == "zh" and not public else None, rel)
                    # CC BY and CC BY-SA ask that changes be indicated: cropped (unless the crop is the
                    # whole source) and colour-adjusted; public domain asks nothing
                    changes = image.license.startswith("CC BY")
                    self.assertEqual(image.note_changes, changes, rel)
                    note = s["lead_photo_edited" if image.cropped else "lead_photo_graded"]
                    self.assertEqual(credit.text().endswith(" · " + note), changes, rel)

    def test_list_rows_show_a_copy_exactly_for_illustrated_stories(self):
        for lang in content.LANGS:
            rel = LANG_DIR[lang] + "index.html"
            doc = self.dom(rel)
            rows = ([doc.find("article", cls="news-lead")] + doc.find("section", cls="home-news").find_all("li", cls="ledger-row")
                    + doc.find("section", cls="tee-block").find("ol", cls="tee-latest").kids("li"))
            pages = [(rel, rows)]
            rel = LANG_DIR[lang] + "latest/index.html"
            pages.append((rel, self.dom(rel).find_all("li", cls="river-item")))
            rel = LANG_DIR[lang] + HUB.lstrip("/") + "index.html"
            pages.append((rel, self.dom(rel).find("section", id="coverage").find("ol", cls="tee-latest").kids("li")))
            for rel, rows in pages:
                self.assertTrue(rows, rel)
                for row in rows:
                    story = self.linked_article(rel, row)
                    thumbs = row.find_all("a", cls="story-thumb")
                    illustrated = self.image_of(story.slug) is not None
                    self.assertEqual((len(thumbs), "has-thumb" in row.classes), (int(illustrated), illustrated),
                                     (rel, story.slug))
                    if thumbs:
                        self.check_thumb(rel, thumbs[0].find("img"))
            # related cards show pictures only when all of them have one
            for a in self.articles(lang):
                rel = f"{LANG_DIR[lang]}articles/{a.slug}/index.html"
                cards = self.dom(rel).find("section", cls="related").find_all("article", cls="card")
                every = all(self.image_of(self.linked_article(rel, c).slug) for c in cards)
                self.assertEqual([bool(c.find("a", cls="story-thumb")) for c in cards], [every] * len(cards), rel)

    def test_a_photo_article_previews_with_the_photo_and_credits_it(self):
        """An article with a photo names the photo's social copy (variants.social) in og:image and
        twitter:image, with the photo's alt text, and as the image of its structured data, with the
        photo's credit and license; every other article keeps its primary topic's card."""
        base = self.model["site"]["base_url"].rstrip("/")
        photos = 0
        for lang in content.LANGS:
            for a in self.articles(lang):
                rel = f"{LANG_DIR[lang]}articles/{a.slug}/index.html"
                doc = self.dom(rel)
                meta = {n.attrs.get("name") or n.attrs.get("property"): n.attrs.get("content") for n in doc.find_all("meta")}
                ld = next(n for n in json.loads(doc.find("script", type="application/ld+json").raw())
                          if n.get("@type") in ("NewsArticle", "Article"))
                image = self.image_of(a.slug)
                social = image.variants.get("social") if image else None
                if social is None:
                    card = f"{base}/assets/og/{discover.card_file(a.primary_topic, lang)}"
                    self.assertEqual((meta["og:image"], meta["twitter:image"], ld["image"]["url"]), (card, card, card), rel)
                    self.assertNotIn("creditText", ld["image"], rel)
                    continue
                photos += 1
                url, alt = base + social.src, norm(self.t(image.alt, lang))
                self.assertEqual([meta[k] for k in ("og:image", "og:image:width", "og:image:height", "og:image:alt",
                                                    "twitter:card", "twitter:image", "twitter:image:alt")],
                                 [url, "1200", "630", alt, "summary_large_image", url, alt], rel)
                self.assertEqual(ld["image"], {"@type": "ImageObject", "url": url, "width": 1200, "height": 630,
                                               "creditText": norm(self.t(image.credit, lang)),
                                               "license": image.license_url}, rel)
                self.assertEqual((self.out / social.src.lstrip("/")).read_bytes(), social.raw, rel)
        self.assertGreater(photos, 0)

    def test_the_manifest_lists_each_lead_image_and_verify_manifest_checks_it(self):
        for out in self.prod:
            doc = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            sources = [e["source"] for e in doc["entries"]]
            self.assertEqual(sources, sorted(sources))
            for a in self.model["articles"]["en"]:
                image = a.lead_image
                if image is None:
                    self.assertNotIn(f"/articles/{a.slug}/illustration.json", sources)
                    continue
                listed = [(image.spec_path, image.spec_raw, "illustration")]
                listed += [(picture.src, picture.raw, "image") for picture in image.published()]  # a photo's copies too
                for source, raw, kind in listed:
                    entry = next(e for e in doc["entries"] if e["source"] == source)
                    self.assertEqual((entry["kind"], entry["title"], entry["sha256"]),
                                     (kind, a.slug, hashlib.sha256(raw).hexdigest()), source)
                    self.assertEqual((out / source.lstrip("/")).read_bytes(), raw, source)
            result = subprocess.run([sys.executable, str(ROOT / "tools" / "verify_manifest.py"), str(out)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn(f"{len(doc['entries'])} entries checked, 0 problems", result.stdout)

    def test_two_production_builds_are_byte_identical(self):
        def tree(out):
            return {p.relative_to(out).as_posix(): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()}
        first, second = (tree(out) for out in self.prod)
        self.assertEqual(sorted(first), sorted(second))
        self.assertEqual([name for name in first if first[name] != second[name]], [])
        self.assertTrue(any(name.startswith("assets/media/") for name in first))


if __name__ == "__main__":
    unittest.main()
