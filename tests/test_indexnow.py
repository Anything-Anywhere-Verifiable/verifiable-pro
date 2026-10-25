"""Deterministic checks of the deployment change notifications, without the network."""
from contextlib import redirect_stderr, redirect_stdout
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.client
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parent.parent
for _path in (str(ROOT), str(ROOT / "tools")):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import indexnow  # noqa: E402


HOST = "example.org"
KEY = "1234567890abcdef1234567890abcdef"
BASE = "https://" + HOST
COMMIT = "a" * 40


def html(path="/", body="Original article", extra="", canonical=None):
    return (f'<html><head><title>Research</title><link rel="canonical" href="{canonical or BASE + path}">'
            f'<meta name="description" content="An introduction">{extra}</head>'
            f'<body><nav>Navigation</nav><main><h1>Research</h1><p>{body}</p></main>'
            '<footer>2026</footer><script>var build="old";</script></body></html>')


class Response:
    """What urlopen returns for one URL."""
    def __init__(self, url, body=b"", status=200):
        self.url, self.body, self.status = url, body, status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.body[:limit]

    def geturl(self):
        return self.url


class IndexNowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / "public"
        self.site.mkdir()
        self.config = self.root / "indexnow.json"
        self.settings = {"host": HOST, "key": KEY}
        self.config.write_text(json.dumps(self.settings))
        self.state = self.root / "state.json"
        (self.site / (KEY + ".txt")).write_text(KEY + "\n")
        (self.site / "robots.txt").write_text("User-agent: *\nAllow: /\n")
        self.pages({"/": html()})
        self.argv = ["--site-dir", str(self.site), "--config", str(self.config), "--state", str(self.state)]

    def pages(self, pages):
        for path, text in pages.items():
            target = self.site / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)
        self.sitemap([BASE + path for path in pages])

    def sitemap(self, urls):
        rows = "".join(f"<url><loc>{url}</loc></url>" for url in urls)
        (self.site / "sitemap.xml").write_text(f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>')

    def baseline(self):
        """A copy of the current build, as an earlier deploy's build; it need not serve the key."""
        earlier = self.root / "earlier"
        shutil.copytree(self.site, earlier)
        (earlier / (KEY + ".txt")).unlink()
        return earlier

    def run_cli(self, *extra):
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output):
            code = indexnow.main(self.argv + list(extra))
        return code, output.getvalue()

    def test_dry_run_is_deterministic_without_network_or_state_writes(self):
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            first = self.run_cli("--dry-run")
            self.assertEqual(first, self.run_cli("--dry-run"))
            self.assertEqual(first, self.run_cli("--dry-run", "--expect-commit", COMMIT))
            bootstrap = self.run_cli("--dry-run", "--bootstrap")
        self.assertEqual(first[0], 0)
        self.assertEqual(json.loads(first[1].splitlines()[0]),
                         {"added": [], "baseline": "none", "changed": [], "deleted": [], "dry_run": True, "host": HOST})
        self.assertIn("records 1 current page(s) as the baseline", first[1])
        self.assertEqual(json.loads(bootstrap[1].splitlines()[0])["added"], [BASE + "/"])
        self.assertFalse(self.state.exists())

    def test_without_state_or_baseline_a_run_records_the_pages_and_notifies_nothing(self):
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            code, output = self.run_cli()
            self.assertEqual(code, 0)
            self.assertIn("recorded 1 current page(s) as the baseline", output)
            self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(self.site, self.settings))
            self.assertIn("No indexable content changes", self.run_cli()[1])

    def test_a_baseline_build_stands_in_for_a_missing_state(self):
        self.pages({"/": html(), "/old/": html("/old/"), "/same/": html("/same/")})
        earlier = self.baseline()
        shutil.rmtree(self.site / "old")
        self.pages({"/": html(body="Updated article"), "/same/": html("/same/"), "/new/": html("/new/")})
        calls = []
        with patch.object(indexnow, "verify_live_key"), \
                patch.object(indexnow, "submit", side_effect=lambda c, u: calls.append(u) or 200):
            code, output = self.run_cli("--baseline-site-dir", str(earlier))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.splitlines()[0])["baseline"], "build")
        self.assertEqual(calls, [[BASE + "/", BASE + "/new/", BASE + "/old/"]])
        self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(self.site, self.settings))

    def test_a_baseline_build_without_changes_records_a_state_without_network(self):
        earlier = self.baseline()
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            code, output = self.run_cli("--baseline-site-dir", str(earlier))
        self.assertEqual(code, 0)
        self.assertIn("No indexable content changes", output)
        self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(self.site, self.settings))

    def test_a_baseline_on_another_host_counts_every_page_as_added(self):
        earlier = self.baseline()
        sitemap = earlier / "sitemap.xml"
        sitemap.write_text(sitemap.read_text().replace(BASE, "https://old.example"))
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            code, output = self.run_cli("--baseline-site-dir", str(earlier), "--dry-run", "--expect-commit", COMMIT)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.splitlines()[0])["added"], [BASE + "/"])

    def test_a_failed_send_from_a_baseline_build_leaves_its_pages_to_retry(self):
        earlier = self.baseline()
        self.pages({"/": html(body="Updated article")})
        with patch.object(indexnow, "verify_live_key"), \
                patch.object(indexnow, "submit", side_effect=ValueError("IndexNow HTTP 429: rate limited")):
            self.assertEqual(self.run_cli("--baseline-site-dir", str(earlier))[0], 1)
        self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(earlier, self.settings, baseline=True))
        self.assertEqual(json.loads(self.run_cli("--dry-run")[1].splitlines()[0])["changed"], [BASE + "/"])

    def test_fingerprint_ignores_global_build_script_chrome_and_css_changes(self):
        before = html(body='A <a href="/paper/">paper</a><aside class="sidebar">Old sidebar</aside><svg><title>Diagram</title></svg>'
                           '<section class="related"><h2>More on agents</h2><a href="/older/">Older story</a></section>'
                           '<div class="check-correct"><a href="https://github.com/owner/repo/edit/main/a.md">Edit</a></div>'
                           '<span class="byline-mark" title="Automated news gathering">W</span>')
        after = (before.replace("Navigation", "New navigation").replace("2026", "2027").replace('build="old"', 'build="new"')
                 .replace("Old sidebar", "New sidebar").replace('<h1>', '<h1 class="red">')
                 .replace("Older story", "Newest story").replace("/older/", "/newest/")
                 .replace("owner/repo", "new-owner/repo").replace("Automated news gathering", "Automated research"))
        self.assertEqual(indexnow.Page(before).fingerprint(), indexnow.Page(after).fingerprint())
        self.assertEqual(indexnow.Page(before).title, ["Research"])

    def test_fingerprint_covers_content_metadata_links_images_and_structured_data(self):
        before = html(body='A <a href="/paper/">paper</a><img src="/picture.png" alt="A plot">',
                      extra='<script type="application/ld+json">{"name":"Research"}</script>')
        for after in (before.replace("A plot", "A chart"), before.replace('/paper/', '/new/'),
                      before.replace("An introduction", "A new summary"), before.replace("A <a", "The <a"),
                      before.replace('{"name":"Research"}', '{"name":"New research"}')):
            with self.subTest(after=after):
                self.assertNotEqual(indexnow.Page(before).fingerprint(), indexnow.Page(after).fingerprint())

    def test_valueless_link_attributes_do_not_break_the_fingerprint(self):
        page = html(extra='<link rel="alternate" hreflang="zh" href><link rel="alternate" hreflang="en" href="/en/">')
        self.assertRegex(indexnow.Page(page).fingerprint(), "^[0-9a-f]{64}$")

    def test_only_canonical_indexable_robot_allowed_sitemap_pages_are_eligible(self):
        self.pages({"/": html(), "/private/": html("/private/", extra='<meta name="robots" content="noindex,follow">'),
                    "/duplicate/": html("/duplicate/", canonical=BASE + "/"), "/blocked/": html("/blocked/")})
        (self.site / "robots.txt").write_text("User-agent: *\nDisallow: /blocked/\n")
        self.assertEqual(set(indexnow.snapshot(self.site, self.settings)), {BASE + "/"})

    def test_robots_rules_are_read_as_rfc_9309_on_every_python(self):
        cases = [
            ("User-agent: *\nAllow: /\nDisallow: /drafts/\n", {"/": True, "/drafts/x/": False}),
            ("User-agent: *\nDisallow: /\nAllow: /articles/\nAllow: /$\n", {"/": True, "/articles/a/": True, "/other/": False}),
            ("User-agent: *\nDisallow: /*/q/\n", {"/search/q/": False, "/search/": True}),
            ("User-agent: *\nAllow: /p\nDisallow: /p\n", {"/p/": True}),
            ("User-agent: *\nAllow: /p\nDisallow: /p$\n", {"/p": False, "/p/": True}),  # the $ counts toward the length
            ("User-agent: *\nDisallow:\n", {"/": True}),
            ("Disallow: /x/\nUser-agent: *\nAllow: /\n", {"/x/": True}),  # a rule outside any group applies to none
        ]
        for text, expected in cases:
            groups = indexnow.robots_rules(text)
            for path, allowed in expected.items():
                with self.subTest(text=text, path=path):
                    self.assertEqual(indexnow.robots_allowed(groups, "*", path), allowed)
        groups = indexnow.robots_rules("# Crawlers: read this\nUser-agent: Googlebot\nUser-agent: Bingbot\nDisallow: /b/\n\n"
                                       "User-agent: *  # every other crawler\nDisallow: /s/\n# Disallow: /c/\n"
                                       "Sitemap: https://example.org/sitemap.xml\n")
        for agent in ("googlebot", "bingbot"):  # both agents of the first group share its rules
            self.assertFalse(indexnow.robots_allowed(groups, agent, "/b/"))
        self.assertTrue(indexnow.robots_allowed(groups, "bingbot", "/s/"))
        self.assertTrue(indexnow.robots_allowed(groups, "*", "/b/"))
        self.assertFalse(indexnow.robots_allowed(groups, "*", "/s/"))
        self.assertTrue(indexnow.robots_allowed(groups, "*", "/c/"))
        # A rule line, even an empty Disallow, ends a group's user-agent lines
        groups = indexnow.robots_rules("User-agent: bingbot\nDisallow:\nUser-agent: other\nDisallow: /x/\n")
        self.assertTrue(indexnow.robots_allowed(groups, "bingbot", "/x/"))
        self.assertFalse(indexnow.robots_allowed(groups, "other", "/x/"))
        # A Disallow after "Allow: /" takes the page out, whichever Python runs the deploy, and so does a
        # rule for Bing's crawler alone, since IndexNow shares the notification with Bing
        self.pages({"/": html(), "/drafts/x/": html("/drafts/x/"), "/b/": html("/b/")})
        (self.site / "robots.txt").write_text("User-agent: *\nAllow: /\nDisallow: /drafts/\n\nUser-agent: Bingbot\n"
                                              "Allow: /\nDisallow: /drafts/\nDisallow: /b/\n")
        self.assertEqual(set(indexnow.snapshot(self.site, self.settings)), {BASE + "/"})

    def test_foreign_noncanonical_and_unsafe_urls_fail_before_network(self):
        for url in ("https://evil.example/", "http://example.org/", BASE + "/?q=x", BASE + "/#part", BASE + "/%2e%2e/a"):
            with self.subTest(url=url):
                self.sitemap([url])
                with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
                    self.assertEqual(self.run_cli("--bootstrap")[0], 1)

    def test_missing_main_or_empty_eligible_sitemap_cannot_trigger_mass_deletion(self):
        self.pages({"/": html().replace("<main>", "<section>").replace("</main>", "</section>")})
        self.assertEqual(self.run_cli("--dry-run")[0], 1)
        self.pages({"/": html(extra='<meta name="robots" content="none">')})
        self.assertEqual(self.run_cli("--dry-run")[0], 1)

    def test_no_change_does_not_fetch_key_or_notify(self):
        indexnow.write_state(self.state, HOST, indexnow.snapshot(self.site, self.settings))
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            code, output = self.run_cli("--expect-commit", COMMIT)  # as in every deploy without changes
        self.assertEqual(code, 0)
        self.assertIn("No indexable content changes", output)

    def test_content_change_and_deletion_are_sent_once_after_key_verification(self):
        self.pages({"/": html(), "/old/": html("/old/")})
        indexnow.write_state(self.state, HOST, indexnow.snapshot(self.site, self.settings))
        self.pages({"/": html(body="Updated article"), "/new/": html("/new/")})
        calls = []
        with patch.object(indexnow, "verify_live_key", side_effect=lambda *a: calls.append("key")), \
                patch.object(indexnow, "submit", side_effect=lambda c, u: calls.append(u) or 200):
            code, output = self.run_cli()
        self.assertEqual(code, 0)
        self.assertEqual(calls, ["key", [BASE + "/", BASE + "/new/", BASE + "/old/"]])
        self.assertIn("not guaranteed", output)
        self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(self.site, self.settings))

    def test_202_records_receipt_and_clearly_reports_validation_pending(self):
        with patch.object(indexnow, "verify_live_key"), patch.object(indexnow, "submit", return_value=202):
            code, output = self.run_cli("--bootstrap")
        self.assertEqual(code, 0)
        self.assertIn("key validation pending", output)
        self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(self.site, self.settings))

    def test_notification_failure_preserves_retryable_state(self):
        indexnow.write_state(self.state, HOST, indexnow.snapshot(self.site, self.settings))
        original = self.state.read_bytes()
        self.pages({"/": html(body="New article")})
        with patch.object(indexnow, "verify_live_key"), patch.object(indexnow, "submit", side_effect=ValueError("HTTP 429")):
            code, output = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("429", output)
        self.assertEqual(self.state.read_bytes(), original)
        self.assertEqual(json.loads(self.run_cli("--dry-run")[1].splitlines()[0])["changed"], [BASE + "/"])

    def test_partial_batch_failure_saves_only_received_urls(self):
        current = {f"{BASE}/{n:05d}/": "a" * 64 for n in range(10001)}
        with patch.object(indexnow, "snapshot", return_value=current), patch.object(indexnow, "verify_live_key"), \
                patch.object(indexnow, "submit", side_effect=[200, ValueError("HTTP 429")]):
            self.assertEqual(self.run_cli("--bootstrap")[0], 1)
        received = indexnow.read_state(self.state, HOST)
        self.assertEqual(set(received), set(sorted(current)[:10000]))
        self.assertEqual(indexnow.plan(current, received)["added"], [sorted(current)[-1]])

    def test_a_deploy_to_another_address_such_as_a_fork_notifies_nothing(self):
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")), \
                patch.object(indexnow, "snapshot", side_effect=AssertionError("snapshot")):
            code, output = self.run_cli("--bootstrap", "--deployed-url", "https://someone.github.io/verifiable-pro/")
        self.assertEqual(code, 0)
        self.assertIn("nothing to notify", output)
        self.assertFalse(self.state.exists())
        calls = []
        with patch.object(indexnow, "verify_live_key"), \
                patch.object(indexnow, "submit", side_effect=lambda c, u: calls.append(u) or 200):
            self.assertEqual(self.run_cli("--bootstrap", "--deployed-url", BASE + "/")[0], 0)
        self.assertEqual(calls, [[BASE + "/"]])

    def test_a_run_whose_commit_is_no_longer_live_sends_nothing(self):
        indexnow.write_state(self.state, HOST, indexnow.snapshot(self.site, self.settings))
        original = self.state.read_bytes()
        self.pages({"/": html(body="An older article")})
        with patch.object(indexnow, "live_commit", return_value="b" * 40), \
                patch.object(indexnow, "verify_live_key") as key, patch.object(indexnow, "submit") as send:
            code, output = self.run_cli("--expect-commit", COMMIT)
        self.assertEqual(code, 0)
        self.assertIn("sent and recorded nothing", output)
        key.assert_not_called()
        send.assert_not_called()
        self.assertEqual(self.state.read_bytes(), original)
        with patch.object(indexnow, "live_commit", return_value=COMMIT), patch.object(indexnow, "verify_live_key"), \
                patch.object(indexnow, "submit", return_value=200) as send:
            self.assertEqual(self.run_cli("--expect-commit", COMMIT)[0], 0)
        send.assert_called_once()

    def test_a_late_rerun_without_a_state_records_nothing(self):
        # With no state to restore, an older run's job would otherwise record its older pages as received
        for with_baseline in (False, True):
            extra = ("--baseline-site-dir", str(self.baseline())) if with_baseline else ()
            with self.subTest(with_baseline=with_baseline):
                with patch.object(indexnow, "live_commit", return_value="b" * 40), \
                        patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
                    code, output = self.run_cli("--expect-commit", COMMIT, *extra)
                self.assertEqual(code, 0)
                self.assertIn("sent and recorded nothing", output)
                self.assertFalse(self.state.exists())
                with patch.object(indexnow, "live_commit", return_value=COMMIT):
                    self.assertEqual(self.run_cli("--expect-commit", COMMIT, *extra)[0], 0)
                self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(self.site, self.settings))
                self.state.unlink()

    def test_a_failed_live_commit_check_leaves_the_baseline_for_the_next_deploy(self):
        earlier = self.baseline()
        self.pages({"/": html(body="Updated article")})
        with patch.object(indexnow, "live_commit", side_effect=ValueError("build.json is not ready")), \
                patch.object(indexnow, "submit") as send:
            code, output = self.run_cli("--baseline-site-dir", str(earlier), "--expect-commit", COMMIT)
        self.assertEqual(code, 1)
        self.assertIn("not ready", output)
        send.assert_not_called()
        self.assertEqual(indexnow.read_state(self.state, HOST), indexnow.snapshot(earlier, self.settings, baseline=True))
        self.assertEqual(json.loads(self.run_cli("--dry-run")[1].splitlines()[0])["changed"], [BASE + "/"])

    def test_live_commit_reads_the_deployed_build_record(self):
        requested = []

        def answer(body):
            def respond(request, timeout):
                requested.append(request.full_url)
                return Response(request.full_url, body)
            return respond
        with patch.object(indexnow, "urlopen", side_effect=answer(json.dumps({"commit": COMMIT}).encode())):
            self.assertEqual(indexnow.live_commit(self.settings, attempts=1), COMMIT)
        self.assertRegex(requested[0], r"^https://example\.org/build\.json\?indexnow=\d+$")
        for body in (b"[]", b'{"commit": "main"}', b"not json"):
            with self.subTest(body=body), patch.object(indexnow, "urlopen", side_effect=answer(body)):
                with self.assertRaisesRegex(ValueError, "not ready"):
                    indexnow.live_commit(self.settings, attempts=1)

    def test_published_key_must_match_without_redirect_before_submission(self):
        with patch.object(indexnow, "urlopen", return_value=Response(f"https://www.{HOST}/{KEY}.txt", KEY.encode())), \
                patch.object(indexnow, "submit") as send:
            self.assertEqual(self.run_cli("--bootstrap", "--key-attempts", "1")[0], 1)
            send.assert_not_called()
        with patch.object(indexnow, "urlopen", return_value=Response(f"https://{HOST}/{KEY}.txt", b"another-key\n")):
            with self.assertRaisesRegex(ValueError, "does not return the key"):
                indexnow.verify_live_key(self.settings, attempts=1)
        with patch.object(indexnow, "urlopen", return_value=Response(f"https://{HOST}/{KEY}.txt", KEY.encode() + b"\n")):
            indexnow.verify_live_key(self.settings, attempts=1)

    def test_retry_live_key_then_proceed(self):
        key_url = f"https://{HOST}/{KEY}.txt"
        for error in (OSError("CDN not ready"), http.client.BadStatusLine("HELLO")):
            with self.subTest(error=type(error).__name__), \
                    patch.object(indexnow, "urlopen", side_effect=[error, Response(key_url, KEY.encode())]) as fetch, \
                    patch.object(indexnow.time, "sleep") as sleep:
                indexnow.verify_live_key(self.settings, attempts=2, delay=3)
            self.assertEqual(fetch.call_count, 2)
            sleep.assert_called_once_with(3)

    def test_http_protocol_errors_end_with_a_clean_failure(self):
        with patch.object(indexnow, "verify_live_key"), patch.object(indexnow, "submit", side_effect=http.client.IncompleteRead(b"")):
            code, output = self.run_cli("--bootstrap")
        self.assertEqual(code, 1)
        self.assertIn("IndexNow notification failed", output)
        self.assertNotIn("Traceback", output)

    def test_actual_post_payload_and_response_codes(self):
        for status in (200, 202, 204):
            with patch.object(indexnow, "urlopen", return_value=Response(indexnow.ENDPOINT, status=status)) as fetch:
                if status == 204:
                    with self.assertRaises(ValueError):
                        indexnow.submit(self.settings, [BASE + "/"])
                else:
                    self.assertEqual(indexnow.submit(self.settings, [BASE + "/"]), status)
                request = fetch.call_args.args[0]
                self.assertEqual(request.get_method(), "POST")
                self.assertEqual(request.full_url, indexnow.ENDPOINT)
                self.assertEqual(json.loads(request.data), {"host": HOST, "key": KEY,
                                 "keyLocation": f"{BASE}/{KEY}.txt", "urlList": [BASE + "/"]})
        for status, reason in ((301, "redirect not followed"), (302, "redirect not followed"), (400, "invalid request"),
                               (403, "key validation"), (422, "host/key/URL mismatch"), (429, "rate limited"),
                               (500, "notification failed")):
            error = HTTPError(indexnow.ENDPOINT, status, "failure", {"Retry-After": "60"}, io.BytesIO(b"error"))
            with patch.object(indexnow, "urlopen", side_effect=error):
                with self.assertRaisesRegex(ValueError, f"HTTP {status}: {reason}"):
                    indexnow.submit(self.settings, [BASE + "/"])

    def test_redirects_are_reported_instead_of_followed(self):
        seen = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append(("POST", self.path))
                self.rfile.read(int(self.headers.get("Content-Length") or 0))
                self.answer(302)

            def do_GET(self):
                seen.append(("GET", self.path))
                self.answer(200 if self.path == "/landing" else 302)

            def answer(self, status):
                self.send_response(status)
                if status == 302:
                    self.send_header("Location", "/landing")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_port}"
        self.assertTrue(any(isinstance(handler, indexnow.NoRedirect) for handler in indexnow._OPENER.handlers))
        # The module's opener, without proxies, so that the test stays on this machine
        with patch.object(indexnow, "_OPENER", build_opener(ProxyHandler({}), indexnow.NoRedirect)), \
                patch.object(indexnow, "ENDPOINT", base + "/indexnow"):
            with self.assertRaisesRegex(ValueError, "HTTP 302: redirect not followed"):
                indexnow.submit(self.settings, [BASE + "/"])
            with self.assertRaisesRegex(ValueError, "not ready"):
                indexnow.fetch_live(base + "/key.txt", 1, 0, lambda text: text)
        self.assertEqual(seen, [("POST", "/indexnow"), ("GET", "/key.txt")])

    def test_malformed_or_wrong_host_state_and_config_are_actionable_failures(self):
        for value in ([], {"version": indexnow.VERSION, "host": "evil.example", "pages": {}},
                      {"version": indexnow.VERSION, "host": HOST, "pages": {"https://evil.example/": "a" * 64}}):
            self.state.write_text(json.dumps(value))
            self.assertEqual(self.run_cli("--dry-run")[0], 1)
        self.state.unlink()
        self.config.write_text("[]")
        self.assertEqual(self.run_cli("--dry-run")[0], 1)

    def test_a_state_of_another_version_counts_as_missing(self):
        self.state.write_text(json.dumps({"version": indexnow.VERSION - 1, "host": HOST, "pages": {BASE + "/": "b" * 64}}))
        with patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            code, output = self.run_cli()
        self.assertEqual(code, 0)
        self.assertIn("warning: ignoring", output)
        self.assertIn("recorded 1 current page(s) as the baseline", output)
        self.assertEqual(json.loads(self.state.read_text())["version"], indexnow.VERSION)

    def test_unusable_arguments_are_refused(self):
        for extra in (("--key-delay", "inf"), ("--key-delay", "nan"), ("--key-delay", "1e10"), ("--key-delay", "-1"),
                      ("--key-attempts", "0"), ("--expect-commit", "main")):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                self.run_cli(*extra)

    def test_the_deploy_cache_key_follows_the_state_version(self):
        workflow = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"indexnow-v(\d+)-", workflow), [str(indexnow.VERSION)] * 3)


class RealBuildTests(unittest.TestCase):
    """The fingerprints of the pages that the generator writes."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "public"
        result = subprocess.run([sys.executable, str(ROOT / "build.py"), "--out", str(cls.out)], cwd=ROOT,
                                capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if result.returncode:
            cls.tmp.cleanup()
            raise AssertionError(result.stderr)
        cls.config = indexnow.load_config(ROOT / "indexnow.json")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_other_stories_correction_links_and_tooltips_leave_an_article_unchanged(self):
        repo = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))["repo_url"]
        markers = ('<section class="related"', '<div class="check-correct">', ' title="')
        text = next(page for page in (path.read_text(encoding="utf-8") for path in sorted((self.out / "articles").glob("*/index.html")))
                    if all(marker in page for marker in markers))
        original = indexnow.Page(text).fingerprint()

        def edit(start_marker, end_marker, change):
            start = text.index(start_marker)
            end = text.index(end_marker, start)
            return text[:start] + change(text[start:end]) + text[end:]
        variants = {
            # a newer story on the same topic takes a card's place
            "related stories": edit(markers[0], "</section>", lambda part: re.sub(r">[^<]+<", ">Another story<", part)),
            # the repository moves and the correction label is reworded
            "correction links": edit(markers[1], "</div>", lambda part: part.replace(repo, "https://github.com/example/moved")
                                     .replace("Request a correction", "Report an error")),
            "tooltips": re.sub(r' title="[^"]*"', ' title="Changed"', text),
        }
        for name, variant in variants.items():
            with self.subTest(name):
                self.assertNotEqual(variant, text)
                self.assertEqual(indexnow.Page(variant).fingerprint(), original)
        headline = text.replace('<h1 class="article-title">', '<h1 class="article-title">Updated: ', 1)
        self.assertNotEqual(indexnow.Page(headline).fingerprint(), original)

    def test_every_sitemap_page_is_eligible_and_an_unchanged_build_plans_nothing(self):
        pages = indexnow.snapshot(self.out, self.config)
        locs = re.findall(r"<loc>([^<]+)</loc>", (self.out / "sitemap.xml").read_text(encoding="utf-8"))
        self.assertEqual(sorted(pages), sorted(locs))
        output = io.StringIO()
        with redirect_stdout(output), redirect_stderr(output), \
                patch.object(indexnow, "urlopen", side_effect=AssertionError("network")):
            code = indexnow.main(["--site-dir", str(self.out), "--baseline-site-dir", str(self.out), "--dry-run"])
        self.assertEqual(code, 0)
        planned = json.loads(output.getvalue().splitlines()[0])
        self.assertEqual((planned["added"], planned["changed"], planned["deleted"]), ([], [], []))


if __name__ == "__main__":
    unittest.main()
