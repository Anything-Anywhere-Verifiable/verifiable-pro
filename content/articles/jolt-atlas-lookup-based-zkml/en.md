---
title: Jolt Atlas Preprint Adapts Lookup-Based Zero-Knowledge Proving to Model Inference
dek: ICME Labs researchers posted a preprint on 19 February 2026 describing Jolt Atlas, a zero-knowledge prover that works directly on neural-network graphs. The preprint reports proof times under a minute for small language models on a laptop, a cost level that matters if inference proofs are to be produced on ordinary devices.
kind: news
topics: [verifiable-inference]
layers: [outputs]
event_date: 2026-02-19
published: 2026-10-20
agent: daily
evidence: [paper, code]
sources:
  - Jolt Atlas: Verifiable Inference via Lookup Arguments in Zero Knowledge | arXiv (Wyatt Benno, Alberto Centelles, Antoine Douchet and Khalil Gibran) | 2026-02-19 | https://arxiv.org/abs/2602.17452
  - JOLT Atlas (ICME-Lab/jolt-atlas README) | GitHub | 2026-05-06 | https://github.com/ICME-Lab/jolt-atlas
---
On 19 February 2026 four researchers at ICME Labs posted a preprint to arXiv describing Jolt Atlas. It is a zero-knowledge machine learning (zkML) framework for proving that a model's inference was computed as claimed.[^1] A zero-knowledge proof shows that a claim is true without revealing anything else. Jolt Atlas extends Jolt, a zero-knowledge virtual machine (zkVM) for RISC-V programs, to neural networks.[^1]

A zkVM proves a program's execution by emulating the CPU instructions it runs. Jolt Atlas instead applies Jolt's lookup-based approach directly to the tensor operations of models in the Open Neural Network Exchange (ONNX) format. A lookup argument proves that a function's inputs and outputs appear in a precomputed table. This suits non-linear functions, such as activation functions, that are costly to express as arithmetic constraints. The authors say that working directly on tensor operations removes CPU registers from the model of computation and simplifies checks that memory reads and writes are consistent.[^1]

The authors also report that Jolt Atlas can prove inference in memory-constrained environments. In addition, they replace Jolt's polynomial commitment scheme with HyperKZG. They say this trades a transparent setup, one relying on no secret parameters, for compact pairing-based proofs suited to verification on a blockchain.[^1]

On a MacBook Pro with an Apple M3 chip and 16 GB of memory, the preprint reports a proof time of about 14 seconds for nanoGPT, a model of about 250,000 parameters. On the same machine, it reports an end-to-end time of about 38 seconds for the 125-million-parameter GPT-2.[^1] It compares the nanoGPT result with a proof time of 237 seconds for the same model. The authors take that figure from the published benchmark of ezkl, another zkML framework.[^1] The project's code is public on GitHub. Its README, last revised in May 2026, lists shorter times on the same laptop configuration, including an end-to-end time of about 17 seconds for GPT-2.[^2]

:::analysis
If the reported times hold, a laptop can prove inference for models of this size in under a minute. That would bring proofs generated on the user's own device within reach for small models. The benchmarks stop at GPT-2's 125 million parameters, so the preprint does not show how proving cost grows for larger models. Its comparison with ezkl relies on numbers measured by another team. A proof also covers only the computation of the committed model, the model fixed in advance by a cryptographic value. So a verifier still needs separate evidence of which model the commitment refers to.
:::

:::checked
On 20 October 2026 we read the arXiv record and full text of the preprint, and the README and commit history of the ICME-Lab/jolt-atlas repository on GitHub. We did not run the prover or reproduce any benchmark, so the Jolt Atlas timings are the authors' own. The preprint does not state the hardware behind the ezkl figure it cites.
:::
