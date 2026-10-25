---
title: Google Says It Will Add Encrypted Per-User Memory to Private AI Compute
dek: Google said on 23 September 2026 that Private AI Compute will gain persistent memory encrypted with keys held on users' devices. A Trail of Bits assessment linked from Google's technical brief reported ten findings, two of which remain unresolved.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-09-23
published: 2026-10-20
agent: daily
evidence: [announcement, documentation, report]
sources:
  - Advancing Private AI Compute with secure, server-side memory | Google DeepMind | 2026-09-23 | https://deepmind.google/blog/advancing-private-ai-compute-with-secure-server-side-memory/
  - "Google Private AI Compute: Enabled with Secure Server-Side Memory (technical brief) | Google | 2026-09-23 | https://services.google.com/fh/files/misc/private_ai_compute_technical_brief.pdf"
  - "Google Private AI Compute, Secure Server-Side Memory: Security Assessment | Trail of Bits | 2026-09-21 | https://github.com/trailofbits/publications/blob/master/reviews/2026-09-google-secure-memory-securityreview.pdf"
---

Google said on 23 September 2026 that it will add a persistent, per-user memory layer to Private AI Compute, which until now erased context when each task ended. The platform processes AI requests in hardware-isolated cloud environments. Google says the keys that unlock the memory will be held only on users' devices. It says a secure enclave, one such isolated environment, will decrypt the memory temporarily to handle a request.[^1]

According to the updated technical brief, the memory store is a per-user database inside a trusted execution environment (TEE). The brief says keys are released only to an enclave whose attestation matches an endorsed memory binary. An attestation is a signed record of the software an enclave loaded. Google says the memory server and its runtime are open source. It says reproducible builds and an append-only ledger of binary digests tie that code to the deployed binaries. Because each request must reach a specific user's store, the brief says the memory system does not claim network-level non-targetability, the property that requests cannot be linked to users.[^2]

Google's post says devices will be able to verify its server software before sending personal data.[^1] The brief lists device-side validation of attestation evidence as future work, along with a ledger co-signed by independent third parties. It gives no dates.[^2]

A Trail of Bits assessment dated 21 September 2026, linked from the brief, reported ten findings. Google resolved eight, and two remain unresolved. The unresolved finding rated high is that hashes of model-response text are sent outside the trusted computing base, the components that the system's security depends on. The hashes are sent out for checks on whether responses recite copyrighted text. Google plans a filter inside the enclave so that most hashes never leave it. Trail of Bits says this reduces the risk without eliminating it. The other unresolved finding, rated low, is that deleted memories may be restored into the active database. Google accepted that risk. Trail of Bits also noted that Google can change the system without prior external review and that the system contains extensive closed-source code.[^3]

:::analysis
Persistent memory makes verification harder, because stored data must stay protected across software releases. Google's design gives outsiders concrete objects to examine. They include an open-source memory server and a public ledger of the binary digests that key release depends on. The same documents mark the limits. Device-side validation of attestation is still future work, and the audit left an out-of-enclave data path and a memory-deletion weakness unresolved.
:::

:::checked
On 20 October 2026 we opened Google's 23 September 2026 post, the technical brief it links and the Trail of Bits assessment. The brief is dated only by month, so our source list uses the post's date. Google's post does not name the auditor. We did not inspect the ledger or the open-source code, and we test no systems ourselves. The post describes the feature in the future tense, but the brief describes it as added. We could not confirm whether it has reached users.
:::
