---
title: "Sandman Authors Report Sandbox Operations for Agent Training on Shared Kubernetes"
dek: "An Amazon-built service reportedly supported millions of training sandboxes. The saved arXiv abstract describes its architecture and scale claims, but does not establish isolation strength or reproducibility."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-10-29
published: 2026-10-30
agent: daily
evidence: [announcement, documentation]
sources:
  - "Sandman: Building and Operating Sandboxes for Agentic Reinforcement Learning on Shared Kubernetes | arXiv | 2026-10-29 | https://arxiv.org/abs/2610.39711"
---

Yiming Yan and co-authors submitted the Sandman paper on 29 October 2026, describing a sandbox service built and operated at Amazon for agent tool execution and evaluation. The authors say it serves multiple production workloads for agentic reinforcement learning (RL) on shared Kubernetes clusters. The announcement concerns a paper and operating experience; its abstract says the daemon, provider and pool will be open-sourced, without establishing that release has happened.[^1]

A training framework supplies a task image, then issues commands and file operations inside the returned sandbox. According to the abstract, files and processes persist between calls until the framework releases the environment. Each sandbox is a Kubernetes pod with a small daemon mounted into the unmodified image; Sandman manages creation, readiness and cleanup.[^1]

The authors report 11,858 concurrent tiny sandboxes in a scale test and 3.1 million sandboxes created across four production SWE-bench Verified training campaigns in October 2026. These are author-reported results. The abstract identifies creation bursts, task preparation, abandoned-sandbox reclamation and controlled evaluation as operational concerns, but provides insufficient detail to independently assess those results or isolation guarantees.[^1]

:::analysis
The claims sit at T6 evaluations, T5 agents and T2 runtime: environment lifecycle and persistent state affect the conditions under which agent behavior is assessed, while this abstract alone leaves implementation and operational claims to trust. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular deployment. Users and operators should verify their own task images, daemon versions, configurations, state lifetimes and cleanup behavior; these are checks prompted by the described architecture, and the saved source names no fixed version or upgrade recommendation.[^1]
:::

:::checked
On 30 October 2026, we read the supplied saved arXiv abstract page for Sandman, identifier 2610.39711v1, including its submission history. We did not read the full paper, inspect code or test the system. This reading establishes what the authors reported and the submission date, without independently confirming performance, isolation or deployment behavior.[^1]
:::

[^1]: Sandman: Building and Operating Sandboxes for Agentic Reinforcement Learning on Shared Kubernetes. arXiv, 29 October 2026. https://arxiv.org/abs/2610.39711
