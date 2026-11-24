---
title: "AWS Advisory Reports Security Policy Bypass in API MCP Server"
dek: "An advisory says incorrect operation-name normalization can bypass custom policy entries in locally run servers. It recommends upgrading and patching derivative code."
kind: news
topics: [agents-accountability, supply-chain]
layers: [agents, runtime]
event_date: 2026-11-10
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "AWS API MCP Server Security Policy Bypass via Incorrect Operation Name Normalization | github.com | 2026-11-10 | https://github.com/awslabs/mcp/security/advisories/GHSA-4wq9-grf3-qg2p"
---

An AWS security advisory published on 10 November 2026 says a flaw in AWS API MCP Server can bypass parts of a custom security policy. The advisory lists versions of `awslabs.aws-api-mcp-server` from 0.2.13 up to, but excluding, 1.5.1 as affected and identifies 1.5.1 as patched.[^1]

The open-source Model Context Protocol (MCP) server lets AI assistants manage AWS accounts through AWS API calls. According to the advisory, the server incorrectly normalizes operation names containing consecutive capital letters before comparing them with a policy. As a result, entries in `denyList` or `elicitList` may not be enforced for those operations.[^1]

The advisory says an actor might consequently execute operations that the policy was meant to deny or require elicitation for. Its examples include creating a federated identity provider, deactivating a multifactor authentication device and deleting database clusters. The issue requires a locally run server with a custom policy listing affected operations, as well as user interaction with the assistant.[^1]

The advisory says the remote AWS API MCP Server offering and the `READ_OPERATIONS_ONLY` and `REQUIRE_MUTATION_CONSENT` settings are not affected. It recommends upgrading to the latest version and ensuring forks or derivative code incorporate the fixes; it lists no workaround other than upgrading.[^1]

:::analysis
The issue sits at the agent layer (T5) and runtime layer (T2): an assistant's access to operations depends on policy enforcement by the server. A user or verifier cannot infer enforcement of an affected entry from the policy text alone. Identifiability matters: if the exact version and configuration serving a user are recorded and checkable, the user can determine whether they were exposed under the advisory's conditions. Operators should verify the running version, whether the server is local, the relevant custom policy entries and whether forks incorporate the fix, and follow the advisory's upgrade recommendation.[^1]
:::

:::checked
On 23 November 2026 we read the saved official [AWS API MCP Server security advisory](https://github.com/awslabs/mcp/security/advisories/GHSA-4wq9-grf3-qg2p), GHSA-4wq9-grf3-qg2p. We did not test the system or independently confirm the flaw, the fix or any deployment's exposure; the account above reports the advisory's claims.[^1]
:::
