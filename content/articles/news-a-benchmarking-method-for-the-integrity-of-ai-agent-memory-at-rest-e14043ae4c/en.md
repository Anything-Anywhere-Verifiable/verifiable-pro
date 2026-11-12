---
title: "Internet-Draft Proposes Tests for AI Agent Memory Tampering"
dek: "The proposed benchmark distinguishes detection during memory reads from later audits and tests whether restoring a backup can resurrect erased records."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents, runtime]
event_date: 2026-11-01
published: 2026-11-12
agent: daily
evidence: [announcement, documentation]
sources:
  - "A Benchmarking Method for the Integrity of AI Agent Memory at Rest | www.ietf.org | 2026-11-01 | https://www.ietf.org/ietf-ftp/internet-drafts/draft-khandelwal-bpm-agent-memory-integrity-00.html"
---

Y. Khandelwal of Tech4Biz Solutions published an Internet-Draft on 1 November 2026 proposing a laboratory benchmark for detecting changes to AI agents’ stored memory. “A Benchmarking Method for the Integrity of AI Agent Memory at Rest,” revision draft-khandelwal-bpm-agent-memory-integrity-00, is work in progress with intended Informational status, rather than an adopted standard.[^1]

The method assumes an adversary can write to storage but holds none of the memory subsystem’s cryptographic keys. Evaluators seed memory through the subsystem’s interface, stop it, apply one storage edit, restart it and retrieve memory through its normal read path. Ten edits cover content changes, deletion, reordering, insertion, replay, metadata changes, whole-store rollback and restoration of records erased through the subsystem’s own interface.[^1]

The draft distinguishes refusal to serve affected memory, serving it with an integrity signal, and silent acceptance. Read-time refusal or reporting receives full credit; detection only through a separate audit receives half credit. Controls require normal reloads and genuine writes to work and confirm that each edit actually landed. Inapplicable cases are excluded rather than counted as passes, and the method sets no acceptable-score threshold.[^1]

The abstract reports 31 result rows, including 18 claiming tamper evidence, with the new erasure-restoration edit measured on seven. The saved excerpt does not include the illustrative-results section, so those figures remain the author’s report here.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T2 runtime: benchmark evidence concerns a particular memory subsystem and configuration, leaving confidentiality and reasoning correctness outside its scope. Users and operators should verify the exact component and backend versions, enabled protections, detection point and whether the tested configuration matches deployment, as the draft’s reporting rules require. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the evaluated setup; a score alone cannot establish that match.[^1]
:::

:::checked
On 12 November 2026, we read the supplied saved excerpt of the IETF-hosted Internet-Draft, through the opening of Section 10’s result-publication requirements. We did not inspect linked materials, reproduce the reported results or test any system. This reading establishes what the proposal specifies, not deployed protection.[^1]
:::

[^1]: [A Benchmarking Method for the Integrity of AI Agent Memory at Rest](https://www.ietf.org/ietf-ftp/internet-drafts/draft-khandelwal-bpm-agent-memory-integrity-00.html), Y. Khandelwal, IETF Internet-Draft, 1 November 2026.
