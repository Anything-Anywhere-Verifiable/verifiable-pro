---
title: NIST Launches AI Agent Standards Initiative and Seeks Input on Agent Identity and Authorization
dek: NIST's Center for AI Standards and Innovation launched the initiative on 17 February 2026 to support industry-led standards and open protocols for AI agents. The consultations it pointed to asked how agents should be identified, authorized and audited, which bears on whether an agent's actions can later be attributed.
kind: news
topics: [agents-accountability]
layers: [agents]
event_date: 2026-02-17
published: 2026-10-20
agent: daily
evidence: [announcement, documentation]
sources:
  - Announcing the "AI Agent Standards Initiative" for Interoperable and Secure Innovation | NIST | 2026-02-17 | https://www.nist.gov/news-events/news/2026/02/announcing-ai-agent-standards-initiative-interoperable-and-secure
  - New Concept Paper on Identity and Authority of Software Agents | NIST National Cybersecurity Center of Excellence | 2026-02-05 | https://www.nist.gov/news-events/news/2026/02/new-concept-paper-identity-and-authority-software-agents
  - CAISI Issues Request for Information About Securing AI Agent Systems | NIST | 2026-01-12 | https://www.nist.gov/news-events/news/2026/01/caisi-issues-request-information-about-securing-ai-agent-systems
  - NCCoE Agentic AI Identity and Authorization Project Resource Hub | NIST National Cybersecurity Center of Excellence | accessed 2026-10-20 | https://pages.nist.gov/nccoe-ai-identity/
  - Center for Advancing Innovation and Standards for Super Intelligence (CAISSI) | NIST | accessed 2026-10-20 | https://www.nist.gov/caissi
related: [nist-nsa-cisa-agent-incident-practices, mcp-july-2026-specification]
---

On 17 February 2026 the Center for AI Standards and Innovation (CAISI) at the National Institute of Standards and Technology (NIST) announced the AI Agent Standards Initiative. NIST says the initiative is meant to help AI agents work securely on behalf of their users and interoperate across the digital ecosystem.[^1] NIST's web page for the center now uses the name Center for Advancing Innovation and Standards for Super Intelligence (CAISSI).[^5]

CAISI will pursue the initiative with NIST's Information Technology Laboratory (ITL), the National Science Foundation and other agencies. The initiative has three pillars. The first is industry-led development of agent standards and U.S. leadership in international standards bodies. The second is community-led open-source protocols for agents. The third is research on agent security and identity.[^1]

The announcement pointed to two consultations. The first was CAISI's request for information on AI agent security, published on 12 January with comments due on 9 March. It focused on risks that arise when AI model outputs are combined with the functionality of software systems. These risks include indirect prompt injection (instructions hidden in content an agent processes) and data poisoning (tampering with the data a model learns from). The request also asked how to constrain and monitor agents' access in deployment.[^1, 3]

The second was a concept paper from ITL's National Cybersecurity Center of Excellence (NCCoE), released on 5 February with comments due on 2 April. It sought input on applying identity standards and best practices to AI agents. It included detailed questions on the identification, authorization, auditing and non-repudiation of agents.[^1, 2] Non-repudiation means that an agent's actions cannot later be falsely denied.

The NCCoE's project site now says the paper drew more than 600 responses. According to the site, the center is setting up a project on agentic AI identity and authorization. The site says the project's final deliverable will be a practice guide in NIST's Special Publication 1800 series, with example implementations built in NCCoE laboratories.[^4]

:::analysis
Identity and authorization standards shape whether an agent's actions can later be attributed to a specific agent and to the person or organization that authorized it. By asking about auditing and non-repudiation, the NCCoE consultation treats the record of an agent's actions as part of the identity problem. An outside reviewer would need that record to check an agent's conduct. The sources we reviewed describe consultations and a planned project, so what the initiative will ask of agent developers remains open.
:::

:::checked
On 20 October 2026 we read NIST's announcement, its news items on the request for information and the concept paper, the NCCoE's project site and NIST's current page for the center. The last two pages show no date, so the dates in our source list are the day we read them. We did not read the full request for information, the concept paper or the public comments, and we test no systems ourselves.
:::
