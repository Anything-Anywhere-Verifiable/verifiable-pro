---
title: "Internet-Draft Examines How to Bind AI Models to Inference Runtimes"
dek: "An individual IETF Internet-Draft examines evidence linking a loaded model to its runtime and, separately, an inference request to an execution instance."
kind: news
topics: [verifiable-inference]
layers: [models, runtime]
event_date: 2026-11-16
published: 2026-11-22
agent: daily
evidence: [announcement, documentation]
sources:
  - "Attestation of AI Inference Execution Environments Using RATS: Trusted Model Loading, Runtime Binding, and Per-Inference Evidence | datatracker.ietf.org | 2026-11-16 | https://datatracker.ietf.org/doc/draft-elekula-rats-model-loading-binding/"
---

On 16 November 2026, an individual Internet-Draft by Kayode Oluwole Elekula set out an approach to a gap in AI inference attestation: evidence about a model and an inference runtime does not by itself establish that the runtime loaded that model. The draft also distinguishes evidence about an execution instance from evidence connecting a particular request to that instance.[^1]

The draft examines a protected model-loading mechanism and a trusted measurement agent that would observe or control loading within a protected trust boundary. It proposes using cryptographically protected evidence to represent the relationship between the measured artifact, the runtime and the execution instance. For individual requests, it describes associating an operation identifier and evidence with the applicable instance. These are candidate approaches and requirements in a draft, not reported deployment results.[^1]

The document examines existing Remote ATtestation procedureS (RATS) architecture and information models, including the Entity Attestation Token, for representing this evidence. It does not define a new attestation protocol or a universal inference receipt format. It is an individual contribution, has no IETF endorsement or formal standing in the standards process, and does not represent RATS Working Group consensus.[^1]

:::analysis
The issue spans the model layer (T3) and runtime layer (T2): a verifier needs evidence of the relationship between the measured model and the runtime that loaded it, while continuing to trust the measurement and loading mechanisms. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular version and configuration. Users and operators should check whether their own evidence binds the loaded model and relevant configuration to the execution instance and, when needed, connects their request to that instance; the draft does not recommend a fixed software version. Attestation does not establish model correctness, safe behavior or output correctness.[^1]
:::

:::checked
On 22 November 2026, we read the saved IETF Datatracker record and included text of `draft-elekula-rats-model-loading-binding-00`.[^1] This establishes what the draft describes and its stated status; we did not test a system or independently confirm an implementation.
:::
