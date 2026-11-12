---
title: "MemoryDojo Authors Report Poisoning Risks Across Five Agent Memory Systems"
dek: "An arXiv submission introduces a benchmark for tracing malicious instructions across sessions. Its abstract reports susceptibility across the evaluated memory systems, but provides no attack success rates or fixed versions."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-11-06
published: 2026-11-11
agent: daily
evidence: [announcement, documentation]
sources:
  - "MemoryDojo: Benchmarking Poisoning Through LLM Agent Memory | arXiv | 2026-11-06 | https://arxiv.org/abs/2611.09721"
---

David H. Yang and coauthors introduced MemoryDojo in an arXiv submission dated 6 November 2026, proposing a benchmark for tracing how poisoned information passes through large language model (LLM) agent memory and influences later behavior. The abstract says all five memory systems evaluated were susceptible to poisoning, with substantial differences in downstream effects.[^1]

The attack pathway crosses session boundaries: malicious instructions encountered during one session can enter memory, persist there, and later be retrieved and acted upon. The authors argue that differences in how memory systems process and retrieve information can change the consequences of poisoning. This makes memory handling part of the behavior an evaluation needs to examine.[^1]

According to the abstract, MemoryDojo contains 155 multi-session, long-horizon trajectories across four domains and supports five memory systems. The authors also report a memory-aware poison optimization process that increases poisoning efficacy. The saved abstract does not identify those systems or domains, quantify the increase, or provide attack success rates. These are author-reported findings, not results independently reproduced for this article.[^1]

:::analysis
The issue sits at T6 (evaluations) and T5 (agents): benchmark coverage determines how far a finding can be generalized, while memory handling determines how earlier content can affect later actions. The reported susceptibility does not establish exposure in a particular deployment; users and operators should check which memory architecture and configuration their system uses and whether relevant evaluation conditions match it. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an implicated setup, although establishing an actual poisoning event requires further evidence. The saved source specifies no fixed version or recommended upgrade, so it supports no claim that a particular release resolves the risk.[^1]
:::

:::checked
On 11 November 2026, we read the supplied saved arXiv abstract page for “MemoryDojo: Benchmarking Poisoning Through LLM Agent Memory,” identified as arXiv:2611.09721v1. It establishes what the authors announced and the submission date; we did not read the full paper, inspect code, run the benchmark, or test any memory system. The reported findings remain unverified by us.[^1]
:::

[^1]: MemoryDojo: Benchmarking Poisoning Through LLM Agent Memory. arXiv, 6 November 2026. https://arxiv.org/abs/2611.09721
