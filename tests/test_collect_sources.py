"""Exercise ingestion boundaries and review queue behavior without the network."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import collect_sources as collect


def feed(repo, version="v1", text="Release notes", updated="2026-10-10T17:47:00Z"):
    return (f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>{version}</title>'
            f'<updated>{updated}</updated><link rel="alternate" '
            f'href="https://github.com/{repo}/releases/tag/{version}"/>'
            f'<content type="html">{text}</content></entry></feed>').encode()


class SourceCollectionTests(unittest.TestCase):
    def test_existing_article_citations_can_be_indexed(self):
        urls = collect.published_urls()
        self.assertIn("https://docs.nvidia.com/confidential-computing/virtual-machines/threat-model", urls)
        self.assertIn("https://token.actions.githubusercontent.com", urls)

    def test_release_link_cannot_redirect_review_to_another_repo(self):
        with self.assertRaisesRegex(ValueError, "configured repository"):
            collect.parse_feed(feed("attacker/example"), "sigstore/model-transparency")

    def test_html_error_and_empty_feed_are_failures(self):
        for raw in (b"<html>Service unavailable</html>",
                    b'<feed xmlns="http://www.w3.org/2005/Atom"/>'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                collect.parse_feed(raw, "sigstore/model-transparency")

    def test_timestamp_requires_timezone(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            collect.parse_feed(feed("a/b", updated="2026-10-10T17:47:00"), "a/b")

    def test_pending_survives_rerun_and_exact_ack_allows_later_revision(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(collect, "SOURCES", (("example", "a/b"),)), \
                patch.object(collect, "published_urls", return_value={}):
            out = Path(tmp)
            first = collect.collect(out, lambda _: feed("a/b"))
            self.assertEqual(first["items"][0]["status"], "new")
            second = collect.collect(out, lambda _: feed("a/b"))
            self.assertEqual(second["items"][0]["status"], "unchanged")
            self.assertEqual(second["pending_review"], first["pending_review"])
            digest = first["pending_review"][0]["entry_sha256"]
            third = collect.collect(out, lambda _: feed("a/b"), acknowledge=[digest])
            self.assertEqual(third["pending_review"], [])
            fourth = collect.collect(out, lambda _: feed("a/b", text="Security correction"))
            self.assertEqual(fourth["pending_review"][0]["status"], "changed")
            with self.assertRaisesRegex(ValueError, "does not match"):
                collect.collect(out, lambda _: feed("a/b"), acknowledge=[digest])

    def test_published_first_seen_is_skipped_but_update_stays_pending(self):
        url = "https://github.com/a/b/releases/tag/v1"
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(collect, "SOURCES", (("example", "a/b"),)), \
                patch.object(collect, "published_urls", return_value={url: ["article:existing"]}):
            out = Path(tmp)
            first = collect.collect(out, lambda _: feed("a/b"))
            self.assertEqual(first["items"][0]["status"], "already_published")
            self.assertFalse(first["pending_review"])
            collect.collect(out, lambda _: feed("a/b", text="Correction"))
            again = collect.collect(out, lambda _: feed("a/b", text="Correction"))
            self.assertEqual(again["pending_review"][0]["status"], "changed")

    def test_source_failure_retains_queue_and_other_source_progress(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(collect, "SOURCES", (("first", "a/b"), ("second", "c/d"))), \
                patch.object(collect, "published_urls", return_value={}):
            def download(url):
                if "c/d" in url:
                    raise TimeoutError("test timeout")
                return feed("a/b")
            report = collect.collect(Path(tmp), download)
            self.assertEqual(len(report["errors"]), 1)
            self.assertEqual(len(report["pending_review"]), 1)
            state = json.loads((Path(tmp) / "state.json").read_text())
            self.assertEqual(len(state["entries"]), 1)

    def test_cli_refuses_repository_output_and_existing_lock(self):
        with self.assertRaises(SystemExit):
            collect.main(["--out", str(collect.ROOT / "content")])
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".collect.lock").touch()
            with self.assertRaises(SystemExit):
                collect.main(["--out", tmp])

    def test_redirect_cannot_downgrade_https_or_change_origin(self):
        handler = collect.SameOriginRedirect()
        for target in ("http://github.com/a/b", "https://example.com/feed"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(None, None, 302, "Found", {}, target)


if __name__ == "__main__":
    unittest.main()
