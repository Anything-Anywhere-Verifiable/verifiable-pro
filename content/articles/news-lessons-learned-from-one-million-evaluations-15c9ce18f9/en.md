---
title: "Kiro Says Pass Rates Missed Coding Agent Tool Failures"
dek: "Kiro reports that a new model encountered invalid tool inputs despite an expected benchmark pass rate. It says its evaluation process now tracks efficiency and user feedback alongside task completion."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents]
event_date: 2026-11-17
published: 2026-11-20
agent: daily
evidence: [announcement, documentation]
sources:
  - "Lessons learned from one million evaluations | kiro.dev | 2026-11-17 | https://kiro.dev/blog/1m-evals-lessons/"
---

On 17 November 2026, Kiro described an evaluation failure in which a new model achieved an expected pass rate on Terminal Bench 2.1 while some tools failed on 40% of their calls. Kiro says the model submitted invalid inputs because a tool description that worked for other models did not work well for the new one. The post does not identify the model or a fixed software version.[^1]

According to Kiro, the model could retry until it submitted a valid request, so the errors did not affect the pass rate. Those retries consumed tokens and increased latency. The company says the incident showed how a benchmark nearing saturation, where tasks are solved despite regressions, can miss changes that matter to users.[^1]

Kiro says it now maintains a versioned benchmark suite informed by aggregated usage categories from internal Amazon users. Its process tracks pass or fail, signals such as latency and token use, and large language model judgments of harder-to-measure qualities such as code quality and response tone. It also compares benchmark signals with surveys, satisfaction ratings and user feedback. Kiro reports that tool-failure data helped it fix the inconsistent description, but the post does not provide results that independently establish the fix's effect.[^1]

The post also describes a curation problem: a highly rated, merged pull request looked suitable as a benchmark example until repository history showed that the next commit fixed bugs it had introduced. Kiro says it plans further research on benchmark curation and complex customer configurations.[^1]

:::analysis
The issue sits at T6 evaluations and T5 agents: a task-completion score can conceal costly agent behavior, so a reader must rely on additional measurements and the evaluator's judgment. The property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the described issue. Users and operators should check their own model, client, tool descriptions and other relevant configuration against available deployment records; the post names no fixed version to check against. Its account does not establish that any particular user's deployment was affected or fixed.[^1]
:::

:::checked
On 20 November 2026 we read Kiro's saved official post, “Lessons learned from one million evaluations.” We did not test Kiro or independently verify its measurements, deployment history or fix. The source is available at https://kiro.dev/blog/1m-evals-lessons/.[^1]
:::
