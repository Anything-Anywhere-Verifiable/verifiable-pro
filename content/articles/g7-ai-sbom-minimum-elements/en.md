---
title: CISA and G7 Partners Publish Minimum Elements for AI Software Bills of Materials
dek: Joint guidance released on 12 May 2026 lists what an inventory of an AI system's components should record, including hashes of model weights and datasets. The elements are voluntary and add to the general minimum elements for software bills of materials.
kind: news
topics: [supply-chain]
layers: [models]
event_date: 2026-05-12
published: 2026-10-20
agent: daily
evidence: [announcement, documentation]
sources:
  - CISA & G7 Partners Release Joint Guidance on the Minimum Elements of a Software Bill of Materials for Artificial Intelligence | Cybersecurity and Infrastructure Security Agency | 2026-05-12 | https://content.govdelivery.com/accounts/USDHSCISA/bulletins/416bd74
  - "Software Bill of Materials for AI: Minimum Elements | G7 Cybersecurity Working Group, via BSI | 2026-05-12 | https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/KI/SBOM-for-AI_minimum-elements.html"
  - 2026 Minimum Elements for a Software Bill of Materials (SBOM) | Cybersecurity and Infrastructure Security Agency | 2026-07-29 | https://www.cisa.gov/resources-tools/resources/2026-minimum-elements-software-bill-materials-sbom
related: [sigstore-model-signing-stable-release]
---

On 12 May 2026 the US Cybersecurity and Infrastructure Security Agency (CISA) and partners released joint guidance on the minimum elements of a software bill of materials (SBOM) for AI systems. The partners came from Germany, Canada, France, Italy, Japan, the United Kingdom and the European Union.[^1] An SBOM is an inventory of the components in a piece of software. CISA likens it to an ingredients list.[^1]

The Cybersecurity Working Group of the Group of Seven (G7) wrote the guidance. The guidance groups its elements into seven clusters: metadata about the SBOM itself, system-level properties, models, datasets, infrastructure, security properties and key performance indicators.[^2]

For each model, an SBOM for AI should record a hash of the weights or model file (a fingerprint computed from its contents) and the hash algorithm. With these values, the component's integrity can be validated. If the SBOM's author has no access to the model artifact, the value should be marked unknown.[^2] Each dataset gets its own hash and a provenance element describing its sources, collection methods and processing steps. The metadata cluster includes a digital signature attributable to the SBOM's author.[^2]

CISA says the elements are neither exhaustive nor mandatory. It adds that they reflect the consensus of G7 experts and will expand over time. Because AI systems are software systems, CISA says, the elements should be considered in addition to the general minimum elements for an SBOM.[^1] CISA and partners updated those general elements on 29 July, replacing the list that the National Telecommunications and Information Administration published in 2021. They noted that AI software may require additional elements.[^3]

:::analysis
Hashes give an SBOM for AI a property that anyone relying on the SBOM can check directly: a downloaded model file or dataset either matches the recorded value or it does not. Other elements, such as a dataset's provenance description, remain statements by the SBOM's author. The signature attributes those statements to the author but does not confirm them. Showing that the hashed model is the one actually serving requests needs separate evidence, for example attestation (a hardware-signed record of the loaded software) from the environment that runs it.
:::

:::checked
On 20 October 2026 we read CISA's 12 May 2026 bulletin, the guidance document from the website of Germany's Federal Office for Information Security (BSI) and CISA's 29 July page on the 2026 minimum elements. We did not evaluate SBOM formats or tools against these elements, and we test no systems ourselves.
:::
