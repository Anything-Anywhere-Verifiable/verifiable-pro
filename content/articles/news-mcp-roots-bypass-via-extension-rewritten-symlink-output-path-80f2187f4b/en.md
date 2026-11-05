---
title: "ChromeDevTools Advisory Reports MCP Roots Bypass, Lists 1.5.0 as Patched"
dek: "An extension rewrite after path validation can redirect tool output through a symlink outside configured workspace roots. The advisory lists versions 1.1.0–1.4.0 as affected."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-10-22
published: 2026-11-05
agent: daily
evidence: [announcement, documentation]
sources:
  - "MCP roots bypass via extension-rewritten symlink output path | github.com | 2026-10-22 | https://github.com/ChromeDevTools/chrome-devtools-mcp/security/advisories/GHSA-5hw5-4q87-m6x9"
---

ChromeDevTools published a Moderate-severity security advisory on 22 October 2026 describing a workspace-boundary bypass in `chrome-devtools-mcp`. Advisory GHSA-5hw5-4q87-m6x9 lists versions 1.1.0 through 1.4.0 as affected and 1.5.0 as patched. The reported impact is overwriting files outside configured Model Context Protocol (MCP) roots, subject to the server’s filesystem permissions.[^1]

The flaw concerns operation order. The server validates a caller-supplied output path, then enforces the output extension and writes to that changed path without validating the final destination. For example, `workspace/report.txt` can pass validation before becoming `workspace/report.png`. If the latter is a symbolic link to a writable file outside the root, the write follows it. Direct validation of that final link would reject it, according to the advisory.[^1]

The source reports four reproductions, including a full MCP stdio workflow using the real server, Chrome and `take_screenshot`. It identifies screenshots as the demonstrated output and lists other paths sharing `McpContext.saveFile`. Exploitation requires an in-root symlink that an attacker or malicious workspace state can create or use; the advisory explicitly says this is not remote code execution and does not establish remote exploitation by itself.[^1]

:::analysis
The issue sits at T5 (agents), where tools receive output requests, and T2 (runtime), where path handling and filesystem writes enforce the boundary: checking the requested filename alone does not establish confinement of the eventual write. Users and operators should verify the deployed package against the advisory’s patched version, 1.5.0, and check configured roots and relevant symlink state; its proposed correction validates the exact destination after path transformations. The verifiable property at stake is identifiability: recording and making checkable the exact version and configuration serving a user lets that user determine whether they were exposed to the affected setup, although it does not establish that an overwrite occurred.[^1]
:::

:::checked
On 5 November 2026, we read the supplied saved copy of ChromeDevTools’ GitHub advisory GHSA-5hw5-4q87-m6x9, published on 22 October 2026. We did not test the system, reproduce the reported results or inspect the patched implementation. Our reading establishes what the advisory reports, including its patched-version listing; it does not independently confirm the fix.[^1]
:::

[^1]: ChromeDevTools, “MCP roots bypass via extension-rewritten symlink output path,” 22 October 2026. https://github.com/ChromeDevTools/chrome-devtools-mcp/security/advisories/GHSA-5hw5-4q87-m6x9
