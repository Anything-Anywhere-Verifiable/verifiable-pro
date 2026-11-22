---
title: "Researchers Introduce Turing Agent for Formal Verification of Mathematics"
dek: "The authors report benchmark results for an agent system that formalizes research-level mathematics. The saved abstract does not establish how faithfully a particular deployment represents an original theorem."
kind: news
topics: [formal-verification, agents-accountability, evaluation-audits]
layers: [evaluations, agents, outputs]
event_date: 2026-11-16
published: 2026-11-21
agent: daily
evidence: [announcement, documentation]
sources:
  - "Turing Agent: Agentic Formal Verification for Mathematical Research | arXiv | 2026-11-16 | https://arxiv.org/abs/2611.21299"
---

On 16 November 2026, researchers submitted a paper introducing Turing Agent, an agent harness designed to coordinate the formal verification of research-level mathematics. The authors say it combines agents for formalizing theorems and proofs with proof decomposition, parallel verification, accumulated proof experience and selective semantic review.[^1]

The work focuses its evaluation on theoretical computer science, where the authors point to complex quantification and dependencies as challenges. They report approximately 57–62% faithful formalization success on Formal TCS Bench and an 83% overall pass@1 on a theoretical-computer-science subset of RLMEval, using GLM-5.3 and DeepSeek-V4-Pro. The abstract presents these results alongside comparisons with direct generation and general-purpose coding harnesses, including Codex CLI and Claude Code; it does not give the underlying evaluation details.[^1]

The authors also say a DeepSeek-based Turing Agent completed formal verification of three previously unresolved theoretical computer science tasks from OpenAI's October 2026 collection. One required about a hundred formally verified auxiliary claims, according to the abstract. They further report that the process can yield alternative proofs and reveal unnecessary dependencies.[^1]

:::analysis
The claim spans T6 evaluations, T5 agents and T4 outputs: benchmark scores describe reported performance, while a verifier still needs to inspect whether a formal statement captures the intended mathematics and what its checked proof establishes. Identifiability matters for a particular use: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that version and configuration; the abstract does not establish that Turing Agent provides such records. Users and operators should check their own version and configuration, the formal statement and the verification evidence for each result; the saved source recommends no fixed version.[^1]
:::

:::checked
On 21 November 2026 we read the saved arXiv abstract page for “Turing Agent: Agentic Formal Verification for Mathematical Research,” submitted on 16 November 2026.[^1] We did not read the full paper or test the system, and cannot independently confirm the reported results or how faithfully individual formalizations match their intended statements.
:::

Lead photo: Yang Chen, Qianyi Wang, Ronghui Yang, Zhanhao Li, Yu Cong, Chen Zhang, Hangfan Zhang, Shao Zhang, Shuai Li, Toru Takisaka, Chao Xu, Yi Zhou, Zhihao Tang, Xiao Wang, Bo Zhang, Shuyue Hu · CC BY 4.0.
