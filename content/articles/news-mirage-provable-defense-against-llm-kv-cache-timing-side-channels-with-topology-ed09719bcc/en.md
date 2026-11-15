---
title: "Mirage Authors Propose Gateway Timing Defense for Shared LLM Caches"
dek: "An arXiv preprint proposes delaying token emission to obscure cache timing signals while preserving sharing. Its abstract reports experimental results, but the saved source does not establish deployment protection."
kind: news
topics: [formal-verification, evaluation-audits]
layers: [runtime]
event_date: 2026-11-07
published: 2026-11-13
agent: daily
evidence: [announcement, documentation]
sources:
  - "Mirage: Provable Defense Against LLM KV Cache Timing Side Channels with Topology-Aware Isolation | arXiv | 2026-11-07 | https://arxiv.org/abs/2611.10756"
---

Xiaobei Yan and Tianwei Zhang submitted Mirage to arXiv on 7 November 2026, proposing a defense against timing side channels in shared large language model (LLM) services. The authors claim their framework bounds timing leakage while retaining the efficiency benefits of sharing key-value (KV) caches across tenants.[^1]

The abstract describes an attack that exploits differences in time to first token (TTFT) between cache hits and misses. By probing matching prefixes, an attacker can use those differences to infer sensitive prompt tokens. Mirage moves the defense to the gateway: it delays token emission while allowing the graphics processing unit (GPU) to continue serving other requests, according to the authors.[^1]

A component called the Privacy Odometer persistently tracks the topological novelty of prefix fan-out expansions to distinguish probing from benign traffic. Once a prefix crosses a safety threshold, a two-phase policy uses a dynamic estimator to pad TTFT toward a calibrated cache-miss baseline. The abstract does not specify the threshold or estimator settings.[^1]

The authors report that, on a 500-sample public corpus across three models, Mirage reduces the timing channel to near random guessing while maintaining lower TTFT than defense baselines. They also claim resistance to a strong adaptive adversary and applicability to semantic caching. These are research claims reported in the abstract; the saved page provides neither detailed measurements nor the mathematical argument supporting the leakage bound.[^1]

:::analysis
The issue sits at T2 (runtime): cache sharing and gateway emission determine what timing an observer sees, so a user or verifier must trust that the deployed policy matches the claimed defense. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the described conditions. Users should seek those records; operators should check cache-sharing behavior, gateway policy, thresholds, and calibration against the claimed mechanism. The saved source recommends no fixed software version and supplies no deployment verification procedure.[^1]
:::

:::checked
On 13 November 2026, we read the supplied saved arXiv abstract and submission record for “Mirage: Provable Defense Against LLM KV Cache Timing Side Channels with Topology-Aware Isolation,” arXiv:2611.10756v1. This establishes what the authors reported and the submission date. We did not read the full paper, inspect an implementation, or test the system; we did not independently validate its mathematical or experimental claims.[^1]
:::

[^1]: Xiaobei Yan and Tianwei Zhang, “Mirage: Provable Defense Against LLM KV Cache Timing Side Channels with Topology-Aware Isolation,” arXiv, 7 November 2026. https://arxiv.org/abs/2611.10756
