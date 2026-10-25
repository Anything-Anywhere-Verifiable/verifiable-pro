"""Turn ordered 3D elements into SVG markup with a fixed camera.

The writer projects every point, culls faces turned away, shades Mat fills by their
normal, and merges runs of consecutive polygons or strokes that share one style into a
single <path>, so a picture stays small. Gradients and filters are collected into one
<defs> block with fixed ids.
"""
import math

from .iso import (Baked, Cyl, El, Glass, Glow, LipMarker, Mat, Outline, Sphere, Sweep, Wall, add, facing_camera, flatten2,
                  fmt, fmt2, hull2, mix, project)

OUTLINE = "#c3c9d0"   # the hero's plate edge
OUTLINE_W = 2.4       # px; the prop covers the inner half, so 1.2 px shows

RX = 1.2643   # a horizontal circle of radius r projects to an axis-aligned ellipse
RY = 0.6322   # of radii RX * r and RY * r (times K)
SX = 1.2643   # a sphere projects to an ellipse of radii SX * r and SY * r
SY = 1.1832


class Camera:
    def __init__(self, k, ox, oy):
        self.k, self.ox, self.oy = k, ox, oy

    def p(self, pt):
        return project(pt, self.k, self.ox, self.oy)


class Defs:
    def __init__(self):
        self.items = {}

    def cyl_grad(self, mat):
        gid = "c" + mat.name
        if gid not in self.items:
            a = mix(mat.left, mat.top, 0.75)
            self.items[gid] = ('<linearGradient id="%s" x1="0" y1="0" x2="1" y2="0">'
                               '<stop offset="0" stop-color="%s"/><stop offset=".18" stop-color="%s"/>'
                               '<stop offset=".82" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
                               '</linearGradient>' % (gid, a, mat.left, mat.right, mix(mat.right, "#000000", 0.04)))
        return "url(#%s)" % gid

    def lin(self, gid, x1, y1, x2, y2, stops):
        if gid not in self.items:
            s = "".join('<stop offset="%s" stop-color="%s"%s/>' % (fmt2(o), c, "" if op is None else ' stop-opacity="%s"' % fmt2(op))
                        for o, c, op in stops)
            self.items[gid] = ('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>'
                               % (gid, fmt2(x1), fmt2(y1), fmt2(x2), fmt2(y2), s))
        return "url(#%s)" % gid

    def radial(self, gid, stops, cx=0.5, cy=0.5, r=0.5):
        if gid not in self.items:
            s = "".join('<stop offset="%s" stop-color="%s"%s/>' % (fmt2(o), c, "" if op is None else ' stop-opacity="%s"' % fmt2(op))
                        for o, c, op in stops)
            self.items[gid] = ('<radialGradient id="%s" cx="%s" cy="%s" r="%s">%s</radialGradient>'
                               % (gid, fmt2(cx), fmt2(cy), fmt2(r), s))
        return "url(#%s)" % gid

    def blur(self, fid, sd):
        if fid not in self.items:
            self.items[fid] = ('<filter id="%s" filterUnits="userSpaceOnUse" x="-100" y="-100" width="1400" height="1000">'
                               '<feGaussianBlur stdDeviation="%s"/></filter>' % (fid, fmt(sd)))
        return "url(#%s)" % fid

    def markup(self):
        if not self.items:
            return ""
        return "<defs>" + "".join(self.items[k] for k in sorted(self.items)) + "</defs>"


ATTR = (("fill", "fill"), ("fop", "fill-opacity"), ("stroke", "stroke"), ("sw", "stroke-width"),
        ("sop", "stroke-opacity"), ("op", "opacity"), ("dash", "stroke-dasharray"), ("dashoff", "stroke-dashoffset"),
        ("cap", "stroke-linecap"), ("join", "stroke-linejoin"), ("filter", "filter"),
        ("rule", "fill-rule"))


def attrs(st):
    out = []
    for key, name in ATTR:
        v = st.get(key)
        if key == "fill" and v is None:
            out.append(' fill="none"')
            continue
        if v is None:
            continue
        if isinstance(v, float) or isinstance(v, int):
            v = fmt2(v) if key in ("fop", "sop", "op") else fmt(v)
        out.append(' %s="%s"' % (name, v))
    return "".join(out)


def _d(cmds, cam):
    out = []
    linear = True
    pts2 = []
    for c in cmds:
        if c[0] == "M":
            x, y = cam.p(c[1])
            out.append("M%s %s" % (fmt(x), fmt(y)))
            pts2.append((x, y))
        elif c[0] == "L":
            x, y = cam.p(c[1])
            out.append("L%s %s" % (fmt(x), fmt(y)))
            pts2.append((x, y))
        elif c[0] == "C":
            q = [cam.p(p) for p in c[1:]]
            out.append("C" + " ".join("%s %s" % (fmt(x), fmt(y)) for x, y in q))
            linear = False
            pts2.append(q[-1])
        else:
            out.append("Z")
    return out, linear, pts2


def _signed_area(pts):
    a = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        a += p[0] * q[1] - q[0] * p[1]
    return a / 2.0


def _loop(pts):
    return "M" + "L".join("%s %s" % (fmt(x), fmt(y)) for x, y in pts) + "Z"


def _ellipse_pts(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def screen_shapes(e, cam, n=16):
    """The filled area an element covers on screen, for the occlusion check: a list of
    shapes, each a list of polygons filled by the even-odd rule. Glass, glows, lips,
    strokes, decorations and faint fills cover nothing. N is how many points stand for
    a round outline."""
    if isinstance(e, El):
        if e.cull and not facing_camera(e.n):
            return []
        st = e.st
        if not e.body or st.get("fill") is None or st.get("filter"):
            return []
        for key in ("fop", "op"):
            v = st.get(key)
            if v is not None and v < 0.5:
                return []
        polys = []
        cur = None
        last = None
        for c in e.cmds:
            if c[0] == "M":
                if cur:
                    polys.append(cur)
                last = cam.p(c[1])
                cur = [last]
            elif c[0] == "L":
                last = cam.p(c[1])
                cur.append(last)
            elif c[0] == "C":
                q = [cam.p(p) for p in c[1:]]
                pts = flatten2([("M",) + last, ("C",) + q[0] + q[1] + q[2]], 6)[1:]
                cur += pts
                last = q[2]
        if cur:
            polys.append(cur)
        return [[p for p in polys if len(p) >= 3]]
    if isinstance(e, Cyl):
        x, y = cam.p(e.c)
        rx, ry = RX * e.r * cam.k, RY * e.r * cam.k
        hpx = e.h * cam.k
        return [[hull2(_ellipse_pts(x, y, rx, ry, n) + _ellipse_pts(x, y - hpx, rx, ry, n))]]
    if isinstance(e, Sphere):
        if e.op is not None and e.op < 0.5:
            return []
        x, y = cam.p(e.c)
        return [[_ellipse_pts(x, y, SX * e.r * cam.k, SY * e.r * cam.k, max(n, 20))]]
    if isinstance(e, Sweep):
        pts = [cam.p(p) for p in e.pts] + [cam.p(add(p, e.d)) for p in e.pts]
        return [[hull2(pts)]]
    if isinstance(e, Wall):
        fo = [cam.p(p) for p in e.outer]
        bo = [cam.p(add(p, e.d)) for p in e.outer]
        fi = [cam.p(p) for p in e.inner]
        bi = [cam.p(add(p, e.d)) for p in e.inner]
        return [[hull2(fo + bo), fo], [fi, bi]]
    if isinstance(e, Baked):
        ax, ay = cam.p(e.anchor)
        k = e.k * cam.k
        return [[[(ax + x * k, ay + y * k) for x, y in pts] for pts in polys] for _, polys in e.paths]
    return []


def screen_bounds(e, cam):
    """The screen box (x0, x1, y0, y1) of an element, or None for one without extent
    (a glow, a blurred shape)."""
    if isinstance(e, Cyl):
        x, y = cam.p(e.c)
        rx, ry = RX * e.r * cam.k, RY * e.r * cam.k
        return (x - rx, x + rx, y - e.h * cam.k - ry, y + ry)
    if isinstance(e, Sphere):
        x, y = cam.p(e.c)
        rx, ry = SX * e.r * cam.k, SY * e.r * cam.k
        return (x - rx, x + rx, y - ry, y + ry)
    if isinstance(e, (Glow, Outline)):
        return None
    if isinstance(e, El) and e.st.get("filter"):
        return None
    if isinstance(e, Baked):
        ax, ay = cam.p(e.anchor)
        k = e.k * cam.k
        pts = [(ax + x * k, ay + y * k) for _, polys in e.paths for poly in polys for x, y in poly]
    else:
        pts = [cam.p(p) for p in e.points()]
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), max(xs), min(ys), max(ys))


class Writer:
    def __init__(self, cam, defs):
        self.cam = cam
        self.defs = defs
        self.out = []        # finished markup
        self.run = None      # (style_key, [d strings], mergeable)

    def flush(self):
        if self.run is not None:
            key, ds, _ = self.run
            self.out.append('<path d="%s"%s/>' % ("".join(ds), key))
            self.run = None

    def raw(self, s):
        self.flush()
        self.out.append(s)

    def path(self, d, st, mergeable):
        key = attrs(st)
        if mergeable and self.run is not None and self.run[0] == key and self.run[2]:
            self.run[1].append(d)
            return
        self.flush()
        self.run = (key, [d], mergeable)

    def el(self, e):
        if isinstance(e, LipMarker):
            e = e.resolve()
        if isinstance(e, El):
            self.el_path(e)
        elif isinstance(e, Cyl):
            self.el_cyl(e)
        elif isinstance(e, Sphere):
            self.el_sphere(e)
        elif isinstance(e, Glow):
            self.el_glow(e)
        elif isinstance(e, Sweep):
            self.el_sweep(e)
        elif isinstance(e, Glass):
            for x in e.els():
                self.el_path(x)
        elif isinstance(e, Wall):
            self.el_wall(e)
        elif isinstance(e, Baked):
            self.el_baked(e)
        elif isinstance(e, Outline):
            self.el_outline(e)

    def el_outline(self, e):
        """The outline under a prop: the hull of each convex part's opaque faces, and every
        opaque face of the other parts, stroked in one path."""
        loops = []
        for part in e.parts:
            polys = []
            for x in part.els:
                for shape in screen_shapes(x, self.cam, 48):
                    polys += [p for p in shape if len(p) >= 3]
            if not polys:
                continue
            if part.convex:
                polys = [hull2([q for p in polys for q in p])]
            for p in polys:
                if len(p) >= 3:
                    loops.append(_loop(p))
        if loops:
            self.path("".join(loops), {"fill": None, "stroke": OUTLINE, "sw": OUTLINE_W, "join": "round"}, False)

    def el_wall(self, e):
        cam = self.cam
        fo = [cam.p(p) for p in e.outer]
        bo = [cam.p(add(p, e.d)) for p in e.outer]
        hull = hull2(fo + bo)
        if len(hull) >= 3:
            self.path(_loop(hull) + _loop(fo), {"fill": e.fill, "rule": "evenodd"}, False)
        fi = [cam.p(p) for p in e.inner]
        bi = [cam.p(add(p, e.d)) for p in e.inner]
        self.path(_loop(fi) + _loop(bi), {"fill": e.fill2, "rule": "evenodd"}, False)

    def el_baked(self, e):
        ax, ay = self.cam.p(e.anchor)
        k = e.k * self.cam.k
        for fill, polys in e.paths:
            d = "".join(_loop([(ax + x * k, ay + y * k) for x, y in pts]) for pts in polys)
            self.path(d, {"fill": fill}, False)

    def el_sweep(self, e):
        pts = [self.cam.p(p) for p in e.pts] + [self.cam.p((p[0] + e.d[0], p[1] + e.d[1], p[2] + e.d[2])) for p in e.pts]
        hull = hull2(pts)
        if len(hull) < 3:
            return
        hull = list(reversed(hull)) if _signed_area(hull) < 0 else hull
        d = "M" + "L".join("%s %s" % (fmt(x), fmt(y)) for x, y in hull) + "Z"
        fill = e.fill.right if isinstance(e.fill, Mat) else e.fill
        self.path(d, {"fill": fill, "stroke": fill, "sw": 0.6, "join": "round"}, True)

    def el_path(self, e):
        if e.cull and not facing_camera(e.n):
            return
        st = dict(e.st)
        f = st.get("fill")
        if isinstance(f, Mat):
            st["fill"] = f.shade(e.n) if e.n is not None else f.top
        s = st.get("stroke")
        if isinstance(s, Mat):
            st["stroke"] = s.shade(e.n) if e.n is not None else s.top
        if st.pop("seam", False) and st.get("stroke") is None and st.get("fill"):
            st["stroke"] = st["fill"]
            st["sw"] = 0.6
            st["join"] = "round"
        # a link's weight and dashes grow with the zoom only up to KMAX (a link stays a
        # fine line however close the camera comes)
        k = min(self.cam.k, st.pop("kmax", self.cam.k))
        if "swu" in st:
            st["sw"] = max(0.3, st.pop("swu") * k)
        if "dashu" in st:
            # a dash pattern in world units, and where along it this path starts (for a
            # link drawn in several runs: its length on screen at zoom 1)
            a, b = st.pop("dashu")
            da, db = fmt(max(0.1, a * k)), fmt(b * k)
            st["dash"] = "%s %s" % (da, db)
            per = float(da) + float(db)
            off = math.fmod(st.pop("dashoffu", 0.0) * self.cam.k, per) if per > 0 else 0.0
            if off > 0.05:
                st["dashoff"] = off
        st.pop("dashoffu", None)
        grad = st.pop("grad", None)
        if grad:
            st["fill"] = grad
        parts, linear, pts2 = _d(e.cmds, self.cam)
        closed = any(c[0] == "Z" for c in e.cmds)
        # polygons: one winding, so merged subpaths never cancel
        if linear and closed and len(pts2) >= 3 and _signed_area(pts2) < 0 and sum(1 for c in e.cmds if c[0] == "M") == 1:
            pts2 = list(reversed(pts2))
            parts = ["M%s %s" % (fmt(pts2[0][0]), fmt(pts2[0][1]))] + \
                    ["L%s %s" % (fmt(x), fmt(y)) for x, y in pts2[1:]] + ["Z"]
        d = "".join(parts)
        mergeable = (linear and closed and not st.get("filter")) or (st.get("fill") is None and not st.get("filter"))
        if st.get("op") is not None and st.get("fill") is not None:
            mergeable = False
        self.path(d, st, mergeable)

    def el_cyl(self, e):
        cam = self.cam
        x, y = cam.p(e.c)
        rx, ry = RX * e.r * cam.k, RY * e.r * cam.k
        hpx = e.h * cam.k
        top_fill = e.top or e.mat.top
        if hpx > 0.05:
            yt = y - hpx
            d = ("M%s %sA%s %s 0 0 0 %s %sL%s %sA%s %s 0 0 1 %s %sZ" %
                 (fmt(x - rx), fmt(y), fmt(rx), fmt(ry), fmt(x + rx), fmt(y),
                  fmt(x + rx), fmt(yt), fmt(rx), fmt(ry), fmt(x - rx), fmt(yt)))
            self.path(d, {"fill": self.defs.cyl_grad(e.mat)}, False)
        else:
            yt = y
        st = {"fill": top_fill}
        if e.rim:
            st["stroke"] = e.rim
            st["sw"] = e.rw
        self.raw('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s/>' % (fmt(x), fmt(yt), fmt(rx), fmt(ry), attrs(st)))

    def el_sphere(self, e):
        cam = self.cam
        x, y = cam.p(e.c)
        rx, ry = SX * e.r * cam.k, SY * e.r * cam.k
        st = {"fill": e.fill}
        if e.shade:
            light, dark = e.shade
            st["fill"] = self.defs.radial("gs%s%s" % (light[1:], dark[1:]), [(0, light, None), (0.55, mix(light, dark, 0.45), None),
                                                                           (1, dark, None)], cx=0.36, cy=0.3, r=0.78)
        if e.op is not None:
            st["op"] = e.op
        self.raw('<ellipse cx="%s" cy="%s" rx="%s" ry="%s"%s/>' % (fmt(x), fmt(y), fmt(rx), fmt(ry), attrs(st)))
        if e.hi:
            self.raw('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity=".75"/>'
                     % (fmt(x - rx * 0.32), fmt(y - ry * 0.36), fmt(rx * 0.34), fmt(ry * 0.26), e.hi))

    def el_glow(self, e):
        cam = self.cam
        x, y = cam.p(e.c)
        rx = e.r * cam.k
        ry = (e.ry if e.ry is not None else e.r) * cam.k
        sd = max(3, int(round(rx * 0.45)))
        self.raw('<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" opacity="%s" filter="%s"/>'
                 % (fmt(x), fmt(y), fmt(rx), fmt(ry), e.color, fmt2(e.op), self.defs.blur("g%d" % sd, sd)))

    def markup(self):
        self.flush()
        return "".join(self.out)
