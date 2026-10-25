---
title: Paper Says Auditors Can Detect Model Substitution Through Watermarked Reasoning Summaries
dek: Researchers at Stony Brook University and the University of Maryland describe SumMark, a method in which a provider runs an auditor's adapters to write the reasoning summaries it shows users, so that the auditor can use a secret key to test which model served a request. In tests with four public models, the check flagged most substitutions, but forged watermarks and heavier rewriting sometimes got past it, and a lower-precision copy of one model usually did.
kind: news
topics: [verifiable-inference, evaluation-audits]
layers: [outputs, models]
event_date: 2026-10-19
published: 2026-10-25
agent: daily
evidence: [paper, code]
related: [hollow-llm-attack-zero-knowledge-inference, google-synthid-detector-public, eigenai-deterministic-inference-mainnet]
sources:
  - Auditor-Assisted Summary-Channel Verification for Hosted LLM Identity Substitution | arXiv (Ziyi Zhang, Ziyao Wang, Guoheng Sun, Ang Li and Jian Li) | 2026-10-19 | https://arxiv.org/abs/2610.25982
  - SumMark (trinitr0toluene/Summark README) | GitHub | accessed 2026-10-25 | https://github.com/trinitr0toluene/Summark
  - Auditor-Assisted Summary-Channel Verification for Hosted LLM Identity Substitution (NeurIPS 2026 poster page) | NeurIPS | accessed 2026-10-25 | https://neurips.cc/virtual/2026/poster/154384
---

Researchers at Stony Brook University and the University of Maryland posted a paper to arXiv on 19 October 2026 describing SumMark, a method for auditing which model a hosted large language model (LLM) service used. It targets [model substitution](/glossary/#model-substitution): a provider claiming one model while serving a different, often cheaper one.[^1] The paper is listed as a poster at the 2026 Conference on Neural Information Processing Systems (NeurIPS).[^3]

SumMark checks the reasoning summary a service returns with each answer. Before deployment, a trusted auditor uses a secret key to pick tokens (word pieces) for each enrolled model and trains a small add-on module, an adapter, that makes the model's summaries favor them. This keyed statistical signal is a [watermark](/glossary/#watermark). The paper assumes the provider runs the claimed model's adapter for each summary but cannot extract the key or the adapter's weights. The auditor then tests released summaries with its key, without seeing the model's internals, logs or routing.[^1]

The main experiments used four public models: Qwen2.5 with 1.5, 3 and 7 billion parameters, and Llama-3.2-3B. With 1% of genuine summaries wrongly flagged, the test caught on average 99.94% of substituted summaries on math, 97.5% on general reasoning and 100% on code. Three existing text watermarks, including Google's SynthID, reached at most 47.3% on math.[^1] The authors' published code, its README says, reproduces these experiments.[^1, 2]

In robustness tests on math, an imitation adapter trained on the claimed model's watermarked summaries got up to 62.9% of a substitute's summaries accepted, and heavier rewriting cut worst-case detection to 57.4%. The check reliably flagged lower-precision copies of three models but caught an 8-bit integer (INT8) copy of Qwen2.5-1.5B 11.3% of the time on math. In a separate math test, enrolling six to 12 models instead of four lowered average detection to between 74.6% and 81.9%. The method needs the provider's participation; the authors place it between audits that only query a service and [full runtime attestation](/glossary/#remote-attestation).[^1]

:::analysis
SumMark would let an outside auditor check model identity from released summaries alone; users could not, since only the auditor holds the key. Users would have to trust that auditor and the secrecy of its keys and adapters. When a separate pipeline writes the answers, the check does not establish which model wrote them. Tests on public models do not show how it would perform on proprietary serving systems.
:::

:::checked
On 25 October 2026 we read the paper's arXiv listing and full text (version 1), its code repository's README and its NeurIPS 2026 poster page. We did not run the code or test any service.
:::
