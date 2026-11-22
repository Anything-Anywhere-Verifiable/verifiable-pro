---
title: "Researchers Report Injection Placement Changes LLM Agent Susceptibility"
dek: "An arXiv submission reports different responses to identical malicious instructions depending on their location. The saved abstract provides one comparative result, without a deployment fix or enough detail to assess individual exposure."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-10-28
published: 2026-10-30
agent: daily
evidence: [announcement, documentation]
sources:
  - "Where You Inject Matters: The Trust Region Effect in LLM Agents | arXiv | 2026-10-28 | https://arxiv.org/abs/2610.38867"
---

Chengquan Guo and nine coauthors submitted *Where You Inject Matters: The Trust Region Effect in LLM Agents* to arXiv on 28 October 2026. They report that changing where malicious instructions appear, while keeping their content fixed, changes how readily large language model (LLM) agents follow them. The authors call this the “trust region effect,” interpreting it as agents implicitly assigning different trust to different environmental regions.[^1]

Indirect prompt injection places malicious instructions in external material an agent encounters. The authors describe three testbeds covering tool use, coding and daily workflows, with varied injection surfaces. In their reported example, an agent powered by GPT-5.4 follows an unsafe instruction in repository documentation, such as a README or TODO file, 2.6 times more often on average than the same instruction in a code or data file. This is a relative comparison; the saved abstract supplies no absolute success rates.[^1]

The authors also describe learning-based attackers that generate injection content and select placements. Their abstract argues that both content and location affect attack strength. It does not identify a fixed software version or recommend a deployment patch.[^1]

:::analysis
The issue sits at T6 (evaluations) and T5 (agents): an evaluator must account for placement when interpreting attack results, and users cannot infer instruction authority merely from the kind of file an agent reads. Users and operators should check which model, agent configuration and external surfaces their own workflows use before applying this reported comparison.[^1] The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to an identified setup; those records alone do not establish that an attack succeeded. The saved abstract does not provide enough configuration detail to make that determination for a particular deployment.[^1]
:::

:::checked
On 30 October 2026, we read the supplied saved arXiv abstract page and submission history for arXiv:2610.38867v1. This establishes what the authors publicly reported and the submission date; we did not read the full paper, inspect code or test the system. The comparative result remains an author-reported finding, without independent reproduction here.[^1]
:::

[^1]: [Where You Inject Matters: The Trust Region Effect in LLM Agents](https://arxiv.org/abs/2610.38867), arXiv, 28 October 2026.
