---
title: Agentic AI Foundation Adds the A2A Protocol for Communication Between Agents
dek: The Linux Foundation's Agentic AI Foundation said on 17 August 2026 that the Agent2Agent (A2A) protocol is joining it as a hosted project, alongside the Model Context Protocol. A2A's specification lets providers sign the cards that describe their agents, so a client can check a card's origin and integrity before delegating work.
kind: news
topics: [agents-accountability]
layers: [agents]
event_date: 2026-08-17
published: 2026-10-20
agent: daily
evidence: [announcement, standard, documentation]
sources:
  - A2A joins AAIF's open agentic stack | Agentic AI Foundation | 2026-08-17 | https://aaif.io/blog/a2a-joins-aaif
  - A New Chapter for A2A: Joining the Agentic AI Foundation | A2A Protocol | 2026-08-27 | https://a2a-protocol.org/latest/blog/2026/08/27/a-new-chapter-for-a2a-joining-the-agentic-ai-foundation/
  - Project Proposal: Agent2Agent Protocol (A2A), issue 37 | Agentic AI Foundation project proposals on GitHub | 2026-06-18 | https://github.com/aaif/project-proposals/issues/37
  - A2A Protocol Specification, section 8.4 Agent Card Signing | A2A Protocol | accessed 2026-10-20 | https://a2a-protocol.org/latest/specification/#84-agent-card-signing
related: [mcp-july-2026-specification, nist-ai-agent-standards-initiative]
---

The Agentic AI Foundation (AAIF), which the Linux Foundation hosts, said on 17 August 2026 that the Agent2Agent (A2A) protocol is joining it as a hosted project.[^1] The foundation's public proposal record shows that its Technical Committee approved A2A as a Growth Stage project on 15 July and its Governing Board approved it on 4 August.[^3] The A2A project announced the move on its own blog on 27 August.[^2]

A2A is an open standard for communication between agents built on different frameworks or by different vendors. An agent publishes an agent card, a structured description of what it can do and how to reach it. According to AAIF, other agents read the card and delegate tasks to that agent without a person coordinating the handoff.[^1]

Google launched A2A in April 2025 and donated it to the Linux Foundation. The first stable specification, version 1.0, followed in March 2026. AAIF says more than 150 organizations back the protocol.[^1]

At AAIF, A2A sits beside the Model Context Protocol (MCP). The A2A project says MCP connects agents to internal tools and databases, while A2A lets agents collaborate as peers.[^2]

AAIF presents signed agent cards as a way to verify identity cryptographically.[^1] Under the specification, a provider may sign its card with a JSON Web Signature (JWS). The signature lets a client check that the card has not been altered and comes from the claimed provider. To verify a signature, a client retrieves the public key from a URL in the signature's header or from its own store of trusted keys. Signing is optional, and the specification says clients should verify at least one signature before trusting a card.[^4]

:::analysis
Moving A2A into AAIF changes where the specification is governed, but does not change what a client can check before delegating. When one agent hands work to another, the agent card is the claim the delegating agent acts on. A valid signature ties that claim to a signing key. It identifies the provider only if the client trusts where that key came from. The skills the card lists remain the provider's own description. The signature also shows nothing about how the receiving agent will handle the task.
:::

:::checked
On 20 October 2026 we read AAIF's 17 August post, the A2A project's 27 August post, the A2A proposal and its approval comments in AAIF's GitHub repository, and the agent card signing section of the A2A specification. We did not verify AAIF's adoption figure, and we test no systems ourselves.
:::
