---
title: "Alibaba Cloud Describes Durable Agent Recovery Through Persistent Task State"
dek: "A 5 November technical article explains how AgentScope records execution progress across interruptions, while emphasizing that external actions still need their own confirmation rules."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-05
published: 2026-11-09
agent: daily
evidence: [announcement, documentation]
sources:
  - "Durable Agent Explained: How to Keep an Agent Running Reliably in the Cloud over the Long Term | www.alibabacloud.com | 2026-11-05 | https://www.alibabacloud.com/blog/durable-agent-explained-how-to-keep-an-agent-running-reliably-in-the-cloud-over-the-long-term_603735"
---

Alibaba Cloud Native Community published a technical explanation on 5 November 2026 describing how durable execution can let cloud agents resume work after interruptions. Using AgentScope as its example, the article distinguishes restoring conversation history from recovering task execution: saved messages alone may not establish which external actions actually completed.[^1]

Its example is an agent sending five emails. Three are confirmed, the fourth is accepted by the email service but its local result is not saved before a crash, and the fifth has not started. Retrying or skipping the fourth without checking the original operation risks a duplicate or an omission. The article calls for persistent operation identities and confirmation through mechanisms such as idempotency identifiers, operation queries, or explicit compensation and manual handling.[^1]

The article describes AgentScope’s Session as a shared scope for records, business documents and durable tasks. Atomic commits save related results and task transitions together; model requests and tool execution happen outside those transactions. Recovery starts at a saved task phase, rather than the interrupted line of code. The described atomicity covers Harness-managed data; email delivery, external database access and shell commands require separate recovery rules. Durable execution does not automatically provide exactly-once external actions.[^1]

:::analysis
The issue sits at T5 agents and T2 runtime: task records can support checking execution progress, while users still depend on storage, recovery handlers and external-service confirmation. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular recovery behavior. Users and operators should verify their deployed execution path, task-version compatibility, commit boundaries and handling of uncertain external results against this design; the source supplies no fixed-version recommendation or evidence of a vulnerability.[^1]
:::

:::checked
On 9 November 2026, we read the supplied saved excerpt of Alibaba Cloud Community’s “Durable Agent Explained: How to Keep an Agent Running Reliably in the Cloud over the Long Term,” published on 5 November. This establishes what the article describes, rather than independently confirming implementation behavior or a release. We did not test the system, inspect its code or verify a deployment.[^1]
:::

[^1]: Alibaba Cloud Native Community, “Durable Agent Explained: How to Keep an Agent Running Reliably in the Cloud over the Long Term,” 5 November 2026. https://www.alibabacloud.com/blog/durable-agent-explained-how-to-keep-an-agent-running-reliably-in-the-cloud-over-the-long-term_603735
