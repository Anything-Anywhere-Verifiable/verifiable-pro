---
title: "Researchers Question Cipher-Based Power Attacks on Complete Neural Networks"
dek: "An arXiv preprint reports obstacles to extracting trained models’ weights even with idealized, noiseless leakage. The saved abstract supports a narrower conclusion than a deployment security assurance."
kind: news
topics: [evaluation-audits]
layers: [models, runtime, hardware]
event_date: 2026-11-09
published: 2026-11-15
agent: daily
evidence: [announcement, documentation]
sources:
  - "ML Models Are Not Ciphers: Power Analysis for Weight Extraction Is Harder Than You Think | arXiv | 2026-11-09 | https://arxiv.org/abs/2611.12532"
---

Mohammed Qaiss and seven coauthors submitted an arXiv preprint on 9 November 2026 questioning whether power-analysis methods adapted from cryptographic attacks can recover complete, trained neural networks. The authors report fundamental obstacles even when an attacker directly observes a leakage model’s output without added noise, an assumption they describe as unrealistically strong.[^1]

Power analysis seeks to infer secrets from computation-related power leakage; here, the targets are model weights. According to the abstract, earlier demonstrations recover only some weights, typically in shallow layers. This study instead considers complete networks that are fully trained and functional, rather than randomly initialized networks.[^1]

The authors identify two obstacles. Limited-precision floating-point arithmetic and linear operations with low diffusion can require unexpectedly many traces for weight recovery, even under ideal channel conditions. They also argue that models reduce data entropy as computation progresses, limiting variability and making deeper layers harder to recover. These are the authors’ reported findings; the saved abstract supplies no numerical trace counts or deployment-specific exposure assessment.[^1]

:::analysis
The claim spans T3 models, T2 runtime and T1 hardware: network behavior, numerical operations and power leakage jointly shape what an extraction evaluation can establish. Users and operators should check whether their own model, arithmetic configuration and leakage assumptions match those evaluated before relying on the reported difficulty; this source names no fixed software version or remediation. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an identified affected configuration, although this abstract identifies no such deployment and cannot establish whether extraction occurred. Difficulty recovering complete networks leaves partial extraction and other configurations unresolved.[^1]
:::

:::checked
On 15 November 2026, we read the saved arXiv abstract page for *ML Models Are Not Ciphers: Power Analysis for Weight Extraction Is Harder Than You Think*, arXiv:2611.12532v1, including its submission history. This establishes what the authors reported and the 9 November submission date. We did not read the full paper, inspect code, reproduce experiments or test any system; we therefore cannot independently confirm the extraction results or their applicability to a deployed service.[^1]
:::
