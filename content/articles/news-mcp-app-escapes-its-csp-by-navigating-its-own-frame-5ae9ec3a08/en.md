---
title: "MCP Inspector Advisory Reports App Sandbox Escape"
dek: "An advisory says an untrusted MCP App can navigate its frame and take over a message bridge in affected Inspector versions. Version 2.14.0 is listed as patched."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-05
published: 2026-11-18
agent: daily
evidence: [announcement, documentation]
sources:
  - "MCP App escapes its CSP by navigating its own frame | github.com | 2026-11-05 | https://github.com/modelcontextprotocol/inspector/security/advisories/GHSA-h9j8-vj8g-v3gg"
---

On 5 November 2026, an advisory for Model Context Protocol (MCP) Inspector reported that an untrusted MCP App could escape its content security policy (CSP) restrictions by navigating its own frame. It lists `@modelcontextprotocol/inspector` versions 2.0.0 through 2.13.0 as affected and 2.14.0 as patched.[^1]

The issue concerns the web client's Apps tab when an app uses the default opaque-origin `srcdoc` path. According to the advisory, the app can navigate its inner frame to an attacker-controlled page. The frame retains its sandbox flags, and the proxy continues to accept messages from the same frame window and relay host messages to it. The advisory says this lets the remote page take over the app's message bridge and bypass the per-app list of allowed connection domains.[^1]

The advisory reports a reproduction using the shipped sandbox proxy with connections and form submissions disallowed by CSP. It says the attacker origin received data in a navigation URL and a subsequent private tool result, while the host received a tool call sent by the attacker page. These are the advisory's reported results; we did not reproduce them.[^1]

Exposure requires a user to render an app from a connected server. The advisory identifies malicious or compromised servers as the relevant threat and says CLI and TUI users, people who do not open the Apps tab, and apps using a dedicated origin take different paths or are outside the affected group.[^1]

:::analysis
The issue sits at T5 (agents), where an app communicates with tools, and T2 (runtime), where the browser sandbox and message relay enforce boundaries. A reviewer cannot rely on the affected path's declared connection allowlist alone to establish where app data can go. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected path; users and operators should check those details, including whether they run the advisory's patched version 2.14.0. That check still depends on accurate deployment records and does not establish that a particular app was exploited.[^1]
:::

:::checked
On 18 November 2026, we read the saved text of the official [MCP Inspector security advisory GHSA-h9j8-vj8g-v3gg](https://github.com/modelcontextprotocol/inspector/security/advisories/GHSA-h9j8-vj8g-v3gg). We did not test the system, reproduce the demonstration, or independently inspect the patch; the advisory's account and version listing are the evidence for this brief.[^1]
:::
