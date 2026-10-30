---
title: "Heads of Security Authors Report Improved Prompt Injection Robustness"
dek: "An arXiv preprint describes learned attention gates that separate instructions from untrusted data. Its abstract reports stronger resistance to adaptive attacks, but does not establish protection for a deployed service."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, models]
event_date: 2026-10-27
published: 2026-10-29
agent: daily
evidence: [announcement, documentation]
sources:
  - "Heads of Security: Learned Attention Gates Improve Prompt Injection Robustness | arXiv | 2026-10-27 | https://arxiv.org/abs/2610.37657"
---

Igor Shilov and eight coauthors submitted *Heads of Security: Learned Attention Gates Improve Prompt Injection Robustness* to arXiv on 27 October 2026. The preprint introduces Heads of Security (HoS), a defense using a small set of learned attention gates for individual attention heads to separate trusted instructions from untrusted data.[^1]

According to the abstract, these gates learn how to redistribute attention between trusted and untrusted tokens. The authors evaluated HoS on Llama-3.3-70B-Instruct and GPT-OSS-20B, comparing it with the finetuning defense SecAlign++ and the architectural defense ASIDE.[^1]

The authors report that the black-box RL-Hammer attack achieved an attack success rate (ASR) of 97% against GPT-OSS-20B, 85% against SecAlign, and 10% against HoS. The abstract uses “SecAlign++” in its comparison overview and “SecAlign” for these results; the saved page does not clarify that naming difference. It also reports that an adapted Claudini white-box attack needed three times as many floating-point operations to reach the same ASR against HoS as against GPT-OSS-20B or SecAlign.[^1]

The abstract claims HoS preserves base-model utility across standard multiple-choice benchmarks and prompting setups. On agentic benchmarks with static attacks, it reports similar performance for HoS and SecAlign. These are author-reported research results.[^1]

:::analysis
The claim sits at T6 (evaluations) and T3 (models): benchmark outcomes concern a learned model intervention, so a user must still trust that a serving system matches the evaluated setup. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the configuration in question; those records alone do not establish resistance to an attack. Users and operators should check the served model, gate configuration, and handling of trusted versus untrusted tokens against the evaluated setup; the saved abstract specifies no fixed release or recommended upgrade.[^1]
:::

:::checked
On 29 October 2026, we read the saved arXiv abstract page for arXiv:2610.37657v1, including its submission history. This establishes what the authors reported and the submission date. We did not read the full paper, inspect code, reproduce benchmarks, or test the system; deployment behavior remains unconfirmed.[^1]
:::

[^1]: [Heads of Security: Learned Attention Gates Improve Prompt Injection Robustness](https://arxiv.org/abs/2610.37657), arXiv, 27 October 2026.

Lead photo: Igor Shilov, Xiaoxue Yang, Alexander Panfilov, Evgenii Kortukov, Matthieu Meeus, Peter Romov, Wojciech Samek, Jonas Geiping, Yves-Alexandre de Montjoye · CC BY 4.0.
