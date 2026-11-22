---
title: "Amazon Says BenchProofer Adds Formal Checks to Coding Benchmarks"
dek: "The open-source tool generates specifications and machine-checked proofs for benchmark tasks. Amazon reports that additional audits found defects in some patches that passed existing tests."
kind: news
topics: [evaluation-audits, formal-verification]
layers: [evaluations]
event_date: 2026-11-16
published: 2026-11-19
agent: daily
evidence: [announcement, documentation]
sources:
  - "BenchProofer: Formally verified coding benchmarks, on demand | www.amazon.science | 2026-11-16 | https://www.amazon.science/blog/benchproofer-formally-verified-coding-benchmarks-on-demand"
---

On 16 November 2026, Amazon announced BenchProofer, an open-source tool that adds formal-verification artifacts to coding benchmarks. The company also released SWE-Proof, which applies the approach to all 500 tasks in SWE-Bench Verified. The aim is to expose errors that a benchmark’s existing tests might miss.[^1]

For each task, BenchProofer uses a problem description, an accepted reference solution and a way to test fixes. It generates a formal specification, a reference implementation and a proof that the implementation satisfies the specification under stated assumptions. A verifier checks the proof; tests and audits assess how the implementation corresponds to the repository code. Contracts for existing functions called by new code are tested rather than formally verified, Amazon says.[^1]

In audit mode, additional tests look for behavioral differences between a test-passing patch and the reference. In verified mode, an agent receives a specification and produces both a repository patch and a separate implementation for verification; an audit checks their correspondence. Amazon reports that its audit flagged 134 of 425 Claude Opus 4.8 patches that passed the original tests. Human reviewers found defects in 21 of a sample of 41 flagged patches; the other 20 were valid fixes.[^1]

:::analysis
The claim sits at T6, the evaluations layer: a checked proof establishes that a particular implementation meets a particular specification within its assumptions, while the specification’s faithfulness and its correspondence to the repository patch still require assessment. Users and operators should check their own benchmark’s specifications, assumptions, test results and audit findings, including whether the checked implementation matches the deployed patch. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue; the announcement does not establish such records for a deployment.[^1]
:::

:::checked
On 19 November 2026, we read the saved Amazon Science article “BenchProofer: Formally verified coding benchmarks, on demand,” published on 16 November 2026: https://www.amazon.science/blog/benchproofer-formally-verified-coding-benchmarks-on-demand.[^1] We did not test BenchProofer, inspect its released artifacts or independently reproduce Amazon’s results. The source does not recommend a fixed version for an identified vulnerability.
:::
