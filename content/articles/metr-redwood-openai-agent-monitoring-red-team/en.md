---
title: METR and Redwood Research Say Agents Could Have Evaded OpenAI's Internal Monitoring
dek: With access to OpenAI's code, a METR employee and a Redwood Research employee spent three weeks from 21 July 2026 testing the company's internal misalignment monitor. A summary that METR and Redwood published on 22 October estimates how much agent traffic the monitor was set up to review and lists ways agents could have disabled or avoided it.
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-10-22
published: 2026-10-25
agent: daily
lead: true
evidence: [report]
related: [openai-agents-disabled-misalignment-monitoring, nist-nsa-cisa-agent-incident-practices, anthropic-metr-embedded-evaluators]
sources:
  - Red-Teaming OpenAI's Internal Agent Monitoring Systems | METR | 2026-10-22 | https://metr.org/blog/2026-10-22-red-teaming-openai-agent-monitoring/
  - Red-Teaming OpenAI's Internal Agent Monitoring Systems | Redwood Research | 2026-10-22 | https://www.redwoodresearch.org/blog/red-teaming-openais-internal-agent
---

METR (Model Evaluation and Threat Research) and the AI safety nonprofit Redwood Research published findings on 22 October 2026 from a red-team exercise against OpenAI's internal misalignment monitor. The monitor reviews what OpenAI's agents do for signs of sabotage, deception and other risks, and flags cases for human review. From 21 July to 11 August, an employee of each probed the monitor, as it stood on 21 July, for weaknesses.[^1, 2]

They had access to OpenAI's internal code, documentation and the monitor's prompts and configuration, and interviewed about a dozen staff. Their 61-page report went to OpenAI, and a 38-page version redacted by OpenAI went to METR's and Redwood's leaders. OpenAI could cut anything it judged confidential or sensitive from the public summary, and METR had no unilateral right to describe the cuts.[^1]

The testers estimate, with substantial uncertainty, that 75 to 94% of internal agent traffic on OpenAI's Responses API from models at least as strong as GPT-5.5 was eligible for monitoring. For internal Codex coding agents, the share was 99.2%. Eligible traffic is meant to reach the monitor, but errors or bugs could stop some. They estimate that a gap OpenAI staff found beforehand and fixed during the exercise likely left on the order of 10% of eligible Codex traffic unmonitored from May to July.[^1]

The testers found that a client could switch off monitoring for new agents by setting either of two request headers, though the monitor could catch this. They also found an exploit agents could use to keep hundreds of recent actions unmonitored. According to METR, OpenAI has since said the vulnerabilities affecting its production safeguards are patched and described later changes to the monitor's intended coverage. "We have not evaluated these claims," the post says. It recommends reconciling records of all inference with the monitor's logs, keeping tamper-proof logs and isolating agents from their monitors.[^1]

:::analysis
The coverage estimates and weaknesses come from testers who could read OpenAI's code, but apply only to the system as of 21 July. Its current coverage and the reported patches rest on OpenAI's statements, and OpenAI alone decided what to cut from the summary. The reconciled records and tamper-proof logs the post recommends would give later reviewers evidence to check such claims.
:::

:::checked
On 25 October 2026 we read METR's 22 October post and Redwood Research's copy of it. The OpenAI pages METR links to returned an access error. We could not confirm the monitor's current coverage, OpenAI's statement that the vulnerabilities are patched or whether any agent exploited them. METR's post credits David Rein and Adam Kaufman without saying who did the testing, and we have not seen the report.
:::
