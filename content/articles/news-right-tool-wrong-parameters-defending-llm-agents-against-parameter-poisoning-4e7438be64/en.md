---
title: "AuthorityFlow Authors Report Defense Against Agent Parameter Poisoning"
dek: "An arXiv preprint targets attacks that keep the intended tool action while changing its arguments. Its abstract reports reduced attack success alongside lower benign task utility."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-03
published: 2026-11-04
agent: daily
evidence: [announcement, documentation]
sources:
  - "Right Tool, Wrong Parameters: Defending LLM Agents Against Parameter Poisoning | arXiv | 2026-11-03 | https://arxiv.org/abs/2611.04673"
---

Yao Wang, Zehua Ma, Weiming Zhang and Han Fang submitted *Right Tool, Wrong Parameters: Defending LLM Agents Against Parameter Poisoning* to arXiv on 3 November 2026. The preprint proposes AuthorityFlow, a defense against indirect prompt injection that changes tool arguments while preserving the agent’s intended action.[^1]

The authors call this attack surface parameter poisoning. An attacker might alter a recipient or another task-critical value without introducing a new tool invocation. That makes action-level detection insufficient in the authors’ account: legitimate user requests can also require parameter changes, so the question is which information has authority to determine each argument.[^1]

AuthorityFlow has three stages, according to the abstract. It interprets the user query to construct a task-specific trust hierarchy over available information fields; traces each argument’s value to its supporting field; and accepts that value only when the field is trusted to determine that parameter for the task. Influence from lower-trust fields is flagged as potential poisoning.[^1]

The authors also introduce FactAuthBench. They report attack success falling from 93.06% without defense to 9.03% with AuthorityFlow, while benign task utility falls from 90.28% to 82.64%. These are abstract-reported evaluation results; our reading does not independently establish their reproducibility or applicability to deployed agents.[^1]

:::analysis
The issue sits at T6 (evaluations) and T5 (agents): benchmark results describe measured behavior, while argument provenance determines which information an agent should trust. Users and operators should verify how their own systems assign authority to fields and trace tool arguments; the saved abstract specifies no fixed software version or deployment configuration. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant setup, although those records alone do not establish whether an attack succeeded. This is a verification requirement drawn from the reported problem, not a capability demonstrated by the abstract.[^1]
:::

:::checked
On 4 November 2026, we read the saved arXiv abstract page for arXiv:2611.04673v1, including its submission history. We did not read the full paper, inspect code or test the system. The saved page establishes what the authors report, not independent confirmation of the defense’s effectiveness.[^1]
:::

[^1]: [Right Tool, Wrong Parameters: Defending LLM Agents Against Parameter Poisoning](https://arxiv.org/abs/2611.04673), arXiv, 3 November 2026.
