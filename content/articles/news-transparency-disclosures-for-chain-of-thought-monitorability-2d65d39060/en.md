---
title: "Researchers Propose Disclosures to Track AI Reasoning Monitorability"
dek: "A paper proposes five disclosure indicators for monitoring AI chain-of-thought reasoning. Its authors say an audit found gaps in current developer disclosures."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, models]
event_date: 2026-11-10
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Transparency Disclosures for Chain-of-Thought Monitorability | arXiv | 2026-11-10 | https://arxiv.org/abs/2611.13873"
---

On 10 November 2026, researchers Jacob Davies and Theo Bearman submitted a paper proposing disclosures to track whether advanced AI systems’ chain-of-thought reasoning remains monitorable. Chain-of-thought (CoT) monitoring examines a model’s reasoning as a way to monitor its behavior. The authors argue that developers should report indicators that make threats to this monitoring trackable and support coordination to preserve it.[^1]

The paper’s abstract identifies five indicators across a five-step chain on which CoT monitoring depends. The first covers third-party access to CoT and base architecture specifications; the authors say it also supports external verification of the remaining indicators. The others concern CoT quality, through naturalness and faithfulness, and monitoring effectiveness, through detection and uplift. The abstract does not describe how each indicator is measured.[^1]

The authors report an audit of public disclosures by Anthropic, OpenAI and Google DeepMind. According to the abstract, no developer disclosed the full set, although each indicator had been reported by at least one of them. The authors say current disclosures rely largely on developers’ own evaluations and recommend repeating a cross-developer audit with deeper access, using embedded evaluators or an Independent Verification Organization.[^1]

:::analysis
The issue sits at T6 evaluations and T3 models: a reader assessing monitorability needs evidence about model reasoning and about how monitoring was evaluated. Disclosures and access can help an outside verifier examine those claims, while the abstract alone leaves the reported audit and measurements to trust. Identifiability also matters: if the exact model version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular configuration. Users and operators should check which version and configuration served them and whether relevant monitoring evidence is available; the abstract recommends no fixed version.[^1]
:::

:::checked
On 18 November 2026 we read the saved arXiv abstract page for “Transparency Disclosures for Chain-of-Thought Monitorability” by Davies and Bearman.[^1] We did not read the full paper or test any system, and cannot independently confirm the reported audit or its findings from the abstract alone.
:::

Lead photo: Jacob Davies, Theo Bearman · CC BY 4.0.
