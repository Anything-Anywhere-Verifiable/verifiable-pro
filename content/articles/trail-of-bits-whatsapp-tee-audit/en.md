---
title: Trail of Bits Reports 28 Findings from Its Pre-Launch Audit of WhatsApp Private Processing
dek: On 7 April 2026, Trail of Bits published lessons from its review of the system Meta built to run WhatsApp AI features inside trusted execution environments. Several flaws it describes would have let attestation pass while the software handling user data differed from what clients expected.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-04-07
published: 2026-10-20
agent: daily
evidence: [report]
sources:
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
  - Meta WhatsApp Private Processing, Security Assessment with Fix Review | Trail of Bits | 2025-08-26 | https://github.com/trailofbits/publications/blob/master/reviews/2025-08-meta-whatsapp-privateprocessing-securityreview.pdf
related: [meta-private-processing-ai-glasses]
---

Trail of Bits published lessons on 7 April 2026 from its pre-launch security audit of WhatsApp's Private Processing. Meta built the system to run AI features, such as message summarization, on end-to-end encrypted chats. The system processes messages inside trusted execution environments (TEEs) based on AMD Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) and NVIDIA confidential GPUs. TEEs are hardware-isolated environments designed to protect the code and data inside them. Trail of Bits says it found 28 issues, eight rated high severity. It says Meta patched the vulnerabilities that compromised WhatsApp's privacy model.[^1]

Two high-severity findings involved data outside the attestation measurement, the checksum of the TEE's code that clients check before connecting.[^1, 2] Configuration files containing environment variables were loaded after the measurement was taken. A malicious insider could therefore have injected code while attestation still passed. Meta now validates those variables. Advanced Configuration and Power Interface (ACPI) tables, the hardware description a virtual machine reads at boot, were left out of the measurement. That omission would let a malicious hypervisor, the software that manages virtual machines, define fake devices with access to protected memory. Meta now verifies the tables in a custom bootloader, so tampering changes the measurement.[^1]

Two other high-severity findings concerned how the client checked attestations.[^1, 2] The client trusted the firmware patch level that the firmware itself reported instead of checking it against AMD's signed certificate, which it now does. Attestation reports also carried no timestamp or client-supplied random value, so an attacker who compromised a TEE once could replay its report indefinitely. Meta now includes the TLS `client_random` nonce in each report.[^1]

The final report, dated 26 August 2025, records that Meta resolved 16 issues, partially resolved four and left eight unresolved. The partially resolved findings include two rated high: attestation that is not bound to Meta-specific machines, and confidential virtual machine images that are not yet fully reproducible.[^2] Trail of Bits says the eight unresolved issues are rated low or informational.[^1, 2]

:::analysis
In each highlighted flaw, an attestation report could pass verification while the code or machine handling user data differed from what the report described. An attestation is therefore only as meaningful as what it measures and what it is bound to. The partially resolved reproducibility finding matters for outside verification, because researchers can tie a published measurement to inspectable code only if they can rebuild the image.
:::

:::checked
On 20 October 2026 we opened the Trail of Bits post of 7 April 2026 and the public audit report it links. The report records fix reviews from April to August 2025, so it does not cover later changes to the system. We did not verify Meta's fixes or examine the current deployment, and we test no systems ourselves.
:::
