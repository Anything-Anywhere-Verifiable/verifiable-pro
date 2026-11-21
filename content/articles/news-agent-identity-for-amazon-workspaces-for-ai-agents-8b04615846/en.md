---
title: "AWS Describes Agent Identity for WorkSpaces for AI Agents"
dek: "AWS says its on-behalf-of flow connects an agent’s identity to the user it serves and records both for audit. The result depends on identity-provider configuration and logging choices."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-21
agent: daily
evidence: [announcement, documentation]
sources:
  - "Agent identity for Amazon WorkSpaces for AI agents | aws.amazon.com | 2026-11-17 | https://aws.amazon.com/blogs/desktop-and-application-streaming/agent-identity-for-amazon-workspaces-for-ai-agents/"
---

On 17 November 2026, AWS described agent identity for Amazon WorkSpaces for AI agents, a way for an AI agent to act in a managed desktop session on behalf of a signed-in user. AWS says the design associates the agent and user with the session and its audit records.[^1]

In the described on-behalf-of flow, the agent authenticates to the organization’s identity provider and exchanges the user’s sign-in for a token naming both identities. AWS Security Token Service validates the token and issues temporary credentials for the agent’s AWS Identity and Access Management (IAM) role. AWS says IAM checks which agents may act for which users and access which environments.[^1]

AWS says CloudTrail records both identities when the agent assumes its role; subsequent requests record the user under that role. Recording each agent action requires CloudTrail data events, and AWS recommends a separate IAM role for each agent so actions can be traced to both parties. Identity-provider sign-in logs add a record of which agent the user allowed to act.[^1]

The design supports non-domain-joined and domain-joined fleets. For the latter, AWS says the identity provider must supply Active Directory attributes and certificate-based authentication must already work. Disabling an identity stops new sessions; AWS says operators must remove role permissions or revoke active role sessions to stop an agent already working.[^1]

:::analysis
The claim sits at T5, the agents layer, and T2, the runtime layer: identity and session records can help an operator attribute requests, but their usefulness depends on the identity provider’s mappings, IAM roles and enabled logging. Operators should check those mappings, role assignments, data events and revocation behavior in their own deployment; AWS says it cannot check whether the identity provider mapped the right details into a token. A separate property is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an issue affecting that version and configuration. The AWS post does not establish that such version records exist for a session or recommend a fixed version.[^1]
:::

:::checked
On 21 November 2026 we read the saved copy of AWS’s 17 November 2026 blog post, “Agent identity for Amazon WorkSpaces for AI agents.” We did not test the system or independently verify its identity checks, logs or revocation behavior.[^1]
:::
