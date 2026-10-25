#!/usr/bin/env python3
"""Draw the news illustrations from their scene specs.

Every illustrated article has content/articles/<slug>/illustration.json (see
tools/scene/README.md). This tool draws its scene to static/media/<slug>.svg and records
the drawing's SHA-256 in the spec's svg_sha256, which the build checks.

    python3 tools/illustrate.py --write [slug ...]   # draw static/media/<slug>.svg, update svg_sha256
    python3 tools/illustrate.py --check [slug ...]   # exit 1 if a committed SVG or digest differs from a fresh draw
    python3 tools/illustrate.py --spec FILE [--out OUT.svg] [--png OUT.png] [--thumb OUT.png] [--debug] [--layers L,...]
    python3 tools/illustrate.py --catalog OUT.svg [--png OUT.png]   # every prop on one sheet, for authors
    python3 tools/illustrate.py --props-md           # the props reference for tools/scene/README.md

--write and --check hold every spec to the composition rules (tools/scene/README.md): a
focal object large and central enough, no prop hidden behind another, the palette's
rules and the story's own layer colours (read from the article's en.md), and a caption
that opens with "Illustration:" / "示意图：". --check also fails when one focal prop
leads more than MAX_FOCAL_USES pictures, or the magnifier more than MAX_MAGNIFIER.

--spec takes an illustration.json or a bare scene object, so a draft can live anywhere;
it prints the picture's numbers, problems and warnings, and still writes the files when
there are problems (exit status 1). --debug overlays the s/t grid, each prop's footprint
and id and the focal box on the draft (never on a published picture). --png and --thumb
render through headless Google Chrome (set CHROME to its path if it is not in the usual
place); --thumb renders the SVG at 240 x 160 and at the lists' 104 x 69 beside it.
Drawing needs only the standard library.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import re  # noqa: E402

from scene import SpecError  # noqa: E402
from scene.compose import LAYER_HUES, render  # noqa: E402
from scene.kit import REGISTRY, GROUPS  # noqa: E402

ENVELOPE_KEYS = ("kind", "alt", "caption", "scene", "svg_sha256")
LANGS = ("en", "zh")
SIZE_WARN = 40 * 1024
# How an illustration's caption opens (CONTENT_GUIDE.md, "Lead images"; tools/lint_content.py
# checks the same, and tests/test_illustrate.py keeps the two in step)
CAPTION_OPENING = {"en": "Illustration:", "zh": "示意图："}
# How often one prop may be the focal object across the site's pictures
MAX_FOCAL_USES = 5
MAX_MAGNIFIER = 4
THUMB = (240, 160)
FLOOR = "#eceef1"   # the catalog's cells: the floor's colour, so a prop shows the contrast it will have
LIST_THUMB = (104, 69)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_envelope(data, where):
    """Check the illustration.json wrapper around a scene; returns the scene, or None
    for a kind this tool does not draw (photo)."""
    if not isinstance(data, dict):
        raise SpecError("%s: expected a JSON object" % where)
    kind = data.get("kind")
    if kind == "photo":
        return None
    if kind != "illustration":
        raise SpecError("%s: kind must be \"illustration\" (or \"photo\"), got %r" % (where, kind))
    for k in data:
        if k not in ENVELOPE_KEYS:
            raise SpecError("%s: unknown key %r (allowed: %s)" % (where, k, ", ".join(ENVELOPE_KEYS)))
    for field in ("alt", "caption"):
        val = data.get(field)
        if not isinstance(val, dict) or set(val) != set(LANGS):
            raise SpecError("%s: %s must have exactly the keys en and zh" % (where, field))
        for lang in LANGS:
            if not isinstance(val[lang], str) or not val[lang].strip():
                raise SpecError("%s: %s.%s must be a non-empty string" % (where, field, lang))
    for lang in LANGS:
        if not data["caption"][lang].startswith(CAPTION_OPENING[lang]):
            raise SpecError("%s: caption.%s must open with %r" % (where, lang, CAPTION_OPENING[lang]))
    if data.get("scene") is None:   # None is what a photo returns, so a null scene is missing too
        raise SpecError("%s: missing scene" % where)
    dg = data.get("svg_sha256")
    if dg is not None and (not isinstance(dg, str) or len(dg) != 64 or any(c not in "0123456789abcdef" for c in dg)):
        raise SpecError("%s: svg_sha256 must be 64 lower-case hex digits" % where)
    return data["scene"]


def pretty_json(obj, indent=0, width=110, lead=0):
    """JSON with two-space indentation that keeps any object or list that fits within
    WIDTH columns on one line, so a scene's items read one per line. LEAD is the width of
    the key already printed on the line."""
    flat = json.dumps(obj, ensure_ascii=False)
    if not isinstance(obj, (dict, list)) or not obj or indent + lead + len(flat) <= width:
        return flat
    pad = " " * (indent + 2)
    if isinstance(obj, dict):
        rows = []
        for k, v in obj.items():
            key = json.dumps(k, ensure_ascii=False) + ": "
            rows.append(pad + key + pretty_json(v, indent + 2, width, len(key)))
        return "{\n" + ",\n".join(rows) + "\n" + " " * indent + "}"
    return "[\n" + ",\n".join(pad + pretty_json(v, indent + 2, width) for v in obj) + "\n" + " " * indent + "]"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def specs(root, slugs):
    base = os.path.join(root, "content", "articles")
    if slugs:
        out = []
        for s in slugs:
            p = os.path.join(base, s, "illustration.json")
            if not os.path.isfile(p):
                raise SystemExit("illustrate: %s has no illustration.json" % s)
            out.append((s, p))
        return out
    out = []
    if os.path.isdir(base):
        for s in sorted(os.listdir(base)):
            p = os.path.join(base, s, "illustration.json")
            if os.path.isfile(p):
                out.append((s, p))
    return out


def front_matter_lists(path, keys=("layers", "topics")):
    """The list fields KEYS of an article's front matter (inline [a, b] or "- a" lines);
    a key that is absent is left out."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.read().split("\n")
    except OSError:
        return {}
    out = {}
    if not lines or lines[0].strip() != "---":
        return out
    cur = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*(?:\s#\s.*)?$", line)
        if m:
            cur, val = m.group(1), m.group(2)
            if cur in keys:
                if val.startswith("[") and val.endswith("]"):
                    out[cur] = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
                else:
                    out[cur] = [val.strip("'\"")] if val else []
            continue
        if cur in keys and re.match(r"^\s+-\s+", line):
            out[cur].append(re.sub(r"^\s+-\s+", "", line).strip().strip("'\""))
    return out


def story_tints(article_dir):
    """The story tints an article's picture may use: the layer hues of its layers, tee
    for a runtime story or one about confidential computing, pcb for a hardware story.
    None when the article has no en.md or no layers (no check)."""
    fm = front_matter_lists(os.path.join(article_dir, "en.md"))
    if "layers" not in fm:
        return None
    layers, topics = fm["layers"], fm.get("topics", [])
    out = {l for l in layers if l in LAYER_HUES}
    if "runtime" in layers or "confidential-computing" in topics:
        out.add("tee")
    if "hardware" in layers:
        out.add("pcb")
    return out


def strict_svg(scene, path):
    """Draw a spec as --write and --check do: every composition rule enforced; returns
    the SVG bytes and the render report."""
    svg, rep = render(scene, strict=True, story=story_tints(os.path.dirname(path)))
    if rep["problems"]:
        raise SpecError("; ".join(rep["problems"]))
    return svg.encode("utf-8"), rep


def failure(slug, exc):
    """How --write and --check report a spec they cannot draw. A SpecError or a JSON error
    (both ValueErrors) says what to fix; anything else, such as a bug in a prop, also names
    its type. Either way the run goes on to the other specs."""
    if isinstance(exc, ValueError):
        return "%s: %s" % (slug, exc)
    return "%s: %s: %s" % (slug, type(exc).__name__, exc)


def cmd_write(root, slugs):
    media = os.path.join(root, "static", "media")
    todo = specs(root, slugs)
    if not todo:
        print("illustrate: no illustration specs found")
        return 0
    os.makedirs(media, exist_ok=True)
    bad = 0
    for slug, path in todo:
        try:
            data = load_json(path)
            scene = check_envelope(data, path)
            if scene is None:
                continue
            svg, rep = strict_svg(scene, path)
        except Exception as e:
            print("illustrate: " + failure(slug, e), file=sys.stderr)
            bad += 1
            continue
        for w in rep["warnings"]:
            print("illustrate: %s: warning: %s" % (slug, w), file=sys.stderr)
        out = os.path.join(media, slug + ".svg")
        old = open(out, "rb").read() if os.path.isfile(out) else None
        if old != svg:
            with open(out, "wb") as f:
                f.write(svg)
            print("wrote static/media/%s.svg (%.1f KB)" % (slug, len(svg) / 1024.0))
        if len(svg) > SIZE_WARN:
            print("illustrate: warning: %s.svg is %.1f KB (aim for under 40 KB)" % (slug, len(svg) / 1024.0), file=sys.stderr)
        digest = sha256(svg)
        if data.get("svg_sha256") != digest:
            data["svg_sha256"] = digest
            with open(path, "w", encoding="utf-8") as f:
                f.write(pretty_json(data) + "\n")
            print("updated %s svg_sha256" % os.path.relpath(path, root))
    return 1 if bad else 0


def cmd_check(root, slugs):
    media = os.path.join(root, "static", "media")
    todo = specs(root, slugs)
    problems = []
    seen = set()   # the drawings that a spec accounts for
    focal = {}
    drawn = 0
    for slug, path in todo:
        try:
            data = load_json(path)
            scene = check_envelope(data, path)
        except Exception as e:
            seen.add(slug + ".svg")   # a broken spec still owns its drawing: report the spec, not an orphan
            problems.append(failure(slug, e))
            continue
        if scene is None:
            continue   # a photo: nothing to draw, so a static/media/<slug>.svg left behind is an orphan
        seen.add(slug + ".svg")
        try:
            svg, _ = strict_svg(scene, path)
        except Exception as e:
            problems.append(failure(slug, e))
            continue
        drawn += 1
        focal.setdefault(focal_prop(scene), []).append(slug)
        out = os.path.join(media, slug + ".svg")
        if not os.path.isfile(out):
            problems.append("%s: static/media/%s.svg is missing (run tools/illustrate.py --write %s)" % (slug, slug, slug))
        elif open(out, "rb").read() != svg:
            problems.append("%s: static/media/%s.svg differs from a fresh draw (run tools/illustrate.py --write %s)" % (slug, slug, slug))
        if data.get("svg_sha256") != sha256(svg):
            problems.append("%s: svg_sha256 does not match the drawing (run tools/illustrate.py --write %s)" % (slug, slug))
    if not slugs and os.path.isdir(media):
        for name in sorted(os.listdir(media)):
            if name.endswith(".svg") and name not in seen:
                problems.append("static/media/%s has no illustration spec" % name)
    if focal and not slugs:
        print("illustrate: focal props: " + ", ".join("%s %d" % (k, len(v)) for k, v in
                                                       sorted(focal.items(), key=lambda kv: (-len(kv[1]), kv[0]))))
        for prop, used in sorted(focal.items()):
            cap = MAX_MAGNIFIER if prop == "magnifier" else MAX_FOCAL_USES
            if len(used) > cap:
                problems.append("%s is the focal prop of %d pictures (at most %d): %s; vary the motifs (see the motif "
                                "bank in tools/scene/README.md)" % (prop, len(used), cap, ", ".join(used)))
    for p in problems:
        print("illustrate: " + p, file=sys.stderr)
    if not drawn and not problems:
        print("illustrate: no illustration specs found")
    elif not problems:
        print("illustrate: %d illustration%s up to date" % (drawn, "" if drawn == 1 else "s"))
    return 1 if problems else 0


def focal_prop(scene):
    """The prop name of a scene's focal item."""
    want = scene.get("focal")

    def walk(items):
        for it in items or []:
            if isinstance(it, dict):
                if it.get("id") == want:
                    return it.get("prop")
                found = walk(it.get("items"))
                if found:
                    return found
        return None
    return walk(scene.get("items")) or "?"


def footprint_line(name):
    """A prop's size with its defaults, as the README's props reference prints it:
    "(about W wide, D deep, H tall)", in grid units, its front facing the lower left."""
    from scene.compose import validate
    pdef = REGISTRY[name]
    item = {"prop": name, "at": [0, 0]}
    if pdef.container:
        item["items"] = []
    n = validate({"items": [item]}).nodes[0]
    s0, s1, t0, t1, h0, h1 = n.bbox
    w, d = (s1 - s0, t1 - t0) if n.tf.r % 2 == 0 else (t1 - t0, s1 - s0)

    def num(v):
        return ("%.2f" % v if v < 0.095 else "%.1f" % v).rstrip("0").rstrip(".")
    return "(about %s wide, %s deep, %s tall)" % (num(w), num(d), num(h1))


def props_reference():
    """The README's props reference, generated from the registry (--props-md)."""
    from scene.kit import ALL, B
    out = []
    for group in GROUPS:
        out.append("### %s\n" % group)
        for name, d in REGISTRY.items():
            if d.group != group:
                continue
            tints = "any" if set(d.tints) >= set(t for t in ALL if t != "seal") else ", ".join("`%s`" % t for t in d.tints)
            b = B(d.tint, {k: (list(p.default) if isinstance(p.default, list) else p.default) for k, p in d.params.items()})
            d.fn(b)
            line = "**`%s`** %s %s Tints: %s; default `%s`." % (name, footprint_line(name), d.doc, tints, d.tint)
            if b.anchors:
                line += " Anchors: %s." % ", ".join("`%s`" % a for a in sorted(b.anchors))
            extra = (["Drawn flat on the floor, under the shadows."] if d.floor else []) + (["Holds its own `items`."] if d.container else [])
            if extra:
                line += " " + " ".join(extra)
            out.append(line)
            if d.params:
                out.append("")
                for k, p in d.params.items():
                    if k == "material":
                        out.append("- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `%s`)" % p.default)
                    else:
                        out.append("- `%s`: %s (%s)" % (k, p.doc, p.describe()))
            out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def find_chrome():
    env = os.environ.get("CHROME")
    if env:
        return env
    for c in ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Chromium.app/Contents/MacOS/Chromium"):
        if os.path.exists(c):
            return c
    for c in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(c)
        if p:
            return p
    raise SystemExit("illustrate: Google Chrome not found; set CHROME to its path")


def to_png(svg_text, png_path, width, height, view=None):
    """Screenshot the SVG at WIDTH x HEIGHT CSS px in headless Chrome. The files are
    copied to a temporary folder first (Chrome cannot always read synced folders)."""
    chrome = find_chrome()
    view = view or (width, height)
    tmp = tempfile.mkdtemp(prefix="illustrate-")
    try:
        with open(os.path.join(tmp, "a.svg"), "w", encoding="utf-8") as f:
            f.write(svg_text)
        with open(os.path.join(tmp, "a.html"), "w", encoding="utf-8") as f:
            f.write('<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;background:#fff}'
                    'img{display:block;width:%dpx;height:%dpx}</style></head><body><img src="a.svg" alt=""></body></html>'
                    % (width, height))
        out = os.path.join(tmp, "a.png")
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                        "--window-size=%d,%d" % view, "--screenshot=" + out, "file://" + os.path.join(tmp, "a.html")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60)
        shutil.copyfile(out, png_path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_spec(path, out, png, thumb, debug=False, layers=None):
    data = load_json(path)
    scene = data
    problems = []
    if isinstance(data, dict) and "kind" in data:
        if data["kind"] == "photo":
            raise SystemExit("illustrate: %s is a photo spec; nothing to draw" % path)
        try:
            scene = check_envelope(data, path)
        except SpecError as e:
            problems.append(str(e))
            scene = data.get("scene")
            if scene is None:   # nothing to draw: report what is wrong with the envelope
                if not str(e).endswith(": missing scene"):
                    problems.append("%s: missing scene" % path)
                raise SystemExit("\n".join("illustrate: " + p for p in problems))
    if layers is not None:
        names = [v.strip() for v in layers.split(",") if v.strip()]
        story = {v for v in names if v in LAYER_HUES}
        if "runtime" in names or "confidential-computing" in names:
            story.add("tee")
        if "hardware" in names:
            story.add("pcb")
    else:
        story = story_tints(os.path.dirname(os.path.abspath(path)))
    try:
        svg, rep = render(scene, strict=True, story=story, debug=debug)
    except SpecError as e:
        raise SystemExit("illustrate: %s: %s" % (path, e))
    problems += rep["problems"]
    line = "zoom %.2f; props cover %d%% of the width and %d%% of the height" % (
        rep["zoom"], round(rep["cover"][0] * 100), round(rep["cover"][1] * 100))
    if "focal" in rep:
        fc = rep["focal"]
        line += "; focal %r is %d x %d px (%d%% of the height), centred at (%d, %d)" % (
            fc["id"], fc["w"], fc["h"], round(100 * fc["h"] / 800.0), fc["center"][0], fc["center"][1])
    print(line)
    by = rep.get("covered_by", {})
    for v, k in sorted((v, k) for k, v in rep.get("visible", {}).items() if v < 0.8):
        print("partly hidden: %s shows %d%% of itself%s" % (k, round(v * 100), " (covered by %s)" % by[k] if k in by else ""))
    for w in rep["warnings"]:
        print("warning: " + w)
    for p in problems:
        print("problem: " + p)
    if story is None:
        print("note: no article layers found, so the story colours were not checked (use --layers)")
    if out:
        with open(out, "w", encoding="utf-8") as f:
            f.write(svg)
        print("wrote %s (%.1f KB)" % (out, len(svg.encode("utf-8")) / 1024.0))
    if png:
        to_png(svg, png, 1200, 800)
        print("wrote " + png)
    if thumb:
        to_png(svg, thumb, *THUMB)
        small = os.path.splitext(thumb)[0] + "-%d.png" % LIST_THUMB[0]
        to_png(svg, small, *LIST_THUMB)
        print("wrote %s and %s" % (thumb, small))
    return 1 if problems else 0


def _variants():
    """Labelled specs for the catalog's variant sections: (group, [(label, spec), ...])."""
    from scene.kit import SCREEN_KINDS

    def one(item, links=None, ground=None):
        sp = {"ground": ground or {"kind": "none"}, "items": [item] if isinstance(item, dict) else item}
        if links:
            sp["links"] = links
        return sp
    out = []
    out.append(("Screen content (monitor, laptop, phone, screen, panel, sheet: content)",
                [(k, one({"prop": "screen", "at": [0, 0], "content": k, "w": 2.2, "h": 1.4, "tint": "tee" if k in ("lock", "shield") else "neutral"}))
                 for k in SCREEN_KINDS]))
    out.append(("Photo: content, mark, tag",
                [("content " + c, one({"prop": "photo", "at": [0, 0], "content": c})) for c in ("landscape", "portrait", "video", "audio", "text")] +
                [("mark wave", one({"prop": "photo", "at": [0, 0], "mark": "wave"})), ("mark dots", one({"prop": "photo", "at": [0, 0], "mark": "dots"})),
                 ("tag tag (outputs)", one({"prop": "photo", "at": [0, 0], "tag": "tag", "tint": "outputs"})),
                 ("tag seal", one({"prop": "photo", "at": [0, 0], "tag": "seal"})), ("tag pin", one({"prop": "photo", "at": [0, 0], "tag": "pin", "tint": "tee"}))]))
    out.append(("Marks and icons",
                [("tool " + i, one({"prop": "tool", "at": [0, 0], "icon": i})) for i in ("gear", "terminal", "globe", "wrench", "search", "doc", "database", "mail")] +
                [("shield " + e, one({"prop": "shield", "at": [0, 0], "emblem": e})) for e in ("lock", "keyhole", "chip", "bars", "none")] +
                [("math_block " + m, one({"prop": "math_block", "at": [0, 0], "mark": m})) for m in ("turnstile", "brackets", "equals", "lambda", "sum", "arrow")] +
                [("magnifier reveal " + r, one({"prop": "magnifier", "at": [0, 0], "reveal": r, "tint": "outputs"})) for r in ("wave", "dots", "grid", "mark")] +
                [("magnifier turn 35", one({"prop": "magnifier", "at": [0, 0], "turn": 35}))] +
                [("agent core " + c, one({"prop": "agent", "at": [0, 0], "core": c})) for c in ("sphere", "cube", "face")] +
                [("agent glow", one({"prop": "agent", "at": [0, 0], "glow": True})), ("agent neutral face", one({"prop": "agent", "at": [0, 0], "core": "face", "tint": "neutral"})),
                 ("person neutral", one({"prop": "person", "at": [0, 0], "tint": "neutral"})), ("person tee", one({"prop": "person", "at": [0, 0], "tint": "tee"}))]))
    out.append(("Tints (server_rack, padlock, bars)",
                [("server_rack " + t, one({"prop": "server_rack", "at": [0, 0], "tint": t, "units": 4})) for t in ("neutral", "tee", "data", "dark")] +
                [("padlock " + t, one({"prop": "padlock", "at": [0, 0], "tint": t})) for t in REGISTRY["padlock"].tints if t != "dark"] +
                [("bars " + t, one({"prop": "bars", "at": [0, 0], "tint": t})) for t in ("models", "outputs", "agents", "evaluations", "institutions", "tee")]))
    a, b = {"prop": "box", "id": "a", "at": [-1.6, 0], "w": 0.7, "d": 0.7, "h": 0.5}, {"prop": "box", "id": "b", "at": [1.6, 0], "w": 0.7, "d": 0.7, "h": 0.5}
    ln = []
    for label, lk in (("straight data, packets 2", {"packets": 2}), ("dashed data, glow", {"style": "dashed", "glow": True}),
                      ("dotted tee", {"style": "dotted", "color": "tee"}), ("broken tee, gap .5", {"style": "broken", "color": "tee"}),
                      ("solid ink, arrow", {"color": "ink", "arrow": True}), ("dotted mute", {"style": "dotted", "color": "mute"}),
                      ("arc dotted, top to top", {"route": "arc", "color": "ink", "style": "dotted", "lift": 1.2, "from": "a.top", "to": "b.top"}),
                      ("dashed evaluations", {"style": "dashed", "color": "evaluations"}),
                      ("floor bend s", {"route": "floor", "from": "a", "to": [0.4, 1.8, 0], "bend": "s", "style": "dashed"}),
                      ("floor bend t", {"route": "floor", "from": "a", "to": [0.4, 1.8, 0], "bend": "t", "style": "dashed"}),
                      ("packets at .2 and .5", {"packets": [0.2, 0.5], "style": "dashed"})):
        link = {"from": "a", "to": "b"}
        link.update(lk)
        ln.append((label, one([dict(a), dict(b)], links=[link])))
    out.append(("Links (from a to b)", ln))
    out.append(("Grounds", [("plate", one({"prop": "box", "at": [0, 0]}, ground={"kind": "plate"})),
                            ("plate tint tee", one({"prop": "box", "at": [0, 0]}, ground={"kind": "plate", "tint": "tee"})),
                            ("tiles", one({"prop": "box", "at": [0, 0]}, ground={"kind": "tiles", "size": [5, 4]})),
                            ("desk", one({"prop": "box", "at": [0, 0]}, ground={"kind": "desk"})),
                            ("plate tint pcb", one({"prop": "chip", "at": [0, 0]}, ground={"kind": "plate", "tint": "pcb"}))]))
    return out


def catalog_svg():
    """Every prop with its default look, grouped, then the variants of content, marks,
    tints, links and grounds, each labelled (the catalog is an authoring aid, so unlike an
    illustration it carries words)."""
    from scene.compose import fragment
    from scene.svg import Defs
    cols, cw, ch, pad, head = 6, 250, 210, 24, 34
    defs = Defs()
    body = []
    y = pad
    sections = []
    for group in GROUPS:
        cells = []
        for name, pdef in REGISTRY.items():
            if pdef.group != group:
                continue
            item = {"prop": name, "at": [0, 0]}
            item.update(pdef.example)
            if pdef.container:
                item.update({"w": 3, "d": 2.4, "h": 1.8, "items": [{"prop": "server", "at": [0, 0], "tint": "tee", "w": 2, "d": 1.2}]})
            cells.append((name, {"ground": {"kind": "none"}, "items": [item]}))
        sections.append((group, cells))
    sections += _variants()
    for title, cells in sections:
        body.append('<text x="%d" y="%d" font-size="17" font-weight="600" fill="#2a2f35">%s</text>' % (pad, y + 20, title))
        y += head
        for i, (label, spec) in enumerate(cells):
            cx = pad + (i % cols) * cw
            cy = y + (i // cols) * ch
            body.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="#dde1e6"/>' % (cx, cy, cw - 10, ch - 10, FLOOR))
            frag, z = fragment(spec, (cx, cy, cw - 10, ch - 34), defs, max_zoom=1.0)
            body.append(frag)
            body.append('<text x="%d" y="%d" font-size="13" fill="#2a2f35" text-anchor="middle">%s%s</text>'
                        % (cx + (cw - 10) // 2, cy + ch - 18, label, "" if z > 0.99 else " (×%s)" % ("%.2f" % z).rstrip("0").rstrip(".")))
        y += ((len(cells) + cols - 1) // cols) * ch + pad
    width = pad * 2 + cols * cw - 10
    height = y
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
            'font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">' % (width, height, width, height)
            + defs.markup() + '<rect width="%d" height="%d" fill="#ffffff"/>' % (width, height) + "".join(body) + "</svg>\n"), (width, height)


def cmd_catalog(out, png):
    svg, (w, h) = catalog_svg()
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print("wrote %s (%d props, %.0f KB)" % (out, len(REGISTRY), len(svg.encode("utf-8")) / 1024.0))
    if png:
        to_png(svg, png, w, h)
        print("wrote " + png)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="draw static/media/<slug>.svg and update svg_sha256")
    g.add_argument("--check", action="store_true", help="exit 1 if a drawing or digest is stale")
    g.add_argument("--spec", metavar="FILE", help="draw one spec file (illustration.json or a bare scene)")
    g.add_argument("--catalog", metavar="OUT.svg", help="draw a sheet of every prop")
    g.add_argument("--props-md", action="store_true", help="print the props reference for tools/scene/README.md")
    ap.add_argument("slugs", nargs="*", help="articles to draw or check (default: all with a spec)")
    ap.add_argument("--out", help="with --spec: the SVG to write")
    ap.add_argument("--png", help="also render a 1200 x 800 PNG (needs Chrome)")
    ap.add_argument("--thumb", help="with --spec: also render a 240 x 160 PNG, and a 104 x 69 one beside it (needs Chrome)")
    ap.add_argument("--debug", action="store_true", help="with --spec: overlay the grid, footprints, ids and focal box")
    ap.add_argument("--layers", help="with --spec: the article's layers (and topics), comma-separated, for the colour check")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.write:
        return cmd_write(a.root, a.slugs)
    if a.check:
        return cmd_check(a.root, a.slugs)
    if a.props_md:
        sys.stdout.write(props_reference())
        return 0
    if a.spec:
        if not (a.out or a.png or a.thumb):
            ap.error("--spec needs --out, --png or --thumb")
        return cmd_spec(a.spec, a.out, a.png, a.thumb, a.debug, a.layers)
    return cmd_catalog(a.catalog, a.png)


if __name__ == "__main__":
    sys.exit(main())
