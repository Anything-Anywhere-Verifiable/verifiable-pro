---
title: "KVGuard Authors Report Block-Level Safety Checks for LLM Serving"
dek: "An arXiv paper describes checks for KV cache errors in vLLM and SGLang, reporting coverage of 29 historical bugs. The saved abstract does not identify affected or fixed releases."
kind: news
topics: [evaluation-audits, verifiable-inference]
layers: [runtime]
event_date: 2026-11-04
published: 2026-11-06
agent: daily
evidence: [announcement, documentation]
sources:
  - "KVGuard: A KV Cache Safety Checker for LLM Serving Systems | arXiv | 2026-11-04 | https://arxiv.org/abs/2611.06138"
---

Jonguk Cheong, Myungbin Hwang, Eulgyu Kim and Byoungyoung Lee submitted KVGuard to arXiv on 4 November 2026, describing a checker for key-value (KV) cache memory safety in large language model serving. The authors report a prototype on vLLM and SGLang that covers all 29 historical KV cache safety bugs they collected from those systems’ patch histories.[^1]

The abstract locates the problem in PagedAttention, which divides a CUDA-allocated GPU memory region into physical blocks and maps requests to them through a CPU-built block table. The authors say errors including double-free, use-after-free, out-of-bounds access, uninitialized reads and permission violations can silently corrupt outputs or break request isolation without crashing. They argue that existing memory sanitizers track CUDA addresses rather than the cache’s blocks, requests and tables.[^1]

KVGuard maintains compact shadow metadata for each physical KV block, recording permissions for each request and initialization for each entry. Its five checks span CPU allocation, block-table construction and translation, and GPU table lookup and cache access. The authors report eight previously unknown violations and no false positives in their evaluation. On Qwen 2.5 14B, they report geometric-mean TPOT overhead of 3.0% for vLLM and 7.4% for SGLang, with memory overhead at most 0.11% of the KV cache.[^1]

:::analysis
The issue sits at T2, runtime: cache allocation and request mapping affect whether users can trust request isolation and output integrity. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed when those records can be matched to affected conditions. Users and operators should verify that deployment records support that comparison; the saved abstract supplies no affected-version list or recommended fixed version, so it cannot settle exposure or remediation for a particular service. Reported checker results also leave the completeness of its coverage to trust.[^1]
:::

:::checked
On 6 November 2026, we read the saved arXiv abstract-page text for “KVGuard: A KV Cache Safety Checker for LLM Serving Systems,” including its v1 submission history. This establishes what the authors reported, not independent confirmation of the results. We did not read the full paper, inspect code, or test the system.[^1]
:::

[^1]: KVGuard: A KV Cache Safety Checker for LLM Serving Systems. arXiv, submitted 4 November 2026. https://arxiv.org/abs/2611.06138
