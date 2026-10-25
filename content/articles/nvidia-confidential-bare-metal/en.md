---
title: NVIDIA Introduces Confidential Bare Metal for Model Builders on Third-Party Infrastructure
dek: On 21 October 2026 NVIDIA introduced Confidential Bare Metal, a mode in which a model builder runs its own host software and attestation checks on dedicated NVIDIA systems that another company operates. Its documentation says the operator stays outside the builder's runtime trust boundary, while the mode does not protect the data of the builder's own end users from the builder.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-10-21
published: 2026-10-25
agent: daily
evidence: [announcement, documentation]
related: [cohere-model-vault-confidential-computing, google-confidential-g4-blackwell-ga, deepmind-double-blind-gemini-evaluation]
sources:
  - NVIDIA Confidential Computing Expands, Enabling Frontier Model Builders to Securely Scale Across Global Infrastructure | NVIDIA | 2026-10-21 | https://blogs.nvidia.com/blog/confidential-computing-model-builders-infrastructure/
  - Confidential Bare Metal (documentation, version Dev) | NVIDIA | accessed 2026-10-25 | https://docs.nvidia.com/confidential-computing/bare-metal/dev
  - Trust and Threat Model (Confidential Bare Metal documentation, version Dev) | NVIDIA | accessed 2026-10-25 | https://docs.nvidia.com/confidential-computing/bare-metal/threat-model
  - Google Cloud and NVIDIA expand co-engineering collaboration to scale infrastructure for the agentic era | Google Cloud | 2026-10-21 | https://cloud.google.com/blog/topics/ai-infrastructure/google-cloud-infrastructure-at-nvidia-gtc-berlin-2026
---

On 21 October 2026 NVIDIA introduced Confidential Bare Metal (CBM), a deployment mode for NVIDIA Confidential Computing. The company says CBM lets model builders run their own software, host included, on dedicated NVIDIA systems that third-party clouds and enterprises operate, and keep control of their models and data.[^1]

The documentation says this release covers Grace Blackwell rack-scale and Vera Rubin platforms. The builder controls the host operating system and drivers, the workload, its keys and its remote attestation policy. Before releasing model weights or other secrets, it appraises fresh platform evidence and the measurements (hashes) of the loaded software that a dynamic root of trust for measurement (DRTM) records at launch. No confidential virtual machine (CVM) is required, and NVIDIA tells builders to plan for substantial engineering.[^2]

After handoff and that appraisal, NVIDIA says, the operator stays outside the builder's runtime trust boundary and has no authority to read the workload's unencrypted data. It still runs power, the baseboard management controller (BMC), fabric and storage, and can remove power or block traffic. Because the builder's administrators and software stay trusted, CBM does not protect end users' data from the builder. NVIDIA describes adding a CVM for that case.[^2, 3]

The documentation also lists limits. On the Grace Blackwell baseline, CPU-to-GPU and CPU-to-CPU links are unencrypted, hardware encryption of PCI Express traffic is unavailable, and NVLink encryption for GPU-to-GPU traffic does not cover those links or network traffic. CPU memory encryption alone does not protect against alteration or replay, and CBM offers no general protection against invasive hardware attacks or timing, cache and power side channels.[^3]

NVIDIA says Cohere plans to integrate CBM into [Model Vault](/articles/cohere-model-vault-confidential-computing/).[^1] Google Cloud says it is introducing CBM on A4X Max instances with GB300 NVL72 systems.[^4]

:::analysis
CBM lets a model builder check hardware that someone else operates before releasing its keys. The builder still trusts NVIDIA's hardware, firmware and reference values, and relies on the operator's physical safeguards where links are unencrypted. CBM alone gives the builder's end users nothing to check: the builder's verifiers read the evidence, and its software stays trusted with their data.
:::

:::checked
On 25 October 2026 we read NVIDIA's blog post, two undated CBM documentation pages and Google Cloud's post. The documentation's only version, Dev, is labeled Beta, and no source gives an availability date. The blog lists systems and cloud providers for NVIDIA Confidential Computing in general; beyond Google Cloud and the platforms the documentation names, we could not confirm which offer CBM. The documentation does not name the DRTM's CPU mechanism or say whether NVLink Switch or BMC state is attested. We tested no deployment.
:::
