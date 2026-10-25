---
title: How to read a remote attestation report
dek: A nine-step worksheet for deciding whether a service's hardware-signed evidence shows software and settings you are prepared to trust, before any data leaves your systems.
needs: the report, the vendor's certificates and published reference values
kind: guide
topics: [confidential-computing]
layers: [runtime, hardware]
published: 2026-10-20
agent: research
evidence: [documentation, report, announcement]
sources:
  - Remote ATtestation procedureS (RATS) Architecture (RFC 9334) | IETF | 2023-01 | https://www.rfc-editor.org/rfc/rfc9334
  - SEV Secure Nested Paging Firmware ABI Specification, Revision 1.59 | AMD | 2026-08-26 | https://docs.amd.com/v/u/en-US/56860_PUB_SEV_SNP
  - Versioned Chip Endorsement Key (VCEK) Certificate and KDS Interface Specification, Revision 1.05 | AMD | 2026-09-03 | https://docs.amd.com/v/u/en-US/57230
  - SEV-SNP Platform Attestation Using VirTEE/SEV, Revision 1.2 | AMD | 2023-07 | https://www.amd.com/content/dam/amd/en/documents/developer/58217-epyc-9004-ug-platform-attestation-using-virtee-snp.pdf
  - Intel Trust Domain Extensions Data Center Attestation Primitives (Intel TDX DCAP): Quote Generation Library and Quote Verification Library, Rev 0.91 | Intel | 2026-09 | https://download.01.org/intel-sgx/latest/dcap-latest/linux/docs/Intel_TDX_DCAP_Quoting_Library_API.pdf
  - Architecture Overview, NVIDIA Attestation Quick Start Guide | NVIDIA | 2026-10-06 | https://docs.nvidia.com/attestation/quick-start-guide/latest/architecture.html
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
  - Private Cloud Compute: A new frontier for AI privacy in the cloud | Apple Security Research | 2024-06-10 | https://security.apple.com/blog/private-cloud-compute/
  - DDRop: Active Memory Interposer Attacks on Confidential VMs by Dropping DDR5 Writes | DDRop researchers (KU Leuven, ETH Zurich, Durham University, Google) | 2026-09-14 | https://ddropattack.eu/
related: [remote-attestation-for-ai-workloads-explained, evaluating-a-verifiable-inference-claim, ddrop-ddr5-interposer-attack]
---

An attestation report is evidence that you must check against your own requirements before any data leaves your systems. In remote attestation, a machine produces hardware-signed evidence about its software and configuration so that a remote party can decide whether to trust it. Vendor tools can confirm that a report is genuine and that the platform's firmware is current. But judging the software the report records remains your task. For instance, Intel's verification library for Trust Domain Extensions (TDX) leaves it to the verifier to compare the measurements in a quote (Intel's signed report) with expected values.[^5] The nine checks below use field names from Intel TDX and AMD Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) as examples.

## When to use this guide

Use it when a service offers attestation evidence and you must decide whether to send it prompts, documents or model weights. Such a service runs in a trusted execution environment (TEE), where hardware is designed to isolate the workload from its host. In this guide, the workload is a whole virtual machine (VM). AMD SEV-SNP, for example, encrypts each VM's memory with its own key.[^3] Repeat the checks whenever the service releases new software or the vendor raises its minimum firmware versions.

In the terms of RFC 9334, the Internet Engineering Task Force (IETF) attestation architecture, the service is the attester. A verifier appraises its evidence against reference values. You, the relying party, apply your own policy to the verifier's result.[^1]

## What you need before you start

- **Evidence:** the report or quote and any certificates sent with it.
- **A verifier:** the vendor's library or service, with current collateral, meaning supporting data such as certificate revocation lists (CRLs).[^5]
- **Reference values:** the measurements the provider publishes for each release, also called known-good values.[^1]
- **A policy:** minimum firmware versions, accepted measurements, flags you reject, and what you will send if every check passes.

## Step 1: Identify the TEE technology and each attester

Identify each attester and its TEE technology, because each technology has its own evidence format and verification tools.[^2, 5] An AI service may add evidence from its graphics processing units (GPUs). NVIDIA's verifiers compare GPU evidence with reference measurements from signed manifests, and an Online Certificate Status Protocol (OCSP) service checks the certificates for revocation.[^6]

- [ ] Name the technology and processor generation behind each report
- [ ] Obtain each verifier from the vendor or another source you have vetted

## Step 2: Verify the signature chain to the vendor's root

Check that the report's signature chains to a key the vendor controls. Otherwise, the report does not count as evidence. An SEV-SNP report's SIGNING_KEY field identifies the key that signed it, such as the chip's Versioned Chip Endorsement Key (VCEK).[^2] AMD's Key Distribution System (KDS) serves VCEK certificates and the chain behind them: the AMD Root Key (ARK) issues the AMD SEV Key (ASK), which issues the VCEK certificate.[^3] For TDX, Intel's library checks the Provisioning Certification Key (PCK) certificate chain and the quote's signature.[^5]

- [ ] The chain ends at a root certificate obtained from the vendor
- [ ] The signature verifies; an SEV-SNP SIGNATURE field filled with zeroes means the report is unsigned[^2]
- [ ] The report's CHIP_ID matches the identifier used to fetch the VCEK[^2, 4]

## Step 3: Check firmware versions against revocation data

Check the versions of the trusted computing base (TCB), the set of components the protection depends on. AMD defines a TCB version as a combination of component versions, such as SNP firmware and processor microcode. AMD raises the minimum patch level when it fixes vulnerabilities. Each VCEK is unique to a chip running a specific TCB version.[^3] A report's REPORTED_TCB names the version used to derive the key that signed it.[^2] AMD's guide compares these values with those in the VCEK certificate.[^4]

Trail of Bits found that WhatsApp's Private Processing system originally trusted the patch level the firmware claimed. Meta's fix instead reads the patch level from the VCEK certificate and enforces a minimum.[^7]

For TDX, Intel's library returns a verification result such as OK, OUT_OF_DATE or REVOKED. Intel also describes policies that accept an out-of-date platform for a grace period.[^5]

- [ ] Take version numbers from vendor-signed data and compare them with your minimums
- [ ] Check the vendor's CRL, such as the one AMD's KDS publishes for each product,[^3] and the age of the collateral
- [ ] Decide in advance whether to accept an out-of-date status, and for how long

## Step 4: Compare measurements with published reference values

Compare the measurements with published reference values. A measurement is a cryptographic hash of code or data, recorded as it loads. SEV-SNP's MEASUREMENT is a hash that the firmware computes at launch, as the hypervisor (the software that manages virtual machines) loads data into the VM's memory.[^2] In TDX, a protected VM is called a trust domain. MRTD covers the trust domain's initial contents. By convention, four runtime registers, RTMR0 to RTMR3, hold measurements taken later by the virtual firmware, the operating system and the runtime.[^5]

Reference values tie each hash to a release that you or others can inspect. In Apple's Private Cloud Compute design, a device encrypts its request only for nodes whose attested measurements match a release in a public, append-only transparency log.[^8]

- [ ] Every measurement field your policy relies on has an expected value
- [ ] Each expected value traces to an auditable source, such as a reproducible build or an append-only log, and to a named release

## Step 5: Confirm the report is fresh

Send a nonce, an unpredictable value used once, and check that the signed report contains it. A valid report from last week says nothing about the machine today. Under the nonce approach in RFC 9334, the appraising party sends the nonce, and the attester includes it in the signed evidence. A match shows that the claims were signed after the nonce was generated.[^1]

Both technologies offer a 64-byte field for such data. In SEV-SNP it is REPORT_DATA, which the firmware does not interpret.[^2] In TDX it is REPORTDATA, which Intel suggests can hold a verifier's nonce.[^5] WhatsApp's reports originally carried no client-supplied value, so an attacker who compromised a TEE once could have replayed its attestation indefinitely.[^7]

- [ ] Send a new, unpredictable nonce for each session
- [ ] Confirm that the report data contains it, directly or through a hash the provider documents
- [ ] Reject cached reports unless your policy sets a maximum age

## Step 6: Confirm the report is bound to your connection

Check that the report is tied to the connection you are about to use. Freshness shows a report is recent. Binding shows that your connection ends inside the attested environment. Intel notes that report data can carry a public key generated inside the trust domain for setting up a secure session.[^5] Meta's fix for WhatsApp placed the client_random value from the Transport Layer Security (TLS) handshake in each report, tying every report to one connection.[^7] Also ask how any GPU evidence is tied to your session. Without that tie, the GPU evidence could come from another machine.

- [ ] The report commits to the key or handshake value of your connection, and your client checks this before sending data
- [ ] Every report presented, including GPU evidence, is tied to the same session

## Step 7: Check debug and policy flags

Check the debug and policy flags even on a genuine, fresh report, because it can still describe an environment the host can inspect. SEV-SNP's POLICY field includes a DEBUG bit. It also includes a setting for whether a migration agent (software that helps move the VM to another machine) may be associated with the VM.[^2] In TDX, setting the DEBUG bit in TDATTRIBUTES lets the host access the trust domain's processor state and private memory. Intel advises against giving production secrets to a trust domain with any debug flag set.[^5]

- [ ] Debugging is disabled: POLICY.DEBUG for SEV-SNP and the TDATTRIBUTES debug flags for TDX are 0
- [ ] Other policy bits, such as migration agents and simultaneous multithreading (SMT), match your policy, and reserved fields are zero[^2]

## Step 8: List what the measurements leave out

List the inputs the service reads after launch. They stay unverified unless measured code records them or checks them against expected values. Trail of Bits found two such gaps in WhatsApp's system. First, environment variables came from configuration files read after the measurement. This would have let an insider load hostile code without changing the attestation. Second, the Advanced Configuration and Power Interface (ACPI) tables, which describe hardware to the operating system, were not measured. This would have let a malicious hypervisor declare rogue devices with access to protected memory.[^7] For an AI service, ask about model weights, adapters, system prompts and serving configuration.

- [ ] List the inputs loaded after launch and, for each, the mechanism that measures or verifies it, such as a hash built into the measured image or an entry in RTMR3
- [ ] Mark the remaining inputs unverified and decide whether that is acceptable for your data

## Step 9: Record the decision

Keep a record that lets you or an auditor reconstruct the decision. You need it because an attestation result reflects the policy, endorsements (usually vendor-signed statements about the hardware) and reference values in force when it was produced.[^1]

- [ ] Save the report, certificates, nonce and verifier output
- [ ] Record the verifier version, policy and reference values you applied
- [ ] Record the decision, the exceptions you accepted and what will trigger a new check, such as a new release

## A worked example

:::example Worked example (hypothetical): a contract-summarization service
A law firm is deciding whether to send contract drafts to an invented summarization service in an SEV-SNP VM. The provider logs a reference measurement for each release. Its documentation says that REPORT_DATA holds a SHA-512 hash of the client's nonce and the server's TLS public key. The firm's software receives this report:

```text
SIMPLIFIED, HYPOTHETICAL REPORT. Field names follow the AMD SEV-SNP
ABI specification; all values are invented and most fields are omitted.

POLICY         DEBUG=0  MIGRATE_MA=0  SMT=1
MEASUREMENT    5e1c...9a0f
REPORT_DATA    7d02...c4b1
REPORTED_TCB   BOOT_LOADER=9  TEE=0  SNP=23  MICROCODE=72
CHIP_ID        c81d...5577
SIGNING_KEY    VCEK
SIGNATURE      ECDSA signature by the chip's VCEK
```

The firm's checks show:

1. The signature and certificate chain verify up to the ARK the firm downloaded from AMD.
2. The VCEK certificate carries the same TCB values as the report, and they meet the firm's minimums. No certificate in the chain appears on AMD's CRL.
3. MEASUREMENT matches release 2026.10.2 in the provider's log.
4. The hash of the firm's nonce and the handshake's TLS key matches REPORT_DATA.
5. POLICY disallows debugging and migration agents and allows SMT, which the firm accepts.
6. The provider's documentation says the model weights are downloaded after boot, with no check against a fixed hash.

The firm records the result. It sends only non-confidential test documents until the provider builds a hash of the weights into the measured image.
:::

:::limits What a passing report does not establish
- A passing report shows which software genuine hardware launched, with which settings, and that your connection ends inside it. It does not show that the software is correct or keeps the provider's data-handling promises; that requires review of the code the measurements identify.
- You still trust the hardware itself and its vendor's keys, firmware and verification services. The DDRop researchers describe an attacker who controls the host's software and installs a small device on the memory bus during one brief visit. They report that this attacker can make a rogue Intel TDX VM pass remote attestation by overwriting its launch measurement with a legitimate one. They say Intel and AMD consider physical attacks on main memory out of scope for their current products.[^9]
- The report does not cover logging, storage or other systems outside the attested environment.
:::
