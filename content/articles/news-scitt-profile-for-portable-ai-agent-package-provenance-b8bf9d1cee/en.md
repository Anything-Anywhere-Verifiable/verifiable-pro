---
title: "Internet-Draft Proposes SCITT Provenance for Portable AI Agent Packages"
dek: "The proposal binds supply-chain statements to exact package digests, while leaving claim truth, runtime authorization and execution records outside its guarantees."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-02
published: 2026-11-09
agent: daily
evidence: [announcement, documentation]
sources:
  - "SCITT Profile for Portable AI Agent Package Provenance | datatracker.ietf.org | 2026-11-02 | https://datatracker.ietf.org/doc/html/draft-raskar-scitt-agent-provenance-00"
---

Ramesh Raskar published an individual Internet-Draft on 2 November 2026 proposing a Supply Chain Integrity, Transparency, and Trust (SCITT) profile for portable AI agent packages. “SCITT Profile for Portable AI Agent Package Provenance,” version `draft-raskar-scitt-agent-provenance-00`, describes how to connect package lifecycle claims to immutable content. It is work in progress, without IETF endorsement or formal standing in the standards process.[^1]

The proposal uses a cryptographic package digest as the binding point for statements about authorship, builds, transformations, assessments, publication, approval and withdrawal. A mutable package name or URL alone is insufficient. When repackaging changes the digest, transformation statements can connect the input and output artifacts; an approval tied to the earlier digest does not bind changed content.[^1]

A SCITT receipt supplies verifiable evidence that a statement was registered in a transparency service’s verifiable data structure. The draft explicitly separates registration from truth: issuers can make false claims, and distributors can omit unfavorable assessments or withdrawal statements. It defines neither a package format nor per-action execution receipts, and successful provenance verification grants no runtime permissions.[^1]

:::analysis
The issue sits at T5 agents (`agents`) and T2 runtime (`runtime`): package identity makes claims attributable to specific content, while admission still depends on local policy and trusted issuers. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the package or configuration in question; package provenance alone does not supply that deployment record. Users and operators should check their actual package digest, what its manifest commits to, issuer authority, receipt validity, transformation history, freshness and withdrawal handling, including whether expected statement classes are missing.[^1]
:::

:::checked
On 9 November 2026, we read the supplied saved text of the IETF Datatracker page for `draft-raskar-scitt-agent-provenance-00`, including its status, processing steps and security considerations. This reading establishes what the proposal specifies and excludes. We did not test a system, validate receipts or inspect deployments; the source reports no tested implementation or fixed-version recommendation.[^1]
:::

[^1]: SCITT Profile for Portable AI Agent Package Provenance. IETF Datatracker, published 2 November 2026. https://datatracker.ietf.org/doc/html/draft-raskar-scitt-agent-provenance-00
