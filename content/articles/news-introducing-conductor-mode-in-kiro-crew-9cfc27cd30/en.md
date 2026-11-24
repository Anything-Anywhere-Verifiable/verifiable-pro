---
title: "Kiro Introduces Conductor Mode for Coordinating Worker Agents"
dek: "Kiro says its new mode delegates tasks, records their state and checks completion evidence. Its announcement also describes an incorrect judgment made during an internal run."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime]
event_date: 2026-11-20
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "Introducing conductor mode in Kiro Crew | kiro.dev | 2026-11-20 | https://kiro.dev/blog/conductor-mode/"
---

Kiro announced conductor mode for Kiro Crew on 20 November 2026, describing a way to divide a user’s goal among worker agents and coordinate their results. The company says the mode is available through a switch in a chat session; users define the goal and what a successful result should look like.[^1]

According to Kiro, each worker is assigned one task and files structured progress, completion, blockage or question reports, with links to evidence such as a pull request. A work ledger holds tasks and results, while a session ledger records the goal, next step and rejected approaches. The company describes an append-only crew log as the source of truth for this saved state.[^1]

Kiro says the conductor checks evidence against each task’s agreed completion condition using a procedure called `accept_eval`. Examples include pull request checks, a required file or a pending request for human approval. The default conductor has no direct file-editing tool and delegates changes to workers, according to the announcement.[^1]

The company also reports an error in an internal run: the conductor blamed a worker’s changes for failing checks after seeing no failures on the main branch, even though main did not run the same tests. Kiro says the conductor later corrected its judgment and that the worker had waited and rebased. This account is Kiro’s report of its own run, not an independent evaluation.[^1]

:::analysis
The agent layer (T5) is where the conductor delegates and judges work; the runtime layer (T2) includes the ledgers and procedures Kiro describes for retaining state and checking results. A task’s acceptance depends on its stated condition and available evidence, so users and operators should inspect those conditions, the linked evidence and any decisions requiring human review in their own systems. Identifiability matters too: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular behavior or issue. The announcement does not specify a fixed version or establish that such records are available.[^1]
:::

:::checked
On 23 November 2026, we read the saved Kiro announcement, [“Introducing conductor mode in Kiro Crew”](https://kiro.dev/blog/conductor-mode/). We did not test the system or independently verify the reported runs, checks or availability.[^1]
:::
