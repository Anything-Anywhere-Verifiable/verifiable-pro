---
title: "Solana Confidential Compute Launches on Devnet, Solana Compass Reports"
dek: "The reported beta checks hardware attestations onchain for AI applications. It remains unaudited and is intended for development use."
kind: news
topics: [confidential-computing, verifiable-inference]
layers: [runtime, hardware]
event_date: 2026-11-13
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Solana Foundation and Nito Launch Solana Confidential Compute on Devnet to Verify Private AI Onchain | solanacompass.com | 2026-11-13 | https://solanacompass.com/news/solana-foundation-and-nito-launch-solana-confidential-compute-on-devnet-to-verify-private-ai-onchain"
---

The Solana Foundation and Nito have released Solana Confidential Compute as a devnet beta, Solana Compass reported on 13 November 2026. The open-source tools are intended to let applications check hardware attestation onchain before accepting signed AI outputs. The publication reports that the software is unaudited and intended for development use.[^1]

A trusted execution environment (TEE) is a hardware-backed environment designed to isolate code and data from the surrounding system. According to Solana Compass’s account of the release, a confidential virtual machine creates a signing key and obtains a hardware-signed report tying the key to a recent Solana slot. An onchain program checks the report and records the key, hardware type and expiry; a recipient can then check an answer’s signature and the key’s onchain record.[^1]

The article reports that the verifier checks the chip signature, whether code matches an approved list, and freshness. It says the beta supports Intel TDX and AMD SEV-SNP attestations, with NVIDIA GPU attestation in development. Solana Compass also reports that an audit is in progress and that mainnet is planned to follow it; it gives no mainnet date.[^1]

:::analysis
The claim sits at the runtime (T2) and hardware (T1) layers: a verifier depends on the onchain checks and the hardware’s attestation, as well as the approved code list. A passing check gives evidence about the attested environment and key; it does not establish that AI answers are correct or independently establish privacy. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue; the article does not establish that this system records those details. Users and operators should check the key’s status, expiry and applicable approved code, and confirm whether their own deployment is within the reported development-only scope.[^1]
:::

:::checked
For this preview prepared on 18 November 2026, we read the saved text of [Solana Compass’s article](https://solanacompass.com/news/solana-foundation-and-nito-launch-solana-confidential-compute-on-devnet-to-verify-private-ai-onchain), published on 13 November 2026. Solana Compass identifies itself as independent of the Solana Foundation; we did not read the Foundation’s announcement or product page directly. We did not test the system or independently verify the release, its security, or the audit’s status.[^1]
:::
