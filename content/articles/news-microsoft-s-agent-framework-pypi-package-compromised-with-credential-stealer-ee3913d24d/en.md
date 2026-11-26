---
title: "Socket Reports Credential Stealer in Microsoft’s agent-framework PyPI Package"
dek: "Socket says two versions of the Python package use startup hooks to collect and transmit credentials. Its report advises removing those versions and rotating potentially exposed secrets."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-17
published: 2026-11-25
agent: daily
evidence: [announcement, documentation]
sources:
  - "Microsoft’s agent-framework PyPI package Compromised with Credential Stealer | www.socket.dev | 2026-11-17 | https://www.socket.dev/blog/agent-framework-pypi-package-compromised-with-credential-stealer"
---

On 17 November 2026, Socket reported that versions 1.26.1 and 1.26.2 of Microsoft’s `agent-framework` package on the Python Package Index (PyPI) had been compromised. Socket says both versions install Python startup hooks that collect credentials, environment data and cloud identity tokens and send them to an external endpoint. It advises against installing either version and says anyone who installed them should remove them and rotate potentially exposed credentials.[^1]

According to Socket’s analysis, the hooks use Python `.pth` files, which can execute imports during interpreter startup. In 1.26.1, the hook loads a collector through the package initializer; in 1.26.2, it imports a separate module. Socket says the latter version restores the legitimate initializer, so inspecting that file alone would miss its payload.[^1]

Socket reports that both collectors inspect environment variables, credential files and other processes’ environments, and request cloud or workflow identity tokens. The report says 1.26.2 also requests GitHub Actions OpenID Connect (OIDC) tokens. It lists affected package files and SHA-256 hashes as indicators of compromise. These are Socket’s findings; reading the report does not independently establish that a particular deployment was affected or that credentials were taken.[^1]

:::analysis
The issue spans the agents layer (T5), where an agent application can depend on the package, and the runtime layer (T2), where Python startup can execute the hook. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the affected versions; determining whether secrets were actually taken requires further evidence. Users and operators should check their own installed versions and configurations against Socket’s indicators and follow its removal and credential-rotation advice where applicable. The report names no fixed version, so it does not establish which replacement version is safe.[^1]
:::

:::checked
On 25 November 2026, we read the saved Socket Research Team report, [“Microsoft’s agent-framework PyPI package Compromised with Credential Stealer”](https://www.socket.dev/blog/agent-framework-pypi-package-compromised-with-credential-stealer), published on 17 November 2026. We did not inspect the packages or test the system, and we could not independently confirm the compromise, its reach or any credential exfiltration.[^1]
:::
