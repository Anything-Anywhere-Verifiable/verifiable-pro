---
title: "Paper Describes Limits on Certifying Programs Written by AI Agents"
dek: "A preprint argues that a gatekeeper using finite, machine-checkable evidence cannot classify every program against certain safety rules. The result depends on the paper’s stated model."
kind: news
topics: [formal-verification, agents-accountability]
layers: [agents]
event_date: 2026-11-09
published: 2026-11-20
agent: daily
evidence: [announcement, documentation]
sources:
  - "No finite rulebook can certify every safe program: an impossibility theorem for gatekeeping AI agents | arXiv | 2026-11-09 | https://arxiv.org/abs/2611.13367"
---

A preprint submitted to arXiv on 9 November 2026 says that a gatekeeper cannot use finite, machine-checkable evidence to completely classify every program written by an AI assistant against certain behavioral rules. Author Tomas Perez-Acle considers a gatekeeper that decides from code alone whether a program may run.[^1]

The abstract considers three requirements: never taking a forbidden action, never letting output depend on a secret, and eventually answering. It says that for forbidden actions, an execution can reveal a violation, but finite observation cannot clear a safe program forever. For confidentiality and eventual response, the abstract says neither compliance nor noncompliance can always be established through the stipulated finite evidence.[^1]

The author also says a time limit makes the problem checkable, but can require running a program for essentially the entire limit. The abstract describes a narrower alternative: a checkable list containing everything the gatekeeper must allow and nothing it must refuse. It reports simulations on random programs and self-referential adversaries, but the saved abstract does not provide enough detail to assess their design or results independently.[^1]

:::analysis
The issue sits at the agents layer (T5): it concerns a gatekeeper deciding whether agent-written code may execute. A user or verifier should check which rules their own gatekeeper enforces, what evidence it uses and whether its decision falls within the model described; the abstract alone does not establish those facts for a deployed system. Identifiability matters too: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to an identified issue affecting that version and configuration. Operators should check those records and their gatekeeper’s actual behavior; this source recommends no fixed software version.[^1]
:::

:::checked
For this preview prepared on 20 November 2026, we read the saved arXiv abstract page for Perez-Acle’s paper, including its submission history. We did not read the full paper, independently verify the mathematical arguments or simulations, or test a gatekeeping system.[^1]
:::

Lead photo: Tomas Perez-Acle · CC BY 4.0.
