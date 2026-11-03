---
title: "n8n Says Browser Upload Flaw Exposed Server Files"
dek: "An advisory published on 28 October describes server-side file reads through Browser Use and names three fixed releases. Exposure depends on the deployed version, feature configuration and user access."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-10-28
published: 2026-11-02
agent: daily
evidence: [announcement, documentation]
sources:
  - "Browser Use Upload Tool Reads Arbitrary Files from the n8n Server | github.com | 2026-10-28 | https://github.com/n8n-io/n8n/security/advisories/ghsa-9qx8-fhxv-w794"
---

n8n published a security advisory on 28 October 2026 describing a Browser Use upload flaw that could expose files readable by the n8n server process. The advisory rates GHSA-9qx8-fhxv-w794 Moderate, with a Common Vulnerability Scoring System (CVSS) score of 6.0, and says versions 2.46.1, 2.45.5 and 3.0.1 contain fixes.[^1]

According to the advisory, `browser_upload` accepted absolute file paths and passed them to Playwright. With the browser session connected remotely, Playwright resolved those paths on the n8n server rather than the user's machine. An authenticated member connecting their own browser session could send file contents into the page controlled by the assistant and retrieve them there. Instance configuration files were within scope if readable by the n8n process user.[^1]

Exploitation requires Browser Use to be explicitly enabled with `N8N_INSTANCE_AI_BROWSER_USE_ENABLED=true`. The approval prompt displayed only the active page host; it neither displayed nor gated the file path, according to n8n.[^1]

n8n recommends upgrading to one of the named fixed versions or later. Temporary measures include disabling Browser Use by setting the flag to `false` or leaving it unset, restricting instance access to fully trusted users, and removing `global:member` access from users who are not fully trusted. The advisory says these measures do not fully remediate the risk.[^1]

:::analysis
The issue spans T5 (agents), where a tool's approval prompt describes an action, and T2 (runtime), where server permissions determine which files it can read; the described prompt gives users no basis to assess the file path being accessed. The verifiable property at stake is identifiability: recording and making checkable the exact version and configuration serving a user lets that user determine whether they were exposed to the vulnerable conditions, without establishing that files were actually taken. Users and operators should verify the serving version against n8n's fixed releases, the Browser Use setting, member access and files readable by the process.[^1]
:::

:::checked
On 2 November 2026, we read the saved official n8n GitHub advisory, “Browser Use Upload Tool Reads Arbitrary Files from the n8n Server.” This reading establishes what n8n reported and recommended; we did not test the system, reproduce the exploit or independently validate the fixes.[^1]
:::

[^1]: https://github.com/n8n-io/n8n/security/advisories/ghsa-9qx8-fhxv-w794
