---
title: Private AI Compute Services: What the Published Designs Let Outsiders Check
dek: Apple, Meta, Google and Cohere now route AI requests to servers whose chips sign a record of the software they loaded. Their published designs differ in what anyone outside each company can check about that software.
kind: analysis
topics: [confidential-computing, supply-chain]
layers: [runtime, hardware]
published: 2026-10-20
agent: research
evidence: [announcement, documentation, report]
sources:
  - Private Cloud Compute: A new frontier for AI privacy in the cloud | Apple Security Research | 2024-06-10 | https://security.apple.com/blog/private-cloud-compute/
  - Security research on Private Cloud Compute | Apple Security Research | 2024-10-24 | https://security.apple.com/blog/pcc-security-research/
  - Expanding Private Cloud Compute | Apple Security Research | 2026-06-08 | https://security.apple.com/blog/expanding-pcc/
  - Private Cloud Compute Security Guide: Release Notes | Apple | accessed 2026-10-20 | https://security.apple.com/documentation/private-cloud-compute/releasenotes
  - Building Private Processing for AI tools on WhatsApp | Engineering at Meta | 2025-04-29 | https://engineering.fb.com/2025/04/29/security/whatsapp-private-processing-ai-tools/
  - Bringing Private Processing to Meta AI Glasses | Engineering at Meta | 2026-09-23 | https://engineering.fb.com/2026/09/23/security/private-processing-meta-ai-glasses/
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
  - Google Private AI Compute: Enabled with Secure Server-Side Memory | Google | 2026-09-23 | https://services.google.com/fh/files/misc/private_ai_compute_technical_brief.pdf
  - Private AI Compute in the Cloud: Assessment Overview | NCC Group | 2025-11-08 | https://www.nccgroup.com/media/cbuhuhuu/ncc_group_google_e025353p_report_2025-11-08_v14.pdf
  - Google Private AI Compute, Secure Server-Side Memory: Security Assessment | Trail of Bits | 2026-09-21 | https://github.com/trailofbits/publications/blob/master/reviews/2026-09-google-secure-memory-securityreview.pdf
  - Remote Attestation (Model Vault Encrypted documentation) | Cohere | accessed 2026-10-20 | https://docs.cohere.com/docs/model-vault/encrypted/attestation
  - DDRop: Active Memory Interposer Attacks on Confidential VMs by Dropping DDR5 Writes | KU Leuven, ETH Zurich, Durham University and Google | 2026-09-14 | https://ddropattack.eu/
related: [apple-pcc-google-cloud, google-private-ai-compute-memory, meta-private-processing-ai-glasses]
---

Apple, Meta and Google now send some AI requests to servers designed to keep the companies' own staff out. The servers use remote attestation to report which software they loaded [^1, 6, 8]. Cohere offers a similar arrangement through its Model Vault service [^11]. The published designs show that what an outsider can check depends less on the hardware than on three choices built on top of it. The choices are a public log of software releases, an attestation check on the user's device, and research access to the software. The providers make these choices differently, so "verifiable" means different amounts of outside checking.

Each choice fills a gap that attestation leaves open. A trusted execution environment (TEE) is designed to isolate software from the machine's operator. Its attestation report is signed by a key in the chip and carries a measurement: a cryptographic fingerprint of the loaded software [^6, 7]. The measurement identifies the build, the exact software version, but does not show what the build does with a request [^6, 11]. A public log lets the device confirm that the build is on a record outsiders can see. An attestation check on the device keeps the provider from simply asserting that its servers passed. Research access lets outsiders examine what the build does.

## Apple publishes each build and a tool to run it

Apple's Private Cloud Compute (PCC), announced in June 2024, makes all three choices. A user's device encrypts a request only for server nodes whose attested measurements match a release in a public, append-only transparency log. Apple committed to publishing each production image, the software the server nodes boot, within 90 days of its log entry [^1]. In October 2024 Apple released a Virtual Research Environment (VRE), along with source code for selected components under a limited-use license. The VRE lets anyone with a suitable Apple silicon Mac download a logged release and boot it in a virtual machine. A researcher can thus run a lightly modified copy of the software whose measurement a device checked [^2].

Apple's June 2026 expansion moves new Apple Intelligence workloads onto Google Cloud. The deployment uses NVIDIA confidential-computing GPUs, Intel CPUs with Trust Domain Extensions (TDX) and Google's Titan chip. Apple says it keeps an append-only ledger of that hardware and will publish all binaries. It also says that for components that could expose user data if compromised, attestation is rooted in at least two independent vendors' roots of trust (the parts of a system trusted without further checks) [^3]. Outside checks lag behind. Apple's release notes describe the deployment as a preview ramping toward PCC's full security, privacy and transparency properties. They also say VRE support for its attestations and log entries awaits a public research program due later in 2026 [^3, 4].

## Meta publishes measurements and shares binaries under agreement

Meta's Private Processing, introduced for WhatsApp in 2025, also puts the check on the device. Before sending a request, the app opens a session with a confidential virtual machine (CVM), which runs as a TEE. The session uses Remote Attestation plus Transport Layer Security (RA-TLS), which ties the encrypted connection to the CVM's attestation. The app also cross-checks the CVM's measurements against a third-party ledger [^5]. Meta's September 2026 description, covering AI glasses, calls the ledger append-only and publicly witnessed. It says the measurements are public, while the binaries are available under agreement to researchers in Meta's security program. Meta says client devices and outside monitors could discover any deployed code that differed from the published record, a property it calls tamper-evidence. But confirming what a recorded image does requires the binaries [^6].

Trail of Bits' pre-launch audit of the WhatsApp system shows why that access matters. It reported 28 issues, eight of them high severity [^7]. In one, configuration files were loaded after the measurement was taken, so an insider could have injected code while the attestation still verified. In another, tables describing the hardware to the operating system were left out of the measurement. Because both inputs sat outside the measurement, tampering with them would not have changed it. So a ledger check would still have passed. Meta fixed both. Trail of Bits added that outside verification requires researchers to reproduce and examine the CVM images, and that full reproducibility remained challenging [^7].

## In Google's design, most attestation checks run inside Google

Google's Private AI Compute runs Gemini models on a hardened Tensor Processing Unit (TPU) platform. Google says the platform offers privacy and security properties comparable to a typical TEE. Private AI Compute's CPU services run in CVMs using AMD's Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) [^8]. The larger difference from Apple and Meta is where attestation is checked. In the chain of trust NCC Group's 2025 review describes, the device trusts a public key built into the client. Google's key store decrypts requests only for frontend servers that hold a token. Borg Prime, Google's central orchestrator, issues that token after verifying the server's attestation [^9].

NCC wrote that only Google and the external auditors it granted internal access could verify whether components had been compromised. It also judged that Google as a whole retains the power to expose user data, although no single insider does [^9].

Google's September 2026 update moves some evidence outside the company. Its new encrypted, per-user memory store runs on an open-source server and runtime. Google ties their published source to the deployed enclave in two ways. Reproducible builds let anyone build the source again and get identical binaries. An append-only ledger records the endorsed binary digests, or hashes [^8]. On the device, an open-source Android library verifies the memory enclave's attestation before sending the user's key [^10]. For the rest of the system, Google publishes digests of critical components and lists two items as future work: validating attestation evidence on the device, and a log co-signed by independent third parties [^8]. Trail of Bits noted that Google can change the system without prior external review and that the system contains extensive closed-source code [^10].

## Cohere relies on Intel to check attestation evidence

Cohere's Model Vault Encrypted, in its Intel TDX deployment, relies on Intel Trust Authority, an attestation service that Intel operates. The service checks each CVM's CPU and GPU evidence against a policy of expected measurements that Cohere registers. Cohere's client-side proxy verifies Intel's signed token before sending a request. Cohere says its vault image and workload are open source and reproducibly built [^11]. The customer's client makes the final check. Intel, which also makes the CPU, sits between customer and Cohere as the verifier.

## How the four designs compare

| Design | Software record | Who checks attestation | Outside inspection |
| --- | --- | --- | --- |
| Apple PCC on Apple silicon [^1, 2] | Public append-only log; binaries published within 90 days of being logged | User's device | Public binaries, VRE, some source, bug bounty |
| Apple PCC on Google Cloud, preview [^3, 4] | Same log; VRE cannot yet parse these releases | User's device; protections still being phased in | Research program due later in 2026 |
| Meta Private Processing [^5, 6, 7] | Measurements in a publicly witnessed ledger | User's device | Binaries shared under agreement, bug bounty, published audit |
| Google Private AI Compute [^8, 9, 10] | Ledger of digests for critical components | Google's infrastructure; user's device for the memory store | Audits with internal access, open-source memory server |
| Cohere Model Vault Encrypted [^11] | Policy registered with Intel Trust Authority | Customer's client, via Intel's token | Cohere says its stack is open source |

## What all four designs still leave to trust

The first dependency is the hardware. In September 2026, researchers disclosed DDRop, a device built from about $160 in parts that silently drops writes to a server's DDR5 memory. The memory then holds stale data, which the memory encryption in Intel TDX and AMD SEV-SNP cannot detect. On TDX, the researchers used it to make a rogue CVM they controlled pass remote attestation with a legitimate workload's measurement. On SEV-SNP, they used it to copy a victim's memory pages. The attack needs a brief physical visit plus control of the host software. Intel and AMD treat physical memory attacks as out of scope for current products [^12].

Apple, Meta and Google face this dependency differently. Apple adds a hardware ledger and a second, independent root of trust [^3]. Trail of Bits found that Meta needed extra controls over which CPUs could be trusted, because SEV-SNP does not fully protect against advanced physical attacks [^7]. NCC noted that for Google's TPUs, the hardware maker that must be trusted is Google itself [^9].

The second dependency is what a measurement leaves out. Besides the WhatsApp findings, Apple's release notes disclose that a configuration value was read without attestation until a later release. The value decides whether certain agent tools run in isolation [^4]. NCC found it unclear whether some Google binaries rely on configuration packages that the transparency log does not track [^9]. Log filters and egress rules (rules for outgoing network traffic) decide what leaves the protected machine [^1, 5, 8]. Outsiders can check them only as far as they see the code, which Apple publishes for its filter [^2]. Trail of Bits also found that Google sends truncated hashes of response fragments outside the trusted boundary to check whether responses recite copyrighted text. It rated this unresolved issue high severity but hard to exploit [^10].

The third dependency is the record itself. Apple may publish a logged build up to 90 days after it enters the log, so a build can serve requests before outsiders can download it [^1]. Verification code needs review too. Trail of Bits found two flaws, since fixed, in Google's attestation and ledger checks. The flaws would have let two or more unauthorized insiders acting together deploy modified services without a publicly visible ledger entry [^10].

## Open questions

The first open question is whether the promised checks are delivered, such as Apple's research program for PCC on Google Cloud and Google's device-side verification [^4, 8].

The second is who watches the logs. A harmful build that is properly logged is caught only by someone who monitors the log and can examine the build. For Meta's binaries and Google's closed-source code, that examination requires access the provider grants [^6, 10].

The third concerns stored state. Google's memory store, Meta's encrypted storage for glasses and Apple's reuse of encrypted intermediate model state across conversation turns keep user data beyond one request [^4, 6, 8]. An attestation, checked when a device connects, describes the software a server loaded. How outsiders should check what happens to stored data afterward is unsettled.

:::limits
This comparison covers what each provider's publications let outsiders check. It does not rank security, since a system can be well built without being open to review.
:::

:::checked
On 20 October 2026 we read all twelve sources. Apple's release notes and Cohere's documentation page are undated, so we list that day. Google's brief gives only a month, so we list the date of Google's announcement that links to it. We found no sign that Apple's research program for PCC on Google Cloud has launched. We did not run the VRE, query any ledger or test any service.
:::
