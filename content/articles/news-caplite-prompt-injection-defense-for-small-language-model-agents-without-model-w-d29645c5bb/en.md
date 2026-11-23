---
title: "Researchers Propose CapLite to Restrict Agent Writes"
dek: "A preprint describes a prompt-injection defense that derives its policy from tool schemas and commits write calls before reading tool results. Its security and evaluation results remain author claims."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-12
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "CapLite: Prompt-Injection Defense for Small Language Model Agents without Model-Written Security Artifacts | arXiv | 2026-11-12 | https://arxiv.org/abs/2611.17115"
---

Researchers Zimo Xu, Wenzhuo Liu and Hideki Nakayama submitted a preprint on 12 November 2026 proposing CapLite, a defense against prompt injection for agents built on small language models. Prompt injection can place instructions in material an agent reads and try to redirect its actions. The authors focus on write calls: tool actions that change something or send information. Their abstract reports a design intended to restrict those actions to what the user requested.[^1]

The authors say CapLite derives a policy from tool schemas and commits write calls before reading any tool result. It admits a write only if every argument deciding whom or what the action affects is stated in the user's request. The authors claim this gives write integrity: injected text cannot add a write or redirect one to an unstated recipient, amount, object or destination. The saved abstract does not provide enough detail to independently establish that guarantee.[^1]

The preprint contrasts this approach with defenses that ask an agent's model to produce artifacts such as policies or dependency graphs for code to enforce. Across 15 open-weight models, the authors report attacks admitted by model-written artifacts for 14 models with Progent, 13 with IPIGuard and 11 with DRIFT; they also report that CaMeL programs failed to run in up to 68% of episodes. They say no attack succeeded in 13,935 attacked AgentDojo episodes with CapLite. These are reported experimental results, not independently checked findings.[^1]

:::analysis
The issue sits at T6, evaluations, and T5, agents: the reported tests concern an agent's authority to use tools, while the agent-layer claim depends on its policy and enforcement in a particular deployment. A user or verifier must trust the reported results unless they can inspect the relevant evidence, and should check their own agent's tool schemas, write-call policy and configuration. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the conditions at issue. The abstract does not identify a fixed version to install or establish how a deployment records that information.[^1]
:::

:::checked
On 23 November 2026, we read the saved arXiv abstract page for *CapLite: Prompt-Injection Defense for Small Language Model Agents without Model-Written Security Artifacts*, version 1. We did not read the full paper or test the system, and could not independently confirm the authors' guarantee or experimental results.[^1]
:::
