#!/usr/bin/env python3
"""Draw the social cards and icons with headless Chrome (standard library only).

    python3 tools/og_images.py            # write static/og/*.png, static/og/cards.json and static/icons/*.png
    python3 tools/og_images.py --check    # compare static/og/cards.json with the content; no browser
    python3 tools/og_images.py --out DIR  # write into DIR/og and DIR/icons instead of static/

Each card is 1200 x 630 pixels: one for the site and one for each topic in
content/topics.json, in English and in Chinese. A card shows the mark and the
wordmark, a kicker and a title from the content (the home page's kicker and
tagline, or "Topic" and the topic's name), and a drawing from sitegen/art.py: the
topic's pattern with its accent in the topic's hue, or for the site the enclave
pattern in TEE indigo. Colours come from the light theme in static/site.css,
fonts from the site's Google Fonts stylesheet (Newsreader, IBM Plex Sans), and
Chinese from the system's Songti SC and PingFang SC, as on the site. The icons
(180, 192 and 512 pixels) are static/mark.svg on its graphite tile.

The script checks what Chrome drew: every title fits its lines, the Latin text is
set in the web fonts and the Chinese text in a Chinese system font, no glyph is
missing, and each file has the stated size and stays under 120 KB. When a check
fails it writes nothing. Otherwise it writes the PNG files and static/og/cards.json,
which records the words on each card and its alt text; the build reads that file
and links the PNGs, and warns when a card's words no longer match the content.

The browser is $CHROME when it is set, else Google Chrome where macOS installs it,
google-chrome or chromium on the PATH on Linux, or chrome.exe on Windows. The
fonts load from Google Fonts, so the script needs the network.
"""

import argparse
import base64
import html
import http.client
import json
import os
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sitegen import art, content, discover, render  # noqa: E402

W, H = discover.CARD_SIZE
# Keep each card under this many bytes, so link previews load fast
MAX_BYTES = 120 * 1024
# The drawing on each card: (art.py pattern, words for the alt text in each language)
MOTIF_WORDS = {
    "enclave": ("memory pages around a sealed, measured region", "内存页环绕着一块经过度量的封闭区域"),
    "proof_tree": ("layers of computation folding into a single commitment", "多层计算汇聚成一个承诺"),
    "lattice": ("proof obligations discharged one by one across a grid", "证明义务在网格上逐一完成"),
    "samples": ("many test runs inside a confidence band, with the failures marked", "置信区间内的多次测试运行，失败的几次被标出"),
    "chain": ("records linked one to the next by hashes", "以哈希逐条相连的记录"),
    "credential": ("an image with an embedded signal beside a signed manifest", "一幅嵌有信号的图像和一份签名清单"),
    "trajectory": ("an agent's path of actions above its tamper-evident log", "智能体的行动路径及其下方的防篡改日志"),
    "die": ("a chip whose cores are metered", "一块各个核心都被计量的芯片"),
}
# Seeds for the drawings; a card's seed may be changed here when its drawing reads badly
SEED = "verifiable.pro social card: {key}"
SEEDS = {}
# The title's largest and smallest size in pixels, and how many lines it may take
TITLE = {"en": (64, 46, 3), "zh": (60, 46, 2)}
SITE_TITLE_LINES = {"en": 4, "zh": 2}
CJK_FONTS = ("PingFang", "Songti", "Hiragino", "Noto Sans CJK", "Noto Serif CJK", "Source Han", "STSong", "STHeiti",
             "Heiti", "Microsoft YaHei", "SimSun", "WenQuanYi")


# ----- inputs -------------------------------------------------------------------

def css_tokens(css):
    """The custom properties of the light theme: the first :root block of site.css."""
    start = css.index(":root {")
    block = css[start:css.index("}", start)]
    return {name: value.strip() for name, value in re.findall(r"--([\w-]+):\s*([^;]+);", block)}


def topic_hues(css, tokens):
    """Each topic's hue, from the rules that set --topic for [data-topic="..."]."""
    hues = {}
    for selectors, var in re.findall(r"([^{}]*)\{\s*--topic:\s*var\(--([\w-]+)\)", css):
        for tid in re.findall(r'\[data-topic="([\w-]+)"\]', selectors):
            hues.setdefault(tid, tokens.get(var))
    return hues


def mark_svg(tokens, size):
    """static/mark.svg with the tile, glyph and seal colours of the light theme."""
    svg = (ROOT / "static" / "mark.svg").read_text(encoding="utf-8")
    inner = svg[svg.index(">", svg.index("<svg")) + 1:svg.rindex("</svg>")]
    style = (f".mark-bg{{fill:{tokens['mark-tile']}}}.mark-fg{{fill:{tokens['mark-seal']}}}"
             f".mark-fg-stroke{{fill:none;stroke:{tokens['mark-glyph']}}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="{size}" height="{size}">'
            f"<style>{style}</style>{inner}</svg>")


def art_svg(tokens, motif, seed, accent):
    """An art.py pattern in the art colours of the light theme, its accent in ACCENT."""
    body = getattr(art, motif)(art.Rng(seed))
    t = tokens
    style = (f".a-bg{{fill:{t['art-bg']}}}.a-grid{{fill:none;stroke:{t['art-grid']};stroke-width:1}}"
             f".a-mute{{fill:{t['art-mute']}}}.a-ink{{fill:{t['art-ink']}}}.a-paper{{fill:{t['art-paper']}}}"
             f".a-stroke,.a-ink-stroke{{fill:none;stroke:{t['art-ink']};stroke-width:1.5}}"
             f".a-faint{{fill:none;stroke:{t['art-faint']};stroke-width:1}}.a-faint-dot{{fill:{t['art-faint']}}}"
             f".a-acc{{fill:{accent}}}.a-acc-stroke{{fill:none;stroke:{accent};stroke-width:2.5}}"
             "*{vector-effect:non-scaling-stroke}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {art.W} {art.H}" preserveAspectRatio="xMidYMid slice">'
            f'<style>{style}</style><rect class="a-bg" width="{art.W}" height="{art.H}"/>{body}</svg>')


def cards(model, tokens, hues):
    """Every card to draw: file name, language, topic, words, drawing and colours."""
    out = []
    topics = [None] + [t["id"] for t in model["topics"]["topics"]]
    for lang in content.LANGS:
        for topic in topics:
            words = discover.card_text(model, topic, lang)
            key = topic or "site"
            motif = art.MOTIFS.get(topic, art.chain).__name__ if topic else "enclave"
            hue = hues.get(topic) or tokens["ink-3"] if topic else tokens["tee-ink"]
            seed = SEEDS.get(key, SEED.format(key=key))
            drawing = MOTIF_WORDS[motif][0 if lang == "en" else 1]
            name = discover.site_name(model)
            if lang == "en":
                quoted = f"“{words['title']}”" + (f" and “{words['kicker']}”" if topic is None else ", marked as a topic")
                alt = f"The {name} logo above the words {quoted}, beside a drawing of {drawing}."
            else:
                quoted = f"“{words['title']}”" + (f"和“{words['kicker']}”" if topic is None else "，标为主题")
                alt = f"{name} 标志下方是{quoted}，旁边是一幅插图：{drawing}。"
            out.append({"file": discover.card_file(topic, lang), "lang": lang, "topic": topic, "kicker": words["kicker"],
                        "title": words["title"], "alt": alt, "motif": motif, "seed": seed, "hue": hue})
    return out


def card_html(card, tokens):
    lang = card["lang"]
    lo, hi = TITLE[lang][1], TITLE[lang][0]
    lines = SITE_TITLE_LINES[lang] if card["topic"] is None else TITLE[lang][2]
    kicker_cls = "kicker" + (" topic" if card["topic"] else "")
    swatch = '<span class="sw"></span>' if card["topic"] else ""
    t = tokens
    return f"""<!doctype html>
<html lang="{discover.HREFLANG[lang]}"><head><meta charset="utf-8">
<link rel="stylesheet" href="{render.FONTS}">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: {W}px; height: {H}px; overflow: hidden; background: {t['paper']}; }}
body {{ position: relative; font-family: "IBM Plex Sans", sans-serif; color: {t['ink-strong']}; -webkit-font-smoothing: antialiased; }}
.brand {{ position: absolute; left: 64px; top: 56px; display: flex; align-items: center; gap: 18px; }}
.brand svg {{ display: block; }}
.wordmark {{ font: 600 40px/1 "Newsreader", serif; letter-spacing: -0.012em; color: {t['ink-strong']}; white-space: nowrap; }}
.wordmark i {{ font-style: italic; font-weight: 400; letter-spacing: 0; color: {t['ink-3']}; }}
.main {{ position: absolute; left: 64px; right: 64px; top: 140px; bottom: 66px; display: flex; align-items: center; gap: 48px; }}
.text {{ flex: 1 1 auto; min-width: 0; }}
.kicker {{ display: flex; align-items: center; gap: 12px; font: 600 22px/1.3 "IBM Plex Sans", sans-serif; color: {t['accent']}; }}
.kicker.topic {{ letter-spacing: 0.1em; text-transform: uppercase; }}
.sw {{ width: 16px; height: 16px; flex: none; background: {card['hue']}; }}
.title {{ margin-top: 18px; font: 500 {hi}px/1.08 "Newsreader", serif; letter-spacing: -0.016em; color: {t['ink-strong']};
  text-wrap: balance; }}
.plate {{ flex: none; width: 512px; height: 288px; background: {t['art-bg']}; }}
.plate svg {{ display: block; width: 512px; height: 288px; }}
.rule {{ position: absolute; left: 0; right: 0; bottom: 0; height: 10px; background: {card['hue']}; }}
:lang(zh-CN) .kicker {{ font-family: "PingFang SC", "Hiragino Sans GB", "Noto Sans CJK SC", "Source Han Sans SC", "IBM Plex Sans", sans-serif;
  letter-spacing: 0.08em; }}
:lang(zh-CN) .title {{ font-family: "Newsreader", "Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", serif;
  font-weight: 600; letter-spacing: 0.01em; line-height: 1.24; word-break: keep-all; line-break: strict; }}
</style></head>
<body data-lo="{lo}" data-hi="{hi}" data-lines="{lines}">
<div class="brand">{mark_svg(tokens, 56)}<span class="wordmark">verifiable<i>.pro</i></span></div>
<div class="main"><div class="text"><p class="{kicker_cls}">{swatch}<span class="kicker-text">{html.escape(card['kicker'])}</span></p>
<h1 class="title">{html.escape(card['title'])}</h1></div>
<div class="plate">{art_svg(tokens, card['motif'], card['seed'], card['hue'])}</div></div>
<div class="rule"></div>
</body></html>
"""


def icon_html(tokens, size):
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>*{{margin:0;padding:0}}'
            f"html,body{{width:{size}px;height:{size}px;overflow:hidden;background:{tokens['mark-tile']}}}"
            f"svg{{display:block}}</style></head><body>{mark_svg(tokens, size)}</body></html>")


# Shrinks the title until it takes at most data-lines lines and no word runs past its box
# (Chinese titles break only at spaces and punctuation), and reports the layout
FIT = """(async () => {
  await document.fonts.ready;
  const faces = ['500 64px Newsreader', '600 40px Newsreader', 'italic 400 40px Newsreader', '600 22px "IBM Plex Sans"'];
  const loaded = {};
  for (const face of faces) loaded[face] = (await document.fonts.load(face, 'verifiable')).length > 0;
  const body = document.body, title = document.querySelector('.title');
  if (!title) return { loaded };
  const lo = +body.dataset.lo, hi = +body.dataset.hi, max = +body.dataset.lines;
  const lines = () => Math.round(title.getBoundingClientRect().height / parseFloat(getComputedStyle(title).lineHeight));
  const tooWide = () => title.scrollWidth > title.clientWidth + 1;
  let size = hi;
  title.style.fontSize = size + 'px';
  while ((lines() > max || tooWide()) && size > lo) { size -= 2; title.style.fontSize = size + 'px'; }
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const box = (el) => { const r = el.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; };
  return { loaded, size, lines: lines(), max, title: box(title), text: box(document.querySelector('.text')),
           main: box(document.querySelector('.main')), wordmark: box(document.querySelector('.wordmark')),
           overflow: tooWide() };
})()"""


# ----- Chrome over the DevTools protocol ---------------------------------------------

def chrome_path():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    if sys.platform == "darwin":
        return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if sys.platform == "win32":
        for root in filter(None, (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                                  os.environ.get("LOCALAPPDATA"))):
            path = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
            if path.exists():
                return str(path)
        return "chrome.exe"
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return "google-chrome"


class Chrome:
    """Headless Chrome and one page, driven over a minimal WebSocket client."""

    def __init__(self):
        self.profile = tempfile.mkdtemp(prefix="vp-og-")
        path = chrome_path()
        try:
            self.proc = subprocess.Popen(
                [path, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                 "--no-default-browser-check", "--force-color-profile=srgb", "--remote-debugging-port=0",
                 f"--user-data-dir={self.profile}", "--allow-file-access-from-files", "about:blank"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError as exc:
            raise SystemExit(f"cannot start Chrome at {path} ({exc}); set CHROME to the browser's path") from exc
        port_file = Path(self.profile) / "DevToolsActivePort"
        for _ in range(200):
            if port_file.exists() and port_file.read_text().count("\n") >= 1:
                break
            if self.proc.poll() is not None:
                break
            time.sleep(0.05)
        else:
            self.close()
            raise SystemExit(f"Chrome at {path} did not open its DevTools port; set CHROME to the browser's path")
        if not port_file.exists():
            self.close()
            raise SystemExit(f"Chrome at {path} exited before opening its DevTools port")
        port = int(port_file.read_text().split()[0])
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        conn.request("PUT", "/json/new?about:blank")
        target = json.loads(conn.getresponse().read())
        conn.close()
        url = urllib.parse.urlsplit(target["webSocketDebuggerUrl"])
        self.sock = socket.create_connection((url.hostname, url.port), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET {url.path} HTTP/1.1\r\nHost: {url.hostname}:{url.port}\r\nUpgrade: websocket\r\n"
                           f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        self.buf = bytearray()
        while b"\r\n\r\n" not in self.buf:
            self.buf += self._recv()
        head, _, rest = bytes(self.buf).partition(b"\r\n\r\n")
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise SystemExit(f"Chrome refused the DevTools connection: {head[:80]!r}")
        self.buf = bytearray(rest)
        self.next_id = 0
        self.events = []
        for domain in ("Page", "Runtime", "DOM", "CSS"):
            self.send(f"{domain}.enable")

    def _recv(self):
        chunk = self.sock.recv(1 << 16)
        if not chunk:
            raise ConnectionError("Chrome closed the DevTools connection")
        return chunk

    def _take(self, n):
        while len(self.buf) < n:
            self.buf += self._recv()
        data = bytes(self.buf[:n])
        del self.buf[:n]
        return data

    def _frame(self, opcode, payload):
        head = bytearray([0x80 | opcode])
        n = len(payload)
        if n < 126:
            head.append(0x80 | n)
        elif n < 1 << 16:
            head += bytes([0x80 | 126]) + struct.pack(">H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        body = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self.sock.sendall(bytes(head) + mask + body)

    def _message(self):
        parts = []
        while True:
            b0, b1 = self._take(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._take(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._take(8))[0]
            mask = self._take(4) if b1 & 0x80 else None
            payload = self._take(n)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            opcode = b0 & 0x0F
            if opcode == 8:
                raise ConnectionError("Chrome closed the DevTools connection")
            if opcode == 9:
                self._frame(10, payload)
                continue
            if opcode == 10:
                continue
            parts.append(payload)
            if b0 & 0x80:
                return json.loads(b"".join(parts).decode("utf-8"))

    def send(self, method, params=None):
        self.next_id += 1
        mid = self.next_id
        self._frame(1, json.dumps({"id": mid, "method": method, "params": params or {}}).encode("utf-8"))
        while True:
            msg = self._message()
            if msg.get("id") == mid:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error'].get('message')}")
                return msg.get("result", {})
            self.events.append(msg)

    def wait(self, method, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            for n, msg in enumerate(self.events):
                if msg.get("method") == method:
                    del self.events[:n + 1]
                    return msg.get("params", {})
            self.events.append(self._message())
        raise TimeoutError(f"no {method} within {timeout}s")

    def evaluate(self, expression):
        result = self.send("Runtime.evaluate", {"expression": expression, "awaitPromise": True, "returnByValue": True})
        if result.get("exceptionDetails"):
            raise RuntimeError(json.dumps(result["exceptionDetails"])[:400])
        return result["result"].get("value")

    def open(self, path, width, height):
        self.send("Emulation.setDeviceMetricsOverride",
                  {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False})
        self.events.clear()
        self.send("Page.navigate", {"url": path.as_uri()})
        self.wait("Page.loadEventFired")

    def fonts(self, selector):
        """The platform fonts that render the text of the element SELECTOR."""
        root = self.send("DOM.getDocument", {"depth": 0})["root"]["nodeId"]
        node = self.send("DOM.querySelector", {"nodeId": root, "selector": selector})["nodeId"]
        return self.send("CSS.getPlatformFontsForNode", {"nodeId": node})["fonts"]

    def shot(self, width, height):
        data = self.send("Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False,
                                                    "clip": {"x": 0, "y": 0, "width": width, "height": height, "scale": 1}})
        return base64.b64decode(data["data"])

    def close(self):
        try:
            self.sock.close()
        except Exception:  # noqa: BLE001 - closing a socket that may never have opened
            pass
        if getattr(self, "proc", None) and self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait(timeout=10)
        shutil.rmtree(self.profile, ignore_errors=True)


# ----- PNG files ----------------------------------------------------------------------

def png_chunks(data):
    pos, out = 8, []
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        out.append((kind, data[pos + 8:pos + 8 + n]))
        pos += 12 + n
    return out


def png_pixels(data):
    """(width, height, channels, rows) of an 8-bit, non-interlaced RGB or RGBA PNG."""
    chunks = png_chunks(data)
    width, height, depth, colour, _, _, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    if depth != 8 or colour not in (2, 6) or interlace:
        raise ValueError(f"unexpected PNG format (depth {depth}, colour type {colour}, interlace {interlace})")
    channels = 3 if colour == 2 else 4
    raw = zlib.decompress(b"".join(body for kind, body in chunks if kind == b"IDAT"))
    stride = width * channels
    rows, prev = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind, line = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        if kind == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif kind == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif kind == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif kind == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b, c = prev[i], prev[i - channels] if i >= channels else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 0xFF
        rows.append(line)
        prev = line
    return width, height, channels, rows


def png_write(width, height, rows, palette=None):
    """An 8-bit PNG: indexed when PALETTE is given (rows of indices), else RGB."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    colour = 3 if palette else 2
    raw = b"".join(b"\x00" + bytes(row) for row in rows)
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, colour, 0, 0, 0))
    if palette:
        out += chunk(b"PLTE", b"".join(bytes(c) for c in palette))
    return out + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def shrink(data):
    """The smallest of Chrome's PNG and a lossless re-encoding: an indexed PNG when the
    picture has at most 256 colours, else RGB without the alpha channel."""
    width, height, channels, rows = png_pixels(data)
    pixels = [bytes(row) for row in rows]
    if channels == 4:
        if any(row[3::4].count(255) != width for row in pixels):
            return data  # keep real transparency as Chrome wrote it
        pixels = [bytes(b for i, b in enumerate(row) if i % 4 != 3) for row in pixels]
    colours = {}
    for row in pixels:
        for i in range(0, len(row), 3):
            colours.setdefault(row[i:i + 3], len(colours))
            if len(colours) > 256:
                break
        if len(colours) > 256:
            break
    if len(colours) <= 256:
        palette = sorted(colours)
        index = {c: n for n, c in enumerate(palette)}
        indexed = [bytes(index[row[i:i + 3]] for i in range(0, len(row), 3)) for row in pixels]
        best = png_write(width, height, indexed, palette)
    else:
        best = png_write(width, height, pixels)
    return best if len(best) < len(data) else data


# ----- drawing -----------------------------------------------------------------------

def check_fonts(chrome, card, report):
    """Latin text in the web fonts, Chinese text in a Chinese font, and no missing glyphs."""
    problems = []
    for selector in (".wordmark", ".wordmark i", ".kicker-text", ".title"):
        fonts = chrome.fonts(selector)
        names = [f"{f.get('familyName')}{' (web)' if f.get('isCustomFont') else ''}" for f in fonts]
        report.append(f"    {selector}: {', '.join(names)}")
        if any("LastResort" in (f.get("familyName") or "") for f in fonts):
            problems.append(f"{selector} has characters that no font covers")
        text = chrome.evaluate(f"document.querySelector({json.dumps(selector)}).textContent")
        latin = re.search(r"[A-Za-z]", text)
        cjk = re.search(r"[\u3000-\u9fff\uff00-\uffef]", text)
        if latin and not any(f.get("isCustomFont") for f in fonts):
            problems.append(f"{selector} is not set in the site's web fonts (do the Google Fonts load?): {names}")
        if cjk and not any(any(c in (f.get("familyName") or "") for c in CJK_FONTS) for f in fonts):
            problems.append(f"{selector} has Chinese text but no Chinese font drew it: {names}")
    return problems


def draw(out_dir, only=None, keep_html=None):
    model = content.load(ROOT)
    css = (ROOT / "static" / "site.css").read_text(encoding="utf-8")
    tokens = css_tokens(css)
    hues = topic_hues(css, tokens)
    todo = cards(model, tokens, hues)
    if only:
        todo = [c for c in todo if c["file"] in only or c["file"].rsplit(".", 1)[0] in only]
    og_dir, icon_dir = out_dir / "og", out_dir / "icons"
    og_dir.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="vp-og-html-"))
    chrome = Chrome()
    problems, report, files = [], [], []
    try:
        for card in todo:
            page = work / card["file"].replace(".png", ".html")
            page.write_text(card_html(card, tokens), encoding="utf-8")
            if keep_html:
                Path(keep_html).mkdir(parents=True, exist_ok=True)
                shutil.copy(page, Path(keep_html) / page.name)
            chrome.open(page, W, H)
            layout = chrome.evaluate(FIT)
            report.append(f"{card['file']}: title {layout['size']}px in {layout['lines']} of {layout['max']} lines")
            missing = [face for face, ok in layout["loaded"].items() if not ok]
            if missing:
                problems.append(f"{card['file']}: fonts did not load from Google Fonts: {', '.join(missing)}")
            if layout["lines"] > layout["max"] or layout["overflow"]:
                problems.append(f"{card['file']}: the title does not fit in {layout['max']} lines")
            if layout["text"][1] < layout["main"][1] - 0.5 or layout["text"][3] > layout["main"][3] + 0.5:
                problems.append(f"{card['file']}: the kicker and title overflow the space between the logo and the foot")
            problems += [f"{card['file']}: {p}" for p in check_fonts(chrome, card, report)]
            data = shrink(chrome.shot(W, H))
            if size_of(data) != (W, H):
                problems.append(f"{card['file']}: Chrome drew {size_of(data)}, not {W}x{H}")
            if len(data) > MAX_BYTES:
                problems.append(f"{card['file']}: {len(data) // 1024} KB, over {MAX_BYTES // 1024} KB")
            files.append((og_dir / card["file"], data))
            report.append(f"    {len(data) // 1024} KB")
        if not only:
            for name, px in discover.ICONS.items():
                page = work / name.replace(".png", ".html")
                page.write_text(icon_html(tokens, px), encoding="utf-8")
                chrome.open(page, px, px)
                data = shrink(chrome.shot(px, px))
                if size_of(data) != (px, px):
                    problems.append(f"{name}: Chrome drew {size_of(data)}, not {px}x{px}")
                files.append((icon_dir / name, data))
                report.append(f"{name}: {px}x{px}, {len(data) // 1024} KB")
    finally:
        chrome.close()
        shutil.rmtree(work, ignore_errors=True)
    print("\n".join(report))
    if problems:  # leave the committed files as they were
        print("\n".join(f"problem: {p}" for p in problems), file=sys.stderr)
        print("nothing written", file=sys.stderr)
        return 1
    for path, data in files:
        path.write_bytes(data)
    index_path = og_dir / "cards.json"
    index = {"cards": {}}
    if only and index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
    for card in todo:
        index["cards"][card["file"]] = {key: card[key] for key in ("lang", "topic", "kicker", "title", "alt", "motif", "seed")}
    index["note"] = ("Written by tools/og_images.py: the words on each social card and its alt text, which the build "
                     "uses for og:image:alt. Redraw the cards instead of editing this file.")
    index["size"] = [W, H]
    index["icons"] = {name: px for name, px in discover.ICONS.items()}
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"drew {len(todo)} cards into {og_dir}" + ("" if only else f" and {len(discover.ICONS)} icons into {icon_dir}"))
    return 0


def size_of(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", data[16:24])


def check():
    """Compare static/og/cards.json with the words the content gives each card, without a browser."""
    model = content.load(ROOT)
    try:
        found, warnings = discover.check_images(ROOT, model)
    except content.ContentError as exc:
        print(f"problem: {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"out of date: {warning}", file=sys.stderr)
    print(f"{len(found)} cards and {len(discover.ICONS)} icons checked, {len(warnings)} out of date")
    return 1 if warnings else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=None, help="write og/ and icons/ into this folder (default: static/)")
    parser.add_argument("--only", default=None, help="comma-separated cards to redraw, such as site-en,formal-verification-zh")
    parser.add_argument("--keep-html", default=None, metavar="DIR", help="also save each card's HTML into DIR")
    parser.add_argument("--check", action="store_true", help="compare static/og/cards.json with the content; no browser")
    args = parser.parse_args()
    out_dir = Path(args.out).resolve() if args.out else ROOT / "static"
    if args.check:
        return check()
    only = {name.strip() for name in args.only.split(",")} if args.only else None
    return draw(out_dir, only, args.keep_html)


if __name__ == "__main__":
    sys.exit(main())
