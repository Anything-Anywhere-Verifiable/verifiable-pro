---
title: "LiteLLM Says Stolen Tokens Enabled Signed Malicious Release"
dek: "LiteLLM’s 23 October report traces version 1.107.0 to an exposed agent-platform key, stolen GitHub credentials and a redirected release workflow. The saved report names no fixed replacement version."
kind: news
topics: [supply-chain, agents-accountability]
layers: [institutions, agents, runtime]
event_date: 2026-10-23
published: 2026-10-28
agent: daily
evidence: [announcement, documentation]
sources:
  - "The attack chain behind the v1.107.0 LiteLLM release | litellm.vercel.app | 2026-10-23 | https://litellm.vercel.app/blog/security-incident-oct-21-2026-attack-chain"
---

LiteLLM published an attack-chain report on 23 October 2026 saying stolen credentials enabled attackers to build, sign and publish compromised `litellm==1.107.0` packages and container images on 21 October. Its account describes a release pipeline carrying out authorized-looking actions with stolen identities.[^1]

According to LiteLLM, an administrative key committed to a public repository on 27 May remained valid after the file was deleted. On 10 October, the attacker used it to query the internal LiteLLM Agent Platform and retrieve an organization owner’s GitHub CLI OAuth token from managed-agent configuration. Malicious continuous integration (CI) workflows then extracted two maintainers’ tokens.[^1]

The attacker changed the release workflow to accept a different source owner, overriding branch protection with the owner’s credentials. It then built from the lookalike `Berri-AI/litellm` fork. A stolen maintainer token approved the production gate; the pipeline signed and published the artifacts. Another token deleted release-run records, and forced history changes concealed the workflow modification from the main branch’s visible history, LiteLLM says.[^1]

The report records PyPI quarantine by 13:23 UTC on 21 October and subsequent container-tag removal or repointing. It directs readers to a separate incident post for exposure checks and cleanup. This saved report names no fixed replacement version; its statement about issuing another release is a plan, not confirmation of delivery.[^1]

:::analysis
The issue spans T7 institutions, T5 agents and T2 runtime: release authority, agent-held credentials and distributed executable artifacts. The reported signed malicious release means users and verifiers still need to trust the source-selection and approval controls behind a signature. The property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed. Users should check deployment records against the reported artifacts; operators should verify source repositories, credential scope and release approvals, while recognizing that this source alone cannot establish a recommended fixed version.[^1]
:::

:::checked
On 28 October 2026, we read the saved official LiteLLM report, “The attack chain behind the v1.107.0 LiteLLM release,” published on 23 October. This reading establishes what LiteLLM reported; we did not test the system, inspect artifacts or audit logs, or read the separately referenced incident post. We did not independently confirm the attack chain or remediation.[^1]
:::

[^1]: LiteLLM, “The attack chain behind the v1.107.0 LiteLLM release,” 23 October 2026. https://litellm.vercel.app/blog/security-incident-oct-21-2026-attack-chain
