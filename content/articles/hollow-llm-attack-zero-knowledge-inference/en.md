---
title: Hollow-LLM Paper Says Zero-Knowledge Inference Proofs Do Not Prove Large-Model Execution
dek: University of Southern California researchers describe how a provider could serve a small language model while producing valid zero-knowledge proofs for a larger declared one. Their paper, on the May 2026 program of the IEEE Symposium on Security and Privacy, concludes that a valid proof does not show that the provider did the declared model's work.
kind: news
topics: [verifiable-inference]
layers: [outputs]
event_date: 2026-05-20
published: 2026-10-20
agent: daily
evidence: [paper]
sources:
  - Hollow-LLM Attack: Computationally Trivial Weights in Zero-Knowledge Verification of LLM Inference | arXiv (Chen Gong, Beijie Liu and Mengyuan Li) | 2026-07-30 | https://arxiv.org/abs/2607.28884
  - IEEE Symposium on Security and Privacy 2026: Agenda | IEEE Computer Society Technical Community on Security and Privacy | 2026-05-20 | https://sp2026.ieee-security.org/program.html
disclosure: verifiable.pro's editor is a co-author of the paper this brief reports on.
related: [proofs-enclaves-and-re-execution-compared, evaluating-a-verifiable-inference-claim, jolt-atlas-lookup-based-zkml]
---
Three researchers at the University of Southern California have described an attack on zero-knowledge proofs of large language model (LLM) inference. In the attack, a provider runs a much smaller model while producing valid proofs for the larger model it advertises. The paper was accepted to the 2026 IEEE Symposium on Security and Privacy, whose program lists it in a session on 20 May 2026. The authors posted it to arXiv on 30 July.[^1, 2]

In zero-knowledge (ZK) inference, a provider publishes a model's architecture and a cryptographic commitment to its private weights. It then proves that an output is consistent with them, without revealing the weights. The authors say such proof systems remain sound, meaning that a false statement cannot be proved, but do not establish how much computation went into an output.[^1] In their Hollow-LLM attack, the provider keeps the declared architecture and parameter count but commits to what the authors call ghost weights. The algebraic structure of these weights makes some layers pass inputs through unchanged and confines wide layers to a small active subspace. The provider can therefore serve requests with a much smaller inner model's computation while its proofs still pass verification.[^1]

The authors' experiments used the proving setup of zkGPT, an existing ZK inference system. The executed model was a six-layer transformer, declared as a 12-layer model of double width. Serving time stayed at the small model's level, and output quality, measured by perplexity, did not change. Proving costs nearly matched those of an honest model of the declared size.[^1]

A program-committee meta-review appended to the paper calls the motivation for overclaiming model size weak. It reasons that a large gap may be detectable and a small one may save little.[^1]

The paper's threat model, the setting it assumes, covers proprietary models, whose verifiers see only the public architecture, a weight commitment and the proof. The authors write that, to their knowledge, no company offers a commercial real-time ZK inference verification service. They add that behavioral audits can raise a cheater's costs but offer no guarantee. They also write that trusted execution environments (TEEs), hardware-isolated areas for running code, lack public verifiability.[^1]

:::analysis
In the proprietary setting the paper studies, the proof is a customer's main evidence that the advertised model is running. The attack shows that this evidence does not cover the computation performed. Each countermeasure the authors review leaves a gap. The experiments use small transformers, so the savings and detectability of such an attack at commercial scale remain unmeasured.
:::

:::checked
On 20 October 2026 we read the paper's arXiv record and full text, including the appended meta-review, and the symposium's program. The program page is undated, so we list it under the date of the paper's session. We did not reproduce the experiments or test any ZK inference system.
:::
