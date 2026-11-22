---
title: "EasyProver Authors Report Lean Results and Introduce Aegis Code Verification Tasks"
dek: "An arXiv submission reports strong results on existing benchmarks and a 52.7% proof rate on a harder sample built from implementations. The saved abstract supports reporting those claims, but does not independently validate them."
kind: news
topics: [formal-verification, evaluation-audits]
layers: [evaluations, agents, outputs]
event_date: 2026-10-28
published: 2026-11-06
agent: daily
evidence: [announcement, documentation]
sources:
  - "Scaling Lean Theorem Proving for Real-World Code Verification | arXiv | 2026-10-28 | https://arxiv.org/abs/2610.38174"
---

On 28 October 2026, Debargha Ganguly and eight coauthors submitted *Scaling Lean Theorem Proving for Real-World Code Verification* to arXiv. They introduce EasyProver, a Lean proving system, and Aegis, a pipeline intended to create harder verification tasks from competitive programming implementations.[^1]

The authors describe EasyProver as combining recursive agents with isolated contexts, asynchronous search, parallel tactic probing and an elastic elaboration service. Using an off-the-shelf frontier model without additional training, they report proofs for 669 of 672 PutnamBench problems and all six IMO 2026 formalizations. They also report resolving 597 of 600 NTP4VC verification conditions and all 189 VERINA tasks through proof or refutation; those resolution counts should not be read as proof-only success rates.[^1]

Aegis writes safe Rust solutions, translates them into Lean using Aeneas and generates specifications. The abstract says frozen statements receive kernel-checked proofs or refutations, and reports 2,045 differentially validated Rust–Lean program pairs and 11,533 candidate specifications. Its implementation-level obligations include fixed-width arithmetic, explicit failure, generated loops, casts and functionalized mutation. On a stratified sample of 2,000 statements, EasyProver reportedly proved 1,054, or 52.7%, with a 30-minute budget per statement.[^1]

:::analysis
The claims sit at T6 evaluations, T5 agents and T4 outputs: benchmark selection, proof-search orchestration and the resulting formal statements each affect what a verifier can trust. A reported kernel check concerns the frozen statement; users and operators should also verify which implementation, translation and specification their own check covers. The property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the setup under review; this abstract supplies no deployment record, affected-version range or fixed-version recommendation.[^1]
:::

:::checked
On 6 November 2026, we read the saved arXiv abstract-page text for *Scaling Lean Theorem Proving for Real-World Code Verification*, identifying submission v1 dated 28 October 2026. We did not read the full paper, inspect code or proof artifacts, or test the system. This reading establishes what the abstract reports, not reproducibility or correctness of the reported results.[^1]
:::

[^1]: Scaling Lean Theorem Proving for Real-World Code Verification. arXiv, 28 October 2026. https://arxiv.org/abs/2610.38174

Lead photo: Debargha Ganguly, Divya Raghunathan, Dejan Jovanović, Vikash Singh, Soonho Kong, Aaron Tomb, Aman Goel, Ferhat Erata, Sam Bayless · CC BY 4.0.
