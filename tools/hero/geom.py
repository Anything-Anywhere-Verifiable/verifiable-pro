"""Small 3D -> scene-projection toolkit for drawing the hero's person (spec 2.7.3);
person.py in this folder uses it.

Model space: s along u (the person's right, screen down-right), t along w (the
person's forward, screen up-right), h up, in model units with the feet centre at
the origin. The scene projects (s, t, h) to

    (GX + SCALE * .894(s + t), GY + SCALE * (.447(s - t) - h))

so SCALE sizes the figure about its feet and (GX, GY) is the feet centre in scene
units; place() sets both before a figure is drawn.

Parts are meshes of small quads. Each part is rasterized on its own grid with a
depth buffer, and its regions (silhouette, lit faces, any labelled faces) are traced
back into polygons with marching squares and simplified, so the output is a few
compact <path> elements per part, with the placement baked into their points.
"""
import math

# The figure's placement, which place() sets: its scale about the feet centre, and that
# centre in scene units (these defaults are the spec's first placement)
SCALE = 1.0
GX, GY = -12.0, 557.0


# ----- vectors -------------------------------------------------------------------
def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def mul(a, k): return (a[0] * k, a[1] * k, a[2] * k)
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def length(a): return math.sqrt(dot(a, a))
def unit(a):
    n = length(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n else (0.0, 0.0, 0.0)
def lerp(a, b, k): return tuple(x + (y - x) * k for x, y in zip(a, b))


def rot(v, axis, deg):
    """Rotate v about a unit axis (Rodrigues)."""
    a = math.radians(deg)
    k = unit(axis)
    c, s = math.cos(a), math.sin(a)
    return add(add(mul(v, c), mul(cross(k, v), s)), mul(k, dot(k, v) * (1 - c)))


U, W, Z = (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
# toward the camera: the null direction of the projection
CAM = unit((1.0, -1.0, 0.894))
# toward the light: the upper left of the screen, as on the plates (their front-left
# faces are lit, their front-right faces in shade, their tops lightest)
LIGHT = unit((-1.0, -1.0, 1.5))


def place(scale, feet):
    """Draw the next figure SCALE times its model size about its feet, with the feet
    centre at FEET = (x, y) in scene units."""
    global SCALE, GX, GY
    SCALE = scale
    GX, GY = feet


def proj(p):
    s, t, h = p
    # SCALE * h is subtracted last, so that SCALE = 1 gives the very same numbers as the
    # unscaled projection (GX + .894(s + t), GY + .447(s - t) - h)
    return (GX + SCALE * 0.894 * (s + t), GY + SCALE * 0.447 * (s - t) - SCALE * h)


def depth(p):
    return dot(p, CAM)


# ----- meshes ----------------------------------------------------------------------
class Quad:
    __slots__ = ("pts", "n", "tag", "vn", "uv")

    def __init__(self, pts, tag=None, vn=None, uv=None):
        self.pts = pts
        a, b, c, d = pts
        self.n = unit(cross(sub(c, a), sub(d, b)))
        self.tag = tag
        self.vn = vn      # vertex normals, for a smooth light/shade boundary
        self.uv = uv      # per-vertex surface coordinates, for smooth region boundaries


def catmull(keys, x):
    """Catmull-Rom through keys [(x, value_tuple)], sorted by x."""
    xs = [k[0] for k in keys]
    if x <= xs[0]:
        return keys[0][1]
    if x >= xs[-1]:
        return keys[-1][1]
    i = max(j for j in range(len(xs) - 1) if xs[j] <= x)
    x0, x1 = xs[i], xs[i + 1]
    p1, p2 = keys[i][1], keys[i + 1][1]
    p0 = keys[i - 1][1] if i > 0 else tuple(2 * a - b for a, b in zip(p1, p2))
    p3 = keys[i + 2][1] if i + 2 < len(keys) else tuple(2 * b - a for a, b in zip(p1, p2))
    # non-uniform spacing: tangents from the neighbouring key spacing
    xm = keys[i - 1][0] if i > 0 else x0 - (x1 - x0)
    xp = keys[i + 2][0] if i + 2 < len(keys) else x1 + (x1 - x0)
    tt = (x - x0) / (x1 - x0)
    out = []
    for a0, a1, a2, a3 in zip(p0, p1, p2, p3):
        m1 = (a2 - a0) / (x1 - xm) * (x1 - x0)
        m2 = (a3 - a1) / (xp - x0) * (x1 - x0)
        t2, t3 = tt * tt, tt * tt * tt
        out.append((2 * t3 - 3 * t2 + 1) * a1 + (t3 - 2 * t2 + tt) * m1 + (-2 * t3 + 3 * t2) * a2 + (t3 - t2) * m2)
    return tuple(out)


def se(c, p):
    """Superellipse coordinate: p = 2 is an ellipse, larger p is boxier."""
    return math.copysign(abs(c) ** (2.0 / p), c)


def ring(centre, e1, e2, r1, r2, p, nphi):
    pts = []
    for j in range(nphi):
        f = 2 * math.pi * j / nphi
        x, y = se(math.cos(f), p) * r1, se(math.sin(f), p) * r2
        pts.append(add(centre, add(mul(e1, x), mul(e2, y))))
    return pts


def frame(T, ref):
    T = unit(T)
    e1 = unit(sub(ref, mul(T, dot(ref, T))))
    e2 = cross(T, e1)
    return e1, e2


def tube(keys, ref=U, step=0.3, nphi=96, cap0=False, cap1=False, tag=None):
    """A tube through keys [(point, r1, r2, p)], with sections perpendicular to the
    spine (r1 along the frame axis nearest REF). cap0/cap1 round the ends off with
    half-ellipsoids; an open end shows its inside (tag 'in')."""
    # arc-length parameter along the key points
    ls = [0.0]
    for a, b in zip(keys, keys[1:]):
        ls.append(ls[-1] + length(sub(b[0], a[0])))
    data = [(l, tuple(k[0]) + (k[1], k[2], k[3])) for l, k in zip(ls, keys)]
    total = ls[-1]
    n = max(2, int(total / step) + 1)
    secs = []
    for i in range(n + 1):
        l = total * i / n
        v = catmull(data, l)
        c = v[:3]
        dl = 0.05
        T = sub(catmull(data, min(total, l + dl))[:3], catmull(data, max(0.0, l - dl))[:3])
        secs.append((c, T, v[3], v[4], v[5]))

    def capped(end, sign):
        c, T, r1, r2, p = end
        T = mul(unit(T), sign)
        out = []
        for k in range(1, 9):
            a = math.radians(90 * k / 9)
            out.append((add(c, mul(T, max(r1, r2) * 0.92 * math.sin(a))), mul(T, sign), r1 * math.cos(a),
                        r2 * math.cos(a), p))
        return out
    if cap0:
        secs = list(reversed(capped(secs[0], -1))) + secs
    if cap1:
        secs = secs + capped(secs[-1], 1)
    rings = []
    for c, T, r1, r2, p in secs:
        e1, e2 = frame(T, ref)
        rings.append(ring(c, e1, e2, max(r1, 0.02), max(r2, 0.02), p, nphi))
    nr = len(rings)
    vns = []
    for i in range(nr):
        row = []
        for j in range(nphi):
            dphi = sub(rings[i][(j + 1) % nphi], rings[i][j - 1])
            dl = sub(rings[min(i + 1, nr - 1)][j], rings[max(i - 1, 0)][j])
            nv = unit(cross(dphi, dl))
            if dot(nv, sub(rings[i][j], secs[i][0])) < 0 and length(sub(rings[i][j], secs[i][0])) > 0.05:
                nv = mul(nv, -1)
            row.append(nv)
        vns.append(row)
    quads = []
    for i, ((ca, *_), (cb, *_), a, b) in enumerate(zip(secs, secs[1:], rings, rings[1:])):
        mid = lerp(ca, cb, 0.5)
        for j in range(nphi):
            k = (j + 1) % nphi
            q = Quad((a[j], a[k], b[k], b[j]), tag)
            c = mul(add(add(a[j], a[k]), add(b[k], b[j])), 0.25)
            if dot(q.n, sub(c, mid)) < 0:
                q.n = mul(q.n, -1)
            vn = [vns[i][j], vns[i][k], vns[i + 1][k], vns[i + 1][j]]
            # tip rings are tiny: fall back to the face normal where a vertex normal flips
            q.vn = [v if dot(v, q.n) > 0 else q.n for v in vn]
            quads.append(q)
    return quads, rings


def ellipsoid(O, ax, ay, az, nu=72, nv=48):
    """An ellipsoid with orthogonal semi-axis vectors ax, ay, az. Each quad carries its
    vertices' unit-sphere coordinates (X toward ax, Y toward ay, Z toward az) in uv."""
    la, lb, lc = dot(ax, ax), dot(ay, ay), dot(az, az)
    grid = []
    for i in range(nv + 1):
        b = -math.pi / 2 + math.pi * i / nv
        row = []
        for j in range(nu):
            a = 2 * math.pi * j / nu
            X, Y, Zc = math.cos(b) * math.cos(a), math.cos(b) * math.sin(a), math.sin(b)
            p = add(O, add(add(mul(ax, X), mul(ay, Y)), mul(az, Zc)))
            nrm = unit(add(add(mul(ax, X / la), mul(ay, Y / lb)), mul(az, Zc / lc)))
            row.append((p, (X, Y, Zc), nrm))
        grid.append(row)
    quads = []
    for i in range(nv):
        for j in range(nu):
            k = (j + 1) % nu
            cells = (grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j])
            q = Quad(tuple(c[0] for c in cells), vn=[c[2] for c in cells], uv=[c[1] for c in cells])
            # the quad's normal must point outward
            if dot(q.n, sub(mul(add(add(q.pts[0], q.pts[1]), add(q.pts[2], q.pts[3])), .25), O)) < 0:
                q.n = mul(q.n, -1)
            quads.append(q)
    return quads


def box(O, ax, ay, az, tag=None):
    """A box with half-axis vectors; returns its six faces."""
    quads = []
    for axis, o1, o2 in ((ax, ay, az), (ay, az, ax), (az, ax, ay)):
        for sgn in (1, -1):
            c = add(O, mul(axis, sgn))
            pts = (add(c, add(o1, o2)), add(c, sub(o1, o2)), sub(c, add(o1, o2)), add(c, sub(o2, o1)))
            q = Quad(pts, tag)
            if dot(q.n, mul(axis, sgn)) < 0:
                q.n = mul(q.n, -1)
            quads.append(q)
    return quads


# ----- raster ----------------------------------------------------------------------
class Raster:
    """A grid of RES scene units over the projected quads, with a depth and a label per cell."""

    def __init__(self, quads, res=0.04, pad=0.5):
        xs, ys = [], []
        for q in quads:
            for p in q.pts:
                x, y = proj(p)
                xs.append(x)
                ys.append(y)
        self.res = res
        self.x0, self.y0 = min(xs) - pad, min(ys) - pad
        self.w = int((max(xs) + pad - self.x0) / res) + 2
        self.h = int((max(ys) + pad - self.y0) / res) + 2
        self.z = [-1e9] * (self.w * self.h)
        self.label = [None] * (self.w * self.h)

    def fill(self, quads, label_of, backfaces=False):
        """Rasterize QUADS. label_of(q, front) gives a label, None to skip, or a pair
        (values, fn): per-vertex value tuples and a function of their interpolation."""
        res, x0, y0, w = self.res, self.x0, self.y0, self.w
        zb, lb = self.z, self.label
        for q in quads:
            facing = dot(q.n, CAM)
            if facing <= 0 and not backfaces:
                continue
            lab = label_of(q, facing > 0)
            if lab is None:
                continue
            vals = fn = None
            if isinstance(lab, tuple):
                vals, fn = lab
                labs = {fn(v) for v in vals}
                if len(labs) == 1:
                    lab, vals = labs.pop(), None
            P = [proj(p) for p in q.pts]
            zq = sum(depth(p) for p in q.pts) / 4 - (0 if facing > 0 else 1e3)
            for tv in ((0, 1, 2), (0, 2, 3)):
                (ax, ay), (bx, by), (cx, cy) = P[tv[0]], P[tv[1]], P[tv[2]]
                area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
                if abs(area) < 1e-12:
                    continue
                i0 = max(0, int((min(ay, by, cy) - y0) / res - 0.5))
                i1 = min(self.h - 1, int((max(ay, by, cy) - y0) / res + 0.5))
                j0 = max(0, int((min(ax, bx, cx) - x0) / res - 0.5))
                j1 = min(w - 1, int((max(ax, bx, cx) - x0) / res + 0.5))
                # cell centres; the differences below are the same as computed per cell, only hoisted
                pxs = [x0 + (j + 0.5) * res for j in range(j0, j1 + 1)]
                for i in range(i0, i1 + 1):
                    py = y0 + (i + 0.5) * res
                    ayp, byp, cyp = ay - py, by - py, cy - py
                    k = i * w + j0 - 1
                    for px in pxs:
                        k += 1
                        if zq <= zb[k]:
                            continue  # a nearer face holds the cell, inside the triangle or not
                        axp, bxp, cxp = ax - px, bx - px, cx - px
                        w0 = bxp * cyp - byp * cxp
                        w1 = cxp * ayp - cyp * axp
                        w2 = axp * byp - ayp * bxp
                        if (w0 >= 0 and w1 >= 0 and w2 >= 0) or (w0 <= 0 and w1 <= 0 and w2 <= 0):
                            zb[k] = zq
                            if vals is None:
                                lb[k] = lab
                            else:
                                va, vb, vc = vals[tv[0]], vals[tv[1]], vals[tv[2]]
                                la, lb_, lc = w0 / area, w1 / area, w2 / area
                                lb[k] = fn(tuple(a * la + b * lb_ + c * lc for a, b, c in zip(va, vb, vc)))

    def mask(self, pred):
        return [1 if (l is not None and pred(l)) else 0 for l in self.label]

    def paths(self, pred, eps=0.05):
        return trace(self.mask(pred), self.w, self.h, self.x0, self.y0, self.res, eps)


# ----- vectorizing -------------------------------------------------------------------
# Marching squares: the segments each case of a cell's four corners adds, as offsets of
# their end points from the cell; corner points are cell centres, and the edge midpoints
# between them are top (1, .5), right (1.5, 1), bottom (1, 1.5) and left (.5, 1)
_T, _R, _B, _L = (1.0, 0.5), (1.5, 1.0), (1.0, 1.5), (0.5, 1.0)
CASES = {
    1: [(_L, _B)], 2: [(_B, _R)], 3: [(_L, _R)], 4: [(_R, _T)],
    5: [(_L, _T), (_R, _B)], 6: [(_B, _T)], 7: [(_L, _T)], 8: [(_T, _L)],
    9: [(_T, _B)], 10: [(_T, _R), (_B, _L)], 11: [(_T, _R)], 12: [(_R, _L)],
    13: [(_R, _B)], 14: [(_B, _L)],
}


def trace(mask, w, h, x0, y0, res, eps):
    """Marching squares on a binary mask; returns closed polygons in scene units,
    simplified with Douglas-Peucker (EPS) and wound so that nonzero fill keeps holes."""
    # the mask inside a border of empty cells: row i, column j is at (i + 1) * pw + j + 1
    pw = w + 2
    pm = bytearray(pw * (h + 2))
    for i in range(h):
        pm[(i + 1) * pw + 1:(i + 1) * pw + 1 + w] = bytes(mask[i * w:(i + 1) * w])
    # edges between cell corners: walk the boundary of each filled cell, row by row, over
    # the columns where either of the cell's two rows has a filled cell
    segs = {}
    for i in range(-1, h):
        r0 = (i + 1) * pw
        r1 = r0 + pw
        cols = [k - r for r in (r0, r1) for k in (pm.find(1, r, r + pw), pm.rfind(1, r, r + pw)) if k >= 0]
        if not cols:
            continue
        for j in range(min(cols) - 2, max(cols)):
            code = pm[r0 + j + 1] * 8 + pm[r0 + j + 2] * 4 + pm[r1 + j + 2] * 2 + pm[r1 + j + 1]
            if code in (0, 15):
                continue
            for (pa, pb), (qa, qb) in CASES[code]:
                segs.setdefault((j + pa, i + pb), []).append((j + qa, i + qb))
    loops = []
    while segs:
        start = next(iter(segs))
        loop = [start]
        cur = start
        while True:
            nxts = segs.get(cur)
            if not nxts:
                break
            nxt = nxts.pop()
            if not nxts:
                del segs[cur]
            if nxt == start:
                break
            loop.append(nxt)
            cur = nxt
        if len(loop) > 3:
            pts = [(x0 + x * res, y0 + y * res) for x, y in loop]
            pts = rdp_closed(pts, eps)
            if len(pts) >= 3 and abs(poly_area(pts)) > 0.3:
                loops.append(pts)
    return loops


def poly_area(pts):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))


def rdp(pts, eps):
    if len(pts) < 3:
        return pts
    (ax, ay), (bx, by) = pts[0], pts[-1]
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy)
    best, idx = -1, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        d = abs(dy * (px - ax) - dx * (py - ay)) / L if L else math.hypot(px - ax, py - ay)
        if d > best:
            best, idx = d, i
    if best <= eps:
        return [pts[0], pts[-1]]
    return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)


def rdp_closed(pts, eps):
    # split at the two points farthest apart, simplify both halves
    i = 0
    j = max(range(len(pts)), key=lambda k: (pts[k][0] - pts[0][0]) ** 2 + (pts[k][1] - pts[0][1]) ** 2)
    a = rdp(pts[i:j + 1], eps)
    b = rdp(pts[j:] + pts[:1], eps)
    return a[:-1] + b[:-1]


def fmt(v, digits=1):
    """A number as the scene writes them: DIGITS decimals (one for coordinates), no
    trailing zeros, no leading zero."""
    s = f"{v:.{digits}f}".rstrip("0").rstrip(".")
    if s in ("-0", "", "-"):
        return "0"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def d_attr(loops, min_size=1.0):
    """Polygons as compact path data in the scene's style: an absolute M, then relative
    l, h and v steps between points rounded to 0.1 (so nothing drifts), and z. Loops
    smaller than MIN_SIZE across both ways are dropped (no feature under one unit)."""
    out = []
    for pts in loops:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if max(xs) - min(xs) < min_size and max(ys) - min(ys) < min_size:
            continue
        q = [(round(x * 10), round(y * 10)) for x, y in pts]
        q = [p for i, p in enumerate(q) if p != q[i - 1]]
        d = f"M{fmt(q[0][0] / 10)},{fmt(q[0][1] / 10)}"
        for (x0, y0), (x1, y1) in zip(q, q[1:]):
            dx, dy = (x1 - x0) / 10, (y1 - y0) / 10
            if dy == 0:
                step = "h" + fmt(dx)
            elif dx == 0:
                step = "v" + fmt(dy)
            else:
                a, b = fmt(dx), fmt(dy)
                step = "l" + a + ("" if b.startswith("-") else ",") + b
            d += step
        out.append(d + "z")
    return "".join(out)
