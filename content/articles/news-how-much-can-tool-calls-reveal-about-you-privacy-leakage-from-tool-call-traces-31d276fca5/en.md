---
title: "PrivacyTrace Authors Report User-Profiling Risk From MCP Tool Calls"
dek: "An arXiv paper reports higher profile-inference success from tool-call traces than from prior-based guessing. The saved abstract describes synthetic benchmarks, not confirmed exposure in deployed services."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [evaluations, agents]
event_date: 2026-10-30
published: 2026-11-02
agent: daily
evidence: [announcement, documentation]
sources:
  - "How Much Can Tool Calls Reveal About You? Privacy Leakage from Tool-Call Traces | arXiv | 2026-10-30 | https://arxiv.org/abs/2610.41885"
---

Donghang Duan and five co-authors submitted a paper on 30 October 2026 reporting that tool-call traces can reveal user attributes without access to conversations. The study examines agents using the Model Context Protocol (MCP), which supports interactions with external tools. Its reported risk arises from protocol-valid interactions, rather than requiring malformed tool calls.[^1]

The authors introduce PrivacyTrace, a benchmark comprising 1,000 synthetic user profiles and 4,000 agent trajectories across four domains, generated using real MCP tools from 25 servers. The abstract reports a 26.25% profile-inference attack success rate with four mainstream large language model attackers, compared with 17.97% for prior-based guessing. These are the authors’ experimental results; the saved page does not provide enough methodological detail to independently assess the comparison.[^1]

According to the abstract, tool arguments and returned results supply the main evidence grounded in traces, while linking traces across sessions increases profiling risk. The authors say code and data are available and call for privacy-aware mechanisms for agent-tool interactions. The saved abstract identifies no fixed software version or validated mitigation.[^1]

:::analysis
The issue sits at T6 evaluations and T5 agents: benchmark evidence informs the risk assessment, while tool interactions carry the signals, so protocol validity alone does not establish privacy. Users and operators should verify which arguments and results their own systems expose, who can observe them, and whether sessions can be linked, matching the channels the authors identify. The verifiable property at stake is identifiability: recording and making checkable the exact version and configuration serving a user lets that user determine whether they were exposed to the relevant trace channels; it does not establish that profiling succeeded. The saved source supplies no deployment-specific evidence or recommended fixed version for that check.[^1]
:::

:::checked
On 2 November 2026, we read the saved arXiv abstract and submission record for “How Much Can Tool Calls Reveal About You? Privacy Leakage from Tool-Call Traces,” version v1. We did not read the full paper, inspect code or data, test the system, or reproduce the results. This check establishes what the saved source reports, not the effectiveness of an attack against any particular service.[^1]
:::

[^1]: https://arxiv.org/abs/2610.41885

Lead photo: Donghang Duan, Qingyu Liu, Yifei Liu, Na Zou, Xia Hu, Dongrui Liu · CC BY 4.0.
