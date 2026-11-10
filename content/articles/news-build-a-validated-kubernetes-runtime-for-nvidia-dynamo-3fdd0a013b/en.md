---
title: "NVIDIA Details Recipe-Based Validation for Dynamo on Kubernetes"
dek: "AICR pins infrastructure versions and checks deployed clusters against recipe requirements. NVIDIA’s walkthrough describes runtime conformance checks, with performance testing handled separately."
kind: news
topics: [evaluation-audits, supply-chain]
layers: [runtime]
event_date: 2026-10-30
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "Build a Validated Kubernetes Runtime for NVIDIA Dynamo | developer.nvidia.com | 2026-10-30 | https://developer.nvidia.com/blog/build-a-validated-kubernetes-runtime-for-nvidia-dynamo"
---

NVIDIA published a walkthrough on 30 October 2026 describing how NVIDIA AI Cluster Runtime (AICR) packages Dynamo and its Kubernetes infrastructure into versioned recipes. The recipes record pinned component versions, compatibility constraints, configuration values, checksums, and validation expectations, giving operators a defined configuration against which to check a deployment.[^1]

The article specifies the Dynamo Platform Helm chart at version 1.4.2. Its example AICR v1.0.0 recipe targets Amazon EKS on NVIDIA GB200 NVL72 and GB300 NVL72 systems. NVIDIA says its team tested the listed component versions together on those platforms and hardware; that claim should not be generalized to other environments.[^1]

The workflow snapshots a cluster, generates a recipe, renders a deployment bundle, installs the runtime, and validates the live cluster before application deployment. Depending on the recipe, deployment and conformance checks cover GPU capacity, operator health and versions, accelerator access, scheduling, metrics, and ingress readiness. Offline validation evaluates declarative constraints and skips behavioral checks. Performance validation runs separately and consumes GPUs through a temporary serving workload.[^1]

The walkthrough also distinguishes Dynamo Frontend routing from Gateway API Inference Extension routing with an Endpoint Picker Plugin. Both use worker-reported key-value (KV) cache events in the illustrated configuration. NVIDIA warns that predicting cache contents from prior routing decisions cannot observe evictions and can let the router’s view drift.[^1]

:::analysis
The claim sits at T2 (runtime): a passing check establishes conformance to the selected recipe’s requirements, leaving model behavior and application correctness outside that result. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that deployment. Operators should compare installed versions, placement settings, routing mode, and live validation results with their selected recipe; users need access to those records for the identifiability check. The article describes compatibility validation, without identifying a security fix or recommending a fixed release.[^1]
:::

:::checked
On 10 November 2026, we read the supplied saved copy of NVIDIA Technical Blog’s “Build a Validated Kubernetes Runtime for NVIDIA Dynamo,” published on 30 October 2026. We did not test the system, inspect a deployed cluster, or independently reproduce NVIDIA’s reported testing; our check establishes what the saved walkthrough describes.[^1]
:::

[^1]: NVIDIA Technical Blog, “Build a Validated Kubernetes Runtime for NVIDIA Dynamo,” 30 October 2026. https://developer.nvidia.com/blog/build-a-validated-kubernetes-runtime-for-nvidia-dynamo
