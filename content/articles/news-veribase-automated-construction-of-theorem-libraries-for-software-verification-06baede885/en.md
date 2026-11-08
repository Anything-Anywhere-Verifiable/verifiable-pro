---
title: "VeriBase Authors Report Gains From Automatically Built Verification Libraries"
dek: "A new preprint describes jointly generalizing code, theorem statements and proofs, with Lean checking the results. Its abstract reports benchmark gains, but the saved source does not establish reproducibility."
kind: news
topics: [formal-verification, evaluation-audits]
layers: [evaluations, outputs]
event_date: 2026-11-01
published: 2026-11-06
agent: daily
evidence: [announcement, documentation]
sources:
  - "VeriBase: Automated Construction of Theorem Libraries for Software Verification | arXiv | 2026-11-01 | https://arxiv.org/abs/2611.01743"
---

Zihao Zhang and co-authors submitted VeriBase on 1 November 2026, proposing a framework that automatically builds reusable software-verification libraries from successful verification solutions. The arXiv abstract says the framework generalizes implementations together with their dependent theorem statements and proofs, addressing work that otherwise requires substantial expert effort.[^1]

VeriBase groups code and its associated theorems into “declaration families.” Its three phases prove seed tasks, generalize code and theorems, and harvest the resulting families into shared interfaces. The authors say it updates dependent declarations when interfaces change and uses Lean to check the resulting code and proofs. This makes the relationship between changed implementations and dependent proofs central to the proposal.[^1]

The authors report evaluation across four benchmarks with three backend large language models (LLMs). They say a general-purpose library built from 4,191 independent programs increases average task success rate by up to 17.0% and reduces proof completion time by up to 21.4%. The abstract also reports further improvement with benchmark-specific libraries, without quantifying it. These are author-reported results; the saved abstract does not specify whether the success-rate increase is relative or in percentage points.[^1]

:::analysis
The claims sit at T6 evaluations and T4 outputs: benchmark measurements concern performance, while Lean checking concerns the generated code and mathematical proofs; readers still need to inspect which theorem statements were checked and how they match the intended task. Users and operators should verify their own library artifacts, theorem statements, Lean checks and backend configuration before applying the reported gains to their systems. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that configuration; the saved abstract supplies no deployment record, fixed-version recommendation or means to establish that connection.[^1]
:::

:::checked
On 6 November 2026 we read the supplied saved arXiv abstract page for “VeriBase: Automated Construction of Theorem Libraries for Software Verification,” arXiv:2611.01743v1. It establishes what the authors publicly claim and the submission date. We did not read the full paper, inspect code, test the system or reproduce the benchmarks.[^1]
:::

[^1]: https://arxiv.org/abs/2611.01743
