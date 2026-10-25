"""Load verifiable.pro content into a site model.

Layout (relative to the project root):

    content/site.json        site configuration
    content/strings.json     interface strings per language
    content/topics.json      topic pillars and the verification stack
    content/resources.json   resource library and reading paths
    content/glossary.json    glossary terms
    content/tee.json         TEE hub: learning path, platforms, trackers and terms
    content/tiers.json       trust tiers and the combinations deployed today
    content/articles/<slug>/en.md, zh.md
    content/articles/<slug>/illustration.json   the article's lead image (optional)
    content/pages/<name>.en.md, <name>.zh.md

A Chinese article file needs only title, dek and body; kind, topics, layers,
dates, sources and the byline are inherited from the English file unless overridden.

Every article has a byline: "author", the person who wrote it, or "agent", an AI
agent from content/site.json "agents" that drafted it, and optionally
"submitted_by", the person who submitted the story. load() stops on an article
with neither, both, an unknown agent, or a person's name that is the
publication's or an agent's.

An article's lead image is described by illustration.json beside its editions:
a photo that tools/photos.py crops and grades into static/media/ (the photo, two
smaller copies for lists and a copy for link previews), with its credit and
license, or a conceptual illustration that tools/illustrate.py draws into
static/media/<slug>.svg from the file's "scene". load() checks the file, each
image it names and their SHA-256 digests, and attaches the result to both
editions as Article.lead_image; it also lists the files in static/media/ that
no spec names (unused_media). content/site.json "lead_image_kinds" lists the
article kinds that must have one.

load() checks every id that the data files name (articles, resources,
glossary terms, stack layers, topics and tiers), that every text has both
languages, and that dates use the source-date forms. A failure raises
ContentError naming the file and the field.
"""

import datetime as dt
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from . import logos, md

KINDS = ("news", "analysis", "explainer", "guide")
LANGS = ("en", "zh")
INHERITED = ("kind", "topics", "layers", "event_date", "published", "updated", "sources", "featured", "author",
             "submitted_by", "agent", "lead", "evidence", "related", "draft")
# Slugs, page names and topic ids become URL paths, file names and HTML ids
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ID_RE = re.compile(r"^[A-Za-z][\w.-]*$")
URL_RE = re.compile(r"^https?://[^\s\"'<>]+$")
TEXT_FIELDS = ("title", "dek", "kind", "author", "submitted_by", "agent", "caption", "disclosure", "needs")
# ----- bylines ---------------------------------------------------------------------
# Every article says who drafted it: "author", the name of the person who wrote it, or
# "agent", the id of the AI agent that drafted it in content/site.json "agents"; never
# both. "submitted_by" may add the person who submitted the story. zh.md inherits all
# three, and may give a person's name in its Chinese form (load() checks the editions).
AGENT_KEYS = ("name", "description")
DATA_FILES = ("topics", "resources", "glossary", "tee", "tiers")

# The topic whose page is the TEE hub; an article that lists it carries the TEE label
TEE_TOPIC = "confidential-computing"
# Groups of TEE resources, in the order the TEE hub and the Resources catalog show them
TEE_AREAS = ("standards", "cpu", "gpu", "services", "attacks", "performance", "uses")
# How a stack layer's TEE line reaches it: direct evidence, or only through measured code
REACHES = ("direct", "via")
# The evidence chain: how far the binding of a layer's evidence to the layer below has got
BIND_STATUSES = ("deployed", "emerging", "missing")
PLATFORM_GROUPS = ("cpu", "gpu")
STACK_SIZE = 7  # T7 to T1: the layer codes, the Latest filter and the stylesheet assume seven
MAX_LAYERS = 3  # stack layers one article may name
MAX_HERO_EXAMPLES = 7  # examples a layer's label beside the home hero may show (one line from 45em)
MAX_CHECKERS = {"en": 100, "zh": 45}  # characters: about three lines in a layer card, two or three in a phone row at 390px
# Front-matter fields of the retired pictures (a plate, a digest drawing), refused; an
# article's lead image is described by illustration.json beside its editions instead
RETIRED_FIELDS = ("illustration", "plate")

# ----- lead images ----------------------------------------------------------------
# content/articles/<slug>/illustration.json describes the article's lead image
LEAD_IMAGE_FILE = "illustration.json"
# The images live in static/media/, which the build publishes at /assets/media/
MEDIA_DIR = Path("static") / "media"
MEDIA_URL = "/assets/media/"
# "photo": a photograph that tools/photos.py crops and grades into static/media/<slug>.webp and
# its copies, with its credit, license and source (the default for news briefs)
# "illustration": drawn by tools/illustrate.py from the spec's scene into static/media/<slug>.svg
LEAD_IMAGE_KINDS = ("illustration", "photo")
LEAD_IMAGE_KEYS = {
    "illustration": ("kind", "alt", "caption", "scene", "svg_sha256"),
    "photo": ("kind", "file", "width", "height", "sha256", "variants", "edits", "alt", "caption", "credit", "license",
              "license_url", "source_url", "retrieved"),
}
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
# A photo's copies, which tools/photos.py writes beside it in static/media/: "list" and
# "thumb", smaller copies of the photo that srcset offers beside it (PHOTO_SRCSET), each of the
# photo's proportions and narrower than the file before it, so that a list loads the smallest
# file its picture needs; and "social", the copy that link previews and the structured data
# show, a JPEG or PNG at the social cards' size. Each is checked as the photo itself is
PHOTO_VARIANTS = ("list", "thumb", "social")
PHOTO_SRCSET = ("list", "thumb")  # widest first, after the photo itself
PHOTO_FILE_KEYS = ("file", "width", "height", "sha256")
PHOTO_SOCIAL_SIZE = (1200, 630)  # the social cards' size (discover.CARD_SIZE)
PHOTO_SOCIAL_TYPES = ("JPEG", "PNG")  # what every link preview reads
# What tools/photos.py did to the source ("edits"): the source file's SHA-256 and size in
# pixels, the boxes it cut out for the photo (and its smaller copies) and for the social copy, as
# [x, y, width, height] in the source's pixels, and the colour grade, one of PHOTO_GRADES
# (tools/photos.py defines each). No photo is enlarged: each box is at least as wide as the
# file made from it
PHOTO_EDIT_KEYS = ("source_sha256", "source_size", "crop", "social_crop", "grade")
PHOTO_GRADES = ("soft-1",)
# The licenses a photo may carry (CONTENT_GUIDE.md, "Photos"): a pattern on the license's
# English name, the address its license_url must start with (None: any), and whether the
# license asks that changes be indicated, which the credit line then does
PHOTO_LICENSES = (
    (re.compile(r"^Public domain\b", re.I), None, False),
    (re.compile(r"^CC0(?: 1\.0)?$"), "creativecommons.org/publicdomain/zero/1.0", False),
    (re.compile(r"^CC BY (1\.0|2\.0|2\.5|3\.0|4\.0)(?: [a-z]{2,3})?$"), "creativecommons.org/licenses/by/{0}", True),
    (re.compile(r"^CC BY-SA (1\.0|2\.0|2\.5|3\.0|4\.0)(?: [a-z]{2,3})?$"), "creativecommons.org/licenses/by-sa/{0}",
     True),
    (re.compile(r"^Unsplash License$"), "unsplash.com/license", False),
    (re.compile(r"^Pexels License$"), "pexels.com/license", False),
)
# Every illustration is drawn on one canvas, so lists can crop all of them alike
ILLUSTRATION_SIZE = (1200, 800)
# A photo's file name inside static/media/: no folders, and a raster type browsers show whose
# header _raster_size() reads, so the build can hold the bytes to the type and the size the
# spec names (PHOTO_TYPES maps each extension to the type's name)
PHOTO_FILE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*\.(?:jpg|jpeg|png|webp)$")
PHOTO_TYPES = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WebP"}
# JPEG markers that start a frame header, which holds the image's size (not C4, C8 or CC)
JPEG_SOF = frozenset((0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF))
# What an illustration's SVG may carry. Pages show it through <img>, which ignores scripts
# and outside references, but the figure also links to the file itself, which a browser
# then opens as a document on the site's origin. So _svg_size() reads the parsed document
# against an allowlist rather than searching the bytes: UTF-8 text with no DOCTYPE,
# entities, comments, CDATA or processing instructions (a leading <?xml ...?> declaration
# aside); an <svg> root in the SVG namespace on the 1200 x 800 canvas; only the elements
# below, all in the SVG namespace (no scripts, styles, animation, text, images, links or
# embedded documents); no style attribute and no event handlers; href only to "#id"; and
# in every attribute value, as the browser decodes it, url() only to "#id", no CSS escapes,
# and no CSS function but a colour or a transform
SVG_NS = "http://www.w3.org/2000/svg"
SVG_ELEMENTS = frozenset((
    "svg", "defs", "g", "title", "desc", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "linearGradient", "radialGradient", "stop", "clipPath", "mask", "filter", "feBlend", "feColorMatrix",
    "feComponentTransfer", "feComposite", "feDropShadow", "feFlood", "feFuncA", "feFuncB", "feFuncG", "feFuncR",
    "feGaussianBlur", "feMerge", "feMergeNode", "feMorphology", "feOffset",
))
# Attributes in a namespace: only these (xlink:href, xml:space, xml:lang)
SVG_NS_ATTRS = frozenset(("{http://www.w3.org/1999/xlink}href", "{http://www.w3.org/XML/1998/namespace}space",
                          "{http://www.w3.org/XML/1998/namespace}lang"))
SVG_FUNCTIONS = frozenset(("url", "rgb", "rgba", "hsl", "hsla", "matrix", "translate", "scale", "rotate", "skewx",
                           "skewy"))
SVG_FUNCTION_RE = re.compile(r"([A-Za-z_-][\w-]*)\s*\(")
SVG_LOCAL_URL_RE = re.compile(r"""\s*(['"]?)#[A-Za-z_][\w.:-]*\1\s*\)""")
SVG_LOCAL_HREF_RE = re.compile(r"^#[A-Za-z_][\w.:-]*$")
SVG_DECLARATION_RE = re.compile(r"""<\?xml\s+version\s*=\s*(["'])1\.[01]\1(?:\s+encoding\s*=\s*(["'])(?i:utf-8)\2)?"""
                                r"""(?:\s+standalone\s*=\s*(["'])(?:yes|no)\3)?\s*\?>""")
SVG_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
# Source-date forms used in the data files: YYYY-MM-DD, YYYY-MM or YYYY
DATE_RE = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
# A data-file source: "article:<slug>" or "resource:<id>"
SOURCE_REF_RE = re.compile(r"^(article|resource):(\S+)$")


class ContentError(Exception):
    pass


def _json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _date(value, where):
    if not value:
        return None
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise ContentError(f"{where}: bad date {value!r}") from exc


def _sources(lines, where):
    out = []
    if isinstance(lines, str):
        lines = [lines]
    for n, line in enumerate(lines or [], 1):
        parts = [p.strip() for p in line.split(" | ")]
        if len(parts) != 4 or not URL_RE.match(parts[3]):
            raise ContentError(f"{where}: source {n} must be 'Title | Publisher | YYYY-MM-DD | URL'")
        out.append({"n": n, "title": parts[0], "publisher": parts[1], "date": parts[2], "url": parts[3]})
    return out


def _retired(meta, where):
    for key in RETIRED_FIELDS:
        if key in meta:
            raise ContentError(f"{where}: remove {key!r}: plates are retired, and an article's lead image is "
                               f"described by {LEAD_IMAGE_FILE} beside its editions")


def reading_minutes(text, lang):
    plain = re.sub(r"[`*_>#|\[\]()-]", " ", text)
    if lang == "zh":
        units = len(re.findall(r"[㐀-鿿]", plain)) / 420 + len(re.findall(r"[A-Za-z]+", plain)) / 220
    else:
        units = len(plain.split()) / 220
    return max(1, round(units))


class Article:
    def __init__(self, slug, lang, meta, body, raw, path):
        self.slug, self.lang, self.meta, self.body, self.raw, self.path = slug, lang, meta, body, raw, path
        where = f"{path}"
        for key in TEXT_FIELDS:
            if isinstance(meta.get(key), list) and meta[key]:
                raise ContentError(f"{where}: {key} must be text, not a list (quote a value that starts with '[')")
        _retired(meta, where)
        self.title = meta.get("title") or ""
        self.dek = meta.get("dek") or ""
        self.kind = meta.get("kind") or ""
        if self.kind not in KINDS:
            raise ContentError(f"{where}: kind must be one of {KINDS}")
        if not self.title or not self.dek:
            raise ContentError(f"{where}: title and dek are required")
        topics = meta.get("topics") or []
        self.topics = topics if isinstance(topics, list) else [topics]
        # Stack layer ids, put in stack order (T7 first) by load(). None when the field
        # is absent, so lists fall back to the layers of the primary topic; [] names none.
        layers = meta.get("layers")
        self.layers = None
        if layers is not None:
            layers = list(layers) if isinstance(layers, list) else [layers]
            if len(layers) > MAX_LAYERS:
                raise ContentError(f"{where}: layers names at most {MAX_LAYERS} stack layers, not {len(layers)}")
            if len(set(layers)) < len(layers):
                raise ContentError(f"{where}: layers names a layer twice")
            self.layers = layers
        self.needs = meta.get("needs") or ""  # guides: what a reader needs before starting
        self.event_date = _date(meta.get("event_date"), where)
        self.published = _date(meta.get("published"), where)
        if not self.published:
            raise ContentError(f"{where}: published date is required")
        self.updated = _date(meta.get("updated"), where)
        self.sources = _sources(meta.get("sources"), where)
        self.featured = str(meta.get("featured", "")).lower() in ("true", "yes", "1")
        self.lead = str(meta.get("lead", "")).lower() in ("true", "yes", "1")
        # the byline: a person's name, or the id of an AI agent (load() checks both)
        self.author = meta.get("author") or ""
        self.submitted_by = meta.get("submitted_by") or ""
        self.agent = meta.get("agent") or ""
        self.caption = meta.get("caption") or ""
        self.disclosure = meta.get("disclosure") or ""
        self.disclosure_lang = lang  # "en" on a Chinese page that still shows the English disclosure
        related = meta.get("related") or []
        self.related = related if isinstance(related, list) else [related]
        self.draft = str(meta.get("draft", "")).lower() in ("true", "yes", "1")
        evidence = meta.get("evidence") or []
        self.evidence = evidence if isinstance(evidence, list) else [evidence]
        self.changes = []
        for n, line in enumerate(meta.get("changes") or [], 1):
            date, _, note = line.partition(" | ")
            self.changes.append({"date": _date(date.strip(), where), "note": note.strip()})
            if not note.strip():
                raise ContentError(f"{where}: change {n} must be 'YYYY-MM-DD | note'")
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.minutes = reading_minutes(body, lang)
        self.html = ""
        self.headings = []
        self.art = ""
        self.art_hash = ""
        # the lead image from illustration.json, shared by both editions (load() sets it)
        self.lead_image = None

    @property
    def sort_key(self):
        return (self.published, self.event_date or self.published, self.slug)

    @property
    def primary_topic(self):
        return self.topics[0] if self.topics else ""


class Page:
    def __init__(self, name, lang, meta, body, raw, path):
        self.name, self.lang, self.meta, self.body, self.raw, self.path = name, lang, meta, body, raw, path
        _retired(meta, str(path))
        self.title = meta.get("title") or name
        self.dek = meta.get("dek") or ""
        self.published = _date(meta.get("published"), str(path))
        self.updated = _date(meta.get("updated"), str(path))
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.html = ""
        self.headings = []


class MediaFile:
    """One file of a lead image in static/media/: its name, where the build publishes it
    (src), its size in pixels, its bytes as loaded and their SHA-256."""

    def __init__(self, file_name, raw, width, height):
        self.file, self.raw, self.width, self.height = file_name, raw, width, height
        self.src = MEDIA_URL + file_name
        self.sha256 = hashlib.sha256(raw).hexdigest()


class LeadImage:
    """An article's lead image, from content/articles/<slug>/illustration.json.

    kind is "illustration" (drawn by tools/illustrate.py into static/media/<slug>.svg)
    or "photo". alt and caption are {"en": ..., "zh": ...} texts. spec_raw and raw are
    the bytes of the spec and of the image as loaded: the build publishes the spec at
    spec_path and the image at src, and lists both digests in the manifest. A photo also
    has its copies (variants: "list", "thumb" and "social", each a MediaFile), which the
    build publishes and lists beside it (published())."""

    def __init__(self, slug, kind, spec, spec_raw, file_name, raw, width, height, variants=None, cropped=False,
                 note_changes=False):
        self.slug, self.kind, self.spec = slug, kind, spec
        self.alt, self.caption = spec["alt"], spec["caption"]
        self.spec_raw, self.raw = spec_raw, raw
        self.spec_sha256 = hashlib.sha256(spec_raw).hexdigest()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self.file = file_name  # the file name in static/media/
        self.src = MEDIA_URL + file_name  # where the build publishes it
        self.spec_path = f"/articles/{slug}/{LEAD_IMAGE_FILE}"
        self.width, self.height = width, height
        # a photo's credit line; an illustration's is the site's standard one (strings.json)
        self.credit = spec.get("credit")
        self.license = spec.get("license")
        self.license_url = spec.get("license_url")
        self.source_url = spec.get("source_url")
        self.retrieved = spec.get("retrieved")
        # a photo's copies, by PHOTO_VARIANTS name; whether its crop leaves out part of the
        # source; and whether its license asks that changes be indicated, so that the credit
        # line says how the photo was changed
        self.variants = dict(variants or {})
        self.cropped, self.note_changes = cropped, note_changes

    def published(self):
        """The files the build publishes under /assets/media/ and the manifest lists, each
        with file, src, raw, sha256, width and height: the image, then a photo's copies."""
        return [self] + [self.variants[name] for name in PHOTO_VARIANTS if name in self.variants]

    def files(self):
        """The names in static/media/ of the image and its copies."""
        return [f.file for f in self.published()]


def _svg_value(value, where, what):
    """Check one attribute value as the browser reads it (character references already
    decoded by the parser): no CSS escapes, url() only to "#id", and no CSS function but
    a colour or a transform, so no value can reach outside the file."""
    if "\\" in value:
        raise ContentError(f"{where}: {what} carries a backslash; CSS escapes are not allowed")
    for found in SVG_FUNCTION_RE.finditer(value):
        name = found.group(1).lower()
        if name not in SVG_FUNCTIONS:
            raise ContentError(f"{where}: {what} uses {found.group(1)}(); only url(#id), colours and transforms "
                               "are allowed")
        if name == "url" and not SVG_LOCAL_URL_RE.match(value, found.end()):
            raise ContentError(f"{where}: {what} has a url() outside the file ({value[:60]!r}); only url(#id) is "
                               "allowed")


def _svg_size(raw, where):
    """Check an illustration's SVG against the allowlist above and return its (width,
    height) in pixels."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ContentError(f"{where}: an illustration is UTF-8 text") from None
    if text.startswith("\ufeff"):
        raise ContentError(f"{where}: an illustration is UTF-8 text without a byte-order mark")
    if SVG_CONTROL_RE.search(text):
        raise ContentError(f"{where}: an illustration may not contain control characters")
    declaration = SVG_DECLARATION_RE.match(text)
    body = text[declaration.end():] if declaration else text
    if "<?" in body:
        raise ContentError(f"{where}: an illustration may not carry processing instructions (such as "
                           "<?xml-stylesheet?>); only a leading <?xml version=\"1.0\" encoding=\"UTF-8\"?> declaration")
    if "<!" in body:
        raise ContentError(f"{where}: an illustration may not declare a DOCTYPE or entities, or carry comments or "
                           "CDATA sections")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ContentError(f"{where}: not well-formed SVG ({exc})") from exc
    if root.tag != f"{{{SVG_NS}}}svg":
        raise ContentError(f"{where}: the root element must be <svg> in the SVG namespace ({SVG_NS}), not "
                           f"{root.tag!r}")
    for el in root.iter():
        namespace, _, name = el.tag[1:].partition("}") if el.tag.startswith("{") else ("", "", el.tag)
        if namespace != SVG_NS or name not in SVG_ELEMENTS:
            raise ContentError(f"{where}: an illustration may not contain <{name}>; it may use only shapes, groups, "
                               "gradients, filters, clip paths and masks in the SVG namespace (SVG_ELEMENTS in "
                               "sitegen/content.py)")
        if name not in ("title", "desc") and (el.text or "").strip():
            raise ContentError(f"{where}: <{name}> carries text; an illustration has no words")
        if (el.tail or "").strip():
            raise ContentError(f"{where}: text after <{name}>; an illustration has no words")
        for attr, value in el.attrib.items():
            if attr.startswith("{") and attr not in SVG_NS_ATTRS:
                raise ContentError(f"{where}: <{name}> has the attribute {attr!r}; the only namespaced attributes "
                                   "allowed are xlink:href, xml:space and xml:lang")
            local = attr.rsplit("}", 1)[-1]
            if local.lower().startswith("on"):
                raise ContentError(f"{where}: <{name}> has an event handler ({local})")
            if local == "style":
                raise ContentError(f"{where}: <{name}> has a style attribute; use presentation attributes "
                                   "(fill, stroke, opacity ...)")
            if local == "href" and not SVG_LOCAL_HREF_RE.match(value):
                raise ContentError(f"{where}: <{name}> links outside the file ({value[:60]!r}); only '#id' is allowed")
            _svg_value(value, where, f"<{name} {local}>")
    try:
        size = (int(root.get("width", "")), int(root.get("height", "")))
    except ValueError:
        size = None
    try:
        view = tuple(float(v) for v in re.split(r"[\s,]+", root.get("viewBox", "").strip()))
    except ValueError:
        view = None
    if size != ILLUSTRATION_SIZE or view != (0, 0) + ILLUSTRATION_SIZE:
        width, height = ILLUSTRATION_SIZE
        raise ContentError(f'{where}: an illustration is drawn at width="{width}" height="{height}" with '
                           f'viewBox="0 0 {width} {height}", not width={root.get("width")!r} '
                           f'height={root.get("height")!r} viewBox={root.get("viewBox")!r}')
    return size


def _lead_image(root, folder):
    """Read and check content/articles/<slug>/illustration.json and the image it names.
    Returns a LeadImage, or None when the article has no spec."""
    path = folder / LEAD_IMAGE_FILE
    if not path.is_file():
        return None
    slug = folder.name
    where = f"content/articles/{slug}/{LEAD_IMAGE_FILE}"
    spec_raw, spec = _data(path)
    _obj(spec, where)
    kind = spec.get("kind")
    if kind not in LEAD_IMAGE_KINDS:
        raise ContentError(f"{where}: kind must be one of {', '.join(LEAD_IMAGE_KINDS)}, not {kind!r}")
    allowed = LEAD_IMAGE_KEYS[kind]
    extra = sorted(set(spec) - set(allowed))
    if extra:
        article = "an" if kind[0] in "aeiou" else "a"
        raise ContentError(f"{where}: unknown field {extra[0]!r}; {article} {kind} has {', '.join(allowed)}")
    missing = [key for key in allowed if key not in spec]
    if missing:
        raise ContentError(f"{where}: {missing[0]} is missing")
    for key in ("alt", "caption"):
        _text(spec[key], f"{where}: {key}")
    if kind == "photo":
        return _photo(root, slug, spec, spec_raw, where)
    _obj(spec["scene"], f"{where}: scene")
    digest, file_name = spec["svg_sha256"], f"{slug}.svg"
    run = "run python3 tools/illustrate.py --write " + slug
    if not isinstance(digest, str) or not HEX64_RE.match(digest):
        raise ContentError(f"{where}: svg_sha256 must be 64 lowercase hex digits; {run}")
    image = Path(root) / MEDIA_DIR / file_name
    rel = (MEDIA_DIR / file_name).as_posix()
    if not image.is_file():
        raise ContentError(f"{where}: {rel} is missing; {run}")
    raw = image.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ContentError(f"{where}: svg_sha256 does not match {rel}; {run}")
    try:
        width, height = _svg_size(raw, rel)
    except ContentError as exc:
        raise ContentError(f"{where}: {exc}; the generator draws a picture that passes: {run}") from None
    return LeadImage(slug, kind, spec, spec_raw, file_name, raw, width, height)


def photo_license(value, url, where):
    """Whether a photo's license (one of PHOTO_LICENSES, by its English name) asks that changes
    be indicated. Stops with a ContentError on a license a photo may not carry, or on a
    license_url that is not that license's address."""
    name = (value.get("en") if isinstance(value, dict) else value) or ""
    for pattern, address, note_changes in PHOTO_LICENSES:
        found = pattern.match(name.strip())
        if not found:
            continue
        if address:
            want = address.format(*found.groups())
            bare = re.sub(r"^https?://(?:www\.)?", "", url if isinstance(url, str) else "")
            if not bare.startswith(want) or bare[len(want):len(want) + 1] not in ("", "/", "?", "#"):
                raise ContentError(f"{where}: license_url must be the address of {name.strip()}, https://{want}/, "
                                   f"not {url!r}")
        return note_changes
    raise ContentError(f"{where}: a photo may carry a public domain, CC0, CC BY or CC BY-SA license (such as "
                       f"\"CC BY-SA 4.0\"), the Unsplash License or the Pexels License, not {name!r} "
                       "(CONTENT_GUIDE.md, \"Photos\")")


def _keys(value, allowed, where):
    """An object with exactly the keys ALLOWED: the first unknown or missing one stops the load."""
    _obj(value, where)
    extra = sorted(set(value) - set(allowed))
    if extra:
        raise ContentError(f"{where}: unknown field {extra[0]!r}; it has {', '.join(allowed)}")
    missing = [key for key in allowed if key not in value]
    if missing:
        raise ContentError(f"{where}: {missing[0]} is missing")
    return value


def _ints(value, n):
    """Whether VALUE is a list of N whole numbers (true and false are not numbers here)."""
    return (isinstance(value, list) and len(value) == n
            and all(isinstance(v, int) and not isinstance(v, bool) for v in value))


def _photo_file(entry, where, root, run):
    """Check one file of a photo, the photo itself or a copy ({"file", "width", "height",
    "sha256", ...}), against its bytes in static/media/, and return it as a MediaFile. The page
    reserves each picture's box from width and height, and the build publishes the file under
    its extension, so both must be true of the bytes."""
    file_name = entry["file"]
    if not isinstance(file_name, str) or not PHOTO_FILE_RE.match(file_name):
        raise ContentError(f"{where}: file must be a lowercase file name in static/media/ ending in .jpg, .jpeg, "
                           f".png or .webp, not {file_name!r}")
    for key in ("width", "height"):
        if isinstance(entry[key], bool) or not isinstance(entry[key], int) or entry[key] <= 0:
            raise ContentError(f"{where}: {key} must be a positive whole number of pixels")
    digest = entry["sha256"]
    if not isinstance(digest, str) or not HEX64_RE.match(digest):
        raise ContentError(f"{where}: sha256 must be 64 lowercase hex digits; {run}")
    image = Path(root) / MEDIA_DIR / file_name
    rel = (MEDIA_DIR / file_name).as_posix()
    if not image.is_file():
        raise ContentError(f"{where}: {rel} is missing; {run}")
    raw = image.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ContentError(f"{where}: sha256 does not match {rel}; {run}")
    width, height = entry["width"], entry["height"]
    kind_name = PHOTO_TYPES[file_name.rsplit(".", 1)[1]]
    actual = _raster_size(raw, kind_name)
    if actual is None:
        raise ContentError(f"{where}: {rel} is not a {kind_name} file, as its name says")
    if actual != (width, height):
        raise ContentError(f"{where}: width and height say {width} x {height} pixels, but {rel} is "
                           f"{actual[0]} x {actual[1]}")
    return MediaFile(file_name, raw, width, height)


def _photo(root, slug, spec, spec_raw, where):
    """The rest of a photo spec (_lead_image() has checked its keys, alt and caption): the
    credit, the license and the source, then the photo, its copies and its edits."""
    run = f"tools/photos.py --write {slug} writes the files and their digests (CONTENT_GUIDE.md, \"Photos\")"
    _name(spec["credit"], f"{where}: credit")
    _name(spec["license"], f"{where}: license")
    for key in ("license_url", "source_url"):
        if not isinstance(spec[key], str) or not URL_RE.match(spec[key]):
            raise ContentError(f"{where}: {key} must be an http(s) URL")
    note_changes = photo_license(spec["license"], spec["license_url"], f"{where}: license")
    _when(spec["retrieved"], f"{where}: retrieved", full=True)
    variants = _keys(spec["variants"], PHOTO_VARIANTS, f"{where}: variants")
    for name in PHOTO_VARIANTS:
        _keys(variants[name], PHOTO_FILE_KEYS, f"{where}: variants.{name}")
    edits = _keys(spec["edits"], PHOTO_EDIT_KEYS, f"{where}: edits")
    photo = _photo_file(spec, where, root, run)
    copies = {name: _photo_file(variants[name], f"{where}: variants.{name}", root, run) for name in PHOTO_VARIANTS}
    names = [photo.file] + [copies[name].file for name in PHOTO_VARIANTS]
    if len(set(names)) < len(names):
        raise ContentError(f"{where}: the photo and its copies must be {len(names)} different files, not "
                           f"{', '.join(names)}")
    # srcset offers the smaller copies beside the photo and tells them apart by width: each is
    # narrower than the file before it (the photo, then the list copy) and within a pixel of
    # the photo's proportions
    wider, wider_name = photo, "photo"
    for name in PHOTO_SRCSET:
        small = copies[name]
        if small.width >= wider.width or abs(small.height * photo.width - small.width * photo.height) > photo.width:
            raise ContentError(f"{where}: variants.{name} is {small.width} x {small.height}; it must be narrower than "
                               f"the {wider.width} x {wider.height} {wider_name} and of the photo's proportions")
        wider, wider_name = small, f"{name} copy"
    social = copies["social"]
    if PHOTO_TYPES[social.file.rsplit(".", 1)[1]] not in PHOTO_SOCIAL_TYPES:
        raise ContentError(f"{where}: variants.social is a JPEG or PNG file, which every link preview reads, "
                           f"not {social.file}")
    if (social.width, social.height) != PHOTO_SOCIAL_SIZE:
        raise ContentError(f"{where}: variants.social is {PHOTO_SOCIAL_SIZE[0]} x {PHOTO_SOCIAL_SIZE[1]} pixels, the "
                           f"social cards' size, not {social.width} x {social.height}")
    cropped = _photo_edits(edits, (photo.width, photo.height), f"{where}: edits")
    return LeadImage(slug, "photo", spec, spec_raw, photo.file, photo.raw, photo.width, photo.height,
                     variants=copies, cropped=cropped, note_changes=note_changes)


def _photo_edits(edits, size, where):
    """Check a photo's edits (PHOTO_EDIT_KEYS) against the photo's SIZE, and return whether
    the photo was cropped: whether its box leaves out part of the source."""
    if not isinstance(edits["source_sha256"], str) or not HEX64_RE.match(edits["source_sha256"]):
        raise ContentError(f"{where}: source_sha256 must be 64 lowercase hex digits")
    source = edits["source_size"]
    if not _ints(source, 2) or min(source) <= 0:
        raise ContentError(f"{where}: source_size must be [width, height] in pixels")
    boxes = {}
    for key, target in (("crop", size), ("social_crop", PHOTO_SOCIAL_SIZE)):
        x, y, w, h = box = edits[key] if _ints(edits[key], 4) else (-1, -1, 0, 0)
        if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > source[0] or y + h > source[1]:
            raise ContentError(f"{where}: {key} must be [x, y, width, height] inside the {source[0]} x {source[1]} "
                               "source")
        if w < target[0]:
            raise ContentError(f"{where}: {key} is {w} pixels wide, narrower than the {target[0]}-pixel file made "
                               "from it; a photo is never enlarged")
        if abs(w * target[1] - h * target[0]) > 0.01 * w * target[1]:
            raise ContentError(f"{where}: {key} is {w} x {h}, not of the proportions of the {target[0]} x "
                               f"{target[1]} file made from it")
        boxes[key] = list(box)
    (cx, cy, cw, ch), (sx, sy, sw, sh) = boxes["crop"], boxes["social_crop"]
    if sx < cx or sy < cy or sx + sw > cx + cw or sy + sh > cy + ch:
        raise ContentError(f"{where}: social_crop must lie inside crop, so that a link preview shows part of the "
                           "photo")
    if edits["grade"] not in PHOTO_GRADES:
        raise ContentError(f"{where}: grade must be one of {', '.join(PHOTO_GRADES)} (tools/photos.py), not "
                           f"{edits['grade']!r}")
    return boxes["crop"] != [0, 0, source[0], source[1]]


def _raster_size(raw, kind_name):
    """(width, height) in pixels of a photo as browsers show it, read from the header of a
    file of type KIND_NAME ("PNG", "JPEG" or "WebP"); None when the bytes are not that type
    or the header cannot be read."""
    if kind_name == "PNG":
        if len(raw) < 24 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            return None
        return int.from_bytes(raw[16:20], "big"), int.from_bytes(raw[20:24], "big")
    if kind_name == "WebP":
        if len(raw) < 30 or raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
            return None
        chunk = raw[12:16]
        if chunk == b"VP8 " and raw[23:26] == b"\x9d\x01\x2a":   # lossy: 14-bit sizes after the start code
            return int.from_bytes(raw[26:28], "little") & 0x3FFF, int.from_bytes(raw[28:30], "little") & 0x3FFF
        if chunk == b"VP8L" and raw[20] == 0x2F:                   # lossless: 14 bits each, minus one
            bits = int.from_bytes(raw[21:25], "little")
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":                                         # extended: the canvas, 24 bits each, minus one
            return int.from_bytes(raw[24:27], "little") + 1, int.from_bytes(raw[27:30], "little") + 1
        return None
    if kind_name == "JPEG":
        if raw[:3] != b"\xff\xd8\xff":
            return None
        i, orientation = 2, 1
        while i + 4 <= len(raw):
            if raw[i] != 0xFF:
                return None
            marker = raw[i + 1]
            if marker == 0xFF:                                       # a fill byte
                i += 1
                continue
            if marker in (0x01, 0xD8) or 0xD0 <= marker <= 0xD7:   # no length field
                i += 2
                continue
            if marker in (0xD9, 0xDA):                               # the end, or the scan, before a frame header
                return None
            length = int.from_bytes(raw[i + 2:i + 4], "big")
            segment = raw[i + 4:i + 2 + length]
            if length < 2 or len(segment) != length - 2:
                return None
            if marker == 0xE1 and segment[:6] == b"Exif\x00\x00":
                orientation = _exif_orientation(segment[6:])
            if marker in JPEG_SOF:
                if len(segment) < 5:
                    return None
                height, width = int.from_bytes(segment[1:3], "big"), int.from_bytes(segment[3:5], "big")
                # browsers turn the picture as its EXIF orientation says: 5 to 8 swap the sides
                return (height, width) if orientation in (5, 6, 7, 8) else (width, height)
            i += 2 + length
    return None


def _exif_orientation(tiff):
    """The Orientation tag (0x0112) of an EXIF block's first image directory, or 1."""
    order = {b"II*\x00": "little", b"MM\x00*": "big"}.get(tiff[:4])
    if order is None or len(tiff) < 8:
        return 1
    ifd = int.from_bytes(tiff[4:8], order)
    count = int.from_bytes(tiff[ifd:ifd + 2], order) if ifd + 2 <= len(tiff) else 0
    for k in range(count):
        entry = ifd + 2 + 12 * k
        if entry + 12 > len(tiff):
            break
        if int.from_bytes(tiff[entry:entry + 2], order) == 0x0112:
            return int.from_bytes(tiff[entry + 8:entry + 10], order)
    return 1


def _read(path):
    raw = path.read_bytes()
    try:
        meta, body = md.parse_front_matter(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ContentError(f"{path}: {exc}") from exc
    return raw, meta, body


def _data(path):
    """A JSON data file as (bytes, parsed); the same bytes are hashed and published."""
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise ContentError(f"{path}: missing (content.DATA_FILES lists it)") from exc
    try:
        return raw, json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ContentError(f"{path}: {exc}") from exc


def _unique(items, where):
    ids = [item.get("id") for item in items]
    for item_id in ids:
        if not isinstance(item_id, str) or not ID_RE.match(item_id):
            raise ContentError(f"{where}: id {item_id!r} must start with a letter and use letters, digits, '-', '_' or '.'")
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise ContentError(f"{where}: duplicate id {dupes[0]!r}")


# ----- checks for the data files ---------------------------------------------
# Each takes "where", the file and field path printed in the error, such as
# "content/tee.json: limits.ddrop.access".

def _obj(value, where):
    if not isinstance(value, dict):
        raise ContentError(f"{where}: must be an object")
    return value


def _list(value, where, min_len=0, max_len=None):
    if not isinstance(value, list):
        raise ContentError(f"{where}: must be a list")
    if len(value) < min_len:
        raise ContentError(f"{where}: needs at least {min_len} {'entry' if min_len == 1 else 'entries'}")
    if max_len is not None and len(value) > max_len:
        raise ContentError(f"{where}: has {len(value)} entries; at most {max_len} are allowed")
    return value


def _objs(value, where, min_len=0):
    """A list of objects, such as the rows of a tracker."""
    items = _list(value, where, min_len)
    for n, item in enumerate(items, 1):
        _obj(item, f"{where}[{n}]")
    return items


def _text(value, where, empty=False):
    """A {"en": ..., "zh": ...} text with both languages filled in.

    empty=True also accepts a text left blank in both languages ("", null or two
    empty strings): an optional field, or a platform cell not yet covered. A text
    filled in one language only is always an error."""
    if empty and value in (None, ""):
        return
    if not isinstance(value, dict) or not all(isinstance(value.get(lang), str) for lang in LANGS):
        raise ContentError(f'{where}: must be {{"en": "...", "zh": "..."}}')
    blank = [lang for lang in LANGS if not value[lang].strip()]
    if blank and not (empty and len(blank) == len(LANGS)):
        raise ContentError(f"{where}: the {' and '.join(blank)} text is empty")


def _name(value, where):
    """A name: one string for both languages (such as "Intel TDX"), or an {en, zh} text."""
    if not (isinstance(value, str) and value.strip()):
        _text(value, where)


def _flag(value, where):
    if not isinstance(value, bool):
        raise ContentError(f"{where}: must be true or false")


def _ids(values, known, where, what, min_len=0, max_len=None):
    """A list of ids that must all be known, each named once."""
    values = _list(values, where, min_len, max_len)
    for value in values:
        if not isinstance(value, str) or value not in known:
            raise ContentError(f"{where}: unknown {what} {value!r}")
    if len(set(values)) < len(values):
        raise ContentError(f"{where}: names the same {what} twice")
    return values


def _id(value, known, where, what):
    if not isinstance(value, str) or value not in known:
        raise ContentError(f"{where}: unknown {what} {value!r}")


def _when(value, where, full=False, empty=False):
    """A date in a source-date form: YYYY-MM-DD, or also YYYY-MM or YYYY unless full=True.
    Returns its range of days as (first, last), or None for an allowed empty value."""
    if empty and value in (None, ""):
        return None
    m = DATE_RE.match(value) if isinstance(value, str) else None
    if not m or (full and not m.group(3)):
        raise ContentError(f"{where}: date {value!r} must be YYYY-MM-DD" + ("" if full else ", YYYY-MM or YYYY"))
    year, month, day = int(m.group(1)), m.group(2), m.group(3)
    try:
        if day:
            first = last = dt.date(year, int(month), int(day))
        elif month:
            first = dt.date(year, int(month), 1)
            last = dt.date(year + int(month) // 12, int(month) % 12 + 1, 1) - dt.timedelta(days=1)
        else:
            first, last = dt.date(year, 1, 1), dt.date(year, 12, 31)
    except ValueError as exc:
        raise ContentError(f"{where}: bad date {value!r}") from exc
    return first, last


def _source_refs(values, where, articles, resources, min_len=1):
    """Sources of a data row: "article:<slug>" for a published English article, or "resource:<id>"."""
    values = _list(values, where, min_len)
    for value in values:
        m = SOURCE_REF_RE.match(value) if isinstance(value, str) else None
        if not m:
            raise ContentError(f"{where}: source {value!r} must be 'article:<slug>' or 'resource:<id>'")
        kind, ref = m.groups()
        if kind == "article" and ref not in articles:
            raise ContentError(f"{where}: {value!r} names no published English article")
        if kind == "resource" and ref not in resources:
            raise ContentError(f"{where}: {value!r} names no entry in content/resources.json")
    if len(set(values)) < len(values):
        raise ContentError(f"{where}: lists the same source twice")


def _newest_first(rows, where):
    """Dated rows run newest first and undated rows come last. A partial date such as
    "2026" spans its year, so it may sit anywhere among the dates of that year."""
    oldest = None  # (last day, id) of the oldest dated row so far
    undated = None
    for row in rows:
        span = _when(row.get("date"), f"{where}.{row['id']}.date", empty=True)
        if span is None:
            undated = undated or row["id"]
            continue
        if undated:
            raise ContentError(f"{where}: {row['id']!r} is dated, so it must come before the undated {undated!r}")
        if oldest and span[0] > oldest[0]:
            raise ContentError(f"{where}: rows run newest first, but {row['id']!r} ({row['date']}) is newer than "
                               f"{oldest[1]!r}, which comes before it")
        if oldest is None or span[1] < oldest[0]:
            oldest = (span[1], row["id"])


def _no_plate(row, where):
    if "plate" in row:
        raise ContentError(f"{where}: remove 'plate': plates are retired, and only news briefs and other articles "
                           f"carry a lead image, from their {LEAD_IMAGE_FILE}")


def _check_stack(topics, topic_ids):
    """Check the stack's layers (T7 first) and return their ids in that order."""
    f = "content/topics.json"
    stack = _objs(topics.get("stack"), f"{f}: stack")
    _unique(stack, f"{f}: stack")
    if len(stack) != STACK_SIZE:
        raise ContentError(f"{f}: stack lists {len(stack)} layers, but the codes T7 to T1, the Latest filter and "
                           f"the stylesheet expect {STACK_SIZE}")
    for layer in stack:
        where = f"{f}: stack.{layer['id']}"
        if not SLUG_RE.match(layer["id"]):
            raise ContentError(f"{where}: layer ids are lowercase words joined by hyphens")
        _ids(layer.get("topics", []), topic_ids, f"{where}.topics", "topic")
        _check_hero(layer.get("hero"), f"{where}.hero")
        _check_checkers(layer.get("checkers"), f"{where}.checkers")
    return [layer["id"] for layer in stack]


def _check_hero(hero, where):
    """A stack layer's label beside the home hero: a short name, a line icon from
    sitegen/logos.py, and one to seven examples, each a vendor mark (a Simple Icons
    slug that sitegen/logos.py vendors), a name, or a mark followed by a name. A mark
    shown alone may carry "name", its accessible name and tooltip when the product is
    more specific than the mark's owner (the OpenAI mark for "OpenAI Codex"). Every
    other mark takes its owner's name from sitegen/logos.py, which must be one string
    or an {en, zh} text with both filled in (欧盟 for the European Union), so that each
    page names it in its own language."""
    hero = _obj(hero, where)
    _text(hero.get("short"), f"{where}.short")
    if hero.get("icon") not in logos.LAYER_ICONS:
        raise ContentError(f"{where}.icon must be one of {', '.join(logos.LAYER_ICONS)}, not {hero.get('icon')!r}")
    examples = _list(hero.get("examples"), f"{where}.examples", min_len=1, max_len=MAX_HERO_EXAMPLES)
    for n, example in enumerate(examples, 1):
        at = f"{where}.examples[{n}]"
        _obj(example, at)
        extra = sorted(set(example) - {"logo", "text", "name"})
        if extra or not (set(example) & {"logo", "text"}):
            raise ContentError(f"{at}: an example is a logo, a text or both" + (f", not {', '.join(extra)}" if extra else ""))
        if "name" in example:
            if "logo" not in example or "text" in example:
                raise ContentError(f"{at}.name: only a mark shown alone takes a name")
            _name(example["name"], f"{at}.name")
        if "logo" in example and example["logo"] not in logos.LOGOS:
            raise ContentError(f"{at}.logo: unknown mark {example['logo']!r}; sitegen/logos.py lists the marks")
        if "logo" in example and "name" not in example:
            _name(logos.LOGOS[example["logo"]].get("title"), f"{at}.logo: sitegen/logos.py's title for {example['logo']!r}")
        if "text" in example:
            _name(example["text"], f"{at}.text")


def _check_checkers(value, where):
    """A stack layer's "checkers": who outside the provider checks the layer's claim, in both languages."""
    _text(value, where)
    for lang, cap in MAX_CHECKERS.items():
        text = value[lang]
        if text != text.strip() or "\n" in text:
            raise ContentError(f"{where}: the {lang} text has a line break or surrounding spaces")
        if len(text) > cap:
            raise ContentError(f"{where}: the {lang} text has {len(text)} characters; the cap is {cap} "
                               "(about three lines in a layer card)")


def _check_tiers(tiers, layer_ids, topic_ids, articles):
    """Check content/tiers.json and return the tier ids."""
    f = "content/tiers.json"
    _obj(tiers, f)
    for key in ("order_note", "he_note"):
        _text(tiers.get(key), f"{f}: {key}")
    baseline = _obj(tiers.get("baseline"), f"{f}: baseline")
    for key in ("trust_name", "text"):
        _text(baseline.get(key), f"{f}: baseline.{key}")
    rows = _objs(tiers.get("tiers"), f"{f}: tiers", min_len=1)
    _unique(rows, f"{f}: tiers")
    for n, tier in enumerate(rows, 1):
        where = f"{f}: tiers.{tier['id']}"
        _no_plate(tier, where)
        if tier.get("n") != n or isinstance(tier.get("n"), bool):
            raise ContentError(f"{where}: n must be {n}, since tiers are numbered in file order from 1")
        for key in ("trust_name", "mechanism", "short", "approaches", "establishes", "not_established", "trust",
                    "hidden", "cost", "summary"):
            _text(tier.get(key), f"{where}.{key}")
        compared = [key for key in ("vs_tee", "focus") if tier.get(key) is not None]
        if len(compared) != 1:
            raise ContentError(f"{where}: set exactly one of vs_tee (how the tier compares with a TEE) and focus "
                               "(on the TEE tier, why it is the main subject)")
        _text(tier[compared[0]], f"{where}.{compared[0]}")
        _text(tier.get("combined"), f"{where}.combined", empty=True)
        _ids(tier.get("layers"), layer_ids, f"{where}.layers", "stack layer")
        _ids(tier.get("topics"), topic_ids, f"{where}.topics", "topic")
        _ids(tier.get("read"), articles, f"{where}.read", "published article", min_len=1, max_len=3)
    tier_ids = {tier["id"] for tier in rows}
    combos = _objs(tiers.get("combinations", []), f"{f}: combinations")
    _unique(combos, f"{f}: combinations")
    for combo in combos:
        where = f"{f}: combinations.{combo['id']}"
        _text(combo.get("name"), f"{where}.name")
        _text(combo.get("text"), f"{where}.text")
        _ids(combo.get("tiers"), tier_ids, f"{where}.tiers", "tier", min_len=2)
        _id(combo.get("article"), articles, f"{where}.article", "published article")
    return tier_ids


def _check_topic_lines(topics, tier_ids):
    """The stack's TEE line and other evidence, and the topics' tiers and TEE comparison."""
    f = "content/topics.json"
    direct_below = None  # a layer with direct TEE evidence, once one is seen going down from T7
    for layer in topics["stack"]:
        where = f"{f}: stack.{layer['id']}"
        tee = _obj(layer.get("tee"), f"{where}.tee")
        if tee.get("reach") not in REACHES:
            raise ContentError(f"{where}.tee.reach must be 'direct' or 'via', not {tee.get('reach')!r}")
        if tee["reach"] == "direct":
            direct_below = direct_below or layer["id"]
        elif direct_below:
            raise ContentError(f"{where}: a TEE gives direct evidence only at the lowest layers, so this 'via' layer "
                               f"cannot sit below the 'direct' layer {direct_below!r}")
        for key in ("short", "text"):
            _text(tee.get(key), f"{where}.tee.{key}")
        others = _objs(layer.get("others"), f"{where}.others")
        for n, other in enumerate(others, 1):
            _id(other.get("tier"), tier_ids, f"{where}.others[{n}].tier", "tier")
            _text(other.get("examples"), f"{where}.others[{n}].examples")
        _ids([other["tier"] for other in others], tier_ids, f"{where}.others", "tier")
        bind = layer.get("bind")
        if layer is topics["stack"][-1]:  # T1 has no layer below it
            if bind is not None:
                raise ContentError(f"{where}.bind: the lowest layer has no layer below to be bound to")
            continue
        bind = _obj(bind, f"{where}.bind")
        if bind.get("status") not in BIND_STATUSES:
            raise ContentError(f"{where}.bind.status must be one of {', '.join(BIND_STATUSES)}, not {bind.get('status')!r}")
        _text(bind.get("text"), f"{where}.bind.text")
    for topic in topics["topics"]:
        where = f"{f}: topics.{topic['id']}"
        _no_plate(topic, where)
        _ids(topic.get("tiers"), tier_ids, f"{where}.tiers", "tier", min_len=1)
        if topic["id"] != TEE_TOPIC:  # the TEE hub has no "How this compares with a TEE" callout
            _text(topic.get("tee_relation"), f"{where}.tee_relation")


def _check_resources(resources, resource_ids):
    """The TEE areas of confidential-computing entries, and the reading paths."""
    f = "content/resources.json"
    for res in resources["resources"]:
        area = res.get("tee_area")
        if TEE_TOPIC in res.get("topics", []):
            if area not in TEE_AREAS:
                problem = "needs a tee_area" if area is None else f"has the unknown tee_area {area!r}"
                raise ContentError(f"{f}: {res['id']}: this {TEE_TOPIC} entry {problem}; use one of "
                                   f"{', '.join(TEE_AREAS)}")
        elif area is not None:
            raise ContentError(f"{f}: {res['id']}: tee_area is only for entries whose topics include {TEE_TOPIC}")
    paths = _objs(resources.get("paths"), f"{f}: paths", min_len=1)
    _unique(paths, f"{f}: paths")
    for path in paths:
        where = f"{f}: paths.{path['id']}"
        _no_plate(path, where)
        for key in ("title", "purpose"):
            _text(path.get(key), f"{where}.{key}")
        entries = _objs(path.get("entries"), f"{where}.entries", min_len=1)
        for n, entry in enumerate(entries, 1):
            _id(entry.get("id"), resource_ids, f"{where}.entries[{n}].id", "resource")
            _text(entry.get("why"), f"{where}.entries[{n}].why")
        _ids([entry["id"] for entry in entries], resource_ids, f"{where}.entries", "resource")


def _check_tee(tee, articles, resource_ids, term_ids):
    """Check content/tee.json, the data of the TEE hub."""
    f = "content/tee.json"
    _obj(tee, f)

    def refs(values, where, min_len=1):
        _source_refs(values, where, articles, resource_ids, min_len)

    _when(tee.get("reviewed"), f"{f}: reviewed", full=True)
    est = _obj(tee.get("establishes"), f"{f}: establishes")
    for key in ("shows", "still"):
        for n, item in enumerate(_list(est.get(key), f"{f}: establishes.{key}", min_len=1), 1):
            _text(item, f"{f}: establishes.{key}[{n}]")
    _text(est.get("boundary"), f"{f}: establishes.boundary")

    steps = _objs(tee.get("path"), f"{f}: path", min_len=1)
    for n, step in enumerate(steps, 1):
        where = f"{f}: path[{n}]"
        _no_plate(step, where)
        if ("article" in step) == ("planned" in step):
            raise ContentError(f"{where}: give either article (the slug of a published step) or planned "
                               "(the title of a planned one)")
        if "article" in step:
            _id(step["article"], articles, f"{where}.article", "published article")
            _text(step.get("outcome"), f"{where}.outcome")
        else:
            _text(step["planned"], f"{where}.planned")
            _text(step.get("outcome"), f"{where}.outcome", empty=True)
    _ids([s["article"] for s in steps if "article" in s], articles, f"{f}: path", "published article")

    platforms = _objs(tee.get("platforms"), f"{f}: platforms", min_len=1)
    _unique(platforms, f"{f}: platforms")
    for p in platforms:
        where = f"{f}: platforms.{p['id']}"
        if p.get("group") not in PLATFORM_GROUPS:
            raise ContentError(f"{where}.group must be 'cpu' or 'gpu', not {p.get('group')!r}")
        _name(p.get("name"), f"{where}.name")
        for key in ("isolates", "signs", "reference_values", "out_of_scope"):
            _text(p.get(key), f"{where}.{key}", empty=True)  # a blank cell reads "Not yet covered here"
        refs(p.get("sources"), f"{where}.sources")
    note = tee.get("gpu_note")  # a text, or {"text": {...}, "sources": [...]}
    if isinstance(note, dict) and "text" in note:
        _text(note["text"], f"{f}: gpu_note.text")
    else:
        _text(note, f"{f}: gpu_note")
    if isinstance(note, dict) and "sources" in note:
        refs(note["sources"], f"{f}: gpu_note.sources", min_len=0)

    services = _objs(tee.get("services"), f"{f}: services", min_len=1)
    _unique(services, f"{f}: services")
    for svc in services:
        where = f"{f}: services.{svc['id']}"
        _name(svc.get("name"), f"{where}.name")
        for key in ("record", "checker", "inspection"):
            _text(svc.get(key), f"{where}.{key}")
        _when(svc.get("as_of"), f"{where}.as_of", full=True)
        refs(svc.get("sources"), f"{where}.sources")

    limits = _objs(tee.get("limits"), f"{f}: limits", min_len=1)
    _unique(limits, f"{f}: limits")
    for lim in limits:
        where = f"{f}: limits.{lim['id']}"
        _name(lim.get("name"), f"{where}.name")
        _flag(lim.get("physical"), f"{where}.physical")
        if lim.get("editor") is not None:  # true prints "The editor co-authored this work."
            _flag(lim["editor"], f"{where}.editor")
        _text(lim.get("defeated"), f"{where}.defeated")
        for key in ("access", "vendor", "status"):
            _text(lim.get(key), f"{where}.{key}", empty=True)
        refs(lim.get("sources"), f"{where}.sources")
    _newest_first(limits, f"{f}: limits")

    responses = _objs(tee.get("responses", []), f"{f}: responses")
    _unique(responses, f"{f}: responses")
    for resp in responses:
        where = f"{f}: responses.{resp['id']}"
        _when(resp.get("date"), f"{where}.date", empty=True)
        _name(resp.get("name"), f"{where}.name")
        _text(resp.get("text"), f"{where}.text")
        refs(resp.get("sources"), f"{where}.sources")
    for kind, rows in (("platforms", platforms), ("limits", limits), ("responses", responses)):
        for row in rows:  # services must carry as_of (checked above); other rows may
            if "as_of" in row:
                _when(row["as_of"], f"{f}: {kind}.{row['id']}.as_of", full=True)
    # the rows share one page, where an id may become an anchor
    _unique(platforms + services + limits + responses, f"{f}: platforms, services, limits and responses")

    for key in ("terms", "learn_terms"):
        _ids(tee.get(key), term_ids, f"{f}: {key}", "glossary term", min_len=1)


def _check_lead_images(site, articles):
    """content/site.json "lead_image_kinds": the article kinds whose every published
    article needs an illustration.json (the list may be empty). A draft, which a
    --drafts preview includes, may still lack one."""
    kinds = site.get("lead_image_kinds", [])
    where = "content/site.json: lead_image_kinds"
    if not isinstance(kinds, list) or any(k not in KINDS for k in kinds) or len(set(kinds)) < len(kinds):
        raise ContentError(f"{where} must list article kinds from {', '.join(KINDS)}, each once, not {kinds!r}")
    missing = [a.slug for a in articles if a.kind in kinds and a.lead_image is None and not a.draft]
    if missing:
        more = f" and {len(missing) - 1} more" if len(missing) > 1 else ""
        raise ContentError(f"content/articles/{missing[0]}/{LEAD_IMAGE_FILE} is missing{more}: {where} says every "
                           f"{' and '.join(kinds)} article needs a lead image; make one with python3 tools/photos.py "
                           "--write (a photo) or python3 tools/illustrate.py --write (an illustration)")


def unused_media(root, named):
    """The files in static/media/ that no lead image names (NAMED: the file names that every
    spec names, drafts' included), leaving out dotfiles such as .gitkeep. Such a file is a
    picture left behind when a spec changed or went; the build does not publish it."""
    media = Path(root) / MEDIA_DIR
    if not media.is_dir():
        return []
    return sorted(p.name for p in media.iterdir() if p.is_file() and not p.name.startswith(".") and p.name not in named)


def _check_agents(site):
    """content/site.json "agents": the AI agents a byline may name, by id. Each has a name
    (one string for both languages, or an {en, zh} text) and a one-sentence description in
    both languages, which the article page shows beside the byline. Returns the registry
    ({} when site.json lists none)."""
    where = "content/site.json: agents"
    agents = _obj(site.get("agents", {}), where)
    for agent_id, entry in agents.items():
        at = f"{where}.{agent_id}"
        if not SLUG_RE.match(agent_id):
            raise ContentError(f"{at}: an agent id is lowercase words joined by hyphens, such as 'daily'")
        _obj(entry, at)
        extra = sorted(set(entry) - set(AGENT_KEYS))
        if extra:
            raise ContentError(f"{at}: unknown field {extra[0]!r}; an agent has {' and '.join(AGENT_KEYS)}")
        _name(entry.get("name"), f"{at}.name")
        _text(entry.get("description"), f"{at}.description")
    return agents


def _not_people(site, agents):
    """Names a person's byline may not use, casefolded: the publication's own names, and the
    ids and names of the AI agents. The structured data turn author into a Person, so a
    byline written as author="verifiable.pro" would invent one."""
    names = {site.get("domain", ""), site.get("alternate_name", "")}
    for agent_id, entry in agents.items():
        name = entry["name"]
        names |= {agent_id, *(name.values() if isinstance(name, dict) else [name])}
    return {" ".join(str(n).split()).casefold() for n in names if n}


def _check_byline(a, agents, not_people, en=None):
    """One edition's byline (see AGENT_KEYS above). EN is the English edition when A is the
    Chinese one, whose byline comes from en.md: it may give a name in its Chinese form, but
    it names the same agent and credits a submitter exactly when en.md does."""
    where = str(a.path)
    if a.author and a.agent:
        raise ContentError(f"{where}: set author or agent, not both: author names the person who wrote the article, "
                           "agent the AI agent that drafted it")
    if not (a.author or a.agent):
        known = ", ".join(sorted(agents)) or "none yet"
        raise ContentError(f"{where}: the byline is missing: set author to the name of the person who wrote the "
                           f"article, or agent to the id of the AI agent that drafted it (content/site.json agents: "
                           f"{known})")
    if a.agent and a.agent not in agents:
        known = ", ".join(sorted(agents)) or "none"
        raise ContentError(f"{where}: unknown agent {a.agent!r}; content/site.json agents lists {known}")
    names = {key: " ".join(getattr(a, key).split()) for key in ("author", "submitted_by")}
    for key, value in names.items():
        if value.casefold() in not_people:
            raise ContentError(f"{where}: {key} is {value!r}, which is not a person's name; an article an AI agent "
                               "drafted sets agent instead")
    if names["submitted_by"] and names["submitted_by"].casefold() == names["author"].casefold():
        raise ContentError(f"{where}: submitted_by repeats author; leave it out when the author submitted the story")
    if en is not None:
        if a.agent != en.agent:
            raise ContentError(f"{where}: agent differs from en.md ({en.agent or 'none'}); zh.md takes the byline "
                               "from en.md, so leave agent out")
        if bool(a.submitted_by) != bool(en.submitted_by):
            raise ContentError(f"{where}: submitted_by is set in one edition only; write it in en.md, which zh.md "
                               "takes it from (zh.md may give the name in its Chinese form)")


def load(root, drafts=False):
    root = Path(root)
    content = root / "content"
    site = _json(content / "site.json")
    strings = _json(content / "strings.json")
    raw_data, parsed = {}, {}
    for name in DATA_FILES:
        raw_data[name], parsed[name] = _data(content / f"{name}.json")
    topics, resources, glossary = parsed["topics"], parsed["resources"], parsed["glossary"]

    _unique(topics["topics"], "content/topics.json")
    for t in topics["topics"]:
        if not SLUG_RE.match(t["id"]):
            raise ContentError(f"content/topics.json: topic id {t['id']!r} must be lowercase words joined by hyphens")
    topic_ids = {t["id"] for t in topics["topics"]}
    if TEE_TOPIC not in topic_ids:
        raise ContentError(f"content/topics.json: the topic {TEE_TOPIC!r} is missing; its page is the TEE hub")
    layer_order = {layer: n for n, layer in enumerate(_check_stack(topics, topic_ids))}
    _unique(resources["resources"], "content/resources.json")
    for res in resources["resources"]:
        if not URL_RE.match(str(res.get("url", ""))):
            raise ContentError(f"content/resources.json: {res['id']}: url must be an http(s) URL")
    _unique(glossary["terms"], "content/glossary.json")
    for term in glossary["terms"]:
        if term.get("topic") and term["topic"] not in topic_ids:
            raise ContentError(f"content/glossary.json: {term['id']}: unknown topic {term['topic']!r}")
    agents = _check_agents(site)
    not_people = _not_people(site, agents)
    articles = {lang: [] for lang in LANGS}
    for folder in sorted(p for p in (content / "articles").iterdir() if p.is_dir() and p.name[:1] not in "._"):
        if not SLUG_RE.match(folder.name):
            raise ContentError(f"{folder}: article folder names are lowercase ASCII words joined by hyphens")
        en_path = folder / "en.md"
        if not en_path.exists():
            raise ContentError(f"{folder}: en.md is required")
        raw, meta, body = _read(en_path)
        en = Article(folder.name, "en", meta, body, raw, en_path)
        editions = [en]
        zh_path = folder / "zh.md"
        if zh_path.exists():
            raw, zmeta, zbody = _read(zh_path)
            for key in INHERITED:
                if key not in zmeta and key in meta:
                    zmeta[key] = meta[key]
            zh = Article(folder.name, "zh", zmeta, zbody, raw, zh_path)
            if en.disclosure and not zh.disclosure:
                # never drop a disclosure: show the English one until it is translated
                zh.disclosure, zh.disclosure_lang = en.disclosure, "en"
            editions.append(zh)
        lead_image = _lead_image(root, folder)
        for a in editions:  # zh.md may override topics and layers, so both editions are checked
            a.lead_image = lead_image
            _check_byline(a, agents, not_people, en=en if a is not en else None)
            for topic in a.topics:
                if topic not in topic_ids:
                    raise ContentError(f"{a.path}: unknown topic {topic!r}")
            if a.layers:
                for layer in a.layers:
                    if layer not in layer_order:
                        raise ContentError(f"{a.path}: unknown stack layer {layer!r} in layers")
                a.layers.sort(key=layer_order.get)
            articles[a.lang].append(a)

    pages = {lang: {} for lang in LANGS}
    for path in sorted((content / "pages").glob("*.md")):
        name, _, lang = path.stem.rpartition(".")
        if lang not in LANGS or not SLUG_RE.match(name):
            raise ContentError(f"{path}: page files are named <name>.<lang>.md, with a lowercase hyphenated name")
        raw, meta, body = _read(path)
        pages[lang][name] = Page(name, lang, meta, body, raw, path)

    for res in resources["resources"]:
        for topic in res.get("topics", []):
            if topic not in topic_ids:
                raise ContentError(f"resource {res.get('title')!r}: unknown topic {topic!r}")

    # the files in static/media/ that a spec names, drafts' included, before drafts leave the lists
    named_media = {name for a in articles["en"] if a.lead_image for name in a.lead_image.files()}
    for lang in LANGS:
        if not drafts:
            articles[lang] = [a for a in articles[lang] if not a.draft]
    # a translation is published only with its English original (en.md may be a draft)
    published = {a.slug for a in articles["en"]}
    articles["zh"] = [a for a in articles["zh"] if a.slug in published]
    for lang in LANGS:
        articles[lang].sort(key=lambda a: a.sort_key, reverse=True)
    _check_lead_images(site, articles["en"])

    # the data files may name only articles that this build publishes
    resource_ids = {r["id"] for r in resources["resources"]}
    tier_ids = _check_tiers(parsed["tiers"], set(layer_order), topic_ids, published)
    _check_topic_lines(topics, tier_ids)
    _check_resources(resources, resource_ids)
    _check_tee(parsed["tee"], published, resource_ids, {g["id"] for g in glossary["terms"]})
    return {
        "site": site,
        "strings": strings,
        "topics": topics,
        "resources": resources,
        "glossary": glossary,
        "tee": parsed["tee"],
        "tiers": parsed["tiers"],
        "articles": articles,
        "pages": pages,
        "raw": raw_data,  # the data files' bytes, hashed in the manifest and published as-is
        "unused_media": unused_media(root, named_media),  # files in static/media/ that no spec names
    }
