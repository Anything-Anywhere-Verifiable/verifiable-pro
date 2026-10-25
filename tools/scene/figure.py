#!/usr/bin/env python3
"""The person prop's figure, baked from the home page hero's own person.

tools/hero/person.py models the reader in an orange coat in 3D and traces each part,
lit and in shade, into flat paths in the hero's projection, which is also the scene
generator's. Tracing takes a few seconds, so this file keeps the result in figure.json:
for each path its colour role and its polygons, in model units with the feet centre at
(0, 0), for a figure FIGURE_HEIGHT model units tall. The person prop scales it to its
height and places it at its feet.

    python3 tools/scene/figure.py --write   # trace the hero's person again into figure.json
    python3 tools/scene/figure.py --check   # exit 1 when figure.json differs from a fresh trace

tests/test_illustrate.py runs --check, so a change to the hero's person reaches the
illustrations' person too.
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "figure.json")
FIGURE_HEIGHT = 90.0   # model units from the soles to the crown (tools/hero/person.py)
# the hero's classes for the figure's paths, and the role each colour plays
ROLES = {"hv-pshoe": "shoe", "hv-plegs": "legs", "hv-plegs2": "legs2", "hv-pcoat": "coat", "hv-pcoat2": "coat2",
         "hv-pskin": "skin", "hv-pskin2": "skin2", "hv-phair": "hair", "hv-pphone": "phone", "hv-pscreen": "screen"}


def _polygons(d):
    """The closed polygons of hero path data (M, then relative l, h and v; z)."""
    polys, cur, x, y = [], None, 0.0, 0.0
    for cmd, args in re.findall(r"([MlhvZz])([^MlhvZz]*)", d):
        nums = [float(v) for v in re.findall(r"-?(?:\d+\.?\d*|\.\d+)", args)]
        if cmd == "M":
            x, y = nums[0], nums[1]
            cur = [(x, y)]
            polys.append(cur)
        elif cmd == "l":
            for i in range(0, len(nums), 2):
                x, y = x + nums[i], y + nums[i + 1]
                cur.append((x, y))
        elif cmd == "h":
            for v in nums:
                x += v
                cur.append((x, y))
        elif cmd == "v":
            for v in nums:
                y += v
                cur.append((x, y))
    return [p for p in polys if len(p) >= 3]


def trace():
    """The figure from tools/hero/person.py, as {"paths": [[role, [polygon, ...]], ...]}."""
    hero = os.path.join(os.path.dirname(HERE), "hero")
    if hero not in sys.path:
        sys.path.insert(0, hero)
    import person  # noqa: E402  (tools/hero/person.py)
    scale = person.SCALE
    out = person.build(person.P, scale, (0.0, 0.0))
    paths = []
    for cls, d in out:
        if cls not in ROLES or not isinstance(d, str) or d.startswith("<"):
            continue
        polys = [[[round(px / scale, 2), round(py / scale, 2)] for px, py in poly] for poly in _polygons(d)]
        if polys:
            paths.append([ROLES[cls], polys])
    ring = next(d for cls, d in out if cls == "ring")
    return {"source": "tools/hero/person.py", "height": FIGURE_HEIGHT, "phone": [round(ring[0] / scale, 2),
                                                                                 round(ring[1] / scale, 2)],
            "paths": paths}


def dumps(data):
    return json.dumps(data, separators=(",", ":")) + "\n"


def load():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def main(argv):
    if argv not in (["--write"], ["--check"]):
        print("usage: python3 tools/scene/figure.py --write | --check", file=sys.stderr)
        return 2
    text = dumps(trace())
    old = open(DATA, encoding="utf-8").read() if os.path.exists(DATA) else None
    if argv == ["--check"]:
        if old == text:
            return 0
        print("tools/scene/figure.json differs from the hero's person; run python3 tools/scene/figure.py --write",
              file=sys.stderr)
        return 1
    if old != text:
        with open(DATA, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote tools/scene/figure.json (%.1f KB)" % (len(text) / 1024.0))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
