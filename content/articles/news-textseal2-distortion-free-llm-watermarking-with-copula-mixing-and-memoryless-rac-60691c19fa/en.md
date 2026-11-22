---
title: "TextSeal2 Authors Claim Watermark Detection Gains Under Speculative Decoding"
dek: "An arXiv submission describes copula-based key mixing and an exponential-race verifier, reporting stronger watermark detection while preserving the target model’s output distribution."
kind: news
topics: [content-provenance, evaluation-audits]
layers: [outputs, runtime]
event_date: 2026-10-29
published: 2026-10-30
agent: daily
evidence: [announcement, documentation]
sources:
  - "TextSeal2: Distortion-Free LLM Watermarking with Copula Mixing and Memoryless Races | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.40613"
---

Tom Sander and 13 co-authors submitted TextSeal2 to arXiv on 29 October 2026, describing a large language model watermark that they say preserves the target model’s output distribution and remains detectable under speculative decoding. The abstract claims unchanged draft acceptance rates, preserved output diversity and no measurable inference latency increase.[^1]

TextSeal routes each token to one of two keys using a coin flip, while its detector averages scores from both keys without knowing which was used. TextSeal2 instead merges two or more keys into a virtual key and couples it to fresh noise through AutoMark’s Gaussian copula. The authors say this permits mixing any number of keys, including publicly shared keys, without diluting detection.[^1]

For speculative decoding, TextSeal2 checks keyed drafts using an additional exponential race over the leftovers of the draft races. The authors attribute exact preservation of the target model’s output distribution to the memorylessness of this race; replacement tokens remain watermarked with the same keys.[^1]

The abstract reports evaluations on three models. At equal output token diversity and a false-positive rate of 10⁻³, TextSeal2 detects 8–22 percentage points more 100-token answers than TextSeal. Under speculative decoding, it reports gains of 18 and 22 percentage points over TextSeal and textGrain, respectively, for 200-token answers at the same acceptance rate. These are author-reported results.[^1]

:::analysis
The claim sits at T4 (outputs), where detection supplies evidence of a watermark signal, and T2 (runtime), where decoding must preserve that signal; the reported detection rates do not establish deployment identity. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that deployment. Users and operators should check the watermark implementation, key configuration and decoding mode against their deployment records; the saved abstract provides no deployment identification mechanism or recommended fixed version.[^1]
:::

:::checked
On 30 October 2026, we read the supplied saved arXiv abstract page for TextSeal2, arXiv:2610.40613v1, submitted on 29 October. This establishes what the authors announced and reported. We did not read the full paper or code, test the system, or independently confirm its distribution, detection or latency claims.[^1]
:::

[^1]: [TextSeal2: Distortion-Free LLM Watermarking with Copula Mixing and Memoryless Races](https://arxiv.org/abs/2610.40613), arXiv, 29 October 2026.
