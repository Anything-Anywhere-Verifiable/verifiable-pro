# verifiable.pro content guide

This guide defines how articles, pages and data files are written for verifiable.pro. Four layers enforce it. The build (`python3 build.py`) stops with `content error:` when content breaks a structural rule, such as an unknown topic id or a citation without a matching source. `tools/lint_content.py` warns about editorial problems it can detect, and CI blocks the structural ones ([CONTRIBUTING.md](CONTRIBUTING.md#proposing-an-article)). `python3 tools/photos.py --check` and `python3 tools/illustrate.py --check`, which the unit tests run, hold each lead photo to its files and the photo pipeline's rules and each lead illustration to the generator's composition and colour rules ([Lead images](#lead-images)). Editors check the remaining rules in review.

## What we cover

verifiable.pro reports on the evidence that lets someone other than an AI provider check the provider's claims, and every piece says what its check establishes and what it leaves to trust. Trusted execution environments (TEEs) come first because AI services already use them; proofs, re-execution, audits and signatures appear as comparisons, since each places that trust with different parties.

A development is in scope when it changes what an outsider can check about an AI system. The full statement of the site's position and goals is the Vision page (`content/pages/vision.en.md` and `vision.zh.md`). Other pages summarize it and link to `/vision/`, and only Vision lists the goals.

## Files

```text
content/articles/<slug>/en.md     English article (required)
content/articles/<slug>/zh.md     Chinese edition (takes most metadata from en.md)
content/articles/<slug>/illustration.json   The article's lead image, a photo or an illustration, for both editions (see Lead images)
static/media/<slug>.webp          A lead photo, with <slug>-800.webp, <slug>-400.webp and <slug>-og.jpg (from python3 tools/photos.py --write; never edit by hand)
static/media/<slug>.svg           A drawn lead image (from python3 tools/illustrate.py --write; never edit by hand)
content/pages/<name>.<lang>.md    Standalone pages: about and vision, in both languages
content/topics.json               Topics, the verification stack and each layer's TEE line
content/tiers.json                Trust tiers and the combinations deployed today
content/tee.json                  The TEE hub: the TEE path, platforms, trackers and terms
content/resources.json            Resource library and reading paths
content/glossary.json             Glossary
content/strings.json              Interface strings in both languages
content/site.json                 Site settings, including the site assistant
```

A slug is lowercase ASCII letters and digits in words joined by hyphens, for example `apple-pcc-google-cloud`; the build rejects other folder names and skips folders whose names start with `.` or `_`. The slug becomes the URL: `/articles/<slug>/` and `/zh/articles/<slug>/`. Every article folder needs `en.md`. The build accepts an article without `zh.md` and lists it on the English site only, but CI requires `zh.md` unless an editor applies the `en-only` label.

## Front matter

Every article starts with front matter between two `---` lines, written in a small subset of YAML:

- One `key: value` per line. Colons inside the value are fine.
- Lists are written inline as `[a, b]` or as indented `- item` lines under the key.
- A value may be wrapped in double or single quotes. Quote a text value that starts with `[` and ends with `]`, or the parser reads it as a list.
- A `#` with a space before it and a space or the end of the line after it starts a comment, and a line that starts with `#` is a comment. Quote a value that must contain ` # `. Do not put a comment after a key with no value, because the parser then takes the comment as the value.
- A long value can continue on indented lines, or use a `>` (folded) or `|` (literal) block.
- `true`, `yes` or `1` turns a flag on; any other value leaves it off. Dates are `YYYY-MM-DD`.

The build stops on a line it cannot read, on an unclosed front matter block and on a bad date.

```yaml
---
title: NIST Publishes Final Guidance on Content Provenance Signals
dek: One or two sentences that state what happened and why a reader should care.
kind: news
topics: [content-provenance, governance-compute]
layers: [institutions, outputs]
event_date: 2026-10-14
published: 2026-10-19
agent: daily
evidence: [announcement, documentation]
related: [other-slug, third-slug]
sources:
  - Title of the primary source | Publisher | 2026-10-14 | https://example.org/announcement
  - Title of a secondary source | Publisher | 2026-10-15 | https://example.org/coverage
---
```

The build stops when `title`, `dek`, `kind` or `published` is missing, and when an article names neither or both of `author` and `agent` (see [Bylines](#bylines)). The editorial rules also require `topics` and `sources`, `event_date` and `layers` for a news brief, and `needs` for a guide; the linter warns when one of these is missing.

| Field | Value and effect |
| --- | --- |
| `title` | The headline. News briefs and analysis use Title Case; explainers and guides use sentence case. |
| `dek` | One or two sentences under the headline. It is also the list text, the page description and the feed summary. |
| `kind` | `news`, `analysis`, `explainer` or `guide`. |
| `topics` | Topic ids, primary topic first (see [Topics](#topics)). Listing `confidential-computing` gives the article the TEE label (see [The TEE label](#the-tee-label)). |
| `layers` | The stack layers of the claim the article reports: layer ids from `topics.json` in stack order, T7 first, for example `[runtime, hardware]`. Name at most three; `[]` names none. Lists show them as codes ("T2 T1"), Latest filters by them, and the article's Filing box links each one to its row on the Stack page. Without the field, lists use the layers that name the primary topic. The build stops on an unknown or repeated id. |
| `event_date` | News only: the date the primary source announced the development, shown as "Source date" (来源日期). |
| `published` | The date the article appeared on verifiable.pro, shown as "Filed" (本站刊发). It orders Latest, the home page's "Latest news" rail and the feeds. |
| `updated` | Optional: the date of the last substantive revision, shown as "Updated" (更新于). It is also the article's last-change date in the sitemap, the feeds and the structured data, which otherwise use `published`. |
| `sources` | Numbered sources (see [Sources](#sources)). |
| `evidence` | Optional: the kinds of evidence the article rests on, from `announcement`, `paper`, `documentation`, `standard`, `regulation`, `code`, `report` and `press`. The published Markdown source keeps the field; no page shows it at present. |
| `related` | Optional: up to three slugs for the "More on ..." row. Slugs that match no article in the same language are skipped without a warning, and empty places are filled with the newest articles that share the primary topic, then with the newest articles. |
| `disclosure` | When needed (see [Editorial rules](#editorial-rules)): one or two sentences, with inline Markdown allowed. The article shows it in the side column and at the end of the body. |
| `changes` | After a correction: one dated entry per change, listed at the end of the article under "Corrections and updates". |
| `lead` | Optional, on a news brief: `true` pins the brief as the first row of the home page's "Latest news" rail. If several briefs are marked, the newest wins; if none is, the newest brief comes first. On other kinds the flag has no effect. |
| `needs` | Guides only: what a reader needs before starting, written to complete "You need:" (你需要：), for example `the report, the vendor's certificates and published reference values`. Learn shows it on the guide's worksheet card. |
| `author` | The name of the person who wrote the article, such as `Ada Lovelace`: one person, never the site's name or an automated byline's. Set it or `agent`, not both (see [Bylines](#bylines)). |
| `agent` | For an article that the site's drafting software wrote: the id of its automated byline, from `agents` in `content/site.json`: `daily` (verifiable.pro Wire, for news briefs) or `research` (verifiable.pro Research, for explainers, analysis and guides). Set it or `author`, not both. |
| `submitted_by` | Optional: the name of the person who submitted the story, as they asked to be credited. The byline adds "Submitted by" (提交者) and the name. Leave it out when the author submitted the story. |
| `draft` | Optional: `true` keeps the article, and its Chinese edition, out of builds unless `python3 build.py --drafts` is used. |

Each `changes` entry is `YYYY-MM-DD | what changed`, and the build stops on an entry with a malformed date or no note:

```yaml
changes:
  - 2026-10-21 | Corrected the date of the announcement from 14 to 15 October.
```

Record every confirmed correction there and set `updated` to the date of the fix; typos and broken links need no entry. The procedure is in [CONTRIBUTING.md](CONTRIBUTING.md#corrections).

**Retired fields.** The build stops on an `illustration` field and on a `plate` field in the front matter of an article or a page: plates are retired, and an article's lead image is described by the `illustration.json` beside its editions (see [Lead images](#lead-images)). The social cards in `static/og/` appear only in link previews. `featured` is still read, but no page uses it.

**The Chinese file.** `zh.md` sets its own `title` and `dek`, and a guide translates `needs` there too. It takes `kind`, `topics`, `layers`, `event_date`, `published`, `updated`, `sources`, `evidence`, `related`, `featured`, `lead`, `author`, `submitted_by`, `agent` and `draft` from `en.md`; a field written in `zh.md` would override the English value, so leave these out. The one exception is a person's name: `author` and `submitted_by` may give it in its Chinese form in `zh.md`. It does not inherit `changes`, so translate every entry into `zh.md`. Translate a `disclosure` too: until `zh.md` has one, the Chinese page shows the English disclosure.

**Metadata-only edits.** The build hashes the whole source file, so adding or changing front matter such as `layers` or `needs` changes the article's source digest, as an edit to the body does. Such an edit is not a correction. Do not set `updated` or add a `changes` entry for it, and say in the commit message that the change touches metadata only, so the changed digests in the manifest are explained.

### Sources

Each source is one line with four fields separated by ` | `, a vertical bar with a space on each side: `Title | Publisher | Date | URL`. A field must not contain ` | ` itself, and the URL must start with `http://` or `https://` and contain no spaces, quotes or angle brackets. The build stops on a line that breaks these rules. Wrap an entry in double quotes when it contains ` # `, which would otherwise start a comment.

The date is the source's own publication date: `YYYY-MM-DD`, or `YYYY-MM` when the source gives only a month. For a page that shows no date, such as documentation or a homepage, write `accessed YYYY-MM-DD` with the day you read it. The site renders these as "14 Oct 2026", "Oct 2026" and "accessed 20 Oct 2026", or as "2026年10月14日", "2026年10月" and "访问于 2026年10月20日". Any other text is printed as written, but a value in one of these forms must be a real calendar date, or the build fails.

Citations count the sources in order: `[^1]` is the first line. Inserting a source shifts the numbers of the ones after it, in both editions.

### Topics

Topic ids: `confidential-computing`, `verifiable-inference`, `formal-verification`, `evaluation-audits`, `supply-chain`, `content-provenance`, `agents-accountability`, `governance-compute`. They are defined in `topics.json`, and the build rejects unknown ids in articles, resources and glossary terms.

The primary topic names the kind of claim being checked; the mechanism used to check it can be the second topic. For example, a TEE-based evaluation is `evaluation-audits` first and `confidential-computing` second. The primary topic sets the article's kicker and the topic of its "More on ..." row, and an article without `layers` takes its layer codes from it.

### The TEE label

An article carries the TEE label in every list, and counts as TEE coverage on Latest and on the TEE hub, exactly when `confidential-computing` is among its topics. Make it the primary topic when the claim concerns a TEE itself, such as a platform, an attestation report or an attack. When a TEE is the mechanism that checks another claim, list it second: EigenAI's re-execution inside TEEs is `verifiable-inference` first and `confidential-computing` second. Add the topic only when the TEE matters to the story, since the label tells readers the story is about TEEs.

### Bylines

Every article says who drafted it, so that readers can tell automated work from a person's. Bylines follow wire-service style. An article a person wrote names that person in `author`. An article that the site's drafting software wrote appears under an automated byline, which `agent` names by an id from `agents` in `content/site.json`; there each automated byline has a name and a one-sentence description in both languages. The site has two: `daily`, verifiable.pro Wire (verifiable.pro 快讯), for the news briefs that the software drafts after scanning primary sources every day, and `research`, verifiable.pro Research (verifiable.pro 研究), for the explainers, analysis and guides that it drafts after studying a subject. Name a new automated byline the same way, "verifiable.pro" and a desk name, and keep the word "agent" out of its name and description: the "Automated" (自动采编) tag beside it says what it is, and the description says plainly what the software does and that the editor decides what is published. The field and its ids keep their names (`agent: daily`, `agent: research`), which no page shows. When someone submits a story, `submitted_by` credits them under the name they gave; the Story tip form asks for one, and leaving it blank means no credit. The drafting software is built on Anthropic's Claude models, so an article about Anthropic also carries a disclosure, written in the same terms ([Editorial rules](#editorial-rules)).

The byline appears in these places:

- The article page opens its meta line with the byline. An automated byline gives its name, a dot and the "Automated" (自动采编) tag, as in "verifiable.pro Wire · Automated" (verifiable.pro 快讯 · 自动采编); the tag links to About's `#ai` section and shows the byline's description as its tooltip. A person's byline reads "By <name>" (作者：<name>). Either way, "Submitted by <name>" (提交者：<name>) follows, after a dot, when the article sets `submitted_by`.
- The home page omits bylines; opening a story shows its full byline. Other list rows end their meta line with a short mark: the automated byline's name, such as "verifiable.pro Wire" (verifiable.pro 快讯), whose tooltip gives its description, or "By <name>" for a person. Screen readers hear the automated byline's name followed by "automated". These rows appear on Latest, the topic pages and the TEE hub, the path steps and worksheet cards on Learn, and the related cards under an article.
- The Atom and JSON Feeds give a person's name as an entry's author, or the automated byline's name followed by "(automated)", or "（自动采编）" in Chinese, with About's `#ai` as its address. An Atom entry also lists the submitter as its contributor.
- The headers in `llms-full.txt` carry `Byline`, in the feeds' form, and, when set, `Submitted by`.
- The structured data name a person as the article's `author` (a `Person`) and the submitter as its `contributor`. For an automated article, the author is the publication (the site's `Organization`), since search engines take only a person or an organization as an author; the page's byline shows the automated byline's name.

The build stops on an article that:

- names neither `author` nor `agent`, or both;
- names an `agent` that `content/site.json` does not list;
- gives the site's name, or an automated byline's id or name, as `author` or `submitted_by`, since the structured data would turn it into a person;
- repeats `author` in `submitted_by`;
- names another `agent` in `zh.md`, or credits a submitter there that `en.md` does not.

Adding a byline field to a published article is a metadata-only edit (see [Front matter](#front-matter)): set no `updated` date and add no `changes` entry.

## Markdown subset

- `## Heading` and `### Subheading`. Never use `#` in the body; the title is the page's only `h1`, and the build turns a body `#` heading into `##`. An article with three or more `##` headings gets an "On this page" list.
- Add an explicit anchor with `## Corrections {#corrections}`. An id starts with a letter and continues with letters, digits, `-` or `_`. The build stops when two headings claim one id or when a heading claims an id the page template uses, such as `main` or `sources-title`.
- Paragraphs, `**bold**`, `*italic*` or `_italic_`, `` `code` ``, `[link text](https://...)` with an optional `"title"`, and bare addresses written as `<https://...>`. A link whose scheme is not `http:`, `https:` or `mailto:`, such as `javascript:`, is shown as plain text.
- Link to other pages of the site with site-absolute paths: `/articles/<slug>/`, `/topics/<id>/`, `/glossary/#<term-id>`, `/resources/#res-<id>` or `/manifest.json`. Preview builds turn them into relative links. In `zh.md`, a path that ends in `/`, with or without an `#anchor`, points to the Chinese page, so write it exactly as in `en.md`. If the target article has no Chinese edition yet, that link breaks and `tools/check_links.py` reports it: translate the target first, or link to the English page with its full URL, `https://verifiable.pro/articles/<slug>/`. Paths to files, such as `/manifest.json`, point to the same file from both editions.
- Anchors you can link to: a stack layer (`/topics/#layer-<id>`), a trust tier (`/topics/#tier-<id>`), the TEE hub's sections (`/topics/confidential-computing/#services`, `#limits`) and rows (`#svc-<id>`, `#limit-<id>`), the TEE path (`/learn/#tee-path`) and Vision's sections (`/vision/#why-tees`, `/vision/#compare`). On Latest, `/latest/#tee` lists the TEE stories and `/latest/#l1` to `#l7` the stories at one layer; the tokens combine with `+`, as in `/latest/#news+tee`.
- Lists with `-` or `1.`; indent two spaces to nest.
- Task lists for worksheets: `- [ ] Confirm the measurement matches the published release`.
- Pipe tables with a `| --- |` separator row; colons in the separator row align a column, and `\|` puts a vertical bar inside a cell.
- `> blockquote` for quoting a source verbatim (keep quotes short and attributed).
- Fenced code blocks, opened with ```` ``` ```` or `~~~` and a language: ```` ```bash ````.
- A line of `---` on its own is a section break.
- Citations: `[^1]` refers to the first entry in `sources`, `[^2, 3]` to several. Every citation must have a matching source; the build checks this. A marker at the end of a passage covers every sentence in that passage that carries no marker of its own.
- Callouts: a line `:::kind Optional title`, the callout body, then a line `:::`.
- Inline HTML is escaped and shown as text. A block that starts with a tag such as `<figure>`, `<details>` or `<table>` passes through unchanged.

| Callout | Default label (en / zh) | Use |
| --- | --- | --- |
| `facts` | Key facts / 要点 | Short list of reported facts |
| `analysis` | Why it matters / 为何重要 | Our interpretation, clearly separated from the reporting |
| `checked` | What we checked / 我们核实了什么 | Which sources we opened, when, and what we could not confirm |
| `limits` | What this does not show / 这不能说明什么 | The boundary of a claim or a mechanism's guarantee |
| `example` | Worked example (hypothetical) / 示例（假设情形） | Hypothetical scenarios and sample data |
| `note` | Note / 注 | Side information |

Open the `checked` callout with a sentence that stands alone, such as "On 20 October 2026 we read ...", because the site assistant quotes a callout as a passage of its own. A callout of any other kind has no default label. The disclosure box comes from the `disclosure` field, so do not write it as a callout.

## Article anatomy

**News brief (`news`, 250–450 words).** The headline uses Title Case and attributes the claim to its source when the claim is the source's own ("Apple Says ...", "NIST Publishes ..."). The opening paragraph states who did what and when, from the primary source. One to three short paragraphs add the facts a reader needs, each with citations. Then a `:::analysis` callout gives our reading in two to four sentences, and a `:::checked` callout lists the primary sources we opened, the date we checked them (2026-10-20 for launch content) and anything we could not confirm. Report vendor security claims as claims ("the company says the service ..."), not as established facts. Give every brief its `layers`. Give it a lead image too: an `illustration.json` beside its editions (see [Lead images](#lead-images)).

**Analysis (`analysis`, 900–1600 words).** Lead with the central judgment in the first paragraph, then develop the evidence. Keep reported facts and interpretation distinguishable, cite primary sources, and end with the open questions rather than a slogan. Headlines use Title Case.

**Explainer (`explainer`, 900–1600 words).** Define the concept, explain why it matters for checking AI systems, describe how it works together with its trust assumptions, state what it does and does not establish, and point to further reading in the sources.

**Guide (`guide`, 900–1800 words).** State the goal and when to use the guide, the inputs a reader needs, then numbered steps with task-list worksheets. Include one `:::example` worked example marked as hypothetical and a `:::limits` callout. Headlines for guides and explainers use sentence case ("How to read a remote attestation report"). Learn counts a guide's steps from the English body's `##` headings that start with `Step 1`, `Step 2` and so on, or with `1.`, `2.`, so number the step headings that way, and give the guide a `needs` line.

`tools/lint_content.py` warns only outside wider ranges (news 200–520 words, analysis and explainers 800–1900, guides 800–2100), so a clean lint does not mean an article meets the targets above.

## Editorial rules

- Every factual claim traces to a source in the front matter. Prefer the primary source: the organization's own announcement, paper, standard or documentation. Do not cite aggregators when the primary source exists.
- Write only what the source supports. Do not add numbers, dates, product names or capabilities that the source does not state. If a detail is uncertain, leave it out or say what is unknown.
- Separate what a mechanism protects from what it establishes. TEE isolation is designed to protect the software inside it, while attestation provides evidence about what was loaded; neither establishes that the software behaves correctly.
- Lead with the main point, make causal links explicit, and define terms on first use.
- Use informative headings rather than slogans. Avoid long strings of parallel clauses and subjective modifiers that add no information.
- Plain, direct sentences. Avoid em-dash asides, "not X but Y" constructions, rhetorical questions as headings, hype words ("revolutionary", "game-changing", "unprecedented") and stock phrases ("it is worth noting").
- American English spelling. Dates in running text are written day month year ("8 June 2026"), matching the site's date labels. Spell out an abbreviation at first use: "trusted execution environment (TEE)".
- Disclosures: an article about work by the editor, or about a company whose AI tools helped produce it (currently Anthropic), carries a `disclosure` in front matter. The Anthropic disclosure first describes the models' part in the terms of the automated bylines' descriptions, then says what the article reports about the company. An automated article (one that sets `agent`) opens with "The software that researched and drafted this brief is built on Anthropic's Claude models." (调研和起草本简报的程序基于 Anthropic 的 Claude 模型构建。); an explainer, an analysis or a guide names its own kind in place of "brief" (本篇解读, 本篇分析 or 本指南 in place of 本简报). An article a person wrote says instead what the models did for it, such as the translation. A data file that cites the editor's work discloses it there too: a limit in `tee.json` sets `editor: true`, which prints "The editor co-authored this work.", and other texts end with "(The editor co-authored that paper.)" and "（本站编辑是该论文的合著者。）", as the Hollow-LLM text in `tiers.json` does.
- Quotes: at most one short quotation per article, under 15 words, attributed. Summarize instead of copying.
- Corrections are made in the open, with an `updated` date and a `changes` entry in both editions.

### Wording for checks and trust

These rules keep each claim within what its evidence shows. They apply to articles, pages and every text in the data files, where a short cell makes overstatement easy, so reuse the cited articles' wording there.

- A check *establishes* or *shows* something. Attestation never "proves" anything, and every piece about a check also says what it leaves to trust.
- An attestation report records the software that was loaded ("a record of the software it loaded"), never "the software that runs".
- Isolation is "designed to" keep something from someone, or holds "within the vendor's threat model". It never "prevents" or "guarantees".
- A vendor's "attested", "private" or "verified" is reported as the vendor's claim. The site never calls a service verified.
- Stack layers say where a claim sits (T1 to T7). Trust tiers say what a passing check rests on; their order shows where the trust sits and is not a ranking, so never present one tier as better.
- In Chinese, proofs are 数学证明 and attestation is 远程证明; do not write 证明 alone where either could be meant. Trust tiers are 档 (信任分档, 第 n 档) and stack layers are 层 or 层级.

The linter flags "proves the software", "proves the model", "guarantees privacy" and "verified service" in English and 硬件证明, 能证明什么 and 可证明审计 in Chinese. It skips quoted text, because a quotation reports someone else's words.

## Chinese edition

- Translate meaning, not word order. Write natural Chinese news prose; avoid translationese and long attributive chains before nouns.
- Use the Chinese terms from `glossary.json`. At first mention give the Chinese term with the English abbreviation, for example 可信执行环境（TEE）. Keep 数学证明, 远程证明, 档 and 层 apart as [the wording rules](#wording-for-checks-and-trust) describe.
- Keep organization, product, paper and standard names in their original form (Apple、NIST、C2PA、Private Cloud Compute).
- Use full-width Chinese punctuation, and put a space between Chinese characters and Latin letters or numbers (使用 TEE 的服务、2026 年).
- Keep citations `[^n]`, callout markers, site-internal links and Markdown structure exactly as in the English file. Callout titles may be translated or omitted to use the default label.
- Open the `:::checked` callout with a sentence that stands alone, as in English (我们于 2026 年 10 月 20 日阅读了……).
- Translate the `disclosure`, every `changes` entry and a guide's `needs` into the Chinese front matter.
- Say no more than the English, and keep its figures and caveats.
- Headlines are concise statements without a trailing full stop.

The linter compares each `zh.md` with its `en.md`: the set of citations and the callout kinds must match, and it flags a missing space between Chinese and Latin text, half-width punctuation after a Chinese character and a headline that ends with a full stop.

## Lead images

Every news brief opens with a lead image, like the briefs of [Audit Commons](https://auditcommons.org/): `content/site.json` lists `news` under `lead_image_kinds`, so the build stops on a published brief without one. The home page, Latest, the topic pages and the TEE hub show a copy of it beside the story ([DESIGN.md](DESIGN.md#lead-illustrations-and-a-quieter-home-page-23-october-2026) lists the places). Other kinds may have one too. The picture is described by `content/articles/<slug>/illustration.json`, one file for both editions, whose `kind` is one of two:

- `photo`: a real photograph from a source whose license allows reuse, which `tools/photos.py` crops and grades. Photos are the default for news briefs ([Photos](#photos)).
- `illustration`: a conceptual picture that `tools/illustrate.py` draws from a scene description ([Illustrations](#illustrations)), for a story that no suitable photo fits.

Both kinds have `alt` and `caption`, each in both languages:

- `alt` says what the picture shows, concretely, in one or two sentences in each language: for a photo, the place, the objects or the people and what they are doing; for an illustration, the shapes, their colors and how they relate. Describe the picture, not the story's claim, in the articles' American spelling (gray, color, center). Screen readers read it on the article page and link previews show it; lists show the picture as decoration beside the story's title, with an empty alt.
- `caption` sits under the picture on the article page; the rules for each kind follow. The site adds a credit line under it, so the caption does not repeat the credit.
- The alt text and caption follow the [wording rules](#wording-for-checks-and-trust): a check establishes or shows something, attestation never proves anything, and nothing is called verified. The Chinese texts follow the [Chinese edition](#chinese-edition) rules, with full-width punctuation and a space between Chinese and Latin text.

### Photos

A photo spec, as `python3 tools/photos.py --write` writes it:

```json
{
  "kind": "photo",
  "file": "<slug>.webp", "width": 1600, "height": 1067, "sha256": "<digest>",
  "variants": {
    "list": {"file": "<slug>-800.webp", "width": 800, "height": 533, "sha256": "<digest>"},
    "thumb": {"file": "<slug>-400.webp", "width": 400, "height": 267, "sha256": "<digest>"},
    "social": {"file": "<slug>-og.jpg", "width": 1200, "height": 630, "sha256": "<digest>"}
  },
  "edits": {"source_sha256": "<digest of the --source file>", "source_size": [4000, 3000],
            "crop": [0, 166, 4000, 2668], "social_crop": [0, 400, 4000, 2100], "grade": "soft-1"},
  "alt": {"en": "Rows of server racks in a data center aisle under white ceiling lights.",
          "zh": "数据中心过道两侧成排的服务器机架，头顶是白色灯光。"},
  "caption": {"en": "A data center in Frankfurt in 2019. The photo does not show the systems in the story.",
              "zh": "法兰克福的一座数据中心，摄于 2019 年。照片并非报道所涉的系统。"},
  "credit": "Jane Doe / Wikimedia Commons",
  "license": "CC BY-SA 4.0",
  "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
  "source_url": "https://commons.wikimedia.org/wiki/File:...",
  "retrieved": "2026-10-24"
}
```

- `file`, `width`, `height` and `sha256` describe the photo that the article's figure shows. `variants.list` and `variants.thumb` are its 800- and 400-pixel copies, which every `<img>` of the photo offers in `srcset` beside the photo itself, so that a browser loads the smallest file wide enough for the picture on its screen: the small pictures beside a list's titles load the 400-pixel copy on most screens, and wider ones the 800-pixel copy. `variants.social` is the 1200 × 630 copy that link previews and the structured data show (`og:image`). `tools/photos.py` writes all four files and their digests; never edit them by hand.
- `edits` records what `tools/photos.py` did: the SHA-256 and size of the file it was given (`--source`, the file as downloaded unless it had to be converted first), the boxes it cut out for the photo and for the social copy (`[x, y, width, height]` in the source's pixels) and the grade.
- `credit` names the photographer and the source as the source asks to be credited, such as "Jane Doe / Wikimedia Commons", "NASA/Joel Kowsky" or "Jane Doe / Unsplash": one string, or an `{"en", "zh"}` text when the name has a Chinese form.
- `license` is the license's short name: "Public domain", "CC0 1.0", "CC BY 4.0" or "CC BY-SA 4.0" (any version, ported ones such as "CC BY-SA 3.0 de" too), "Unsplash License" or "Pexels License". `license_url` is the license's own address, such as `https://creativecommons.org/licenses/by-sa/4.0/`; for a public-domain photo it is the source's statement, such as the agency's copyright page.
- `source_url` is the page the photo comes from (the file's page on Commons, the agency's page, the photo's page on Unsplash or Pexels), not the image file, and `retrieved` is the day the file was downloaded.

**Sources and licenses.** A photo comes from one of these sources, under one of these licenses:

- Wikimedia Commons: a file whose page gives a public-domain, CC0, CC BY or CC BY-SA license. Take the credit and the license from the file's page, and pass over a file whose license is doubtful, such as a photo of someone else's poster or screen.
- US government sites: a work of the US federal government is in the public domain, such as a photo by NASA, NIST or the Department of Energy. Check the credit, since a contractor's or a news agency's photo on a government site is not a government work.
- Unsplash and Pexels, under the Unsplash License and the Pexels License, crediting the photographer and the site.

Licenses that forbid commercial use or changes (NC, ND), "editorial use only" terms, press kits, stock agencies and news agencies are not used. A cropped and graded CC BY-SA photo is an adaptation, so it stays under CC BY-SA, which its credit line names. The build stops on a license outside the list and on a `license_url` that is not that license's address; `python3 tools/photos.py --check` warns about a `source_url` outside Wikimedia Commons, US government sites, Unsplash and Pexels.

**Choosing a photo.**

- Prefer a photo of the story's own subject: the institution's building, the device, the hardware or the event. Otherwise use a stand-in that shows the kind of thing the story concerns, such as a data center, a chip or a server rack, and never one that suggests that a company, a product or a person is involved when they are not.
- A photo is a real photograph. Never use an AI-generated image, a render or a composite of different scenes or subjects as a photo, and never change what a photo shows: `tools/photos.py` crops it and applies the grade, and nothing in it is retouched, added or removed. A focus stack, which merges frames of a single subject taken at different focus distances so that all of it is sharp, counts as a photograph.
- Show a public figure only when the story concerns them, at a public event, and identify them as the source does. An identifiable private person is never the subject. A photo may show people who cannot be recognized, such as a figure seen from behind, in silhouette or only by the hands.
- A logo or a sign may appear in a photo, but a photo whose subject is a company's logo or advertising is not used, since it reads as an endorsement.
- The crop must be at least 1600 pixels wide, since a photo is never enlarged, and the photo sharp, without a watermark or a border.

**Captions.** A photo's caption says what the photo shows, and where and when it was taken when the source says so: "The Berlaymont building in Brussels, seat of the European Commission, in 2021." (布鲁塞尔的贝尔莱蒙大楼，欧盟委员会所在地，摄于 2021 年。). A stand-in's caption ends by saying what the photo does not show, as an illustration's does: "The photo does not show the systems in the story." (照片并非报道所涉的系统。). A caption never names a person, a place or a date that the source does not give. The credit line that the site adds reads "Photo: <credit> · <license> · Source", with the license and the source linked; CC BY and CC BY-SA ask that changes be indicated, so under such a photo it ends with "Cropped and color-adjusted" (经裁剪和调色), or "Color-adjusted" (经调色) when the crop keeps the whole source.

**The grade.** Every photo gets one grade, so that the photos read as one series beside the site's grays and its warm accent, softer and more muted, like Audit Commons' pictures. The grade `soft-1` lowers saturation to 88% and contrast to 92% around middle gray, as the CSS filter `saturate(0.88) contrast(0.92)` does, then adds a faint warm tone (red × 1.012, blue × 0.976): white becomes `#f8f5ef` and black `#0a0a0a`. The same matrix applies to every pixel. The files carry no metadata, so no EXIF (camera or GPS), XMP or color profile is published. On dark pages the site dims photos to 90% brightness ([DESIGN.md](DESIGN.md#photos-as-lead-images-24-october-2026)).

To add or change a photo, from the repository root:

```bash
python3 tools/photos.py --draft /tmp/vp-photo <slug> --source photo.jpg --focus 0.5,0.4 --meta meta.json   # look first; writes nothing in the repository (needs Chrome)
python3 tools/photos.py --write <slug> --source photo.jpg --focus 0.5,0.4 --meta meta.json   # the four files and the spec; deletes static/media/<slug>.svg
python3 tools/photos.py --write <slug> --source photo.jpg --same-crop   # the files again from the same source and boxes, keeping the texts
python3 tools/photos.py --check            # every photo spec and its files, as the unit tests run it
python3 tools/lint_content.py <slug>       # the alt text and caption against the style and wording rules
python3 build.py --mode preview --out /tmp/vp-preview
```

`--focus` names the point to keep in the middle of the 3:2 crop, as fractions of the source's width and height (`0.5,0.4`, or `center`, `top`, `bottom`, `left` or `right`), or a box in the source's pixels that the crop must stay inside (`X,Y,W,H`); the link-preview strip is centered on the same point. `meta.json` holds `alt`, `caption`, `credit`, `license`, `license_url`, `source_url` and `retrieved`, and flags such as `--caption-zh` or `--credit` set one field. Without them, `--write` keeps the texts of the photo in place, so a photo can be cropped again. `--same-crop`, instead of `--focus`, cuts the two boxes that `edits` records, and only from the file whose SHA-256 it records: it makes a photo's files again exactly as they were cropped, such as after a change to the copies or the budgets, and Chrome writes the same bytes from the same source. `--write` refuses a source or a crop narrower than 1600 pixels and a license outside the list, and `python3 tools/photos.py --help` lists the rest.

The encoder lowers each file's quality step by step until the file fits its budget: about 250 KB for the photo, 70 and 25 KB for the 800- and 400-pixel copies and 150 KB for the social copy. Most photos fit at the first step. A crop full of fine detail, such as foliage, gravel or a parking lot, steps further, where the detail hides the coarser encoding; a photo that would need more is better replaced by a calmer one.

The build stops when the photo or a copy is missing, does not match its digest, is not the type its name says or not the size its spec says; when the 800-pixel copy is not narrower than the photo, the 400-pixel copy not narrower than the 800-pixel one, or either has other proportions, or the social copy is not a 1200 × 630 JPEG or PNG; when an edit box lies outside the source, the social copy's box lies outside the photo's, or a box is narrower than the file made from it or has other proportions; and when the license is not one of those above. `python3 tools/photos.py --check` also holds the files to the names and sizes above, the current grade and no metadata, warns about a file over its budget, and fails on a file in `static/media/` that no spec names, as the build warns about one.

### Illustrations

An illustration spec:

```json
{
  "kind": "illustration",
  "alt": {"en": "Two stacked gray plates, the lower one tinted indigo, with a ...", "zh": "两块叠放的灰色平板，下面一块带靛蓝色调，……"},
  "caption": {"en": "Illustration: a conceptual scene of ... It does not show Apple's or Google's servers.",
              "zh": "示意图：……的概念场景，不表现 Apple 或 Google 的真实服务器。"},
  "scene": {"version": 1, "focal": "<id>", "items": ["..."], "links": ["..."]}
}
```

- `alt` describes the shapes, their colors and how they relate ("A person in an orange coat sends orange packets into a glass box on the lowest gray plate").
- An illustration's `caption` opens with "Illustration:" (示意图：), says in one sentence what the scene stands for, and ends by saying what it does not depict, such as "It does not show Meta's servers or its glasses." The site adds the credit line, "Drawn by code from its published scene description", with links to the spec and to About's `#illustrations`.
- `scene` is the generator's input; [tools/scene/README.md](tools/scene/README.md) describes its fields and props. The site publishes it with the spec and never reads it.
- `svg_sha256` is the digest of `static/media/<slug>.svg`. Leave it out of a new spec: `python3 tools/illustrate.py --write` adds it, and it refuses a placeholder such as `"<digest>"`.

Editorial rules for a scene:

- A conceptual scene, not a picture of the event. It shows the parts of an AI system that the story concerns, such as a chip, a server, a model, a document, a check or the reader's data, with the generic shapes of the home page hero, and the caption says what it does not depict.
- No logos or trademarks, no real people, products or buildings, no words, numbers or digests inside the picture, no check marks and no crowds. Indigo marks TEE things and the chain of evidence only, as on the pages; the reader's data is orange; cinnabar is for a seal.
- Scene descriptions may be drafted with AI tools, currently Anthropic's Claude models, like the text. Before publication the editor checks each scene, its alt text and its caption against the story, as About's `#illustrations` section says.

To add or change a picture, follow the steps in [Adding or changing an illustration](tools/scene/README.md#adding-or-changing-an-illustration), in the generator's guide: write or edit the spec, draft it and look, draw it, then check it and build. In short, from the repository root:

```bash
python3 tools/illustrate.py --spec content/articles/<slug>/illustration.json --png /tmp/draft.png --debug   # draft and look (needs Chrome)
python3 tools/illustrate.py --write <slug>      # draw static/media/<slug>.svg from the spec and update svg_sha256
python3 tools/illustrate.py --check             # exit 1 if a committed picture or digest differs from a fresh draw
python3 tools/lint_content.py <slug>            # the alt text and caption against the style and wording rules
python3 build.py --mode preview --out /tmp/vp-preview   # stops if a picture is missing or does not match its digest
```

`python3 tools/illustrate.py --catalog OUT.svg` draws a sheet that shows every prop.

Never edit `static/media/*.svg` by hand. The build stops with `content error:` when a spec is not a JSON object, has a field its kind does not use or lacks one, gives `alt` or `caption` in one language only, names an unknown kind, or when its picture is missing or does not match its digest. An illustration must be UTF-8 SVG on a 1200 × 800 canvas (`width="1200" height="800" viewBox="0 0 1200 800"`), and since a reader can open it as a document on the site, the build reads it against an allowlist: shapes, groups, gradients, filters, clip paths and masks in the SVG namespace (no scripts, styles, animation, text, images, links or embedded documents), presentation attributes but no `style` attribute or event handler, `href` and `url()` only to an `#id` inside the file, no CSS escapes, and no DOCTYPE, entities, comments or processing instructions. Every picture the generator draws passes. `python3 tools/illustrate.py --check`, which the unit tests and CI run, also fails when a committed picture or its digest differs from a fresh draw, or when `static/media/` holds an SVG without a spec. A draft (`draft: true`) may lack its spec; the build publishes only the pictures that a published article's spec names. `tools/lint_content.py` checks the alt text and caption by the style, wording and Chinese typesetting rules, and that an illustration's caption opens with "Illustration:" or "示意图：" and says what the picture does not depict.

### Publishing and corrections

The build publishes each spec beside its article's sources, at `/articles/<slug>/illustration.json`, and the pictures under `/assets/media/` (a photo with its three copies, or an illustration's SVG), and the manifest lists the spec (kind `illustration`) and each picture (kind `image`), so anyone can compare digests and draw an illustration again. A change to a spec or a picture changes those digests, not the article's. Replacing a photo, cropping it again, redrawing a picture, or rewording its alt text or caption without changing a fact, is not a correction: it needs no `updated` date or `changes` entry, and the commit message says it touches the lead image only. A caption or a credit that misstated a fact is corrected like the text: fix it in both languages, set `updated` and add a `changes` entry to both editions ([CONTRIBUTING.md](CONTRIBUTING.md#corrections)).

## Pages

A page is `content/pages/<name>.<lang>.md`, published at `/<name>/` and `/zh/<name>/`. The name is lowercase words joined by hyphens, and a name that collides with a section of the site, such as `latest`, stops the build. The front matter takes `title`, `dek` and optional `published` and `updated` dates. A page shows those dates in its Filing box and lists every `##` heading under "On this page". Unlike an article, it has no verification record at its end; the manifest lists its source digest like an article's. The header links Vision (`vision`), and the footer links About (`about`).

### Includes

A page can show text that is kept elsewhere, so each statement is written once. Write an include as a line of its own:

```html
<div data-include="positioning"></div>
<div data-include="tiers-summary"></div>
```

`positioning` becomes the site's positioning paragraph (the `home_positioning` string), set as the page's lead. `tiers-summary` becomes the order note and the summary table built from `tiers.json`. The build stops on any other name and on an include that shares its line with other text.

### Anchors other pages use

Other parts of the site link to anchors on About and Vision, so both editions keep these heading ids:

- About: `#integrity`, `#corrections` (the footer and each article's correction box), `#contribute` (the footer), `#assistant` (the site assistant's panel), `#contact` (the repository's issue forms), `#ai` (Vision and CONTRIBUTING.md), `#editor` and `#illustrations` (how the site chooses photos and makes illustrations, which the credit line under every illustration links). The About page's assistant section also contains the sentences that `build.py` checks before a production build may switch the assistant to `live`; see the README's [Site assistant](README.md#site-assistant) section.
- Vision: `#problem`, `#verifiable`, `#why-tees` (linked from the home page and the TEE hub), `#compare` (linked from the Stack page), `#goals`, `#non-goals`, `#readers`, `#editor` and `#accountability`.

Until the owner fills them in, About and Vision carry marked placeholders, such as the editor line in square brackets that starts `[editor` and the goal dates `[to be confirmed by the owner]`. A production build prints a warning for each one, so replace a placeholder only with the owner's text.

## Data files

`content.DATA_FILES` lists five data files: `topics.json`, `resources.json`, `glossary.json`, `tee.json` and `tiers.json`. The manifest hashes each of them, and the build publishes them at `/data/<name>.json`. Rules shared by the newer fields:

- A text is `{"en": "...", "zh": "..."}`, with both languages filled in. Only a platform cell in `tee.json` may stay empty, and then in both languages. A name, such as a platform's or a service's, may instead be one string shared by both languages.
- Dates use the source-date forms `YYYY-MM-DD`, `YYYY-MM` or `YYYY`.
- A source in `tee.json` is `article:<slug>`, a published English article, or `resource:<id>`, an entry in `resources.json`.
- `load()` checks every id these files name (articles, resources, glossary terms, stack layers, topics and tiers) and stops the build on any it cannot find, naming the file and the field.

### `resources.json`

The file holds `{"paths": [...], "resources": [...]}`. Each resource is one object:

```json
{"id": "attestable-audits", "title": "Attestable Audits: Verifiable AI Safety Benchmarks Using Trusted Execution Environments",
 "url": "https://arxiv.org/abs/2506.23706", "org": "Author or organization", "year": 2025,
 "type": "paper", "topics": ["evaluation-audits", "confidential-computing"], "tee_area": "uses",
 "note": {"en": "One neutral sentence on what it is.", "zh": "一句中性的中文说明。"},
 "verified_on": "2026-10-19"}
```

- `id` is unique, starts with a letter and uses letters, digits, `-`, `_` or `.`. It becomes the anchor `#res-<id>` on the Resources page. The build stops on a duplicate or malformed id.
- `url` is an `http(s)` address; the build checks it. `year` may be left out.
- `type` is one of `paper`, `standard`, `specification`, `tool`, `project`, `organization`, `report`, `benchmark`, `course` and `dataset`. Its label comes from the `type_<type>` string; any other value is shown as written.
- `topics` lists topic ids. Every listed topic's page includes the entry, and the first one decides the catalog section of an entry without a TEE area.
- `tee_area` is required on every entry whose `topics` include `confidential-computing`, and allowed on no other: `standards`, `cpu`, `gpu`, `services`, `attacks`, `performance` or `uses`. The catalog lists these entries first, under their areas, the "TEE area" filter selects by it, and the TEE hub's "Primary documents" groups them the same way.
- `note` is one neutral sentence in each language; without a `zh` text, the Chinese site shows the English one.
- `verified_on` is the date an editor last opened the link, shown as "Link checked" with the date. A value that is not `YYYY-MM-DD` is left out.
- `featured` is still accepted, but no page uses it.

`paths` holds the reading paths at the top of Resources. Each path has an `id`, a `title` and a `purpose`, and `entries`: resources in reading order, each `{"id": "<resource id>", "why": {"en": "...", "zh": "..."}}`, where `why` is one line on what the reader gets from that entry.

### `glossary.json`

The file holds `{"terms": [...]}`, one object per term:

```json
{"id": "remote-attestation", "term": {"en": "...", "zh": "..."}, "definition": {"en": "...", "zh": "..."}, "topic": "confidential-computing"}
```

The `id` follows the same rules as a resource id and becomes the anchor `/glossary/#<id>`. Terms are sorted and grouped by the first letter of the English term. `topic` is optional; when it is set, it must be a topic id, and the term is linked from that topic's page. `tee.json` picks the TEE terms by id.

### `topics.json`

`stack` lists the verification-stack layers from top to bottom, so the first layer is shown as `T7` and the last as `T1`. The build requires exactly seven, because the codes, the Latest filter and the stylesheet assume them. Each layer has `id`, `name`, `claim` and `topics`, plus:

- `checkers`, right after `claim`: one sentence on who outside the provider checks the layer's claim, and with what evidence, starting with the checker, such as "Readers and platforms can check a response's signature or an image's Content Credential." It shows in three places: after "Who checks:" (谁来核查：) in the layer's card on the home page hero, as the "Who checks" line under the layer's label on phones (at rest on T1 and T2, where it addresses the reader, and on the other layers once the reader opens the row), and under the claim in the Stack page's table. Name the evidence the checker uses, such as a signature, a hash, a log or an inspection, and write "can" (可以) wherever the check depends on the checker's access or on a practice that is still emerging. At T1 and T2 the texts address the reader ("your device", 你的设备), an owner decision; "a user's device" (用户的设备) is the alternative. The field is required in both languages, on one line with no surrounding spaces, and the build stops on a text longer than 100 characters in English or 45 in Chinese (`content.MAX_CHECKERS`), which keeps it to about three lines in a layer card and two or three in a phone row at 390px.
- `tee`: what a TEE contributes at that layer. `reach` is `direct` where the TEE's evidence bears on the claim itself (T1 and T2) or `via` where it counts only through code the TEE measures; a `via` layer cannot sit below a `direct` one. `short` is the TEE line in the layer's card on the home page hero and in its row on the Stack page, and `text`, the fuller version, is folded under that row.
- `others`: other evidence at that layer, as `{"tier": "<tier id>", "examples": {...}}` items that the Stack page links to their tiers.
- `bind`: on every layer except T1, how the layer's evidence is bound to the layer below. `status` is `deployed` (in use), `emerging` or `missing`, and `text` says how in one sentence. The statuses draw the evidence chain in the home page hero and in its legend ("The chain of evidence today"), and through the codes of the Stack page's table, which also prints `text`. T1 has no `bind`, since no layer lies below it; the build stops on one there and on an unknown status.
- `hero`: the layer's label beside the home page hero. `short` is its short name (`{"en": "Policy", "zh": "政策"}`), which the label shows after the layer's code, "T7 Policy" (T7 政策), so it does not repeat the code; the code and the name make up the label's name area, where a pointer opens the layer. `icon` one of the line icons in `sitegen/logos.py` (`policy`, `evaluations`, `agents`, `outputs`, `models`, `runtime`, `hardware`), and `examples` one to seven examples of the best-known companies, products and bodies at the layer, each `{"logo": "<slug>"}` (a vendor mark from `sitegen/logos.py`, named for screen readers by its owner, or by `"name"` when the product is more specific, such as the OpenAI mark with `"name": "OpenAI Codex"`), `{"text": "..."}` (a name), or both (a mark followed by a name, such as Google's mark before "SynthID"). The examples must fit one line beside the hero from 45em: prefer marks to names and keep names short. A named mark's name (its owner's, or `"name"`) is what screen readers hear for it, what its tooltip shows when a mouse or pen rests on it or a tap touches it, and what the open card lists on touch screens, so write it as a reader should see it; pointing at an example shows its name and opens no layer. Give `"name"` as one string, or as an `{"en", "zh"}` text when it adds words to a name, as `"Meta (AI labels)"` (`"Meta（AI 标签）"`) does. The owner's name is the mark's `title` in `sitegen/logos.py`, in the page's language: one string where the Chinese edition keeps it in its original form, as it does for companies and products ("NVIDIA", "Apple"), or an `{"en", "zh"}` pair where the Chinese edition writes it in Chinese, as for the European Union (`"欧盟"`); the build stops on a title that is neither. When you add a mark or a name, check how the Chinese page names it. Add a mark by vendoring its Simple Icons path into `sitegen/logos.py`, or, where Simple Icons has none (as for Azure or DeepSeek), its Lobe Icons paths (MIT). The examples are illustrations, not endorsements: About says so, and the hero tells screen readers right before the labels (`hero_layers_note`).

`topics` lists the topics in the order every page shows them, each with `id`, `name`, `one_liner`, `description`, `questions` and `techniques`, plus `tiers`, the trust tiers its checks rest on with the main one first. Every topic except `confidential-computing` also has `tee_relation`, the "How this compares with a TEE" callout on its page. Texts are `{"en": "...", "zh": "..."}`, `questions` is `{"en": [...], "zh": [...]}`, and `techniques` is a list of `{"name": {...}, "description": {...}}` objects. Topic ids are lowercase words joined by hyphens.

Adding or removing a topic or a layer also needs other files. The stylesheet gives each topic id a hue and is written for seven layers, and `sitegen/art.py` draws a pattern for each topic id; see [DESIGN.md](DESIGN.md). The lead illustrations name layers too: `tools/scene/palette.py` gives each layer from T3 up a hue, and `story_tints()` in `tools/illustrate.py` allows the indigo tint for `runtime` and `confidential-computing` stories and the circuit-board tint for `hardware`. Each topic also has a social card in each language, which shows its `name`: the build stops until a new topic's cards exist and warns when a renamed topic's cards still show the old name, so run `python3 tools/og_images.py` (see the README's [Social cards and icons](README.md#social-cards-and-icons)).

### `tiers.json`

The file holds the comparison on the Stack page (`/topics/#tiers`) and the summary that Vision includes:

- `order_note`, printed above every list of tiers and above the Vision summary. It must keep the statement that the order is not a ranking.
- `he_note`, on homomorphic encryption and multiparty computation, which also hide data in use but are not checks in themselves.
- `baseline`: the provider's word, an unnumbered row with `trust_name` and `text`.
- `tiers`: the tiers in order, with `n` counting from 1 in file order. Each has `id`, `n`, `trust_name` (what you trust, which also names the tier), `mechanism`, `short`, `approaches`, `establishes`, `not_established`, `trust`, `hidden` (what stays hidden from the operator), `cost` and `summary` (the Vision table's "Compared with a TEE" cell). It also has exactly one of `vs_tee`, how the tier compares with a TEE, and `focus`, which only the TEE tier uses to say why TEEs are the main subject. `combined` is optional, and `layers`, `topics` and `read` (one to three article slugs) complete the row.
- `combinations`: combinations deployed today, each with `id`, `name`, `text`, `tiers` (at least two tier ids) and `article`.

### `tee.json`

The file holds the TEE hub (`/topics/confidential-computing/`) and the TEE path:

- `reviewed`: the date an editor last reviewed the file, `YYYY-MM-DD`.
- `establishes`: `shows` and `still`, the hub's two lists of what a checked attestation report shows and what you still trust, and `boundary`, the line under them.
- `path`: the TEE path in reading order, shown on Learn, on the hub and on the home page. A published step is `{"article": "<slug>", "outcome": {...}}`; the outcome completes "After this you can" (读完之后，你可以), so it starts in lowercase. A planned step is `{"planned": {...}}` and shows as "Planned" without a link. The home page's "Learn TEEs in five steps" (`tee_block_path`) and Learn's "Read these five articles in order" (`learn_path_dek`) count the published steps: the build fills their `{n}` with that number, written as a word ("five", 五), so publishing a planned step updates both. Learn's line also names the path's first and last subjects, so edit it when a new step changes either.
- `platforms`: CPU and GPU cards with `id`, `group` (`cpu` or `gpu`), `name`, `isolates`, `signs`, `reference_values`, `out_of_scope` and `sources`. A cell left empty reads "Not yet covered here". `gpu_note` is the line on binding CPU and GPU evidence to one session.
- `services`: AI services that publish attestation evidence, with `id`, `name`, `record`, `checker`, `inspection`, `as_of` (the day the row was checked, `YYYY-MM-DD`) and `sources`.
- `limits`: attacks and limits, newest first and undated rows last, with `id`, `date`, `name`, `physical` (whether the attack needs physical access), `defeated`, `access`, `vendor`, `status`, `sources` and `editor`.
- `responses`: proposed responses to those limits, with `id`, `date`, `name`, `text` and `sources`.
- `terms` and `learn_terms`: glossary ids for the hub's "Terms to know" and Learn's "Terms to know first".

Row ids become anchors on the hub (`#plat-<id>`, `#svc-<id>`, `#limit-<id>` and `#resp-<id>`), so they are unique across the four lists. An article that a service, limit or response row cites gets a "Tracked in the TEE hub" line in its Filing box, which links to that row. The services and limits are dated records: when a row changes, check its sources again and update `as_of` or `date`.

### `strings.json`

The file holds the interface text as `{"en": {...}, "zh": {...}}`, keyed by string id. Every key exists in both languages, and a unit test checks this. The exceptions are the `_one` variants, such as `articles_count_one`, which the templates use instead of the base key when a count is 1; Chinese needs none. Placeholders in braces, such as `{n}`, `{topic}`, `{date}` or `{year}`, are filled in by the templates and must survive translation. The `chat_*` keys belong to the site assistant. Changing a string does not change the manifest digest.

`home_positioning` is the lead of Vision (the `positioning` include), and `home_lead` says it in one sentence in the home page's first band (Vision, which the band's first link opens, says the rest; a unit test keeps `home_lead` to one sentence), so edit them together with `vision.en.md` and `vision.zh.md`, and with the README's Scope section, which restates `home_positioning`. `home_title` is the home pages' title, which search results and link previews show (`<title>` and `og:title`): it starts with the site's name and says what the site covers, in at most about 60 characters in English and 30 in Chinese, and a unit test holds it to 60 and 30. The structured data still name the site `verifiable.pro`, and other pages append " | verifiable.pro" unless their title already names the site. Latest, Learn, Resources and Glossary use `*_meta_title` strings that name their subject in search results while keeping the short visible heading. Their `*_meta_description` strings, and those for the Stack and TEE hub, summarize the full introductions for search results and link previews. `home_kicker`, the line above the home page's tagline, is an owner decision: "Evidence you can check, from the chip up" (从芯片往上，你能核查的证据) suits the chain drawn as it holds today, and "An unbroken chain of evidence, from the chip up" fits only a chain drawn whole, since the page must not contradict its own legend. Change it only with the owner; [DESIGN.md](DESIGN.md) records the owner decisions and how to switch each. The site's social card shows `home_kicker` above `tagline`, so redraw the cards with `python3 tools/og_images.py` after changing either. `home_editor` is the editor line after the copyright in every page's footer: "Edited by Mengyuan Li" (编辑：Mengyuan Li). It remains a link to Vision's `#editor` section. `footer_about` briefly states only the site’s subject. Directly below it, the footer’s maintenance line reads "Maintained by SEPT Lab · Contributors" (由 SEPT Lab 维护 · 贡献者), with Contributors linking to the current-language `/contributors/` page. This entry appears only in the black footer, without a matching line in the home intro or a new main-navigation item. In the wordmark, colour only SEPT in #ff9b9b, the readable dark adaptation of the lab website’s canonical #990000; Lab stays in the footer’s neutral ink. The footer is black in both page themes, so keep this adaptation in the light page theme too. Use SEPT Lab as the maintenance name; Vision and About give its USC affiliation.

`lead_credit`, `lead_credit_spec` and `lead_credit_how` make the credit line under an illustration on its article page: `{spec}` in `lead_credit` becomes `lead_credit_spec`, linked to the published spec, and `lead_credit_how` links to About's `#illustrations` and repeats that section's heading, "How we choose photos and make illustrations" (我们如何选用照片和制作插图), so change it with the heading. `lead_photo_credit` (with `{credit}`) and `lead_photo_source` do the same for a photo, and under a photo whose license asks that changes be indicated (CC BY and CC BY-SA) the line ends with `lead_photo_edited` ("Cropped and color-adjusted"), or `lead_photo_graded` ("Color-adjusted") when its crop keeps the whole source. The license link shows the spec's `license` as written, such as "CC BY 4.0", except "Public domain", which names no license: it shows `lead_photo_public_domain` ("Public domain", 公有领域), so Chinese pages say it in Chinese.

`byline_by` ("By {name}", 作者：{name}) makes a person's byline and `byline_submitted` ("Submitted by {name}", 提交者：{name}) credits a submitter. `byline_agent` is the "Automated" (自动采编) tag of an automated byline, `byline_agent_vh` ("{name}, automated.") is what screen readers hear for an automated byline's mark in a list row, and `byline_agent_named` ("{name} (automated)") gives an automated byline in the feeds and in `llms-full.txt` (see [Bylines](#bylines)). The keys keep the internal word "agent", after the front-matter field; their texts never use it.

`search_hint` gives the search page's minimum query, which `static/site.js` sets: two characters, or a single Chinese character. Change the two together.

`hero_scene_title` and `hero_scene_desc` describe the home page hero for screen readers, so edit them together if the scene changes. The figure has no caption, so `hero_scene_desc` also says what a caption would: that the scene is a conceptual illustration, that the indigo line is the chain of evidence and the two indigo plates are the layers where TEEs give direct evidence, that the dotted path carries the reader's prompts and data and brings an answer back, and that the layers are positions in this site's own scheme, not security levels, to which the stories' T1 to T7 tags refer. `hero_scene_desc` describes only the still scene, which is all a page without JavaScript shows. `hero_scene_desc_live` holds what the script adds: the person starts in gray, gains colour with each layer checked, and once all seven are, small dots of data travel the path. `static/hero.js` appends it to the description (from the scene's `data-hv-live`) once it has set the figure up, so a reader without the script never hears of a gray person. `hero_scene_desc` says what a solid, a dashed and a broken stretch of the chain mean without naming the layers where each is drawn, so it stays true whatever `bind.status` says; keep it that way. If the chain is drawn whole at rest (`HERO_CHAIN_REST = "whole"` in `sitegen/render.py`), its chain sentence becomes "An indigo line rises from the GPU die through a ring on every plate and ends at the seal." and, in Chinese, "一条靛蓝色的线从 GPU 芯片升起，穿过每块平板上的一个圆环，止于印章。" `hero_layers_label` names the list of layer labels, and `hero_layers_note` ("Logos and names are examples, not endorsements.") is read to screen readers right before it and shown nowhere; About's `#coverage` section says the same in view, so keep the two in step. Every other line on the home page stays short, since the pages it links to explain the rest: the hero keeps one short line each for the person's label, the hint and the legend's title, and the TEE block lists the path's steps without what each lets the reader do. The guide cards under "Checks you can run" (`checks_title`) likewise leave out each guide's dek, which Learn's worksheet card and the guide itself show. The other hero strings:

- `hero_person` and `hero_person_who` label the person drawn beside the board, right under the scene. The person is the reader, talking with an AI system, whose prompts and data go into it, so both strings speak to "you" (你). `hero_person_who` says in one short sentence that the reader's prompts and data pass through all seven layers, which is what the dotted route shows, now that no caption explains it: keep it to about 60 characters in English and 20 in Chinese, one line on a phone (a unit test holds it there). From 45em the person's label, with the count of layers checked on its name line, and the hint share the 5.75rem that the hero's height cap leaves under the scene, and a longer label pushes them below the first screen on laptops such as 1366 × 768 and 1280 × 720 (`node tools/cdp.mjs hero SITE --sizes 1366x768,1280x720` checks it). The layer cards' "Who checks" lines (`checkers` in `topics.json`) name the real checkers. `hero_scene_title` and `hero_scene_desc` describe the same person and the dotted route that carries their data through all seven layers and back; they say what the picture shows, not an order of events, so only `hero_scene_desc_live` says that the person starts in gray and that the data moves once every layer is checked.
- The hint, which `static/hero.js` reveals, has a line for each way of opening a layer, and the stylesheet shows the one that fits the reader's input through the hover and pointer media features: `hero_hint` for pointing at a layer (its name or its plate; the examples under a name open nothing) or tabbing to it, from 45em with a mouse or a pen; `hero_hint_touch` for a tap on a layer's arrow (the chevron) on touch screens; and `hero_hint_click` for a click on the arrow in the list below 45em with a mouse. Each is one short sentence that asks the reader to open each layer until they turn colorful: the person starts in gray and gains colour with each layer checked. Keep each to about 60 characters in English and 25 in Chinese, as a unit test does. The touch and click lines name the arrow, since a tap or a click on a layer's name follows its link to the Stack page. Once all seven layers are checked, `hero_hint_done`, `hero_hint_touch_done` and `hero_hint_click_done` replace them, without the promise of colour. A line and its `_done` line share one grid cell, so keep the `_done` line shorter than the line it replaces, and the hint keeps its height. From 45em the hint stands under the column of layer labels, beside the person's label; on phones it sits under the person's label. In English the hint's lines are balanced, so prefer wording whose natural break falls near the middle ("Point at or tab to each layer / until you turn colorful"). In Chinese the hint breaks only between words (`keep-all`) and fills each line instead of balancing it, and a space there is a break too (as around "Tab"), so put a comma after the first clause, where the line should break: it runs to two lines on laptops, beside the person's label.
- `hero_progress` and `hero_progress_done` are the count of layers checked, on the name line of the person's label, which `static/hero.js` reveals and announces to screen readers. In `hero_progress` the script fills in `{n}`, the number checked, and the build fills in `{total}`, the number of layers; `hero_progress_done` replaces it once every layer is checked. Keep both short, since they share a line with `hero_person`. `hero_check_all` is the button that checks every layer at once, and `hero_checked` is what a screen reader hears for the mark beside a checked layer's name.
- `hero_chain_title` and `hero_chain_run` make the chain's legend. The build merges consecutive bindings with the same `bind.status` into runs and fills `{lo}` and `{hi}` with the codes of the layers where each run starts and ends, as in "Emerging · T2 to T6". What a break means is said under the Stack page's table (`chain_legend`), not in the legend.
- `checkers_label` labels each layer's `checkers` in the layer cards, on phones and on the Stack page.
- In a layer card, `hero_card_root` and `hero_card_root_text` take the place of the binding line on T1, `hero_card_none` stands in for the story count of a layer without stories, and `hero_card_open` is the cue at the card's foot that a click opens the Stack page. `hero_card_examples` ("Examples", 举例) labels the line in which the card lists the names of its label's examples on touch screens, where no pointer can rest on a mark to see its name in the tooltip; the names come from `topics.json`, so the line needs no other string.
- `hero_more` names, for screen readers, the button that opens a layer's card on touch screens and phones; `{name}` is the layer's short name.
- `hero_code_sep` is what screen readers hear between a layer's code and its name, in the label and in the card's head, where the page shows only a little space: ", " in English ("T5, Agents") and "，" in Chinese (T5，智能体). It is not shown, so keep it to the separator alone.

### `site.json`

| Key | Use |
| --- | --- |
| `domain` | The site name recorded in the manifest, the `CNAME` file and the feed entry ids, and the name of the site and its publisher in the structured data, `llms.txt` and the feeds |
| `base_url` | Canonical URLs, language alternates, the feeds, the sitemap, `robots.txt`, `llms.txt`, the structured data, the social cards' addresses and the page address in correction issues |
| `alternate_name` | Another name for the site, given as `alternateName` of the `WebSite` and the `Organization` in the structured data. "Verifiable AI Systems" is the line under the wordmark in the logo lockup. |
| `description` | A plain description of the site in both languages, `{"en": "...", "zh": "..."}`: what it covers and what it publishes, in the words people search for. `llms.txt`, the `llms-full.txt` files and the web app manifests use it, and the abstract in `CITATION.cff` opens with the English text, so update that file with it. Pages keep `site_description` from `strings.json` as their meta description. |
| `contact_email` | The editorial address in the footer and in the structured data (`Organization`), and in the correction boxes when `repo_url` is empty |
| `repo_url` | The public repository. When it is set, the footer links to it, each article's correction box opens a prefilled correction issue and links to the source file on GitHub, and the structured data (`sameAs`) and `llms.txt` name it. |
| `repo_branch` | The branch for those source links (default `main`) |
| `analytics.ga4_measurement_id` | Optional GA4 stream ID, such as `G-XXXXXXXXXX`; an empty string omits the analytics controls and script reference. Only production pages on the configured HTTPS origin can activate it, after the reader allows statistics. Keep all Enhanced measurement off in GA4. See [Optional visit statistics](docs/MAINTAINING.md#optional-visit-statistics). |
| `agents` | The automated bylines that an article the site's software drafted may appear under, by id: `{"daily": {"name": {"en": ..., "zh": ...}, "description": {"en": ..., "zh": ...}}, ...}`. The name is one string or an `{en, zh}` text in wire-service style, such as "verifiable.pro Wire"; the description is one sentence in each language that says plainly what the software does and that the editor decides what is published. The "Automated" tag beside the byline and a list row's mark show it as their tooltip, and About's `#ai` section says the same, so keep the two in step. Ids are lowercase words joined by hyphens. See [Bylines](#bylines) |
| `illustrations` | `false` keeps the drawings that `sitegen/art.py` generates from each article's digest off the pages. Leave it off: an article's lead image comes from its `illustration.json` (see [Lead images](#lead-images)). (The social cards for link previews use the same patterns; no page shows them.) |
| `lead_image_kinds` | The article kinds whose every published article must have an `illustration.json`, such as `["news"]`; the build stops on an article of a listed kind without one. `[]` requires none, and an article of any kind may still have one. See [Lead images](#lead-images) |
| `chat` | The site assistant's settings; see the README's [Site assistant](README.md#site-assistant) section |
