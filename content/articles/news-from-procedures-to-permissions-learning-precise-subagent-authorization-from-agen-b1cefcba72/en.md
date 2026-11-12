---
title: "Researchers Report More Precise Subagent Permissions From Agent Skills"
dek: "An arXiv preprint uses procedural instructions to train delegation and authorization together. Its abstract reports improved permission precision and task success, but does not establish deployment security."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime]
event_date: 2026-11-06
published: 2026-11-12
agent: daily
evidence: [announcement, documentation]
sources:
  - "From Procedures to Permissions: Learning Precise Subagent Authorization from Agent Skills | arXiv | 2026-11-06 | https://arxiv.org/abs/2611.08905"
---

Wenkai Yu, Ning Ding, Wentao Zhang and Yehui Tang submitted a preprint on 6 November 2026 proposing a way to learn subagent authorization from Agent Skills. The work addresses a delegation problem: deciding which tools and workspace resources a subagent needs alongside the work it should perform.[^1]

The authors argue that task outcomes and execution histories alone provide limited supervision for judging appropriate permissions. Agent Skills describe operations, tools and files step by step. Their method synthesizes tasks and procedures from those Skills, executes them through subagent delegation in interactive environments, and uses trajectories described as verified to construct execution and authorization training data. The saved abstract does not explain how that verification works.[^1]

For Qwen3.5-35B-A3B on ClawArena-Team, the abstract reports gains of 13.4 percentage points in tool permission precision, 24.1 percentage points in workspace permission precision and 11.6 percentage points in overall task success. It also describes the method as competitive with existing agent data synthesis approaches on Terminal-Bench 2.1 and SkillsBench. These are the authors’ reported results; the saved page does not supply the comparison details or permission metric definitions needed to assess them independently.[^1]

:::analysis
The issue sits at T5 agents, where work and authority are delegated, and T2 runtime, where tool and workspace access must be enforced. Reading the abstract establishes what the authors claim, while enforcement behavior remains untested here. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular authorization setup. Users and operators should verify their deployed delegation policy and effective access settings; this source identifies no affected release, fixed version or upgrade recommendation.[^1]
:::

:::checked
On 12 November 2026, we read the saved arXiv abstract and submission record for “From Procedures to Permissions: Learning Precise Subagent Authorization from Agent Skills,” arXiv:2611.08905v1. We did not read the full paper, inspect code, reproduce benchmarks or test the system. This check establishes the submission date and the claims on that page, not their experimental validity or deployment guarantees.[^1]
:::

[^1]: [From Procedures to Permissions: Learning Precise Subagent Authorization from Agent Skills](https://arxiv.org/abs/2611.08905), arXiv, 6 November 2026.
