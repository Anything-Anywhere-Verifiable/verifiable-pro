---
title: "CSA Reports SGLang Incident and SEV-SNP Attacks on Confidential AI"
dek: "A Cloud Security Alliance research note examines an inference-server compromise and two attacks on AMD’s confidential virtual machine technology, highlighting separate software and hardware trust boundaries."
kind: news
topics: [confidential-computing, verifiable-inference]
layers: [runtime, hardware]
event_date: 2026-11-16
published: 2026-11-21
agent: daily
evidence: [announcement, documentation]
sources:
  - "Confidential AI Under Pressure: SGLang RCE and SEV-SNP Attacks | labs.cloudsecurityalliance.org | 2026-11-16 | https://labs.cloudsecurityalliance.org/research/csa-research-note-confidential-ai-inference-tee-limits-20261/"
---

The Cloud Security Alliance (CSA) published a research note on 16 November 2026 examining an SGLang compromise at NEAR AI and two attacks on AMD’s SEV-SNP confidential virtual machine technology. The note draws on incident reports, advisories and research; its account does not establish that the attacks are connected.[^1]

CSA reports that NEAR AI disclosed an attacker’s use of a remote code execution vulnerability in the SGLang inference engine to compromise one inference server and move into other infrastructure. NEAR AI said requests processed on that server on 8 November, including confidential-mode requests, could have been observed; it did not say whether anyone actually read them. The company did not identify the exploited SGLang flaw. CSA says NEAR AI deployed its own fix and reported the flaw upstream.[^1]

Separately, CSA describes Mior and Skyfall, attacks that assume a malicious host or hypervisor. According to the note, Mior requires hypervisor and BIOS control and can enable guest-memory access and forged attestation reports on an unpatched platform. Skyfall can leak guest register state through a side channel. CSA says full mitigation depends on firmware and BIOS updates from platform owners and manufacturers.[^1]

:::analysis
The issues sit at T2, runtime, where users must trust the inference software handling their requests, and T1, hardware, where verifiers depend on the platform and its firmware. Attestation evidence can identify a loaded build, but it does not establish that the build is free of vulnerabilities; the note also warns that Mior can forge reports on an unpatched platform.[^1]

The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed. Operators should inventory SGLang deployments, restrict access and track upstream fixes; CSA reports no fixed release for one tracked flaw as of 16 November. Users and verifiers should ask providers about remediation, enforce the applicable minimum SEV firmware values, and seek confirmation of BIOS updates because the firmware values alone may not establish that those updates are installed.[^1]
:::

:::checked
On 21 November 2026 we read the saved Cloud Security Alliance research note, [Confidential AI Under Pressure: SGLang RCE and SEV-SNP Attacks](https://labs.cloudsecurityalliance.org/research/csa-research-note-confidential-ai-inference-tee-limits-20261/).[^1] We did not independently open its underlying incident reports or advisories, or test the systems, attacks or fixes.
:::
