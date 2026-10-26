# Guide for coding agents

verifiable.pro is a bilingual (English and Simplified Chinese) editorial site about verifiable AI systems. This repository holds its content, a static-site generator written in Python with no third-party dependencies, the styles and scripts, and the tests. [README.md](README.md) explains the project for people, [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) details the build and its tools, and this file says how to change it safely.

## Repository map

| Path | Contents |
| --- | --- |
| `build.py` | Build entry point. `--mode prod` (the default, root-absolute links, into `public/`), `preview` (relative links) and `artifact` (preview with the English home page as a fragment) |
| `indexnow.json` | The IndexNow key and host. The host must equal `base_url` in `content/site.json`, and every build publishes the key as `/<key>.txt` |
| `sitegen/` | The generator: `content.py` loads and checks the content, `md.py` renders the Markdown subset, `render.py` holds the page templates, `discover.py` writes robots.txt, llms.txt, llms-full.txt, the JSON Feeds, the web app manifests, the structured data and the social tags, `logos.py` and `templates/` serve the home page hero |
| `content/` | Articles (`articles/<slug>/en.md`, `zh.md`, and `illustration.json`, the article's lead image: a photo's files, credit, license and texts, or an illustration's scene and texts), pages (`pages/<name>.<lang>.md`), data files (`topics.json`, `resources.json`, `glossary.json`, `tee.json`, `tiers.json`), interface strings (`strings.json`) and site settings (`site.json`) |
| `static/` | Stylesheets, scripts, logo files, the social cards (`og/`), the icons (`icons/`) and the lead images (`media/`), published under `/assets/` |
| `tools/` | Link, accessibility and manifest checkers, the content linter, screenshot and layout tools (`shoot.py`, `cdp.mjs`), `og_images.py` for the social cards and icons, `hero/` for the hero's generated drawings, `photos.py` for the lead photos (crop, grade, copies and `--check`), `illustrate.py` with `scene/` (its props, palette and guide, `scene/README.md`) for the lead illustrations, and `indexnow.py`, which the deploy workflow runs to tell IndexNow which pages changed (`--dry-run` with `--baseline-site-dir` previews it, as [docs/MAINTAINING.md](docs/MAINTAINING.md#discoverability) shows) |
| `tests/` | `unittest` suites: `test_sitegen.py` (generator, templates, hero), `test_hardening.py` (edge cases), `test_discoverability.py` (robots.txt, llms.txt, feeds, structured data, cards), `test_photos.py` (the lead photos: crops, the grade, metadata, photo specs, their copies and edits, and `--check` of every committed photo), `test_illustrate.py` (the lead illustrations' generator: determinism, validation, composition and colour rules, and `--check` of every committed picture), `test_indexnow.py` (the IndexNow notifier: the pages it picks, their fingerprints, its state and its requests, without the network) |
| `api/`, `backend/` | The site assistant's API contract and its mock backend |
| `docs/` | The maintainer handbook and the assistant's architecture |

## Commands

Run them from the repository root. CI uses Python 3.12; the generator also runs on 3.9. Nothing needs installing.

```bash
python3 build.py --mode preview --out /tmp/vp-preview   # relative links, for local viewing
python3 -m http.server 8000 --directory /tmp/vp-preview  # then open http://localhost:8000/
python3 build.py --out /tmp/vp-public                    # the production build that deploy.yml publishes
python3 -m unittest discover -s tests -t .              # every test, in about ten seconds
python3 tools/check_links.py /tmp/vp-preview            # internal links and anchors (preview or artifact builds)
python3 tools/check_a11y.py /tmp/vp-preview             # landmarks, headings, ids and accessible names
python3 tools/verify_manifest.py /tmp/vp-public         # recompute every source digest
python3 tools/lint_content.py <slug>                    # editorial warnings for one article, or all without a slug
python3 tools/photos.py --check                         # every lead photo and its copies match their spec; no stray media
python3 tools/illustrate.py --check                     # every lead illustration matches a fresh draw from its spec
```

Build outside the repository, or into its ignored `public/` or `dist-*/` folders; the build empties its output folder first and refuses the repository's own source folders. `tools/cdp.mjs` checks layouts and the hero in headless Chrome and needs Node.js 22 or later (see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#checks-before-publishing)).

## Where the rules live

- [CONTENT_GUIDE.md](CONTENT_GUIDE.md): front matter, the Markdown subset, editorial and wording rules, the Chinese edition, the lead images (the photos' sources, licenses, captions and grade, and the illustrations), the data file formats and `site.json`.
- [DESIGN.md](DESIGN.md): the design system, the home page hero and the logo rules.
- [tools/scene/README.md](tools/scene/README.md): the lead illustrations' generator, its scene format and props, and the steps to add or change a picture ([Adding or changing an illustration](tools/scene/README.md#adding-or-changing-an-illustration)).
- [CONTRIBUTING.md](CONTRIBUTING.md): issues, pull requests, what CI blocks and how corrections work.
- [docs/MAINTAINING.md](docs/MAINTAINING.md): GitHub settings, deployment, the published build records and discoverability.

The build stops with `content error:` on a structural problem, such as an unknown topic id or a citation without a source. Every source file is hashed into `/manifest.json`, so change an article only to change its content: a correction sets `updated` and adds a dated `changes` entry in both editions, and a metadata-only edit says so in its commit message.

## Files never to edit by hand

- Build output (`public/`, `dist/`, `dist-*/`, `_site*/`) is ignored by git; `manifest.json`, the Atom and JSON Feeds, `search-index.json`, `sitemap.xml`, `robots.txt`, `llms.txt`, `llms-full.txt`, `site.webmanifest` and the IndexNow key file (`<key>.txt`) exist only there, generated from the content and `indexnow.json`.
- `static/og/*.png`, `static/og/cards.json` and `static/icons/*.png` come from `python3 tools/og_images.py`, which needs Google Chrome and the network (for Google Fonts). Redraw them after changing a topic's name, the tagline, the home page kicker, the colours or the mark; `python3 tools/og_images.py --check` reports cards whose words no longer match the content, and the build warns about them too.
- In `api/fixtures/`, the mock's responses come from `python3 backend/mock/make_fixtures.py`. The two request fixtures carry the manifest digest and passages of a production build: after changing an article, a page, a data file or a lead image's spec or picture, run `python3 backend/mock/refresh_requests.py --write` (it needs Node.js), then `make_fixtures.py` (see `backend/mock/README.md`).
- A lead photo's files in `static/media/` (`<slug>.webp`, `<slug>-800.webp`, `<slug>-400.webp` and `<slug>-og.jpg`) and the `file`, `width`, `height`, `sha256`, `variants` and `edits` fields of its `illustration.json` come from `python3 tools/photos.py --write <slug> --source <file> --focus <...> --meta <json>`, which crops and grades the source in headless Chrome and deletes the article's `static/media/<slug>.svg`. Edit the alt text, caption, credit or source fields in place (the build checks them; `--write` without `--meta` keeps them), and make the files again rather than editing them. The build stops when a photo or a copy is missing or differs from its digest, type or size, and the unit tests run `python3 tools/photos.py --check`, which also fails on a file in `static/media/` that no spec names ([CONTENT_GUIDE.md](CONTENT_GUIDE.md#photos)).
- `static/media/*.svg` and the `svg_sha256` field of each `content/articles/<slug>/illustration.json` come from `python3 tools/illustrate.py --write`; edit the spec's scene, alt text or caption, then redraw, following [Adding or changing an illustration](tools/scene/README.md#adding-or-changing-an-illustration). The build stops when a picture is missing, its digest differs or it breaks the rules for an illustration's SVG, and the unit tests and CI run `python3 tools/illustrate.py --check`, which draws every picture again ([CONTENT_GUIDE.md](CONTENT_GUIDE.md#lead-images)).
- `tools/scene/catalog.svg` comes from `python3 tools/illustrate.py --catalog tools/scene/catalog.svg`, `tools/scene/figure.json` from `python3 tools/scene/figure.py --write`, and the props reference in `tools/scene/README.md` (from "### Primitives" up to "## Materials") from `python3 tools/illustrate.py --props-md`; the unit tests fail while any of them is stale.
- In `sitegen/templates/hero-scene.svg`, the person comes from `python3 tools/hero/person.py --write` and the data path from `python3 tools/hero/flow.py --write`; the unit tests run both with `--check`. The lead illustrations' person is traced from the same figure, so after `tools/hero/person.py --write` also run `python3 tools/scene/figure.py --write` and `python3 tools/illustrate.py --write`.

## How to check a change

1. Run the unit tests.
2. Build a preview and run `tools/check_links.py` and `tools/check_a11y.py` on it.
3. Build production twice into two folders and compare them with `diff -r`: CI requires byte-identical output.
4. For content, run `tools/lint_content.py` on the articles you touched; for a lead photo, run `python3 tools/photos.py --check` and look at the files (`--draft DIR` makes them without touching the repository); for a lead illustration, run `python3 tools/illustrate.py --check` and look at a draft (`--spec … --png`); for layout, take screenshots with `tools/cdp.mjs shots` or `tools/shoot.py`.

Text written for readers follows the editorial rules in CONTENT_GUIDE.md: a check *establishes* or *shows* something, attestation never "proves" anything, a vendor's "attested" or "private" is reported as the vendor's claim, and the site never calls a service verified.
