"""Tests for the lead-illustration generator (tools/illustrate.py, tools/scene/).

Run with: PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_illustrate
"""
import contextlib
import copy
import hashlib
import io
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import illustrate  # noqa: E402
from scene import SpecError, draw, validate  # noqa: E402
from scene import compose  # noqa: E402
from scene.compose import render  # noqa: E402
from scene.kit import REGISTRY  # noqa: E402

SVG_NS = "{http://www.w3.org/2000/svg}"
ALLOWED_TAGS = {"svg", "defs", "linearGradient", "radialGradient", "stop", "filter", "feGaussianBlur",
                "rect", "path", "ellipse", "g"}
CINNABAR = ("#b3261e", "#cf3b31", "#7e1a15")

# Three of the six drafted samples, as the news stories use the generator.
SAMPLES = {
    "interposer": {
        "focal": "cpu",
        "items": [
            {"prop": "chip", "id": "cpu", "at": [-1.3, 0.8], "size": 2.6, "enclave": True},
            {"prop": "certificate", "id": "report", "at_uv": [-2.0, 3.2], "tint": "tee", "w": 1.6, "h": 1.15},
            {"prop": "dimm", "id": "mem", "at": [3.1, 1.5], "count": 1, "length": 2.4},
            {"prop": "interposer", "id": "probe", "at": [2.5, -0.3], "length": 2.4, "cable": 0.6, "lamp": False},
            {"prop": "packet", "id": "lost", "at": [0.6, -0.3], "ghost": True},
        ],
        "links": [
            {"from": [0.05, 1.5, 0], "to": "mem"},
            {"from": [0.05, -0.3, 0], "to": "probe", "style": "broken", "gap": 0.5},
            {"from": "cpu", "to": "report", "style": "dotted", "color": "tee"},
        ],
    },
    "glasses": {
        "focal": "cvm",
        "items": [
            {"prop": "glasses", "id": "glasses", "at": [2.72, -2.82]},
            {"prop": "gate", "id": "check", "at": [0, -0.9], "w": 1.8, "h": 2.0, "tint": "tee"},
            {"prop": "certificate", "id": "report", "at": [3.6, -0.4], "tint": "tee", "w": 1.4, "h": 1.0},
            {"prop": "ledger", "id": "ledger", "at_uv": [-4.4, -1.6], "count": 4, "size": 0.55},
            {"prop": "enclosure", "id": "cvm", "at": [-1.4, 0.7], "w": 2.6, "d": 2.1, "h": 3.1, "items": [
                {"prop": "server_rack", "id": "rack", "at": [-1.4, 0.7], "tint": "tee", "units": 6}]},
        ],
        "links": [
            {"from": "glasses", "to": "rack.lamp", "route": "via", "via": [[0.05, -0.9, 0.6]], "style": "dashed",
             "packets": [0.3, 0.8], "glow": True},
            {"from": "check", "to": "report", "style": "dotted", "color": "tee"},
            {"from": "check", "to": "ledger", "style": "dotted", "color": "tee"},
        ],
    },
    "signing": {
        "focal": "model",
        "items": [
            {"prop": "weights", "id": "model", "at": [-1.2, 0.6], "size": 1.7},
            {"prop": "seal", "id": "sig", "on": "model", "at": [-1.2, 0.6], "r": 0.5},
            {"prop": "certificate", "id": "cert", "at": [-2.6, -2.0], "tint": "neutral", "w": 1.6, "h": 1.1},
            {"prop": "ledger", "id": "log", "at_uv": [-4.6, -4.6], "count": 4, "size": 0.6, "tint": "models"},
            {"prop": "gate", "id": "check", "at": [1.2, 0.6], "w": 1.4, "h": 1.6, "tint": "neutral", "facing": "right"},
            {"prop": "laptop", "id": "user", "at": [3.3, 0.6], "w": 1.7, "content": "code"},
        ],
        "links": [
            {"from": "sig.rim", "to": "log.new", "route": "arc", "lift": 0.4, "style": "dotted", "color": "mute"},
            {"from": "cert", "to": "model", "style": "dotted", "color": "mute"},
            {"from": "model", "to": "user", "style": "dashed", "packets": 1},
        ],
    },
}
STORIES = {"interposer": {"tee", "pcb"}, "glasses": {"tee", "pcb"}, "signing": {"models"}}

# The art director's README-only draft: a packet hidden behind the laptop, a floor link
# that starts behind it (tests the occlusion check)
HIDDEN = {
    "focal": "net",
    "items": [
        {"prop": "neural_net", "id": "net", "at": [-0.6, 1.0], "w": 2.8, "h": 1.9, "columns": [3, 5, 5, 2], "tint": "neutral"},
        {"prop": "bars", "id": "score", "at": [-2.4, 2.6], "heights": [2.2, 2.1, 1.6], "tint": "evaluations"},
        {"prop": "math_block", "id": "claim", "at": [1.6, 2.2], "size": 0.8, "mark": "turnstile", "tint": "evaluations"},
        {"prop": "laptop", "id": "tool", "at": [1.4, -1.6], "content": "code"},
        {"prop": "packet", "id": "cex", "at": [0.4, -0.4], "glow": True},
    ],
    "links": [
        {"from": "tool.screen", "to": "net", "route": "arc", "style": "dashed", "packets": 1},
        {"from": "net", "to": "claim", "color": "ink", "style": "dotted", "route": "floor"},
    ],
}


def two_boxes(**kw):
    """Two small boxes, a and b, and a link between them with the given keys."""
    link = {"from": "a", "to": "b"}
    link.update(kw)
    return {"items": [{"prop": "box", "id": "a", "at": [-2, 0], "w": 0.6, "d": 0.6, "h": 0.5},
                      {"prop": "box", "id": "b", "at": [2, 0], "w": 0.6, "d": 0.6, "h": 0.5}], "links": [link]}


def check_svg(case, svg, limit=40 * 1024):
    """The contract for a published drawing: size, shape, palette, and no active or
    external content."""
    data = svg.encode("utf-8")
    case.assertLess(len(data), limit)
    root = ET.fromstring(svg)
    case.assertEqual(root.tag, SVG_NS + "svg")
    case.assertEqual(root.get("viewBox"), "0 0 1200 800")
    case.assertEqual((root.get("width"), root.get("height")), ("1200", "800"))
    ids = set()
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        case.assertIn(tag, ALLOWED_TAGS, "unexpected element <%s>" % tag)
        if el.get("id"):
            ids.add(el.get("id"))
        for k, v in el.attrib.items():
            case.assertNotIn("href", k)
            case.assertNotEqual(k, "style")
            case.assertFalse(k.startswith("on"), "event handler %s" % k)
            case.assertNotIn("javascript", v.lower())
        case.assertFalse((el.text or "").strip(), "text content in <%s>" % tag)
    for ref in re.findall(r"url\(([^)]*)\)", svg):
        case.assertTrue(ref.startswith("#"), "external reference %s" % ref)
        case.assertIn(ref[1:], ids)
    for c in re.findall(r'(?:fill|stroke|stop-color)="([^"]+)"', svg):
        case.assertTrue(c == "none" or re.fullmatch(r"#[0-9a-f]{6}", c) or c.startswith("url(#"), "colour %s" % c)


def variants(name, pdef):
    out = [{}]
    for key, prm in pdef.params.items():
        if prm.kind == "enum":
            out += [{key: c} for c in prm.choices]
        elif prm.kind == "bool":
            out.append({key: not prm.default})
    out += [{"tint": t} for t in pdef.tints]
    out += [{"facing": f} for f in (pdef.facings or ("right", "back-right", "back-left"))]
    return out


class DrawTest(unittest.TestCase):
    def test_samples_are_deterministic_and_safe(self):
        for name, scene in SAMPLES.items():
            with self.subTest(name):
                a = draw(copy.deepcopy(scene))
                b = draw(copy.deepcopy(scene))
                self.assertEqual(a, b)
                self.assertTrue(a.endswith("</svg>\n"))
                check_svg(self, a)

    def test_samples_meet_every_composition_rule(self):
        for name, scene in SAMPLES.items():
            with self.subTest(name):
                svg, rep = render(copy.deepcopy(scene), strict=True, story=STORIES[name])
                self.assertEqual(rep["problems"], [])
                self.assertEqual(rep["warnings"], [])
                self.assertEqual(svg, draw(scene))

    def test_drawing_does_not_change_the_spec(self):
        scene = copy.deepcopy(SAMPLES["glasses"])
        render(scene, strict=True, debug=True)
        self.assertEqual(scene, SAMPLES["glasses"])

    def test_numbers_have_one_decimal_at_most(self):
        svg = draw(SAMPLES["signing"])
        for d in re.findall(r' d="([^"]+)"', svg):
            for n in re.findall(r"-?\d+\.\d+", d):
                self.assertLessEqual(len(n.split(".")[1]), 1, n)

    def test_every_prop_draws_with_defaults_and_each_choice(self):
        for name, pdef in REGISTRY.items():
            for v in variants(name, pdef):
                item = {"prop": name, "at": [0, 0]}
                item.update(v)
                if pdef.container:
                    item["items"] = [{"prop": "box", "at": [0, 0], "w": 0.5, "d": 0.5, "h": 0.5}]
                with self.subTest(prop=name, variant=v):
                    svg = draw({"items": [item]})
                    check_svg(self, svg, limit=60 * 1024)

    def test_extreme_parameters_draw(self):
        for name, pdef in REGISTRY.items():
            for end in ("lo", "hi"):
                item = {"prop": name, "at": [0, 0]}
                for key, prm in pdef.params.items():
                    if prm.kind in ("num", "int"):
                        item[key] = getattr(prm, end)
                if pdef.container:
                    item["items"] = []
                with self.subTest(prop=name, end=end):
                    draw({"items": [item]})

    def test_cinnabar_appears_only_on_seals(self):
        """No prop paints cinnabar unless it is a seal mark the colour rule counts."""
        for name, pdef in REGISTRY.items():
            for v in variants(name, pdef):
                item = {"prop": name, "at": [0, 0]}
                item.update(v)
                if pdef.container:
                    item["items"] = []
                svg = draw({"items": [item]})
                marks = compose._seal_marks(validate({"items": [item]}).nodes[0])
                with self.subTest(prop=name, variant=v):
                    if not marks:
                        for c in CINNABAR:
                            self.assertNotIn(c, svg)

    def test_the_person_is_the_heros_figure(self):
        from scene import figure
        data = figure.load()
        self.assertEqual(data["source"], "tools/hero/person.py")
        roles = {role for role, _ in data["paths"]}
        self.assertTrue({"coat", "coat2", "legs", "hair", "phone"} <= roles)
        svg = draw({"items": [{"prop": "person", "at": [0, 0]}]})
        self.assertIn("#df7a00", svg)
        check_svg(self, svg)
        with self.assertRaises(SpecError) as cm:
            draw({"items": [{"prop": "person", "at": [0, 0], "facing": "left"}]})
        self.assertIn("can only face back-right", str(cm.exception))


class CompositionTest(unittest.TestCase):
    def test_the_plate_runs_off_the_canvas_by_default(self):
        sc, defs = compose._build(copy.deepcopy(SAMPLES["signing"]))
        _, cam = compose._camera(sc, defs, True)
        s0, s1, t0, t1 = sc.ground_box
        for x, y in ((0, compose.H), (compose.W, compose.H)):
            u = (x - cam.ox) / (cam.k * 0.894)
            v = (y - cam.oy) / (cam.k * 0.447)
            s, t = (u + v) / 2, (u - v) / 2
            self.assertTrue(s0 < s < s1 and t0 < t < t1, (x, y))
        # the fit camera keeps the whole plate in view, with its shadow
        fit = dict(copy.deepcopy(SAMPLES["signing"]), camera={"zoom": "fit"})
        self.assertIn('id="sg"', draw(fit))
        self.assertNotIn('id="sg"', draw(SAMPLES["signing"]))

    def test_the_items_camera_frames_the_props_tightly(self):
        _, rep = render(SAMPLES["glasses"])
        self.assertGreater(max(rep["cover"]), 0.85)

    def test_strict_needs_a_focal_object(self):
        scene = {k: v for k, v in copy.deepcopy(SAMPLES["signing"]).items() if k != "focal"}
        draw(scene)
        with self.assertRaises(SpecError) as cm:
            draw(scene, strict=True)
        self.assertIn('"focal"', str(cm.exception))
        with self.assertRaises(SpecError) as cm:
            draw(dict(scene, focal="modle"))
        self.assertIn("did you mean 'model'", str(cm.exception))

    def test_the_focal_object_must_be_large_and_central(self):
        scene = {"focal": "small", "items": [
            {"prop": "box", "id": "small", "at": [0, 0], "w": 0.5, "d": 0.5, "h": 0.5},
            {"prop": "server_rack", "id": "a", "at": [-4, 4]}, {"prop": "server_rack", "id": "b", "at": [4, -4]}]}
        _, rep = render(scene, strict=True)
        self.assertTrue(any("px tall" in p and "small" in p for p in rep["problems"]), rep["problems"])
        scene = {"focal": "edge", "items": [
            {"prop": "server_rack", "id": "edge", "at": [-5, 0], "units": 9},
            {"prop": "box", "id": "far", "at": [5, 0], "w": 0.3, "d": 0.3, "h": 0.3}]}
        _, rep = render(scene, strict=True)
        self.assertTrue(any("centred at" in p for p in rep["problems"]), rep["problems"])

    def test_a_hidden_prop_is_refused_and_named_with_its_cover(self):
        _, rep = render(copy.deepcopy(HIDDEN), strict=True)
        self.assertTrue(any("packet 'cex'" in p and "laptop 'tool' covers it" in p for p in rep["problems"]), rep)
        allowed = copy.deepcopy(HIDDEN)
        allowed["items"][4]["allow_hidden"] = True
        _, rep = render(allowed, strict=True)
        self.assertEqual(rep["problems"], [])

    def test_covered_links_are_reported(self):
        _, rep = render(copy.deepcopy(HIDDEN), strict=True)
        self.assertTrue(any(w.startswith("links[1] (net to claim)") and "start is hidden behind laptop 'tool'" in w
                            for w in rep["warnings"]), rep["warnings"])

    def test_arcs_are_sorted_with_the_props(self):
        """An arc from a.top to b.top passes behind a tall wall in front of it: in the depth
        layer most of it is covered; drawn over everything, none of it is."""
        base = {"items": [{"prop": "box", "id": "a", "at": [-3, 0], "w": 0.6, "d": 0.6, "h": 0.4},
                          {"prop": "box", "id": "b", "at": [0, 3], "w": 0.6, "d": 0.6, "h": 0.4},
                          {"prop": "box", "id": "wall", "at": [0, -0.2], "w": 4.5, "d": 0.6, "h": 4.0}],
                "links": [{"from": "a.top", "to": "b.top", "route": "arc", "lift": 0.6}]}
        _, rep = render(copy.deepcopy(base), analyse=True)
        self.assertTrue(any(w.startswith("links[0]") for w in rep["warnings"]), rep["warnings"])
        over = copy.deepcopy(base)
        over["links"][0]["layer"] = "over"
        _, rep = render(over, analyse=True)
        self.assertEqual(rep["warnings"], [])

    def test_a_dashed_link_split_by_a_prop_keeps_its_rhythm(self):
        """An arc rises behind a box, passes over it and comes down in front: it is drawn in a
        few runs with the box between them, and a later run carries on the dash pattern."""
        scene = {"items": [{"prop": "box", "id": "a", "at": [-2, 2], "w": 0.6, "d": 0.6, "h": 0.4},
                           {"prop": "box", "id": "b", "at": [2, -2], "w": 0.6, "d": 0.6, "h": 0.4},
                           {"prop": "box", "id": "mid", "at": [0, 0], "w": 0.6, "d": 0.6, "h": 1.5}],
                 "links": [{"from": "a.top", "to": "b.top", "route": "arc", "lift": 2.5, "style": "dashed"}]}
        svg = draw(scene)
        runs = re.findall(r'<path d="[^"]*" fill="none" stroke="#df7a00"[^>]*>', svg)
        self.assertTrue(2 <= len(runs) <= 3, runs)
        self.assertTrue(any("stroke-dashoffset" in r for r in runs[1:]), runs)
        between = svg[svg.index(runs[0]) + len(runs[0]):svg.index(runs[1])]
        self.assertIn('fill="#c7ccd3"', between)   # the middle box's shaded face, drawn between two runs

    def test_debug_overlay_is_for_drafts_only(self):
        svg, _ = render(copy.deepcopy(SAMPLES["glasses"]), debug=True)
        self.assertIn("<text", svg)
        self.assertIn(">cvm</text>", svg)
        self.assertNotIn("<text", draw(SAMPLES["glasses"]))

    def test_at_uv_places_like_at(self):
        a = draw({"items": [{"prop": "box", "at": [1.0, -2.0]}, {"prop": "box", "at": [-2, 1]}]})
        b = draw({"items": [{"prop": "box", "at_uv": [-1.0, 3.0]}, {"prop": "box", "at": [-2, 1]}]})
        self.assertEqual(a, b)
        with self.assertRaises(SpecError):
            draw({"items": [{"prop": "box", "at": [0, 0], "at_uv": [0, 0]}]})


class LinkTest(unittest.TestCase):
    """Where links start and end, how they run, and what they carry."""

    def test_a_link_to_a_sparse_prop_ends_at_its_port(self):
        """A magnifier is mostly empty space: a link that names it ends at the tip of its
        handle, and one that ends on the floor under its lens is a problem."""
        items = [{"prop": "box", "id": "a", "at": [-3, -1], "w": 0.6, "d": 0.6, "h": 0.5},
                 {"prop": "magnifier", "id": "m", "at": [0.5, -0.5]}]
        sc = validate({"items": items, "links": [{"from": "a", "to": "m"}]})
        self.assertEqual(sc.links[0].layer, "under")
        self.assertLess(compose._dist(sc.links[0].pieces[-1][-1][:2] + (0.0,), sc.by_id["m"].anchors["tip"][:2] + (0.0,)), 0.15)
        _, rep = render({"items": items, "links": [{"from": "a", "to": "m"}]}, analyse=True)
        self.assertEqual(rep["problems"], [])
        _, rep = render({"items": items, "links": [{"from": "a", "to": "m.lens", "route": "floor"}]}, analyse=True)
        self.assertTrue(any("its end stops" in p and "magnifier 'm'" in p and "tip" in p for p in rep["problems"]), rep["problems"])

    def test_links_from_the_person_start_at_the_phone(self):
        sc = validate({"items": [{"prop": "person", "id": "me", "at": [-2, -2]}, {"prop": "box", "id": "b", "at": [2, 1]}],
                       "links": [{"from": "me", "to": "b"}]})
        lk = sc.links[0]
        self.assertEqual(lk.pieces[0][0], sc.by_id["me"].anchors["phone"])
        self.assertEqual(lk.layer, "depth")
        # the line meets the box where it reaches its side, not at its base
        s0, s1, t0, t1, h0, h1 = sc.by_id["b"].bbox
        end = lk.pieces[-1][-1]
        self.assertTrue(min(abs(end[0] - s0), abs(end[0] - s1), abs(end[1] - t0), abs(end[1] - t1), abs(end[2] - h1)) < 1e-6, end)

    def test_straight_is_the_default_and_lies_on_the_floor(self):
        sc = validate(two_boxes())
        lk = sc.links[0]
        self.assertEqual(lk.layer, "under")
        self.assertEqual(len(lk.path_cmds[0]), 2)               # one segment
        a, b = lk.pieces[0][0], lk.pieces[0][-1]
        # stopped where the boxes start on screen: a's right corner, b's front face
        self.assertTrue(-1.8 < a[0] < -1.5 and 1.3 < b[0] < 1.8, (a, b))
        self.assertAlmostEqual(a[2], 0.012)
        with self.assertRaises(SpecError) as cm:
            draw(two_boxes(bend="t"))
        self.assertIn('"route": "floor"', str(cm.exception))

    def test_floor_routes_that_double_back_are_reported(self):
        """An L whose legs run toward the front and back turns through an acute angle on
        screen (a hook); a straight link between the same props does not."""
        scene = {"items": [{"prop": "box", "id": "a", "at": [-2, 2], "w": 0.6, "d": 0.6, "h": 0.5},
                           {"prop": "box", "id": "b", "at": [2, -2], "w": 0.6, "d": 0.6, "h": 0.5}],
                 "links": [{"from": "a", "to": "b", "route": "floor"}]}
        _, rep = render(copy.deepcopy(scene), analyse=True)
        self.assertTrue(any("doubles back" in w for w in rep["warnings"]), rep["warnings"])
        del scene["links"][0]["route"]
        _, rep = render(scene, analyse=True)
        self.assertEqual(rep["warnings"], [])
        # an L whose legs both run toward the right turns gently, as the hero's traces do
        _, rep = render(two_boxes(route="floor", to=[2, 3, 0]), analyse=True)
        self.assertFalse(any("doubles back" in w for w in rep["warnings"]), rep["warnings"])
        self.assertEqual(compose.CORNER, 0.15)

    def test_an_arc_comes_down_onto_a_top_from_above(self):
        scene = {"items": [{"prop": "box", "id": "low", "at": [3, 0], "w": 0.8, "d": 0.8, "h": 0.8},
                           {"prop": "box", "id": "tall", "at": [0, 1], "w": 0.8, "d": 0.8, "h": 3.0}],
                 "links": [{"from": "low.top", "to": "tall.top", "route": "arc", "lift": 0.3}]}
        sc = validate(copy.deepcopy(scene))
        pts = sc.links[0].pieces[0]
        top = sc.by_id["tall"].bbox[5]
        s0, s1, t0, t1 = sc.by_id["tall"].bbox[:4]
        over = [p for p in pts if s0 <= p[0] <= s1 and t0 <= p[1] <= t1]
        self.assertTrue(over and all(p[2] >= top - 1e-6 for p in over), over)
        self.assertGreaterEqual(max(p[2] for p in pts), top + compose.ARC_STUB - 1e-6)
        _, rep = render(scene, analyse=True)
        self.assertEqual(rep["warnings"], [])
        # a straight line from high up to the tall box's base runs through its side
        _, rep = render({"items": scene["items"], "links": [{"from": [3, 3, 4], "to": "tall.base"}]}, analyse=True)
        self.assertTrue(any("enters box 'tall' through a side" in w for w in rep["warnings"]), rep["warnings"])

    def test_packets_go_where_they_are_told_and_are_checked(self):
        sc = validate(two_boxes(packets=[0.2, 0.7]))
        self.assertEqual([pk.f for pk in sc.links[0].packets], [0.2, 0.7])
        self.assertEqual(len(validate(two_boxes(packets=3)).links[0].packets), 3)
        for bad in ([0.5] * 7, [1.2], "two", True):
            with self.assertRaises(SpecError):
                draw(two_boxes(packets=bad))
        # a packet behind a wall is a problem; one beside a third prop is a warning
        wall = {"prop": "box", "id": "wall", "at": [0.6, -0.6], "w": 0.6, "d": 0.3, "h": 1.5}
        scene = two_boxes(packets=[0.5])
        scene["items"].append(wall)
        _, rep = render(scene, analyse=True)
        self.assertTrue(any(p.startswith("packet 1 of links[0]") and "box 'wall' covers it" in p for p in rep["problems"]), rep)
        near = {"prop": "box", "id": "near", "at": [0, 0.42], "w": 0.4, "d": 0.4, "h": 0.4}
        scene = two_boxes(packets=[0.5])
        scene["items"].append(near)
        _, rep = render(scene, analyse=True)
        self.assertTrue(any(w.startswith("packet 1 of links[0]") and "touches box 'near'" in w for w in rep["warnings"]), rep)
        scene["links"][0]["packets"] = [0.2]
        _, rep = render(scene, analyse=True)
        self.assertFalse(any("touches" in w for w in rep["warnings"]), rep)

    def test_crossing_links_are_reported(self):
        items = [{"prop": "box", "id": k, "at": at, "w": 0.5, "d": 0.5, "h": 0.4}
                 for k, at in (("a", [-2, -2]), ("b", [2, 2]), ("c", [-2, 2]), ("d", [2, -2]))]
        _, rep = render({"items": items, "links": [{"from": "a", "to": "b"}, {"from": "c", "to": "d"}]}, analyse=True)
        self.assertTrue(any("links[0] (a to b) and links[1] (c to d) cross at" in w for w in rep["warnings"]), rep["warnings"])
        _, rep = render({"items": items, "links": [{"from": "a", "to": "c"}, {"from": "d", "to": "b"}]}, analyse=True)
        self.assertEqual(rep["warnings"], [])

    def test_link_weight_stops_growing_at_zoom_two(self):
        svg, rep = render(copy.deepcopy(SAMPLES["interposer"]))
        self.assertGreater(rep["zoom"], 2.5)
        widths = [float(w) for w in re.findall(r'stroke="#df7a00" stroke-width="([\d.]+)"', svg)]
        self.assertTrue(widths and max(widths) <= 0.055 * compose.LINK_KMAX + 0.05, widths)

    def test_via_points_may_name_anchors(self):
        scene = {"items": [{"prop": "box", "id": "a", "at": [-3, 0]}, {"prop": "gate", "id": "g", "at": [0, 0], "tint": "neutral"},
                           {"prop": "box", "id": "b", "at": [3, 0]}],
                 "links": [{"from": "a", "to": "b", "route": "via", "via": ["g.opening"]}]}
        named = draw(copy.deepcopy(scene))
        scene["links"][0]["via"] = [list(validate(scene).by_id["g"].anchors["opening"])]
        self.assertEqual(draw(copy.deepcopy(scene)), named)
        scene["links"][0]["via"] = ["g.nowhere"]
        with self.assertRaises(SpecError) as cm:
            draw(scene)
        self.assertIn("no anchor 'nowhere'", str(cm.exception))


class OutlineTest(unittest.TestCase):
    def test_props_get_a_hairline_outline(self):
        svg = draw({"items": [{"prop": "box", "at": [0, 0]}]})
        self.assertIn('fill="none" stroke="#c3c9d0" stroke-width="2.4"', svg)
        # under the prop: the outline comes before the box's faces
        self.assertLess(svg.index('stroke="#c3c9d0" stroke-width="2.4"'), svg.index('fill="#f3f4f6"'))
        # the person, the zone and glass have none
        for item in ({"prop": "person", "at": [0, 0]}, {"prop": "zone", "at": [0, 0]}, {"prop": "glass_box", "at": [0, 0]}):
            with self.subTest(item["prop"]):
                self.assertNotIn('stroke-width="2.4"', draw({"ground": {"kind": "none"}, "items": [item]}))


class ColourTest(unittest.TestCase):
    def assertSpecError(self, scene, *fragments, **kw):
        with self.assertRaises(SpecError) as cm:
            draw(scene, **kw)
        for f in fragments:
            self.assertIn(f, str(cm.exception))

    def test_cinnabar_is_for_seals(self):
        self.assertSpecError({"items": [{"prop": "ledger", "at": [0, 0], "tint": "seal"}]}, "tint 'seal'", "cinnabar is for seals")
        base = [{"prop": "box", "id": "a", "at": [-2, 0]}, {"prop": "box", "id": "b", "at": [2, 0]}]
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "b", "color": "seal"}]}, "never a link")
        three = [{"prop": "seal", "at": [-3, 0]}, {"prop": "stamp", "at": [0, -3]},
                 {"prop": "document", "at": [3, 0], "seal": "seal"}]
        self.assertSpecError({"items": three}, "3 cinnabar marks")
        draw({"items": three[:2]})

    def test_one_glow_per_picture_lamps_aside(self):
        base = [{"prop": "box", "id": "a", "at": [-2, 0]}, {"prop": "box", "id": "b", "at": [2, 0]}]
        self.assertSpecError({"items": base + [{"prop": "packet", "at": [0, 3], "glow": True}],
                              "links": [{"from": "a", "to": "b", "glow": True}]}, "2 glows")
        draw({"items": base + [{"prop": "interposer", "at": [0, 3]}], "links": [{"from": "a", "to": "b", "glow": True}]})
        # a lamp with a wide halo counts as a glow
        from scene.iso import Glow
        sc = validate({"items": base, "links": [{"from": "a", "to": "b", "glow": True}]})
        sc.nodes[0].parts[0].els.append(Glow((0, 0, 0.5), 0.3, "#e2b93b", lamp=True))
        with self.assertRaises(SpecError) as cm:
            compose.check_colours(sc, [{"glow": True}], None)
        self.assertIn("2 glows", str(cm.exception))
        sc.nodes[0].parts[0].els[-1].r = 0.1
        compose.check_colours(sc, [{"glow": True}], None)

    def test_story_tints(self):
        scene = {"items": [{"prop": "bars", "at": [0, 0]}]}
        self.assertSpecError(scene, "evaluations tint", "allow models", story={"models"})
        draw(scene, story={"evaluations"})
        self.assertSpecError({"items": [{"prop": "gate", "at": [0, 0]}]}, "tee tint", story={"models"})
        self.assertSpecError({"items": [{"prop": "box", "at": [0, 0], "material": "outputslight"}]}, "outputs tint",
                             story={"models"})
        base = [{"prop": "box", "id": "a", "at": [-2, 0]}, {"prop": "box", "id": "b", "at": [2, 0]}]
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "b", "color": "agents"}]}, "links[0]",
                             story={"models"})

    def test_story_tints_come_from_the_front_matter(self):
        tmp = tempfile.mkdtemp(prefix="illustrate-test-")
        try:
            def story(text):
                with open(os.path.join(tmp, "en.md"), "w", encoding="utf-8") as f:
                    f.write(text)
                return illustrate.story_tints(tmp)
            self.assertEqual(story("---\ntitle: X\ntopics: [confidential-computing]\nlayers: [runtime, hardware]\n---\nBody\n"),
                             {"tee", "pcb"})
            self.assertEqual(story("---\ntopics: [supply-chain]\nlayers:\n  - models\n---\n"), {"models"})
            self.assertEqual(story("---\ntopics: [confidential-computing, evaluation-audits]\nlayers: [evaluations]\n---\n"),
                             {"evaluations", "tee"})
            self.assertIsNone(story("---\ntitle: No layers\n---\n"))
            os.remove(os.path.join(tmp, "en.md"))
            self.assertIsNone(illustrate.story_tints(tmp))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class ValidationTest(unittest.TestCase):
    def assertSpecError(self, scene, *fragments):
        with self.assertRaises(SpecError) as cm:
            draw(scene)
        msg = str(cm.exception)
        for f in fragments:
            self.assertIn(f, msg)
        return msg

    def test_unknown_prop_suggests_a_name(self):
        self.assertSpecError({"items": [{"prop": "server_rak", "at": [0, 0]}]}, "unknown prop 'server_rak'", "server_rack")

    def test_unknown_parameter(self):
        self.assertSpecError({"items": [{"prop": "server_rack", "at": [0, 0], "unit": 4}]},
                             "items[0]", "unknown key 'unit'", "units")

    def test_bad_values(self):
        self.assertSpecError({"items": [{"prop": "server_rack", "at": [0, 0], "units": 40}]}, "units", "out of range")
        self.assertSpecError({"items": [{"prop": "monitor", "at": [0, 0], "content": "charts"}]}, "content", "chart")
        self.assertSpecError({"items": [{"prop": "gate", "at": [0, 0], "tint": "teal"}]}, "tint 'teal'")
        self.assertSpecError({"items": [{"prop": "box", "at": [0, 0], "facing": "up"}]}, "facing 'up'")
        self.assertSpecError({"items": [{"prop": "box", "at": [0]}]}, "'at' must be")
        self.assertSpecError({"items": [{"prop": "box", "at": [0, 0], "lip": "yes"}]}, "true or false")
        self.assertSpecError({"items": [{"prop": "box", "at": [0, 0], "allow_hidden": 1}]}, "allow_hidden must be true or false")
        self.assertSpecError({"items": []}, "non-empty")
        self.assertSpecError({"items": [{"prop": "box", "at": [0, 0]}], "colour": 1}, "unknown key 'colour'")

    def test_values_of_the_wrong_type_are_spec_errors(self):
        """A list or an object where a name belongs, or a number JSON readers accept but
        no parameter can hold, is a SpecError naming the key, never a TypeError."""
        two = [{"prop": "box", "id": "a", "at": [-2, 0]}, {"prop": "box", "id": "b", "at": [2, 0]}]
        cases = [
            ({"items": [{"prop": ["box"], "at": [0, 0]}]}, "items[0]: prop: expected a name"),
            ({"items": [{"prop": "box", "at": [0, 0], "facing": ["left"]}]}, "facing: expected a name"),
            ({"items": [{"prop": "box", "at": [0, 0], "tint": {"tee": 1}}]}, "tint: expected a name"),
            ({"items": two[:1] + [{"prop": "box", "at": [3, 0], "on": ["a"]}]}, "on: expected a name"),
            ({"items": two[:1], "focal": [1]}, "scene: focal: expected a name"),
            ({"items": two[:1], "backdrop": ["white"]}, "scene: backdrop: expected a name"),
            ({"items": two[:1], "ground": {"kind": {"plate": 1}}}, "ground: kind: expected a name"),
            ({"items": two, "links": [{"from": "a", "to": "b", "color": ["data"]}]}, "links[0]: color: expected a name"),
            ({"items": two, "links": [{"from": "a", "to": "b", "layer": ["over"]}]}, "links[0]: layer: expected a name"),
            ({"items": [{"prop": "server_rack", "at": [0, 0], "units": float("inf")}]}, "units: expected a finite number"),
            ({"items": [{"prop": "server_rack", "at": [0, 0], "units": float("nan")}]}, "units: expected a finite number"),
        ]
        for scene, fragment in cases:
            with self.subTest(fragment):
                self.assertSpecError(scene, fragment)

    def test_ids(self):
        self.assertSpecError({"items": [{"prop": "box", "id": "a", "at": [0, 0]}, {"prop": "box", "id": "a", "at": [3, 0]}]},
                             "used twice")
        self.assertSpecError({"items": [{"prop": "box", "id": "Rack 1", "at": [0, 0]}]}, "lower case")
        self.assertSpecError({"items": [{"prop": "box", "on": "desk", "at": [0, 0]}]}, "'on' names 'desk'")

    def test_overlap_is_refused_unless_allowed(self):
        a = {"prop": "box", "at": [0, 0], "w": 2}
        b = {"prop": "box", "at": [0.5, 0], "w": 2}
        self.assertSpecError({"items": [a, b]}, "overlap", "allow_overlap")
        b2 = dict(b, allow_overlap=True)
        draw({"items": [a, b2]})

    def test_stacking_with_on_is_not_an_overlap(self):
        svg = draw({"items": [{"prop": "desk", "id": "desk", "at": [0, 0]},
                              {"prop": "laptop", "on": "desk", "at": [0, 0]}]})
        check_svg(self, svg)

    def test_enclosure_contents_must_fit(self):
        self.assertSpecError({"items": [{"prop": "enclosure", "at": [0, 0], "w": 2, "d": 2, "h": 1, "items": [
            {"prop": "server_rack", "at": [0, 0]}]}]}, "does not fit inside the enclosure")

    def test_off_plate_and_off_canvas(self):
        self.assertSpecError({"ground": {"size": [4, 4]}, "items": [{"prop": "box", "at": [5, 0]}]}, "off the ground plate")
        draw({"ground": {"size": [4, 4]}, "items": [{"prop": "box", "at": [5, 0], "outside": True}]})
        self.assertSpecError({"camera": {"zoom": 3}, "items": [{"prop": "server_rack", "at": [0, 0]},
                                                               {"prop": "box", "at": [6, 6]}]}, "runs off", "fits at zoom")

    def test_links(self):
        base = [{"prop": "box", "id": "a", "at": [-2, 0]}, {"prop": "box", "id": "b", "at": [2, 0]}]
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "c"}]}, "no item has id 'c'")
        self.assertSpecError({"items": base, "links": [{"from": "a.lid", "to": "b"}]}, "no anchor 'lid'")
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "b", "style": "wavy"}]}, "style 'wavy'")
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "b", "colour": "data"}]}, "unknown key 'colour'")
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "b", "packets": 9}]}, "packets")
        self.assertSpecError({"items": base, "links": [{"from": "a", "to": "b", "layer": "top"}]}, "layer 'top'")
        self.assertSpecError({"items": base, "links": [{"from": "a.top", "to": "a.top", "route": "straight"}]}, "no length")
        for route in ("floor", "straight", "arc"):
            for layer in ("under", "depth", "over"):
                draw({"items": base, "links": [{"from": "a", "to": "b.top", "route": route, "packets": 2, "arrow": True,
                                                "layer": layer, "style": "dotted"}]})
        draw({"items": base, "links": [{"from": "a", "to": "b", "route": "via", "via": [[0, 2, 0.5]], "style": "broken"}]})

    def test_older_parameter_names(self):
        a = draw({"items": [{"prop": "neural_net", "at": [0, 0], "columns": [2, 3]}]})
        b = draw({"items": [{"prop": "neural_net", "at": [0, 0], "layers": [2, 3]}]})
        self.assertEqual(a, b)
        self.assertSpecError({"items": [{"prop": "neural_net", "at": [0, 0], "layers": [2, 3], "columns": [2, 3]}]},
                             "'columns' or its older name 'layers'")

    def test_validate_returns_without_drawing(self):
        sc = validate(SAMPLES["interposer"])
        self.assertEqual(len(sc.nodes), 5)


class EnvelopeTest(unittest.TestCase):
    def envelope(self, scene=None):
        return {"kind": "illustration", "alt": {"en": "A box.", "zh": "一个盒子。"},
                "caption": {"en": "Illustration: a box. It does not show a real box.", "zh": "示意图：一个盒子，并非真实的盒子。"},
                "scene": scene or {"items": [{"prop": "box", "at": [0, 0]}]}}

    def test_envelope_rules(self):
        illustrate.check_envelope(self.envelope(), "x")
        self.assertIsNone(illustrate.check_envelope({"kind": "photo"}, "x"))
        bad = self.envelope()
        bad["alt"] = {"en": "A box."}
        with self.assertRaises(SpecError):
            illustrate.check_envelope(bad, "x")
        bad = self.envelope()
        bad["credit"] = "me"
        with self.assertRaises(SpecError):
            illustrate.check_envelope(bad, "x")
        bad = self.envelope()
        bad["svg_sha256"] = "XYZ"
        with self.assertRaises(SpecError):
            illustrate.check_envelope(bad, "x")
        # None means "a photo" to the callers, so an illustration's null scene is missing
        bad = self.envelope()
        bad["scene"] = None
        with self.assertRaises(SpecError) as cm:
            illustrate.check_envelope(bad, "x")
        self.assertIn("missing scene", str(cm.exception))

    def test_captions_open_as_the_content_guide_says(self):
        for lang, text in (("en", "Conceptual illustration: a box."), ("zh", "概念示意图：一个盒子。")):
            bad = self.envelope()
            bad["caption"][lang] = text
            with self.assertRaises(SpecError) as cm:
                illustrate.check_envelope(bad, "x")
            self.assertIn("caption.%s must open with" % lang, str(cm.exception))
        import lint_content
        self.assertEqual(illustrate.CAPTION_OPENING, lint_content.CAPTION_OPENING)

    def test_the_linter_reads_the_alt_text_and_caption(self):
        """tools/lint_content.py holds an illustration's texts to the house style, American
        spelling included (in lower case, so a proper name passes), and its caption to the
        opening and the "does not depict" rule."""
        import lint_content
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            data = self.envelope()
            data["alt"]["en"] = "A grey plate centred under the National Cyber Security Centre's colourful sign."
            data["caption"]["en"] = "A box on a plate."
            with open(os.path.join(tmp, "illustration.json"), "w", encoding="utf-8") as f:
                json.dump(data, f)
            issues = lint_content.illustration_issues(Path(tmp))
        spelling = [i for i in issues if "American spelling" in i]
        self.assertEqual([i.rsplit(" ", 1)[1] for i in spelling], ["'grey'", "'centred'", "'colourful'"])
        self.assertTrue(all(i.startswith("illustration.json: alt.en: ") for i in spelling), spelling)
        self.assertIn("illustration.json: caption.en: start with 'Illustration:'", issues)
        self.assertIn("illustration.json: caption.en: say what the picture does not depict", issues)
        self.assertEqual(len(issues), 5, issues)


class CommandTest(unittest.TestCase):
    """--write, --check and --spec on a temporary copy of the layout they work on."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="illustrate-test-")
        os.makedirs(os.path.join(self.tmp, "static", "media"))
        self.slug = "example-story"
        self.add_story(self.slug, SAMPLES["signing"])
        os.makedirs(os.path.join(self.tmp, "content", "articles", "no-picture"))
        self.spec = os.path.join(self.tmp, "content", "articles", self.slug, "illustration.json")
        self.svg = os.path.join(self.tmp, "static", "media", self.slug + ".svg")

    def add_story(self, slug, scene, layers="[models]"):
        d = os.path.join(self.tmp, "content", "articles", slug)
        os.makedirs(d)
        with open(os.path.join(d, "en.md"), "w", encoding="utf-8") as f:
            f.write("---\ntitle: Example\ntopics: [supply-chain]\nlayers: %s\n---\nBody.\n" % layers)
        data = EnvelopeTest().envelope(copy.deepcopy(scene))
        with open(os.path.join(d, "illustration.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = illustrate.main(list(args) + ["--root", self.tmp])
        return code, out.getvalue() + err.getvalue()

    def test_write_then_check(self):
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("missing", out)
        code, out = self.run_cli("--write")
        self.assertEqual(code, 0, out)
        with open(self.svg, "rb") as f:
            svg = f.read()
        with open(self.spec, encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["svg_sha256"], hashlib.sha256(svg).hexdigest())
        self.assertEqual(svg.decode("utf-8"), draw(SAMPLES["signing"]))
        code, out = self.run_cli("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("focal props: weights 1", out)
        self.assertEqual(self.run_cli("--check", self.slug)[0], 0)
        # a second write changes nothing
        before = os.path.getmtime(self.spec)
        self.assertEqual(self.run_cli("--write")[0], 0)
        self.assertEqual(os.path.getmtime(self.spec), before)

    def test_write_refuses_a_spec_that_breaks_the_rules(self):
        with open(self.spec, encoding="utf-8") as f:
            data = json.load(f)
        del data["scene"]["focal"]
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        code, out = self.run_cli("--write")
        self.assertEqual(code, 1)
        self.assertIn('"focal"', out)
        self.assertFalse(os.path.exists(self.svg))
        data["scene"] = copy.deepcopy(SAMPLES["glasses"])     # indigo, in a story tagged [models]
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        code, out = self.run_cli("--write")
        self.assertEqual(code, 1)
        self.assertIn("tee tint", out)

    def test_check_finds_stale_drawings_and_digests(self):
        self.run_cli("--write")
        with open(self.svg, "ab") as f:
            f.write(b"<!-- edited -->")
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("differs from a fresh draw", out)
        self.run_cli("--write")
        with open(self.spec, encoding="utf-8") as f:
            data = json.load(f)
        data["scene"]["items"][0]["size"] = 1.8
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("svg_sha256 does not match", out)

    def test_check_reports_bad_specs_and_orphans(self):
        self.run_cli("--write")
        with open(os.path.join(self.tmp, "static", "media", "gone.svg"), "w") as f:
            f.write("<svg/>")
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("gone.svg has no illustration spec", out)
        os.remove(os.path.join(self.tmp, "static", "media", "gone.svg"))
        with open(self.spec, encoding="utf-8") as f:
            data = json.load(f)
        data["scene"]["items"][0]["prop"] = "weight"
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("unknown prop 'weight'", out)
        self.assertNotIn("has no illustration spec", out)   # a broken spec still owns its drawing

    def test_one_bad_spec_does_not_stop_the_others(self):
        """A malformed value, or an unexpected error drawing one spec, is reported for that
        slug and the run goes on to report the rest."""
        self.add_story("second-story", SAMPLES["signing"])
        self.assertEqual(self.run_cli("--write")[0], 0)
        with open(self.spec, encoding="utf-8") as f:
            data = json.load(f)
        data["scene"]["items"][0]["facing"] = ["left"]
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump(data, f)
        second = os.path.join(self.tmp, "static", "media", "second-story.svg")
        with open(second, "ab") as f:
            f.write(b"<!-- edited -->")
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("example-story: items[0] (weights 'model'): facing: expected a name", out)
        self.assertIn("second-story: static/media/second-story.svg differs from a fresh draw", out)
        self.assertNotIn("Traceback", out)
        saved = illustrate.strict_svg

        def broken(scene, path):
            if "second-story" in path:
                raise TypeError("a bug in a prop")
            return saved(scene, path)
        illustrate.strict_svg = broken
        try:
            for mode in ("--check", "--write"):
                code, out = self.run_cli(mode)
                self.assertEqual(code, 1, mode)
                self.assertIn("second-story: TypeError: a bug in a prop", out)
                self.assertIn("example-story: items[0] (weights 'model'): facing", out)
        finally:
            illustrate.strict_svg = saved

    def test_a_drawing_left_behind_by_a_photo_is_an_orphan(self):
        self.add_story("second-story", SAMPLES["signing"])
        self.assertEqual(self.run_cli("--write")[0], 0)
        with open(self.spec, "w", encoding="utf-8") as f:
            json.dump({"kind": "photo"}, f)
        code, out = self.run_cli("--check")
        self.assertEqual(code, 1)
        self.assertIn("static/media/%s.svg has no illustration spec" % self.slug, out)
        os.remove(self.svg)
        code, out = self.run_cli("--check")
        self.assertEqual(code, 0, out)
        self.assertIn("1 illustration up to date", out)   # the photo is not counted

    def test_check_limits_how_often_one_prop_leads(self):
        self.add_story("second-story", SAMPLES["signing"])
        self.assertEqual(self.run_cli("--write")[0], 0)
        saved = illustrate.MAX_FOCAL_USES
        illustrate.MAX_FOCAL_USES = 1
        try:
            code, out = self.run_cli("--check")
        finally:
            illustrate.MAX_FOCAL_USES = saved
        self.assertEqual(code, 1)
        self.assertIn("weights is the focal prop of 2 pictures (at most 1)", out)

    def test_no_specs_is_fine(self):
        os.remove(self.spec)
        self.assertEqual(self.run_cli("--check")[0], 0)
        self.assertEqual(self.run_cli("--write")[0], 0)

    def test_written_json_is_compact_and_lossless(self):
        data = EnvelopeTest().envelope(copy.deepcopy(SAMPLES["glasses"]))
        text = illustrate.pretty_json(data)
        self.assertEqual(json.loads(text), data)
        self.assertIn('{"prop": "glasses", "id": "glasses", "at": [2.72, -2.82]}', text)

    def test_spec_draft(self):
        out_svg = os.path.join(self.tmp, "draft.svg")
        code, out = self.run_cli("--spec", self.spec, "--out", out_svg)
        self.assertEqual(code, 0, out)
        self.assertIn("focal 'model' is", out)
        with open(out_svg, encoding="utf-8") as f:
            self.assertEqual(f.read(), draw(SAMPLES["signing"]))
        # a draft with problems is still drawn, and the problems are listed
        bare = os.path.join(self.tmp, "hidden.json")
        with open(bare, "w", encoding="utf-8") as f:
            json.dump(HIDDEN, f)
        code, out = self.run_cli("--spec", bare, "--out", out_svg, "--debug", "--layers", "evaluations")
        self.assertEqual(code, 1)
        self.assertIn("problem: items[4] (packet 'cex') shows only", out)
        self.assertIn("partly hidden: packet 'cex' shows 0% of itself (covered by laptop 'tool')", out)
        self.assertIn("warning: links[1]", out)
        with open(out_svg, encoding="utf-8") as f:
            self.assertIn("<text", f.read())

    def test_spec_names_what_keeps_it_from_drawing(self):
        """--spec on an envelope it cannot draw says why: a photo has nothing to draw, and an
        illustration without a scene is missing its scene (not "a photo")."""
        draft = os.path.join(self.tmp, "draft.json")
        out_svg = os.path.join(self.tmp, "draft.svg")
        envelope = EnvelopeTest().envelope()
        del envelope["scene"]
        cases = (({"kind": "photo"}, "is a photo spec; nothing to draw"),
                 (envelope, "draft.json: missing scene"),
                 (dict(envelope, credit="me"), "unknown key 'credit'"))
        for data, fragment in cases:
            with self.subTest(fragment):
                with open(draft, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                with self.assertRaises(SystemExit) as cm:
                    self.run_cli("--spec", draft, "--out", out_svg)
                self.assertIn(fragment, str(cm.exception.code))
                if data.get("kind") != "photo":
                    self.assertNotIn("photo", str(cm.exception.code))
                    self.assertIn("missing scene", str(cm.exception.code))
                self.assertFalse(os.path.exists(out_svg))


class RepositoryTest(unittest.TestCase):
    def test_committed_illustrations_are_current(self):
        """Every content/articles/*/illustration.json draws to its committed SVG."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = illustrate.main(["--check"])
        self.assertEqual(code, 0, err.getvalue())

    def test_catalog_is_current(self):
        with open(os.path.join(ROOT, "tools", "scene", "catalog.svg"), encoding="utf-8") as f:
            committed = f.read()
        self.assertEqual(committed, illustrate.catalog_svg()[0],
                         "redraw it: python3 tools/illustrate.py --catalog tools/scene/catalog.svg")

    def test_the_figure_matches_the_heros_person(self):
        from scene import figure
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(figure.main(["--check"]), 0, err.getvalue())

    def test_readme_documents_every_prop_and_parameter(self):
        with open(os.path.join(ROOT, "tools", "scene", "README.md"), encoding="utf-8") as f:
            readme = f.read()
        self.assertIn(illustrate.props_reference(), readme,
                      "regenerate the props reference: python3 tools/illustrate.py --props-md")
        for name, pdef in REGISTRY.items():
            self.assertIn("**`%s`** %s" % (name, illustrate.footprint_line(name)), readme, name)
            for key in pdef.params:
                self.assertIn("`%s`" % key, readme, "%s.%s" % (name, key))


if __name__ == "__main__":
    unittest.main()
