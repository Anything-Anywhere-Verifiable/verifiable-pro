---
title: Meta Says It Is Extending Private Processing to Its AI Glasses
dek: Meta said on 23 September 2026 that its confidential computing platform will run cloud AI workloads for its glasses. Before sending data, the glasses are designed to check a server's attestation against a publicly witnessed ledger.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-09-23
published: 2026-10-20
agent: daily
evidence: [announcement, report]
sources:
  - Bringing Private Processing to Meta AI Glasses | Engineering at Meta | 2026-09-23 | https://engineering.fb.com/2026/09/23/security/private-processing-meta-ai-glasses/
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
related: [trail-of-bits-whatsapp-tee-audit, google-private-ai-compute-memory]
---

Meta said on 23 September 2026 that it is extending Private Processing to its AI glasses. Private Processing is the confidential computing infrastructure Meta introduced in 2025 for WhatsApp and the Meta AI app. The platform runs AI models inside confidential virtual machines (CVMs), which are designed to keep their memory encrypted and isolated from the host. Meta says the platform is designed so that even Meta cannot access user data. Meta named streaming transcription, contextual search and long-term recall as workloads it designed the system to offload.[^1]

According to Meta, the glasses verify the server before sending any context. Over a remote attestation and TLS (RA-TLS) session, the device obtains a hardware-signed certificate from the server's trusted execution environment (TEE). It checks that the signature chains to a root key published by the chip vendor. It also checks that the measured software image matches an entry in an append-only ledger witnessed by an independent third party. If either check fails, it does not connect. To keep requests from being tied to an account, Meta says devices use anonymous credentials and reach its gateways through a third-party Oblivious HTTP (OHTTP) relay run by Fastly or Cloudflare.[^1]

For memory features, Meta says it built the storage engine inside the TEE and encrypts stored data with user-provided keys. Meta says the public ledger makes tampering with deployments detectable. It adds that researchers in its security program have access to the binaries under agreement, which lets them confirm that a recorded image behaves as described. Meta is also extending its bug bounty program to Private Processing on glasses and plans to give researchers tools, CVM binaries and documentation.[^1]

Trail of Bits audited the WhatsApp version before launch. In an April 2026 post, it said it found 28 issues, eight rated high severity, including attestation reports without freshness guarantees. It said Meta fixed that issue by adding a TLS nonce.[^2] We cover that audit in a [separate brief](/articles/trail-of-bits-whatsapp-tee-audit/).

:::analysis
The pre-connection checks are where outsiders can test Meta's privacy claim. The public ledger can show only whether a deployment matches the published record. Checking whether a recorded image handles context as Meta describes requires the binaries. Outside verification of the glasses therefore depends on the research access Meta grants under agreement.
:::

:::checked
On 20 October 2026 we opened Meta's 23 September 2026 engineering post and Trail of Bits' 7 April 2026 post. Meta's post does not name the third party that witnesses the ledger, and we did not inspect the ledger. The post also does not say which glasses features use Private Processing today or when the expanded bug bounty coverage starts. The Trail of Bits audit covered the WhatsApp deployment, not the glasses. We test no systems ourselves, and statements about who can access data are Meta's claims.
:::
