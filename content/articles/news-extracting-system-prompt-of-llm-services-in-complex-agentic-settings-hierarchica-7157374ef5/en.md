---
title: "Researchers Report Gains in System Prompt Extraction From Agentic Services"
dek: "The ExtraHerO preprint proposes structural reconstruction and downstream attack metrics. Its saved abstract reports improvements but does not identify affected deployments or a fixed version."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-11-03
published: 2026-11-04
agent: daily
evidence: [announcement, documentation]
sources:
  - "Extracting System Prompt of LLM Services in Complex (Agentic) Settings: Hierarchical Optimization and Reliable Evaluation Metrics | arXiv | 2026-11-03 | https://arxiv.org/abs/2611.04803"
---

Researchers Shuaidong Li and colleagues submitted a preprint on 3 November 2026 proposing Extraction with Hierarchical Optimization (ExtraHerO), a method for extracting system prompts from large language model (LLM) services. The authors report improvements on chatbots and agents, including settings where attackers observe only post-processed outputs, such as agent actions.[^1]

The abstract describes two obstacles: longer, structured prompts containing tool schemas, execution logic and safety guardrails; and restricted visibility into raw model responses. ExtraHerO reconstructs prompts hierarchically using a predefined structural template. It updates adversarial queries using differences between feedback and that template, and monitors information gain to stop or reset optimization.[^1]

The authors also argue that prompt-fidelity metrics can mislead when they ignore structure. Their approach combines global textual similarity with emphasis on structural keywords, and introduces “adversarial utility” to measure whether extracted prompts help downstream attacks. The abstract reports average improvements in fidelity, functionality and adversarial utility of 12.5%, 2.3% and 6.0% on chatbots, respectively, and 12.2%, 34.3% and 30.5% on agents. These are author-reported experimental results; the saved abstract does not specify the comparison baselines or whether the percentages represent relative changes.[^1]

:::analysis
The issue sits at T6 (evaluations) and T5 (agents): judging reconstruction quality and interpreting visible agent actions require different evidence, so a similarity score alone cannot establish downstream attack usefulness. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed when applicable affected conditions are known. Users and operators should verify those deployment records and whether their prompt structures and output interfaces match the conditions described; this abstract supplies neither an affected-version list nor a recommended fixed version, so it cannot establish an individual deployment’s exposure.[^1]
:::

:::checked
On 4 November 2026, we read the saved arXiv abstract page for “Extracting System Prompt of LLM Services in Complex (Agentic) Settings: Hierarchical Optimization and Reliable Evaluation Metrics,” arXiv:2611.04803v1. We checked its abstract and submission history, not the full paper, code or experimental artifacts. We did not test the system or independently reproduce the reported gains.[^1]
:::

[^1]: https://arxiv.org/abs/2611.04803
