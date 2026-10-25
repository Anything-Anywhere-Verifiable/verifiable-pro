"""The prop registry, parameter types and the builder that props draw with.

A prop is a function registered with @prop. It receives a Builder (B) and draws in
local coordinates: x along its front, y into its depth (the front faces -y), z up, with
its footprint centred on the origin and its base at z = 0. The compositor turns it to
its facing, scales it and moves it into the scene, so a prop never needs to know where
it stands.
"""
import difflib
import math

from . import palette as P
from .iso import (Glow, Part, Plane, Sphere, Sweep, add, arc2, box_els, circle2, cyl_els, flatten2, mul,
                  poly, rect, rrect, unit)


class SpecError(ValueError):
    pass


# ----- parameter types -----------------------------------------------------------------
class Param:
    __slots__ = ("kind", "default", "lo", "hi", "choices", "doc", "nlo", "nhi")

    def __init__(self, kind, default, doc, lo=None, hi=None, choices=None, nlo=None, nhi=None):
        self.kind, self.default, self.doc = kind, default, doc
        self.lo, self.hi, self.choices = lo, hi, choices
        self.nlo, self.nhi = nlo, nhi

    def describe(self):
        if self.kind == "num":
            return "number %s to %s, default %s" % (_n(self.lo), _n(self.hi), _n(self.default))
        if self.kind == "int":
            return "integer %d to %d, default %d" % (self.lo, self.hi, self.default)
        if self.kind == "bool":
            return "true or false, default %s" % ("true" if self.default else "false")
        if self.kind == "enum":
            return "one of %s; default %s" % (", ".join(self.choices), self.default)
        if self.kind == "nums":
            return "list of %d to %d numbers, each %s to %s; default %s" % (
                self.nlo, self.nhi, _n(self.lo), _n(self.hi), "[" + ", ".join(_n(v) for v in self.default) + "]")
        return self.kind

    def check(self, v, where):
        if self.kind in ("num", "int"):
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise SpecError("%s: expected a number, got %r" % (where, v))
            if not math.isfinite(v):   # JSON readers accept Infinity and NaN; int() would fail on them
                raise SpecError("%s: expected a finite number, got %r" % (where, v))
            if self.kind == "int" and int(v) != v:
                raise SpecError("%s: expected a whole number, got %r" % (where, v))
            if not (self.lo - 1e-9 <= v <= self.hi + 1e-9):
                raise SpecError("%s: %s is out of range (%s to %s)" % (where, _n(v), _n(self.lo), _n(self.hi)))
            return int(v) if self.kind == "int" else float(v)
        if self.kind == "bool":
            if not isinstance(v, bool):
                raise SpecError("%s: expected true or false, got %r" % (where, v))
            return v
        if self.kind == "enum":
            if v not in self.choices:
                hint = difflib.get_close_matches(str(v), self.choices, 1)
                raise SpecError("%s: %r is not one of %s%s" % (where, v, ", ".join(self.choices),
                                                               "; did you mean %r?" % hint[0] if hint else ""))
            return v
        if self.kind == "nums":
            if not isinstance(v, list) or not (self.nlo <= len(v) <= self.nhi):
                raise SpecError("%s: expected a list of %d to %d numbers" % (where, self.nlo, self.nhi))
            out = []
            for i, x in enumerate(v):
                if isinstance(x, bool) or not isinstance(x, (int, float)) or not (self.lo <= x <= self.hi):
                    raise SpecError("%s[%d]: expected a number from %s to %s, got %r" % (where, i, _n(self.lo), _n(self.hi), x))
                out.append(float(x))
            return out
        raise SpecError("%s: unknown parameter kind" % where)


def _n(x):
    return ("%g" % x) if isinstance(x, (int, float)) else str(x)


def num(default, lo, hi, doc):
    return Param("num", float(default), doc, lo=lo, hi=hi)


def integer(default, lo, hi, doc):
    return Param("int", int(default), doc, lo=lo, hi=hi)


def flag(default, doc):
    return Param("bool", bool(default), doc)


def choice(default, choices, doc):
    return Param("enum", default, doc, choices=list(choices))


def nums(default, nlo, nhi, lo, hi, doc):
    return Param("nums", list(default), doc, lo=lo, hi=hi, nlo=nlo, nhi=nhi)


MATERIALS = ["plate", "tplate", "metal", "paper", "soft", "steel", "dark", "ink", "int", "hbm", "die", "pcb",
             "gold", "tee", "teelight", "data", "datalight", "kraft",
             "models", "outputs", "agents", "evaluations", "institutions",
             "modelslight", "outputslight", "agentslight", "evaluationslight", "institutionslight"]
P.M["kraft"] = P.Mat("#ecdcbc", "#dcc39a", "#c6a878", None, "kraft")


def material(default, doc="the material of the solid (see palette)"):
    return choice(default, ["auto"] + MATERIALS, doc + "; auto follows the tint")


# ----- registry ------------------------------------------------------------------------
class PropDef:
    __slots__ = ("name", "fn", "group", "doc", "params", "tints", "tint", "floor", "container", "example", "facings",
                 "aliases")

    def __init__(self, name, fn, group, doc, params, tints, tint, floor, container, example, facings=None, aliases=None):
        self.name, self.fn, self.group, self.doc = name, fn, group, doc
        self.params, self.tints, self.tint = params, tints, tint
        self.floor, self.container, self.example = floor, container, example
        self.facings = facings
        self.aliases = aliases or {}   # an older parameter name -> its current name


REGISTRY = {}
GROUPS = []
ALL = tuple(P.TINT_NAMES)
CORE = ("neutral", "tee", "data", "seal", "dark")


def prop(name, group, doc, tints=ALL, tint="neutral", floor=False, container=False, example=None, facings=None,
         aliases=None, **params):
    # cinnabar is for seals: only the seal props take the seal tint
    tints = tuple(t for t in dict.fromkeys(tints) if t != "seal" or name in P.SEAL_PROPS)
    assert tint in tints, name

    def deco(fn):
        REGISTRY[name] = PropDef(name, fn, group, doc, params, tuple(tints), tint, floor, container, example or {},
                                 facings, aliases)
        if group not in GROUPS:
            GROUPS.append(group)
        return fn
    return deco


# ----- builder -------------------------------------------------------------------------
class B:
    """What a prop draws into. Parts are sorted against each other by their boxes once
    the prop is turned; elements inside a part are drawn in the order given."""

    def __init__(self, tint, params):
        self.tint = tint
        self.t = P.TINTS[tint]
        self.p = params
        self.parts = []
        self.anchors = {}
        self.surface = None        # height things stand on when placed "on" this prop
        self.shadow = True
        self.footprint = None      # (x0, y0, x1, y1) for the cast shadow, else the box
        self.lift = 0.0            # how far the prop floats (its shadow stays on the ground)
        self.contacts = []         # (x, y, radius): small dark shadows where a thin part touches the ground
        self.port = None           # the anchor a link uses when it names this prop without one
        self.outline = True        # draw the hairline outline around the prop

    def mat(self, name):
        if name == "auto":
            return self.t.body
        return P.M[name]

    def add(self, els, name="", convex=False):
        part = Part(list(els), name, convex)
        self.parts.append(part)
        return part

    def box(self, x0, y0, z0, x1, y1, z1, mat, lip=P.LIP, top=None, edge=None, ew=0.8, name=""):
        return self.add(box_els(x0, y0, z0, x1, y1, z1, mat, lip=lip, top=top, edge=edge, ew=ew), name, convex=True)

    def cbox(self, cx, cy, z0, w, d, h, mat, **kw):
        """A box by its base centre and size."""
        return self.box(cx - w / 2.0, cy - d / 2.0, z0, cx + w / 2.0, cy + d / 2.0, z0 + h, mat, **kw)

    def cyl(self, cx, cy, z0, z1, r, mat, top=None, rim=None, rw=0.8, name=""):
        return self.add(cyl_els(cx, cy, z0, z1, r, mat, top=top, rim=rim, rw=rw), name, convex=True)

    def sphere(self, c, r, fill, hi=None, glow=None, glow_op=0.45, name=""):
        els = []
        if glow:
            els.append(Glow(c, r * 2.2, glow, glow_op))
        els.append(Sphere(c, r, fill, hi))
        return self.add(els, name, convex=True)

    def obox_els(self, o, ex, ey, ez, mat, seam=True):
        """An oriented box from corner O along edge vectors EX, EY, EZ (right-handed)."""
        c = [o, add(o, ex), add(add(o, ex), ey), add(o, ey)]
        top = [add(p, ez) for p in c]
        faces = [
            ([top[0], top[1], top[2], top[3]], unit(ez)),
            ([c[3], c[2], c[1], c[0]], unit(mul(ez, -1))),
            ([c[0], c[1], top[1], top[0]], unit(mul(ey, -1))),
            ([c[1], c[2], top[2], top[1]], unit(ex)),
            ([c[2], c[3], top[3], top[2]], unit(ey)),
            ([c[3], c[0], top[0], top[3]], unit(mul(ex, -1))),
        ]
        out = []
        for pts, n in faces:
            st = {"fill": mat}
            if seam:
                st["seam"] = True
            out.append(poly(pts, n=n, **st))
        return out

    def obox(self, o, ex, ey, ez, mat, name=""):
        return self.add(self.obox_els(o, ex, ey, ez, mat), name, convex=True)

    def extrude_els(self, plane, pieces, depth, front, side=None, back=None):
        """Extrude convex 2D PIECES on PLANE backwards (against its normal) by DEPTH:
        the walls as hulls, then the front and back caps (whichever faces the viewer)."""
        n = plane.n
        d = mul(n, -depth)
        side = side or front
        els = []
        for pc in pieces:
            pts = [plane.at(u, v) for u, v in flatten2(pc, 6)]
            els.append(Sweep(pts, d, side))
        cmds = [c for pc in pieces for c in pc]
        els.append(plane.shape(cmds, fill=front))
        bplane = Plane(add(plane.o, d), mul(plane.ex, -1), plane.ey)
        bcmds = []
        for pc in pieces:
            for c in pc:
                if c[0] in ("M", "L"):
                    bcmds.append((c[0], -c[1], c[2]))
                elif c[0] == "C":
                    bcmds.append(("C", -c[1], c[2], -c[3], c[4], -c[5], c[6]))
                else:
                    bcmds.append(c)
        els.append(bplane.shape(bcmds, fill=back or front))
        return els

    def extrude(self, plane, pieces, depth, front, side=None, back=None, extra=(), name=""):
        return self.add(self.extrude_els(plane, pieces, depth, front, side, back) + list(extra), name)


# ----- shared drawing helpers -----------------------------------------------------------
def tline(plane, u0, v, u1, color=P.SOFT2, w=0.07, **kw):
    """A 'text' line: a rounded bar standing for a line of writing (never words)."""
    return plane.line([(u0, v), (u1, v)], stroke=color, swu=w, cap="round", **kw)


def disc(plane, cu, cv, r, fill, **kw):
    return plane.shape(circle2(cu, cv, r), fill=fill, body=False, **kw)


def ring(plane, cu, cv, r, color, w=0.05, **kw):
    return plane.path(circle2(cu, cv, r), stroke=color, swu=w, **kw)


def lock_glyph(plane, cu, cv, s, color, hole=P.PAPER):
    """A small padlock drawn flat on a plane (body, shackle, keyhole), size S."""
    els = [plane.path(arc2(cu, cv + s * 0.12, s * 0.27, 0, 180), stroke=color, swu=s * 0.12, cap="butt"),
           plane.shape(rrect(cu - s * 0.42, cv - s * 0.5, cu + s * 0.42, cv + s * 0.14, s * 0.08), fill=color, body=False),
           plane.shape(circle2(cu, cv - s * 0.14, s * 0.09), fill=hole, body=False),
           plane.line([(cu, cv - s * 0.16), (cu, cv - s * 0.36)], stroke=hole, swu=s * 0.07, cap="round")]
    return els


def shield2(cu, cv, w, h):
    """A shield outline (convex), counter-clockwise, top edge at cv + h / 2."""
    x0, x1 = cu - w / 2.0, cu + w / 2.0
    top, bot = cv + h / 2.0, cv - h / 2.0
    mid = cv + h * 0.05
    return [("M", cu, bot),
            ("C", cu + w * 0.28, bot + h * 0.1, x1, mid - h * 0.15, x1, mid + h * 0.12),
            ("L", x1, top - h * 0.05),
            ("C", cu + w * 0.3, top, cu + w * 0.1, top + h * 0.02, cu, top + h * 0.06),
            ("C", cu - w * 0.1, top + h * 0.02, cu - w * 0.3, top, x0, top - h * 0.05),
            ("L", x0, mid + h * 0.12),
            ("C", x0, mid - h * 0.15, cu - w * 0.28, bot + h * 0.1, cu, bot),
            ("Z",)]


def landscape(plane, u0, v0, u1, v1, sky, hill, hill2, sun=P.SUN):
    w, h = u1 - u0, v1 - v0
    els = [plane.shape(rect(u0, v0, u1, v1), fill=sky, body=False)]
    els.append(plane.shape([("M", u0, v0), ("L", u0, v0 + h * 0.42),
                            ("C", u0 + w * 0.18, v0 + h * 0.62, u0 + w * 0.3, v0 + h * 0.66, u0 + w * 0.42, v0 + h * 0.5),
                            ("C", u0 + w * 0.5, v0 + h * 0.4, u0 + w * 0.56, v0 + h * 0.36, u0 + w * 0.62, v0 + h * 0.4),
                            ("L", u1, v0 + h * 0.58), ("L", u1, v0), ("Z",)], fill=hill, body=False))
    els.append(plane.shape([("M", u0, v0), ("L", u0, v0 + h * 0.2),
                            ("C", u0 + w * 0.3, v0 + h * 0.34, u0 + w * 0.55, v0 + h * 0.08, u1, v0 + h * 0.3),
                            ("L", u1, v0), ("Z",)], fill=hill2, body=False))
    els.append(plane.shape(circle2(u0 + w * 0.74, v0 + h * 0.74, min(w, h) * 0.11), fill=sun, body=False))
    return els


def screen_content(plane, u0, v0, u1, v1, kind, t, dark=False):
    """Abstract screen content in the box (u0, v0)-(u1, v1) of PLANE: no words, only
    bars, blocks, marks and pictures. T is the prop's Tint."""
    w, h = u1 - u0, v1 - v0
    ln = "#5d6570" if dark else P.SOFT2
    ln2 = "#7a838e" if dark else P.MUTE
    acc = t.accent
    els = []
    s = min(w, h)
    if kind == "blank":
        return els
    if kind in ("log", "text"):
        n = 6
        lens = (0.82, 0.6, 0.74, 0.5, 0.68, 0.4)
        for i in range(n):
            v = v1 - h * (0.16 + i * 0.68 / (n - 1))
            c = acc if (kind == "log" and i == 2) else ln
            if kind == "log":
                els.append(plane.shape(circle2(u0 + w * 0.09, v, h * 0.035), fill=ln2 if i != 2 else acc, body=False))
                els.append(tline(plane, u0 + w * 0.17, v, u0 + w * (0.17 + lens[i] * 0.72), c, w=h * 0.055))
            else:
                els.append(tline(plane, u0 + w * 0.1, v, u0 + w * (0.1 + lens[i] * 0.8), c, w=h * 0.055))
    elif kind == "code":
        rows = [(0.0, 0.34, acc), (0.1, 0.42, ln2), (0.1, 0.28, ln), (0.2, 0.36, ln2), (0.2, 0.22, acc),
                (0.1, 0.3, ln), (0.0, 0.14, ln2)]
        for i, (ind, ln_, c) in enumerate(rows):
            v = v1 - h * (0.14 + i * 0.72 / (len(rows) - 1))
            els.append(tline(plane, u0 + w * (0.1 + ind), v, u0 + w * (0.1 + ind + ln_ * 1.4), c, w=h * 0.06))
    elif kind == "chart":
        hs = (0.3, 0.5, 0.42, 0.72)
        bw = w * 0.13
        for i, f in enumerate(hs):
            bu = u0 + w * (0.16 + i * 0.19)
            els.append(plane.shape(rect(bu, v0 + h * 0.16, bu + bw, v0 + h * (0.16 + f * 0.72)),
                                   fill=acc if i == 3 else ln2, body=False))
        els.append(tline(plane, u0 + w * 0.1, v0 + h * 0.14, u1 - w * 0.08, ln, w=h * 0.025))
    elif kind == "line":
        pts = [(0.1, 0.25), (0.28, 0.42), (0.44, 0.36), (0.62, 0.6), (0.8, 0.55), (0.9, 0.78)]
        els.append(tline(plane, u0 + w * 0.08, v0 + h * 0.14, u1 - w * 0.06, ln, w=h * 0.025))
        els.append(plane.line([(u0 + w * a, v0 + h * b) for a, b in pts], stroke=acc, swu=h * 0.05, cap="round", join="round"))
        for a, b in pts[-1:]:
            els.append(plane.shape(circle2(u0 + w * a, v0 + h * b, h * 0.06), fill=acc, body=False))
    elif kind == "timeline":
        vm = v0 + h * 0.5
        els.append(tline(plane, u0 + w * 0.08, vm, u1 - w * 0.08, ln2, w=h * 0.03))
        for i in range(5):
            uu = u0 + w * (0.14 + i * 0.18)
            hot = i == 3
            els.append(plane.shape(circle2(uu, vm, h * (0.07 if hot else 0.05)), fill=acc if hot else ln2, body=False))
            vv = vm + h * (0.2 if i % 2 == 0 else -0.2)
            els.append(tline(plane, uu - w * 0.05, vv, uu + w * 0.05, acc if hot else ln, w=h * 0.05))
    elif kind == "image":
        els += landscape(plane, u0 + w * 0.06, v0 + h * 0.08, u1 - w * 0.06, v1 - h * 0.08,
                         t.wash if t.name != "neutral" else "#dfe5ec", t.accent2 if t.name != "neutral" else P.HILL,
                         t.accent if t.name != "neutral" else P.HILL2)
    elif kind == "lock":
        els += lock_glyph(plane, (u0 + u1) / 2.0, (v0 + v1) / 2.0, s * 0.55, acc, hole=P.PAPER if not dark else P.SUB1)
    elif kind == "shield":
        els.append(plane.shape(shield2((u0 + u1) / 2.0, (v0 + v1) / 2.0, s * 0.42, s * 0.55), fill=acc, body=False))
    elif kind == "wave":
        n = 15
        for i in range(n):
            f = 0.15 + 0.85 * abs(math.sin(i * 1.7) * math.cos(i * 0.45))
            uu = u0 + w * (0.1 + i * 0.8 / (n - 1))
            els.append(plane.line([(uu, v0 + h * (0.5 - f * 0.3)), (uu, v0 + h * (0.5 + f * 0.3))],
                                  stroke=acc if 5 <= i <= 8 else ln2, swu=w * 0.022, cap="round"))
    elif kind == "graph":
        nodes = [(0.2, 0.3), (0.2, 0.7), (0.5, 0.5), (0.8, 0.28), (0.8, 0.72)]
        for a, b in ((0, 2), (1, 2), (2, 3), (2, 4)):
            els.append(plane.line([(u0 + w * nodes[a][0], v0 + h * nodes[a][1]), (u0 + w * nodes[b][0], v0 + h * nodes[b][1])],
                                  stroke=ln2, swu=h * 0.025))
        for i, (a, b) in enumerate(nodes):
            els.append(plane.shape(circle2(u0 + w * a, v0 + h * b, h * 0.075), fill=acc if i == 2 else ln2, body=False))
    elif kind == "chat":
        for i, (side, f) in enumerate(((0, 0.6), (1, 0.5), (0, 0.42))):
            vv = v1 - h * (0.12 + i * 0.28)
            bw = w * f
            uu0 = u0 + w * 0.08 if side == 0 else u1 - w * 0.08 - bw
            els.append(plane.shape(rrect(uu0, vv - h * 0.18, uu0 + bw, vv, h * 0.05),
                                   fill=(acc if side == 1 else (ln if not dark else "#4a525b")), body=False))
    elif kind == "grid":
        for i in range(4):
            for j in range(3):
                uu = u0 + w * (0.08 + i * 0.22)
                vv = v0 + h * (0.12 + j * 0.27)
                els.append(plane.shape(rect(uu, vv, uu + w * 0.18, vv + h * 0.2),
                                       fill=acc if (i, j) == (2, 1) else ln, body=False))
    elif kind == "check":
        pass
    return els


SCREEN_KINDS = ["blank", "log", "text", "code", "chart", "line", "timeline", "image", "lock", "shield",
                "wave", "graph", "chat", "grid"]
