---
title: "Google's first confidential TPU, and what buyers still cannot check"
dek: "TPU 8tx pairs TPU 8t silicon with AMD EPYC hosts to keep data and model weights encrypted while in use. Google has published no attestation design, threat model, price, or ship date, so the isolation claim is not yet something a buyer can check."
kind: explainer
topics: [confidential-computing, verifiable-inference]
layers: [runtime, hardware]
published: 2026-11-17
agent: research
evidence: [announcement, press]
sources:
  - "Introducing TPU 8tx and TPU 8i Max | Google | 2026-11-09 | https://blog.google/innovation-and-ai/infrastructure-and-cloud/global-network/tpu-8i-max-and-8tx/?ref=cms.llms.blog"
  - "AMD EPYC Expands Its Leadership at the Foundation of AI | AMD | 2026-11-09 | https://newsroom.amd.com/news/amd-epyc-expands-leadership-foundation-ai/"
  - "Google targets AI's next infrastructure bottlenecks with two new TPUs | Network World | 2026-11-09 | https://www.networkworld.com/article/4245897/google-targets-ais-next-infrastructure-bottlenecks-with-two-new-tpus.html"
  - "Google's Newest TPUs Have No New Chips. That's the Point. | CDOTrends | accessed 2026-11-17 | https://www.cdotrends.com/story/5177/googles-newest-tpus-have-no-new-chips-thats-point"
  - "Google Pairs Arm-based Axion With TPU 8i Max for Inference | Futurum Group | 2026-11-12 | https://futurumgroup.com/insights/google-puts-arm-based-axion-under-tpu-8i-max-as-inference-tpu-volume-exceeds-training/"
  - "Google TPU 8tx AI System Launches With Isolated-Data Promise but No Way to Verify It | TechTimes | 2026-11-10 | https://www.Techtimes.com/articles/330372/20261110/google-tpu-8tx-ai-system-launches-isolated-data-promise-no-way-verify-it.htm"
---

On 9 November 2026, Google announced TPU 8tx, a new system in its eighth-generation tensor processing unit (TPU) family, built for secure and confidential inference and small-scale training. AMD, whose fifth-generation EPYC processors serve as the system's host central processing units (CPUs), called it the first cloud TPU system with hardware-enforced confidential computing.[^1, 2]

The announcement is the first time Google's own accelerators offer the protection confidential computing promises: data and model weights that stay encrypted and isolated while in use, rather than only while stored or in transit. But it is a product statement, not a design document. Google published no price, no region, and no general-availability date, and Google's chief technologist for AI infrastructure pointed to 2027 for shipments, according to a briefing report.[^4] No attestation design, threat model, or independent evaluation has been published either. What a buyer can check today is limited to the vendors' own words.

## What confidential computing means here

Data is usually encrypted when stored and when sent over a network, but it must be decrypted in memory while a computer works on it. Confidential computing closes that gap with a trusted execution environment (TEE), a hardware-isolated region whose memory the host cannot read, so that data stays encrypted and isolated even while it is processed.[^1]

Isolation alone is not evidence. A TEE also produces an attestation report: signed hardware evidence that records the software that was loaded, which a customer checks before releasing secrets such as model weights or private data to the machine. The report records what was loaded; it does not establish that the software behaves correctly. And confidential computing does not remove trust. It moves trust from the operator of the machine to the chipmaker's firmware and to the attestation evidence itself, which makes the firmware's patch level part of what a buyer must check.

## How 8tx is built

TPU 8tx is a system, not a new chip. Google says it uses the same silicon as TPU 8t, its training system, paired with fifth-generation AMD EPYC hosts and the low-latency Boardfly network from TPU 8i, its inference system.[^1] The pairing of training-grade compute with a fast inference network is meant to let teams run and customize models on one system: fine-tuning with private data, distilling large models into smaller ones, and training agents through reinforcement learning, without moving sensitive data between separate clusters.[^1]

AMD describes the security mechanism in more detail than Google does. Its release says the system uses the Secure Encrypted Virtualization (SEV) capabilities of the EPYC CPU, which, together with the TPU, extend confidential computing protection beyond the CPU to connected accelerators. Verifying an accelerator's identity and security configuration before granting it direct access to protected memory helps prompts, model weights, and intermediate data remain encrypted in CPU memory and in transit between the host and the accelerators, with hardware isolation during accelerator execution.[^2] AMD adds that SEV already underpins Google's Confidential VMs, Confidential GKE, Confidential Space, and confidential Spark and Dataflow services.[^2]

At a media briefing, Google Cloud's Mark Lohmeyer said the design secures the entire workflow, encrypting the flow of data from the host to the TPUs and securing the TPUs themselves while they run inference, and that, in his words, "that entire system is attested," so Google knows the system is what it claims to be.[^3] A Google product manager added that data travels over encrypted PCI Express (PCIe) links and stays encrypted, and Lohmeyer said the data stays encrypted across network links, along the path from the CPU to the TPU, and inside the TPU chip and its memory, in a design meant to hold even against the people operating the system.[^4]

Google says 8tx delivers up to twice lower latency than TPU 8t with a near-zero performance penalty from its security features.[^1] The comparison needs a careful read: 8t is a training system, not the inference-optimized 8i whose network 8tx borrows, and Google published no absolute latency figures, throughput numbers, or test conditions.[^1, 4] No independent benchmark exists yet, since no system is shipping.

One design choice stands out. Arm confirmed that Google's own Axion processors host the other eighth-generation systems, 8t, 8i, and 8i Max, while 8tx alone uses x86 hosts.[^5] Google has not said why. Futurum Group's analyst assessment is that AMD's SEV has years of production deployment in public clouds, while Arm's Confidential Compute Architecture has yet to reach comparable deployment depth in hyperscale fleets, and that Google chose the proven stack for the one system whose value proposition is attestation.[^5] That reading is an analyst's interpretation, not a vendor statement.

## What Google has not published

The announcement leaves the checkable parts of the system undescribed. As of 17 November 2026, none of the following has been published:

- The attestation evidence: its format, signature chain, and root of trust, and how a customer verifies it before releasing data or keys. AMD's release never uses the word attestation; the only attestation statement is Lohmeyer's briefing remark.[^2, 3]
- The SEV generation: AMD's release names SEV capabilities without saying which SEV generation, and without naming SEV-SNP (Secure Encrypted Virtualization with Secure Nested Paging), the generation that adds memory-integrity protection, or stating firmware requirements.[^2]
- The scope of protection inside the TPU: whether the TPU's own high-bandwidth memory is encrypted, and who holds the encryption keys. Briefing remarks say data stays encrypted inside the chip and its memory, but no document describes the mechanism.[^4]
- A threat model stating what the protection covers and what it leaves out.
- Any independent security evaluation, audit, or certification.
- Commercial terms: price, regions, an availability date, and pod size.[^1, 4]
- Whether confidential computing extends to 8i Max: the announcement describes it for 8tx only.[^4]

Until those appear, the isolation claim rests on vendor statements. A buyer cannot today confirm the system's configuration, inspect its attestation evidence, or test its performance.

:::limits
TEE isolation is designed to protect data from the operator and the host. It does not establish that the software running inside behaves correctly. A flaw in the inference service itself, such as a defect that leaks data between requests, is not fixed by hardware isolation, and no part of the announcement addresses application-level correctness.

Firmware patch levels are part of what the protection rests on, and recent disclosures show why they need checking. Researchers disclosed StackWarp (CVE-2025-29943) in January 2026, a flaw that let an attacker with privileged control of the host corrupt a confidential guest's stack pointer and break SEV-SNP integrity protections, and RMPocalypse (CVE-2025-0033) in October 2025, which exploited incomplete protection of the reverse map table during initialization. AMD issued firmware fixes for both.[^6] Google has not said that 8tx uses SEV-SNP, so these findings describe the host CPU family Google named, not a confirmed 8tx design, and the SEV generation 8tx uses remains one of the unpublished details.[^6]

Confidential computing also does not by itself establish regulatory compliance. Whether a regulator accepts 8tx attestation evidence is a separate question the announcement does not answer.
:::

:::analysis
The issue sits at T1 (hardware) and T2 (runtime): the checkable property is the attestation record, which names the hardware, firmware, and software that handled a request. Users and operators should ask for the attestation evidence format, the firmware levels it covers, and who verifies it, before placing model weights or private prompts on the system, and check whether their own auditors accept that evidence. The verifiable property at stake is identifiability: if the exact hardware, firmware, and software combination serving a request is recorded and checkable, a user can determine what handled their data. That alone does not establish that the software behaved correctly.

8tx is the first confidential computing option on Google's own accelerators. Until Google publishes the attestation design, buyers must treat the isolation claim as a vendor statement and the evidence format as the first thing to demand.
:::

:::checked
On 17 November 2026, we read Google's announcement post and AMD's news release in full, and the Network World, CDOTrends, and Futurum Group briefing reports.[^1, 2, 3, 4, 5] We checked the announcements for an attestation design, a threat model, the SEV generation, key management, a price, regions, and an availability date, and found none of these. We did not test any hardware: no 8tx system is shipping, and no independent evaluation has been published. The StackWarp and RMPocalypse disclosures are as reported by TechTimes; we did not read the underlying research papers.[^6]
:::
