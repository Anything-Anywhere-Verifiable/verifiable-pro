"""Live discovery audit checks against offline HTTP fixtures, never the network."""
from contextlib import redirect_stdout
from email.message import Message
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import check_live_discovery as live  # noqa: E402

BASE = "https://example.org"


def page(path):
    english = path[3:] if path.startswith("/zh/") else path
    return (f'<html><head><title>News &amp; analysis</title><meta name="description" content="Coverage">'
            f'<link rel="canonical" href="{BASE + path}">'
            f'<link rel="alternate" hreflang="en" href="{BASE + english}">'
            f'<link rel="alternate" hreflang="zh-CN" href="{BASE}/zh{english}">'
            f'<link rel="alternate" hreflang="x-default" href="{BASE + english}">'
            '</head><body><main>Readable content</main></body></html>')


def fixture(url, agent, timeout):
    path = url[len(BASE):]
    result = {"url": url, "status": 200, "final_url": url, "user_agent": agent,
              "content_type": "text/html; charset=utf-8", "x_robots_tag": [], "error": None}
    if path == "/robots.txt":
        result["content_type"] = "text/plain"
        return result, f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n"
    if path == "/sitemap.xml":
        result["content_type"] = "application/xml"
        urls = [BASE + p for english in live.PATHS for p in (english, "/zh" + english)]
        return result, ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' +
                        ''.join(f'<url><loc>{url}</loc></url>' for url in urls) + '</urlset>')
    return result, page(path)


class LiveDiscoveryTests(unittest.TestCase):
    def test_fetch_keeps_http_error_headers_and_transport_error(self):
        headers = Message()
        headers.add_header("Content-Type", "text/html")
        headers.add_header("X-Robots-Tag", "noindex")
        denied = HTTPError(BASE + "/", 403, "Forbidden", headers, io.BytesIO(b"Denied"))
        with patch.object(live, "urlopen", side_effect=denied):
            response, text = live.fetch(BASE + "/", live.BOT_AGENT, 5)
        self.assertEqual(response["status"], 403)
        self.assertIsNone(response["error"])
        self.assertEqual(response["x_robots_tag"], ["noindex"])
        self.assertEqual(text, "Denied")
        with patch.object(live, "urlopen", side_effect=URLError("DNS lookup failed")):
            response, text = live.fetch(BASE + "/", live.USER_AGENT, 5)
        self.assertIsNone(response["status"])
        self.assertIn("DNS lookup failed", response["error"])
        self.assertEqual(text, "")

    def test_complete_bilingual_site_and_single_bot_probe(self):
        report = live.audit(BASE, fetcher=fixture)
        self.assertTrue(report["ok"])
        self.assertEqual(len(report["checks"]), 11)
        self.assertEqual(sum(c["user_agent"] == live.BOT_AGENT for c in report["checks"]), 1)
        self.assertIn("not verified", report["bot_probe_limit"])

    def test_specific_robot_group_can_block_while_wildcard_allows(self):
        def blocked(url, agent, timeout):
            response, text = fixture(url, agent, timeout)
            if url.endswith("robots.txt"):
                text += "User-agent: OAI-SearchBot\nDisallow: /\nAllow: /learn/\n"
            return response, text
        report = live.audit(BASE, fetcher=blocked)
        self.assertFalse(report["ok"])
        blocked_paths = report["checks"][0]["blocked_paths"]
        self.assertIn("/", blocked_paths["OAI-SearchBot"])
        self.assertNotIn("/learn/", blocked_paths["OAI-SearchBot"])
        self.assertEqual(blocked_paths["Googlebot"], [])

    def test_http_failures_and_network_errors_remain_distinct(self):
        def broken(url, agent, timeout):
            response, text = fixture(url, agent, timeout)
            if url.endswith("robots.txt"):
                response.update(status=None, final_url=None, error="DNS lookup failed")
            elif agent == live.BOT_AGENT:
                response["status"] = 403
            return response, text
        report = live.audit(BASE, fetcher=broken)
        self.assertFalse(report["ok"])
        self.assertEqual(report["request_errors"], 1)
        self.assertEqual(report["checks"][-1]["issues"], ["expected HTTP 200"])
        self.assertTrue(report["checks"][0]["issues"][0].startswith("request_error:"))

    def test_html_and_http_robots_restrictions(self):
        response, text = fixture(BASE + "/", live.USER_AGENT, 15)
        response["x_robots_tag"] = ["max-image-preview:large", "googlebot: noindex"]
        text = text.replace("</head>", '<meta name="OAI-SearchBot" content="none"></head>')
        issues, _ = live.page_issues(response, text, BASE, "/")
        self.assertTrue(any("X-Robots-Tag" in issue for issue in issues))
        self.assertTrue(any("HTML robots" in issue for issue in issues))

    def test_image_preview_none_does_not_mean_noindex(self):
        response, text = fixture(BASE + "/", live.USER_AGENT, 15)
        text = text.replace("</head>", '<meta name="robots" content="max-image-preview: none"></head>')
        issues, _ = live.page_issues(response, text, BASE, "/")
        self.assertEqual(issues, [])
        self.assertTrue(live.noindex("max-image-preview: none, noindex"))
        self.assertTrue(live.noindex("none"))
        self.assertTrue(live.noindex("noindex nofollow"))

    def test_header_robot_scope_applies_until_next_agent_and_resets_per_header(self):
        cases = [
            (["GPTBot: noindex"], False),
            (["GPTBot: noindex, nofollow, none"], False),
            (["GPTBot: noindex, Googlebot: none, nofollow"], True),
            (["googlebot: max-snippet:0, noindex"], True),
            (["GPTBot: max-snippet:0, noindex"], False),
            (["max-snippet:0, noindex"], True),
            (["max-image-preview:large, none"], True),
            (["GPTBot: noindex", "none"], True),
            (["noindex", "GPTBot: index"], True),
            (["OAI-SearchBot: noindex, GPTBot: index"], True),
            (["nosnippet, max-snippet:0"], False),
        ]
        for headers, expected in cases:
            with self.subTest(headers=headers):
                self.assertEqual(live.header_blocks_indexing(headers), expected)

    def test_nonsearch_restrictions_are_preserved_without_failing_audit(self):
        def scoped(url, agent, timeout):
            response, text = fixture(url, agent, timeout)
            response["x_robots_tag"] = ["GPTBot: noindex, nofollow"]
            return response, text
        report = live.audit(BASE, fetcher=scoped)
        self.assertTrue(report["ok"])
        self.assertEqual(report["checks"][-1]["x_robots_tag"], ["GPTBot: noindex, nofollow"])
        self.assertIn("not checked", report["snippet_limit"])

    def test_redirect_canonical_hreflang_and_content_type(self):
        response, text = fixture(BASE + "/zh/learn/", live.USER_AGENT, 15)
        response["final_url"] = BASE + "/"
        response["content_type"] = "text/plain"
        text = text.replace('rel="canonical"', 'rel="alternate"').replace('hreflang="en"', 'hreflang="de"')
        issues, _ = live.page_issues(response, text, BASE, "/zh/learn/")
        for expected in ("redirects", "Content-Type", "canonical", "hreflang"):
            self.assertTrue(any(expected in issue for issue in issues), issues)

    def test_sitemap_missing_pages_and_invalid_xml(self):
        for content in ('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>', '<bad'):
            def incomplete(url, agent, timeout):
                response, text = fixture(url, agent, timeout)
                return response, content if url.endswith("sitemap.xml") else text
            with self.subTest(content=content):
                report = live.audit(BASE, fetcher=incomplete)
                self.assertFalse(report["ok"])
                self.assertTrue(report["checks"][1]["issues"])

    def test_cli_saves_report_and_failure_exit_status(self):
        report = {"ok": False, "request_errors": 1, "checks": []}
        with tempfile.TemporaryDirectory() as folder, patch.object(live, "audit", return_value=report):
            target = Path(folder) / "report.json"
            with redirect_stdout(io.StringIO()) as output:
                code = live.main(["--base-url", BASE, "--out", str(target)])
            self.assertEqual(code, 1)
            self.assertEqual(json.loads(target.read_text()), report)
            self.assertEqual(json.loads(output.getvalue()), report)


if __name__ == "__main__":
    unittest.main()
