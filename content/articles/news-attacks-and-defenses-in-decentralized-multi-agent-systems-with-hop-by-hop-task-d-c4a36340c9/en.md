---
title: "Researchers Report Attacks and Trace-Based Auditing for Decentralized AI Agents"
dek: "A preprint describes attacks by malicious agents and proposes cryptographic execution traces and an auditor. Its reported results come from the authors’ evaluation, which we did not independently test."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-18
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Attacks and Defenses in Decentralized Multi-Agent Systems with Hop-by-Hop Task Decomposition and Delegation | arXiv | 2026-11-18 | https://arxiv.org/abs/2611.25056"
---

On 18 November 2026, researchers submitted a preprint describing attacks on decentralized systems of AI agents and proposing a way to record and audit their actions. In the system described, independently operated agents decompose tasks, perform subtasks and delegate remaining work to peers; no single operator has a complete view of execution or authority over every agent.[^1]

The authors report that, in their attacks, one malicious agent caused up to 100% task failure, increased token consumption by up to 7.7 times and runtime by up to 3.2 times, and extracted up to 94% of relevant prior tasks from benign agents. These are the authors’ reported maxima, not expected results for every deployment.[^1]

The proposed defense combines a cryptographic protocol for an execution trace with an auditor that analyzes traces to detect and attribute malicious behavior. The authors claim that the protocol produces a verified trace of every system action. They report that, in an evaluation on HiddenBench using gpt-6.1-sol and Qwen3.8-27B-FP8, the auditor detected and correctly attributed 98% of attacks, including attacks that complied with the protocol, while the protocol added negligible latency. The abstract does not establish those results for other systems or configurations.[^1]

:::analysis
The issue sits at T6, evaluations, and T5, agents: the reported detection rate concerns an evaluation, while the trace concerns accountability for agents’ actions. A user or verifier must still assess whether the trace and auditor apply to their own deployment; the abstract does not establish that an action was correct merely because it was recorded. The verifiable property at stake includes **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant vulnerability. Users and operators should check their own versions, configurations and audit coverage; the saved source recommends no fixed version.[^1]
:::

:::checked
On 24 November 2026, we read the saved arXiv abstract page for [“Attacks and Defenses in Decentralized Multi-Agent Systems with Hop-by-Hop Task Decomposition and Delegation”](https://arxiv.org/abs/2611.25056), submitted on 18 November 2026.[^1] We did not read the full paper or test the system, attacks, protocol or auditor, and could not independently confirm the reported results.
:::

Lead photo: Matthew D. Laws, Maria Lazou, Alina Oprea, Cristina Nita-Rotaru · CC BY 4.0.
