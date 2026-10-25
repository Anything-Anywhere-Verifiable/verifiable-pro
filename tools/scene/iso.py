"""Isometric projection, scene elements, depth sorting and SVG emission.

World space is the hero's: s runs down-right on screen, t up-right, h up. A point
(s, t, h) lands at

    x = OX + K * .894 * (s + t)
    y = OY + K * (.447 * (s - t) - h)

which is the projection of sitegen/templates/hero-scene.svg (tools/hero/geom.py), so a
generated illustration shares its angle with the hero. The viewer looks along -CAM, so
of an axis-aligned box only three faces show: the top, the front-left face (normal -t,
lit) and the front-right face (normal +s, in shade). Light comes from the upper left
(LIGHT), as on the hero's plates.

Every element is defined in 3D; nothing is drawn in screen space except through the
projection, so props can be turned (facing) and scaled without redrawing them by hand.
Numbers are written with one decimal after rounding to four, so a draw is byte-identical
on any platform.
"""
import math

C1, C2 = 0.894, 0.447   # the hero's 2:1 projection
K = 40.0                # pixels per world unit at zoom 1


# ----- vectors -----------------------------------------------------------------------
def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def unit(a):
    n = math.sqrt(dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, 0.0)


CAM = unit((1.0, -1.0, 0.894))     # toward the viewer: the projection's null direction
LIGHT = unit((-1.0, -1.0, 1.5))    # toward the light: upper left, as on the hero's plates
V_TOP = dot((0.0, 0.0, 1.0), LIGHT)
V_LEFT = dot((0.0, -1.0, 0.0), LIGHT)
V_RIGHT = dot((1.0, 0.0, 0.0), LIGHT)


def facing_camera(n):
    return dot(n, CAM) > 1e-6


def project(p, k=K, ox=0.0, oy=0.0):
    s, t, h = p
    return (ox + k * C1 * (s + t), oy + k * (C2 * (s - t) - h))


def depth(p):
    return dot(p, CAM)


# ----- numbers -----------------------------------------------------------------------
def fmt(x):
    """One decimal, after rounding to four (so a last-bit difference in a platform's
    libm cannot move a digit), without a trailing .0 or a negative zero."""
    v = round(x, 4)
    s = "%.1f" % v
    if s.endswith(".0"):
        s = s[:-2]
    if s == "-0":
        s = "0"
    return s


def fmt2(x):
    v = round(x, 5)
    s = "%.2f" % v
    s = s.rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s


# ----- colour ------------------------------------------------------------------------
def rgb(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def hexc(r):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(v)))) for v in r)


def mix(a, b, k):
    """Mix two #rrggbb colours: k = 0 gives a, k = 1 gives b."""
    k = max(0.0, min(1.0, k))
    ra, rb = rgb(a), rgb(b)
    return hexc(tuple(x + (y - x) * k for x, y in zip(ra, rb)))


class Mat:
    """A material: the colours of a top, a lit front-left face and a shaded front-right
    face. A face in any other direction is shaded between them by its normal."""
    __slots__ = ("top", "left", "right", "edge", "name")

    def __init__(self, top, left, right, edge=None, name=""):
        self.top, self.left, self.right = top, left, right
        self.edge = edge
        self.name = name

    def shade(self, n):
        v = dot(n, LIGHT)
        if v >= V_LEFT:
            return mix(self.left, self.top, (v - V_LEFT) / (V_TOP - V_LEFT))
        return mix(self.right, self.left, (v - V_RIGHT) / (V_LEFT - V_RIGHT))

    def lighter(self, k):
        return Mat(mix(self.top, "#ffffff", k), mix(self.left, "#ffffff", k),
                   mix(self.right, "#ffffff", k), self.edge, self.name)

    def darker(self, k):
        return Mat(mix(self.top, "#000000", k), mix(self.left, "#000000", k),
                   mix(self.right, "#000000", k), self.edge, self.name)


# ----- 2D path helpers (in a plane's own u, v coordinates, v up) ------------------------
KAPPA = 0.5522847498


def rect(u0, v0, u1, v1):
    return [("M", u0, v0), ("L", u1, v0), ("L", u1, v1), ("L", u0, v1), ("Z",)]


def poly2(pts):
    out = [("M",) + tuple(pts[0])]
    out += [("L",) + tuple(p) for p in pts[1:]]
    out.append(("Z",))
    return out


def ellipse2(cu, cv, ru, rv):
    """A closed ellipse, counter-clockwise, as four cubic Beziers."""
    k = KAPPA
    return [("M", cu + ru, cv),
            ("C", cu + ru, cv + k * rv, cu + k * ru, cv + rv, cu, cv + rv),
            ("C", cu - k * ru, cv + rv, cu - ru, cv + k * rv, cu - ru, cv),
            ("C", cu - ru, cv - k * rv, cu - k * ru, cv - rv, cu, cv - rv),
            ("C", cu + k * ru, cv - rv, cu + ru, cv - k * rv, cu + ru, cv),
            ("Z",)]


def circle2(cu, cv, r):
    return ellipse2(cu, cv, r, r)


def arc2(cu, cv, r, a0, a1, move=True, rv=None):
    """An arc from angle a0 to a1 (degrees, counter-clockwise if a1 > a0), split into
    Bezier pieces of at most 90 degrees."""
    rv = r if rv is None else rv
    n = max(1, int(math.ceil(abs(a1 - a0) / 90.0 - 1e-9)))
    out = []
    step = (a1 - a0) / n
    for i in range(n):
        t0 = math.radians(a0 + step * i)
        t1 = math.radians(a0 + step * (i + 1))
        k = 4.0 / 3.0 * math.tan((t1 - t0) / 4.0)
        p0 = (cu + r * math.cos(t0), cv + rv * math.sin(t0))
        p3 = (cu + r * math.cos(t1), cv + rv * math.sin(t1))
        p1 = (p0[0] - k * r * math.sin(t0), p0[1] + k * rv * math.cos(t0))
        p2 = (p3[0] + k * r * math.sin(t1), p3[1] - k * rv * math.cos(t1))
        if i == 0:
            out.append(("M" if move else "L", p0[0], p0[1]))
        out.append(("C", p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]))
    return out


def rrect(u0, v0, u1, v1, r):
    """A rounded rectangle, counter-clockwise."""
    r = max(0.0, min(r, (u1 - u0) / 2.0, (v1 - v0) / 2.0))
    if r <= 1e-9:
        return rect(u0, v0, u1, v1)
    out = [("M", u0 + r, v0), ("L", u1 - r, v0)]
    out += arc2(u1 - r, v0 + r, r, -90, 0, move=False)[1:]
    out.append(("L", u1, v1 - r))
    out += arc2(u1 - r, v1 - r, r, 0, 90, move=False)[1:]
    out.append(("L", u0 + r, v1))
    out += arc2(u0 + r, v1 - r, r, 90, 180, move=False)[1:]
    out.append(("L", u0, v0 + r))
    out += arc2(u0 + r, v0 + r, r, 180, 270, move=False)[1:]
    out.append(("Z",))
    return out


def flatten2(cmds, steps=8):
    """Points along a 2D path (for hulls and bounds)."""
    pts = []
    cur = (0.0, 0.0)
    for c in cmds:
        if c[0] in ("M", "L"):
            cur = (c[1], c[2])
            pts.append(cur)
        elif c[0] == "C":
            p0 = cur
            p1, p2, p3 = (c[1], c[2]), (c[3], c[4]), (c[5], c[6])
            for i in range(1, steps + 1):
                t = i / float(steps)
                a = (1 - t) ** 3
                b = 3 * (1 - t) ** 2 * t
                cc = 3 * (1 - t) * t * t
                d = t ** 3
                pts.append((a * p0[0] + b * p1[0] + cc * p2[0] + d * p3[0],
                            a * p0[1] + b * p1[1] + cc * p2[1] + d * p3[1]))
            cur = p3
    return pts


def hull2(pts):
    """Convex hull (Andrew's monotone chain), counter-clockwise."""
    pts = sorted(set((round(p[0], 6), round(p[1], 6)) for p in pts))
    if len(pts) < 3:
        return pts

    def turn(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and turn(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and turn(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


# ----- elements ----------------------------------------------------------------------
class El:
    """A drawable path in 3D: commands ('M', p), ('L', p), ('C', p1, p2, p3), ('Z',)
    with 3D points, a style, and an optional normal. An element with a normal is
    culled when it faces away, and a Mat fill is shaded by it."""
    __slots__ = ("cmds", "st", "n", "cull", "body", "kind", "ell")

    def __init__(self, cmds, n=None, cull=True, body=True, **st):
        self.cmds = cmds
        self.n = n
        self.cull = cull and n is not None
        self.body = body          # counts toward the part's bounding box
        self.kind = "path"
        self.ell = None           # (centre, rx, ry) for a screen-aligned ellipse
        self.st = st

    def points(self):
        for c in self.cmds:
            for p in c[1:]:
                yield p

    def transformed(self, tf):
        e = El([(c[0],) + tuple(tf.point(p) for p in c[1:]) for c in self.cmds],
               n=None if self.n is None else tf.vec(self.n), cull=self.cull, body=self.body)
        e.cull = self.cull
        e.kind = self.kind
        e.st = dict(self.st)
        if "swu" in e.st:
            e.st["swu"] = e.st["swu"] * tf.k
        if self.ell is not None:
            c, rx, ry = self.ell
            e.ell = (tf.point(c), rx * tf.k, ry * tf.k)
        return e


def poly(pts, n=None, **st):
    """A planar polygon; its normal comes from its winding (Newell) unless given."""
    if n is None:
        nx = ny = nz = 0.0
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            nx += (a[1] - b[1]) * (a[2] + b[2])
            ny += (a[2] - b[2]) * (a[0] + b[0])
            nz += (a[0] - b[0]) * (a[1] + b[1])
        n = unit((nx, ny, nz))
    cmds = [("M", pts[0])] + [("L", p) for p in pts[1:]] + [("Z",)]
    return El(cmds, n=n, **st)


def line(pts, closed=False, host=None, **st):
    """A polyline; HOST is the normal of the face it is drawn on (for culling)."""
    cmds = [("M", pts[0])] + [("L", p) for p in pts[1:]]
    if closed:
        cmds.append(("Z",))
    st.setdefault("fill", None)
    st.setdefault("body", False)
    return El(cmds, n=host, **st)


class Plane:
    """A plane through O spanned by EX (u) and EY (v); its normal is EX x EY."""
    __slots__ = ("o", "ex", "ey")

    def __init__(self, o, ex, ey):
        self.o, self.ex, self.ey = o, ex, ey

    @property
    def n(self):
        return unit(cross(self.ex, self.ey))

    def at(self, u, v):
        return add(self.o, add(mul(self.ex, u), mul(self.ey, v)))

    def shape(self, cmds2, **st):
        out = []
        for c in cmds2:
            if c[0] in ("M", "L"):
                out.append((c[0], self.at(c[1], c[2])))
            elif c[0] == "C":
                out.append(("C", self.at(c[1], c[2]), self.at(c[3], c[4]), self.at(c[5], c[6])))
            else:
                out.append(("Z",))
        return El(out, n=self.n, **st)

    def line(self, pts2, closed=False, **st):
        return line([self.at(u, v) for u, v in pts2], closed=closed, host=self.n, **st)

    def path(self, cmds2, **st):
        """A stroked path on the plane (decoration: culled with the plane, no bbox)."""
        st.setdefault("fill", None)
        st.setdefault("body", False)
        return self.shape(cmds2, **st)


# Planes of the three faces of an axis-aligned box that the camera sees (front, right and
# top), with u and v in world units from the face's lower-left corner as seen from outside.
def front_plane(x0, x1, z0, y):           # normal -y
    return Plane((x0, y, z0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def right_plane(y0, y1, z0, x):           # normal +x
    return Plane((x, y0, z0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def top_plane(x0, y0, z):                 # normal +z: u along x, v along y
    return Plane((x0, y0, z), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))


# ----- transforms --------------------------------------------------------------------
FACINGS = {"left": 0, "right": 1, "back-right": 2, "back-left": 3}


class Tf:
    """Turn about the vertical axis by quarter turns, scale uniformly, then move."""
    __slots__ = ("r", "k", "d")

    def __init__(self, r=0, k=1.0, d=(0.0, 0.0, 0.0)):
        self.r, self.k, self.d = r % 4, k, d

    def vec(self, v):
        x, y, z = v
        if self.r == 1:
            x, y = -y, x
        elif self.r == 2:
            x, y = -x, -y
        elif self.r == 3:
            x, y = y, -x
        return (x, y, z)

    def point(self, p):
        x, y, z = self.vec(p)
        return (self.d[0] + x * self.k, self.d[1] + y * self.k, self.d[2] + z * self.k)


# ----- boxes, cylinders, spheres as element lists ------------------------------------------
def box_els(x0, y0, z0, x1, y1, z1, mat, lip=None, seam=True, edge=None, ew=0.8, top=None,
            all_faces=True):
    """The six faces of a box (the hidden ones are culled after the prop is turned).
    LIP draws a highlight along the top's edges where they meet a visible side, as the
    hero's plates do (resolved after turning, see Part.finish)."""
    p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [
        ((4, 5, 6, 7), (0.0, 0.0, 1.0)),    # top
        ((0, 1, 5, 4), (0.0, -1.0, 0.0)),   # front (-y)
        ((1, 2, 6, 5), (1.0, 0.0, 0.0)),    # right (+x)
        ((2, 3, 7, 6), (0.0, 1.0, 0.0)),    # back (+y)
        ((3, 0, 4, 7), (-1.0, 0.0, 0.0)),   # left (-x)
    ]
    out = []
    for idx, n in faces:
        st = {"fill": mat}
        if top is not None and n[2] > 0.5:
            st["fill"] = top
        if seam:
            st["seam"] = True
        if edge:
            st["stroke"] = edge
            st["sw"] = ew
        e = poly([p[i] for i in idx], n=n, **st)
        out.append(e)
    if lip:
        out.append(LipMarker((x0, y0, z1, x1, y1, z1), lip))
    return out


class LipMarker:
    """Placeholder resolved after turning: the highlight on a box top's front edges."""
    __slots__ = ("box", "color", "body", "kind")

    def __init__(self, box, color):
        self.box, self.color = box, color
        self.body = False
        self.kind = "lip"

    def points(self):
        x0, y0, z, x1, y1, _ = self.box
        return iter([(x0, y0, z), (x1, y1, z)])

    def transformed(self, tf):
        x0, y0, z, x1, y1, _ = self.box
        a = tf.point((x0, y0, z))
        b = tf.point((x1, y1, z))
        m = LipMarker((min(a[0], b[0]), min(a[1], b[1]), a[2], max(a[0], b[0]), max(a[1], b[1]), a[2]), self.color)
        return m

    def resolve(self, sw=1.0):
        s0, t0, h, s1, t1, _ = self.box
        # world-aligned now: the visible top edges are t = t0 (front-left) and s = s1 (front-right)
        return line([(s0, t0, h), (s1, t0, h), (s1, t1, h)], stroke=self.color, sw=sw, cap="round", join="round")


def cyl_els(cx, cy, z0, z1, r, mat, top=None, rim=None, rw=0.8):
    """A vertical cylinder: side and top. It turns about its own axis, so the side is
    drawn in screen space at emit time (Cyl)."""
    return [Cyl((cx, cy, z0), r, z1 - z0, mat, top=top, rim=rim, rw=rw)]


class Cyl:
    __slots__ = ("c", "r", "h", "mat", "top", "rim", "rw", "body", "kind", "st")

    def __init__(self, c, r, h, mat, top=None, rim=None, rw=0.8):
        self.c, self.r, self.h, self.mat = c, r, h, mat
        self.top, self.rim, self.rw = top, rim, rw
        self.body = True
        self.kind = "cyl"
        self.st = {}

    def points(self):
        x, y, z = self.c
        r = self.r
        return iter([(a, b, c) for a in (x - r, x + r) for b in (y - r, y + r) for c in (z, z + self.h)])

    def transformed(self, tf):
        return Cyl(tf.point(self.c), self.r * tf.k, self.h * tf.k, self.mat, self.top, self.rim, self.rw)


class Sphere:
    """A ball: a flat disc with an optional highlight, or, with SHADE = (light, dark), a
    disc shaded from its upper left (a round solid's only gradient)."""
    __slots__ = ("c", "r", "fill", "hi", "body", "kind", "st", "op", "shade")

    def __init__(self, c, r, fill, hi=None, op=None, shade=None):
        self.c, self.r, self.fill, self.hi, self.op = c, r, fill, hi, op
        self.shade = shade
        self.body = True
        self.kind = "sphere"
        self.st = {}

    def points(self):
        x, y, z = self.c
        r = self.r
        return iter([(x - r, y - r, z - r), (x + r, y + r, z + r)])

    def transformed(self, tf):
        return Sphere(tf.point(self.c), self.r * tf.k, self.fill, self.hi, self.op, self.shade)


class Glow:
    """A soft blurred spot in screen space around a 3D point (a core, a data path's
    halo). A picture may hold one glow; LAMP marks a device's small light, which the
    one-glow rule ignores only while its radius stays within LAMP_MAX units."""
    __slots__ = ("c", "r", "color", "op", "body", "kind", "st", "ry", "lamp")

    def __init__(self, c, r, color, op=0.5, ry=None, lamp=False):
        self.c, self.r, self.color, self.op = c, r, color, op
        self.ry = ry
        self.lamp = lamp
        self.body = False
        self.kind = "glow"
        self.st = {}

    def points(self):
        return iter([self.c])

    def transformed(self, tf):
        return Glow(tf.point(self.c), self.r * tf.k, self.color, self.op,
                    None if self.ry is None else self.ry * tf.k, self.lamp)


class Wall:
    """The visible wall of a ring pushed along D (a magnifier's rim): OUTER and INNER are
    the front edge's two loops of 3D points. Drawn in screen space as the outer wall (the
    hull of the outer loop and its pushed copy, less the front disc) and the inner wall
    seen through the hole (the inner loop and its pushed copy, even-odd); the ring's front
    face, drawn after it, covers the rest."""
    __slots__ = ("outer", "inner", "d", "fill", "fill2", "body", "kind", "st")

    def __init__(self, outer, inner, d, fill, fill2):
        self.outer, self.inner, self.d, self.fill, self.fill2 = outer, inner, d, fill, fill2
        self.body = True
        self.kind = "wall"
        self.st = {}

    def points(self):
        return iter(list(self.outer) + [add(p, self.d) for p in self.outer])

    def transformed(self, tf):
        v = tf.vec(self.d)
        return Wall([tf.point(p) for p in self.outer], [tf.point(p) for p in self.inner],
                    (v[0] * tf.k, v[1] * tf.k, v[2] * tf.k), self.fill, self.fill2)


class Baked:
    """Paths drawn once in the scene's projection (the hero's person): PATHS is a list of
    (fill, [polygon, ...]) in projected units with the feet at (0, 0), where one unit is
    one world unit at zoom 1 divided by K. ANCHOR is the 3D point the feet stand on and
    BOX the 3D box the figure occupies (for sorting and framing)."""
    __slots__ = ("paths", "anchor", "k", "box", "body", "kind", "st")

    def __init__(self, paths, anchor, k, box):
        self.paths, self.anchor, self.k, self.box = paths, anchor, k, box
        self.body = True
        self.kind = "baked"
        self.st = {}

    def points(self):
        x0, y0, z0, x1, y1, z1 = self.box
        return iter([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])

    def transformed(self, tf):
        x0, y0, z0, x1, y1, z1 = self.box
        a, b = tf.point((x0, y0, z0)), tf.point((x1, y1, z1))
        box = (min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]), max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2]))
        return Baked(self.paths, tf.point(self.anchor), self.k * tf.k, box)


class Sweep:
    """The side of a convex planar piece pushed along D (an extrusion's walls): drawn
    as the screen-space hull of the piece and its pushed copy."""
    __slots__ = ("pts", "d", "fill", "body", "kind", "st")

    def __init__(self, pts, d, fill):
        self.pts, self.d, self.fill = pts, d, fill
        self.body = True
        self.kind = "sweep"
        self.st = {}

    def points(self):
        return iter(list(self.pts) + [add(p, self.d) for p in self.pts])

    def transformed(self, tf):
        v = tf.vec(self.d)
        return Sweep([tf.point(p) for p in self.pts], (v[0] * tf.k, v[1] * tf.k, v[2] * tf.k), self.fill)


class Glass:
    """One half of a glass box: WHICH is 'back' (the faces turned away, seen through the
    glass, drawn before what is inside) or 'front' (the faces toward the viewer, drawn
    after). The box stays axis-aligned when a prop is turned by quarter turns."""
    __slots__ = ("box", "which", "fill", "edge", "fop", "ew", "body", "kind", "st", "floor")

    def __init__(self, box, which, fill, edge, fop=0.08, ew=1.2, floor=None):
        self.box, self.which, self.fill, self.edge = box, which, fill, edge
        self.fop, self.ew, self.floor = fop, ew, floor
        self.body = True
        self.kind = "glass"
        self.st = {}

    def points(self):
        x0, y0, z0, x1, y1, z1 = self.box
        return iter([(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])

    def transformed(self, tf):
        x0, y0, z0, x1, y1, z1 = self.box
        a, b = tf.point((x0, y0, z0)), tf.point((x1, y1, z1))
        return Glass((min(a[0], b[0]), min(a[1], b[1]), min(a[2], b[2]), max(a[0], b[0]), max(a[1], b[1]), max(a[2], b[2])),
                     self.which, self.fill, self.edge, self.fop, self.ew * tf.k, self.floor)

    def els(self):
        s0, t0, h0, s1, t1, h1 = self.box
        P = lambda s, t, h: (s, t, h)
        out = []
        if self.which == "back":
            fl = [P(s0, t0, h0), P(s1, t0, h0), P(s1, t1, h0), P(s0, t1, h0)]
            out.append(poly(fl, n=(0.0, 0.0, 1.0), cull=False, fill=self.floor or self.fill, fop=min(1.0, self.fop * 2.2)))
            out.append(poly([P(s0, t0, h0), P(s0, t1, h0), P(s0, t1, h1), P(s0, t0, h1)], n=(1.0, 0.0, 0.0), cull=False,
                            fill=self.fill, fop=self.fop * 1.4))
            out.append(poly([P(s0, t1, h0), P(s1, t1, h0), P(s1, t1, h1), P(s0, t1, h1)], n=(0.0, -1.0, 0.0), cull=False,
                            fill=self.fill, fop=self.fop * 1.4))
            c = P(s0, t1, h0)
            for q in (P(s1, t1, h0), P(s0, t0, h0), P(s0, t1, h1)):
                out.append(line([c, q], stroke=self.edge, swu=self.ew * 0.6 / 40.0, sop=0.45, cap="round"))
        else:
            out.append(poly([P(s0, t0, h1), P(s1, t0, h1), P(s1, t1, h1), P(s0, t1, h1)], n=(0.0, 0.0, 1.0), cull=False,
                            fill=self.fill, fop=self.fop))
            out.append(poly([P(s0, t0, h0), P(s1, t0, h0), P(s1, t0, h1), P(s0, t0, h1)], n=(0.0, -1.0, 0.0), cull=False,
                            fill=self.fill, fop=self.fop))
            out.append(poly([P(s1, t0, h0), P(s1, t1, h0), P(s1, t1, h1), P(s1, t0, h1)], n=(1.0, 0.0, 0.0), cull=False,
                            fill=self.fill, fop=self.fop * 1.5))
            hexa = [P(s0, t0, h0), P(s1, t0, h0), P(s1, t1, h0), P(s1, t1, h1), P(s0, t1, h1), P(s0, t0, h1)]
            out.append(line(hexa, closed=True, stroke=self.edge, swu=self.ew / 40.0, join="round"))
            c = P(s1, t0, h1)
            out.append(line([P(s0, t0, h1), c, P(s1, t1, h1)], stroke=self.edge, swu=self.ew / 40.0, join="round", cap="round"))
            out.append(line([c, P(s1, t0, h0)], stroke=self.edge, swu=self.ew / 40.0, cap="round"))
        return out


LAMP_MAX = 0.12


class Outline:
    """A prop's hairline outline, drawn just before the prop: every opaque face of its
    PARTS stroked twice as wide as the outline, so the prop, painted over it, leaves
    only the outer half showing (resolved by the writer, which knows the camera)."""
    __slots__ = ("parts", "body", "kind", "st")

    def __init__(self, parts):
        self.parts = parts
        self.body = False
        self.kind = "outline"
        self.st = {}

    def points(self):
        return iter(())

    def transformed(self, tf):
        return self


# ----- parts and sorting ------------------------------------------------------------------
class Part:
    """A convex-ish solid drawn as a unit: its elements in order. Its box is computed
    from the elements that count as body. CONVEX marks a part that is one convex solid (a
    box, a cylinder, a ball), whose outline is the hull of its faces."""
    __slots__ = ("els", "bbox", "name", "convex")

    def __init__(self, els, name="", convex=False):
        self.els = els
        self.name = name
        self.bbox = None
        self.convex = convex

    def transformed(self, tf):
        p = Part([e.transformed(tf) for e in self.els], self.name, self.convex)
        p.compute_bbox()
        return p

    def compute_bbox(self):
        pts = []
        for e in self.els:
            if e.body:
                pts.extend(e.points())
        if not pts:
            pts = [p for e in self.els for p in e.points()]
        if not pts:
            self.bbox = None
            return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        zs = [p[2] for p in pts]
        self.bbox = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def union_bbox(boxes):
    boxes = [b for b in boxes if b is not None]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), max(b[1] for b in boxes), min(b[2] for b in boxes),
            max(b[3] for b in boxes), min(b[4] for b in boxes), max(b[5] for b in boxes))


def bbox_screen(b):
    """The screen-space bounds of a world box (unit projection, no offset)."""
    xs, ys = [], []
    for s in (b[0], b[1]):
        for t in (b[2], b[3]):
            for h in (b[4], b[5]):
                x, y = project((s, t, h), 1.0)
                xs.append(x)
                ys.append(y)
    return (min(xs), max(xs), min(ys), max(ys))


def bbox_center(b):
    return ((b[0] + b[1]) / 2.0, (b[2] + b[3]) / 2.0, (b[4] + b[5]) / 2.0)


EPS = 1e-6


def before(a, b):
    """True when box A must be painted before box B, False when after, None when the
    boxes intersect (no separating axis). Toward the viewer is +s, -t and +h."""
    if a[1] <= b[0] + EPS:
        return True
    if b[1] <= a[0] + EPS:
        return False
    if a[2] >= b[3] - EPS:
        return True
    if b[2] >= a[3] - EPS:
        return False
    if a[5] <= b[4] + EPS:
        return True
    if b[5] <= a[4] + EPS:
        return False
    return None


def parts_before(a_parts, b):
    """Whether a prop made of parts with boxes A_PARTS comes before box B, when the prop's
    whole box intersects B: by the parts that overlap B on screen. None when they
    disagree or none decides."""
    sb = bbox_screen(b)
    votes = set()
    for pb in a_parts:
        sa = bbox_screen(pb)
        if sa[1] <= sb[0] + 0.01 or sb[1] <= sa[0] + 0.01 or sa[3] <= sb[2] + 0.01 or sb[3] <= sa[2] + 0.01:
            continue
        r = before(pb, b)
        if r is not None:
            votes.add(r)
    return votes.pop() if len(votes) == 1 else None


def depth_sort(items, key_bbox, key_parts=None):
    """Painter's order for items with world boxes: a topological sort over the pairs
    whose screen bounds overlap, falling back to the depth of the box centres (farthest
    first, then input order) for ties, intersections and cycles. KEY_PARTS, when given,
    returns an item's part boxes (or None): two items whose boxes intersect are then
    ordered by the parts that overlap the other item, before falling back."""
    n = len(items)
    boxes = [key_bbox(it) for it in items]
    parts = [key_parts(it) if key_parts else None for it in items]
    scr = [bbox_screen(b) if b is not None else None for b in boxes]
    # ties break on the depth rounded to 1e-6, then the input order, never on raw floats,
    # so another platform's libm cannot reorder the drawing
    dk = [(round(depth(bbox_center(b)), 6) if b is not None else -1e9, i) for i, b in enumerate(boxes)]
    succ = [[] for _ in range(n)]
    indeg = [0] * n
    for i in range(n):
        if boxes[i] is None:
            continue
        for j in range(i + 1, n):
            if boxes[j] is None:
                continue
            si, sj = scr[i], scr[j]
            if si[1] <= sj[0] + 0.01 or sj[1] <= si[0] + 0.01 or si[3] <= sj[2] + 0.01 or sj[3] <= si[2] + 0.01:
                continue
            r = before(boxes[i], boxes[j])
            if r is None and parts[i]:
                r = parts_before(parts[i], boxes[j])
            if r is None and parts[j]:
                r2 = parts_before(parts[j], boxes[i])
                r = None if r2 is None else not r2
            if r is None:
                r = dk[i] < dk[j]
            if r:
                succ[i].append(j)
                indeg[j] += 1
            else:
                succ[j].append(i)
                indeg[i] += 1
    done = [False] * n
    order = []
    ready = sorted([dk[i] for i in range(n) if indeg[i] == 0])
    import heapq
    heapq.heapify(ready)
    while len(order) < n:
        if not ready:
            # a cycle: take the farthest item left
            rest = sorted(dk[i] for i in range(n) if not done[i])
            heapq.heappush(ready, rest[0])
            indeg[rest[0][1]] = 0
        _, i = heapq.heappop(ready)
        if done[i]:
            continue
        done[i] = True
        order.append(i)
        for j in succ[i]:
            indeg[j] -= 1
            if indeg[j] == 0 and not done[j]:
                heapq.heappush(ready, dk[j])
    return [items[i] for i in order]
