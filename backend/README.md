# Chat backend

The site's chat widget ("Ask / 提问") answers questions from verifiable.pro's own articles. The goal is a backend whose readers can check, in their own browser, where an answer was computed: in a hardware-isolated confidential VM with an NVIDIA GPU in confidential-computing mode, running published code and a published model. This folder holds the parts of that backend that live in the site repository. Today that is only the phase-0 mock.

The protocol is fixed first, in [`api/chat-v1.md`](../api/chat-v1.md), so the widget can be finished now and each later backend only has to implement the same three endpoints. The reasoning behind the design, including what a browser can and cannot verify, is in [`docs/assistant-architecture.md`](../docs/assistant-architecture.md).

## The split between browser and backend

The browser does the retrieval. It selects passages from the site's published files and sends them with the question. The backend is an attested language model and nothing more: it keeps no index and no conversation, and it answers only from the passages it receives. This keeps the backend small enough to measure and attest. It also lets the browser check every citation against `/manifest.json` without trusting the backend.

## Phases

| Phase | Backend | Where it lives | What a reader can check |
| --- | --- | --- | --- |
| **0, now** | [`mock/`](mock/): stdlib Python server with extractive answers or a passthrough to a local OpenAI-compatible model. Nothing is attested; the widget shows the demo status. | This repo | Citations against the manifest. Nothing about the backend. |
| 1 | A managed attested-inference provider behind a thin proxy (`backend/proxy/`, a Cloudflare Worker or small VM). Tinfoil is the first choice: its browser verifier is in the Apache-2.0 `tinfoil` npm package, and its EHBP protocol encrypts request bodies to a key inside the attested enclave. Privatemode is the alternative through its browser SDK `privatemode-ai` (MIT), never its proxyless API, which has no client-side attestation. The proxy holds the provider API key, rate-limits, relays the attestation bundle and forwards only ciphertext. | This repo | The provider's enclave evidence and signed release, through the provider's verifier. The operator and proxy see only ciphertext, timing and sizes. |
| 2 | Self-hosted pilot: a measured gateway plus vLLM serving Qwen3.5-9B on one H100 in CC mode, built reproducibly and signed with GitHub build-provenance attestations. First host: Google Cloud Confidential Space on `a3-highgpu-1g` (Intel TDX + 1×H100; only zones us-central1-a, us-east5-a and europe-west4-c; no reservations; about $12/h or more including the confidential-computing surcharge [estimate]). Cheaper 24/7 alternative: Phala Cloud dstack on an H200 (about $5.50/h, 24 h prepaid minimum, US only). | A separate repo, `verifiable-pro-chat` | CPU evidence and its binding to the session keys, the release's Sigstore record, NVIDIA's GPU attestation token, the model and system-prompt digests, and a signed receipt per answer |
| 3 | Independence and hardening: a `vp-verify` command-line verifier that re-checks exported evidence (including the TLS binding a browser cannot see), reproducibility documentation, a published TCB update policy, third-party review | Separate repo | Everything in phase 2, without trusting the site's JavaScript |

Costs, latencies and provider details are snapshots from October 2026 and are explained, with their uncertainty flags, in the architecture document.

## What stays true in every phase

- The badge is computed from checks that ran in the browser. Claims the server makes about itself are shown as *reported*.
- There is no silent fallback. If the backend fails, the widget offers demo answers as an explicit choice.
- Nothing typed is stored server-side. Logs hold time, endpoint, status, latency and token counts, never bodies, IP addresses or user agents.
- A `/privacy/` page (EN and zh) must exist before phase 1 goes live.

## Running the mock

```bash
python3 backend/mock/server.py
```

```bash
python3 -m unittest discover -s backend/mock -p 'test_*.py'
```

Details, flags, test triggers and curl examples are in [`mock/README.md`](mock/README.md).
