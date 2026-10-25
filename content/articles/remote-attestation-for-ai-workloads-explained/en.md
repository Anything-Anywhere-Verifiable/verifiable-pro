---
title: Remote attestation for AI workloads, explained
dek: Before a client sends a prompt or a model owner releases its weights, remote attestation can show which software a machine loaded and on what hardware. This explainer shows how that evidence is produced and checked, including on GPUs, and what a valid report leaves open.
kind: explainer
topics: [confidential-computing]
layers: [runtime, hardware]
published: 2026-10-20
agent: research
evidence: [standard, documentation, report, announcement]
disclosure: The software that researched and drafted this explainer is built on Anthropic's Claude models. This explainer describes Anthropic's published confidential inference design.
sources:
  - Remote ATtestation procedureS (RATS) Architecture (RFC 9334) | IETF | 2023-01 | https://www.rfc-editor.org/rfc/rfc9334
  - Intel Trust Domain Extensions (white paper) | Intel | 2025-06 | https://cdrdv2-public.intel.com/856790/Intel%20Trust%20Domain%20Extensions%20Overview%20-%20June%202025.pdf
  - AMD SEV-SNP: Strengthening VM Isolation with Integrity Protection and More | AMD | 2020-01 | https://docs.amd.com/v/u/en-US/SEV-SNP-strengthening-vm-isolation-with-integrity-protection-and-more
  - Confidential Computing on NVIDIA H100 GPUs for Secure and Trustworthy AI | NVIDIA Technical Blog | 2023-08-03 | https://developer.nvidia.com/blog/confidential-computing-on-h100-gpus-for-secure-and-trustworthy-ai/
  - Architecture Overview, NVIDIA Attestation Quick Start Guide | NVIDIA | 2026-10-06 | https://docs.nvidia.com/attestation/quick-start-guide/latest/architecture.html
  - RIM Service introduction, NVIDIA Attestation Cloud Services | NVIDIA | 2026-10-06 | https://docs.nvidia.com/attestation/cloud-services/latest/rim/rim_introduction.html
  - What we learned about TEE security from auditing WhatsApp's Private Inference | Trail of Bits | 2026-04-07 | https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/
  - Private Cloud Compute: A new frontier for AI privacy in the cloud | Apple Security Research | 2024-06-10 | https://security.apple.com/blog/private-cloud-compute/
  - Confidential Space attestation token claims | Google Cloud | 2026-10-13 | https://docs.cloud.google.com/confidential-computing/confidential-space/docs/reference/token-claims
  - Confidential Inference via Trusted Virtual Machines | Anthropic | 2025-06-18 | https://www.anthropic.com/research/confidential-inference-trusted-vms
  - DDRop: Active Memory Interposer Attacks on Confidential VMs by Dropping DDR5 Writes (project site) | DDRop researchers (KU Leuven, ETH Zurich, Durham University, Google) | 2026-09-14 | https://ddropattack.eu/
related: [how-to-read-a-remote-attestation-report, private-ai-compute-published-designs, ddrop-ddr5-interposer-attack]
---

Remote attestation lets one party obtain hardware-signed evidence about another machine's software state before trusting it with data or work.[^1, 2] For AI workloads, a user's device may want to know which software will receive a prompt before encrypting it, and a model owner may want the same evidence before releasing the key that decrypts its weights.[^1, 8] The evidence comes from a trusted execution environment (TEE). A TEE is a hardware-isolated execution mode of a processor that records what it loads and signs a report about it.[^2, 3] A valid report tells that party what was loaded and on which hardware. It does not show that the loaded software behaves as its operator says.

## The roles defined in RFC 9334

The Internet Engineering Task Force (IETF) published the Remote ATtestation procedureS (RATS) architecture as RFC 9334. The architecture names the roles independently of any processor or protocol.[^1] The third column is our illustration.

| Role | What it does | Typical party in an AI service |
| --- | --- | --- |
| Attester | Produces evidence: claims such as measurements and configuration | The confidential virtual machine (VM) and the graphics processing units (GPUs) that run the model |
| Verifier | Appraises evidence against reference values, endorsements and an appraisal policy, then issues an attestation result | A vendor's attestation service, or a library in the client |
| Relying party | Uses the attestation result to make its own decision | The user's client, or a key service that holds model keys |
| Endorser | Vouches for the attester's capabilities, for example by certifying a signing key held only in hardware | The chip maker |
| Reference value provider | Supplies the expected values that claims are compared with | The software publisher, and the hardware maker for firmware |

A client that checks evidence itself is both verifier and relying party.[^1]

## How the hardware measures software and signs the evidence

Evidence starts with measurements, cryptographic hashes of code and data recorded as they are loaded. In what RFC 9334 calls layered attestation, each stage measures the next one before starting it. No stage may alter the record of its own loading.[^1]

Confidential VMs apply this pattern at launch. The hardware is designed to isolate their memory from the host and from the hypervisor, the software that manages virtual machines. In Intel Trust Domain Extensions (TDX), the TDX module records a measurement of the VM's initial memory pages in a measurement register. Software inside the VM can extend runtime measurement registers with measurements of code and data it loads later.[^2] In AMD Secure Encrypted Virtualization with Secure Nested Paging (SEV-SNP), the AMD Secure Processor measures the VM's initial memory pages and their placement into a launch digest.[^3]

The measurements are then signed. Intel's design converts a report generated by the processor into a quote, signed with an attestation key. The key's certificate chain leads to an Intel certification authority, and Intel aims to publish the certificates and revocation lists for that chain.[^2] AMD's firmware signs reports with a Versioned Chip Endorsement Key (VCEK). Each chip has its own VCEK, derived from the version numbers of its trusted components, so a valid signature also identifies those versions.[^3] Both designs let software inside the VM add its own data to the report, such as a public key it will use to communicate, or a hash of that key.[^2, 3]

## How a verifier appraises a report

Before anything sensitive is sent, a verifier works through these checks:

1. **Signature and certificate chain.** The report's signing key must chain to the hardware maker's root, with no revoked certificate along the way.[^2, 4]
2. **Firmware versions.** The trusted computing base (TCB) is all the hardware, firmware and software that must work correctly for a security policy to hold. Intel treats a TCB as up to date when each component's security version number meets a threshold its author publishes.[^2] Trail of Bits audited WhatsApp's Private Processing before launch and found that the system trusted the patch level the firmware reported about itself. The fix checks AMD-signed certificate fields.[^7]
3. **Measurements.** The verifier compares measurements with reference values.[^1] In Apple's Private Cloud Compute (PCC), the reference values come from a public transparency log. Apple says a user's device wraps (encrypts) its request payload key only for nodes whose attested measurements match a release in the log.[^8]
4. **Freshness.** A nonce, an unpredictable value chosen by the verifier and signed into the evidence, shows that the evidence was signed after the nonce was generated.[^1] The WhatsApp audit found reports with no random value supplied by the client. An attacker who compromised a TEE once could therefore replay its report and session keys indefinitely. Meta's fix puts the client's random value in each report. The value comes from the Transport Layer Security (TLS) handshake, the exchange that sets up the encrypted connection.[^7]
5. **Binding to the connection.** The report should be bound to the key that protects the session, so that only the attested machine can read the data. AMD's design lets a VM place the hash of its public key in the report.[^3] The auditors recommend attesting to a value derived from the TLS handshake.[^7]

## How GPUs join the trust boundary

Large models run on GPUs, which hold the model and the data during inference. An attestation from the central processing unit (CPU) alone therefore says nothing about the GPUs. NVIDIA's confidential computing mode for H100 GPUs works with a confidential VM on AMD SEV-SNP or Intel TDX.[^4] Data transfers, command buffers and CUDA kernels are encrypted before they cross the PCI Express bus between the VM and the GPU. The GPU's on-package memory is not encrypted. NVIDIA says this memory is considered secure against everyday physical attack tools.[^4]

The VM's trust boundary encloses the components it trusts with the data. Before including the GPU in it, the VM checks the certificate for the GPU's identity key against NVIDIA's certificate authority and confirms that the certificate has not been revoked. That identity key is burned into the chip's fuses. The GPU also produces a signed attestation report of its measurements.[^4] NVIDIA's Remote Attestation Service (NRAS), or a local verifier, compares those measurements with reference integrity manifests (RIMs). RIMs are reference values that NVIDIA generates and signs as part of its driver and GPU firmware builds.[^5, 6] The measured components include hardware configuration, firmware and driver microcode.[^6]

With evidence from the CPU's TEE and from each GPU, the machine is what RFC 9334 calls a composite device. Each component produces its own evidence, and a lead attester collects it.[^1] A relying party needs all of it, tied to one machine.

## What a valid report establishes and what it leaves open

A report that passes these checks shows that genuine hardware at known firmware versions loaded the measured software in a protected mode, with fresh evidence tied to the connection. Four gaps remain.

**Behavior and later inputs are outside the report.** A measurement identifies code. It does not show that the code enforces its policy, and it says nothing about inputs loaded afterward. The WhatsApp audit found configuration files with environment variables that were loaded after measurement. An insider could have used them to load malicious code while attestation still passed.[^7]

**A matching measurement helps only if someone knows what the build does.** Apple committed to publishing every production PCC image so that researchers can check it against the logged measurements.[^8] Trail of Bits notes that it remains challenging to make confidential VM images fully reproducible, so that outsiders can rebuild and examine them.[^7]

**The hardware maker stays trusted.** RFC 9334 uses the term roots of trust for components that no evidence describes, so endorsements must vouch for them.[^1] A threat model states what a design defends against and what it trusts. AMD's SEV-SNP threat model, for example, treats the chip's hardware and its secure processor as fully trusted.[^3]

**Physical attacks and side channels are often out of scope.** AMD lists attacks on the memory bus while a VM is running as out of scope. It also says hardware does not specifically prevent architectural side channels.[^3] Intel says TDX does not prevent all types of hardware attacks.[^2] In September 2026, researchers disclosed DDRop, a memory-bus interposer: a device inserted between the processor and its memory. Its parts cost less than $200. The researchers report using it on Intel TDX to forge the measurement in an attestation report. Intel and AMD told them physical attacks on main memory are out of scope for current products.[^11]

## What changes for AI workloads: model weights and a larger TCB

**Model weights need their own check.** A launch measurement describes what was in memory at start-up. If weights are loaded afterward, the attestation says nothing about which model is serving, unless the software measures the weights or verifies a signature over them before use. It can measure them into a TDX runtime measurement register, for example.[^2] Google's Confidential Space reports the image digest of the workload container.[^9] That digest covers weights built into the image, but not weights downloaded later.

Attestation can also be a condition for releasing the weights. RFC 9334 describes a model owner that releases a model, or the key to decrypt it, only to a device that passes attestation.[^1] Anthropic's 2025 design sketch keeps weights encrypted and decrypts them only in a small trusted loader, after a key server has checked attestation.[^10]

**The trusted computing base grows with the inference stack.** Everything inside a confidential VM belongs to the workload's TCB, because AMD's threat model treats the VM itself as fully trusted and responsible for protecting its own interfaces.[^3] With GPUs, the TCB includes the NVIDIA driver,[^4] along with the operating system and serving software. Anthropic's sketch keeps the trusted part small. Within its inference server, only a small loader can access decrypted data. Anthropic says the rest might change frequently without affecting the system's security.[^10]

## Further reading

RFC 9334 defines the full vocabulary,[^1] and the Trail of Bits audit shows where one deployment's checks fell short.[^7]
