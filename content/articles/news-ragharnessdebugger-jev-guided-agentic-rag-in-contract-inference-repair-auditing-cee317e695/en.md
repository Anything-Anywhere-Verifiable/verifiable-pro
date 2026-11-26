---
title: "Researchers Present RagHarnessDebugger for Auditing RAG Repair Decisions"
dek: "An arXiv abstract describes a framework for tracing and auditing how an agentic retrieval system repairs contract inference answers. Its reported results are claims from the authors; the system was not tested for this article."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-11-17
published: 2026-11-26
agent: daily
evidence: [announcement, documentation]
sources:
  - "RagHarnessDebugger: Jev-Guided Agentic RAG in Contract Inference Repair Auditing | arXiv | 2026-11-17 | https://arxiv.org/abs/2611.22991"
---

Researchers presented RagHarnessDebugger in a paper submitted to arXiv on 17 November 2026. The framework records and audits decisions made while an agentic retrieval-augmented generation (RAG) system repairs answers in contract inference, according to the paper’s abstract.[^1]

RAG combines generation with retrieved evidence. The authors describe repair as a process in which a system gathers more evidence, tests alternative policies and decides whether and how to revise an answer. Their proposed debugger uses a Jev-guided harness to record that process. The abstract says it checks trace integrity, whether a validation applies to the candidate for which it is counted, and which answers an acceptance rule can reach.[^1]

The authors report testing on ContractNLI non-disclosure agreements with two reader models and a separate set of contracts for replication. They say the audit exposed failure patterns obscured by aggregate metrics, including available repairs that the acceptance policy did not realize. They also report accuracy improvements over an initial BM25-only baseline and a full-contract-access reference. These are the authors’ results; the abstract alone does not establish how the system would perform on other contracts or deployments.[^1]

:::analysis
The work sits at T6, evaluations, and T5, agents: the proposed audit examines the decisions an agent makes, while its reported findings depend on the traces and checks available to the evaluator. A user or verifier must still trust that the recorded trace corresponds to the actual execution and that the evaluation applies to their use. Operators should check which version, configuration, traces and acceptance rules their own system uses before applying these findings. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the system or behavior in question; the abstract does not establish that such records are available.[^1]
:::

:::checked
On 26 November 2026 we read the saved arXiv abstract page for “RagHarnessDebugger: Jev-Guided Agentic RAG in Contract Inference Repair Auditing.” We did not read the full paper or test the system, and could not independently confirm the reported results. The saved abstract recommends no fixed version.[^1]
:::
