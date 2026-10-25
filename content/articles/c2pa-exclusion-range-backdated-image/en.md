---
title: Researcher Says C2PA Exclusion Ranges Let a Malicious Signer Backdate Edited Images
dek: On 2 October 2026, security researcher David Buchanan published an image whose Content Credentials signature and trusted timestamp, he says, are valid but cover none of its content. The demonstration separates two checks that are easy to confuse: whether a signature is valid and what it covers.
kind: news
topics: [content-provenance]
layers: [outputs]
event_date: 2026-10-02
published: 2026-10-20
agent: daily
evidence: [report, standard, paper]
sources:
  - How to Hack Time, With C2PA | David Buchanan | 2026-10-02 | https://www.da.vidbuchanan.co.uk/blog/hacking-time.html
  - "Content Credentials: C2PA Technical Specification, Version 2.4 | C2PA | 2026-04-01 | https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html"
  - "Verifying Provenance of Digital Media: Security Analysis of C2PA and its Implementation | IACR Cryptology ePrint Archive | 2026-04-23 | https://eprint.iacr.org/2026/804"
related: [c2pa-security-analysis-umbc, tiktok-c2pa-steering-committee]
---

Security researcher David Buchanan reported on 2 October 2026 that a signer can produce Content Credentials whose signature and trusted timestamp stay valid but cover none of a file's content.[^1] Content Credentials are the provenance format specified by the Coalition for Content Provenance and Authenticity (C2PA). They attach a signed record, called a manifest, that makes claims about a file's origin. Manifests often include a timestamp from an independent time-stamp authority, which attests that the signature existed at a given time.[^1]

The method uses exclusion ranges, byte ranges that a signer can leave out of the cryptographic hash that the signature covers. Buchanan set a single exclusion covering the entire file, so the claim signature covers the hash of an empty string. He says he edited the image after signing and that the signature and the timestamp stayed valid.[^1] His example is a photo of a lottery ticket. He says it shows the winning numbers of the 28 August 2026 EuroMillions draw but carries a trusted timestamp from hours before the draw. He reports that the C2PA verification tools he could find did not flag anything unusual.[^1]

Version 2.4 of the C2PA specification says the software that creates a manifest must limit exclusion ranges to the manifest store or to asset metadata. It also tells validators to reject a manifest when the exclusion range that holds it contains other data, and to report any additional exclusion ranges with an informational code.[^2]

Buchanan writes that a whole-file exclusion is easy to detect, but a small one is harder to judge. He adds that exclusions cannot simply be dropped, because some file formats contain checksums that must be updated after signing. He therefore proposes defining which bytes may be excluded in each format and requiring verifiers to enforce those limits.[^1]

An April analysis by researchers at the University of Maryland, Baltimore County (UMBC), Hacker Factor and the National Security Agency had already reported that the exclusion range enables undetectable alterations.[^3]

:::analysis
A valid signature and a trusted timestamp show only that the signed bytes have not changed since a given time. Whether those bytes include the image is a separate question. Version 2.4 appears to require validators to reject a whole-file exclusion like Buchanan's. So if his report is accurate, the tools he tried do not apply that rule. Anyone treating Content Credentials as evidence needs a validator that reports what the signature covers.
:::

:::checked
On 20 October 2026 we read Buchanan's post, version 2.4 of the C2PA specification (dated 1 April 2026) and the abstract of the April analysis. We did not download his image, inspect its manifest or run any C2PA validator, so the results he reports are his own.
:::
