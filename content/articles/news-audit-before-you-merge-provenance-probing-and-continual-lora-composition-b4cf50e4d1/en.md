---
title: "LoRA Study Calls for Provenance Audits Before Model Merging"
dek: "An arXiv preprint reports that incompatible or nearly empty adapters can distort forgetting measurements. Its proposed checks address model identity and evaluation setup; the saved abstract does not establish deployment safety."
kind: news
topics: [evaluation-audits, supply-chain]
layers: [evaluations, models]
event_date: 2026-11-07
published: 2026-11-14
agent: daily
evidence: [announcement, documentation]
sources:
  - "Audit Before You Merge: Provenance, Probing, and Continual LoRA Composition | arXiv | 2026-11-07 | https://arxiv.org/abs/2611.10684"
---

Lenny Aharon, Neta Glazer and Lior Aharon submitted *Audit Before You Merge: Provenance, Probing, and Continual LoRA Composition* to arXiv on 7 November 2026. The authors propose auditing public low-rank adaptation (LoRA) adapters before studying how merging them affects a model’s existing capabilities. Their abstract reports silent base-version mismatches and near-zero adapter update norms, whose inclusion inflates measured interference by roughly 10 percentage points.[^1]

The study treats each adapter merge as a sequential learning task, with the instruction-tuned base model’s capabilities as Task 0. Its proposed audit checks that the adapter matches the base model and that its parameter update has a non-trivial norm. The authors also propose a probing protocol they describe as leakage-free.[^1]

On an audited set of four adapters for Llama-3.1-8B-Instruct, the authors report that naive merging reduces GSM8K performance by 10.5 percentage points and HumanEval performance by 18.3 points. Task Arithmetic with a coefficient of 0.5 falls within one standard error of the unmerged baseline. A coordinate search selects a coefficient of −0.5 for the math adapter as probe-optimal. On Mistral-7B-Instruct-v0.3, two of four candidate adapters fail the audit; the audited merge yields the same ordering of merge methods on GSM8K.[^1]

:::analysis
The claims sit at T6 (evaluations) and T3 (models): adapter identity and selection affect what a forgetting comparison can establish, so users cannot infer reliable composition from an adapter listing alone. Users and operators should verify base-model compatibility and non-trivial update norms, and record the adapters and merge coefficients behind their own evaluations, following the proposed checks.[^1] The verifiable property at stake is **identifiability**: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the configuration in question; this alone does not establish its behavior.
:::

:::checked
On 14 November 2026, we read the saved arXiv abstract page and submission history for arXiv:2611.10684v1. This establishes what the authors reported and the submission date. We did not read the full paper or code, test the system, or reproduce the measurements; the reported results remain author claims.[^1]
:::
