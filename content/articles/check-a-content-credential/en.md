---
title: How to check a Content Credential, and what it does not show
dek: Before you publish or cite an image or video, use this six-step worksheet to decide what its C2PA manifest establishes: who signed which claims, and which bytes those claims cover.
needs: the file as you received it, a C2PA validator and the C2PA trust lists
kind: guide
topics: [content-provenance]
layers: [outputs]
published: 2026-10-20
agent: research
evidence: [standard, documentation, paper, report, announcement]
related: [c2pa-exclusion-range-backdated-image, c2pa-security-analysis-umbc, google-synthid-detector-public]
sources:
  - "Content Credentials: C2PA Technical Specification, Version 2.4 | C2PA | 2026-04-01 | https://spec.c2pa.org/specifications/specifications/2.4/specs/C2PA_Specification.html"
  - Using C2PA Tool | Content Authenticity Initiative | accessed 2026-10-20 | https://opensource.contentauthenticity.org/docs/sdk-repos/c2patool/docs/usage/
  - Trust lists | Content Authenticity Initiative | accessed 2026-10-20 | https://opensource.contentauthenticity.org/docs/conformance/trust-lists
  - C2PA Conformance Program, Version 0.2 | C2PA | 2026-07-31 | https://github.com/c2pa-org/conformance-public/blob/main/docs/v0.2/C2PA%20Conformance%20Program.md
  - How to Hack Time, With C2PA | David Buchanan | 2026-10-02 | https://www.da.vidbuchanan.co.uk/blog/hacking-time.html
  - "Verifying Provenance of Digital Media: Security Analysis of C2PA and its Implementation | IACR Cryptology ePrint Archive (Golaszewski et al.) | 2026-04-23 | https://eprint.iacr.org/2026/804"
  - "Verifying Provenance of Digital Media: Why the C2PA Specifications Fall Short | arXiv (Golaszewski et al.) | 2026-04-27 | https://arxiv.org/abs/2604.24890"
  - C2PA Cameras Do Not Survive Contact With Reality | David Buchanan | 2026-08-25 | https://www.da.vidbuchanan.co.uk/blog/android-c2pa.html
  - Durable Content Credentials | Content Authenticity Initiative | 2024-04-08 | https://contentauthenticity.org/blog/durable-content-credentials
  - Google expands SynthID Detector for AI content | Google | 2026-10-07 | https://blog.google/innovation-and-ai/models-and-research/google-deepmind/synth-id-ai-content/
---

A Content Credential that validates shows which certificate holder signed a set of claims about a file, and which of the file's bytes those claims cover. The person relying on the claims still has to judge whether they are true.[^1] Content Credentials are manifests specified by the Coalition for Content Provenance and Authenticity (C2PA). A manifest lists statements about an asset, called assertions, in a claim that the signer signs.[^1] Run the six checks below before you rely on a credential to publish, cite or label an image or video.

## What you need

- **A validator**, such as c2patool, an open-source command-line tool documented by the Content Authenticity Initiative (CAI).[^2] The CAI's documentation says the Verify tool at verify.contentauthenticity.org checks signers against a legacy interim trust list instead of the C2PA trust lists.[^2, 3]
- **The file** as you received it, with any separate `.c2pa` manifest file, which c2patool reads with `--external-manifest`.[^2] A re-encoded or resized copy cannot match the manifest's hard binding, which is a cryptographic hash of the original asset's bytes.[^1]
- **The C2PA trust lists.** One names the certification authorities (CAs) that issue signing certificates to conforming products. The other names the CAs that issue certificates to time-stamping authorities (TSAs). Both are in the C2PA's conformance-public repository on GitHub.[^3]

## Step 1: Confirm that a manifest is present and validates

The specification defines three manifest states, each requiring the one before:[^1]

| State | What validation has confirmed |
| --- | --- |
| Well-formed | The manifest and its assertions meet the specification's requirements |
| Valid | The signature verifies; the certificate was within its validity period and is not reported as revoked |
| Trusted | The certificate also chains to a trust anchor, a CA certificate that the validator accepts; or the user has added it to the validator's private credential store |

The asset is valid only if the hashed bytes are also unchanged. If the manifest is valid, you can attribute its claim to the claim generator: the hardware or software named in `claim_generator_info`.[^1] In c2patool, `--info` reports whether the manifest validated, and the plain command prints the manifest data.[^2]

```bash
c2patool image.jpg --info
c2patool image.jpg
```

- [ ] The claim signature validates (`claimSignature.validated`)
- [ ] The hard binding matches the file, for example `assertion.dataHash.match`
- [ ] Record the claim generator and any failure codes

## Step 2: Identify the signer and check it against the C2PA trust list

Find the signer: the holder of the signing certificate, identified by its subject.[^1] In the C2PA conformance program, the signer is always an instance of a generator product, a system that produces assets with manifests. CAs on the C2PA trust list may issue signing certificates only to conforming products.[^4] Each certificate names the product and records an assurance level, currently 1 or 2, reflecting the security requirements the product met.[^4] A credential trusted against this list therefore names a product, such as a camera app.

The `--certs` option prints the certificate chain, and the `trust` subcommand checks it against the list passed with `--trust_anchors`.[^2] If the chain reaches no accepted trust anchor, the validator reports `signingCredential.untrusted`.[^1]

```bash
c2patool image.jpg --certs
c2patool image.jpg trust --trust_anchors='https://raw.githubusercontent.com/c2pa-org/conformance-public/refs/heads/main/trust-list/C2PA-TRUST-LIST.pem'
```

Both the program and conforming validators have documented gaps. An April 2026 security analysis led by researchers at the University of Maryland, Baltimore County (UMBC) says version 0.1 of the program certified products without technical review.[^6] Version 0.2 has been the only version accepting applicants since 9 October 2026. It requires sample output files and a second approver for each record.[^4] The UMBC-led authors also found two conforming validators that did not report Nikon's November 2025 revocation of a camera's certificate.[^7] The specification says online validators should attempt a revocation check.[^1]

- [ ] Record the certificate's subject, issuer, validity dates and assurance level
- [ ] Check the chain against the C2PA trust list, and note when you fetched the list
- [ ] Record whether the validator checked revocation

## Step 3: Separate what the signer asserts from other data

Sort what the validator displays, because only part of it is attributed to the signer. Created assertions are attributed to the signer. Gathered assertions come from other parts of the workflow, such as a person typing in details. They are signed as part of the claim but are not attributed to the signer.[^1] Metadata outside the manifest, such as Exchangeable Image File Format (EXIF) fields, is not attributed to the signer even when hashed. The exception is metadata copied into a `c2pa.metadata` assertion among the created assertions.[^1]

The actions assertion declares what was done to the asset. For a new asset, the first action is `c2pa.created`, with a digital source type such as `trainedAlgorithmicMedia` for output from a generative AI model. For an edited asset, the first action is `c2pa.opened`, with an ingredient assertion that describes the original.[^1] Version 2.4 of the specification adds a `c2pa.ai-disclosure` assertion for details such as the type of model.[^1] Unless `allActionsIncluded` is true, other actions may have gone unrecorded.[^1]

- [ ] List the created assertions, with each action and its digital source type
- [ ] List gathered assertions separately as unattributed
- [ ] Mark displayed metadata outside the manifest, such as location, as unsigned
- [ ] Record the validation result of each ingredient's manifest

## Step 4: Find the bytes the hash leaves out

A hash match protects only the bytes it covers, so list the exclusion ranges: the byte ranges that the hash leaves out. One range holds the manifest, and the specification allows others only for asset metadata. The claim generator must ensure that whatever an attacker writes there cannot materially change how the asset is interpreted.[^1] Validators must reject a manifest if the range holding it contains other data. They must flag extra ranges with an informational code such as `assertion.dataHash.additionalExclusionsPresent`.[^1]

The UMBC-led authors report that a Pixel 10 Pro stored location data in an exclusion range. They also report that a conforming validator did not detect their change to that data.[^7] On 2 October 2026, security researcher David Buchanan published an image with a single exclusion range that spanned the whole file. He said the image's signature was valid but protected none of the file, and that no verification tool he could find flagged it. He showed the range with c2patool's detailed report.[^2, 5]

```bash
c2patool image.jpg -d
```

- [ ] List the exclusion ranges in the hard-binding assertion (`c2pa.hash.data`, `c2pa.hash.boxes` or `c2pa.hash.bmff.v3`)
- [ ] Compare each range with the file size; a whole-file range protects nothing
- [ ] Identify what each extra range holds, and treat it as unprotected

## Step 5: Check the time-stamp against the TSA trust list

Look for a TSA time-stamp, the only source of a trusted time for a manifest. The TSA countersigns the claim signature, which shows that the signature existed at the attested time. Times written by the claim generator, such as an action's `when` field, are untrusted.[^1] The validator must chain the TSA's certificate to its TSA trust anchors, which include the C2PA TSA trust list. If it cannot, it reports `timeStamp.untrusted` and ignores the time-stamp.[^1]

With a trusted time-stamp, the validator judges the certificate's validity at the attested time. The credential therefore still validates if the certificate expires or is revoked after that time.[^1, 3] Without one, an unchanged file stops validating once the certificate expires.[^1, 7]

Even a trusted time-stamp dates only the signature. Buchanan says he edited the winning numbers into his image after a lottery draw. According to him, its trusted time-stamp from hours before the draw remained valid, because the signature covered none of the image.[^5] The UMBC-led authors add that nothing in the signed data refers to the time-stamp, so it can be removed and replaced without detection.[^7]

- [ ] Confirm `timeStamp.trusted` and record the attested time
- [ ] Check that the validator's TSA trust anchors include the C2PA TSA trust list
- [ ] Without a trusted time-stamp, record the certificate's expiry date
- [ ] Read the attested time as the time by which the signature existed

## Step 6: If the credential is missing, look for soft bindings and watermarks

Do not treat a missing manifest as evidence about a file's origin, because metadata can be removed deliberately or accidentally.[^9] Soft bindings can lead back to the manifest. A soft binding is an identifier computed from the content, such as a fingerprint, or embedded in the content as an invisible watermark. It can therefore match a copy whose bytes differ.[^1]

If the original manifest recorded a soft binding and a copy is stored in a manifest repository, the binding can locate that copy. The matcher must then confirm that every soft binding in the recovered manifest matches those used in the search.[^1] The CAI adds a fingerprint check that the content matches the recovered manifest. It notes that watermarks can be removed or spoofed, and that fingerprint matches are never certain.[^9]

A watermark detector covers only generators that embed its watermark. Google opened its SynthID Detector to everyone on 7 October 2026. Google says the detector checks whether an image, video or audio file was made with AI from Google or from partners including OpenAI, NVIDIA and Kakao.[^10] A negative result therefore says nothing about other generators, as our [brief on the detector](/articles/google-synthid-detector-public/) notes.

- [ ] Ask the source for the original file, and validate any recovered manifest with Steps 1 to 5
- [ ] Record each detector result with the detector's stated coverage
- [ ] Do not read a missing credential or a negative detector result as evidence either way

## A worked example

:::example Worked example (hypothetical): a photo of a flooded street
A newsroom receives a reader's photo said to show a flooded street that morning. An editor checks it with c2patool and the C2PA trust list:

```text
SIMPLIFIED SUMMARY. Names and values are invented.

Signer          ExampleCam 6.1; issuing CA on the C2PA trust list
First action    c2pa.created, digitalCapture
Hard binding    c2pa.hash.data, two exclusion ranges
Success         claimSignature.validated, signingCredential.trusted,
                timeStamp.trusted (08:12), assertion.dataHash.match
Informational   assertion.dataHash.additionalExclusionsPresent
```

The hashed bytes are unchanged. The signer is the camera app, and its certificate says nothing about who held the phone. The second exclusion range covers the EXIF block. So the location and capture time shown in the newsroom's software are neither hashed nor attributed to the signer.

The credential supports one statement: an instance of ExampleCam signed a capture claim for these pixels by 08:12. Before publishing, the newsroom checks the location with the reader and against independent images of the street.
:::

:::limits What a valid credential does not establish
- The specification's trust model covers the signer's identity and leaves the truth of the signed claims to the person relying on them.[^1]
- A signer with a valid certificate can sign false claims. In August 2026, Buchanan reported using root access to a Pixel phone to have the Pixel Camera app's hardware-protected keys sign an AI-generated image as an unedited photograph.[^8]
- The UMBC-led authors found that conforming validators can disagree about the same file, so record which validator and trust lists you used.[^7]
:::
