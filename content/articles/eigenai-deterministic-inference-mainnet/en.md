---
title: Eigen Labs Says EigenAI Is Live with Deterministic Inference and TEE Re-Execution
dek: In a 23 January 2026 post, Eigen Labs said EigenAI is live on mainnet, with LLM outputs that can be challenged and re-executed byte for byte. The approach relies on identical GPUs, trusted hardware and at least two-thirds of verifier stake behaving honestly.
kind: news
topics: [verifiable-inference, confidential-computing]
layers: [outputs]
event_date: 2026-01-23
published: 2026-10-20
agent: daily
evidence: [announcement, paper]
sources:
  - "Deterministic Inference Is Here: How EigenAI Makes Every AI Output Verifiable | Eigen Labs | 2026-01-23 | https://www.eigenlabs.org/blog/deterministic-ai-inference-eigenai/"
  - "EigenAI: Deterministic Inference, Verifiable Results | arXiv | 2026-01-30 | https://arxiv.org/abs/2602.00182"
---

Eigen Labs said in a 23 January 2026 blog post that EigenAI is live on mainnet, meaning in production rather than on a test network. The company describes EigenAI as a service that runs large language model (LLM) inference so that results can be reproduced bit for bit. Inference is the process of generating a model's outputs. The post links a whitepaper with the full design.[^1]

The company reports 100% reproducibility across 10,000 test runs. It puts the performance overhead under 2%, citing about 1.8% added latency for end-to-end inference. Reproducibility holds only within one GPU architecture. In the company's tests, every run on the same architecture matched and no run across architectures did. Operators and verifiers must therefore use identical GPU models. Eigen Labs attributes the result to controlling every layer of the stack. That includes fixed-seed decoding, which makes the model's random choices repeatable. It also includes custom matrix-multiplication kernels that avoid floating-point atomic operations, whose execution order can change from run to run.[^1]

According to the post, verification is optimistic, meaning results are accepted unless someone challenges them. Operators publish encrypted results to EigenDA, the company's data availability layer, which stores published data so that others can retrieve it. Results can be challenged during a dispute window. A challenge sends the request to a committee of verifiers. The committee re-executes it inside trusted execution environments (TEEs), hardware-isolated environments designed to protect the code and data inside them. Because the computation is deterministic, the committee only needs to check whether the bytes match. A mismatch triggers slashing, a penalty taken from the collateral the operator has staked. The post says a single honest verifier can detect fraud.[^1]

Eigen Labs authors set out the assumptions behind this design in a paper posted to arXiv on 30 January 2026. The committee decides disputes by vote, which assumes that verifiers holding at least two-thirds of the network's stake behave honestly. Verifiers receive the key that decrypts requests only after their TEEs produce an attestation, a signed record of the code they loaded. The key is secret-shared across several key-management shards, so no single shard holds the whole key.[^2]

:::analysis
Determinism reduces checking an inference to comparing bytes, so one honest verifier can spot a mismatch. Settling a dispute without exposing requests requires more: identical GPU hardware for re-execution, an honest two-thirds of verifier stake for the verdict, and trusted hardware for confidentiality. An output that nobody challenges has not been independently re-executed. It is backed by the threat of slashing instead.
:::

:::checked
On 20 October 2026 we opened Eigen Labs' 23 January 2026 post and arXiv paper 2602.00182. The whitepaper linked from the post returned an access error. We therefore relied on the arXiv paper for the design's assumptions and could not confirm that the two documents match. We did not confirm EigenAI's current status on mainnet or reproduce the determinism and overhead measurements. We test no systems ourselves.
:::
