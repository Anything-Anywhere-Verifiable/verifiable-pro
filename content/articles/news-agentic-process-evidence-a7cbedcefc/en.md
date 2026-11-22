---
title: "Researchers Propose Signed Evidence for AI Agent Processes"
dek: "Agentic Process Evidence would link agent sessions to their outcomes. The saved arXiv abstract describes the proposal but does not establish implementation performance or deployment guarantees."
kind: news
topics: [agents-accountability, supply-chain]
layers: [institutions, agents, runtime]
event_date: 2026-10-29
published: 2026-10-30
agent: daily
evidence: [announcement, documentation]
sources:
  - "Agentic process evidence | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.40071"
---

Yuval Kainan and Carmit Hershman proposed Agentic Process Evidence (APE) in an arXiv submission dated 29 October 2026. The authors describe APE as signed, tamper-evident, machine-readable evidence linking AI agent sessions to their outcomes, intended to make software development processes more accountable.[^1]

The abstract identifies a gap between recording code changes and recording the decisions behind them. It argues that a git log does not capture what an agent did, which model it used, which tools it called, or who was accountable. The authors group the resulting procedural problems into software supply-chain risk, compliance with organizational policies, and alignment with assigned tasks and goals.[^1]

APE is presented as process-aware logging that supports policy-as-code controls and human intervention when needed. The authors say it supports an in-toto-style attestation framework and aligns with relevant regulations. The saved abstract does not name those regulations or provide enough detail to assess that alignment; its descriptions of signatures and tamper evidence remain proposal claims here.[^1]

:::analysis
The proposal sits at T7 institutions, T5 agents, and T2 runtime: organizational accountability depends on evidence connecting agent actions to the environment that performed them. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular deployment; the abstract does not establish that APE captures those details. Users and operators should verify whether their own records identify the model, tools, session, outcome, and deployed version and configuration, and what supports the claimed signatures and tamper evidence. The source recommends no fixed software version, and a signed process record alone does not establish that an agent followed policy or completed its task correctly.[^1]
:::

:::checked
On 30 October 2026, we read the saved arXiv abstract page for “Agentic process evidence,” arXiv:2610.40071v1, including its submission history. This establishes what the authors proposed and the submission date. We did not read the full paper, inspect an implementation, or test the system; we did not independently validate its security or regulatory claims.[^1]
:::

[^1]: Agentic process evidence. arXiv, 29 October 2026. https://arxiv.org/abs/2610.40071
