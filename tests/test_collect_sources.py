"""Exercise ingestion boundaries and review queue behavior without the network."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import select
import signal
import subprocess
import sys
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

    def test_cli_refuses_repository_output(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            collect.main(["--out", str(collect.ROOT / "content")])

    def test_cli_reuses_existing_lock_file_after_normal_exit(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(collect, "collect", return_value={"errors": [], "pending_review": []}), \
                redirect_stdout(io.StringIO()):
            (Path(tmp) / ".collect.lock").touch()
            inode = (Path(tmp) / ".collect.lock").stat().st_ino
            self.assertEqual(collect.main(["--out", tmp]), 0)
            self.assertEqual(collect.main(["--out", tmp]), 0)
            self.assertEqual((Path(tmp) / ".collect.lock").stat().st_ino, inode)

    def test_cli_releases_lock_after_collection_error(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(collect, "collect", side_effect=[
                    ValueError("invalid state"), {"errors": [], "pending_review": []}]), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(collect.main(["--out", tmp]), 2)
            self.assertEqual(collect.main(["--out", tmp]), 0)

    def test_cli_rejects_concurrency_and_recovers_after_process_termination(self):
        # Exercise the actual CLI lock lifetime in a separate process, without
        # network access. Both graceful termination and forced death skip cleanup.
        holder_script = """
import signal
import sys
from tools import collect_sources
def hold(out, **kwargs):
    print("locked", flush=True)
    signal.pause()
collect_sources.collect = hold
sys.exit(collect_sources.main(sys.argv[1:]))
"""
        for termination in (signal.SIGTERM, signal.SIGKILL):
            with self.subTest(signal=termination), tempfile.TemporaryDirectory() as tmp:
                holder = subprocess.Popen(
                    [sys.executable, "-c", holder_script, "--out", tmp],
                    cwd=collect.ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    text=True,
                )
                try:
                    ready, _, _ = select.select([holder.stdout], [], [], 10)
                    self.assertTrue(ready, "collector did not acquire its lock in time")
                    self.assertEqual(holder.stdout.readline().strip(), "locked")
                    lock = Path(tmp) / ".collect.lock"
                    inode = lock.stat().st_ino
                    with patch.object(collect, "collect", return_value={
                            "errors": [], "pending_review": []}) as run, \
                            redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
                        self.assertEqual(collect.main(["--out", tmp]), 2)
                        self.assertIn("another collection holds", errors.getvalue())
                        run.assert_not_called()
                        holder.send_signal(termination)
                        self.assertEqual(holder.wait(timeout=10), -termination)
                        self.assertEqual(collect.main(["--out", tmp]), 0)
                        run.assert_called_once()
                    self.assertEqual(lock.stat().st_ino, inode)
                finally:
                    if holder.poll() is None:
                        holder.kill()
                    holder.communicate(timeout=10)

    def test_redirect_cannot_downgrade_https_or_change_origin(self):
        handler = collect.SameOriginRedirect()
        for target in ("http://github.com/a/b", "https://example.com/feed"):
            with self.subTest(target=target), self.assertRaises(ValueError):
                handler.redirect_request(None, None, 302, "Found", {}, target)


if __name__ == "__main__":
    unittest.main()
