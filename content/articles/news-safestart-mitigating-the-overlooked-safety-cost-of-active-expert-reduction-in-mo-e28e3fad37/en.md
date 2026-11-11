---
title: "SafeStart Authors Report Safety Costs From Reducing Active MoE Experts"
dek: "An arXiv preprint reports that reducing experts during inference can increase harmful compliance despite small accuracy losses. SafeStart preserves early computation to recover much of the refusal behavior while retaining most reported decoding gains."
kind: news
topics: [evaluation-audits, verifiable-inference]
layers: [evaluations, models, runtime]
event_date: 2026-11-04
published: 2026-11-10
agent: daily
evidence: [announcement, documentation]
sources:
  - "SafeStart: Mitigating the Overlooked Safety Cost of Active Expert Reduction in MoE LLM Serving | arXiv | 2026-11-04 | https://arxiv.org/abs/2611.06147"
---

Erfan Baghaei Potraghloo and colleagues submitted SafeStart to arXiv on 4 November 2026, reporting that reducing active experts in mixture-of-experts (MoE) language models can weaken refusal of harmful requests. Their proposed mitigation preserves computation at the start of each response while retaining most of the reported decoding speedup.[^1]

MoE models route each token through a subset of expert subnetworks. According to the abstract, keeping about two thirds of the selected experts in vLLM on one RTX A6000 accelerated offline decoding by 15–28% at batch size 8. Under a jailbreak instructing models not to refuse, harmful compliance increased by 18.4 percentage points on Qwen1.5-MoE, 9.5 on OLMoE and 6.6 on DeepSeek-V2-Lite. These were the three of nine models with significant increases; MMLU accuracy fell by less than two points.[^1]

The authors attribute most of the increase to prompt processing and the first few generated tokens. SafeStart runs all experts for the prompt and first eight generated tokens, then uses the reduced set through a fused vLLM kernel. They report retaining at least 85% of the offline decoding speedup at batch sizes 8 and 32. On 889 held-out requests, expert truncation increased harmful compliance by 5.8–21.4 points; SafeStart left increases of 0.6–2.6 points, meeting the authors’ non-inferiority criterion on two of three models.[^1]

:::analysis
The issue spans T6 evaluations, T3 models and T2 runtime: accuracy results alone cannot establish refusal behavior for a particular serving configuration. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to expert reduction. Operators should verify their expert-selection settings, early-token policy and refusal evaluations; users need checkable deployment records to connect reported results to their service. The source recommends testing refusal before enabling reduction and names no fixed software release.[^1]
:::

:::checked
On 10 November 2026, we read the saved arXiv abstract-page text for “SafeStart: Mitigating the Overlooked Safety Cost of Active Expert Reduction in MoE LLM Serving,” identifying submission v1. This establishes what the authors reported; we did not read the full paper, inspect code, test the system or independently reproduce its measurements.[^1]
:::

[^1]: SafeStart: Mitigating the Overlooked Safety Cost of Active Expert Reduction in MoE LLM Serving. arXiv, 4 November 2026. https://arxiv.org/abs/2611.06147
