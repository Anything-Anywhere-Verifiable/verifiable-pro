---
title: "NVIDIA Says Snapshot Restores GPU Workloads in Seconds"
dek: "NVIDIA reports 8×–36× faster startup across tested inference configurations. The measurements exclude infrastructure provisioning and container image loading, and restoration requires compatible hardware and software."
kind: news
topics: [evaluation-audits]
layers: [evaluations, runtime, hardware]
event_date: 2026-11-10
published: 2026-11-12
agent: daily
evidence: [announcement, documentation]
sources:
  - "Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot | developer.nvidia.com | 2026-11-10 | https://developer.nvidia.com/blog/start-and-restore-gpu-workloads-in-seconds-with-nvidia-snapshot"
---

NVIDIA introduced Snapshot, an open-source checkpoint and restore component for GPU workloads on Kubernetes, in a technical blog post published on 10 November 2026. The company reports restoring initialized inference replicas in 3.6–42.7 seconds across its tested configurations, an 8×–36× speedup over cold starts.[^1]

Snapshot captures CPU and GPU memory after workload initialization. NVIDIA says a new Pod can resume from that artifact on a node with the same GPU model and driver, skipping weight loading, compilation and CUDA graph capture. Compatible workloads can span multiple GPUs within one node. The workload must also implement a small pause-and-resume handshake and meet checkpoint, restore and runtime compatibility requirements.[^1]

The reported benchmarks used NVIDIA B200 GPUs, driver 615.71.09 and VAST NFS storage, with vLLM 0.31.0, SGLang 0.5.21 and TensorRT LLM 1.3.0. Cold-start timing ran from process launch until engine initialization returned, before inference; restore timing ran from the restore request until serving resumed. Infrastructure provisioning and container image loading are outside the measured restore path. NVIDIA also says the key-value cache was released before every checkpoint and excluded from the artifact.[^1]

:::analysis
The claim spans T6 evaluations, T2 runtime and T1 hardware: readers must assess the timing boundaries, restored process configuration and GPU compatibility before applying these results to their service. Users and operators should verify their deployed engine and driver versions, GPU model, checkpoint configuration and storage conditions against the reported setup and compatibility requirements; the post identifies no security fix or recommended fixed version.[^1] The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the deployment conditions in question. Such records would support that determination; this article establishes neither their availability nor equivalent performance on another system.
:::

:::checked
On 12 November 2026, we read the saved NVIDIA Technical Blog article “Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot,” including its methodology, setup and three results tables.[^1] This reading establishes what NVIDIA reports. We did not test Snapshot, reproduce the benchmarks or inspect the linked repository; performance and compatibility remain vendor-reported claims.
:::

[^1]: NVIDIA, “Start and Restore GPU Workloads in Seconds with NVIDIA Snapshot,” 10 November 2026. https://developer.nvidia.com/blog/start-and-restore-gpu-workloads-in-seconds-with-nvidia-snapshot
