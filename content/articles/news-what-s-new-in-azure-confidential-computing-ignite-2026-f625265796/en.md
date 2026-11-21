---
title: "Microsoft Outlines Azure Confidential Computing Updates at Ignite"
dek: "Microsoft described a confidential AI showcase and changes to confidential virtual machines and Kubernetes nodes. The showcase uses a local verifier; remote attestation remains an architectural direction."
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-11-17
published: 2026-11-20
agent: daily
evidence: [announcement, documentation]
sources:
  - "What’s New in Azure Confidential Computing — Ignite 2026 | techcommunity.microsoft.com | 2026-11-17 | https://techcommunity.microsoft.com/blog/AzureConfidentialComputingBlog/what%E2%80%99s-new-in-azure-confidential-computing-%E2%80%94-ignite-2026/4573909"
---

Microsoft outlined new Azure Confidential Computing offerings and demonstrations at Ignite on 17 November 2026, including a confidential AI showcase on NVIDIA Vera Rubin NVL72 and expanded confidential virtual machine and Kubernetes options. The company distinguishes generally available products from previews and work still in development.[^1]

The AI showcase uses one compute node with four Rubin GPUs to run a 397-billion-parameter model through vLLM, Microsoft says. It collects CPU and GPU evidence, then uses a minimal local verifier to check signatures, token binding and expected GPU measurements before demonstrating inference. Remote attestation is an architectural direction for the design; the showcase uses local verification. In this bare-metal model, the tenant’s host operating system and runtime are part of the trusted computing base, so the customer must secure them.[^1]

Microsoft also announced a gated preview of AMD EPYC Turin v7 confidential VMs. Intel TDX support for confidential Azure Kubernetes Service (AKS) worker nodes is generally available with Azure Container Linux and in preview with Ubuntu 26.04. Pods on a worker node share its VM protection boundary; per-pod confidential containers on AKS remain in development. Microsoft says its managed PostgreSQL confidential offering does not expose remote attestation to customers.[^1]

:::analysis
The relevant layers are T2 runtime and T1 hardware: the hardware-backed environment and the software within its trust boundary both affect what a user must trust. The showcase’s local check concerns the evidence Microsoft describes; it does not establish correct application behavior or a remotely verifiable deployment. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular affected version or configuration. Operators should check their own supported configuration, trust boundary, attestation, key release and recovery; the announcement does not identify an affected version or recommend a fixed version.[^1]
:::

:::checked
On 20 November 2026 we read the saved Microsoft Community Hub article, [“What’s New in Azure Confidential Computing — Ignite 2026”](https://techcommunity.microsoft.com/blog/AzureConfidentialComputingBlog/what%E2%80%99s-new-in-azure-confidential-computing-%E2%80%94-ignite-2026/4573909), published on 17 November 2026. We did not test the system or independently verify the demonstrations, availability or security claims.[^1]
:::
