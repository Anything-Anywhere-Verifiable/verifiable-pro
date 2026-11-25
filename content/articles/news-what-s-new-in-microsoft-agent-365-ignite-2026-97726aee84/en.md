---
title: "Microsoft Expands Agent 365 Identity and Activity Monitoring"
dek: "Microsoft says its Ignite updates give administrators a broader view of agents across platforms, with identity, activity and risk controls at different stages of release."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-25
agent: daily
evidence: [announcement, documentation]
sources:
  - "What's new in Microsoft Agent 365: Ignite 2026 | techcommunity.microsoft.com | 2026-11-17 | https://techcommunity.microsoft.com/blog/agent-365-blog/whats-new-in-microsoft-agent-365-ignite-2026/4571753"
---

Microsoft announced updates to Agent 365 on 17 November 2026 that it says expand how organizations identify, monitor and govern AI agents across platforms and employee devices. The announcement describes capabilities at different release stages, including previews and generally available features.[^1]

Microsoft says connected agents receive a Microsoft Entra Agent ID, giving administrators a way to distinguish agent identities from human identities and apply supported policies. The company says support is rolling out across several partner platforms and is due to complete in December. Capabilities vary by platform.[^1]

The company also says Microsoft Defender and Microsoft Entra Global Secure Access discover local agents and their configured Model Context Protocol (MCP) servers, with signals appearing in the Agent 365 registry. Defender's local agent discovery is generally available; network-level and registry discovery are in preview. Separate local-agent identity controls are also in preview, starting with GitHub Copilot CLI and Claude Code.[^1]

Administrators can export agent traces to Azure Monitor and Application Insights, filtering by agent or platform and choosing which prompts and responses to include, Microsoft says. Its dynamic agent risk feature, in preview, combines runtime signals into a risk level that changes as circumstances change. Microsoft also describes multi-tenant management in preview, including comparison of agent configuration and access across tenants.[^1]

:::analysis
The claims sit at the agents layer (T5) and runtime layer (T2): identity, activity records and runtime signals can give operators evidence to inspect, while the completeness and accuracy of that evidence remain to be checked in their deployment. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue. Users and operators should verify which agents and platforms their deployment actually covers, what configuration and activity records it retains, and which preview or generally available controls are enabled; the announcement does not establish these facts for any particular system.[^1]
:::

:::checked
On 25 November 2026 we read the saved Microsoft Community Hub announcement, “What's new in Microsoft Agent 365: Ignite 2026.”[^1] We did not test Agent 365 or independently confirm its coverage, records, risk assessments or enforcement in a deployment.
:::
