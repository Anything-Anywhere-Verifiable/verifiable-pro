# Maintaining verifiable.pro

This handbook is for the maintainer and editors. It covers the repository layout, roles and code owners, the GitHub settings the workflows rely on, publishing to GitHub Pages under verifiable.pro, how article and correction pull requests move through review, the public repository’s fresh start, and the records each deploy publishes so that readers can check the site. Contributor instructions are in [CONTRIBUTING.md](../CONTRIBUTING.md); writing rules are in [CONTENT_GUIDE.md](../CONTENT_GUIDE.md).

## Repository layout

```
verifiable-pro/
├── .github/
│   ├── CODEOWNERS                  who must approve changes to which paths
│   ├── PULL_REQUEST_TEMPLATE.md    editorial and code checklist
│   ├── dependabot.yml              keeps the action SHA pins current
│   ├── ISSUE_TEMPLATE/             config.yml story.yml resource.yml correction.yml bug.yml
│   └── workflows/
│       ├── ci.yml                  pull requests and main: tests, builds, links, manifest, content lint
│       ├── deploy.yml              main: build, attest, publish to GitHub Pages, check the live site, notify IndexNow
│       └── links.yml               weekly external-link check, reported in a link-rot issue
├── api/                            Ask assistant API contract, version 1
│   ├── chat-v1.md                  human-readable contract (phase 0 subset marked)
│   ├── chat-v1.schema.json         JSON Schema for meta, attestation bundle, chat request, stream events
│   └── fixtures/*.json             example messages used by tests and the mock backend
├── backend/
│   ├── README.md                   backend phases 0–3
│   └── mock/                       standard-library mock server (Python 3.9+), its README, tests and fixture scripts
├── content/
│   ├── articles/<slug>/en.md, zh.md, illustration.json (the lead image: a photo's files, credit, license and texts, or an illustration's scene and texts)
│   ├── pages/<name>.en.md, <name>.zh.md (About, Vision and Contributors)
│   └── site.json strings.json topics.json resources.json glossary.json
├── docs/
│   ├── MAINTAINING.md              this file
│   ├── DEVELOPMENT.md              the development guide: build options, hero, lead images, checks, machine-readable files, assistant, deploy
│   └── assistant-architecture.md   how the Ask assistant and its attestation fit together
├── sitegen/                        md.py content.py render.py discover.py logos.py art.py, templates/ (the hero scene and its anchors)
├── static/                         copied to /assets/: site.css site.js hero.js chat.css chat.js, the logo files,
│                                   og/ (social cards and cards.json) and icons/, both drawn by tools/og_images.py,
│                                   and media/ (the lead photos and their copies, made by tools/photos.py, or illustrations, drawn by tools/illustrate.py)
├── tests/                          unit tests for the generator, content, the Ask widget build, the machine-readable files, the lead photos, the illustration generator and the IndexNow notifier
├── tools/                          check_links.py check_a11y.py lint_content.py verify_manifest.py shoot.py cdp.mjs og_images.py, hero/ (draws the hero's person and their data's path),
│                                   photos.py (crops and grades the lead photos), illustrate.py and scene/ (draw the lead illustrations from each illustration.json),
│                                   indexnow.py (tells IndexNow which pages a deploy changed)
├── build.py                        build entry point
├── indexnow.json                   the IndexNow key and host; every build publishes the key as /<key>.txt
├── README.md AGENTS.md CONTRIBUTING.md CONTENT_GUIDE.md DESIGN.md CITATION.cff THIRD_PARTY_NOTICES.md
├── LICENSE LICENSE-CONTENT         MIT for the code, CC BY 4.0 for the content
└── .gitignore .gitattributes
```

Ignored by `.gitignore` and never committed: build output (`public/`, `dist/`, `dist-*/`, `_site*/`), agent and tool scratch space (`.build/`, `.claude/`, `.codex/`, `tmp/`, `shots/`), design explorations (`design/`), raw research (`research/`), the ChatGPT Sites hosting file (`.openai/`), the IndexNow notification state (`.indexnow-state.json`, which the deploy keeps in the Actions cache), Python caches, local secrets (`.env`, `*.pem`, `*.key`, `*.local.*`) and model weights.

The code is under the MIT License (`LICENSE`) and the content under CC BY 4.0 (`LICENSE-CONTENT`). [CONTRIBUTING.md](../CONTRIBUTING.md#licensing) says which files each covers; the About pages' Reuse section (`#license`) states the same terms to readers, so change them together.

## Roles

| Role | Who | GitHub access | Responsibilities |
| --- | --- | --- | --- |
| Maintainer | @Mengyuan-L | Admin | Repository settings, rulesets, secrets and environments, the publishing workflows, editorial policy, final decision on what is published |
| Editor | invited by the maintainer | Triage to label and close issues; Write to approve pull requests | Check claims against sources, review the Chinese edition, apply labels such as `accepted` and `en-only` |
| Contributor | anyone | none needed; works from a fork | Issues and pull requests |

An approval counts toward the ruleset's required review only when the reviewer has Write access. Move the repository to a GitHub organization once there are two or more editors, so CODEOWNERS can name teams.

## Code owners

`.github/CODEOWNERS` maps paths to the people who must review them. GitHub requests a review from the owners of every path a pull request touches, and the ruleset on `main` blocks the merge until one of them approves. The last matching line wins, which is why specific paths follow the `*` default.

- Every path is currently owned by @Mengyuan-L. The extra lines for `api/`, `backend/`, `static/chat.*`, `.github/` and the governance files are there so that a future editor team can own `content/` without gaining approval rights over the publishing workflow or the Ask assistant's contract.
- An owner must have Write access, or GitHub ignores the line. GitHub shows CODEOWNERS syntax errors on the file's page.
- To add an editor for the Chinese edition: give them Write access, then add a line such as `/content/articles/**/zh.md @their-handle` below the `/content/` line. With an organization, use a team instead.
- A sole maintainer cannot approve their own pull request. The ruleset therefore lets repository admins bypass it for pull requests only: the maintainer merges their own pull request after CI passes, and nobody can push to `main` directly.

## GitHub settings checklist

Do this once, after the first push to GitHub. The ruleset's status-check picker lists a check after CI has run once; until then, type the job names exactly.

**General** (Settings → General)

- [ ] Pull requests: allow squash merging only; default commit message "Pull request title and description".
- [ ] Automatically delete head branches.
- [ ] Require contributors to sign off on web-based commits.
- [ ] Wiki off. Issues on.

**Ruleset for `main`** (Settings → Rules → Rulesets → New branch ruleset; target: default branch; enforcement: Active)

- [ ] Restrict deletions.
- [ ] Block force pushes.
- [ ] Require linear history.
- [ ] Require signed commits. Squash merges made in the web interface are signed by GitHub, so contributors who do not sign still pass.
- [ ] Require a pull request before merging: 1 required approval; dismiss stale approvals when new commits are pushed; require review from Code Owners; require conversation resolution; allowed merge method: squash.
- [ ] Require status checks to pass: `Unit tests`, `Mock backend on Python 3.9`, `Build and check`, `Content checks`, and `DCO` if the DCO app is installed. Leave "Require branches to be up to date" off. A job skipped by its `if:` condition counts as passing, so `Content checks` does not block pushes.
- [ ] Bypass list: Repository admin, mode "For pull requests only".
- [ ] Record the result: `gh api repos/Anything-Anywhere-Verifiable/verifiable-pro/rulesets` lists the rulesets as JSON.

**Ruleset for tags** (New tag ruleset; target patterns `archive/**` and `edition/**`; enforcement: Active)

- [ ] Restrict creations, restrict updates, restrict deletions, block force pushes.
- [ ] Bypass list: Repository admin, mode "Always", so the maintainer can still create new edition tags.

**Actions** (Settings → Actions → General)

- [ ] Allow actions created by GitHub, plus `lycheeverse/lychee-action@*`. Turn on "Require actions to be pinned to a full-length commit SHA" if the setting is offered.
- [ ] Fork pull request workflows: require approval for all external contributors.
- [ ] Workflow permissions: read repository contents only; do not allow GitHub Actions to create or approve pull requests. Each workflow asks for the extra permissions it needs per job.

**Environments** (Settings → Environments)

- [ ] `github-pages` (created when Pages uses GitHub Actions): deployment branches limited to `main`.
- [ ] Any future backend deployment environment: a required reviewer, and secrets stored only in that environment.

**Security** (Settings → Security)

- [ ] Private vulnerability reporting on. The issue chooser links to it.
- [ ] Dependabot alerts and security updates on.
- [ ] Secret scanning and push protection on.

**Labels.** The issue forms apply `triage` plus one type label. Create the set once (from a clone, or add `--repo Anything-Anywhere-Verifiable/verifiable-pro`); `--force` updates a label that already exists:

```bash
gh label create triage      --color FBCA04 --description "Needs a first look" --force
gh label create story-tip   --color 0E8A16 --description "Suggested development to cover" --force
gh label create resource    --color 1D76DB --description "Resource library suggestion" --force
gh label create correction  --color B60205 --description "Possible error in a published page" --force
gh label create bug         --color D93F0B --description "Site display or behavior problem" --force
gh label create accepted    --color 0E8A16 --description "Editor confirmed; ready for a pull request" --force
gh label create en-only     --color C5DEF5 --description "Chinese edition follows in a later pull request" --force
gh label create translation --color 5319E7 --description "Translation work" --force
gh label create link-rot    --color B60205 --description "External links that no longer resolve" --force
```

`links.yml` also creates `link-rot` itself before it opens an issue. Only people with Triage access or more can apply labels, so a contributor cannot set `en-only` on their own pull request.

**Optional:** install the [DCO app](https://github.com/apps/dco) and add its `DCO` check to the ruleset.

**Before the first public push**, run [actionlint](https://github.com/rhysd/actionlint) on `.github/workflows/` if it is available.

## Publishing: GitHub Pages, custom domain and DNS

`deploy.yml` publishes every push to `main`. It builds with `python build.py --out public`, which uses root-absolute links and the settings in `content/site.json`, including the Ask assistant's mode. A custom Actions workflow ignores the `CNAME` file that the production build writes; the domain is set in the repository settings instead.

1. **Pages source.** Repository Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. **Verify the domain for the repository's owner.** Organization `Anything-Anywhere-Verifiable` → Settings → Pages → Add a domain → `verifiable.pro`. Add the TXT record GitHub shows (`_github-pages-challenge-Anything-Anywhere-Verifiable`) to GoDaddy and press Verify. Keep that record after verification. Domain verification belongs to an organization, not a personal account, and only one account can hold it: while it does, only that account's repositories can publish to the domain.
3. **Custom domain.** In `Anything-Anywhere-Verifiable/verifiable-pro`, open Settings → Pages → Custom domain, enter `verifiable.pro` and save before changing the public DNS records. This repository deploys with GitHub Actions, so the setting does not add a `CNAME` commit.
4. **DNS records** in GoDaddy. Replace only conflicting A, AAAA, ALIAS or CNAME records for the apex and `www`; preserve TXT verification and mail records.

   | Type | Name | Value |
   | --- | --- | --- |
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | AAAA | `@` | `2606:50c0:8000::153` |
   | AAAA | `@` | `2606:50c0:8001::153` |
   | AAAA | `@` | `2606:50c0:8002::153` |
   | AAAA | `@` | `2606:50c0:8003::153` |
   | CNAME | `www` | `anything-anywhere-verifiable.github.io` |

   If the domain has CAA records, one of them must allow `letsencrypt.org`, which issues the Pages certificate. Check the records with:

   ```bash
   dig +noall +answer verifiable.pro A
   dig +noall +answer verifiable.pro AAAA
   dig +noall +answer www.verifiable.pro CNAME
   ```

5. **HTTPS.** Wait for the DNS check to pass, then enable **Enforce HTTPS** once the certificate is issued. With the apex as the custom domain and the `www` CNAME in place, GitHub redirects `www.verifiable.pro` to the apex. GitHub documents the [custom-domain setup](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site) and [organization domain verification](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/verifying-your-custom-domain-for-github-pages).
6. **Mail.** The editorial address in `content/site.json` (`contact_email`) needs its own mailbox and MX records; GitHub Pages does not provide mail.

**After moving the repository to another owner**, as on 25 October 2026 from `sept-usc` to `Anything-Anywhere-Verifiable`: remove `verifiable.pro` from the old organization's verified domains (Settings → Pages), verify it for the new owner as in step 2, point the `www` CNAME at the new owner's `github.io` host, and check that the repository's Pages settings still name `verifiable.pro` with Enforce HTTPS on. Then point `repo_url` in `content/site.json`, `repository-code` in `CITATION.cff`, the repository links in both About pages and the issue and pull request templates, README.md and this file at the new address, and refresh the assistant's request fixtures, since the About pages are hashed sources.

**If the domain is not ready at the first deploy**, the site is served at `https://anything-anywhere-verifiable.github.io/verifiable-pro/`, where the production build's root-absolute links break. Either attach the domain before the first deploy, or change the Build step in `deploy.yml` to `--mode preview` (relative links) through a pull request until the domain works, then change it back.

**After each deploy**, the `Check the live site` job waits until `/build.json` on the live site names the deployed commit, then runs `tools/verify_manifest.py` against the live site. A failure there means the CDN is still serving an older build or a published source does not match the manifest. Then the `Notify search engines of content changes` job tells IndexNow which pages the deploy changed (see [Discoverability](#discoverability)); its failure shows as a warning and does not fail the run.

**Rolling back.** Revert the faulty pull request with a new pull request (the GitHub "Revert" button creates one). Its merge deploys the earlier content. Re-running only the deploy job of an old run fails after a day, because the Pages artifact is kept for one day, while re-running all of its jobs builds and deploys that old commit again.

**Ask assistant mode.** `chat.mode` in `content/site.json` (`demo`, `live` or `off`) and `chat.api_base` are publishing decisions and go through a pull request like any content change. Pull request previews built by CI always use `--chat demo`, so they never call a backend. Before switching to `live`, the backend must implement `api/chat-v1.md`, serve HTTPS and allow the origin `https://verifiable.pro`; see `backend/README.md` and `docs/assistant-architecture.md`.

## Optional visit statistics

`analytics.ga4_measurement_id` in `content/site.json` selects the GA4 stream. An empty string omits the consent controls, configuration and script reference. Preview and artifact builds also omit them; a production build only activates them over HTTPS on the configured `base_url` origin.

The local `analytics.js` asks before loading Google's tag. **Allow** stores consent in the browser and starts measurement; **Decline** leaves the site usable without sending analytics requests. **Statistics choice** in the footer reopens the choice. Withdrawal disables measurement, deletes this site's host-only Analytics cookies and reloads to unload the tag. If browser storage refuses the change, measurement stays disabled on the current page and the control explains that the choice could not be saved. The bilingual `/privacy/` pages describe the data and choice.

In the GA4 web stream, keep **all Enhanced measurement off**, including page changes, site search, forms and outbound clicks. The implementation queues a page view with `page_location` limited to the origin and path, a referrer without query or fragment, and the path as its title. It sends no search query, Ask message, conversation or user ID. Google Analytics can also generate its standard session and engagement events. Google Signals and advertising personalization are disabled in the tag configuration; keep Google Signals, user-provided data collection and advertising features off in the Analytics property too. Changing those settings changes the site's privacy behavior and requires a review of the notice and tests.

## Discoverability

For the search baseline, owner-side index checks and a repeatable weekly review, see [Search visibility](SEARCH_VISIBILITY.md). Run `python3 tools/check_live_discovery.py --out /tmp/verifiable-discovery.json` for a read-only HTTP audit of the published robots rules, sitemap and key bilingual pages. A successful HTTP check shows accessibility from the machine running it, not indexing, ranking or access from a crawler's real IP range.

**Search titles and navigation.** Latest, Learn, Resources and Glossary have concise titles that name their subject in both languages. The `*_meta_title` and `*_meta_description` strings describe these sections in search results and link previews; their short visible headings and full introductions stay in the page body. The Stack and TEE hub also have shorter search summaries. Article and other page metadata come from their own titles and introductions. Tests check unique titles and descriptions, and that ordinary HTML links from each edition's home page reach every indexable page.

Google selects [sitelinks automatically](https://developers.google.com/search/docs/appearance/sitelinks), using the site's structure and link text. Keep category links descriptive and the hierarchy useful to readers. The breadcrumb data describes that hierarchy; it does not request or guarantee sitelinks. Source citations retain their complete labels in the page and Markdown. Their structured data gives the work's title, URL and date, and omits a publisher entity when the source label combines authors and venues, because [Schema.org requires a Person or Organization](https://schema.org/publisher).

Every build writes what search engines, AI answer engines and agents read: `robots.txt`, `llms.txt` and the two `llms-full.txt` files, the Atom and JSON Feeds, the sitemap, the web app manifests, and in each page's head the language alternates, the Markdown alternate, the structured data and the social tags. The development guide's [Machine-readable files](DEVELOPMENT.md#machine-readable-files) section lists them; `sitegen/discover.py` generates them and `tests/test_discoverability.py` checks a production build of them. `build.py` also publishes the IndexNow key named in `indexnow.json`, which `tests/test_indexnow.py` checks (see Incremental search notifications below). The site's description in these files is `description` in `content/site.json`, and the alternate name in the structured data is `alternate_name`.

**robots.txt.** Every crawler may fetch every page. The file also names crawlers in four groups (`ROBOTS_GROUPS` in `sitegen/discover.py`), each with the token its operator documents:

| Group | Tokens | Operator's documentation |
| --- | --- | --- |
| Search engines | `Googlebot`, `Bingbot`, `Applebot`, `Baiduspider` | [Google](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers), [Bing](https://blogs.bing.com/webmaster/2010/09/03/bingbot-is-coming-to-town), [Apple](https://support.apple.com/en-us/119829), [Baidu](https://www.baidu.com/search/robots_english.html) |
| AI search and answer engines | `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `DuckAssistBot`, `Amzn-SearchBot`, `Meta-WebIndexer` | [OpenAI](https://developers.openai.com/api/docs/bots), [Anthropic](https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler), [Perplexity](https://docs.perplexity.ai/guides/bots), [DuckDuckGo](https://duckduckgo.com/duckduckgo-help-pages/results/duckassistbot), [Amazon](https://developer.amazon.com/amazonbot), [Meta](https://developers.facebook.com/docs/sharing/webmasters/web-crawlers/) |
| Assistants that fetch a page when a person asks | `ChatGPT-User`, `Claude-User`, `Perplexity-User` | OpenAI, Anthropic and Perplexity, as above; OpenAI and Perplexity say that their fetchers may not follow robots.txt, since a person asked for the page |
| AI model training and open web datasets | `GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`, `CCBot`, `Amazonbot`, `Meta-ExternalAgent` | OpenAI, Anthropic, Google, Apple, [Common Crawl](https://commoncrawl.org/ccbot), Amazon and Meta, as above |

The tokens were checked against these pages on 23 October 2026; check them again before adding or renaming one. A crawler obeys only the most specific group that names it, so the build writes `ROBOTS_RULES` (now `Allow: /`) into the `*` group and into every named group: a rule meant for all crawlers goes into `ROBOTS_RULES`. Naming the training crawlers with `Allow: /` changes nothing in effect, but it states a choice that belongs to the owner while no reuse license is chosen. To keep the site out of model training while search engines and AI search crawlers still fetch it, give that group in `sitegen/discover.py` its own rules as a third item, `("Disallow: /",)`. `Google-Extended` and `Applebot-Extended` fetch nothing themselves and do not affect search: they control how Google and Apple may use the pages that Googlebot and Applebot fetch. Blocking some of these tokens reaches beyond training. Google also applies `Google-Extended` to grounding answers in Gemini Apps and on Vertex AI. Amazon says `Amazonbot` also helps it answer customers more precisely, and Meta says `Meta-ExternalAgent` also indexes pages to improve its products.

**Pages kept out of search results.** The search pages list no results without JavaScript, and the 404 pages answer any missing address, so they carry `noindex` (`indexable=False` in `Site.layout`), and the sitemap, `llms.txt`, the `llms-full.txt` files and the feeds leave them out. Keep them fetchable in `robots.txt`: a crawler that may not fetch a page never reads its `noindex`. Every other page carries `max-image-preview:large` (`ROBOTS_INDEX` in `sitegen/render.py`), so search results may show a large preview of its images, such as its social card. The home pages' title (`home_title` in `content/strings.json`) starts with the site's name and says what the site covers, while the structured data name the site `verifiable.pro`; other titles end with " | verifiable.pro" unless they name the site already, as About and Vision do.

**Social cards and icons.** `tools/og_images.py` draws the social cards (`static/og/`) and the icons (`static/icons/`) with headless Google Chrome and the Google Fonts the site uses, so it needs Chrome and the network. It writes nothing when a font does not load, when Chinese text is not set in a Chinese font, when a title does not fit, or when a file is not the stated size or exceeds 120 KB. Commit the PNG files and `static/og/cards.json` together. The build only links them, warns when a card's words no longer match the content and stops when one is missing. Redraw the cards after renaming a topic or changing the tagline, the home page kicker, the colours, the fonts or the mark, and check the result by opening the files.

**Incremental search notifications.** `indexnow.json` holds this host's [IndexNow](https://www.indexnow.org/documentation) key, and every build serves the key at `/<key>.txt`, a file that holds exactly the key, with no newline, since search engines compare it with the key they are sent. After the live check confirms the deployed commit, the `Notify search engines of content changes` job in `deploy.yml` checks that key URL and sends `api.indexnow.org` the canonical URLs that the deploy added, changed or removed. IndexNow shares them with the search engines that take part, such as Bing. Google does not take part, so keep its Search Console sitemap submission. A notification asks for a crawl; it does not guarantee crawling, indexing, ranking or a citation in an AI answer.

`tools/indexnow.py` takes the pages from the built sitemap and stops when the sitemap lists anything other than this host's HTTPS HTML pages. It leaves out a page whose canonical link names another address, a page marked `noindex` and a page that `robots.txt` closes to `*` or to `bingbot`. It reads `robots.txt` as RFC 9309 does, so the result does not depend on the Python version. It fingerprints each page's title, search metadata, canonical and alternate links (the other edition, the feeds and the Markdown source), structured data, and the elements, text, links and images in `<main>`. It leaves out the social card's alt text, which on the pages that share the site's card repeats the home page's kicker and tagline; a page's own picture counts through its `<img>` alt text. Navigation, footers, scripts, elements hidden from readers, tooltips, the filing-details and Ask asides, the related-stories cards and the correction links are left out, because they repeat other pages or the site's settings. A new brief therefore notifies itself and the home, Latest and topic pages that list it, not the older articles that show it among their related stories, and an unchanged rebuild notifies nothing. A change to the elements in `<main>`, such as a template change that adds a wrapper or changes a tag, notifies every page it touches; a change of class, id or style does not.

The job keeps the fingerprints that IndexNow received (HTTP 200, or 202 while IndexNow validates the key) in `.indexnow-state.json`, which the Actions cache carries from one deploy to the next. A refused request, such as a 429, leaves its URLs at their earlier fingerprints, so a deploy within 7 days that finds that state in the cache sends them again. The failure shows in the job and in the run's summary without failing the deploy. A deploy that changes the cache key, by editing `indexnow.json` or changing `VERSION`, does not find that state and does not resend the refused pages. To retry sooner, after a longer pause or before such a deploy, re-run only the failed job, while its commit is still the live one. The job sends and records nothing once `/build.json` names another commit, or when the run deployed to an address other than `https://<host>/`, as a fork's Pages site does. Re-running all jobs of an older run redeploys that older commit.

GitHub evicts a cache entry that no run has used for 7 days, and an edit of `indexnow.json` changes the cache key. Without a state, the job builds the commit that `/build.json` named before the deploy and compares with that build, so the deploy still notifies only its own changes. The build job records that commit only if it belongs to `main`'s history, because the notify job runs its `build.py`. When there is no such commit, as at a first deploy, or the build job cannot confirm it, the tool records the current pages as the baseline and notifies nothing, and the job warns about it. `--bootstrap` notifies every page instead, which IndexNow's FAQ accepts only when the whole site has changed, as after a move or a redesign. A change to what a fingerprint covers can change many pages' fingerprints, so it goes with a new `VERSION` in `tools/indexnow.py` and the same number in the cache key in `deploy.yml`, which a unit test checks. The next deploy then compares with the previous build.

A local run cannot see the state, which cannot be downloaded from the cache. To preview what a deploy would send, build the commit that the live site serves and the new one in a fresh folder, and compare the builds without network requests or writes. Each command runs only if the one before it succeeded, so a live commit missing from your clone stops the preview:

```bash
git fetch -q origin \
  && commit=$(curl -fsS https://verifiable.pro/build.json | python3 -c 'import json, sys; print(json.load(sys.stdin)["commit"])') \
  && work=$(mktemp -d) && mkdir "$work/live" \
  && git archive -o "$work/live.tar" "$commit" && tar -x -f "$work/live.tar" -C "$work/live" \
  && python3 "$work/live/build.py" --out "$work/live-site" \
  && python3 build.py --out "$work/new-site" \
  && python3 tools/indexnow.py --site-dir "$work/new-site" --baseline-site-dir "$work/live-site" --dry-run
```

Leave sending to the deploy job, so that its cached state matches what IndexNow received. The key cannot be secret, because `SHA256SUMS` lists every published file. Anyone can therefore send this host's URLs with it, and such submissions count toward the per-site limits behind a 429. To replace the key, change `key` in `indexnow.json` and deploy; the host there must stay equal to `base_url` in `content/site.json`, or the build stops. That deploy publishes the new key file, and its notify job compares with the previous build because the cache key changed.

**After the first deploy**, the owner:

1. verifies the domain in [Google Search Console](https://search.google.com/search-console) as a Domain property, with the DNS TXT record it shows, and submits `https://verifiable.pro/sitemap.xml`;
2. adds the site to [Bing Webmaster Tools](https://www.bing.com/webmasters), by importing it from Search Console or with its own DNS record, and submits the sitemap there too;
3. checks a home page, an article and the glossary with Google's [Rich Results Test](https://search.google.com/test/rich-results) and the [Schema Markup Validator](https://validator.schema.org/), and an article's link preview with a social network's preview tool.

DNS records keep verification tags out of the pages; a verification tag in `render.py` would also need the owner's account. On GitHub, the repository's description, website (`https://verifiable.pro`) and topics, such as `verifiable-ai`, `remote-attestation`, `confidential-computing`, `trusted-execution-environment`, `zkml`, `c2pa` and `ai-governance`, help people find the source; set them under the repository's About settings once it is public.

## How an article pull request flows

1. **Tip.** Someone opens a Story tip issue, or an editor proposes a piece. An editor checks the primary source and labels the issue `accepted`.
2. **Draft.** The contributor forks the repository, creates `article/<slug>`, adds `content/articles/<slug>/en.md` and `zh.md` and, for a news brief, `illustration.json` for its lead image, and runs the local checks in CONTRIBUTING.md. The lead image is usually a photo, whose four files in `static/media/` come from `python3 tools/photos.py --write`, or else an illustration, which `python3 tools/illustrate.py --write` draws as `static/media/<slug>.svg`.
3. **Pull request.** The contributor opens a pull request with the template's checklist completed and "Closes #N" for the issue. For a first-time contributor, a maintainer approves the CI run after reading the diff (Actions settings above). Look for changes outside `content/` and `static/media/` before approving. CI cannot make a photo again, because its source is not in the repository, so compare the spec's credit, license and `source_url` with the source page and look at the photo itself. An illustration's `static/media/<slug>.svg` is redrawn by CI from its spec, so look closely at any change to `tools/illustrate.py` or `tools/scene/`, which would change what that check draws.
4. **CI.** `Unit tests` and `Mock backend on Python 3.9` run the tests; the unit tests also hold every lead photo and its copies to their spec and fail on a file in `static/media/` that no spec names (`tools/photos.py --check`). `Build and check` draws every lead illustration again from its spec (`tools/illustrate.py --check`), holds every lead photo and its copies to their spec (`tools/photos.py --check`), builds the preview with `--chat demo`, checks internal links and anchors, verifies the manifest, builds with the assistant off, builds production twice to confirm byte-identical output, and looks for files that must not be published. `Content checks` lists the changed articles and blocks invalid slugs, a missing `zh.md` without `en-only`, and the structural lint findings listed in CONTRIBUTING.md; other lint findings appear as warnings on the diff.
5. **Preview.** Download the `site-preview` artifact from the CI run and serve it:

   ```bash
   gh run download <run-id> -n site-preview -D /tmp/pr-<number>
   python3 -m http.server 8000 --directory /tmp/pr-<number>
   ```

6. **Review.** An editor checks every claim against its source and the checklist against CONTENT_GUIDE.md; a Chinese-language editor reviews `zh.md`; the code owner approves.
7. **Merge.** Squash merge with a title that starts with the area (`content:`, `correction(<slug>):` and so on). The issue closes through "Closes #N".
8. **Publish.** `deploy.yml` runs the tests, builds, attests, deploys, checks the live site and tells IndexNow which pages changed. The new article's source digest appears on its page and in `/manifest.json`; `/build.json` names the merge commit.

## How a correction flows

1. **Report.** A reader opens a Correction request issue (page, edition, the exact sentence, the corrected statement and a primary source), or emails the editors. For an emailed report, the maintainer opens the issue and leaves out the reporter's name and address unless the reporter agrees to be named.
2. **Triage.** An editor opens the cited source. If the report is confirmed, the editor labels the issue `accepted`; if not, the editor replies with the reason and closes it.
3. **Pull request.** The fix edits `en.md` and, if affected, `zh.md`; sets `updated:` in `en.md` (inherited by `zh.md`); adds a dated `changes:` entry (`YYYY-MM-DD | what changed`) to `en.md` and a translated entry to `zh.md`, which does not inherit the field; uses a commit title starting with `correction(<slug>):`; and links the issue with "Closes #N". Typos and broken links need no `changes:` entry.
4. **Review and merge** as for an article.
5. **Publish.** After the deploy, the article shows the new Updated date and the dated note under "Corrections and updates", and its source digest changes. The previous text stays in the repository history, and `git log --grep '^correction'` lists every correction. Reply on the issue with the link to the corrected page.

## Public repository and initial snapshot

The public repository is `Anything-Anywhere-Verifiable/verifiable-pro`. It moved there from `sept-usc/verifiable-pro` on 25 October 2026, and GitHub redirects the old web and Git addresses. It starts with one initial commit of the completed source snapshot. Earlier private Git history, raw research, design explorations and the retired prototype’s `DESIGN-NOTES.txt` and `brand/` are excluded. The original private checkout remains separate.

After that initial commit, retain the public history and make changes through pull requests. Do not reset or replace its root to publish an update. Build provenance and attestations refer to commits in this public repository.

`tools/draft_content.py` is an unused research scaffold, not part of the build or publishing workflow. It reads the ignored `research/` folder, requires a separate `--out DIR` and refuses to overwrite `content/`. Current editorial work follows CONTRIBUTING.md and CONTENT_GUIDE.md.

## Verifiable publishing

### What each deploy publishes

| File | What it records | Produced by |
| --- | --- | --- |
| `/manifest.json` | The SHA-256 of every article and page source (`/articles/<slug>/<lang>.md`, `/pages/<name>.<lang>.md`), of the data files `topics.json`, `resources.json`, `glossary.json`, `tee.json` and `tiers.json`, and of each lead image's spec (`/articles/<slug>/illustration.json`, kind `illustration`) and files (kind `image`: a photo's `/assets/media/<slug>.webp`, `<slug>-800.webp`, `<slug>-400.webp` and `<slug>-og.jpg`, or an illustration's `/assets/media/<slug>.svg`), plus a digest over the whole list | `build.py` |
| `/build.json` | The manifest digest, the repository, the commit, its time, the ref, the workflow run and the Python version | `deploy.yml` |
| `/SHA256SUMS` | The SHA-256 of every published file, `build.json` and `manifest.json` included | `deploy.yml` |
| `/SHA256SUMS.sigstore.json` | A Sigstore bundle holding one SLSA build provenance attestation whose subjects are the files in `SHA256SUMS` | `deploy.yml` with `actions/attest` |

### Manifest digest and commit

The manifest digest is the manifest's own `digest` field (`manifest.json` → `digest`); the footer links the manifest, and each article's record shows that article's source digest and links the manifest. The digest covers the content sources and the lead images only. Changes to templates, CSS, JavaScript, `strings.json` or `site.json` leave it unchanged, so several commits can share one digest, while each deploy has exactly one commit.

- **Digest to commit:** `/build.json` on the live site pairs the current manifest digest with the commit that produced the deployment. Each CI and deploy run also prints the commit and the manifest digest in its job summary.
- **Commit to digest:** check out the commit and run `python3 build.py --mode preview --out <dir>`; the build prints the digest. `tools/verify_manifest.py <dir>` recomputes it.
- **Which commits can change the digest:** `git log --format='%h %ad %s' --date=short -- content/articles content/pages content/topics.json content/resources.json content/glossary.json content/tee.json content/tiers.json`.

The Ask assistant sends the manifest digest with every question (`context.manifest_digest` in `api/chat-v1.md`), so an answer can be tied to the build whose passages it was given.

### Build provenance attestations

`deploy.yml` runs `actions/attest`, which signs an in-toto statement with SLSA build provenance through Sigstore's public-good instance, records it in the Rekor transparency log, and stores it with the repository. (`actions/attest-build-provenance` v4 is a wrapper around `actions/attest`; GitHub recommends `actions/attest` for new workflows.) The provenance names the repository, the workflow file, the commit and the ref, and states that a GitHub-hosted runner built it. The job needs `id-token: write` and `attestations: write`; no secret is involved. One attestation can hold at most 1024 subjects, so above 1000 files the workflow attests only `SHA256SUMS`, `manifest.json` and `build.json`, and readers check the other files against the attested `SHA256SUMS`.

A reader checks a page source with the GitHub CLI:

```bash
curl -s https://verifiable.pro/build.json                  # the commit behind this deployment
curl -sO https://verifiable.pro/articles/<slug>/en.md
gh attestation verify en.md --repo Anything-Anywhere-Verifiable/verifiable-pro \
  --signer-workflow Anything-Anywhere-Verifiable/verifiable-pro/.github/workflows/deploy.yml \
  --source-ref refs/heads/main --deny-self-hosted-runners
# Offline, with the bundle published next to the site:
curl -sO https://verifiable.pro/SHA256SUMS.sigstore.json
gh attestation verify en.md --bundle SHA256SUMS.sigstore.json --repo Anything-Anywhere-Verifiable/verifiable-pro
```

Deploys made before the move on 25 October 2026 were signed as `sept-usc/verifiable-pro`: to check one of their files, give that name in `--repo` and `--signer-workflow`. To check that a file came from the commit named in `build.json`, add `--source-digest <commit>` to the first `gh attestation verify` command. Readers without the GitHub CLI can compare `shasum -a 256 en.md` with the line for `articles/<slug>/en.md` in `/SHA256SUMS`; that check is only as strong as the attestation on `SHA256SUMS`.

### Signed commits and tags

Sign commits and tags with an SSH key and register the same key on GitHub as a **Signing key** (Settings → SSH and GPG keys):

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global tag.gpgsign true
```

Squash merges made in the web interface are signed with GitHub's key. Mark a citable snapshot with a signed edition tag on the commit that the live site serves:

```bash
commit=$(curl -s https://verifiable.pro/build.json | python3 -c 'import json, sys; print(json.load(sys.stdin)["commit"])')
digest=$(curl -s https://verifiable.pro/build.json | python3 -c 'import json, sys; print(json.load(sys.stdin)["manifest_digest"])')
git fetch origin
git tag -s edition/2026-10 "$commit" -m "verifiable.pro edition 2026-10, manifest digest $digest"
git push origin edition/2026-10
```

GitHub marks the tag "Verified". To verify locally, list trusted keys in an allowed-signers file (`git config gpg.ssh.allowedSignersFile <file>`, one line per key in the form `<email> <key type> <public key>`), then run `git tag -v edition/2026-10`. The tag ruleset stops edition and archive tags from being moved or deleted.

### What this shows and what it does not

- It shows that the published bytes came from `deploy.yml` at a named public commit on a GitHub-hosted runner, with an entry in a public transparency log.
- It does not show that the reporting is correct, or that the commit was reviewed. The commit links to its pull request, where the review is visible.
- It relies on GitHub and Sigstore operating honestly.
- It does not show that other readers received the same bytes; each reader can check their own copy.
- It cannot reveal a page that was removed. Watching the repository's attestations would show an unexpected deploy.
- The Ask assistant's answers are a separate chain (backend attestation); see `docs/assistant-architecture.md`.

### Planned improvements

- Make `build.json` reproducible from the commit alone (`build.py --commit` and `SOURCE_DATE_EPOCH` for the footer year), so anyone can rebuild a commit and match `SHA256SUMS` exactly.
- Show the source commit and a link to the build record in the footer, and a "History" link on each article to its file's commit log on GitHub.
- Rename the footer label "Build digest" to "Content digest", since the manifest covers content sources only.
