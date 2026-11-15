---
title: "Kiro Adds LLM Review for Tool Approvals"
dek: "The opt-in “Approve for me” feature reviews actions outside explicit permission rules. Kiro’s launch post reports fewer prompts, while distinguishing approval decisions from sandbox limits."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-10
published: 2026-11-14
agent: daily
evidence: [announcement, documentation]
sources:
  - "Introducing “Approve for me” in Kiro | kiro.dev | 2026-11-10 | https://kiro.dev/blog/introducing-approve-for-me/"
---

Kiro announced “Approve for me” on 10 November 2026 for its IDE, CLI and Web products. When enabled, the feature sends actions not covered by explicit permission rules to a large language model (LLM) review, currently using an Anthropic model. Kiro says the review can approve an action, block it or ask the user to decide.[^1]

Existing allow, ask and deny rules take precedence; actions they cover bypass the model review. After three consecutive steps with a blocked action, Kiro returns to asking the user and includes the reason. The feature is off by default and available to paid users in us-east-1 and eu-central-1. Reviews are charged against the user’s plan. The announcement recommends Kiro IDE 1.4.154 or later, or CLI 2.36 or later; Web requires no update.[^1]

Kiro reports that, in a one-week internal sample, permission rules handled around 70% of actions and model review handled around 30%. Roughly 97% of reviewed actions required no user prompt, and median review latency was under a second. These are vendor-reported operational figures; the post does not establish how reliably the reviewer identifies unsafe actions.[^1]

Approval also does not restrict a shell command’s access once executed. Kiro describes an optional local sandbox for IDE and CLI, with outbound networking blocked unless allowed, and a managed cloud sandbox for Web sessions.[^1]

:::analysis
The claim sits at T5 (agents), where actions receive permission, and T2 (runtime), where sandbox boundaries constrain execution; a model’s approval alone establishes neither an action’s safety nor its confinement. Users and operators should check the recommended client version, feature availability and enablement, explicit rules, trust-all-tools status, and applicable sandbox and network settings. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to this approval path; the announcement does not establish such records are available.[^1]
:::

:::checked
On 14 November 2026, we read the saved official Kiro post “Introducing ‘Approve for me’ in Kiro,” published on 10 November 2026. This reading establishes what Kiro announced and reported. We did not test the system or independently validate its approval decisions, sandbox enforcement or internal measurements.[^1]
:::

[^1]: Kiro, “Introducing ‘Approve for me’ in Kiro,” 10 November 2026. https://kiro.dev/blog/introducing-approve-for-me/
