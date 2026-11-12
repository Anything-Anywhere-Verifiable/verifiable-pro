---
title: "Researchers Propose Call-Level Contracts for Revising LLM Workflows"
dek: "An arXiv paper proposes static and runtime checks to govern reuse of completed calls after model-written workflows change. Its abstract reports replay results, with guarantees conditional on three assumptions."
kind: news
topics: [agents-accountability, formal-verification]
layers: [agents, runtime]
event_date: 2026-11-04
published: 2026-11-11
agent: daily
evidence: [announcement, documentation]
sources:
  - "Call-Level Revision Contracts for LLM-Authored Workflows | arXiv | 2026-11-04 | https://arxiv.org/abs/2611.06967"
---

Chenyang Jiang, Benyang Pan and Puqu Wu submitted *Call-Level Revision Contracts for LLM-Authored Workflows* to arXiv on 4 November 2026. The paper proposes a contract for repairing workflows written by a large language model (LLM), addressing when completed calls can be reused after orchestration code changes.[^1]

The abstract says durable execution engines replay recorded history without comparing activity payloads. Its proposed contract gives each capability call a structural identity combining its callsite, fanout position and occurrence count. Committed call expressions become frozen while surrounding code remains editable. A static gate rejects changes to committed calls before a container starts; a runtime digest stops changed payloads at committed identities; an occurrence ledger identifies repeated paid payloads.[^1]

The authors claim that, under three assumptions, an accepted revision replays every committed call it invokes, executes only new work and reports skipped identities. The saved abstract does not enumerate those assumptions. It also describes a limit: local identity cannot both survive relocation and avoid incorrect reuse, so relocating a call triggers a stop before spending.[^1]

The abstract reports that 22 gate-passed media-workflow repairs replayed 258 committed identities without duplicates, and that a live six-way fanout made seven paid calls instead of twelve. It also describes a 12-task customer-support study using two models. These are author-reported results.[^1]

:::analysis
The issue sits at T5 (agents), where model-authored revisions change workflows, and T2 (runtime), where checks govern replay and execution: trusting a revision therefore depends on both its acceptance and runtime enforcement. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the replay behavior in question. Users and operators should check their own identity rules, gate and digest enforcement, and skipped-call records against the proposed contract; the saved source recommends no fixed software version.[^1]
:::

:::checked
On 11 November 2026, we read the supplied saved arXiv abstract page and submission history for arXiv:2611.06967v1. This establishes what the abstract reports and its submission date. We did not read the full paper, inspect code, test the system or independently reproduce the results.[^1]
:::

[^1]: [Call-Level Revision Contracts for LLM-Authored Workflows](https://arxiv.org/abs/2611.06967), arXiv, submitted 4 November 2026.
