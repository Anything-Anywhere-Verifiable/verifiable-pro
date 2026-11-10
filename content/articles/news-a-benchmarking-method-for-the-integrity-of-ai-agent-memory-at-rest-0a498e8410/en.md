---
title: "Internet-Draft Proposes Tests for AI Agent Memory Tampering and Erasure Reversal"
dek: "An individual Internet-Draft adds a backup-restoration test for erased agent memory and specifies how evaluators should distinguish read-time detection from later audits."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents, runtime]
event_date: 2026-11-01
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "A Benchmarking Method for the Integrity of AI Agent Memory at Rest | datatracker.ietf.org | 2026-11-01 | https://datatracker.ietf.org/doc/html/draft-khandelwal-bpm-agent-memory-integrity-00"
---

Yasha Khandelwal published an individual Internet-Draft on 1 November 2026 proposing a laboratory method for measuring whether AI agent memory subsystems detect storage tampering before serving persisted memory as genuine. The document, *A Benchmarking Method for the Integrity of AI Agent Memory at Rest*, is work in progress; its Datatracker notice says it is not endorsed by the IETF and has no formal standing in the IETF standards process.[^1]

Revision `draft-khandelwal-bpm-agent-memory-integrity-00` defines ten storage edits. Its new erasure-resurrection case restores a complete backup taken before a record was deleted through the subsystem’s own interface. This asks whether an acknowledged erasure survives restoration of older, otherwise genuine storage contents. The assumed adversary can write to storage but holds none of the subsystem’s cryptographic keys.[^1]

Evaluators stop the subsystem, apply an edit, restart it and read through its own interface. Refusal or an integrity signal before or while serving memory earns a pass; detection only through a separate audit earns half credit. Controls require unchanged memory to remain readable, genuine writes after restart to work, and confirmation that each edit actually landed. Inapplicable cases are excluded rather than counted as passes. The method sets no acceptable-score threshold and does not measure confidentiality, prompt-injection resistance or reasoning correctness.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T2 runtime: a benchmark result supports a claim about memory handling only within its stated test boundary and configuration. Users and operators should verify the deployed version, integrity settings, dependencies, integrity-head location and whether detection occurs on reads or only during audits, as the draft requires these distinctions for comparison. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the configuration under assessment; a score alone cannot establish that deployment link.[^1]
:::

:::checked
On 10 November 2026, we read the saved excerpt of this draft’s official IETF Datatracker HTML page, ending partway through Section 9. It establishes the proposed procedure; the abstract’s claims of 31 result rows and seven measurements of the new edit were not independently verified. We did not test any system or inspect the later results or reference implementation.[^1]
:::

[^1]: A Benchmarking Method for the Integrity of AI Agent Memory at Rest. IETF Datatracker, 1 November 2026. https://datatracker.ietf.org/doc/html/draft-khandelwal-bpm-agent-memory-integrity-00
