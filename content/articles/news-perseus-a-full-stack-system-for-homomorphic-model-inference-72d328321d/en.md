---
title: "Perseus Authors Report Faster Homomorphic Model Inference"
dek: "An arXiv submission describes a Python library spanning encrypted inference and claims faster Llama-3-8B decoding. The saved abstract supports reporting those claims, but does not independently establish performance or deployment security."
kind: news
topics: [verifiable-inference]
layers: [models, runtime]
event_date: 2026-11-03
published: 2026-11-04
agent: daily
evidence: [announcement, documentation]
sources:
  - "Perseus: A Full-Stack System for Homomorphic Model Inference | arXiv | 2026-11-03 | https://arxiv.org/abs/2611.04488"
---

Alessandro Zirilli and co-authors submitted *Perseus: A Full-Stack System for Homomorphic Model Inference* to arXiv on 3 November 2026. They describe Perseus as a free and open Python library covering encrypted inference, from its cryptographic backend and data packing through encrypted nonlinear operations and end-to-end model execution.[^1]

Fully homomorphic encryption (FHE) enables computation directly on encrypted data. The authors frame its computational cost and fragmented tooling as barriers to practical remote inference. Their proposed optimizations span three levels: regenerating key-switching keys inside kernels, a complex variant of Cachemir data packing, and a bootstrap placer that accounts for both packing and numerical magnitude.[^1]

The abstract claims state-of-the-art latency across multiple models and modalities, with accuracy and perplexity within 3% of plaintext models. It also reports single-token decoding on Llama-3-8B that is 3.96 times faster than any other implementation, and announces a public encrypted GPT-2 speedrun. These are the authors’ reported results; the saved abstract does not supply the benchmark configurations or comparison details needed to assess those claims independently.[^1]

:::analysis
The claims sit at T3 (models) and T2 (runtime): model execution and the software machinery performing encrypted computation. Reading this source establishes what the authors claim, while leaving their implementation and measurements to trust; it does not establish that a particular service uses that implementation. Users and operators should verify the exact library version, model, packing and execution configuration behind their own service before applying these performance claims; the saved source recommends no fixed software version. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the deployment under examination, although this record alone establishes neither security nor correct inference.[^1]
:::

:::checked
On 4 November 2026, we read the saved arXiv abstract page for arXiv:2611.04488, including its submission history identifying v1 on 3 November. We did not read the full paper, inspect code, or test the system. This preview establishes the submission metadata and the claims present in that saved page, without independently confirming speed, accuracy, openness or security.[^1]
:::

[^1]: [Perseus: A Full-Stack System for Homomorphic Model Inference](https://arxiv.org/abs/2611.04488), arXiv, 3 November 2026.
