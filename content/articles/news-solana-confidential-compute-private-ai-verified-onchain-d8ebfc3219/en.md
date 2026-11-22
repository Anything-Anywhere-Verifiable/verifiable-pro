---
title: "Solana Foundation Announces Confidential Compute Beta for Onchain Attestation"
dek: "The open-source toolkit checks hardware attestations and records verification details on Solana, according to the foundation. The project is on devnet and has not yet been audited."
kind: news
topics: [confidential-computing, verifiable-inference]
layers: [runtime, hardware]
event_date: 2026-11-13
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Solana Confidential Compute: Private AI, Verified Onchain | solana.ai | 2026-11-13 | https://solana.ai/blog/nito-solana-confidential-compute"
---

On 13 November 2026, the Solana Foundation introduced Solana Confidential Compute, an open-source software development kit and onchain verification program built by the Nito team in coordination with the foundation. The foundation says the project is in beta on Solana devnet, with mainnet planned. It has not yet been audited, and the announcement recommends using it for development for now.[^1]

The project is intended to check hardware attestations: signed reports containing evidence about a trusted execution environment (TEE), a hardware-backed environment designed to isolate code and data from the surrounding system. The foundation says its onchain program checks a report and records a signing key, hardware type and expiry date on Solana. AI computation takes place offchain; the record need not include the conversation or private inputs.[^1]

According to the announcement, a machine in a confidential virtual machine generates a signing key, and hardware signs a report binding the key to a recent Solana slot. The machine signs its answers with that key, allowing a recipient to check the signature and look up the key’s onchain record. The release covers Intel TDX and AMD SEV-SNP attestations; NVIDIA GPU attestation is in progress. The foundation also describes Nito’s Confidential Chat, which it says encrypts prompts on the user’s device and responses before their return.[^1]

:::analysis
The claim spans runtime (T2) and hardware (T1): a verifier depends on the attestation check and hardware evidence to assess the environment behind a signing key. A matching signature and record do not by themselves establish that the model’s answer is correct or identify the exact software version and configuration that served a user. Identifiability matters: if that exact version and configuration are recorded and checkable, a user can determine whether they were exposed to a relevant issue. Users and operators should check what their own deployment records, whether they can link a response to it, and whether their use follows the announcement’s development-only advice; the source specifies no fixed version.[^1]
:::

:::checked
On 18 November 2026 we read the saved Solana Foundation announcement, [“Solana Confidential Compute: Private AI, Verified Onchain”](https://solana.ai/blog/nito-solana-confidential-compute).[^1] We did not test the system, inspect its code or independently verify its security claims, deployment configuration or onchain records.
:::
