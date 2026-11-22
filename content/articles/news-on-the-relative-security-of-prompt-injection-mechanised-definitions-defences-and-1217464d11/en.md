---
title: "PlanTERS Paper Defines Prompt-Injection Security Relative to a Reference Agent"
dek: "An arXiv preprint reports mechanized results for agent defenses under explicit assumptions. Its security definition allows leaks already present in the reference agent."
kind: news
topics: [formal-verification, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-08
published: 2026-11-17
agent: daily
evidence: [announcement, documentation]
sources:
  - "On the Relative Security of Prompt Injection: Mechanised Definitions, Defences and Verdicts for LLM Agents | arXiv | 2026-11-08 | https://arxiv.org/abs/2611.11506"
---

Brijesh Dongol submitted a preprint introducing PlanTERS on 8 November 2026, proposing a relative definition of prompt-injection security for large language model (LLM) agents. The arXiv abstract reports mechanized results in Isabelle/HOL for agents using fences, budgets, approvals, loops and dual LLMs.[^1]

The paper starts from a practical difficulty: useful agents must let untrusted material, such as emails and web pages, influence their actions. It therefore compares an agent with a reference that executes the same plan under the same runtime monitor, using a model that never obeys untrusted content. Relative security means that every leak from the agent is already a leak from that reference. This definition permits baseline leakage; it does not claim that the reference keeps all user data secret.[^1]

The abstract reports a fence theorem: revoking injectable tools at the first untrusted read, without restoring them, makes every plan relatively secure at the event level on finite runs. The result assumes each injection is a single call and model obedience follows a schedule fixed in advance. A fairness condition extends the result to potentially infinite runs. The abstract says the framework proves or refutes relative security for several defense patterns, without listing their individual verdicts.[^1]

:::analysis
The claim sits at T5 agents and T2 runtime: trust depends on the agent plan, model-behavior assumptions and runtime monitor matching the formal setting. Users and operators should check their tool-revocation behavior and those assumptions before applying the reported theorem; the saved source recommends no fixed software version. The operational property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant setup, although those records alone do not establish leakage or theorem applicability.[^1]
:::

:::checked
On 17 November 2026, we read the saved arXiv abstract-page snapshot for “On the Relative Security of Prompt Injection: Mechanised Definitions, Defences and Verdicts for LLM Agents,” identifying submission v1. We did not read the full paper or proof artifacts, reproduce the proofs, or test a system. This check establishes what the abstract reports, not independent validation of its results.[^1]
:::

[^1]: Brijesh Dongol, arXiv, submitted 8 November 2026. https://arxiv.org/abs/2611.11506
