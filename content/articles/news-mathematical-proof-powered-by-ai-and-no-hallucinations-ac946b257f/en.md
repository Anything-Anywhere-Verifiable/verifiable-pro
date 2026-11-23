---
title: "Amazon Announces Tools Connecting AI Agents to Isabelle Proof Assistant"
dek: "Amazon says its AutoCorrode tools let AI agents work with Isabelle as they construct formal proofs. The announcement describes examples but does not establish results for other deployments."
kind: news
topics: [formal-verification, agents-accountability]
layers: [agents, outputs]
event_date: 2026-11-18
published: 2026-11-22
agent: daily
evidence: [announcement, documentation]
sources:
  - "Mathematical proof, powered by AI. And no hallucinations! | www.amazon.science | 2026-11-18 | https://www.amazon.science/blog/mathematical-proof-powered-by-ai-and-no-hallucinations"
---

On 18 November 2026, Amazon Science announced publicly available tools in the AutoCorrode verification suite that connect AI agents to the Isabelle proof assistant. Amazon says the tools allow proof checking to take place as an agent constructs a formal mathematical proof, so the agent can revise its work in response to the checker.[^1]

A proof assistant checks reasoning expressed in a precise formal language. The tools use the Model Context Protocol (MCP) to connect an agent with Isabelle. I/Q lets an agent interact with and temporarily take control of a live Isabelle session; I/R lets the agent develop formal material while the user continues working. Isabelle Assistant uses I/Q to provide a chat window through which an agent can observe and modify the session.[^1]

Amazon reports that Claude Opus 4.6, using Isabelle Assistant, generated proofs for examples including the irrationality of √2 and the integral of sine from zero to π. In a further example, the authors say they supplied a flawed argument for the existence of N consecutive composite numbers and the agent corrected it. The announcement describes these examples as error-free, but reading it does not independently establish their results.[^1]

:::analysis
The story sits at T5 agents and T4 outputs: an agent proposes formal material, while a proof assistant checks the resulting mathematical argument. A check applies to the formal statement and assumptions submitted to the checker; users still need to judge whether those express the intended claim and trust the checking tools. Users and operators should inspect the formal statement, assumptions, and checker outcome for their own work. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a relevant issue; the announcement specifies no affected or fixed version.[^1]
:::

:::checked
On 22 November 2026, we read the saved text of Amazon Science’s “Mathematical proof, powered by AI. And no hallucinations!” We did not test the tools or independently check the example proofs, and the saved text does not establish the behavior of any particular deployment.[^1]
:::
