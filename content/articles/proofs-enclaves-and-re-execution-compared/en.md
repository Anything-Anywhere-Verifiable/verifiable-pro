---
title: Three Ways to Check an AI Answer: Proofs, Enclaves and Re-execution Compared
dek: Zero-knowledge proofs, attested enclaves and re-execution each give evidence about which model produced an answer. None is both cheap and low in trust assumptions, so the choice should depend on what each one establishes and what it leaves to trust.
kind: analysis
topics: [verifiable-inference, confidential-computing]
layers: [outputs]
published: 2026-10-20
agent: research
evidence: [paper, documentation, standard, report, announcement]
sources:
  - zkLLM: Zero Knowledge Proofs for Large Language Models | arXiv (Sun, Li and Zhang; ACM CCS 2024) | 2024-04-24 | https://arxiv.org/abs/2404.16109
  - DeepProve: Verifiable End-to-End Large Language Model Inference | IACR Cryptology ePrint Archive (Gailly et al.) | 2026-05-30 | https://eprint.iacr.org/2026/1112
  - ZKML Inference Proving (DeepProve zkml README) | Lagrange Labs on GitHub | 2026-05-01 | https://github.com/Lagrange-Labs/deep-prove/blob/master/zkml/README.md
  - Benchmarking Confidential Computing Performance on NVIDIA Blackwell GPUs | arXiv (Asad and Grunseid, Confidential.ai) | 2026-08-27 | https://arxiv.org/abs/2608.26575
  - Remote ATtestation procedureS (RATS) Architecture, RFC 9334 | IETF | 2023-01 | https://www.rfc-editor.org/rfc/rfc9334
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
  - DDRop: Active Memory Interposer Attacks on Confidential VMs by Dropping DDR5 Writes | KU Leuven, ETH Zurich, Durham University and Google | 2026-09-14 | https://ddropattack.eu/
  - Defeating Nondeterminism in LLM Inference | Thinking Machines Lab | 2025-09-10 | https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/
  - TOPLOC: A Locality Sensitive Hashing Scheme for Trustless Verifiable Inference | arXiv (Ong et al.; ICML 2025) | 2025-01-27 | https://arxiv.org/abs/2501.16007
  - Verde: Verification via Refereed Delegation for Machine Learning Programs | arXiv (Arun et al.) | 2025-02-26 | https://arxiv.org/abs/2502.19405
  - IMMACULATE: A Practical LLM Auditing Framework via Verifiable Computation | arXiv (Guo et al.) | 2026-02-26 | https://arxiv.org/abs/2602.22700
  - Deterministic Inference Is Here: How EigenAI Makes Every AI Output Verifiable | EigenCloud (Eigen Labs) | 2026-01-23 | https://www.eigenlabs.org/blog/deterministic-ai-inference-eigenai/
related: [hollow-llm-attack-zero-knowledge-inference, jolt-atlas-lookup-based-zkml, eigenai-deterministic-inference-mainnet]
---

None of the three main approaches checks a hosted model's answer both cheaply and with few parties to trust. Zero-knowledge proofs give cryptographic evidence that the answer was computed by a model fixed in advance, so they avoid trusting the provider's hardware. But the systems examined here are slow and have been demonstrated only on smaller models. Attested enclaves are hardware-isolated environments that report which software they loaded. When tuned, they can run large models at a few percent overhead. In exchange, anyone relying on them must trust the chip vendors, the measured software and whoever checks the measurements. Re-execution reruns the model and compares the answers. It costs far less than proving, but its assurance rests on tolerances, sampling or disputes, and on an honest checker. Each family answers a different question at a different cost.

## The claim being checked is which model produced an output

Verifiable-inference work checks a narrow claim: this output came from running a specific model on this input. The model is identified by its weights, and the run uses stated settings such as numeric precision and decoding method [^2, 9, 12]. Providers have a motive to deviate: a smaller or lower-precision model costs less to serve, and users see only text [^9, 11]. Confidentiality, whether the provider can read the prompt, is a separate property.

## Zero-knowledge proofs remove hardware trust at a high proving cost

Zero-knowledge machine learning (zkML) systems prove that an output was computed from committed weights. The weights are fixed in advance by a cryptographic fingerprint, the commitment, which hides them. A verifier checks the proof without seeing the weights [^1]. In 2024, zkLLM proved inference over a 2,048-token input for Llama 2 13B in 803 seconds on one NVIDIA A100 GPU. Verifying the 188 kB proof took about 4 seconds [^1]. The 2026 DeepProve paper reports proving every generated token of a response: about 174 tokens per minute for GPT-2 and 86 for Gemma 3, and up to 1,855 with distributed proving [^2].

Such a proof shows that the output is consistent with a commitment. That matters only if the commitment is tied to a known model. In zkLLM's setting, the developer publishes the commitment once and proves each response against it [^1].

The proven computation is also an integer version of the model. zkLLM maps it into a finite field (a number system with finitely many values), and DeepProve quantizes weights and activations (the intermediate values the model computes) to 12 bits by default [^1, 3]. DeepProve's proofs also require each token to be the model's top-scoring prediction, as in greedy decoding [^3]. The zero-knowledge property hides the weights from the verifier, but the provider still sees the prompt [^1].

## Attested enclaves can add little overhead but move trust to hardware and measurements

A trusted execution environment (TEE) is a hardware-isolated environment designed to keep its memory from the host operating system and the hypervisor, the software that manages virtual machines. A confidential virtual machine, one that runs as a TEE, can use Intel Trust Domain Extensions (TDX) and be paired with NVIDIA GPUs in confidential computing mode. Remote attestation then supplies a measurement of the software loaded at launch: a cryptographic hash that the hardware signs [^4]. A preprint by Confidential.ai authors tested generation-heavy serving of a 229-billion-parameter model on NVIDIA B200 GPUs. With a tuned software stack, they measured about 1% to 3% throughput overhead; stock inference stacks lost 30% to 40% [^4].

The enclave is designed to keep prompts and weights from the operator, while attestation is evidence about which software was loaded [^4]. Neither shows that the software computes the advertised model correctly, so trusting the output means trusting the measured inference stack.

Under the attestation architecture of the Internet Engineering Task Force (IETF), a verifier compares the evidence with reference values, such as known-good measurements [^5]. That comparison covers only what was measured and tied to the current session. Trail of Bits' pre-launch audit of WhatsApp's TEE-based AI processing found gaps of both kinds. Configuration loaded after the measurement could let an insider run malicious code while attestation still passed. And because reports lacked a fresh value from the client, anyone who had compromised an enclave once could replay them, presenting old reports as new. Meta fixed both [^6].

The auditors' rule is that every loaded input must be measured or treated as hostile [^6]. By that rule, weights loaded after launch are covered only if measured code checks them, for example against a published hash.

Physical access can also defeat attestation. In September 2026, researchers disclosed DDRop, a device that costs under $200 to build and silently drops a server's memory writes. With one brief physical visit and control of the host software, they made a rogue Intel TDX virtual machine pass attestation using a legitimate workload's measurement. Intel and AMD consider physical attacks on server memory out of scope for current products [^7].

## Re-execution must distinguish GPU noise from cheating and depends on an honest checker

Re-execution checks an answer by rerunning the model on the same input and comparing, but GPU inference is often not reproducible. Thinking Machines Lab ran one prompt 1,000 times on a 235-billion-parameter Qwen3 model at temperature zero, a setting that removes randomness from token selection. The runs produced 80 distinct completions. The lab traced the differences to the order of operations in GPU kernels, the programs that perform the model's arithmetic. That order shifts with batch size, the number of requests processed together, and therefore with server load [^8].

TOPLOC tolerates the noise. The provider commits to locality-sensitive hashes of intermediate activations: fingerprints designed to absorb small numeric differences. A validator with the weights recomputes the hashes in one pass over all tokens, faster than generation. In the authors' tests, it caught every changed model, prompt and precision without false alarms. But it cannot catch a provider that generates tokens with a cheaper model and hashes them with the claimed one. Catching that requires checking the sampling step that picks each token [^9].

Verde removes the noise instead. Its RepOps library fixes the order of floating-point operations. When two providers disagree, a referee narrows the dispute to one operator, a single step of the computation, and recomputes only that. The client therefore gets the correct result if at least one provider is honest. On A100 GPUs, the authors report that RepOps adds 58% overhead relative to PyTorch for inference with a 1-billion-parameter Llama model and 98% with an 8-billion-parameter one. So far it covers only single-GPU runs. Running each job twice at least doubles the cost. The authors still put this cost under one order of magnitude, compared with at least four for cryptographic proofs [^10].

IMMACULATE checks a sample. An auditor sends requests that look like ordinary traffic. The auditor then asks the provider to prove how far its next-token scores for those requests stray from the claimed full-precision model's. The authors report under 1% throughput overhead. Their guarantee assumes an honest auditor whose requests the provider cannot single out. It also assumes a provider that cheats on at least 10% of queries [^11]. So the guarantee does not cover rare cheating. Every scheme here also fails if no one runs the check.

## How the three families compare

| Property | Zero-knowledge proofs | Attested enclaves | Re-execution and sampling |
| --- | --- | --- | --- |
| A passing check shows | The output follows from the committed weights under the proven computation | Genuine hardware launched software matching the reported measurements | A rerun or audited sample matched, exactly or within a tolerance |
| What must be trusted | Proof-system assumptions; a proven computation faithful to the model's architecture; a commitment tied to a known model | Chip vendors; the measured software; reference values and the verifier; physical security | An honest checker who runs the check; the reproducibility method or threshold |
| Reported cost | 803 seconds per proof for a 13B model [^1]; 86 to 174 tokens per minute, up to 1,855 distributed [^2] | 1% to 3% throughput loss when tuned, 30% to 40% stock [^4] | One pass over all tokens per check [^9]; 58% to 98% inference overhead relative to PyTorch on A100 GPUs, plus a duplicate run [^10]; under 1% overhead with sampling [^11] |
| Maturity | Research systems; DeepProve's code is marked not production ready [^3] | Commercial hardware [^4]; WhatsApp AI features, audited before launch [^6] | Research protocols; one deployment reported live [^12] |
| Typical failure modes | Commitment not tied to the served model; proven computation differs from the served one | Unmeasured inputs; replayable reports; physical attacks that forge attestation | Thresholds that miss subtle changes [^9]; unchecked token sampling; rare cheating; absent checkers |

## Combinations cover some gaps but keep each method's assumptions

EigenAI, which Eigen Labs says launched in January 2026, joins two of the families: re-execution and attested enclaves. Operators run bit-exact deterministic inference, with the random seed fixed as an input. Results are accepted unless someone challenges them within a dispute window. A challenge triggers re-execution by a committee of verifiers inside attested enclaves. A mismatch triggers a penalty drawn from the operator's staked funds, the collateral it has locked up. Eigen Labs reports 1.8% added latency. It requires the same GPU model for operators and verifiers, because its tests across architectures never matched. Determinism reduces the check to a byte comparison. The company also says requests are decrypted only inside the enclaves during verification [^12]. IMMACULATE's prototype likewise ran its audit computations in an Intel TDX enclave. That was hundreds of times slower than GPU inference, so the prototype relied on sampling to keep the cost negligible [^11].

Each combination keeps its parts' assumptions. EigenAI still needs a challenger to act within the dispute window. The privacy of re-executed requests is only as strong as the enclave hardware, including against physical attacks such as DDRop [^7, 12].

:::example
A law firm weighing a hosted open-weights model, whose weights are public, would want to limit who can read its contracts. So before sending any, it would check an enclave's attestation, including a hash of the weights. To test whether the provider serves the full-precision model it bills for, it could also have a checker it trusts re-execute a sample of requests.
:::

## Open questions

- Whether proofs can cover the model sizes, floating-point arithmetic and sampled decoding that services use, at an acceptable cost.
- Who publishes and checks the reference values that give attestations meaning, including hashes of weights and configuration loaded after launch.
- Which settings, such as weight hashes, precision, decoding method and random seeds, providers should publish to give every method a fixed target.
- How to weigh physical attacks that chip vendors place outside the TEE threat model (the attacks a TEE is designed to resist).
