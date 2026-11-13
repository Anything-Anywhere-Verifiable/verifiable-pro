---
title: "Cloudflare Announces Experimental Codex Agent Loop on Workers"
dek: "The Agents SDK example records completed model and tool results for recovery after restarts. Interrupted steps may run again, making deployment identity and recovery behavior important checks."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-09
published: 2026-11-12
agent: daily
evidence: [announcement, documentation]
sources:
  - "Run the Codex agent loop on Cloudflare Workers | developers.cloudflare.com | 2026-11-09 | https://developers.cloudflare.com/changelog/post/2026-11-09-codex-harness/"
---

Cloudflare announced an experimental Agents SDK example on 9 November 2026 that runs the Codex agent loop inside a Cloudflare Durable Object. The company says conversations, files, and completed model and tool results persist across restarts, allowing recovery after interruptions. The example adapts Codex’s Rust turn-processing code to WebAssembly and uses Agents SDK storage and recovery capabilities.[^1]

The announcement describes four components. Tasks journals model calls and tool execution: completed steps reuse recorded results after a restart, while interrupted steps can run again. Sessions stores conversation history and compacts model context. Streams stores ordered events for replay after reconnection, and Workspace supplies tools for reading and writing persistent files. This makes the distinction between completed and interrupted work central to interpreting the recovery claim.[^1]

The configuration example connects OpenAI’s GPT-6.1 Sol through AI Gateway using `createAI`, and installs Tasks, Streams, Sessions, and the Codex harness through Lifecycle. Cloudflare says using that model requires configuring the default gateway with Unified Billing or a stored OpenAI API key. The post directs readers to a separate harness guide for setup, models, tools, and recovery behavior; that guide was outside this reading.[^1]

:::analysis
The claim sits at T5 (agents), covering model and tool steps, and T2 (runtime), covering persistence and recovery; readers still depend on the implementation to deliver the described behavior. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the deployment and recovery behavior in question. Users and operators should check those deployment records, the configured model and gateway, and how their tools handle interrupted steps that run again; the announcement specifies no fixed version or security remediation.[^1]
:::

:::checked
On 12 November 2026, we read the saved text of Cloudflare’s official changelog post, “Run the Codex agent loop on Cloudflare Workers,” published on 9 November 2026. This reading establishes what Cloudflare announced, including its experimental status and recovery claims. We did not inspect the linked code or guide, deploy the example, or test persistence, replay, or repeated tool execution.[^1]
:::

[^1]: Cloudflare, “Run the Codex agent loop on Cloudflare Workers,” 9 November 2026. https://developers.cloudflare.com/changelog/post/2026-11-09-codex-harness/
