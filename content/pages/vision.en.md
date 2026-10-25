---
title: Powerful AI should come with evidence
dek: Our vision for AI whose claims people can check.
published: 2026-10-21
updated: 2026-10-24
---
<div data-include="positioning"></div>

## Why this matters {#problem}

The more we ask AI to do on our behalf, the more we need evidence for the trust we place in it.

Before sharing private data or granting an agent access to tools, people should be able to check the service's promises. Engineers and auditors should have evidence they can examine and challenge.

## What should be checkable {#verifiable}

- **Privacy.** Who can read a prompt and its result? How are they retained?
- **Security policies.** Which policy governed a request, and was it enforced?
- **Model identity.** Which model, software and settings actually processed a request?
- **Agent actions.** What did an agent do, and under whose permissions?

These are questions we want AI systems to answer with evidence. Each check should state the claim it covers and the trust assumptions behind it.

## Why we start with TEEs {#why-tees}

Trusted execution environments (TEEs) give this vision a practical starting point. Their hardware is designed to isolate running software from the host within a defined threat model. Remote attestation provides a signed record of the loaded software, which a client can check before sending data.

AI services already use these mechanisms, and TEE security is our editor's research area. We examine their deployment and failures. Attestation alone does not establish that software enforces its policy correctly or that an AI answer is true.

### How other methods help {#compare}

Proofs, re-execution, audits and signatures cover other parts of the problem. We compare them with TEEs and study how they work together, keeping [their trust assumptions](/topics/#tiers) in view.

## What we are working toward {#goals}

verifiable.pro connects this vision to work people can use:

1. A bilingual [TEE learning path](/learn/#tee-path), from the basics to checking a real attestation report, including CPU and GPU confidential computing and how TEEs fail.
2. Dated records of [AI services and their evidence](/topics/confidential-computing/#services) and [attacks on TEEs](/topics/confidential-computing/#limits), showing what outsiders can inspect.
3. An assistant running inside GPU confidential computing, with browser checks of its serving environment's attestation evidence. Today it [runs in demo mode](/about/#assistant).

Our aim is to make checking evidence a normal part of choosing, building and using AI systems.

### Our standard {#non-goals}

We report what the evidence supports, attribute vendor claims and correct errors in public. We do not certify services.

## Who is building it {#editor}

verifiable.pro is maintained by SEPT Lab and edited by Mengyuan Li. Meet the [contributors](/contributors/) who help build it.

### Who it is for {#readers}

We write in English and Chinese for people using, building, researching or assessing AI systems.

### Check our work {#accountability}

Read [how we work](/about/) and [how to report an error](/about/#corrections). Our sources and dated corrections are open to scrutiny.
