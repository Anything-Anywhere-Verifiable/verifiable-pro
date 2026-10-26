# verifiable.pro

[verifiable.pro](https://verifiable.pro) is an open, bilingual (English and Simplified Chinese) publication on verifiable AI: the evidence that lets people check what an AI service claims, such as which model answered a request or which software handled their data, before they trust it. This repository holds everything that builds the site: the articles and data, a static-site generator written in Python with no third-party dependencies, the styles and scripts, and the tests. Anyone can contribute a story tip, a correction, an article, a translation or a code change. The code is under the [MIT License](LICENSE) and the content under [CC BY 4.0](LICENSE-CONTENT).

## Scope

We believe future AI systems should provide checkable evidence for their claims about privacy, security policies and behavior. verifiable.pro follows the work that can make this possible, starting with trusted execution environments (TEEs) and comparing them with proofs, re-execution, audits and signatures. The Vision page ([`content/pages/vision.en.md`](content/pages/vision.en.md)) holds the full statement and the site's goals.

## What the site publishes

Reporting starts from TEEs, the hardware behind confidential computing, and from remote attestation, the signed record in which a TEE reports the software it loaded. Articles compare that evidence with other ways to check an AI system: verifiable inference with zero-knowledge proofs (zkML), formal verification, AI evaluations and audits, model signing and content credentials (C2PA). The site also follows checks on whether AI governance commitments are kept.

The site publishes four kinds of articles: news briefs, analysis, explainers and practical guides. Every news brief opens with a lead image, usually a photograph whose license allows reuse and whose credit line names its author, license and source. Alongside the articles, the site keeps a hub on TEEs, a map of the verification stack and its trust tiers, a resource library and a glossary. An "Ask" assistant answers questions from the site's own published pages; today it runs entirely in the browser.

## How the site lets readers check its own pages

The site holds its own pages to the standard it reports on. The build hashes the Markdown source of every article and page, and of each data file, with SHA-256 and publishes the digests in `/manifest.json`. Anyone can recompute them from a local build or from the live site:

```bash
python3 tools/verify_manifest.py https://verifiable.pro
```

A clean result shows that the published sources match the recorded build. It does not show that the reporting is correct, so each article ends with a route to check or correct it, and confirmed corrections are listed in the article itself. Search engines, AI answer engines and agents get the same material in forms they can parse: `llms.txt`, the full text as Markdown, Atom and JSON feeds, structured data and a sitemap. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md#how-the-site-verifies-its-own-pages) describes what the manifest covers and every machine-readable file.

## Build and preview the site

You need Python 3.12 or later, the version CI uses. The generator also runs on Python 3.9, such as the `python3` that ships with macOS, but CI does not test it there. Nothing needs installing.

1. Clone the repository. To contribute, fork it first and clone your fork.

   ```bash
   git clone https://github.com/Anything-Anywhere-Verifiable/verifiable-pro.git
   cd verifiable-pro
   ```

2. Build a preview with relative links into `dist-preview/`.

   ```bash
   python3 build.py --mode preview
   ```

   The build prints the page count and the first 16 hex characters of the manifest digest, both of which change with the content:

   ```text
   built 162 pages into /path/to/verifiable-pro/dist-preview (manifest digest e0311417e93ff559)
   ```

3. Serve the preview over HTTP. Search and the assistant load JSON with `fetch`, which browsers refuse for pages opened as `file://`.

   ```bash
   python3 -m http.server 8000 --directory dist-preview
   ```

4. Open <http://localhost:8000/> for the English site and <http://localhost:8000/zh/> for the Chinese site.

After changing content, styles or templates, run step 2 again and reload the page. If your checkout sits in a synced folder such as iCloud Drive, build outside it with `--out /tmp/verifiable-pro-preview` and serve that folder instead. When content breaks a structural rule, such as an unknown topic id or a citation without a matching source, the build prints `content error:` with the file and the problem and exits with status 1.

Run the unit tests before opening a pull request:

```bash
python3 -m unittest discover -s tests -t .
```

The other checks (links, accessibility, content lint, lead images and layout screenshots) and every build option are in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

## Contributing

Contributions are welcome in English or Chinese, and you do not need write access: open an issue, or work from a fork and open a pull request.

| You want to | Start with |
| --- | --- |
| Suggest a development to cover | A **Story tip** issue; a tip that becomes an article credits you in its byline |
| Suggest a paper, standard, tool or dataset | A **Resource suggestion** issue, or a pull request to `content/resources.json` |
| Report an error in a published page | A **Correction request** issue, or a pull request with the fix |
| Write or translate an article | A Story tip issue first, then a pull request following [CONTENT_GUIDE.md](CONTENT_GUIDE.md) |
| Change the generator, styles, tools or the assistant | A pull request with tests |
| Report a security problem | "Report a vulnerability" on the Security tab, not a public issue |

[CONTRIBUTING.md](CONTRIBUTING.md) explains each path, how editors review claims against their sources, what CI checks and the DCO sign-off on each commit. Say in your pull request which AI tools you used, if any; you remain responsible for every claim you submit.

## Repository layout

| Path | Contents |
| --- | --- |
| `content/` | Articles (`articles/<slug>/en.md`, `zh.md`, `illustration.json`), the About and Vision pages, data files (topics and the verification stack, trust tiers, the TEE hub, resources, glossary), interface strings and site settings |
| `build.py`, `sitegen/` | The build entry point and the generator: Markdown renderer, content loader and checks, page templates, machine-readable files and the home page hero |
| `static/` | Stylesheets, scripts, logo files, social cards, icons and lead images, published under `/assets/` |
| `tools/` | Link, accessibility and manifest checkers, the content linter, layout and screenshot tools, and the generators of the social cards, lead photos and lead illustrations |
| `tests/` | `unittest` suites for the generator, templates, machine-readable files, lead images and IndexNow notifier |
| `api/`, `backend/` | The site assistant's API contract and a standard-library mock backend |
| `docs/` | The development guide, the maintainer handbook and the assistant's architecture |
| `.github/` | Issue forms, the pull request template, code owners and the CI, deploy and link-check workflows |

## Documentation

| Document | Read it to |
| --- | --- |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Open an issue or pull request and follow it through review |
| [CONTENT_GUIDE.md](CONTENT_GUIDE.md) | Write an article: front matter, the Markdown subset, editorial and wording rules, the Chinese edition, lead images and data file formats |
| [DESIGN.md](DESIGN.md) | Change the look: design tokens, type, layout, components, the hero and logo usage |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Work on the source: build options, the hero, lead images, checks and layout tools, the manifest, machine-readable files, the site assistant and deployment |
| [docs/MAINTAINING.md](docs/MAINTAINING.md) | Maintain the repository: roles, GitHub settings, publishing to GitHub Pages and the published build records |
| [docs/assistant-architecture.md](docs/assistant-architecture.md) | Understand what GPU confidential computing and attestation can establish for the assistant |
| [AGENTS.md](AGENTS.md) | Point a coding agent at the repository map, commands and rules |

## How to cite

Cite an article by its title, its address (`https://verifiable.pro/articles/<slug>/`, or `/zh/articles/<slug>/` for the Chinese edition), its filing or update date and the date you read it. The article's Markdown source and its digest in the manifest let a reader check that the text has not changed since. To cite the site as a whole, use [CITATION.cff](CITATION.cff), which GitHub offers under "Cite this repository".

## License

The repository has two licenses, so that both the site's code and its reporting can be reused and improved by anyone:

- **Code**: the generator, tools, tests, mock backend, workflows and the stylesheets and scripts in `static/` are under the [MIT License](LICENSE).
- **Content**: the articles, pages and data files in `content/`, the drawn illustrations, social cards, icons and logo files, and the documentation are under the [Creative Commons Attribution 4.0 International License](LICENSE-CONTENT) (CC BY 4.0). Credit verifiable.pro, link the page you used and say whether you changed it.

Contributions are released under the license that covers the files they change, and contributors keep the copyright in their work ([CONTRIBUTING.md](CONTRIBUTING.md#licensing)). Neither license covers material the site does not own. Quoted material and linked sources stay under their owners' terms, and each lead photo keeps the license its credit line names. The vendor marks in the hero are trademarks of their owners, and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) holds the notices for their path data. The licenses grant no trademark rights in the verifiable.pro name or logo.

The public repository was previously `sept-usc/verifiable-pro`, whose addresses GitHub redirects. It starts from one source snapshot and does not include the earlier private history.
