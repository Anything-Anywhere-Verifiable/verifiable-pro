---
title: "Cloudflare Says SGLang KV Cache Bug Exposed Other Users’ Data in GLM-5.3 Responses"
dek: "Cloudflare attributes 155 affected Workers AI responses to an undersized cache pool and faulty rejected-request handling, and recommends SGLang v0.5.22 or later."
kind: news
topics: [confidential-computing, verifiable-inference]
layers: [models, runtime]
event_date: 2026-10-26
published: 2026-10-28
agent: daily
evidence: [announcement, documentation]
sources:
  - "Cross-request KV cache exposure in the GLM-5.3 Workers AI model, and our remediation with SGLang | Cloudflare | 2026-10-26 | https://blog.cloudflare.com/kv-cache-exposure-remediation/"
  - "SGLang v0.5.22 release notes | SGLang | 2026-10-19 | https://github.com/sgl-project/sglang/releases/tag/v0.5.22"
  - "[VLM] Retire aborted disaggregated prefill results (PR #36988) | SGLang | 2026-09-06 | https://github.com/sgl-project/sglang/pull/36988"
  - "[PD] Do not admit intake-rejected requests to a PD handoff (PR #38935) | SGLang | 2026-09-16 | https://github.com/sgl-project/sglang/pull/38935"
---

Cloudflare disclosed cross-request KV cache exposure in Workers AI’s GLM-5.3 on October 26, 2026, in a coordinated publication with the researcher and SGLang maintainers. Cloudflare says only GLM-5.3 was affected: 155 responses contained other customers’ data, all answering prompts longer than 681,280 tokens. It found no evidence of deliberate exploitation.[^1]

Two failures combined. Cloudflare configured a 1,048,576-token context window, but its prefill GPUs’ KV cache pool held only 681,280 tokens. In SGLang’s disaggregated prefill/decode pipeline, an oversized request was marked rejected and replaced with a one-token stub, yet still reported itself as live. Prefill processed the stub and signaled transfer completion; decode assumed the full prompt’s cache had arrived and read stale pages containing earlier requests’ data.[^1]

The exposure began with the model’s August 27, 2026 launch. Knostic’s Gadi Evron reported it through HackerOne on September 8. Cloudflare declared an incident on September 9 at 13:22 UTC and restored the model at 19:40 UTC that day.[^1]

SGLang merged #36988 on September 6, 2026, adding cleanup for aborted prefill results; Cloudflare identifies it as the fix that stops this exposure.[^1][^3] PR #38935 merged September 16 to reject requests earlier at admission. Its description explicitly calls this a waste-and-latency improvement, rather than an additional correctness fix after #36988.[^4]

Cloudflare expanded the pool to about 2.04 million tokens and patched rejection handling before restoring service. It recommends SGLang v0.5.22 or later, pool-capacity checks, deferred KV release and bounded transfers. It also recommends transfer checksums and KV canaries where supported, while noting incomplete architecture coverage, including GLM-5.3. Broader support and checks at every decode step remain work in progress.[^1]

:::analysis
Our reading is that KV cache pages form a tenant-isolation boundary: ownership and handoff checks determine whose data decode can read. The leak originated in the inference-serving pipeline, rather than the model itself. Long prompts triggered it because only requests exceeding this deployment’s 681,280-token pool reached the faulty rejection path.[^1] In verifiable terms, this is a runtime-layer failure: the leak came from the serving stack’s handoff rather than the model itself, so trusting a response requires trusting the serving layer’s isolation as well as the model.[^1] For users, the check is currency plus configuration: confirm your deployment runs SGLang v0.5.22 or later, the version Cloudflare recommends, with the pool-capacity checks it lists, and ask the same of any provider serving you.[^1] On this site’s stack, this is a T2 (Software & runtime) failure, not a T3 (Models & data) one, and T2’s claim is exactly the point: that this exact code and configuration processed the request, so when the serving-stack version and configuration are recorded and checkable, a user can determine whether their requests ran on an exposed deployment.[^1]
:::
:::checked
On 2026-10-28 we read Cloudflare’s disclosure, SGLang v0.5.22 release facts and PRs #36988/#38935.[^1][^2][^3][^4]
The v0.5.22 release notes do not describe this KV fix; the first release containing it was not independently confirmed.[^2]
No systems were tested.
:::
