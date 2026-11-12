---
title: "Cymulate Reports Agent Attack Chains Reaching Azure and GCP"
dek: "Two reported scenarios connect malicious agent inputs to cross-user compromise and cloud credentials. The saved post does not identify fixed release versions."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-03
published: 2026-11-11
agent: daily
evidence: [announcement, documentation]
sources:
  - "Across the Kill Chain: How Agents Became the Enterprise's New Front Door | cymulate.com | 2026-11-03 | https://cymulate.com/blog/ai-agent-security-kill-chains/"
---

Cymulate published a research summary on 3 November 2026 describing two agent attack chains that it says reached privileged Azure and Google Cloud Platform (GCP) identities. Written by Ben Zamir, the post summarizes a SecTor 2026 presentation. Its scenarios assume shared Windows hosts, multiple users and agents connected to corporate accounts; they are reported demonstrations, not evidence of compromises at customer organizations.[^1]

In the first chain, Cymulate says a malicious web page induced AWS Kiro to write execution configuration, gaining execution as one user. A permissive Codex CLI named pipe and configuration weaknesses then enabled a pivot to another user's OpenAI token. The researchers describe using that identity to alter a shared Codex cloud environment, whose setup script subsequently collected QA workflow secrets, including credentials for an Azure app registration with broad permissions.[^1]

The second chain reportedly began with a poisoned README that caused Cursor CLI to write a project-local executable. Executable search order and machine-wide configuration enabled execution across users; a modified repository then supplied a binary that Gemini CLI launched before its sandbox started. The post also describes exposure of Google OAuth credentials. Cymulate says AWS fixed the Kiro issue, CVE-2026-10591, while Cursor's initial execution issue remained unresolved at writing. These are the author's status statements; the saved text supplies no fixed release numbers.[^1]

:::analysis
The relevant layers are T5 (agents), where untrusted content becomes delegated action, and T2 (runtime), where executable lookup, configuration permissions and local communication determine whose authority is exercised. Reading this account leaves users trusting the reported demonstrations and remediation status. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed. Users and operators should check those records against the described Windows conditions, inspect shared configuration and cloud setup scripts, and verify remediation for their deployed releases; this saved source provides no fixed version to target.[^1]
:::

:::checked
On 11 November 2026, we read the supplied saved copy of Cymulate's “Across the Kill Chain: How Agents Became the Enterprise's New Front Door,” published on 3 November 2026. The copy ends mid-sentence during the second chain. We did not open its linked research posts, test any system, reproduce the attacks or independently verify fixes. This check establishes what the saved account reports.[^1]
:::

[^1]: Cymulate, “Across the Kill Chain: How Agents Became the Enterprise's New Front Door,” 3 November 2026. https://cymulate.com/blog/ai-agent-security-kill-chains/
