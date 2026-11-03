---
title: "Researchers Report a Tool Update Gap in AI Agent Security"
dek: "The ETUDE paper reports attacks through updated tool code outside the model’s context. Its saved abstract provides aggregate results but no affected versions or fixed release."
kind: news
topics: [supply-chain, agents-accountability]
layers: [agents, runtime]
event_date: 2026-11-01
published: 2026-11-03
agent: daily
evidence: [announcement, documentation]
sources:
  - "Beyond Prompt Injection: The Tool Update Gap in LLM Agent Security | arXiv | 2026-11-01 | https://arxiv.org/abs/2611.01976"
---

Researchers from Shanghai Jiao Tong University and Inria submitted a paper on 1 November 2026 describing a supply-chain vulnerability in large language model (LLM) agents: frameworks may keep trusting tools after their implementations change, without checking their safety again. The authors call this the tool update gap.[^1]

Their attack, ETUDE (Exploiting Tool Updates for Direct Execution), embeds malicious functionality in updates to initially benign tools while preserving legitimate functionality. According to the abstract, the malicious code executes outside the LLM’s context and requires no adversarial instructions. The authors therefore argue that defenses restricted to content visible to the model leave this attack path uncovered.[^1]

The authors report evaluating three attack workloads across seven commercial and open-source agent frameworks, including Gemini CLI, Codex CLI, and Claude Code. They report a 97.6% attack success rate and a 95.9% legitimate task completion rate, and say existing defenses provide insufficient protection. These are author-reported aggregate findings; the saved abstract does not provide per-framework results, tested versions, or enough methodology to assess their applicability to a particular deployment.[^1]

:::analysis
The issue sits at T5, agents, where tool trust is retained, and T2, runtime, where updated tool code executes: checking model-visible interactions alone cannot establish what that code does, under the attack described. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed when those records can be matched to affected conditions. Users and operators should verify which tool implementations their systems actually used and whether updates triggered renewed safety checks; the saved source supplies neither an affected-version list nor a recommended fixed version, so it cannot resolve deployment-specific exposure or remediation.[^1]
:::

:::checked
On 3 November 2026, we read the supplied saved arXiv abstract and submission record for *Beyond Prompt Injection: The Tool Update Gap in LLM Agent Security*, arXiv:2611.01976v1. This establishes what the authors reported and the 1 November submission date. We did not read the full paper, test any system, reproduce the results, or confirm a fix.[^1]
:::

[^1]: *Beyond Prompt Injection: The Tool Update Gap in LLM Agent Security*. arXiv, 1 November 2026. https://arxiv.org/abs/2611.01976
