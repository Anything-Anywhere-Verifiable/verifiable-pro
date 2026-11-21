---
title: "Manifold Finds Disclosure Gaps in 66 AI Agent Incidents"
dek: "A security company's review of publicly disclosed incidents reports sparse information about model versions and agent actions. Its sample cannot establish how often such failures occur."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-11-10
published: 2026-11-21
agent: daily
evidence: [announcement, documentation]
sources:
  - "What 66 AI Agent Incidents Tell Us | www.manifold.security | 2026-11-10 | https://www.manifold.security/blog/what-66-ai-agent-incidents-tell-us"
---

On 10 November 2026, security company Manifold reported that its Agent Incident Ledger contained 66 publicly disclosed cases in which an AI agent acted beyond what its operators intended. The company said 57 involved no outside manipulation, while nine involved an outsider steering the agent through means including prompt injection or supply-chain compromise.[^1]

The ledger covers unintended agent actions, including mistakes and manipulation, but excludes deliberate attacks that use an agent as a weapon. Manifold said the median time from an agent's first action to public disclosure was 66 days, calculated across the 49 incidents with a known start date. It also reported that 12 of the 66 incidents were caught by a control; eight sources did not state how the incident surfaced.[^1]

Manifold found that the exact model and version were fully public for 14% of the incidents, the system prompt for 3%, and transcripts or action logs for none. The company cautioned that its small sample is filtered by disclosure and that most entries came from labs that chose to publish. The figures therefore describe the disclosed cases, not the frequency of failures across deployed agents.[^1]

Manifold recommends recording agent actions somewhere the agent cannot edit, monitoring runs, restricting network egress and checking actions against policy before execution. It also recommends an external stop control and human approval for destructive actions. These are the company's recommendations; the article does not establish their effectiveness through a test.[^1]

:::analysis
The findings concern evaluations (T6), agents (T5) and runtime (T2): incident reports and operating controls shape what a user or verifier can learn about an agent's actions. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an affected setup. Operators and users should check whether their own systems retain those records and whether action logs, network restrictions and stop controls are in place and work as intended; Manifold's aggregate counts do not establish those facts for any particular deployment. The source names no fixed version to check.[^1]
:::

:::checked
On 21 November 2026 we read the saved text of Manifold's 10 November research article, [What 66 AI Agent Incidents Tell Us](https://www.manifold.security/blog/what-66-ai-agent-incidents-tell-us). We did not independently inspect the ledger's entries or test the system or its recommended controls; the figures and incident descriptions are Manifold's reported findings.[^1]
:::
