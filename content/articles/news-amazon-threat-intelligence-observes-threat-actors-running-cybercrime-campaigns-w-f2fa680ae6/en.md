---
title: "Amazon Reports Cybercrime Campaigns Using ARTEX AI Agents"
dek: "Amazon says decoy AI interfaces captured agents’ records of credential theft and deepfake campaigns. It could not independently verify the outcomes described in those records."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-13
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Amazon Threat Intelligence observes threat actors running cybercrime campaigns with ARTEX AI agents | aws.amazon.com | 2026-11-13 | https://aws.amazon.com/blogs/security/amazon-threat-intelligence-observes-threat-actors-running-cybercrime-campaigns-with-artex-ai-agents/"
---

Amazon Threat Intelligence reported on 13 November 2026 that its MadPot decoy sensors had captured requests containing AI agents’ records of cybercrime campaigns. Amazon assessed with moderate confidence that the actors used ARTEX, an open-source agentic penetration-testing framework. The records described credential theft and attempts to bypass cryptocurrency exchanges’ identity checks.[^1]

From 3 October to 5 November, MadPot presented interfaces resembling large language model (LLM) inference APIs. Amazon says the requests sent to them included task context, instructions, tool histories and reported findings. Those records described activity on systems MadPot did not monitor: Amazon did not observe that activity as it happened and could not verify its reported outcomes.[^1]

In one campaign, the records described agents searching exposed AI applications and gateways for provider keys, validating credentials and putting stolen keys into a model gateway to power further searches. Amazon lists attack paths including default credentials, unauthenticated interfaces, exposed secrets and unpatched software. It says it assessed activity referencing potentially affected AWS customers and notified them as appropriate; it could not confirm activity against other organizations.[^1]

A separate campaign sought to bypass identity checks with forged documents and real-time deepfake video. The agents’ records described attempts against a liveness check, but the vendor’s server-side verdict rejected the deepfake in every recorded attempt, according to Amazon. The post also publishes indicators of compromise for organizations to review.[^1]

:::analysis
The issue spans T5 agents, where instructions and retained histories shape tool use, and T2 runtime, where exposed interfaces and credentials can give an agent access. A captured agent history is evidence of what it reported, while outcomes outside the sensor remain unverified. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an affected condition; such records alone do not establish that an attack succeeded. Users and operators should check their own versions, configurations, exposed interfaces and credentials, address unpatched software and review unusual AI-service usage; Amazon gives no specific fixed version in this post.[^1]
:::

:::checked
On 18 November 2026 we read the saved text of [Amazon’s AWS Security Blog report](https://aws.amazon.com/blogs/security/amazon-threat-intelligence-observes-threat-actors-running-cybercrime-campaigns-with-artex-ai-agents/), published 13 November 2026.[^1] We did not test ARTEX, MadPot or the affected systems, and we could not independently confirm the campaigns’ reported outcomes.
:::
