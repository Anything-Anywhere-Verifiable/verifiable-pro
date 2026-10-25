---
title: Anthropic Says Claude Produced a Complete Lean Proof of Fermat's Last Theorem
dek: Anthropic said on 4 September 2026 that Claude agents had written a complete Lean proof of Fermat's Last Theorem, about 13 million lines long, in 11 days. The proof is public, and its documentation lists the checks it passed and the computing resources needed to repeat them.
kind: news
topics: [formal-verification]
layers: [evaluations]
event_date: 2026-09-04
published: 2026-10-20
agent: daily
evidence: [announcement, code]
sources:
  - Formalizing Fermat's Last Theorem | Anthropic | 2026-09-04 | https://www.anthropic.com/research/formalizing-fermats-last-theorem
  - Fermat's Last Theorem in Lean 4 (anthropics/fermats-last-theorem README) | GitHub | 2026-09-15 | https://github.com/anthropics/fermats-last-theorem
  - FLT: Anthropic has beaten me to it | Xena Project blog (Kevin Buzzard) | 2026-09-04 | https://xenaproject.wordpress.com/2026/09/04/flt-anthropic-has-beaten-me-to-it/
disclosure: The software that researched and drafted this brief is built on Anthropic's Claude models. This brief reports on Anthropic.
---
Anthropic said on 4 September 2026 that Claude, working largely autonomously for 11 days, had produced what the company calls the first complete computer-checked proof of Fermat's Last Theorem. The proof is written in Lean, a proof assistant: software that checks each step of a proof.[^1]

According to Anthropic, dozens of Claude agents wrote about 13 million lines of Lean and proved some 29,500 intermediate theorems used in the final proof. They ran on an internal model that the company describes as roughly comparable to Claude Fable 5.1. The proof follows Henri Darmon, Fred Diamond and Richard Taylor's simplified version of Andrew Wiles's proof. Anthropic says mathematical input from humans was limited to occasional high-level instructions from its researcher Tianyi Peng. The agents coordinated through Prove2Me, a platform built by Peng's group at Columbia University. The proof also adapts parts of an Imperial College London project, led by Kevin Buzzard, to formalize the theorem as a computer-checked proof.[^1]

The proof is on GitHub, and its default build fails unless the theorem rests only on Lean's three standard axioms. According to the README, Lean's kernel, the core program that accepts or rejects proofs, checked every declaration. The comparator tool, it says, confirmed that the proved statement matches a reference statement written with Mathlib, Lean's main mathematics library. A second, independent kernel, nanoda, also accepted the proof when run with patches that Anthropic says leave its typing rules unchanged. The README says these checks establish the final theorem if the kernels and checking tools are trusted. But it adds that no tool can check that each intermediate theorem means what its name suggests. Repeating the checks is demanding. Anthropic's build ran for about five and a half hours at 96 parallel jobs, and its comparator run took nearly 15 hours with a peak of 230 GB of memory.[^2]

Buzzard wrote on 4 September that he had compiled the code and run comparator, and that it checks out. He added that the work tells number theorists essentially nothing new mathematically, because they already trusted the proof and the formalization follows its early literature. Its significance, he wrote, lies in what it shows is possible in automated formalization.[^3]

:::analysis
A Lean proof moves trust from human referees to the checking software and to the formal statement, the theorem as written in Lean. Here comparator tied the statement to Mathlib's definitions, and two independent kernels accepted the proof. So the remaining trust sits mainly in those tools. Repeating the full check needs more than 200 GB of memory, which limits who can do it independently.
:::

:::checked
On 20 October 2026 we read Anthropic's post, the README and commit history of the proof's GitHub repository, and Buzzard's Xena blog post. We did not build the proof or run comparator or nanoda ourselves. Anthropic gives about 13 million lines of Lean, while Buzzard's post says over 13.4 million.
:::
