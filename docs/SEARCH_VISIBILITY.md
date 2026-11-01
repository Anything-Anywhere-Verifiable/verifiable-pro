# Search visibility

This is a measurement and editorial backlog, not a ranking guarantee. Keep existing discovery files working; prioritize useful original reporting and clear descriptions of what the site covers. [Google's AI search guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) retains foundational SEO, emphasizes original expertise, and says `llms.txt` does not affect Google visibility or rankings.

## Baseline: 1 November 2026

These are limited samples from the `web.run` search tool, with no domain restriction. Its underlying engine and result coverage were not established. They are not Google/Bing rank measurements or a complete index inventory. “Absent” means no result URL on `verifiable.pro` appeared in that returned sample.

| Exact query | Own-domain result | Observation |
| --- | --- | --- |
| `"verifiable.pro"` | Absent | [Mengyuan Li's homepage](https://mengyuanli.com/) and [research page](https://mengyuanli.com/verifiable-ai.html) mention the site. |
| `site:verifiable.pro` | Absent | Tool returned no results; this does not establish non-indexing. |
| `TEE confidential computing news analysis websites` | Absent | Related reporting, technical blogs and consortium documents appeared. |
| `verifiable AI news analysis` | Absent | Many results concerned fact-checking AI news: possible ambiguity in the query. |
| `GPU TEE remote attestation technical blogs` | Absent | NVIDIA and Intel technical material appeared. |
| `TEE 机密计算 新闻 分析 网站` | Absent | Chinese technical resources and industry reporting appeared. |

Direct navigation successfully retrieved the [homepage](https://verifiable.pro/), [TEE hub](https://verifiable.pro/topics/confidential-computing/), [Latest](https://verifiable.pro/latest/) and [About](https://verifiable.pro/about/). Some initial opens failed before succeeding through homepage links. Three article URLs returned a tool `Cache miss`. These observations do not establish an origin outage, crawler blocking, indexing, ranking, or answer citation.

Latest showed 69 entries: 61 news, two analyses, two explainers and four guides. The existing analyses already compare proofs/enclaves/re-execution and private AI service designs; improve those pages rather than duplicate them.

## Owner checks

No Search Console, Bing Webmaster Tools, analytics or hosting-log account was accessed for this baseline. These steps require an authorized account with access to the verified property. Verification may need DNS or site-file access; submissions and settings need the appropriate property permissions. Request access or an export from the owner rather than assuming it exists.

1. In Search Console, inspect the homepage, TEE hub and both analysis URLs: record indexing status, last crawl, selected canonical and exclusion reasons. Compare the indexed result with the live inspection. Check robots, `noindex`, snippet controls and generative AI inclusion settings.
2. Check sitemap processing and discovered/indexed page counts. After fixing a specific problem, request indexing where permitted; record submission separately from successful indexing.
3. In Bing Webmaster Tools, inspect the same URLs and sitemap, then review crawl/indexing issues and search performance. Existing IndexNow notifications are discovery requests, not evidence of inclusion.
4. Export query/page impressions and clicks for a fixed period. If available, separately inspect Google's generative AI performance report and consented referral analytics. Missing referral data is not evidence of no citations.
5. Where hosting logs are available, investigate failed crawler requests. [OpenAI's crawler documentation](https://developers.openai.com/api/docs/bots) distinguishes search (`OAI-SearchBot`) from training (`GPTBot`) and user-triggered fetches (`ChatGPT-User`). Check robots rules and access from published search-crawler IP ranges; a spoofed user-agent test alone cannot establish that access.

## Weekly manual measurement

Repeat the exact queries above in fresh sessions without previously mentioning the site. Record date/time zone, product/tool, model if known, language/location, exact query, returned URLs and errors. Keep brand and non-brand results separate.

Track two independent outcomes: **retrieval appearance** (an own-domain URL in results) and **answer citation** (an own-domain URL actually cited in a generated answer). Record answer citations as “not tested” for raw search runs. Keep denominators and retained result sets consistent; compare repeated observations, not a single run. Archive evidence alongside the deployed commit and metadata changes.

## Next 30 days

- **Days 1–7:** Complete owner checks; validate deployed titles, descriptions and visible coverage language. Preserve the baseline before comparing changes.
- **Days 8–14:** Extend the existing service comparison with dated, source-linked evidence about model identity, verifier responsibility and documented limits. Distinguish document review from actual testing.
- **Days 15–21:** Develop one original GPU attestation walkthrough with reproducible evidence, configuration, CPU/GPU binding checks and failure cases. Obtain genuine technical review before crediting a reviewer.
- **Days 22–30:** Review results and reader feedback. Prepare a useful technical summary for a relevant community or project, disclose affiliation and follow its rules. Share only with explicit authorization; do not manufacture endorsements or solicit artificial mentions.

This document creates no scheduled task and sends no external messages.
