---
title: "Researchers Present guardscope to Measure Agent Control Coverage"
dek: "The proposed framework compares runtime-control decisions with kernel-level observations to assess which agent actions are checked. Its authors report experiments but give no results in the saved abstract."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-11-11
published: 2026-11-17
agent: daily
evidence: [announcement, documentation]
sources:
  - "guardscope: Measuring Which Actions Runtime Controls Check in LLM Agent Systems | arXiv | 2026-11-11 | https://arxiv.org/abs/2611.15223"
---

Researchers introduced guardscope in a paper submitted on 11 November 2026, proposing a way to measure which actions an LLM agent’s runtime controls can check. The authors say a control sees only actions that cross its position in a system, while an agent may act through paths beyond the tool-call channel.[^1]

The paper describes two stages. First, static analysis predicts which of 15 agent action paths a control can check from its source. Second, an empirical stage runs a fixed workload on a deployment using one of eight topology designs. It reconciles the control’s decision records with kernel-level ground truth and classifies executed actions as checked, bypassed or prevented.[^1]

The authors say a control developer could use the framework to publish which paths its product inspects under a kernel-verified protocol. They report experiments with two agent harnesses and real runtime controls, including Microsoft’s agent governance toolkit and agentgateway. The saved abstract does not report the experiments’ results or identify a recommended fixed version.[^1]

:::analysis
The question spans evaluations (T6), agents (T5) and runtime (T2): a coverage assessment depends on the agent’s available action paths and where the runtime control is placed. A verifier should examine the workload, deployment topology, decision records and kernel-level observations behind any coverage claim; users and operators should check those details against their own systems rather than assume a published result applies to every deployment. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a specific identified gap, provided the affected conditions are known. The abstract does not establish that such records exist or identify an affected version.[^1]
:::

:::checked
On 17 November 2026 we read the saved arXiv abstract page for “guardscope: Measuring Which Actions Runtime Controls Check in LLM Agent Systems.”[^1] We did not read the full paper or test the framework, controls or deployments, and the abstract does not let us independently confirm the reported experiments or their results.
:::

[^1]: https://arxiv.org/abs/2611.15223
