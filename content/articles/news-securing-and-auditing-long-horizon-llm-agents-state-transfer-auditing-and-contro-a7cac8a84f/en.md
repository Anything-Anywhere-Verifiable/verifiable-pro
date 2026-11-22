---
title: "Paper Proposes State-Transfer Audits for Long-Horizon LLM Agents"
dek: "The authors say records at agent state-transfer boundaries can help attribute failures and support runtime controls. Their arXiv abstract reports a reference implementation and evaluation."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-21
agent: daily
evidence: [announcement, documentation]
sources:
  - "Securing and Auditing Long-Horizon LLM Agents: State-Transfer Auditing and Controls in the Agent Harness | arXiv | 2026-11-17 | https://arxiv.org/abs/2611.23346"
---

On 17 November 2026, Deep Shah and Nehal Kathrotia submitted a paper proposing audits of state transfers in long-horizon large language model (LLM) agents. The authors argue that conventional traces of prompts and tool calls can miss failures as information moves among an agent’s working context, session history, persistent memory and external environment.[^1]

The arXiv abstract describes three kinds of transfer failure: admitting unchecked content, rewriting state in a way that loses information, and restoring state incompletely. Its examples include context compaction dropping user constraints and workspace rollbacks leaving aborted key-value cache state active on an inference server. Such gaps can make it harder to attribute failures across a sequence of agent actions, the authors say.[^1]

The proposed architecture places an audit point at each transfer boundary. According to the abstract, each point specifies a minimal hash-chained record emitted by the agent harness, separates deterministic checks from model-based semantic checks, and binds internal context, memory and inference-server cache state to external actions. The authors say these records can also support runtime controls, including least-privilege capabilities, authorization outside the prompt, information-flow control, obligation monitors and transactional recovery.[^1]

The abstract reports a reference middleware implementation evaluated on 240 multi-step fault-injection trajectories. It says the records localized root causes and caught cross-transfer violations missed by lifecycle and tool-only logs, with microsecond deterministic overhead. These are the authors’ reported results; the abstract alone does not establish how the evaluation would generalize to other systems.[^1]

:::analysis
The issue sits at T5 agents and T2 runtime: an auditor’s account depends on which state transfers the harness records and which runtime state those records cover. Identifiability matters too: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular affected setup. Users and operators should check which version and configuration serve their requests, which transfer boundaries are recorded, and whether those records can be inspected; the abstract recommends no fixed version. A record’s presence alone does not establish that every transfer was captured or that a semantic check was correct.[^1]
:::

:::checked
On 21 November 2026 we read the saved arXiv abstract page for *Securing and Auditing Long-Horizon LLM Agents: State-Transfer Auditing and Controls in the Agent Harness*.[^1] We did not read the full paper or test the system, and therefore did not independently confirm the implementation, evaluation results or overhead.
:::
