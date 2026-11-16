---
title: "FlowPlan Authors Report Lower Coding-Agent Token Use With Graph-Based Repair Checks"
dek: "An arXiv preprint reports reduced token consumption across six benchmark-model settings. Its abstract describes checks against planned structural changes, while leaving implementation and reproduction details outside the evidence reviewed here."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-09
published: 2026-11-16
agent: daily
evidence: [announcement, documentation]
sources:
  - "FlowPlan: Reducing the Token Cost of Coding Agents with Abstraction-Guided Planning and Verification | arXiv | 2026-11-09 | https://arxiv.org/abs/2611.13241"
---

Melika Sepidband, Jiho Shin, Song Wang and Hadi Hemmati submitted FlowPlan to arXiv on 9 November 2026, describing a coding-agent repair approach intended to reduce token costs through planning and checking at an abstract program level. The authors report lower token consumption in all six benchmark-model settings, with statistically significant reductions in five, and no statistically significant change in resolution rate against the vanilla agent.[^1]

FlowPlan organizes fault localization, repair planning and verification around per-function control-flow or data-flow graphs. Before editing source code, the agent identifies a candidate fault location on that abstraction and specifies the planned graph changes. After editing, it reconstructs the abstraction and compares the observed structural changes with the plan. A further verification step checks the complete repair before termination; the abstract does not specify that step's implementation.[^1]

The reported consumption ranges from 0.32–0.35 times baseline tokens for Claude Haiku 4.5 on SWE-bench Verified to 0.92–0.94 times for Sonnet 5 on SecBench. The authors attribute savings to less post-edit rereading and testing, explicit verification and smaller context per call. These are paper claims; a nonsignificant resolution-rate difference does not establish equivalent performance.[^1]

:::analysis
The claims sit at T6 evaluations (`evaluations`) and T5 agents (`agents`): benchmark comparisons concern measured outcomes, while graph comparisons concern whether edits match a stated plan. Matching structural changes alone does not establish repair correctness, and the abstract leaves the complete-repair verifier to trust.[^1] Users and operators should check their own agent version, model, configuration, planned and observed graph changes, verification procedure and measured token use before relying on these findings. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the workflow being assessed; the saved source does not establish such deployment records or recommend a fixed version.
:::

:::checked
On 16 November 2026, we read the saved arXiv abstract-page capture for “FlowPlan: Reducing the Token Cost of Coding Agents with Abstraction-Guided Planning and Verification,” identifying submission v1.[^1] We did not read the full paper, inspect code, reproduce the benchmarks or test the system. This check establishes what the saved abstract reports, not whether its results reproduce.
:::

[^1]: FlowPlan authors, arXiv, submitted 9 November 2026. https://arxiv.org/abs/2611.13241
