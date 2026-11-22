---
title: "Pre-QED Authors Propose Environment Specifications for Agentic Verification"
dek: "The preprint proposes executable harnesses that model legal API usage, arguing that a proof’s reach depends on the specification it checks. The saved abstract does not establish that the proposed coverage has been achieved."
kind: news
topics: [formal-verification, agents-accountability]
layers: [evaluations, agents, runtime]
event_date: 2026-11-11
published: 2026-11-16
agent: daily
evidence: [announcement, documentation]
sources:
  - "Pre-QED: Environment Specifications for Agentic Verification | arXiv | 2026-11-11 | https://arxiv.org/abs/2611.15207"
---

Tristan Lim and colleagues submitted *Pre-QED: Environment Specifications for Agentic Verification* to arXiv on 11 November 2026. The authors argue that the bottleneck in verification using large language model agents has shifted from producing proofs to specifying what those proofs should cover. They propose executable verification harnesses intended to model all legal uses of an application programming interface (API).[^1]

The abstract criticizes approaches that reuse fuzz-testing harnesses as formal specifications. It names OSS-Verify from Anthropic and Theorem, saying its agents prove that individual harnesses never crash. In the authors’ account, a fuzz harness follows one sequence of API calls in one calling context, so proving that harness covers a usage scenario rather than the whole library. This is the preprint’s characterization; our reading does not independently establish OSS-Verify’s coverage.[^1]

Pre-QED’s proposed workflow extracts an API’s usage contract from code and documentation, then uses Linear-time Temporal Logic (LTL) to exclude illegal call orders. The authors say they release their harnesses as open-source challenges and identify difficulties in proving them. Coverage of every well-behaved client is the proposed objective, not a demonstrated result established by the saved abstract.[^1]

:::analysis
The issue sits at T6 evaluations, T5 agents and T2 runtime: a verifier’s conclusion depends on the specification, the agent’s interpretation of the API contract and the library usage actually covered. Users and operators should check whether their library version, configuration and permitted call sequences match the verification target; the source recommends no fixed release. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a documented coverage gap, provided the gap is mapped to those records. This is an operational implication of the specification problem, not a capability demonstrated by Pre-QED.[^1]
:::

:::checked
On 16 November 2026 we read the saved arXiv abstract page for arXiv:2611.15207, including its v1 submission history. We did not read the full paper, inspect the released harnesses or test the system. The page establishes what the authors propose and claim to release; it does not let us confirm specification completeness or successful proofs.[^1]
:::
