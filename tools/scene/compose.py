"""From a scene spec to an SVG: validation, placement, depth order, shadows, links,
framing, and the composition checks.

See tools/scene/README.md for the spec format. draw(scene) returns the SVG text and
validate(scene) raises SpecError with a message that names the item and the key.
render(scene, strict=True) also checks the composition the way tools/illustrate.py
--write does (a focal object large and central enough, no prop hidden behind another)
and returns a report with the picture's numbers, its problems and its warnings.
"""
import difflib
import math
import re
from array import array

from . import palette as P
from .iso import (C1, C2, FACINGS, K, LAMP_MAX, El, Glass, Glow, Outline, Part, Tf, add, bbox_screen, box_els, depth_sort,
                  fmt, fmt2, hull2, line, mul, poly, project, sub, union_bbox, unit)
from .kit import REGISTRY, B, SpecError
from .svg import Camera, Defs, Writer, screen_bounds, screen_shapes
from . import props, props2  # noqa: F401  (register the props)

W, H = 1200, 800
MARGIN = 12
FIT_X, FIT_Y, FIT_MAX = 64, 56, 2.2      # "fit": the whole drawing, plate included
ITEMS_X, ITEMS_Y, ITEMS_MAX = 48, 40, 3.0  # "items" (the default): the props, the plate runs off the canvas
FOCAL_MIN_H = 0.32 * H                   # the focal object's least height on screen (256 px) ...
FOCAL_MIN_W = 0.40 * W                   # ... or width, for a flat one (480 px)
FOCAL_BOX = (0.30 * W, 0.70 * W, 0.25 * H, 0.75 * H)   # where its centre must fall: the middle 40% x 50%
HIDDEN_MIN = 0.40                        # a prop must show at least this share of its own silhouette
LINK_COVER_MAX = 0.50                    # warn when more of a link than this is covered
SEG_LEN = 0.25                           # a sorted link's segments, in grid units
RASTER = 0.25                            # the occlusion check's buffer, as a share of the canvas
MAX_SEALS = 2                            # cinnabar marks per picture
LAYER_HUES = tuple(P.LAYERS)
SCENE_KEYS = ("version", "backdrop", "camera", "ground", "focal", "items", "links", "note")
ITEM_KEYS = ("prop", "id", "at", "at_uv", "on", "facing", "tint", "scale", "shadow", "outside", "allow_overlap",
             "allow_hidden", "items", "note")
GROUND_KEYS = ("kind", "size", "margin", "tint", "thickness", "note")
GROUND_KINDS = ("plate", "tiles", "desk", "none")
LINK_KEYS = ("from", "to", "route", "style", "color", "packets", "glow", "arrow", "lift", "via", "bend", "layer",
             "width", "gap", "note")
LINK_LAYERS = ("under", "depth", "over")
ID_RE = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


def _suggest(word, options):
    m = difflib.get_close_matches(str(word), list(options), 1)
    return "; did you mean %r?" % m[0] if m else ""


def _name(v, where):
    """A value that must be a name, checked before it is looked up (a list or an object
    there would otherwise fail the lookup with a TypeError instead of a SpecError)."""
    if not isinstance(v, str):
        raise SpecError("%s: expected a name, got %r" % (where, v))
    return v


def _num(v, where, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise SpecError("%s: expected a number, got %r" % (where, v))
    if not (lo <= v <= hi):
        raise SpecError("%s: %g is out of range (%g to %g)" % (where, v, lo, hi))
    return float(v)


def _keys(d, allowed, where):
    if not isinstance(d, dict):
        raise SpecError("%s: expected an object" % where)
    for k in d:
        if k not in allowed:
            raise SpecError("%s: unknown key %r%s (allowed: %s)" % (where, k, _suggest(k, allowed), ", ".join(allowed)))


# ----- nodes -----------------------------------------------------------------------------
class PropNode:
    def __init__(self, item, pdef, parts, anchors, b, tf, where):
        self.item, self.pdef, self.parts, self.anchors = item, pdef, parts, anchors
        self.b, self.tf, self.where = b, tf, where
        self.bbox = union_bbox([p.bbox for p in parts])
        self.children = []
        self.pre = self.post = None
        self.base = tf.d[2]
        self.label = where
        self.sil = None

    def part_boxes(self):
        boxes = [p.bbox for p in self.parts if p.bbox is not None]
        for ch in self.children:
            boxes += ch.part_boxes()
        return boxes

    def all_nodes(self):
        out = [self]
        for ch in self.children:
            out += ch.all_nodes()
        return out

    def tagged(self):
        """(owner, element) in painter's order; an enclosure's contents are their own owners."""
        out = []
        if self.b.outline and self.parts:
            out.append((self, Outline(self.parts)))
        if self.pre is not None:
            out += [(self, e) for e in self.pre.els]
        if self.children:
            for ch in depth_sort(self.children, lambda n: n.bbox, lambda n: n.part_boxes()):
                out += ch.tagged()
        parts = depth_sort(self.parts, lambda p: p.bbox) if len(self.parts) > 1 else self.parts
        for p in parts:
            out += [(self, e) for e in p.els]
        if self.post is not None:
            out += [(self, e) for e in self.post.els]
        return out

    def els(self):
        return [e for _, e in self.tagged()]


class Scene:
    def __init__(self):
        self.nodes = []       # top-level nodes
        self.by_id = {}
        self.ground_els = []
        self.ground_box = None
        self.ground_spec = None
        self.links = []
        self.backdrop = P.BACKDROPS["white"]
        self.zoom = "items"
        self.pan = (0.0, 0.0)
        self.focal = None

    def all_nodes(self):
        out = []
        for n in self.nodes:
            out += n.all_nodes()
        return out


# ----- items -----------------------------------------------------------------------------
def build_item(item, scene, where, inside=None):
    if not isinstance(item, dict):
        raise SpecError("%s: expected an object" % where)
    name = _name(item.get("prop"), where + ": prop")
    if name not in REGISTRY:
        raise SpecError("%s: unknown prop %r%s (see the catalog in tools/scene/README.md)"
                        % (where, name, _suggest(name, REGISTRY)))
    pdef = REGISTRY[name]
    _keys(item, ITEM_KEYS + tuple(pdef.params) + tuple(pdef.aliases), "%s (%s)" % (where, name))
    for old, new in sorted(pdef.aliases.items()):
        if old in item:
            if new in item:
                raise SpecError("%s (%s): give %r or its older name %r, not both" % (where, name, new, old))
            item = dict(item)
            item[new] = item.pop(old)
    iid = item.get("id")
    if iid is not None:
        if not isinstance(iid, str) or not ID_RE.match(iid):
            raise SpecError("%s: id %r must be lower case letters, digits, - or _, starting with a letter" % (where, iid))
        if iid in scene.by_id:
            raise SpecError("%s: id %r is used twice" % (where, iid))
        where = "%s (%s %r)" % (where, name, iid)
        label = "%s %r" % (name, iid)
    else:
        where = "%s (%s)" % (where, name)
        label = where
    # parameters
    params = {}
    for k, prm in pdef.params.items():
        params[k] = prm.check(item[k], "%s: %s" % (where, k)) if k in item else (
            list(prm.default) if isinstance(prm.default, list) else prm.default)
    tint = _name(item.get("tint", pdef.tint), where + ": tint")
    if tint not in pdef.tints:
        hint = " (cinnabar is for seals: only %s take it)" % ", ".join(P.SEAL_PROPS) if tint == "seal" else ""
        raise SpecError("%s: tint %r is not available for %s (choose from %s)%s%s"
                        % (where, tint, name, ", ".join(pdef.tints), _suggest(tint, pdef.tints), hint))
    facing = _name(item.get("facing", pdef.facings[0] if pdef.facings else "left"), where + ": facing")
    if facing not in FACINGS:
        raise SpecError("%s: facing %r is not one of %s%s" % (where, facing, ", ".join(FACINGS), _suggest(facing, FACINGS)))
    if pdef.facings and facing not in pdef.facings:
        raise SpecError("%s: %s can only face %s" % (where, name, " or ".join(pdef.facings)))
    scale = _num(item.get("scale", 1.0), where + ": scale", 0.25, 4.0)
    if "at" in item and "at_uv" in item:
        raise SpecError("%s: give either 'at' or 'at_uv', not both" % where)
    if "at_uv" in item:
        at = item["at_uv"]
        if not isinstance(at, list) or len(at) not in (2, 3):
            raise SpecError("%s: 'at_uv' must be [u, v] or [u, v, h] (u = s + t across, v = s - t down)" % where)
        u = _num(at[0], where + ": at_uv[0] (u)", -60, 60)
        v = _num(at[1], where + ": at_uv[1] (v)", -60, 60)
        s, t = (u + v) / 2.0, (u - v) / 2.0
        h = _num(at[2], where + ": at_uv[2] (h)", -5, 30) if len(at) == 3 else None
    else:
        at = item.get("at")
        if not isinstance(at, list) or len(at) not in (2, 3):
            raise SpecError("%s: 'at' must be [s, t] or [s, t, h] in grid units" % where)
        s = _num(at[0], where + ": at[0] (s)", -30, 30)
        t = _num(at[1], where + ": at[1] (t)", -30, 30)
        h = _num(at[2], where + ": at[2] (h)", -5, 30) if len(at) == 3 else None
    on = item.get("on")
    if on is not None:
        if h is not None:
            raise SpecError("%s: give either 'on' or a height in 'at', not both" % where)
        if _name(on, where + ": on") not in scene.by_id:
            raise SpecError("%s: 'on' names %r, which is not an earlier item's id%s" % (where, on, _suggest(on, scene.by_id)))
        h = scene.by_id[on].surface()
    if h is None:
        h = 0.0
    b = B(tint, params)
    pdef.fn(b)
    tf = Tf(FACINGS[facing], scale, (s, t, h))
    parts = [p.transformed(tf) for p in b.parts]
    anchors = {k: tf.point(v) for k, v in b.anchors.items()}
    node = PropNode(item, pdef, parts, anchors, b, tf, where)
    node.label = label
    node.tint = tint
    node.params = params
    node.lifted = b.lift * scale
    node.on = on
    node.surface = (lambda node=node, b=b, tf=tf: (tf.point((0, 0, b.surface))[2] if b.surface is not None
                                                     else node.bbox[5]))
    if iid:
        scene.by_id[iid] = node
    node.id = iid
    for key in ("shadow", "allow_hidden", "outside", "allow_overlap"):
        if key in item and not isinstance(item[key], bool):
            raise SpecError("%s: %s must be true or false" % (where, key))
    node.shadow = item.get("shadow", True)
    if pdef.container:
        kids = item.get("items", [])
        if not isinstance(kids, list):
            raise SpecError("%s: items must be a list" % where)
        glass = parts[0]
        node.parts = []
        gb = b.glassbox
        x0, y0, z0, x1, y1, z1 = gb
        a, c = tf.point((x0, y0, z0)), tf.point((x1, y1, z1))
        wbox = (min(a[0], c[0]), max(a[0], c[0]), min(a[1], c[1]), max(a[1], c[1]), min(a[2], c[2]), max(a[2], c[2]))
        node.pre = Part([e for e in glass.els if getattr(e, "which", "") == "back"])
        node.post = Part([e for e in glass.els if getattr(e, "which", "") != "back"])
        node.bbox = wbox
        for i, kid in enumerate(kids):
            kw = "%s.items[%d]" % (where, i)
            kn = build_item(kid, scene, kw, inside=node)
            kb = kn.bbox
            tol = 0.02
            if kb[0] < wbox[0] - tol or kb[1] > wbox[1] + tol or kb[2] < wbox[2] - tol or kb[3] > wbox[3] + tol \
                    or kb[4] < wbox[4] - tol or kb[5] > wbox[5] + tol:
                raise SpecError("%s: does not fit inside the enclosure (its box is s %.2f..%.2f, t %.2f..%.2f, h %.2f..%.2f;"
                                " the glass is s %.2f..%.2f, t %.2f..%.2f, h %.2f..%.2f)"
                                % ((kn.where,) + kb + wbox))
            node.children.append(kn)
        _check_overlaps(node.children)
    elif "items" in item:
        raise SpecError("%s: only an enclosure holds items" % where)
    return node


def _overlap(a, b, tol=0.03):
    return (a[0] < b[1] - tol and b[0] < a[1] - tol and a[2] < b[3] - tol and b[2] < a[3] - tol
            and a[4] < b[5] - tol and b[4] < a[5] - tol)


def _check_overlaps(nodes):
    solid = [n for n in nodes if not n.pdef.floor]
    for i, a in enumerate(solid):
        for b in solid[i + 1:]:
            if a.item.get("allow_overlap") or b.item.get("allow_overlap"):
                continue
            if a.on is not None and a.on == b.id or b.on is not None and b.on == a.id:
                continue
            if _overlap(a.bbox, b.bbox):
                raise SpecError("%s and %s overlap (boxes s %.2f..%.2f, t %.2f..%.2f and s %.2f..%.2f, t %.2f..%.2f): "
                                "move one, or set \"allow_overlap\": true on one if the drawing order still looks right"
                                % (a.where, b.where, a.bbox[0], a.bbox[1], a.bbox[2], a.bbox[3],
                                   b.bbox[0], b.bbox[1], b.bbox[2], b.bbox[3]))


# ----- colour rules ------------------------------------------------------------------------------
def _seal_marks(n):
    """How many cinnabar marks a prop carries."""
    name, p = n.pdef.name, n.params
    if name in P.SEAL_PROPS:
        return 1 if n.tint == "seal" else 0
    if name == "document" and p.get("seal") == "seal":
        return 1
    if name == "photo" and p.get("tag") == "seal" and n.tint != "tee":
        return 1
    if name == "book" and p.get("emblem") == "seal":
        return 1
    return 0


def _story_hues(n):
    """The story tints a prop uses: layer hues, tee and pcb."""
    out = set()
    if n.tint in LAYER_HUES or n.tint == "tee":
        out.add(n.tint)
    mat = n.params.get("material")
    if isinstance(mat, str):
        base = mat[:-5] if mat.endswith("light") else mat
        if base in LAYER_HUES or base in ("tee", "pcb"):
            out.add(base)
    return out


def check_colours(sc, links, ground_tint, story=None):
    """The palette's rules: at most MAX_SEALS cinnabar marks, one glow (small lamps aside), and,
    when STORY (the tints the article's layers allow) is given, no other story tint."""
    nodes = sc.all_nodes()
    seals = [n.label for n in nodes for _ in range(_seal_marks(n))]
    if len(seals) > MAX_SEALS:
        raise SpecError("scene: %d cinnabar marks (%s); cinnabar is for seals and signatures, at most %d per picture"
                        % (len(seals), ", ".join(seals), MAX_SEALS))
    glows = []
    for n in nodes:
        for p in n.parts:
            for e in p.els:
                if isinstance(e, Glow) and (not e.lamp or e.r > LAMP_MAX + 1e-9):
                    glows.append(n.label)
    for i, lk in enumerate(links):
        if lk.get("glow"):
            glows.append("links[%d]" % i)
    if len(glows) > 1:
        raise SpecError("scene: %d glows (%s); a picture keeps one glow, on its data path or its core, and lamps"
                        % (len(glows), ", ".join(glows)))
    if story is None:
        return
    allowed = sorted(story)
    for n in nodes:
        for hue in sorted(_story_hues(n)):
            if hue not in story:
                raise SpecError("%s: the %s tint marks a layer this story is not tagged with (its layers allow %s); "
                                "choose another tint" % (n.where, hue, ", ".join(allowed) or "none"))
    for i, lk in enumerate(links):
        c = lk.get("color", "data")
        if (c in LAYER_HUES or c == "tee") and c not in story:
            raise SpecError("links[%d]: the %s colour marks a layer this story is not tagged with (its layers allow %s)"
                            % (i, c, ", ".join(allowed) or "none"))
    if ground_tint in ("tee", "pcb") and ground_tint not in story:
        raise SpecError("ground: the %s tint marks a layer this story is not tagged with (its layers allow %s)"
                        % (ground_tint, ", ".join(allowed) or "none"))


# ----- ground ----------------------------------------------------------------------------------
def _plan(n):
    """A prop's plan-view rectangle (s0, s1, t0, t1): its footprint, else its box."""
    if n.b.footprint is not None and not n.pdef.container:
        x0, y0, x1, y1 = n.b.footprint
        a, c = n.tf.point((x0, y0, 0)), n.tf.point((x1, y1, 0))
        return (min(a[0], c[0]), max(a[0], c[0]), min(a[1], c[1]), max(a[1], c[1]))
    return n.bbox[:4]


def _items_extent(scene):
    """The plan-view extent (s0, s1, t0, t1) of the items standing on the ground."""
    boxes = [_plan(n) for n in scene.nodes if not n.item.get("outside", False)]
    if not boxes:
        return (-2.0, 2.0, -2.0, 2.0)
    return (min(b[0] for b in boxes), max(b[1] for b in boxes), min(b[2] for b in boxes), max(b[3] for b in boxes))


def parse_ground(g):
    if g is None:
        g = {}
    _keys(g, GROUND_KEYS, "ground")
    kind = _name(g.get("kind", "plate"), "ground: kind")
    if kind not in GROUND_KINDS:
        raise SpecError("ground: kind %r is not one of %s%s" % (kind, ", ".join(GROUND_KINDS), _suggest(kind, GROUND_KINDS)))
    size = g.get("size", "auto")
    margin = _num(g.get("margin", 0.8), "ground: margin", 0.2, 4)
    if size != "auto":
        if not isinstance(size, list) or len(size) != 2:
            raise SpecError("ground: size must be \"auto\" or [width along s, depth along t]")
        size = (_num(size[0], "ground: size[0]", 2, 24), _num(size[1], "ground: size[1]", 2, 24))
    tint = _name(g.get("tint", "neutral"), "ground: tint")
    if tint not in ("neutral", "tee", "pcb"):
        raise SpecError("ground: tint %r is not one of neutral, tee, pcb%s" % (tint, _suggest(tint, ("neutral", "tee", "pcb"))))
    th = _num(g.get("thickness", 0.38 if kind != "desk" else 0.22), "ground: thickness", 0.05, 2)
    return {"kind": kind, "size": size, "margin": margin, "tint": tint, "thickness": th}


def ground_box(gs, scene):
    if gs["size"] == "auto":
        m = gs["margin"]
        e0, e1, e2, e3 = _items_extent(scene)
        return (e0 - m, e1 + m, e2 - m, e3 + m)
    w, d = gs["size"]
    return (-w / 2.0, w / 2.0, -d / 2.0, d / 2.0)


def build_ground(gs, box, scene, defs, bleed=False):
    """The ground's elements for plan box BOX = (s0, s1, t0, t1). BLEED: the plate runs off
    the canvas, so it casts no shadow of its own."""
    kind, tint, th = gs["kind"], gs["tint"], gs["thickness"]
    scene.ground_kind = kind
    if kind == "none":
        scene.ground_box = None
        scene.ground_els = []
        return
    s0, s1, t0, t1 = box
    w, d = s1 - s0, t1 - t0
    scene.ground_box = box
    els = []
    lift = 1.6 if kind == "desk" else 0.0
    if not bleed:
        # the soft shadow under the whole plate, as the hero's hv-ground
        sh = [(s0 + 0.3, t0 - 0.1, -th - lift), (s1 + 0.9, t0 - 0.1, -th - lift), (s1 + 0.9, t1, -th - lift), (s0 + 0.3, t1, -th - lift)]
        els.append(poly(sh, n=(0, 0, 1), cull=False, fill=P.SHADOW, op=0.2, filter=defs.blur("sg", 14)))
    if tint == "tee":
        mat, top0, top1, edge = P.M["tplate"], P.TPLATE_TOP0, P.TPLATE_TOP1, P.TPLATE_EDGE
    elif tint == "pcb":
        mat, top0, top1, edge = P.M["pcb"], "#2f7550", "#2a6b45", "#1d4a31"
    else:
        mat, top0, top1, edge = P.M["plate"], P.PLATE_TOP0, P.PLATE_TOP1, P.PLATE_EDGE
    grad = defs.lin("gt" + tint, 0, 0, 0, 1, [(0.2, top0, None), (0.9, top1, None)])
    if kind == "desk":
        mat = P.Mat("#f1f2f4", "#d9dde2", "#c3c9d0", None, "desk")
        grad = defs.lin("gdesk", 0, 0, 0, 1, [(0.2, "#eceef1", None), (0.9, "#f7f8f9", None)])
        lw = 0.22
        for (ls, lt) in ((s0 + 0.35, t0 + 0.35), (s1 - 0.35, t0 + 0.35), (s1 - 0.35, t1 - 0.35)):
            els += [e for e in box_els(ls - lw / 2, lt - lw / 2, -th - lift, ls + lw / 2, lt + lw / 2, -th, P.M["steel"], lip=None)]
    for e in box_els(s0, t0, -th, s1, t1, 0.0, mat, lip=None, seam=True):
        if e.n is not None and e.n[2] > 0.5:
            e.st["fill"] = mat
            e.st["grad"] = grad
            e.st.pop("seam", None)
            e.st["stroke"] = edge
            e.st["sw"] = 0.9
        els.append(e)
    els.append(line([(s0, t0, 0.0), (s1, t0, 0.0), (s1, t1, 0.0)], stroke=P.LIP, sw=1.4, join="round", cap="round"))
    if kind == "tiles":
        n_s, n_t = int(round(w / 1.5)), int(round(d / 1.5))
        for i in range(1, n_s):
            ss = s0 + w * i / n_s
            els.append(line([(ss, t0, 0.0), (ss, t1, 0.0)], stroke="#dde1e6", sw=0.9))
        for j in range(1, n_t):
            tt = t0 + d * j / n_t
            els.append(line([(s0, tt, 0.0), (s1, tt, 0.0)], stroke="#dde1e6", sw=0.9))
    scene.ground_els = els


# ----- shadows ---------------------------------------------------------------------------------
def node_shadow(n):
    """Soft shadows on the surface under a prop: for each of its parts, the part's
    footprint and the footprint pushed toward the lower right, more for taller parts.
    A prop that declares a footprint casts one shadow from it instead."""
    if not n.shadow or not n.b.shadow or n.bbox is None:
        return []
    base = n.tf.d[2]
    floating = getattr(n, "lifted", 0.0) > 0
    if floating:
        base = n.tf.d[2] - n.lifted
    if n.b.footprint is not None:
        boxes = [_plan(n) + (base, n.bbox[5])]
    else:
        boxes = [p.bbox for p in n.parts if p.bbox is not None and p.bbox[5] - base > 0.03]
    out = []
    for x, y, r in n.b.contacts:
        c = n.tf.point((x, y, 0.0))
        rr = r * n.tf.k
        out.append(([(c[0] + rr * math.cos(i * math.pi / 6), c[1] + rr * math.sin(i * math.pi / 6), base + 0.002)
                     for i in range(12)], 1.0))
    for s0, s1, t0, t1, h0, h1 in boxes:
        hgt = max(0.0, min(h1 - base, 4.0))
        push = 0.1 + 0.22 * hgt
        r = [(s0 - 0.04, t0 - 0.04), (s1 + 0.04, t0 - 0.04), (s1 + 0.04, t1 + 0.04), (s0 - 0.04, t1 + 0.04)]
        pushed = [(x + push, y + push * 0.25) for x, y in r]
        out.append(([(x, y, base + 0.002) for x, y in hull2(r + pushed)], 0.55 if floating else 1.0))
    return out


# ----- links -----------------------------------------------------------------------------------
def anchor_point(ref, scene, where):
    """A link end: (point, node, anchor name). The anchor name is '' for a bare item id
    and None for a point [s, t, h]."""
    if isinstance(ref, list):
        if len(ref) != 3:
            raise SpecError("%s: a point must be [s, t, h]" % where)
        return tuple(_num(v, where, -30, 30) for v in ref), None, None
    if not isinstance(ref, str):
        raise SpecError("%s: expected an item id, 'id.anchor' or [s, t, h]" % where)
    iid, _, anc = ref.partition(".")
    if iid not in scene.by_id:
        raise SpecError("%s: no item has id %r%s" % (where, iid, _suggest(iid, scene.by_id)))
    n = scene.by_id[iid]
    allp = node_anchors(n)
    if not anc:
        return allp["base"], n, ""
    if anc not in allp:
        raise SpecError("%s: %s has no anchor %r (it has %s)%s" % (where, iid, anc, ", ".join(sorted(allp)), _suggest(anc, allp)))
    return allp[anc], n, anc


def node_anchors(n):
    """Every anchor of a placed prop: base, top, center, front (the middle of its front
    face, after turning) and the prop's own."""
    s0, s1, t0, t1, h0, h1 = n.bbox
    std = {
        "base": ((s0 + s1) / 2, (t0 + t1) / 2, h0),
        "top": ((s0 + s1) / 2, (t0 + t1) / 2, h1),
        "center": ((s0 + s1) / 2, (t0 + t1) / 2, (h0 + h1) / 2),
    }
    fv = n.tf.vec((0, -1, 0))
    if fv[1] < -0.5:
        std["front"] = ((s0 + s1) / 2, t0, (h0 + h1) / 2)
    elif fv[0] > 0.5:
        std["front"] = (s1, (t0 + t1) / 2, (h0 + h1) / 2)
    elif fv[1] > 0.5:
        std["front"] = ((s0 + s1) / 2, t1, (h0 + h1) / 2)
    else:
        std["front"] = (s0, (t0 + t1) / 2, (h0 + h1) / 2)
    std.update(n.anchors)
    return std


def _inside(p, r, pad=0.0):
    return r[0] - pad <= p[0] <= r[1] + pad and r[2] - pad <= p[1] <= r[3] + pad


def _trim_end(pts, r, pad=0.12):
    """Cut the end of a floor polyline where it enters rectangle R (grown by PAD), so a
    link stops at the edge of the prop it points to."""
    if not _inside(pts[-1], r, pad):
        return pts
    for i in range(len(pts) - 1, 0, -1):
        a, b = pts[i - 1], pts[i]
        if not _inside(a, r, pad):
            lo, hi = 0.0, 1.0
            for _ in range(40):
                m = (lo + hi) / 2.0
                q = _lerp(a, b, m)
                if _inside(q, r, pad):
                    hi = m
                else:
                    lo = m
            return pts[:i] + [_lerp(a, b, lo)]
    return pts


def _lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f)


UNIT = Camera(K, 0.0, 0.0)   # zoom 1, no offset: silhouettes before the camera is chosen


def _silhouette(n):
    """A prop's opaque shapes on screen at zoom 1, each with its bounds (cached)."""
    if n.sil is None:
        out = []
        for _, e in n.tagged():
            for shape in screen_shapes(e, UNIT):
                shape = [q for q in shape if len(q) >= 3]
                if shape:
                    xs = [x for q in shape for x, _ in q]
                    ys = [y for q in shape for _, y in q]
                    out.append(((min(xs), max(xs), min(ys), max(ys)), shape))
        n.sil = out
    return n.sil


def _in_silhouette(n, p):
    x, y = UNIT.p(p)
    for (x0, x1, y0, y1), shape in _silhouette(n):
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        inside = False
        for q in shape:
            j = len(q) - 1
            for i in range(len(q)):
                xi, yi = q[i]
                xj, yj = q[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
        if inside:
            return True
    return False


def _walk(pts, step=0.04):
    """Points along a polyline about STEP apart: (segment index, fraction, point)."""
    out = [(0, 0.0, pts[0])]
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        k = max(1, int(math.ceil(_dist(a, b) / step)))
        out += [(i, j / float(k), _lerp(a, b, j / float(k))) for j in range(1, k + 1)]
    return out


TUCK = 0.06   # how far a floor link runs under the prop it stops at, so its cap hides


def _trim_silhouette(pts, n):
    """Cut the end of a floor polyline where it meets prop N's silhouette on screen (when
    it ends inside it, where it last comes out from behind it; otherwise where it first
    touches it), tucked a little under the prop. Unchanged if it never touches it."""
    w = _walk(pts)
    inside = [_in_silhouette(n, q) for _, _, q in w]
    cut = None
    if inside[-1]:
        for k in range(len(w) - 1, 0, -1):
            if not inside[k - 1]:
                cut = k
                break
    elif not inside[0]:
        cut = next((k for k in range(1, len(w)) if inside[k]), None)
    if cut is None:
        return pts
    (i0, f0, q0), (i1, f1, q1) = w[cut - 1], w[cut]
    for _ in range(24):
        m = _lerp(q0, q1, 0.5)
        if _in_silhouette(n, m):
            q1 = m
        else:
            q0 = m
    seg = sub(pts[i1 + 1], pts[i1])
    L = math.sqrt(dot3(seg, seg))
    q = add(q1, mul(seg, TUCK / L)) if L > 1e-9 else q1
    return pts[:i1 + 1] + [q]


def dot3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _trim_floor(pts, n, at_end):
    """Stop a floor polyline at prop N (its end, or its start when AT_END is false): an
    enclosure at its glass, any other prop at its silhouette."""
    if not at_end:
        return list(reversed(_trim_floor(list(reversed(pts)), n, True)))
    if n.pdef.container:
        return _trim_end(pts, _plan(n))
    return _trim_silhouette(pts, n)


def _box_hit(p, n):
    """Where the segment from P toward the centre of N's box first meets the box."""
    s0, s1, t0, t1, h0, h1 = n.bbox
    c = ((s0 + s1) / 2, (t0 + t1) / 2, (h0 + h1) / 2)
    lo, hi = 0.0, 1.0
    for j, (a0, a1) in enumerate(((s0, s1), (t0, t1), (h0, h1))):
        d = c[j] - p[j]
        if abs(d) < 1e-12:
            if not (a0 <= p[j] <= a1):
                return c
            continue
        u0, u1 = (a0 - p[j]) / d, (a1 - p[j]) / d
        lo, hi = max(lo, min(u0, u1)), min(hi, max(u0, u1))
    return _lerp(p, c, max(0.0, min(1.0, lo)))


def _top_end(p, n):
    """Whether P sits on the top of N's box, inside its outline (an arc must come down
    onto it from above)."""
    if n is None:
        return False
    s0, s1, t0, t1, h0, h1 = n.bbox
    return s0 + 0.05 < p[0] < s1 - 0.05 and t0 + 0.05 < p[1] < t1 - 0.05 and p[2] >= h1 - 0.06


def _on_floor(p, n):
    """Whether P lies on, or just above, the surface N stands on (or, for a point, the
    ground): a magnifier's tip, the middle of its handle's end, counts."""
    base = 0.0 if n is None else n.tf.d[2] - getattr(n, "lifted", 0.0)
    return -0.02 < p[2] - base < 0.1


def _dist(a, b):
    return math.sqrt(sum((b[i] - a[i]) ** 2 for i in range(3)))


def _polyline_len(pts):
    return sum(_dist(a, b) for a, b in zip(pts, pts[1:]))


def _point_at(pts, f):
    total = _polyline_len(pts)
    target = total * f
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = _dist(a, b)
        if acc + seg >= target and seg > 0:
            k = (target - acc) / seg
            return tuple(a[i] + (b[i] - a[i]) * k for i in range(3)), unit(sub(b, a))
        acc += seg
    return pts[-1], unit(sub(pts[-1], pts[-2]))


def _sub_polyline(pts, f0, f1, n=20):
    return [_point_at(pts, f0 + (f1 - f0) * k / float(n))[0] for k in range(n + 1)]


def _bezier_pts(p0, p1, p2, p3, n=24):
    out = []
    for i in range(n + 1):
        t = i / float(n)
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append(tuple(a * p0[j] + b * p1[j] + c * p2[j] + d * p3[j] for j in range(3)))
    return out


def _rounded(pts, r=0.35):
    """Commands for a polyline with its corners rounded by quadratic-like cubics."""
    if len(pts) < 3:
        return [("M", pts[0])] + [("L", p) for p in pts[1:]]
    cmds = [("M", pts[0])]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        rr = min(r, _dist(a, b) / 2.0, _dist(b, c) / 2.0)
        if rr <= 1e-6:
            cmds.append(("L", b))
            continue
        p = add(b, mul(unit(sub(a, b)), rr))
        q = add(b, mul(unit(sub(c, b)), rr))
        cmds.append(("L", p))
        cmds.append(("C", add(p, mul(sub(b, p), 0.55)), add(q, mul(sub(b, q), 0.55)), q))
    cmds.append(("L", pts[-1]))
    return cmds


def _cmd_points(cmds, steps=6):
    """Points along 3D path commands (curves sampled)."""
    out = []
    for c in cmds:
        if c[0] in ("M", "L"):
            out.append(c[1])
        elif c[0] == "C":
            out += _bezier_pts(out[-1], c[1], c[2], c[3], steps)[1:]
    return out


def _unit_len(a, b):
    """The length of a segment on screen at zoom K = 1."""
    pa, pb = project(a, 1.0), project(b, 1.0)
    return math.hypot(pb[0] - pa[0], pb[1] - pa[1])


CORNER = 0.15        # a floor route's corner radius, as the hero's traces
BREAK_HALF = 0.24    # half the gap of a broken link, in units at least
ARC_STUB = 0.6       # an arc meets a top anchor straight from above, over this height
LINK_KMAX = 2 * K    # a link's weight grows with the zoom up to zoom 2 (about 4 px)


class Packet:
    """A packet a link carries: drawn as a small cube, and checked like a prop."""

    def __init__(self, link, j, f):
        self.link, self.j, self.f = link, j, f
        self.label = "packet %d of %s" % (j + 1, link.label)
        self.id = None
        self.on = None


class Link:
    """A connector, ready to draw: its pieces (polylines), its stroke, the bits it
    carries (packets, an arrow, the stubs of a broken link) and, for a link sorted with
    the props, its segments."""

    def __init__(self, i, label, layer, ends):
        self.i, self.label, self.layer, self.ends = i, label, layer, ends
        self.pieces = []      # 3D polylines
        self.path_cmds = []   # commands to draw each piece in one go (under, over)
        self.st = {}
        self.glow = None      # the glow element
        self.bits = []        # (elements, box, owner): owner is the link or a Packet
        self.packets = []
        self.segments = []    # (piece index, points, box, screen length before it)
        self.main = {}        # id of each element that draws the line itself -> (piece, screen length before it)
        self.corners = None   # a floor route's polyline before its corners are rounded
        self.warnings = []

    def split(self):
        for pi, pts in enumerate(self.pieces):
            acc = 0.0
            cur = [pts[0]]
            run = 0.0
            start_len = 0.0
            for a, b in zip(pts, pts[1:]):
                cur.append(b)
                run += _dist(a, b)
                acc += _unit_len(a, b)
                if run >= SEG_LEN:
                    self._add(pi, cur, start_len)
                    cur = [b]
                    run = 0.0
                    start_len = acc
            if len(cur) > 1:
                self._add(pi, cur, start_len)

    def _add(self, pi, pts, start_len):
        xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
        self.segments.append((pi, list(pts), (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)), start_len))

    def run_el(self, pi, pts, start_len):
        st = dict(self.st)
        if "dashu" in st:
            st["dashoffu"] = start_len
        return self.mark(El([("M", pts[0])] + [("L", p) for p in pts[1:]], **st), pi, start_len)

    def mark(self, e, pi=0, start_len=0.0):
        self.main[id(e)] = (pi, start_len)
        return e


def _via_point(v, scene, where):
    if isinstance(v, str):
        return anchor_point(v, scene, where)[0]
    if not isinstance(v, list) or len(v) != 3:
        raise SpecError("%s must be [s, t, h] or 'id.anchor'" % where)
    return tuple(_num(x, where, -30, 30) for x in v)


def build_link(lk, scene, i):
    where = "links[%d]" % i
    _keys(lk, LINK_KEYS, where)
    if "from" not in lk or "to" not in lk:
        raise SpecError("%s: needs 'from' and 'to'" % where)
    route = _name(lk.get("route", "straight"), where + ": route")
    routes = ("straight", "floor", "arc", "via")
    if route not in routes:
        raise SpecError("%s: route %r is not one of %s%s" % (where, route, ", ".join(routes), _suggest(route, routes)))
    style = _name(lk.get("style", "solid"), where + ": style")
    styles = ("solid", "dashed", "dotted", "broken")
    if style not in styles:
        raise SpecError("%s: style %r is not one of %s%s" % (where, style, ", ".join(styles), _suggest(style, styles)))
    color = _name(lk.get("color", "data"), where + ": color")
    if color not in P.LINK_COLORS:
        hint = " (cinnabar is for seals, never a link)" if color == "seal" else ""
        raise SpecError("%s: color %r is not one of %s%s%s" % (where, color, ", ".join(P.LINK_COLORS),
                                                              _suggest(color, P.LINK_COLORS), hint))
    a, na, aa = anchor_point(lk["from"], scene, where + ": from")
    b, nb, ba = anchor_point(lk["to"], scene, where + ": to")
    # a bare item id takes the prop's own contact point (its port), when it has one
    bare = set()
    if aa == "" and na.b.port:
        a, aa = na.anchors[na.b.port], na.b.port
        bare.add(id(na))
    if ba == "" and nb.b.port:
        b, ba = nb.anchors[nb.b.port], nb.b.port
        bare.add(id(nb))

    def ref_bare(n):
        return id(n) in bare
    width = _num(lk.get("width", 1.0), where + ": width", 0.5, 3)
    packets = lk.get("packets", 0)
    if isinstance(packets, list):
        if len(packets) > 6:
            raise SpecError("%s: packets: at most 6 positions" % where)
        fs = [_num(f, "%s: packets[%d]" % (where, j), 0.05, 0.95) for j, f in enumerate(packets)]
    elif isinstance(packets, bool) or not isinstance(packets, int) or not 0 <= packets <= 6:
        raise SpecError("%s: packets must be a whole number from 0 to 6, or a list of positions along the link "
                        "(0.05 to 0.95)" % where)
    else:
        fs = [(j + 1) / float(packets + 1) for j in range(packets)]
    glow = lk.get("glow", False)
    arrow = lk.get("arrow", False)
    for k, v in (("glow", glow), ("arrow", arrow)):
        if not isinstance(v, bool):
            raise SpecError("%s: %s must be true or false" % (where, k))
    gap = _num(lk.get("gap", 0.5), where + ": gap", 0.1, 0.9)
    if "bend" in lk and route != "floor":
        raise SpecError("%s: bend is for the floor route only (add \"route\": \"floor\")" % where)

    def trimmable(anc, n):
        """A floor link aims at a bare id's base (or its port) and stops where it meets the
        prop on screen; a named anchor is met exactly."""
        return anc in ("", "base") or (n is not None and anc == n.b.port and ref_bare(n))
    on_floor = False
    if route == "floor":
        # an L along the floor: on the plate, or on the surface both props stand on
        same = na is not None and nb is not None and abs(na.tf.d[2] - nb.tf.d[2]) < 1e-6
        h = 0.012 + (na.tf.d[2] if same else 0.0)
        bend = _name(lk.get("bend", "s"), where + ": bend")
        if bend not in ("s", "t"):
            raise SpecError("%s: bend must be s (along s first) or t" % where)
        a2, b2 = (a[0], a[1], h), (b[0], b[1], h)
        corner = (b[0], a[1], h) if bend == "s" else (a[0], b[1], h)
        pts = [a2, corner, b2]
        if abs(a[0] - b[0]) < 1e-6 or abs(a[1] - b[1]) < 1e-6:
            pts = [a2, b2]
        on_floor = True
    elif route == "straight" and _on_floor(a, na) and _on_floor(b, nb) and abs(a[2] - b[2]) < 0.1:
        # both ends on the floor (a port may sit just above it): one segment along it
        h = min(a[2], b[2]) + 0.012
        pts = [(a[0], a[1], h), (b[0], b[1], h)]
        on_floor = True
    if on_floor:
        # stop at the props at either end (not under them)
        if nb is not None and trimmable(ba, nb):
            pts = _trim_floor(pts, nb, True)
        if na is not None and trimmable(aa, na):
            pts = _trim_floor(pts, na, False)
        link_pts = pts
        cmds = _rounded(pts, CORNER)
        dense = _cmd_points(cmds)
    elif route == "straight":
        # in space: a bare id without a port is met where the line reaches its box
        if ba == "":
            b = _box_hit(a, nb)
        if aa == "":
            a = _box_hit(b, na)
        cmds = [("M", a), ("L", b)]
        n = max(2, int(math.ceil(_dist(a, b) / (SEG_LEN / 2))))
        dense = [_lerp(a, b, k / float(n)) for k in range(n + 1)]
    elif route == "arc":
        lift = _num(lk.get("lift", 1.5), where + ": lift", 0, 10)
        if aa == "":
            a = node_anchors(na)["top"]
        if ba == "":
            b = node_anchors(nb)["top"]
        # an end on a prop's top is met straight from above, so the arc clears the prop
        a_top, b_top = _top_end(a, na), _top_end(b, nb)
        a1 = (a[0], a[1], a[2] + ARC_STUB) if a_top else a
        b1 = (b[0], b[1], b[2] + ARC_STUB) if b_top else b
        p1 = (a1[0], a1[1], a1[2] + lift)
        p2 = (b1[0], b1[1], b1[2] + lift)
        cmds = [("M", a)] + ([("L", a1)] if a_top else []) + [("C", p1, p2, b1)] + ([("L", b)] if b_top else [])
        dense = ([a] if a_top else []) + _bezier_pts(a1, p1, p2, b1, 32) + ([b] if b_top else [])
    else:
        via = lk.get("via")
        if not isinstance(via, list) or not via:
            raise SpecError("%s: route via needs 'via': a list of [s, t, h] points or 'id.anchor' names" % where)
        vpts = [_via_point(v, scene, "%s: via[%d]" % (where, j)) for j, v in enumerate(via)]
        if ba == "":
            b = _box_hit(vpts[-1], nb)
        if aa == "":
            a = _box_hit(vpts[0], na)
        cmds = _rounded([a] + vpts + [b], 0.3)
        dense = _cmd_points(cmds)
    if _polyline_len(dense) < 0.05:
        raise SpecError("%s: the link has no length (its ends meet)" % where)
    layer = _name(lk.get("layer", "under" if on_floor else "depth"), where + ": layer")
    if layer not in LINK_LAYERS:
        raise SpecError("%s: layer %r is not one of %s%s" % (where, layer, ", ".join(LINK_LAYERS), _suggest(layer, LINK_LAYERS)))

    def name(ref):
        return ref if isinstance(ref, str) else "[%s]" % ", ".join(fmt2(v) for v in ref)
    link = Link(i, "%s (%s to %s)" % (where, name(lk["from"]), name(lk["to"])), layer, (na, nb))
    if route == "floor":
        link.corners = link_pts
    dense = _resample(dense, SEG_LEN / 2.0)
    _through_ends(link, dense)
    stroke, glowc = P.LINK_COLORS[color]
    sw = 0.055 * width
    st = {"fill": None, "stroke": stroke, "swu": sw, "cap": "round", "join": "round", "body": False, "kmax": LINK_KMAX}
    if style == "dashed":
        st["dashu"] = (sw * 2.6, sw * 2.2)
        st["cap"] = "butt"
    elif style == "dotted":
        st["dashu"] = (0.1 / K, sw * 2.6)
    link.st = st
    if glow and glowc:
        link.glow = El(cmds, fill=None, stroke=glowc, swu=sw * 5.5, sop=0.28, cap="round", join="round", body=False,
                       kmax=LINK_KMAX)
    if style == "broken":
        half = max(0.07, BREAK_HALF / max(1e-6, _polyline_len(dense)))
        g0, g1 = max(0.02, gap - half), min(0.98, gap + half)
        link.pieces = [_sub_polyline(dense, 0.0, g0), _sub_polyline(dense, g1, 1.0)]
        link.path_cmds = [[("M", p[0])] + [("L", q) for q in p[1:]] for p in link.pieces]
        # the two stubs' end bars
        for f in (g0, g1):
            p, dvec = _point_at(dense, f)
            perp = unit((-dvec[1], dvec[0], 0.0)) if abs(dvec[2]) < 0.9 else (1.0, 0.0, 0.0)
            e0, e1 = add(p, mul(perp, 0.16)), add(p, mul(perp, -0.16))
            bar = El([("M", e0), ("L", e1)], fill=None, stroke=stroke, swu=sw, cap="round", body=False, kmax=LINK_KMAX)
            link.bits.append(([bar], _pts_box([e0, e1]), link))
    else:
        link.pieces = [dense]
        link.path_cmds = [cmds]
    if arrow:
        p, dvec = _point_at(dense, 1.0)
        back = add(p, mul(dvec, -0.42))
        perp = unit((-dvec[1], dvec[0], 0.0)) if abs(dvec[2]) < 0.9 else (1.0, 0.0, 0.0)
        tri = [p, add(back, mul(perp, 0.22)), add(back, mul(perp, -0.22))]
        link.bits.append(([poly(tri, n=(0, 0, 1), cull=False, fill=stroke, stroke=stroke, sw=1, join="round")], _pts_box(tri),
                          link))
    pk_color = {"data": P.M["data"], "tee": P.M["tee"]}.get(color, P.M[color] if color in LAYER_HUES else P.M["steel"])
    for j, f in enumerate(fs):
        if style == "broken" and abs(f - gap) < 0.1:
            continue
        p, _ = _point_at(dense, f)
        sz = 0.22 * min(1.4, width)
        c = (p[0], p[1], p[2] - (sz / 2.0 if not on_floor else 0.0))
        box = (c[0] - sz / 2, c[1] - sz / 2, c[2], c[0] + sz / 2, c[1] + sz / 2, c[2] + sz)
        pk = Packet(link, j, f)
        link.packets.append(pk)
        link.bits.append((box_els(*box, pk_color, lip="#ffffff"), (box[0], box[3], box[1], box[4], box[2], box[5]), pk))
    if layer == "depth":
        link.split()
    return link


def _through_ends(link, dense):
    """Warn when a link runs inside one of the parts of the prop it starts or ends at, away
    from that end: it then seems to leave or enter the prop through a side."""
    na, nb = link.ends
    acc = [0.0]
    for p, q in zip(dense, dense[1:]):
        acc.append(acc[-1] + _dist(p, q))
    total = acc[-1]
    for n, which, near in ((na, "start", lambda d: d <= SEG_LEN), (nb, "end", lambda d: total - d <= SEG_LEN)):
        if n is None or n.pdef.container:
            continue
        e = 0.03
        boxes = [b for b in n.part_boxes() if b is not None]
        for p, d in zip(dense, acc):
            if near(d):
                continue
            if any(s0 + e < p[0] < s1 - e and t0 + e < p[1] < t1 - e and h0 + e < p[2] < h1 - e
                   for s0, s1, t0, t1, h0, h1 in boxes):
                if which == "end":
                    link.warnings.append("%s: it enters %s through a side; end it at an anchor on the prop's surface "
                                         "(an arc at its top, which it then meets from above)" % (link.label, n.label))
                else:
                    link.warnings.append("%s: it leaves %s through a side; start it at an anchor on the prop's surface"
                                         % (link.label, n.label))
                break


def _pts_box(pts):
    xs, ys, zs = [p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


# ----- scene -----------------------------------------------------------------------------------
def validate(scene, story=None):
    """Build everything a draw needs, raising SpecError on any problem; returns the Scene."""
    return _build(scene, story)[0]


def _build(spec, story=None):
    if not isinstance(spec, dict):
        raise SpecError("scene: expected an object")
    _keys(spec, SCENE_KEYS, "scene")
    if spec.get("version", 1) != 1:
        raise SpecError("scene: version must be 1")
    sc = Scene()
    defs = Defs()
    bd = _name(spec.get("backdrop", "white"), "scene: backdrop")
    if bd not in P.BACKDROPS:
        raise SpecError("scene: backdrop %r is not one of %s" % (bd, ", ".join(P.BACKDROPS)))
    sc.backdrop = P.BACKDROPS[bd]
    cam = spec.get("camera", {})
    _keys(cam, ("zoom", "pan", "note"), "camera")
    z = cam.get("zoom", "items")
    sc.zoom = z if z in ("fit", "items") else _num(z, "camera: zoom (a number, \"fit\" or \"items\")", 0.3, 3.0)
    pan = cam.get("pan", [0, 0])
    if not isinstance(pan, list) or len(pan) != 2:
        raise SpecError("camera: pan must be [x, y] in pixels")
    sc.pan = (_num(pan[0], "camera: pan[0]", -400, 400), _num(pan[1], "camera: pan[1]", -300, 300))
    items = spec.get("items")
    if not isinstance(items, list) or not items:
        raise SpecError("scene: items must be a non-empty list")
    if len(items) > 40:
        raise SpecError("scene: %d items; keep a scene to 40 or fewer (few, large objects read best)" % len(items))
    for i, it in enumerate(items):
        node = build_item(it, sc, "items[%d]" % i)
        sc.nodes.append(node)
    _check_overlaps(sc.nodes)
    focal = spec.get("focal")
    if focal is not None:
        if _name(focal, "scene: focal") not in sc.by_id:
            raise SpecError("scene: focal names %r, which is not an item's id%s" % (focal, _suggest(focal, sc.by_id)))
        sc.focal = sc.by_id[focal]
    gs = parse_ground(spec.get("ground"))
    sc.ground_spec = gs
    sc.ground_kind = gs["kind"]
    sc.ground_box = ground_box(gs, sc) if gs["kind"] != "none" else None   # drawn once the camera is set
    # props on the ground must stand on the plate unless marked outside
    if sc.ground_box is not None:
        g0, g1, g2, g3 = sc.ground_box
        for n in sc.nodes:
            if n.on is None and abs(n.tf.d[2]) < 1e-6 and not n.item.get("outside", False):
                bb = _plan(n)
                if bb[0] < g0 - 0.05 or bb[1] > g1 + 0.05 or bb[2] < g2 - 0.05 or bb[3] > g3 + 0.05:
                    raise SpecError("%s stands off the ground plate (its footprint is s %.2f..%.2f, t %.2f..%.2f; the plate is "
                                    "s %.2f..%.2f, t %.2f..%.2f): move it, enlarge the ground, or set \"outside\": true"
                                    % (n.where, bb[0], bb[1], bb[2], bb[3], g0, g1, g2, g3))
    links = spec.get("links", [])
    if not isinstance(links, list):
        raise SpecError("scene: links must be a list")
    for i, lk in enumerate(links):
        sc.links.append(build_link(lk, sc, i))
    check_colours(sc, links, gs["tint"] if gs["kind"] != "none" else None, story)
    return sc, defs


def _sequence(sc):
    """Every element in painter's order, as (layer, [(owner, element), ...]): ground,
    floor props, shadows, links under the props (and the glows of sorted links), the
    props with the sorted links' runs among them, links over the props. Shadows are
    (points, opacity) pairs, drawn as one group. An owner is a PropNode, a Link or None."""
    floor_nodes = [n for n in sc.nodes if n.pdef.floor]
    solid = [n for n in sc.nodes if not n.pdef.floor]
    shadow_polys = []
    for n in solid:
        for m in n.all_nodes():
            shadow_polys += node_shadow(m)
    seq = [("ground", [(None, e) for e in sc.ground_els])]
    fl = []
    for n in floor_nodes:
        fl += n.tagged()
    seq.append(("floor", fl))
    seq.append(("shadow", shadow_polys))
    under, over = [], []
    for lk in sc.links:
        if lk.glow is not None:
            under.append((lk, lk.glow))
        if lk.layer == "depth":
            continue
        dest = under if lk.layer == "under" else over
        for pi, cmds in enumerate(lk.path_cmds):
            dest.append((lk, lk.mark(El(cmds, **dict(lk.st)), pi)))
        for els, _, own in lk.bits:
            dest += [(own, e) for e in els]
    seq.append(("under", under))
    # the props and the sorted links' segments and bits, in one painter's order
    things = [("node", n, n.bbox) for n in solid]
    for lk in sc.links:
        if lk.layer != "depth":
            continue
        for j, sg in enumerate(lk.segments):
            things.append(("seg", (lk, j), sg[2]))
        for els, box, own in lk.bits:
            things.append(("bit", (own, els), box))
    order = _gather(depth_sort(things, lambda t: t[2], lambda t: t[1].part_boxes() if t[0] == "node" else None))
    body = []
    run = None   # (link, piece, [points], start length, first and last segment index)

    def flush():
        if run is not None:
            lk, pi, pts, start, _, _ = run
            body.append((lk, lk.run_el(pi, pts, start)))
    for kind, obj, _ in order:
        if kind == "seg":
            lk, j = obj
            pi, pts, box, start = lk.segments[j]
            if run is not None and run[0] is lk and run[1] == pi and run[5] == j - 1:
                run = (lk, pi, run[2] + pts[1:], run[3], run[4], j)
                continue
            if run is not None and run[0] is lk and run[1] == pi and run[4] == j + 1:
                run = (lk, pi, pts[:-1] + run[2], start, j, run[5])
                continue
            flush()
            run = (lk, pi, list(pts), start, j, j)
            continue
        flush()
        run = None
        if kind == "node":
            body += obj.tagged()
        else:
            lk, els = obj
            body += [(lk, e) for e in els]
    flush()
    seq.append(("body", body))
    seq.append(("over", over))
    return seq


def _gather(order):
    """Bring each link segment next to its neighbour on the same piece when nothing drawn
    between them overlaps it on screen (swapping items that do not overlap leaves the
    picture unchanged), so a link is drawn in as few runs as its depth allows."""
    order = list(order)
    scr = {id(t): bbox_screen(t[2]) for t in order}

    def overlaps(a, b):
        sa, sb = scr[id(a)], scr[id(b)]
        return not (sa[1] <= sb[0] + 0.01 or sb[1] <= sa[0] + 0.01 or sa[3] <= sb[2] + 0.01 or sb[3] <= sa[2] + 0.01)
    i = 0
    while i < len(order):
        t = order[i]
        if t[0] == "seg":
            lk, j = t[1]
            pi = lk.segments[j][0]
            for p in range(i - 1, -1, -1):
                u = order[p]
                if u[0] == "seg" and u[1][0] is t[1][0] and abs(u[1][1] - j) == 1 and lk.segments[u[1][1]][0] == pi:
                    if p < i - 1:
                        order.insert(p + 1, order.pop(i))
                    break
                if overlaps(u, t):
                    break
        i += 1
    return order


def _bounds(pairs, cam):
    bx = []
    for _, e in pairs:
        b = screen_bounds(e, cam)
        if b is not None:
            bx.append(b)
    if not bx:
        return (0.0, 1.0, 0.0, 1.0)
    return (min(b[0] for b in bx), max(b[1] for b in bx), min(b[2] for b in bx), max(b[3] for b in bx))


def _framed(seq, with_ground):
    out = []
    for name, els in seq:
        if name == "shadow" or (name == "ground" and not with_ground):
            continue
        out += els
    return out


def _paint(seq, cam, defs):
    wr = Writer(cam, defs)
    for name, els in seq:
        if name == "shadow":
            if not els:
                continue
            wr.raw('<g fill="%s" opacity=".16" filter="%s">' % (P.SHADOW, defs.blur("ss%d" % int(round(max(2.0, 0.14 * cam.k))),
                                                                                       max(2.0, 0.14 * cam.k))))
            for pts, op in els:
                d = "M" + "L".join("%s %s" % (fmt(x), fmt(y)) for x, y in (cam.p(p) for p in pts)) + "Z"
                wr.raw('<path d="%s"%s/>' % (d, "" if op >= 1 else ' opacity="%s"' % fmt2(op)))
            wr.raw("</g>")
            continue
        for _, e in els:
            wr.el(e)
    return wr.markup()


def _bleed_box(sc, cam):
    """The plate's plan box when it runs off the canvas: its two back edges stay where the
    props put them (plus the margin), its front edges move past the canvas's bottom corners."""
    s0, s1, t0, t1 = ground_box(sc.ground_spec, sc)

    def plan(x, y):
        u = (x - cam.ox) / (cam.k * C1)
        v = (y - cam.oy) / (cam.k * C2)
        return (u + v) / 2.0, (u - v) / 2.0
    pad = 0.6
    s_bl, t_bl = plan(0.0, H)
    s_br, t_br = plan(W, H)
    return (min(s0, s_bl - pad), max(s1, s_br + pad), min(t0, t_bl - pad), max(t1, t_br + pad))


def _camera(sc, defs, check_bounds):
    """Choose the zoom and offset; with the items camera, let the plate run off the canvas."""
    gs = sc.ground_spec
    build_ground(gs, ground_box(gs, sc), sc, Defs())   # the hugging plate, for framing
    seq = _sequence(sc)
    items_cam = sc.zoom == "items"
    with_ground = not items_cam or gs["kind"] == "desk"
    framed = _framed(seq, with_ground)
    x0, x1, y0, y1 = _bounds(framed, Camera(K, 0.0, 0.0))
    if sc.zoom in ("fit", "items"):
        fx, fy, zmax = (ITEMS_X, ITEMS_Y, ITEMS_MAX) if items_cam else (FIT_X, FIT_Y, FIT_MAX)
        zoom = min(zmax, (W - 2 * fx) / max(1e-6, x1 - x0), (H - 2 * fy) / max(1e-6, y1 - y0))
    else:
        zoom = sc.zoom
        framed = _framed(seq, True)
        x0, x1, y0, y1 = _bounds(framed, Camera(K, 0.0, 0.0))
    k = K * zoom
    x0, x1, y0, y1 = x0 * zoom, x1 * zoom, y0 * zoom, y1 * zoom
    ox = W / 2.0 - (x0 + x1) / 2.0 + sc.pan[0]
    oy = H / 2.0 - (y0 + y1) / 2.0 + sc.pan[1]
    if check_bounds and (x0 + ox < MARGIN or x1 + ox > W - MARGIN or y0 + oy < MARGIN or y1 + oy > H - MARGIN):
        fit = min((W - 2 * MARGIN) / max(1e-6, x1 - x0), (H - 2 * MARGIN) / max(1e-6, y1 - y0)) * zoom
        raise SpecError("scene: the drawing runs off the 1200 x 800 canvas (it spans %d x %d px at zoom %s, plus pan "
                        "%s, %s); it fits at zoom %.2f or less without pan"
                        % (int(x1 - x0), int(y1 - y0), fmt2(zoom), fmt(sc.pan[0]), fmt(sc.pan[1]),
                           math.floor(fit * 100) / 100.0))
    cam = Camera(k, ox, oy)
    sc.bleed = items_cam and gs["kind"] in ("plate", "tiles") and gs["size"] == "auto"
    build_ground(gs, _bleed_box(sc, cam) if sc.bleed else ground_box(gs, sc), sc, defs, bleed=sc.bleed)
    seq[0] = ("ground", [(None, e) for e in sc.ground_els])
    sc.zoom_used = zoom
    return seq, cam


# ----- composition checks ----------------------------------------------------------------------
def _spans(shape, gw, gh):
    """Even-odd scanline spans (row, x0, x1) of a shape (polygons in buffer pixels)."""
    rows = {}
    for pts in shape:
        n = len(pts)
        for i in range(n):
            ax, ay = pts[i]
            bx, by = pts[(i + 1) % n]
            if ay == by:
                continue
            if ay > by:
                ax, ay, bx, by = bx, by, ax, ay
            r0 = max(0, int(math.ceil(ay - 0.5)))
            r1 = min(gh - 1, int(math.ceil(by - 0.5)) - 1)
            if r1 < r0:
                continue
            slope = (bx - ax) / (by - ay)
            for r in range(r0, r1 + 1):
                rows.setdefault(r, []).append(ax + (r + 0.5 - ay) * slope)
    for r, xs in rows.items():
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            c0 = max(0, int(math.ceil(xs[i] - 0.5)))
            c1 = min(gw, int(math.ceil(xs[i + 1] - 0.5)))
            if c1 > c0:
                yield r, c0, c1


def _analyse(sc, seq, cam, rep):
    """Rasterize the props and the links' packets in painter's order into an owner buffer
    at RASTER scale; report props that show less than HIDDEN_MIN of themselves, packets
    that are hidden or touch a prop, links that are mostly covered, and link ends that
    stop short of their props."""
    gw, gh = int(W * RASTER), int(H * RASTER)
    scam = Camera(cam.k * RASTER, cam.ox * RASTER, cam.oy * RASTER)
    owners = array("h", [-1]) * (gw * gh)
    orders = array("i", [-1]) * (gw * gh)
    nodes = [n for n in sc.all_nodes() if not n.pdef.floor]
    packets = [pk for lk in sc.links for pk in lk.packets]
    things = nodes + packets
    index = {id(n): i for i, n in enumerate(things)}
    sil = {}
    samples = []    # (link, point, order, (piece, length along it))
    pos = 0
    for name, els in seq:
        if name == "shadow":
            continue
        for owner, e in els:
            pos += 1
            if owner is None or id(owner) not in index:
                continue
            oi = index[id(owner)]
            for shape in screen_shapes(e, scam):
                if not shape:
                    continue
                buf = sil.get(oi)
                if buf is None:
                    buf = sil[oi] = bytearray(gw * gh)
                for r, c0, c1 in _spans(shape, gw, gh):
                    i0, i1 = r * gw + c0, r * gw + c1
                    owners[i0:i1] = array("h", [oi]) * (i1 - i0)
                    orders[i0:i1] = array("i", [pos]) * (i1 - i0)
                    buf[i0:i1] = b"\x01" * (i1 - i0)
    # where each link's samples sit in the painter's order
    pos = 0
    for name, els in seq:
        if name == "shadow":
            continue
        for owner, e in els:
            pos += 1
            if isinstance(owner, Link) and id(e) in owner.main:
                pi, along = owner.main[id(e)]
                prev = None
                for p in _resample(_cmd_points(e.cmds), 0.1):
                    if prev is not None:
                        along += _unit_len(prev, p)
                    prev = p
                    samples.append((owner, p, pos, (pi, along)))

    def family(n):
        """N, what it holds (an enclosure's contents) and what stands on it."""
        out = {index[id(m)] for m in n.all_nodes() if id(m) in index}
        out |= {index[id(m)] for m in nodes if m.on is not None and n.id is not None and m.on == n.id}
        return out

    def main_cover(oi, ok):
        buf = sil[oi]
        cover = {}
        for i in range(gw * gh):
            if buf[i] and owners[i] not in ok and owners[i] >= 0:
                cover[owners[i]] = cover.get(owners[i], 0) + 1
        return max(sorted(cover), key=lambda o: cover[o]) if cover else None

    visible, covered_by = {}, {}
    for oi, n in enumerate(things):
        buf = sil.get(oi)
        if buf is None:
            continue
        total = buf.count(1)
        if total < 4 and not isinstance(n, Packet):
            continue
        ok = {oi} if isinstance(n, Packet) else family(n)
        seen = sum(owners.count(o) for o in ok)
        share = seen / float(max(1, total))
        if isinstance(n, Packet):
            if share < PACKET_MIN:
                by = main_cover(oi, ok)
                rep["problems"].append("%s shows only %d%% of itself%s: move it along the link with \"packets\": "
                                       "[positions from 0.05 to 0.95]" % (n.label, int(round(share * 100)),
                                                                          " (%s covers it)" % things[by].label if by is not None else ""))
            continue
        visible[n.label] = share
        if share < 0.8:
            by = main_cover(oi, ok)
            if by is not None:
                covered_by[n.label] = things[by].label
        if share < HIDDEN_MIN and not n.item.get("allow_hidden"):
            by = main_cover(oi, ok)
            rep["problems"].append("%s shows only %d%% of itself%s: move it, or set \"allow_hidden\": true if that is the point"
                                   % (n.where, int(round(share * 100)),
                                      "; %s covers it" % things[by].label if by is not None else ""))
    rep["visible"] = visible
    rep["covered_by"] = covered_by
    # packets: none may touch a prop other than the ones its link joins
    for pk in packets:
        oi = index[id(pk)]
        if oi not in sil:
            continue
        b = _bounds([(pk, e) for e in _packet_els(pk)], cam)
        ends = set()
        for n in pk.link.ends:
            if n is not None:
                ends |= family(n)
        near = _near_pixels(b, PACKET_GAP, gw, gh)
        hit = None
        for i in near:
            o = None
            for oj, buf in sorted(sil.items()):
                if oj != oi and oj not in ends and not isinstance(things[oj], Packet) and buf[i]:
                    o = oj
                    break
            if o is not None:
                hit = o
                break
        if hit is not None:
            rep["warnings"].append("%s touches %s (it comes within %d px of it): move it along the link with \"packets\": "
                                   "[positions from 0.05 to 0.95]" % (pk.label, things[hit].label, PACKET_GAP))
    # links: share covered, covered ends, and ends that stop short of their props
    for lk in sc.links:
        pts = [(p, o) for l2, p, o, key in sorted((x for x in samples if x[0] is lk), key=lambda x: x[3])]
        own = set()
        for n in lk.ends:
            if n is not None and id(n) in index:
                own |= family(n)
        own |= {index[id(pk)] for pk in lk.packets}
        msgs = []
        if pts:
            cov = []
            for p, o in pts:
                x, y = scam.p(p)
                xi, yi = int(x), int(y)
                if 0 <= xi < gw and 0 <= yi < gh:
                    i = yi * gw + xi
                    cov.append(owners[i] if orders[i] > o and owners[i] not in own else -1)
                else:
                    cov.append(-1)
            share = sum(1 for c in cov if c >= 0) / float(len(cov))
            if share > LINK_COVER_MAX:
                msgs.append("%d%% of it is hidden behind props" % int(round(share * 100)))
            for label, c in (("its start", cov[0]), ("its end", cov[-1])):
                if c >= 0:
                    msgs.append("%s is hidden behind %s" % (label, things[c].label))
        if msgs:
            rep["warnings"].append("%s: %s" % (lk.label, "; ".join(msgs)))
        for which, n, p in (("start", lk.ends[0], lk.pieces[0][0]), ("end", lk.ends[1], lk.pieces[-1][-1])):
            if n is None:
                continue
            d = _gap_to(n, family(n), p, cam, sil, gw)
            if d > END_GAP:
                x, y = cam.p(p)
                anchors = sorted(k for k in n.anchors)
                rep["problems"].append("%s: its %s stops %s px from %s (at %d, %d), on empty floor: %s"
                                       % (lk.label, which, "%d" % d if d < 1e8 else "far", n.label, x, y,
                                          "name one of its anchors (%s)" % ", ".join(anchors) if anchors
                                          else "move the props closer or change the route"))


PACKET_MIN = 0.80    # a packet must show this share of itself
PACKET_GAP = 6       # px: how close a packet may come to a prop its link does not join
END_GAP = 10         # px: how far a link's end may stop from the prop it names


def _packet_els(pk):
    for els, _, own in pk.link.bits:
        if own is pk:
            return els
    return []


def _near_pixels(b, pad, gw, gh):
    """Buffer pixels whose centres lie within PAD px of screen box B."""
    x0, x1, y0, y1 = b
    c0, c1 = max(0, int((x0 - pad) * RASTER)), min(gw - 1, int((x1 + pad) * RASTER))
    r0, r1 = max(0, int((y0 - pad) * RASTER)), min(gh - 1, int((y1 + pad) * RASTER))
    out = []
    for r in range(r0, r1 + 1):
        cy = (r + 0.5) / RASTER
        dy = max(0.0, y0 - cy, cy - y1)
        for c in range(c0, c1 + 1):
            cx = (c + 0.5) / RASTER
            dx = max(0.0, x0 - cx, cx - x1)
            if dx * dx + dy * dy <= pad * pad:
                out.append(r * gw + c)
    return out


def _gap_to(n, fam, p, cam, sil, gw):
    """How far point P (on the canvas) lies from the outline of prop N (with what it
    holds and what stands on it): its silhouette, or, for glass and a gate's field, the
    translucent faces it draws. (A prop in front of both is the covered-end warning's
    business.)"""
    x, y = cam.p(p)
    best = 1e9
    half = 0.5 / RASTER
    for o in sorted(fam):
        buf = sil.get(o)
        if buf is None:
            continue
        i = buf.find(1)
        while i >= 0:
            r, c = divmod(i, gw)
            d = math.hypot((c + 0.5) / RASTER - x, (r + 0.5) / RASTER - y) - half
            if d < best:
                best = d
            i = buf.find(1, i + 1)
    # translucent faces: glass, a field (not in the owner buffer)
    for m in n.all_nodes():
        for _, e in m.tagged():
            for poly in _translucent(e, cam):
                if _point_in(poly, x, y):
                    return 0.0
                for (ax, ay), (bx, by) in zip(poly, poly[1:] + poly[:1]):
                    best = min(best, _seg_dist(x, y, ax, ay, bx, by))
    return max(0.0, best)


def _translucent(e, cam):
    """Screen polygons of an element's see-through faces (glass, a scanning field)."""
    out = []
    if isinstance(e, Glass):
        for x in e.els():
            if x.st.get("fill") is not None and x.n is not None:
                out.append([cam.p(c[1]) for c in x.cmds if c[0] in ("M", "L")])
    elif isinstance(e, El) and e.st.get("fill") is not None and e.st.get("fop") is not None and e.st["fop"] < 0.5:
        pts = [cam.p(c[1]) for c in e.cmds if c[0] in ("M", "L")]
        if len(pts) >= 3:
            out.append(pts)
    return out


def _point_in(poly, x, y):
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def _seg_dist(x, y, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    f = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
    return math.hypot(ax + f * dx - x, ay + f * dy - y)


HOOK_MIN = 24        # px: both legs of a floor route longer than this, and it may not double back
CROSS_CLEAR = 24     # px: links may meet near their ends, not cross away from them


def _route_checks(sc, cam, rep):
    """Warnings about the links' shapes on screen: a floor route that doubles back (its
    corner turns through more than a right angle, as every L whose legs run toward the
    front and back does in this projection), and two links that cross."""
    for lk in sc.links:
        if lk.corners is None or len(lk.corners) < 3:
            continue
        sp = [cam.p(p) for p in lk.corners]
        for a, b, c in zip(sp, sp[1:], sp[2:]):
            l1, l2 = math.hypot(b[0] - a[0], b[1] - a[1]), math.hypot(c[0] - b[0], c[1] - b[1])
            if l1 > HOOK_MIN and l2 > HOOK_MIN and (b[0] - a[0]) * (c[0] - b[0]) < 0:
                rep["warnings"].append("%s: this floor route doubles back on screen (x %d, %d, %d); use the straight "
                                       "route, or a via point" % (lk.label, a[0], b[0], c[0]))
                break
    lines = []
    for lk in sc.links:
        pl = []
        for piece in lk.pieces:
            pl.append([cam.p(p) for p in piece])
        ends = [cam.p(lk.pieces[0][0]), cam.p(lk.pieces[-1][-1])]
        lines.append((lk, pl, ends))
    for i, (la, pa, ea) in enumerate(lines):
        for lb, pb, eb in lines[i + 1:]:
            hit = _crossing(pa, pb, ea + eb)
            if hit is not None:
                rep["warnings"].append("%s and %s cross at (%d, %d): move a prop, or route one around the other"
                                       % (la.label, lb.label, hit[0], hit[1]))


def _crossing(pa, pb, ends):
    def box(q):
        xs, ys = [x for x, _ in q], [y for _, y in q]
        return min(xs), max(xs), min(ys), max(ys)
    for qa in pa:
        ba = box(qa)
        for qb in pb:
            bb = box(qb)
            if ba[1] < bb[0] or bb[1] < ba[0] or ba[3] < bb[2] or bb[3] < ba[2]:
                continue
            for (a0, a1) in zip(qa, qa[1:]):
                for (b0, b1) in zip(qb, qb[1:]):
                    x = _seg_cross(a0, a1, b0, b1)
                    if x is not None and all(math.hypot(x[0] - e[0], x[1] - e[1]) > CROSS_CLEAR for e in ends):
                        return x
    return None


def _seg_cross(p, p2, q, q2):
    rx, ry = p2[0] - p[0], p2[1] - p[1]
    sx, sy = q2[0] - q[0], q2[1] - q[1]
    den = rx * sy - ry * sx
    if abs(den) < 1e-9:
        return None
    t = ((q[0] - p[0]) * sy - (q[1] - p[1]) * sx) / den
    u = ((q[0] - p[0]) * ry - (q[1] - p[1]) * rx) / den
    if 0.0 <= t <= 1.0 and 0.0 <= u <= 1.0:
        return (p[0] + t * rx, p[1] + t * ry)
    return None


def _resample(pts, step):
    """PTS with long steps cut into pieces of at most about STEP."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        d = _dist(a, b)
        n = max(1, int(math.ceil(d / step - 1e-9)))
        for k in range(1, n + 1):
            out.append(tuple(a[j] + (b[j] - a[j]) * k / float(n) for j in range(3)))
    return out


def _focal(sc, cam, rep):
    n = sc.focal
    b = _bounds(n.tagged(), cam)
    w, h = b[1] - b[0], b[3] - b[2]
    cx, cy = (b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0
    rep["focal"] = {"id": n.id, "box": b, "w": w, "h": h, "center": (cx, cy)}
    if h < FOCAL_MIN_H and w < FOCAL_MIN_W:
        rep["problems"].append("focal %s is %d px tall and %d px wide (%d%% of the picture's height); make it at least %d px "
                               "tall, or %d px wide for a flat object: enlarge it, drop a prop, or move the others closer"
                               % (n.label, h, w, int(round(100 * h / H)), FOCAL_MIN_H, FOCAL_MIN_W))
    x0, x1, y0, y1 = FOCAL_BOX
    if not (x0 <= cx <= x1 and y0 <= cy <= y1):
        rep["problems"].append("focal %s is centred at (%d, %d); its centre must fall in the middle of the picture, x %d to %d "
                               "and y %d to %d: move it toward the middle of the props, or balance them around it"
                               % (n.label, cx, cy, x0, x1, y0, y1))


# ----- debug overlay ---------------------------------------------------------------------------
def _overlay(sc, cam):
    """Draft-only marks: the s/t grid with its numbers, each prop's footprint and id, and
    the focal object's box. Uses text, so it is never part of a published picture."""
    out = ['<g fill="none" font-family="Menlo,monospace" font-size="12">']
    e = _items_extent(sc)
    s0, s1, t0, t1 = e[0] - 2, e[1] + 2, e[2] - 2, e[3] + 2
    if sc.ground_box is not None:
        g = sc.ground_box
        s0, s1, t0, t1 = max(s0, g[0]), min(s1, g[1]), max(t0, g[2]), min(t1, g[3])

    def P2(p):
        x, y = cam.p(p)
        return "%s %s" % (fmt(x), fmt(y))

    def label(x, y, text, color):
        return ('<text x="%s" y="%s" fill="%s" stroke="#ffffff" stroke-width="3" paint-order="stroke" '
                'text-anchor="middle">%s</text>' % (fmt(x), fmt(y), color, text))
    grid = []
    for s in range(int(math.ceil(s0)), int(math.floor(s1)) + 1):
        grid.append("M%sL%s" % (P2((s, t0, 0)), P2((s, t1, 0))))
    for t in range(int(math.ceil(t0)), int(math.floor(t1)) + 1):
        grid.append("M%sL%s" % (P2((s0, t, 0)), P2((s1, t, 0))))
    out.append('<path d="%s" stroke="#2f6fd0" stroke-opacity=".35" stroke-width="1"/>' % "".join(grid))
    for s in range(int(math.ceil(s0)), int(math.floor(s1)) + 1):
        x, y = cam.p((s, t0, 0))
        if 0 < x < W and 0 < y < H:
            out.append(label(x - 10, y + 14, "s%d" % s, "#2f6fd0"))
    for t in range(int(math.ceil(t0)), int(math.floor(t1)) + 1):
        x, y = cam.p((s1, t, 0))
        if 0 < x < W and 0 < y < H:
            out.append(label(x + 10, y + 14, "t%d" % t, "#2f6fd0"))
    for n in sc.all_nodes():
        r = _plan(n)
        h = n.tf.d[2] - getattr(n, "lifted", 0.0)
        pts = [(r[0], r[2], h), (r[1], r[2], h), (r[1], r[3], h), (r[0], r[3], h)]
        out.append('<path d="M%sZ" stroke="#c2255c" stroke-width="1.5" stroke-dasharray="5 3"/>'
                   % "L".join(P2(p) for p in pts))
        top = ((r[0] + r[1]) / 2, (r[2] + r[3]) / 2, n.bbox[5])
        x, y = cam.p(top)
        out.append(label(x, y - 8, n.id or n.pdef.name, "#c2255c"))
    if sc.focal is not None:
        b = _bounds(sc.focal.tagged(), cam)
        out.append('<rect x="%s" y="%s" width="%s" height="%s" stroke="#0b7f81" stroke-width="2"/>'
                   % (fmt(b[0]), fmt(b[2]), fmt(b[1] - b[0]), fmt(b[3] - b[2])))
    x0, x1, y0, y1 = FOCAL_BOX
    out.append('<rect x="%s" y="%s" width="%s" height="%s" stroke="#0b7f81" stroke-dasharray="4 4"/>'
               % (fmt(x0), fmt(y0), fmt(x1 - x0), fmt(y1 - y0)))
    out.append("</g>")
    return "".join(out)


# ----- drawing ---------------------------------------------------------------------------------
def render(spec, strict=False, story=None, analyse=None, debug=False, check_bounds=True):
    """Draw SPEC and check its composition. Returns (svg, report): the report holds the
    zoom, how much of the canvas the props cover, the focal object's size and centre,
    each prop's visible share, and lists of problems (which --write refuses) and
    warnings. STRICT requires a focal object; ANALYSE (default: STRICT) runs the
    occlusion checks; STORY is the set of story tints the article's layers allow."""
    sc, defs = _build(spec, story)
    seq, cam = _camera(sc, defs, check_bounds)
    rep = {"zoom": sc.zoom_used, "problems": [], "warnings": []}
    x0, x1, y0, y1 = _bounds(_framed(seq, False), cam)
    rep["cover"] = ((min(W, x1) - max(0, x0)) / W, (min(H, y1) - max(0, y0)) / H)
    if sc.focal is not None:
        _focal(sc, cam, rep)
    elif strict:
        rep["problems"].append("scene: name the focal object with \"focal\": \"<id>\" (the one prop the picture is about)")
    for lk in sc.links:
        rep["warnings"] += lk.warnings
    if strict if analyse is None else analyse:
        _analyse(sc, seq, cam, rep)
        _route_checks(sc, cam, rep)
    inner = _paint(seq, cam, defs)
    if debug:
        inner += _overlay(sc, cam)
    head = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H)
    bg = '<rect width="%d" height="%d" fill="%s"/>' % (W, H, sc.backdrop)
    return head + defs.markup() + bg + inner + "</svg>\n", rep


def draw(spec, check_bounds=True, strict=False, story=None):
    """The SVG text for a scene spec (raises SpecError; with STRICT, also on any problem
    of composition)."""
    svg, rep = render(spec, strict=strict, story=story, check_bounds=check_bounds)
    if strict and rep["problems"]:
        raise SpecError(rep["problems"][0] if len(rep["problems"]) == 1 else
                        "%d problems: %s" % (len(rep["problems"]), " | ".join(rep["problems"])))
    return svg


def fragment(spec, box, defs, max_zoom=1.0):
    """Markup for SPEC fitted into BOX = (x, y, w, h) of a larger sheet, sharing DEFS
    (for the catalog). Returns (markup, zoom used)."""
    sc, d0 = _build(spec)
    build_ground(sc.ground_spec, ground_box(sc.ground_spec, sc), sc, d0)
    for key, val in d0.items.items():
        defs.items.setdefault(key, val)
    seq = _sequence(sc)
    framed = _framed(seq, True)
    x0, x1, y0, y1 = _bounds(framed, Camera(K, 0.0, 0.0))
    bx, by, bw, bh = box
    z = min(max_zoom, (bw - 16) / max(1e-6, x1 - x0), (bh - 16) / max(1e-6, y1 - y0))
    x0, x1, y0, y1 = x0 * z, x1 * z, y0 * z, y1 * z
    ox = bx + bw / 2.0 - (x0 + x1) / 2.0
    oy = by + bh / 2.0 - (y0 + y1) / 2.0
    return _paint(seq, Camera(K * z, ox, oy), defs), z
