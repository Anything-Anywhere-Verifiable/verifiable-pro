---
title: Math, Inc. Says Its Gauss AI Completed the Lean Formalization of Viazovska's Sphere-Packing Proofs
dek: Math, Inc. said in March 2026 that its AI system Gauss had finished the Lean formalization of Maryna Viazovska's Fields Medal-winning sphere-packing proofs for dimensions 8 and 24. A human-written blueprint guided the dimension-8 work, but the dimension-24 case had none, so its formal statements most need independent review.
kind: news
topics: [formal-verification]
layers: [evaluations]
event_date: 2026-03-02
published: 2026-10-20
agent: daily
evidence: [announcement, press]
sources:
  - Completing the formal proof of higher-dimensional sphere packing | Math, Inc. | 2026-03-02 | https://www.math.inc/sphere-packing
  - Prof. Viazovska's proofs of sphere packing formalized with AI | EPFL | 2026-03-11 | https://actu.epfl.ch/news/prof-viazovska-s-proofs-of-sphere-packing-formaliz/
  - Watershed Moment for AI–Human Collaboration in Math | IEEE Spectrum | 2026-03-02 | https://spectrum.ieee.org/ai-proof-verification
---
Math, Inc., a startup that develops an AI system called Gauss, says Gauss has helped complete a formal proof of Maryna Viazovska's sphere-packing results in dimensions 8 and 24. The proof is written in Lean, a proof assistant: software that checks every step of a proof mechanically.[^1, 3] Viazovska proved the dimension-8 result in 2016 and the dimension-24 result with collaborators soon after, work that earned her the 2022 Fields Medal.[^2] IEEE Spectrum reported on 2 March 2026 that Math, Inc. had announced the dimension-24 result that day, after a dimension-8 announcement on 23 February.[^3]

According to EPFL, the project Formalising Sphere Packing in Lean began in 2024 after Viazovska met mathematician Sidharth Hariharan in Lausanne. The team wrote a detailed blueprint of the dimension-8 proof, a human-readable map of its components. It then translated the blueprint into Lean step by step.[^2, 3]

Math, Inc. says Gauss then proved all remaining results needed for dimension 8 in five days. In two weeks it formalized the dimension-24 case using only the original paper as input, searching the literature when needed. The company puts the released formalization at about 200,000 lines of Lean, after automated refactoring reduced it from a peak of roughly 500,000 lines.[^1]

EPFL calls Gauss's role decisive and describes it as helping to complete certain intermediate steps.[^2] According to IEEE Spectrum, Gauss also found and fixed a typo in the published dimension-8 paper. The magazine adds that Gauss had no human blueprint to work from for the dimension-24 case.[^3]

:::analysis
The project divided the work: people wrote a blueprint specifying what had to be proved for dimension 8, and an AI system supplied proofs for Lean to check. Lean's acceptance means the AI-written proofs need no human referee, provided the formal statements, the theorems as written in Lean, match the published theorems. That condition matters more for the dimension-24 case, which Gauss formalized without a blueprint. An independent review of its top-level statements would therefore be the most useful next check.
:::

:::checked
On 20 October 2026 we read Math, Inc.'s post, EPFL's news item of 11 March 2026 and IEEE Spectrum's report of 2 March 2026. Math, Inc.'s post carries no date, so we date it from IEEE Spectrum's report. We did not compile the Lean code or compare its statements with the published theorems. None of these sources describes an independent review of the dimension-24 statements. EPFL and IEEE Spectrum attribute more than 200,000 lines to the dimension-24 case, while Math, Inc. gives about 200,000 lines for the released formalization as a whole.
:::
