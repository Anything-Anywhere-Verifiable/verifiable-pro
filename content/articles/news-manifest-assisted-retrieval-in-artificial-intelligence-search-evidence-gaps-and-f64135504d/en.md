---
title: "Manifest Retrieval Study Reports Output Effects, Leaves Live Agent Risks Open"
dek: "An arXiv manuscript reports attacker-target adoption in a controlled pilot involving supplied manifest content. Its abstract explicitly leaves live retrieval and downstream actions outside the experiment."
kind: news
topics: [evaluation-audits, agents-accountability]
layers: [evaluations, agents, outputs]
event_date: 2026-10-28
published: 2026-10-30
agent: daily
evidence: [announcement, documentation]
sources:
  - "Manifest-Assisted Retrieval in Artificial Intelligence Search: Evidence Gaps and a Security Evaluation | arXiv | 2026-10-28 | https://arxiv.org/abs/2610.38361"
---

Gangzhen Qian and seven coauthors submitted a manuscript on 28 October 2026 examining evidence gaps around `/llms.txt` consumption in AI search. The saved arXiv abstract reports a controlled pilot in which ordinary evidence was held fixed, while explicitly leaving full retrieval and agent evaluation open.[^1]

The authors say their non-systematic audit of external sources did not isolate the incremental security or utility effect of consuming `/llms.txt`. A purposive study of 15 tools observed no automatic requests in 45 trials at one endpoint. A separate non-probability log study found that 97% of domains with detected files received no recorded requests in May 2026. These observations concern fetching; the abstract separately distinguishes publication, fetching, model use and action.[^1]

The reduced pilot covered 24 tasks across eight sites, five conditions and 120 real model responses. According to the abstract, frozen automatic scoring identified attacker-target adoption in 21 of 24 raw adversarial responses, with one further response unresolved. The adversarial URLs-only condition had no known adoptions and one unresolved response. These are reported output changes conditional on supplied evidence; the pilot involved neither live retrieval nor external actions. The authors also report exercising deterministic pre-model controls with 30 author-defined parser fixtures.[^1]

:::analysis
The issue spans T6 evaluations, T5 agents and T4 outputs: the reported scoring concerns outputs under controlled evidence, so a verifier cannot infer a deployed agent’s retrieval or action behavior from those results. Users and operators should check whether their own systems fetch manifests, pass their contents to models and permit downstream actions; the saved abstract recommends no fixed software version. The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the relevant manifest-processing path; those records alone do not establish harmful output or action.[^1]
:::

:::checked
On 30 October 2026, we read the saved arXiv abstract and submission record for “Manifest-Assisted Retrieval in Artificial Intelligence Search: Evidence Gaps and a Security Evaluation,” version v1. We did not read the full manuscript or reproducibility artifact, reproduce the reported measurements, or test the system. This reading establishes what the authors report and the experiment’s stated boundaries, not independent confirmation of its results.[^1]
:::

[^1]: https://arxiv.org/abs/2610.38361

Lead photo: Gangzhen Qian, Kainan Zhou, Chuhong Xu, Hang Xiao, Zhi Jing, Rong Bao, Lu Yi, Zhaoyi Li · CC BY 4.0.
