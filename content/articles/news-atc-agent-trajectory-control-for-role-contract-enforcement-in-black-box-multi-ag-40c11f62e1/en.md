---
title: "ATC Authors Propose Message-Level Control for Agent Role Drift"
dek: "The research proposes checking and regenerating agent messages against explicit role contracts. Its arXiv abstract reports improvements, but the saved source does not establish deployment behavior or reproducible results."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-03
published: 2026-11-17
agent: daily
evidence: [announcement, documentation]
sources:
  - "ATC: Agent Trajectory Control for Role-Contract Enforcement in Black-Box Multi-Agent Systems | arXiv | 2026-11-03 | https://arxiv.org/abs/2611.04321"
---

Maisha Maliha, Vishal Pramanik and Sumit Kumar Jha proposed Agent Trajectory Control (ATC) in an arXiv submission dated 3 November 2026. The method checks whether an agent’s proposed message exceeds its assigned authority before admitting it to a shared conversation, according to the saved abstract. The listing identifies version v1 and says the paper was accepted at EMNLP 2026.[^1]

The authors define role drift as a turn-level breach of an agent’s role contract. Examples include a verifier beginning to plan, a retriever asserting unsupported conclusions, or an executor changing state without approval. ATC makes role authority explicit, then scores proposed outputs for out-of-role deviation, leakage into other roles’ functions, impermissible speech acts and logical contract breaches. It computes a leakage-regularized target to constrain regeneration and checks the revised message again before admission. The authors say this message-level approach accommodates agents whose internal representations are unavailable.[^1]

The abstract reports better task performance and role consistency, with lower role-drift energy, against baselines covering prompting, memory, workflow control and activation editing. It says the largest gains occur under explicit role-confusion stress tests and in larger, more diverse teams. The saved abstract supplies no numerical results or experimental configurations, so these remain author-reported findings.[^1]

:::analysis
The claims sit at T6 (evaluations) and T5 (agents): reported comparisons concern performance, while enforcement concerns authority at the shared-message boundary. Users still depend on the adequacy of role contracts, scoring and admission checks; this abstract does not establish their correctness. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that deployment’s role-control behavior. Users and operators should check those records, the applicable contracts and whether regenerated messages are rechecked; these are verification questions derived from the proposed mechanism, and the source recommends no fixed software version.[^1]
:::

:::checked
On 17 November 2026, we read the supplied saved arXiv abstract-page text for “ATC: Agent Trajectory Control for Role-Contract Enforcement in Black-Box Multi-Agent Systems,” including its submission history and acceptance comment. We did not read the full paper, inspect code, reproduce results or test the system. This reading establishes what the listing and abstract report, not operational effectiveness.[^1]
:::

[^1]: https://arxiv.org/abs/2611.04321

Lead photo: Maisha Maliha, Vishal Pramanik, Sumit Kumar Jha · CC BY 4.0.
