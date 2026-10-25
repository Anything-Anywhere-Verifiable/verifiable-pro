## What this changes

<!-- Say what changes in one or two sentences, and link the issue it resolves, for example "Closes #12". -->

## Type of change

- [ ] New article
- [ ] Correction or update to a published article
- [ ] Translation
- [ ] Lead image only (an `illustration.json` and its photo files or its illustration)
- [ ] Resources, glossary or topics data
- [ ] Site code, styles or tools
- [ ] Ask assistant: widget, API contract (`api/`) or backend (`backend/`)
- [ ] Repository settings, workflows or documentation

## Editorial checklist

<!-- Delete this section for code-only changes. Each item restates a rule in CONTENT_GUIDE.md:
     https://github.com/Anything-Anywhere-Verifiable/verifiable-pro/blob/main/CONTENT_GUIDE.md -->

**Sources and claims**

- [ ] Every factual claim traces to an entry in `sources` and is cited with `[^n]`; every source is cited.
- [ ] The primary source is cited where one exists (the organization's own announcement, paper, standard or documentation), not an aggregator.
- [ ] The text adds no numbers, dates, product names or capabilities that the sources do not state; uncertain details are left out or marked as unknown.
- [ ] Vendor security claims are reported as claims ("the company says the service ...").
- [ ] What a mechanism protects is kept separate from what it establishes.
- [ ] At most one quotation, under 15 words, attributed.
- [ ] Source dates are the source's own publication date (`YYYY-MM-DD` or `YYYY-MM`), or `accessed YYYY-MM-DD` for a page that shows no date.

**Structure**

- [ ] Front matter has `title`, `dek`, `kind`, `topics` (primary topic first: the kind of claim being checked) and `published`; a news brief also has `event_date`.
- [ ] The body uses `##` and `###` headings only, never `#`.
- [ ] News brief (250–450 words): the opening paragraph states who did what and when; a `:::analysis` callout gives our reading; a `:::checked` callout opens with a sentence that stands alone ("On 20 October 2026 we read ...") and lists the primary sources opened, the date they were checked and anything we could not confirm.
- [ ] Analysis or explainer (900–1600 words), or guide (900–1800 words) with numbered steps, one `:::example` marked as hypothetical and a `:::limits` callout.
- [ ] Headline: Title Case for news briefs; sentence case for explainers and guides.
- [ ] A `disclosure` is present if the article reports on a company whose AI tools helped produce it (currently Anthropic) or on work by the editor.
- [ ] If `evidence` is set, its values come from the list in CONTENT_GUIDE.md (`announcement`, `paper`, `documentation`, `standard`, `regulation`, `code`, `report`, `press`).
- [ ] A news brief has `illustration.json` (CONTENT_GUIDE.md, "Lead images"), with alt text that says what the picture shows and a caption, in both languages. A photo comes from an allowed source under an allowed license, its credit names the author and the source, a stand-in's caption says what the photo does not show, and its files were made with `python3 tools/photos.py --write <slug>`. An illustration's caption says it is an illustration and what it does not depict, and its picture was drawn with `python3 tools/illustrate.py --write <slug>`. Neither was edited by hand.

**Style**

- [ ] The main point comes first, causal links are explicit, terms are defined at first use, and headings are informative rather than slogans.
- [ ] Plain, direct sentences, with no long strings of parallel clauses, subjective modifiers, em-dash asides, "not X but Y" constructions, rhetorical questions as headings, hype words or stock phrases.
- [ ] American English spelling; dates in running text written as "8 June 2026"; each abbreviation spelled out at first use.

**Both editions**

- [ ] `en.md` and `zh.md` are both included, or this pull request asks for the `en-only` label and says when the Chinese edition will follow.
- [ ] `zh.md` has its own `title` and `dek` (and a translated `disclosure` when `en.md` has one) and keeps the citations, callout markers, internal links and Markdown structure of `en.md` exactly.
- [ ] `zh.md` uses the Chinese terms from `glossary.json` (with the English abbreviation at first mention), keeps names in their original form, uses full-width punctuation with a space between Chinese and Latin text or numbers, and has no full stop at the end of the headline.

**Corrections and updates** (published articles only; see [CONTRIBUTING.md](https://github.com/Anything-Anywhere-Verifiable/verifiable-pro/blob/main/CONTRIBUTING.md#corrections))

- [ ] `updated:` is set in `en.md`.
- [ ] A `changes:` entry (`YYYY-MM-DD | note`) records each confirmed correction in `en.md`, and a translated entry is added to `zh.md`, which does not inherit `changes`.
- [ ] The commit title starts with `correction(<slug>):`.

**Data files** (resources, glossary, topics)

- [ ] New entries follow the formats in CONTENT_GUIDE.md, "Data files": a `type` from the listed types, the catalog topic first, a one-sentence `note` in English and Chinese, and at most six resources marked `featured`.

## Checks run locally

- [ ] `python3 -m unittest discover -s tests -t .`
- [ ] `python3 tools/lint_content.py <slug>` (warnings explained below, if any)
- [ ] `python3 build.py --mode preview && python3 tools/check_links.py dist-preview`
- [ ] For a lead image: `python3 tools/photos.py --check` for a photo, `python3 tools/illustrate.py --check` for an illustration
- [ ] For backend changes: `python3 -m unittest discover -s backend/mock -v`

## AI use

- [ ] No AI tools were used, **or** I list them here with what they did, and I checked every claim against its cited source myself:

## Sign-off

- [ ] Every commit is signed off (`git commit -s`) under the [Developer Certificate of Origin](https://developercertificate.org/).
