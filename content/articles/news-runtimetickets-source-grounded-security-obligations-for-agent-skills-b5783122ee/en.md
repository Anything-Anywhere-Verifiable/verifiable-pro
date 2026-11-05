---
title: "RuntimeTickets Authors Propose Auditable Security Obligations for Agent Skills"
dek: "An arXiv preprint links approved security requirements to runtime checks and execution records. Its authors report zero missed malicious Skills and zero blocked benign Skills in their evaluation; we read only the saved abstract page."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime]
event_date: 2026-11-02
published: 2026-11-04
agent: daily
evidence: [announcement, documentation]
sources:
  - "RuntimeTickets: Source-Grounded Security Obligations for Agent Skills | arXiv | 2026-11-02 | https://arxiv.org/abs/2611.03772"
---

Kuiyi Gao, Xue Liu and Bowei He submitted RuntimeTickets to arXiv on 2 November 2026, proposing a protocol to enforce and audit security requirements while third-party agent Skills execute. The saved listing identifies version v1 and describes the paper as under review for ICLR 2027. It presents research claims, without announcing a production release.[^1]

The authors argue that a Skill’s description and tool permissions do not establish whether its execution meets a user’s security requirements. Their protocol uses a language model to propose task-specific obligations from the task’s delivery contract. Each obligation cites relevant Skill source lines; the ticket can tighten host approvals but cannot loosen them.[^1]

According to the abstract, a runtime gate checks the recipient, object and amount of every outbound send before forwarding it. Trusted monitors record effects within their observation scope, and a deterministic decoder checks obligations against ticket records. Neither enforcement nor decoding uses a language model. The authors say injected Skill text can influence proposals but cannot change the rule deciding a send.[^1]

The authors report evaluation at the network egress boundary of three unmodified agent frameworks, comparing RuntimeTickets with Skill scanners and runtime baselines. They report 0.0% overlook, meaning malicious Skills allowed through, and 0.0% overkill, meaning benign Skills blocked. Reading the abstract establishes that these results were reported; it does not independently validate them.[^1]

:::analysis
The claim sits at T5 agents and T2 runtime: trust depends on approved obligations, the gate’s enforcement and the monitors’ stated observation scope. Users and operators should check which Skill source, obligations, host approvals, gate and monitor configuration apply to their own runs. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant risk; the abstract does not establish that deployment record. It names no fixed version or upgrade recommendation.[^1]
:::

:::checked
On 4 November 2026, we read the supplied saved arXiv abstract and submission listing for RuntimeTickets, arXiv:2611.03772v1. We did not read the full paper, inspect code or test the system; the saved page does not provide enough experimental detail to assess reproducibility or coverage beyond the stated boundary.[^1]
:::

[^1]: [RuntimeTickets: Source-Grounded Security Obligations for Agent Skills](https://arxiv.org/abs/2611.03772), arXiv, 2 November 2026.
