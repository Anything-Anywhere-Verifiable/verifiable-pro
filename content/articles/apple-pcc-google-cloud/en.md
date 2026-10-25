---
title: Apple Says It Is Extending Private Cloud Compute to Google Cloud
dek: On 8 June 2026, Apple said new Apple Intelligence workloads would run on Google Cloud hardware under its Private Cloud Compute commitments. Apple's release notes say its research tool cannot yet parse attestations from the new deployment.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-06-08
published: 2026-10-20
agent: daily
evidence: [announcement, documentation]
sources:
  - Expanding Private Cloud Compute | Apple Security Research | 2026-06-08 | https://security.apple.com/blog/expanding-pcc/
  - NVIDIA Confidential Computing to Help Expand Apple's Private Cloud Compute | NVIDIA | 2026-06-09 | https://blogs.nvidia.com/blog/nvidia-confidential-computing-apple-private-cloud-compute/
  - "Private Cloud Compute Security Guide: Release Notes | Apple | accessed 2026-10-20 | https://security.apple.com/documentation/private-cloud-compute/releasenotes"
---

Apple said on 8 June 2026 that it is expanding Private Cloud Compute (PCC) beyond its own data centers. PCC is Apple's cloud system for Apple Intelligence tasks too complex for on-device models. For the most demanding tasks, including agentic tool use and complex reasoning, Apple worked with Google and NVIDIA to extend PCC to Google Cloud systems with NVIDIA GPUs. Apple said this is the first time its PCC privacy commitments extend to third-party data centers.[^1]

Apple said PCC's core requirements are unchanged. It said the new implementation combines NVIDIA Confidential Computing on NVIDIA GPUs, Intel CPUs with Trust Domain Extensions (TDX) and Google's Titan chip.[^1] NVIDIA said the next day that the deployment uses its Blackwell GPUs.[^2]

To reduce the risk of supply-chain attacks, Apple says it keeps a cryptographically verifiable, append-only ledger of all Google Cloud hardware in the PCC fleet. For components that could leak user data if compromised, Apple says its software attestation is rooted in at least two roots of trust from independent vendors. An attestation is a signed record of the software a machine loaded, and a root of trust is a component trusted without further checks. Apple adds that its devices will trust only PCC software it has cryptographically approved.[^1]

Apple said it would publish all binaries and give researchers public tooling and access to live PCC nodes in research mode through the Apple Security Bounty. It said PCC on Google Cloud would move gradually toward its complete set of protections during a summer preview period.[^1]

As of 20 October 2026, the release notes in Apple's PCC Security Guide say a public security research program for PCC on Google Cloud will launch later this year. A known issue in the notes says Apple's research tool, `pccvre`, does not yet parse attestations from PCC on Google Cloud or the deployment's releases in the PCC transparency log. Apple says support will come when the program launches.[^3]

:::analysis
PCC's transparency model relies on researchers comparing the software that devices trust with the software Apple publishes. Because Google Cloud has no Apple silicon, Apple's claim that the same protections apply there rests on new mechanisms such as the hardware ledger and the two roots of trust. Until Apple's tool can read the new attestations and log entries, outsiders cannot check the deployment with Apple's tooling and must rely on Apple's description.
:::

:::checked
On 20 October 2026 we read Apple's 8 June 2026 post, NVIDIA's 9 June post and the PCC Security Guide's release notes. The release notes are undated, so the date in our source list is the day we read them. We found no published details of the research program on Apple's security research site. We test no systems ourselves and did not verify Apple's claims about the hardware ledger, the attestation design or the preview's progress.
:::
