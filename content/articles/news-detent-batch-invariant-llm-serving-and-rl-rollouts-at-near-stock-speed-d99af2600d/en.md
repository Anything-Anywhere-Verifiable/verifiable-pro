---
title: "Detent Authors Report Batch-Invariant LLM Serving at Near-Stock Speed"
dek: "The preprint targets batch-dependent kernel selection and reports reproducible outputs with lower overhead than engine deterministic modes. We reviewed only the saved arXiv abstract page."
kind: news
topics: [verifiable-inference, evaluation-audits]
layers: [evaluations, runtime]
event_date: 2026-11-07
published: 2026-11-14
agent: daily
evidence: [announcement, documentation]
sources:
  - "Detent: Batch-Invariant LLM Serving and RL Rollouts at Near-Stock Speed | arXiv | 2026-11-07 | https://arxiv.org/abs/2611.10611"
---

On 7 November 2026, the authors of Detent submitted a preprint describing a method for batch-invariant large language model (LLM) serving: a request should produce the same output bits regardless of which other requests share its batch. The abstract reports performance close to standard engine settings, with applications to reproducible evaluation, verifiable inference and reinforcement learning (RL).[^1]

The authors identify kernel selection as a remaining source of variability even when individual kernels are batch-invariant. Engines choose kernels and their parameters using batch-dependent information; mathematically equivalent sums can round differently. Detent represents kernel selection as a program, identifies the smallest set of values that must remain fixed, and tunes those values for a workload before deployment.[^1]

For multi-GPU Llama-3.1-70B and Qwen3-30B-A3B deployments in vLLM and SGLang, the abstract reports batch invariance. With tuning for each load, latency per output token was 1.04–1.17 times Stock, meaning each engine’s standard settings, compared with 1.67–10.3 times Stock for deterministic modes. It also reports bit-for-bit replay of seeded RL rollouts under different batches and cache splits, and matching trainer and rollout log probabilities at 1.03 times Stock’s rollout time per token. These are the authors’ reported results.[^1]

:::analysis
The claim sits at T6 (evaluations) and T2 (runtime): runtime choices affect whether evaluation and replay can reproduce the same bits, so users still depend on the deployed configuration matching the tested conditions. Identifiability is the verifiable property at stake: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the batch-dependent behavior at issue. Users and operators should verify their engine, model, deployment settings and fixed kernel-selection values, then check replay across batch and cache changes; the abstract supplies no recommended fixed software version. Reproducibility alone does not establish that an answer is correct.[^1]
:::

:::checked
On 14 November 2026, we read the supplied saved arXiv abstract page for “Detent: Batch-Invariant LLM Serving and RL Rollouts at Near-Stock Speed,” arXiv:2611.10611v1. This establishes what the abstract claims and its submission date. We did not read the full paper or code, test the system, or independently confirm its performance and reproducibility results.[^1]
:::

[^1]: https://arxiv.org/abs/2611.10611
