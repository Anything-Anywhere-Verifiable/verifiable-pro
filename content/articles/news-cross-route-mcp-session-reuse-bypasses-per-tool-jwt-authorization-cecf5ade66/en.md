---
title: "Agent Router Advisory Reports Per-Tool Authorization Bypass Through MCP Session Reuse"
dek: "The advisory lists version 1.2.0 as affected and 1.2.1 as patched. Its evidence covers an isolated handler test, with full gateway and OAuth integration untested."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-06
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "Cross-route MCP session reuse bypasses per-tool JWT authorization | github.com | 2026-11-06 | https://github.com/theagentrouter/agent-router/security/advisories/ghsa-72hp-5vm2-frr7"
---

An Agent Router security advisory published on 6 November 2026 reports that reusing a Model Context Protocol (MCP) session across routes can bypass per-tool JSON Web Token (JWT) authorization under a specific mixed-authentication configuration. Advisory GHSA-72hp-5vm2-frr7 lists 1.2.0 as affected and 1.2.1 as patched, with Moderate severity and a CVSS 3.1 score of 6.8.[^1]

The configuration involves two routes sharing one Gateway proxy: route A uses OAuth and a per-tool JWT rule; route B does not validate the bearer token or set the session-subject header. According to the advisory, session resumption restores route A from the session ID without comparing it with the current request route. Route A's authorization code then parses the current token without verifying its signature, allowing forged scope claims to satisfy its tool rule.[^1]

The caller still needs a valid low-scope account to establish a route-A session, access to route B, and the retained session ID and subject. Backend and tool selectors remain effective. The advisory says this does not bypass initial OAuth login or grant cluster-admin privileges; consequences depend on the tools and data exposed.[^1]

:::analysis
The issue spans T5 agents, where tool permissions define allowed actions, and T2 runtime, where routing and session handling enforce those permissions: a verifier cannot infer enforcement from a protected route's policy alone. Users and operators should verify the deployed package identity, whether they run the listed patched version 1.2.1, and whether their routes share the described proxy and authentication configuration; the advisory's package field names `github.com/envoyproxy/ai-gateway`, while its narrative names Agent Router. The property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the described vulnerable conditions.[^1]
:::

:::checked
On 10 November 2026, we read the saved official GitHub advisory “Cross-route MCP session reuse bypasses per-tool JWT authorization.” We did not test the system or inspect its code. Our reading establishes what the advisory reports: an isolated handler test reached a loopback backend, its saved evidence lacks a negative control, and full Envoy/Kubernetes/OAuth integration was not tested. The patched-version designation remains the advisory's claim.[^1]
:::

[^1]: https://github.com/theagentrouter/agent-router/security/advisories/ghsa-72hp-5vm2-frr7
