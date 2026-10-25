---
title: Checklist: evaluating a verifiable inference claim
dek: Ten checks to run when a provider or protocol says its model outputs can be verified. Each comes with a worksheet for recording what the evidence covers and what you still have to trust.
needs: the written claim, the paper or specification behind it, and the verification tools
kind: guide
topics: [verifiable-inference, agents-accountability]
layers: [outputs]
published: 2026-10-20
agent: research
evidence: [paper, announcement, report]
disclosure: verifiable.pro's editor is a co-author of the Hollow-LLM paper, which this guide cites.
sources:
  - zkLLM: Zero Knowledge Proofs for Large Language Models | arXiv (Sun, Li and Zhang; ACM CCS 2024) | 2024-04-24 | https://arxiv.org/abs/2404.16109
  - DeepProve: Verifiable End-to-End Large Language Model Inference | IACR Cryptology ePrint Archive (Gailly et al.) | 2026-05-30 | https://eprint.iacr.org/2026/1112
  - Hollow-LLM Attack: Computationally Trivial Weights in Zero-Knowledge Verification of LLM Inference | arXiv (Gong, Liu and Li; IEEE S&P 2026) | 2026-07-30 | https://arxiv.org/abs/2607.28884
  - TOPLOC: A Locality Sensitive Hashing Scheme for Trustless Verifiable Inference | arXiv (Ong et al.; ICML 2025) | 2025-05-30 | https://arxiv.org/abs/2501.16007v2
  - Verde: Verification via Refereed Delegation for Machine Learning Programs | arXiv (Arun et al.) | 2025-02-26 | https://arxiv.org/abs/2502.19405
  - IMMACULATE: A Practical LLM Auditing Framework via Verifiable Computation | arXiv (Guo et al.) | 2026-02-26 | https://arxiv.org/abs/2602.22700
  - Are You Getting What You Pay For? Auditing Model Substitution in LLM APIs | arXiv (Cai, Shi, Zhao and Song) | 2025-09-29 | https://arxiv.org/abs/2504.04715v2
  - Deterministic Inference Is Here: How EigenAI Makes Every AI Output Verifiable | EigenCloud | 2026-01-23 | https://www.eigenlabs.org/blog/deterministic-ai-inference-eigenai/
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
related: [proofs-enclaves-and-re-execution-compared, hollow-llm-attack-zero-knowledge-inference, how-to-read-a-remote-attestation-report]
---

A provider's statement that its model outputs are verifiable is only as useful as the specific claim behind it, because the mechanisms grouped under verifiable inference check different things. A zero-knowledge proof reveals nothing beyond the statement it establishes. Such a proof can show that an output is consistent with weights the provider has committed to.[^1] A sampled audit checks only some requests and is designed to detect large-scale cheating with high probability.[^6] This checklist turns a general claim into ten questions, each with a worksheet.

## When to use this checklist

Use it before you rely on a provider's or protocol's claim that its outputs are verifiable. For example, you might rely on the claim when you pay for a particular model or let an agent act on the outputs. Gather the written claim with the paper or specification behind it, the verification tools, and your own requirements, including what a single wrong output would cost you.

## 1. Write down exactly what is claimed

Write the claim out in full, naming the model, input, output, decoding settings (which control how each token is chosen) and time of the run. Each mechanism covers only some of these. zkLLM's zero-knowledge proofs show that a returned result is correct for the prompt and for a confidential model the provider has committed to.[^1] Gong, Liu and Li argue that such proofs do not bind the computational effort spent. In their Hollow-LLM attack, a provider keeps the declared architecture and parameter count but uses weights that reduce the work to that of a much smaller model. The proofs still verify.[^3] TOPLOC checks hashes of the model's internal activations. Its authors note that it cannot detect speculative decoding, in which a cheaper model generates the tokens. In their tests, though, it caught every change of model, prompt or numerical precision.[^4]

- [ ] Write the claim as one sentence naming the model, input, output, decoding settings and time
- [ ] Mark which parts the evidence covers and which the provider only asserts
- [ ] Check whether "the model" means a named release or only weights the provider committed to

## 2. Identify the mechanism

Name the mechanism the claim relies on. Each family of mechanisms rests on different evidence and assumptions.

| Mechanism | Example | A passing check shows | Main assumption |
| --- | --- | --- | --- |
| Zero-knowledge proof | zkLLM, DeepProve[^1, 2] | The output matches the public architecture run on committed weights[^3] | The commitment identifies the intended weights |
| Hardware attestation | Serving in a trusted execution environment (TEE)[^7, 9] | Which software genuine hardware loaded | The hardware vendor and the measured software |
| Activation fingerprint | TOPLOC[^4] | Recomputed activations match the provider's hashes within set thresholds | A validator able to rerun the model |
| Refereed delegation | Verde[^5] | The correct result, if at least one provider is honest | Operators in the model's computation give bit-identical results across hardware |
| Optimistic re-execution | EigenAI[^8] | Nobody challenged within the dispute window, or re-execution matched | Someone challenges; verifiers use identical hardware |
| Sampled audit | IMMACULATE[^6] | Audited requests were consistent with the claimed model | Audit requests are indistinguishable from normal ones |

- [ ] Name the mechanism and the document that specifies it

## 3. Find out who can run the verification

Find out what data and hardware the verifier needs, because these decide whether you, or someone you trust, can run it. Zero-knowledge proofs promise public verifiability,[^3] and DeepProve reports verification times of 1 to 3.7 seconds.[^2] TOPLOC's validator reruns the model over the generated tokens to recompute activations,[^4] so it needs the weights and suitable hardware. EigenAI requires verifiers to use the same graphics processing unit (GPU) models as the operators who run inference, because A100 and H100 GPUs produce different results for identical operations.[^8]

- [ ] Find out whether you can verify yourself or must rely on the provider, a committee or an auditor
- [ ] Confirm that the verifier code is published and that you can run it
- [ ] Note the weights, hardware or data the verifier needs

## 4. List what you still have to trust

List each party or component whose failure would let a wrong output pass. Every mechanism leaves at least one, and the table's last column names the main one. Outside testing does not remove that dependence. Cai and colleagues conclude that tests run without the provider's cooperation cannot reliably detect model substitution. Statistical tests on text outputs need many queries and miss subtle substitutions, and tests on log probabilities fail because production inference is nondeterministic.[^7] Cai and colleagues propose TEEs instead. A TEE moves trust to the hardware vendor and the measured software. Our guide to [reading a remote attestation report](/articles/how-to-read-a-remote-attestation-report/) covers those checks.

- [ ] List each party or component whose failure would let a wrong output pass
- [ ] Mark which assumptions the provider states and which you inferred, and decide whether each is acceptable

## 5. Check whether every output is covered

Find out whether the scheme checks each output, a sample or only disputed results. An IMMACULATE auditor sends a small number of random requests that look like normal traffic. The auditor then asks the provider to prove how it served them. The authors reason that cheating pays only if a provider deviates on a non-negligible share of requests. So, they argue, such sampling detects large-scale deviations with overwhelming probability.[^6] Under EigenAI's optimistic design, results stand unless someone challenges them during a dispute window.[^8] Both designs target systematic cheating. Neither guarantees that a particular output you received was checked.

- [ ] State whether every output, a random sample or only challenged outputs are checked
- [ ] For sampling, find the audit rate and whether audit requests are indistinguishable from normal ones
- [ ] Decide whether a single unchecked output could cause harm in your use

## 6. Check how the evidence is bound to your request

Check that the evidence refers to your request, so that it cannot be reused for another. It must also capture every input that determines the output. EigenAI describes its output as a pure function of the model, prompt, seed and decoding settings, that is, as depending only on these four inputs. So all four must be recorded for a re-execution to match.[^8] Session binding matters too. Attestation reports in WhatsApp's TEE-based system originally carried no client-supplied value, so they could have been replayed. Meta's fix ties each report to one Transport Layer Security (TLS) connection.[^9] Keep the evidence with the record of any action an agent takes on the output. You can then trace that action to a verified result.

- [ ] The evidence identifies your input, the output and the decoding settings, directly or by hash
- [ ] It is tied to your request, session or nonce, so it cannot be replayed for another request
- [ ] You can store it with the output and with any action taken on it

## 7. Check how the model is committed

Check the model commitment, a published cryptographic fingerprint of the weights that later proofs refer to. In zkLLM, the provider spends up to 20 minutes committing to a model and publishes a commitment of about 10 MB.[^1] A commitment fixes a set of weights without saying which weights they are. Unless the provider links it to a release you can inspect or evaluate, a proof shows only consistency with some fixed weights. The Hollow-LLM results show that weights fitting a large declared architecture can do a much smaller model's work.[^3]

- [ ] Find the published commitment and the date it was published
- [ ] Check how it links to weights you can identify, such as an open release or an evaluated model
- [ ] Ask how you would learn that the commitment had changed

## 8. Find out what happens when a check fails

Find out what consequence a failed check has. Without a defined consequence, detecting an error changes nothing. In EigenAI, a mismatch found on re-execution leads to slashing, which takes funds from the operator's stake.[^8] In Verde, a dispute narrows to a single operator in the model's computation. The referee re-executes that operator to find which provider was wrong.[^5] With proofs and attestations, your own client decides the consequence, so confirm that it rejects an output that fails.

- [ ] Find the documented consequence of a failed check, such as rejection, refund, penalty or public disclosure
- [ ] Check who is notified and whether failures are published
- [ ] Decide what your system does with an output that fails or skips verification

## 9. Weigh cost and latency

Record what verification costs, because cost decides how much traffic a provider can afford to verify. zkLLM reports proving one inference of a 13-billion-parameter model in under 15 minutes.[^1] DeepProve reports about 174 proven tokens per minute for GPT-2 and 86 for Gemma 3.[^2] IMMACULATE limits its verifiable computation to audited requests and reports under 1% throughput overhead.[^6] EigenAI reports under 2% overhead in its own tests.[^8] Verde runs each task on at least two providers, so total cost at least doubles. Its reproducible operators also carry overhead relative to PyTorch: on A100 GPUs, the authors report 58% for Llama inference at 1 billion parameters and 98% at 8 billion.[^5]

- [ ] Record the proving and verification cost per output, and who pays it
- [ ] Check whether the figures come from the provider or from independent measurement
- [ ] Confirm that the cost fits the coverage claimed under question 5

## 10. Look for independent review

Look for outside review of both the mechanism and its deployment. zkLLM was accepted to the ACM Conference on Computer and Communications Security (CCS) in 2024; DeepProve's ePrint entry lists a minor revision for CCS 2026.[^1, 2] Academic analysis can also expose a gap in a whole class of claims, as the Hollow-LLM paper argues for zero-knowledge inference.[^3] Deployments need their own review. Trail of Bits' pre-launch audit of WhatsApp's TEE-based system found 28 issues, eight of them rated high severity.[^9] Treat figures that only the provider has measured, such as EigenAI's reproducibility results, as claims until others reproduce them.[^8]

- [ ] Find external reviews of the mechanism and of the specific deployment
- [ ] Check whether known attacks on the mechanism are addressed

## A worked example

:::example Worked example (hypothetical): two invented claims
A research team wants to pay only for the model it requests. Provider A says every response comes with a zero-knowledge proof that its 70-billion-parameter model generated it. Provider B says all outputs are verifiable because inference is deterministic, outputs are published and anyone can challenge a result within 24 hours. The team's answers:

| Question | Provider A | Provider B |
| --- | --- | --- |
| What is claimed | Output consistent with committed weights | Output reproducible from model, prompt, seed and settings |
| Coverage | Every response | Only challenged responses |
| Who verifies | Anyone with the verifier | Challengers with identical GPUs |
| Model commitment | Published, with no documented link to a named release | Model named, no commitment published |
| On failure | Client rejects the response | Operator's stake is slashed |
| Cost | Proof latency not stated | Challengers bear re-execution costs |

Neither claim settles the team's question. A's proofs cannot show that the committed weights are the advertised model. The Hollow-LLM work makes this gap concrete.[^3] B would catch a substituted model only if someone challenges, so the team would need its own challenger for a sample of outputs. The team asks A to link its commitment to published, evaluated weights, and asks B how often results are challenged.
:::

:::limits What this checklist does not establish
- Complete answers show what a claim covers. They do not show that the mechanism is implemented correctly; that requires review of the deployed code and configuration.
- Verification checks a computation against a specification, such as committed weights and decoding settings. It does not show that the output is accurate, safe or fit for your task.
- Sampled and optimistic schemes are designed to catch systematic deviation, so a single altered response can go unchecked.
:::
