---
title: "LeanGuard Authors Report Lean-Checked Guardrails for Tool-Using Agents"
dek: "An arXiv preprint describes policy checks before tool execution and reports fewer forbidden actions. The saved abstract supports attribution of those claims, without independently validating the implementation or results."
kind: news
topics: [formal-verification, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-02
published: 2026-11-11
agent: daily
evidence: [announcement, documentation]
sources:
  - "LEANGUARD: Lean-Verified Guardrails for Tool-Using Agents | arXiv | 2026-11-02 | https://arxiv.org/abs/2611.02332"
---

Sreehari Sankar and co-authors submitted LeanGuard to arXiv on 2 November 2026. The preprint describes a runtime that checks each proposed tool call against a policy written in Lean4 before forwarding it to the environment. The authors report eliminating calls forbidden by their Lean policy in a Tau-Bench evaluation.[^1]

According to the abstract, policies combine conditions on state with scoped temporal operators that refer to execution history. Evaluation is fail-closed, and the authors say their decision procedure is mathematically proved equivalent to a LeanLTL semantics. After a denial, feedback can identify the violated rule and offer a hint. A separate repair mechanism uses Lean metaprogramming to search for a nearby admissible call and prove policy admission without using the model.[^1]

On Tau-Bench with five Qwen models ranging from 0.8 billion to 27 billion parameters, the authors report at least 33 forbidden calls from unguarded agents and none from LeanGuard; task success with feedback did not change significantly. On DTap, they report direct prompt-injection success falling from 57.9% to 5.9%. These are results reported in the abstract, whose stated policy and evaluation scope matter when interpreting them.[^1]

:::analysis
The claim sits at T5 (agents) and T2 (runtime): policy admission governs proposed actions at the execution boundary. Equivalence to a specified semantics would support trust in the policy decision within that formal scope; users and verifiers still need to check that their intended restrictions are represented and their tool calls pass through the checker. Operators should verify and record the deployed checker version, policy configuration and enforcement path: the property at stake is identifiability, because a user can determine whether they were exposed to a particular deployment only if its exact serving version and configuration are recorded and checkable. The saved abstract provides no deployment-identification mechanism or recommended fixed version.[^1]
:::

:::checked
On 11 November 2026, we read the saved arXiv abstract page for “LEANGUARD: Lean-Verified Guardrails for Tool-Using Agents,” identifying submission v1 dated 2 November 2026. We did not read the full paper, inspect code, check Lean proofs or test the system; this reading establishes what the abstract reports, without independently confirming its results.[^1]
:::

[^1]: [LEANGUARD: Lean-Verified Guardrails for Tool-Using Agents](https://arxiv.org/abs/2611.02332), arXiv, 2 November 2026.
