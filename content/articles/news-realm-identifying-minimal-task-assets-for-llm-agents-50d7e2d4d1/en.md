---
title: "REALM Authors Report Lower Prompt-Injection Success With Task-Scoped Assets"
dek: "An arXiv preprint separates discovering resources from authorizing their use. Its abstract reports lower attack success alongside limited task completion; we read the saved abstract page and did not test the system."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-10-29
published: 2026-11-05
agent: daily
evidence: [announcement, documentation]
sources:
  - "REALM: Identifying Minimal Task Assets for LLM Agents | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.39155"
---

Zihou Ren, Byungchul Tak and Long Wang submitted REALM: Identifying Minimal Task Assets for LLM Agents to arXiv on 29 October 2026. The authors propose identifying and maintaining the resources an agent needs for a task, including resources discovered during execution. Their stated problem is excess access to files, accounts and services, which prompt injection can exploit to redirect an agent toward unrelated resources.[^1]

REALM, short for Required Execution Assets Linked to a Mission, represents required assets as dependency-graph nodes and resolves their prerequisite relationships. According to the abstract, newly discovered assets enter through source-scoped selection, separating discovery from authorization while leaving the agent free to choose its computation. A REALM Builder maintains selected grants and projects Asset Files; a Partial API Manager exposes resource-bound Partial APIs to the agent inside a Task Container.[^1]

The authors report results on 60 clean tasks and 560 injected cases in AgentDyn, using qwen3.5-flash as the base model. The abstract gives task-completion rates of 40.0% and 36.4%, respectively, and reports attack success rate (ASR) falling from 16.6% to 0.2%. These are the authors’ reported evaluation results; reading the abstract does not independently establish their reproducibility or applicability to another deployment.[^1]

:::analysis
The claim spans T6 evaluations, T5 agents and T2 runtime: benchmark evidence, task-level authorization decisions and the interfaces exposing resources. Users and operators should check their own selected grants, newly discovered asset authorization and resource-bound interfaces before relying on this approach; the saved abstract supplies no fixed-version recommendation. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant deployment condition; this source does not establish such deployment records or checks.[^1]
:::

:::checked
On 5 November 2026, we read the supplied saved arXiv abstract page for REALM, identifier 2610.39155, whose submission history lists v1 on 29 October 2026. This establishes what the page reports about the proposal and results. We did not read the full paper, inspect code, reproduce the evaluation or test the system.[^1]
:::

[^1]: REALM: Identifying Minimal Task Assets for LLM Agents. arXiv, 29 October 2026. https://arxiv.org/abs/2610.39155
