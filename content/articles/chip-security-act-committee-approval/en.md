---
title: House Committee Advances Chip Security Act With Location Verification as One of Several Options
dek: The House Foreign Affairs Committee voted 42-0 on 26 March 2026 to report a revised Chip Security Act to the full House. Under it, the Commerce Department would require exported data-center AI chips to be secured by mechanisms that can show whether they were diverted, with ping-based location checks as one listed option.
kind: news
topics: [governance-compute]
layers: [institutions, hardware]
event_date: 2026-03-26
published: 2026-10-20
agent: daily
evidence: [regulation, announcement]
related: [cset-ai-chip-location-verification, bis-h200-china-third-party-testing]
sources:
  - 3/26/2026 Foreign Affairs Markup Summary | House Committee on Foreign Affairs (House Committee Repository) | 2026-03-26 | https://docs.house.gov/meetings/FA/FA00/20260326/118999/HMKP-119-FA00-20260326-SD002-U1.pdf
  - Huizenga Amendment in the Nature of a Substitute #2 to H.R. 3447 | House Committee on Foreign Affairs (House Committee Repository) | 2026-03-17 | https://docs.house.gov/meetings/FA/FA00/20260326/118999/BILLS-1193447ANSih-U2.pdf
  - H.R. 3447, Chip Security Act, as introduced in the House | US Government Publishing Office (GovInfo) | 2025-05-15 | https://www.govinfo.gov/content/pkg/BILLS-119hr3447ih/html/BILLS-119hr3447ih.htm
  - "Bill status: H.R. 3447 (119th Congress), Chip Security Act | US Government Publishing Office (GovInfo bulk data) | 2026-10-10 | https://www.govinfo.gov/bulkdata/BILLSTATUS/119/hr/BILLSTATUS-119hr3447.xml"
---

The House Foreign Affairs Committee voted 42-0 on 26 March 2026 to report the Chip Security Act, H.R. 3447, to the House as amended.[^1] The committee worked from a substitute, a replacement text for the whole bill, offered by Representative Bill Huizenga of Michigan. Huizenga had introduced the bill on 15 May 2025.[^1, 4]

As introduced, the bill would have given the Commerce Department 180 days from enactment to mandate location verification mechanisms on covered AI chips and computers before export.[^3] Under the committee's text, Commerce would instead have one year to require that covered products sent abroad be secured by a chip security mechanism. The mechanism would have to enable reliable verification of whether a product was illegally diverted to destinations of concern, to the maximum extent practicable.[^2] The text names three examples:

- periodic on-site audits at the approved destination
- attestations by a US-headquartered company that keeps secure control of the chips
- ping-based location verification through a trusted landmark server using secure software or firmware, a method that estimates where a chip is from how quickly it answers the server

Commerce could also accept other mechanisms if it determines that they show with significant confidence that a product was not diverted.[^2]

The text states that nothing in it directs Commerce to require mechanisms that could hinder a chip's functionality, such as a kill switch or geofencing. It also states that nothing in it directs Commerce to mandate location verification that requires hardware changes. It covers only items designed or marketed for data centers and does not apply to products in the United States. A final rule would require reports to Commerce's Bureau of Industry and Security whenever the mechanisms fail to confirm that a product has not been diverted. The reporting requirement includes cases with evidence of spoofing or other tampering. Commerce could waive the requirements on competitiveness and national security grounds after giving Congress 30 days' notice.[^2]

GovInfo's bill status record lists the committee vote as the latest action. A Senate bill of the same name, S. 1705, has remained with the Senate Banking Committee since 8 May 2025.[^4]

:::analysis
The committee's text calls for reliable evidence of whether a chip was diverted and leaves the choice of evidence to Commerce. A ping-based check relies on trusted landmark servers and on the chip's software or firmware, while a company attestation rests on that company's control of the chips. The text does not direct Commerce to mandate hardware changes, so the strength of a ping-based check may depend on how well that software or firmware resists spoofing. The bill leaves this question to later Commerce assessments.
:::

:::checked
On 20 October 2026 we read the committee's markup summary and substitute text, the introduced text and GovInfo's bill status record, updated 10 October 2026. The Congressional Budget Office's 1 May 2026 cost estimate did not load for us. We found no committee report and did not assess whether chipmakers could comply.
:::
