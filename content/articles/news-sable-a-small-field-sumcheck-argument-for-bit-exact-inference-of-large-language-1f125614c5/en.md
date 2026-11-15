---
title: "Sable Paper Claims Bit-Exact Proofs of Integer LLM Inference"
dek: "The preprint reports a single-GPU prover for committed transformer inference. Its exactness claim applies to a specified integer function, whose outputs can differ from BF16 inference."
kind: news
topics: [verifiable-inference]
layers: [outputs, models, runtime]
event_date: 2026-11-10
published: 2026-11-15
agent: daily
evidence: [announcement, documentation]
sources:
  - "Sable: A Small-Field Sumcheck Argument for Bit-Exact Inference of Large Language Models | arXiv | 2026-11-10 | https://arxiv.org/abs/2611.14083"
---

Tomer Solberg submitted Sable to arXiv on 10 November 2026, describing an argument system and single-GPU prover intended to establish that a committed, integer-quantized transformer produced a specified token sequence from a given prompt, bit for bit. The preprint targets open-weight models and explicitly says its proofs are not zero-knowledge.[^1]

The abstract defines an integer function, F_O, with no floating-point step: rounding, normalization, softmax and sampling decisions are determined by its inputs. It claims constraints that never wrap modulo the 31-bit KoalaBear prime. The construction batches zerochecks and LogUp-GKR lookups into one sumcheck per domain, commits to witness tensors and weights, and streams model layers through one GPU.[^1]

The author reports proving all 64 layers of Qwen2.5-32B on one NVIDIA RTX PRO 6000 Blackwell GPU in 92.5 seconds for 4,096 tokens and 398 seconds for 16,384 tokens. Reported proof generation costs 41–50 times serving time; verification with a compiled core takes 19–56 seconds on one CPU core. The abstract states a round-by-round soundness error of 2^-103 for the interactive proof in the random-oracle model.[^1]

Bit-exactness concerns F_O. The abstract reports that its greedy token matches the BF16 model at 86.3% of WikiText-2 positions. Those results distinguish the claimed execution check from equivalence to BF16 behavior.[^1]

:::analysis
The claim sits at T4 outputs, T3 models and T2 runtime: it concerns the relationship between a token sequence, committed weights and specified integer execution rules. A verifier must check which model and configuration the statement covers; users and operators should verify that those match the system serving their request. The property at stake is identifiability: if the exact serving version and configuration are recorded and checkable, users can determine whether they were exposed to that implementation; the saved abstract does not establish that deployment linkage.[^1]
:::

:::checked
On 15 November 2026, we read the supplied saved arXiv abstract page for Sable, arXiv:2611.14083v1, submitted on 10 November. We did not read the full paper or code, test the system, reproduce benchmarks, or independently validate its security argument. The page establishes what the author reports, rather than confirming those results.[^1]
:::

[^1]: [Sable: A Small-Field Sumcheck Argument for Bit-Exact Inference of Large Language Models](https://arxiv.org/abs/2611.14083), Tomer Solberg, arXiv, 10 November 2026.
