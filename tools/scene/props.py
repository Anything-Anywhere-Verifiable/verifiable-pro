"""The prop library. Each prop draws in local coordinates (see kit.py): x along its
front, y into its depth, the front facing -y, z up, footprint centered on the origin.
Sizes are in grid units (one unit is 40 px at zoom 1)."""
import math

from . import palette as P
from .iso import (Glass, Glow, Plane, Sphere, Wall, add, arc2, circle2, front_plane, line, mul, poly, poly2, rect,
                  right_plane, rrect, top_plane)
from .kit import (CORE, SCREEN_KINDS, choice, flag, integer, lock_glyph, material, num, nums, prop,
                  screen_content, shield2, tline)

LAYER_TINTS = ("models", "outputs", "agents", "evaluations", "institutions")


# ======================================================================= primitives
@prop("box", "Primitives", "A plain box, for anything the library lacks (a cabinet, a block, a step).",
      example={"w": 1.4, "d": 1.0, "h": 0.9},
      w=num(1, 0.1, 12, "width along the front (x)"), d=num(1, 0.1, 12, "depth (y)"),
      h=num(1, 0.02, 10, "height"), material=material("auto"), lip=flag(True, "white highlight on the top's front edges"))
def p_box(b):
    p = b.p
    b.box(-p["w"] / 2, -p["d"] / 2, 0, p["w"] / 2, p["d"] / 2, p["h"], b.mat(p["material"]),
          lip=P.LIP if p["lip"] else None)


@prop("slab", "Primitives", "A thin slab: a tile, a tray, a board, a step.",
      w=num(2, 0.1, 16, "width (x)"), d=num(1.4, 0.1, 16, "depth (y)"), h=num(0.14, 0.02, 1, "thickness"),
      material=material("auto"), radius=num(0, 0, 1, "corner radius (rounded slabs have no lip)"))
def p_slab(b):
    p = b.p
    w, d, h, r = p["w"], p["d"], p["h"], p["radius"]
    m = b.mat(p["material"])
    if r <= 0:
        b.box(-w / 2, -d / 2, 0, w / 2, d / 2, h, m)
    else:
        pl = top_plane(0, 0, h)
        b.extrude(pl, [rrect(-w / 2, -d / 2, w / 2, d / 2, r)], h, m.top, side=m.right)


@prop("cylinder", "Primitives", "An upright cylinder: a drum, a post, a column, a token.",
      r=num(0.5, 0.05, 5, "radius"), h=num(1, 0.02, 10, "height"), material=material("auto"),
      rim=flag(False, "a thin lighter rim around the top"))
def p_cylinder(b):
    p = b.p
    m = b.mat(p["material"])
    b.cyl(0, 0, 0, p["h"], p["r"], m, rim="#ffffff" if p["rim"] else None)


@prop("sphere", "Primitives", "A ball resting on the ground (or floating, with a height in 'at').",
      r=num(0.4, 0.05, 4, "radius"), material=material("auto"))
def p_sphere(b):
    p = b.p
    m = b.mat(p["material"])
    b.sphere((0, 0, p["r"]), p["r"], m.left, hi=m.top)


@prop("panel", "Primitives", "A standing card or sign board with abstract content on its front.",
      w=num(1.6, 0.2, 8, "width"), h=num(1.2, 0.2, 6, "height"), thickness=num(0.08, 0.02, 0.6, "thickness"),
      content=choice("text", SCREEN_KINDS, "what the front shows"), material=material("paper"),
      lift=num(0, 0, 3, "height of the card's bottom edge above its base (a floating card)"))
def p_panel(b):
    p = b.p
    w, h, th, z0 = p["w"], p["h"], p["thickness"], p["lift"]
    m = b.mat(p["material"])
    part = b.box(-w / 2, -th / 2, z0, w / 2, th / 2, z0 + h, m)
    pl = front_plane(-w / 2, w / 2, z0, -th / 2)
    part.els += screen_content(pl, 0.0, 0.0, w, h, p["content"], b.t)
    b.lift = z0 if z0 > 0 else 0.0


@prop("sheet", "Primitives", "A flat sheet lying on the ground or on a desk: a page, a mat.",
      w=num(1.4, 0.2, 10, "width (x)"), d=num(1.8, 0.2, 10, "depth (y)"), content=choice("text", SCREEN_KINDS, "what it shows"),
      material=material("paper"))
def p_sheet(b):
    p = b.p
    w, d = p["w"], p["d"]
    part = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, 0.03, b.mat(p["material"]), lip=None)
    pl = top_plane(-w / 2, -d / 2, 0.03)
    part.els += screen_content(pl, 0.0, 0.0, w, d, p["content"], b.t)


@prop("screen", "Primitives", "A bare display panel, standing, with a dark bezel and light content.",
      w=num(2.2, 0.4, 8, "width"), h=num(1.4, 0.3, 6, "height"), content=choice("log", SCREEN_KINDS, "what it shows"),
      dark=flag(False, "a dark screen with light content"), lift=num(0, 0, 4, "bottom edge height (a floating screen)"))
def p_screen(b):
    p = b.p
    w, h, z0 = p["w"], p["h"], p["lift"]
    part = b.box(-w / 2, -0.06, z0, w / 2, 0.06, z0 + h, P.M["ink"], lip=None)
    pl = front_plane(-w / 2, w / 2, z0, -0.06)
    bez = 0.09
    part.els.append(pl.shape(rrect(bez, bez, w - bez, h - bez, 0.04), fill=P.SUB1 if p["dark"] else "#f7f8fa", body=False))
    part.els += screen_content(pl, bez, bez, w - bez, h - bez, p["content"], b.t, dark=p["dark"])
    b.lift = z0


@prop("glass_box", "Primitives", "An empty glass case (to put things in glass use enclosure).",
      tints=("neutral", "tee", "data", "agents", "models"), tint="tee",
      w=num(2, 0.3, 12, "width"), d=num(1.6, 0.3, 12, "depth"), h=num(1.4, 0.2, 8, "height"))
def p_glass_box(b):
    p = b.p
    w, d, h = p["w"], p["d"], p["h"]
    fill = b.t.accent if b.tint != "neutral" else "#9aa6b5"
    edge = b.t.accent if b.tint != "neutral" else P.MUTE
    box = (-w / 2, -d / 2, 0, w / 2, d / 2, h)
    b.add([Glass(box, "back", fill, edge), Glass(box, "front", fill, edge)])
    b.shadow = False


@prop("enclosure", "Structure", "A glass enclosure around a group of props (an enclave, a sandbox, a TEE). "
      "Put the props inside it in its own 'items' list; they must fit inside the glass.",
      tints=("tee", "neutral", "data", "agents", "models"), tint="tee", container=True,
      w=num(4, 0.5, 16, "width (x)"), d=num(3, 0.5, 16, "depth (y)"), h=num(2.4, 0.3, 10, "height"),
      wash=flag(True, "a tinted floor inside the glass"))
def p_enclosure(b):
    p = b.p
    w, d, h = p["w"], p["d"], p["h"]
    fill = b.t.accent if b.tint != "neutral" else "#9aa6b5"
    edge = b.t.accent if b.tint != "neutral" else P.MUTE
    box = (-w / 2, -d / 2, 0, w / 2, d / 2, h)
    fl = b.t.wash if p["wash"] else None
    b.add([Glass(box, "back", fill, edge, floor=fl, fop=0.07), Glass(box, "front", fill, edge, fop=0.07)])
    b.glassbox = box
    b.shadow = False


@prop("plate", "Structure", "A raised platform on the ground, like the hero's plates (a second level, a TEE base).",
      tints=("neutral", "tee", "dark"), w=num(4, 0.5, 16, "width (x)"), d=num(3, 0.5, 16, "depth (y)"),
      h=num(0.25, 0.05, 2, "thickness"))
def p_plate(b):
    p = b.p
    w, d, h = p["w"], p["d"], p["h"]
    if b.tint == "tee":
        m, edge = P.M["tplate"], P.TPLATE_EDGE
    elif b.tint == "dark":
        m, edge = P.M["dark"], P.SUB2
    else:
        m, edge = P.M["plate"], P.PLATE_EDGE
    part = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, h, m)
    for e in part.els:
        if getattr(e, "n", None) is not None and e.n[2] > 0.5:
            e.st["stroke"] = edge
            e.st["sw"] = 0.8
            e.st.pop("seam", None)
    b.surface = h


@prop("zone", "Structure", "A painted area on the floor with a dashed edge: a boundary, a region, a trust zone.",
      tints=("tee", "data", "neutral", "seal") + LAYER_TINTS, tint="tee", floor=True,
      w=num(4, 0.4, 20, "width (x)"), d=num(3, 0.4, 20, "depth (y)"), dashed=flag(True, "a dashed edge (else solid)"),
      fill=flag(True, "a light wash inside"))
def p_zone(b):
    p = b.p
    w, d = p["w"], p["d"]
    pl = top_plane(0, 0, 0.004)
    els = []
    if p["fill"]:
        els.append(pl.shape(rrect(-w / 2, -d / 2, w / 2, d / 2, 0.25), fill=b.t.wash, fop=0.85))
    st = {"stroke": b.t.accent, "swu": 0.05, "cap": "round"}
    if p["dashed"]:
        st["dash"] = "7 5"
        st["cap"] = "butt"
    els.append(pl.path(rrect(-w / 2, -d / 2, w / 2, d / 2, 0.25), **st))
    els[0].body = True
    b.add(els)
    b.shadow = False
    b.outline = False


LAMP_WARN = "#e2b93b"   # a device's warning lamp: the sign's yellow


# ======================================================================= hardware
@prop("chip", "Hardware", "A processor package on a green substrate, with a metal lid or a bare die; enclave marks the "
      "protected region in indigo.", tints=CORE, tint="neutral",
      size=num(2, 0.6, 6, "side of the substrate"), lid=choice("metal", ("metal", "die"), "a metal lid or a bare die"),
      enclave=flag(False, "an indigo die and a dashed boundary: a TEE inside the chip"),
      lock=flag(False, "a small padlock mark on the lid"), pins=flag(True, "gold contacts along two edges"),
      boundary=flag(True, "with enclave: the dashed indigo ring on the substrate"))
def p_chip(b):
    p = b.p
    s = p["size"]
    hs = s / 2
    sub = b.box(-hs, -hs, 0, hs, hs, 0.12, P.M["pcb"], lip=None)
    tee = p["enclave"] or b.tint == "tee"
    if p["pins"]:
        pl = top_plane(-hs, -hs, 0.12)
        n = max(4, int(s * 4))
        for i in range(n):
            u = s * (0.12 + 0.76 * i / (n - 1))
            sub.els.append(pl.shape(rect(u - s * 0.025, s * 0.03, u + s * 0.025, s * 0.075), fill=P.GOLD, body=False))
            sub.els.append(pl.shape(rect(s - s * 0.075, u - s * 0.025, s - s * 0.03, u + s * 0.025), fill=P.GOLD, body=False))
    if tee and p["boundary"]:
        pl = top_plane(-hs, -hs, 0.121)
        sub.els.append(pl.path(rrect(s * 0.12, s * 0.12, s * 0.88, s * 0.88, s * 0.04), stroke=P.TEE_RULE, swu=0.045,
                               dash="6 4", cap="butt"))
    li = s * 0.3
    if p["lid"] == "metal":
        lm = P.M["teelight"] if tee else P.M["steel"].lighter(0.35)
        lid = b.box(-li, -li, 0.12, li, li, 0.26, lm)
        if p["lock"] or tee:
            pl = top_plane(-li, -li, 0.26)
            lid.els += _flat_lock(pl, li, li, li * 0.7, P.TEE2 if tee else P.INK2)
    else:
        dm = P.M["tee"] if tee else P.M["die"]
        die = b.box(-li, -li, 0.12, li, li, 0.22, dm, lip=None)
        pl = top_plane(-li, -li, 0.22)
        for i in range(1, 4):
            die.els.append(pl.line([(2 * li * i / 4, 0.04), (2 * li * i / 4, 2 * li - 0.04)], stroke=P.GRID if not tee else "#aab2ea",
                                   swu=0.025, sop=0.7))
            die.els.append(pl.line([(0.04, 2 * li * i / 4), (2 * li - 0.04, 2 * li * i / 4)], stroke=P.GRID if not tee else "#aab2ea",
                                   swu=0.025, sop=0.7))
        if tee:
            die.els.insert(0, Glow((0, 0, 0.22), li * 1.6, P.GLOW, 0.35, ry=li * 0.9))
        if p["lock"]:
            die.els += _flat_lock(pl, li, li, li * 0.7, "#ffffff")
    b.surface = 0.26
    b.anchors["die"] = (0, 0, 0.26)


def _flat_lock(pl, cu, cv, s, color):
    """A padlock lying flat on a top plane (drawn in the plane's own u, v)."""
    return [pl.path(arc2(cu, cv + s * 0.1, s * 0.26, 0, 180), stroke=color, swu=s * 0.11, cap="butt"),
            pl.shape(rrect(cu - s * 0.38, cv - s * 0.42, cu + s * 0.38, cv + s * 0.12, s * 0.06), fill=color, body=False)]


@prop("gpu", "Hardware", "An accelerator package as on the hero: a die ringed by memory (HBM) stacks on an interposer. "
      "Tint tee draws the confidential-computing boundary.", tints=CORE, tint="neutral",
      size=num(2.6, 1, 6, "side of the substrate"), hbm=choice("4", ("2", "4", "6"), "memory stacks (as a string)"))
def p_gpu(b):
    p = b.p
    s = p["size"]
    hs = s / 2
    tee = b.tint == "tee"
    sub = b.box(-hs, -hs, 0, hs, hs, 0.12, P.M["pcb"], lip=None)
    if tee:
        pl = top_plane(-hs, -hs, 0.121)
        sub.els.append(pl.path(rrect(s * 0.06, s * 0.06, s * 0.94, s * 0.94, s * 0.04), stroke="#aab2ea", swu=0.05,
                               dash="7 5", cap="butt"))
    ip = s * 0.4
    b.box(-ip, -ip, 0.12, ip, ip, 0.2, P.M["int"], lip=None)
    dw, dd = s * 0.15, s * 0.22
    die = b.box(-dw, -dd, 0.2, dw, dd, 0.3, P.M["tee"] if tee else P.M["die"], lip=None)
    pl = top_plane(-dw, -dd, 0.3)
    for i in range(1, 3):
        die.els.append(pl.line([(2 * dw * i / 3, 0.04), (2 * dw * i / 3, 2 * dd - 0.04)], stroke=P.GRID, swu=0.025, sop=0.7))
    for i in range(1, 4):
        die.els.append(pl.line([(0.04, 2 * dd * i / 4), (2 * dw - 0.04, 2 * dd * i / 4)], stroke=P.GRID, swu=0.025, sop=0.7))
    if tee:
        die.els.insert(0, Glow((0, 0, 0.3), dw * 2.4, P.GLOW, 0.4, ry=dw * 1.3))
    per = int(p["hbm"]) // 2
    gap = 0.06
    span = 2 * ip - 0.16
    sh = (span - gap * (per - 1)) / per
    for side in (-1, 1):
        x0 = side * (dw + 0.08) if side > 0 else -(ip - 0.06)
        x1 = (ip - 0.06) if side > 0 else -(dw + 0.08)
        for j in range(per):
            y0 = -ip + 0.08 + j * (sh + gap)
            part = b.box(x0, y0, 0.2, x1, y0 + sh, 0.44, P.M["hbm"])
            fp = front_plane(x0, x1, 0.2, y0)
            rp = right_plane(y0, y0 + sh, 0.2, x1)
            for k in range(1, 4):
                v = 0.24 * k / 4
                part.els.append(fp.line([(0, v), (x1 - x0, v)], stroke=P.HBMS, swu=0.018))
                part.els.append(rp.line([(0, v), (sh, v)], stroke=P.HBMS, swu=0.018))
    b.surface = 0.3
    b.anchors["die"] = (0, 0, 0.3)


@prop("gpu_card", "Hardware", "A graphics card standing on its edge: shroud, two fans, gold fingers.",
      tints=("neutral", "tee", "dark"), tint="dark", length=num(3.2, 1.6, 6, "length (x)"))
def p_gpu_card(b):
    p = b.p
    L = p["length"]
    hL = L / 2
    shroud = P.M["dark"] if b.tint != "neutral" else P.M["steel"]
    pcb = b.box(-hL, 0.12, 0.1, hL, 0.18, 1.2, P.M["pcb"], lip=None)
    sh = b.box(-hL + 0.05, -0.2, 0.18, hL - 0.25, 0.12, 1.18, shroud, lip="#5d646d" if shroud.name == "dark" else P.LIP)
    fp = front_plane(-hL + 0.05, hL - 0.25, 0.18, -0.2)
    fw = L - 0.3
    for cu in (fw * 0.27, fw * 0.72):
        sh.els.append(fp.shape(circle2(cu, 0.5, 0.4), fill="#1d2025" if shroud.name == "dark" else "#8d949d", body=False))
        for k in range(6):
            a = math.radians(k * 60 + 15)
            sh.els.append(fp.path(arc2(cu, 0.5, 0.2, k * 60, k * 60 + 40), stroke="#454b53" if shroud.name == "dark" else "#bfc5cd",
                                  swu=0.07, cap="round"))
        sh.els.append(fp.shape(circle2(cu, 0.5, 0.1), fill=b.t.accent if b.tint == "tee" else "#5b626c", body=False))
    sh.els.append(fp.line([(0.15, 0.93), (fw - 0.2, 0.93)], stroke=P.TEE2 if b.tint == "tee" else "#5b626c", swu=0.05))
    b.box(-hL - 0.04, -0.2, 0.0, -hL + 0.03, 0.2, 1.25, P.M["steel"], lip=None)
    b.box(-hL + 0.6, 0.11, 0.0, hL - 0.9, 0.19, 0.1, P.M["gold"], lip=None)
    b.surface = 1.2


@prop("dimm", "Hardware", "Memory modules (DIMMs) standing in their slots, in a row from front to back.",
      tints=("neutral",), count=integer(2, 1, 6, "how many modules"), slot=flag(True, "draw the slots"),
      length=num(2.6, 1.2, 4, "module length (x)"), spacing=num(0.55, 0.3, 1.5, "distance between modules (y)"))
def p_dimm(b):
    p = b.p
    n, L, sp = p["count"], p["length"], p["spacing"]
    y0 = -(n - 1) * sp / 2
    for i in range(n):
        y = y0 + i * sp
        _dimm(b, -L / 2, y, L, slot=p["slot"], z=0.0)
    b.anchors["front"] = (0, y0 - 0.1, 0.4)


def _dimm(b, x0, y, L, slot=True, z=0.0, raise_by=0.0):
    if slot:
        b.box(x0 - 0.15, y - 0.11, z, x0 + L + 0.15, y + 0.11, z + 0.16, P.M["ink"], lip=None)
        for xe in (x0 - 0.15, x0 + L + 0.03):
            b.box(xe, y - 0.12, z + 0.16, xe + 0.12, y + 0.12, z + 0.32, P.M["soft"], lip=None)
    zb = z + 0.1 + raise_by
    mod = b.box(x0, y - 0.035, zb, x0 + L, y + 0.035, zb + 0.75, P.M["pcb"], lip=None)
    fp = front_plane(x0, x0 + L, zb, y - 0.035)
    nchip = 4 if L >= 2 else 3
    cw = L / (nchip * 1.45)
    for k in range(nchip):
        u = L * (k + 0.5) / nchip
        mod.els.append(fp.shape(rect(u - cw / 2, 0.2, u + cw / 2, 0.58), fill=P.SUB1, body=False))
        mod.els.append(fp.shape(rect(u - cw / 2, 0.55, u + cw / 2, 0.58), fill="#4a5058", body=False))
    mod.els.append(fp.shape(rect(0.12, 0.0, L - 0.12, 0.1), fill=P.GOLD, body=False))
    for k in range(1, 12):
        u = 0.12 + (L - 0.24) * k / 12
        mod.els.append(fp.line([(u, 0.0), (u, 0.1)], stroke="#9c7d18", swu=0.012))
    return mod


@prop("interposer", "Hardware", "A memory interposer: a module raised high on a gray adapter board in its slot, with a "
      "ribbon cable from the adapter to a small controller box (a DDRop-style probe).", tints=("dark", "data", "neutral"),
      tint="dark", length=num(2.6, 1.2, 4, "module length (x)"), cable=num(1.2, 0.5, 4, "cable length to the box (toward the front)"),
      lamp=flag(True, "a small yellow lamp on the controller box"))
def p_interposer(b):
    p = b.p
    L = p["length"]
    x0 = -L / 2
    b.box(x0 - 0.15, -0.11, 0, x0 + L + 0.15, 0.11, 0.16, P.M["ink"], lip=None)
    for xe in (x0 - 0.15, x0 + L + 0.03):
        b.box(xe, -0.12, 0.16, xe + 0.12, 0.12, 0.32, P.M["soft"], lip=None)
    rm = P.M["int"] if b.tint != "data" else P.M["data"]
    zr0, zr1 = 0.1, 0.72
    riser = b.box(x0 - 0.05, -0.08, zr0, x0 + L + 0.05, 0.08, zr1, rm, lip="#8d949d")
    rp = front_plane(x0 - 0.05, x0 + L + 0.05, zr0, -0.08)
    for k in range(3):
        u = (L + 0.1) * (0.18 + 0.24 * k)
        riser.els.append(rp.shape(rect(u - 0.17, 0.2, u + 0.17, 0.46), fill=P.SUB2, body=False))
    riser.els.append(rp.line([(0.1, 0.54), (L, 0.54)], stroke=P.GOLD, swu=0.035))
    _dimm(b, x0, 0.0, L, slot=False, z=0.0, raise_by=zr1 - 0.12)
    # the cable: a plug on the adapter's front face, a drop to the base, then flat to the box
    cx = x0 + L * 0.82
    cl = p["cable"]
    by = -0.45 - cl
    zp = (zr0 + 0.16 + zr1) / 2
    b.box(cx - 0.2, -0.17, zp - 0.1, cx + 0.2, -0.08, zp + 0.1, P.M["dark"], lip=None)
    rib = P.Mat("#8d949d", "#6f767e", "#5f6770", None, "ribbon")
    b.add([poly([(cx - 0.16, -0.45, 0.012), (cx + 0.16, -0.45, 0.012), (cx + 0.16, -0.17, zp - 0.06), (cx - 0.16, -0.17, zp - 0.06)],
                 fill=rib, seam=True)])
    flat = b.add([poly([(cx - 0.16, by + 0.3, 0.012), (cx + 0.16, by + 0.3, 0.012), (cx + 0.16, -0.45, 0.012), (cx - 0.16, -0.45, 0.012)],
                       n=(0, 0, 1), fill=rib, seam=True)])
    tp = top_plane(cx - 0.16, by + 0.3, 0.013)
    for k in range(1, 5):
        flat.els.append(tp.line([(0.32 * k / 5, 0), (0.32 * k / 5, -0.45 - by - 0.3)], stroke="#a3abb4", swu=0.014))
    dm = P.M["dark"] if b.tint in ("dark", "neutral") else b.t.solid
    box = b.box(cx - 0.5, by - 0.4, 0, cx + 0.5, by + 0.3, 0.34, dm, lip="#5d646d")
    fp = front_plane(cx - 0.5, cx + 0.5, 0, by - 0.4)
    box.els.append(fp.line([(0.16, 0.2), (0.5, 0.2)], stroke="#5d646d", swu=0.04))
    if p["lamp"]:
        # a device's lamp: a small dot with no halo, in the warning yellow (orange is the reader's data)
        box.els.append(fp.shape(circle2(0.78, 0.2, 0.05), fill=LAMP_WARN, body=False))
    b.anchors["slot"] = (0, 0, 0)
    b.port = "slot"
    b.anchors["device"] = (cx, by - 0.05, 0.34)
    b.anchors["module"] = (0, 0, zr1 - 0.12 + 0.1 + 0.75)
    b.anchors["adapter"] = (0, -0.08, (zr0 + zr1) / 2)


@prop("server_rack", "Hardware", "A rack cabinet with stacked servers and their lamps. Tint tee: indigo lamps and trim, "
      "for confidential computing.", tints=CORE, tint="neutral",
      units=integer(6, 2, 10, "servers in the rack"), w=num(1.6, 1, 3, "width"), d=num(1.3, 0.8, 3, "depth"))
def p_server_rack(b):
    p = b.p
    n, w, d = p["units"], p["w"], p["d"]
    uh = 0.38
    h = n * uh + 0.34
    tee = b.tint == "tee"
    body = P.M["teelight"] if tee else (P.M["dark"] if b.tint == "dark" else P.M["metal"])
    part = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, h, body)
    fp = front_plane(-w / 2, w / 2, 0, -d / 2)
    fw = w
    part.els.append(fp.shape(rect(0.1, 0.12, fw - 0.1, h - 0.14), fill=P.SRV1, body=False))
    lamp = P.LED if tee else (P.DATA if b.tint == "data" else ("#e07767" if b.tint == "seal" else "#aeb5be"))
    for i in range(n):
        v0 = 0.17 + i * uh
        part.els.append(fp.shape(rect(0.16, v0, fw - 0.16, v0 + uh - 0.07), fill="#4a5159", body=False))
        nb = 5
        for k in range(nb):
            u = 0.24 + k * (fw - 0.66) / nb
            part.els.append(fp.shape(rect(u, v0 + 0.08, u + (fw - 0.66) / nb - 0.05, v0 + uh - 0.15), fill="#5f6770", body=False))
        part.els.append(fp.shape(circle2(fw - 0.27, v0 + uh * 0.42, 0.045), fill=lamp, body=False))
    if tee:
        part.els.append(fp.line([(0.1, h - 0.07), (fw - 0.1, h - 0.07)], stroke=P.TEE2, swu=0.06))
    rp = right_plane(-d / 2, d / 2, 0, w / 2)
    for k in (1, 2):
        part.els.append(rp.line([(d * k / 3, 0.25), (d * k / 3, h - 0.25)], stroke=body.right if body.name != "metal" else "#b6bcc4",
                                swu=0.03))
    tp = top_plane(-w / 2, -d / 2, h)
    for k in range(1, 4):
        part.els.append(tp.line([(0.25, d * k / 4), (w - 0.25, d * k / 4)], stroke=body.left, swu=0.035))
    b.anchors["front"] = (0, -d / 2, h * 0.5)
    b.anchors["lamp"] = (fw / 2 - 0.27, -d / 2, 0.17 + uh * 1.42)


@prop("server", "Hardware", "One server lying flat: a wide chassis with drive bays and lamps on its front.",
      tints=CORE, tint="neutral", w=num(3, 1.2, 6, "width (x)"), d=num(1.6, 0.8, 4, "depth"),
      lock=flag(False, "a small indigo padlock on the front"))
def p_server(b):
    p = b.p
    w, d, h = p["w"], p["d"], 0.5
    tee = b.tint == "tee"
    body = P.M["teelight"] if tee else P.M["metal"]
    part = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, h, body)
    fp = front_plane(-w / 2, w / 2, 0, -d / 2)
    part.els.append(fp.shape(rect(0.08, 0.07, w - 0.08, h - 0.07), fill=P.SRV1, body=False))
    nb = max(4, int(w * 2.6))
    bw = (w - 0.75) / nb
    for k in range(nb):
        u = 0.16 + k * bw
        for r in (0, 1):
            part.els.append(fp.shape(rect(u, 0.12 + r * 0.14, u + bw - 0.05, 0.22 + r * 0.14), fill=P.BAY, body=False))
    lamp = P.LED if tee else (P.DATA if b.tint == "data" else "#aeb5be")
    for r in range(3):
        part.els.append(fp.shape(circle2(w - 0.3, 0.13 + r * 0.11, 0.04), fill=lamp, body=False))
    if p["lock"] or tee:
        part.els += lock_glyph(fp, w - 0.48, 0.25, 0.26, P.TEE2 if tee else P.INK2, hole=P.SRV1)
    tp = top_plane(-w / 2, -d / 2, h)
    for k in range(1, 6):
        part.els.append(tp.line([(w * 0.55, d * k / 6), (w - 0.25, d * k / 6)], stroke=body.left, swu=0.03))
    b.anchors["front"] = (0, -d / 2, h * 0.5)


@prop("database", "Hardware", "A database: stacked discs, as on the hero's model layer.",
      tints=("neutral", "tee", "data") + LAYER_TINTS, tiers=integer(3, 1, 5, "discs"), r=num(0.8, 0.3, 2, "radius"))
def p_database(b):
    p = b.p
    r = p["r"]
    th = r * 0.42
    m = P.Mat("#f2f4f6", "#dde1e6", "#c3c9d0", None, "dbn") if b.tint == "neutral" else b.t.solid
    rim = "#ffffff" if b.tint == "neutral" else b.t.light.top
    for i in range(p["tiers"]):
        z0 = i * (th + r * 0.07)
        b.cyl(0, 0, z0, z0 + th, r, m, rim=rim, rw=1.2)
    b.anchors["top"] = (0, 0, p["tiers"] * (th + r * 0.07))


@prop("cloud", "Hardware", "A cloud, standing like a cut-out with some depth: a cloud service. Use a height in 'at' to "
      "float it.", tints=("neutral", "tee", "data") + LAYER_TINTS, w=num(2.6, 1, 6, "width"))
def p_cloud(b):
    p = b.p
    w = p["w"]
    k = w / 2.6
    pl = front_plane(0, 0, 0, -0.2 * k)
    pieces = [circle2(-0.62 * k, 0.5 * k, 0.48 * k), circle2(0.05 * k, 0.78 * k, 0.68 * k), circle2(0.72 * k, 0.48 * k, 0.5 * k),
              rrect(-1.1 * k, 0.02 * k, 1.22 * k, 0.6 * k, 0.3 * k)]
    front = P.SOFT if b.tint == "neutral" else b.t.light.top
    side = P.SOFT2 if b.tint == "neutral" else b.t.light.right
    part = b.extrude(pl, pieces, 0.4 * k, front, side=side)
    part.els.append(pl.path(arc2(0.05 * k, 0.78 * k, 0.5 * k, 105, 160), stroke="#ffffff", swu=0.07 * k, cap="round"))
    b.anchors["center"] = (0, 0, 0.6 * k)


# ======================================================================= devices
@prop("monitor", "Devices", "A desktop monitor on a stand, with abstract content on its screen.",
      w=num(2.6, 1.2, 6, "screen width"), h=num(1.65, 0.8, 4, "screen height"),
      content=choice("chart", SCREEN_KINDS, "what the screen shows"), dark=flag(False, "a dark screen"))
def p_monitor(b):
    p = b.p
    w, h = p["w"], p["h"]
    z0 = 0.42
    b.box(-0.5, -0.25, 0, 0.5, 0.35, 0.06, P.M["steel"])
    b.box(-0.1, 0.07, 0.06, 0.1, 0.2, z0 + 0.3, P.M["steel"], lip=None)
    part = b.box(-w / 2, -0.06, z0, w / 2, 0.07, z0 + h, P.M["ink"], lip="#5d646d")
    pl = front_plane(-w / 2, w / 2, z0, -0.06)
    bez = 0.08
    part.els.append(pl.shape(rect(bez, bez + 0.04, w - bez, h - bez), fill=P.SUB1 if p["dark"] else "#f7f8fa", body=False))
    part.els += screen_content(pl, bez, bez + 0.04, w - bez, h - bez, p["content"], b.t, dark=p["dark"])
    b.anchors["screen"] = (0, -0.07, z0 + h / 2)


@prop("laptop", "Devices", "An open laptop, its screen tilted back.",
      w=num(2.2, 1, 4, "width"), content=choice("code", SCREEN_KINDS, "what the screen shows"), dark=flag(False, "a dark screen"))
def p_laptop(b):
    p = b.p
    w = p["w"]
    d = w * 0.68
    base = b.box(-w / 2, -d / 2, 0, w / 2, d / 2, 0.08, P.M["metal"])
    tp = top_plane(-w / 2, -d / 2, 0.08)
    base.els.append(tp.shape(rrect(w * 0.08, d * 0.42, w * 0.92, d * 0.92, 0.04), fill="#cdd2d9", body=False))
    for r in range(4):
        for c in range(10):
            u = w * (0.1 + c * 0.08)
            v = d * (0.47 + r * 0.11)
            base.els.append(tp.shape(rect(u, v, u + w * 0.065, v + d * 0.08), fill="#f3f4f6", body=False))
    base.els.append(tp.shape(rrect(w * 0.36, d * 0.08, w * 0.64, d * 0.34, 0.03), fill="#e3e6ea", body=False))
    sh = w * 0.62
    ang = math.radians(14)
    sa, ca = math.sin(ang), math.cos(ang)
    o = (-w / 2, d / 2 - 0.02, 0.08)
    ey = (0.0, sa * sh, ca * sh)
    ez = (0.0, -ca * 0.06, sa * 0.06)
    lid = b.obox(o, (w, 0.0, 0.0), ey, ez, P.M["ink"])
    pl = Plane((o[0], o[1] + ez[1], o[2] + ez[2]), (1.0, 0.0, 0.0), (0.0, sa, ca))
    bez = 0.07
    lid.els.append(pl.shape(rect(bez, bez + 0.03, w - bez, sh - bez), fill=P.SUB1 if p["dark"] else "#f7f8fa", body=False))
    lid.els += screen_content(pl, bez, bez + 0.03, w - bez, sh - bez, p["content"], b.t, dark=p["dark"])
    b.anchors["screen"] = (0, d / 2 - 0.1, 0.08 + sh / 2)


@prop("phone", "Devices", "A smartphone standing upright, its screen toward the front.",
      content=choice("chat", SCREEN_KINDS, "what the screen shows"), h=num(1.5, 0.6, 3, "height"),
      dark=flag(False, "a dark screen"))
def p_phone(b):
    p = b.p
    h = p["h"]
    w = h * 0.5
    pl = front_plane(-w / 2, w / 2, 0, -0.06)
    els = b.extrude_els(pl, [rrect(0, 0, w, h, w * 0.14)], 0.12, P.SRV1, side="#1e2226")
    els.append(pl.shape(rrect(w * 0.07, h * 0.05, w * 0.93, h * 0.95, w * 0.09), fill=P.SUB1 if p["dark"] else "#f7f8fa", body=False))
    els.append(pl.shape(rrect(w * 0.38, h * 0.9, w * 0.62, h * 0.925, h * 0.01), fill=P.SRV1, body=False))
    els += screen_content(pl, w * 0.1, h * 0.1, w * 0.9, h * 0.86, p["content"], b.t, dark=p["dark"])
    b.add(els)
    b.anchors["screen"] = (0, -0.07, h / 2)


@prop("glasses", "Devices", "Smart glasses resting on their frame and temples, lenses toward the front, with a small "
      "camera at one hinge. Tint tee tints the lenses indigo.", tints=("neutral", "tee", "data", "dark"), tint="neutral",
      w=num(1.7, 1, 4, "frame width"))
def p_glasses(b):
    p = b.p
    k = p["w"] / 2.2
    w = 2.2 * k
    lw, lh = 0.86 * k, 0.6 * k
    rim = 0.08 * k
    zc = lh / 2 + rim                      # the frame's bottom rests on the base
    temple = P.Mat("#6a7280", "#5b626c", "#454b53", None, "temple")
    # temples first (behind the frame): from the hinges back and down to the base
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.06 * k)
        tz = zc + 0.1 * k
        L = 1.45 * k
        b.obox((x - 0.035 * k, 0.03 * k, tz), (0.07 * k, 0, 0), (0, L, -tz), (0, 0, 0.07 * k), temple)
    pl = front_plane(0, 0, 0, -0.03 * k)
    pieces = [rrect(-w / 2, 0, -0.08 * k, zc + lh / 2 + rim, 0.2 * k),
              rrect(0.08 * k, 0, w / 2, zc + lh / 2 + rim, 0.2 * k),
              rect(-0.2 * k, zc + 0.05 * k, 0.2 * k, zc + 0.2 * k)]
    els = b.extrude_els(pl, pieces, 0.06 * k, "#5b626c", side="#454b53")
    tee = b.tint == "tee"
    lens = "#c9cdf0" if tee else ("#ffe2bd" if b.tint == "data" else "#dfe5ec")
    lens2 = "#aab2ea" if tee else ("#f6c48a" if b.tint == "data" else "#c5ced9")
    for sx in (-1, 1):
        cu = sx * (w / 4 + 0.04 * k)
        els.append(pl.shape(rrect(cu - lw / 2, zc - lh / 2, cu + lw / 2, zc + lh / 2, 0.15 * k), fill=lens, body=False))
        els.append(pl.shape([("M", cu - lw / 2 + 0.05 * k, zc - lh / 2 + 0.05 * k), ("L", cu + lw * 0.05, zc + lh / 2 - 0.02 * k),
                             ("L", cu + lw * 0.3, zc + lh / 2 - 0.02 * k), ("L", cu - lw * 0.1, zc - lh / 2 + 0.03 * k), ("Z",)],
                            fill=lens2, body=False, op=0.55))
    # camera at the left hinge, lamp at the right
    cz = zc + lh / 2 - 0.02 * k
    els.append(pl.shape(circle2(-w / 2 + 0.17 * k, cz, 0.075 * k), fill=P.INK2, body=False))
    els.append(pl.shape(circle2(-w / 2 + 0.17 * k, cz, 0.04 * k), fill="#0f1113", body=False))
    els.append(pl.shape(circle2(w / 2 - 0.17 * k, cz, 0.04 * k), fill=P.LED if tee else (P.DATA_GLOW if b.tint == "data" else P.SOFT),
                        body=False))
    b.add(els)
    b.anchors["lens"] = (-w / 4, -0.04 * k, zc)
    b.anchors["camera"] = (-w / 2 + 0.17 * k, -0.04 * k, cz)
    b.port = "camera"
    b.footprint = (-w / 2, -0.05 * k, w / 2, 1.5 * k)


@prop("packet", "Devices", "A small data packet (a cube), for data in transit; ghost draws a dashed outline only (data "
      "that went missing). Links can also carry packets.",
      tints=("data", "tee", "seal", "neutral"), tint="data", size=num(0.3, 0.1, 1, "edge"), glow=flag(False, "a soft glow"),
      ghost=flag(False, "only a dashed outline: a lost or dropped packet"))
def p_packet(b):
    p = b.p
    s = p["size"]
    h = s / 2
    els = []
    if p["ghost"]:
        c = b.t.accent
        P_ = [(-h, -h, 0), (h, -h, 0), (h, h, 0), (h, h, s), (-h, h, s), (-h, -h, s)]
        hexa = poly(P_, n=(0, 0, 1), cull=False, fill=b.t.wash, fop=0.6, stroke=c, swu=0.035, dash="3 2.5", join="round")
        els.append(hexa)
        els.append(line([(-h, -h, s), (h, -h, s), (h, h, s)], stroke=c, swu=0.035, dash="3 2.5"))
        els.append(line([(h, -h, s), (h, -h, 0)], stroke=c, swu=0.035, dash="3 2.5"))
        b.add(els)
        b.shadow = False
        return
    if p["glow"]:
        els.append(Glow((0, 0, s / 2), s * 1.6, b.t.glow, 0.55))
    from .iso import box_els
    els += box_els(-h, -h, 0, h, h, s, b.t.solid, lip="#ffffff")
    b.add(els)


# ======================================================================= documents
@prop("document", "Documents", "A page with lines of writing (never words), standing or lying, with an optional seal "
      "or signature: a report, a policy, a paper.", tints=("neutral", "tee", "seal", "data") + LAYER_TINTS,
      pose=choice("standing", ("standing", "lying"), "standing on its edge or lying flat"),
      w=num(1.25, 0.5, 3, "width"), h=num(1.65, 0.6, 4, "height (length when lying)"),
      header=flag(True, "a colored bar at the top (the tint's accent)"),
      seal=choice("none", ("none", "seal", "tee", "ring"), "seal: cinnabar seal; tee: indigo ring (an attestation); ring: tint ring"),
      signature=flag(False, "a signature stroke at the bottom"), lines=integer(6, 0, 10, "lines of writing"))
def p_document(b):
    p = b.p
    w, h = p["w"], p["h"]
    if p["pose"] == "standing":
        part = b.box(-w / 2, -0.03, 0, w / 2, 0.03, h, P.M["paper"])
        pl = front_plane(-w / 2, w / 2, 0, -0.03)
    else:
        part = b.box(-w / 2, -h / 2, 0, w / 2, h / 2, 0.035, P.M["paper"], lip=None)
        pl = top_plane(-w / 2, -h / 2, 0.035)
    part.els += _page(pl, w, h, p, b.t)
    b.anchors["seal"] = (w * 0.25, -0.04, h * 0.2) if p["pose"] == "standing" else (w * 0.25, 0, 0.04)


def _page(pl, w, h, p, t):
    els = []
    acc = t.accent if t.name != "neutral" else P.INK2
    v = h - h * 0.13
    if p.get("header", True):
        els.append(pl.line([(w * 0.14, v), (w * 0.52, v)], stroke=acc, swu=h * 0.05, cap="round"))
        v -= h * 0.12
    n = p.get("lines", 6)
    lens = (0.72, 0.64, 0.7, 0.5, 0.68, 0.58, 0.66, 0.44, 0.6, 0.52)
    seal = p.get("seal", "none")
    bottom = h * (0.36 if seal != "none" or p.get("signature") else 0.14)
    step = (v - bottom) / max(1, n) if n else 0
    for i in range(n):
        vv = v - step * (i + 0.5)
        right = lens[i % len(lens)]
        if seal != "none" and vv < h * 0.42:
            right = min(right, 0.42)
        els.append(tline(pl, w * 0.14, vv, w * (0.14 + right), P.SOFT2, w=min(h * 0.032, 0.06)))
    if p.get("signature"):
        sv = h * 0.2
        els.append(pl.path([("M", w * 0.14, sv), ("C", w * 0.2, sv + h * 0.08, w * 0.25, sv - h * 0.04, w * 0.3, sv + h * 0.02),
                            ("C", w * 0.34, sv + h * 0.07, w * 0.38, sv - h * 0.03, w * 0.46, sv + h * 0.03)],
                           stroke=P.INK2, swu=0.035, cap="round"))
    if seal != "none":
        cu, cv, r = w * 0.72, h * 0.2, min(w, h) * 0.13
        if seal == "seal":
            els.append(pl.shape(circle2(cu, cv, r), fill=P.SEAL, body=False))
            els.append(pl.path(circle2(cu, cv, r * 0.66), stroke=P.SEAL2, swu=r * 0.14))
        else:
            c = P.TEE2 if seal == "tee" else acc
            els.append(pl.path(circle2(cu, cv, r), stroke=c, swu=r * 0.22))
            els.append(pl.shape(circle2(cu, cv, r * 0.42), fill=c, body=False))
    return els


@prop("papers", "Documents", "A small stack of pages lying flat, the top one written on.",
      tints=("neutral", "tee", "seal") + LAYER_TINTS, count=integer(4, 2, 8, "pages"), w=num(1.3, 0.6, 3, "width"),
      d=num(1.7, 0.6, 3, "length"))
def p_papers(b):
    p = b.p
    w, d, n = p["w"], p["d"], p["count"]
    th = 0.045
    for i in range(n):
        off = 0.06 * ((i * 7) % 3 - 1)
        top = i == n - 1
        part = b.box(-w / 2 + off, -d / 2 - off * 0.5, i * th, w / 2 + off, d / 2 - off * 0.5, (i + 1) * th, P.M["paper"],
                     lip=None)
        for e in part.els:
            if getattr(e, "n", None) is not None and abs(e.n[2]) < 0.5:
                e.st["fill"] = P.M["paper"].darker(0.03) if i % 2 else P.M["paper"]
        if top:
            pl = top_plane(-w / 2 + off, -d / 2 - off * 0.5, (i + 1) * th)
            part.els += _page(pl, w, d, {"header": True, "lines": 6}, b.t)
    b.surface = n * th


@prop("certificate", "Documents", "A certificate or credential card standing on its edge, with a border, lines and a "
      "ribboned seal. Tint seal: a cinnabar seal; tee: an indigo attestation seal; other tints: a seal in that tint.", tints=("seal", "tee", "neutral") + LAYER_TINTS,
      tint="seal", w=num(2.1, 1, 4, "width"), h=num(1.45, 0.7, 3, "height"))
def p_certificate(b):
    p = b.p
    w, h = p["w"], p["h"]
    part = b.box(-w / 2, -0.04, 0, w / 2, 0.04, h, P.M["paper"])
    pl = front_plane(-w / 2, w / 2, 0, -0.04)
    acc = b.t.accent if b.tint != "seal" else P.MUTE
    part.els.append(pl.path(rect(0.1, 0.1, w - 0.1, h - 0.1), stroke=acc, swu=0.03, join="round"))
    part.els.append(pl.path(rect(0.15, 0.15, w - 0.15, h - 0.15), stroke=P.SOFT2, swu=0.02, join="round"))
    part.els.append(tline(pl, w * 0.3, h * 0.76, w * 0.7, P.INK2 if b.tint == "seal" else acc, w=0.075))
    for i, f in enumerate((0.58, 0.48, 0.38)):
        part.els.append(tline(pl, w * 0.2, h * (0.6 - i * 0.12), w * (0.2 + f), P.SOFT2, w=0.05))
    # the seal stands just in front, with two ribbon tails: cinnabar only with tint seal
    sc = P.M["seal"] if b.tint == "seal" else (b.t.solid if b.tint != "neutral" else P.M["steel"])
    cu, cv, r = w * 0.76, h * 0.3, h * 0.15
    sp = front_plane(-w / 2, w / 2, 0, -0.05)
    tails = [sp.shape(poly2([(cu - r * 0.55, cv - r * 0.3), (cu - r * 0.15, cv - r * 0.3), (cu - r * 0.3, cv - r * 1.8),
                              (cu - r * 0.55, cv - r * 1.45), (cu - r * 0.8, cv - r * 1.8)]), fill=sc.right, body=False),
             sp.shape(poly2([(cu + r * 0.15, cv - r * 0.3), (cu + r * 0.55, cv - r * 0.3), (cu + r * 0.8, cv - r * 1.8),
                              (cu + r * 0.55, cv - r * 1.45), (cu + r * 0.3, cv - r * 1.8)]), fill=sc.right, body=False)]
    seal = b.extrude_els(sp, [circle2(cu, cv, r)], 0.01, sc.left, side=sc.right)
    seal.append(sp.path(circle2(cu, cv, r * 0.68), stroke=P.SEAL2 if b.tint == "seal" else sc.top, swu=r * 0.12))
    part.els += tails + seal[1:]
    b.anchors["seal"] = (-w / 2 + cu, -0.06, cv)


@prop("book", "Documents", "A closed book lying flat (a rule book, a code of practice, a standard), optionally with a "
      "ribbon and an emblem on the cover.", tints=("neutral", "tee", "seal", "data") + LAYER_TINTS, tint="institutions",
      w=num(1.5, 0.6, 3, "width"), d=num(1.9, 0.8, 3, "length"), thick=num(0.32, 0.1, 1, "thickness"),
      emblem=choice("bars", ("none", "ring", "seal", "bars", "lock"), "the mark on the cover (seal: a cinnabar seal)"),
      ribbon=flag(True, "a ribbon bookmark in the cover's dark shade"))
def p_book(b):
    p = b.p
    w, d, th = p["w"], p["d"], p["thick"]
    cover = b.t.solid if b.tint != "neutral" else P.M["steel"]
    b.box(-w / 2, -d / 2, 0, w / 2, d / 2, 0.04, cover, lip=None)
    pages = b.box(-w / 2 + 0.04, -d / 2 + 0.05, 0.04, w / 2 - 0.06, d / 2 - 0.02, th - 0.04, P.M["paper"], lip=None)
    fp = front_plane(-w / 2 + 0.04, w / 2 - 0.06, 0.04, -d / 2 + 0.05)
    rp = right_plane(-d / 2 + 0.05, d / 2 - 0.02, 0.04, w / 2 - 0.06)
    for k in range(1, 4):
        v = (th - 0.08) * k / 4
        pages.els.append(fp.line([(0.03, v), (w - 0.13, v)], stroke=P.SOFT2, swu=0.012))
        pages.els.append(rp.line([(0.03, v), (d - 0.1, v)], stroke=P.SOFT2, swu=0.012))
    top = b.box(-w / 2, -d / 2, th - 0.04, w / 2, d / 2, th, cover, lip=b.t.light.top if b.tint != "neutral" else P.LIP)
    b.box(-w / 2 - 0.02, -d / 2, 0, -w / 2 + 0.05, d / 2, th, cover.darker(0.08), lip=None)
    tp = top_plane(-w / 2, -d / 2, th)
    accent = "#ffffff"
    cu, cv = w * 0.55, d * 0.55
    em = p["emblem"]
    if em == "ring":
        top.els.append(tp.path(circle2(cu, cv, w * 0.2), stroke=accent, swu=w * 0.04, sop=0.9))
        top.els.append(tp.shape(circle2(cu, cv, w * 0.07), fill=accent, body=False, op=0.9))
    elif em == "seal":
        top.els.append(tp.shape(circle2(cu, cv, w * 0.18), fill=P.SEAL, body=False))
        top.els.append(tp.path(circle2(cu, cv, w * 0.12), stroke=P.SEAL2, swu=0.025))
    elif em == "bars":
        for k in range(3):
            top.els.append(tline(tp, w * 0.3, d * (0.68 - k * 0.12), w * (0.8 - k * 0.1), accent, w=0.07))
    elif em == "lock":
        top.els += _flat_lock(tp, cu, cv, w * 0.4, accent)
    if p["ribbon"]:
        shade = cover.darker(0.18).right
        rp = front_plane(-w / 2, w / 2, 0, -d / 2 - 0.004)
        rb = b.add([rp.shape(poly2([(w * 0.66, th), (w * 0.76, th), (w * 0.76, -0.02), (w * 0.71, 0.05), (w * 0.66, -0.02)]),
                             fill=shade)])
        rb.els[0].body = False
        top.els.append(tp.line([(w * 0.71, 0.0), (w * 0.71, 0.18)], stroke=shade, swu=0.1, cap="butt"))
    b.surface = th


@prop("ledger", "Documents", "An append-only log: blocks joined in a row (or stacked), the newest one in the tint, "
      "for a transparency log or a public ledger.", tints=("tee", "data", "seal", "neutral") + LAYER_TINTS, tint="tee",
      count=integer(4, 2, 7, "blocks"), layout=choice("row", ("row", "stack"), "a row along x or a stack"),
      size=num(0.75, 0.3, 1.5, "block size"), pending=flag(True, "the newest block floats just above its place (being added)"))
def p_ledger(b):
    p = b.p
    n, s = p["count"], p["size"]
    hs = s / 2
    if p["layout"] == "row":
        step = s * 1.45
        x0 = -(n - 1) * step / 2
        for i in range(n):
            x = x0 + i * step
            new = i == n - 1
            z = 0.25 if (new and p["pending"]) else 0.0
            m = b.t.solid if new else P.M["metal"]
            part = b.box(x - hs, -hs, z, x + hs, hs, z + s, m)
            fp = front_plane(x - hs, x + hs, z, -hs)
            for k, f in enumerate((0.62, 0.42)):
                part.els.append(tline(fp, s * 0.2, s * (0.68 - k * 0.24), s * (0.2 + f), "#ffffff" if new else P.SOFT2, w=s * 0.07))
            if i < n - 1:
                jm = b.t.solid if b.tint != "neutral" else P.M["steel"]
                b.box(x + hs, -hs, s * 0.4, x + step - hs, -hs + 0.12, s * 0.56, jm, lip=None)
        b.anchors["new"] = (x0 + (n - 1) * step, 0, s + 0.25)
        b.anchors["first"] = (x0, 0, s)
    else:
        th = s * 0.32
        for i in range(n):
            new = i == n - 1
            z = i * (th + 0.04) + (0.22 if (new and p["pending"]) else 0)
            m = b.t.solid if new else P.M["metal"]
            part = b.box(-s * 0.8, -s * 0.8, z, s * 0.8, s * 0.8, z + th, m)
            fp = front_plane(-s * 0.8, s * 0.8, z, -s * 0.8)
            part.els.append(tline(fp, s * 0.25, th * 0.5, s * 0.95, "#ffffff" if new else P.SOFT2, w=th * 0.28))
        b.anchors["new"] = (0, 0, n * (th + 0.04) + 0.22)


# ======================================================================= security
@prop("seal", "Security", "A wax seal (a signature, an attestation): a disc lying flat, or standing upright.",
      tints=("seal", "tee", "data") + LAYER_TINTS, tint="seal", r=num(0.45, 0.15, 1.5, "radius"),
      pose=choice("lying", ("lying", "standing"), "lying flat or standing on its edge"))
def p_seal(b):
    p = b.p
    r = p["r"]
    m = b.t.solid
    inner = P.SEAL2 if b.tint == "seal" else b.t.light.top
    if p["pose"] == "lying":
        n = 14
        pts = []
        for i in range(n * 2):
            a = math.radians(i * 180.0 / n)
            rr = r * (1.0 if i % 2 == 0 else 0.92)
            pts.append((math.cos(a) * rr, math.sin(a) * rr))
        pl = top_plane(0, 0, r * 0.22)
        part = b.extrude(pl, [poly2(pts)], r * 0.22, m.top, side=m.right)
        part.els.append(pl.path(circle2(0, 0, r * 0.66), stroke=inner, swu=r * 0.1))
        part.els.append(pl.shape(circle2(0, 0, r * 0.25), fill=m.left, body=False))
        b.anchors["rim"] = (-r * 0.74, r * 0.74, r * 0.22)
    else:
        pl = front_plane(0, 0, 0, -0.08)
        part = b.extrude(pl, [circle2(0, r, r)], 0.16, m.left, side=m.right)
        part.els.append(pl.path(circle2(0, r, r * 0.66), stroke=inner, swu=r * 0.1))
        part.els.append(pl.shape(circle2(0, r, r * 0.25), fill=m.top, body=False))
        b.anchors["rim"] = (0, 0.0, 2 * r)


@prop("padlock", "Security", "A padlock standing, keyhole toward the front; open lifts the shackle.",
      tints=("tee", "neutral", "data", "seal", "dark") + LAYER_TINTS, tint="tee",
      size=num(1, 0.3, 3, "body width"), open=flag(False, "the shackle lifted out"))
def p_padlock(b):
    p = b.p
    s = p["size"]
    w, h, dep = s, s * 0.82, s * 0.36
    pl = front_plane(0, 0, 0, -dep / 2)
    mid = front_plane(0, 0, 0, 0)
    lift = s * 0.32 if p["open"] else 0.0
    sh_r = w * 0.3
    if p["open"]:
        shackle = mid.path([("M", -sh_r, h * 0.85 + lift)] + arc2(-sh_r + sh_r, h + lift, sh_r, 180, 0)[1:] +
                           [("L", sh_r, h * 0.7)], stroke="#8d949d", swu=s * 0.15, cap="round")
        shackle_l = mid.line([(-sh_r, h * 0.85 + lift), (-sh_r, h + lift)], stroke="#8d949d", swu=s * 0.15, cap="round")
        sh_els = [shackle, shackle_l]
    else:
        sh_els = [mid.path([("M", -sh_r, h * 0.7), ("L", -sh_r, h)] + arc2(0, h, sh_r, 180, 0, move=False)[1:] +
                           [("L", sh_r, h * 0.7)], stroke="#8d949d", swu=s * 0.15, cap="butt", join="round")]
    for e in sh_els:
        e.body = True
    body = b.extrude_els(pl, [rrect(-w / 2, 0, w / 2, h, s * 0.12)], dep, b.t.solid.left, side=b.t.solid.right)
    hole = "#ffffff" if b.tint not in ("neutral",) else P.INK
    keyh = [pl.shape(circle2(0, h * 0.52, s * 0.1), fill=hole, body=False),
            pl.shape(poly2([(-s * 0.05, h * 0.5), (s * 0.05, h * 0.5), (s * 0.07, h * 0.24), (-s * 0.07, h * 0.24)]), fill=hole, body=False)]
    hi = pl.line([(-w / 2 + s * 0.12, h * 0.9), (w / 2 - s * 0.12, h * 0.9)], stroke="#ffffff", swu=s * 0.03, sop=0.35)
    b.add(sh_els + body + keyh + [hi])
    b.anchors["center"] = (0, -dep / 2, h * 0.5)


@prop("key", "Security", "A key lying flat on the ground, its bow toward the back-left.",
      tints=("neutral", "tee", "data", "seal") + LAYER_TINTS, tint="neutral", size=num(1.6, 0.5, 4, "length"))
def p_key(b):
    p = b.p
    L = p["size"]
    k = L / 1.6
    m = P.Mat("#e2c766", P.GOLD, P.GOLD_D, None, "keygold") if b.tint == "neutral" else b.t.solid
    pl = top_plane(0, 0, 0.1 * k)
    bow = circle2(-0.5 * k, 0, 0.32 * k)
    shaft = rect(-0.25 * k, -0.07 * k, 0.8 * k, 0.07 * k)
    teeth = [rect(0.45 * k, -0.22 * k, 0.55 * k, -0.06 * k), rect(0.65 * k, -0.18 * k, 0.75 * k, -0.06 * k)]
    part = b.extrude(pl, [bow, shaft] + teeth, 0.1 * k, m.top, side=m.right)
    part.els.append(pl.shape(circle2(-0.58 * k, 0, 0.12 * k), fill="#ffffff", body=False))
    part.els.append(pl.path(circle2(-0.5 * k, 0, 0.24 * k), stroke=m.left, swu=0.03 * k))


@prop("shield", "Security", "A shield standing upright with an emblem: protection, a security claim.",
      tints=("tee", "neutral", "data", "seal") + LAYER_TINTS, tint="tee", size=num(1.3, 0.4, 3, "width"),
      emblem=choice("lock", ("none", "lock", "keyhole", "chip", "bars"), "the mark on the shield"))
def p_shield(b):
    p = b.p
    w = p["size"]
    h = w * 1.22
    pl = front_plane(0, 0, 0, -0.1 * w)
    m = b.t.solid
    els = b.extrude_els(pl, [shield2(0, h / 2, w, h * 0.94)], 0.2 * w, m.left, side=m.right)
    els.append(pl.path(shield2(0, h / 2 + h * 0.01, w * 0.8, h * 0.74), stroke="#ffffff", swu=w * 0.025, sop=0.45))
    em = p["emblem"]
    white = "#ffffff"
    if em == "lock":
        els += lock_glyph(pl, 0, h * 0.5, w * 0.42, white, hole=m.left)
    elif em == "keyhole":
        els.append(pl.shape(circle2(0, h * 0.58, w * 0.12), fill=white, body=False))
        els.append(pl.shape(poly2([(-w * 0.06, h * 0.56), (w * 0.06, h * 0.56), (w * 0.1, h * 0.32), (-w * 0.1, h * 0.32)]), fill=white,
                            body=False))
    elif em == "chip":
        els.append(pl.shape(rect(-w * 0.17, h * 0.38, w * 0.17, h * 0.66), fill=white, body=False))
        for k in range(3):
            v = h * (0.43 + k * 0.09)
            els.append(pl.line([(-w * 0.27, v), (-w * 0.17, v)], stroke=white, swu=w * 0.03))
            els.append(pl.line([(w * 0.17, v), (w * 0.27, v)], stroke=white, swu=w * 0.03))
    elif em == "bars":
        for k in range(3):
            els.append(tline(pl, -w * 0.2, h * (0.62 - k * 0.11), w * (0.2 - k * 0.07), white, w=w * 0.05))
    b.add(els)


# ======================================================================= analysis
@prop("magnifier", "Analysis", "A magnifying glass standing on the tip of its handle, the lens upright: detection, "
      "inspection. reveal draws what the lens finds (a hidden watermark). Use it only where detection itself is the story.",
      tints=("neutral", "tee", "data") + LAYER_TINTS, tint="neutral", r=num(0.62, 0.3, 2, "lens radius"),
      height=num(0, 0, 5, "lens center above the base; 0 rests the handle's tip on the base (the center then sits at "
                 "about 2.1 r); a larger value lengthens the handle down to the base, up to 3 r, then the glass floats"),
      turn=num(0, -60, 60, "turn the lens about the upright, in degrees (+ turns its face toward the lower right)"),
      reveal=choice("none", ("none", "wave", "dots", "grid", "mark"), "what shows inside the lens"))
def p_magnifier(b):
    p = b.p
    r = p["r"]
    a = math.radians(p["turn"])
    ex = (math.cos(a), math.sin(a), 0.0)
    nrm = (math.sin(a), -math.cos(a), 0.0)          # the lens's face, toward the viewer at turn 0
    ring_out, depth = r * 1.17, r * 0.13
    ang = math.radians(-55)
    hu, hv = math.cos(ang), math.sin(ang)           # the handle's direction in the lens plane
    th = r * 0.24
    if p["height"] <= 0:
        L = r * 1.5
        zc = (ring_out + L) * -hv + th * 0.5
    else:
        zc = max(p["height"], (ring_out + r * 0.9) * -hv + th * 0.5)
        L = min(r * 3.0, (zc - th * 0.5) / -hv - ring_out)
    c = (0.0, 0.0, zc)

    def at(u, v, off=0.0):
        return (c[0] + ex[0] * u + nrm[0] * off, c[1] + ex[1] * u + nrm[1] * off, zc + v)
    hd = (ex[0] * hu, ex[1] * hu, hv)                 # unit handle direction
    q = (hd[1] * nrm[2] - hd[2] * nrm[1], hd[2] * nrm[0] - hd[0] * nrm[2], hd[0] * nrm[1] - hd[1] * nrm[0])
    # the handle: a dark bar from the rim down to the base, with a light ferrule at the rim
    st = at(ring_out * hu * 0.98, ring_out * hv * 0.98)
    fl = r * 0.36
    fth = th * 1.3
    o = (st[0] - nrm[0] * fth / 2 - q[0] * fth / 2, st[1] - nrm[1] * fth / 2 - q[1] * fth / 2, st[2] - nrm[2] * fth / 2 - q[2] * fth / 2)
    b.obox(o, mul(hd, fl), mul(nrm, fth), mul(q, fth), P.Mat("#9aa2ab", "#7a838e", "#5f6770", None, "ferrule"), name="ferrule")
    hs = (st[0] + hd[0] * fl, st[1] + hd[1] * fl, st[2] + hd[2] * fl)
    o = (hs[0] - nrm[0] * th / 2 - q[0] * th / 2, hs[1] - nrm[1] * th / 2 - q[1] * th / 2, hs[2] - nrm[2] * th / 2 - q[2] * th / 2)
    b.obox(o, mul(hd, max(0.05, L - fl)), mul(nrm, th), mul(q, th), P.Mat("#4a5159", P.SUB0, P.SUB1, None, "handle"),
           name="handle")
    tip = (hs[0] + hd[0] * (L - fl), hs[1] + hd[1] * (L - fl), hs[2] + hd[2] * (L - fl))
    # the ring: walls, the lens, what it reveals, then the ring's two faces
    n = 40
    loop = lambda rad, off: [at(math.cos(2 * math.pi * i / n) * rad, math.sin(2 * math.pi * i / n) * rad, off)
                             for i in range(n)]
    els = [Wall(loop(ring_out, depth / 2), loop(r, depth / 2), mul(nrm, -depth), "#9aa2ab", "#8d949d")]
    mid = Plane(c, ex, (0.0, 0.0, 1.0))
    front = Plane(add(c, mul(nrm, depth / 2)), ex, (0.0, 0.0, 1.0))
    back = Plane(add(c, mul(nrm, -depth / 2)), mul(ex, -1), (0.0, 0.0, 1.0))
    lens = mid.shape(circle2(0, 0, r), fill="#ffffff", fop=0.35, cull=False)
    lens.body = False
    els.append(lens)
    acc = b.t.accent if b.tint != "neutral" else P.INK2
    sw = r * 0.045
    rv = p["reveal"]
    marks = []
    if rv == "wave":
        for j in range(-2, 3):
            vv = j * r * 0.28
            half = math.sqrt(max(0.0, (r * 0.84) ** 2 - vv ** 2))
            pts = [(-half + 2 * half * i / 14.0, vv + math.sin((-half + 2 * half * i / 14.0) / r * 7.0 + j) * r * 0.06)
                   for i in range(15)]
            marks.append(mid.line(pts, stroke=acc, swu=sw, cap="round", join="round"))
    elif rv == "dots":
        for i in range(-3, 4):
            for j in range(-3, 4):
                u, v = i * r * 0.24, j * r * 0.24
                if u * u + v * v < (r * 0.8) ** 2 and (i + j) % 2 == 0:
                    marks.append(mid.shape(circle2(u, v, r * 0.05), fill=acc, body=False))
    elif rv == "grid":
        for j in range(-2, 3):
            vv = j * r * 0.3
            half = math.sqrt(max(0.0, (r * 0.84) ** 2 - vv ** 2))
            marks.append(mid.line([(-half, vv), (half, vv)], stroke=acc, swu=sw * 0.8))
            marks.append(mid.line([(vv, -half), (vv, half)], stroke=acc, swu=sw * 0.8))
    elif rv == "mark":
        marks.append(mid.path([("M", -r * 0.42, -r * 0.05), ("C", -r * 0.2, r * 0.35, r * 0.05, -r * 0.4, r * 0.42, r * 0.12)],
                              stroke=acc, swu=r * 0.09, cap="round"))
        marks.append(mid.shape(circle2(r * 0.42, r * 0.12, r * 0.09), fill=acc, body=False))
    for e in marks:
        e.cull = False
    els += marks
    ring = circle2(0, 0, ring_out) + circle2(0, 0, r)    # even-odd: the annulus
    els.append(front.shape(ring, fill="#c7ccd3", rule="evenodd"))
    els.append(back.shape(ring, fill="#c7ccd3", rule="evenodd"))
    els.append(front.path(arc2(0, 0, r * 0.8, 110, 160), stroke="#ffffff", swu=r * 0.07, cap="round", sop=0.9))
    b.add(els, name="ring")
    b.lift = max(0.0, tip[2] - th * 0.5) if tip[2] - th * 0.5 > 0.02 else 0.0
    if not b.lift:
        b.contacts.append((tip[0], tip[1], th * 0.9))
    b.anchors["lens"] = c
    b.anchors["tip"] = tip
    b.port = "tip"


@prop("scale", "Analysis", "A balance scale as on the hero's top plate: a white column on a round foot, a thin beam "
      "and two bowl pans hanging from it, drawn in the tint's line color: weighing, judgment, oversight, a law.",
      tints=("neutral", "institutions", "tee", "data", "evaluations"), tint="institutions",
      tilt=num(0, -1, 1, "beam tilt: -1 left pan down, 1 right pan down"), size=num(1, 0.5, 3, "overall scale factor"))
def p_scale(b):
    p = b.p
    k = p["size"]
    white = P.M["paper"]
    ink = b.t.accent if b.tint != "neutral" else P.INK2
    wash = b.t.wash if b.tint != "neutral" else P.SOFT
    b.cyl(0, 0, 0, 0.12 * k, 0.5 * k, white)
    b.box(-0.06 * k, -0.06 * k, 0.12 * k, 0.06 * k, 0.06 * k, 1.86 * k, white)
    b.sphere((0, 0, 1.96 * k), 0.09 * k, P.SOFT, hi="#ffffff")
    tilt = p["tilt"] * 0.18 * k
    zb = 1.86 * k
    # beam, strings and pans in a plane facing the viewer, so a pan's rim is the ellipse a
    # horizontal circle projects to (u spans 1.2643 K per unit, v spans K)
    face = Plane((0.0, 0.0, 0.0), (0.7071, 0.7071, 0.0), (0.0, 0.0, 1.0))
    half = 0.95 * k
    els = [face.line([(-half, zb + tilt), (half, zb - tilt)], stroke=ink, swu=0.045 * k, cap="round", cull=False)]
    rp, drop = 0.34 * k, 0.78 * k
    for side in (-1, 1):
        u = side * half
        ztop = zb - side * tilt
        zp = ztop - drop
        for du in (-rp * 0.86, rp * 0.86):
            els.append(face.line([(u, ztop), (u + du, zp)], stroke=ink, swu=0.022 * k, cap="round", cull=False))
        rim = 0.6322 * rp
        bowl = [("M", u - rp, zp)] + arc2(u, zp, rp, 180, 360, move=False, rv=rim)[1:] + \
            arc2(u, zp, rp, 0, -180, move=False, rv=rim * 1.9)[1:] + [("Z",)]
        e = face.shape(bowl, fill=wash, stroke=ink, swu=0.03 * k, join="round", cull=False)
        els.append(e)
    for e in els:
        e.cull = False
    b.add(els, name="beam")
    b.footprint = (-0.5 * k, -0.5 * k, 0.5 * k, 0.5 * k)


@prop("gauge", "Analysis", "A dial standing upright with a needle and a filled arc: a score, a threshold, a benchmark.",
      tints=("neutral", "tee", "data") + LAYER_TINTS, tint="evaluations", value=num(0.7, 0, 1, "needle position 0 to 1"),
      size=num(1.4, 0.6, 3, "dial width"))
def p_gauge(b):
    p = b.p
    w = p["size"]
    r = w / 2
    zc = r * 0.42
    pl = front_plane(0, 0, 0, -0.12 * w)
    top = [("M", r, zc)] + arc2(0, zc, r, 0, 180, move=False)[1:] + [("Z",)]
    els = b.extrude_els(pl, [rect(-r, 0, r, zc), top], 0.24 * w, P.PAPER, side="#cdd2d9")
    v = p["value"]
    rr = r * 0.7
    els.append(pl.path(arc2(0, zc, rr, 0, 180), stroke=P.SOFT, swu=w * 0.13, cap="butt"))
    els.append(pl.path(arc2(0, zc, rr, 180 - 180 * v, 180), stroke=b.t.accent if b.tint != "neutral" else P.INK2, swu=w * 0.13,
                       cap="butt"))
    for i in range(5):
        a = math.radians(i * 45)
        els.append(pl.line([(math.cos(a) * r * 0.9, zc + math.sin(a) * r * 0.9), (math.cos(a) * r * 0.97, zc + math.sin(a) * r * 0.97)],
                           stroke=P.MUTE, swu=r * 0.04))
    a = math.radians(180 - 180 * v)
    els.append(pl.line([(0, zc), (math.cos(a) * r * 0.66, zc + math.sin(a) * r * 0.66)], stroke=P.INK, swu=r * 0.09, cap="round"))
    els.append(pl.shape(circle2(0, zc, r * 0.17), fill=P.INK, body=False))
    els.append(pl.line([(-r * 0.5, zc * 0.45), (r * 0.5, zc * 0.45)], stroke=P.SOFT2, swu=r * 0.06, cap="round"))
    b.add(els)


@prop("bars", "Analysis", "A 3D bar chart standing on the ground: results, scores, measurements.",
      tints=("neutral", "tee", "data") + LAYER_TINTS, tint="evaluations",
      heights=nums([0.8, 1.3, 1.0, 1.9], 2, 8, 0.1, 5, "bar heights, left to right"),
      highlight=integer(-1, -1, 7, "index of the bar in the tint (-1: the tallest)"), bar=num(0.42, 0.15, 1, "bar width"))
def p_bars(b):
    p = b.p
    hs = p["heights"]
    bw = p["bar"]
    step = bw * 1.45
    x0 = -(len(hs) - 1) * step / 2
    hi = p["highlight"]
    if hi < 0 or hi >= len(hs):
        hi = max(range(len(hs)), key=lambda i: (hs[i], -i))
    pale = b.t.light if b.tint != "neutral" else P.M["soft"]
    for i, h in enumerate(hs):
        x = x0 + i * step
        b.box(x - bw / 2, -bw / 2, 0, x + bw / 2, bw / 2, h, b.t.solid if i == hi else pale)
    b.anchors["top"] = (x0 + hi * step, 0, hs[hi])
