"""The prop library, part two: media, institutions, agents and models, proofs,
location and supply chain, people and furniture. Conventions as in props.py."""
import math

from . import palette as P
from .iso import (Baked, Glass, Glow, Plane, Sphere, arc2, box_els, circle2, ellipse2, front_plane, line, mix, poly,
                  poly2, rect, right_plane, rrect, top_plane)
from .kit import choice, flag, integer, landscape, num, nums, prop, tline

LAYER_TINTS = ("models", "outputs", "agents", "evaluations", "institutions")


# ======================================================================= media
@prop("photo", "Media", "A picture standing on its edge: a landscape, a portrait, a video frame or a sound clip. "
      "mark overlays a faint watermark pattern; tag hangs a provenance tag or a seal on its corner.",
      tints=("neutral", "outputs", "tee", "data", "seal", "models", "agents", "evaluations", "institutions"), tint="neutral",
      w=num(2.2, 0.8, 5, "width"), h=num(1.6, 0.6, 4, "height"),
      content=choice("landscape", ("landscape", "portrait", "video", "audio", "text"), "what the picture shows"),
      mark=choice("none", ("none", "wave", "dots"), "a faint watermark pattern over the picture"),
      tag=choice("none", ("none", "tag", "seal", "pin"), "tag: a label tag; seal: a small cinnabar seal (indigo with tint tee); "
                 "pin: a round badge"))
def p_photo(b):
    p = b.p
    w, h = p["w"], p["h"]
    part = b.box(-w / 2, -0.05, 0, w / 2, 0.05, h, P.M["paper"])
    pl = front_plane(-w / 2, w / 2, 0, -0.05)
    m = 0.1
    u0, v0, u1, v1 = m, m, w - m, h - m
    neutral = b.tint == "neutral"
    sky = "#dfe5ec" if neutral else b.t.wash
    hill = P.HILL if neutral else b.t.accent2
    hill2 = P.HILL2 if neutral else b.t.accent
    c = p["content"]
    if c in ("landscape", "video"):
        part.els += landscape(pl, u0, v0, u1, v1, sky, hill, hill2)
    elif c == "portrait":
        part.els.append(pl.shape(rect(u0, v0, u1, v1), fill=sky, body=False))
        cu = (u0 + u1) / 2
        hh = v1 - v0
        part.els.append(pl.shape([("M", cu - hh * 0.42, v0)] + arc2(cu, v0, hh * 0.42, 180, 0, move=False, rv=hh * 0.36)[1:] + [("Z",)],
                                 fill=hill2, body=False))
        part.els.append(pl.shape(ellipse2(cu, v0 + hh * 0.56, hh * 0.17, hh * 0.2), fill=hill, body=False))
    elif c == "audio":
        part.els.append(pl.shape(rect(u0, v0, u1, v1), fill=sky, body=False))
        n = 17
        for i in range(n):
            f = 0.12 + 0.88 * abs(math.sin(i * 1.3 + 0.4) * math.cos(i * 0.37))
            uu = u0 + (u1 - u0) * (0.08 + 0.84 * i / (n - 1))
            vm = (v0 + v1) / 2
            part.els.append(pl.line([(uu, vm - f * (v1 - v0) * 0.34), (uu, vm + f * (v1 - v0) * 0.34)], stroke=hill2,
                                    swu=(u1 - u0) * 0.022, cap="round"))
    else:
        part.els.append(pl.shape(rect(u0, v0, u1, v1), fill="#f7f8fa", body=False))
        for i, f in enumerate((0.7, 0.55, 0.66, 0.4)):
            vv = v1 - (v1 - v0) * (0.2 + i * 0.2)
            part.els.append(tline(pl, u0 + 0.12, vv, u0 + 0.12 + (u1 - u0 - 0.24) * f, P.SOFT2, w=0.07))
    if c == "video":
        cu, cv = (u0 + u1) / 2, (v0 + v1) / 2 + 0.05
        rr = min(u1 - u0, v1 - v0) * 0.24
        part.els.append(pl.shape(circle2(cu, cv, rr), fill="#ffffff", body=False, op=0.92))
        part.els.append(pl.shape(poly2([(cu - rr * 0.34, cv - rr * 0.6), (cu + rr * 0.68, cv), (cu - rr * 0.34, cv + rr * 0.6)]),
                                 fill=P.INK2, body=False))
        part.els.append(pl.line([(u0 + 0.1, v0 + 0.1), (u1 - 0.1, v0 + 0.1)], stroke="#ffffff", swu=0.05, sop=0.7))
        part.els.append(pl.line([(u0 + 0.1, v0 + 0.1), (u0 + (u1 - u0) * 0.45, v0 + 0.1)], stroke=P.MUTE if neutral else b.t.accent,
                                swu=0.05))
    if p["mark"] == "wave":
        for j in range(5):
            vv = v0 + (v1 - v0) * (0.14 + j * 0.18)
            pts = [(u0 + (u1 - u0) * i / 24.0, vv + math.sin(i * 0.9 + j) * 0.035) for i in range(25)]
            part.els.append(pl.line(pts, stroke="#ffffff", swu=0.025, sop=0.55))
    elif p["mark"] == "dots":
        for i in range(9):
            for j in range(6):
                if (i + j) % 2 == 0:
                    part.els.append(pl.shape(circle2(u0 + (u1 - u0) * (i + 0.5) / 9, v0 + (v1 - v0) * (j + 0.5) / 6, 0.025),
                                             fill="#ffffff", body=False, op=0.6))
    tg = p["tag"]
    if tg != "none":
        tp = front_plane(-w / 2, w / 2, 0, -0.07)
        tu, tv = w - 0.05, h - 0.05
        acc = b.t.accent if not neutral else P.INK2
        if tg == "tag":
            ang = math.radians(-35)
            ca, sa = math.cos(ang), math.sin(ang)

            def rot(x, y):
                return (tu + x * ca - y * sa, tv + x * sa + y * ca)
            shape = [rot(0, 0), rot(0.18, 0.16), rot(0.62, 0.16), rot(0.62, -0.16), rot(0.18, -0.16)]
            tagel = b.extrude_els(tp, [poly2(list(reversed(shape)) if _cw(shape) else shape)], 0.03, acc, side=mix(acc, "#000000", 0.25))
            hx, hy = rot(0.16, 0)
            tagel.append(tp.shape(circle2(hx, hy, 0.045), fill="#ffffff", body=False))
            sx, sy = rot(0.42, 0)
            tagel.append(tp.line([(sx - 0.1 * ca, sy - 0.1 * sa), (sx + 0.12 * ca, sy + 0.12 * sa)], stroke="#ffffff", swu=0.035, sop=0.9))
            part.els += tagel[1:]
        elif tg == "seal":
            sm = P.M["tee"] if b.tint == "tee" else P.M["seal"]
            sl = b.extrude_els(tp, [circle2(tu - 0.18, tv - 0.18, 0.24)], 0.03, sm.left, side=sm.right)
            sl.append(tp.path(circle2(tu - 0.18, tv - 0.18, 0.15), stroke=sm.top if b.tint == "tee" else P.SEAL2, swu=0.03))
            part.els += sl[1:]
        else:
            part.els.append(tp.shape(circle2(tu - 0.2, tv - 0.2, 0.2), fill="#ffffff", body=False))
            part.els.append(tp.path(circle2(tu - 0.2, tv - 0.2, 0.2), stroke=acc, swu=0.05))
            part.els.append(tp.shape(circle2(tu - 0.2, tv - 0.2, 0.08), fill=acc, body=False))
    b.anchors["picture"] = (0, -0.06, h / 2)


def _cw(pts):
    a = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        a += p[0] * q[1] - q[0] * p[1]
    return a < 0


@prop("camera", "Media", "A camera with its lens toward the front: capture, a photo's origin.",
      tints=("neutral", "tee", "data", "seal", "outputs"), tint="neutral", size=num(1.3, 0.5, 3, "body width"))
def p_camera(b):
    p = b.p
    k = p["size"] / 1.3
    w, d, h = 1.3 * k, 0.7 * k, 0.85 * k
    body = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, h, P.M["ink"], lip="#5d646d")
    fp = front_plane(-w / 2, w / 2, 0, -d / 2)
    body.els.append(fp.shape(rect(0, h * 0.2, w, h * 0.32), fill="#4a5058", body=False))
    b.box(-w / 2 + 0.12 * k, -0.15 * k, h, -w / 2 + 0.42 * k, 0.15 * k, h + 0.12 * k, P.M["ink"], lip=None)
    b.box(w / 2 - 0.42 * k, -0.18 * k, h, w / 2 - 0.12 * k, 0.12 * k, h + 0.22 * k, P.M["ink"], lip="#5d646d")
    lens = b.extrude_els(Plane((0, -d / 2 - 0.3 * k, 0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), [circle2(0.05 * k, h * 0.5, 0.34 * k)],
                         0.3 * k, "#2c3036", side="#1e2226")
    lens.append(Plane((0, -d / 2 - 0.3 * k, 0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)).shape(circle2(0.05 * k, h * 0.5, 0.24 * k),
                                                                                       fill="#4f5a7c" if b.tint != "tee" else P.TEE2, body=False))
    lens.append(Plane((0, -d / 2 - 0.3 * k, 0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)).shape(circle2(-0.02 * k, h * 0.56, 0.07 * k),
                                                                                       fill="#ffffff", body=False, op=0.6))
    b.add(lens)
    b.anchors["lens"] = (0.05 * k, -d / 2 - 0.3 * k, h * 0.5)


# ======================================================================= institutions
@prop("building", "Institutions", "A public building with columns and a pediment: a government, a regulator, a court, "
      "a standards body.", tints=("neutral",) + LAYER_TINTS + ("tee", "seal"), tint="neutral",
      w=num(3.6, 2, 7, "width"), d=num(2.4, 1.4, 5, "depth"), columns=integer(5, 3, 9, "columns"),
      emblem=flag(True, "a round emblem in the pediment (the tint's accent)"))
def p_building(b):
    p = b.p
    w, d, n = p["w"], p["d"], p["columns"]
    stone = P.Mat("#f7f8f9", "#e3e6ea", "#cbd0d7", None, "stone")
    b.box(-w / 2 - 0.2, -d / 2 - 0.2, 0, w / 2 + 0.2, d / 2 + 0.2, 0.12, P.M["soft"])
    b.box(-w / 2 - 0.1, -d / 2 - 0.1, 0.12, w / 2 + 0.1, d / 2 + 0.1, 0.24, stone)
    b.box(-w / 2, -d / 2, 0.24, w / 2, d / 2, 0.36, stone)
    zc0, zc1 = 0.36, 2.0
    cella = b.box(-w / 2 + 0.3, -d / 2 + 0.75, zc0, w / 2 - 0.3, d / 2 - 0.15, zc1, P.Mat("#eef0f3", "#dde1e6", "#c6ccd3", None, "cella"),
                  lip=None)
    fp = front_plane(-w / 2 + 0.3, w / 2 - 0.3, zc0, -d / 2 + 0.75)
    cw = w - 0.6
    cella.els.append(fp.shape(rect(cw / 2 - 0.32, 0, cw / 2 + 0.32, 1.05), fill="#c3c9d0", body=False))
    yc = -d / 2 + 0.36
    step = (w - 0.5) / (n - 1)
    for i in range(n):
        x = -w / 2 + 0.25 + i * step
        b.cyl(x, yc, zc0, zc1, 0.15, P.Mat("#ffffff", "#eceef1", "#cfd4da", None, "col"))
    b.box(-w / 2 - 0.05, -d / 2 + 0.1, zc1, w / 2 + 0.05, d / 2, zc1 + 0.28, stone)
    # pediment: a triangular prism with the gable to the front
    z0, z1 = zc1 + 0.28, zc1 + 0.28 + 0.7
    y0, y1 = -d / 2 + 0.1, d / 2
    xl, xr = -w / 2 - 0.05, w / 2 + 0.05
    els = [poly([(xl, y0, z0), (xr, y0, z0), (0, y0, z1)], n=(0, -1, 0), fill=stone, seam=True),
           poly([(xr, y1, z0), (xl, y1, z0), (0, y1, z1)], n=(0, 1, 0), fill=stone, seam=True),
           poly([(0, y0, z1), (xr, y0, z0), (xr, y1, z0), (0, y1, z1)], fill=P.Mat("#e9ecef", "#e9ecef", "#c9ced5", None, "roofr"), seam=True),
           poly([(xl, y0, z0), (0, y0, z1), (0, y1, z1), (xl, y1, z0)], fill=P.Mat("#f4f5f7", "#f4f5f7", "#d5dae0", None, "roofl"), seam=True)]
    els.append(line([(xl, y0, z0), (0, y0, z1), (xr, y0, z0)], stroke="#ffffff", swu=0.03, join="round"))
    gp = front_plane(xl, xr, z0, y0 - 0.001)
    els.append(gp.path([("M", 0.35, 0.08), ("L", (xr - xl) / 2, 0.62), ("L", xr - xl - 0.35, 0.08), ("Z",)], stroke="#d5dae0", swu=0.03,
                       join="round"))
    if p["emblem"]:
        acc = b.t.accent if b.tint != "neutral" else P.INK2
        els.append(gp.shape(circle2((xr - xl) / 2, 0.27, 0.14), fill=acc, body=False))
    b.add(els)
    b.anchors["door"] = (0, -d / 2 + 0.74, 0.8)
    b.anchors["top"] = (0, 0, z1)


@prop("gavel", "Institutions", "A judge's gavel resting on its square sound block: a ruling, enforcement.",
      tints=("neutral", "institutions"), tint="institutions", size=num(1, 0.5, 3, "scale factor"))
def p_gavel(b):
    k = b.p["size"]
    wood = P.M["institutions"] if b.tint == "institutions" else P.M["ink"]
    cap = P.Mat(mix(wood.top, "#ffffff", 0.45), mix(wood.left, "#ffffff", 0.4), mix(wood.right, "#ffffff", 0.3), None, "gcap")
    b.box(-0.55 * k, -0.55 * k, 0, 0.55 * k, 0.55 * k, 0.18 * k, wood.darker(0.18), lip=mix(wood.top, "#ffffff", 0.3))
    # the head: a cylinder lying across the block (along y), lighter at both ends
    R, L = 0.19 * k, 0.86 * k
    xh, zc = -0.12 * k, 0.18 * k + 0.19 * k
    cl = 0.13 * L
    for y0, y1, m in ((-L / 2, -L / 2 + cl, cap), (-L / 2 + cl, L / 2 - cl, wood), (L / 2 - cl, L / 2, cap)):
        pl = Plane((0.0, y0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        b.add(b.extrude_els(pl, [circle2(xh, zc, R)], y1 - y0, m.left, side=m.right), convex=True)
    # the handle: a thin bar from the head toward the front right, its end resting lower
    b.obox((xh + R * 0.6, -0.035 * k, zc - 0.035 * k), (1.25 * k, 0, -0.16 * k), (0, 0.07 * k, 0), (0, 0, 0.07 * k), wood)
    b.footprint = (-0.6 * k, -0.6 * k, 1.2 * k, 0.6 * k)


# ======================================================================= agents and models
@prop("agent", "Agents", "An AI agent: a glass cube with a core (a sphere, a cube or a face). Tint agents: "
      "teal as on the hero; tee: indigo, an agent in an enclave; neutral: plain glass.", tints=("agents", "tee", "data", "neutral", "models"),
      tint="agents", size=num(1.2, 0.5, 3, "cube edge"), core=choice("sphere", ("sphere", "cube", "face"), "the core"),
      glow=flag(False, "a soft glow around the core (a picture keeps one glow)"))
def p_agent(b):
    p = b.p
    s = p["size"]
    hs = s / 2
    neutral = b.tint == "neutral"
    acc = b.t.accent if not neutral else "#6d7680"
    core = b.t.solid if not neutral else P.Mat("#c3c9d0", "#9aa2ab", "#6d7680", None, "agentcore")
    eye = "#ffffff" if not neutral else P.INK
    glow = b.t.glow
    box = (-hs, -hs, 0, hs, hs, s)
    els = [Glass(box, "back", acc, acc, fop=0.06, floor=b.t.wash)]
    zc = s * 0.5
    if p["core"] == "sphere":
        if p["glow"]:
            els.append(Glow((0, 0, zc), s * 0.36, glow, 0.38))
        els.append(Sphere((0, 0, zc), s * 0.2, core.left, hi=core.top))
    elif p["core"] == "cube":
        if p["glow"]:
            els.append(Glow((0, 0, zc), s * 0.5, glow, 0.5))
        c = s * 0.18
        els += box_els(-c, -c, zc - c, c, c, zc + c, core, lip="#ffffff")
    else:
        c = s * 0.3
        els += box_els(-c, -c, zc - c, c, c, zc + c, core, lip="#ffffff")
        fp = front_plane(-c, c, zc - c, -c)
        els.append(fp.shape(circle2(c * 0.62, c * 1.1, c * 0.15), fill=eye, body=False))
        els.append(fp.shape(circle2(c * 1.38, c * 1.1, c * 0.15), fill=eye, body=False))
        els.append(line([(0, 0, zc + c), (0, 0, zc + c + s * 0.12)], stroke=core.right, swu=0.03))
        els.append(Sphere((0, 0, zc + c + s * 0.14), s * 0.04, core.right))
    els.append(Glass(box, "front", acc, acc, fop=0.06))
    b.add(els)
    b.anchors["core"] = (0, 0, zc)


@prop("robot_arm", "Agents", "An industrial robot arm on a round base: an agent acting in the world, automation.",
      tints=("neutral", "agents", "data", "tee"), tint="neutral", reach=num(1, 0.6, 2, "scale factor"))
def p_robot_arm(b):
    k = b.p["reach"]
    metal = P.M["metal"]
    joint = b.t.solid if b.tint != "neutral" else P.M["data"]
    b.cyl(0, 0, 0, 0.18 * k, 0.6 * k, P.M["steel"])
    b.cyl(0, 0, 0.18 * k, 0.48 * k, 0.36 * k, metal)
    # lower arm: from the base up and back, upper arm: forward and down
    a0 = (0.0, 0.0, 0.5 * k)
    a1 = (0.0, 0.55 * k, 1.75 * k)
    a2 = (0.0, -0.75 * k, 2.05 * k)
    lower = _beam(a0, a1, 0.26 * k, 0.22 * k, metal)
    upper = _beam(a1, a2, 0.22 * k, 0.18 * k, metal)
    b.add(lower)
    b.add(upper)
    b.sphere(a1, 0.2 * k, joint.left, hi=joint.top)
    b.sphere((0.0, 0.0, 0.52 * k), 0.22 * k, joint.left, hi=joint.top)
    # gripper
    g = a2
    b.cbox(g[0], g[1] - 0.05 * k, g[2] - 0.34 * k, 0.34 * k, 0.16 * k, 0.24 * k, P.M["steel"], lip=None)
    for sx in (-1, 1):
        b.cbox(g[0] + sx * 0.12 * k, g[1] - 0.05 * k, g[2] - 0.62 * k, 0.07 * k, 0.1 * k, 0.28 * k, P.M["ink"], lip=None)
    b.footprint = (-0.6 * k, -0.9 * k, 0.6 * k, 0.8 * k)
    b.anchors["gripper"] = (g[0], g[1], g[2] - 0.6 * k)


def _beam(a, c, w, t, mat):
    """A straight bar of width W (x) and thickness T between two points in the y-z plane."""
    dy, dz = c[1] - a[1], c[2] - a[2]
    L = math.sqrt(dy * dy + dz * dz)
    ny, nz = -dz / L * t / 2, dy / L * t / 2
    o = (a[0] - w / 2, a[1] - ny, a[2] - nz)
    ex = (w, 0.0, 0.0)
    ey = (0.0, dy, dz)
    ez = (0.0, 2 * ny, 2 * nz)
    # keep the frame right-handed
    cx = (ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0])
    if cx[0] * ez[0] + cx[1] * ez[1] + cx[2] * ez[2] < 0:
        o = (o[0], o[1] + ez[1], o[2] + ez[2])
        ez = (0.0, -ez[1], -ez[2])
    from .kit import B
    return B("neutral", {}).obox_els(o, ex, ey, ez, mat)


@prop("tool", "Agents", "A tool an agent calls, as a standing tile with an icon (as on the hero's agent layer).",
      tints=("agents", "neutral", "tee", "data") + LAYER_TINTS, tint="agents",
      icon=choice("gear", ("gear", "terminal", "globe", "wrench", "search", "doc", "database", "mail"), "the icon"),
      size=num(0.9, 0.4, 2, "tile width"))
def p_tool(b):
    p = b.p
    s = p["size"]
    part = b.box(-s / 2, -0.08, 0, s / 2, 0.08, s * 1.05, P.M["paper"])
    pl = front_plane(-s / 2, s / 2, 0, -0.08)
    acc = b.t.accent if b.tint != "neutral" else P.INK2
    cu, cv, r = s / 2, s * 0.52, s * 0.28
    ic = p["icon"]
    els = []
    if ic == "gear":
        pts = []
        for i in range(16):
            a = math.radians(i * 22.5 + 11.25)
            rr = r if i % 2 == 0 else r * 0.74
            for da in (-7, 7):
                aa = a + math.radians(da)
                pts.append((cu + math.cos(aa) * rr, cv + math.sin(aa) * rr))
        els.append(pl.shape(poly2(pts), fill=acc, body=False))
        els.append(pl.shape(circle2(cu, cv, r * 0.34), fill="#ffffff", body=False))
    elif ic == "terminal":
        els.append(pl.shape(rrect(cu - r * 1.1, cv - r * 0.85, cu + r * 1.1, cv + r * 0.85, r * 0.15), fill=acc, body=False))
        els.append(pl.line([(cu - r * 0.7, cv + r * 0.35), (cu - r * 0.3, cv), (cu - r * 0.7, cv - r * 0.35)], stroke="#ffffff",
                           swu=r * 0.16, cap="round", join="round"))
        els.append(pl.line([(cu - r * 0.1, cv - r * 0.4), (cu + r * 0.6, cv - r * 0.4)], stroke="#ffffff", swu=r * 0.16, cap="round"))
    elif ic == "globe":
        els.append(pl.path(circle2(cu, cv, r), stroke=acc, swu=r * 0.16))
        els.append(pl.path(ellipse2(cu, cv, r * 0.45, r), stroke=acc, swu=r * 0.12))
        els.append(pl.line([(cu - r, cv), (cu + r, cv)], stroke=acc, swu=r * 0.12))
    elif ic == "wrench":
        els.append(pl.line([(cu - r * 0.7, cv - r * 0.7), (cu + r * 0.35, cv + r * 0.35)], stroke=acc, swu=r * 0.36, cap="round"))
        els.append(pl.path(arc2(cu + r * 0.55, cv + r * 0.55, r * 0.42, -100, 190), stroke=acc, swu=r * 0.3, cap="butt"))
    elif ic == "search":
        els.append(pl.path(circle2(cu - r * 0.15, cv + r * 0.15, r * 0.6), stroke=acc, swu=r * 0.2))
        els.append(pl.line([(cu + r * 0.3, cv - r * 0.3), (cu + r * 0.85, cv - r * 0.85)], stroke=acc, swu=r * 0.26, cap="round"))
    elif ic == "doc":
        els.append(pl.shape(rrect(cu - r * 0.75, cv - r, cu + r * 0.75, cv + r, r * 0.1), fill=acc, body=False))
        for i in range(3):
            els.append(tline(pl, cu - r * 0.45, cv + r * (0.45 - i * 0.4), cu + r * 0.45, "#ffffff", w=r * 0.13))
    elif ic == "database":
        for i in range(3):
            vv = cv - r * 0.7 + i * r * 0.6
            els.append(pl.shape(ellipse2(cu, vv, r * 0.8, r * 0.28), fill=acc if i % 2 == 0 else mix(acc, "#ffffff", 0.3), body=False))
    elif ic == "mail":
        els.append(pl.shape(rect(cu - r, cv - r * 0.65, cu + r, cv + r * 0.65), fill=acc, body=False))
        els.append(pl.line([(cu - r, cv + r * 0.65), (cu, cv), (cu + r, cv + r * 0.65)], stroke="#ffffff", swu=r * 0.12, join="round"))
    part.els += els


@prop("nodes", "Agents", "A small network: spheres joined by lines, standing on the ground (agents talking, a protocol, "
      "a mesh). The highlighted node takes the tint.", tints=("neutral", "tee", "data") + LAYER_TINTS, tint="agents",
      layout=choice("mesh", ("mesh", "ring", "star", "chain"), "how the nodes are joined"), count=integer(5, 3, 8, "nodes"),
      w=num(3, 1, 8, "width (x)"), d=num(2.2, 0.6, 8, "depth (y)"), post=num(0, 0, 0.15, "a short post under each node"),
      highlight=integer(0, -1, 7, "index of the node in the tint (-1: none)"))
def p_nodes(b):
    p = b.p
    r = 0.26
    n, w, d, zc = p["count"], p["w"], p["d"], r + p["post"]
    lay = p["layout"]
    pts = []
    if lay == "ring":
        for i in range(n):
            a = math.radians(90 + i * 360.0 / n)
            pts.append((math.cos(a) * w / 2, math.sin(a) * d / 2))
        edges = [(i, (i + 1) % n) for i in range(n)]
    elif lay == "star":
        pts.append((0.0, 0.0))
        for i in range(n - 1):
            a = math.radians(30 + i * 360.0 / (n - 1))
            pts.append((math.cos(a) * w / 2, math.sin(a) * d / 2))
        edges = [(0, i) for i in range(1, n)]
    elif lay == "chain":
        for i in range(n):
            pts.append((-w / 2 + w * i / (n - 1), d * 0.25 * (1 if i % 2 else -1)))
        edges = [(i, i + 1) for i in range(n - 1)]
    else:
        base = [(-0.5, -0.1), (-0.12, 0.42), (0.1, -0.38), (0.45, 0.15), (-0.32, -0.48), (0.48, -0.42), (-0.05, 0.05), (0.22, 0.5)]
        pts = [(x * w, y * d) for x, y in base[:n]]
        edges = []
        for i in range(n):
            ds = sorted(range(n), key=lambda j: ((pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2, j))
            for j in ds[1:3]:
                e = (min(i, j), max(i, j))
                if e not in edges:
                    edges.append(e)
    lines = []
    for i, j in edges:
        lines.append(line([(pts[i][0], pts[i][1], zc), (pts[j][0], pts[j][1], zc)], stroke=P.MUTE, swu=0.06, cap="round"))
    for e in lines:
        e.body = True
    b.add(lines, name="links")
    hi = p["highlight"]
    for i, (x, y) in enumerate(pts):
        m = b.t.solid if i == hi else P.Mat("#ffffff", "#e3e6ea", "#c3c9d0", None, "node")
        if p["post"] > 0.02:
            b.cyl(x, y, 0, p["post"] + r * 0.3, 0.06, P.M["steel"])
        b.sphere((x, y, zc), r, m.left if i == hi else "#e3e6ea", hi=m.top if i == hi else "#ffffff")
    if 0 <= hi < n:
        b.anchors["hub"] = (pts[hi][0], pts[hi][1], zc)
    b.footprint = (-w / 2 - 0.3, -d / 2 - 0.3, w / 2 + 0.3, d / 2 + 0.3)


@prop("neural_net", "Models", "A model as a standing card of layered nodes and connections, as on the hero's model "
      "layer.", tints=("models", "neutral", "tee", "data") + LAYER_TINTS, tint="models", aliases={"layers": "columns"},
      columns=nums([3, 4, 2], 2, 5, 1, 6, "nodes in each column of the network, left to right (`layers` is accepted "
                   "as its older name)"), w=num(2.2, 1, 5, "card width"),
      h=num(1.5, 0.8, 4, "card height"))
def p_neural_net(b):
    p = b.p
    w, h = p["w"], p["h"]
    part = b.box(-w / 2, -0.05, 0, w / 2, 0.05, h, P.M["paper"])
    pl = front_plane(-w / 2, w / 2, 0, -0.05)
    ls = [int(x) for x in p["columns"]]
    acc = b.t.accent if b.tint != "neutral" else P.INK2
    acc2 = b.t.accent2 if b.tint != "neutral" else P.MUTE
    cols = []
    for i, n in enumerate(ls):
        u = w * (0.16 + 0.68 * i / (len(ls) - 1))
        col = [(u, h * (0.5 + (j - (n - 1) / 2.0) * min(0.2, 0.7 / max(1, n - 1)))) for j in range(n)]
        cols.append(col)
    for a, c in zip(cols, cols[1:]):
        for p1 in a:
            for p2 in c:
                part.els.append(pl.line([p1, p2], stroke=acc2, swu=0.018, sop=0.55))
    r = min(0.1, h * 0.07)
    for i, col in enumerate(cols):
        last = i == len(cols) - 1
        for (u, v) in col:
            if last:
                part.els.append(pl.shape(circle2(u, v, r), fill=acc, body=False))
            else:
                part.els.append(pl.shape(circle2(u, v, r), fill="#ffffff", body=False))
                part.els.append(pl.path(circle2(u, v, r), stroke=acc, swu=0.03))


@prop("weights", "Models", "Model weights as a block: a cube whose faces carry a regular grid of cells shaded like a "
      "matrix of values, two of them in the tint's strong shade (a model file, a checkpoint).",
      tints=("models", "neutral", "tee", "data", "seal") + LAYER_TINTS, tint="models", size=num(1.4, 0.5, 3, "edge"))
def p_weights(b):
    s = b.p["size"]
    hs = s / 2
    neutral = b.tint == "neutral"
    pale = P.Mat("#f6f7f9", "#e6e9ee", "#cfd5dd", None, "wpale") if neutral else b.t.light.lighter(0.35)
    part = b.box(-hs, -hs, 0, hs, hs, s, pale)
    acc = b.t.accent if not neutral else P.INK2
    acc2 = b.t.accent2 if not neutral else P.MUTE
    n = 4
    c = s / n
    m = c * 0.09
    # every side face carries the grid (the ones turned away are culled); the shades
    # follow a fixed table, so neighboring faces differ and the block reads as values
    shades = (0.18, 0.42, 0.1, 0.3, 0.34, 0.12, 0.5, 0.2, 0.08, 0.28, 0.16, 0.44, 0.38, 0.22, 0.06, 0.26)
    faces = [(front_plane(-hs, hs, 0, -hs), 0, (9, 6)), (right_plane(-hs, hs, 0, hs), 5, (2, 13)),
             (Plane((hs, hs, 0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)), 10, (4, 11)),
             (Plane((-hs, hs, 0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)), 3, (7, 12)),
             (top_plane(-hs, -hs, s), 7, (5,))]
    for pl, shift, hot in faces:
        for i in range(n):
            for j in range(n):
                idx = j * n + i
                fill, op = (acc, 0.88) if idx in hot else (acc2, shades[(idx + shift) % len(shades)])
                part.els.append(pl.shape(rect(i * c + m, j * c + m, (i + 1) * c - m, (j + 1) * c - m), fill=fill, body=False,
                                         op=op))


@prop("proof_tree", "Proofs", "Building blocks stacked as a stepped pyramid, many lemmas at the bottom and one theorem at "
      "the top: a formal proof, verified building blocks. The top block takes the tint.",
      tints=("evaluations", "tee", "data", "neutral", "models", "institutions", "seal"), tint="evaluations",
      levels=integer(4, 2, 5, "rows of blocks (the bottom row has this many)"), block=num(0.62, 0.3, 1.2, "block edge"))
def p_proof_tree(b):
    p = b.p
    L, s = p["levels"], p["block"]
    gap = s * 0.12
    back = s * 0.32          # each row steps back by this much, so the rows read as steps
    pale = P.Mat("#ffffff", "#e5e9ee", "#c9cfd7", None, "lemma")
    y0 = -(L - 1) * back / 2
    for lev in range(L):
        n = L - lev
        z = lev * s
        y = y0 + lev * back
        x0 = -(n - 1) * (s + gap) / 2
        for i in range(n):
            x = x0 + i * (s + gap)
            top = lev == L - 1
            part = b.box(x - s / 2, y - s / 2, z, x + s / 2, y + s / 2, z + s, b.t.solid if top else pale)
            if top:
                fp = front_plane(x - s / 2, x + s / 2, z, y - s / 2)
                part.els.append(fp.line([(s * 0.36, s * 0.72), (s * 0.36, s * 0.28)], stroke="#ffffff", swu=s * 0.08, cap="round"))
                part.els.append(fp.line([(s * 0.36, s * 0.5), (s * 0.7, s * 0.5)], stroke="#ffffff", swu=s * 0.08, cap="round"))
    b.anchors["top"] = (0, y0 + (L - 1) * back, L * s)
    b.footprint = (-(L - 1) * (s + gap) / 2 - s / 2, y0 - s / 2, (L - 1) * (s + gap) / 2 + s / 2, -y0 + s / 2)


@prop("math_block", "Proofs", "A block with an abstract mark on its front (a turnstile, brackets, an equals sign, a "
      "lambda, a sum): a formula, a lemma, a statement.", tints=("neutral", "evaluations", "tee", "data", "models", "seal"),
      tint="neutral", size=num(1, 0.4, 2.5, "edge"),
      mark=choice("turnstile", ("turnstile", "brackets", "equals", "lambda", "sum", "arrow"), "the mark"))
def p_math_block(b):
    p = b.p
    s = p["size"]
    hs = s / 2
    solid = b.tint != "neutral"
    m = b.t.solid if solid else P.Mat("#ffffff", "#e8ebef", "#cdd2d9", None, "lemma")
    part = b.box(-hs, -hs, 0, hs, hs, s, m)
    fp = front_plane(-hs, hs, 0, -hs)
    c = "#ffffff" if solid else P.INK2
    sw = s * 0.08
    mk = p["mark"]
    L = []
    if mk == "turnstile":
        L = [[(s * 0.3, s * 0.75), (s * 0.3, s * 0.25)], [(s * 0.3, s * 0.5), (s * 0.72, s * 0.5)]]
    elif mk == "brackets":
        L = [[(s * 0.38, s * 0.78), (s * 0.26, s * 0.78), (s * 0.26, s * 0.22), (s * 0.38, s * 0.22)],
             [(s * 0.62, s * 0.78), (s * 0.74, s * 0.78), (s * 0.74, s * 0.22), (s * 0.62, s * 0.22)]]
    elif mk == "equals":
        L = [[(s * 0.28, s * 0.6), (s * 0.72, s * 0.6)], [(s * 0.28, s * 0.4), (s * 0.72, s * 0.4)]]
    elif mk == "lambda":
        L = [[(s * 0.3, s * 0.24), (s * 0.52, s * 0.6)], [(s * 0.36, s * 0.78), (s * 0.7, s * 0.24)]]
    elif mk == "sum":
        L = [[(s * 0.7, s * 0.76), (s * 0.3, s * 0.76), (s * 0.52, s * 0.5), (s * 0.3, s * 0.24), (s * 0.7, s * 0.24)]]
    else:
        L = [[(s * 0.26, s * 0.5), (s * 0.72, s * 0.5)], [(s * 0.56, s * 0.66), (s * 0.72, s * 0.5), (s * 0.56, s * 0.34)]]
    for pts in L:
        part.els.append(fp.line(pts, stroke=c, swu=sw, cap="round", join="round"))


# ======================================================================= location and supply chain
@prop("map", "Location", "A map tile lying on the ground: land, roads, a river and a border.",
      tints=("neutral", "tee", "data", "seal"), tint="neutral", w=num(3.2, 1, 10, "width (x)"), d=num(2.4, 1, 10, "depth (y)"),
      border=flag(True, "a dashed border line across the map"))
def p_map(b):
    p = b.p
    w, d = p["w"], p["d"]
    part = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, 0.06, P.Mat("#f3f6f2", "#dde3dc", "#c8d0c7", None, "mapland"), lip=P.LIP)
    tp = top_plane(-w / 2, -d / 2, 0.06)
    part.els.append(tp.shape([("M", w * 0.55, 0), ("C", w * 0.6, d * 0.3, w * 0.4, d * 0.5, w * 0.5, d), ("L", w * 0.58, d),
                              ("C", w * 0.48, d * 0.5, w * 0.68, d * 0.3, w * 0.62, 0), ("Z",)], fill="#c9d6e6", body=False))
    part.els.append(tp.shape(poly2([(w * 0.05, d * 0.6), (w * 0.3, d * 0.55), (w * 0.38, d * 0.92), (w * 0.08, d * 0.95)]),
                             fill="#e3eadf", body=False))
    part.els.append(tp.line([(0, d * 0.25), (w * 0.4, d * 0.32), (w * 0.75, d * 0.2), (w, d * 0.28)], stroke="#ffffff", swu=0.07,
                            join="round"))
    part.els.append(tp.line([(w * 0.3, 0), (w * 0.34, d * 0.5), (w * 0.22, d)], stroke="#ffffff", swu=0.05, join="round"))
    if p["border"]:
        acc = b.t.accent if b.tint != "neutral" else P.INK2
        part.els.append(tp.line([(w * 0.8, 0), (w * 0.74, d * 0.4), (w * 0.88, d * 0.7), (w * 0.82, d)], stroke=acc, swu=0.04,
                                dash="5 4", cap="butt"))
    b.surface = 0.06


@prop("map_pin", "Location", "A location pin standing on its point: where something is (a chip, a server, a user).",
      tints=("data", "tee", "seal", "neutral") + LAYER_TINTS, tint="data", size=num(0.9, 0.3, 2, "pin width"))
def p_map_pin(b):
    p = b.p
    s = p["size"]
    r = s / 2
    pl = front_plane(0, 0, 0, -0.1 * s)
    m = b.t.solid
    head = circle2(0, s * 1.15, r)
    tip = poly2([(-r * 0.93, s * 1.15 - r * 0.38), (0, 0), (r * 0.93, s * 1.15 - r * 0.38)])
    els = b.extrude_els(pl, [head, tip], 0.2 * s, m.left, side=m.right)
    els.append(pl.shape(circle2(0, s * 1.15, r * 0.4), fill="#ffffff", body=False))
    ringp = top_plane(0, 0, 0.005)
    b.add([ringp.path(ellipse2(0, 0, r * 0.7, r * 0.7), stroke=m.left, swu=0.04, sop=0.6)])
    b.add(els)
    b.footprint = (-r * 0.5, -0.1 * s, r * 0.5, 0.1 * s)
    b.anchors["tip"] = (0, 0, 0)


@prop("satellite", "Location", "A satellite with two solar wings and a dish, floating (give it a height in 'at'): "
      "positioning, location checks, remote sensing.", tints=("neutral", "tee", "data"), tint="neutral",
      size=num(1, 0.5, 2.5, "scale factor"))
def p_satellite(b):
    k = b.p["size"]
    body = P.M["metal"] if b.tint == "neutral" else b.t.light
    b.cbox(0, 0, 0, 0.7 * k, 0.7 * k, 0.8 * k, body)
    panel = P.Mat("#4a5058", P.SUB0, P.SUB1, None, "solar")
    for sx in (-1, 1):
        x0 = sx * 0.35 * k
        x1 = sx * 1.75 * k
        part = b.box(min(x0, x1) + (0.12 * k if sx > 0 else 0), -0.36 * k, 0.36 * k, max(x0, x1) - (0.12 * k if sx < 0 else 0), 0.36 * k,
                     0.42 * k, panel, lip="#8d949d")
        tp = top_plane(min(x0, x1) + (0.12 * k if sx > 0 else 0), -0.36 * k, 0.42 * k)
        L = abs(x1 - x0) - 0.12 * k
        for i in range(1, 4):
            part.els.append(tp.line([(L * i / 4, 0), (L * i / 4, 0.72 * k)], stroke="#6a7280", swu=0.02 * k))
        part.els.append(tp.line([(0, 0.36 * k), (L, 0.36 * k)], stroke="#6a7280", swu=0.02 * k))
    b.cyl(0, 0, 0.8 * k, 0.9 * k, 0.08 * k, P.M["steel"])
    b.cyl(0, 0, 0.9 * k, 0.98 * k, 0.32 * k, P.M["paper"], rim=P.SOFT2)
    if b.tint != "neutral":
        fp = front_plane(-0.35 * k, 0.35 * k, 0, -0.35 * k)
        b.parts[0].els.append(fp.shape(circle2(0.35 * k, 0.55 * k, 0.07 * k), fill=b.t.accent, body=False))
    b.lift = 1.0
    b.footprint = (-0.4 * k, -0.4 * k, 0.4 * k, 0.4 * k)


@prop("globe", "Location", "A globe on a small stand: a shaded sphere with meridians on its lit side: international, "
      "global standards, worldwide.", tints=("neutral", "tee", "data") + LAYER_TINTS, tint="neutral", r=num(0.8, 0.3, 2, "radius"))
def p_globe(b):
    r = b.p["r"]
    b.cyl(0, 0, 0, 0.08, r * 0.55, P.M["steel"])
    b.cyl(0, 0, 0.08, r * 0.4, 0.05, P.M["steel"])
    neutral = b.tint == "neutral"
    light, dark = ("#e9eef4", "#9fb0c4") if neutral else (b.t.light.top, b.t.solid.left)
    line_c = "#7d8a9c" if neutral else b.t.accent
    zc = r * 0.4 + r
    from .iso import Sphere as S
    els = [S((0, 0, zc), r, dark, shade=(light, dark))]
    # a plane facing the viewer, scaled so a circle of radius r matches the sphere's outline
    pl = Plane((0, 0, zc), (0.7071, 0.7071, 0.0), (0.0, 0.0, 1.1832))
    sw = 0.035 * r
    for f in (0.42, 0.78):                          # meridians, on the lit (left) half only
        els.append(pl.path(arc2(0, 0, r * f, 100, 260, rv=r * 0.97), stroke=line_c, swu=sw, sop=0.55, cap="round"))
    els.append(pl.path(arc2(0, 0, r * 0.98, 190, 290, rv=r * 0.3), stroke=line_c, swu=sw, sop=0.55, cap="round"))
    els.append(pl.path(arc2(0, r * 0.45, r * 0.86, 195, 280, rv=r * 0.22), stroke=line_c, swu=sw * 0.8, sop=0.45, cap="round"))
    for e in els[1:]:
        e.cull = False
    b.add(els, convex=True)


@prop("crate", "Supply chain", "A shipping crate with slats and a label: a shipment, the supply chain, an export.",
      tints=("neutral", "tee", "data", "seal") + LAYER_TINTS, tint="neutral", size=num(1.3, 0.5, 3, "edge"),
      label=flag(True, "a label on the front in the tint"))
def p_crate(b):
    p = b.p
    s = p["size"]
    hs = s / 2
    kraft = P.M["kraft"]
    part = b.box(-hs, -hs, 0, hs, hs, s * 0.9, kraft)
    h = s * 0.9
    for pl, wd in ((front_plane(-hs, hs, 0, -hs), s), (right_plane(-hs, hs, 0, hs), s)):
        part.els.append(pl.path(rect(0.05 * s, 0.05 * s, wd - 0.05 * s, h - 0.05 * s), stroke="#c6a878", swu=0.06 * s))
        part.els.append(pl.line([(0.08 * s, 0.08 * s), (wd - 0.08 * s, h - 0.08 * s)], stroke="#c6a878", swu=0.06 * s))
    tp = top_plane(-hs, -hs, h)
    for i in range(1, 4):
        part.els.append(tp.line([(0, s * i / 4), (s, s * i / 4)], stroke="#d8c39c", swu=0.02 * s))
    if p["label"]:
        fp = front_plane(-hs, hs, 0, -hs - 0.002)
        acc = b.t.accent if b.tint != "neutral" else P.INK2
        part.els.append(fp.shape(rect(s * 0.56, h * 0.58, s * 0.88, h * 0.82), fill="#ffffff", body=False))
        part.els.append(fp.line([(s * 0.62, h * 0.74), (s * 0.82, h * 0.74)], stroke=acc, swu=0.05 * s))
        part.els.append(fp.line([(s * 0.62, h * 0.65), (s * 0.76, h * 0.65)], stroke=P.SOFT2, swu=0.04 * s))
    b.surface = h


@prop("chain", "Supply chain", "A chain of solid links lying along x, alternately standing and lying, whole or broken: a "
      "chain of evidence, of custody, of trust. broken opens the chain after that link.",
      tints=("tee", "neutral", "data") + LAYER_TINTS, tint="tee",
      links=integer(5, 2, 9, "links"), broken=integer(-1, -1, 8, "the link after which the chain is open (-1: whole)"),
      size=num(0.8, 0.4, 2, "link length"))
def p_chain(b):
    p = b.p
    n, L = p["links"], p["size"]
    step = L * 0.78
    m = b.t.solid if b.tint != "neutral" else P.M["steel"]
    br = p["broken"] if p["broken"] < n - 1 else -1
    gap = 0.75 * L if br >= 0 else 0.0
    x0 = -((n - 1) * step + gap) / 2
    r = L * 0.26
    w = 0.13 * L                    # the wire's width, and how far its shaded side shows
    zc = r + w
    for i in range(n):
        x = x0 + i * step + (gap if 0 <= br < i else 0.0)
        if i % 2 == 0:
            # standing: the lit face in front, the wire's depth behind it
            pl = Plane((x, -w / 2, zc), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
            back = Plane((x, w / 2, zc), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
            col, side = m.left, m.right
        else:
            # lying: the top face up, its depth below it
            pl = top_plane(x, 0, w)
            back = top_plane(x, 0, 0.0)
            col, side = m.top, m.right
        if i == br or i == br + 1:
            # an opened link: a C with its open end toward the break
            u0, u1 = -L / 2 + r, L / 2 - r
            if i == br:
                cmds = [("M", u1, r), ("L", u0, r)] + arc2(u0, 0, r, 90, 270, move=False)[1:] + [("L", u1, -r)]
            else:
                cmds = [("M", u0, -r), ("L", u1, -r)] + arc2(u1, 0, r, -90, 90, move=False)[1:] + [("L", u0, r)]
        else:
            cmds = rrect(-L / 2, -r, L / 2, r, r)
        els = [back.path(cmds, cull=False, stroke=side, swu=w, cap="round", join="round"),
               pl.path(cmds, cull=False, stroke=col, swu=w, cap="round", join="round"),
               pl.path(cmds, cull=False, stroke="#ffffff", swu=w * 0.22, sop=0.5, cap="round", join="round")]
        for e in els[:2]:
            e.body = True
        b.add(els)
    if br >= 0:
        b.anchors["gap"] = (x0 + br * step + L / 2 + gap / 2, 0, zc)
    b.footprint = (x0 - L / 2, -L * 0.3, x0 + (n - 1) * step + gap + L / 2, L * 0.3)


@prop("gate", "Supply chain", "A gateway of two pillars and a lintel, with an optional scanning field between them: a "
      "checkpoint, a border, an access check.", tints=("neutral", "tee", "data", "seal") + LAYER_TINTS, tint="tee",
      w=num(2.2, 1, 6, "inner width"), h=num(2.4, 1, 6, "inner height"), field=flag(True, "a glowing scanning field"))
def p_gate(b):
    p = b.p
    w, h = p["w"], p["h"]
    pw, pd = 0.38, 0.5
    m = P.M["metal"]
    for sx in (-1, 1):
        x = sx * (w / 2 + pw / 2)
        b.cbox(x, 0, 0, pw, pd, h, m)
    top = b.box(-w / 2 - pw, -pd / 2, h, w / 2 + pw, pd / 2, h + 0.38, m)
    fp = front_plane(-w / 2 - pw, w / 2 + pw, h, -pd / 2)
    acc = b.t.accent if b.tint != "neutral" else P.INK2
    top.els.append(fp.line([(0.3, 0.19), (w + 2 * pw - 0.3, 0.19)], stroke=acc, swu=0.07))
    if p["field"]:
        pl = Plane((-w / 2, 0, 0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        f = [pl.shape(rect(0, 0.02, w, h), fill=b.t.glow if b.tint != "neutral" else "#c3cedb", fop=0.16, cull=False, body=False)]
        for i in range(1, 4):
            f.append(pl.line([(0.05, h * i / 4), (w - 0.05, h * i / 4)], stroke=acc, swu=0.03, sop=0.45))
        for e in f:
            e.cull = False
        fe = b.add(f)
        fe.els[0].body = True
    b.anchors["through"] = (0, 0, 0)
    b.anchors["opening"] = (0, 0, min(0.62, h / 2))
    b.port = "through"


@prop("sign", "Supply chain", "A warning sign on a post: a triangle with an exclamation mark (no words): a risk, an attack, "
      "a caution.", tints=("warn", "seal", "data", "neutral"), tint="warn", size=num(1, 0.5, 2.5, "scale factor"))
def p_sign(b):
    k = b.p["size"]
    b.cbox(0, 0.06 * k, 0, 0.1 * k, 0.1 * k, 1.1 * k, P.M["steel"], lip=None)
    pl = front_plane(0, 0, 0, -0.02 * k)
    if b.tint == "warn":
        face, side, mark = "#e2b93b", "#b8902a", P.INK
    elif b.tint == "neutral":
        face, side, mark = "#ffffff", "#cdd2d9", P.INK
    else:
        face, side, mark = b.t.solid.left, b.t.solid.right, "#ffffff"
    tri = [(-0.62 * k, 0.9 * k), (0.62 * k, 0.9 * k), (0, 1.98 * k)]
    els = b.extrude_els(pl, [poly2(tri)], 0.06 * k, face, side=side)
    els.append(pl.path(poly2([(-0.48 * k, 0.98 * k), (0.48 * k, 0.98 * k), (0, 1.82 * k)]), stroke=mark, swu=0.05 * k, join="round"))
    els.append(pl.line([(0, 1.5 * k), (0, 1.22 * k)], stroke=mark, swu=0.12 * k, cap="round"))
    els.append(pl.shape(circle2(0, 1.08 * k, 0.065 * k), fill=mark, body=False))
    b.add(els)


@prop("conveyor", "Supply chain", "A conveyor belt on legs: a pipeline, a processing line. Put props on it with 'on'.",
      tints=("neutral", "tee", "data"), tint="neutral", length=num(4, 1.5, 12, "length (x)"), width=num(1.2, 0.6, 3, "belt width"))
def p_conveyor(b):
    p = b.p
    L, wd = p["length"], p["width"]
    z = 0.7
    for x in (-L / 2 + 0.3, L / 2 - 0.3):
        for y in (-wd / 2 + 0.12, wd / 2 - 0.12):
            b.cbox(x, y, 0, 0.12, 0.12, z - 0.18, P.M["steel"], lip=None)
    frame = b.box(-L / 2, -wd / 2, z - 0.2, L / 2, wd / 2, z, P.M["metal"])
    fp = front_plane(-L / 2, L / 2, z - 0.2, -wd / 2)
    n = int(L / 0.5)
    for i in range(n + 1):
        frame.els.append(fp.shape(circle2(0.1 + (L - 0.2) * i / n, 0.1, 0.055), fill="#aeb5be", body=False))
    belt = b.box(-L / 2 + 0.05, -wd / 2 + 0.08, z, L / 2 - 0.05, wd / 2 - 0.08, z + 0.04, P.M["ink"], lip=None)
    tp = top_plane(-L / 2 + 0.05, -wd / 2 + 0.08, z + 0.04)
    for i in range(1, int(L / 0.4)):
        belt.els.append(tp.line([(0.4 * i, 0.04), (0.4 * i, wd - 0.2)], stroke="#4a5058", swu=0.03))
    if b.tint != "neutral":
        belt.els.append(tp.line([(0.1, (wd - 0.16) / 2), (L - 0.2, (wd - 0.16) / 2)], stroke=b.t.accent, swu=0.04, dash="6 6"))
    b.surface = z + 0.04
    b.anchors["start"] = (-L / 2, 0, z + 0.04)
    b.anchors["end"] = (L / 2, 0, z + 0.04)


# ======================================================================= people and furniture
_FIGURE = []


def _figure():
    if not _FIGURE:
        from .figure import load
        _FIGURE.append(load())
    return _FIGURE[0]


PERSON_COLOURS = {
    "data": {"coat": P.DATA, "coat2": P.DATA2},
    "neutral": {"coat": "#aeb5be", "coat2": "#8d949d"},
    "tee": {"coat": P.TEE2, "coat2": P.TEE},
}
PERSON_BASE = {"shoe": P.SHOE, "legs": P.LEGS, "legs2": P.LEGS2, "skin": P.SKIN, "skin2": P.SKIN2, "hair": P.HAIR,
               "phone": "#1e2226", "screen": P.TPLATE_TOP1}


@prop("person", "People", "The reader from the home page hero: one person seen from behind in the orange coat, reading a "
      "phone held in both hands (the hero's own figure, traced by tools/scene/figure.py). They face up and to the right "
      "(facing back-right, the only facing), so stand them at the front left, looking into the scene. No faces, no crowds: "
      "at most one per picture.", tints=("data", "neutral", "tee"), tint="data", facings=("back-right",),
      height=num(2.4, 1.4, 3.5, "height"))
def p_person(b):
    fig = _figure()
    f = b.p["height"] / fig["height"]
    cols = dict(PERSON_BASE)
    cols.update(PERSON_COLOURS[b.tint])
    paths = [(cols[role], [[(x, y) for x, y in poly] for poly in polys]) for role, polys in fig["paths"]]
    # local coordinates: the figure's forward (the hero's +t) is the prop's front (-y), turned to +t by back-right
    box = (-10 * f, -12 * f, 0.0, 10 * f, 4 * f, 88 * f)
    b.add([Baked(paths, (0.0, 0.0, 0.0), f, box)])
    b.footprint = (-7 * f, -6 * f, 7 * f, 6 * f)
    b.contacts.append((0.0, -1.2 * f, 9 * f))
    b.anchors["phone"] = (-3.3 * f, -11.6 * f, 58.6 * f)
    b.anchors["head"] = (-0.25 * f, -2.2 * f, 86 * f)
    b.port = "phone"
    b.outline = False


@prop("desk", "People", "A desk on four legs; place things on it with 'on'.",
      tints=("neutral",), w=num(3.2, 1.2, 8, "width (x)"), d=num(1.8, 0.8, 4, "depth (y)"), h=num(1.1, 0.5, 2, "height"))
def p_desk(b):
    p = b.p
    w, d, h = p["w"], p["d"], p["h"]
    for x in (-w / 2 + 0.15, w / 2 - 0.15):
        for y in (-d / 2 + 0.15, d / 2 - 0.15):
            b.cbox(x, y, 0, 0.12, 0.12, h - 0.1, P.M["steel"], lip=None)
    b.box(-w / 2, -d / 2, h - 0.1, w / 2, d / 2, h, P.Mat("#f7f8f9", "#e1e4e8", "#c9ced5", None, "desktop"))
    b.surface = h


@prop("stamp", "Security", "A rubber stamp with a knob handle, and optionally its fresh impression beside it: signing, "
      "approval, certification.", tints=("seal", "tee", "data", "neutral"), tint="seal", size=num(1, 0.5, 2.5, "scale factor"),
      impression=flag(True, "a stamped ring on the ground beside it"))
def p_stamp(b):
    k = b.p["size"]
    m = b.t.solid if b.tint != "neutral" else P.M["ink"]
    if b.p["impression"]:
        tp = top_plane(0, 0, 0.004)
        ring = tp.path(circle2(0.95 * k, -0.15 * k, 0.32 * k), stroke=m.left, swu=0.07 * k, sop=0.85)
        dot = tp.shape(circle2(0.95 * k, -0.15 * k, 0.12 * k), fill=m.left, body=False, op=0.85)
        ring.body = True
        b.add([ring, dot])
    b.cbox(0, 0, 0, 0.8 * k, 0.8 * k, 0.12 * k, m, lip=None)
    b.cbox(0, 0, 0.12 * k, 0.86 * k, 0.86 * k, 0.16 * k, P.M["institutions"].lighter(0.2), lip=P.LIP)
    b.cyl(0, 0, 0.28 * k, 0.75 * k, 0.12 * k, P.M["ink"])
    b.sphere((0, 0, 0.92 * k), 0.24 * k, m.left, hi=m.top)
    b.footprint = (-0.43 * k, -0.43 * k, 0.43 * k, 0.43 * k)
