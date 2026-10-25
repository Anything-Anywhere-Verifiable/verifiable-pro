#!/usr/bin/env python3
"""Make an article's lead photo: crop, grade and encode it with headless Chrome.

    python3 tools/photos.py --write SLUG --source FILE [--focus FOCUS | --same-crop] [--meta META]
    python3 tools/photos.py --draft DIR SLUG --source FILE [--focus FOCUS | --same-crop] [--meta META]
    python3 tools/photos.py --check [SLUG ...]

--write turns a photograph into SLUG's lead photo. It crops the source to 3:2 around
FOCUS and writes four files into static/media/: SLUG.webp, 1600 x 1067 pixels, which
the article's figure shows; two smaller copies of the same crop, SLUG-800.webp (800 x
533) and SLUG-400.webp (400 x 267), which srcset offers beside it so that a list loads
the smallest file its picture's width needs; and SLUG-og.jpg, 1200 x 630, the widest
strip of the crop at that shape, which link previews show. Every file gets the same
colour grade (GRADE, below), carries no metadata (no EXIF, XMP, colour profile or
comment) and should stay under about 250, 70, 25 and 150 KB (FILES). It then writes
content/articles/SLUG/illustration.json as a photo spec, with each file's size and
SHA-256 digest, what it did to the source ("edits") and the texts from META, and deletes
static/media/SLUG.svg, the drawing that a photo replaces. A photo is never enlarged: a
source or a crop narrower than 1600 pixels is refused.

--same-crop, instead of FOCUS, cuts the boxes that SLUG's spec already records
(edits.crop and edits.social_crop) from the same source, which must be the file whose
digest the spec records (edits.source_sha256). It makes a photo's files again exactly as
they were cropped, such as after a change to the copies, the budgets or the encoder.

FOCUS says where to crop: "center" (the default), "top", "bottom", "left" or "right";
"X,Y", the point to keep in the middle, as fractions of the source's width and height,
such as 0.5,0.35; or "X,Y,W,H", a box in the source's pixels that the crop must stay
inside (the crop is the largest 3:2 box centred in it). The link-preview strip is
centred on the same point, or on the box's centre.

META is a JSON file, or JSON text, with the photo's alt and caption
({"en": "...", "zh": "..."}), credit, license, license_url, source_url and retrieved
(the day the source was downloaded, YYYY-MM-DD), and optionally focus. --alt-en,
--alt-zh, --caption-en, --caption-zh, --credit, --license, --license-url, --source-url
and --retrieved set one field each and override META. Without them, an article that
already has a photo keeps its texts, so --write can crop a photo again. The texts follow
CONTENT_GUIDE.md ("Photos"), and the license must be one a photo may carry there.

--draft DIR writes the four files and the spec into DIR and changes nothing in the
repository, to look at a crop first. --check needs no browser: it checks every photo
spec, its files and their digests as the build does, holds the files to the names and
sizes above, the current grade and no metadata, warns about a file over its budget or a
source outside Wikimedia Commons, US government sites, Unsplash and Pexels, and fails
when static/media/ holds a file that no spec names.

GRADE "soft-1" is the one colour grade of every photo, so that the photos read as one
series beside the site's grays and its warm accent. On sRGB values it lowers saturation
to 88% and contrast to 92% around middle gray, exactly as the CSS filter
saturate(0.88) contrast(0.92) does, then adds a faint warm tone (red x 1.012, blue x
0.976): white becomes #f8f5ef, black #0a0a0a and middle gray #81807d. The same matrix
(grade_matrix()) is applied to every pixel; nothing in a photo is retouched, added,
removed or sharpened.

The browser is $CHROME when it is set, else Google Chrome where macOS installs it, or
google-chrome or chromium on the PATH (as for tools/og_images.py). Chrome decodes JPEG,
PNG, WebP, GIF and AVIF sources, and turns a JPEG as its EXIF orientation says; convert
another type first (on macOS: sips -s format png in.tif --out in.png).
"""

import argparse
import base64
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _path in (str(ROOT), str(ROOT / "tools")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from sitegen import content  # noqa: E402

# The four files, by their place in the spec: the photo itself, then its copies (variants,
# content.PHOTO_VARIANTS). Each: file name, size in pixels, type, starting quality, lowest
# quality, quality step and byte budget. The encoder steps the quality down until a file fits
# its budget or reaches the lowest quality; a file still over its budget then is written with
# a warning. Most photos fit at the starting quality; only a crop full of fine detail, such as
# foliage or gravel, steps down far, and there the detail hides the coarser encoding. "list"
# and "thumb" are the photo's crop at a half and a quarter of its width, which srcset offers
# beside it (sitegen/render.py): a list copy under about 140 CSS pixels wide loads the
# 400-pixel file on most screens, a wider one or a sharper screen the 800-pixel file
FILES = {
    "photo": ("{slug}.webp", (1600, 1067), "image/webp", 0.82, 0.46, 0.04, 250 * 1024),
    "list": ("{slug}-800.webp", (800, 533), "image/webp", 0.8, 0.52, 0.04, 70 * 1024),
    "thumb": ("{slug}-400.webp", (400, 267), "image/webp", 0.8, 0.52, 0.04, 25 * 1024),
    "social": ("{slug}-og.jpg", content.PHOTO_SOCIAL_SIZE, "image/jpeg", 0.85, 0.5, 0.05, 150 * 1024),
}
PHOTO_SIZE = FILES["photo"][1]
# The colour grades, by the id that a spec's edits.grade records. Add a new grade under a new
# id (and to content.PHOTO_GRADES) rather than changing one in use, then make every photo again
GRADE = "soft-1"
GRADES = {"soft-1": {"saturation": 0.88, "contrast": 0.92, "gains": (1.012, 1.0, 0.976)}}
# CSS saturate()'s luminance weights (Filter Effects Module Level 1)
LUMA = (0.213, 0.715, 0.072)
# What META may hold
META_KEYS = ("alt", "caption", "credit", "license", "license_url", "source_url", "retrieved", "focus")
TEXT_KEYS = ("alt", "caption", "credit", "license", "license_url", "source_url", "retrieved")
FOCUS_NAMES = {"center": (0.5, 0.5), "centre": (0.5, 0.5), "top": (0.5, 0.0), "bottom": (0.5, 1.0),
               "left": (0.0, 0.5), "right": (1.0, 0.5)}
# The sources CONTENT_GUIDE.md allows, by host: Wikimedia Commons, US government sites,
# Unsplash and Pexels. Another host only warns: an editor may have a reason
SOURCE_HOSTS = ("commons.wikimedia.org", "commons.m.wikimedia.org", "upload.wikimedia.org", "unsplash.com",
                "pexels.com")
SOURCE_SUFFIXES = (".gov", ".mil", ".fed.us")
# What Chrome can decode, by the first bytes of a file
SOURCE_TYPES = ((b"\xff\xd8\xff", "JPEG"), (b"\x89PNG\r\n\x1a\n", "PNG"), (b"GIF8", "GIF"))


class PhotoError(Exception):
    """A source, a focus, a META or a file that tools/photos.py refuses, with the reason."""


# ----- the grade --------------------------------------------------------------------

def grade_matrix(grade=GRADE):
    """GRADE as a 3 x 4 matrix on sRGB values from 0 to 255, row by row: each output channel
    (red, then green, then blue) is m[0] * r + m[1] * g + m[2] * b + m[3], rounded to the
    nearest whole number (halves to even) and clamped to 0..255, as Chrome stores it."""
    params = GRADES[grade]
    s, c, gains = params["saturation"], params["contrast"], params["gains"]
    rows = []
    for i in range(3):
        saturate = [(1 - s) * LUMA[j] + (s if i == j else 0) for j in range(3)]
        rows += [round(gains[i] * c * v, 6) for v in saturate] + [round(gains[i] * 255 * (1 - c) / 2, 6)]
    return rows


def apply_grade(rgb, grade=GRADE):
    """One sRGB colour (r, g, b from 0 to 255) as GRADE changes it: what Chrome does to each pixel."""
    m = grade_matrix(grade)
    return tuple(min(255, max(0, round(m[4 * i] * rgb[0] + m[4 * i + 1] * rgb[1] + m[4 * i + 2] * rgb[2]
                                       + m[4 * i + 3]))) for i in range(3))


# ----- crops ------------------------------------------------------------------------

def parse_focus(value):
    """FOCUS (see the module docstring), as text or a list of numbers, as ("point", (x, y))
    with fractions of the source's width and height, or ("box", (x, y, w, h)) in pixels."""
    if value is None:
        value = "center"
    if isinstance(value, (list, tuple)):
        value = ",".join(str(v) for v in value)
    text = str(value).strip().lower()
    if text in FOCUS_NAMES:
        return "point", FOCUS_NAMES[text]
    try:
        numbers = [float(part) for part in text.split(",")]
    except ValueError:
        numbers = []
    if len(numbers) == 2 and all(0 <= n <= 1 for n in numbers):
        return "point", (numbers[0], numbers[1])
    if len(numbers) == 4 and all(n == int(n) and n >= 0 for n in numbers) and numbers[2] > 0 and numbers[3] > 0:
        return "box", tuple(int(n) for n in numbers)
    raise PhotoError(f"focus {value!r} must be center, top, bottom, left or right; X,Y, fractions from 0 to 1 of the "
                     "source's width and height; or X,Y,W,H, a box in the source's whole pixels")


def fit(width, height, shape):
    """The largest whole-pixel (w, h) with SHAPE's proportions (a (width, height) pair) inside
    WIDTH x HEIGHT. A box within 0.1% of those proportions is kept whole: a 3:2 camera frame
    (6000 x 4000) makes the 1600 x 1067 photo without losing a pixel column to rounding."""
    if abs(width * shape[1] - height * shape[0]) <= 0.001 * width * shape[1]:
        return width, height
    if width * shape[1] > height * shape[0]:
        return min(width, round(height * shape[0] / shape[1])), height
    return width, min(height, round(width * shape[1] / shape[0]))


def _clamp(value, low, high):
    return max(low, min(high, value))


def focus_point(focus, size):
    """The point, in the source's pixels, that FOCUS keeps in the middle: its point, or its box's centre."""
    kind, value = focus
    if kind == "box":
        return value[0] + value[2] / 2, value[1] + value[3] / 2
    return value[0] * size[0], value[1] * size[1]


def crop_box(size, focus, shape=PHOTO_SIZE):
    """The box [x, y, w, h] in the source's pixels (SIZE) that the photo and its list copy are
    cut from: the largest box with SHAPE's proportions, centred on FOCUS's point as far as the
    source allows, or the largest one centred in FOCUS's box."""
    width, height = size
    kind, value = focus
    if kind == "box":
        bx, by, bw, bh = value
        if bx + bw > width or by + bh > height:
            raise PhotoError(f"the focus box {bx},{by},{bw},{bh} reaches outside the {width} x {height} source")
        w, h = fit(bw, bh, shape)
        return [bx + (bw - w) // 2, by + (bh - h) // 2, w, h]
    w, h = fit(width, height, shape)
    fx, fy = focus_point(focus, size)
    return [_clamp(round(fx - w / 2), 0, width - w), _clamp(round(fy - h / 2), 0, height - h), w, h]


def social_box(crop, focus, size):
    """The box of the link-preview copy: the widest strip of CROP at the social cards'
    proportions (1200 x 630), centred on FOCUS's point as far as the crop allows, so a link
    preview shows part of the photo and nothing the crop leaves out."""
    cx, cy, cw, ch = crop
    w, h = fit(cw, ch, content.PHOTO_SOCIAL_SIZE)
    fx, fy = focus_point(focus, size)
    return [_clamp(round(fx - w / 2), cx, cx + cw - w), _clamp(round(fy - h / 2), cy, cy + ch - h), w, h]


def plan(size, focus):
    """The crop and the social box for a source of SIZE, or a PhotoError when the source or
    the crop is too narrow for the photo without enlarging it."""
    width, height = size
    if width < PHOTO_SIZE[0]:
        raise PhotoError(f"the source is {width} x {height} pixels; a lead photo needs a source at least "
                         f"{PHOTO_SIZE[0]} pixels wide, since a photo is never enlarged")
    crop = crop_box(size, focus)
    if crop[2] < PHOTO_SIZE[0]:
        raise PhotoError(f"the crop {crop} is {crop[2]} pixels wide; it needs at least {PHOTO_SIZE[0]}, since a photo "
                         "is never enlarged (choose a larger focus box)")
    return crop, social_box(crop, focus, size)


# ----- files: types, metadata ----------------------------------------------------------

def source_type(raw):
    """The type of a source file that Chrome decodes, from its first bytes, or None."""
    for magic, name in SOURCE_TYPES:
        if raw.startswith(magic):
            return name
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return "WebP"
    if raw[4:12] in (b"ftypavif", b"ftypavis"):
        return "AVIF"
    return None


def riff_chunks(raw):
    """The chunks of a WebP file as (four-byte kind, data) pairs."""
    if raw[:4] != b"RIFF" or raw[8:12] != b"WEBP":
        raise PhotoError("not a WebP file")
    i, out = 12, []
    while i + 8 <= len(raw):
        kind, n = raw[i:i + 4], int.from_bytes(raw[i + 4:i + 8], "little")
        out.append((kind, raw[i + 8:i + 8 + n]))
        i += 8 + n + (n & 1)
    return out


def jpeg_segments(raw):
    """The segments of a JPEG file before its scan, as (marker, whole segment) pairs."""
    if raw[:2] != b"\xff\xd8":
        raise PhotoError("not a JPEG file")
    i, out = 2, []
    while i + 4 <= len(raw) and raw[i] == 0xFF:
        marker = raw[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        if marker in (0x01,) or 0xD0 <= marker <= 0xD7:
            i += 2
            continue
        if marker in (0xD9, 0xDA):
            break
        n = int.from_bytes(raw[i + 2:i + 4], "big")
        out.append((marker, raw[i:i + 2 + n]))
        i += 2 + n
    return out


def metadata(raw, file_name):
    """What metadata a file of the photo carries, by name ([] for none): EXIF, XMP, IPTC,
    a colour profile, text or a comment. A JPEG's JFIF and Adobe segments describe the image
    data itself and are not metadata."""
    found = []
    ext = file_name.rsplit(".", 1)[-1]
    if ext in ("jpg", "jpeg"):
        for marker, segment in jpeg_segments(raw):
            body = segment[4:]
            if marker == 0xE1:
                found.append("XMP" if body.startswith(b"http://ns.adobe.com/") else "EXIF")
            elif marker == 0xE2:
                found.append("a colour profile" if body.startswith(b"ICC_PROFILE") else "APP2 data")
            elif marker == 0xED:
                found.append("IPTC")
            elif marker == 0xFE:
                found.append("a comment")
            elif 0xE3 <= marker <= 0xEF and marker != 0xEE:
                found.append(f"APP{marker - 0xE0} data")
    elif ext == "webp":
        names = {b"EXIF": "EXIF", b"XMP ": "XMP", b"ICCP": "a colour profile"}
        found += [names[kind] for kind, _ in riff_chunks(raw) if kind in names]
    elif ext == "png":
        pos, names = 8, {b"tEXt": "text", b"zTXt": "text", b"iTXt": "text", b"eXIf": "EXIF", b"iCCP": "a colour profile",
                         b"tIME": "a time stamp"}
        while pos + 8 <= len(raw):
            n, kind = int.from_bytes(raw[pos:pos + 4], "big"), raw[pos + 4:pos + 8]
            if kind in names:
                found.append(names[kind])
            pos += 12 + n
    return sorted(set(found))


def strip_jpeg(raw):
    """A JPEG without its APP1 to APP15 segments (EXIF, XMP, the colour profile, IPTC) and
    comments, keeping APP0 (JFIF), APP14 (Adobe) and the image data."""
    segments = jpeg_segments(raw)
    kept = [segment for marker, segment in segments if not ((0xE1 <= marker <= 0xEF and marker != 0xEE) or marker == 0xFE)]
    scan = 2 + sum(len(segment) for _, segment in segments)
    if raw[scan:scan + 2] != b"\xff\xda":
        raise PhotoError("Chrome's JPEG has no scan where expected")
    return raw[:2] + b"".join(kept) + raw[scan:]


def strip_webp(raw):
    """A WebP in the simple format, its one VP8 chunk alone: no VP8X header, colour profile,
    EXIF or XMP. Chrome writes an opaque still picture, so nothing else may be there."""
    chunks = riff_chunks(raw)
    image = [(kind, data) for kind, data in chunks if kind in (b"VP8 ", b"VP8L")]
    other = sorted({kind for kind, _ in chunks} - {b"VP8X", b"VP8 ", b"VP8L", b"ICCP", b"EXIF", b"XMP "})
    if len(image) != 1 or other:
        raise PhotoError(f"Chrome's WebP has chunks this tool does not expect: {[k for k, _ in chunks]}")
    kind, data = image[0]
    body = b"WEBP" + kind + len(data).to_bytes(4, "little") + data + (b"\x00" if len(data) & 1 else b"")
    return b"RIFF" + len(body).to_bytes(4, "little") + body


# ----- META -------------------------------------------------------------------------------

def read_meta(value):
    """META: JSON text (starting with "{") or the path of a JSON file, as a dict."""
    if value is None:
        return {}
    text = value if value.lstrip().startswith("{") else None
    if text is None:
        try:
            text = Path(value).read_text(encoding="utf-8")
        except OSError as exc:
            raise PhotoError(f"cannot read --meta {value}: {exc}") from None
    try:
        meta = json.loads(text)
    except ValueError as exc:
        raise PhotoError(f"--meta is not JSON: {exc}") from None
    if not isinstance(meta, dict):
        raise PhotoError("--meta must be a JSON object")
    extra = sorted(set(meta) - set(META_KEYS))
    if extra:
        raise PhotoError(f"--meta has the unknown field {extra[0]!r}; it may hold {', '.join(META_KEYS)}")
    return meta


def merge_meta(old, meta, overrides):
    """The photo's texts: an existing photo spec's (OLD), then META's, then the command line's
    OVERRIDES ({"alt.en": ..., "credit": ...}), each later one winning."""
    kept = old if isinstance(old, dict) and old.get("kind") == "photo" else {}
    out = {key: json.loads(json.dumps(kept[key])) for key in TEXT_KEYS if key in kept}
    out.update({key: value for key, value in meta.items() if key != "focus"})
    for key, value in overrides.items():
        if value is None:
            continue
        field, _, lang = key.partition(".")
        if lang:
            current = out.get(field)
            out[field] = dict(current) if isinstance(current, dict) else {}
            out[field][lang] = value
        else:
            out[field] = value
    return out


def check_meta(meta, where="the photo's texts"):
    """META's texts as a photo spec needs them (sitegen/content.py's own checks), or a PhotoError."""
    missing = [key for key in TEXT_KEYS if key not in meta]
    if missing:
        raise PhotoError(f"{where} lack {', '.join(missing)}: give them in --meta or with --{missing[0].replace('_', '-')}")
    try:
        for key in ("alt", "caption"):
            content._text(meta[key], f"{where}: {key}")
        content._name(meta["credit"], f"{where}: credit")
        content._name(meta["license"], f"{where}: license")
        for key in ("license_url", "source_url"):
            if not isinstance(meta[key], str) or not content.URL_RE.match(meta[key]):
                raise content.ContentError(f"{where}: {key} must be an http(s) URL")
        content.photo_license(meta["license"], meta["license_url"], f"{where}: license")
        content._when(meta["retrieved"], f"{where}: retrieved", full=True)
    except content.ContentError as exc:
        raise PhotoError(str(exc)) from None


def source_allowed(url):
    """Whether URL is on a source CONTENT_GUIDE.md allows: Wikimedia Commons, a US government
    site, Unsplash or Pexels."""
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host in SOURCE_HOSTS or host.endswith(SOURCE_SUFFIXES)


# ----- the spec ---------------------------------------------------------------------------

def pretty_json(obj, indent=0, width=110, lead=0):
    """JSON with two-space indentation that keeps any object or list that fits within WIDTH
    columns on one line, as tools/illustrate.py writes its specs. LEAD is the width of the key
    already printed on the line."""
    flat = json.dumps(obj, ensure_ascii=False)
    if not isinstance(obj, (dict, list)) or not obj or indent + lead + len(flat) <= width:
        return flat
    pad = " " * (indent + 2)
    if isinstance(obj, dict):
        rows = [pad + json.dumps(k, ensure_ascii=False) + ": "
                + pretty_json(v, indent + 2, width, len(json.dumps(k, ensure_ascii=False)) + 2) for k, v in obj.items()]
        return "{\n" + ",\n".join(rows) + "\n" + " " * indent + "}"
    return "[\n" + ",\n".join(pad + pretty_json(v, indent + 2, width) for v in obj) + "\n" + " " * indent + "]"


def file_entry(name, data):
    """A file's entry in the spec: its name, size from its header and SHA-256."""
    kind = content.PHOTO_TYPES[name.rsplit(".", 1)[1]]
    width, height = content._raster_size(data, kind)
    return {"file": name, "width": width, "height": height, "sha256": hashlib.sha256(data).hexdigest()}


def make_spec(slug, files, source_sha256, source_size, crop, social, meta, grade=GRADE):
    """The photo spec (content/articles/SLUG/illustration.json) for FILES ({"photo": bytes,
    "list": bytes, "social": bytes}), in the order CONTENT_GUIDE.md shows its fields."""
    names = {role: FILES[role][0].format(slug=slug) for role in FILES}
    photo = file_entry(names["photo"], files["photo"])
    spec = {"kind": "photo", **photo,
            "variants": {role: file_entry(names[role], files[role]) for role in content.PHOTO_VARIANTS},
            "edits": {"source_sha256": source_sha256, "source_size": list(source_size), "crop": list(crop),
                      "social_crop": list(social), "grade": grade}}
    spec.update({key: meta[key] for key in TEXT_KEYS})
    return spec


def spec_files(spec):
    """The files in static/media/ that a spec names, read as leniently as a broken spec allows:
    an illustration's drawing, or a photo's file and copies."""
    if not isinstance(spec, dict):
        return set()
    if spec.get("kind") != "photo":
        return set()
    names = {spec.get("file")}
    variants = spec.get("variants")
    if isinstance(variants, dict):
        names |= {v.get("file") for v in variants.values() if isinstance(v, dict)}
    return {n for n in names if isinstance(n, str)}


# ----- Chrome -------------------------------------------------------------------------------

# The page that Chrome runs: open() decodes the source and gives its size as the browser shows
# it (after EXIF orientation); render() cuts each file's box at full size with drawImage, which
# turns the source as its EXIF orientation says, shrinks it with createImageBitmap's high-quality
# filter, applies the grade matrix to every pixel, and encodes the file, stepping the quality
# down until it fits its budget. White fills any transparency, so every file is opaque.
PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>tools/photos.py</title></head><body><script>
window.vp = {
  async open(src) {
    const img = new Image();
    img.src = src;
    await img.decode();
    window.vpSource = img;
    return [img.naturalWidth, img.naturalHeight];
  },
  async render(job) {
    const img = window.vpSource, m = job.matrix, out = [];
    let box = null, boxKey = "";
    for (const t of job.files) {
      const [sx, sy, sw, sh] = t.crop;
      if (boxKey !== t.crop.join(",")) {
        if (box) { box.width = 0; box.height = 0; }
        box = document.createElement("canvas");
        box.width = sw;
        box.height = sh;
        const bc = box.getContext("2d");
        bc.fillStyle = "#ffffff";
        bc.fillRect(0, 0, sw, sh);
        bc.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);
        boxKey = t.crop.join(",");
      }
      const small = await createImageBitmap(box, {resizeWidth: t.width, resizeHeight: t.height, resizeQuality: "high"});
      const canvas = document.createElement("canvas");
      canvas.width = t.width;
      canvas.height = t.height;
      const ctx = canvas.getContext("2d", {willReadFrequently: true});
      ctx.drawImage(small, 0, 0);
      small.close();
      const data = ctx.getImageData(0, 0, t.width, t.height), p = data.data;
      for (let i = 0; i < p.length; i += 4) {
        const r = p[i], g = p[i + 1], b = p[i + 2];
        p[i] = m[0] * r + m[1] * g + m[2] * b + m[3];
        p[i + 1] = m[4] * r + m[5] * g + m[6] * b + m[7];
        p[i + 2] = m[8] * r + m[9] * g + m[10] * b + m[11];
        p[i + 3] = 255;
      }
      ctx.putImageData(data, 0, 0);
      let q = t.quality, blob = null;
      for (;;) {
        blob = await new Promise((resolve) => canvas.toBlob(resolve, t.type, q));
        if (!blob) throw new Error("Chrome could not encode " + t.type);
        if (blob.size <= t.budget || q <= t.floor + 1e-9) break;
        q = Math.max(t.floor, Math.round((q - t.step) * 1000) / 1000);
      }
      const url = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
      });
      out.push({role: t.role, quality: q, data: url.slice(url.indexOf(",") + 1)});
    }
    return out;
  },
};
</script></body></html>
"""


class Browser:
    """Headless Chrome (tools/og_images.py's DevTools client) with the page above and a copy of
    the source beside it, in a temporary folder (Chrome cannot always read synced folders)."""

    def __init__(self, source):
        from og_images import Chrome  # only --write and --draft need a browser
        self.work = Path(tempfile.mkdtemp(prefix="vp-photo-"))
        self.name = "source" + (Path(source).suffix.lower() or ".img")
        shutil.copyfile(source, self.work / self.name)
        (self.work / "photo.html").write_text(PAGE, encoding="utf-8")
        try:
            self.chrome = Chrome()
        except BaseException:
            shutil.rmtree(self.work, ignore_errors=True)
            raise
        try:
            self.chrome.open(self.work / "photo.html", 1280, 800)
        except BaseException:
            self.close()
            raise

    def size(self):
        try:
            width, height = self.chrome.evaluate(f"vp.open({json.dumps(self.name)})")
        except RuntimeError as exc:
            raise PhotoError(f"Chrome could not decode the source ({str(exc)[:160]}); use a JPEG, PNG or WebP file") \
                from None
        return width, height

    def render(self, crop, social):
        files = []
        for role, (_, (width, height), mime, quality, floor, step, budget) in FILES.items():
            files.append({"role": role, "crop": social if role == "social" else crop, "width": width,
                          "height": height, "type": mime, "quality": quality, "floor": floor, "step": step,
                          "budget": budget})
        try:
            done = self.chrome.evaluate(f"vp.render({json.dumps({'matrix': grade_matrix(), 'files': files})})")
        except RuntimeError as exc:
            raise PhotoError(f"Chrome could not make the files ({str(exc)[:160]}); a very large source may need "
                             "scaling down first, such as sips -Z 6000 in.jpg --out smaller.jpg on macOS") from None
        return {d["role"]: (base64.b64decode(d["data"]), d["quality"]) for d in done}

    def close(self):
        try:
            self.chrome.close()
        finally:
            shutil.rmtree(self.work, ignore_errors=True)


def recorded_boxes(old, raw, where):
    """--same-crop: the crop and the social box that the photo spec OLD records, for a source
    whose bytes (RAW) are the file it records, as (source size, crop, social box)."""
    edits = old.get("edits") if isinstance(old, dict) and old.get("kind") == "photo" else None
    if not isinstance(edits, dict):
        raise PhotoError(f"{where} has no photo spec whose edits record a crop; --same-crop needs one")
    try:
        content._photo_edits(content._keys(edits, content.PHOTO_EDIT_KEYS, f"{where}: edits"), PHOTO_SIZE,
                             f"{where}: edits")
    except content.ContentError as exc:
        raise PhotoError(f"--same-crop cannot use the recorded boxes: {exc}") from None
    digest = hashlib.sha256(raw).hexdigest()
    if digest != edits["source_sha256"]:
        raise PhotoError(f"--same-crop cuts the recorded boxes from the recorded source only, and this file's SHA-256 "
                         f"is {digest[:12]}..., not {edits['source_sha256'][:12]}... (edits.source_sha256 in {where})")
    return tuple(edits["source_size"]), list(edits["crop"]), list(edits["social_crop"])


def encode(source, focus, boxes=None):
    """Decode SOURCE in Chrome, plan its crops (or take BOXES, recorded_boxes()'s (source
    size, crop, social box)) and make the four files. Returns (source size, crop, social box,
    {role: (bytes, quality)}) with every file stripped of metadata and checked for its type
    and size."""
    browser = Browser(source)
    try:
        size = browser.size()
        if boxes:
            if tuple(size) != tuple(boxes[0]):
                raise PhotoError(f"Chrome decodes the source at {size[0]} x {size[1]} pixels, not the recorded "
                                 f"{boxes[0][0]} x {boxes[0][1]}")
            crop, social = boxes[1], boxes[2]
        else:
            crop, social = plan(size, focus)
        made = browser.render(crop, social)
    finally:
        browser.close()
    out = {}
    for role, (data, quality) in made.items():
        name, want, mime = FILES[role][0], FILES[role][1], FILES[role][2]
        data = strip_webp(data) if mime == "image/webp" else strip_jpeg(data)
        kind = content.PHOTO_TYPES[name.rsplit(".", 1)[1]]
        got = content._raster_size(data, kind)
        if got != tuple(want) or metadata(data, name):
            raise PhotoError(f"Chrome made the {role} file at {got} with {metadata(data, name)}; expected {want} with "
                             "no metadata")
        out[role] = (data, quality)
    return size, crop, social, out


# ----- --write and --draft --------------------------------------------------------------------

def write(root, slug, source, focus=None, meta=None, overrides=None, draft=None, same_crop=False):
    """--write (DRAFT None) or --draft DRAFT, with --same-crop (SAME_CROP): see the module
    docstring. Returns the spec."""
    root = Path(root)
    folder = root / "content" / "articles" / slug
    if not content.SLUG_RE.match(slug) or not (folder / "en.md").is_file():
        raise PhotoError(f"content/articles/{slug}/en.md does not exist")
    spec_path = folder / content.LEAD_IMAGE_FILE
    old = None
    if spec_path.is_file():
        try:
            old = json.loads(spec_path.read_text(encoding="utf-8"))
        except ValueError:
            old = None
    meta = read_meta(meta) if not isinstance(meta, dict) else meta
    texts = merge_meta(old, meta, overrides or {})
    if isinstance(old, dict) and old.get("kind") != "photo" and not {"alt", "caption"} <= set(texts):
        raise PhotoError(f"content/articles/{slug} has an illustration, whose alt text and caption describe the "
                         "drawing: give the photo's own alt and caption in --meta")
    check_meta(texts, f"{slug}'s photo")
    if same_crop and (focus is not None or "focus" in meta):
        raise PhotoError("--same-crop cuts the recorded boxes, so it takes no focus")
    focus = parse_focus(focus if focus is not None else meta.get("focus"))
    source = Path(source)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise PhotoError(f"cannot read the source {source}: {exc}") from None
    kind = source_type(raw)
    if kind is None:
        raise PhotoError(f"{source} is not a JPEG, PNG, WebP, GIF or AVIF file, which Chrome decodes; convert it "
                         "first (on macOS: sips -s format png in.tif --out in.png)")
    boxes = recorded_boxes(old, raw, f"content/articles/{slug}/{content.LEAD_IMAGE_FILE}") if same_crop else None
    early = content._raster_size(raw, kind) if kind in ("JPEG", "PNG", "WebP") else None
    if early and not boxes:
        plan(early, focus)  # refuses a narrow source or crop before starting a browser
    size, crop, social, made = encode(source, focus, boxes)
    files = {role: data for role, (data, _) in made.items()}
    spec = make_spec(slug, files, hashlib.sha256(raw).hexdigest(), size, crop, social, texts)
    names = {role: FILES[role][0].format(slug=slug) for role in FILES}
    media = Path(draft) if draft else root / content.MEDIA_DIR
    media.mkdir(parents=True, exist_ok=True)
    print(f"photos: {slug}: source {size[0]} x {size[1]}, crop {crop}, link-preview strip {social}, grade {GRADE}")
    for role in FILES:
        data, quality = made[role]
        budget = FILES[role][6]
        (media / names[role]).write_bytes(data)
        w, h = FILES[role][1]
        shown = (media / names[role]) if draft else (content.MEDIA_DIR / names[role]).as_posix()
        print(f"wrote {shown} ({w} x {h}, {len(data) / 1024:.0f} KB at quality {quality:.2f})")
        if len(data) > budget:
            print(f"photos: warning: {names[role]} is {len(data) / 1024:.0f} KB, over its {budget // 1024} KB budget "
                  "even at the lowest quality; a tighter crop or a calmer photo would load faster", file=sys.stderr)
    target = Path(draft) / content.LEAD_IMAGE_FILE if draft else spec_path
    target.write_text(pretty_json(spec) + "\n", encoding="utf-8")
    print(f"wrote {target if draft else target.relative_to(root).as_posix()}")
    if not source_allowed(texts["source_url"]):
        print(f"photos: warning: {texts['source_url']} is not on Wikimedia Commons, a US government site, Unsplash or "
              "Pexels, the sources CONTENT_GUIDE.md allows", file=sys.stderr)
    if draft:
        return spec
    # the drawing a photo replaces, and the files of an earlier photo that this one does not reuse
    stale = ({f"{slug}.svg"} | spec_files(old)) - set(names.values())
    for name in sorted(stale):
        path = root / content.MEDIA_DIR / name
        if path.is_file():
            path.unlink()
            print(f"deleted {(content.MEDIA_DIR / name).as_posix()}"
                  + (" (the illustration the photo replaces)" if name.endswith(".svg") else ""))
    try:
        content._lead_image(root, folder)
    except content.ContentError as exc:
        raise PhotoError(f"the build would refuse what was written: {exc}") from None
    return spec


# ----- --check ----------------------------------------------------------------------------------

def conventions(image, slug):
    """What --check holds a loaded photo (a content.LeadImage) to beyond the build's checks:
    (problems, warnings)."""
    problems, warnings = [], []
    for role in FILES:
        picture = image if role == "photo" else image.variants[role]
        name, size, _, _, _, _, budget = FILES[role]
        want = name.format(slug=slug)
        where = f"{slug}: {(content.MEDIA_DIR / picture.file).as_posix()}"
        if picture.file != want:
            problems.append(f"{slug}: the {role} file is {picture.file}, not {want}; run tools/photos.py --write {slug}")
        if (picture.width, picture.height) != tuple(size):
            problems.append(f"{where} is {picture.width} x {picture.height}, not {size[0]} x {size[1]}")
        found = metadata(picture.raw, picture.file)
        if found:
            problems.append(f"{where} carries {', '.join(found)}; tools/photos.py writes files without metadata")
        if len(picture.raw) > budget:
            warnings.append(f"{where} is {len(picture.raw) / 1024:.0f} KB, over its {budget // 1024} KB budget")
    grade = image.spec["edits"]["grade"]
    if grade != GRADE:
        warnings.append(f"{slug}: graded {grade}, not the current {GRADE}; make it again with tools/photos.py --write")
    if not source_allowed(image.source_url):
        warnings.append(f"{slug}: source_url {image.source_url} is not on Wikimedia Commons, a US government site, "
                        "Unsplash or Pexels")
    return problems, warnings


def check(root, slugs=()):
    """--check: every photo spec (or SLUGS'), then the files in static/media/ that no spec names.
    Returns the exit status."""
    root = Path(root)
    base = root / "content" / "articles"
    if slugs:
        folders = [base / slug for slug in slugs]
    else:
        folders = sorted(p for p in base.iterdir() if p.is_dir() and p.name[:1] not in "._") if base.is_dir() else []
    problems, warnings, named, photos = [], [], set(), 0
    for folder in folders:
        path = folder / content.LEAD_IMAGE_FILE
        if not path.is_file():
            if slugs:
                problems.append(f"{folder.name}: no {content.LEAD_IMAGE_FILE}")
            continue
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            problems.append(f"{folder.name}: {content.LEAD_IMAGE_FILE} is not JSON ({exc})")
            continue
        if not isinstance(spec, dict) or spec.get("kind") != "photo":
            named.add(f"{folder.name}.svg")  # an illustration's drawing: tools/illustrate.py --check checks it
            continue
        named |= spec_files(spec)  # a broken spec still owns its files: report the spec, not orphans
        photos += 1
        try:
            image = content._lead_image(root, folder)
        except content.ContentError as exc:
            problems.append(str(exc))
            continue
        found, notes = conventions(image, folder.name)
        problems += found
        warnings += notes
    if not slugs:
        for name in content.unused_media(root, named):
            problems.append(f"{(content.MEDIA_DIR / name).as_posix()} is named by no {content.LEAD_IMAGE_FILE}; "
                            "delete it")
    for line in warnings:
        print(f"photos: warning: {line}", file=sys.stderr)
    for line in problems:
        print(f"photos: {line}", file=sys.stderr)
    if not problems:
        print(f"photos: {photos} photo{'' if photos == 1 else 's'} checked, no problems")
    return 1 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", metavar="SLUG", help="make SLUG's lead photo in static/media/ and its spec")
    mode.add_argument("--draft", nargs=2, metavar=("DIR", "SLUG"), help="make the files and the spec in DIR only")
    mode.add_argument("--check", action="store_true", help="check every photo spec and its files; no browser")
    parser.add_argument("slugs", nargs="*", help="with --check: the articles to check (default: all)")
    parser.add_argument("--source", help="the photograph to start from")
    parser.add_argument("--focus", help="where to crop: center, top, bottom, left, right, X,Y or X,Y,W,H")
    parser.add_argument("--same-crop", action="store_true",
                        help="cut the boxes the spec in place records, from the source it records, instead of --focus")
    parser.add_argument("--meta", help="a JSON file, or JSON text, with the photo's texts")
    fields = {"alt-en": "the English alt text", "alt-zh": "the Chinese alt text", "caption-en": "the English caption",
              "caption-zh": "the Chinese caption", "credit": "whom to credit, such as 'Jane Doe / Wikimedia Commons'",
              "license": "the license's short name, such as 'CC BY-SA 4.0'", "license-url": "the license's address",
              "source-url": "the page the photo comes from", "retrieved": "the day the source was downloaded, YYYY-MM-DD"}
    for flag, what in fields.items():
        parser.add_argument(f"--{flag}", metavar="TEXT", help=f"{what} (overrides --meta)")
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.check:
        if args.same_crop:
            parser.error("--same-crop goes with --write or --draft")
        return check(args.root, args.slugs)
    if args.slugs:
        parser.error("only --check takes slugs after the options")
    if not args.source:
        parser.error("--write and --draft need --source")
    overrides = {"alt.en": args.alt_en, "alt.zh": args.alt_zh, "caption.en": args.caption_en,
                 "caption.zh": args.caption_zh, "credit": args.credit, "license": args.license,
                 "license_url": args.license_url, "source_url": args.source_url, "retrieved": args.retrieved}
    draft, slug = (args.draft[0], args.draft[1]) if args.draft else (None, args.write)
    try:
        write(args.root, slug, args.source, args.focus, args.meta, overrides, draft, args.same_crop)
    except PhotoError as exc:
        print(f"photos: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
