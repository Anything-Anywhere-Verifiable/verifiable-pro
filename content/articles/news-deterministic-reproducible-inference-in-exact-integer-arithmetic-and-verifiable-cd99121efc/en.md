---
title: "Tritify Paper Claims Exact Integer Inference Enables Reproducible Distributed Outputs"
dek: "An arXiv preprint reports matching output bytes across hardware and distributed execution. Its abstract explicitly leaves guarantees against dishonest servers to future work."
kind: news
topics: [verifiable-inference]
layers: [models, runtime, hardware]
event_date: 2026-11-10
published: 2026-11-15
agent: daily
evidence: [announcement, documentation]
sources:
  - "Deterministic, Reproducible Inference in Exact Integer Arithmetic, and Verifiable Distributed Inference as Its Consequence | arXiv | 2026-11-10 | https://arxiv.org/abs/2611.13730"
---

Sayed Amir Karim of Pelloran Inc. submitted a preprint on 10 November 2026 describing tritify, an open-source runtime that, according to its abstract, executes model forward passes entirely in exact integer arithmetic. Floating point remains in offline quantization and the reference used for verification. The reported scope includes decoder-only language models, Mixture-of-Experts (MoE) decoders, and the Segment Anything 2.1 image/video stack.[^1]

The abstract separates three claims: bit-identical outputs across runs and hardware, agreement with the floating-point reference’s decisions on tested models and inputs, and unchanged output bits when computation moves between machines. It reports a reproducing SHA-256 output digest and measured numeric exceptions to decision fidelity. These are distinct checks: matching output bytes and matching reference decisions establish different properties.[^1]

For distributed execution, the author reports that GLM-4.5-Air, with 106,852,251,264 parameters and 427 GB of integer codes, generated an answer across three machines bit-identically to a single-host reference. None of those machines could hold all its integer codes in RAM. The proposed verification approach uses an open scalar oracle to re-derive exact bytes; the abstract explicitly leaves a guarantee against a dishonest server to future work. It claims neither a per-device speedup nor confidentiality.[^1]

:::analysis
The claims sit at T3 models, T2 runtime and T1 hardware: they concern model decisions, execution arithmetic and consistency across devices, respectively. Re-execution offers a basis for checking output agreement, while the source leaves protection against dishonest servers unresolved. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that execution setup. Users and operators should check those records and whether their models, inputs and execution paths fall within the reported scope; the saved abstract specifies no recommended deployment version.[^1]
:::

:::checked
On 15 November 2026, we read the saved arXiv abstract page for “Deterministic, Reproducible Inference in Exact Integer Arithmetic, and Verifiable Distributed Inference as Its Consequence,” identified as arXiv:2611.13730v1. This establishes what the author reports and the submission date. We did not read the full paper or code, test the system, or independently reproduce its results.[^1]
:::

[^1]: https://arxiv.org/abs/2611.13730
