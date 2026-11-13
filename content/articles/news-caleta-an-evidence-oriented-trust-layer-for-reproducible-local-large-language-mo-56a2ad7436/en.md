---
title: "Caleta Paper Proposes an Evidence Layer for Local LLM Inference"
dek: "The paper combines artifact checks and execution records while identifying unresolved provenance and isolation limits. Its reported experiment covers one Windows CPU configuration."
kind: news
topics: [verifiable-inference, supply-chain]
layers: [models, runtime]
event_date: 2026-11-06
published: 2026-11-13
agent: daily
evidence: [announcement, documentation]
sources:
  - "Caleta: An Evidence-Oriented Trust Layer for Reproducible Local Large Language Model Inference | arXiv | 2026-11-06 | https://arxiv.org/abs/2611.10324"
---

Joan-Marc Fisa of BiVelio Inc submitted a paper introducing Caleta to arXiv on 6 November 2026. The abstract describes an Apache-2.0 process supervisor and evidence layer for local large language model (LLM) inference, built around an existing backend. It separates claims about integrity, provenance, privacy controls, and reproducibility into explicit contracts.[^1]

According to the abstract, Caleta combines versioned manifests, exact-size and SHA-256 artifact verification, controlled backend construction, a restricted OpenAI-compatible proxy, execution records without prompts, benchmark reports, and a small conformance suite. The paper distinguishes artifact integrity from authenticated provenance, and privacy controls from operating-system isolation. Signed manifests, replacement between checking and use, and operating-system containment remain identified challenges.[^1]

The author reports static checks, 22 unit tests, deterministic end-to-end tests on Ubuntu, macOS, and Windows, and a real-model experiment on Windows CPU using Qwen2.5-0.5B-Instruct Q4_K_M with backend build b11981. Three benchmark invocations reportedly yielded 15 successful warm requests without failures. The reported median time to first token was 18.066 milliseconds and median decode throughput was 54.394 tokens per second. The abstract explicitly limits these measurements to that configuration; they establish neither cross-engine superiority nor output quality, energy efficiency, or performance across hardware.[^1]

:::analysis
The claims sit at T3 models and T2 runtime: artifact checks concern model files, while backend construction and execution records concern how inference is launched and documented. A verifier still needs to distinguish matching bytes from authenticated origin and operating-system containment, which the abstract treats separately. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular configuration. Users and operators should check their own manifest, artifact checks, backend build, and execution metadata; the abstract recommends no fixed version and leaves replacement after checking unresolved.[^1]
:::

:::checked
On 13 November 2026, we read the saved arXiv abstract-page text for “Caleta: An Evidence-Oriented Trust Layer for Reproducible Local Large Language Model Inference,” including its v1 submission history. This establishes what the abstract reports. We did not read the full paper, inspect the claimed published raw data or code, reproduce the benchmarks, or test the system.[^1]
:::

[^1]: https://arxiv.org/abs/2611.10324
