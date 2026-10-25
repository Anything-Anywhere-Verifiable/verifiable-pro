#!/usr/bin/env python3
"""Refresh the curated request fixtures api/fixtures/chat.request.json and chat.request.zh.json.

    python3 backend/mock/refresh_requests.py               # report what is stale; exit 1 if anything is
    python3 backend/mock/refresh_requests.py --write       # rewrite what is stale
    python3 backend/mock/refresh_requests.py --build DIR   # use an existing production build of the site

The two request fixtures carry real passages from the site: the manifest digest,
the page's source digest, and for each chunk its title, heading, address, source
digest, UTF-16 offsets and text. Changing any article, page or data file changes
the manifest digest, and editing a chunk's article can move its offsets, so run
this after a content change. It keeps each fixture's questions and chunk ids and
cuts the chunks again from a production build with static/chat.js's own passage
parser, so they match what the widget would send. api/chat-v1.md names the first
eight characters of the manifest digest; --write updates that too.

Without --build, the script builds the production site into a temporary folder
first (python3 build.py --out <folder>). The parser runs in Node.js through
chat_passages.mjs beside this file, which needs only Node's own modules. After
--write, regenerate the fixtures that the mock produces from these requests, and
run the mock's tests:

    python3 backend/mock/make_fixtures.py
    python3 backend/mock/make_fixtures.py --check
    python3 -m unittest discover -s backend/mock -p 'test_*.py'

Exit status: 0 when everything is current or was rewritten, 1 when something is
stale and --write was not given, 2 when the build or the parser fails or a
fixture's chunk id no longer names a passage (pick another passage by hand).

Standard library only; Python 3.9+.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FIXTURES = os.path.join(ROOT, "api", "fixtures")
NAMES = ("chat.request.json", "chat.request.zh.json")
CONTRACT = os.path.join(ROOT, "api", "chat-v1.md")
# "... from the build whose manifest digest is `<first 8 hex digits>…`" in the contract's fixture table
CONTRACT_DIGEST_RE = re.compile(r"(whose manifest digest is `)([0-9a-f]{8})(…`)")
PARSER = os.path.join(HERE, "chat_passages.mjs")
# The chunk fields that come from the build; a chunk keeps its other fields
CHUNK_KEYS = ("id", "slug", "lang", "kind", "title", "heading", "url", "source", "source_sha256", "start", "end", "text")


def dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def fail(message):
    sys.stderr.write("refresh_requests.py: %s\n" % message)
    return 2


def build_site(out):
    """The production build that deploy.yml publishes, into OUT."""
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, os.path.join(ROOT, "build.py"), "--out", out], cwd=ROOT,
                          capture_output=True, text=True, env=env)


def passages(build, sources):
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js is needed to run static/chat.js's passage parser (chat_passages.mjs)")
    res = subprocess.run([node, PARSER, ROOT, build] + sources, capture_output=True, text=True)
    if res.returncode:
        raise RuntimeError("chat_passages.mjs failed:\n" + res.stderr.strip())
    return json.loads(res.stdout)


def utf16_slice(raw, start, end):
    """What chat.js's source.slice(start, end) gives: START and END count UTF-16 code units."""
    units = raw.decode("utf-8").encode("utf-16-le")
    return units[2 * start:2 * end].decode("utf-16-le")


def refresh(fixture, data, manifest, build):
    """FIXTURE with its digests and chunks taken from the build. Raises LookupError when a
    chunk id names no current passage."""
    by_page = {e["page"]: e for e in manifest["entries"] if e["page"]}
    fixture["context"]["manifest_digest"] = manifest["digest"]
    if fixture.get("page") is not None:
        fixture["page"]["source_sha256"] = by_page[fixture["page"]["path"]]["sha256"]
    for chunk in fixture["context"]["chunks"]:
        hits = [p for p in data["docs"][chunk["source"]]["passages"] if p["id"] == chunk["id"]]
        if len(hits) != 1:
            raise LookupError(chunk["id"])
        for key in CHUNK_KEYS:
            chunk[key] = hits[0][key]
        with open(os.path.join(build, chunk["source"].lstrip("/")), "rb") as fh:
            raw = fh.read()
        # the contract: source.slice(start, end) == text
        if utf16_slice(raw, chunk["start"], chunk["end"]) != chunk["text"]:
            raise AssertionError("%s: the offsets do not reslice the text" % chunk["id"])
        if len(chunk["text"]) > server.MAX_CHUNK_CHARS:  # the mock refuses a longer passage
            raise AssertionError("%s: the passage is longer than %d characters" % (chunk["id"], server.MAX_CHUNK_CHARS))
    return fixture


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--write", action="store_true", help="rewrite the stale fixtures and the digest in api/chat-v1.md")
    p.add_argument("--build", metavar="DIR", help="an existing production build (default: build one in a temporary folder)")
    args = p.parse_args(argv)

    fixtures = {}
    for name in NAMES:
        with open(os.path.join(FIXTURES, name), encoding="utf-8") as fh:
            fixtures[name] = json.load(fh)
    sources = sorted({c["source"] for f in fixtures.values() for c in f["context"]["chunks"]})

    with tempfile.TemporaryDirectory() as tmp:
        build = args.build
        if build is None:
            build = os.path.join(tmp, "public")
            res = build_site(build)
            if res.returncode:
                return fail("the production build failed:\n" + res.stderr.strip())
        try:
            data = passages(build, sources)
            with open(os.path.join(build, "manifest.json"), encoding="utf-8") as fh:
                manifest = json.load(fh)
            if data["manifest_digest"] != manifest["digest"]:
                return fail("the parser read another manifest than the build's")
            stale = {}
            for name, fixture in fixtures.items():
                before = dump(fixture)
                after = dump(refresh(fixture, data, manifest, build))
                if after != before:
                    stale[name] = after
        except LookupError as exc:
            return fail("no current passage has the id %s; choose another passage for that chunk by hand" % exc)
        except (RuntimeError, AssertionError) as exc:
            return fail(str(exc))

    digest = manifest["digest"]
    with open(CONTRACT, encoding="utf-8") as fh:
        contract = fh.read()
    named = CONTRACT_DIGEST_RE.search(contract)
    if named is None:
        return fail("api/chat-v1.md no longer says which manifest digest the request fixtures come from")
    contract_stale = named.group(2) != digest[:8]

    if args.write:
        for name, text in stale.items():
            with open(os.path.join(FIXTURES, name), "w", encoding="utf-8") as fh:
                fh.write(text)
        if contract_stale:
            with open(CONTRACT, "w", encoding="utf-8") as fh:
                fh.write(CONTRACT_DIGEST_RE.sub(lambda m: m.group(1) + digest[:8] + m.group(3), contract, count=1))
    changed = sorted(stale) + (["api/chat-v1.md"] if contract_stale else [])
    print("manifest digest %s" % digest)
    if not changed:
        print("request fixtures up to date")
        return 0
    print(("rewrote: " if args.write else "stale: ") + ", ".join(changed))
    if args.write:
        print("next: python3 backend/mock/make_fixtures.py, then its --check and the mock's tests")
        return 0
    print("run python3 backend/mock/refresh_requests.py --write")
    return 1


if __name__ == "__main__":
    sys.exit(main())
