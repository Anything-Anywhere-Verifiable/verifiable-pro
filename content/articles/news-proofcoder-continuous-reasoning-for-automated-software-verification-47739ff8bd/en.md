---
title: "ProofCoder Authors Report Gains in Automated Proof Synthesis"
dek: "The researchers say their Rocq agent uses continuous reasoning and proof-assistant feedback to construct and revise proofs. Their benchmark results remain claims from the paper, not independently tested findings."
kind: news
topics: [formal-verification, agents-accountability]
layers: [agents, outputs]
event_date: 2026-11-10
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "ProofCoder: Continuous Reasoning for Automated Software Verification | arXiv | 2026-11-10 | https://arxiv.org/abs/2611.14106"
---

Researchers introduced ProofCoder, an agentic system for generating software-verification proofs in the Rocq proof assistant, in a paper submitted on 10 November 2026. The authors say the system uses feedback during proof search to decide when to inspect a proof state, seek information, revise a proof fragment or backtrack.[^1]

The paper describes ProofCoder as a coding-agent approach to proof synthesis. It contrasts this with systems in which a surrounding loop controls the retrieval of relevant premises, proof-state management and backtracking while a language model generates tactics. ProofCoder can work on individual tactics or whole proofs, according to the abstract.[^1]

The authors report evaluating the system on 280 tasks from the AutoRocq Benchmark. They say their best-performing configurations raised proof success from 47% for AutoRocq to 60%, at approximately half the cost. They also report that removing continuous reasoning solved fewer lemmas at substantially higher cost, with more backtracking. These are the authors’ reported results; the saved source is an abstract, not the underlying evaluation details.[^1]

:::analysis
The claims sit at T5, agents, where ProofCoder directs proof search, and T4, outputs, where the resulting proof and its stated property matter to a verifier. A proof checked by a proof assistant concerns the property expressed in its statement; assessing a particular result still requires examining that statement and the checking setup. Identifiability matters too: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to that configuration. Users and operators should check the version, configuration, proof statement and checking setup for their own use; the abstract gives no fixed version recommendation or deployment identification mechanism.[^1]
:::

:::checked
For this preview on 18 November 2026, we read the saved arXiv abstract page for *ProofCoder: Continuous Reasoning for Automated Software Verification*, identifying the displayed revision as v2. We did not read the full paper or test the system, and we did not independently confirm the benchmark results or costs.[^1]
:::
