---
title: "Google Describes Verification Loops for Antigravity Agents"
dek: "A Google Cloud post proposes tests, evaluation gates and budget limits for coding agents. Its reliability figures are illustrative, and the example is described as experimental."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents, runtime]
event_date: 2026-11-18
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "How to Build Durable Agentic Systems with Google Antigravity: From Instructions to Loops | cloud.google.com | 2026-11-18 | https://cloud.google.com/blog/topics/developers-practitioners/how-to-build-durable-agentic-systems-with-google-antigravity-from-instructions-to-loops"
---

On 18 November 2026, Google Cloud published an account of how developers might build longer-running coding-agent workflows with Google Antigravity. Developer relations author Alex Astrum recommends setting acceptance criteria and tests before an agent starts, then using checks, limited retries and human intervention to manage the work.[^1]

The post describes Git-backed checkpoints for state, test suites and compilers as verification gates, evaluations for judgments that cannot be checked deterministically, and limits on turns, tokens or cost. It says project instructions should forbid an agent from passing a gate by deleting or weakening a test. Astrum also recommends inspecting evaluations for accuracy and checking for missed edge cases.[^1]

Astrum describes `/grill-me` as a way to establish constraints and tests before using `/goal` loops in Google Antigravity 2.0. The post also presents an experimental SDK example in which a supervisor delegates work, runs a test suite, feeds failure output back for one retry and stops when configured budgets are exceeded. The author explicitly calls the example a starting point rather than a production-ready solution.[^1]

The post’s calculation of a 95% success rate over 20 steps assumes 95% per-step accuracy and a 95% chance of detecting and fixing each error. Those are illustrative assumptions, not measured results for Antigravity. A passing test also establishes only what that test checks; the post itself cautions about overlooked cases.[^1]

:::analysis
The proposal sits at T6 evaluations, T5 agents and T2 runtime: checks assess selected outcomes, agents perform the work, and the surrounding execution environment applies the configured limits. Users and operators should inspect their own tests, evaluation accuracy, retry behavior and budgets before relying on a run; the post does not establish that a particular deployment enforces them. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular issue; the post does not document such a record or identify an affected or fixed version.[^1]
:::

:::checked
On 23 November 2026, we read the saved text of Google Cloud’s “How to Build Durable Agentic Systems with Google Antigravity: From Instructions to Loops.” We did not test Antigravity, the SDK example or its claimed behavior, and reading the post does not independently establish the reliability of a deployed system.[^1]
:::
