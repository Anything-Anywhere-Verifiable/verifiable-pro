---
title: "FLASH: checkpointing confidential LLM inference on NVIDIA H100"
dek: "FLASH reuses GPU ciphertext and UVM dirty-page tracking to shorten checkpoint pauses. Its H100 and Intel TDX evaluation distinguishes pause latency, serving impact, and recovery time."
kind: explainer
topics: [confidential-computing]
layers: [runtime, hardware]
published: 2026-11-04
agent: pipeline-research
evidence: [paper, code]
disclosure: "Mengyuan Li, editor of verifiable.pro, is a co-author of FLASH."
sources:
  - "FLASH: Fault-Led, Attested, Secure Hybrid-Key Checkpoint for Confidential Inference | Jonghyun Lee et al., ACM SIGOPS ATC 2026 | 2026 | https://github.com/sept-usc/FLASH/blob/cfe082f3fa9d6f68374b312c934fc86668ffc510/docs/flash-atc2026.pdf"
  - "FLASH source code and reproduction instructions | FLASH authors | accessed 2026-11-04 | https://github.com/sept-usc/FLASH"
  - "ATC 2026 artifact evaluation results | Systems Research Artifacts | accessed 2026-11-04 | https://sysartifacts.github.io/atc2026/results"
  - "jonghyunL/artifact_flash: ATC Artifact Evaluation | Zenodo | 2026-10-07 | https://doi.org/10.5281/zenodo.23199897"
related: [remote-attestation-for-ai-workloads-explained, how-to-read-a-remote-attestation-report, private-ai-compute-published-designs]
---

FLASH saves the protected data state of large language model (LLM) inference so a service can recover without pausing for a full graphics processing unit (GPU) memory dump at every checkpoint. Its approach combines reuse of GPU-generated ciphertext with driver-level tracking of modified memory. The operational problem is preserving active requests while keeping the act of saving them from disrupting serving.[^1]

The [final FLASH paper](https://github.com/sept-usc/FLASH/blob/cfe082f3fa9d6f68374b312c934fc86668ffc510/docs/flash-atc2026.pdf), by Jonghyun Lee and colleagues for ACM SIGOPS ATC 2026, evaluates that approach on one confidential H100. Understanding its result requires separating three things: the checkpoint pause, the effect on requests during background copying, and the time needed to recover afterward.[^1]

## Why protection makes saving state expensive

Inference builds a key-value (KV) cache containing attention state for previously processed tokens. Losing that cache discards work for active requests. Recomputing from prompts repeats processing, and stochastic token sampling can produce a different continuation. A checkpoint preserves the data needed to resume from a saved position.[^1]

Confidential inference places the central processing unit (CPU) and GPU inside trusted execution environments (TEEs), designed to protect their contents from a malicious cloud operator. In the evaluated H100 configuration, the Peripheral Component Interconnect Express (PCIe) connection remains untrusted, so GPU data must leave protected memory encrypted.[^1]

A conventional secure checkpoint decrypts that arriving ciphertext inside the CPU TEE, then encrypts the saved state under a checkpoint key. The paper measures roughly 40 GB/s without confidential mode and 7.3 GB/s with it. Transferring 80 GB at the latter rate alone takes about 11 seconds, before additional checkpoint encryption.[^1]

## Keep the encryption already performed

<figure class="article-diagram" aria-labelledby="figure-hybrid-key-caption">
<a class="article-diagram-link" href="../../assets/figures/flash-hybrid-key.svg" title="Open full-size diagram">
<img class="article-diagram-img" src="../../assets/figures/flash-hybrid-key.svg" width="1360" height="748" loading="lazy" alt="Hybrid-key checkpoint creation: FLASH retains GPU ciphertext and separately protects CPU state and the source GPU key.">
</a>
<figcaption id="figure-hybrid-key-caption"><a href="../../assets/figures/flash-hybrid-key.svg">View full size</a> · Hybrid-key checkpoint creation. GPU ciphertext is retained; CPU state and the source GPU key are protected separately. Adapted from FLASH Figure 4. <a href="https://github.com/sept-usc/FLASH/blob/main/docs/figures/hybrid-key.svg">Diagram source</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</figcaption>
</figure>

FLASH retains the device-to-host ciphertext produced by the GPU copy engine. A custom driver interface retrieves encrypted pages together with their initialization vectors (IVs) and authentication tags. This removes a redundant CPU decryption and re-encryption cycle from checkpoint creation.[^1]

The image therefore contains two protection domains. GPU pages remain encrypted under the source GPU session key. CPU state and that source key are encrypted under the checkpoint key. Saved IVs, tags, and metadata let the recovery agent reconstruct the original decryption context.[^1]

Recovery still performs cryptographic work. The destination obtains the checkpoint key, unwraps the source GPU key, and authenticates and decrypts saved GPU pages inside protected CPU memory. Loading them onto the destination GPU uses its new protected transfer session. Retaining ciphertext accelerates repeated saving; it does not eliminate reconstruction or decryption during recovery.[^1]

## Find writes while inference continues

<figure class="article-diagram" aria-labelledby="figure-dirty-tracking-caption">
<a class="article-diagram-link" href="../../assets/figures/flash-dirty-tracking.svg" title="Open full-size diagram">
<img class="article-diagram-img" src="../../assets/figures/flash-dirty-tracking.svg" width="1360" height="752" loading="lazy" alt="UVM write faults mark modified 2 MB regions during background copying; the final pause copies the dirty delta.">
</a>
<figcaption id="figure-dirty-tracking-caption"><a href="../../assets/figures/flash-dirty-tracking.svg">View full size</a> · Concurrent copying with UVM dirty tracking. The final pause recopies modified 2 MB regions. Adapted from FLASH Figure 5. <a href="https://github.com/sept-usc/FLASH/blob/main/docs/figures/dirty-tracking.svg">Diagram source</a> · <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</figcaption>
</figure>

Most copying overlaps with inference. Because inference can change a page after it has been copied, FLASH must identify which pages need another copy during the final pause.[^1]

It brings allocations under NVIDIA Unified Virtual Memory (UVM) management by intercepting allocation calls and substituting managed allocations, then prefetching them onto the GPU. Tracked pages become read-only. A write raises a fault, allowing the guest driver to record the affected region as dirty and restore write permission before execution continues.[^1]

FLASH tracks at 2 MB granularity. On the first fault in a region, it proactively handles the larger region, avoiding the cost of potentially hundreds of separate 4 KB faults. This can count some unchanged bytes as dirty, but reduces fault handling. It requires neither changes to LLM kernels nor offline analysis of Parallel Thread Execution (PTX) code.[^1]

At an intercepted framework synchronization point, outstanding GPU work has drained. FLASH pauses execution, copies the accumulated dirty regions, and resumes serving. The tracking window depends partly on when the application reaches that synchronization point, so it can extend beyond the background copy itself.[^1]

## Reuse static data without dropping it from recovery

Model weights usually remain unchanged after loading. The paper's static classification captures such state once and reuses it across checkpoints. Static pages remain monitored: a later write faults and promotes the affected region to dynamic state. Recovery restores both static and dynamic data, including request metadata needed by the restarted framework.[^1]

The release makes an implementation distinction worth preserving. Its default `v3-static` mode identifies static allocations through host-to-device allocation flags. Learning is a separate, opt-in `--learn` path. A run using the default should not be described as automatically exercising the paper's learning mechanism.[^2]

## What the H100 measurements establish

The evaluation uses one 80 GB NVIDIA H100 in confidential mode, Intel Trust Domain Extensions (TDX), and vLLM 0.8.5. It covers Llama-3.2-1B, Qwen-2.5-7B, and Llama-2-13B under short-context Chatbot and long-context Reasoning workloads. Images are staged in memory-backed `tmpfs`, and the load generator bypasses the web-serving layer.[^1]

The paper's 1.2-second mean stop-and-copy summary spans FLASH and FLASH-SC, its version without static classification. It reports a 9.4× reduction relative to PhoenixOS (PhOS) and 7.8× relative to GCR at a one-minute checkpoint interval. Those comparisons use reimplemented data paths because the original systems do not run unchanged on this confidential stack. They measure the authors' implementations of the comparison protocols under the shared setup.[^1]

At a one-minute checkpoint interval, serving overhead varies substantially. In the Llama-1B Reasoning workload, FLASH reports 75.8 ms at the 99th percentile for time to first token, compared with 14,364.9 ms for PhOS and 6,385.6 ms for GCR. Yet the one-minute Llama-1B Chatbot case produces a FLASH 95th-percentile first-token time of about 13.3 seconds, worse than both comparisons. Write-fault tracking also adds time between tokens. Short checkpoint pauses do not imply uniformly low serving overhead.[^1]

Recovery is a separate measurement. Restoring the full approximately 66–67 GB footprint takes 18.7, 17.1, and 18.1 seconds across the three models. Static classification does not remove weights from that transfer.[^1]

## Integrity and freshness depend on trusted services

Encryption alone cannot reject an old, valid checkpoint. FLASH combines authenticated encryption with a manifest binding page positions and cryptographic metadata. A TDX-signed report binds the manifest hash, confidential virtual machine identity, checkpoint counter, and timestamp. A trusted remote attestation service (RAS) retains checkpoint keys and the latest counter and manifest hash; recovery rejects images that disagree with that record.[^1]

This relies on the CPU and GPU protections, guest kernel, driver, checkpoint agent, and RAS operating correctly. The RAS must preserve its trusted state across guest teardown and remain outside the adversary's control. Attestation supplies evidence about software loaded into an environment; it never guarantees runtime correctness. Our [remote attestation explainer](/articles/remote-attestation-for-ai-workloads-explained/) and [guide to reading an attestation report](/articles/how-to-read-a-remote-attestation-report/) explain that distinction.

Availability and leakage through volume, access patterns, and timing remain outside FLASH's protection. A malicious host can withhold an image or service. The protocol fails closed when required state is unavailable.[^1]

## The deployment boundary

FLASH saves inference data state and rebuilds execution context by restarting the framework. It supplies no general GPU control-state snapshot, and globally consistent multi-GPU checkpointing is outside the evaluated scope. Future trusted input/output paths can also remove the intermediary ciphertext that its reuse optimization depends on.[^1]

The [FLASH repository](https://github.com/sept-usc/FLASH) and [illustrated README](https://github.com/sept-usc/FLASH/blob/main/README.md) provide driver modifications and evaluation programs. They do not supply a complete production RAS and key-release deployment; that needs additional integration.[^2] The [conference artifact record](https://sysartifacts.github.io/atc2026/results) lists Artifacts Available, Artifacts Evaluated – Functional, and Results Reproduced.[^3] The [archived evaluation artifact](https://doi.org/10.5281/zenodo.23199897) preserves the release.[^4] Our [comparison of published private AI compute designs](/articles/private-ai-compute-published-designs/) offers broader context for separating mechanisms from deployment claims.

:::analysis
FLASH shows how an existing encrypted transfer path can support recoverable confidential inference with shorter checkpoint pauses. Deployment decisions still depend on workload behavior, complete restore integration, and a durable trusted freshness service. The reported pause is one part of that assessment.
:::
