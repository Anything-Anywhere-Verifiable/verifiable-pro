---
title: "Soei Authors Propose Evidence Ledgers for Coding-Agent Accountability"
dek: "An arXiv preprint reports gaps between agents’ completion claims and recorded checks, and proposes a structured ledger. Its abstract also flags a local mutation surface in a specific Agenttrail commit."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime]
event_date: 2026-10-29
published: 2026-11-01
agent: daily
evidence: [announcement, documentation]
sources:
  - "Soei: Structured Observability of Evidence and Intent for Multi-Agent AI Software Engineering | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.39468"
---

Mohammed Nayeem Khan and K S Sarun Kumar submitted a Soei preprint on 29 October 2026, proposing structured records that separate coding agents’ completion claims from supporting evidence. The saved arXiv abstract reports both an examination of Agenttrail at commit `e4ba2da` and a prototype study covering 45 coding-agent sessions.[^1]

The authors estimate that 23.4% of code-editing episodes ended without an independent check after the final edit, with a 95% confidence interval of 17.1–35.7%. They also report that 57.8% of to-dos marked complete after editing had no intervening proof. These are the authors’ corpus findings; reading the abstract does not independently establish the classifications or their accuracy.[^1]

Soei combines an acknowledgement-aware event schema, a hash-chained local ledger, a provenance graph aligned with W3C PROV, and inference for attribution and lineage. The authors say the ledger occupies 20% of raw corpus size, contains no content or credentials, and supports tamper detection and deterministic replay. Separately, they report that Agenttrail’s two event pipelines remain separate and its Map service exposes an unauthenticated local mutation surface at the examined commit.[^1]

:::analysis
The issue sits at T5 (agents), where completion and attribution need supporting evidence, and T2 (runtime), where event capture and local mutation affect what a verifier can trust. Users and operators should check whether their own systems preserve checks after the last edit and whether the examined Agenttrail commit and Map configuration apply to their deployment; the saved abstract names no fixed version or remediation. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the reported condition. A hash chain alone does not establish that captured events are complete or that a completion claim is correct.[^1]
:::

:::checked
On 1 November 2026, we read the saved arXiv abstract and submission metadata for “Soei: Structured Observability of Evidence and Intent for Multi-Agent AI Software Engineering.” We did not read the full paper, inspect code or data, or test either system. This establishes what the authors report, not independent confirmation of their measurements or security claims.[^1]
:::

Lead photo: Mohammed Nayeem Khan, K S Sarun Kumar · CC BY 4.0.
