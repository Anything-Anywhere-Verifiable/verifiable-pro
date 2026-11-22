---
title: "Researchers Report Agent Self-Evaluation Method Without External Feedback"
dek: "A paper describes agents that inspect their own task artifacts and update how they execute and evaluate work. Its benchmark results are author-reported."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-11
published: 2026-11-19
agent: daily
evidence: [announcement, documentation]
sources:
  - "Verify by Doing: Co-Evolving Agent Execution and Evaluation without External Feedback | arXiv | 2026-11-11 | https://arxiv.org/abs/2611.15276"
---

On 11 November 2026, researchers submitted a paper describing Verify by Doing (VbD), a method for improving an agent's execution and evaluation procedures within a task when external feedback is unavailable. The paper says the method keeps the model's weights fixed while changing the procedures around it.[^1]

The authors describe two components: an Actor that executes tasks and an Evaluator that uses tools to inspect artifacts and the state of the environment. The Evaluator's findings provide an internal signal for selecting outputs and guiding changes to both components. Proposed Evaluators are compared on common candidate outputs, while proposed Actor updates require support from their own fresh outputs.[^1]

The abstract reports the highest overall scores among the compared methods without external feedback on AutomationBench, τ³ Banking and selected GDPval tasks. It claims gains of 3.3, 4.1 and 2.3 percentage points, respectively, over the strongest baselines on the main backbone. The authors also report ablations supporting active verification and Evaluator evolution, and say improved verification selected successful outputs from fixed candidate pools without generating new ones. These are the authors' reported results, not independent findings.[^1]

:::analysis
The work sits at T6 evaluations and T5 agents: the Evaluator's checks affect which agent outputs are selected, so their usefulness depends on what the tools inspect and how the findings are interpreted. A user or verifier still needs evidence that those checks cover the task and that the reported outcomes apply to their own system. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to that version and configuration. Users and operators should verify those records and the checks used in their deployment; the saved source recommends no fixed version.[^1]
:::

:::checked
On 19 November 2026, we read the saved arXiv abstract page for “Verify by Doing,” including its submission history.[^1] We did not read the full paper or test the system, and cannot independently confirm the reported results or their applicability to a deployment. Source: https://arxiv.org/abs/2611.15276
:::
