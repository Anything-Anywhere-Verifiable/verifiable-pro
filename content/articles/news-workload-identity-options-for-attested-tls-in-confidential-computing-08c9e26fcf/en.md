---
title: "Internet-Draft Sets Out Workload Identity Options for Attested TLS"
dek: "An individual draft distinguishes approved workload types from specific instances and describes two ways to bind TLS keys to attestation. Its central caveats concern authorization and private-key provenance."
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-10-28
published: 2026-11-09
agent: daily
evidence: [announcement, documentation]
sources:
  - "Workload Identity Options for Attested TLS in Confidential Computing | datatracker.ietf.org | 2026-10-28 | https://datatracker.ietf.org/doc/html/draft-reddy-seat-cc-workload-identity-00"
---

An individual Internet-Draft published on 28 October 2026 sets out two workload identity options for attested Transport Layer Security (TLS). Written by Tirumaleswar Reddy.K, Nathanael Ritz, Yaron Sheffer and Ionuț Mihalcea, draft-reddy-seat-cc-workload-identity-00 offers discussion material for SEAT. It describes deployment models and options rather than specifying a protocol; it is work in progress, without IETF endorsement or formal standards standing.[^1]

The draft distinguishes a workload’s type from a particular instance: two instances can have identical measurements. Option A uses a workload-generated key, conveyed in signed attestation evidence and presented as a raw public key or self-signed certificate. It requires no public key infrastructure (PKI) and supplies no separate workload identifier. Option B uses a WIMSE workload identity certificate, with the same public key also bound through attestation; the identifier can persist across key rotation.[^1]

The authors warn that checking a certificate and attestation independently does not establish that the measured environment is authorized for the asserted identity. Where that assurance is required, the relying party must evaluate identity and measurements jointly. Both options also depend on assurance about key generation, non-exportability and storage: merely including a public key in evidence or a certificate does not establish those properties.[^1]

:::analysis
The issue sits at T2 runtime and T1 hardware: interpreting workload measurements and TLS key bindings still depends on the attestation roots and appraisal policy described in the draft. Users and operators should verify key matching, the identity-to-measurement authorization policy, and evidence supporting private-key provenance for their chosen option. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant deployment condition; type measurements alone cannot distinguish identical instances. These are deployment checks derived from the draft’s distinctions, not a reported vulnerability or fixed-version recommendation.[^1]
:::

:::checked
On 9 November 2026 we read the supplied saved excerpt of “Workload Identity Options for Attested TLS in Confidential Computing,” version 00, on IETF Datatracker. The excerpt ends partway through Section 7, so our reading establishes the options and caveats above, not the complete key-attestation mechanism or later security considerations. We did not test the system, inspect implementations or independently validate the cloud deployments surveyed.[^1]
:::

[^1]: Workload Identity Options for Attested TLS in Confidential Computing. IETF Datatracker, individual Internet-Draft, published 28 October 2026. https://datatracker.ietf.org/doc/html/draft-reddy-seat-cc-workload-identity-00
