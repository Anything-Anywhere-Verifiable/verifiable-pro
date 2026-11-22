---
title: "Confidential Containers Releases Trustee v0.23.0 With Verifier Changes"
dek: "The release notes list changes to reference values, TPM verification and resource-policy responses. Operators will need to check how the breaking changes apply to their deployments."
kind: news
topics: [confidential-computing]
layers: [runtime]
event_date: 2026-11-17
published: 2026-11-17
agent: daily
evidence: [code, announcement]
sources:
  - "Trustee v0.23.0: official release notes | Confidential Containers | 2026-11-17 | https://github.com/confidential-containers/trustee/releases/tag/v0.23.0"
---

Confidential Containers published Trustee v0.23.0 on 17 November 2026, describing it as the version used with Confidential Containers (CoCo) v0.24.0. Its release notes list changes to verification, reference values and resource handling, including several that affect interfaces or installation and distribution.[^1]

Among the breaking changes, the notes say the reference value provider service (RVPS) no longer returns expired reference values, and the Trusted Platform Module (TPM) verifier requires a full platform configuration register (PCR) bank. They also list a change to keep the Intel Data Center Attestation Primitives verifier's PIID in Intel's native byte order. The notes give the change titles but do not explain their effects on individual deployments.[^1]

For the key broker service (KBS), the release lists HTTP 403 for resource-policy denial and HTTP 404 when a plugin reports a missing resource. It also lists timeouts for remote fetches and documentation of rate limiting for the `/kbs/v0/auth` endpoint. Separately, the release says Arm Confidential Compute Architecture (CCA) was added to the default CPU policy and its RIM is compared as hexadecimal.[^1]

:::analysis
These changes sit at T2, the runtime layer: a verifier's assessment depends on the verification software, reference values and policy configured for the deployment. The release notes identify changes; a user or verifier still has to trust that the deployed system uses the stated version and configuration unless those details can be checked. Identifiability is the property at stake: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed to a particular affected behavior, provided its scope is known. Operators should check their deployed version, verifier, reference values and policies against the listed changes; the notes do not recommend a fixed version for a specific vulnerability or establish exposure criteria.[^1]
:::

:::checked
On 17 November 2026 we read the saved official [Trustee v0.23.0 release notes](https://github.com/confidential-containers/trustee/releases/tag/v0.23.0). We did not test Trustee, inspect the linked changes or verify any deployment. The notes alone do not establish how these changes behave in a particular system.[^1]
:::
