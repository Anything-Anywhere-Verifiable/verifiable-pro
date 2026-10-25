---
title: Researchers Say C2PA Falls Short of Its Stated Security Goals
dek: An 11-author analysis posted on 23 April 2026 reports that the C2PA content provenance specification and conforming implementations do not achieve their claimed security goals, and that C2PA's conformance program certifies products without technical review. The authors say C2PA should not yet be relied on for high-stakes uses such as legal evidence.
kind: news
topics: [content-provenance]
layers: [outputs]
event_date: 2026-04-23
published: 2026-10-20
agent: daily
evidence: [paper, announcement]
sources:
  - "Verifying Provenance of Digital Media: Security Analysis of C2PA and its Implementation | IACR Cryptology ePrint Archive | 2026-04-23 | https://eprint.iacr.org/2026/804"
  - "Verifying Provenance of Digital Media: Why the C2PA Specifications Fall Short | arXiv | 2026-04-27 | https://arxiv.org/abs/2604.24890"
  - The C2PA Launches Content Credentials 2.3 and Celebrates 5 Years of Impact Across the Digital Ecosystem | C2PA | 2026-02-09 | https://c2pa.org/the-c2pa-launches-content-credentials-2-3-and-celebrates-5-years-of-impact-across-the-digital-ecosystem/
  - Conformance | C2PA | accessed 2026-10-23 | https://c2pa.org/conformance/
related: [c2pa-exclusion-range-backdated-image, tiktok-c2pa-steering-committee]
---

Researchers from the University of Maryland, Baltimore County, Hacker Factor and the US National Security Agency posted a security analysis of the Coalition for Content Provenance and Authenticity (C2PA) system to the Cryptology ePrint Archive on 23 April 2026.[^1] The 11 authors examined version 2.2 of the C2PA specification, selected claim validators and version 0.1 of the conformance program. They say they performed the first formal-methods analysis of C2PA's core protocols.[^1]

The authors report that the specification and conforming implementations achieve neither C2PA's claimed security goals nor further goals they consider essential.[^1] Their formal analysis found that the tools that sign provenance claims and the validators that check them disagree on a signature's trusted timestamp, so timestamps can be altered.[^1]

A companion arXiv summary posted on 27 April gives examples. After Nikon revoked a camera's signing certificate in November 2025, one conforming validator still reported a signature made with it as valid. Another reported it as invalid, and neither reported the revocation.[^2] In another example, the authors changed the location data that a Pixel 10 Pro stores in an exclusion range, a part of the file the signature does not cover. A conforming validator did not detect the change.[^2]

According to the authors, the conformance program certifies products largely on self-reported compliance, without examining a product's functionality or source code.[^2] The C2PA launched the program in mid-2025.[^4] It says the program helps ensure that any product displaying a Content Credential badge handles authenticity data accurately.[^3]

The authors say the Pixel 10 Pro and version 2.3 of the specification adopted some of their proposed fixes, but version 2.4, from April 2026, does not address their concerns.[^1, 2] They conclude that C2PA should not yet be relied on for high-stakes uses such as financial disclosures, journalism or legal evidence.[^2]

:::analysis
The authors find weaknesses in the specification as well as in validators and certification. For a person checking a file, a credential shown as valid is only as strong as the validator that checked it, including how that validator handles revocation and exclusion ranges. Because conforming validators can disagree, a single valid result carries limited weight as evidence until validator behavior is specified and independently tested.
:::

:::checked
On 20 October 2026 we read the ePrint abstract page, the authors' arXiv summary and the C2PA's 9 February 2026 post on version 2.3. The full ePrint paper was behind an automated access check, so details beyond its abstract come from the summary. The summary dates the Nikon results over six months after the revocation. That would be after its 27 April posting, so we omit that interval. We found no published C2PA response to the paper. On 23 October 2026 we read the C2PA's conformance page. It dates the program's launch to mid-2025, while the February post says late 2025.
:::
