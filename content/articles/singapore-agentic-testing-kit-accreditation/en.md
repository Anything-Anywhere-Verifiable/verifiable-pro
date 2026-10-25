---
title: Singapore Publishes Testing Kit for AI Agents and Accredits Five AI Testing Firms
dek: On 14 October 2026, Singapore's Infocomm Media Development Authority released a guide to testing agentic AI systems, and the AI Verify Foundation named the first five firms accredited to test AI systems for others. Accreditation gives buyers a reference point for choosing testers, within limits the foundation states.
kind: news
topics: [evaluation-audits]
layers: [evaluations]
event_date: 2026-10-14
published: 2026-10-20
agent: daily
evidence: [announcement, documentation]
sources:
  - Singapore Introduces New Initiatives to Strengthen AI Safety and Resilience | Infocomm Media Development Authority | 2026-10-14 | https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/new-initiatives-to-strengthen-ai-safety-and-resilience
  - Starter Kit for Testing Agentic Systems for Safety and Reliability, Version 1.0 | Infocomm Media Development Authority | 2026-10 | https://www.imda.gov.sg/assets/603572eb-724a-46cf-ac12-14fe38e1558c.pdf
  - AI Tester Accreditation Programme | AI Verify Foundation | accessed 2026-10-20 | https://aiverifyfoundation.sg/ai-assurance/tester-accreditation/
---

On 14 October 2026 Singapore's Infocomm Media Development Authority (IMDA) released a Starter Kit for Testing Agentic Systems for Safety and Reliability. On the same day, the AI Verify Foundation launched an accreditation program for companies that test AI systems on behalf of others.[^1] IMDA also formed a task force on AI-enabled cyber threats to the country's infocomm and media sector.[^1]

The kit starts from the observation that agents act on their environment with limited human involvement, so a malfunction can have real effects.[^2] It organizes testing into four steps, from identifying risks such as erroneous or unauthorized actions to continuous monitoring and re-testing.[^1]

Because agents take actions over multiple steps, the kit recommends testing an agent's entire trajectory, including its reasoning and actions, in addition to its final output.[^1, 2] It asks for logs of the agent's actions, tool calls and state changes, so that its behavior can be reconstructed and assessed. It also proposes agent-specific metrics such as tool use accuracy and handoff accuracy.[^2] IMDA says the kit draws on consultations with government agencies and more than 20 deployers and testers. It says the kit will be updated as a living document.[^1]

Firms seeking accreditation under the foundation's AI Tester Accreditation Programme undergo technical, operational and financial evaluations. The first five accredited firms are AIDX Tech, Knovel Engineering, PwC Singapore, Resaro and Vulcan. Accreditation lasts one year.[^1]

According to the foundation's program page, the technical evaluation checks a firm's claimed testing services against guidelines such as IMDA's earlier starter kit for testing large language model applications. The page says accreditation signifies that a firm has shown it can assess AI systems within a specific, documented scope of risks. It adds that accreditation is not a guarantee or certification that AI systems are completely safe or free from all risk.[^3]

:::analysis
Accreditation gives buyers of AI testing an outside assessment of a tester's competence, so they need not rely only on the tester's own description. It does not make an individual test result checkable, because a buyer still relies on the accredited firm's report. The assurance also covers only the documented scope. The kit's emphasis on logging agent trajectories matters for verification, because those logs are what a second tester or a later auditor could re-examine.
:::

:::checked
On 20 October 2026 we read IMDA's 14 October 2026 release, the Starter Kit (version 1.0, dated October 2026) and the AI Verify Foundation's program page. We did not review the accreditation assessments of the five firms or any test they performed, and we test no systems ourselves.
:::
