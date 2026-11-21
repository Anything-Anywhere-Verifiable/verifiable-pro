---
title: "CrowdStrike Reports Two-Stage Search for Backdoors in LoRA Models"
dek: "The company describes a weight scanner and a trigger search for modified open-weight models. Its controlled study shows why a suspicious modification still needs investigation."
kind: news
topics: [supply-chain, evaluation-audits]
layers: [models]
event_date: 2026-11-16
published: 2026-11-20
agent: daily
evidence: [announcement, documentation]
sources:
  - "Hidden in the Weights: Supply Chain Risk from Backdoored LoRA Models | www.crowdstrike.com | 2026-11-16 | https://www.crowdstrike.com/en-us/blog/supply-chain-risk-from-backdoored-lora-models/"
---

On 16 November 2026, CrowdStrike described a two-stage method for finding backdoors in open-weight models modified with low-rank adaptation (LoRA). The company says the method first examines model weights for signs of modification, then searches for inputs that trigger suspect behavior.[^1]

LoRA fine-tunes a model by training a smaller set of additional parameters, known as an adapter. The adapter can be distributed separately or merged into the original weights. CrowdStrike says a backdoor can leave a model behaving normally until a particular input activates unwanted behavior, such as a malicious tool call or insecure code.[^1]

The first stage compares a suspect artifact with its base model and examines the differences in shape, rank and promoted output tokens. CrowdStrike reports that it scanned 16 artifacts in a controlled lab: eight backdoored models, four benign models built in the lab and four public controls. It says all eight backdoored models were escalated for further investigation. Two benign merged models were also escalated, while another control was classified as an abliterated model. The company notes that a malicious merged LoRA and a benign one can look alike to the scanner.[^1]

The second stage probes escalated models for candidate triggers, using next-token probabilities and checking candidates with full generations. The supplied source describes this procedure, but its saved text ends as the stage-two results begin, so those results cannot be established from the material available here.[^1]

:::analysis
The issue sits at the models layer, T3: a user or verifier needs evidence about the actual model weights and configuration serving a request, while a scanner's finding still requires interpretation. Identifiability is the property at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular suspect model. Users and operators should verify which base model and adapters or merged weights their systems use, and investigate flagged modifications; the source does not recommend a fixed software version.[^1]
:::

:::checked
On 20 November 2026 we read the saved text of CrowdStrike's “Hidden in the Weights: Supply Chain Risk from Backdoored LoRA Models,” published on 16 November 2026. The saved text ends at the start of the second-stage results. We did not test the system or independently reproduce the reported findings.[^1]
:::
