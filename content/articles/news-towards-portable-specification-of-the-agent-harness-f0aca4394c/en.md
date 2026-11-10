---
title: "Researchers Propose Versioned Records for Agent Harnesses"
dek: "An arXiv preprint proposes recording which model ran in which harness, including configuration changes within a run. The saved abstract describes a framework, without establishing deployment or effectiveness."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-10-29
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "Towards Portable Specification of the Agent Harness | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.40917"
---

Nicolas Gertler, Claudio Novelli and Luciano Floridi proposed a portable specification framework for agent harnesses in a preprint submitted to arXiv on 29 October 2026. The framework would record which model ran in which harness, treating the infrastructure surrounding a model as a versioned part of the system.[^1]

The authors describe the harness as the infrastructure through which large language models act. Their abstract says they decompose it into eight functional components that can be specified and compared across systems. The saved abstract does not name those components or give the framework's detailed record format.[^1]

The authors argue that different harness configurations can produce several-fold differences in reported scores for the same model, and that much of an agent's attack surface lies in its harness. These are claims in the abstract; our reading does not independently establish the score differences or assess the attack surface.[^1]

Existing model and agent cards, they write, provide release and operational information without establishing the sequence of effective configurations during a run. Harnesses can change between releases, between runs and, when agents edit their own tools or configuration, within a run. The abstract also says enacted AI laws contain relevant documentation duties, subject to scope and application dates, without prescribing this common record.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T2 runtime: interpreting a score or an agent's actions requires knowing the configuration that produced them. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a configuration under examination. Users and operators should verify whether their own records identify the model, harness version and effective configuration changes within each run; the abstract recommends explicit versioned specification but names no fixed software version. A proposed record alone does not establish that a deployed system matches it.[^1]
:::

:::checked
On 10 November 2026, we read the saved arXiv abstract page for *Towards Portable Specification of the Agent Harness*, including its v1 submission history. We did not read the full paper or test the system. This check establishes what the saved page reports, not implementation, adoption or effectiveness.[^1]
:::

[^1]: *Towards Portable Specification of the Agent Harness*. arXiv, 29 October 2026. https://arxiv.org/abs/2610.40917

Lead photo: Nicolas Gertler, Claudio Novelli, Luciano Floridi · CC BY 4.0.
