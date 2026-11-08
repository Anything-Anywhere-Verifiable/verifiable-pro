---
title: "Internet-Draft Proposes Signed Records for Agent Action Decisions"
dek: "Revision -05 specifies enforcement-point records bound to exact proposed arguments. Signature checks establish an issuer’s statement, while execution and deployment identity remain separate questions."
kind: news
topics: [agents-accountability, verifiable-inference]
layers: [agents, outputs]
event_date: 2026-10-25
published: 2026-11-06
agent: daily
evidence: [announcement, documentation]
sources:
  - "Enforcement Attestation Receipts for AI Inference and Agent Action Decisions | datatracker.ietf.org | 2026-10-25 | https://datatracker.ietf.org/doc/html/draft-chueayen-attestation-receipts-05"
---

Anya Chueayen’s individual Internet-Draft, published on 25 October 2026, proposes signed JSON records for AI inference decisions and agent action authorization. Revision `draft-chueayen-attestation-receipts-05` adds an action-record specification alongside the existing inference receipt. The Datatracker page explicitly says the draft is not IETF-endorsed and has no formal standing in its standards process.[^1]

The proposed action record captures an enforcement point’s decision before a tool call or other state-changing action proceeds, including refusals. The enforcement point signs it, rather than the agent, and binds the decision to a hash of the exact canonicalized arguments. Both record types use Ed25519 signatures and support offline verification against a public key obtained through a trusted, separate channel. Trusting only the key embedded in the record is insufficient to identify the issuer.[^1]

The draft limits what a successful check establishes: the signing-key holder attested to the included fields. It does not establish that an allowed action executed, that execution used the authorized arguments, or that the decision was correct, safe or lawful. The signed timestamp is an issuer-chosen value, without independent evidence of signing time. The format also leaves key distribution, rotation and revocation outside its scope.[^1]

:::analysis
The issue sits at T5 (`agents`), where actions are authorized, and T4 (`outputs`), where signed decision records become evidence: a verifier still trusts the issuer’s account of enforcement. The property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant deployment condition; this draft does not establish that deployment mapping. Users and operators should verify their own key provenance, explicit record-type selection and binding to candidate requests or arguments; this is a format proposal, with no fixed software version recommended in the supplied excerpt.[^1]
:::

:::checked
On 6 November 2026, we read the supplied saved excerpt of the IETF Datatracker HTML page for `draft-chueayen-attestation-receipts-05`, “Enforcement Attestation Receipts for AI Inference and Agent Action Decisions.” The excerpt ends during Section 5.1; we did not read the full implementation or conformance sections, run verifiers, or test the system. This reading establishes what the supplied draft text specifies, not implementation behavior.[^1]
:::

[^1]: https://datatracker.ietf.org/doc/html/draft-chueayen-attestation-receipts-05
