"""Lead photos: tools/photos.py (crops, the grade, metadata, its texts, the spec it writes and
--check) and what sitegen/content.py, sitegen/render.py and sitegen/discover.py do with a photo
spec's copies and edits. tests/test_sitegen.py's IllustratedBuildTests builds a project with
photos and checks the pages, the link previews and the manifest.

The end-to-end test that runs headless Chrome is skipped unless VP_CHROME_TESTS=1 is set, so
the suite needs no browser:

    VP_CHROME_TESTS=1 python3 -m unittest tests.test_photos -v
"""

import contextlib
import copy
import hashlib
import io
import json
import os
import re
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _path in (str(ROOT), str(ROOT / "tools")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import photos  # noqa: E402
from sitegen import content, discover, render  # noqa: E402
from sitegen.render import Site  # noqa: E402
from tests.test_sitegen import jpeg_header, photo_files, tiny_png, webp_header, write_photo  # noqa: E402

SLUG = "test-photo"
DELETE = object()


def photo_root(tmp, slug=SLUG, **fields):
    """A minimal project for one photo spec: content/articles/SLUG/ and static/media/, as
    tests/test_sitegen.py's write_photo() writes them."""
    root = Path(tmp)
    (root / "content" / "articles" / slug).mkdir(parents=True, exist_ok=True)
    spec = write_photo(root, slug, **fields)
    return root, root / "content" / "articles" / slug, spec


def mutate(spec, path, value):
    """SPEC with the field at PATH ("variants.list.width") set to VALUE, or removed for DELETE."""
    spec = copy.deepcopy(spec)
    *parents, last = path.split(".")
    node = spec
    for key in parents:
        node = node[key]
    if value is DELETE:
        node.pop(last, None)
    else:
        node[last] = value
    return spec


def save(folder, spec):
    (folder / content.LEAD_IMAGE_FILE).write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def exif_segment(orientation=1):
    """An APP1 EXIF segment with a camera make and an orientation, as cameras write."""
    tiff = (b"MM\x00*" + struct.pack(">I", 8) + struct.pack(">H", 2)
            + struct.pack(">HHII", 0x010F, 2, 4, 0x4D414B00) + struct.pack(">HHIHH", 0x0112, 3, 1, orientation, 0)
            + struct.pack(">I", 0))
    body = b"Exif\x00\x00" + tiff
    return b"\xff\xe1" + struct.pack(">H", len(body) + 2) + body


def segment(marker, body):
    return bytes([0xFF, marker]) + struct.pack(">H", len(body) + 2) + body


def riff(*chunks):
    body = b"WEBP" + b"".join(kind + struct.pack("<I", len(data)) + data + (b"\x00" if len(data) & 1 else b"")
                              for kind, data in chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def vp8(width, height):
    """A lossy WebP image chunk's start: a frame tag, the start code and the 14-bit sizes."""
    return b"\x00\x00\x00\x9d\x01\x2a" + struct.pack("<HH", width, height) + bytes(8)


def pipeline_files(slug=SLUG):
    """Header-only files with tools/photos.py's names and sizes, in its order: what --check expects."""
    return {f"{slug}.webp": riff((b"VP8 ", vp8(1600, 1067))), f"{slug}-800.webp": riff((b"VP8 ", vp8(800, 533))),
            f"{slug}-400.webp": riff((b"VP8 ", vp8(400, 267))), f"{slug}-og.jpg": jpeg_header(1200, 630)}


def pipeline_spec(root, slug=SLUG, files=None, **fields):
    """Write pipeline_files() (or FILES) and the spec photos.make_spec() makes for them."""
    files = files or pipeline_files(slug)
    media = root / content.MEDIA_DIR
    media.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (media / name).write_bytes(data)
    texts = {key: value for key, value in write_photo_texts().items()}
    texts.update(fields)
    by_role = dict(zip(photos.FILES, files.values()))
    spec = photos.make_spec(slug, by_role, "ef" * 32, (4000, 3000), [0, 166, 4000, 2668], [0, 400, 4000, 2100], texts)
    folder = root / "content" / "articles" / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / content.LEAD_IMAGE_FILE).write_text(photos.pretty_json(spec) + "\n", encoding="utf-8")
    return spec


def write_photo_texts():
    return {"alt": {"en": "A server rack in a data center aisle.", "zh": "数据中心过道里的一个服务器机架。"},
            "caption": {"en": "A data center. The photo does not show the systems in the story.",
                        "zh": "一座数据中心，照片并非报道所涉的系统。"},
            "credit": "Jane Doe / Wikimedia Commons", "license": "CC BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "source_url": "https://commons.wikimedia.org/wiki/File:Rack.jpg", "retrieved": "2026-10-24"}


def gradient_png(width, height):
    """An opaque RGB PNG with a horizontal red ramp and a vertical blue ramp, made without a browser."""
    ramp = bytes(x * 255 // (width - 1) for x in range(width))
    rows = []
    for y in range(height):
        row = bytearray(width * 3)
        row[0::3] = ramp
        row[1::3] = bytes([96]) * width
        row[2::3] = bytes([y * 255 // (height - 1)]) * width
        rows.append(b"\x00" + bytes(row))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 6)) + chunk(b"IEND", b""))


class GradeTest(unittest.TestCase):
    """GRADE "soft-1": CSS saturate(0.88) contrast(0.92), then a faint warm tone, the same on every pixel."""

    def test_the_grade_is_one_the_build_knows(self):
        self.assertIn(photos.GRADE, content.PHOTO_GRADES)
        self.assertEqual(set(photos.GRADES), set(content.PHOTO_GRADES))

    def test_the_matrix_is_css_saturate_then_contrast_then_the_warm_gains(self):
        s, c, gains = 0.88, 0.92, (1.012, 1.0, 0.976)
        # Filter Effects Module Level 1: saturate(s), then contrast(c) = c * v + (1 - c) / 2
        saturate = [[0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s],
                    [0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s],
                    [0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s]]
        want = []
        for i in range(3):
            want += [gains[i] * c * v for v in saturate[i]] + [gains[i] * 255 * (1 - c) / 2]
        for got, expected in zip(photos.grade_matrix(), want):
            self.assertAlmostEqual(got, expected, places=5)

    def test_the_grade_is_gentle_soft_and_faintly_warm(self):
        grade = photos.apply_grade
        self.assertEqual(grade((255, 255, 255)), (248, 245, 239))  # #f8f5ef: whites soften and warm
        self.assertEqual(grade((0, 0, 0)), (10, 10, 10))           # #0a0a0a: blacks lift, still neutral
        self.assertEqual(grade((128, 128, 128)), (129, 128, 125))  # #81807d
        # what the module docstring promises
        for colour in ("#f8f5ef", "#0a0a0a", "#81807d"):
            self.assertIn(colour, photos.__doc__)
        # less saturation: a strong red keeps its hue and loses some chroma; no channel moves much
        r, g, b = grade((208, 48, 32))
        self.assertTrue(r > g > b and (r - b) < (208 - 32), (r, g, b))
        for rgb in ((208, 48, 32), (32, 64, 192), (230, 200, 170), (20, 140, 60)):
            graded = grade(rgb)
            self.assertLessEqual(max(abs(a - b) for a, b in zip(graded, rgb)), 26, (rgb, graded))
            self.assertGreaterEqual(graded[0] - graded[2], rgb[0] - rgb[2] - 30, (rgb, graded))
        # never a channel out of range
        for v in (0, 1, 254, 255):
            self.assertTrue(all(0 <= x <= 255 for x in grade((v, 255 - v, v))))


class CropTest(unittest.TestCase):
    def test_focus_forms(self):
        self.assertEqual(photos.parse_focus(None), ("point", (0.5, 0.5)))
        self.assertEqual(photos.parse_focus("top"), ("point", (0.5, 0.0)))
        self.assertEqual(photos.parse_focus(" 0.25, 0.75 "), ("point", (0.25, 0.75)))
        self.assertEqual(photos.parse_focus([0.5, 0.35]), ("point", (0.5, 0.35)))
        self.assertEqual(photos.parse_focus("10,20,3000,2000"), ("box", (10, 20, 3000, 2000)))
        for bad in ("middle", "1.5,0.5", "0.5", "0.1,0.2,0.3", "10,20,0,100", "10.5,20,300,200", "-1,0,300,200", "a,b"):
            with self.subTest(bad=bad), self.assertRaises(photos.PhotoError):
                photos.parse_focus(bad)

    def test_the_crop_is_the_largest_box_around_the_focus(self):
        point = photos.parse_focus("0.5,0.3")
        crop, social = photos.plan((4000, 3000), point)
        self.assertEqual(crop, [0, 0, 4000, 2668])               # full width; the top, as far as it goes
        crop, social = photos.plan((6000, 3000), photos.parse_focus("right"))
        self.assertEqual(crop, [6000 - 4499, 0, 4499, 3000])     # full height, at the right edge
        crop, _ = photos.plan((5000, 3000), photos.parse_focus("2000,500,2500,2000"))
        self.assertEqual(crop, [2000, 666, 2500, 1667])          # the largest 3:2 box centred in the focus box

    def test_every_planned_crop_passes_the_builds_edit_checks(self):
        sizes = ((1600, 1067), (1600, 2400), (2400, 1600), (3024, 4032), (4032, 3024), (6000, 4000), (8000, 2000),
                 (1601, 5000), (4000, 4000))
        foci = ("center", "top", "bottom", "left", "right", "0,0", "1,1", "0.31,0.72")
        for size in sizes:
            for focus in foci:
                with self.subTest(size=size, focus=focus):
                    crop, social = photos.plan(size, photos.parse_focus(focus))
                    edits = {"source_sha256": "ab" * 32, "source_size": list(size), "crop": crop, "social_crop": social,
                             "grade": photos.GRADE}
                    content._photo_edits(edits, photos.PHOTO_SIZE, "test")
                    self.assertGreaterEqual(crop[2], 1600)
                    self.assertEqual(social[2], crop[2])          # the widest strip of the crop

    def test_the_link_preview_strip_follows_the_focus_inside_the_crop(self):
        crop, social = photos.plan((3000, 4000), photos.parse_focus("0.5,0.9"))
        self.assertEqual(crop[1] + crop[3], 4000)                  # the crop sits at the bottom
        self.assertEqual(social[1] + social[3], crop[1] + crop[3])  # and the strip at the crop's bottom
        crop, social = photos.plan((3000, 2000), photos.parse_focus("0.5,0.5"))
        self.assertEqual(crop, [0, 0, 3000, 2000])                 # a 3:2 frame is kept whole
        top, bottom = social[1] - crop[1], (crop[1] + crop[3]) - (social[1] + social[3])
        self.assertLessEqual(abs(top - bottom), 1)                  # centred, to the pixel

    def test_a_photo_is_never_enlarged(self):
        with self.assertRaisesRegex(photos.PhotoError, "at least 1600 pixels wide"):
            photos.plan((1500, 1000), photos.parse_focus("center"))
        with self.assertRaisesRegex(photos.PhotoError, "needs at least 1600"):
            photos.plan((4000, 3000), photos.parse_focus("0,0,1500,1000"))
        with self.assertRaisesRegex(photos.PhotoError, "reaches outside"):
            photos.plan((4000, 3000), photos.parse_focus("3000,0,2000,1500"))


class MetadataTest(unittest.TestCase):
    """The files carry no metadata: tools/photos.py strips what Chrome adds, and --check finds any."""

    def test_stripping_a_jpeg_keeps_the_image_data(self):
        icc = segment(0xE2, b"ICC_PROFILE\x00\x01\x01" + bytes(20))
        comment = segment(0xFE, b"made by a camera")
        adobe = segment(0xEE, b"Adobe" + bytes(7))
        plain = jpeg_header(1200, 630)
        raw = plain[:2] + segment(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00") + exif_segment(6) + icc \
            + comment + adobe + plain[2:]
        self.assertEqual(photos.metadata(raw, "x.jpg"), ["EXIF", "a colour profile", "a comment"])
        stripped = photos.strip_jpeg(raw)
        self.assertEqual(photos.metadata(stripped, "x.jpg"), [])
        self.assertEqual([m for m, _ in photos.jpeg_segments(stripped)], [0xE0, 0xEE, 0xDB, 0xC0])
        self.assertTrue(stripped.endswith(plain[-14:]))           # the scan is untouched
        self.assertEqual(content._raster_size(stripped, "JPEG"), (1200, 630))

    def test_stripping_a_webp_leaves_the_simple_format(self):
        extended = riff((b"VP8X", b"\x20" + bytes(9)), (b"ICCP", bytes(31)), (b"VP8 ", vp8(1600, 1067)))
        self.assertEqual(photos.metadata(extended, "x.webp"), ["a colour profile"])
        simple = photos.strip_webp(extended)
        self.assertEqual(simple, riff((b"VP8 ", vp8(1600, 1067))))
        self.assertEqual(photos.metadata(simple, "x.webp"), [])
        self.assertEqual(content._raster_size(simple, "WebP"), (1600, 1067))
        with self.assertRaises(photos.PhotoError):                 # transparency or animation: not a photo
            photos.strip_webp(riff((b"VP8X", bytes(10)), (b"ALPH", bytes(5)), (b"VP8 ", vp8(4, 4))))

    def test_png_metadata_is_found(self):
        png = tiny_png(4, 4)
        text = struct.pack(">I", 9) + b"tEXt" + b"Author\x00me" + struct.pack(">I", 0)
        self.assertEqual(photos.metadata(png, "x.png"), [])
        self.assertEqual(photos.metadata(png[:33] + text + png[33:], "x.png"), ["text"])


class MetaTest(unittest.TestCase):
    """META: the photo's texts, from a JSON file, JSON text, the command line or the spec in place."""

    def test_meta_is_a_json_object_with_known_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "meta.json"
            path.write_text(json.dumps(write_photo_texts()), encoding="utf-8")
            self.assertEqual(photos.read_meta(str(path)), write_photo_texts())
        self.assertEqual(photos.read_meta('{"credit": "NASA"}'), {"credit": "NASA"})
        self.assertEqual(photos.read_meta(None), {})
        for bad in ('{"credits": "x"}', "[1]", "{", "/no/such/file.json"):
            with self.subTest(bad=bad), self.assertRaises(photos.PhotoError):
                photos.read_meta(bad)

    def test_the_command_line_wins_over_meta_and_meta_over_the_photo_in_place(self):
        old = dict(write_photo_texts(), kind="photo")
        texts = photos.merge_meta(old, {"credit": "From META"}, {"alt.zh": "新的替代文字。", "retrieved": "2026-10-25",
                                                                  "license": None})
        self.assertEqual(texts["credit"], "From META")
        self.assertEqual(texts["alt"], {"en": old["alt"]["en"], "zh": "新的替代文字。"})
        self.assertEqual((texts["retrieved"], texts["license"]), ("2026-10-25", old["license"]))
        # an illustration's texts describe the drawing, so none carry over
        self.assertEqual(photos.merge_meta({"kind": "illustration", "alt": old["alt"]}, {}, {}), {})

    def test_the_texts_are_checked_as_the_build_checks_them(self):
        photos.check_meta(write_photo_texts())
        cases = {
            "no caption": {"caption": DELETE},
            "alt in English only": {"alt": {"en": "A rack."}},
            "a license a photo may not carry": {"license": "CC BY-ND 4.0"},
            "an editorial-use license": {"license": "Editorial use only"},
            "another license's address": {"license_url": "https://creativecommons.org/licenses/by/4.0/"},
            "a source that is not http(s)": {"source_url": "ftp://example.org/x.jpg"},
            "a retrieval month": {"retrieved": "2026-10"},
        }
        for name, change in cases.items():
            texts = write_photo_texts()
            for key, value in change.items():
                if value is DELETE:
                    texts.pop(key)
                else:
                    texts[key] = value
            with self.subTest(case=name), self.assertRaises(photos.PhotoError):
                photos.check_meta(texts)

    def test_the_sources_content_guide_allows(self):
        for url in ("https://commons.wikimedia.org/wiki/File:X.jpg", "https://www.nasa.gov/image-detail/x/",
                    "https://www.army.mil/article/1", "https://unsplash.com/photos/abc", "https://www.pexels.com/photo/x/",
                    "https://upload.wikimedia.org/wikipedia/commons/a/ab/X.jpg"):
            self.assertTrue(photos.source_allowed(url), url)
        for url in ("https://www.flickr.com/photos/x", "https://example.gov.evil.com/x", "https://pexels.com.example/x",
                    "https://www.gettyimages.com/x"):
            self.assertFalse(photos.source_allowed(url), url)


class SpecValidationTest(unittest.TestCase):
    """sitegen/content.py on a photo's copies (variants) and edits: each copy is checked as the
    photo itself is, and the edits say how the photo was cut from its source."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root, self.folder, self.spec = photo_root(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def load(self):
        return content._lead_image(self.root, self.folder)

    def refuse(self, spec, fragment):
        save(self.folder, spec)
        with self.assertRaises(content.ContentError) as caught:
            self.load()
        self.assertIn(fragment, str(caught.exception))
        self.assertIn(f"content/articles/{SLUG}/illustration.json", str(caught.exception))

    def media(self, name, data):
        (self.root / content.MEDIA_DIR / name).write_bytes(data)
        return {"file": name, "sha256": sha(data)}

    def test_a_valid_photo_and_its_copies(self):
        image = self.load()
        self.assertEqual(list(image.variants), ["list", "thumb", "social"])
        self.assertEqual(image.files(), [f"{SLUG}.png", f"{SLUG}-list.png", f"{SLUG}-thumb.png", f"{SLUG}-og.jpg"])
        self.assertEqual([(p.width, p.height) for p in image.published()], [(6, 4), (3, 2), (2, 1), (1200, 630)])
        social = image.variants["social"]
        self.assertEqual((social.src, social.sha256), (f"/assets/media/{SLUG}-og.jpg", sha(photo_files(SLUG)[f"{SLUG}-og.jpg"])))
        self.assertEqual((image.cropped, image.note_changes), (True, True))  # part of the source, under CC BY 4.0

    def test_broken_copies_stop_the_load(self):
        spec = self.spec
        wide = self.media("wide.png", tiny_png(6, 4))
        tall = self.media("tall.png", tiny_png(3, 4))
        webp = self.media("og.webp", webp_header(b"VP8 ", 1200, 630))
        short = self.media("short.jpg", jpeg_header(1200, 600))
        as_wide = self.media("as-wide.png", tiny_png(3, 2))
        upright = self.media("upright.png", tiny_png(2, 3))
        cases = (
            (mutate(spec, "variants.list", DELETE), "variants: list is missing"),
            (mutate(spec, "variants.thumb", DELETE), "variants: thumb is missing"),
            (mutate(spec, "variants.small", spec["variants"]["thumb"]), "variants: unknown field 'small'"),
            (mutate(spec, "variants.social.alt", "x"), "variants.social: unknown field 'alt'"),
            (mutate(spec, "variants.list", dict(wide, width=6, height=4)), "must be narrower than the 6 x 4 photo"),
            (mutate(spec, "variants.list", dict(tall, width=3, height=4)), "of the photo's proportions"),
            # srcset tells the copies apart by width: the thumb is narrower than the list copy too
            (mutate(spec, "variants.thumb", dict(as_wide, width=3, height=2)),
             "variants.thumb is 3 x 2; it must be narrower than the 3 x 2 list copy"),
            (mutate(spec, "variants.thumb", dict(upright, width=2, height=3)), "of the photo's proportions"),
            (mutate(spec, "variants.social", dict(webp, width=1200, height=630)), "a JPEG or PNG file"),
            (mutate(spec, "variants.social", dict(short, width=1200, height=600)), "1200 x 630 pixels"),
            (mutate(spec, "variants.list.sha256", "0" * 64), "variants.list: sha256 does not match"),
            (mutate(spec, "variants.thumb.sha256", "0" * 64), "variants.thumb: sha256 does not match"),
            (mutate(spec, "variants.list.file", "gone.png"), "static/media/gone.png is missing"),
            (mutate(spec, "variants.list.width", 4), "width and height say 4 x 2 pixels"),
            (mutate(spec, "variants.list", {k: spec[k] for k in content.PHOTO_FILE_KEYS}), "must be 4 different files"),
            (mutate(spec, "variants.thumb", spec["variants"]["list"]), "must be 4 different files"),
            (mutate(spec, "variants", []), "variants: must be an object"),
        )
        for broken, fragment in cases:
            with self.subTest(fragment):
                self.refuse(broken, fragment)

    def test_broken_edits_stop_the_load(self):
        spec = self.spec
        cases = (
            (mutate(spec, "edits.grade", DELETE), "edits: grade is missing"),
            (mutate(spec, "edits.grade", "vivid-1"), "grade must be one of soft-1"),
            (mutate(spec, "edits.source_sha256", "AB" * 32), "source_sha256 must be 64 lowercase hex digits"),
            (mutate(spec, "edits.source_size", [3000]), "source_size must be [width, height]"),
            (mutate(spec, "edits.crop", [2000, 0, 2400, 1600]), "inside the 3000 x 2000 source"),
            (mutate(spec, "edits.crop", [True, 0, 2400, 1600]), "crop must be [x, y, width, height]"),
            (mutate(spec, "edits.crop", [0, 0, 3, 2]), "narrower than the 6-pixel file made from it"),
            (mutate(spec, "edits.crop", [0, 0, 2400, 2000]), "not of the proportions of the 6 x 4 file"),
            (mutate(spec, "edits.social_crop", [0, 170, 2400, 1260]), "social_crop must lie inside crop"),
            (mutate(spec, "edits.social_crop", [300, 170, 1000, 525]), "narrower than the 1200-pixel file"),
            (mutate(spec, "edits.social_crop", [300, 0, 2400, 1600]), "not of the proportions of the 1200 x 630"),
            (mutate(spec, "edits.focus", "center"), "edits: unknown field 'focus'"),
        )
        for broken, fragment in cases:
            with self.subTest(fragment):
                self.refuse(broken, fragment)

    def test_licenses(self):
        accepted = (
            ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/deed.en", True),
            ("CC BY-SA 2.0", "http://creativecommons.org/licenses/by-sa/2.0/", True),
            ("CC BY 3.0 de", "https://creativecommons.org/licenses/by/3.0/de/deed.en", True),
            ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/", False),
            ("CC0", "https://creativecommons.org/publicdomain/zero/1.0/deed.en", False),
            ("Public domain", "https://commons.wikimedia.org/wiki/Template:PD-USGov", False),
            ({"en": "Public domain", "zh": "公有领域"}, "https://www.usa.gov/government-copyright", False),
            ("Unsplash License", "https://unsplash.com/license", False),
            ("Pexels License", "https://www.pexels.com/license/", False),
            ("Press reuse permission", "https://example.org/press", False),
        )
        for license_, url, notes in accepted:
            with self.subTest(license=license_):
                save(self.folder, dict(self.spec, license=license_, license_url=url))
                self.assertEqual(self.load().note_changes, notes)
        refused = (
            ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/", "a photo may carry"),
            ("CC BY-ND 4.0", "https://creativecommons.org/licenses/by-nd/4.0/", "a photo may carry"),
            ("All rights reserved", "https://example.org/terms", "a photo may carry"),
            ("CC BY 4.5", "https://creativecommons.org/licenses/by/4.5/", "a photo may carry"),
            ({"en": "CC BY-NC-SA 4.0", "zh": "CC BY-NC-SA 4.0"}, "https://creativecommons.org/licenses/by-nc-sa/4.0/",
             "a photo may carry"),
            ("CC BY 4.0", "https://creativecommons.org/licenses/by-sa/4.0/", "license_url must be the address of CC BY 4.0"),
            ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/3.0/", "license_url must be the address"),
            ("Unsplash License", "https://unsplash.com/licensing-terms-of-others", "license_url must be the address"),
            ("CC0 1.0", "https://example.org/creativecommons.org/publicdomain/zero/1.0/", "license_url must be"),
        )
        for license_, url, fragment in refused:
            with self.subTest(license=license_, url=url):
                self.refuse(dict(self.spec, license=license_, license_url=url), fragment)

    def test_a_crop_of_the_whole_source_is_not_cropped(self):
        save(self.folder, mutate(self.spec, "edits.crop", [0, 0, 3000, 2000]))
        self.assertIs(self.load().cropped, False)

    def test_unused_media_are_listed_without_dotfiles(self):
        media = self.root / content.MEDIA_DIR
        (media / ".gitkeep").write_bytes(b"")
        (media / "left-behind.webp").write_bytes(b"x")
        named = set(self.load().files())
        self.assertEqual(content.unused_media(self.root, named), ["left-behind.webp"])
        self.assertEqual(content.unused_media(self.root / "nowhere", named), [])


class SpecWritingTest(unittest.TestCase):
    """The spec tools/photos.py writes: the fields in CONTENT_GUIDE.md's order, and one the build accepts."""

    def test_make_spec_writes_a_spec_the_build_accepts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            spec = pipeline_spec(root)
            self.assertEqual(list(spec), list(content.LEAD_IMAGE_KEYS["photo"]))
            self.assertEqual(list(spec["variants"]), list(content.PHOTO_VARIANTS))
            self.assertEqual(spec["variants"]["list"], {"file": f"{SLUG}-800.webp", "width": 800, "height": 533,
                                                        "sha256": sha(pipeline_files()[f"{SLUG}-800.webp"])})
            self.assertEqual(spec["variants"]["thumb"], {"file": f"{SLUG}-400.webp", "width": 400, "height": 267,
                                                         "sha256": sha(pipeline_files()[f"{SLUG}-400.webp"])})
            self.assertEqual(spec["edits"]["grade"], photos.GRADE)
            image = content._lead_image(root, root / "content" / "articles" / SLUG)
            self.assertEqual((image.file, image.width, image.height), (f"{SLUG}.webp", 1600, 1067))
            self.assertEqual(image.variants["social"].file, f"{SLUG}-og.jpg")
            text = (root / "content" / "articles" / SLUG / content.LEAD_IMAGE_FILE).read_text(encoding="utf-8")
            self.assertEqual(json.loads(text), spec)
            self.assertIn('"source_size": [4000, 3000],', text)  # short lists stay on one line

    def test_spec_files_reads_even_a_broken_spec(self):
        self.assertEqual(photos.spec_files({"kind": "photo", "file": "a.webp", "variants": {"list": {"file": "b.webp"},
                                                                                            "social": None}}),
                         {"a.webp", "b.webp"})
        self.assertEqual(photos.spec_files({"kind": "illustration"}), set())
        self.assertEqual(photos.spec_files([]), set())


class CheckTest(unittest.TestCase):
    """--check: the build's checks of every photo, the pipeline's names, sizes, grade and lack of
    metadata, budgets and sources as warnings, and the files that no spec names."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        pipeline_spec(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, *slugs):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = photos.check(self.root, slugs)
        return code, out.getvalue() + err.getvalue()

    def test_a_pipeline_photo_passes(self):
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("1 photo checked, no problems", out)

    def test_left_behind_files_fail_but_an_illustrations_drawing_does_not(self):
        media = self.root / content.MEDIA_DIR
        (media / "old-story.svg").write_bytes(b"<svg/>")
        (media / "stray-og.jpg").write_bytes(b"x")
        (media / ".gitkeep").write_bytes(b"")
        drawn = self.root / "content" / "articles" / "old-story"
        drawn.mkdir()
        (drawn / content.LEAD_IMAGE_FILE).write_text('{"kind": "illustration"}', encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("static/media/stray-og.jpg is named by no illustration.json", out)
        self.assertNotIn("old-story.svg", out)
        self.assertEqual(self.run_check(SLUG)[0], 0)  # naming slugs checks only those

    def test_pipeline_conventions(self):
        files = pipeline_files()
        with_exif = files[f"{SLUG}-og.jpg"][:2] + exif_segment() + files[f"{SLUG}-og.jpg"][2:]
        cases = (
            ({f"{SLUG}-og.jpg": with_exif}, "carries EXIF"),
            ({f"{SLUG}.webp": riff((b"VP8 ", vp8(1200, 800)))}, "is 1200 x 800, not 1600 x 1067"),
        )
        for change, fragment in cases:
            with self.subTest(fragment):
                pipeline_spec(self.root, files=dict(files, **change))
                code, out = self.run_check()
                self.assertEqual(code, 1, out)
                self.assertIn(fragment, out)
        # a file named otherwise than tools/photos.py names it
        pipeline_spec(self.root)
        spec_path = self.root / "content" / "articles" / SLUG / content.LEAD_IMAGE_FILE
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        (self.root / content.MEDIA_DIR / "other.webp").write_bytes(files[f"{SLUG}.webp"])
        (self.root / content.MEDIA_DIR / f"{SLUG}.webp").unlink()
        spec["file"] = "other.webp"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1, out)
        self.assertIn(f"the photo file is other.webp, not {SLUG}.webp", out)

    def test_budgets_grades_and_sources_only_warn(self):
        big = riff((b"VP8 ", vp8(800, 533) + bytes(81 * 1024)))
        big_thumb = riff((b"VP8 ", vp8(400, 267) + bytes(30 * 1024)))
        pipeline_spec(self.root, files=dict(pipeline_files(), **{f"{SLUG}-800.webp": big, f"{SLUG}-400.webp": big_thumb}),
                      source_url="https://www.flickr.com/photos/someone/1")
        code, out = self.run_check()
        self.assertEqual(code, 0, out)
        self.assertIn(f"{SLUG}-800.webp is 81 KB, over its 70 KB budget", out)
        self.assertIn(f"{SLUG}-400.webp is 30 KB, over its 25 KB budget", out)
        self.assertIn("is not on Wikimedia Commons, a US government site, Unsplash or Pexels", out)

    def test_the_copies_halve_the_width_and_keep_the_photos_shape(self):
        """The 800 and 400 px copies are the photo's crop at a half and a quarter of its width,
        within a pixel of its 1600 x 1067 shape, and the budgets shrink with them."""
        (pw, ph), (lw, lh), (tw, th) = (photos.FILES[role][1] for role in ("photo", "list", "thumb"))
        self.assertEqual((lw * 2, tw * 4), (pw, pw))
        for w, h in ((lw, lh), (tw, th)):
            self.assertLessEqual(abs(h * pw - w * ph), pw, (w, h))
        budgets = [photos.FILES[role][6] for role in ("photo", "list", "thumb")]
        self.assertEqual(budgets, sorted(budgets, reverse=True))
        self.assertEqual([photos.FILES[role][0].format(slug="s") for role in photos.FILES],
                         ["s.webp", "s-800.webp", "s-400.webp", "s-og.jpg"])
        self.assertEqual(list(photos.FILES)[1:], list(content.PHOTO_VARIANTS))

    def test_a_broken_spec_is_reported_and_keeps_its_files(self):
        spec_path = self.root / "content" / "articles" / SLUG / content.LEAD_IMAGE_FILE
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        spec["sha256"] = "0" * 64
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        code, out = self.run_check()
        self.assertEqual(code, 1)
        self.assertIn("sha256 does not match", out)
        self.assertNotIn("named by no illustration.json", out)


class WriteTest(unittest.TestCase):
    """--write's refusals, which come before any browser starts."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        folder = self.root / "content" / "articles" / SLUG
        folder.mkdir(parents=True)
        (folder / "en.md").write_text("---\ntitle: T\n---\n", encoding="utf-8")
        self.source = self.root / "narrow.png"
        self.source.write_bytes(tiny_png(1200, 800))

    def tearDown(self):
        self.tmp.cleanup()

    def test_refusals(self):
        texts = write_photo_texts()
        with self.assertRaisesRegex(photos.PhotoError, "en.md does not exist"):
            photos.write(self.root, "no-such-story", self.source, meta=texts)
        with self.assertRaisesRegex(photos.PhotoError, "lack alt, caption"):
            photos.write(self.root, SLUG, self.source, meta={k: v for k, v in texts.items() if k not in ("alt", "caption")})
        with self.assertRaisesRegex(photos.PhotoError, "at least 1600 pixels wide"):
            photos.write(self.root, SLUG, self.source, meta=texts)
        text_file = self.root / "notes.txt"
        text_file.write_text("not a picture", encoding="utf-8")
        with self.assertRaisesRegex(photos.PhotoError, "not a JPEG, PNG, WebP, GIF or AVIF"):
            photos.write(self.root, SLUG, text_file, meta=texts)
        # an article with an illustration needs the photo's own alt text and caption
        (self.root / "content" / "articles" / SLUG / content.LEAD_IMAGE_FILE).write_text(
            json.dumps({"kind": "illustration", "alt": texts["alt"], "caption": texts["caption"]}), encoding="utf-8")
        with self.assertRaisesRegex(photos.PhotoError, "has an illustration"):
            photos.write(self.root, SLUG, self.source, meta={k: v for k, v in texts.items() if k not in ("alt", "caption")})
        self.assertFalse((self.root / content.MEDIA_DIR).exists())  # nothing written

    def test_the_command_line(self):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = photos.main(["--write", SLUG, "--source", str(self.source), "--root", str(self.root),
                                "--meta", json.dumps(write_photo_texts())])
        self.assertEqual(code, 1)
        self.assertIn("photos: the source is 1200 x 800 pixels", err.getvalue())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            photos.main(["--check", "--same-crop"])

    def test_same_crop_takes_the_recorded_boxes_from_the_recorded_source_only(self):
        raw = b"the source file"
        spec = {"kind": "photo", "edits": {"source_sha256": sha(raw), "source_size": [4000, 3000],
                                           "crop": [0, 166, 4000, 2668], "social_crop": [0, 400, 4000, 2100],
                                           "grade": photos.GRADE}}
        self.assertEqual(photos.recorded_boxes(spec, raw, "spec"),
                         ((4000, 3000), [0, 166, 4000, 2668], [0, 400, 4000, 2100]))
        with self.assertRaisesRegex(photos.PhotoError, "recorded source only"):
            photos.recorded_boxes(spec, b"another file", "spec")
        with self.assertRaisesRegex(photos.PhotoError, "narrower than the 1600-pixel file"):
            photos.recorded_boxes(mutate(spec, "edits.crop", [0, 0, 1200, 800]), raw, "spec")
        with self.assertRaisesRegex(photos.PhotoError, "no photo spec whose edits record a crop"):
            photos.recorded_boxes({"kind": "illustration"}, raw, "spec")
        # --write refuses before any browser starts: no spec in place, another source, a focus
        texts = write_photo_texts()
        with self.assertRaisesRegex(photos.PhotoError, "no photo spec whose edits record a crop"):
            photos.write(self.root, SLUG, self.source, meta=texts, same_crop=True)
        pipeline_spec(self.root)
        with self.assertRaisesRegex(photos.PhotoError, "recorded source only"):
            photos.write(self.root, SLUG, self.source, same_crop=True)
        with self.assertRaisesRegex(photos.PhotoError, "takes no focus"):
            photos.write(self.root, SLUG, self.source, focus="center", same_crop=True)


class RenderTest(unittest.TestCase):
    """The templates offer a photo's 400 and 800 px copies and its full-size file in srcset, name
    the 800 px copy in a list's src and the full-size file in the figure's, credit the photo, and
    use its social copy for link previews."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root, _, _ = photo_root(cls.tmp.name)
        cls.image = content._lead_image(root, root / "content" / "articles" / SLUG)
        cls.site = Site(content.load(ROOT), "prod")
        cls.site.lang, cls.site.current = "en", "/"

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_list_copy_has_a_width_for_srcset(self):
        source = (ROOT / "sitegen" / "render.py").read_text(encoding="utf-8")
        classes = set(re.findall(r'self\.thumb\(\w+, "([\w-]+)"', source))
        self.assertEqual(classes, {"news-lead-media", "ledger-thumb", "brief-thumb", "river-thumb", "card-thumb"})
        self.assertEqual(classes - set(render.THUMB_SIZES), set())
        # a topic page's river, narrower than Latest's, gives its own widths
        self.assertIn("sizes=TOPIC_RIVER_SIZES", source)

    def test_lists_start_from_the_copy_and_the_figure_from_the_photo(self):
        srcset = (f'srcset="/assets/media/{SLUG}-thumb.png 2w, /assets/media/{SLUG}-list.png 3w, '
                  f'/assets/media/{SLUG}.png 6w"')
        thumb = self.site.lead_img(self.image, "story-thumb-img", sizes=render.THUMB_SIZES["river-thumb"])
        self.assertIn(f'src="/assets/media/{SLUG}-list.png"', thumb)
        self.assertIn(srcset, thumb)
        self.assertIn(f'sizes="{render.THUMB_SIZES["river-thumb"]}"', thumb)
        self.assertIn('width="3" height="2"', thumb)
        self.assertIn('loading="lazy"', thumb)
        figure = self.site.lead_img(self.image, "lead-figure-img", alt="A rack.", eager=True)
        self.assertIn(f'src="/assets/media/{SLUG}.png"', figure)
        self.assertIn(srcset, figure)
        self.assertIn(f'sizes="{render.FIGURE_SIZES}"', figure)
        self.assertIn('width="6" height="4"', figure)
        self.assertIn('loading="eager" fetchpriority="high"', figure)

    def test_small_list_copies_fit_the_400_px_file(self):
        """THUMB_SIZES gives each list copy's widest width at each breakpoint. The home page's
        rail and the TEE rows never pass 8.5rem (136 CSS px), so the 400 px copy covers them at
        about three device pixels per CSS pixel; every value ends with a width for any window."""
        length = re.compile(r"^(\d+(?:\.\d+)?)rem$")
        for cls, value in dict(render.THUMB_SIZES, topic_river=render.TOPIC_RIVER_SIZES).items():
            entries = [part.strip() for part in value.split(",")]
            with self.subTest(cls=cls):
                self.assertFalse(entries[-1].startswith("("), value)  # a default width, without a condition
                for entry in entries[:-1]:
                    self.assertRegex(entry, r"^\(min-width: \d+(?:\.\d+)?rem\) \S")
                # conditions from the widest window down, so the first that matches is the right one
                widths = [float(re.search(r"min-width: ([\d.]+)rem", e).group(1)) for e in entries[:-1]]
                self.assertEqual(widths, sorted(widths, reverse=True))
        for cls in ("ledger-thumb", "brief-thumb"):
            for entry in render.THUMB_SIZES[cls].split(","):
                found = length.match(entry.strip().rsplit(" ", 1)[-1])
                self.assertIsNotNone(found, (cls, entry))
                self.assertLessEqual(float(found.group(1)) * 16 * 2.9, photos.FILES["thumb"][1][0], (cls, entry))

    def test_the_credit_line_says_how_the_photo_was_changed(self):
        credit = self.site.lead_credit(self.image)
        self.assertTrue(credit.startswith("Photo: Example Photographer · "), credit)
        self.assertTrue(credit.endswith(" · Cropped and color-adjusted"), credit)
        self.site.lang = "zh"
        try:
            self.assertTrue(self.site.lead_credit(self.image).endswith(" · 经裁剪和调色"))
        finally:
            self.site.lang = "en"

    def test_link_previews_use_the_social_copy(self):
        article = type("A", (), {"lead_image": self.image})()
        card = discover.photo_card(self.site, article)
        self.assertEqual(card, {"url": f"{self.site.base_url}/assets/media/{SLUG}-og.jpg", "width": 1200, "height": 630,
                                "alt": self.image.alt["en"], "credit": "Example Photographer",
                                "license": "https://creativecommons.org/licenses/by/4.0/"})
        tags = discover.social_meta(self.site, image_topic=card)
        self.assertIn(f'<meta property="og:image" content="{card["url"]}">', tags)
        self.assertIn('<meta property="og:image:width" content="1200">', tags)
        self.assertIn(f'<meta name="twitter:image" content="{card["url"]}">', tags)
        self.assertIsNone(discover.photo_card(self.site, type("A", (), {"lead_image": None})()))


class StylesheetTest(unittest.TestCase):
    def test_photos_dim_less_than_illustrations_on_dark_pages(self):
        css = (ROOT / "static" / "site.css").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"--media-dim-photo:\s*brightness\(0\.9\)", css)), 2)  # both dark themes
        self.assertRegex(css, r"--media-dim-photo:\s*none;")
        self.assertRegex(css, r'\.lead-figure\[data-image-kind="photo"\],\s*\.story-thumb\[data-image-kind="photo"\]'
                              r"\s*\{\s*--media-dim:\s*var\(--media-dim-photo\);\s*\}")


class DocsTest(unittest.TestCase):
    def test_the_content_guide_names_the_licenses_and_the_grade(self):
        guide = (ROOT / "CONTENT_GUIDE.md").read_text(encoding="utf-8")
        section = guide.split("### Photos", 1)[1].split("\n## ", 1)[0] if "### Photos" in guide else ""
        for words in ("public domain", "CC0", "CC BY", "CC BY-SA", "Unsplash License", "Pexels License",
                      "Wikimedia Commons", "tools/photos.py --write", photos.GRADE, "saturate(0.88) contrast(0.92)"):
            self.assertIn(words, section, words)


class RepositoryTest(unittest.TestCase):
    def test_every_committed_photo_passes_the_check(self):
        """python3 tools/photos.py --check on the repository: every photo spec, its files and
        their digests, and no file in static/media/ that no spec names."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = photos.check(ROOT)
        self.assertEqual(code, 0, err.getvalue())


@unittest.skipUnless(os.environ.get("VP_CHROME_TESTS") == "1", "set VP_CHROME_TESTS=1 to run headless Chrome")
class ChromeTest(unittest.TestCase):
    """--write end to end in a scratch project, on a gradient made here."""

    def test_write_makes_four_files_without_metadata_twice_the_same(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "content" / "articles" / SLUG
            folder.mkdir(parents=True)
            (folder / "en.md").write_text("---\ntitle: T\n---\n", encoding="utf-8")
            media = root / content.MEDIA_DIR
            media.mkdir(parents=True)
            (media / f"{SLUG}.svg").write_bytes(b"<svg/>")    # the illustration a photo replaces
            source = root / "source.png"
            source.write_bytes(gradient_png(2400, 1800))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                spec = photos.write(root, SLUG, source, "0.5,0.4", write_photo_texts())
            self.assertFalse((media / f"{SLUG}.svg").exists(), out.getvalue())
            self.assertEqual(spec["edits"]["crop"], [0, 0, 2400, 1600])
            for name, size in ((f"{SLUG}.webp", (1600, 1067)), (f"{SLUG}-800.webp", (800, 533)),
                               (f"{SLUG}-400.webp", (400, 267)), (f"{SLUG}-og.jpg", (1200, 630))):
                data = (media / name).read_bytes()
                kind = content.PHOTO_TYPES[name.rsplit(".", 1)[1]]
                self.assertEqual(content._raster_size(data, kind), size, name)
                self.assertEqual(photos.metadata(data, name), [], name)
                self.assertLess(len(data), photos.FILES["photo"][6], name)
            self.assertEqual(photos.check(root), 0)
            first = (folder / content.LEAD_IMAGE_FILE).read_bytes()
            files = {p.name: p.read_bytes() for p in media.iterdir()}
            with contextlib.redirect_stdout(io.StringIO()):
                photos.write(root, SLUG, source, "0.5,0.4")   # the texts in place are kept
            self.assertEqual((folder / content.LEAD_IMAGE_FILE).read_bytes(), first)
            # --same-crop cuts the recorded boxes from the same source: the same files and spec
            with contextlib.redirect_stdout(io.StringIO()):
                photos.write(root, SLUG, source, same_crop=True)
            self.assertEqual((folder / content.LEAD_IMAGE_FILE).read_bytes(), first)
            self.assertEqual({p.name: p.read_bytes() for p in media.iterdir()}, files)


if __name__ == "__main__":
    unittest.main()
