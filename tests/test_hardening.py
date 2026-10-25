"""Regression tests for generator edge cases: Markdown, front matter, content
validation, feeds, escaping and accessibility markup.

Each test names the input that used to break and what the build now does.
"""

import contextlib
import hashlib
import io
import json
import re
import shutil
import signal
import sys
import tempfile
import unittest
import xml.dom.minidom
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build  # noqa: E402
from sitegen import art, content, md, render  # noqa: E402
from sitegen.render import Site  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
import check_a11y  # noqa: E402
import draft_content  # noqa: E402
import verify_manifest  # noqa: E402

EN = """---
title: {title}
dek: A dek.
kind: news
topics: [confidential-computing]
event_date: 2026-10-01
published: 2026-10-02
{extra}
sources:
  - First source | Publisher One | 2026-10-01 | https://example.org/1
  - Second source | 出版方 | 2026-10 | https://example.org/2
---
Body text.[^1] More.[^2]

## Main

## Overview

## Summary {{#overview-final}}
"""
ZH = """---
title: {title}
dek: 摘要。
{extra}
---
正文。[^1][^2]

## 概述
"""


class Project:
    """A throwaway project root: the real data files, plus articles and pages written by a test."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        src = ROOT / "content"
        (self.root / "content" / "articles").mkdir(parents=True)
        (self.root / "content" / "pages").mkdir()
        for name in ("site.json", "strings.json", "topics.json", "resources.json", "glossary.json"):
            shutil.copyfile(src / name, self.root / "content" / name)
        self.page("about", "en", "---\ntitle: About\ndek: d\n---\n## A {#a}\n")
        self.page("about", "zh", "---\ntitle: 关于\ndek: d\n---\n## 甲 {#a}\n")

    def article(self, slug, en=None, zh=None, en_extra="", zh_extra="", title="A Title"):
        folder = self.root / "content" / "articles" / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "en.md").write_text(en if en is not None else EN.format(title=title, extra=en_extra), encoding="utf-8")
        if zh is not False:
            (folder / "zh.md").write_text(zh if zh is not None else ZH.format(title="一个标题", extra=zh_extra), encoding="utf-8")
        return folder

    def page(self, name, lang, text):
        (self.root / "content" / "pages" / f"{name}.{lang}.md").write_text(text, encoding="utf-8")

    def data(self, name, mutate):
        path = self.root / "content" / f"{name}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        mutate(doc)
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    def load(self, **kw):
        return content.load(self.root, **kw)

    def close(self):
        self.tmp.cleanup()


def render(text, **kw):
    return md.render(text, md.Context(**kw))


class InlineMarkdownTests(unittest.TestCase):
    def test_link_label_with_code_span_renders(self):
        # used to raise IndexError: the label was rendered with a fresh stash
        html, _ = render("Run [`c2patool`](https://example.org/tool).")
        self.assertIn('<a href="https://example.org/tool" rel="noopener" class="ext"><code>c2patool</code></a>', html)

    def test_citation_inside_link_label_moves_after_the_link(self):
        html, ctx = render("See [the report [^1]](https://example.org).", source_count=1)
        self.assertIn('class="ext">the report</a><sup class="cite">[<a href="#source-1"', html)
        self.assertEqual(ctx.cited, ["1"])
        self.assertNotRegex(html, r"<a [^>]*>[^<]*<sup")

    def test_nul_character_does_not_hang(self):
        if hasattr(signal, "alarm"):
            signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError("render hung")))
            signal.alarm(5)
        try:
            html, _ = render("a\x00b `c\x00d`")
        finally:
            if hasattr(signal, "alarm"):
                signal.alarm(0)
        self.assertEqual(html, "<p>ab <code>cd</code></p>")

    def test_link_target_with_parentheses(self):
        html, _ = render("[Trust](https://en.wikipedia.org/wiki/Trust_(social_science)) here")
        self.assertIn('href="https://en.wikipedia.org/wiki/Trust_(social_science)"', html)
        self.assertIn("</a> here", html)

    def test_unsafe_link_schemes_render_as_text(self):
        for target in ("javascript:alert(1)", "JavaScript:alert(1)", "data:text/html,x", "vbscript:x"):
            html, _ = render(f"[click & go]({target})")
            self.assertEqual(html, "<p>click &amp; go</p>", target)
        html, _ = render("[mail](mailto:hello@verifiable.pro)")
        self.assertIn('href="mailto:hello@verifiable.pro"', html)

    def test_protocol_relative_link_is_not_resolved_as_a_site_path(self):
        html, _ = render("[cdn](//cdn.example.org/x/)", resolve=lambda t: "RESOLVED" + t)
        self.assertIn('href="//cdn.example.org/x/" rel="noopener" class="ext"', html)

    def test_link_titles_and_labels_are_escaped_once(self):
        html, _ = render('[a & *b*](/x/ "T & t")', resolve=lambda t: t)
        self.assertIn('<a href="/x/" title="T &amp; t">a &amp; <em>b</em></a>', html)


class BlockMarkdownTests(unittest.TestCase):
    def test_heading_keeps_a_trailing_hash_in_a_word(self):
        html, _ = render("## Learn C# and F#\n\n### Closed ###")
        self.assertIn(">Learn C# and F#</h2>", html)
        self.assertIn(">Closed</h3>", html)

    def test_body_h1_becomes_h2(self):
        html, ctx = render("# Title in the body\n\nText")
        self.assertIn('<h2 id="title-in-the-body">', html)
        self.assertEqual(ctx.headings[0][0], 2)

    def test_duplicate_explicit_ids_are_an_error(self):
        with self.assertRaises(ValueError):
            render("## A {#x}\n\n## B {#x}")

    def test_explicit_id_wins_over_an_earlier_automatic_one(self):
        html, _ = render("## Overview\n\n## Summary {#overview}")
        self.assertIn('<h2 id="overview-2">Overview</h2>', html)
        self.assertIn('<h2 id="overview">Summary</h2>', html)

    def test_template_ids_are_reserved(self):
        html, _ = render("## Main\n\n## Source 1", reserved={"main", "source-1"})
        self.assertIn('id="main-2"', html)
        self.assertIn('id="source-1-2"', html)
        with self.assertRaises(ValueError):
            render("## Top {#main}", reserved={"main"})

    def test_heading_ids_ignore_link_targets_and_citations(self):
        html, _ = render("## See [NIST AI 100-4](https://nist.gov/x)[^1]")
        self.assertIn('<h2 id="see-nist-ai-100-4">', html)

    def test_long_fence_holds_a_shorter_one(self):
        html, _ = render("````md\n```bash\necho hi\n```\n````\n\nAfter")
        self.assertIn('<code class="language-md">```bash\necho hi\n```</code>', html)
        self.assertIn("<p>After</p>", html)

    def test_tilde_fence_and_info_string(self):
        html, _ = render("~~~python title=x\nprint(1)\n~~~")
        self.assertIn('<code class="language-python">print(1)</code>', html)

    def test_callout_does_not_end_inside_a_code_block(self):
        html, _ = render(":::note\n```text\n:::\n```\nStill inside\n:::\n\nOutside")
        self.assertIn('<code class="language-text">:::</code></pre>\n<p>Still inside</p></div></aside>', html)
        self.assertTrue(html.endswith("<p>Outside</p>"))

    def test_fenced_explicit_ids_are_not_claimed(self):
        html, _ = render("## Real {#x}\n\n```md\n## Shown {#x}\n```")
        self.assertIn('<h2 id="x">Real</h2>', html)

    def test_table_cell_with_escaped_pipe(self):
        html, _ = render("| a | b |\n| --- | --- |\n| x \\| y | z |")
        self.assertIn("<td>x | y</td><td>z</td>", html)

    def test_thematic_breaks(self):
        for rule in ("* * *", "- - -", "___", "***"):
            html, _ = render(f"a\n\n{rule}\n\nb")
            self.assertIn("<hr>", html, rule)
            self.assertNotIn("<li>", html, rule)

    def test_only_a_list_starting_at_one_interrupts_a_paragraph(self):
        html, _ = render("The year was\n2026. A new rule came")
        self.assertEqual(html, "<p>The year was 2026. A new rule came</p>")
        html, _ = render("Steps:\n1. one\n2. two")
        self.assertIn("<ol><li>one</li><li>two</li></ol>", html)


class FrontMatterTests(unittest.TestCase):
    def parse(self, head, body="x"):
        return md.parse_front_matter(f"---\n{head}\n---\n{body}")

    def test_inline_comments_do_not_leak_into_values(self):
        # "draft: true  # keep out" used to read as the string "true  # keep out",
        # which is not a true value, so the draft was published
        meta, _ = self.parse("draft: true  # keep out\nfeatured: yes # x\ntopics: [a, b]   # first is primary")
        self.assertEqual((meta["draft"], meta["featured"], meta["topics"]), ("true", "yes", ["a", "b"]))

    def test_hash_inside_a_value_is_kept(self):
        meta, _ = self.parse("title: Ranked #1 in C# tests\nsources:\n  - T | P | 2026-10-14 | https://e.org/x#frag")
        self.assertEqual(meta["title"], "Ranked #1 in C# tests")
        self.assertEqual(meta["sources"], ["T | P | 2026-10-14 | https://e.org/x#frag"])

    def test_bracketed_words_in_a_title_are_not_a_list(self):
        meta, _ = self.parse("title: [Updated] Foo [beta]")
        self.assertEqual(meta["title"], "[Updated] Foo [beta]")

    def test_wrapped_values_continue_on_indented_lines(self):
        meta, _ = self.parse("dek: One line\n  continues here.\nsources:\n  - T | P | 2026-10-14 |\n    https://e.org/x\nkind: news")
        self.assertEqual(meta["dek"], "One line continues here.")
        self.assertEqual(meta["sources"], ["T | P | 2026-10-14 | https://e.org/x"])
        self.assertEqual(meta["kind"], "news")

    def test_folded_and_literal_blocks(self):
        meta, _ = self.parse("dek: >\n  第一行\n  第二行\nnote: |\n  a\n  b")
        self.assertEqual((meta["dek"], meta["note"]), ("第一行第二行", "a\nb"))

    def test_quoted_values(self):
        meta, _ = self.parse('title: "He said \\"hi\\" # kept"  # dropped\nalt: \'It\'\'s\'')
        self.assertEqual((meta["title"], meta["alt"]), ('He said "hi" # kept', "It's"))

    def test_unindented_stray_line_is_an_error(self):
        with self.assertRaises(ValueError):
            self.parse("dek: One line\nwhat happened.")

    def test_unclosed_front_matter_is_an_error(self):
        with self.assertRaises(ValueError):
            md.parse_front_matter("---\ntitle: x\n")

    def test_crlf_and_horizontal_rule_at_the_top(self):
        meta, body = md.parse_front_matter("---\r\ntitle: crlf\r\n---\r\nBody\r\n")
        self.assertEqual((meta, body), ({"title": "crlf"}, "Body\r\n"))
        self.assertEqual(md.parse_front_matter("----\ntext\n"), ({}, "----\ntext\n"))


class DraftContentTests(unittest.TestCase):
    """tools/draft_content.py used to write into content/ by default, which replaced the data
    files and deleted every article; it now needs --out and refuses content/ and its folders.
    The refusal is tested on out_folder() alone, so no test can reach a write into content/."""

    def test_out_is_required(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            draft_content.main([])
        self.assertEqual(raised.exception.code, 2)

    def test_content_and_folders_inside_it_are_refused(self):
        content = ROOT / "content"
        for path in (content, content / "articles", content / "articles" / "new", content / ".." / "content"):
            with self.subTest(path=str(path)), self.assertRaises(SystemExit) as raised:
                draft_content.out_folder(path)
            self.assertIn("refusing to write into", str(raised.exception.code))

    def test_a_symlink_to_content_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "content-link"
            link.symlink_to(ROOT / "content", target_is_directory=True)
            with self.assertRaises(SystemExit):
                draft_content.out_folder(link)
            with self.assertRaises(SystemExit):
                draft_content.out_folder(link / "articles")

    def test_other_folders_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(draft_content.out_folder(Path(tmp) / "draft"), (Path(tmp) / "draft").resolve())
        self.assertEqual(draft_content.out_folder(ROOT), ROOT.resolve())


if __name__ == "__main__":
    unittest.main()
