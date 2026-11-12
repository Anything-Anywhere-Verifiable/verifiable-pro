---
title: "Trace2Eval Proposes Coding-Agent Evaluation From Real-World Traces"
dek: "An arXiv preprint describes reconstructing user tasks and calibrating automated judges against human assessments. Its reported score gains remain author claims, not independently tested results."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents, runtime]
event_date: 2026-11-04
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "Trace2Eval: Contextualized Evaluation of Coding Agents from Real-World Traces | arXiv | 2026-11-04 | https://arxiv.org/abs/2611.06506"
---

Ji Shi and seven coauthors submitted Trace2Eval to arXiv on 4 November 2026, proposing a dynamically updatable pipeline that builds coding-agent benchmarks from real-world interaction trajectories. The authors position it as a way to assess overall artifact quality in user workflows beyond correctness on static public tasks.[^1]

According to the abstract, a multi-agent reconstruction system analyzes filtered trajectories, recovers the original user query, restores workspace files to their pre-interaction state, and rebuilds an execution environment intended to be equivalent to the recorded trajectory. A candidate agent then executes the reconstructed query to produce an initial artifact.[^1]

The evaluation pipeline iteratively refines human rubrics through alignment among annotators and calibrates judge agents against human assessments using source-code and runtime evidence. The authors report that revising artifacts with pipeline feedback produced a mean score gain of 10.05 percentage points across 19 model-harness configurations. They report a maximum gain of 19.28 percentage points for DeepSeek-V4-Pro with Claude Code. These are reported evaluation outcomes; the saved abstract does not establish how well those gains transfer to other workflows.[^1]

:::analysis
The claim sits at T6 evaluations, T5 agents and T2 runtime: trusting a score requires assessing the rubric and judge calibration, the agent configuration, and the reconstructed environment. Users and operators should check whether their own evaluation records identify those components and substantiate reconstruction and calibration; the abstract describes these steps without giving enough detail to independently assess their fidelity. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the evaluated setup, while performance still requires separate evidence. The saved source identifies no security defect or fixed version to install.[^1]
:::

:::checked
On 10 November 2026, we read the supplied saved arXiv abstract-page text for Trace2Eval, arXiv:2611.06506, which records submission of v1 on 4 November 2026. This establishes what the authors describe and report; we did not read the full paper, inspect implementation or data, reproduce the scores, or test the system.[^1]
:::

[^1]: Trace2Eval: Contextualized Evaluation of Coding Agents from Real-World Traces. arXiv, 4 November 2026. https://arxiv.org/abs/2611.06506
