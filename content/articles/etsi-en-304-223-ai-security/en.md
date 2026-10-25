---
title: ETSI Publishes European Standard Setting Baseline Cybersecurity Requirements for AI Models and Systems
dek: ETSI announced EN 304 223 on 14 January 2026, turning its 2025 technical specification on AI security into a European Standard. Among other provisions, it requires developers to release cryptographic hashes of the model components they share and to record where public training data came from.
kind: news
topics: [supply-chain]
layers: [models]
event_date: 2026-01-14
published: 2026-10-20
agent: daily
evidence: [standard, announcement]
sources:
  - ETSI releases world-leading standard for securing AI | ETSI | 2026-01-14 | https://www.etsi.org/newsroom/press-releases/2627-etsi-releases-world-leading-standard-for-securing-ai/
  - ETSI EN 304 223 V2.1.1, Securing Artificial Intelligence (SAI); Baseline Cyber Security Requirements for AI Models and Systems | ETSI | 2025-12 | https://www.etsi.org/deliver/etsi_en/304200_304299/304223/02.01.01_60/en_304223v020101p.pdf
  - "A world first: the ETSI global cybersecurity standard for AI | ETSI | 2026-05-15 | https://www.etsi.org/enjoy-magazine/articles/ai-cybersecurity-standard-etsi-en-304-223/"
related: [g7-ai-sbom-minimum-elements, sigstore-model-signing-stable-release, en-18286-ai-act-harmonized-standard]
---

On 14 January 2026, the European Telecommunications Standards Institute (ETSI) announced ETSI EN 304 223, a European Standard (EN) that sets baseline cybersecurity requirements for AI models and systems.[^1] ETSI's Technical Committee on Securing Artificial Intelligence produced the standard, which was adopted on 8 December 2025. It began as a technical specification, ETSI TS 104 223, published in April 2025.[^2] ETSI names two UK bodies among the main contributors: the National Cyber Security Centre and the Department for Science, Innovation and Technology.[^3]

The standard sets out 13 principles across five lifecycle phases, from secure design to secure end of life. For each principle, it names the stakeholders mainly responsible, such as developers, system operators and data custodians. It covers AI systems that incorporate deep neural networks, such as generative AI.[^1, 2]

Several provisions concern the integrity and origin of models and data. Developers must release cryptographic hashes, or file fingerprints, for model components they make available to other stakeholders, so that recipients can verify that the components are authentic. Attackers plant poisoned training data to change a model's behavior. Such data is likely to be found only after training, if at all. So developers must document where any public training data came from and how they obtained it. The standard recommends recording at least the source, such as the URL of a scraped page, and the date and time of collection. The aim is to let a developer tell whether a reported poisoning attack reached its datasets. Developers should share their documentation, including training-data sources, with downstream system operators and data custodians.[^2]

The standard's foreword set 30 September 2026 as the deadline for adopting or endorsing the EN nationally and for withdrawing conflicting national standards. The standard points to a separate specification, ETSI TS 104 216, for assessing conformance with its provisions.[^2]

:::analysis
The hashes let an operator check that a model file it received matches the one the developer released. A hash identifies the release only if the operator obtains the hash through a channel it trusts. Yet the standard does not call for signatures or for transparency logs, which are public, append-only records. The training-data records stay within the supply chain. The standard does not require developers to publish them, so it gives outside parties no way to check them.
:::

:::checked
On 20 October 2026 we read ETSI's press release of 14 January 2026, the text of EN 304 223 V2.1.1 and ETSI's magazine article of 15 May 2026. ETSI TS 104 216 was not in ETSI's public download directory, so we could not review how conformance is to be assessed. We did not check which national standards bodies have adopted the standard or whether any organization claims conformance.
:::
