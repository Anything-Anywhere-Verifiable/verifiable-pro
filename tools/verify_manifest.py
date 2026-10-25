#!/usr/bin/env python3
"""Check a verifiable.pro manifest against the files it lists.

    python3 tools/verify_manifest.py dist                    # a local build
    python3 tools/verify_manifest.py https://verifiable.pro  # the live site

For each entry the script downloads or reads the source file, recomputes its
SHA-256 digest and compares it with the manifest. It also recomputes the
manifest digest from the canonical serialization described in the manifest.
A clean result shows that the published sources match the recorded build; it
says nothing about whether the content is accurate.
"""

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

# A source is a path on the site itself: "/articles/<slug>/en.md". Anything else
# ("@host/x", "//host/x", "/../x") could make the check read another site or file.
SOURCE_RE = re.compile(r"^/(?!/)[A-Za-z0-9._~-]+(?:/[A-Za-z0-9._~-]+)*$")


def safe_source(path):
    return isinstance(path, str) and bool(SOURCE_RE.match(path)) and ".." not in path.split("/")


def fetch(base, path):
    if base.startswith(("http://", "https://")):
        with urllib.request.urlopen(base.rstrip("/") + path, timeout=30) as resp:
            return resp.read()
    return (Path(base) / path.lstrip("/")).read_bytes()


def main(base):
    manifest = json.loads(fetch(base, "/manifest.json"))
    body = {k: v for k, v in manifest.items() if k not in ("digest", "digest_note")}
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    ok = digest == manifest.get("digest")
    print(f"manifest digest {'matches' if ok else 'DOES NOT MATCH'}: {digest}")
    failures = 0
    for entry in manifest["entries"]:
        if not safe_source(entry.get("source")):
            print(f"  UNSAFE   {entry.get('source')!r} is not a path on this site")
            failures += 1
            continue
        try:
            data = fetch(base, entry["source"])
        except Exception as exc:  # network or missing file
            print(f"  MISSING  {entry['source']} ({exc})")
            failures += 1
            continue
        actual = hashlib.sha256(data).hexdigest()
        if actual != entry["sha256"]:
            print(f"  CHANGED  {entry['source']}")
            failures += 1
    print(f"{len(manifest['entries'])} entries checked, {failures} problems")
    return 0 if ok and not failures else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
