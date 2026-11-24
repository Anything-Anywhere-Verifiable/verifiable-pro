---
title: "Effycace Says Familiar Software Flaws Dominate AI Agent Tooling Vulnerabilities"
dek: "A review of 2,979 published vulnerabilities found familiar software weaknesses in most cases, while agent-specific risks were harder to see in vulnerability data."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-12
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Securing AI agents: the familiar flaws come first | www.effycace.com | 2026-11-12 | https://www.effycace.com/research/reports/securing-ai-agents-2026/"
---

On 12 November 2026, Effycace Solutions published a report on vulnerabilities in AI agent and application tooling. The research team says it analyzed 2,979 vulnerabilities published between January 2023 and 11 November 2026, covering selected products and Model Context Protocol (MCP) servers. MCP connects agents to tools and data.[^1]

Effycace reports that 66.2% of the vulnerabilities fell into four familiar weakness families: authentication and access control, injection and code execution, path traversal and file handling, and request forgery. It says 13 appeared in the US Cybersecurity and Infrastructure Security Agency’s Known Exploited Vulnerabilities catalogue; all were in self-hosted platforms. The report cautions that vulnerability counts also reflect research attention and should not be treated as security rankings.[^1]

The report says prompt injection, in which input can redirect an agent’s behavior, is difficult to find through vulnerability records alone. Its search found 67 descriptions mentioning the phrase among the selected AI tooling vulnerabilities. Effycace describes its separate agent threat model as structured expert judgment based on published guidance, not an empirical test. It recommends inventorying components, restricting agent credentials, reviewing third-party servers and plugins, and patching platforms promptly.[^1]

:::analysis
The issue spans the agents layer (T5), where permissions and exposure to untrusted content shape what an agent can do, and the runtime layer (T2), where platform software and its configuration affect exposure. A user or verifier needs evidence of the deployed components and their settings to assess a particular system; the report’s aggregate counts cannot establish whether that system was exposed. Identifiability is the property at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular documented vulnerability, provided its affected conditions are known. Users and operators should check their inventories, versions, configurations and applicable fixes, as well as the access each agent has; the report recommends prompt patching but names no fixed version.[^1]
:::

:::checked
On 24 November 2026, we read the saved text of Effycace Solutions’ report, [“Securing AI agents: the familiar flaws come first”](https://www.effycace.com/research/reports/securing-ai-agents-2026/). We did not independently inspect its datasets or code, verify its counts, or test any system. The report says it was reviewed by its author and had not been independently peer reviewed.[^1]
:::
