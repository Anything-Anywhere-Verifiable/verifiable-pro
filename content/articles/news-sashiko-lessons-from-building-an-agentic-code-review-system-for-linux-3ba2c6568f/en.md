---
title: "Google Reports Lessons From Sashiko’s Linux Code Reviews"
dek: "Google describes a multi-agent review pipeline and reports results from its use on Linux kernel patches. Public review records aid inspection, while the reported outcomes remain Google’s claims."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, outputs]
event_date: 2026-11-18
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "Sashiko: Lessons from building an agentic code review system for Linux | cloud.google.com | 2026-11-18 | https://cloud.google.com/blog/products/application-development/lessons-from-building-sashiko-an-agentic-code-review-system"
---

On 18 November 2026, Google described how Sashiko, its Gemini-powered agentic code review system, examines Linux kernel patches and reported results from its use. Google says it donated the open-source project to the Linux Foundation earlier in the year and runs a service that reviews patches sent to public kernel mailing lists.[^1]

The review pipeline gathers surrounding code and subsystem guidance, then runs up to seven specialist sessions on areas such as locking, resource lifetimes and security. A lead verifier triages both potential bugs and concerns that specialists dismissed. Difficult cases receive separate checks, with agents asked to support both bug claims and dismissals with code evidence across call sites. The system then produces a review report.[^1]

Google says prompts, tool calls, reasoning steps and ruled-out bugs are public. It also says maintainers must opt in before Sashiko sends review emails to their lists. Local users can choose different models and customize prompts, while the current prompt system combines generated code notes with maintainer instructions.[^1]

Google reports that, among 21,500 tracked mainline commits, 0.9% of patches with a clean Sashiko review received a follow-up fix within 60 days, compared with 7.6% of patches merged despite a critical warning. These are reported observations, not a controlled demonstration that Sashiko caused the difference. Google also reports that its benchmark contains nearly 1,000 historical kernel bugs; it says Sashiko caught 75.8% with Gemini 4 Carbon at high thinking level.[^1]

:::analysis
The issue sits at T5 `agents`, where review decisions and tool use occur, and T4 `outputs`, where reports expose the findings and supporting material for inspection. Public records can help a verifier examine a particular review, but a clean report still leaves the reviewer’s coverage and judgment to trust. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to that version and configuration. Users and operators should check which model, prompts and review settings their own instance uses, and whether its records support that identification; the source recommends no fixed version.[^1]
:::

:::checked
On 23 November 2026, we read the saved text of Google Cloud’s “Sashiko: Lessons from building an agentic code review system for Linux,” published 18 November 2026.[^1] We did not test Sashiko or independently check the reported figures, review records or benchmark.
:::

[^1]: https://cloud.google.com/blog/products/application-development/lessons-from-building-sashiko-an-agentic-code-review-system
