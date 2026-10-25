#!/usr/bin/env python3
"""Draw the hero scene's person (spec 2.7) for sitegen/templates/hero-scene.svg: you,
the reader, talking with an AI system, and the small moment the scene plays for you.

The model: an adult seen from behind in a three-quarter rear view, standing on the
ground left of and in front of the board's left corner and reading a phone held in
both hands at chest height; the phone's screen carries the chain's indigo ring. P
poses the figure in model units (s to the person's right, t forward, h up; about 90
from soles to crown at scale 1): shoes, legs, a knee-length coat, arms, neck and head
built from tubes, ellipsoids and a box. geom.py projects each part into the scene's
isometric view, rasterizes it with a depth buffer, splits it into lit and shaded faces
(the light comes from the upper left, as on the plates) and traces each region back
into a compact path of straight segments. The scene keeps only those paths: the
geometry is baked into their points, never into a transform (build.py refuses one;
the scene's stylesheet may still play a hop on g.hv-person that ends where it starts).

The block also holds what the person's moment needs, placed from the figure: a glow
behind them and their foot shadow (outside g.hv-person, so neither hops), over the
phone's ring the screen in the TEE's indigo with a small lock, a thought bubble over
the head with a shield and two sparkles, two ripples at the phone, and last the hit
area, path.hv-you-hit, that static/hero.js listens to. The stylesheet shows them
while T1 or T2 is open and for a moment after a click (DESIGN.md, "The person's
moment"); tools/hero/flow.py starts the data's route at the phone's ring.

The parameters:
    SCALE  the figure's size, as a factor about its feet; the foot shadow and the
           phone's halo, ring and dot scale with it
    FEET   the feet centre (x, y) in scene units, on the ground plane
The figure must stay inside the scene's viewBox (x from -28) and end at x <= 7.3, 6
units clear of the board's left corner at x = 13.3; tests/test_sitegen.py checks both
on the scene's path points.

The commands, from the repository root (standard library only; a few seconds):
    python3 tools/hero/person.py           # print the block: its comment line to the hit area
    python3 tools/hero/person.py --write   # replace that block in sitegen/templates/hero-scene.svg
    python3 tools/hero/person.py --check   # exit 0 when the scene's block is what this draws, else 1

The colours are the scene's --hv-coat, --hv-coat2, --hv-legs, --hv-legs2, --hv-shoe,
--hv-skin, --hv-skin2, --hv-hair and --hv-phone, with --hv-lit (the filter that lights
the figure while a layer is open), --hv-yglow (and its opacity --hv-yglow-o) for the
glow and --hv-spark for the sparkles, set in each of its three palette blocks (light,
dark by system, dark by choice); the screen, the lock, the bubble and the ripples use
the scene's TEE indigo.

The review protocol (spec 2.7.6), after any change to the figure or its colours: build
a preview and look at the person on the home page at 1440 and 390px wide, in light
and dark, at 1x and 2x:
    node tools/cdp.mjs eval SITE --page home --width 1440 --height 1000 \\
        --js "JSON.stringify(document.querySelector('.hv-person').getBoundingClientRect())"
    node tools/cdp.mjs zoom SITE out.png --page home --width 1440 --clip x,y,w,h --scale 2 [--dark]
(--clip is in CSS pixels of the page: the box above with a margin; zoom lays the page
out 1000px tall unless --height says otherwise). It passes when
  - at 1x, the figure reads as a person seen from behind looking at a phone;
  - at 2x, the indigo ring on the phone is visible, and with T1 open the lock on the
    indigo screen and the shield in the bubble read as such;
  - the coat, both tones, keeps at least 3:1 against the page (#ffffff light,
    #111416 dark) in both themes;
  - the trousers and hair keep at least 3:1 against the page in dark;
  - the bubble and its sparkles stay left of the data's dotted route.
"""
import math
import re
import sys
from pathlib import Path

# No __pycache__ beside the script; geom.py is found beside it from any folder
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from geom import (LIGHT, U, W, Z, Raster, add, box, cross, d_attr, dot, ellipsoid, fmt, lerp, mul,  # noqa: E402
                  place, proj, rot, sub, tube, unit)

ROOT = HERE.parent.parent
SCENE = Path("sitegen") / "templates" / "hero-scene.svg"
# The figure's size about its feet, and the feet centre in scene units. At 1.2 it spans
# x -27.5 to 7.0 and y 452.5 to 563.9; 1.25 would cross both bounds in the docstring.
# (1.0 at (-12, 557) draws the spec's first figure.)
SCALE = 1.2
FEET = (-15.0, 557.5)
COMMENT = ("<!-- The person: you, talking with an AI system, seen from behind on the ground in front of the board, "
           "reading a phone that shows the chain's ring; then the moment it plays: a glow, a thought bubble with a "
           "shield, ripples from the phone, and the hit area that a click or a tap plays it from -->")
# The person's block in the scene: its comment line, up to and including the hit area,
# which is the block's last line
BLOCK = re.compile(r'^<!-- The person:[^\n]*-->\n.*?^<path class="hv-you-hit"[^\n]*/>\n', re.S | re.M)
P = {
    # shoes: heel back point (s, t), direction (degrees from forward, + = outward), length
    "shoe_r": ((2.75, -2.5), 8.0, 9.4),
    "shoe_l": ((-3.35, -0.9), -8.0, 9.4),
    # legs, top (under the coat) to the trouser hem: (s, t, h, r1, r2)
    "leg_r": [(2.5, -0.3, 30.0, 2.3, 2.4), (2.55, -0.45, 24.0, 2.1, 2.2), (2.62, -0.6, 14.0, 1.95, 2.05),
              (2.7, -0.75, 6.0, 1.62, 1.72), (2.72, -0.8, 2.2, 1.66, 1.78)],
    "leg_l": [(-2.65, 0.1, 30.0, 2.3, 2.4), (-2.95, 0.75, 24.0, 2.1, 2.2), (-3.2, 1.15, 14.0, 1.95, 2.05),
              (-3.35, 1.3, 6.0, 1.62, 1.72), (-3.38, 1.32, 2.2, 1.66, 1.78)],
    # coat: (cs, ct, h, a, d, p) from the hem up to the top of its stand collar
    "coat": [(0.45, 0.25, 26.5, 8.6, 5.5, 2.2), (0.5, 0.12, 32.5, 7.9, 5.1, 2.2), (0.5, 0.0, 41.0, 7.25, 4.75, 2.25),
             (0.35, 0.0, 49.0, 6.7, 4.35, 2.3), (0.2, 0.15, 56.0, 7.1, 4.5, 2.35), (0.1, 0.4, 62.0, 7.6, 4.7, 2.4),
             (0.0, 0.65, 66.5, 7.75, 4.65, 2.45), (0.0, 0.8, 69.0, 7.3, 4.45, 2.4), (0.0, 0.9, 71.2, 6.3, 4.1, 2.3),
             (0.0, 0.98, 73.1, 4.9, 3.55, 2.15), (0.0, 1.0, 74.7, 3.45, 2.95, 2.0), (0.0, 0.8, 76.4, 3.15, 2.8, 2.0),
             (0.0, 0.5, 77.5, 3.0, 2.6, 2.0)],
    # arms: shoulder and elbow joints; each forearm runs to a wrist beside the phone
    "shoulder_r": (7.55, 0.5, 68.6), "elbow_r": (9.25, -0.1, 53.3),
    "shoulder_l": (-7.45, 0.5, 68.3), "elbow_l": (-8.85, 1.0, 53.8),
    "arm": (2.25, 2.05, 1.95), "fore": (1.9, 1.55),
    # the phone, held in both hands in landscape: centre, long axis (across, the person's right),
    # screen normal (toward the eyes), half long, half wide, half thick, screen inset
    "phone": (3.3, 11.6, 58.6), "phone_l": (0.96, 0.22, 0.06), "phone_n": (-0.1, -0.45, 0.88),
    "phone_size": (3.0, 1.98, 0.26), "inset": 0.42,
    # neck and head
    "neck": [(0.0, 1.1, 73.0, 1.95, 2.05), (0.1, 1.6, 74.6, 1.9, 2.0), (0.25, 2.2, 75.9, 1.88, 1.98)],
    "head_pivot": (0.25, 2.2, 75.9), "head_offset": (0.0, 1.2, 4.8), "bow": 38.0, "yaw": 6.0,
    "head_axes": (3.85, 4.6, 5.5),
    # the foot shadow: centre (s, t) and radii in scene units at scale 1
    "shadow": (0.0, 1.2), "shadow_r": (11.5, 5.8),
}


def lit_label(q, front):
    """Two tones: lit where the surface faces the light (interpolated from the vertex
    normals, so the boundary is smooth), in shade elsewhere; back faces are 'inner'."""
    if not front:
        return "inner"
    if not q.vn:
        return "lit" if dot(q.n, LIGHT) > 0 else "shade"
    return ([(dot(v, LIGHT),) for v in q.vn], lambda v: "lit" if v[0] > 0 else "shade")


def part(quads, out, base, lit=None, label=None, extra=()):
    """Rasterize one part and append its paths: the whole silhouette in BASE (back
    faces fill any pinholes and show inside an open end), then its lit faces in LIT,
    then any labelled regions in EXTRA [(label, class)]."""
    r = Raster(quads, res=0.04)
    if label is None:
        label = lit_label if lit else (lambda q, front: "all" if front else "inner")
    r.fill(quads, label, backfaces=True)
    out.append((base, d_attr(r.paths(lambda l: True))))
    if lit:
        out.append((lit, d_attr(r.paths(lambda l: l == "lit"))))
    for tag, cls in extra:
        loops = r.paths(lambda l, tag=tag: l == tag)
        if loops:
            out.append((cls, d_attr(loops)))
    return r


def shoe(heel, ang, L):
    d = (math.sin(math.radians(ang)), math.cos(math.radians(ang)), 0.0)
    # (distance from the heel back, half width, half height)
    prof = [(1.2, 1.25, 1.25), (3.0, 1.45, 1.22), (5.4, 1.6, 1.0), (7.4, 1.45, 0.84), (L - 1.0, 1.05, 0.7)]
    keys = [((heel[0] + d[0] * x, heel[1] + d[1] * x, hh), hw, hh, 2.6) for x, hw, hh in prof]
    q, _ = tube(keys, ref=Z, cap0=True, cap1=True, nphi=64)
    return q


def limb(a, b, ra, rb, n=48):
    q, _ = tube([(a, ra, ra, 2.0), (lerp(a, b, 0.5), (ra + rb) / 2, (ra + rb) / 2, 2.0), (b, rb, rb, 2.0)],
                ref=U, cap0=True, cap1=True, nphi=n, step=0.2)
    return q


def build(p, scale=SCALE, feet=FEET):
    """The figure posed by P, SCALE times its model size with the feet centre at FEET:
    a list of (class, path data) from back to front, with the foot shadow as markup and
    the phone's halo and ring as their centres."""
    place(scale, feet)
    out = []
    sx, sy = proj((p["shadow"][0], p["shadow"][1], 0.0))
    rx, ry = p["shadow_r"]
    out.append(("hv-foot", f'<ellipse class="hv-foot" cx="{fmt(sx)}" cy="{fmt(sy)}" rx="{fmt(rx * scale)}" '
                           f'ry="{fmt(ry * scale)}"/>'))
    # far leg first: its shoe, its trousers; then the near leg
    for side, cls in (("l", "hv-plegs2"), ("r", "hv-plegs")):
        heel, ang, L = p["shoe_" + side]
        part(shoe(heel, ang, L), out, "hv-pshoe")
        keys = [((s, t, h), r1, r2, 2.0) for s, t, h, r1, r2 in p["leg_" + side]]
        q, _ = tube(keys, ref=U, nphi=72)
        part(q, out, cls)
    # the phone's frame: Lx along its length (across the person, to their right), n toward
    # the eyes, Wx across the screen (away from the person)
    Lx = unit(p["phone_l"])
    n0 = unit(p["phone_n"])
    n = unit(sub(n0, mul(Lx, dot(n0, Lx))))
    Wx = unit(cross(n, Lx))
    pc = p["phone"]
    hl, hw, ht = p["phone_size"]
    wrist_r = add(add(add(pc, mul(Lx, 3.2)), mul(Wx, -1.2)), mul(n, -1.1))
    wrist_l = add(add(add(pc, mul(Lx, -3.2)), mul(Wx, -1.2)), mul(n, -1.1))
    a1, a2, a3 = p["arm"]
    f1, f2 = p["fore"]
    # the left arm, behind the coat: forearm, then the upper arm
    part(limb(p["elbow_l"], wrist_l, f1, f2), out, "hv-pcoat2", "hv-pcoat")
    part(limb(p["shoulder_l"], p["elbow_l"], a1, a3), out, "hv-pcoat2", "hv-pcoat")
    # the coat, open at the collar (its inside shows in shade)
    keys = [((s, t, h), a, d, pp) for s, t, h, a, d, pp in p["coat"]]
    q, _ = tube(keys, ref=U, nphi=160, step=0.2)
    part(q, out, "hv-pcoat2", "hv-pcoat")
    # the neck, then the head
    keys = [((s, t, h), r1, r2, 2.0) for s, t, h, r1, r2 in p["neck"]]
    q, _ = tube(keys, ref=U, nphi=48)
    part(q, out, "hv-pskin")
    piv, bow, yaw = p["head_pivot"], p["bow"], p["yaw"]

    def orient(v):
        return rot(rot(v, U, -bow), Z, -yaw)  # bow: the face tips forward and down
    O = add(piv, orient(p["head_offset"]))
    hx, hy, hz = p["head_axes"]
    ax, ay, az = mul(orient(U), hx), mul(orient(W), hy), mul(orient(Z), hz)

    def face(X, Y, Zc):
        """> 0 in front of the hairline and the jaw: the temple line runs forward as it
        rises, the sideburn drops in front of the ear, the jaw line runs forward to the chin."""
        if Zc >= 0.25:
            yh = 0.12 + 0.5 * (Zc - 0.25)
        elif Zc >= -0.35:
            yh = 0.04
        else:
            yh = 0.04 + 0.6 * (-0.35 - Zc)
        return Y - yh

    def head_label(q, front):
        # hair down to the neck at the back; the neck below it is the nape
        if not front:
            return "hair"
        return ([(face(*c),) for c in q.uv], lambda v: "face" if v[0] > 0 else "hair")
    q = ellipsoid(O, ax, ay, az)
    part(q, out, "hv-phair", label=head_label, extra=(("face", "hv-pskin2"),))
    ear = add(O, add(add(mul(orient(U), hx * 0.96), mul(orient(W), -0.25)), mul(orient(Z), -0.6)))
    q = ellipsoid(ear, mul(orient(U), 0.42), mul(orient(W), 0.85), mul(orient(Z), 1.25), nu=32, nv=16)
    part(q, out, "hv-pskin2")
    # the right arm: upper arm, hand, phone, forearm
    part(limb(p["shoulder_r"], p["elbow_r"], a1, a3), out, "hv-pcoat2", "hv-pcoat")
    # the hands hold the phone's two ends from below; their outer edges show
    for sgn in (-1, 1):
        hand = add(add(add(pc, mul(Lx, sgn * 2.55)), mul(Wx, -0.35)), mul(n, -0.55))
        part(ellipsoid(hand, mul(Lx, 1.0), mul(Wx, 1.45), mul(n, 0.75), nu=40, nv=20), out, "hv-pskin2")
    top = add(pc, mul(n, ht + 0.01))
    # the halo glows behind the phone, so the phone's dark body reads against it in both themes
    out.append(("halo", proj(top)))
    part(box(pc, mul(Lx, hl), mul(Wx, hw), mul(n, ht)), out, "hv-pphone")
    i = p["inset"]
    corners = [add(add(top, mul(Lx, a * (hl - i))), mul(Wx, b * (hw - i))) for a, b in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    out.append(("hv-pscreen", d_attr([list(map(proj, corners))])))
    out.append(("ring", proj(top)))
    part(limb(p["elbow_r"], wrist_r, f1, f2), out, "hv-pcoat2", "hv-pcoat")
    return out


def points(d):
    """The points of path data in the scene's style (M, then relative l, h and v)."""
    pts, x, y = [], 0.0, 0.0
    for cmd, args in re.findall(r"([MlhvZz])([^MlhvZz]*)", d):
        nums = [float(v) for v in re.findall(r"-?(?:\d+\.?\d*|\.\d+)", args)]
        step = 1 if cmd in "hv" else 2
        for i in range(0, len(nums) if cmd not in "Zz" else 0, step):
            if cmd == "M":
                x, y = nums[i], nums[i + 1]
            elif cmd == "l":
                x, y = x + nums[i], y + nums[i + 1]
            elif cmd == "h":
                x += nums[i]
            else:
                y += nums[i]
            pts.append((x, y))
    return pts


def sparkle(x, y, r):
    """A four-pointed sparkle centred on (x, y), R from its centre to each point."""
    k = r * 0.16  # the waist: how far the curves pass from the centre
    f = lambda v: fmt(v, 2)
    return (f"M{f(x)},{f(y - r)}C{f(x + k)},{f(y - k)} {f(x + k)},{f(y - k)} {f(x + r)},{f(y)}"
            f"C{f(x + k)},{f(y + k)} {f(x + k)},{f(y + k)} {f(x)},{f(y + r)}"
            f"C{f(x - k)},{f(y + k)} {f(x - k)},{f(y + k)} {f(x - r)},{f(y)}"
            f"C{f(x - k)},{f(y - k)} {f(x - k)},{f(y - k)} {f(x)},{f(y - r)}Z")


def markup(out, scale=SCALE):
    """The scene's block for the parts OUT of build(): the comment line; the glow behind
    the person and their foot shadow, which stay put while the figure hops; the group
    g.hv-person, with the phone's halo, ring and dot SCALE times their size at scale 1
    (radii keep up to two decimals, as the dot's .45 needs) and, over the ring, the
    screen as it turns indigo with a small lock (hidden at rest); then the person's
    moment, placed from the head and the phone: the thought bubble with the shield and
    two sparkles, the two ripples from the phone, and last the transparent hit area
    that a click or a tap on the person plays the moment from. The scene's stylesheet
    shows these; every size here scales with SCALE (k)."""
    k = scale / 1.2  # the moment was drawn for SCALE 1.2

    def r(v):
        return fmt(v * scale, 2)

    def f(v):
        return fmt(v, 2)
    body = [pt for cls, d in out if cls.startswith("hv-p") and not d.startswith("<") for pt in points(d)]
    x0, x1 = min(x for x, y in body), max(x for x, y in body)
    y0, y1 = min(y for x, y in body), max(y for x, y in body)
    hair = points(next(d for cls, d in out if cls == "hv-phair"))
    hx = (min(x for x, y in hair) + max(x for x, y in hair)) / 2
    ht = min(y for x, y in hair)
    lines = [COMMENT]
    # the glow: an ellipse over the figure's box, lit by a radial gradient (the scene's hv-yglow)
    lines.append(f'<ellipse class="hv-you-glow" cx="{f((x0 + x1) / 2)}" cy="{f((y0 + y1) / 2 + 4 * k)}" '
                 f'rx="{f((x1 - x0) / 2 + .6 * k)}" ry="{f((y1 - y0) / 2 + 6 * k)}" fill="url(#hv-yglow)"/>')
    screen = ""
    for cls, d in out:
        if cls == "hv-foot":
            lines.append(d.replace('class="hv-foot"', 'class="hv-foot hv-pfoot"'))
            lines.append('<g class="hv-person">')
        elif cls == "halo":
            cx, cy = map(fmt, d)
            lines.append(f'<ellipse class="hv-nh hv-t" cx="{cx}" cy="{cy}" rx="{r(4.4)}" ry="{r(2.2)}" style="--hv-d:0s"/>')
        elif cls == "ring":
            px, py = d
            cx, cy = fmt(px), fmt(py)
            lines.append(f'<ellipse class="hv-nr hv-t hv-ph-ring" cx="{cx}" cy="{cy}" rx="{r(1.7)}" ry="{r(1.1)}"/>')
            lines.append(f'<ellipse class="hv-nd hv-t" cx="{cx}" cy="{cy}" rx="{r(.7)}" ry="{r(.45)}"/>')
            # the screen in the TEE's indigo, and a small lock on it, drawn in straight segments;
            # one group, so that showing it restyles one element
            u = scale / 1.2
            lines.append('<g class="hv-ptee">')
            lines.append(f'<path class="hv-pscreen-tee" d="{screen}"/>')
            lines.append(f'<rect class="hv-plock" x="{f(px - .95 * u)}" y="{f(py - .15 * u)}" width="{f(1.9 * u)}" '
                         f'height="{f(1.45 * u)}"/>')
            lines.append(f'<path class="hv-plock-s" d="M{f(px - .55 * u)},{f(py - .1 * u)}V{f(py - .6 * u)}'
                         f'L{f(px - .3 * u)},{f(py - .95 * u)}H{f(px + .3 * u)}L{f(px + .55 * u)},{f(py - .6 * u)}'
                         f'V{f(py - .1 * u)}"/>')
            lines.append('</g>')
        elif d.startswith("<"):
            lines.append(d)
        elif d:
            if cls == "hv-pscreen":
                screen = d
            lines.append(f'<path class="{cls}" d="{d}"/>')
    lines.append("</g>")
    # the moment: a thought bubble over the head (left of the data's route up from the phone),
    # with a shield and a lock in the TEE's indigo, its tail of two dots down to the head, and
    # two sparkles
    bx, by, br = hx - 0.5 * k, ht - 21.0 * k, 9.0 * k
    lines.append('<g class="hv-bubble">')
    lines.append(f'<circle class="hv-bub" cx="{f(hx + 0.6 * k)}" cy="{f(ht - 3.0 * k)}" r="{f(1.05 * k)}"/>')
    lines.append(f'<circle class="hv-bub" cx="{f(hx + 0.1 * k)}" cy="{f(ht - 7.3 * k)}" r="{f(1.6 * k)}"/>')
    lines.append(f'<circle class="hv-bub" cx="{f(bx)}" cy="{f(by)}" r="{f(br)}"/>')
    s = 0.95 * k  # the shield: 8.6 wide and 10.6 tall at k = 1, its centre a little above the bubble's
    sx, sy = bx, by - .3 * k

    def q(x, y):
        return f"{f(sx + x * s)},{f(sy + y * s)}"
    lines.append(f'<path class="hv-shield" d="M{q(0, -5.2)}C{q(1.9, -4.1)} {q(3.4, -3.9)} {q(4.3, -3.9)}L{q(4.3, .2)}'
                 f'C{q(4.3, 2.9)} {q(2.3, 4.6)} {q(0, 5.6)}C{q(-2.3, 4.6)} {q(-4.3, 2.9)} {q(-4.3, .2)}'
                 f'L{q(-4.3, -3.9)}C{q(-3.4, -3.9)} {q(-1.9, -4.1)} {q(0, -5.2)}Z"/>')
    lines.append(f'<rect class="hv-shlock" x="{f(sx - 1.75 * s)}" y="{f(sy - .1 * s)}" width="{f(3.5 * s)}" '
                 f'height="{f(2.7 * s)}" rx="{f(.45 * s)}"/>')
    lines.append(f'<path class="hv-shlock-s" d="M{q(-1.05, 0)}L{q(-1.05, -1.1)}A{f(1.05 * s)},{f(1.05 * s)} 0 0 1 '
                 f'{q(1.05, -1.1)}L{q(1.05, 0)}"/>')
    # the two sparkles are one path, so that their twinkle, a burst out from between them, is
    # one element to restyle
    lines.append(f'<path class="hv-twinkle" d="{sparkle(bx + 10.2 * k, by - 6.5 * k, 3.3 * k)}'
                 f'{sparkle(bx - 11.0 * k, by - 3.5 * k, 2.0 * k)}"/>')
    lines.append("</g>")
    # the ripples: two rings in the halo's shape that leave the phone when the person is clicked
    px, py = next(d for cls, d in out if cls == "ring")
    for n in (1, 2):
        lines.append(f'<ellipse class="hv-ripple hv-rp{n}" cx="{fmt(px)}" cy="{fmt(py)}" rx="{r(4.4)}" ry="{r(2.2)}"/>')
    # the hit area: the figure's box, a little larger; it ends 6 units clear of the board
    lines.append(f'<path class="hv-you-hit" d="M{fmt(max(-28.0, x0 - 1.5))},{fmt(ht - 3)}H{fmt(min(x1 + 1.3, 8.3))}'
                 f'V{fmt(y1 + 5)}H{fmt(max(-28.0, x0 - 1.5))}Z"/>')
    return "\n".join(lines)


def fragment(scale=SCALE, feet=FEET):
    """The person's block as the scene holds it, ending in a newline."""
    return markup(build(P, scale, feet), scale) + "\n"


def main(argv):
    if argv not in ([], ["--write"], ["--check"]):
        print("usage: python3 tools/hero/person.py [--write | --check]", file=sys.stderr)
        return 2
    if not argv:
        sys.stdout.write(fragment())
        return 0
    name = SCENE.as_posix()
    try:
        svg = (ROOT / SCENE).read_bytes().decode("utf-8")
    except OSError as exc:
        print(f"{name}: cannot read it ({exc.strerror})", file=sys.stderr)
        return 1
    found = list(BLOCK.finditer(svg))
    if len(found) != 1:
        print(f'{name}: needs one person block, a "<!-- The person: ... -->" line and <g class="hv-person"> '
              f"... </g>; found {len(found)}", file=sys.stderr)
        return 1
    block = found[0]
    text = fragment()
    if argv == ["--check"]:
        if block.group(0) == text:
            return 0
        print(f"{name}: the person is not what tools/hero/person.py draws; run python3 tools/hero/person.py --write",
              file=sys.stderr)
        return 1
    if block.group(0) == text:
        print(f"{name}: the person is up to date")
        return 0
    (ROOT / SCENE).write_bytes((svg[:block.start()] + text + svg[block.end():]).encode("utf-8"))
    print(f"{name}: wrote the person ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
