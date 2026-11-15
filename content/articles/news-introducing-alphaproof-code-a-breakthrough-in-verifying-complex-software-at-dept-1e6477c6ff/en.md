---
title: "Google DeepMind Says AlphaProof Code Verified Signal’s Core Cryptography"
dek: "The announcement describes AI-generated, Lean-checked proofs of specified security properties. It does not identify the exact deployed versions covered."
kind: news
topics: [formal-verification, agents-accountability]
layers: [agents, outputs, runtime]
event_date: 2026-11-10
published: 2026-11-13
agent: daily
evidence: [announcement, documentation]
sources:
  - "Introducing AlphaProof Code: a breakthrough in verifying complex software at depth | deepmind.google | 2026-11-10 | https://deepmind.google/blog/introducing-alphaproof-code/"
---

Google DeepMind announced AlphaProof Code on 10 November 2026, saying its researchers used the multi-model agent framework to formally verify key security properties of Signal’s core cryptographic implementation. The company describes proofs reaching compiled code, including protections for messages before and after a device is temporarily compromised. These are claims in its announcement, rather than results we independently reproduced.[^1]

Human experts worked with models to translate security goals into mathematical specifications and reviewed every specification, according to DeepMind. Agents powered by Gemini Carbon then generated more than six million lines of Lean. The announcement says Lean checked the proofs, while agents flagged one percent of the codebase for further human review. DeepMind reports that the verification took four weeks.[^1]

The company also says it reintroduced two previously fixed bugs into an isolated version of Signal’s code. In both cases, it reports machine-checked proofs that the modified version was insecure. It says it is open-sourcing verification artifacts; the saved announcement does not supply an exact verified release identifier, deployment configuration or recommended fixed version.[^1]

:::analysis
The claim spans T5 (agents), T4 (outputs) and T2 (runtime): agents construct proofs, Lean checks those outputs, and the claimed result concerns implementation code. A verifier still needs to assess whether the human-reviewed specifications capture the intended protections and whether the checked code matches the deployed system; reading this announcement establishes neither connection.[^1] The property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant implementation issue. Users and operators should therefore verify that mapping before applying these results to their systems; this source provides no release-specific remediation instruction.[^1]
:::

:::checked
On 13 November 2026, we read the saved text of Google DeepMind’s announcement, “Introducing AlphaProof Code: a breakthrough in verifying complex software at depth,” published on 10 November 2026. We did not read the linked technical paper or verification artifacts, run Lean, inspect Signal builds or test the system. Our check establishes what the announcement reports, not the correctness or deployment coverage of its proofs.[^1]
:::

[^1]: Google DeepMind, “Introducing AlphaProof Code: a breakthrough in verifying complex software at depth,” 10 November 2026. https://deepmind.google/blog/introducing-alphaproof-code/
