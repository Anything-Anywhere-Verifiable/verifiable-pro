---
title: Singapore's Revised Agentic AI Framework Calls for Cryptographically Verifiable Agent Identities
dek: Singapore updated its Model AI Governance Framework for Agentic AI on 20 May 2026. The revised text's additions to the January version include two measures: each AI agent should have a cryptographically verifiable identity, and records of agent failures should not be deletable.
kind: news
topics: [agents-accountability]
layers: [institutions, agents]
event_date: 2026-05-20
published: 2026-10-20
agent: daily
evidence: [announcement, documentation]
sources:
  - Opening Address by Minister Josephine Teo at ATxSummit 2026 | Ministry of Digital Development and Information | 2026-05-20 | https://www.mddi.gov.sg/newsroom/opening-address-by-minister-josephine-teo-at-atxsummit-2026/
  - Model AI Governance Framework for Agentic AI, Version 1.5 (updated 5 June 2026) | Infocomm Media Development Authority | 2026-05-20 | https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf
  - Model AI Governance Framework for Agentic AI, Version 1.0 (Internet Archive copy captured 23 January 2026) | Infocomm Media Development Authority | 2026-01-22 | https://web.archive.org/web/20260123193221/https://www.imda.gov.sg/-/media/imda/files/about/emerging-tech-and-research/artificial-intelligence/mgf-for-agentic-ai.pdf
  - Singapore Launches New Model AI Governance Framework for Agentic AI | Infocomm Media Development Authority | 2026-01-22 | https://www.imda.gov.sg/resources/press-releases-factsheets-and-speeches/press-releases/2026/new-model-ai-governance-framework-for-agentic-ai
related: [singapore-agentic-testing-kit-accreditation, nist-ai-agent-standards-initiative]
---

Singapore's Minister for Digital Development and Information, Josephine Teo, said on 20 May 2026 that the government was updating its Model AI Governance Framework for Agentic AI. She said the update adds case studies of agent deployments by companies such as PwC and Workday.[^1] The Infocomm Media Development Authority (IMDA) marks version 1.5 as published that day and updated on 5 June. IMDA says the revision incorporates feedback from more than 60 companies.[^2]

Teo launched the framework at the World Economic Forum in Davos on 22 January 2026. IMDA describes it as guidance for organizations that deploy AI agents, whether they build the agents in-house or use third-party products.[^4]

On agent identity, the January version 1.0 asked that each agent have its own unique identity. The purpose was to let the agent identify itself to its organization, its human user or other agents. Version 1.0 also asked that delegations of authority be clearly recorded.[^3] Version 1.5 adds that this identity should be cryptographically verifiable. It also says that a central system should issue and track all agent identities, so that an organization can track its deployed agents and remove identities it no longer needs. Authorizations should generally be limited in scope, tied to a time or session, and non-transferable.[^2]

Version 1.5 also suggests keeping complete audit trails by ensuring that records of an agent's problematic actions and failures cannot be deleted.[^2]

Version 1.0 called for regular audits of whether human oversight remains effective.[^3] For those audits, the revision proposes measures that include reviewers' response times and the override rate, meaning how often reviewers reject or modify agent actions. It says a low override rate may signal rubber-stamping, in which reviewers approve actions without real scrutiny.[^2]

:::analysis
Version 1.5 asks for properties that someone outside the deploying organization could, in principle, test: an identity that other agents can verify cryptographically, and failure records that cannot be deleted. The framework is guidance and prescribes no identity scheme or logging mechanism. So whether a counterparty can verify an agent, or an auditor can confirm that no records were removed, will depend on the systems each organization adopts. Override rates turn the effectiveness of human review into numbers, but the deploying organization produces those numbers itself.
:::

:::checked
On 20 October 2026 we read Teo's address of 20 May 2026, version 1.5 of the framework and IMDA's press release of 22 January 2026. IMDA's link now serves version 1.5 as updated on 5 June 2026, so we could not see the text as first published on 20 May. We read version 1.0 in an Internet Archive copy captured on 23 January 2026. We did not review the case studies or check how any organization applies the framework.
:::
