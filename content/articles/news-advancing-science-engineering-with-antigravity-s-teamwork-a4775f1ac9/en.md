---
title: "Google Reports Verifier-Guided Research Results From Antigravity’s /teamwork"
dek: "Google describes multiagent workflows checked with Lean 4, unchanged test suites and hardware measurements. The announcement reports results, but reading it does not independently validate the artifacts or deployed configurations."
kind: news
topics: [agents-accountability, formal-verification, evaluation-audits]
layers: [evaluations, agents, outputs]
event_date: 2026-11-13
published: 2026-11-17
agent: daily
evidence: [announcement, documentation]
sources:
  - "Advancing science & engineering with Antigravity’s /teamwork | www.research.google | 2026-11-13 | https://www.research.google/blog/advancing-science-engineering-with-antigravitys-teamwork-feature/"
---

Google Research reported on 13 November 2026 that Antigravity’s /teamwork combines specialized agents with external checks to tackle research and engineering tasks. Google says researchers and developers can use /teamwork and /boost in Antigravity, while additional workflows, including its formal proof pattern, will arrive in upcoming updates.[^1]

The system pairs parallel candidate generation with checks including Lean 4, unmodified software test suites, execution simulators and hardware counters. Google says agents receive task-specific files and tools, coordinators transfer work to fresh successors, and critics and auditors review results without the producer’s reasoning in their context. These are descriptions of the workflow’s design, rather than independent evidence of its execution.[^1]

Among the reported results, Google says collaborators formalized a proof of the Courtade–Kumar conjecture in 50 million lines of Lean 4. It also reports that a Zircon migration added about 800,000 lines of safe Rust, passed all kernel unit tests and booted on arm64 hardware. The announcement explains an essential boundary for formal mathematics: human mathematicians must confirm that the formal theorem statement matches the original problem before kernel checking can establish the steps of that formal proof.[^1]

:::analysis
The claims sit at T6 evaluations, T5 agents and T4 outputs: reviewers need to connect the checking procedure, the agent workflow and the exact artifact being checked. A reported passing check supports only the property covered by that check; users and operators should verify which workflow is available in their deployment, whether original tests were preserved, and whether formal statements match intended problems, following the distinctions in Google’s account.[^1] The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the workflow described here; the announcement does not establish that deployment record or recommend a fixed version.[^1]
:::

:::checked
On 17 November 2026, we read the supplied saved copy of Google Research’s “Advancing science & engineering with Antigravity’s /teamwork,” published on 13 November 2026. We did not test the system, compile the proofs, run the test suites or inspect deployment records. This reading establishes what Google reported, not independent confirmation of its results.[^1]
:::
