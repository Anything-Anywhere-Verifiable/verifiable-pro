---
title: Lava Says Exposed Monitoring Endpoints at China-Geolocated Addresses Reported 32 NVIDIA B300 GPUs
dek: The security company Lava said on 22 October 2026 that GPU monitoring endpoints left open to the internet, at addresses geolocated to China, reported 32 NVIDIA B300 chips. Lava says IP geolocation is not definitive and that the finding does not establish an export-control violation.
kind: news
topics: [governance-compute]
layers: [institutions, hardware]
event_date: 2026-10-22
published: 2026-10-25
agent: daily
evidence: [report, documentation]
related: [cset-ai-chip-location-verification, chip-security-act-committee-approval, bis-h200-china-third-party-testing]
sources:
  - We Analyzed 12,000+ GPUs. Here's What We Found About the AI Boom | Lava | 2026-10-22 | https://lava.security/blog/nvidia-b300-gpus-china
  - DCGM Exporter (repository README) | NVIDIA on GitHub | accessed 2026-10-25 | https://github.com/NVIDIA/dcgm-exporter
  - CVE-2026-47483: How We Could Disrupt Thousands of Exposed GPU Servers | Lava | 2026-10-08 | https://lava.security/blog/cve-2026-47483-nvidia-dcgm-exporter-vulnerability
  - Security Bulletin: NVIDIA DCGM Exporter - July 2026 | NVIDIA on GitHub | 2026-07-28 | https://github.com/NVIDIA/product-security/blob/main/2026/5857/5857.md
  - Lava uncovers banned Nvidia chips linked to China Telecom addresses | Crypto Briefing | 2026-10-22 | https://cryptobriefing.com/lava-nvidia-b300-chips-china-telecom/
---

The security company Lava said on 22 October 2026 that it identified 32 B300 graphics processing units (GPUs), from NVIDIA's Blackwell Ultra generation, through publicly reachable monitoring endpoints whose Internet Protocol (IP) addresses geolocate to China. Lava says the finding raises questions about the hardware's location and supply chain but "does not establish that any export-control violation occurred."[^1]

Lava says the endpoints ran DCGM Exporter, an NVIDIA tool that publishes GPU telemetry from NVIDIA Data Center GPU Manager (DCGM) for monitoring software such as Prometheus.[^1, 2] Lava also says they disclosed GPU model names and device identifiers without authentication. Across several scans, it counted 4,724 unique NVIDIA GPUs at China-geolocated addresses, including 374 of four Blackwell models. Lava's initial analysis puts about 86% of the Blackwell GPUs in eight-GPU configurations, which it says fit compute servers. Another 1,156 were consumer RTX 4090s, which Lava says have been under US export restrictions since 2023.[^1]

Lava cautions that IP geolocation is not definitive, since a proxy, virtual private network (VPN) or tunnel could relay traffic through an address in China while the hardware is elsewhere. It adds that one endpoint can report for several machines. The post lists no addresses and masks device identifiers in its example.[^1]

Lava's earlier post, on 8 October 2026, covered four scans between March and May 2026 that found about 2,100 hosts serving DCGM Exporter metrics without authentication. They reported more than 12,000 unique GPUs, 1,967 of them at endpoints in China. That post also reported a flaw, CVE-2026-47483, that let unauthenticated requests crash the exporter.[^3] NVIDIA's bulletin lists version 4.8.2 as the fix.[^4]

:::analysis
Lava's evidence is monitoring data meant for internal use, which shows what the software at each address reported. The location comes from address lookups, which Lava calls not definitive, so the data does not establish where a chip is or who controls it. Without addresses or raw data, outsiders cannot check Lava's counts. [Location verification](/articles/cset-ai-chip-location-verification/), as proposed for export enforcement, would instead time a chip's signed responses to servers at known locations.
:::

:::checked
On 25 October 2026 we read Lava's posts of 8 and 22 October, NVIDIA's security bulletin and DCGM Exporter repository, and reports by Crypto Briefing, TokenPost and Tom's Hardware. The newer post gives no dates for its China scans and does not explain why its China count exceeds the earlier 1,967. Nor does it say whether Lava told NVIDIA or US export authorities about the B300s. Crypto Briefing, which says The Information first reported the findings, links the B300 addresses to a Chinese carrier.[^5] Lava's posts name no network for them, and we could not confirm the link.
:::
