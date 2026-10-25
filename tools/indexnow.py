#!/usr/bin/env python3
"""Tell IndexNow which canonical pages a deploy added, changed or removed (stdlib only).

indexnow.json names the host and its key, which every build serves as /<key>.txt. The key
cannot be secret, because SHA256SUMS lists every published file. The state file keeps the
fingerprint of each page version that IndexNow received: it records receipts, not indexing.

A run compares the build with --baseline-site-dir, an earlier build, when one is given (the
deploy workflow builds the previously deployed commit when it has no state), and otherwise
with the state. With neither, it records the current pages as the baseline and notifies
nothing; --bootstrap notifies every page instead. --dry-run prints the plan without network
requests or state writes. See https://www.indexnow.org/documentation and "Incremental search
notifications" in docs/MAINTAINING.md.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import http.client
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sitegen.discover import indexnow_config as load_config  # noqa: E402

ENDPOINT = "https://api.indexnow.org/indexnow"
# deploy.yml's cache key starts with indexnow-v<VERSION>-; change both together. A state of another
# version counts as missing, so a change to what a fingerprint covers re-baselines once.
VERSION = 2
BATCH = 10000  # IndexNow's limit of URLs per request
USER_AGENT = "IndexNow-site-notifier/1.0"
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
# Attributes that carry a page's content; the pages use title only for tooltips
SEMANTIC_ATTRS = {"alt", "datetime", "href", "lang", "src", "aria-label"}
META_NAMES = {"description", "robots", "googlebot", "bingbot", "author"}
# Parts of <main> that repeat other pages or the site's settings: the filing-details and Ask asides,
# the related-stories cards and the correction links (the repository's issue form and editor)
REPEATED_CLASSES = {"doc-aside", "sidebar", "chat-aside", "related", "check-correct"}
# IndexNow shares a notification with every participating engine, so a page must be open to all
# crawlers (*) and to Bing's
ROBOTS_AGENTS = ("*", "bingbot")


def own_url(url, host):
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.netloc != host or not parts.path.startswith("/")
            or parts.query or parts.fragment or re.search(r"[\s\\]", url)):
        raise ValueError(f"not a canonical HTTPS URL on {host}: {url}")
    decoded = unquote(parts.path)
    if any(part in (".", "..") for part in decoded.split("/")) or "%" in decoded or "\\" in decoded:
        raise ValueError(f"unsafe encoded URL path: {url}")
    return parts.path


class Page(HTMLParser):
    """Fingerprint search metadata and main content, excluding scripts and repeated parts.

    Navigation, footers, scripts, elements hidden from readers and REPEATED_CLASSES show other
    pages or the site's settings, so a new article, a footer year, the assistant's build digest
    or a repository move does not resubmit every article. The title, descriptions, alternates,
    structured data and the elements and visible text, links and images of <main> remain covered.
    """
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.stack, self.main, self.title, self.ld = [], [], [], []
        self.meta, self.links, self.canonicals = [], [], []
        self.noindex, self.has_main = False, False
        self._title, self._ld = False, None
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title" and any(item[0] == "head" for item in self.stack):
            self._title = True
        if tag == "link":
            rel = (attrs.get("rel") or "").lower().split()
            if "canonical" in rel:
                self.canonicals.append(attrs.get("href"))
            if set(rel) & {"canonical", "alternate"}:
                self.links.append(sorted((k, v or "") for k, v in attrs.items() if k in {"rel", "href", "hreflang", "type"}))
        if tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or "").lower()
            value = attrs.get("content") or ""
            if name in {"robots", "googlebot", "bingbot"} and set(re.split(r"[,\s]+", value.lower())) & {"noindex", "none"}:
                self.noindex = True
            if name in META_NAMES or name.startswith(("og:", "twitter:")):
                self.meta.append((name, value))
        if tag == "script" and attrs.get("type") == "application/ld+json":
            self._ld = []
        parent_main = bool(self.stack and self.stack[-1][1])
        parent_blocked = bool(self.stack and self.stack[-1][2])
        in_main = parent_main or tag == "main"
        if tag == "main":
            self.has_main = True
        classes = set((attrs.get("class") or "").split())
        blocked = (parent_blocked or tag in {"script", "style", "nav", "footer"}
                   or "hidden" in attrs or attrs.get("aria-hidden") == "true"
                   or bool(classes & REPEATED_CLASSES))
        if in_main and not blocked:
            self.main.append((tag, sorted((k, v) for k, v in attrs.items() if k in SEMANTIC_ATTRS)))
        if tag not in VOID:
            self.stack.append((tag, in_main, blocked))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._title = False
        if tag == "script" and self._ld is not None:
            self.ld.append(json.loads("".join(self._ld)))
            self._ld = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
        if self._title:
            self.title.append(data)
        if self.stack and self.stack[-1][1] and not self.stack[-1][2]:
            text = " ".join(data.split())
            if text:
                self.main.append(text)

    def fingerprint(self):
        if not self.has_main:
            raise ValueError("indexable page has no <main>; refusing an incomplete fingerprint")
        data = {"title": " ".join("".join(self.title).split()), "meta": sorted(self.meta),
                "links": sorted(self.links), "structured_data": self.ld, "main": self.main}
        return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def robots_rules(text):
    """robots.txt grouped as RFC 9309 reads it: {lowercased user agent: [(length, allow, pattern)]}.

    urllib.robotparser applies the first matching rule and ignores wildcards in Python 3.12 and in
    releases of 3.13 and 3.14 before 3.13.14 and 3.14.5, so the tool reads the file itself: which
    pages are eligible must not depend on the Python that runs the deploy.
    """
    groups, members, in_agents = {}, [], False
    for line in text.splitlines():
        field, colon, value = line.split("#", 1)[0].partition(":")
        field, value = field.strip().lower(), value.strip()
        if not colon:
            continue
        if field == "user-agent":
            if not in_agents:  # a user-agent line after rules starts the next group
                members, in_agents = [], True
            members.append(value.lower())
            groups.setdefault(value.lower(), [])
        elif field in ("allow", "disallow"):
            in_agents = False
            if value:  # an empty Disallow allows everything
                rule = (len(value), field == "allow", robots_pattern(value))
                for agent in members:
                    groups[agent].append(rule)
    return groups


def robots_pattern(path):
    """A robots.txt path as a regular expression: * matches any characters and a final $ ends the path."""
    body, anchored = (path[:-1], True) if path.endswith("$") else (path, False)
    return re.compile(".*".join(re.escape(part) for part in body.split("*")) + ("$" if anchored else ""))


def robots_allowed(groups, agent, path):
    """Whether robots.txt lets agent fetch path: the agent's group applies, or else the * group; the
    longest matching rule wins, and Allow wins a tie (RFC 9309, section 2.2.2)."""
    rules = groups.get(agent.lower(), groups.get("*", []))
    matches = [(length, allow) for length, allow, pattern in rules if pattern.match(path)]
    return max(matches)[1] if matches else True


def page_entry(site_dir, item, host, groups):
    """(url, fingerprint) for one sitemap entry, or None when the page is not eligible."""
    locs = [el.text for el in item if el.tag.rsplit("}", 1)[-1] == "loc"]
    if len(locs) != 1 or not locs[0]:
        raise ValueError("each sitemap entry needs one loc")
    url = locs[0]
    path = own_url(url, host)
    target = site_dir / unquote(path).lstrip("/")
    if path.endswith("/"):
        target = target / "index.html"
    if site_dir not in target.resolve().parents:
        raise ValueError(f"page escapes build directory: {url}")
    if target.suffix != ".html":
        raise ValueError(f"sitemap entry is not an HTML page: {url}")
    page = Page(target.read_text(encoding="utf-8"))
    if (page.noindex or page.canonicals != [url]
            or not all(robots_allowed(groups, agent, path) for agent in ROBOTS_AGENTS)):
        return None
    return url, page.fingerprint()


def snapshot(site_dir, config, baseline=False):
    """Fingerprints of the canonical, indexable pages in a build's sitemap, by URL.

    The build to notify about must serve the key and list only pages of this host, or the run
    stops. A baseline (an earlier build to compare with) needs no key file and may be empty; it
    leaves out entries it cannot fingerprint, such as another host's pages, which then count as
    added or changed.
    """
    site_dir = Path(site_dir).resolve()
    if not baseline and (site_dir / (config["key"] + ".txt")).read_text(encoding="utf-8").strip() != config["key"]:
        raise ValueError("built IndexNow key file does not match indexnow.json")
    tree = ET.parse(site_dir / "sitemap.xml")
    if tree.getroot().tag.rsplit("}", 1)[-1] != "urlset":
        raise ValueError("expected a sitemap urlset, not a sitemap index")
    groups = robots_rules((site_dir / "robots.txt").read_text(encoding="utf-8"))
    pages = {}
    for item in tree.getroot():
        try:
            entry = page_entry(site_dir, item, config["host"], groups)
            if entry and entry[0] in pages:
                raise ValueError(f"duplicate sitemap URL: {entry[0]}")
        except (ValueError, OSError):
            if baseline:
                continue
            raise
        if entry:
            pages[entry[0]] = entry[1]
    if not pages and not baseline:
        raise ValueError("no canonical indexable HTML pages found; refusing a mass deletion")
    return dict(sorted(pages.items()))


def read_state(path, host):
    """The received fingerprints by URL, or None when there is no state of this VERSION."""
    path = Path(path)
    if not path.exists():
        return None
    state = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(state, dict) and state.get("host") == host and state.get("version") != VERSION:
        print(f"warning: ignoring {path}, a state of version {state.get('version')!r} rather than {VERSION}", file=sys.stderr)
        return None
    if (not isinstance(state, dict) or state.get("version") != VERSION
            or state.get("host") != host or not isinstance(state.get("pages"), dict)):
        raise ValueError("IndexNow state has the wrong host, version or pages format")
    for url, digest in state["pages"].items():
        own_url(url, host)
        if not isinstance(digest, str) or not re.fullmatch("[a-f0-9]{64}", digest):
            raise ValueError(f"invalid stored fingerprint for {url}")
    return state["pages"]


def plan(current, previous):
    return {"added": sorted(set(current) - set(previous)),
            "changed": sorted(url for url in current.keys() & previous.keys() if current[url] != previous[url]),
            "deleted": sorted(set(previous) - set(current))}


class NoRedirect(HTTPRedirectHandler):
    """Turn a redirect into an HTTPError: urllib would resend a redirected POST as a GET without
    its body, and a 200 from the new address would then pass for a receipt."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = build_opener(NoRedirect)


def urlopen(request, timeout):
    return _OPENER.open(request, timeout=timeout)


def fetch_live(url, attempts, delay, accept):
    """GET url until accept(text) returns without ValueError, waiting for a CDN that is not ready.
    Returns accept's result, or raises ValueError with the last error."""
    error = "not checked"
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
            with urlopen(request, timeout=30) as response:
                if response.status != 200 or response.geturl() != url:
                    raise ValueError(f"HTTP {response.status} from {response.geturl()}")
                return accept(response.read(65536).decode("utf-8"))
        except HTTPError as exc:
            error = str(exc)
            exc.close()
        except (URLError, http.client.HTTPException, OSError, ValueError) as exc:
            error = str(exc) or type(exc).__name__
        if attempt + 1 < attempts:
            time.sleep(delay)
    raise ValueError(f"{url} is not ready after {attempts} attempt(s): {error}")


def verify_live_key(config, attempts=6, delay=10):
    """Check that the live site serves the key at its canonical URL, where IndexNow looks for it."""
    def accept(text):
        if text.strip() != config["key"]:
            raise ValueError("the key URL does not return the key in indexnow.json")
    fetch_live(f"https://{config['host']}/{config['key']}.txt", attempts, delay, accept)


def live_commit(config, attempts=6, delay=10):
    """The commit that the live /build.json names; deploy.yml writes that file."""
    def accept(text):
        record = json.loads(text)
        commit = record.get("commit") if isinstance(record, dict) else None
        if not isinstance(commit, str) or not re.fullmatch("[0-9a-f]{40}", commit):
            raise ValueError("build.json names no commit")
        return commit
    # Pages purges its CDN when it deploys, which keeps this read fresh; the CDN ignores the query
    # string, which only marks the request, as the live-check job's does
    return fetch_live(f"https://{config['host']}/build.json?indexnow={time.time_ns()}", attempts, delay, accept)


def live_is_newer(config, args):
    """Whether --expect-commit names a commit that the live site no longer serves: a late re-run of an
    older deploy's job, which must neither send nor record anything, since the newer deploy does."""
    if args.expect_commit is None:
        return False
    live = live_commit(config, args.key_attempts, args.key_delay)
    if live == args.expect_commit:
        return False
    print(f"https://{config['host']}/ serves commit {live}, not {args.expect_commit}. The newer deploy "
          "notifies its own changes, so this run sent and recorded nothing.")
    return True


def submit(config, urls):
    payload = {"host": config["host"], "key": config["key"],
               "keyLocation": f"https://{config['host']}/{config['key']}.txt", "urlList": urls}
    request = Request(ENDPOINT, data=json.dumps(payload, separators=(",", ":")).encode(),
                      headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
    except HTTPError as exc:
        headers = exc.headers or {}
        extra = f"; Retry-After: {headers.get('Retry-After')}" if headers.get("Retry-After") else ""
        reasons = {400: "invalid request format", 403: "key validation failed", 422: "host/key/URL mismatch",
                   429: "rate limited; retry later"}
        reason = reasons.get(exc.code, "redirect not followed" if 300 <= exc.code < 400 else "notification failed")
        exc.close()
        raise ValueError(f"IndexNow HTTP {exc.code}: {reason}{extra}") from exc
    if status not in (200, 202):
        raise ValueError(f"unexpected IndexNow HTTP {status}; state was not advanced")
    return status


def write_state(path, host, pages):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps({"version": VERSION, "host": host, "pages": pages}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site-dir", type=Path, required=True, help="the production build of the deployed commit")
    parser.add_argument("--config", type=Path, default=ROOT / "indexnow.json")
    parser.add_argument("--state", type=Path, default=ROOT / ".indexnow-state.json",
                        help="the received fingerprints; written after each received batch")
    parser.add_argument("--baseline-site-dir", type=Path,
                        help="compare with this earlier build, such as the previously deployed commit's, instead of the state")
    parser.add_argument("--bootstrap", action="store_true",
                        help="with no state or baseline build, notify every page instead of recording a baseline")
    parser.add_argument("--deployed-url", help="where the deploy published; nothing is sent unless it is https://<host>/")
    parser.add_argument("--expect-commit", help="send nothing unless the live /build.json names this commit")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without network requests or state writes")
    parser.add_argument("--key-attempts", type=int, default=6)
    parser.add_argument("--key-delay", type=float, default=10)
    args = parser.parse_args(argv)
    if args.key_attempts < 1 or not 0 <= args.key_delay <= 3600:  # also refuses nan and inf
        parser.error("--key-attempts must be positive and --key-delay between 0 and 3600 seconds")
    if args.expect_commit is not None and not re.fullmatch("[0-9a-f]{40}", args.expect_commit):
        parser.error("--expect-commit must be a full commit SHA in lowercase hex")
    try:
        config = load_config(args.config)
        host = config["host"]
        if args.deployed_url is not None and args.deployed_url.rstrip("/") != f"https://{host}":
            print(f"This run deployed to {args.deployed_url or 'no address'}, not https://{host}/; nothing to notify.")
            return 0
        current = snapshot(args.site_dir, config)
        if args.baseline_site_dir is not None:
            previous, baseline = snapshot(args.baseline_site_dir, config, baseline=True), "build"
        else:
            previous, baseline = read_state(args.state, host), "state"
            if previous is None and args.bootstrap:
                previous, baseline = {}, "empty"
        if previous is None:
            print(json.dumps({"added": [], "baseline": "none", "changed": [], "deleted": [], "dry_run": args.dry_run,
                              "host": host}, sort_keys=True))
            if args.dry_run:
                print(f"Dry run: with no state or baseline build, a run records {len(current)} current page(s) as "
                      "the baseline and notifies nothing. No requests or state changes.")
                return 0
            if live_is_newer(config, args):
                return 0
            write_state(args.state, host, current)
            print(f"No state or baseline build: recorded {len(current)} current page(s) as the baseline and "
                  "notified nothing (--bootstrap notifies every page).")
            return 0
        changes = plan(current, previous)
        print(json.dumps({"baseline": baseline, "dry_run": args.dry_run, "host": host, **changes}, sort_keys=True))
        urls = sorted(set(sum(changes.values(), [])))
        if args.dry_run:
            print("Dry run; no requests or state changes.")
            return 0
        if not urls:
            if baseline != "state":
                if live_is_newer(config, args):
                    return 0
                write_state(args.state, host, current)
            print("No indexable content changes; no notification sent.")
            return 0
        try:
            if live_is_newer(config, args):
                return 0
        except ValueError:
            if baseline != "state":
                write_state(args.state, host, previous)  # so that the next deploy sends this deploy's changes
            raise
        received = dict(previous)
        if baseline != "state":
            # Likewise if the key check or a request fails: the next run finds the earlier versions
            write_state(args.state, host, received)
        verify_live_key(config, args.key_attempts, args.key_delay)
        for offset in range(0, len(urls), BATCH):
            batch = urls[offset:offset + BATCH]
            status = submit(config, batch)
            for url in batch:
                if url in current:
                    received[url] = current[url]
                else:
                    received.pop(url, None)
            # Keep received batches if a later batch fails; its URLs keep their old fingerprints and retry
            write_state(args.state, host, received)
            detail = "received; key validation pending" if status == 202 else "received"
            print(f"IndexNow HTTP {status}: {len(batch)} URL(s) {detail}. Crawling and indexing are not guaranteed.")
        return 0
    except (ValueError, OSError, URLError, http.client.HTTPException, ET.ParseError) as exc:
        print(f"IndexNow notification failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
