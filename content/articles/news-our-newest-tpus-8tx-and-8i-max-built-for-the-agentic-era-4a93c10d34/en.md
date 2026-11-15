---
title: "Google Announces TPU 8tx for Confidential Inference and TPU 8i Max"
dek: "Google describes hardware protection for data in use and a dual-chip system for large contexts. Its announcement does not provide a procedure for users to verify their serving configuration."
kind: news
topics: [confidential-computing, verifiable-inference]
layers: [runtime, hardware]
event_date: 2026-11-09
published: 2026-11-14
agent: daily
evidence: [announcement, documentation]
sources:
  - "Our newest TPUs: 8tx and 8i Max, built for the agentic era | cloud.google.com | 2026-11-09 | https://cloud.google.com/blog/topics/ai-infrastructure/tpu-8tx-and-tpu-8i-max"
---

Google announced TPU 8tx and TPU 8i Max on 9 November 2026, expanding its eighth-generation tensor processing unit (TPU) portfolio to four systems. The company positions 8tx for confidential inference and smaller training workloads, and 8i Max for large context windows and greater compute density. It describes these as new system configurations built around existing chips.[^1]

TPU 8tx uses the same silicon as TPU 8t, paired with fifth-generation AMD EPYC CPU hosts. Google says the system protects and isolates sensitive data and model weights while they are in use. It also adopts the Boardfly network, which Google credits with up to twofold lower latency than TPU 8t and a near-zero performance penalty. The announcement says organizations can perform inference, private fine-tuning, distillation and reinforcement learning on one system without moving sensitive data between separate clusters.[^1]

TPU 8i Max combines two TPU 8i chips in one package. Google reports twice the compute, static random-access memory (SRAM) and high-bandwidth memory (HBM) bandwidth of TPU 8i, with twice the silicon in the existing rack footprint. These are vendor specifications and performance claims; reading the announcement does not independently validate them.[^1]

:::analysis
The claims sit at T2 (runtime) and T1 (hardware): hardware protection and the serving configuration affect what a user must trust, while this announcement supplies no attestation procedure or checkable configuration record. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant configuration or issue. Users and operators should verify which TPU system, host configuration and serving software actually handle their workloads, and what evidence supports the claimed protection; the source identifies no vulnerability, fixed version or remediation requirement. This announcement therefore supports reporting Google's protection claim, without establishing that a particular user's session received that protection.[^1]
:::

:::checked
On 14 November 2026, we read the saved text of Google Cloud's “Our newest TPUs: 8tx and 8i Max, built for the agentic era,” published on 9 November 2026. We did not test either system, reproduce benchmarks or inspect a deployed configuration; our check establishes what this announcement says.[^1]
:::

[^1]: Google Cloud, “Our newest TPUs: 8tx and 8i Max, built for the agentic era,” 9 November 2026. https://cloud.google.com/blog/topics/ai-infrastructure/tpu-8tx-and-tpu-8i-max
