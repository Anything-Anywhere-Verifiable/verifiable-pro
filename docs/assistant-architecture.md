# Site assistant architecture: GPU confidential computing and what readers can verify

This document explains how the site's chat assistant is meant to run on GPU confidential computing, and what a reader's browser can and cannot check about where an answer was computed. It condenses the fact-checked backend design report of 20 October 2026. The wire format is specified in [`api/chat-v1.md`](../api/chat-v1.md), and the phase-0 mock is in [`backend/mock/`](../backend/mock/).

Markers carried over from the report:

- **[unverified]**: not confirmed from a primary source.
- **[from memory]**: prior knowledge, not re-checked during the research.
- **[estimate]**: a number derived by the report's author.
- **[observed]**: checked directly with `curl` against the live endpoint on 2026-10-20.

Prices, availability and version numbers are snapshots from August to October 2026.

## The design decision that shapes everything else: retrieval in the browser

The site's corpus is public and small: 51 English articles of about 35,000 words, their 51 Chinese editions, the About and Vision pages in both languages and 5 data files, listed with the 51 lead images' specs and pictures as 213 entries in `/manifest.json`. The browser can therefore choose the relevant passages itself. It sends the question with those passages, and from phase 1 on it encrypts the request end to end with HPKE (RFC 9180) to a public key that the hardware attestation binds to the measured inference code.

Three consequences follow from this split.

- The backend is an attested language model and nothing more. Every hop between the browser and the enclave can be limited to ciphertext: a Cloudflare or other proxy, a managed provider's router, and Mengyuan as operator.
- The same widget works against the mock (phase 0), a managed attested provider (phase 1) and a self-hosted H100 confidential VM (phase 2). Only the adapter and the trust anchors change.
- Citations can be checked entirely in the browser. The browser hashes the cited article source with WebCrypto and compares the digest with `manifest.json`.

A simpler-looking alternative would bind the enclave's TLS certificate to the attestation, as RA-TLS and NEAR AI's `include_tls_fingerprint` do. That does not work for a web page, because **browsers do not expose the peer TLS certificate to page code**. The only exception is a TLS client compiled to WASM and tunnelled over a WebSocket proxy, such as Concrete Security's atlas. Application-layer encryption to an attested HPKE key is the pattern a browser can use. Tinfoil's EHBP and Apple's Private Cloud Compute both use it.

## Trust model

### What the hardware provides

A confidential VM (CVM) runs inside a CPU trusted execution environment (TEE), Intel TDX or AMD SEV-SNP. The CPU measures what the VM loads and signs a report whose 64-byte `report_data` field can carry data chosen by the VM. Putting a digest of the session keys and the client's nonce there is the basic way to bind a session to an attestation; both TDX and SNP offer the 64 bytes.

An NVIDIA H100 or Blackwell GPU in confidential-computing mode joins that boundary. NVIDIA's whitepaper *Secure AI with Blackwell and Hopper GPUs* (v1.3, August 2025) describes three modes. **CC-On** blocks performance counters. **CC-DevTools** keeps encryption on but unblocks the counters, and Google's token documentation says it disables security protections, so production must reject it. **Off** is the third. Data moves between CPU and GPU through encrypted bounce buffers. Direct link encryption (TDISP/IDE) needs Blackwell and compatible CPUs and switches; whether any rentable cloud offers it today is [unverified], so the design assumes bounce buffers everywhere. Multi-GPU differs by generation. Hopper uses Protected PCIe, which works only on air-cooled 8-GPU HGX systems and leaves NVLink unencrypted. Blackwell encrypts NVLink for up to 8 GPUs per CVM. A single-GPU H100 avoids both questions.

The whitepaper's threat model covers software attacks, basic physical attacks such as bus interposers on PCIe and DDR, rollback, replay and cryptographic attacks. Sophisticated physical attacks and denial of service are out of scope.

### How GPU evidence is tied to the CVM

A verifier needs CPU evidence and GPU evidence, and has to know they describe the same machine. Three patterns are in use.

| Pattern | Used by | What establishes the binding |
| --- | --- | --- |
| The CVM verifies the GPU at boot and refuses to start otherwise; the client checks only the CPU report | Tinfoil (`nvattest` at boot), Privatemode (attestation agent enables the GPU through NVML) | The measured boot code and its policy |
| The same client nonce goes into both reports; the client checks the TDX quote and sends the GPU payload to NVIDIA's service | NEAR AI Cloud, Phala/RedPill | Freshness only. That the GPU is attached to *this* CVM still rests on the measured code that collected the evidence. |
| A composite verifier token | Intel Trust Authority (TDX plus up to 8 GPUs, one JWT); IETF draft-kykdxy-rats-tdx-cgpu-ear-profile-02 | The verifier asserts it; the draft does not specify the cryptographic binding |

The plan for verifiable.pro uses the first two together. The measured code verifies the GPU at boot against an explicit policy (CC mode on, not DevTools, `measres=success`, OCSP good) and publishes the policy's digest. Each session also gets a fresh token from NVIDIA's Remote Attestation Service (NRAS) whose nonce is derived from the session nonce, together with the signing key's certificate chain, so readers can check NVIDIA's signature themselves. The interface must still say plainly that GPU evidence alone does not prove which CVM the GPU is attached to.

NRAS returns what NVIDIA calls a detached EAT: an overall JWT plus one JWT per GPU, signed ES384. **[observed]** Its JWKS held about 200 P-384 keys with `kid`s timestamped within the last three days. Each key's `x5c` chain runs from a leaf valid for about 12 hours ("NVIDIA Attestation Service GPU GH100") through "GPU Intermediate 004" to "NVIDIA Attestation Service CA 001". The client must therefore pin the CA and verify the chain at the token's `iat`; pinning JWKS keys would break within hours. NVIDIA's documentation names the overall claim both `x-nvidia-overall-att-result` and `x-nvidia-overall-result`, so the client accepts either and is tested against real tokens.

### What a reader must still trust

| | Self-hosted CVM (phase 2) | Managed provider (phase 1) | Mock (phase 0) |
| --- | --- | --- | --- |
| Trusted | Intel or AMD silicon, root keys and TCB policy; NVIDIA GPU firmware, and NRAS with its RIM and OCSP services; the datacenter's physical security; Google or Intel Trust Authority as token issuer; GitHub Actions and Sigstore for provenance; **the page JavaScript served from the site's repository** | The same hardware vendors and physical security; the provider's published code, release pipeline and verifier SDK; the page JavaScript | Everything. Nothing is protected, and the interface says so. |
| Not trusted for confidentiality | Mengyuan as operator, the network, cloud administrators | The proxy, when the provider's encryption ends inside the model enclave (Tinfoil EHBP, Privatemode's browser SDK) | n/a |
| "Which model and code" means | The project's own image, model and system-prompt digests, in its release record | The provider's release (Tinfoil pins weights; others vary) plus the project's public system-prompt digest | Nothing |

The verifier code is itself served by the site, and Mengyuan is both operator and author of that verifier. Tinfoil states there is currently no viable defence against a persistent attacker on the server that serves the page. The Freedom of the Press Foundation's WEBCAT extension (v3.0.0, alpha) is the emerging fix. Until then the widget shows the page script's SHA-256 from `/manifest.json`, lets readers export the evidence, and phase 3 adds a command-line verifier that does not depend on the page.

### Known attacks the interface must acknowledge

- **TEE.fail** (Georgia Tech, Purdue and Synkhronix, October 2025). A DDR5 bus interposer costing under $1,000 extracted attestation keys from up-to-date platforms and forged TDX quotes. The authors also passed NVIDIA CC attestation while running outside a TEE. Phala's dstack is named as affected. The attack needs physical access and root; Intel and AMD treat physical attacks as out of scope.
- **DDRop** (disclosed September 2026; ACM CCS 2026). An interposer with about $159 in parts drops DDR5 writes so that stale ciphertext is read back undetected, against TDX, Scalable SGX and SEV-SNP. It forced debug mode and forged attestation on up-to-date TDX. The site's article `ddrop-ddr5-interposer-attack` covers it.
- **Trail of Bits' audit of WhatsApp Private Inference** (blog post 7 April 2026). Of 28 issues, 8 were high severity. Each relevant finding maps to a requirement here: configuration loaded after measurement, no attestation freshness, the SNP TCB not checked against the VCEK, GPU models that did not verify NVIDIA attestation, and a non-reproducible VM image.

## What the browser can and cannot verify

| Check | In the browser? | How |
| --- | --- | --- |
| Google Confidential Space token (RS256) with its `x5c` chain | Yes | WebCrypto plus an X.509 library such as `@peculiar/x509` or pkijs [library choice: suggestion]. The root must be pinned, because Google's PKI root URL sends no CORS header [observed]. |
| TDX quote v4, TCB status and debug bit | Yes | `@phala/dcap-qvl`, pure JavaScript (0.7.0; at least 0.3.9 because of CVE-2026-22696). Intel's collateral is relayed by the API and checked against the pinned Intel root; Intel PCS sends no CORS header [observed]. |
| SEV-SNP report, VCEK chain, TCB against VCEK | Yes | Tinfoil's JS verifier code path. AMD KDS allows any origin [observed], but the API relays it to keep reader IPs from AMD and avoid KDS rate limits. |
| NVIDIA NRAS token: signature, claims, nonce | Yes | ES384 with WebCrypto; chain verified to the pinned NVIDIA CA. A missing or invalid chain is reported as `unverifiable`, never as passed or failed. |
| Raw GPU evidence (SPDM measurements, device certificates, RIM signatures, OCSP) | Not practical: no maintained JS library is known [unverified] | The measured boot check plus the NRAS token. The raw evidence is offered for download and can be checked with `nvattest attest --gpu-evidence-file`. |
| Sigstore bundle of the backend release | Yes | `@freedomofpress/sigstore-browser` (MIT), also used inside Tinfoil's SDK |
| TLS certificate bound to the attestation | No, except through a WASM TLS client | Shown as "checkable with the CLI" |
| HPKE encryption and Ed25519 receipts | Yes | `@hpke/core` (MIT) or the `ehbp` package (MIT); WebCrypto Ed25519 or `@noble/ed25519` [native support versions from memory] |
| Citation integrity | Yes | SHA-256 of the fetched `.md` compared with `manifest.json`, then the passage re-sliced at its offsets |

The badge follows from this table. It is computed only from checks that ran in the browser. Claims the backend reports about itself, such as "GPU policy passed at boot", appear separately as reported by the measured code, and they carry weight only because the image check passed. Overall states are `demo`, `reported`, `partly_verified`, `verified` and `failed`; phase 0 can only produce `demo` and `reported`. No state is drawn as a green check mark, and any skipped check makes the headline read "Partly verified". A permanent panel lists what the reader still trusts, and an export button saves the bundle, the plaintext request, the transcript and the receipt for re-verification with other tools.

## Phases

### Phase 0: contract, mock and widget (now)

The contract, schema and fixtures are in `api/`. The mock in `backend/mock/` speaks the contract with `mode: "mock"` and `encryption: "none"`, answers by quoting the passages it receives, and can forward to a local OpenAI-compatible model. Its attestation bundle contains no evidence and says so (`tee.cpu: "none"`, `cc_mode: "off"`, `verified_by: []`). The widget's demo transport answers entirely in the browser from the site's files.

### Phase 1: managed attested provider behind a ciphertext-only proxy (2 to 3 weeks)

Only providers whose end-to-end encryption terminates inside an attested model enclave keep "the operator cannot read your question" true.

| Provider | What the client can verify | Browser support | Notes |
| --- | --- | --- | --- |
| **Tinfoil** (first choice) | The CPU enclave's SEV-SNP or TDX report (GPU verified at boot), compared with the release's Sigstore bundle. `tinfoil-config.yml` pins the model commitment, container images and CVM version; weights are dm-verity volumes. The enclave's TLS fingerprint and HPKE key are in the report's user data. | Native JS/TS verifier of just under 50 KB in the `tinfoil` npm package (Apache-2.0, v1.2.2), built on `sigstore-browser` and `tuf-browser`. EHBP has an official proxy pattern. | Per-token prices are not public [unverified]. The proxy must pin or allowlist the enclave origin and never trust a client-supplied `X-Tinfoil-Enclave-Url`. |
| **Privatemode** (alternative) | The Coordinator's evidence against AMD and Intel roots and a published, reproducible manifest; workers verify GPUs | `privatemode-ai` (MIT) runs in browsers with a bundled Wasm verifier | gpt-oss-120b €0.20/€0.65 per million tokens. Never use its proxyless API, which has no client-side attestation. |
| Phala / RedPill | A TDX quote with nonce and keyset binding | No browser library documented | Its encryption ends at an attested gateway, which sees plaintext: "encrypted to an attested gateway; the model hop is not end to end". Current prices [unverified]. |
| NEAR AI Cloud | Gateway and model attestations; signed responses | API key in the examples (mandatory? [unverified]), so a proxy relay is needed; TLS binding not checkable in a browser | "Attested model, not end-to-end private" |
| OPAQUE | n/a | n/a | On 13 October 2026 Anthropic licensed OPAQUE's technology and hired part of the team; do not build on it. |

The proxy (`backend/proxy/`, a Cloudflare Worker or small VM) serves `/v1/meta`, relays the provider's attestation bundle with a `summary` and `release` added, forwards EHBP ciphertext and headers unchanged to an allowlisted enclave origin with the API key added, and rate-limits. It sees IP addresses, timing, sizes and token counts, not plaintext. Before launch the site needs a `/privacy/` page and an updated About page; the label reads "Beta · answers run in Tinfoil's attested enclave; verifiable.pro cannot read them". Token cost for 3,000 chats a month is about €4 on Privatemode [estimate]; Tinfoil's is unknown.

### Phase 2: self-hosted pilot (1 to 2 months)

A new repository, `verifiable-pro-chat`, holds a measured gateway (Rust or Go), a container image pinned by digest, and a release workflow that builds the image, signs build provenance with `actions/attest@v4`, and publishes `release.json` with the image digest, model file list and digest, engine version, system-prompt digest and GPU policy digest. The gateway checks the GPU at boot, generates the HPKE and receipt keys in memory, verifies every model file against a hash list compiled into the image, binds the keyset and nonce into the evidence, rejects requests that are not EHBP-encrypted, and signs a receipt per answer.

Model: **Qwen3.5-9B** (Apache-2.0, about 18 to 20 GB in BF16, leaving 50 to 55 GB of an H100's 80 GB for the KV cache; bilingual), served by a pinned stable vLLM release. Qwen3-8B is the fallback. Its Chinese quality and the first stable vLLM release that supports it are [unverified].

| Host | CPU TEE + GPU | Caveats | Price |
| --- | --- | --- | --- |
| **GCP `a3-highgpu-1g` with Confidential Space** (pilot) | Intel TDX + 1×H100 | Confidential Space on H100 GA 29 April 2026; Intel Trust Authority tokens for H100 GA 15 September 2026. Only zones europe-west4-c, us-central1-a and us-east5-a; no reservations, no live migration. Google says `cc_mode` attests the GPU driver only, not the whole device, so the design adds its own NRAS evidence. Raw TDX quote access is [unverified]; the documentation describes only tokens, so readers trust Google or Intel Trust Authority as the CPU verifier. | About $11.06/h base plus about $0.98/h CC surcharge per H100 and vCPU/RAM surcharges: about $12/h or more [estimate]; about $8.8k a month 24/7 |
| **Phala Cloud dstack** (cheaper 24/7) | TDX + H200 | Open source; compose hash lands in `mr_config_id` and RTMR3, so `@phala/dcap-qvl` covers the CPU side in the browser. Adds dstack's KMS to the trusted set; named as affected by TEE.fail. The 24-hour prepaid minimum rules out scheduled hours. | H200 $5.50/h (US only), $4.40/h on a 180-day term; about $4.0k a month 24/7 |
| Azure `Standard_NCC40ads_H100_v5` | SEV-SNP + 1×H100 | Ubuntu 22.04 only; the measurement covers Microsoft's paravisor, harder for outsiders to reproduce; the vTPM-based freshness path is not confirmed by Microsoft | $6.98/h on demand in East US 2; about $5.1k a month 24/7 |
| Corvex (B200), Verda (RTX PRO 6000) | TDX / SEV-SNP | Not researched [unverified] | |
| GCP `g4-standard-48` (rejected) | AMD SEV, not SNP | No integrity protection and no SNP-style report | |

Scheduled hours or on-demand start keep costs down (GCP and Azure only), at the price of a cold start of several minutes for VM boot, driver install, GPU attestation and model loading [estimate]. When the self-hosted backend is off or GCP has no capacity, the widget falls back to the phase-1 provider and shows which backend answered.

**Confidential-computing overhead.** An arXiv study (2409.03992) measured under 7% for most typical LLM queries on Hopper with vLLM, mostly from PCIe transfers. Tinfoil's measurements on 8×H200 and 8×B300 (June 2026) show much larger overhead for a single short request on a CC-naive vLLM (+118% inter-token latency for Kimi K2.6 at TP=8 on B300) and about 14% (Hopper) to 25–30% (Blackwell) when saturated; a single H200 running Llama-3.1-8B showed about 8% throughput overhead. Its advice is to keep CUDA graphs on, avoid pinned host memory and profile speculative decoding before enabling it. A low-traffic site chatbot runs at concurrency 1, so the plan budgets up to about twice the inter-token latency for a single-GPU 9B model and measures it [estimate].

### Phase 3: independence and hardening (ongoing)

- A `vp-verify` command-line verifier (Go or Rust) that re-verifies an exported bundle and adds the TLS-binding checks a browser cannot do.
- Reproducibility documentation, so anyone can rebuild the image and get the same digest.
- Rekor entries per release, and later an optional transparency log of keysets.
- Third-party review, WEBCAT enrolment once it is stable, and an optional OHTTP relay to hide reader IP addresses.
- A published TCB policy and its update procedure (TCB recovery, monthly Confidential Space images, NRAS outages, NVIDIA CA rotation).

## The protocol in brief

The full contract is in [`api/chat-v1.md`](../api/chat-v1.md). A session runs like this:

1. When the reader opens the chat, the widget loads its script, the site's search data and the static `trust.json` from the site itself. Readers who never open it make no extra requests.
2. The browser draws a 32-byte nonce and calls `GET /v1/attestation?nonce=…`. The enclave builds a keyset (HPKE key, receipt key, release), computes `keyset_digest = sha256("vp-keyset/v1\n" ‖ JCS(keyset))`, and binds `keyset_digest ‖ nonce` into the CPU evidence; the GPU evidence uses `sha256(nonce ‖ keyset_digest)` as its nonce.
3. The browser verifies the bundle and renders the badge from its own checks.
4. The browser selects passages, encrypts the request to the attested HPKE key, and calls `POST /v1/chat` with `VP-Attestation-Id` and `VP-Keyset-Digest`.
5. The answer streams back as server-sent events (`meta`, `citations`, `delta`…, `done`), encrypted chunk by chunk. `done` carries a receipt signed with the attested receipt key.
6. Optionally, the browser fetches each cited source, checks its SHA-256 against `manifest.json` and re-slices the passage.

**Freshness and cost.** Bundles expire after about 10 minutes, and keys are generated per boot, so a restart forces re-attestation. Fresh quotes and NRAS calls are rate-limited; NRAS results may be cached for about 60 seconds across sessions, in which case readers see `gpu_nonce_bound: false`. The relayed NRAS signing key and its chain go into the bundle so an export can be re-verified after the 12-hour leaf certificate expires.

**Encryption and streaming.** The design uses EHBP framing as Tinfoil specifies it (HPKE base mode with X25519, HKDF-SHA256 and AES-256-GCM, length-prefixed chunks, `Ehbp-Encapsulated-Key` and `Ehbp-Response-Nonce` headers), so phase 1 and phase 2 share one format and existing reference code. EHBP passes a request without `Ehbp-Encapsulated-Key` through as plaintext, so the client must always encrypt and the production gateway must refuse plaintext. The widget reads the stream with `fetch()` and a `ReadableStream`, not `EventSource`, which cannot POST, set headers or decrypt. A `: ping` comment every 15 seconds keeps the connection alive; under EHBP it sits inside the encryption, so a separate transport keep-alive may be needed [unverified].

**Hosting.** The site stays on GitHub Pages, which cannot set headers, so a `<meta http-equiv="Content-Security-Policy">` with at least `connect-src 'self' https://api.verifiable.pro` is needed [from memory: meta CSP supports `connect-src` but not `frame-ancestors`]. In phase 2 the API sits behind an L4 passthrough load balancer; a TLS-terminating CDN would be acceptable for confidentiality because bodies are encrypted, but it would break the CLI's TLS binding.

**Abuse control without reading text.** Limits are 10 requests per 10 minutes and 40 per day per client key, a global daily cap, questions of at most 1,200 characters, at most 6 turns and 8 passages, and at most 700 output tokens. The client key is an HMAC of the IPv4 /24 or IPv6 /56 under a daily rotating secret, held in memory, inside the CVM from phase 2. Above the thresholds a hashcash-style proof-of-work challenge applies; Cloudflare Turnstile would add a third party that sees reader IPs. Content safety has to run inside the TEE, because nothing outside can read the text: a strict public system prompt, output caps, and optionally a small guard model.

**Citations.** The browser numbers the passages it sends, the system prompt requires `[n]` markers, and the server echoes the passages in a `citations` event before generating. Each citation shows title, anchor link, language, the first 12 hex characters of `source_sha256` and the manifest digest, which matches the `digest` of `/manifest.json`. If the site was rebuilt since the passages were loaded, the check reads "source changed since this answer".

## Privacy implications

A `/privacy/` page in English and Chinese is needed **before phase 1**, and the About page's AI-use statement should be updated. The page must cover:

1. **What is sent.** The question, the selected public article excerpts and earlier turns in the session. From phase 1 they are encrypted in the browser to an enclave key, and the operator and proxy see only ciphertext. In mock mode nothing is protected.
2. **Who processes it.** The provider (phase 1) or the cloud (phase 2). NVIDIA NRAS, Intel PCS, AMD KDS and Google or Intel Trust Authority are contacted by the server and receive hardware evidence, not the question. GitHub sees the reader's request if the browser fetches Sigstore bundles from GitHub, so they should be served from the API or the static site instead.
3. **Metadata visible to the operator or proxy.** IP address in transit, timing, message sizes and token counts.
4. **Retention.** No conversation storage on the server. Browser storage holds nothing unless the reader opts in to keeping the chat on the device.
5. **Scope of the confidentiality claim.** It holds only if attestation passes and the hardware and measured code are sound. Physical attacks on the datacenter (TEE.fail, DDRop), side channels and compromise of the page's JavaScript are out of scope.
6. **Accuracy.** The model may be wrong; citations point to the site's articles.
7. **Controller role.** Under GDPR the operator is likely still a controller even when processing only ciphertext, so the page names a contact (`hello@verifiable.pro`) [unverified legal analysis].

The phase-0 mock is consistent with this: its log holds only time, endpoint, status and latency, its rate limiter keeps only HMAC keys in memory, and it stores nothing.

## Open questions

1. TDISP/IDE for B200 in any rentable cloud: [unverified]; assume bounce buffers.
2. Whether NRAS works without a service key, and at what rate limits. The "no valid service keys" note is in the deprecated Python SDK and concerns the optional key; confirm in the pilot.
3. Where NVIDIA publishes the "NVIDIA Attestation Service CA 001" root and how it rotates; whether the EAT header carries `x5c` or only `kid`; which overall-result claim name real tokens use.
4. Confidential Space: raw TDX quote access [unverified]; conflicting `eat_nonce` length limits in Google's documentation (8–88 vs 10–74 bytes; a 64-character hex string fits both); which image versions to pin and how often they change.
5. The Azure NCC H100 v5 attestation path and custom `report_data` through a vTPM quote: consistent with secondary documentation, not confirmed by Microsoft.
6. Provider details: Tinfoil per-token prices; weights-digest pinning at NEAR and Phala; whether NEAR's attestation endpoint requires an API key; current Phala prices.
7. Model quality: Chinese quality of Qwen3.5-9B and gpt-oss-20b; the first stable vLLM release for Qwen3.5; an FP8 checkpoint for Qwen3.5-35B-A3B.
8. Prices and latency figures are snapshots or [estimate]; Phala's own pages disagree with each other.
9. CORS [observed 2026-10-20]: NRAS JWKS and AMD KDS allow any origin; Intel PCS and Google's PKI root send no CORS header. Signed collateral is relayed through the API regardless, for reader IP privacy and rate limits.
10. Legal review of the privacy page.
11. The EHBP key-configuration error (422) must be handled like `412 attestation_mismatch`; the contract's `message/ehbp` content type is a project convention, not part of the EHBP specification.

## Sources (accessed 2026-10-20)

**NVIDIA**
- *Secure AI with Blackwell and Hopper GPUs* whitepaper v1.3, Aug 2025: https://docs.nvidia.com/nvidia-secure-ai-with-blackwell-and-hopper-gpus-whitepaper.pdf
- Attestation architecture (updated 6 Oct 2026): https://docs.nvidia.com/attestation/quick-start-guide/latest/architecture.html
- Hopper single-GPU example: https://docs.nvidia.com/attestation/quick-start-guide/latest/attestation-examples/hopper_single_gpu.html
- NRAS "Most Secure": https://docs.nvidia.com/attestation/poc-to-production/latest/integration-options/remote_verifier.html
- Python SDK APIs (deprecated): https://docs.nvidia.com/attestation/attestation-client-tools-sdk/latest/sdk_apis_and_configuration.html
- C SDK attest API: https://docs.nvidia.com/attestation/nv-attestation-sdk-c/api/group__attest.html
- GPU claims guide: https://docs.nvidia.com/attestation/advanced-documentation/latest/claims-guide/gpu_claims.html
- nvattest command reference: https://docs.nvidia.com/attestation/nv-attestation-sdk-cpp/1.2.0/sdk-cli/command-reference.html
- Rust bindings: https://docs.nvidia.com/attestation/nv-attestation-sdk-cpp/1.2.0/sdk-rust/index.html
- NRAS JWKS: https://nras.attestation.nvidia.com/.well-known/jwks.json (observed)
- Confidential Containers supported platforms: https://docs.nvidia.com/datacenter/cloud-native/confidential-containers/latest/supported-platforms.html
- R580 TRD1 release notes: https://docs.nvidia.com/580trd1-trusted-computing-solutions-release-notes.pdf

**Intel Trust Authority and IETF**
- ITA GPU attestation (16 Jun 2026): https://docs.trustauthority.intel.com/main/articles/concept-gpu-attestation.html
- draft-kykdxy-rats-tdx-cgpu-ear-profile-02: https://datatracker.ietf.org/doc/draft-kykdxy-rats-tdx-cgpu-ear-profile/
- draft-fossati-seat-expat-04: https://datatracker.ietf.org/doc/draft-fossati-seat-expat/
- draft-reddy-seat-expat-transport-02: https://datatracker.ietf.org/doc/draft-reddy-seat-expat-transport/

**Azure**
- Confidential GPU options: https://learn.microsoft.com/en-us/azure/confidential-computing/gpu-options
- Price snapshot: https://sparecores.com/server/azure/Standard_NCC40ads_H100_v5
- vTPM/HCL binding: https://docs.rs/az-snp-vtpm

**Google Cloud**
- Confidential VM release notes: https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/release-notes
- Supported configurations: https://docs.cloud.google.com/confidential-computing/confidential-vm/docs/supported-configurations
- Confidential VM pricing: https://cloud.google.com/confidential-computing/confidential-vm/pricing
- Confidential Space release notes: https://docs.cloud.google.com/confidential-computing/confidential-space/docs/release-notes
- Token claims (updated 13 Oct 2026): https://docs.cloud.google.com/confidential-computing/confidential-space/docs/reference/token-claims
- External resources, nonces, launcher, PKI: https://docs.cloud.google.com/confidential-computing/confidential-space/docs/connect-external-resources
- a3-highgpu-1g price snapshot: https://gcloud-compute.com/a3-highgpu-1g.html

**Tinfoil**
- Attestation architecture: https://docs.tinfoil.sh/verification/attestation-architecture
- Predicate formats: https://docs.tinfoil.sh/verification/predicate
- Browser-native verification: https://tinfoil.sh/blog/2025-12-18-browser-native-verification
- EHBP spec: https://raw.githubusercontent.com/tinfoilsh/encrypted-http-body-protocol/HEAD/SPEC.md
- Proxy-server guide: https://docs.tinfoil.sh/guides/proxy-server
- CC overhead: https://tinfoil.sh/blog/2026-06-23-confidential-computing-overhead
- Pricing: https://tinfoil.sh/pricing
- Go verifier: https://pkg.go.dev/github.com/tinfoilsh/verifier
- npm package: https://cdn.jsdelivr.net/npm/tinfoil@latest/package.json

**Privatemode**
- Docs home: https://docs.privatemode.ai/
- JS SDK: https://docs.privatemode.ai/reference/sdk/
- Proxyless API: https://docs.privatemode.ai/api/proxyless-api/
- Attestation: https://docs.privatemode.ai/security/attestation/overview/
- Pricing: https://docs.privatemode.ai/pricing/

**Phala / RedPill**
- Verify attestation: https://docs.phala.com/phala-cloud/confidential-ai/verify/verify-attestation
- E2EE: https://docs.phala.com/phala-cloud/confidential-ai/confidential-model/e2ee-encryption.md
- GPU TEE pricing: https://cloud.phala.com/about/pricing
- Models: https://phala.com/confidential-ai-models
- CVE-2026-22696: https://osv.dev/vulnerability/CVE-2026-22696

**NEAR AI Cloud**
- Quote, nonce and signer binding: https://docs.near.ai/cloud/verification/reference/quote-nonce-signer
- Response signatures: https://docs.near.ai/cloud/verification/cloud-api/response-signatures
- Gateway attestation: https://docs.near.ai/cloud/verification/cloud-api/gateway-attestation

**Other providers and industry news**
- Corvex (3 Mar 2026): https://www.barchart.com/story/news/544507/corvex-among-the-first-companies-to-achieve-verified-production-deployment-of-confidential-computing-for-ai-on-nvidia-hgx-b200-systems
- Verda: https://docs.verda.com/cpu-and-gpu-instances/confidential-compute/
- OPAQUE / Anthropic: https://constellationr.com/insights/news/anthropic-licenses-releases-opaque-acquihire
- Fortanix Confidential AI (GTC 2026): https://www.businesswire.com/news/home/20260304380475/en/Fortanix-Showcases-Confidential-AI-Innovation-at-NVIDIA-GTC-2026

**Patterns and tooling**
- Apple Private Cloud Compute (10 Jun 2024): https://security.apple.com/blog/private-cloud-compute/
- GitHub artifact attestations: https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations
- FPF WEBCAT: https://addons.mozilla.org/en-US/firefox/addon/webcat/
- Atlas: https://www.mintlify.com/concrete-security/atlas/platforms/browser-wasm

**Attacks, audits and performance**
- arXiv 2409.03992: https://arxiv.org/abs/2409.03992
- Trail of Bits, WhatsApp Private Inference audit (7 Apr 2026): https://blog.trailofbits.com/2026/04/07/what-we-learned-about-tee-security-from-auditing-whatsapps-private-inference/ and https://trailofbits.com/library/meta-whatsapp-private-processing/
- TEE.fail coverage: https://www.bleepingcomputer.com/news/security/teefail-attack-breaks-confidential-computing-on-intel-amd-nvidia-cpus/
- DDRop: https://research.google/pubs/ddrop-generic-memory-interposer-attacks-on-confidential-vms-by-dropping-ddr5-writes/ and https://thehackernews.com/2026/09/new-ddrop-attack-breaks-intel-tdx-and.html

**Models**
- https://huggingface.co/Qwen/Qwen3.5-9B
- https://docs.vllm.ai/projects/recipes/en/stable/Qwen/Qwen3.5.html
- https://huggingface.co/openai/gpt-oss-20b
- https://docs.vllm.ai/projects/recipes/en/stable/OpenAI/GPT-OSS.html
