---
title: "vLLM Advisory Reports Model Redirection Flaw, Lists 0.33.0 as Patched"
dek: "A crafted model configuration can redirect model and tokenizer loading to another directory, the advisory says. The reported exposure concerns both private tokenizer data and the identity of the model actually served."
kind: news
topics: [verifiable-inference, supply-chain]
layers: [models, runtime]
event_date: 2026-11-02
published: 2026-11-04
agent: daily
evidence: [announcement, documentation]
sources:
  - "vLLM Speculators Config verifier.name_or_path Element Directory Traversal Information Disclosure Vulnerability | github.com | 2026-11-02 | https://github.com/vllm-project/vllm/security/advisories/GHSA-qrj2-j723-m6w8"
---

The vLLM project published a security advisory on 2 November 2026 describing a configuration flaw that can redirect a service to another model directory. Advisory GHSA-qrj2-j723-m6w8 rates the issue Moderate, with a Common Vulnerability Scoring System (CVSS) score of 5.4, and lists versions below 0.33.0 as affected and 0.33.0 as patched.[^1]

According to the advisory, when an operator serves an untrusted model repository, its `config.json` can supply `speculators_config["verifier"]["name_or_path"]`. The loading path assigns that value to both the model and tokenizer without checking whether the destination stays inside an allowed directory. An absolute path also works, the advisory says. The override runs for non-cloud-storage models without requiring `--speculative-config`, and keeping `trust_remote_code=False` does not block this path.[^1]

The advisory reports an end-to-end reproduction against a live `vllm serve`: unauthenticated requests to `/detokenize` disclosed the target directory’s tokenizer vocabulary, while the engine loaded the target checkpoint as its primary model. It also describes query access through the ordinary completions API and identifies shared and multi-tenant hosts as the realistic setting. These are the advisory’s reported results; we did not reproduce them. It credits fix #61587 and lists 0.33.0 as patched; we did not inspect that change or release artifacts.[^1]

:::analysis
The issue sits at T3 (models), where the selected checkpoint and tokenizer determine model identity, and T2 (runtime), where configuration controls what gets loaded. A user or verifier therefore needs evidence of the resolved model identity as well as the advertised repository name. The verifiable property at stake is identifiability: if the exact version and configuration serving a user are recorded and checkable, that user can determine whether they were exposed under the advisory’s conditions. Operators should verify that they run the listed patched version, 0.33.0, and check the configuration, resolved model and tokenizer paths, and directory reachability relevant to their deployment; users should seek those records.[^1]
:::

:::checked
On 4 November 2026, we read the saved official GitHub advisory GHSA-qrj2-j723-m6w8 supplied for this preview. This reading establishes what the advisory reports about affected versions, behavior and remediation; we did not test the system, inspect the referenced fix, or confirm any deployment’s exposure.[^1]
:::

[^1]: vLLM project, “vLLM Speculators Config verifier.name_or_path Element Directory Traversal Information Disclosure Vulnerability,” published 2 November 2026. https://github.com/vllm-project/vllm/security/advisories/GHSA-qrj2-j723-m6w8
