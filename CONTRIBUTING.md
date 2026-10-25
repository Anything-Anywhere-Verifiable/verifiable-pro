# Contributing to verifiable.pro

You can contribute to verifiable.pro in English or Chinese. The table below shows where each kind of contribution goes, from a story tip to a code change. The sections after it follow a pull request from review to publication. Maintainer procedures, such as repository settings, deployment and the publishing records, are in [docs/MAINTAINING.md](docs/MAINTAINING.md).

## Ways to contribute

| You want to | Do this |
| --- | --- |
| Suggest a development we should cover | Open a **Story tip** issue |
| Suggest a paper, standard, tool or dataset | Open a **Resource suggestion** issue, or a pull request that edits `content/resources.json` |
| Report an error in a published page | Open a **Correction request** issue, or a pull request with the fix |
| Write an article or translate one | Open a pull request (see [Proposing an article](#proposing-an-article)) |
| Report a display or behavior problem, including in the Ask assistant | Open a **Site bug** issue |
| Change the generator, styles, tools, the Ask widget, the chat API contract or the mock backend | Open a pull request (see [Code changes](#code-changes)) |
| Report a security problem | Use "Report a vulnerability" on the repository's Security tab. Do not open a public issue |

For a new article, open a Story tip issue first so an editor can confirm the angle before you write.

**Credit for a story tip.** A tip that becomes an article credits you in its byline as "Submitted by" (提交者), under the name you give in the Story tip form. Leave that field blank if you prefer no credit. An article you write yourself names you as its author ([CONTENT_GUIDE.md](CONTENT_GUIDE.md#bylines)).

## Roles

- **Maintainer** (@Mengyuan-L): makes the final decision on what is published. The maintainer also owns the editorial policy, the publishing workflow and the repository settings.
- **Editors**: review content pull requests against [CONTENT_GUIDE.md](CONTENT_GUIDE.md) and check each claim against its cited source. They also review the Chinese edition and apply labels.
- **Contributors**: anyone who opens an issue or a pull request. You do not need write access; work from a fork.

The paths each role reviews are listed in [.github/CODEOWNERS](.github/CODEOWNERS).

## Setting up

The site generator needs only the Python standard library. Use Python 3.12 or later, the version CI uses (check with `python3 --version`). The current generator, `tools/verify_manifest.py`, `tools/lint_content.py`, `tools/illustrate.py` and the mock backend in `backend/mock/` also run on the Python 3.9 that ships with macOS, but CI tests only the mock backend on 3.9.

```bash
git clone https://github.com/<you>/verifiable-pro.git
cd verifiable-pro
python3 build.py --mode preview
python3 -m http.server 8000 --directory dist-preview
```

Then open `http://localhost:8000/`. Search and the Ask assistant load their data with `fetch`, so they work only when the preview is served over HTTP, not when it is opened as a file. Git ignores the build output (`public/`, `dist-*/`, `_site*/`); never commit it.

The Ask assistant has three modes. `chat.mode` in `content/site.json` sets the mode, and `--chat` overrides it for one build:

- `--chat demo` answers in the browser from the site's own published files. Nothing typed leaves the page.
- `--chat live --chat-api <URL>` sends questions to a backend that implements the contract in `api/chat-v1.md`. For local work, run the mock backend described in [backend/mock/README.md](backend/mock/README.md).
- `--chat off` builds the site without the assistant.

## Proposing an article

1. Fork the repository and create a branch named after the slug, for example `article/apple-pcc-research-environment`.
2. Create `content/articles/<slug>/en.md` and `content/articles/<slug>/zh.md`. Slugs are lowercase ASCII words joined by hyphens. [CONTENT_GUIDE.md](CONTENT_GUIDE.md) defines the front matter, the Markdown subset, the callouts and the editorial rules. Put your name in `author` in `en.md`: every article names the person who wrote it or, for an article that the site's software drafted, its automated byline, and the build stops on one that names neither ([Bylines](CONTENT_GUIDE.md#bylines)). A news brief also has `content/articles/<slug>/illustration.json`, which describes its lead image: usually a photo from a source whose license allows reuse, with its credit, license and source page, or else a drawn illustration, with alt text and a caption in both languages ([CONTENT_GUIDE.md](CONTENT_GUIDE.md#lead-images)). An article of another kind may have one too.
3. Set `published` to the date you expect the article to appear. An editor updates it at merge if needed. While the article is in review, `draft: true` keeps it out of the build, and `python3 build.py --mode preview --drafts` builds a preview that includes it. A draft may still lack its `illustration.json`.
4. Run the checks:

   ```bash
   python3 tools/photos.py --write <slug> --source <file> --focus <point> --meta <json>   # a lead photo: crops and grades it into static/media/ and records its files in illustration.json
   python3 tools/photos.py --check
   python3 -m unittest discover -s tests -t .
   python3 tools/lint_content.py <slug>
   python3 build.py --mode preview && python3 tools/check_links.py dist-preview
   ```

   Make a photo's files with `tools/photos.py`, following [Photos](CONTENT_GUIDE.md#photos), and never edit them, or the `file`, `width`, `height`, `sha256`, `variants` and `edits` fields of the spec, by hand: the build checks every file against its digest. `python3 tools/photos.py --draft /tmp/vp-photo <slug> --source <file> --focus <point> --meta <json>` makes the files outside the repository so that you can look at them first; both commands need Google Chrome. A drawn illustration comes from `python3 tools/illustrate.py --write <slug>` instead ([Adding or changing an illustration](tools/scene/README.md#adding-or-changing-an-illustration)), and CI draws every illustration again and fails on any difference. The build stops with `content error:` when an article breaks a structural rule, such as an unknown topic id or a citation without a matching source. The linter only prints warnings. If any remain, explain them in the pull request.
5. Open a pull request and complete its checklist. CI runs the unit tests, which check every lead photo against its spec, draws any lead illustrations again, builds the site, checks its internal links and manifest, and lints the articles you changed. To review the pages, download the preview build, which the CI run attaches as the `site-preview` artifact, and serve it with `python3 -m http.server`.
6. Review happens in two passes: an editor checks every claim against its source, then a Chinese-language editor reviews `zh.md`. Requests for changes are normal.
7. A maintainer merges with a squash commit. The deploy workflow then publishes the site and records the commit in `/build.json`.

**Both editions.** A pull request that adds or changes an article must leave it with both `en.md` and `zh.md`. If the Chinese edition will follow in a separate pull request, ask an editor to apply the `en-only` label, which lets CI pass without `zh.md`.

**What CI blocks.** For each article a pull request changes, CI fails when:

- the folder name is not a valid slug;
- the article has no `zh.md` and the pull request does not carry the `en-only` label;
- a news brief lacks a `:::analysis` or `:::checked` callout;
- a citation points past the end of `sources`, or a listed source is never cited;
- the Chinese edition's citations differ from the English, or it is missing a callout the English has.

Any `content error:` from the build fails CI, whatever the pull request changes. A news brief without its `illustration.json` is one while `content/site.json` lists `news` under `lead_image_kinds`. So is a photo or a copy of it that is missing or does not match its digest, a photo license outside the allowed list, and an illustration that does not match its `svg_sha256` or breaks the rules for an illustration's SVG. CI also fails when a file in `static/media/` belongs to no spec (`python3 tools/photos.py --check`, which the unit tests run) and when an illustration differs from a fresh draw (`python3 tools/illustrate.py --check`). Other linter findings, such as word counts, headline case, style phrases and Chinese spacing, appear as warnings for the reviewer.

## Corrections

Confirmed errors are corrected in the open. To fix a published article:

1. Edit the sentence in `en.md` and, if affected, in `zh.md`.
2. Set `updated:` in `en.md` to the date of the fix. `zh.md` inherits it.
3. Add a `changes:` entry to `en.md` and a translated entry to `zh.md`, because the Chinese file does not inherit this field. Each entry is `YYYY-MM-DD | what changed`:

   ```yaml
   changes:
     - 2026-10-21 | Corrected the date of the announcement from 14 to 15 October.
   ```

   The article then lists the note, with its date, under "Corrections and updates".
4. Start the commit title with `correction(<slug>):`, for example `correction(apple-pcc-google-cloud): fix announcement date`. `git log --grep '^correction'` then lists every correction.

Typos and broken links do not need a `changes:` entry.

Any edit to `en.md` or `zh.md` changes that file's source digest, which the article's verification record and the site manifest show. This is expected. The previous text stays in the repository history, and each deployed build records its commit, so anyone can see what a page said before the correction.

## Resources and the glossary

Add resource entries to `content/resources.json` and glossary terms to `content/glossary.json` in the formats given in [CONTENT_GUIDE.md](CONTENT_GUIDE.md#data-files). Write the `note` as one neutral sentence in each language. Leave out `verified_on`: the editor who opens and checks the link sets it. If you are an author or maintainer of a resource, say so in the pull request, and its listing will identify that connection.

## Code changes

- Keep the generator dependency-free: Python 3.12 standard library only. The mock backend in `backend/mock/` must stay standard-library only and run on Python 3.9 or later; CI runs its tests on both versions.
- Keep the build deterministic. Two builds of the same commit must produce identical files, and CI checks this. Do not write the current time into the output, and seed any randomness from content.
- The manifest format and its canonical serialization are part of the public verification method (`tools/verify_manifest.py`). Changing them breaks verification of earlier builds, so open an issue first.
- `api/chat-v1.md` and `api/chat-v1.schema.json` are the contract between the Ask widget and any backend. Change the widget, the schema, the fixtures in `api/fixtures/` and the mock backend in the same pull request, and say whether the change is compatible with existing backends.
- The Ask widget must not report more than the browser has checked. A server's claims are shown as "reported"; never add a check mark or a "verified" state that the browser did not compute.
- A change in behavior needs new or updated tests, in `tests/` for the generator and the widget build or in `backend/mock/` for the mock backend. Run the unit tests and a preview build before opening the pull request.
- Visual changes follow [DESIGN.md](DESIGN.md). Attach before and after screenshots at desktop and phone widths, in light and dark themes.

## Commits and sign-off

Sign off each commit under the [Developer Certificate of Origin](https://developercertificate.org/) (DCO). The sign-off certifies that you wrote the contribution or otherwise have the right to submit it.

```bash
git commit -s -m "content: add brief on the NIST agent standards initiative"
```

This adds a `Signed-off-by:` line with your name and email. Commits made in the GitHub web editor can include the sign-off automatically.

Commit titles start with an area: `content:`, `correction(<slug>):`, `translation:`, `data:`, `build:`, `style:`, `tools:`, `chat:`, `api:`, `backend:`, `ci:` or `docs:`.

## AI tools

You may use AI tools to search, draft or translate. The site's own articles are drafted by software built on Anthropic's Claude models and appear under the automated bylines verifiable.pro Wire and verifiable.pro Research, each with an "Automated" tag (see the [About page](https://verifiable.pro/about/#ai)). Say in the pull request which tools you used and for what. You remain responsible for every claim: open each cited source and confirm that it supports the sentence that cites it. An article you write with such help still names you as its `author`; the `agent` field is only for the site's automated bylines, listed under `agents` in `content/site.json`.

## Licensing

The repository has no LICENSE file yet, so no license to reuse its code, text, data or illustrations is granted at present. The maintainer will choose the licenses, add the LICENSE files and update this section.

Until then, by opening a pull request you agree that your contribution may be published on verifiable.pro and released under the licenses the maintainer later chooses for the part of the repository it belongs to. If you cannot agree to that, say so in the pull request before it is merged. Quoted material and linked sources remain under their owners' terms, and each lead photo keeps the license that its spec and credit line name.

## Conduct

Be precise and courteous. Critique claims and evidence, not people. The maintainer may close issues or pull requests that are abusive, promotional or off topic.
