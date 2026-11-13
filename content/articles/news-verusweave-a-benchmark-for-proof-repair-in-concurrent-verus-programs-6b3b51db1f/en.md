---
title: "VerusWeave Authors Report Benchmark for Concurrent Proof Repair"
dek: "The authors report 75 focused tasks and 17 full-module variants, with lower success rates on module-wide repairs. The saved abstract describes verifier checks but does not establish independently reproduced results."
kind: news
topics: [formal-verification, evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-10-30
published: 2026-11-13
agent: daily
evidence: [announcement, documentation]
sources:
  - "VerusWeave: A Benchmark for Proof Repair in Concurrent Verus Programs | arXiv | 2026-10-30 | https://arxiv.org/abs/2611.00287"
---

Pedro Ribeiro, Martim Afonso, André Vasconcelos and João F. Ferreira introduced VerusWeave in an arXiv submission dated 30 October 2026. The authors describe a benchmark for coding agents repairing mathematical proofs in concurrent Verus programs, addressing limited concurrency coverage in existing Verus benchmarks.[^1]

Verus extends Rust with formal verification capabilities. According to the abstract, VerusWeave draws on four open-source projects and contains 75 focused tasks and 17 full-module variants. Tasks remove selected proof annotations; agents must restore the missing material while preserving executable code and specifications. This constraint makes preservation of the original verification target part of the evaluation.[^1]

The authors say their evaluation harness checks repairs with Verus and a change checker, recording solutions, execution traces and resource usage. Their initial evaluation of four general-purpose coding-agent harnesses reports success rates of 75–85% on focused tasks and 29–47% on full-module variants. These are author-reported results; the saved abstract does not identify the four harnesses or provide their configurations or detailed scoring rules.[^1]

:::analysis
The claim sits at T6 (evaluations) and T5 (agents): the described checks provide a way to assess proof repairs against preserved code and specifications, while users still depend on the verifier and change checker. Users and operators should check which task variant, agent configuration and verifier setup produced a result, and whether both checks passed; the saved source supplies no recommended fixed version. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that setup; the abstract does not establish such deployment records.[^1]
:::

:::checked
On 13 November 2026, we read the saved arXiv abstract-page text for “VerusWeave: A Benchmark for Proof Repair in Concurrent Verus Programs,” including its submission history identifying v1. This reading establishes what the authors reported. We did not read the full paper, inspect code, run the benchmark or test the system, and did not independently confirm the success rates.[^1]
:::

[^1]: https://arxiv.org/abs/2611.00287
