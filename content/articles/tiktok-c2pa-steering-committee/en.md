---
title: TikTok Joins the C2PA Steering Committee and Says It Has Labeled 3 Billion AI-Generated Videos
dek: TikTok said on 10 July 2026 that it was joining the Steering Committee of the Coalition for Content Provenance and Authenticity, and the coalition confirmed the move on 27 July. TikTok pairs the coalition's Content Credentials with an invisible watermark that it says only TikTok can read.
kind: news
topics: [content-provenance]
layers: [outputs]
event_date: 2026-07-10
published: 2026-10-20
agent: daily
evidence: [announcement]
sources:
  - Helping people spot and understand AI-generated content on TikTok | TikTok Newsroom | 2026-07-10 | https://newsroom.tiktok.com/helping-people-spot-and-understand-ai-generated-content-on-tiktok?lang=en-GB
  - C2PA Welcomes TikTok to Steering Committee, Advancing the Adoption of Content Credentials at a Global Scale | C2PA | 2026-07-27 | https://c2pa.org/c2pa-welcomes-tiktok-to-steering-committee/
  - More ways to spot, shape and understand AI-generated content | TikTok Newsroom | 2025-11-19 | https://newsroom.tiktok.com/more-ways-to-spot-shape-and-understand-ai-content?lang=en
related: [c2pa-security-analysis-umbc, google-synthid-detector-public]
---

TikTok said on 10 July 2026 that it was joining the Steering Committee of the Coalition for Content Provenance and Authenticity (C2PA). The coalition develops Content Credentials, a standard for recording where a piece of media came from and how it was changed.[^1, 2] The coalition announced on 27 July that TikTok had upgraded from general member to Steering Committee member. It said TikTok will help guide technical development of the standard and its adoption across platforms.[^2]

In its 10 July post, TikTok said it had labeled more than 3 billion videos as AI-generated. It said it used a combination of Content Credentials, creator labeling tools and its own invisible watermarking. It also said that two years earlier it had become the first video platform to implement Content Credentials.[^1]

TikTok announced the watermark in November 2025 as a response to a weakness it described then. Content Credentials embed metadata that tells platforms using the C2PA standard, including TikTok, when content is AI-generated. But such labels may be removed when content is re-uploaded or edited elsewhere.[^3] TikTok described the watermark as one "only we can read" that is harder for others to remove. It said it would add the mark to AI-generated content made with TikTok tools and to uploads carrying Content Credentials.[^3]

:::analysis
The two signals give outsiders different abilities. Content Credentials are an open format that other platforms can read. A watermark that only TikTok can read may let TikTok restore a label after metadata is stripped but gives no one else a way to check it. TikTok has described the re-upload problem first-hand, and its seat on the Steering Committee gives it a role in how the open standard deals with that problem.
:::

:::checked
On 20 October 2026 we read TikTok's newsroom posts of 10 July 2026 and 19 November 2025 and the C2PA release. The release carries a 27 July dateline, but the coalition's website dates the post 28 July. TikTok's post counts more than 3 billion videos, while the C2PA release counts pieces of content and lists creator education among the methods. We did not verify the labeling figure or examine TikTok's labels or watermark, and we test no systems ourselves.
:::
