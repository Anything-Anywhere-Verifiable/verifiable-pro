---
title: "Requant Reports Batched GPU Inference Proofs and a Full-Model Memory Gate"
dek: "A Requant technical report says its verifier accepted 560 small-workload request proofs, while a full-model script stopped at a host-memory check. The results do not establish production-model throughput."
kind: news
topics: [verifiable-inference]
layers: [runtime]
event_date: 2026-11-15
published: 2026-11-21
agent: daily
evidence: [announcement, documentation]
sources:
  - "Verifiable GPU Inference: Batching, Proofs and Memory | requant.network | 2026-11-15 | https://requant.network/research/gpu-verifiable-inference"
---

Requant reported on 15 November 2026 that its native CPU verifier accepted all 560 request proofs in two cohorts of a small GPU inference experiment. The company says batching reduced the median generation time per request by spreading process and model setup costs across requests. Its technical report is not peer reviewed or an independent replication.[^1]

The experiment used synthetic weights, a reused model commitment and fresh seeded prompts. Each timed call still started a process and loaded model and key state; it did not test a persistent server. Proofs covered the stated next-token computation under an exact-match acceptance policy. They did not certify that earlier prompt tokens were the model’s choices. Requant says native acceptance does not formally establish the correctness of the C++/CUDA implementation; the commitment assumptions and proof-of-work accounting remain part of the acceptance statement.[^1]

The report says an unchanged full-model script stopped before GPU execution because it required at least 280 GB of available host memory and about 59 GB was available. GPU memory figures came from sampled process allocations, not an instantaneous whole-device peak. Requant recommends the supported batch interface when requests can be grouped and retaining the qualified generic fallback; it cautions against extrapolating the small-model results to the full configuration. It reports that hosted CPU CI repeated public-proof controls but did not rerun GPU timings.[^1]

:::analysis
This work sits at T2, the runtime layer: a verifier’s confidence depends on the proof’s stated coverage, the commitment assumptions and the implementation behind the acceptance result. The relevant property for users is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue. Users and operators should check the version, configuration and proof coverage of their own deployment against the report’s tested setup and recommended fallback; the report does not identify a fixed version or establish that those records are available to users.[^1]
:::

:::checked
On 21 November 2026 we read the saved web edition of Requant’s [“Verifiable GPU Inference: Batching, Proofs and Memory”](https://requant.network/research/gpu-verifiable-inference), evidence revision 4b784115420b. We did not run its code, inspect the underlying artifacts or test the system; the measurements and verification results above are Requant’s reports.[^1]
:::
