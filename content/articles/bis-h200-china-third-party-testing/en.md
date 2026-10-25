---
title: BIS Moves H200-Class Chip Exports to China to Case-by-Case Review With US Lab Testing
dek: A US export rule that took effect on 15 January 2026 allows case-by-case review of license applications to export chips such as the NVIDIA H200 to China. An independent US lab must confirm each shipment's performance specifications, while the rule's other conditions rest on the exporter's certifications.
kind: news
topics: [governance-compute]
layers: [institutions, hardware]
event_date: 2026-01-15
published: 2026-10-20
agent: daily
evidence: [regulation, announcement, report]
related: [chip-security-act-committee-approval, cset-ai-chip-location-verification]
sources:
  - Revision to License Review Policy for Advanced Computing Commodities (91 FR 1684) | Bureau of Industry and Security, Federal Register | 2026-01-15 | https://www.federalregister.gov/documents/2026/01/15/2026-00789/revision-to-license-review-policy-for-advanced-computing-commodities
  - Department of Commerce Revises License Review Policy for Semiconductors Exported to China | Bureau of Industry and Security | 2026-01-13 | https://www.bis.gov/press-release/department-commerce-revises-license-review-policy-semiconductors-exported-china
  - NVIDIA Corporation Form 10-Q for the quarter ended 26 July 2026 | NVIDIA (filing with the US Securities and Exchange Commission) | 2026-08-26 | https://www.sec.gov/Archives/edgar/data/1045810/000104581026000075/nvda-20260726.htm
  - "New BIS Licensing Policy for H200s: Tough Guidelines, Weak Enforcement | Institute for AI Policy and Strategy | 2026-01-16 | https://www.iaps.ai/research/bis-licensing-policy-for-h200s"
---

The US Commerce Department's Bureau of Industry and Security (BIS) issued a rule that was published and took effect on 15 January 2026. It applies to license applications to export certain advanced AI chips from the United States to China or Macau. If the exporter submits certain certifications, an application can receive case-by-case review instead of a presumption of denial. The policy covers chips below a total processing performance (TPP) of 21,000 and a total dynamic random-access memory (DRAM) bandwidth of 6,500 GB/s. TPP is a measure of computing power defined in US export rules. Covered chips include the NVIDIA H200 and AMD MI325X.[^1]

Before export, a qualified third-party lab must review every shipment. It must confirm that the chips' TPP, DRAM bandwidth, interconnect bandwidth and co-packaged DRAM capacity do not exceed the figures in the license application. The lab must be headquartered in the United States, test there and have no financial stake in any party to the transaction. It may test a representative sample of each batch. The rule's summary says the testing verifies performance specifications,[^1] while BIS's announcement says it verifies performance and security.[^2]

The other conditions are certifications by the exporter, some based on information from the buyer. Exporters must show that sales to China will not delay US orders or divert foundry capacity. They must show that exports to China and Macau will total at most half of the chip's cumulative US shipments. They must also describe the buyer's physical security and its Know Your Customer procedures against unauthorized remote access. The rule says BIS will routinely confirm relevant elements of the certifications by methods it deems appropriate.[^1] The Institute for AI Policy and Strategy (IAPS) argued on 16 January that BIS has no way to verify the supply and foundry claims. IAPS also argued that once the chips leave the United States, BIS has almost no leverage to enforce buyers' security plans.[^4]

NVIDIA said on 26 August 2026 that licenses granted since February let it ship small amounts of H200 chips, inspected in the United States, to specific customers in China. But it said Chinese government restrictions have limited its sales.[^3]

:::analysis
Only the lab test brings in an independent party, and it checks the chips' technical specifications. After delivery, the remote-access and security commitments depend on the buyer's procedures and on checks the rule leaves to BIS. The rule requires no means of confirming where the chips go after export. Proposals such as the [Chip Security Act](/articles/chip-security-act-committee-approval/) take up that question.
:::

:::checked
On 20 October 2026 we read the Federal Register rule, BIS's announcement, the IAPS memo and NVIDIA's filing. We found no public list of qualified labs or of licenses granted, and could not determine how BIS checks the certifications in practice. We did not verify NVIDIA's account of its shipments.
:::
