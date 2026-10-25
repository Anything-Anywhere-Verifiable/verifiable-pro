---
title: Brave Says Leo Now Encrypts GLM 5.3 Flash Chats to Attested NEAR AI Enclaves
dek: Brave said on 15 October 2026 that Leo, the AI assistant in its browser, now encrypts chats with the open-weight GLM 5.3 Flash model to a key held inside trusted execution environments run by NEAR AI. Brave says its gateway checks the environments' attestation before handing the browser the matching public key, and that checks in the browser and attestation of the loaded weights are planned.
kind: news
topics: [confidential-computing, supply-chain]
layers: [models, runtime, hardware]
event_date: 2026-10-15
published: 2026-10-25
agent: daily
evidence: [announcement, code]
related: [cohere-model-vault-confidential-computing, google-private-ai-compute-memory, apple-pcc-google-cloud]
sources:
  - Another Brave User-First AI Win: Leo adds End-to-end Encryption, Oblivious HTTP, and Verifiable Confidential Computing | Brave | 2026-10-15 | https://brave.com/blog/browser-ai-e2ee/
  - NEAR AI Cloud Brings Private Inference to Brave Leo | NEAR AI | 2026-10-15 | https://near.ai/blog/near-ai-cloud-brings-private-inference-to-brave-leo
  - near-tee-verifier (brave/near-verifier README) | Brave on GitHub | accessed 2026-10-25 | https://github.com/brave/near-verifier
---

Brave said on 15 October 2026 that chats in Leo, its browser's AI assistant, are now end-to-end encrypted in Brave's Release, Beta and Nightly channels when users choose GLM 5.3 Flash, an open-weight model from Z.ai that NEAR AI hosts.[^1, 2]

The browser encrypts each request with Oblivious HTTP (OHTTP) for NEAR AI's trusted execution environments (TEEs), hardware-isolated areas designed to shield code and data from the machine's operator. Brave says only the TEEs hold the decryption key. The TEEs run on Intel Trust Domain Extensions (TDX) and NVIDIA confidential-computing graphics processing units (GPUs). Brave says its AI Gateway strips users' Internet Protocol (IP) addresses and gives the browser the TEE's public key only after checking the TEE's current attestation against a verification oracle's approvals.[^1]

Before approving a deployment, Brave says, the oracle checks Intel's signature on the TDX quote (the processor's signed attestation report) and the GPUs through NVIDIA's Remote Attestation Service. It checks signed build records for NEAR AI's own images, rebuilds them from the source Brave reviewed and compares the results with the deployed images. The third-party model runtime is not rebuilt; a hardware-attested deployment log pins it and records the model image.[^1] Brave publishes the oracle's code as near-verifier, whose README says anyone with a NEAR AI API key can run it against the live service.[^1, 3]

The README adds that the oracle does not rebuild NEAR AI's compose-manager-launcher image, pins the weights' Hugging Face revision without hashing the downloaded files and cannot establish which GPU served a request.[^3] Brave plans, without giving dates, to move the gateway's check into the browser, publish a log of TEE keys so anyone can confirm all users get the same one, and have the TEEs attest to the weights they load. It says its checks still rest on Intel, NVIDIA, Sigstore, GitHub, Hugging Face, the public Domain Name System and dstack, the TEEs' operating system.[^1]

:::analysis
By the README's account, outsiders can now repeat the oracle's checks, but Leo users still take the key on the word of Brave's gateway, which also sees their IP addresses. Beyond the parties Brave lists, the checks leave the weight files' contents, the runtime's source and the GPU behind each request to trust.
:::

:::checked
On 25 October 2026 we read Brave's and NEAR AI's posts of 15 October 2026 and the near-verifier README. Neither post says which platforms are covered or how Leo users could see the attestation evidence, and the README does not say how to get an API key. We did not run near-verifier or test the service. Statements about who can read chats are the companies' claims.
:::
