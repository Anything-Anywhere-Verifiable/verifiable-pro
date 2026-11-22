---
title: "AWS Advisory Says Serverless MCP Path Traversal Is Fixed in 0.2.1"
dek: "The advisory describes JSON file reads outside the deployment status directory and writes when enabled. It recommends upgrading and patching derivative code."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-02
published: 2026-11-03
agent: daily
evidence: [announcement, documentation]
sources:
  - "Improper limitation of a pathname to a restricted directory in the AWS Serverless MCP Server | github.com | 2026-11-02 | https://github.com/awslabs/mcp/security/advisories/GHSA-r6mm-377j-qg8m"
---

An awslabs/mcp security advisory published on 2 November 2026 says AWS Serverless MCP Server version 0.2.1 addresses a path traversal vulnerability in its deployment status component. The advisory lists versions below 0.2.1 of the pip package `awslabs.aws-serverless-mcp-server` as affected and identifies the issue as CVE-2026-116635, rated Moderate with a CVSS score of 6.1.[^1]

According to the advisory, an actor able to influence the MCP agent could supply directory traversal sequences or an absolute path through the project name input. Under the described conditions, this could let the agent read JSON files outside the intended deployment status directory, returning their contents to the agent’s context. If the server was started with `--enable-write`, the issue could also allow JSON files outside that directory to be created or overwritten. The advisory says overwritten data would consist of serverless deployment metadata.[^1]

The maintainers recommend upgrading to the latest version and incorporating the fixes into forked or derivative code. They list 0.2.1 as the patched version and state that there is no workaround. These are the advisory’s remediation claims; reading the notice does not independently establish the patch’s behavior.[^1]

:::analysis
The issue spans T5 agents and T2 runtime: influenced agent input reaches a filesystem boundary, so users cannot infer directory confinement from the intended tool workflow alone. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected conditions described in the advisory. Users and operators should verify the serving package version, whether `--enable-write` was enabled, and whether forks incorporate the fixes, following the advisory’s upgrade recommendation; those records alone do not establish that exploitation occurred.[^1]
:::

:::checked
On 3 November 2026, we read the saved copy of the official awslabs/mcp GitHub security advisory GHSA-r6mm-377j-qg8m, titled “Improper limitation of a pathname to a restricted directory in the AWS Serverless MCP Server.” This preview uses its publication date, 2 November, as the event date. We did not test the system, reproduce the vulnerability, or inspect the patch; our reading establishes what the advisory reports.[^1]
:::

[^1]: https://github.com/awslabs/mcp/security/advisories/GHSA-r6mm-377j-qg8m
