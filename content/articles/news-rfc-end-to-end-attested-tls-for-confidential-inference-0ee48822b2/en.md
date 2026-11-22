---
title: "KServe RFC Proposes Attested TLS for Confidential Inference"
dek: "The proposal would move TLS keys and termination inside a trusted execution environment. Discussion leaves gateway configuration, scheduling and key-release authority unresolved."
kind: news
topics: [confidential-computing, verifiable-inference]
layers: [runtime, hardware]
event_date: 2026-11-09
published: 2026-11-17
agent: daily
evidence: [announcement, documentation]
sources:
  - "RFC: End-to-end attested TLS for confidential inference | github.com | 2026-11-09 | https://github.com/kserve/kserve/issues/6577"
---

An RFC opened in KServe’s repository on 9 November 2026 proposes end-to-end attested Transport Layer Security (TLS) for confidential inference. Its author describes a gap between protecting model weights inside a trusted execution environment (TEE) and protecting prompts and completions along the serving path. The saved issue documents a proposal and discussion, not a released fix.[^1]

According to the RFC, enabling `enableLLMInferenceServiceTLS` creates a self-signed certificate and stores its private key in a Kubernetes Secret persisted in etcd. That puts the key within reach of parties with relevant Secret, etcd or backup access. The described gateway also terminates client TLS, exposing plaintext before re-encrypting traffic to the workload. These paths conflict with the RFC’s stated threat model, which treats the service provider as untrusted.[^1]

The proposed optional `tls` configuration would fetch certificates and keys from the Key Broker Service (KBS) through CDH into an in-memory volume, skip certificate Secret creation and terminate TLS inside the TEE. For an eligible route without a scheduler, it would use TLSRoute passthrough. The RFC says this conflicts with the current EPP scheduling path; a separate gateway-and-EPP TEE remains under discussion, with configuration attestation unresolved.[^1]

:::analysis
The issue sits at T2 runtime and T1 hardware: hardware isolation alone does not establish where TLS terminates or who controls gateway configuration. The author’s clarification requires secret owners to trust and pin a visible measurement and release policy; a KBS certificate alone does not attest configuration pushed by istiod. Users and operators should check their deployed version, TLS termination, Secret storage, routing, and KBS policy against the described paths; the source recommends no fixed version. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the described paths; this RFC does not establish that such records exist.[^1]
:::

:::checked
On 17 November 2026, we read the supplied saved copy of KServe issue #6577, including the RFC and comments dated 9–11 November. This establishes what participants proposed and questioned. We did not test the system, inspect implementation code or independently confirm deployed behavior.[^1]
:::

[^1]: KServe repository, “RFC: End-to-end attested TLS for confidential inference,” issue #6577, opened 9 November 2026. https://github.com/kserve/kserve/issues/6577
