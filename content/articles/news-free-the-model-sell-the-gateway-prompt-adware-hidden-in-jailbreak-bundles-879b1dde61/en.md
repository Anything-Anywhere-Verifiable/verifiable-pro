---
title: "Check Point Reports Persistent Prompt Adware in Haiou Codex Bundle"
dek: "Researchers say Haiou 4.5.0 changes agent instructions to advertise an LLM gateway. The report highlights why package authenticity alone cannot establish acceptable instruction content."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, outputs, runtime]
event_date: 2026-11-03
published: 2026-11-13
agent: daily
evidence: [announcement, documentation]
sources:
  - "Free the Model, Sell the Gateway: Prompt Adware hidden in Jailbreak Bundles | research.checkpoint.com | 2026-11-03 | https://research.checkpoint.com/2026/free-the-model-sell-the-gateway-prompt-adware-hidden-in-jailbreak-bundles/"
---

Check Point Research reported on 3 November 2026 that Haiou, a jailbreak bundle targeting OpenAI Codex, persistently modifies agent instructions to advertise its author's large language model (LLM) gateway. Its analysis covers version 4.5.0 and classifies the behavior as prompt adware: natural-language changes to trusted instructions that influence future responses for commercial or behavioral objectives.[^1]

According to the report, the bundle installs six security-related Skills and modular prompts, including instructions intended to suppress refusals and reframe offensive-security requests as educational exercises. An identity module directs the agent to answer specified greetings with a gateway advertisement. Another module designates the promoted service as protected infrastructure and forbids offensive testing against it, even when a user claims authorization.[^1]

The launchers reportedly check Ed25519 signatures and SHA-256 hashes, then decrypt a packaged payload using an embedded AES-256-GCM key. Those checks concern the package; they do not establish that its instructions match a user's expectations. Check Point says encrypted packaging obscures the prompts from casual repository inspection. It also reports an uninstaller that restores original configurations and removes the advertisement, but identifies no fixed release or recommended upgrade version.[^1]

Check Point found the bundle on a cybercrime actor's exposed server. It explicitly says this does not establish that the author created it for cybercrime, and reports no indication that the advertised gateway itself is malicious.[^1]

:::analysis
The issue spans T5 agents, T4 outputs and T2 runtime: installed instructions and configuration can steer later responses, so checking the model's identity alone leaves those inputs to trust. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the reported modification. Users and operators should inspect installed prompts, Skills, global instruction files and gateway settings against the reported behavior; any use of the described uninstaller should be followed by checking the resulting configuration.[^1]
:::

:::checked
On 13 November 2026, we read the saved copy of Check Point Research's “Free the Model, Sell the Gateway: Prompt Adware hidden in Jailbreak Bundles,” published on 3 November 2026. This establishes what the report says; we did not inspect the repository, decrypt the package, test Codex, test the gateway or verify the uninstaller's behavior.[^1]
:::

[^1]: Check Point Research, “Free the Model, Sell the Gateway: Prompt Adware hidden in Jailbreak Bundles,” 3 November 2026. https://research.checkpoint.com/2026/free-the-model-sell-the-gateway-prompt-adware-hidden-in-jailbreak-bundles/
