---
title: "Internet-Draft Proposes Architecture for Auditable AI Decision Trails"
dek: "The VAP draft describes how existing security technologies could support checks on decision records, while limiting what those records can establish."
kind: news
topics: [agents-accountability, verifiable-inference]
layers: [agents, runtime]
event_date: 2026-11-15
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Verifiable AI Provenance Framework (VAP): An Architectural Framework for Auditable AI Decision Trails | www.ietf.org | 2026-11-15 | https://www.ietf.org/archive/id/draft-kamimura-vap-framework-03.html"
---

On 15 November 2026, an Internet-Draft by T. Kamimura of the VeritasChain Standards Organization proposed the Verifiable AI Provenance Framework (VAP), an architecture for producing auditable records of automated decisions. The document is work in progress, intended to prompt discussion; it is not a finished standard.[^1]

The draft maps the proposed framework to existing technologies: Supply Chain Integrity, Transparency and Trust (SCITT) for transparency infrastructure; Remote Attestation Procedures (RATS) for environment attestation; and CBOR Object Signing and Encryption (COSE) for cryptographic operations. It does not define a new protocol, wire format or API. Domain-specific profiles would supply requirements for particular uses.[^1]

The proposed records aim to make changes to committed entries and omissions from anchored batches detectable. An inclusion proof checks that a record appears in a particular log state; a consistency proof checks that a later state extends an earlier one without removing or changing records. The draft also proposes attribution to the holder of a signing key. These checks cannot reveal an event that was never measured and that no other record implies.[^1]

:::analysis
The issue sits at **T5, agents**, where actions need attribution, and **T2, runtime**, where a decision and its operating context are recorded. Identifiability matters: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to a particular affected version or configuration; the draft does not report such an incident or establish that any deployment records those details. Users and operators should check whether their own records identify the relevant system version and configuration, and whether commitments, proofs and signing-key identities can be checked independently. Even a passing record check leaves the accuracy of the original capture and the correctness, fairness and safety of the decision outside what the record establishes.[^1]
:::

:::checked
On 24 November 2026 we read the saved official IETF Internet-Draft, [draft-kamimura-vap-framework-03](https://www.ietf.org/archive/id/draft-kamimura-vap-framework-03.html). We did not test a VAP system or independently verify an implementation; the document describes an architecture and its intended properties.[^1]
:::
