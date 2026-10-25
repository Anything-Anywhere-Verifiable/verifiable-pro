---
title: Researchers Say DDRop Memory Interposer Can Forge Intel TDX Attestation
dek: On 14 September 2026, a team from KU Leuven, ETH Zurich, Durham University and Google disclosed DDRop, a low-cost device that silently drops DDR5 memory writes. Intel and AMD say such physical attacks fall outside their confidential computing threat models.
kind: news
topics: [confidential-computing]
layers: [runtime, hardware]
event_date: 2026-09-14
published: 2026-10-20
agent: daily
evidence: [announcement]
sources:
  - "DDRop: Active Memory Interposer Attacks on Confidential VMs by Dropping DDR5 Writes (project site) | DDRop researchers (KU Leuven, ETH Zurich, Durham University, Google) | 2026-09-14 | https://ddropattack.eu/"
  - DDRop – Physical Memory Interposer Research | Intel | 2026-09-14 | https://www.intel.com/content/www/us/en/security-center/announcement/intel-security-announcement-2026-08-11-001.html
  - Physical Memory Fault Injection Attacks on DDR5 (AMD-SB-3048) | AMD | 2026-09-14 | https://www.amd.com/en/resources/product-security/bulletin/amd-sb-3048.html
---

Researchers from KU Leuven, ETH Zurich, Durham University and Google disclosed DDRop on 14 September 2026, after sharing their findings with Intel and AMD. DDRop is a small hardware interposer on a server's DDR5 memory bus. It silently discards selected memory writes. As a result, a confidential virtual machine (VM), whose memory the hardware encrypts, later reads old data that still decrypts correctly. Their paper is listed for the 2026 ACM Conference on Computer and Communications Security.[^1]

The researchers say the memory encryption in Intel Trust Domain Extensions (TDX), Intel's Scalable Software Guard Extensions (SGX) and AMD Secure Encrypted Virtualization-Secure Nested Paging (SEV-SNP) keeps data confidential but does not provide freshness. Without freshness, they say, the processor cannot tell whether a value in memory is current. In TDX's default integrity mode, they report forcing a victim VM into debug mode so the hypervisor, the software that manages virtual machines, can read its memory. They also report overwriting the launch measurement of a rogue VM under their control, even in TDX's stronger cryptographic integrity mode. The launch measurement, which remote attestation reports, is a hash of the software the VM started with. They say the rogue VM then passes remote attestation as a legitimate workload. The parts for one interposer cost $159 at a build quantity of ten, according to the team's bill of materials, which excludes labor.[^1]

The attack assumes an adversary who controls the host operating system, hypervisor and BIOS. The adversary also needs a brief, one-time physical visit to install the device. After that, the attack runs in software. The team lists data-center insiders, supply-chain tampering and compelled access as possible routes to the hardware.[^1]

Intel's announcement says the scenarios fall outside its standard threat model, the attacks its confidential computing technology is designed to resist. Intel recommends limiting physical access and protecting the supply chain, and says it is evaluating further hardening and detection options.[^2] AMD's bulletin says the technique falls outside the published SEV-SNP threat model. It says AMD does not plan to assign a Common Vulnerabilities and Exposures (CVE) identifier or release mitigations.[^3] The researchers say software or firmware updates can make the attack harder, but a lasting fix would require memory encryption with integrity and freshness.[^1]

:::analysis
Some services ask clients to check remote attestation before sending data. For them, the researchers' TDX results mean that a valid report cannot by itself rule out an operator with physical access to the server. Claims that such a service excludes its operator therefore also depend on how physical access to the hardware is controlled, which attestation does not show.
:::

:::checked
On 20 October 2026 we opened the DDRop project site and the Intel and AMD advisories, all dated 14 September 2026. We did not reproduce the attack, examine the hardware designs or confirm the cost figure, and did not check which AI services use the affected platforms. We test no systems ourselves.
:::
