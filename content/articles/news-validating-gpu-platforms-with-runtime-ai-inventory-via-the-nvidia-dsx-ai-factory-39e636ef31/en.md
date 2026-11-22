---
title: "NVIDIA Adds Runtime AI Inventory to GPU Platform Recipes"
dek: "NVIDIA says its AI Cluster Runtime now integrates k8s-aibom to inventory supported Kubernetes AI workloads. The records have coverage and verification limits."
kind: news
topics: [supply-chain, verifiable-inference]
layers: [models, runtime]
event_date: 2026-11-11
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "Validating GPU Platforms with Runtime AI Inventory via the NVIDIA DSX AI Factory | developer.nvidia.com | 2026-11-11 | https://developer.nvidia.com/blog/validating-gpu-platforms-with-runtime-ai-inventory-via-the-nvidia-dsx-ai-factory"
---

On 11 November 2026, NVIDIA described an integration that adds an AI bill of materials (AIBOM) for supported Kubernetes workloads to NVIDIA AI Cluster Runtime (AICR), part of the DSX AI Factory Platform. The company says the integration combines version-locked GPU platform recipes with workload inventory from the open-source k8s-aibom project.[^1]

AICR recipes record desired platform configuration, while k8s-aibom watches workload and pod APIs and produces CycloneDX 1.6 records for recognized AI workloads. Two H100 Google Kubernetes Engine recipes select the inventory component by default; other GKE recipes can opt in. NVIDIA's example uses AICR v1.2.0 with a catalog that pins k8s-aibom 1.6.2.[^1]

The inventory covers supported workload kinds with a recognized AI signal in namespaces opted in for reporting. Each recorded attribute has a confidence tier and an evidence locator. An AIBOM can exist before a pod runs: it records the workload specification and, when a pod exists, available resolution evidence. It does not establish successful execution. The namespace label controls which records are emitted, while the controller still caches workload and pod specifications cluster-wide.[^1]

NVIDIA says its qualification process binds specific upstream artifacts and a digest-pinned controller image, checks provenance and exercises deployment operations on tested paths. Runtime observations themselves are unsigned, model-claim signature verification is disabled by default, and connecting platform provenance to runtime inventory remains future work. A matching storage version alone also does not establish that the full custom resource definition schema is current.[^1]

:::analysis
The issue sits at T3 models and T2 runtime: an inventory can help a verifier identify model and runtime attributes, but its coverage and evidence limit what can be trusted. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed. Users and operators should check whether their workloads and namespaces are covered, inspect evidence and confidence for relevant attributes, and verify the installed versions, schema and controller health against their own deployment; NVIDIA's example specifies AICR v1.2.0 and k8s-aibom 1.6.2.[^1]
:::

:::checked
On 18 November 2026 we read the saved NVIDIA Technical Blog article, [“Validating GPU Platforms with Runtime AI Inventory via the NVIDIA DSX AI Factory”](https://developer.nvidia.com/blog/validating-gpu-platforms-with-runtime-ai-inventory-via-the-nvidia-dsx-ai-factory), published on 11 November 2026.[^1] We did not test the system or independently confirm NVIDIA's qualification claims or the inventory's behavior.
:::
