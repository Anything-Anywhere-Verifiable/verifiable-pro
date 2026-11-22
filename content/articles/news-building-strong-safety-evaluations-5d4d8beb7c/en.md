---
title: "Anthropic Sets Out Recommendations for AI Safety Evaluations"
dek: "Anthropic describes how it designs and grades safety evaluations, while warning that scores depend on the scenarios, environment and measurement choices behind them."
kind: news
topics: [evaluation-audits]
layers: [evaluations, runtime, models]
event_date: 2026-11-13
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Building strong safety evaluations | www.anthropic.com | 2026-11-13 | https://www.anthropic.com/research/building-strong-safety-evaluations"
---

On 13 November 2026, Anthropic published recommendations for building AI safety evaluations, arguing that a model safety claim depends on how well the evaluation measures the behavior in question. The company says its evaluations inform deployment and safeguard decisions, and that results can change with details such as question format and answer order.[^1]

Anthropic describes multi-turn evaluations in which a domain expert specifies a simulated user's objectives and tactics, a separate Claude model generates subsequent user turns, and a grader model scores the transcript against a risk-specific rubric. It says a conversation fails its appropriate-response measure if any turn is judged inappropriate. The company also recommends testing harmful and benign requests in the same domain, to measure both harmful compliance and over-refusal.[^1]

The company says evaluation settings should match the intended deployment, including tool access and system prompts. It recommends checking graders against human labels, testing their sensitivity to changes in models or rubrics, and flagging grading failures. Anthropic also recommends running safety evaluations in a sandbox without internet access and monitoring them in real time; it says it has temporarily stopped many evaluations that give models internet access following its own incidents.[^1]

:::analysis
The issue spans evaluations (T6), runtime (T2) and models (T3): a score depends on the test and grader, the environment, and the model being assessed. In stack order, these are T6, T3 and T2. Users and operators should check that their own evaluation scenarios, graders and environment match the behavior and deployment they want to assess; a reported score alone leaves those choices to trust. Identifiability matters too: if the exact model version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to the system being evaluated. The source does not establish that such records are available to users.[^1]
:::

:::checked
On 18 November 2026, we read the saved text of Anthropic's [“Building strong safety evaluations”](https://www.anthropic.com/research/building-strong-safety-evaluations), published 13 November 2026.[^1] We did not test Anthropic's evaluation system or independently verify its practices or results. The saved text available to us ends during its discussion of preregistration, so we cannot assess the remainder of the page.
:::
