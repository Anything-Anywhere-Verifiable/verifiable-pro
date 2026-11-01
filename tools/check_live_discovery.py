#!/usr/bin/env python3
"""Read-only discovery checks for a deployed site; prints a JSON evidence report.

This checks responses from this machine, not indexing or ranking. The bot probe
only changes a User-Agent header: it does not originate from a crawler's IP
range, and cannot establish whether a CDN/WAF permits the real crawler.
"""
import argparse
import datetime as dt
from html.parser import HTMLParser
import http.client
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))
from indexnow import robots_allowed, robots_rules  # noqa: E402

PATHS = ("/", "/latest/", "/learn/", "/topics/confidential-computing/")
AGENTS = ("Googlebot", "Bingbot", "OAI-SearchBot", "PerplexityBot", "Claude-SearchBot")
USER_AGENT = "verifiable.pro-discovery-check/1.0"
BOT_AGENT = "Mozilla/5.0 (compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot)"
MAX_BYTES = 2 * 1024 * 1024
ROBOTS_VALUE_DIRECTIVES = {"max-snippet", "max-image-preview", "max-video-preview", "unavailable_after"}


def noindex(value):
    # "none" as the value of max-image-preview is not the standalone robots
    # directive "none" (which means noindex, nofollow).
    directives = re.sub(r"\b[a-z][a-z_-]*:\s*[^,\s]+", "", value.lower())
    return bool(set(re.split(r"[,\s]+", directives)) & {"noindex", "none"})


def header_blocks_indexing(values):
    """Check global/search-agent noindex; an agent scope lasts to the next agent.

    Each header starts without a scope. Colons in value-bearing directives such
    as max-snippet:0 are not agent prefixes. Preserve all headers in the report,
    including restrictions for training or other agents outside this audit.
    """
    search_agents = {agent.lower() for agent in AGENTS}
    for value in values:
        scope = None
        for item in value.lower().split(","):
            directive = item.strip()
            prefix, colon, remainder = directive.partition(":")
            if colon and prefix.strip() not in ROBOTS_VALUE_DIRECTIVES:
                scope, directive = prefix.strip(), remainder.strip()
            if scope is None or scope in search_agents:
                if directive in {"noindex", "none"}:
                    return True
    return False


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.canonical, self.alternates, self.robots = [], {}, []
        self.title, self.description, self.has_main = "", "", False
        self.in_title = self.in_head = False
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "head":
            self.in_head = True
        if tag == "main":
            self.has_main = True
        if tag == "title" and self.in_head:
            self.in_title = True
        if tag == "meta":
            name = (attrs.get("name") or "").lower()
            value = attrs.get("content") or ""
            if name == "description":
                self.description = value
            if name in {"robots", *(agent.lower() for agent in AGENTS)}:
                self.robots.append({"agent": name, "value": value})
        if tag == "link":
            rel = (attrs.get("rel") or "").lower().split()
            if "canonical" in rel:
                self.canonical.append(attrs.get("href"))
            if "alternate" in rel and attrs.get("hreflang"):
                self.alternates.setdefault(attrs["hreflang"].lower(), []).append(attrs.get("href"))

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        if tag == "title":
            self.in_title = False

    def handle_data(self, text):
        if self.in_title:
            self.title += text


def fetch(url, user_agent, timeout):
    """Preserve transport errors separately from HTTP failures; bound response size."""
    result = {"url": url, "user_agent": user_agent, "status": None,
              "final_url": None, "content_type": "", "x_robots_tag": [], "error": None}
    try:
        request = Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
        try:
            response = urlopen(request, timeout=timeout)
        except HTTPError as exc:
            response = exc
        with response:
            result.update(status=response.status, final_url=response.geturl(),
                          content_type=response.headers.get("Content-Type", ""),
                          x_robots_tag=response.headers.get_all("X-Robots-Tag", []))
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError("response exceeds 2 MiB limit")
            text = body.decode("utf-8-sig")
        return result, text
    except (OSError, URLError, ValueError, http.client.HTTPException) as exc:
        result["error"] = str(exc)
        return result, ""


def response_issues(response, accepted_types):
    if response["error"]:
        return ["request_error: " + response["error"]]
    issues = []
    if response["status"] != 200:
        issues.append("expected HTTP 200")
    if response["final_url"] != response["url"]:
        issues.append("requested canonical URL redirects")
    if response["content_type"].split(";", 1)[0].strip().lower() not in accepted_types:
        issues.append("unexpected Content-Type")
    return issues


def page_issues(response, text, base, path):
    issues = response_issues(response, {"text/html", "application/xhtml+xml"})
    if response["error"] or response["status"] != 200:
        return issues, {}
    page = Metadata(text)
    if header_blocks_indexing(response["x_robots_tag"]):
        issues.append("X-Robots-Tag blocks indexing globally or for a checked search crawler")
    if any(noindex(rule["value"]) for rule in page.robots):
        issues.append("HTML robots metadata blocks a search crawler")
    if page.canonical != [base + path]:
        issues.append("canonical is missing, duplicated or does not match requested URL")
    english = path[3:] if path.startswith("/zh/") else path
    expected = {"en": [base + english], "zh-cn": [base + "/zh" + english],
                "x-default": [base + english]}
    if page.alternates != expected:
        issues.append("hreflang links do not match both editions and x-default")
    if not page.title.strip() or not page.description.strip() or not page.has_main:
        issues.append("missing title, description or main content landmark")
    metadata = {"title": page.title.strip(), "description": page.description,
                "canonical": page.canonical, "hreflang": page.alternates,
                "robots": page.robots, "has_main": page.has_main}
    return issues, metadata


def audit(base, timeout=15, fetcher=fetch):
    paths = tuple(path for english in PATHS for path in (english, "/zh" + english))
    report = {"checked_at": dt.datetime.now(dt.timezone.utc).isoformat(), "base_url": base,
              "scope": "HTTP responses from this machine; not a search-index or ranking test",
              "snippet_limit": "Snippet eligibility is not checked (including nosnippet, max-snippet and data-nosnippet)",
              "bot_probe_limit": "User-Agent simulation only; real crawler IP/CDN/WAF access is not verified",
              "checks": []}

    def get(path, agent=USER_AGENT):
        response, text = fetcher(base + path, agent, timeout)
        report["checks"].append(response)
        return response, text

    robots, text = get("/robots.txt")
    robots["issues"] = response_issues(robots, {"text/plain"})
    if not robots["issues"]:
        groups = robots_rules(text)
        robots["blocked_paths"] = {agent: [path for path in paths if not robots_allowed(groups, agent, path)]
                                   for agent in AGENTS}
        if any(robots["blocked_paths"].values()):
            robots["issues"].append("robots.txt blocks a checked page for a search crawler")
        declared = [line.split(":", 1)[1].strip() for line in text.splitlines()
                    if line.lower().startswith("sitemap:")]
        if base + "/sitemap.xml" not in declared:
            robots["issues"].append("robots.txt does not declare this sitemap")

    sitemap, text = get("/sitemap.xml")
    sitemap["issues"] = response_issues(sitemap, {"application/xml", "text/xml"})
    if not sitemap["issues"]:
        try:
            root = ET.fromstring(text)
            if root.tag.rsplit("}", 1)[-1] != "urlset":
                raise ValueError("expected a urlset sitemap")
            urls = [node.text for node in root.findall("{*}url/{*}loc")]
            sitemap["url_count"] = len(urls)
            sitemap["missing_pages"] = [base + path for path in paths if base + path not in urls]
            if sitemap["missing_pages"]:
                sitemap["issues"].append("sitemap omits checked canonical pages")
        except (ET.ParseError, ValueError) as exc:
            sitemap["issues"].append("invalid sitemap: " + str(exc))

    for path in paths:
        response, text = get(path)
        response["issues"], response["metadata"] = page_issues(response, text, base, path)
    response, text = get("/", BOT_AGENT)
    response["probe"] = "OAI-SearchBot User-Agent simulation"
    response["issues"], response["metadata"] = page_issues(response, text, base, "/")
    report["ok"] = not any(check["issues"] for check in report["checks"])
    report["request_errors"] = sum(check["error"] is not None for check in report["checks"])
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="https://verifiable.pro")
    parser.add_argument("--timeout", type=float, default=15, help="seconds per HTTP request")
    parser.add_argument("--out", type=Path, help="also save the JSON report at this path")
    args = parser.parse_args(argv)
    base = args.base_url.rstrip("/")
    parts = urlsplit(base)
    if (parts.scheme not in {"http", "https"} or not parts.netloc or parts.path
            or parts.query or parts.fragment or parts.username or parts.password):
        parser.error("--base-url must be an HTTP(S) origin without a path or credentials")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    report = audit(base, args.timeout)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
