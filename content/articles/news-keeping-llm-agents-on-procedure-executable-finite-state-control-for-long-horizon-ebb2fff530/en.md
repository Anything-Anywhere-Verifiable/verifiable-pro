---
title: "Researchers Report Finite-State Control Reduces Agent Procedure Drift"
dek: "An arXiv preprint reports better long-run procedural compliance by keeping workflow state outside the model. The saved abstract supports reporting the authors’ results, but does not independently establish deployment reliability."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-11-07
published: 2026-11-15
agent: daily
evidence: [announcement, documentation]
sources:
  - "Keeping LLM Agents on Procedure: Executable Finite-State Control for Long-Horizon Instruction Fidelity | arXiv | 2026-11-07 | https://arxiv.org/abs/2611.10884"
---

Yutao Sun and colleagues submitted a preprint on 7 November 2026 reporting that executable finite-state control improves language-model agents’ adherence to procedures over long runs. Their proposed finite-state machine (FSM) stores workflow state outside the model’s context and enforces the procedure at tool calls, state transitions and the end of an agent’s turn.[^1]

The authors say agents drift from procedures supplied at the start, and that repeating instructions or resuming a stopped agent merely shifts the shortcut they take. In an experiment described as pre-registered, using 200-account SOP-Bench batches, Claude Haiku 4.5 with the FSM averaged 139 accounts decided correctly and according to procedure, compared with 48 for the strongest baseline. The abstract reports a 95% confidence interval of [46, 130] for the difference and says performance persisted through the end of the run.[^1]

The authors also report that Haiku 4.5 with the FSM averaged more procedurally correct decisions than plain Claude Sonnet 4.6 at 38% of its cost. They describe additional analyses on SWE-bench Verified, τ²-bench, and staged and cross-context workflows as suggesting benefits from stronger execution control. These are research claims reported in the abstract.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T2 runtime: benchmark results concern procedural behavior enforced by an external controller, so trusting a deployed agent requires checking which controller and procedure actually govern its actions. Users and operators should verify their model, controller version, workflow configuration and enforcement at all three stated boundaries; the saved source specifies no fixed release to install. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the deployment under question, although those records alone do not establish correct execution. These are verification requirements suggested by the mechanism, not capabilities established by the abstract.[^1]
:::

:::checked
On 15 November 2026, we read the supplied saved arXiv abstract-page text for “Keeping LLM Agents on Procedure: Executable Finite-State Control for Long-Horizon Instruction Fidelity,” identified as arXiv:2611.10884v1. This establishes what the saved page reports; we did not read the full paper, inspect code, reproduce the experiments or test the system.[^1]
:::

[^1]: https://arxiv.org/abs/2611.10884
