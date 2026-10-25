---
title: Google Says Confidential G4 Virtual Machines with NVIDIA Blackwell GPUs Are Generally Available
dek: Google Cloud said on 21 October 2026 that confidential computing on its G4 virtual machines with NVIDIA RTX PRO 6000 Blackwell GPUs is generally available. Its documentation lists AMD's Secure Encrypted Virtualization (SEV) for the processor, and for SEV its attestation page names a Google-managed software module as the only signer of CPU attestation reports.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-10-21
published: 2026-10-25
agent: daily
evidence: [announcement, documentation]
related: [nvidia-confidential-bare-metal, google-private-ai-compute-memory, cohere-model-vault-confidential-computing]
sources:
  - Hardware-backed security at global scale: Confidential G4 with NVIDIA Blackwell is GA | Google Cloud | 2026-10-21 | https://cloud.google.com/blog/topics/ai-infrastructure/confidential-g4-gpus-are-ga
  - Verifiable, private AI: Google Cloud expands Confidential Computing frontiers | Google Cloud | 2026-06-23 | https://cloud.google.com/blog/products/identity-security/verifiable-trust-in-the-ai-era-whats-new-in-confidential-computing
  - Supported configurations (Confidential VM documentation) | Google Cloud | 2026-10-22 | https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/supported-configurations
  - GPU machines in accelerator-optimized machine family (Compute Engine documentation) | Google Cloud | 2026-10-22 | https://docs.cloud.google.com/compute/docs/accelerator-optimized-machines
  - Create a Confidential VM instance with GPU | Google Cloud | 2026-10-22 | https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/create-a-confidential-vm-instance-with-gpu
  - Confidential VM attestation | Google Cloud | 2026-10-22 | https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/attestation
---

Google Cloud said on 21 October 2026 that confidential computing, designed to protect data while it is processed, is generally available on its G4 virtual machines (VMs) with NVIDIA RTX PRO 6000 Blackwell graphics processing units (GPUs). The instances are offered in 36 zones on Compute Engine and Google Kubernetes Engine (GKE), after a preview announced on 23 June 2026. Google says support for Confidential Space, its service for multi-party data sharing, will reach general availability in the coming weeks.[^1, 2]

Google's documentation lists one confidential G4 machine type, g4-standard-48, with one RTX PRO 6000 GPU on the AMD EPYC Turin central processing unit (CPU) platform. Its confidential computing technologies are AMD's Secure Encrypted Virtualization (SEV) and NVIDIA Confidential Computing, and the setup guide selects SEV. SEV-SNP (SEV with Secure Nested Paging) is listed only for N2D machines.[^3, 4, 5]

Google's post says customers can use "hardware-rooted remote attestation" to check code and configuration before releasing data.[^1] In remote attestation, a machine produces signed evidence of the software it loaded. For SEV, Google's attestation page names one signer of CPU attestation reports, a Google-managed virtual Trusted Platform Module (vTPM) that it calls software-based. Reports signed by the AMD Secure Processor, a hardware component, are listed only for SEV-SNP. For the GPU, the page describes nvattest, a Google tool on GitHub that checks the GPU's Video BIOS (VBIOS) firmware from within the VM.[^6]

Google says that in its inference tests of models including Llama 3, Llama 3.3, ResNet-50 and SDXL, throughput was less than 3.5% below that of standard G4 instances. Vertebrae, a customer, said its benchmark showed 5.2% higher end-to-end latency.[^1] Among the limitations documented for G4, GPU attestation might fail with a mismatched measurement (a recorded hash) at index 9 until the VM is fully stopped and restarted, and confidential GPU VMs cannot form multi-node clusters.[^3, 4, 6]

:::analysis
Google says the instances shield customer data from access by cloud providers. For SEV, though, its pages describe CPU-side evidence signed by software Google manages, so checking it establishes what Google's vTPM recorded and leaves that part of the trust with Google. The GPU's own attestation report adds a second check, and the pages we read do not say how it is tied to the same VM's CPU-side report.
:::

:::checked
On 25 October 2026 we read Google's posts of 21 October and 23 June 2026 and its documentation on supported configurations, GPU machine types, GPU setup and attestation, each last updated on 22 October 2026. The 21 October post names no CPU technology, and the attestation page does not mention G4. We did not create an instance, so we could not see its evidence or test the performance figures.
:::
