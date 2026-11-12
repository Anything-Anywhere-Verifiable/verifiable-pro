---
title: "Glow Labs Says Coding Agents Install Deprecated MCP Servers"
dek: "Glow Labs reports four high-severity flaws in retired reference servers. Its findings highlight the need to check the packages and configurations agents actually install on developer machines."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-02
published: 2026-11-11
agent: daily
evidence: [announcement, documentation]
sources:
  - "MCPhantom: AI Coding Agents Are Installing Vulnerable Deprecated MCP Servers from Training Data | www.glow.io | 2026-11-02 | https://www.glow.io/blogs/mcphantom-ai-coding-agents-are-installing-vulnerable-deprecated-mcp-servers-from-training-data"
---

Glow Labs reported on 2 November 2026 that AI coding agents were installing deprecated Model Context Protocol (MCP) servers on developer machines, potentially introducing vulnerabilities in software that no longer receives security updates. The company calls the pattern McPhantom.[^1]

Glow says it reviewed real-world coding-session transcripts and discovered local servers through endpoint inventory research. In 98% of sessions involving a deprecated-server setup, it attributes package selection to apparent reliance on training data; in the remaining 2%, users requested the deprecated package by name. The saved article gives no session count or reproducible method for establishing training-data attribution, limiting how readers can assess that explanation.[^1]

The company reports four high-severity vulnerabilities across deprecated Anthropic reference servers, including remote code execution in the Puppeteer server. It says prompt injection could cause an agent to launch arbitrary processes under permission intended for browser use. According to Glow, maintainers declined a fix because the repository was archived and unmaintained. Glow says it had seen no exploitation at the time of its report.[^1]

Glow recommends searching developer-machine MCP configurations for deprecated `@modelcontextprotocol` servers, replacing them with service-owner implementations where available, standardizing one approved server per service, and checking npm deprecation status before approval. It names no fixed version for the reported flaws and describes the archived servers as receiving no fixes.[^1]

:::analysis
The issue sits at T5 (agents), where software is selected and configured, and T2 (runtime), where local server processes execute; an agent's choice alone gives users no evidence of current maintenance. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to an affected deployment, although this does not establish exploitation. Users and operators should check endpoint configurations and installed versions against their approved replacements and npm deprecation status, following the source's replacement advice.[^1]
:::

:::checked
On 11 November 2026, we read the saved copy of Glow's “MCPhantom: AI Coding Agents Are Installing Vulnerable Deprecated MCP Servers from Training Data.” This establishes what Glow reported; we did not test the system, reproduce the vulnerabilities, or independently inspect transcripts, packages, or maintainer correspondence. The source date follows the supplied publication timestamp, 2 November, rather than the later date also displayed in the saved page.[^1]
:::

[^1]: Glow, “MCPhantom: AI Coding Agents Are Installing Vulnerable Deprecated MCP Servers from Training Data,” 2 November 2026. https://www.glow.io/blogs/mcphantom-ai-coding-agents-are-installing-vulnerable-deprecated-mcp-servers-from-training-data
