---
title: "Researchers Report Request-Level Analysis of Live GPU Hidden States"
dek: "An arXiv paper describes recovering intermediate states from a live inference process and using them to distinguish refusal from compliance. The reported results come from the paper’s abstract; we did not test the method."
kind: news
topics: [evaluation-audits, verifiable-inference]
layers: [evaluations, runtime]
event_date: 2026-11-13
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "From Bytes to Behavior: Request-Level Attribution from Live GPU Hidden States | arXiv | 2026-11-13 | https://arxiv.org/abs/2611.18272"
---

A paper submitted to arXiv on 13 November 2026 describes a method for recovering intermediate states from a running GPU inference process and using them to examine large language model behavior. The authors say the method can work without restarting or modifying the service and without prior knowledge of the model’s architecture parameters or weights.[^1]

The abstract describes a six-stage process that uses platform-specific adapters and a non-modifying debugger. It says the method uses either a PyTorch allocator clock or a kernel-launch clock to identify and read tensor allocations in GPU memory. The targeted data are per-layer residual-stream activations: intermediate values produced as the model processes a request.[^1]

The authors report validating acquisition on 33 open-source decoder-only models across nine architecture classes. They say the recovered bytes matched exactly and were usable for downstream analysis. In one use case, they applied linear probes trained on standard framework activations to the recovered states; the abstract reports an AUROC of 0.88 for distinguishing refusal from compliance on held-out prompts. AUROC summarizes how well a classifier ranks examples across thresholds; this result is the authors’ reported measurement, not an independently reproduced test.[^1]

:::analysis
The work sits at T6, evaluations, and T2, runtime: it proposes runtime observations as evidence for an evaluation of behavior. A verifier must still trust or check the acquisition and analysis, and the reported classification result does not by itself establish what happened for every request. Identifiability also matters: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed to a particular condition; operators and users should verify what their own records establish. The abstract gives no fixed version or recommendation to install one, and does not establish whether a particular deployment is exposed.[^1]
:::

:::checked
On 23 November 2026 we read the saved arXiv abstract page for “From Bytes to Behavior: Request-Level Attribution from Live GPU Hidden States.”[^1] We did not read the full paper or test the system, and cannot independently confirm the reported acquisition or classification results from the abstract.
:::
