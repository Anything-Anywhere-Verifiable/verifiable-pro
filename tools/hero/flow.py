#!/usr/bin/env python3
"""Draw the hero scene's data flow, and the loop that it and the pulse share, for
sitegen/templates/hero-scene.svg: the reader's prompts and data leave the person's phone
and pass through every layer of the stack in order, T1 to T7, touching each layer's main
object, and an answer comes back to the phone; then the evidence pulse rises.

The route is computed from the scene's own geometry. It starts at the centre of the phone's
screen (the ring that tools/hero/person.py draws), runs along the board in front of its row
of capacitors, crosses the dashed TEE boundary around the accelerator package and rests on
the GPU die (T1); it hops up into the glass enclave and onto the inference server (T2), up
out of the glass to the neural network (T3), the generated-text card (T4), the agent (T5),
the tallest benchmark bar (T6) and the top sheet of the standards documents (T7). The
answer runs from there down the left of the stack, outside every plate, to the phone. Each
leg is a smooth curve (Catmull-Rom through the touch points and a few via points that steer
it clear of the scene's objects), so the route never doubles back.

A packet is in the reader's own colour (--hv-data) outside the TEE layers and in the TEE's
indigo, with a soft ring (the scene's --hv-pkring: white on light pages, so that the packet
stays visible on the dark GPU die, and indigo on dark ones), from where it crosses the TEE
boundary on the board until it leaves the top of the glass: T1 and T2 are the layers where a
TEE gives direct evidence. The scene draws the route and the packets in two groups.
g.hv-flow-lo, right before the glass's front faces, holds the route from the phone to the top
of the glass, so that a packet on the board rises from behind the phone and one inside the
glass is seen through it; g.hv-flow-hi,
over the top plate and under the person, holds the rest of the route, from the top of the
glass up through T3 to T7 and the answer's way down, and the answer sinks behind the phone.
Each request packet is therefore two circles, one in each group, which hand over where the
route leaves the glass, at the same place and time. g.hv-flow-hi also holds each plate's
front edges (path.hv-reach), which light in the layer's hue (indigo on T1 and T2) when the
packet reaches the layer.

The loop lasts PERIOD seconds: the request leaves the phone at REQUEST[0], rests DWELL
seconds on each layer's object and rests on T7's at REQUEST[1]; the answer leaves there at
ANSWER[0] and reaches the phone at ANSWER[1], when the phone's halo lights a second time
(the first is as the request leaves) together with the ring at the die; then the pulse
rises along the chain of evidence from PULSE[0] to PULSE[1], lighting each ring as it
passes (each ring's --hv-d, which this script writes), and the scene is still until the
loop starts again. Each leg's time is in proportion to its length, eased at both ends
(the speed ramps up over RAMP of the leg and down over as much). Each packet is a circle
moved by a CSS transform (translate, in the scene's units) along keyframes sampled every
STEP seconds while it moves; the trailing packet runs the same keyframes a little later
(--hv-d). The scene's own stylesheet runs the loop only under data-animated, which
static/hero.js sets once the reader has checked all seven layers; it holds it with
data-motion (paused, suspended), drops it under data-motion="static", hides the flow
while a layer is open and leaves the packets and the edges out under reduced motion.

The blocks this writes: the "<!-- The data flow (1 of 2): ... -->" comment and
g.hv-flow-lo, right before the T2 run that draws the glass's front faces; the
"<!-- The data flow (2 of 2): ... -->" comment and g.hv-flow-hi, right before the
person's block; in the scene's <style>, between "/* the loop (tools/hero/flow.py) */" and
"/* end of the loop */", the animation rules and keyframes of the pulse (hv-rise), the
rings and the phone's halo (hv-ping, hv-yping), the packets (hv-q, hv-r, hv-a) and the
edges (hv-reached); and the --hv-d of each ring's halo (g.hv-ring1 to hv-ring6).

The commands, from the repository root (standard library only):
    python3 tools/hero/flow.py           # print the two blocks, the style block and the timeline
    python3 tools/hero/flow.py --write   # replace them (and the rings' delays) in the scene
    python3 tools/hero/flow.py --check   # exit 0 when the scene holds what this draws, else 1
Run person.py --write first when the person moves: the route starts and ends on their phone.
"""
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from geom import fmt  # noqa: E402

ROOT = HERE.parent.parent
SCENE = Path("sitegen") / "templates" / "hero-scene.svg"
PERIOD = 12.0             # the loop, in seconds
REQUEST = (0.15, 7.0)     # the lead packet leaves the phone; it rests on T7's object
ANSWER = (7.15, 9.8)      # the answer leaves T7's object; it reaches the phone
PULSE = (9.8, 11.85)      # the pulse rises from below the die to past the chain's top
DWELL = 0.22              # a packet rests on each layer's object
RAMP = (0.32, 0.22)       # each leg's speed ramps up over this share of it and down over as much:
                          # a request's leg, then the answer's one long leg
FADE = 0.12               # a packet fades in as it leaves the phone and out as it arrives
SWITCH = 0.025            # the colour change where the route crosses into or out of the TEE
STEP = 0.05               # keyframe spacing while a packet moves
INSTANT = 0.015           # a change that should look instant takes this long (keyframes keep 2 decimals)
PING = (0.21, 0.7)        # a ring's halo peaks this long after its delay and is back by the second
REACH = (0.15, 0.45, 0.95)  # a plate's edges are lit this long after the packet arrives, held, gone
CHAIN = (16.0, 347.0)     # hv-rise moves the pulse's 16-unit dash from below the die to past the top
# the packets: (radius, delay) for the request's two and the answer's one. Each packet is an
# element that the scene restyles when a card opens or closes (the loop holds), so they are few
REQUEST_PACKETS = ((2.2, 0.0), (1.65, 0.1))
ANSWER_PACKETS = ((2.4, 0.0),)
COMMENT_LO = ("<!-- The data flow (1 of 2): your prompts and data leave the phone, cross the TEE boundary on the "
              "board to the GPU die and hop into the glass enclave, indigo inside the TEE layers; drawn under the "
              "glass's front faces (tools/hero/flow.py) -->")
COMMENT_HI = ("<!-- The data flow (2 of 2): from the top of the glass up through every plate to the standards on "
              "top, and the answer back down to the phone; and each plate's front edges, lit as the data reaches "
              "it (tools/hero/flow.py) -->")
BLOCK_LO = re.compile(r'^<!-- The data flow \(1 of 2\):[^\n]*-->\n<g class="hv-flow hv-flow-lo">\n.*?^</g>\n',
                      re.S | re.M)
BLOCK_HI = re.compile(r'^<!-- The data flow \(2 of 2\):[^\n]*-->\n<g class="hv-flow hv-flow-hi">\n.*?^</g>\n',
                      re.S | re.M)
CSS = re.compile(r"/\* the loop \(tools/hero/flow\.py\) \*/\n.*?/\* end of the loop \*/\n", re.S)
RING = r'(<g class="hv-ring hv-ring{n}">\n<ellipse class="hv-nh[^"]*"[^>]*?style="--hv-d:)([^"]*)(")'
NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)")
# each layer's hue for the lit edges: the TEE indigo on T1 and T2, else the layer's own
HUES = {1: "tee", 2: "tee", 3: "c3", 4: "c4", 5: "c5", 6: "c6", 7: "c7"}


# ----- reading the scene -------------------------------------------------------------------
def groups(svg, cls):
    """The text of every <g class="CLS"> in SVG, each up to its own closing tag."""
    out = []
    for m in re.finditer(rf'<g class="{re.escape(cls)}">', svg):
        depth, i = 0, m.start()
        for t in re.finditer(r"<g[\s>]|</g>", svg[i:]):
            depth += 1 if t.group(0) != "</g>" else -1
            if depth == 0:
                out.append(svg[i:i + t.end()])
                break
    return out


def layer(svg, n):
    """Everything that layer N draws, its runs joined."""
    return "".join(groups(svg, f"hv-layer hv-ly{n}"))


def points(d):
    """The corners of path data D made of M, L, H, V and Z steps, absolute or relative."""
    pts, x, y = [], 0.0, 0.0
    for cmd, args in re.findall(r"([MLHVZmlhvz])([^MLHVZmlhvz]*)", d):
        nums = [float(v) for v in NUM.findall(args)]
        step = 1 if cmd in "HhVv" else 2
        for i in range(0, len(nums) - step + 1, step):
            rel = cmd.islower()
            if cmd in "Hh":
                x = x * rel + nums[i]
            elif cmd in "Vv":
                y = y * rel + nums[i]
            elif cmd in "MmLl":
                x, y = (x + nums[i], y + nums[i + 1]) if rel else (nums[i], nums[i + 1])
            pts.append((x, y))
    return pts


def paths(text, cls):
    """The corner lists of every path whose class list starts with CLS in TEXT."""
    found = re.findall(rf'<path class="{re.escape(cls)}(?:"| [^"]*")[^>]*?\sd="([^"]+)"', text)
    return [points(d) for d in found]


def circles(text, cls):
    """The centres of every circle whose class list starts with CLS in TEXT."""
    found = re.findall(rf'<circle class="{re.escape(cls)}(?:"| [^"]*")[^>]*?\scx="([^"]+)" cy="([^"]+)"', text)
    return [(float(x), float(y)) for x, y in found]


def centre(pts):
    return (sum(x for x, y in pts) / len(pts), sum(y for x, y in pts) / len(pts))


def on_face(face, u, v):
    """A point of the parallelogram FACE, given as its corners in the order a plate's top is
    drawn (back, right, front, left): U along its front-left edge from the left corner, V
    from there toward the back."""
    back, right, front, left = face[:4]
    return (left[0] + u * (front[0] - left[0]) + v * (back[0] - left[0]),
            left[1] + u * (front[1] - left[1]) + v * (back[1] - left[1]))


def inside(face, p):
    """Whether P lies inside the convex polygon FACE."""
    sign = 0
    for a, b in zip(face, face[1:] + face[:1]):
        c = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if c:
            if sign and (c > 0) != (sign > 0):
                return False
            sign = c
    return True


def plate(svg, n):
    """Layer N's plate top as (back, right, front, left) corners."""
    return paths(layer(svg, n), "hv-pt")[0][:4]


def on_plate(top, s, t):
    """A point on a plate's top: S along the front-left edge from the left corner (0) to the
    front corner (1), T from that edge toward the back (0 to 1)."""
    back, right, front, left = top
    return (left[0] + s * (front[0] - left[0]) + t * (back[0] - left[0]),
            left[1] + s * (front[1] - left[1]) + t * (back[1] - left[1]))


def scene(svg):
    """What the route is built from: the phone's ring, each layer's touch point, the TEE
    boundary, the glass's top face and each plate's top."""
    m = re.search(r'<ellipse class="[^"]*\bhv-ph-ring\b[^"]*" cx="([^"]+)" cy="([^"]+)"', svg)
    if not m:
        raise ValueError("no ring on the person's phone (hv-ph-ring)")
    phone = (float(m.group(1)), float(m.group(2)))
    ly = {n: layer(svg, n) for n in range(1, 8)}
    if not all(ly.values()):
        raise ValueError("the scene lacks a layer group (g.hv-layer.hv-ly1 to hv-ly7)")
    die = paths(ly[1], "hv-dt")[0]
    server = paths(ly[2], "hv-svt")[0]
    nodes = circles(ly[3], "hv-node")
    mid = centre(nodes)
    sheets = [p for p in paths(ly[7], "hv-pa") if max(x for x, y in p) - min(x for x, y in p) > 50]
    touch = {
        1: on_face(die, .3, .2),                                         # the GPU die, its open front-left part
        2: on_face(server, .5, .5),                                      # the inference server, in the glass
        3: min(nodes, key=lambda c: math.dist(c, mid)),                  # the network's middle node
        4: centre(min(paths(ly[4], "hv-pa"), key=lambda p: min(x for x, y in p))),   # the text card's face
        5: centre(paths(ly[5], "hv-ag")[0]),                             # the agent's top
        6: centre(paths(ly[6], "hv-tk")[0]),                             # the tallest bar's top
        7: centre(min(sheets, key=lambda p: min(y for x, y in p))),      # the top sheet of the standards
    }
    return {"phone": phone, "touch": touch, "tee": paths(ly[1], "hv-tb")[0][:4],
            "glass": paths(ly[2], "hv-gt")[0][:4], "plates": {n: plate(svg, n) for n in range(1, 8)}}


# ----- the route -----------------------------------------------------------------------------
def waypoints(sc):
    """The request's points, phone to T7, as (point, rest): REST marks a layer's touch point,
    where the packet rests; the others steer the curve. Then the answer's, T7 to the phone."""
    t1, t7 = sc["plates"][1], sc["plates"][7]
    touch = sc["touch"]
    left = t7[3][0]                         # the plates' left corners, T2 to T7
    request = [
        (sc["phone"], 0),
        (on_plate(t1, .05, .08), None),     # onto the board by its left corner
        (on_plate(t1, .45, .10), None),     # along it, in front of the capacitors
        (touch[1], 1),                      # across the TEE boundary to the die
        (touch[2], 2), (touch[3], 3), (touch[4], 4), (touch[5], 5), (touch[6], 6), (touch[7], 7),
    ]
    answer = [
        (touch[7], 7),
        (on_plate(t7, .02, .05), None),     # off the standards to the top plate's left corner
        ((left - 13.6, t7[3][1] + 26.5), None),   # down the left of the stack, outside every plate
        ((left - 15.1, (t7[3][1] + t1[3][1]) / 2), None),
        ((left - 17.6, t1[3][1] - 45.5), None),
        (sc["phone"], 0),
    ]
    return request, answer


def spline(pts, tension=0.5):
    """Cubic Bezier segments through PTS (Catmull-Rom, with end tangents along the first and
    last chords): [(p0, c1, c2, p3), ...]."""
    tan = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        k = tension if 0 < i < len(pts) - 1 else tension * 1.0
        tan.append(((b[0] - a[0]) * k, (b[1] - a[1]) * k))
    return [(pts[i], (pts[i][0] + tan[i][0] / 3, pts[i][1] + tan[i][1] / 3),
             (pts[i + 1][0] - tan[i + 1][0] / 3, pts[i + 1][1] - tan[i + 1][1] / 3), pts[i + 1])
            for i in range(len(pts) - 1)]


def bezier(seg, t):
    p0, p1, p2, p3 = seg
    a, b, c, d = (1 - t) ** 3, 3 * t * (1 - t) ** 2, 3 * t * t * (1 - t), t ** 3
    return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])


def split(seg, t):
    """SEG split at T (de Casteljau): (first part, second part)."""
    p0, p1, p2, p3 = seg

    def lerp(a, b):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    a, b, c = lerp(p0, p1), lerp(p1, p2), lerp(p2, p3)
    d, e = lerp(a, b), lerp(b, c)
    f = lerp(d, e)
    return (p0, a, d, f), (f, e, c, p3)


class Route:
    """A chain of Bezier segments, sampled densely, with arc lengths."""
    N = 160

    def __init__(self, segs):
        self.segs = segs
        self.pts, self.acc, self.where = [segs[0][0]], [0.0], [(0, 0.0)]
        for i, seg in enumerate(segs):
            for j in range(1, self.N + 1):
                p = bezier(seg, j / self.N)
                self.acc.append(self.acc[-1] + math.dist(self.pts[-1], p))
                self.pts.append(p)
                self.where.append((i, j / self.N))
        self.length = self.acc[-1]

    def knot(self, i):
        """The arc length at the start of segment I (I = len(segs): the end)."""
        return self.acc[i * self.N]

    def at(self, s):
        """The point at arc length S."""
        s = max(0.0, min(self.length, s))
        lo, hi = 0, len(self.acc) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.acc[mid] < s:
                lo = mid
            else:
                hi = mid
        seg = self.acc[hi] - self.acc[lo] or 1.0
        k = (s - self.acc[lo]) / seg
        a, b = self.pts[lo], self.pts[hi]
        return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)

    def param(self, s):
        """(segment index, Bezier parameter) at arc length S."""
        s = max(0.0, min(self.length, s))
        i = next(j for j in range(1, len(self.acc)) if self.acc[j] >= s)
        (si, ta), (sj, tb) = self.where[i - 1], self.where[i]
        if sj != si:
            ta = 0.0
        k = (s - self.acc[i - 1]) / ((self.acc[i] - self.acc[i - 1]) or 1.0)
        return sj, ta + (tb - ta) * k

    def crossing(self, face, s0, entering):
        """The first arc length from S0 on where the route enters FACE (ENTERING) or leaves it."""
        start = next(j for j in range(len(self.acc)) if self.acc[j] >= s0)
        for j in range(start, len(self.pts)):
            if inside(face, self.pts[j]) == entering:
                return self.acc[j]
        raise ValueError("the route never crosses that face")

    def d(self, s0, s1):
        """Path data for the route from arc length S0 to S1."""
        i0, t0 = self.param(s0)
        i1, t1 = self.param(s1)
        segs = []
        for i in range(i0, i1 + 1):
            seg = self.segs[i]
            a, b = (t0 if i == i0 else 0.0), (t1 if i == i1 else 1.0)
            if b < 1.0:
                seg = split(seg, b)[0]
                a = a / b if b else 0.0
            if a > 0.0:
                seg = split(seg, a)[1]
            if math.dist(seg[0], seg[3]) > 1e-6:
                segs.append(seg)
        out = f"M{fmt(segs[0][0][0])},{fmt(segs[0][0][1])}"
        for _, c1, c2, p in segs:
            out += f"C{fmt(c1[0])},{fmt(c1[1])} {fmt(c2[0])},{fmt(c2[1])} {fmt(p[0])},{fmt(p[1])}"
        return out


def ease(x, ramp):
    """The share of a leg covered at share X of its time: the speed ramps up evenly over RAMP,
    holds, and ramps down over RAMP."""
    vp = 1 / (1 - ramp)
    if x <= ramp:
        return vp * x * x / (2 * ramp)
    if x >= 1 - ramp:
        return 1 - vp * (1 - x) ** 2 / (2 * ramp)
    return vp * (ramp / 2 + x - ramp)


def schedule(route, rests, t0, t1, ramp):
    """The moves of a packet along ROUTE from T0, resting DWELL at each arc length in RESTS
    (the first is the start), and arriving at the last at T1: [(start time, end time, from
    arc length, to arc length, ramp)], one per leg, in time order. A leg's time is in
    proportion to its length."""
    legs = list(zip(rests, rests[1:]))
    moving = t1 - t0 - DWELL * (len(legs) - 1)
    total = sum(b - a for a, b in legs)
    moves, t = [], t0
    for a, b in legs:
        dt = moving * (b - a) / total
        moves.append((t, t + dt, a, b, ramp))
        t += dt + DWELL
    return moves


def where(route, moves, t):
    """The arc length of a packet at time T, on its MOVES."""
    for start, end, a, b, ramp in moves:
        if t < start:
            return a
        if t <= end:
            return a + (b - a) * ease((t - start) / (end - start), ramp)
    return moves[-1][3]


def build(svg):
    """The flow: both routes, the request's and the answer's moves, the arc lengths where the
    request turns indigo and leaves the glass, and the time it reaches each layer."""
    sc = scene(svg)
    request, answer = waypoints(sc)
    req = Route(spline([p for p, _ in request]))
    ans = Route(spline([p for p, _ in answer]))
    rests = [req.knot(i) for i, (_, n) in enumerate(request) if n is not None]
    moves = schedule(req, rests, *REQUEST, RAMP[0])
    tee = req.crossing(sc["tee"], 0.0, True)
    exit_ = req.crossing(sc["glass"], rests[2], False)
    arrive = {n: moves[n - 1][1] for n in range(1, 8)}
    back = schedule(ans, [0.0, ans.length], *ANSWER, RAMP[1])
    return {"scene": sc, "req": req, "ans": ans, "moves": moves, "back": back, "tee": tee, "exit": exit_,
            "arrive": arrive}


# ----- writing -----------------------------------------------------------------------------
def pct(t):
    return fmt(t / PERIOD * 100, 2) + "%"


def xy(p):
    return f"translate({fmt(p[0])}px,{fmt(p[1])}px)"


def frames(name, positions, shown, colours):
    """@keyframes NAME for a packet: POSITIONS [(time, point)] while it moves, SHOWN [(time,
    opacity)] and COLOURS [(time, fill, stroke opacity)]; the first and last frames hold."""
    out = {}

    def put(t, **props):
        out.setdefault(pct(t), {}).update(props)
    for t, p in positions:
        put(t, transform=xy(p))
    for t, o in shown:
        put(t, opacity=o)
    for t, fill, so in colours:
        put(t, fill=fill, **{"stroke-opacity": so})
    order = sorted(out, key=lambda k: float(k[:-1]))
    body = "".join(f"{k}{{{';'.join(f'{p}:{v}' for p, v in out[k].items())}}}" for k in order)
    return f"@keyframes {name}{{{body}}}"


def samples(route, moves, t_from, t_to):
    """The packet's positions on ROUTE from T_FROM to T_TO: at each move's ends and every STEP
    while it moves."""
    out = [(t_from, route.at(where(route, moves, t_from)))]
    for start, end, a, b, ramp in moves:
        if end <= t_from or start >= t_to:
            continue
        n = max(2, round((end - start) / STEP))
        for i in range(n + 1):
            t = start + (end - start) * i / n
            if t_from < t < t_to:
                out.append((t, route.at(where(route, moves, t))))
    out.append((t_to, route.at(where(route, moves, t_to))))
    return out


def fragment(svg):
    """(the low block, the high block, the style block, the rings' delays, a timeline), the
    blocks each ending in a newline."""
    f = build(svg)
    req, ans, moves, back = f["req"], f["ans"], f["moves"], f["back"]
    data, tee = "var(--hv-data)", "var(--hv-tee2)"

    def time_at(s):
        """When the lead packet passes arc length S of the request's route."""
        lo, hi = REQUEST
        for _ in range(60):
            mid = (lo + hi) / 2
            if where(req, moves, mid) < s:
                lo = mid
            else:
                hi = mid
        return hi
    t_tee, t_exit = time_at(f["tee"]), time_at(f["exit"])
    t_end = REQUEST[1] + DWELL   # the request hands over to the answer on T7's object
    start = req.at(0.0)
    # the request, low: from the phone to the top of the glass, indigo from the TEE boundary on
    q_pos = samples(req, moves, REQUEST[0], t_exit)
    q = frames("hv-q", [(0.0, start)] + q_pos + [(PERIOD, req.at(f["exit"]))],
               [(0.0, "0"), (REQUEST[0], "0"), (REQUEST[0] + FADE, "1"), (t_exit, "1"), (t_exit + INSTANT, "0"),
                (PERIOD, "0")],
               [(0.0, data, "0"), (t_tee - SWITCH, data, "0"), (t_tee + SWITCH, tee, ".5"), (PERIOD, tee, ".5")])
    # the request, high: from the top of the glass to T7's object, back in the reader's colour
    r_pos = samples(req, moves, t_exit, t_end)
    r = frames("hv-r", [(0.0, req.at(f["exit"]))] + r_pos + [(PERIOD, req.at(req.length))],
               [(0.0, "0"), (t_exit - INSTANT, "0"), (t_exit, "1"), (t_end - FADE, "1"), (t_end, "0"), (PERIOD, "0")],
               [(0.0, tee, ".5"), (t_exit, tee, ".5"), (t_exit + 2 * SWITCH, data, "0"), (PERIOD, data, "0")])
    # the answer: from T7's object down the left of the stack to the phone
    a_pos = samples(ans, back, ANSWER[0], ANSWER[1])
    a = frames("hv-a", [(0.0, ans.at(0.0))] + a_pos + [(PERIOD, ans.at(ans.length))],
               [(0.0, "0"), (ANSWER[0] - FADE, "0"), (ANSWER[0], "1"), (ANSWER[1] - FADE, "1"), (ANSWER[1], "0"),
                (PERIOD, "0")],
               [(0.0, data, "0"), (PERIOD, data, "0")])
    # the pulse, the rings' and the phone's halos, and the lit edges
    lead, top = CHAIN
    rise = (f"@keyframes hv-rise{{0%,{pct(PULSE[0])}{{stroke-dashoffset:calc(var(--hv-s) + {fmt(lead)}px)}}"
            f"{pct(PULSE[1])},100%{{stroke-dashoffset:calc(var(--hv-s) - {fmt(top)}px)}}}}")
    peak, calm = PING
    ping = (f"@keyframes hv-ping{{0%,100%{{opacity:var(--hv-nh-o)}}{pct(peak)}{{opacity:calc(var(--hv-nh-o) * 2.6)}}"
            f"{pct(calm)}{{opacity:var(--hv-nh-o)}}}}")
    home = ANSWER[1] - .05
    yping = (f"@keyframes hv-yping{{0%,{pct(home)},100%{{opacity:var(--hv-nh-o)}}{pct(peak)},{pct(home + peak)}"
             f"{{opacity:calc(var(--hv-nh-o) * 2.6)}}{pct(calm)},{pct(home + calm)}{{opacity:var(--hv-nh-o)}}}}")
    fade_in, hold, gone = REACH
    reached = (f"@keyframes hv-reached{{0%,100%{{opacity:0}}{pct(fade_in)},{pct(hold)}{{opacity:1}}"
               f"{pct(gone)}{{opacity:0}}}}")
    speed = (lead + top) / (PULSE[1] - PULSE[0])
    rings = {1: PULSE[0]}
    for n, s in zip(range(2, 7), (66.5, 105.5, 161.5, 217.5, 273.5)):
        rings[n] = PULSE[0] + (s + lead / 2) / speed
    period = fmt(PERIOD, 2) + "s"
    css = ["/* the loop (tools/hero/flow.py) */",
           f"[data-animated] .hv-pulse{{opacity:1;animation:hv-rise {period} linear infinite}}",
           f"[data-animated] .hv-nh{{animation:hv-ping {period} linear infinite;animation-delay:var(--hv-d,0s)}}",
           f"[data-animated] .hv-person .hv-nh{{animation:hv-yping {period} linear infinite;"
           "animation-delay:var(--hv-d,0s)}",
           f"[data-animated] .hv-pkq{{animation:hv-q {period} linear infinite;animation-delay:var(--hv-d,0s)}}",
           f"[data-animated] .hv-pkr{{animation:hv-r {period} linear infinite;animation-delay:var(--hv-d,0s)}}",
           f"[data-animated] .hv-pka{{animation:hv-a {period} linear infinite;animation-delay:var(--hv-d,0s)}}",
           f"[data-animated] .hv-reach{{animation:hv-reached {period} linear infinite;"
           "animation-delay:var(--hv-d,0s)}",
           rise, ping, yping, reached, q, r, a, "/* end of the loop */"]
    # the blocks
    lo = [COMMENT_LO, '<g class="hv-flow hv-flow-lo">', f'<path class="hv-route" d="{req.d(0.0, f["exit"])}"/>']
    for radius, delay in REQUEST_PACKETS:
        style = f' style="--hv-d:{fmt(delay, 2)}s"' if delay else ""
        lo.append(f'<circle class="hv-pk hv-pkq" r="{fmt(radius, 2)}"{style}/>')
    lo.append("</g>")
    hi = [COMMENT_HI, '<g class="hv-flow hv-flow-hi">']
    for n in range(1, 8):
        back_, right, front, left = f["scene"]["plates"][n]
        d = f"M{fmt(left[0])},{fmt(left[1])}L{fmt(front[0])},{fmt(front[1])}L{fmt(right[0])},{fmt(right[1])}"
        hi.append(f'<path class="hv-reach hv-reach{n}" d="{d}" style="--hv-d:{fmt(f["arrive"][n] - .05, 2)}s"/>')
    hi.append(f'<path class="hv-route" d="{req.d(f["exit"], req.length)}{ans.d(0.0, ans.length)}"/>')
    for radius, delay in REQUEST_PACKETS:
        style = f' style="--hv-d:{fmt(delay, 2)}s"' if delay else ""
        hi.append(f'<circle class="hv-pk hv-pkr" r="{fmt(radius, 2)}"{style}/>')
    for radius, delay in ANSWER_PACKETS:
        style = f' style="--hv-d:{fmt(delay, 2)}s"' if delay else ""
        hi.append(f'<circle class="hv-pk hv-pka" r="{fmt(radius, 2)}"{style}/>')
    hi.append("</g>")
    timeline = [f"loop {fmt(PERIOD, 2)}s; request {fmt(req.length)} units, answer {fmt(ans.length)} units",
                f"TEE boundary at {fmt(t_tee, 2)}s, out of the glass at {fmt(t_exit, 2)}s"]
    for (s0, s1, a0, b0, _), n in zip(moves, range(1, 8)):
        timeline.append(f"  T{n}: {fmt(s0, 2)}s to {fmt(s1, 2)}s, {fmt(b0 - a0)} units, "
                        f"{fmt((b0 - a0) / (s1 - s0))} units/s on average")
    timeline.append(f"  answer: {fmt(back[0][0], 2)}s to {fmt(back[0][1], 2)}s, "
                    f"{fmt(ans.length / (back[0][1] - back[0][0]))} units/s on average")
    timeline.append(f"  pulse: {fmt(PULSE[0], 2)}s to {fmt(PULSE[1], 2)}s; rings at "
                    + ", ".join(f"{fmt(t, 2)}s" for t in rings.values()))
    return ("\n".join(lo) + "\n", "\n".join(hi) + "\n", "\n".join(css) + "\n",
            {n: fmt(t, 2) + "s" for n, t in rings.items()}, "\n".join(timeline) + "\n")


def apply(svg, lo, hi, css, rings):
    """SVG with the blocks and the rings' delays replaced, or None when a block is missing."""
    found = [list(BLOCK_LO.finditer(svg)), list(BLOCK_HI.finditer(svg)), list(CSS.finditer(svg))]
    if [len(x) for x in found] != [1, 1, 1]:
        return None
    new = svg
    for pattern, text in ((BLOCK_LO, lo), (BLOCK_HI, hi), (CSS, css)):
        m = pattern.search(new)
        new = new[:m.start()] + text + new[m.end():]
    for n, delay in rings.items():
        new, k = re.subn(RING.format(n=n), lambda m: m.group(1) + delay + m.group(3), new)
        if k != 1:
            return None
    return new


def main(argv):
    if argv not in ([], ["--write"], ["--check"]):
        print("usage: python3 tools/hero/flow.py [--write | --check]", file=sys.stderr)
        return 2
    name = SCENE.as_posix()
    try:
        svg = (ROOT / SCENE).read_bytes().decode("utf-8")
    except OSError as exc:
        print(f"{name}: cannot read it ({exc.strerror})", file=sys.stderr)
        return 1
    lo, hi, css, rings, timeline = fragment(svg)
    if not argv:
        sys.stdout.write(lo + hi + css + timeline)
        return 0
    new = apply(svg, lo, hi, css, rings)
    if new is None:
        print(f'{name}: needs one "<!-- The data flow (1 of 2): ... -->" block with g.hv-flow-lo, one "<!-- The data '
              f'flow (2 of 2): ... -->" block with g.hv-flow-hi, one "/* the loop (tools/hero/flow.py) */ ... '
              f'/* end of the loop */" in its style, and a halo with --hv-d in each of g.hv-ring1 to hv-ring6',
              file=sys.stderr)
        return 1
    if argv == ["--check"]:
        if new == svg:
            return 0
        print(f"{name}: the data flow is not what tools/hero/flow.py draws; run python3 tools/hero/flow.py --write",
              file=sys.stderr)
        return 1
    if new == svg:
        print(f"{name}: the data flow is up to date")
        return 0
    (ROOT / SCENE).write_bytes(new.encode("utf-8"))
    print(f"{name}: wrote the data flow")
    sys.stdout.write(timeline)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
