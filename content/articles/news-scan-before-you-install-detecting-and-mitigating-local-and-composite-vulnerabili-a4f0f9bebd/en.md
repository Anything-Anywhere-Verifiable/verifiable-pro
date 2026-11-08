---
title: "Researchers Report Scanner for Vulnerabilities Within and Across Agent Skills"
dek: "An arXiv preprint reports detection and mitigation results for agent skills, including interactions that isolated scans can miss. The saved abstract does not identify a fixed release users can install."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-10-27
published: 2026-11-06
agent: daily
evidence: [announcement, documentation]
sources:
  - "Scan Before You Install: Detecting and Mitigating Local and Composite Vulnerabilities in Skills | arXiv | 2026-10-27 | https://arxiv.org/abs/2610.37901"
---

Parth A. Gandhi and colleagues submitted *Scan Before You Install: Detecting and Mitigating Local and Composite Vulnerabilities in Skills* to arXiv on 27 October 2026. The authors report a six-module scanner for unintended vulnerabilities within agent skills and vulnerabilities arising when skills interact. This is a research report; the saved abstract identifies no fixed software release.[^1]

A skill packages natural-language instructions, scripts, and reference files for an agent based on a large language model. Under user-authorized permissions, skills may access files, the shell, and the network. The authors say existing scanners focus primarily on malicious skills and examine skills individually, missing weaknesses in benign packages and interactions through shared resources, invocations, or instructions.[^1]

The authors report that three analysts confirmed 53 of 59 findings across 23 repositories in a survey of 1,587 skills from the 75 most-starred GitHub repositories. They also report two composite findings validated through proof-of-concept attacks. On SCR-Bench, their composite analysis achieved an F1 score of 0.991, compared with 0.816–0.858 for three SkillsGuard configurations. These are author-reported results.[^1]

The mitigation module recommends skill substitution, patches, and configuration changes. For 47 of 55 GitHub findings, the authors say mitigations blocked proof-of-concept attacks in all trials while preserving the legitimate functionality they tested. That statement is bounded by those attacks and functionality checks.[^1]

:::analysis
The issue spans T5 (agents), where skills supply instructions and interact, and T2 (runtime), where authorized file, shell, and network access can turn weaknesses into unsafe execution. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed. Users and operators should verify their installed skill versions, combinations, permissions, and applicable substitutions, patches, or configuration changes; the saved abstract supplies no recommended fixed version, and its results do not establish safety for their deployment.[^1]
:::

:::checked
On 6 November 2026, we read the saved arXiv abstract page for arXiv:2610.37901v1, including its submission history. We did not read the full paper, inspect code, reproduce benchmarks, or test the system. This check establishes what the authors reported, leaving implementation and effectiveness to their evidence.[^1]
:::

[^1]: [Scan Before You Install: Detecting and Mitigating Local and Composite Vulnerabilities in Skills](https://arxiv.org/abs/2610.37901), arXiv, 27 October 2026.
