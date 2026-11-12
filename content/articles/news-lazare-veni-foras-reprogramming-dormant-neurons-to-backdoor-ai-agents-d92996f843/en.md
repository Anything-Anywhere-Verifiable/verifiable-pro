---
title: "Microsoft Reports Lazarus Backdoors Through Dormant Model Neurons"
dek: "Microsoft Research says small weight edits can trigger malicious agent commands while preserving normal evaluation behavior. The announcement puts model provenance and weight integrity at the center of detection."
kind: news
topics: [supply-chain, agents-accountability, evaluation-audits]
layers: [agents, models]
event_date: 2026-11-10
published: 2026-11-12
agent: daily
evidence: [announcement, documentation]
sources:
  - "Lazare, veni foras: Reprogramming Dormant Neurons to Backdoor AI Agents | www.microsoft.com | 2026-11-10 | https://www.microsoft.com/en-us/research/blog/lazare-veni-foras-reprogramming-dormant-neurons-to-backdoor-ai-agents/"
---

Microsoft Research reported on 10 November 2026 that Lazarus, a model backdoor technique, can reprogram fewer than 10 dormant neurons without retraining, causing an AI agent to issue malicious commands when a hidden trigger appears. The announcement says the modified model can behave normally and pass standard evaluations before activation.[^1]

The reported attack requires write access to a model checkpoint. Dormant neurons become trigger detectors; activated neurons then force output tokens that can form a command. The post gives a date change into 2027 as an example trigger. An agent with terminal access could execute the resulting command with its existing permissions. Microsoft says compromised accounts, pipelines or storage could expose internally developed models as well as open-weight models.[^1]

Microsoft says Foundry ties onboarded open-weight models to their original publishers and runs them in Microsoft containers scanned for critical vulnerabilities. Its claim that these controls protect models from trusted labs remains a vendor claim. The post identifies compromise of a trusted provider as a remaining risk. Agent-assisted weight scanning and a red-teaming harness are under development or exploration; model signing and provenance audits are planned.[^1]

:::analysis
The issue spans T5 (agents), where permissions turn generated commands into actions, and T3 (models), where altered weights encode the trigger; ordinary evaluation results therefore leave weight integrity to trust. Users and operators should verify checkpoint provenance, compare deployed weights with the original unmodified weights, and review agent permissions and monitoring, following the source’s guidance; it specifies no fixed release to install. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an identified affected deployment. Such records would not establish that every backdoor had been found; the source explicitly says scanning cannot establish model safety beyond doubt.[^1]
:::

:::checked
On 12 November 2026, we read the saved Microsoft Research blog post, “Lazare, veni foras: Reprogramming Dormant Neurons to Backdoor AI Agents,” published on 10 November 2026. We did not open its linked paper or mitigation guidance, inspect weights, reproduce the attack, or test Foundry. This reading establishes what Microsoft reported and which controls it describes as current or planned; it does not independently validate effectiveness.[^1]
:::

[^1]: Microsoft Research, “Lazare, veni foras: Reprogramming Dormant Neurons to Backdoor AI Agents,” 10 November 2026. https://www.microsoft.com/en-us/research/blog/lazare-veni-foras-reprogramming-dormant-neurons-to-backdoor-ai-agents/
