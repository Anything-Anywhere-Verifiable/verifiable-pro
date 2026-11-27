---
title: "Researchers Report Verifier Judgment Changes Across Agent Abstractions"
dek: "A paper introduces a test for whether verifier judgments remain stable when agent execution evidence is abstracted. Its authors report failures and partial recovery when provenance is restored."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-11-13
published: 2026-11-27
agent: daily
evidence: [announcement, documentation]
sources:
  - "Do Verifier Judgments Survive Abstraction? Measuring Verification Transport for LLM Agent Evaluation | arXiv | 2026-11-13 | https://arxiv.org/abs/2611.18471"
---

On 13 November 2026, Disha Sheshanarayana and Sai Linisha Reddy Goli submitted a paper reporting that judgments by large language model (LLM) verifiers can change when the same agent execution is presented through different levels of abstraction. The authors call their test Verification Transport.[^1]

An agent execution may be shown to a verifier through composed tools, delegation boundaries, or compacted histories. These views can change which execution evidence is directly visible. The paper’s abstract describes matched native, abstracted, and restored views of frozen executions, with the task, trajectory, outcome, ground truth, evaluation criterion, and verifier held fixed.[^1]

Across four agent-evaluation benchmarks, seven verifier backbones, four verification protocols, and three abstraction boundaries, the authors report transport failure reaching about 31% under macro abstraction and delegation. They say direct verification more often produced incorrect verdicts, while evidence-grounded and deliberative protocols tended to abstain when observability was limited. A lower failure rate therefore does not necessarily mean a protocol is more reliable.[^1]

The authors also report that restoring corresponding execution provenance recovered 85.5% of transport failures, with lower recovery when provenance was lossy or unavailable. The abstract does not establish that this recovery rate applies to other systems.[^1]

:::analysis
The issue sits at T6 evaluations and T5 agents: a verifier’s result depends on the execution evidence available at the evaluation boundary, so users should treat a verdict in light of the view the verifier received. Users and operators should check how their own systems preserve execution provenance and whether judgments change across native, abstracted, and restored views. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular affected setup; the abstract does not identify a fixed version or establish such records for any deployment.[^1]
:::

:::checked
On 27 November 2026 we read the saved arXiv abstract page for *Do Verifier Judgments Survive Abstraction? Measuring Verification Transport for LLM Agent Evaluation*.[^1] We did not read the full paper or test the system, and cannot independently confirm the reported results.

Lead photo: Disha Sheshanarayana, Sai Linisha Reddy Goli · CC BY 4.0.
