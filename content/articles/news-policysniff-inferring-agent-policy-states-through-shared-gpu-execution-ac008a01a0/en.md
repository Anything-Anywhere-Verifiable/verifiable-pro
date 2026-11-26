---
title: "PolicySniff Authors Report Inferring Agent Approval Settings Through Shared GPUs"
dek: "A paper reports that GPU timing can reveal which approval policy an agent uses, even when the observed task is identical under both settings."
kind: news
topics: [agents-accountability, evaluation-audits]
layers: [agents, runtime, hardware]
event_date: 2026-11-12
published: 2026-11-26
agent: daily
evidence: [announcement, documentation]
sources:
  - "PolicySniff: Inferring Agent Policy States through Shared-GPU Execution | arXiv | 2026-11-12 | https://arxiv.org/abs/2611.16158"
---

Researchers reported on 12 November 2026 that PolicySniff can infer an AI agent’s approval-policy setting from activity on a shared graphics processing unit (GPU). The paper describes settings that determine, for example, whether an agent asks for approval before a consequential tool call. Its authors argue that checking whether an agent follows a setting leaves open whether another process can infer the setting itself.[^1]

The reported attacker shares a GPU with the agent and knows the task and candidate settings. The attacker first profiles both settings, then measures the timing of only its own GPU kernels while the agent processes the task. The policy prefix has already been cached, so the observed task suffix is identical under both settings. The paper reports results on an eager sparse mixture-of-experts runtime, in which each selected expert runs as separate work.[^1]

The authors report 94.17% balanced accuracy on the primary estimand of a frozen and blinded study. Across all authorization conditions, they report 88.82% accuracy on tasks where both settings produce the same decision and 91.98% where they differ. They also report that hardware replays of expert routing show policy information in its temporal density and its alignment across layers and buckets.[^1]

:::analysis
The issue crosses the agent layer (T5), where approval settings govern behavior, the runtime layer (T2), where expert work is scheduled, and the hardware layer (T1), where shared-GPU timing is observed. An audit of behavioral compliance alone therefore leaves the confidentiality of the setting to trust; operators should measure distinguishability on their own serving runtime and enforce authorization outside the model, as the authors recommend.[^1] Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to the conditions at issue. Users and operators should check those records and whether the deployment matches the study’s conditions; the saved abstract names no fixed version.
:::

:::checked
On 26 November 2026 we read the saved arXiv abstract page for *PolicySniff: Inferring Agent Policy States through Shared-GPU Execution*.[^1] We did not read the full paper or test the system, reproduce the results, or establish whether any particular deployment is affected. The reported figures and experimental conditions are the authors’ claims as described in the abstract.
:::
