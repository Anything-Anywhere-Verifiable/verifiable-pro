"""Deterministic editorial illustrations.

Every illustration is drawn from the SHA-256 digest of a seed string (the
article's source text), so anyone can regenerate it from the published
source. Colors come from CSS classes, so the art follows the site theme.
Only ``random.Random.random()`` is used because Python keeps that sequence
stable for a given seed.
"""

import hashlib
import html
import math
import random

W, H = 640, 360


class Rng:
    def __init__(self, seed):
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        self.hex = digest.hex()
        self._r = random.Random(int.from_bytes(digest, "big"))

    def f(self, a=0.0, b=1.0):
        return a + (b - a) * self._r.random()

    def i(self, a, b):
        return a + int(self._r.random() * (b - a + 1))

    def pick(self, seq):
        return seq[int(self._r.random() * len(seq))]

    def chance(self, p):
        return self._r.random() < p


def _rect(cls, x, y, w, h, extra=""):
    return f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{extra}/>'


def _line(cls, x1, y1, x2, y2):
    return f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'


def _circle(cls, x, y, r):
    return f'<circle class="{cls}" cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}"/>'


def _grid(cell, cls="a-grid"):
    lines = [_line(cls, x, 0, x, H) for x in range(0, W + 1, cell)]
    lines += [_line(cls, 0, y, W, y) for y in range(0, H + 1, cell)]
    return "".join(lines)


def enclave(rng):
    """Confidential computing: memory pages and a measured, sealed region."""
    cell = rng.pick([20, 24])
    out = [_grid(cell)]
    cols, rows = W // cell, H // cell
    ew, eh = rng.i(8, 11), rng.i(7, 9)
    ex, ey = rng.i(cols // 2 - ew // 2 - 3, cols // 2 - ew // 2 + 3), rng.i(2, max(2, rows - eh - 2))
    for y in range(rows):
        for x in range(cols):
            inside = ex - 1 <= x <= ex + ew and ey - 1 <= y <= ey + eh
            if not inside and rng.chance(0.28):
                out.append(_rect("a-mute", x * cell + 4, y * cell + 4, cell - 8, cell - 8))
    x0, y0, w0, h0 = ex * cell, ey * cell, ew * cell, eh * cell
    out.append(_rect("a-paper", x0 - 8, y0 - 8, w0 + 16, h0 + 16))
    out.append(_rect("a-stroke", x0 - 8, y0 - 8, w0 + 16, h0 + 16))
    out.append(_rect("a-stroke", x0, y0, w0, h0))
    for y in range(ey + 1, ey + eh - 1):
        for x in range(ex + 1, ex + ew - 1):
            if rng.chance(0.42):
                out.append(_rect("a-ink", x * cell + 5, y * cell + 5, cell - 10, cell - 10))
    cx, cy = x0 + rng.i(2, ew - 3) * cell, y0 + rng.i(2, eh - 3) * cell
    out.append(_rect("a-acc", cx + 2, cy + 2, cell - 4, cell - 4))
    for k in range(ew + 1):
        out.append(_line("a-stroke", x0 + k * cell, y0 - 8, x0 + k * cell, y0 - 14))
    return "".join(out)


def proof_tree(rng):
    """Verifiable inference: layered computation folded into one commitment."""
    out = []
    layers = rng.i(5, 7)
    xs = [70 + k * (W - 200) / (layers - 1) for k in range(layers)]
    nodes = []
    for k, x in enumerate(xs):
        n = max(2, rng.i(4, 8) - (k * 4 // layers))
        gap = (H - 80) / (n + 1)
        nodes.append([(x, 40 + gap * (j + 1)) for j in range(n)])
    path = [rng.i(0, len(layer) - 1) for layer in nodes]
    for k in range(layers - 1):
        for a, (x1, y1) in enumerate(nodes[k]):
            for b, (x2, y2) in enumerate(nodes[k + 1]):
                if rng.chance(0.45):
                    out.append(_line("a-faint", x1, y1, x2, y2))
    for k in range(layers - 1):
        (x1, y1), (x2, y2) = nodes[k][path[k]], nodes[k + 1][path[k + 1]]
        out.append(_line("a-acc-stroke", x1, y1, x2, y2))
    for k, layer in enumerate(nodes):
        for j, (x, y) in enumerate(layer):
            out.append(_circle("a-acc" if j == path[k] else "a-ink", x, y, 5 if j == path[k] else 3.5))
    tx, ty = W - 70, H / 2
    lx, ly = nodes[-1][path[-1]]
    out.append(_line("a-acc-stroke", lx, ly, tx - 16, ty))
    out.append(_rect("a-paper", tx - 16, ty - 16, 32, 32))
    out.append(_rect("a-stroke", tx - 16, ty - 16, 32, 32))
    out.append(_rect("a-acc", tx - 7, ty - 7, 14, 14))
    return "".join(out)


def lattice(rng):
    """Formal verification: proof obligations discharged across a lattice."""
    cell = rng.pick([24, 30])
    cols, rows = W // cell, H // cell
    out = [_grid(cell)]
    phase = rng.f(0.0, 6.0)
    slope = rng.f(0.35, 0.8)
    for y in range(rows):
        for x in range(cols):
            front = (x + y * slope + phase) / (cols + rows * slope)
            if front < 0.48:
                out.append(_rect("a-ink", x * cell + 9, y * cell + 9, cell - 18, cell - 18))
            elif front < 0.64 and rng.chance(0.55):
                out.append(_rect("a-stroke", x * cell + 7, y * cell + 7, cell - 14, cell - 14))
    gx, gy = rng.i(cols * 2 // 3, cols - 2), rng.i(1, rows - 2)
    out.append(_rect("a-paper", gx * cell + 1, gy * cell + 1, cell - 2, cell - 2))
    out.append(_rect("a-acc", gx * cell + 6, gy * cell + 6, cell - 12, cell - 12))
    return "".join(out)


def samples(rng):
    """Evaluation and audits: many runs, a confidence band, flagged failures."""
    out = []
    base = H * 0.62
    band = rng.f(0.08, 0.16) * H
    out.append(_rect("a-mute", 30, base - band, W - 60, band * 2))
    out.append(_line("a-stroke", 30, base, W - 30, base))
    n = rng.i(70, 96)
    step = (W - 80) / n
    for k in range(n):
        x = 40 + k * step
        fail = rng.chance(0.07)
        dev = (rng.pick([-1, 1]) * rng.f(1.25, 2.1) if fail else rng.f(-0.9, 0.9)) * band
        out.append(_line("a-acc-stroke" if fail else "a-ink-stroke", x, base, x, base - dev))
        if fail:
            out.append(_circle("a-acc", x, base - dev, 3.2))
    for k in range(5):
        y = 34 + k * 12
        out.append(_rect("a-ink", 34, y, rng.f(60, 220), 3))
    return "".join(out)


def chain(rng):
    """Provenance and supply chain: hash-linked records."""
    out = [_grid(40, "a-grid")]
    count = rng.i(4, 5)
    bw, bh = 92, 120
    gap = (W - 60 - count * bw) / (count - 1)
    y0 = H / 2 - bh / 2 + rng.f(-20, 20)
    for k in range(count):
        x0 = 30 + k * (bw + gap)
        last = k == count - 1
        out.append(_rect("a-paper", x0, y0, bw, bh))
        out.append(_rect("a-stroke", x0, y0, bw, bh))
        for row in range(6):
            width = rng.f(0.35, 0.85) * (bw - 24)
            out.append(_rect("a-acc" if last and row == 0 else "a-ink", x0 + 12, y0 + 14 + row * 16, width, 5))
        if k < count - 1:
            mx = x0 + bw
            out.append(_line("a-stroke", mx, y0 + bh / 2, mx + gap, y0 + bh / 2))
            out.append(_circle("a-ink", mx + gap / 2, y0 + bh / 2, 4))
    return "".join(out)


def credential(rng):
    """Content provenance: an image, its embedded signal and a signed manifest."""
    out = []
    px = 16
    cols, rows = rng.i(17, 20), 15
    x0, y0 = 36, (H - rows * px) / 2
    fa, fb, ph = rng.f(0.25, 0.55), rng.f(0.2, 0.5), rng.f(0, 6.3)
    for y in range(rows):
        for x in range(cols):
            v = math.sin(x * fa + ph) + math.cos(y * fb - ph / 2) + rng.f(-0.35, 0.35)
            if v > 0.9:
                out.append(_rect("a-ink", x0 + x * px + 2, y0 + y * px + 2, px - 4, px - 4))
            elif v > -0.2:
                out.append(_rect("a-mute", x0 + x * px + 2, y0 + y * px + 2, px - 4, px - 4))
    step = rng.i(3, 4)
    for k in range(0, min(cols, rows) * 2, step):
        x, y = k % cols, (k * 3 + rng.i(0, 1)) % rows
        out.append(_rect("a-acc", x0 + x * px + 5, y0 + y * px + 5, px - 10, px - 10))
    out.append(_rect("a-stroke", x0, y0, cols * px, rows * px))
    cx = x0 + cols * px + 44
    cw, ch = W - cx - 30, 172
    cy = H / 2 - ch / 2
    out.append(_line("a-stroke", x0 + cols * px, H / 2, cx, H / 2))
    out.append(_rect("a-paper", cx, cy, cw, ch))
    out.append(_rect("a-stroke", cx, cy, cw, ch))
    out.append(_rect("a-ink", cx, cy, cw, 18))
    for row in range(6):
        out.append(_rect("a-ink" if row % 3 else "a-mute", cx + 12, cy + 32 + row * 18, rng.f(0.4, 0.8) * (cw - 24), 5))
    out.append(_rect("a-acc", cx + cw - 30, cy + ch - 30, 18, 18))
    return "".join(out)


def trajectory(rng):
    """Agents and accountability: an action path and its tamper-evident log."""
    cell = 40
    cols, rows = W // cell, (H - 80) // cell
    out = []
    for y in range(1, rows + 1):
        for x in range(1, cols):
            out.append(_circle("a-faint-dot", x * cell, y * cell, 1.6))
    x, y = 1, rng.i(1, rows)
    pts = [(x, y)]
    while x < cols - 1 and len(pts) < 34:
        if rng.chance(0.6):
            x += 1
        else:
            y = max(1, min(rows, y + rng.pick([-1, 1])))
        pts.append((x, y))
    d = " ".join(f"{'M' if k == 0 else 'L'}{px * cell} {py * cell}" for k, (px, py) in enumerate(pts))
    out.append(f'<path class="a-stroke" d="{d}"/>')
    for k, (px, py) in enumerate(pts):
        if k % 3 == 0 or k == len(pts) - 1:
            out.append(_circle("a-acc" if k == len(pts) - 1 else "a-ink", px * cell, py * cell, 5))
    ly = H - 52
    out.append(_line("a-stroke", 30, ly, W - 30, ly))
    for k in range(len(pts)):
        lx = 30 + k * (W - 60) / max(1, len(pts) - 1)
        out.append(_line("a-ink-stroke", lx, ly, lx, ly + (14 if k % 3 == 0 else 7)))
    return "".join(out)


def die(rng):
    """Governance and compute verification: a chip with metered cores."""
    out = []
    size = H - 70
    x0, y0 = (W - size) / 2 + rng.f(-90, 90), 35
    n = rng.pick([8, 10])
    pitch = size / n
    for k in range(n * 2):
        px = x0 + (k % n + 0.5) * pitch
        out.append(_line("a-stroke", px, y0 - 12, px, y0) if k < n else _line("a-stroke", px, y0 + size, px, y0 + size + 12))
    for k in range(n):
        py = y0 + (k + 0.5) * pitch
        out.append(_line("a-stroke", x0 - 12, py, x0, py))
        out.append(_line("a-stroke", x0 + size, py, x0 + size + 12, py))
    out.append(_rect("a-paper", x0, y0, size, size))
    out.append(_rect("a-stroke", x0, y0, size, size))
    for y in range(n):
        for x in range(n):
            cls = "a-acc" if rng.chance(0.06) else ("a-ink" if rng.chance(0.5) else "a-mute")
            out.append(_rect(cls, x0 + x * pitch + 4, y0 + y * pitch + 4, pitch - 8, pitch - 8))
    return "".join(out)


MOTIFS = {
    "confidential-computing": enclave,
    "verifiable-inference": proof_tree,
    "formal-verification": lattice,
    "evaluation-audits": samples,
    "supply-chain": chain,
    "content-provenance": credential,
    "agents-accountability": trajectory,
    "governance-compute": die,
}


def illustration(seed, topic, label, show_hash=True):
    """Return an inline SVG string and the digest it was drawn from."""
    rng = Rng(seed)
    motif = MOTIFS.get(topic, chain)
    body = motif(rng)
    tag = ""
    if show_hash:
        tag = (
            f'<rect class="a-paper" x="{W - 168}" y="{H - 30}" width="156" height="20"/>'
            f'<text class="a-text" x="{W - 18}" y="{H - 15.5}" text-anchor="end">sha256 {rng.hex[:12]}</text>'
        )
    svg = (
        f'<svg class="art" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice" '
        f'role="img" aria-label="{html.escape(label, quote=False).replace(chr(34), "&quot;")}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<rect class="a-bg" width="{W}" height="{H}"/>{body}{tag}</svg>'
    )
    return svg, rng.hex
