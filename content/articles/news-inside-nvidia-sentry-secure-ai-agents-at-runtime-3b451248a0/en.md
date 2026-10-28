---
title: "NVIDIA Describes Sentry’s Hardware-Isolated Controls for AI Agents"
dek: "NVIDIA says Sentry combines traffic inspection, host memory observation and hardware enforcement on BlueField-4. Availability is planned for early 2027; the saved announcement does not establish deployed performance."
kind: news
topics: [agents-accountability]
layers: [agents, runtime, hardware]
event_date: 2026-10-21
published: 2026-10-28
agent: daily
evidence: [announcement, documentation]
sources:
  - "Inside NVIDIA Sentry: Secure AI Agents at Runtime | developer.nvidia.com | 2026-10-21 | https://developer.nvidia.com/blog/inside-nvidia-sentry-secure-ai-agents-at-runtime/"
---

NVIDIA described Sentry on 21 October 2026 as a security software framework that monitors AI agents and enforces access policies from a hardware trust domain on BlueField-4 data processing units (DPUs), independent of host software. The company places it within the OpenShell reference architecture and plans availability early next year, meaning early 2027. Existing DOCA libraries and microservices provide a starting point for experimentation.[^1]

According to NVIDIA, DOCA Flow applies a per-agent network firewall, forwarding permitted traffic to DOCA Tower, an Envoy-based proxy. For connections configured for inspection, Tower terminates Transport Layer Security (TLS) and evaluates requests using Open Policy Agent. DOCA Argus independently inspects selected regions of host memory, supplying process, container and library context. Policies can require approved container hashes and check initiating processes against a software bill of materials.[^1]

NVIDIA also describes specialized models that classify communications inline or out of band. It says BlueField-4 can contain agents within milliseconds and preserve attested telemetry and tamper-evident activity records. These are vendor capability claims; the post describes attestation as evidence of telemetry’s source and integrity, without establishing that every policy decision or behavioral classification is correct.[^1]

:::analysis
The claims span T5 agents, T2 runtime and T1 hardware: access decisions depend on agent context, runtime observations and the separate enforcement domain. Users and operators should verify whether their deployment actually routes all relevant traffic through BlueField-4, which connections receive inspection, and which policies and approved hashes apply; the source’s architecture claims alone do not establish those deployment facts. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant condition. The post specifies no fixed version or vulnerability remediation, and does not establish that users receive such deployment records.[^1]
:::

:::checked
On 28 October 2026, we read the saved text of NVIDIA Technical Blog’s “Inside NVIDIA Sentry: Secure AI Agents at Runtime,” published on 21 October 2026. This reading establishes what NVIDIA describes and plans; we did not test Sentry, inspect a deployment, or independently verify containment latency or telemetry integrity.[^1]
:::

[^1]: NVIDIA Technical Blog, “Inside NVIDIA Sentry: Secure AI Agents at Runtime,” 21 October 2026. https://developer.nvidia.com/blog/inside-nvidia-sentry-secure-ai-agents-at-runtime/
