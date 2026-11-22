---
title: "Individual IETF Draft Proposes Per-Call Authorization for AI Agents"
dek: "The work-in-progress profile would bind agent sessions to sponsors and evaluate each tool call against a bounded permission set."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-22
agent: daily
evidence: [announcement, documentation]
sources:
  - "Session-Scoped Authorization for AI Agents: A Per-Tool-Call Authorization Profile Building on WIMSE and OAuth | datatracker.ietf.org | 2026-11-17 | https://datatracker.ietf.org/doc/draft-pandey-agent-identity/"
---

On 17 November 2026, Karmendra Pandey published an individual Internet-Draft proposing session-scoped authorization for AI agents. The profile builds on the Workload Identity in Multi System Environments (WIMSE) architecture and the OAuth 2.0 family. It is work in progress: the IETF Datatracker says the draft is not endorsed by the IETF, and the document says no working group has adopted it.[^1]

The proposal assigns each agent its own identity and binds each session to an authenticated sponsor through a delegation chain. For every tool call, it specifies an authorization decision based on the intersection of the agent’s permissions, the sponsor’s permissions and the session scope. The draft calls for denial when a call cannot be evaluated and sponsor approval for defined classes of irreversible actions.[^1]

A policy enforcement point would sit on the path to each tool, apply the decision and issue an audit receipt. The draft calls for a tamper-evident receipt store outside the agent’s write permissions; it also says a deployment that lets an agent bypass the enforcement point does not implement the profile. These are proposed requirements, not findings about a deployed system. The profile defines no new wire protocol, token format or policy language.[^1]

:::analysis
The proposal sits at the agents layer (T5) and runtime layer (T2): it addresses who acts and how tool calls are authorized during a session. A user or verifier would still need evidence that the deployment enforces those controls and retains trustworthy records; the draft alone cannot establish either. Users and operators should check their own identities, delegation chains, enforcement paths and audit records against the proposed requirements. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue; the draft does not establish that such records exist for any deployment.[^1]
:::

:::checked
On 22 November 2026, we read the saved IETF Datatracker page and its text of `draft-pandey-agent-identity-00`.[^1] We did not test the system or independently verify any implementation, deployment or security claim.
:::
