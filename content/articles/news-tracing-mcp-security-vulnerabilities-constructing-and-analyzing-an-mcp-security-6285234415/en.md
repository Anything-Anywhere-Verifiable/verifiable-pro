---
title: "MCP Vulnerability Study Reports 24-Case Dataset From CVE Disclosures"
dek: "The authors report that 87.5% of their curated snapshot’s vulnerabilities have Critical or High severity. The saved abstract supports a research finding, not a deployment security assessment."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents, runtime]
event_date: 2026-11-08
published: 2026-11-11
agent: daily
evidence: [announcement, documentation]
sources:
  - "Tracing MCP Security Vulnerabilities: Constructing and Analyzing an MCP Security Vulnerability Dataset | arXiv | 2026-11-08 | https://arxiv.org/abs/2611.11104"
---

Xu He, Sagar Patel and Shu Wang submitted an MCP security dataset study to arXiv on 8 November 2026. The authors report curating 24 vulnerabilities from 119 MCP-related Common Vulnerabilities and Exposures (CVE) records retrieved through February 2026. Model Context Protocol (MCP) connects large language models to external data sources and tools, placing the research at the interface used by AI agents.[^1]

The authors say their filtering addresses ambiguity in the MCP acronym and achieves 96.7% inter-rater agreement in a sampled exclusion audit. They also report retaining all known high-severity MCP cases identified in public advisories. These are the authors’ methodological claims; reading the abstract does not independently establish the dataset’s completeness.[^1]

Within the 24-case snapshot, the authors classify 87.5% of vulnerabilities as Critical or High severity, with injection and path traversal accounting for 66.7% of cases. They identify recurring insufficient input validation, inadequate access control and protocol-level security gaps. Those percentages describe the selected vulnerability records; they do not measure the proportion of MCP deployments that are vulnerable.[^1]

The abstract says the authors release the dataset, reproducibility tooling and a maintenance workflow, and examine six representative cases. The page’s comments describe a maintained dataset extending beyond the original snapshot. We did not inspect those artifacts, so the reported counts here remain tied to the original snapshot.[^1]

:::analysis
The issue spans T6 evaluations (`evaluations`), T5 agents (`agents`) and T2 runtime (`runtime`): dataset findings inform assessment of agent integrations, while exposure depends on the deployed software and configuration. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed by matching those records to applicable vulnerability conditions. Users and operators should verify that correspondence; the saved abstract supplies no affected-version ranges, fixed versions or configuration-specific exposure criteria.[^1]
:::

:::checked
On 11 November 2026, we read the supplied saved arXiv abstract page for “Tracing MCP Security Vulnerabilities: Constructing and Analyzing an MCP Security Vulnerability Dataset,” including its comments and submission history. This establishes what the page reports, not whether its findings reproduce. We did not read the full paper, inspect the dataset or tooling, reproduce exploits, or test any MCP system.[^1]
:::

[^1]: arXiv, “Tracing MCP Security Vulnerabilities: Constructing and Analyzing an MCP Security Vulnerability Dataset,” submitted 8 November 2026. https://arxiv.org/abs/2611.11104
