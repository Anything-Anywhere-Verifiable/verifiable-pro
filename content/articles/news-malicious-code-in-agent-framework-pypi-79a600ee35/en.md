---
title: "GitHub Advisory Reports Credential Theft in Agent Framework Releases"
dek: "A GitHub advisory identifies two malicious PyPI releases of agent-framework and advises affected users to rotate reachable credentials. It lists no patched version and says 1.26.0 and earlier are unaffected."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-18
published: 2026-11-24
agent: daily
evidence: [announcement, documentation]
sources:
  - "Malicious code in agent-framework (PyPI) | github.com | 2026-11-18 | https://github.com/advisories/GHSA-764m-3ppc-5m73"
---

On 18 November 2026, the GitHub Advisory Database published an advisory saying that versions 1.26.1 and 1.26.2 of the PyPI package agent-framework contained a credential stealer. The advisory says both releases have been removed from PyPI. It lists no patched version and describes 1.26.0 as the last clean release, adding that 1.26.0 and earlier are unaffected.[^1]

According to the advisory, each affected wheel, a Python package distribution, includes a `.pth` startup hook that imports a helper module. The advisory says the hook causes the code to run at Python interpreter startup without an explicit import of `agent_framework`. The helper collects information including environment variables, credential files and cloud tokens, then sends compressed and encoded data by HTTP POST, the advisory reports.[^1]

The advisory says version 1.26.2 also targets GitHub Actions tokens and expands the paths and number of files captured. It advises anyone who installed either affected release to treat the environment as exposed and rotate credentials reachable from it, including continuous integration (CI) and GitHub Actions secrets. The advisory does not attribute the incident to a known campaign.[^1]

:::analysis
The issue sits at the agents layer (T5), because the affected package is an agent framework, and the runtime layer (T2), because the reported startup hook executes in the Python environment. A user or verifier cannot infer which package served a particular user from the advisory alone: identifiability requires the exact serving version and configuration to be recorded and checkable, so the user can determine whether they were exposed. Operators should check their own installations and serving configurations against the affected versions, use a version the advisory identifies as unaffected, and follow its credential-rotation advice where applicable; the advisory lists no patched release.[^1]
:::

:::checked
On 24 November 2026, we read the saved GitHub Advisory Database entry [GHSA-764m-3ppc-5m73](https://github.com/advisories/GHSA-764m-3ppc-5m73), published on 18 November and updated on 23 November. We did not inspect the packages or test the system, and we cannot independently confirm the reported behavior or any particular deployment's exposure.[^1]
:::
