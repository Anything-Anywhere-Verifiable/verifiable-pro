---
title: "vLLM Advisory Says Systemone Endpoint Bypasses Chat Template Trust Check"
dek: "The advisory says callers of an affected endpoint can supply a chat template despite the server’s default restriction. It identifies version 0.34.0 as patched, while listing an inconsistent affected-version range."
kind: news
topics: [verifiable-inference]
layers: [runtime]
event_date: 2026-11-18
published: 2026-11-25
agent: daily
evidence: [announcement, documentation]
sources:
  - "/v1/systemone bypasses the --trust-request-chat-template gate | github.com | 2026-11-18 | https://github.com/vllm-project/vllm/security/advisories/GHSA-xgh8-qwjh-q853"
---

On 18 November 2026, the vLLM project published a security advisory saying that its `/v1/systemone` endpoint bypassed a check on request-supplied chat templates. The advisory says a caller able to reach the endpoint could control how a conversation is serialized, including replacing a system block that an operator normally pins with `--chat-template`. It says the default configuration is affected and no flag is needed.[^1]

According to the advisory, the endpoint passes request-level `chat_template_kwargs` to a shared renderer without calling `validate_chat_template()`. Other serving paths call that check before reaching the renderer. The advisory says the bypass can also allow special tokens or turn boundaries that message-level validation would otherwise disallow.[^1]

The advisory limits the issue to models supported by the relevant read strategies; for unsupported architectures, it says, the endpoint returns 501. It also says the endpoint is registered through the normal app build path and is listed among API-key-protected endpoints. The report does not claim resource exhaustion or escape from the Jinja sandbox.[^1]

The version information is inconsistent. The advisory’s package summary lists affected versions from `0.32.0rc0` through `0.34.0`, inclusive, while also listing `0.34.0` as patched. Its detailed text instead says the issue affects `0.32.0rc0` through `0.33.0` and that `0.34.0` applies the trust check before rendering structured-decision requests.[^1]

:::analysis
The issue sits at the runtime layer, T2: a request path can reach rendering without the intended template trust check. A user or verifier cannot infer that this check was applied to a particular request from the server’s default setting alone. The property at stake is identifiability: if the exact serving version and configuration are recorded and checkable, a user can determine whether they were exposed, subject here to resolving the advisory’s conflicting version range and checking the model and endpoint conditions. Operators should verify their deployed version and configuration, endpoint access and model support, and check the fix in `0.34.0` that the advisory identifies; the version conflict leaves its package summary ambiguous.[^1]
:::

:::checked
On 25 November 2026, we read the saved copy of the vLLM project’s GitHub security advisory GHSA-xgh8-qwjh-q853.[^1] We did not test the system, reproduce the bypass, or independently verify the fix or affected versions.
:::
