---
title: "Paper Catalogs Agent Harness Decisions and Tests"
dek: "A preprint describes testable invariants for the software that turns language-model replies into actions. Its worked example is a self-assessment of the author’s own harness."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-11-15
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Anatomy of an Agent Harness: Decisions, Invariants and Corner Cases | arXiv | 2026-11-15 | https://arxiv.org/abs/2611.19960"
---

On 15 November 2026, Resham Joshi submitted a preprint cataloging design decisions and testable invariants for agent harnesses, the programs that turn language-model replies into actions. An invariant is a condition intended to hold when the system encounters a specified situation. The paper’s abstract presents the catalog as a way to document decisions that are often embedded in code.[^1]

A harness assembles model requests, executes requested tools, decides which actions need a person’s permission, stores conversations, recovers from failures and displays what happened. The paper describes a system model with trust boundaries and 30 decision cards in six groups. Each card records options and costs, an invariant, corner cases, a test and an evidence tag. The abstract also describes six classes of failure, a checklist and a test method using scripted providers, recorded behavior and planted changes.[^1]

The author says the cards draw on building Crewroom, the author’s desktop harness, manually testing ten other harnesses and studying open-source harnesses as references. Some cataloged patterns were adopted from those references, so the catalog is not independent of them. Of 83 invariant clauses, the abstract labels 56 Tested, 12 Believed and 15 Open.[^1]

In the paper’s worked example, Crewroom’s builder applied the checklist without a second rater: 11 of 30 items held, 14 did not and five were not tested. The abstract says the example is not a ranking and that the paper does not evaluate or rank other harnesses or claim results for answer quality, cost or other platforms.[^1]

:::analysis
The work sits at T6 evaluations and T5 agents: the distinction matters because a checklist result concerns the harness and conditions examined, while a user must still trust that the result applies to the system serving them. Identifiability is the property at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an identified issue. Users and operators should check their own harness version, configuration and behavior against the relevant invariants and tests; the saved abstract recommends no fixed version.[^1]
:::

:::checked
On 24 November 2026, we read the saved arXiv abstract page for *Anatomy of an Agent Harness: Decisions, Invariants and Corner Cases*, submitted by Resham Joshi.[^1] We did not read the full paper or test Crewroom or any other harness, and cannot independently confirm the reported results.
:::
