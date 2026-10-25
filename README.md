# verifiable.pro

verifiable.pro is a bilingual (English and Simplified Chinese) editorial site about verifiable AI: the evidence that lets someone other than an AI provider check a claim about an AI system, such as which model answered a request or which software handled it. Its reporting starts from trusted execution environments (TEEs), the hardware behind confidential computing, and from remote attestation, the signed record in which a TEE reports the software it loaded. It compares that evidence with other ways to check an AI system. These include verifiable inference with zero-knowledge proofs (zkML), formal verification, AI evaluations and audits, model signing and content credentials (C2PA). The site also follows checks on whether AI governance commitments are kept. Alongside news briefs, analysis, explainers and practical guides, the site keeps a hub on TEEs, a map of the verification stack and its trust tiers, a resource library and a glossary.

The site holds its own pages to the standard it reports on. The Markdown source of every article and page is hashed at build time, the digests are published in a manifest that anyone can recompute, and each article ends with a route to check or correct it. Search engines, AI answer engines and agents get the same material in forms they can parse: an `llms.txt` guide, the full text as Markdown, feeds, structured data and a sitemap (see [Machine-readable files](#machine-readable-files)).

The public repository, `sept-usc/verifiable-pro`, starts with one initial source snapshot; it does not include the earlier private history. It contains the content, a small static-site generator written in Python with no third-party dependencies, the stylesheets and the logo files. It also holds the site assistant: a browser widget that answers questions from the site's own published pages, the API contract for the backend it will use later, and a mock of that backend. A build produces plain HTML, CSS and JavaScript that any static host can serve. Coding agents start with [AGENTS.md](AGENTS.md).

## Scope

We believe future AI systems should provide checkable evidence for their claims about privacy, security policies and behavior. verifiable.pro follows the work that can make this possible, starting with trusted execution environments (TEEs) and comparing them with proofs, re-execution, audits and signatures. The Vision page ([`content/pages/vision.en.md`](content/pages/vision.en.md)) holds the full statement and the site's goals.

## Browse the site locally

You need Python 3.12 or later, the version CI uses. The generator currently also runs on Python 3.9, such as the `python3` that ships with macOS, but CI does not test it there. Nothing needs installing.

1. Clone the public repository.

   ```bash
   git clone https://github.com/sept-usc/verifiable-pro.git
   cd verifiable-pro
   ```

2. Build a preview. It uses relative links and is written into `dist-preview/`.

   ```bash
   python3 build.py --mode preview
   ```

3. Serve the preview over HTTP.

   ```bash
   python3 -m http.server 8000 --directory dist-preview
   ```

4. Open <http://localhost:8000/> for the English site and <http://localhost:8000/zh/> for the Chinese site. Press Ctrl+C in the terminal to stop the server.

After you change content, styles or templates, run step 2 again and reload the page; the server can keep running. If port 8000 is taken, use another number in step 3 and in the address. The pages also open from the file system, but search and the site assistant load JSON with `fetch`, which browsers refuse for `file://` pages.

If your copy of the repository sits in a synced folder such as iCloud Drive, write the preview outside it, so the build output is not copied to your other devices:

```bash
python3 build.py --mode preview --out /tmp/verifiable-pro-preview
python3 -m http.server 8000 --directory /tmp/verifiable-pro-preview
```

The build prints the page count and the first 16 hex characters of the manifest digest. Both change with the content:

```text
built 138 pages into /path/to/verifiable-pro/dist-preview (manifest digest c7009174e213d4de)
```

When content breaks a structural rule, such as an unknown topic id or a citation without a matching source, the build prints `content error:` with the file and the problem and exits with status 1.

Run the unit tests before opening a pull request:

```bash
python3 -m unittest discover -s tests -t .
```

## Build options

`python3 build.py` without options makes the production build: root-absolute links for a site served at the root of its domain, written into `public/` together with a `CNAME` file. The options change the link style, the output folder and the assistant's mode:

| Option | Effect |
| --- | --- |
| `--mode preview` | Relative links, so the pages work from any folder or subpath. Writes into `dist-preview/`. |
| `--mode artifact` | Relative links as in preview, but the English home page is written as head elements and page markup without the `<!doctype>`, `<html>`, `<head>` and `<body>` tags, for a host that supplies the page frame. Every page carries `claude:viewport-fit-sides`, a hint for the Claude artifact viewer that the other modes leave out. Writes into `dist-artifact/`. |
| `--out DIR` | Output folder instead of `public/` or `dist-<mode>/` in the repository root. A relative `DIR` is resolved from the current directory. |
| `--drafts` | Include articles marked `draft: true`. |
| `--css FILE` | Publish `FILE` as `assets/site.css` instead of `static/site.css`, for trying a stylesheet. |
| `--mark FILE` | Inline another 48×48 mark in the header and footer instead of `static/mark.svg`. Its shapes need the classes `mark-bg`, `mark-fg-stroke` and `mark-fg`. |
| `--chat MODE` | The assistant's mode for this build: `off`, `demo` or `live` (see [Site assistant](#site-assistant)). |
| `--chat-api URL` | The backend for `--chat live`. |

A production build also prints a warning for each placeholder the site owner still has to fill in, in the About and Vision pages (see [Before launch](#before-launch)). Every build warns about a social card whose words no longer match the content, and stops when a card or an icon is missing (see [Social cards and icons](#social-cards-and-icons)).

The build empties the output folder before writing. It therefore refuses the repository itself, any folder above it, your home folder, the source folders and anything inside them, and a non-empty folder that has neither an `index.html` nor a `manifest.json`.

Each build writes the English site at `/` and the Chinese site at `/zh/`; a Chinese article page exists only for articles with a `zh.md`. The build also writes, for each language, an Atom feed and a JSON Feed of the 20 newest articles, a search index, the full text as Markdown (`llms-full.txt`), a web app manifest and a 404 page. For the whole site it writes `llms.txt`, a sitemap with language alternates and last-change dates, `robots.txt`, the published Markdown sources and data files, and `manifest.json`. [Machine-readable files](#machine-readable-files) describes them.

## The home page hero

The hero in the home page's first band is the site's one inline drawing (articles open on lead images, which are separate files; see [Lead images](#lead-images)): the seven layers of an AI system drawn as a stack of plates, from an accelerator board up to a sealed agreement, with an indigo line for the chain of evidence, and you, the reader, outside the stack: a person seen from behind, talking with the system on a phone that shows the chain's ring, from which a dotted path carries your data through every layer, T1 to T7, and back. The chain is drawn as each layer's binding to the layer below holds today (`bind.status` in `content/topics.json`): solid where it is in use, dashed where it is emerging and broken where there is none, and a legend beside the board, its samples of the line in the chain's indigo, says how far it holds. The build inlines the SVG scene in `sitegen/templates/hero-scene.svg`, with its title and description in the page language (`hero_scene_title` and `hero_scene_desc` in `content/strings.json`, and `hero_scene_desc_live`, the sentences on the gray and the moving data that `hero.js` adds to the description once it runs); `hero_scene_check` in `build.py` stops the build when the scene loses a part the page addresses, such as a plate's hit area or the person, or when the person carries a transform. `tools/hero/person.py` draws the person and bakes its size and place into the path data: `--write` updates the scene, and `--check`, which the unit tests run, compares the scene with what it draws. Beside each plate sits a label: the layer's icon, its code and short name ("T1 Hardware") linked to the Stack page, and examples of who works at that layer, as vendor marks or names, from the `hero` block of each layer in `content/topics.json`; `sitegen/templates/hero-anchors.json` says where each leader line meets its plate. Each label holds a layer card with what the Stack page's table says about the layer and who outside the provider checks its claim (`checkers`). Pointing at a plate or at a label's name checks that layer at once, and its card shows beside the scene once the pointer settles, so a sweep down the names checks each layer in turn with no card in its way. The card stays while the pointer moves onto it, and it closes shortly after the pointer has left the card, the name and the plate. The examples under a name open nothing: pointing at a vendor mark only shows the brand's name. Focusing a label, or tapping a plate or a layer's chevron on a touch screen, opens the card at once, and the page scrolls a tapped card wholly into view below the sticky header; on phones a chevron opens it in the list, where only T1 and T2, the layers that the reader's own device can check, show their "Who checks" line at rest. The stack table itself is on the Stack page only. `static/hero.js`, which only the two home pages load, opens the cards and counts the layers the reader has opened: the person is drawn in gray and regains colour with each layer, and once all seven are checked (or the reader presses "Check all layers"), small packets of your data travel the path and a pulse runs up the evidence line, with a pause control. Without JavaScript the scene is a still picture in full colour. `tools/hero/flow.py` computes the data's route from the scene's geometry and writes it and the loop into the scene, with the same `--write` and `--check`. The scene is a conceptual picture made for this site; it depicts no real person, product, system or event and carries no evidence, and the logos are examples, not endorsements. [DESIGN.md](DESIGN.md#the-hero) describes it.

The vendor marks are path data vendored in `sitegen/logos.py`: from [Simple Icons](https://simpleicons.org) (CC0 1.0), and, for the marks Simple Icons does not carry (Azure, DeepSeek, Qwen, Cursor, Manus, MCP, vLLM, Claude Code, Codex, Pi and Meta AI), from [Lobe Icons](https://github.com/lobehub/lobe-icons) (`@lobehub/icons-static-svg` 1.98.0, MIT). The marks are trademarks of their owners. [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) holds the Lobe Icons copyright and permission notice, which must travel with those marks, and the credit for Simple Icons.

## Lead images

Every news brief opens with a lead image, usually a real photograph, and other articles may have one too. The home page, Latest, the topic pages and the TEE hub show a copy beside the story. Photos come from Wikimedia Commons, US government sites, Unsplash and Pexels, under licenses that allow reuse, and the credit line under each one names its author, its license and its source. `python3 tools/photos.py --write <slug> --source <file> --focus <x,y> --meta <json>` crops a photo to 3:2 in headless Chrome and gives it the site's one gentle colour grade. It writes `static/media/<slug>.webp` (1600 × 1067), 800- and 400-pixel copies for lists and a 1200 × 630 copy for link previews, all without metadata, and records their sizes and digests, the crop and the photo's texts in `content/articles/<slug>/illustration.json`; `python3 tools/photos.py --check`, which the unit tests and CI run, checks every photo without a browser. An article may instead have a conceptual illustration in the hero's style, which `python3 tools/illustrate.py --write <slug>` draws from a scene description in the same file into `static/media/<slug>.svg` ([Adding or changing an illustration](tools/scene/README.md#adding-or-changing-an-illustration)). The build stops when a picture is missing or no longer matches its digest, publishes each spec beside its article's sources and lists the spec and every picture in the manifest. `content/site.json` `"lead_image_kinds"` lists the article kinds that must have one (`["news"]`). The format, the sources and licenses and the editorial rules are in [CONTENT_GUIDE.md](CONTENT_GUIDE.md#lead-images), the illustration generator's guide is [tools/scene/README.md](tools/scene/README.md), and the photos' design and where the pictures appear are in [DESIGN.md](DESIGN.md#photos-as-lead-images-24-october-2026).

## Repository layout

| Path | Contents |
| --- | --- |
| `build.py` | Build entry point |
| `sitegen/` | The generator: Markdown renderer (`md.py`), content loader (`content.py`), page templates (`render.py`), the machine-readable files, structured data and social tags (`discover.py`), the hero scene and its leader anchors (`templates/hero-scene.svg`, `templates/hero-anchors.json`), the hero's layer and person icons and vendor marks (`logos.py`) and generated illustrations (`art.py`, which the pages keep off and the social cards use) |
| `content/` | Articles (`articles/<slug>/en.md`, `zh.md`, and the lead image's `illustration.json`), pages (About and Vision), topics and the verification stack (`topics.json`), the trust tiers (`tiers.json`), the TEE hub (`tee.json`), resources, glossary, interface strings and site settings |
| `static/` | Stylesheets and scripts (`site.css`, `site.js`, `hero.js`, and `chat.css`, `chat.js` for the site assistant), logo and favicon files, the social cards (`og/`), the icons (`icons/`) and the lead images (`media/`: photos made by `tools/photos.py` and drawings by `tools/illustrate.py`), copied to `/assets/` |
| `tools/` | Link checker, accessibility checker, content linter, manifest verifier, screenshot tools, the generator of the social cards and icons (`og_images.py`), the generator of the hero's person (`tools/hero/`), the lead photos' crop, grade and checks (`photos.py`) and the generator of the lead illustrations (`illustrate.py` and `scene/`) |
| `tests/` | Unit and regression tests for the generator, the page templates, the site assistant's markup and the machine-readable files (`test_discoverability.py`), the lead photos (`test_photos.py`, which also checks every committed photo) and the lead illustrations' generator (`test_illustrate.py`, which also redraws every committed picture) |
| `api/` | The site assistant's API contract (`chat-v1.md`), its JSON Schema and example messages |
| `backend/` | Backend plan by phase, and a standard-library mock server with its tests (`backend/mock/`) |
| `docs/` | The maintainer handbook and the site assistant's architecture |
| `.github/` | Issue forms, the pull request template, code owners and the CI, deploy and link-check workflows |
| `CONTENT_GUIDE.md` | Front matter, Markdown subset, editorial rules and data-file formats for writers |
| `DESIGN.md` | Design system: tokens, type, layout, components and logo usage |
| `CONTRIBUTING.md` | How to contribute, how pull requests are reviewed, and what CI checks |
| `AGENTS.md` | A short guide for coding agents: the repository map, commands, rules and generated files |
| `CLAUDE.md` | Imports `AGENTS.md` for Claude Code, which reads `CLAUDE.md` |
| `CITATION.cff` | Citation metadata for the site as a whole |
| `THIRD_PARTY_NOTICES.md` | The license notice for the Lobe Icons marks in the hero and the credit for Simple Icons |

Build output (`public/`, `dist/`, `dist-*/`, `_site*/`) and local working folders such as `.build/`, `design/` and `research/` are ignored by git.

## Writing content

Articles are Markdown files with front matter. A news brief records two dates: `event_date`, when the primary source announced the development (shown as "Source date"), and `published`, when the brief appeared on the site (shown as "Filed"). Sources are listed in the front matter and cited in the text with `[^1]`. Callouts separate reported facts from interpretation: `:::analysis` holds the site's reading of a story and `:::checked` records which sources were opened and when. Front matter also places each story on the verification stack (`layers`) and gives each guide the line Learn shows as "You need" (`needs`). The TEE hub, the trust tiers and the stack's TEE lines are data: `content/tee.json`, `content/tiers.json` and the `stack` in `content/topics.json`. The full rules, including the wording rules for checks and trust, the Chinese typesetting conventions and the formats of the data files, are in [CONTENT_GUIDE.md](CONTENT_GUIDE.md).

Six checks help before publishing:

```bash
python3 tools/lint_content.py <slug>
python3 build.py --mode preview && python3 tools/check_links.py dist-preview
python3 tools/check_a11y.py dist-preview
python3 tools/photos.py --check
python3 tools/illustrate.py --check
python3 -m unittest discover -s tests -t .
```

- `tools/lint_content.py` prints editorial warnings for the named articles, or for every article when no slug is given: word counts outside the expected range, missing callouts, uncited sources, headline case, phrases the style guide avoids, a missing or mismatched Chinese edition, and Chinese spacing and punctuation. It always exits with status 0; CI turns the structural findings listed in [CONTRIBUTING.md](CONTRIBUTING.md#proposing-an-article) into errors.
- `tools/check_links.py` resolves every internal link and anchor in a preview or artifact build. It reports root-absolute links as problems, so it cannot check a production build.
- `tools/check_a11y.py` parses every page of a build for landmarks, the heading outline, unique ids and their references, and accessible names, and exits with status 1 when it finds a problem; `--warnings` adds best-practice notes.
- `tools/photos.py --check` checks every lead photo without a browser and exits with status 1 when a photo or a copy is missing, differs from its digest, is not the size or name that `tools/photos.py` gives it, carries metadata, or has a license outside the content guide's list, or when `static/media/` holds a file that no spec names; it warns about a file over its size budget or a source outside the allowed sites, and the unit tests and CI run it too.
- `tools/illustrate.py --check` draws every lead illustration again from its spec and exits with status 1 when a committed picture or its `svg_sha256` differs, when a spec breaks the composition or colour rules, or when `static/media/` holds an SVG without a spec; the unit tests run it too.
- Some unit tests build the site into a temporary folder: one fails if phrases retired from the interface (listed in `tests/test_sitegen.py`) reappear in either language, and others check the assistant's markup with `--chat demo`, `--chat live` and `--chat off`.

The layout tools drive headless Google Chrome. `tools/shoot.py` uses the one installed at `/Applications/Google Chrome.app`; `tools/cdp.mjs` uses the browser that the `CHROME` environment variable names, or else Google Chrome where macOS installs it, `google-chrome` or `chromium` on the `PATH` on Linux, or `chrome.exe` under Program Files on Windows, and it needs Node.js 22 or later:

```bash
node tools/cdp.mjs check dist-preview --pages home,article,zh-home,zh-article --widths 360,390,768,1024,1440 --article articles/apple-pcc-google-cloud/index.html
node tools/cdp.mjs shots dist-preview shots --pages home,article --widths 390 --dark home
node tools/cdp.mjs hero dist-preview --widths 1440,1184,1024,768,390 --sizes 1536x864,1366x768,1280x800,1280x720,1024x768,720x450x2 --nojs
python3 tools/shoot.py dist-preview shots
```

`check` reports horizontal overflow for each page and width (`--small` adds text below the 12px floor, `--measure` characters per line), and `shots` writes PNG files (`--full` of the whole page, `--touch` as a touch screen, `--open N` with layer N's card open). `hero` checks the home page hero with real mouse, key and touch input: the person gray until every layer is checked, the count of layers checked and "Check all layers", the data passing T1 to T7 in order, its seven layer labels, its pause control, its suspension off-screen and in a hidden tab, and the still frame under reduced motion, which draws the chain by status. It checks the guard against a script failure: the person is gray in every frame while `hero.js` loads, and in full colour once the page has loaded with `hero.js` blocked or made to throw. From 45em it sweeps the mouse down and up the labels and the plates, which must check every layer in turn and reach each label with no card over it; then it sweeps the names again with a rest on each, after which each card must show clear of the next label, and it rests on the first name before sweeping on. It also checks the layer cards: the examples under the names, vendor marks and names, open and check nothing; each name and each plate opens its layer, with its card on a side where the card fits, or fitted over its own label's head, never over its examples, when neither side has room, below the pause control and within the stage, with the labels it lies over hidden; a path from each name into its card keeps the card open, and a click on the card's link follows it; real Tab and Shift+Tab walk the figure with each focused element and the open card in view; and leaving the stage, Esc, taps and swipes on a touch screen and the chevrons on phones open and close the cards as they should. On touch tablets (1024x768, 768x1024, 1180x820 and 820x1180) and a phone on its side (932x430), or the windows that `--tablets` lists (`none` skips them), a tap on each chevron and plate must leave its card wholly between the sticky header and the window's bottom, by the least scroll. In windows from 1920x1080 down to 1024x768, or those that `--tipsizes` lists, and on phones, the mouse rests on every vendor mark, on a fresh page and after a rest on its layer's name, and every mark's name must show in the tooltip; on a touch tablet and a phone a tap on each mark must give its name, in the tooltip or in the card's Examples line. Below 45em it checks that "Who checks" shows at rest on T1 and T2 only, and at every width that the legend's samples match the chain's indigo in light and dark and are `CanvasText` in forced colours. At one width it also replays behaviour that broke once, such as slow mouse paths from a plate into its card. From 45em it checks the completion too: once the seventh layer is checked, with the mouse left on an empty part of the stage, on the person or on the last label, or with focus on the last name, and at that one width after a tap on a chevron or "Check all layers" with a tapped card open, the person's moment must play and the data must move within 2 seconds while the last card stays open. Each `--widths` width is 900px tall; `--sizes` adds windows of other heights from 720px wide (`1366x768`, or `720x450x2` for a device scale factor of 2) for the cards, the sweeps and the keyboard. Where the intro stands beside the figure and the window is at least 720px tall, it checks that the person's label and the hint are on the first screen. From 1184px it checks that the intro stands beside the figure. `--nojs` adds the page without JavaScript, and `--only` runs only the groups of checks it names, such as `--only finale` (the comment at the top of `tools/cdp.mjs` lists them). `hero` exits with status 1 when a check fails; the full run above takes about an hour, and `hero` alone checks 1440 and 390, the touch tablets and the vendor marks' names. `zoom` writes a crop at a device scale factor (`--scale 2`), in dark with `--dark` and in forced colours with `--forced`. `tools/cdp.mjs` sets the viewport through the Chrome DevTools protocol, so media queries see true phone widths. `tools/shoot.py` sizes the Chrome window instead, and headless Chrome keeps windows at least 500px wide, so its "mobile" shots are laid out at 500px. Both tools use the alphabetically first article unless `--article` names another, and `zh-article` loads that article's Chinese page, so name an article that has a Chinese edition. The `shots/` folder is ignored by git.

## How the site verifies its own pages

The build computes the SHA-256 digest of every article and page source, of the data files `topics.json`, `resources.json`, `glossary.json`, `tee.json` and `tiers.json`, and of each lead image's `illustration.json` and pictures (a photo with its three copies). It publishes the sources next to the pages (`/articles/<slug>/en.md`, `/articles/<slug>/illustration.json`), the data files under `/data/` and the pictures under `/assets/media/`, and lists the digests in `/manifest.json`, together with a digest of the whole list. Each article shows its own digest in the folded verification record at its end; no other page prints a digest. The manifest digest identifies that set of sources: it is the manifest's own `digest` field, and the footer links the manifest. It does not cover the templates, styles, scripts, other images, `strings.json` or `site.json`. Anyone can recompute the digests of a local build or, once the site is deployed, of the live site:

```bash
python3 tools/verify_manifest.py public
python3 tools/verify_manifest.py https://verifiable.pro
```

The script reports whether the manifest digest matches and how many entries it checked, and exits with status 1 if a source is missing or changed. A clean result shows that the published sources match the recorded build. It does not show that the reporting is correct, so corrections are also recorded in the articles themselves.

`sitegen/art.py` can also draw an illustration for each article from the same digests: one of eight topic patterns, chosen by the article's primary topic, with a random number generator seeded by the English source's SHA-256. The site keeps these drawings off its pages (`"illustrations": false` in `content/site.json`); its pictures are the home page hero and the lead images. The social cards that link previews show (see [Social cards and icons](#social-cards-and-icons)) use the same patterns with fixed seeds.

## Machine-readable files

Each build also writes files that search engines, AI answer engines and agents can read without parsing the pages. `sitegen/discover.py` generates them from the same content as the pages, so drafts stay out. A production build writes full addresses into them; preview and artifact builds use relative links, so a local copy works too.

| Address | Contents |
| --- | --- |
| `/llms.txt` | A guide for language models in the [llmstxt.org](https://llmstxt.org/) format: what the site covers, how its pages are checked, and links to the Markdown source of every English article, the topics, the data files, the feeds and the Chinese edition |
| `/llms-full.txt`, `/zh/llms-full.txt` | Every published article and page of one edition as Markdown in one file, each under a header with its address, kind, byline, dates, topics, sources and source digest |
| `/feed.xml`, `/zh/feed.xml` | Atom feeds of the 20 newest articles with their full text and bylines: the person who wrote an article, or the automated byline it appeared under (verifiable.pro Wire or verifiable.pro Research), marked as automated |
| `/feed.json`, `/zh/feed.json` | The same articles in [JSON Feed 1.1](https://www.jsonfeed.org/version/1.1/), each with its numbered sources |
| `/manifest.json` | The SHA-256 digest of every article, page and data source (see [How the site verifies its own pages](#how-the-site-verifies-its-own-pages)) |
| `/articles/<slug>/en.md`, `zh.md`, `/pages/<name>.<lang>.md`, `/data/<name>.json` | The Markdown sources and data files the pages are built from |
| `/search-index.json`, `/zh/search-index.json` | Titles, summaries and addresses of the articles, topics, pages, trust tiers, resources and glossary terms, which the site search and the assistant use |
| `/sitemap.xml` | Every page except the 404 pages and the search pages, with its other edition and the English page as `x-default` where both exist, and the date it last changed where the content records one |
| `/robots.txt` | Open to every crawler, with groups that name search engines, AI search and answer engines, assistants that fetch a page on request, and AI training crawlers; a comment points agents to `/llms.txt` |
| `/site.webmanifest`, `/zh/site.webmanifest` | Web app manifests with the site's name, description, colours and icons |

Each page's head points to these files: an article or page links its Markdown source (`<link rel="alternate" type="text/markdown">`), every page links the feeds of its language and, as llmstxt.org suggests, `/llms.txt` (`rel="describedby"`), and the footer links `llms.txt` too. A page with an edition in the other language names both editions and the English one as `x-default`. Each page also describes itself in structured data (JSON-LD with schema.org types):

| Pages | Structured data |
| --- | --- |
| Home pages | `WebSite`, and `Organization` for the publisher, with its logo, repository and editorial address |
| Articles | `NewsArticle` for news briefs, otherwise `Article`, with the article's card, dates and language, its topics as keywords, its kind as its section, its sources as citations and its other edition as a translation |
| Latest, Learn, the Stack page, the topic pages and Resources | `CollectionPage` with an `ItemList` of what the page lists: Learn starts with the TEE path, and the Stack page lists its topics |
| Glossary | `DefinedTermSet` with a `DefinedTerm` for each term |
| About | `AboutPage` and the publisher's `Organization` |

Every page except the home pages, the search pages and the 404 pages also carries its breadcrumb trail (`BreadcrumbList`); a home page has no trail, and Google accepts none shorter than two items. The search pages list no results without JavaScript and the 404 pages answer any missing address, so these four pages carry `noindex`, with no canonical URL, language alternates or structured data, and stay out of the sitemap, `llms.txt`, the `llms-full.txt` files and the feeds. `robots.txt` still lets crawlers fetch them, so that they read the `noindex`. Every other page carries `max-image-preview:large`, which lets search results show a large preview of its images, such as its social card. A home page's title (`home_title` in `content/strings.json`) starts with the site's name and says what the site covers; the structured data name the site `verifiable.pro`. Every other page's title ends with " | verifiable.pro", unless it names the site already, as About and Vision do. Every article names the person who wrote it (`author`) or, for an article that the site's software drafted, its automated byline (`agent`, from `content/site.json`: verifiable.pro Wire or verifiable.pro Research), and the pages, the feeds and `llms-full.txt` show that byline ([CONTENT_GUIDE.md](CONTENT_GUIDE.md#bylines)). In the structured data the author is that person, or the publication itself for an automated article, since search engines take only a person or an organization as an author. The visible source list retains publisher labels as text. Structured citations omit that optional publisher field because a label can combine authors and venues.

### Social cards and icons

Link previews show a card of 1200 × 630 pixels: one for the site and one for each topic, in each language. A card carries the mark and the wordmark, a kicker and a title from the content (the home page's kicker and tagline, or "Topic" and the topic's name) and a pattern from `sitegen/art.py`: the topic's own, its accent in the topic's hue, or on the site's card the enclave pattern in TEE indigo. An article with a lead photo shows the photo's own 1200 × 630 copy instead, with the photo's alt text, and names it as the image of its structured data with the photo's credit and license; other articles use the card of their first topic. Every page names its card in `og:image`, with the card's size and alt text, and in `twitter:image` with `summary_large_image`, together with `og:locale`; articles add `article:published_time`, `article:modified_time`, `article:section` and an `article:tag` for each topic.

`tools/og_images.py` draws the cards and the icons, the 180-pixel touch icon and the 192- and 512-pixel icons of the web app manifest, from `static/mark.svg` and the site's colours and fonts with headless Google Chrome. It writes the PNG files to `static/og/` and `static/icons/`, which are committed, and `static/og/cards.json`, which records each card's words and alt text. The build needs no browser: it reads only the files' headers and `cards.json`, and it stops with a message that names the file when a card or an icon is missing or has the wrong size. When a topic's name, the tagline or the home page kicker changes, the build warns that a card is out of date. Redraw the cards then:

```bash
python3 tools/og_images.py          # needs Google Chrome, and the network for Google Fonts
python3 tools/og_images.py --check  # compares static/og/cards.json with the content, without a browser
```

The 512-pixel icon is also the logo in the structured data. No page shows a card; they exist for link previews.

## How to cite

Cite an article by its title, its address (`https://verifiable.pro/articles/<slug>/`, or `/zh/articles/<slug>/` for the Chinese edition), its filing or update date, and the date you read it. The article's Markdown source and its digest in the manifest let a reader check that the text has not changed since. To cite the site as a whole, use [CITATION.cff](CITATION.cff), which GitHub offers under "Cite this repository".

## Site assistant

Every page has an "Ask" button (提问 in Chinese) in the header. It opens a panel for questions about the site's coverage; on article pages, an "Ask about this article" box below the verification record opens it with questions about that article. Each answer lists the pages it draws on, so you can open each source and compare. The browser also hashes the sources it fetched and compares them with the manifest, but the panel does not print the digests.

The assistant runs in demo mode today. The browser does all the work: it ranks entries in the site's `search-index.json`, fetches the matching published Markdown sources, checks them against `manifest.json` and assembles an answer from the passages it picked. No language model is involved, and the question is never sent anywhere; the only requests are for the site's own static files. The panel labels these answers as demo answers, and the conversation is kept in the tab's `sessionStorage` until the tab is closed.

In live mode the browser still picks the passages. It then sends the question, the earlier turns and those passages to a backend that implements the [chat API v1](api/chat-v1.md): `GET /v1/meta`, `GET /v1/attestation?nonce=…` and `POST /v1/chat`, which streams the answer as server-sent events. The status strip at the top of the panel shows only what the browser checked. Whatever the service says about itself is shown as "reported", never as verified. Phase 0, the current one, has no encryption to an enclave and no attestation verification in the browser; those steps are planned for the GPU confidential-computing backend described in [docs/assistant-architecture.md](docs/assistant-architecture.md). If the backend fails, the panel offers an explicit "Use demo answers instead" button; it never switches to demo answers on its own.

The assistant is configured in the `chat` block of `content/site.json`:

| Setting | Values | Effect |
| --- | --- | --- |
| `chat.mode` | `demo`, `live`, `off` | `off` builds the site without the assistant's markup, stylesheet and script. A `chat` block without `mode` means `demo`; a `site.json` without the block builds with the assistant off. |
| `chat.api_base` | An `http(s)` URL without query or fragment, for example `https://api.example.org` | The backend for `live` mode, which needs one |
| `chat.launcher` | `header` (default), `float` | `float` replaces the header button with a square tab at the bottom right, hidden while the footer is in view |
| `chat.allow_demo_fallback` | `true` (default), `false` | Whether a failed backend offers the "Use demo answers instead" button |
| `chat.suggestions` | `{"en": [...], "zh": [...]}` | Example questions shown in an empty panel, per language |

`build.py --chat {off,demo,live}` and `--chat-api URL` override `chat.mode` and `chat.api_base` for one build, so a preview can try another mode without editing the settings. The interface text is in `content/strings.json` under the `chat_*` keys, in both languages, and the build stops if one is missing while the assistant is on.

A production build guards the switch away from demo mode. It refuses a `live` backend on plain `http://` unless the host is `localhost`, `127.0.0.1` or `::1`. When `content/site.json` itself sets `live`, the build also stops if the backend is on this machine or if the About pages still describe the assistant as demo-only (the sentences listed in `DEMO_ONLY_CLAIMS` in `build.py`); with `--chat` or `--chat-api` on the command line, these two problems only print warnings. Switching to `live` therefore takes a backend that implements `api/chat-v1.md`, serves HTTPS and allows the origin `https://verifiable.pro`, together with a rewrite of the About page's assistant section in the same change.

### Running the assistant against the mock backend

[`backend/mock/server.py`](backend/mock/server.py) implements the API with the standard library and attests nothing; the panel shows it as a demo backend. Run each command from the repository root, in its own terminal:

```bash
python3 backend/mock/server.py
```

```bash
python3 build.py --mode preview --chat live --chat-api http://127.0.0.1:8787 --out dist-live
```

```bash
python3 -m http.server 8767 --directory dist-live
```

Then open `http://localhost:8767/` and press "Ask". The mock listens on `http://127.0.0.1:8787` and accepts requests from any `localhost` or `127.0.0.1` port; a page opened from `file://` is refused. It quotes the passages the browser sent, with their `[n]` markers. The words `slow`, `error` and `429` in a question make it stream slowly, fail mid-answer or answer with a rate limit, for testing those states. `--openai-base URL --model NAME` sends the question and passages to any OpenAI-compatible endpoint instead, such as a local Ollama or vLLM. Flags and test commands are in [backend/mock/README.md](backend/mock/README.md).

Further reading:

- [api/chat-v1.md](api/chat-v1.md): the contract, with each part marked by the phase that implements it, and [api/chat-v1.schema.json](api/chat-v1.schema.json)
- [backend/README.md](backend/README.md): the backend phases, from this mock to a managed attested provider, a self-hosted confidential GPU and an independent verifier
- [docs/assistant-architecture.md](docs/assistant-architecture.md): what GPU confidential computing and attestation can establish for the assistant, and what they cannot
- The About page's [assistant section](content/pages/about.en.md), which tells readers what the assistant does and does not show

## Deploying

`.github/workflows/deploy.yml` publishes every push to `main` to GitHub Pages. It runs the unit tests, builds with `python build.py --out public`, verifies the manifest, writes `build.json` (the manifest digest and the commit) and `SHA256SUMS` for every published file, attests them with a build provenance attestation, deploys, and then checks the live site against its manifest. The assistant's mode in that build is whatever `content/site.json` sets.

The production build also writes a `CNAME` file containing `verifiable.pro`. GitHub Pages ignores it when a custom Actions workflow deploys; the custom domain is set in the repository's Pages settings instead. The Pages settings, DNS records, HTTPS and rollback steps are in [docs/MAINTAINING.md](docs/MAINTAINING.md#publishing-github-pages-custom-domain-and-dns), and the published build records and how to check them are in [its verifiable publishing section](docs/MAINTAINING.md#verifiable-publishing). `public/` is a complete static site, so another static host can serve it too, as long as the site sits at the root of its domain; for a subpath, build with `--mode preview`.

## Contributing

Story tips, resource suggestions, corrections, articles, translations and code changes are welcome, in English or Chinese. [CONTRIBUTING.md](CONTRIBUTING.md) explains which issue form or pull request each one needs, how pull requests are reviewed, the checks CI runs, and the commit sign-off. Maintainer procedures (repository settings, branch protection, deployment and the publishing records) are in [docs/MAINTAINING.md](docs/MAINTAINING.md).

The repository has no LICENSE file yet, so no reuse license is granted at present. [CONTRIBUTING.md](CONTRIBUTING.md#licensing) states the terms for contributions until the maintainer chooses licenses.

## Before launch

These placeholders need the site owner's decision before launch:

- [ ] **Editorial mailbox.** `contact_email` in `content/site.json` (currently `hello@verifiable.pro`) is shown in the footer, and the same address is written into the Contact section of both About pages. The mailbox and its MX records must exist.
- [x] **Editor details.** About and Vision identify SEPT Lab at USC as maintainer and Mengyuan Li as editor. The footer names the maintainer, links the contributors and credits the editor.
- [x] **Hero description.** `hero_scene_title` and `hero_scene_desc` in `content/strings.json` describe the hero in both languages.
- [ ] **Reuse license.** The Reuse section (`#license`) of both About pages says that no license has been chosen for the site's original text and illustrations. A license can cover only the site's own work: quoted material, other organizations' logos, such as the vendor marks in the hero, and linked sources stay under their owners' terms, as that section says. Each lead photo also keeps the license that its credit line names.
- [ ] **Code license.** The repository has no LICENSE file for the generator, styles and tools.
- [ ] **Search engines.** Verify `verifiable.pro` in Google Search Console and Bing Webmaster Tools, preferably with a DNS TXT record so that no verification tag is added to the pages, and submit `https://verifiable.pro/sitemap.xml` to both.
- [ ] **AI training crawlers.** `robots.txt` names GPTBot, ClaudeBot, Google-Extended, Applebot-Extended, CCBot, Amazonbot and Meta-ExternalAgent with `Allow: /`. Every crawler is allowed already, so this changes nothing in effect, but while no reuse license is chosen the owner should confirm it; [docs/MAINTAINING.md](docs/MAINTAINING.md#discoverability) says how to change that group.
- [ ] **Repository.** Publish this source snapshot as the public `sept-usc/verifiable-pro` repository with one initial commit, set its website to `https://verifiable.pro` and its topics, and configure GitHub Pages as described above.
