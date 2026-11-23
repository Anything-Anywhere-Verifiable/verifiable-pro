---
title: "Researchers Report Authorization Gaps Across Agent Frameworks"
dek: "A preprint reports unauthorized tool use and other boundary failures in experiments across four orchestration frameworks. Its abstract also describes protections that stopped specific operations in the configurations tested."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-16
published: 2026-11-22
agent: daily
evidence: [announcement, documentation]
sources:
  - "Evaluating Authorization and Trust Boundaries in Agentic Orchestration Frameworks | arXiv | 2026-11-16 | https://arxiv.org/abs/2611.21259"
---

A preprint submitted to arXiv on 16 November 2026 reports that adversarial inputs induced unauthorized tool invocation in an evaluation of agentic orchestration frameworks. The authors studied LangChain, LangGraph, AutoGen and OpenClaw in 12 experiments using the same language model, gpt-4o-mini.[^1]

According to the abstract, the experiments mapped to the OWASP Top 10 for Agentic Applications and covered prompt injection, unauthorized resource access and command execution, memory poisoning, and attacks on inter-agent trust and identity. The authors report that tool chaining, stale filesystem validation, encoded instructions and delegation between agents exposed weaknesses in authorization across component boundaries.[^1]

The abstract distinguishes memory poisoning from conventional access-control violations: untrusted state influenced responses. It also says that, in the protected configurations evaluated, explicit authorization, controlled capability assignment, filesystem containment and execution safeguards prevented specific unauthorized operations. Those are findings about the configurations and operations evaluated; the abstract does not establish that every deployment of these frameworks is vulnerable or protected.[^1]

:::analysis
The issue sits at T6, evaluations, and T5, agents: readers must assess both what the experiments actually checked and how an agent workflow authorizes actions and handles information. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant condition; an abstract alone cannot identify their deployment or establish its behavior. Users and operators should check their own versions and configurations, including authorization, capability assignment, filesystem containment and execution safeguards; the saved abstract names no fixed version. A verifier still has to trust or independently check the deployment records and how those controls operate.[^1]
:::

:::checked
For this preview prepared on 22 November 2026, we read the saved arXiv abstract page for *Evaluating Authorization and Trust Boundaries in Agentic Orchestration Frameworks*.[^1] We did not read the full paper or test the system, and the abstract does not provide enough detail to independently confirm the experiments or identify affected or fixed framework versions.
:::

Lead photo: Sahaya Jestus Lazer, Kshitiz Aryal, Maanak Gupta, Elisa Bertino · CC BY 4.0.
