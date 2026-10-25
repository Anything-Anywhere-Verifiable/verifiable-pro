---
title: CSET Says Ping-Based Checks Backed by Inspections Are the Most Feasible Way to Track Exported AI Chips
dek: A Georgetown CSET report published on 29 September 2026 finds that ping-based checks, backed by physical inspections, are the most feasible and cost-effective way to verify where export-controlled AI chips are. The authors say such a system could only detect diversion after the fact, and they decline to say whether it should be required.
kind: news
topics: [governance-compute, confidential-computing]
layers: [institutions, hardware]
event_date: 2026-09-29
published: 2026-10-20
agent: daily
evidence: [report, regulation]
related: [chip-security-act-committee-approval, bis-h200-china-third-party-testing]
sources:
  - "Tracking AI Chips: Assessing Location Verification as an Export Control Enforcement Tool | Center for Security and Emerging Technology, Georgetown University | 2026-09 | https://cset.georgetown.edu/publication/tracking-ai-chips/"
  - "Tracking AI Chips: What Does It Cost? | Center for Security and Emerging Technology, Georgetown University | 2026-09-29 | https://cset.georgetown.edu/article/tracking-ai-chips-what-does-it-cost/"
  - Huizenga Amendment in the Nature of a Substitute #2 to H.R. 3447 | House Committee on Foreign Affairs (House Committee Repository) | 2026-03-17 | https://docs.house.gov/meetings/FA/FA00/20260326/118999/BILLS-1193447ANSih-U2.pdf
---

Georgetown University's Center for Security and Emerging Technology (CSET) published a report on 29 September 2026 that assesses location verification as a tool for enforcing US export controls on AI chips. Its authors, Jacob Feldgoise, Kyle Miller and Hanna Dohmen, compared methods on verifiability, accuracy, security and repeatability. They conclude that a centralized ping-based location verification (PLV) system, supplemented by physical inspections to investigate leads, would be the most robust and feasible approach. They make no recommendation on whether policymakers should mandate location verification.[^1, 2] A House committee's version of the [Chip Security Act](/articles/chip-security-act-committee-approval/) lists ping-based location verification as one acceptable mechanism.[^3]

In PLV, trusted landmark servers at known locations estimate a chip's location from the round-trip time of signals sent to it. The authors recommend that each chip sign its responses in the firmware of its trusted execution environment (TEE), an isolated area of the processor. They judge that this offers the best balance of security, cost and ease of implementation. One reason they give is that firmware updates can reach TEE-equipped chips already in use. Any implementation, they add, is unlikely to withstand state-backed attackers.[^1]

The report estimates that a PLV system would cost $3.1 million to $28.8 million a year if the landmark servers are owned. If they are rented, the estimate is $2.6 million to $72.4 million a year. In more than ten million simulated scenarios, physical inspections never detected more diverted chips per dollar than PLV. This held even though the authors deliberately chose model parameters that favor inspections.[^1, 2]

The authors also describe inherent limits. PLV can detect diversion only after it occurs. A chip that stops responding may be in storage or deliberately disconnected. Accuracy is likely no better than about 20 miles, so the system cannot reliably distinguish nearby data centers run by different operators. Because PLV verifies locations rather than users, it cannot detect a transfer to a restricted company in the same data center.[^1]

:::analysis
The report separates evidence about where a chip is from evidence about who is using it. PLV supplies only the first kind. That evidence is only as strong as the chip's firmware signing and the landmark servers, which the report considers vulnerable to well-resourced adversaries. Location checks can generate leads, but the authors say a change of user at the same site would need other rules, such as Know Your Customer due diligence.
:::

:::checked
On 20 October 2026 we read CSET's report page, the full report, the companion post and the committee-approved Chip Security Act text. The report is dated September 2026. The 29 September date comes from the companion post and the page's publication metadata. We did not rerun CSET's cost model or check its accuracy estimates.
:::
