---
title: "Microsoft Says VS Code Fixes Code Execution Flaw in MCP Notifications"
dek: "The advisory identifies VS Code versions before 1.145.3 as affected. Exploitation requires a malicious connected MCP server and a user clicking a crafted notification link."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-10
published: 2026-11-16
agent: daily
evidence: [announcement, documentation]
sources:
  - "Remote Code Execution via MCP Elicitation Notifications | github.com | 2026-11-10 | https://github.com/microsoft/vscode/security/advisories/GHSA-66hq-jw93-462h"
---

Microsoft published a VS Code security advisory on 10 November 2026 describing a code execution vulnerability in the fallback notification path for Model Context Protocol (MCP) elicitation requests. The advisory, GHSA-66hq-jw93-462h, lists versions before 1.145.3 as affected and 1.145.3 as patched. It assigns the issue CVE-2026-120779 and a High severity rating with a CVSS score of 8.3.[^1]

According to the advisory, server-controlled message content could be interpreted as an interactive VS Code command link. A malicious MCP server could thereby cause command execution if a user activated the crafted notification. The stated prerequisites are control of a connected MCP server and persuading the user to click the malicious link; the described attack requires user interaction.[^1]

Microsoft says the fix, available starting with VS Code 1.145.3, renders elicitation messages as literal text and validates the request payload before displaying it. The advisory identifies patches 305e248 and e3a4962. Its workarounds are to connect only to trusted MCP servers and avoid activating notification links produced by an untrusted server.[^1]

:::analysis
The issue sits at T5 (agents), where an MCP server supplies content, and T2 (runtime), where VS Code interprets and displays that content: the advisory describes server text crossing into an actionable command interface. Users and operators should verify the version actually serving each user against the recommended fixed version, 1.145.3, and check which MCP servers are connected and trusted.[^1] The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected setup; those records alone do not establish that exploitation occurred.
:::

:::checked
On 16 November 2026, we read the supplied saved copy of Microsoft’s GitHub advisory, “Remote Code Execution via MCP Elicitation Notifications.” It establishes what Microsoft reported about affected versions, attack prerequisites and the fix. We did not inspect the referenced patches, test the system, reproduce the attack or independently confirm the fix’s effectiveness.[^1]
:::

[^1]: Microsoft, “Remote Code Execution via MCP Elicitation Notifications,” published 10 November 2026. https://github.com/microsoft/vscode/security/advisories/GHSA-66hq-jw93-462h
