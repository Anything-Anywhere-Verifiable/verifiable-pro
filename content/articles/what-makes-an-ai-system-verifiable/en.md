---
title: What makes an AI system verifiable?
dek: Verifying an AI system takes a precise claim, evidence that someone other than the developer can check, and a party able to check it. This explainer shows the layers where claims arise, then describes six kinds of evidence and the trust each one leaves in place.
kind: explainer
topics: [evaluation-audits, confidential-computing, verifiable-inference]
layers: []
published: 2026-10-20
agent: research
featured: true
evidence: [paper, standard, announcement, code]
sources:
  - Toward Trustworthy AI Development: Mechanisms for Supporting Verifiable Claims | Brundage et al., arXiv | 2020-04-15 | https://arxiv.org/abs/2004.07213
  - Private Cloud Compute: A new frontier for AI privacy in the cloud | Apple Security Research | 2024-06-10 | https://security.apple.com/blog/private-cloud-compute/
  - Remote ATtestation procedureS (RATS) Architecture (RFC 9334) | IETF | 2023-01 | https://www.rfc-editor.org/rfc/rfc9334
  - zkLLM: Zero Knowledge Proofs for Large Language Models | Sun, Li and Zhang, ACM CCS 2024 (arXiv) | 2024-04-24 | https://arxiv.org/abs/2404.16109
  - TOPLOC: A Locality Sensitive Hashing Scheme for Trustless Verifiable Inference | Ong et al., ICML 2025 (arXiv) | 2025-01-27 | https://arxiv.org/abs/2501.16007
  - model-transparency v1.1.1, model signing library (README) | Sigstore, GitHub | 2025-10-10 | https://github.com/sigstore/model-transparency/tree/v1.1.1
  - Towards Guaranteed Safe AI: A Framework for Ensuring Robust and Reliable AI Systems | Dalrymple et al., arXiv | 2024-05-10 | https://arxiv.org/abs/2405.06624
  - Black-Box Access is Insufficient for Rigorous AI Audits | Casper et al., arXiv | 2024-01-25 | https://arxiv.org/abs/2401.14446
  - Frontier AI Auditing: Toward Rigorous Third-Party Assessment of Safety and Security Practices at Leading AI Companies | Brundage et al., arXiv | 2026-01-16 | https://arxiv.org/abs/2601.11699
  - Attestable Audits: Verifiable AI Safety Benchmarks Using Trusted Execution Environments | Schnabl et al., arXiv | 2025-06-30 | https://arxiv.org/abs/2506.23706
  - Proof-of-Guardrail in AI Agents and What (Not) to Trust from It | Jin et al., arXiv | 2026-03-06 | https://arxiv.org/abs/2603.05786
  - What does it take to catch a Chinchilla? Verifying Rules on Large-Scale Neural Network Training via Compute Monitoring | Shavit, arXiv | 2023-03-20 | https://arxiv.org/abs/2303.11341
related: [remote-attestation-for-ai-workloads-explained, proofs-enclaves-and-re-execution-compared, check-a-content-credential]
---

An AI system is verifiable to the extent that someone other than its developer can check a specific claim about it against evidence. The **claim** is a precise statement about a particular system, such as which model answered a request or which software handled it. The **evidence** is something other than the developer's word, such as a signature, a hardware-signed report or a mathematical proof. The **verifier** is whoever examines the evidence and decides whether the claim holds. Every check rests on **trust assumptions**: the components or parties that the check does not examine, such as a chip maker's signing keys.

This definition builds on a 2020 report by Brundage and colleagues. The report defines verifiable claims as falsifiable statements for which evidence and arguments can bear on how likely they are to be true.[^1] Verifiability is therefore a matter of degree. A claim can also be checkable for one party and opaque to another.

## Why a developer's statement cannot settle a claim

When the party making a claim is the only source of information about it, its statement cannot settle whether the claim holds. This matters because cloud AI services process personal data, and users of AI agents rely on developers' accounts of how safety measures are enforced.[^2, 11] Apple makes the same point in its 2024 description of Private Cloud Compute (PCC), the cloud system behind its more demanding AI features. When a cloud AI service says it does not log certain user data, Apple notes, researchers generally have no way to verify the promise.[^2]

PCC's design also narrows that gap. Apple says PCC deletes a user's data after fulfilling a request and that "no user data is retained in any form" once the response is returned.[^2] Users cannot watch that deletion, so the design adds narrower claims that a device can check. In Apple's design, a user's device sends data only to PCC nodes that can cryptographically attest to running publicly listed software. Apple also committed to publishing the measurements (cryptographic hashes) of that software in an append-only transparency log, together with production software images for researchers.[^2] The device can confirm which software it is talking to. But whether that software retains no data is left to researchers who analyze the images.

## The seven layers where claims arise

This site sorts claims into a [verification stack](/topics/). Lower layers support higher ones: knowing which model answered depends on knowing which software and hardware ran it.

| Layer | Typical claim | Example of evidence |
| --- | --- | --- |
| Hardware and compute | The computation ran on genuine hardware in a protected mode. | A hardware-signed attestation report[^3] |
| Software and runtime | This exact code and configuration handled the request. | Measurements compared with published values[^2, 3] |
| Models and data | These are the released weights, unchanged since they were signed. | A signed manifest of the model's file hashes[^6] |
| Outputs and content | This output came from this model and this input. | A proof of inference or a re-execution check[^4, 5] |
| Agents and actions | The stated guardrail ran before this agent responded. | A hardware attestation that the guardrail code ran[^11] |
| Evaluations and audits | This score came from the stated model and test set. | An evaluation run in a trusted execution environment, or an audit with deeper access[^8, 10] |
| Policy | A developer or government kept a commitment about training compute. | Proposed monitoring of the chips used for large training runs[^12] |

## Six kinds of evidence and what each leaves to trust

Each kind answers a narrower question than the claim a reader cares about. Each also moves trust somewhere else.

**Cryptographic proofs.** A zero-knowledge proof lets a provider show that an output was computed from a given input and a committed model without revealing the model's weights. To commit to a model, the provider publishes a cryptographic value derived from its weights, which binds the provider to those weights. In zkLLM, the provider commits to the weights of a model whose architecture is public. The authors report proving a 13-billion-parameter model's inference in under 15 minutes, with proofs under 200 kB.[^4] The verifier still trusts the proof system's soundness, the property that a false statement cannot be proved. It also needs separate evidence that the committed weights are those of the advertised model.

**Hardware attestation.** A trusted execution environment (TEE) is a hardware-isolated execution mode of a processor. It records cryptographic hashes, called measurements, of the software it loads and reports them in evidence signed with a hardware-rooted key.[^10] In the attestation architecture of the Internet Engineering Task Force (IETF), a verifier compares that evidence with reference values and manufacturer endorsements. A relying party then uses the result to decide whether to trust the machine.[^3] Attestation establishes which software was loaded on genuine hardware in a protected mode. The hardware maker and the behavior of the measured software remain trusted.

**Signatures and transparency logs.** A signature ties specific bytes to a signer's key. Sigstore's model signing library hashes every file of a model into a manifest and signs the manifest. A user can therefore check that a downloaded model is what a known identity signed. When signing goes through Sigstore, the event is recorded in an append-only transparency log, where signers can watch for signatures they did not make.[^6] Such records establish who signed what and make quiet replacement detectable. They say nothing about whether the signed model is good.

**Re-execution and sampling.** A checker can repeat all or part of a computation, for every request or a sample, and compare the results. In TOPLOC, the provider commits to compact hashes of the model's intermediate activations, the values the model computes inside its layers. A validator recomputes these hashes faster than the original generation. In the authors' experiments, the method detected changed models, prompts and numeric precision while tolerating numerical differences across graphics processors.[^5] The validator must hold the claimed model. The scheme also covers only what it hashes. Its authors note that it cannot catch a provider that generates its output with a cheaper model and computes the hashed activations with the claimed one.[^5]

**Formal proofs.** Formal verification seeks a mathematical proof that a technical claim is true, subject to certain assumptions.[^1] The guaranteed safe AI framework proposes extending this idea to AI systems. In the framework, a verifier component would provide an auditable proof certificate that a system satisfies a safety specification relative to a world model. A world model is a mathematical description of how the system affects the world.[^7] The certificate is only as useful as its specification and world model.

**Audits with structured access.** Claims about a developer's internal practices cannot be settled by one cryptographic check, so auditors examine them with more access than the public has. Casper and colleagues argue that black-box access, meaning querying a system and observing its outputs, is insufficient for rigorous audits. They also argue that access to weights and to training and deployment information, such as code, allows more scrutiny.[^8] A 2026 proposal defines frontier AI auditing as rigorous third-party verification of developers' safety and security claims, based on deep, secure access to non-public information. The proposal also describes four AI Assurance Levels of increasing confidence.[^9] A proposed protocol called Attestable Audits runs benchmarks inside TEEs. The aim is to keep model weights and test data confidential while letting users verify that they interacted with a compliant model.[^10] Audits place trust in the auditor's competence, independence and access.

## A successful check still leaves three gaps

A verification result covers only the claim as stated, so three gaps remain.

First, an attestation shows what was loaded. It does not show that the software is safe. For example, the proof-of-guardrail system uses TEE attestation to show that an agent's response passed through a specific open-source guardrail. Its authors warn that a developer could still actively jailbreak the guardrail, that is, trick it into letting through content it should block.[^11]

Second, a proof covers its specification. If the specification or the world model leaves out a harm, a valid proof says nothing about that harm.[^7]

Third, some parties must still be trusted. The IETF architecture uses the term roots of trust for components that no evidence describes, so endorsements must vouch for them. For hardware attestation, the verifier typically trusts the chip manufacturer and its hardware.[^3]

## A hypothetical hospital maps its questions to evidence

:::example Hypothetical: a hospital evaluates a hosted model for clinical notes
A hospital is considering a vendor's hosted model to draft summaries of clinical notes. The vendor says notes are processed in a TEE, deleted afterward and handled by the model the hospital tested. Before sending any note, the hospital maps each question to evidence:

| Question | Evidence that could answer it | What would remain unverified |
| --- | --- | --- |
| Do notes reach only the software the vendor describes? | An attestation report, checked by the hospital's gateway against measurements published in a log | Flaws in that software; the chip maker's keys |
| Is the served model the one the hospital tested? | A signed manifest of the weight files, measured when the model is loaded | How the model behaves on future patients |
| Are notes deleted after processing? | Published software images that independent researchers can analyze | Systems outside the attested environment, such as gateway logs |
| Are the summaries accurate enough? | The hospital's own evaluation on its notes, or an evaluation run in a TEE | Whether the test notes represent future use |
| Does the vendor follow its security practices? | A third-party audit with access to internal information | The audit's scope and the auditor's independence |

The hospital can make the first three rows conditions for sending data and manage the last column by contract.
:::

## Further reading by topic

- [Confidential computing & attestation](/topics/confidential-computing/)
- [Verifiable inference & computation](/topics/verifiable-inference/)
- [Formal verification](/topics/formal-verification/)
- [Verifiable evaluation & audits](/topics/evaluation-audits/)
- [Model & data supply chain](/topics/supply-chain/)
- [Content provenance & watermarking](/topics/content-provenance/)
- [Agent identity & accountability](/topics/agents-accountability/)
- [Compute governance & verification](/topics/governance-compute/)
