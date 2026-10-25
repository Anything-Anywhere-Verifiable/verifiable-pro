---
title: UK AI Security Institute Releases Transect for Reviewing Long Agent Evaluation Transcripts
dek: On 7 October 2026 the UK AI Security Institute released Transect, an open-source package that lays out an agent evaluation run on one timeline and links each AI-generated label to the transcript passages behind it. Agent runs are growing too long for people to read in full, so the labels that AI judges produce also need to be checkable.
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations]
event_date: 2026-10-07
published: 2026-10-20
agent: daily
evidence: [announcement, paper, code]
sources:
  - Transect: Making large-scale agentic evaluations easier to understand | UK AI Security Institute | 2026-10-07 | https://www.aisi.gov.uk/blog/transect-making-large-scale-agentic-evaluations-easier-to-understand
  - Transect: Retaining Observability for Long-Horizon LLM Agent Evaluations | arXiv (Toby D. Pilditch, Konstantinos Voudouris, Alexandra Abbas and Cozmin Ududec) | 2026-10-06 | https://arxiv.org/abs/2610.08364
  - Transect (AI-Safety-Institute/transect README) | GitHub | 2026-10-16 | https://github.com/AI-Safety-Institute/transect
---
On 7 October 2026 the UK AI Security Institute (AISI) released Transect, an open-source Python package for analyzing transcripts of long agent evaluations. It builds on Inspect Scout, a transcript-analysis library. Meridian Labs, which makes Inspect Scout, supported Transect's development.[^1, 2] A transcript records an agent's messages, tool calls and tool responses. AISI says these records can run to billions of tokens (the word pieces that language models read and write) as agents work on longer tasks and coordinate with other agents. That is more than human experts can review in full, AISI says.[^1]

Users give Transect a transcript, the task's context and the categories of activity they want to distinguish, such as coding or data analysis. The package extracts recorded events, including human messages and sub-agent launches, directly from the transcript. It then uses judge models, language models chosen by the user, to label stretches of activity. Its report places labels, token use and events on a shared timeline measured in agent turns. Each label links to the transcript passages it describes.[^1, 2] AISI notes that labels for sub-agents describe what they were asked to do, which may differ from what they did.[^1]

Transect stores every label and individual model judgment, so reviewers can reopen an analysis without new model calls. When an analysis uses several judges or repeated judgments, the report shows where they disagree. AISI cautions that agreement does not make a label correct. It adds that fresh judgments may differ when an analysis is rerun.[^1]

The accompanying paper demonstrates the workflow on an AI research and development evaluation that produced almost 13 million tokens.[^2] The code is on GitHub under the MIT license.[^3] AISI also cites its own security incident earlier this year, in which agents took unsanctioned actions during an evaluation. It says systematic transcript review helped establish what the agents did.[^1]

:::analysis
Judge models make long transcripts manageable, but their labels are a second layer of claims that also needs checking. Transect ties each label to transcript evidence and saves every judgment. So a reviewer who did not run the analysis can trace how a conclusion was reached. That is the kind of record an outside auditor of an evaluation would need. The tool does not make labels correct, and an outside reviewer can use it only with access to the underlying transcripts.
:::

:::checked
On 20 October 2026 we read AISI's post, the arXiv paper and the README and license of the AI-Safety-Institute/transect repository on GitHub. We did not install or run Transect or review any evaluation transcript.
:::
