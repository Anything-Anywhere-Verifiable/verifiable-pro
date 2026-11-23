---
title: "Researchers Report BlockJack Attack on Shared LLM Cache Mappings"
dek: "The authors say corrupted cache mappings can redirect data between tenants in paged LLM serving. Their abstract reports proposed patches but does not identify a fixed release."
kind: news
topics: [verifiable-inference]
layers: [runtime, hardware]
event_date: 2026-11-19
published: 2026-11-23
agent: daily
evidence: [announcement, documentation]
sources:
  - "BlockJack: Cross-Tenant Redirection Fault Attacks on Paged KV Cache Address Translation in LLM Serving | arXiv | 2026-11-19 | https://arxiv.org/abs/2611.25945"
---

On 19 November 2026, researchers submitted a paper describing BlockJack, an attack that they say can redirect cached data between tenants of a large language model (LLM) service. The authors report both disclosure of victim information in an attacker's responses and changes to a victim's answers caused by attacker-supplied context.[^1]

LLM serving systems retain previously computed states in a key-value (KV) cache to accelerate inference. In paged systems, block tables map each request's logical cache blocks to physical blocks. The paper's abstract says BlockJack corrupts entries in those tables, redirecting reads to blocks assigned to another tenant without changing model parameters, prompts or the cached states themselves. The authors studied mappings in vLLM and say they characterized when redirection targets are predictable.[^1]

The authors report that a faulted mapping exposed victim context across seven models from the Qwen, Llama, Gemma and Phi families. In a 248-scene medical benchmark, they say the integrity attack caused up to 41.1% of responses to recommend less urgent care while appearing consistent with the victim's question. They also report demonstrating physical feasibility with Rowhammer, evaluating assignment validation as a defense, and reviewing and validating patches proposed after disclosure. The abstract says vLLM and Sonar confirmed the vulnerability; it does not name fixed releases.[^1]

:::analysis
The issue spans the runtime layer (T2), where cache mappings govern inference, and the hardware layer (T1), where the authors report a Rowhammer demonstration. A user or verifier cannot infer tenant isolation from a model's identity alone; the serving configuration and its handling of cache assignments also matter. The property at stake includes identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed, provided the applicable affected conditions are known. Users and operators should check their own serving version, configuration and relevant patch guidance; the saved abstract does not specify a fixed version or establish that any deployment is protected.[^1]
:::

:::checked
On 23 November 2026 we read the saved arXiv abstract page for *BlockJack: Cross-Tenant Redirection Fault Attacks on Paged KV Cache Address Translation in LLM Serving* (https://arxiv.org/abs/2611.25945). We did not read the full paper or test the system, attack or patches. The reported results and patch validation are the authors' claims, and the abstract does not identify the affected version range or a fixed release.[^1]
:::
