---
title: "Paper Proposes Intent-Graph Auditing for Agent Tool Calls"
dek: "An arXiv paper describes deterministic checks and a reasoning guardian for flagged calls, while explicitly leaving end-to-end attack validation open."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-11-08
published: 2026-11-14
agent: daily
evidence: [announcement, documentation]
sources:
  - "Least-Privilege Auditing of Agent Tool Calls with Intent Graphs and Reasoning-Guided Escalation | arXiv | 2026-11-08 | https://arxiv.org/abs/2611.11305"
---

Doron Shavit submitted a paper to arXiv on 8 November 2026 proposing a runtime audit for tool-using agents exposed to indirect prompt injection: instructions hidden in tool outputs that steer an agent toward actions the user did not request. The abstract describes a way to check tool calls against the user's objective, but explicitly says end-to-end validation remains open.[^1]

The proposed audit uses one large language model (LLM) call per task to derive an executable intent graph from the objective and the deployment's tool catalog. A deterministic loop then checks each tool call against that graph without additional LLM calls. The abstract reports a median of 5.7 microseconds per call; that is the author's reported measurement, which we have not reproduced.[^1]

Two mechanisms aim to recover utility. Lookups of the user's own state bypass the audit, based on the author's rationale that an attack's harm lies in its write or outward step. Remaining flagged calls go to a reasoning guardian. It receives the objective, plan, call history without tool outputs, and flagged call, and can check facts using a restricted Python-expression tool. The abstract also says a current agent showed no baseline attack success, leaving the proposed defense's end-to-end validation unresolved.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T2 runtime: reported check speed does not establish attack resistance, and users still depend on how intent is derived and exceptions are applied. Users and operators should verify their deployed tool catalog, lookup exemptions and guardian inputs against the described design; the saved source recommends no fixed software version.[^1] The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant deployment, while effectiveness remains a separate question.
:::

:::checked
On 14 November 2026, we read the saved arXiv abstract-page text for “Least-Privilege Auditing of Agent Tool Calls with Intent Graphs and Reasoning-Guided Escalation,” identifying submission v1. We did not read the full paper or test the system. This check establishes what the saved abstract reports, without independently confirming performance or security effectiveness.[^1]
:::

[^1]: https://arxiv.org/abs/2611.11305
