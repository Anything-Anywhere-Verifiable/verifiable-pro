---
title: "MCP Inspector Advisory Reports Windows Daemon Authorization Bypass"
dek: "The advisory lists versions 2.10.0 through 2.14.0 as affected and 2.15.0 as patched. It describes a local attack against a predictable Windows named pipe."
kind: news
topics: [supply-chain, agents-accountability]
layers: [runtime]
event_date: 2026-11-12
published: 2026-11-19
agent: daily
evidence: [announcement, documentation]
sources:
  - "[paths.ts] CWE-863 Authorization Bypass | github.com | 2026-11-12 | https://github.com/modelcontextprotocol/inspector/security/advisories/GHSA-5572-x678-xmv8"
---

On 12 November 2026, a security advisory published in the Model Context Protocol Inspector repository reported an authorization bypass affecting the Windows daemon communication path. The advisory lists npm package `@modelcontextprotocol/inspector` versions 2.10.0 through 2.14.0 as affected and version 2.15.0 as patched.[^1]

The advisory says the Windows branch of `getDaemonSocketPath` derives a named pipe from a hash of the resolved, lowercased daemon directory path. It describes that pipe name as predictable and says a local attacker could create the pipe first, impersonate the daemon and capture a bearer token sent by clients. It also says the Windows implementation of `assertTrustedPrivateRoot` returns without validating ownership or access controls.[^1]

The advisory proposes generating a random pipe name, publishing it in the token file, validating the daemon directory’s Windows access controls and owner, rejecting certain pre-existing pipe instances, and authenticating the daemon before clients send the token. Its page rates the issue Moderate with a CVSS score of 5.0, while the advisory description itself calls the severity HIGH. The saved source does not resolve that difference.[^1]

:::analysis
The issue sits at the runtime layer (T2): the trust boundary concerns communication between a client and a daemon while the software operates. A verifier reading the advisory can identify the reported affected and patched versions, but must still trust or independently check the deployment’s actual version and configuration. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected setup described in the advisory. Users and operators should check their own version and Windows deployment configuration, including whether they are running the listed patched version, 2.15.0; the advisory alone does not establish that any particular deployment has been fixed.[^1]
:::

:::checked
For this preview, prepared on 19 November 2026, we read the saved text of the official [GHSA-5572-x678-xmv8 advisory](https://github.com/modelcontextprotocol/inspector/security/advisories/GHSA-5572-x678-xmv8) in the `modelcontextprotocol/inspector` repository.[^1] We did not test the system, independently inspect the source code or verify the patch or any deployment. The advisory’s code and attack descriptions are reported as its claims.
:::
