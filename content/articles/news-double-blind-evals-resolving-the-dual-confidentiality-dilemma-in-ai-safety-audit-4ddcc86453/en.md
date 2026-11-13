---
title: "Double Blind Evals Authors Report Confidential AI Safety Audit Pilot"
dek: "An arXiv preprint describes evaluating Gemini 2.5 Flash Lite against private AILuminate prompts using an NVIDIA H100 secure enclave and PySyft. The saved abstract reports mutual confidentiality, but does not independently establish its guarantees."
kind: news
topics: [evaluation-audits, confidential-computing]
layers: [evaluations, runtime, hardware]
event_date: 2026-11-09
published: 2026-11-13
agent: daily
evidence: [announcement, documentation]
sources:
  - "Double Blind Evals: Resolving the Dual Confidentiality Dilemma in AI Safety Auditing | arXiv | 2026-11-09 | https://arxiv.org/abs/2611.12604"
---

Andrew Trask and coauthors submitted *Double Blind Evals: Resolving the Dual Confidentiality Dilemma in AI Safety Auditing* to arXiv on 9 November 2026. The preprint reports a pilot intended to keep evaluation prompts confidential from a model owner while preserving the confidentiality of proprietary model weights and inference code.[^1]

The abstract describes competing requirements: evaluators want secret prompts to avoid deliberate or incidental leakage and preserve benchmark usefulness; model owners want weights and inference code to remain within their own secure infrastructure. The authors propose secure enclaves, described as encrypting data in RAM at the hardware level, to support this arrangement.[^1]

For the pilot, the authors report evaluating Google DeepMind’s Gemini 2.5 Flash Lite against a selection of the private AILuminate benchmark corpus. They identify an NVIDIA H100 secure enclave on Google Cloud Platform and OpenMined’s PySyft as components. The abstract claims cryptographic guarantees for prompt confidentiality alongside confidentiality of weights and inference code, and describes the pilot as a first. These are author claims; the saved abstract supplies no evaluation scores, detailed threat model or independent validation.[^1]

:::analysis
The claim spans T6 evaluations, T2 runtime and T1 hardware: confidence in the audit’s confidentiality depends on the evaluation arrangement, its software and its enclave mechanism, while confidentiality alone does not establish model safety. Users and operators should seek checkable records connecting their evaluation or service session to the exact model, software versions and enclave configuration; the saved abstract names components but gives no fixed software version or configuration checklist. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the deployment in question; the abstract does not establish that this capability exists.[^1]
:::

:::checked
On 13 November 2026, we read the saved arXiv abstract-page text for arXiv:2611.12604, whose submission history identifies v1. This establishes what the page reports, including its submission date and named pilot components. We did not read the full paper, inspect code or attestation evidence, or test the system; we cannot independently confirm the confidentiality or priority claims.[^1]
:::

[^1]: *Double Blind Evals: Resolving the Dual Confidentiality Dilemma in AI Safety Auditing*. arXiv, 9 November 2026. https://arxiv.org/abs/2611.12604
