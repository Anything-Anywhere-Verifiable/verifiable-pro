"""What search engines, AI answer engines and agents read (sitegen/discover.py).

The production build that deploy.yml publishes is made once into a temporary
folder, and the tests read it as a crawler would: robots.txt, llms.txt and the
llms-full.txt files, the structured data and social tags in each head, the
social cards and icons, the language alternates, the sitemap, the JSON Feeds and
the Markdown alternates. Preview and artifact builds must still work.
"""

import datetime as dt
from collections import deque
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.robotparser
from urllib.parse import urljoin, urlsplit
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sitegen import content, discover  # noqa: E402

# Crawler tokens that robots.txt must name, each checked against its operator's documentation
CRAWLERS = ("Googlebot", "Bingbot", "Google-Extended", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot",
            "Claude-SearchBot", "Claude-User", "PerplexityBot", "Perplexity-User", "Applebot", "Applebot-Extended",
            "CCBot", "Amazonbot", "Meta-ExternalAgent", "DuckAssistBot")
LLMS_SECTIONS = ("Start here", "Topics", "Articles", "Data and verification", "中文", "Optional")
# Written by deploy.yml after the build, so only the live site has them
DEPLOY_FILES = ("/build.json", "/SHA256SUMS")
LIST_ENTRY_RE = re.compile(r"^- \[(?:[^\]\\]|\\.)+\]\(\S+\)(?:: \S.*)?$")
SITE_URL_RE = re.compile(r"https://verifiable\.pro(/[^\s)\]<>\"'`，。；：、）]*)(<?)")
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")
LD_TYPES_ARTICLE = ("NewsArticle", "Article")
# Pages that ask search engines not to index them, and that the sitemap, llms.txt, the
# llms-full.txt files and the feeds leave out: the 404 pages, which hosts serve at any
# missing address, and the search pages, which list no results without JavaScript
UNLISTED = ("404.html", "zh/404.html", "search/index.html", "zh/search/index.html")
# The longest home page title, in characters, that search results show whole
HOME_TITLE_MAX = {"en": 60, "zh": 30}


def build(out, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, str(ROOT / "build.py"), "--out", str(out), *args], cwd=ROOT,
                          capture_output=True, text=True, env=env)


def png_size(path):
    return discover.png_size(path)


class Head(HTMLParser):
    """The <link> and <meta> elements of a page, the JSON-LD blocks it carries and its
    title (the head's <title>, not the titles of the inline SVGs in the body)."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links, self.metas, self.ld, self._ld = [], [], [], None
        self.titles, self._title, self._in_head = [], None, False
        self.feed(text)
        self.close()

    @property
    def title(self):
        return self.titles[0] if len(self.titles) == 1 else None

    def handle_starttag(self, tag, attrs):
        a = {k: v or "" for k, v in attrs}
        if tag == "head":
            self._in_head = True
        elif tag == "title" and self._in_head:
            self._title = []
        elif tag == "link":
            self.links.append(a)
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._ld = []

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
        elif tag == "title" and self._title is not None:
            self.titles.append("".join(self._title))
            self._title = None
        elif tag == "script" and self._ld is not None:
            self.ld.append("".join(self._ld))
            self._ld = None

    def handle_data(self, data):
        if self._ld is not None:
            self._ld.append(data)
        elif self._title is not None:
            self._title.append(data)

    def meta(self, key):
        return [m.get("content") for m in self.metas if m.get("property") == key or m.get("name") == key]

    def link(self, rel, **attrs):
        return [ln for ln in self.links if rel in ln.get("rel", "").split()
                and all(ln.get(k.replace("_", "-")) == v for k, v in attrs.items())]

    def nodes(self):
        out = []
        for blob in self.ld:
            data = json.loads(blob)
            out += data if isinstance(data, list) else [data]
        return out


class DiscoverabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.out = Path(cls.tmp.name) / "public"
        result = build(cls.out)
        if result.returncode:
            raise AssertionError(result.stderr)
        cls.model = content.load(ROOT)
        cls.site = cls.model["site"]
        cls.base = cls.site["base_url"].rstrip("/")
        cls.pages = sorted(p.relative_to(cls.out).as_posix() for p in cls.out.rglob("*.html"))
        cls.heads = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # ----- helpers -------------------------------------------------------------------
    def read(self, rel):
        return (self.out / rel).read_text(encoding="utf-8")

    def head(self, rel):
        if rel not in self.heads:
            self.heads[rel] = Head(self.read(rel))
        return self.heads[rel]

    def target(self, url):
        """The file in the build that a site URL or root-relative path names."""
        path = url[len(self.base):] if url.startswith(self.base) else url
        path = path.split("#", 1)[0].split("?", 1)[0]
        return self.out / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))

    def url_of(self, rel):
        """The canonical URL of a page file: "zh/latest/index.html" is BASE/zh/latest/."""
        return self.base + "/" + (rel[: -len("index.html")] if rel.endswith("index.html") else rel)

    def lang_of(self, rel):
        return "zh" if rel.startswith("zh/") else "en"

    def articles(self, lang):
        return self.model["articles"][lang]

    def byline(self, a, lang):
        """The byline that the feeds and the llms-full.txt headers give an article, from the
        content: an automated byline's name marked as automated ("verifiable.pro Wire
        (automated)"), with the address of About's #ai, or the name of the person who wrote it."""
        if a.agent:
            name = self.model["site"]["agents"][a.agent]["name"]
            name = name[lang] if isinstance(name, dict) else name
            return {"name": self.model["strings"][lang]["byline_agent_named"].format(name=name),
                    "url": f"{self.base}{'/zh' if lang == 'zh' else ''}/about/#ai"}
        return {"name": " ".join(a.author.split())}

    def missing_site_urls(self, text):
        """Site URLs in TEXT that name no file in the build. Templates such as
        https://verifiable.pro/articles/<slug>/en.md and the deploy's own files are skipped."""
        found = []
        for path, template in SITE_URL_RE.findall(text):
            if template or path in DEPLOY_FILES:
                continue
            if not self.target(path).exists():
                found.append(path)
        return found

    def indexable(self):
        return [rel for rel in self.pages if rel not in UNLISTED]

    # ----- robots.txt ------------------------------------------------------------------
    def test_robots_txt_welcomes_named_crawlers_and_points_to_llms_txt(self):
        text = self.read("robots.txt")
        lines = text.splitlines()
        for line in ("User-agent: *", "Allow: /", f"Sitemap: {self.base}/sitemap.xml"):
            self.assertIn(line, lines)
        self.assertTrue(any(ln.startswith("#") and f"{self.base}/llms.txt" in ln for ln in lines))
        named = {ln.split(":", 1)[1].strip() for ln in lines if ln.startswith("User-agent:")}
        self.assertLessEqual(set(CRAWLERS), named)
        self.assertEqual(named - {"*"}, {agent for group in discover.ROBOTS_GROUPS for agent in group[1]})
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(lines)
        # every crawler may fetch the pages, unless its group carries rules of its own
        self.assertTrue(parser.can_fetch("SomeOtherBot", f"{self.base}/articles/x/"))
        for group in discover.ROBOTS_GROUPS:
            open_to_all = "Allow: /" in (group[2] if len(group) > 2 else discover.ROBOTS_RULES)
            for agent in group[1]:
                self.assertEqual(parser.can_fetch(agent, f"{self.base}/articles/x/"), open_to_all, agent)
        searchers = {agent for group in discover.ROBOTS_GROUPS[:2] for agent in group[1]}
        self.assertTrue(all(parser.can_fetch(agent, f"{self.base}/") for agent in searchers))
        self.assertEqual(parser.site_maps(), [f"{self.base}/sitemap.xml"])

    # ----- llms.txt and llms-full.txt -------------------------------------------------
    def test_llms_txt_follows_the_llmstxt_format(self):
        text = self.read("llms.txt")
        lines = text.split("\n")
        self.assertEqual(lines[0], f"# {self.site['domain']}")
        self.assertTrue(lines[2].startswith("> ") and len(lines[2]) > 40, lines[2])
        self.assertEqual([ln for ln in lines if ln.startswith("# ")], [lines[0]])
        sections = [ln[3:] for ln in lines if ln.startswith("## ")]
        self.assertEqual(sections, list(LLMS_SECTIONS))
        first = lines.index("## " + LLMS_SECTIONS[0])
        intro = [ln for ln in lines[3:first] if ln]
        self.assertTrue(intro and not any(ln.startswith(("#", "- ")) for ln in intro), "paragraphs before the lists")
        self.assertIn("manifest", " ".join(intro))
        # the bylines: a person's name, or one of the automated bylines by name, never "AI agent"
        for entry in self.model["site"]["agents"].values():
            name = entry["name"]["en"] if isinstance(entry["name"], dict) else entry["name"]
            self.assertIn(name, " ".join(intro))
        self.assertIn("marked as automated", " ".join(intro))
        self.assertNotIn("ai agent", " ".join(intro).casefold())
        entries = {}
        for ln in lines[first:]:
            if ln.startswith("## "):
                current = ln[3:]
                entries[current] = []
            elif ln:
                self.assertRegex(ln, LIST_ENTRY_RE)
                entries[current].append(ln)
        # every published English article, newest first, linked to its Markdown source
        sources = [re.search(r"\]\((\S+)\)", ln).group(1) for ln in entries["Articles"]]
        self.assertEqual(sources, [f"{self.base}/articles/{a.slug}/en.md" for a in self.articles("en")])
        start = " ".join(entries["Start here"])
        for name in ("about", "vision"):
            self.assertIn(f"{self.base}/pages/{name}.en.md", start)
        for a in self.articles("en"):
            if a.kind in ("explainer", "guide"):
                self.assertIn(f"{self.base}/articles/{a.slug}/en.md", start)
        topics = " ".join(entries["Topics"])
        for t in self.model["topics"]["topics"]:
            self.assertIn(f"{self.base}/topics/{t['id']}/", topics)
        data = " ".join(entries["Data and verification"])
        for path in ("/manifest.json", "/feed.xml", "/feed.json", "/search-index.json", "/data/glossary.json",
                     "/data/resources.json", "/llms-full.txt"):
            self.assertIn(self.base + path, data)
        self.assertIn(f"{self.base}/zh/llms-full.txt", " ".join(entries["中文"]))
        self.assertEqual(self.missing_site_urls(text), [])

    def test_llms_full_txt_holds_every_published_article_and_page(self):
        for lang, rel in (("en", "llms-full.txt"), ("zh", "zh/llms-full.txt")):
            text = self.read(rel)
            prefix = "/zh" if lang == "zh" else ""
            urls = re.findall(r"^- URL: (\S+)$", text, re.M)
            expected = [f"{self.base}{prefix}/articles/{a.slug}/" for a in self.articles(lang)]
            expected += [f"{self.base}{prefix}/{name}/" for name in ("vision", "about")
                         if name in self.model["pages"][lang]]
            expected += sorted(f"{self.base}{prefix}/{name}/" for name in self.model["pages"][lang]
                               if name not in ("vision", "about"))
            self.assertEqual(urls, expected, rel)  # no draft and nothing unpublished
            for a in self.articles(lang):
                block = text.split(f"- URL: {self.base}{prefix}/articles/{a.slug}/\n", 1)[1].split("\n---\n", 1)[0]
                self.assertIn(f"\n# {' '.join(a.title.split())}\n\n- URL: {self.base}{prefix}/articles/{a.slug}/\n", text, a.slug)
                for key, value in (("Kind", a.kind), ("Published", a.published.isoformat()),
                                   ("SHA-256", a.sha256), ("Byline", self.byline(a, lang)["name"])):
                    self.assertIn(f"- {key}: {value}\n", block, (rel, a.slug, key))
                self.assertEqual(f"- Submitted by: {a.submitted_by}\n" in block, bool(a.submitted_by), (rel, a.slug))
                if a.topics:
                    self.assertIn("- Topics: ", block, (rel, a.slug))
                self.assertEqual(len(re.findall(r"^  \d+\. ", block, re.M)), len(a.sources), (rel, a.slug))
                # the body follows the header: its first paragraph, with site links as full URLs
                first = next(p for p in a.body.strip().split("\n\n") if p.strip() and "](/" not in p)
                self.assertIn(first.strip(), block, (rel, a.slug))
            self.assertNotIn('data-include="', text, rel)
            self.assertNotRegex(text, r"\]\(/(?!/)", rel)
            self.assertEqual(self.missing_site_urls(text), [], rel)

    # ----- Markdown alternates ----------------------------------------------------------
    def test_markdown_alternates_point_to_published_sources(self):
        sources = {e["page"]: e["source"] for e in json.loads(self.read("manifest.json"))["entries"] if e["page"]}
        for rel in self.pages:
            alternates = self.head(rel).link("alternate", type="text/markdown")
            page = "/" + (rel[: -len("index.html")] if rel.endswith("index.html") else rel)
            if page in sources:
                self.assertEqual([ln["href"] for ln in alternates], [sources[page]], rel)
                self.assertTrue(self.target(sources[page]).is_file(), rel)
                self.assertNotIn("hreflang", alternates[0], rel)
            else:
                self.assertEqual(alternates, [], rel)
        self.assertTrue(any(p.startswith("/articles/") for p in sources))

    # ----- structured data --------------------------------------------------------------
    def assert_logo(self, logo, where):
        self.assertEqual(logo["@type"], "ImageObject", where)
        path = self.target(logo["url"])
        self.assertTrue(path.is_file() and logo["url"].endswith(".png"), where)
        self.assertEqual(png_size(path), (logo["width"], logo["height"]), where)
        self.assertGreaterEqual(min(logo["width"], logo["height"]), 112, where)

    def test_structured_data_parses_and_names_the_required_properties(self):
        repo, email = self.site.get("repo_url"), self.site.get("contact_email")
        for rel in self.pages:
            nodes = self.head(rel).nodes()  # every block parses
            types = [n["@type"] for n in nodes]
            lang = self.lang_of(rel)
            url = self.url_of(rel)
            by_type = {n["@type"]: n for n in nodes}
            self.assertTrue(all(n.get("@context") == "https://schema.org" for n in nodes), rel)
            if rel in UNLISTED:  # pages that search engines are asked not to index describe nothing
                self.assertEqual(nodes, [], rel)
                continue
            if rel in ("index.html", "zh/index.html"):
                self.assertNotIn("BreadcrumbList", types, rel)  # a trail of one item is no trail
                site, org = by_type["WebSite"], by_type["Organization"]
                # the site's name is its domain, while the page's title also says what it covers
                self.assertEqual((site["name"], site["url"]), (self.site["domain"], self.base + "/"), rel)
                self.assertEqual(org["name"], self.site["domain"], rel)
                self.assertTrue(site["alternateName"], rel)
                self.assertEqual(site["inLanguage"], ["en", "zh-CN"], rel)
                self.assertEqual(site["publisher"], {"@id": org["@id"]}, rel)
                self.assertEqual((org["url"], org["sameAs"], org["email"]), (self.base + "/", [repo], email), rel)
                self.assert_logo(org["logo"], rel)
                continue
            crumbs = by_type["BreadcrumbList"]["itemListElement"]
            self.assertGreaterEqual(len(crumbs), 2, rel)
            self.assertEqual([c["position"] for c in crumbs], list(range(1, len(crumbs) + 1)), rel)
            self.assertEqual(crumbs[0]["item"], self.base + ("/zh/" if lang == "zh" else "/"), rel)
            for crumb in crumbs[:-1]:
                self.assertTrue(self.target(crumb["item"]).is_file(), (rel, crumb))
            self.assertNotIn("item", crumbs[-1], rel)
            kind = next((t for t in types if t in LD_TYPES_ARTICLE), None)
            if kind:
                self.check_article(rel, by_type[kind], url, lang)
        for lang in content.LANGS:
            prefix = "zh/" if lang == "zh" else ""
            for rel in [f"{prefix}{name}/index.html" for name in ("latest", "learn", "topics", "resources")] + [
                    f"{prefix}topics/{t['id']}/index.html" for t in self.model["topics"]["topics"]]:
                page = {n["@type"]: n for n in self.head(rel).nodes()}["CollectionPage"]
                items = page["mainEntity"]["itemListElement"]
                self.assertEqual(page["mainEntity"]["@type"], "ItemList", rel)
                self.assertTrue(items, rel)
                self.assertEqual(page["mainEntity"]["numberOfItems"], len(items), rel)
                self.assertEqual([i["position"] for i in items], list(range(1, len(items) + 1)), rel)
                self.assertTrue(all(i["url"].startswith("http") and i["name"] for i in items), rel)
                self.assertEqual(len({i["url"] for i in items}), len(items), rel)
                self.assertEqual(page["url"], self.url_of(rel), rel)
            latest = {n["@type"]: n for n in self.head(f"{prefix}latest/index.html").nodes()}["CollectionPage"]
            self.assertEqual([i["url"] for i in latest["mainEntity"]["itemListElement"]],
                             [f"{self.base}/{prefix}articles/{a.slug}/" for a in self.articles(lang)])
            self.check_learn_and_stack_lists(lang, prefix)
            terms = {n["@type"]: n for n in self.head(f"{prefix}glossary/index.html").nodes()}["DefinedTermSet"]
            self.assertEqual(len(terms["hasDefinedTerm"]), len(self.model["glossary"]["terms"]))
            for term in terms["hasDefinedTerm"]:
                self.assertEqual(term["@type"], "DefinedTerm")
                self.assertTrue(term["name"] and term["description"] and term["alternateName"], term)
                self.assertTrue(term["url"].startswith(f"{self.base}/{prefix}glossary/#"), term)
            about = {n["@type"]: n for n in self.head(f"{prefix}about/index.html").nodes()}
            self.assertEqual(about["AboutPage"]["about"], {"@id": about["Organization"]["@id"]})
            self.assert_logo(about["Organization"]["logo"], f"{prefix}about")

    def check_learn_and_stack_lists(self, lang, prefix):
        """Learn lists the introductory routes, then the TEE path and remaining guides; the Stack page lists the topics of its index. Each item is a link on the page."""
        learn = {n["@type"]: n for n in self.head(f"{prefix}learn/index.html").nodes()}["CollectionPage"]
        items = learn["mainEntity"]["itemListElement"]
        urls = [i["url"] for i in items]
        mine, english = ({a.slug: a for a in self.articles(code)} for code in (lang, "en"))
        starts = ["what-makes-an-ai-system-verifiable", "proofs-enclaves-and-re-execution-compared",
                  "how-to-read-a-remote-attestation-report", "private-ai-compute-published-designs"]
        steps = list(dict.fromkeys(starts + [step["article"] for step in self.model["tee"]["path"] if "article" in step]))
        # a step without an edition in the page language links the English article, as the page does
        path = [f"{self.base}/{prefix if slug in mine else ''}articles/{slug}/" for slug in steps
                if slug in mine or slug in english]
        self.assertTrue(path, lang)
        self.assertEqual(urls[:len(path)], path, lang)
        rest = [a for a in self.articles(lang) if a.kind == "guide" and a.slug not in steps]
        rest += [a for a in self.articles(lang) if a.kind == "explainer" and a.slug not in steps]
        self.assertEqual(urls[len(path):], [f"{self.base}/{prefix}articles/{a.slug}/" for a in rest], lang)
        titles = {f"{self.base}/{prefix if a.lang == lang else ''}articles/{a.slug}/": a.title
                  for a in list(english.values()) + list(mine.values())}
        self.assertEqual([i["name"] for i in items], [titles[u] for u in urls], lang)
        stack = {n["@type"]: n for n in self.head(f"{prefix}topics/index.html").nodes()}["CollectionPage"]
        self.assertEqual([(i["url"], i["name"]) for i in stack["mainEntity"]["itemListElement"]],
                         [(f"{self.base}/{prefix}topics/{t['id']}/", t["name"][lang]) for t in self.model["topics"]["topics"]])
        for rel, page in ((f"{prefix}learn/index.html", learn), (f"{prefix}topics/index.html", stack)):
            main = self.read(rel).split('<main id="main">', 1)[1].split("</main>", 1)[0]
            hrefs = set(re.findall(r'href="([^"]+)"', main))
            for item in page["mainEntity"]["itemListElement"]:
                self.assertIn(item["url"][len(self.base):], hrefs, (rel, item["url"]))

    def check_article(self, rel, art, url, lang):
        slug = rel.split("/articles/", 1)[-1].split("/", 1)[0] if "/articles/" in rel else rel.split("/")[1]
        a = next(x for x in self.articles(lang) if x.slug == slug)
        self.assertEqual(art["@type"], "NewsArticle" if a.kind == "news" else "Article", rel)
        self.assertEqual((art["headline"], art["description"]), (a.title, a.dek), rel)
        self.assertEqual(art["datePublished"], a.published.isoformat(), rel)
        self.assertEqual(art["dateModified"], (a.updated or a.published).isoformat(), rel)
        self.assertEqual(art["inLanguage"], discover.HREFLANG[lang], rel)
        self.assertIs(art["isAccessibleForFree"], True, rel)
        self.assertEqual(art["mainEntityOfPage"], url, rel)
        self.assertEqual(art["@id"], url + "#article", rel)
        self.assertTrue(art["articleSection"], rel)
        self.assertEqual(len(art["keywords"]), len(a.topics), rel)
        image = art["image"]
        social = a.lead_image.variants.get("social") if a.lead_image else None
        if social is None:
            self.assertEqual(image["url"], f"{self.base}/assets/og/{discover.card_file(a.primary_topic, lang)}", rel)
            self.assertEqual(png_size(self.target(image["url"])), (image["width"], image["height"]), rel)
        else:  # a photo's copy for link previews, with the photo's credit and license
            self.assertEqual(image["url"], self.base + social.src, rel)
            kind = content.PHOTO_TYPES[social.file.rsplit(".", 1)[1]]
            self.assertEqual(content._raster_size(self.target(image["url"]).read_bytes(), kind),
                             (image["width"], image["height"]), rel)
            credit = a.lead_image.credit
            self.assertEqual((image["creditText"], image["license"]),
                             (" ".join((credit.get(lang) if isinstance(credit, dict) else credit).split()),
                              a.lead_image.license_url), rel)
        self.assertEqual(art["publisher"]["name"], self.site["domain"], rel)
        self.assert_logo(art["publisher"]["logo"], rel)
        # a person who wrote the article is its author; for an automated article, the publication
        # is (the visible byline names the automated byline), so no person is made up
        if a.author and not a.agent:
            self.assertEqual(art["author"], {"@type": "Person", "name": " ".join(a.author.split())}, rel)
        else:
            self.assertEqual(art["author"], {"@type": "Organization", "@id": self.base + "/#organization",
                                             "name": self.site["domain"], "url": self.base + "/"}, rel)
        if a.submitted_by:
            self.assertEqual(art["contributor"], {"@type": "Person", "name": " ".join(a.submitted_by.split())}, rel)
        else:
            self.assertNotIn("contributor", art, rel)
        citations = art.get("citation", [])
        self.assertEqual([c["url"] for c in citations], [s["url"] for s in a.sources], rel)
        for c, s in zip(citations, a.sources):
            self.assertEqual((c["@type"], c["name"]), ("CreativeWork", s["title"]), rel)
            # Mixed authors/venue labels stay in sources, not invented as entities.
            self.assertNotIn("publisher", c, rel)
            if re.match(r"^\d{4}(-\d{2}){0,2}$", s["date"]):
                self.assertEqual(c["datePublished"], s["date"], rel)
            else:
                self.assertNotIn("datePublished", c, rel)
        other = "en" if lang == "zh" else "zh"
        has_other = any(x.slug == slug for x in self.articles(other))
        key = "translationOfWork" if lang == "zh" else "workTranslation"
        if has_other:
            other_url = f"{self.base}{'/zh' if other == 'zh' else ''}/articles/{slug}/#article"
            self.assertEqual(art[key], {"@id": other_url}, rel)
        else:
            self.assertNotIn(key, art, rel)

    # ----- social cards and icons --------------------------------------------------------
    def test_social_cards_and_icons_exist_with_the_stated_size(self):
        topics = {t["id"] for t in self.model["topics"]["topics"]}
        for rel in self.pages:
            head, lang = self.head(rel), self.lang_of(rel)
            image = head.meta("og:image")
            self.assertEqual(len(image), 1, rel)
            path = self.target(image[0])
            # an article with a photo previews with the photo's social copy, at the cards' size
            shown = (next((x for x in self.articles(lang) if x.slug == rel.split("/")[-2]), None)
                     if "/articles/" in "/" + rel else None)
            social = shown.lead_image.variants.get("social") if shown is not None and shown.lead_image else None
            if social is None:
                self.assertTrue(image[0].startswith(self.base + "/assets/og/") and path.is_file(), rel)
                size = png_size(path)
            else:
                self.assertEqual(image[0], self.base + social.src, rel)
                size = content._raster_size(path.read_bytes(), content.PHOTO_TYPES[social.file.rsplit(".", 1)[1]])
            self.assertEqual(size, discover.CARD_SIZE, rel)
            self.assertEqual((head.meta("og:image:width"), head.meta("og:image:height")),
                             ([str(size[0])], [str(size[1])]), rel)
            self.assertTrue(head.meta("og:image:alt")[0].strip(), rel)
            self.assertEqual(head.meta("twitter:card"), ["summary_large_image"], rel)
            self.assertEqual(head.meta("twitter:image"), image, rel)
            self.assertEqual(head.meta("twitter:image:alt"), head.meta("og:image:alt"), rel)
            self.assertEqual(head.meta("og:locale"), [discover.OG_LOCALE[lang]], rel)
            paired = bool(head.link("alternate", hreflang="x-default"))
            other = discover.OG_LOCALE["zh" if lang == "en" else "en"]
            self.assertEqual(head.meta("og:locale:alternate"), [other] if paired else [], rel)
            parts = rel.split("/")
            topic = parts[-2] if len(parts) >= 3 and parts[-3] == "topics" and parts[-2] in topics else None
            if "/articles/" in "/" + rel:
                slug = parts[-2]
                a = next(x for x in self.articles(lang) if x.slug == slug)
                topic = a.primary_topic
                self.assertEqual(head.meta("article:published_time"), [a.published.isoformat()], rel)
                self.assertEqual(head.meta("article:modified_time"), [(a.updated or a.published).isoformat()], rel)
                self.assertEqual(len(head.meta("article:section")), 1, rel)
                self.assertEqual(len(head.meta("article:tag")), len(a.topics), rel)
            else:
                self.assertEqual(head.meta("article:published_time"), [], rel)
            if social is None:
                self.assertEqual(image[0].rsplit("/", 1)[1], discover.card_file(topic, lang), rel)
            # the touch icon and the web app manifest
            touch = head.link("apple-touch-icon")
            self.assertEqual(len(touch), 1, rel)
            self.assertEqual(png_size(self.target(touch[0]["href"])), (180, 180), rel)
            manifest = head.link("manifest")
            self.assertEqual([m["href"] for m in manifest], [("/zh" if lang == "zh" else "") + "/site.webmanifest"], rel)
        for card in (ROOT / discover.CARD_DIR).glob("*.png"):
            self.assertLessEqual(card.stat().st_size, 120 * 1024, card.name)  # tools/og_images.py's MAX_BYTES
        for lang in content.LANGS:
            rel = ("zh/" if lang == "zh" else "") + "site.webmanifest"
            doc = json.loads(self.read(rel))
            for key in ("name", "short_name", "icons", "theme_color", "background_color", "start_url"):
                self.assertTrue(doc.get(key), (rel, key))
            sizes = set()
            for icon in doc["icons"]:
                path = (self.out / rel).parent / icon["src"]
                w, h = (int(v) for v in icon["sizes"].split("x"))
                self.assertEqual((png_size(path), icon["type"]), ((w, h), "image/png"), (rel, icon))
                sizes.add(w)
            self.assertLessEqual({192, 512}, sizes, rel)

    # ----- language alternates and the sitemap --------------------------------------------
    def hreflangs(self, rel):
        return {(ln["hreflang"], ln["href"]) for ln in self.head(rel).link("alternate") if ln.get("hreflang")}

    def test_hreflang_pairs_are_reciprocal_with_an_english_x_default(self):
        paired = 0
        for rel in self.indexable():
            links = self.hreflangs(rel)
            if not links:
                continue
            paired += 1
            url = self.url_of(rel)
            codes = dict(links)
            self.assertEqual(set(codes), {"en", "zh-CN", "x-default"}, rel)
            self.assertEqual(codes[discover.HREFLANG[self.lang_of(rel)]], url, rel)
            self.assertEqual(codes["x-default"], codes["en"], rel)
            for code in ("en", "zh-CN"):
                other = codes[code]
                other_rel = self.target(other).relative_to(self.out).as_posix()
                self.assertEqual(self.hreflangs(other_rel), links, (rel, other_rel))
        self.assertGreater(paired, 100)

    def test_sitemap_lists_built_pages_with_alternates_and_last_changes(self):
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        root = ET.parse(self.out / "sitemap.xml").getroot()
        revised = {}
        for lang in content.LANGS:
            prefix = "/zh" if lang == "zh" else ""
            for a in self.articles(lang):
                revised[f"{self.base}{prefix}/articles/{a.slug}/"] = (a.updated or a.published).isoformat()
            for page in self.model["pages"][lang].values():
                if page.updated or page.published:
                    revised[f"{self.base}{prefix}/{page.name}/"] = (page.updated or page.published).isoformat()
        locs = []
        for url in root.findall("s:url", ns):
            loc = url.find("s:loc", ns).text
            locs.append(loc)
            self.assertTrue(self.target(loc).is_file(), loc)
            lastmod = url.find("s:lastmod", ns)
            self.assertEqual(lastmod.text if lastmod is not None else None, revised.get(loc), loc)
            if lastmod is not None:
                dt.date.fromisoformat(lastmod.text)
            alts = {link.get("hreflang"): link.get("href") for link in url.findall("x:link", ns)}
            for href in alts.values():
                self.assertTrue(self.target(href).is_file(), href)
            # the language versions the page's head names, or none for a page in one language
            self.assertEqual(alts, dict(self.hreflangs(self.target(loc).relative_to(self.out).as_posix())), loc)
            if alts:
                self.assertEqual(alts["x-default"], alts["en"], loc)
                self.assertIn(loc, alts.values())
        expected = {self.url_of(rel) for rel in self.indexable()}
        self.assertEqual(set(locs), expected)
        self.assertEqual(len(locs), len(set(locs)))

    def test_sitemap_names_no_alternates_for_a_page_in_one_language(self):
        import build  # the repository root is on sys.path
        base = "https://example.org"
        pages = dict.fromkeys(("/articles/both/", "/zh/articles/both/", "/articles/english-only/", "/404.html"), "")
        # a page whose head asks search engines not to index it stays out, as the search pages do
        pages["/search/"] = f"<head>{build.render.ROBOTS_NOINDEX}</head>"
        root = ET.fromstring(build.sitemap(pages, base, {"/articles/english-only/": dt.date(2026, 10, 20)}))
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "x": "http://www.w3.org/1999/xhtml"}
        found = {url.find("s:loc", ns).text: url for url in root.findall("s:url", ns)}
        self.assertEqual(set(found), {base + p for p in pages if not p.endswith(".html") and p != "/search/"})
        alone = found[base + "/articles/english-only/"]
        self.assertEqual((alone.findall("x:link", ns), alone.find("s:lastmod", ns).text), ([], "2026-10-20"))
        for loc in (base + "/articles/both/", base + "/zh/articles/both/"):
            alts = {link.get("hreflang"): link.get("href") for link in found[loc].findall("x:link", ns)}
            self.assertEqual(alts, {"en": base + "/articles/both/", "zh-CN": base + "/zh/articles/both/",
                                    "x-default": base + "/articles/both/"}, loc)

    # ----- titles and what search engines may index ---------------------------------------
    def test_home_titles_name_the_site_and_what_it_covers(self):
        """A home page's title, in search results and link previews, starts with the site's name
        and says what the site covers, short enough to show whole; the structured data still name
        the site by its domain."""
        domain = self.site["domain"]
        for lang, rel in (("en", "index.html"), ("zh", "zh/index.html")):
            head, title = self.head(rel), self.model["strings"][lang]["home_title"]
            self.assertEqual(head.title, title, rel)
            self.assertEqual(head.meta("og:title"), [title], rel)
            self.assertEqual(head.meta("og:site_name"), [domain], rel)
            self.assertTrue(title.startswith(domain) and len(title) > len(domain) + 8, title)
            self.assertLessEqual(len(title), HOME_TITLE_MAX[lang], title)
            site = {n["@type"]: n for n in head.nodes()}["WebSite"]
            self.assertEqual(site["name"], domain, rel)
        # every other page keeps its own title (og:title), followed by the site's name unless the
        # title names the site already, as About does: the name appears once
        for rel in self.pages:
            if rel in ("index.html", "zh/index.html"):
                continue
            head = self.head(rel)
            own = head.meta("og:title")[0]
            named = domain.lower() in own.lower()
            self.assertEqual(head.title, own if named else f"{own} | {domain}", rel)
            self.assertEqual(head.title.lower().count(domain.lower()), 1, rel)
        for lang in content.LANGS:
            prefix = "zh/" if lang == "zh" else ""
            for name in ("about", "vision"):
                page = self.model["pages"][lang][name]
                self.assertEqual(self.head(f"{prefix}{name}/index.html").meta("og:title"), [page.title], (lang, name))
        self.assertEqual(self.head("latest/index.html").title, f"{self.model['strings']['en']['latest_meta_title']} | {domain}")

    def test_section_search_metadata_names_the_subject_without_replacing_visible_headings(self):
        sections = (("latest", "latest_title"), ("learn", "learn_title"),
                    ("resources", "resources_page_title"), ("glossary", "glossary_title"))
        for lang in content.LANGS:
            prefix = "zh/" if lang == "zh" else ""
            strings = self.model["strings"][lang]
            for path, visible_key in sections:
                rel = f"{prefix}{path}/index.html"
                head = self.head(rel)
                self.assertIn("AI", head.title, rel)
                self.assertLessEqual(len(head.title), 70 if lang == "en" else 45, rel)
                # Short navigation/heading labels stay as the visible page labels.
                headings = re.findall(r'<h1\b[^>]*>(.*?)</h1>', self.read(rel), re.S)
                self.assertEqual(headings, [strings[visible_key]], rel)
            for path in ("latest", "learn", "resources", "topics", "topics/confidential-computing"):
                rel = f"{prefix}{path}/index.html"
                description = self.head(rel).meta("description")[0]
                self.assertLessEqual(len(description), 160 if lang == "en" else 85, rel)
                self.assertEqual(self.head(rel).meta("og:description"), [description], rel)

    def test_indexable_pages_have_unique_titles_and_descriptions(self):
        titles, descriptions = {}, {}
        for rel in self.pages:
            if rel in UNLISTED:
                continue
            head = self.head(rel)
            self.assertTrue(head.title and head.meta("description")[0].strip(), rel)
            self.assertNotIn(head.title, titles, (rel, titles.get(head.title)))
            self.assertNotIn(head.meta("description")[0], descriptions,
                             (rel, descriptions.get(head.meta("description")[0])))
            titles[head.title] = rel
            descriptions[head.meta("description")[0]] = rel

    def test_every_indexable_page_is_reachable_by_html_links_from_its_home(self):
        class Links(HTMLParser):
            def __init__(self, text):
                super().__init__()
                self.hrefs = []
                self.feed(text)

            def handle_starttag(self, tag, attrs):
                href = dict(attrs).get("href")
                if tag == "a" and href:
                    self.hrefs.append(href)

        links = {self.url_of(rel): Links(self.read(rel)).hrefs for rel in self.pages}
        host = urlsplit(self.base).netloc
        for lang in content.LANGS:
            home = self.base + ("/zh/" if lang == "zh" else "/")
            distances, queue = {home: 0}, deque([home])
            while queue:
                url = queue.popleft()
                for href in links[url]:
                    target = urlsplit(urljoin(url, href))
                    if target.netloc != host:
                        continue
                    canonical = self.base + target.path
                    if canonical in links and canonical not in distances:
                        distances[canonical] = distances[url] + 1
                        queue.append(canonical)
            for rel in self.pages:
                if rel not in UNLISTED and self.lang_of(rel) == lang:
                    self.assertIn(self.url_of(rel), distances, rel)
                    self.assertLessEqual(distances[self.url_of(rel)], 4, rel)

    def test_search_and_404_pages_ask_not_to_be_indexed_and_stay_unlisted(self):
        for rel in self.pages:
            head = self.head(rel)
            if rel in UNLISTED:
                self.assertEqual(head.meta("robots"), ["noindex"], rel)
                # no canonical URL, language alternates or og:url that would contradict it
                self.assertEqual(head.link("canonical"), [], rel)
                self.assertEqual(self.hreflangs(rel), set(), rel)
                self.assertEqual(head.meta("og:url"), [], rel)
            else:
                # every indexable page lets search results show a large preview of its images
                self.assertEqual(head.meta("robots"), ["max-image-preview:large"], rel)
                self.assertEqual([ln["href"] for ln in head.link("canonical")], [self.url_of(rel)], rel)
            # the Claude artifact viewer's hint belongs to artifact builds only
            self.assertEqual(head.meta("claude:viewport-fit-sides"), [], rel)
        unlisted = [self.url_of(rel) for rel in UNLISTED if rel.endswith("index.html")]
        self.assertEqual(unlisted, [f"{self.base}/search/", f"{self.base}/zh/search/"])
        for rel in ("sitemap.xml", "llms.txt", "llms-full.txt", "zh/llms-full.txt", "feed.xml", "zh/feed.xml",
                    "feed.json", "zh/feed.json"):
            text = self.read(rel)
            for url in unlisted:
                self.assertNotIn(url, text, rel)

    # ----- the JSON Feeds ----------------------------------------------------------------
    def test_json_feeds_follow_json_feed_1_1(self):
        for lang in content.LANGS:
            prefix = "/zh" if lang == "zh" else ""
            rel = prefix.lstrip("/") + ("/" if prefix else "") + "feed.json"
            feed = json.loads(self.read(rel))
            self.assertEqual(feed["version"], "https://jsonfeed.org/version/1.1", rel)
            self.assertTrue(feed["title"], rel)
            self.assertEqual((feed["home_page_url"], feed["feed_url"]), (f"{self.base}{prefix}/", f"{self.base}{prefix}/feed.json"))
            self.assertEqual(feed["language"], discover.HREFLANG[lang])
            for key in ("icon", "favicon"):
                self.assertTrue(self.target(feed[key]).is_file(), key)
            items = feed["items"]
            newest = self.articles(lang)[:discover.FEED_ITEMS]
            self.assertEqual([i["url"] for i in items], [f"{self.base}{prefix}/articles/{a.slug}/" for a in newest])
            atom = ET.parse(self.out / rel.replace(".json", ".xml")).getroot()
            atom_ids = [e.text for e in atom.iter("{http://www.w3.org/2005/Atom}id")][1:]
            self.assertEqual([i["id"] for i in items], atom_ids, rel)
            # the Atom entries' authors: the same bylines, an automated one with About's #ai as its address
            ns = "{http://www.w3.org/2005/Atom}"
            self.assertEqual([(e.findtext(f"{ns}author/{ns}name"), e.findtext(f"{ns}author/{ns}uri"))
                              for e in atom.iter(f"{ns}entry")],
                             [(self.byline(a, lang)["name"], self.byline(a, lang).get("url")) for a in newest], rel)
            for item, a in zip(items, newest):
                self.assertIsInstance(item["id"], str)
                self.assertTrue(item["content_html"].strip() and item["title"] == a.title, item["url"])
                for key in ("date_published", "date_modified"):
                    self.assertRegex(item[key], RFC3339_RE)
                self.assertEqual(item["date_published"][:10], a.published.isoformat())
                self.assertEqual(item["authors"], [self.byline(a, lang)], item["url"])
                relative = [h for h in re.findall(r'(?:href|src)="([^"]*)"', item["content_html"])
                            if not h.startswith(("https://", "http://", "mailto:"))]
                self.assertEqual(relative, [], item["url"])
        for rel in self.pages:
            feeds = self.head(rel).link("alternate", type="application/feed+json")
            want = ("/zh" if self.lang_of(rel) == "zh" else "") + "/feed.json"
            self.assertEqual([ln["href"] for ln in feeds], [want], rel)

    # ----- the agents' links in every head ------------------------------------------------
    def test_every_page_names_llms_txt(self):
        for rel in self.pages:
            self.assertEqual([ln["href"] for ln in self.head(rel).link("describedby")], ["/llms.txt"], rel)
            self.assertIn('href="/llms.txt"', self.read(rel).split('<footer class="site-footer">', 1)[1], rel)

    # ----- the build's checks of the committed images --------------------------------------
    def test_a_missing_or_resized_card_stops_the_build_with_a_clear_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "static").mkdir()
            for folder in (discover.CARD_DIR, discover.ICON_DIR):
                shutil.copytree(ROOT / folder, root / folder)
            cards, warnings = discover.check_images(root, self.model)
            self.assertEqual(len(cards), len(content.LANGS) * (1 + len(self.model["topics"]["topics"])))
            victim = root / discover.CARD_DIR / discover.card_file(None, "zh")
            shutil.copy(root / discover.ICON_DIR / "icon-192.png", victim)
            with self.assertRaisesRegex(content.ContentError, r"site-zh\.png is 192x192, not 1200x630.*og_images\.py"):
                discover.check_images(root, self.model)
            victim.unlink()
            with self.assertRaisesRegex(content.ContentError, r"static/og/site-zh\.png is missing.*og_images\.py"):
                discover.check_images(root, self.model)
            shutil.copy(ROOT / discover.CARD_DIR / victim.name, victim)
            index = json.loads((root / discover.CARD_INDEX).read_text(encoding="utf-8"))
            index["cards"][victim.name]["title"] = "An older title"
            (root / discover.CARD_INDEX).write_text(json.dumps(index), encoding="utf-8")
            cards, warnings = discover.check_images(root, self.model)
            self.assertEqual(len(warnings), 1)
            self.assertIn("An older title", warnings[0])
            (root / discover.ICON_DIR / "apple-touch-icon.png").unlink()
            with self.assertRaisesRegex(content.ContentError, r"apple-touch-icon\.png is missing"):
                discover.check_images(root, self.model)

    # ----- the repository's files for citation and for coding agents ------------------------
    def test_citation_file_and_agent_guide(self):
        cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
        self.assertTrue(cff.startswith("cff-version: 1.2.0\n"))
        for line in ("type: dataset", f"url: \"{self.base}/\"", f"repository-code: \"{self.site['repo_url']}\"",
                     "  - name: verifiable.pro"):
            self.assertIn(line + "\n", cff)
        for key in ("message", "title", "abstract", "keywords", "authors"):
            self.assertRegex(cff, rf"(?m)^{key}:")
        # the abstract is the site's description (content/site.json), which it extends at the end
        abstract = " ".join(re.search(r"(?ms)^abstract: >-\n(.*?)\n(?=\S)", cff).group(1).split())
        self.assertTrue(abstract.startswith(discover.describe(self.model, "en").rstrip(".")), abstract)
        if not any((ROOT / name).exists() for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")):
            self.assertNotRegex(cff, r"(?m)^license:")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for command in ("python3 build.py --mode preview", "python3 -m unittest discover -s tests -t .",
                        "python3 tools/og_images.py"):
            self.assertIn(command, agents)


class OtherBuildModeTests(unittest.TestCase):
    """Preview and artifact builds still work with the new files and head links."""

    def test_preview_and_artifact_builds_still_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ("preview", "artifact"):
                out = Path(tmp) / mode
                result = build(out, "--mode", mode)
                self.assertEqual(result.returncode, 0, result.stderr)
                for rel in ("llms.txt", "llms-full.txt", "zh/llms-full.txt", "feed.json", "zh/feed.json",
                            "site.webmanifest", "robots.txt", "assets/og/site-en.png", "assets/icons/icon-512.png"):
                    self.assertTrue((out / rel).is_file(), (mode, rel))
                links = subprocess.run([sys.executable, str(ROOT / "tools" / "check_links.py"), str(out)],
                                       capture_output=True, text=True)
                self.assertEqual(links.returncode, 0, links.stdout)
                # relative links that resolve from each file; the deploy's own files are left out here
                for rel in ("llms.txt", "llms-full.txt", "zh/llms-full.txt"):
                    text = (out / rel).read_text(encoding="utf-8")
                    for target in re.findall(r"\]\(([^)\s]+)\)", text):
                        if target.startswith(("http://", "https://")):
                            continue
                        self.assertTrue(((out / rel).parent / target.split("#", 1)[0]).exists(), (mode, rel, target))
                self.assertNotIn("build.json", (out / "llms.txt").read_text(encoding="utf-8"), mode)
                # the Claude artifact viewer's hint: on every page of an artifact build, nowhere else
                for page in out.rglob("*.html"):
                    hints = Head(page.read_text(encoding="utf-8")).meta("claude:viewport-fit-sides")
                    self.assertEqual(hints, ["cover"] if mode == "artifact" else [], (mode, page.relative_to(out)))
            fragment = (Path(tmp) / "artifact" / "index.html").read_text(encoding="utf-8")
            self.assertFalse(fragment.lstrip().lower().startswith("<!doctype"))
            self.assertIn('property="og:image"', fragment)


if __name__ == "__main__":
    unittest.main()
