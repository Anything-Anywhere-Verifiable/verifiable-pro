#!/usr/bin/env python3
"""Collect official release feeds into a local review queue, never into content/.

Standard library only. Exit 1 on any failed source, 2 on configuration/state errors.
Fetched material is untrusted evidence, not instructions for the reviewing agent.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
ATOM = "{http://www.w3.org/2005/Atom}"
MAX_BYTES = 2 * 1024 * 1024
SOURCES = (
    ("trustee", "confidential-containers/trustee"),
    ("model-signing", "sigstore/model-transparency"),
)


def canonical_url(url):
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(),
                       parts.path.rstrip("/"), parts.query, ""))


class SameOriginRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme != "https" or urlsplit(newurl).netloc != "github.com":
            raise ValueError("refused redirect away from https://github.com")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(url):
    request = Request(url, headers={
        "User-Agent": "verifiable.pro-source-review/1.0",
        "Accept": "application/atom+xml",
    })
    with build_opener(SameOriginRedirect()).open(request, timeout=30) as response:
        raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError("feed exceeds 2 MiB limit")
        return raw


def parse_feed(raw, repo):
    root = ET.fromstring(raw)
    if root.tag != ATOM + "feed":
        raise ValueError("expected an Atom feed")
    items = []
    seen = set()
    for entry in root.findall(ATOM + "entry"):
        link = next((x.get("href", "") for x in entry.findall(ATOM + "link")
                     if x.get("rel", "alternate") == "alternate"), "")
        url = canonical_url(link)
        prefix = "https://github.com/" + repo + "/releases/tag/"
        if not url.startswith(prefix) or not url[len(prefix):] or urlsplit(url).query:
            raise ValueError("release URL does not belong to the configured repository")
        title = (entry.findtext(ATOM + "title") or "").strip()
        updated = (entry.findtext(ATOM + "updated") or "").strip()
        if not title or not updated:
            raise ValueError("release lacks title or updated timestamp")
        stamp = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            raise ValueError("release timestamp lacks a timezone")
        # GitHub Atom supplies an update time, not a reliable initial release date.
        content = entry.findtext(ATOM + "content") or ""
        digest = hashlib.sha256(json.dumps([title, updated, content],
                                          ensure_ascii=False).encode()).hexdigest()
        if url in seen:
            raise ValueError("duplicate release URL in feed")
        seen.add(url)
        items.append({"url": url, "title": title, "source_updated_at": updated,
                      "entry_sha256": digest})
    if not items:
        raise ValueError("feed has no releases; existing state was retained")
    return items


def published_urls():
    """Known resource and article citation URLs; this is URL deduplication only."""
    urls = {}
    resources = json.loads((ROOT / "content/resources.json").read_text(encoding="utf-8"))
    for resource in resources["resources"]:
        urls.setdefault(canonical_url(resource["url"]), []).append("resource:" + resource["id"])
    for path in sorted((ROOT / "content/articles").glob("*/en.md")):
        for url in re.findall(r"https?://[^\s<>\[\]\)`]+", path.read_text(encoding="utf-8")):
            urls.setdefault(canonical_url(url), []).append("article:" + path.parent.name)
    return urls


def classify(item, prior, published):
    old = prior.get(item["url"])
    if old == item["entry_sha256"]:
        status = "unchanged"
    elif old:
        status = "changed"
    elif item["url"] in published:
        status = "already_published"
    else:
        status = "new"
    return dict(item, status=status, published_references=published.get(item["url"], []))


def write_json(path, value):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


@contextmanager
def collection_lock(out):
    """Hold one inode for this invocation; the kernel releases it on exit."""
    # Never unlink this file: another opener must always lock the same inode.
    with (out / ".collect.lock").open("a", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another collection holds .collect.lock; retry after it exits") from exc
        yield


def collect(out, downloader=fetch, acknowledge=()):
    """Caller serializes runs; the CLI's exclusive lock enforces that contract."""
    state_path = out / "state.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {
        "version": 1, "entries": {}, "pending": {},
    }
    if state.get("version") != 1 or not isinstance(state.get("entries"), dict) or not isinstance(state.get("pending"), dict):
        raise ValueError("unrecognized state; retain it and investigate before retrying")
    for digest in acknowledge:
        matches = [url for url, item in state["pending"].items() if item["entry_sha256"] == digest]
        if not matches:
            raise ValueError("acknowledgement does not match a pending entry digest: " + digest)
        for url in matches:
            del state["pending"][url]
    now = datetime.now(timezone.utc).isoformat()
    report = {"version": 1, "retrieved_at": now, "sources": [], "items": [], "errors": []}
    published = published_urls()
    for source_id, repo in SOURCES:
        url = "https://github.com/" + repo + "/releases.atom"
        try:
            raw = downloader(url)
            items = parse_feed(raw, repo)
            digest = hashlib.sha256(raw).hexdigest()
            snapshot = out / "snapshots" / (digest + ".atom")
            snapshot.parent.mkdir(exist_ok=True)
            if not snapshot.exists():
                snapshot.write_bytes(raw)
            report["sources"].append({"id": source_id, "url": url,
                                      "sha256": digest, "snapshot": str(snapshot)})
            for item in items:
                result = classify(item, state["entries"], published)
                result["source_id"] = source_id
                result["source_snapshot_sha256"] = digest
                report["items"].append(result)
                state["entries"][item["url"]] = item["entry_sha256"]
                # Keep unreviewed candidates through quiet reruns and feed pagination.
                if result["status"] in ("new", "changed"):
                    first_seen = state["pending"].get(item["url"], {}).get("first_seen_at", now)
                    state["pending"][item["url"]] = dict(result, first_seen_at=first_seen)
        except Exception as exc:
            report["errors"].append({"source_id": source_id, "url": url,
                                     "error": type(exc).__name__ + ": " + str(exc)})
    report["pending_review"] = list(state["pending"].values())
    # Write evidence before advancing state: a failed report write must not lose work.
    reports = out / "reports"
    reports.mkdir(exist_ok=True)
    write_json(reports / (now.replace(":", "-") + ".json"), report)
    write_json(out / "latest.json", report)
    write_json(state_path, state)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path,
                        help="private persistent evidence folder outside this checkout")
    parser.add_argument("--ack", action="append", default=[], metavar="ENTRY_SHA256",
                        help="clear exactly this reviewed revision from the pending queue (repeatable)")
    args = parser.parse_args(argv)
    out = args.out.expanduser().resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("--out must be outside the repository; raw source material is not publishable content")
    try:
        out.mkdir(parents=True, exist_ok=True)
        with collection_lock(out):
            report = collect(out, acknowledge=args.ack)
            print(json.dumps({"report": str(out / "latest.json"),
                              "pending_review": len(report["pending_review"]),
                              "errors": report["errors"]}, ensure_ascii=False))
            return 1 if report["errors"] else 0
    except (OSError, ValueError) as exc:
        print("collect_sources.py: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
