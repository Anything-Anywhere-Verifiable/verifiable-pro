---
title: "KLA Reports Authority Leaks at Multi-Agent Handoffs"
dek: "KLA summarizes experiments in four configured agent frameworks and reports a local reproduction of a file-access race. The results leave questions about deployed systems."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime]
event_date: 2026-11-20
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Multi-agent delegation: where authority leaks at handoffs | kla.digital | 2026-11-20 | https://kla.digital/blog/multi-agent-delegation-authorization-handoffs"
---

On 20 November 2026, KLA published research notes describing how authority can be lost as AI agents delegate tasks. Summarizing a preprint, the company said chains of permitted tools and a swapped symbolic link each reached a protected file in configured LangChain, LangGraph, AutoGen and OpenClaw systems. KLA also reported its own local reproduction of the link-swap case.[^1]

According to KLA’s account, the preprint tested 12 experiments across four setups, all using the same model. In one delegation experiment, an untrusted instruction embedded in a project summary reached a file-reading agent: all four configurations read and disclosed the secret without an authorization stage. KLA says that, with a check on the originating agent’s authority before the handoff, the downstream agent received no privileged tool and no read or disclosure occurred.[^1]

The link-swap experiment concerned a file path approved before a symbolic link was redirected outside the permitted directory. KLA reports that its single-process simulation exposed a remaining race when the path was checked again before opening: a swap between that check and the open still caused a private file to be read. In its reported cases, opening the file, checking what the resulting descriptor referred to and reading through that descriptor refused the swapped target.[^1]

:::analysis
The issue sits at the agents layer (T5), where delegated authority and approvals cross handoffs, and the runtime layer (T2), where a file is actually opened. A user or verifier needs evidence about both the delegation and the resource operation; a clean final answer alone does not establish that no unauthorized tool call occurred. Operators should check their own handoff authorization, approval records and file-access behavior, including whether checks bind to the opened object. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the reported conditions; this record alone does not establish whether an unauthorized action occurred.[^1]
:::

:::checked
For this preview prepared on 24 November 2026, we read the saved text of KLA’s [“Multi-agent delegation: where authority leaks at handoffs”](https://kla.digital/blog/multi-agent-delegation-authorization-handoffs), published on 20 November 2026. We did not read the preprint or test the systems. KLA says it found no released repository containing the prompts, traces or per-trial counts; its reproduction was a local simulation and did not test KLA’s product.[^1]
:::
