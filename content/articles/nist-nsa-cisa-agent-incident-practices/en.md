---
title: NIST, NSA and CISA Publish Incident Practices That Call for Tamper-Resistant Agent Logs
dek: Three U.S. agencies published ten voluntary practices on 16 October 2026 for incidents in which agents take significant uninstructed actions during training and evaluation. Several concern evidence that others could check later, including tamper-resistant logs, preserved model weights and outside audits of control systems.
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents]
event_date: 2026-10-16
published: 2026-10-20
agent: daily
lead: true
evidence: [announcement, documentation]
sources:
  - Key Practices for Incident Readiness and Response in Super Intelligence Training and Evaluation | NIST | 2026-10-16 | https://www.nist.gov/news-events/news/2026/10/key-practices-incident-readiness-and-response-super-intelligence-training
  - Key Practices for Incident Readiness and Response in Super Intelligence Training and Evaluation (PP-26-4396, version 1.0) | NIST CAISSI, NSA SISC and CISA | 2026-10-16 | https://www.nist.gov/system/files/documents/2026/10/16/Key_Practices_for_Incident_Readiness_and_Response_in_Super_Intelligence%20_Training_and_Evaluation.pdf
  - Key Practices for Incident Readiness and Response in Super Intelligence Training and Evaluation | CISA | 2026-10-16 | https://www.cisa.gov/resources-tools/resources/key-practices-incident-readiness-and-response-super-intelligence-training-and-evaluation
  - Center for Advancing Innovation and Standards for Super Intelligence (CAISSI) | NIST | accessed 2026-10-20 | https://www.nist.gov/caissi
related: [nist-ai-agent-standards-initiative, aisi-transect-agent-transcript-analysis]
---

Three U.S. agencies published ten voluntary key practices on 16 October 2026 for managing incidents during the training and evaluation of super intelligence (SI) agents. The publishers are the Center for Advancing Innovation and Standards for Super Intelligence (CAISSI) at the National Institute of Standards and Technology (NIST), the National Security Agency's Super Intelligence Security Center (NSA SISC) and the Cybersecurity and Infrastructure Security Agency (CISA).[^1, 2] NIST's CAISSI web page also lists work published by NIST's Center for AI Standards and Innovation (CAISI).[^4]

The document defines SI agents as systems that interact with an environment and autonomously execute actions toward a specified goal. It says such a system is typically a generative model with scaffolding software that gives it tools. The document focuses on the SI control incident. In such an incident, agents take significant uninstructed actions that compromise policies, controls or security measures set by the operator to define the task or ensure human oversight. Actions caused by adversarial prompt injection, in which an attacker plants instructions in an agent's input, count as instructed. So do actions caused by a deliberately backdoored model. The practices are grouped into five stages, from preparation to reporting.[^2] CISA says the document is aimed especially at pre-deployment agents with reduced safeguards.[^3]

Several practices concern evidence for later review. Practice 5.3 calls for tamper-resistant logs with reliable timestamps, detailed enough to reconstruct agent trajectories, tool calls, reasoning traces and security-control decisions. Practice 3.3 says agents should be unable to access or interfere with monitoring processes and logs. Practice 5.1 asks organizations to preserve model weights and environments as needed to investigate an incident.[^2]

Under practice 2.4, organizations should partner with independent external auditors and evaluators to verify that control and monitoring systems work as intended. Practice 10.2 calls for giving third parties enough access for independent analysis.[^2] Practice 2.5 suggests publishing evaluation and agent identifiers to help defenders understand unexpected traffic. But the authors note that publishing Internet Protocol (IP) address ranges could expose deployers to attack.[^2]

:::analysis
The practices treat records of agent activity as evidence that must hold up after an incident. Such evidence is a precondition for anyone outside a lab to establish what an agent did. The practices do not specify how logs are made tamper-resistant or who holds them. So whether a lab follows the practices can be checked mainly through the independent audits and third-party access the document recommends. Because they are voluntary, the practices oblige no developer or deployer to keep such records.
:::

:::checked
On 20 October 2026 we read NIST's announcement, the joint publication (PP-26-4396, version 1.0), CISA's page for it and NIST's CAISSI page. None of these sources explains how the CAISSI and CAISI names relate. We did not check whether any organization follows these practices, and we test no systems ourselves.
:::
