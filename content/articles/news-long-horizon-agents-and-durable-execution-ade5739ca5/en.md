---
title: "Durable Execution Gives Long-Horizon Agents a Recovery Record"
dek: "Kiran Prakash describes how recorded steps let agents resume after failures. The saved article excerpt explains recovery mechanics but does not establish end-to-end correctness."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-10
published: 2026-11-15
agent: daily
evidence: [announcement, documentation]
sources:
  - "Long-horizon agents and durable execution | martinfowler.com | 2026-11-10 | https://martinfowler.com/articles/durable-execution-agents.html"
---

Kiran Prakash published an architectural article on martinfowler.com on 10 November 2026 explaining how durable execution can help agents carry out tasks spanning days or weeks. Its purchasing example separates brief actions from long waits for approvals, supplier replies and deliveries, during which processes can crash and messages can be delayed or duplicated.[^1]

The article describes a runtime that persistently records the inputs and outputs of steps interacting with external systems, including model calls and tool execution. After a crash, replay starts the program again: steps with recorded outputs return those outputs, while local code runs again to reconstruct state. In the Temporal example, model decisions and tool calls are activities; approval waits use a separate workflow primitive.[^1]

Prakash says the example was built on Temporal and Cloudflare Workflows. The excerpt describes a recorded Temporal run in which the process stopped while awaiting approval, then resumed without repeating earlier completed actions. This is the author's account of an example, rather than an independently reproduced test or a product release announcement. The source also identifies retries that duplicate orders, unseen external outcomes, changing prices, code changes and untrusted input as concerns; the saved text ends before their detailed treatment.[^1]

:::analysis
The issue sits at T5 agents and T2 runtime: the harness controls available actions, while the runtime supplies the recovery record, leaving business correctness dependent on application logic and external outcomes. Users and operators should check which model and tool calls their system records, how approval rules are enforced, and how retries and code changes affect ongoing work. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an identified failure condition; this excerpt establishes no such deployment record and recommends no fixed version.[^1]
:::

:::checked
On 15 November 2026, we read the saved excerpt of Kiran Prakash's “Long-horizon agents and durable execution,” published on martinfowler.com on 10 November 2026. It ends mid-discussion of waiting. We did not test the system, inspect implementation repositories or independently confirm recovery behavior.[^1]
:::

[^1]: https://martinfowler.com/articles/durable-execution-agents.html
