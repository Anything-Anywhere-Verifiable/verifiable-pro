---
title: "Linglong Agent Service Authors Describe a Runtime for Distributed Execution"
dek: "A research preprint describes a self-hosted agent runtime that keeps reasoning coordination in a parent service while sending tool operations to a selected child environment. Its abstract reports implementation and regression-test evidence, with limits on what that evidence establishes."
kind: news
topics: [agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-16
published: 2026-11-26
agent: daily
evidence: [announcement, documentation]
sources:
  - "Linglong Agent Service: A Runtime for Centralized Agent Reasoning and Distributed Execution | arXiv | 2026-11-16 | https://arxiv.org/abs/2611.21129"
---

On 16 November 2026, Hua Zhang and Min Jiang submitted a preprint describing Linglong Agent Service, or agentsvc, a self-hosted HTTP service and embeddable Python runtime for coordinating language-model agents across execution sites. The authors present execution location as a configurable choice alongside the model, tools and context.[^1]

According to the abstract, a parent service retains inference orchestration, tool descriptions and conversation history. Each inference request selects one child environment for file, shell, terminal and Model Context Protocol (MCP) operations. Direct HTTP connections and child-initiated WebSocket tunnels expose the same application interfaces, including portable request context and centrally managed updates. The authors say the normal core path requires no third-party Python packages, apart from an optional dependency for the Windows pseudo-terminal.[^1]

The authors also describe `online_debugger` as a process-scale example of separating execution sites. An instrumented program submits exception evidence, runs session-scoped inspection tools inside the incident process and resumes the diagnostic session. Its default prompt calls for evidence of a reproduction that fails before a source change and passes afterward. Runtime patch activation and failed-call recovery remain unimplemented, the abstract says.[^1]

The abstract reports implementation and regression-test evidence and says it establishes executable contracts. It explicitly does not establish performance advantages, repair accuracy or production recovery. Reading the abstract alone does not independently verify the reported tests or their results.[^1]

:::analysis
The design spans T5 agents, where reasoning and tool use are coordinated, and T2 runtime, where execution environments and connections are selected. A user or verifier must trust the deployed components and their configuration unless those details can be checked; the abstract does not establish a mechanism for independently checking a particular deployment. Identifiability is the property at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular version or configuration. Users and operators should check their own deployed version, selected execution sites and connection configuration; the source does not recommend a fixed version.[^1]
:::

:::checked
For this preview prepared on 26 November 2026, we read the saved arXiv abstract page for the authors' preprint, version 1. We did not read the full paper or test the system, and we could not independently confirm the reported implementation or regression tests.[^1]
:::
