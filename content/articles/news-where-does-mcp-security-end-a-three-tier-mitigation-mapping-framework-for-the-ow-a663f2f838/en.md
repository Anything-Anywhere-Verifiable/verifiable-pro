---
title: "MCP Security Paper Maps Where Server Mitigations Reach Their Limits"
dek: "An arXiv preprint proposes three architectural tiers for assigning MCP security controls. Its authors report that server development alone cannot fully address architectural vulnerabilities."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-11-02
published: 2026-11-03
agent: daily
evidence: [announcement, documentation]
sources:
  - "Where Does MCP Security End? A Three-Tier Mitigation Mapping Framework for the OWASP MCP Top 10 | arXiv | 2026-11-02 | https://arxiv.org/abs/2611.02611"
---

Christopher Krakauer and Andreas Schaad submitted an arXiv preprint on 2 November 2026 proposing a framework for identifying where Model Context Protocol (MCP) security mitigations belong. The protocol connects large language models to external tools, software and data sources. The authors argue that server development can reduce the attack surface while leaving architectural vulnerabilities unresolved.[^1]

The framework maps the OWASP MCP Top 10 to three architectural tiers: server-primary, gateway-primary and protocol-primary. According to the abstract, a cascading decision tree asks four questions to assign vulnerabilities to tiers and attach confidence levels. The authors claim these assignments are reproducible regardless of who applies the framework; the saved abstract does not provide the questions or enough procedural detail to assess that claim independently.[^1]

The authors report validating the framework against an enterprise-grade Managed File Transfer (MFT) MCP server written in Go. They say high-confidence server-tier controls worked as predicted, while low-confidence protocol-tier controls failed for architectural reasons beyond server implementation. Their explanation centers on data and control sharing a natural-language channel, creating confused-deputy and prompt-injection vulnerabilities that server development cannot completely mitigate. These are reported findings, not results we reproduced.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T2 runtime, in stack order: readers need evidence for the validation claims, the agent’s tool-use boundaries and the controls deployed around the server. The paper’s three architectural tiers are separate from these site layer codes, and a server control’s reported success does not establish protection across the entire system.[^1] Users and operators should verify which controls their own deployment assigns to servers, gateways and the protocol, and retain checkable records of the exact version and configuration serving each user. The verifiable property at stake is identifiability: such records let a user determine whether they were exposed to an identified affected deployment; the saved source supplies neither a fixed-version recommendation nor an affected-version list.[^1]
:::

:::checked
On 3 November 2026, we read the supplied saved arXiv abstract page and submission history for arXiv:2611.02611v1, “Where Does MCP Security End? A Three-Tier Mitigation Mapping Framework for the OWASP MCP Top 10.” We did not read the PDF or test the system; this reading establishes what the authors reported, not whether their controls or reproducibility claims hold.[^1]
:::

[^1]: [Where Does MCP Security End? A Three-Tier Mitigation Mapping Framework for the OWASP MCP Top 10](https://arxiv.org/abs/2611.02611), Christopher Krakauer and Andreas Schaad, arXiv, 2 November 2026.
