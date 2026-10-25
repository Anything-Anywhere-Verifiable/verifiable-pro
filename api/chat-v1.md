# verifiable.pro chat API, version 1

This document is the contract between the site's chat widget ("Ask / 提问") and any backend that answers it. The widget, the phase-0 mock in `backend/mock/` and every later backend implement the same three endpoints, so moving from the mock to an attested provider or a self-hosted confidential VM changes the adapter and the trust anchors, not the protocol. The JSON Schema for every payload is [`chat-v1.schema.json`](chat-v1.schema.json); example payloads are in [`fixtures/`](fixtures/). The architecture behind the contract is described in [`docs/assistant-architecture.md`](../docs/assistant-architecture.md).

## Phases and what is implemented now

Each part of the contract carries a phase marker. Only **P0** exists today.

| Marker | Phase | Backend | Encryption | What the browser can check |
| --- | --- | --- | --- | --- |
| **P0** | 0, now | `backend/mock/server.py`, or the in-browser demo transport | `none` | Nothing about the backend. Citations can be hashed against `/manifest.json`. |
| P1 | 1 | Managed attested provider (Tinfoil first, Privatemode as the alternative) behind a proxy that forwards only ciphertext | `ehbp-v1` | The provider's enclave evidence and release, through the provider's browser verifier |
| P2 | 2 | Self-hosted confidential VM with an NVIDIA H100 in CC mode | `ehbp-v1` | CPU evidence, binding, release, NVIDIA's GPU token, signed receipt |
| P3 | 3 | As P2, plus an independent command-line verifier | `ehbp-v1` | As P2; TLS binding through the CLI |

Fields marked P1 or later are part of the format now so that clients can be written against it, but a P0 backend sends `null` or an empty array for them.

## The rule the contract is built around

Retrieval happens in the browser. The widget picks the relevant passages from the site's own published files (`search-index.json`, `manifest.json` and the published `.md` sources) and sends them with the question as `context.chunks`. The backend is an attested language model and nothing more: it holds no index, stores nothing, and answers only from the passages it receives. Two consequences follow. Citations can be checked entirely in the browser, because every passage names its source file and that file's SHA-256 from the manifest. And from phase 1 on, every hop between the browser and the enclave can be limited to ciphertext, because nothing outside the enclave needs to read the question.

The widget computes the badge from checks that ran in the browser. Anything the server says about itself is displayed as *reported*.

## Conventions

- JSON is UTF-8. Hashes and nonces are lowercase hex. `b64u` is base64url without padding. Timestamps are RFC 3339 in UTC with second precision (`2026-10-20T14:02:11Z`).
- `api_version` is the string `"1"`.
- Clients and servers ignore fields they do not know. Fields marked *extension* below were added by this document and are not in the design report's draft.
- Every API response carries `Cache-Control: no-store` and a `VP-Request-Id` header.
- `{api}` is the base URL from the site configuration (`chat.api_base` in `content/site.json`), for example `http://127.0.0.1:8787` for the mock.

## Endpoints

| Method and path | Phase | Purpose |
| --- | --- | --- |
| `GET {api}/v1/meta` | P0 | Backend mode, encryption, models and published limits |
| `GET {api}/v1/attestation?nonce=<64 hex>` | P0 | Attestation bundle bound to the browser's nonce |
| `POST {api}/v1/chat` | P0 | Question plus passages in, `text/event-stream` answer out |
| `GET {api}/healthz` | P0 | `{"status":"ok"}`, readable from any origin |
| `GET {api}/v1/attestation/{id}/evidence[/gpu\|/cpu]` | P2 | Raw evidence for offline tools, kept for the attestation's lifetime plus one hour. Not served in P0 (404). |

## `GET /v1/meta`

```json
{
  "api_version": "1",
  "mode": "mock",
  "backend": { "id": "mock-local", "label": "Demo backend (no TEE)" },
  "encryption": "none",
  "attestation_required": false,
  "models": [{ "id": "mock-extractive", "display": "Extractive mock (no model)", "langs": ["en", "zh"] }],
  "limits": { "max_question_chars": 1200, "max_turns": 6, "max_context_chunks": 8,
              "max_input_tokens": 6000, "max_output_tokens": 700, "requests_per_10min": 10,
              "max_body_bytes": 262144 },
  "privacy_url": null,
  "status": "ok",
  "system_prompt_sha256": null,
  "notice": "MOCK BACKEND. Nothing here is attested: ..."
}
```

| Field | Values | Notes |
| --- | --- | --- |
| `mode` | `mock` (P0), `managed` (P1), `self_hosted` (P2) | The widget shows the demo status for `mock` whatever else the backend sends. |
| `backend.id`, `backend.label` | e.g. `mock-local`, `tinfoil`, `vp-gcp-cs-1` | Shown in each answer's header, so readers can see which backend answered. |
| `encryption` | `none` (P0), `ehbp-v1` (P1+) | With `ehbp-v1` the client must encrypt; see the chat section. |
| `attestation_required` | `false` only in mock mode | When `true`, chat requests without valid attestation headers are refused. |
| `limits` | integers | The client enforces these before sending. `max_turns` counts user messages; `messages` may hold at most `2 × max_turns` entries. `max_body_bytes` is an extension. |
| `privacy_url` | URL or `null` | `null` until the `/privacy/` page exists, which must happen before phase 1. |
| `status` | `ok`, `degraded`, `offline` | |
| `system_prompt_sha256` | hex or `null` | *Extension.* SHA-256 of the public system prompt's UTF-8 bytes; `null` when no prompt is used (the extractive mock). |
| `notice` | string | *Extension.* Human-readable warning. |

## `GET /v1/attestation?nonce=<64 hex>`

The browser draws 32 random bytes with `crypto.getRandomValues`, sends them as 64 lowercase hex characters, and keeps the nonce for the session. Any other nonce format gets `400 bad_request`. The response is an `AttestationBundle`; the full P2 shape is in `fixtures/attestation.selfhosted.example.json`.

| Field | Phase | Mock value | Meaning |
| --- | --- | --- | --- |
| `schema` | P0 | `verifiable.pro/attestation/v1` | |
| `attestation_id` | P0 | `att_mock_<16 hex>` | Opaque. Sent back as `VP-Attestation-Id`. |
| `mode` | P0 | `mock` | |
| `nonce` | P0 | echoed | |
| `issued_at`, `expires_at` | P0 | 10 minutes apart | The client re-attests after `expires_at` or on `409 attestation_expired`. |
| `keyset` | P0 shape, P1+ content | every slot `null` except `epoch` | `{epoch, hpke, receipt, tls_spki_sha256, release}`. `hpke` is the HPKE public key requests are encrypted to (`null` when `encryption` is `none`); `receipt` is the Ed25519 key that signs receipts. Keys are generated per boot, and `epoch` is the boot time. |
| `keyset_digest` | P0 | computed | `hex(sha256("vp-keyset/v1\n" ‖ JCS(keyset)))`, where JCS is RFC 8785 canonical JSON. This digest is what the hardware report binds. |
| `binding` | P2 | `{"method":"none", ..., "gpu_nonce":null}` | How the keyset and nonce are bound into the hardware evidence. Methods: `tdx-report-data-split-v1` and `snp-report-data-split-v1` (`report_data[0:32] = keyset_digest`, `report_data[32:64] = nonce`), `gcp-cs-eat-nonce-v1` (Confidential Space token `eat_nonce = [nonce, keyset_digest]`), `provider` (P1, the provider's own scheme), `none`. `gpu_nonce = hex(sha256(nonce_bytes ‖ keyset_digest_bytes))` is the nonce given to NVIDIA's evidence collection. |
| `evidence` | P1+ | `[]` | Raw evidence: `tdx_quote`, `snp_report`, `gcp_cs_token`, `nvidia_eat` (with `cached: true` when a cached NVIDIA token is served), `nvidia_evidence` (a URL), `provider_bundle`. |
| `collateral` | P1+ | `[]` | Vendor-signed material the browser needs and cannot fetch itself (Intel PCS TCB info and CRLs, AMD VCEK, the NVIDIA token-signing key with its `x5c` chain). Safe to relay because Intel, AMD or NVIDIA signed it. Trust roots are never taken from here; they are pinned in the site's static `trust.json`. |
| `release` | P2 | `null` | What the measurement should equal: `release_json_url`, an inline `sigstore_bundle`, and `expected` digests for the image, model, system prompt and GPU policy. |
| `server_checks` | P2 | `[]` | Checks the backend's measured code reports about itself, such as the GPU policy check at boot. Displayed as *reported*; they never set the badge on their own. |
| `summary` | P0 | see below | Display object. |
| `report_url` | P2 | `null` | Full evidence download. |
| `notice` | P0 | warning text | *Extension.* |
| `example` | | absent | *Extension.* `true` only in documentation fixtures. A running backend never sends it. |

### `summary` (server claims)

The summary is what the server says about itself. The client overwrites each claim it can check with its own result and labels the rest *reported*.

| Field | Mock value | P2 example |
| --- | --- | --- |
| `tee` | `{"cpu":"none","label":"None (mock backend; nothing is attested)","platform":"mock","tcb_status":null,"debug":null}` | `{"cpu":"intel-tdx","platform":"gcp-confidential-space","tcb_status":"UpToDate","debug":false}` |
| `gpu` | `null` | `{"vendor":"nvidia","model":"H100 80GB HBM3","arch":"hopper","count":1,...}` |
| `cc_mode` | `off` | `on`. Other values: `devtools` (must be rejected in production), `ppcie`, `unknown`. |
| `model` | `{"id":"mock-extractive",...}` or the passthrough model | `{"id":"Qwen/Qwen3.5-9B","revision":...,"license":"apache-2.0","engine":"vllm@<version>"}` |
| `model_digest`, `image_digest`, `measurement`, `code` | `null` | digests, TDX/SNP/Confidential Space measurement, release repo/tag/commit |
| `system_prompt_sha256` | `null`, or the passthrough prompt's digest | the release's prompt digest |
| `corpus` | `null` | `{"manifest_digest":"…","manifest_url":"https://verifiable.pro/manifest.json"}` |
| `verified_by` | `[]` | parties whose signatures stand behind the claims, e.g. `google-cloud-attestation` (cpu), `nvidia-nras` (gpu) |
| `verified_at`, `report_url` | `null` | |
| `nonce` | echoed | |
| `claims` | `{"operator_can_read_plaintext":true,"basis":"Mock backend: ..."}` | `false`, with the basis "request bodies are HPKE-encrypted to `keyset.hpke.public_key`, bound to the attested VM via `binding.method`" |

A mock bundle must satisfy `#/$defs/MockAttestationBundle` in the schema: `mode` `mock`, no evidence or collateral, `binding.method` `none`, `summary.tee.cpu` `none`, `summary.cc_mode` `off`, `summary.verified_by` empty and `operator_can_read_plaintext` `true`. Nothing in a mock response may suggest that anything was attested.

## `POST /v1/chat`

### Request headers

| Header | Phase | Notes |
| --- | --- | --- |
| `Content-Type: application/json` | P0 | Plaintext body. Required when `encryption` is `none`. |
| `Content-Type: message/ehbp` and `Ehbp-Encapsulated-Key` | P1+ | Encrypted body. `message/ehbp` is this project's convention; the EHBP specification defines no content type. A P0 backend answers either with `400 bad_request`. |
| `VP-Attestation-Id`, `VP-Keyset-Digest` | P0 optional, P1+ required | From the bundle the client verified. The mock checks them when present: an unknown id or a different keyset digest gives `412 attestation_mismatch`, an expired id gives `409 attestation_expired`, and a body `nonce` different from the attested one gives `412`. |
| `VP-Challenge` | P2 | Proof-of-work answer when the backend escalates abuse control. |

The widget sends requests with `credentials: "omit"` and `cache: "no-store"`, and reads the response with `fetch()` and a `ReadableStream`. `EventSource` cannot send a POST body or custom headers, and in phase 1 it could not decrypt the stream.

### Request body

The body below is plaintext in phase 0. From phase 1 the same bytes are encrypted as a whole.

```json
{
  "api_version": "1",
  "lang": "en",
  "nonce": "<the 64 hex sent to /v1/attestation>",
  "page": { "path": "/articles/remote-attestation-for-ai-workloads-explained/", "source_sha256": "<hex>" },
  "messages": [{ "role": "user", "content": "What does a valid remote attestation report prove?" }],
  "context": {
    "manifest_digest": "<the manifest digest: manifest.json → digest>",
    "chunks": [{
      "n": 1,
      "id": "remote-attestation-for-ai-workloads-explained/en#intro/0",
      "slug": "remote-attestation-for-ai-workloads-explained", "lang": "en", "kind": "explainer",
      "title": "Remote attestation for AI workloads, explained", "heading": null,
      "url": "/articles/remote-attestation-for-ai-workloads-explained/",
      "source": "/articles/remote-attestation-for-ai-workloads-explained/en.md",
      "source_sha256": "<sha256 of that file, as listed in /manifest.json>",
      "start": 2792, "end": 3483,
      "text": "Remote attestation lets one party obtain hardware-signed evidence ..."
    }]
  },
  "options": { "max_output_tokens": 700, "temperature": 0.2 }
}
```

| Field | Rules |
| --- | --- |
| `lang` | `en` or `zh`; the answer is written in this language even when passages are in the other one. |
| `nonce` | The attestation nonce. |
| `page` | `null`, or the page the reader is on (`path` is the canonical site path). Lets the backend know the question is about one article. |
| `messages` | Non-empty; roles `user` or `assistant`; the last message is the user's question. At most `limits.max_turns` user messages and `2 × max_turns` messages in total. The question is at most `limits.max_question_chars` characters; earlier messages at most 8,000. |
| `context.manifest_digest` | 64 hex or `null`. The digest of the manifest the passages came from. |
| `context.chunks` | At most `limits.max_context_chunks`, ranked by the browser, most relevant first. `n` values are unique positive integers and are the citation numbers. Required: `n`, `id`, `title`, `url` (canonical site path), `text` (at most 8,000 characters). Optional and nullable: `slug`, `lang`, `kind`, `heading`, `source` (a path listed in `/manifest.json`), `source_sha256`, `start`, `end`. |
| `start`, `end` | Offsets into the source file decoded as UTF-8, counted in **UTF-16 code units** (JavaScript string indices), with `end` exclusive, so `sourceText.slice(start, end) === text`. For text without characters outside the Basic Multilingual Plane these equal Python string indices; a Python verifier must otherwise convert. Both are `null` when the text is not a verbatim slice of a published source, for example a title and summary taken from `search-index.json`. |
| `options` | `max_output_tokens` is clamped to the published limit. `temperature` is 0 to 2. |

A request that breaks these rules gets `400 bad_request`; one that exceeds a published limit gets `413 too_long`. A body larger than `limits.max_body_bytes` gets `413 too_long` before it is parsed.

### Response stream

A successful response is `200` with `Content-Type: text/event-stream; charset=utf-8` and `X-Accel-Buffering: no`. In phase 0 the stream is plaintext. From phase 1 the identical text is carried inside EHBP chunks, and the client decrypts each chunk before parsing.

Framing is standard server-sent events: `event: <name>`, `data: <one line of JSON>`, then a blank line. Lines starting with `:` are comments. The server sends `: ping` right after the headers and whenever it has been silent for 15 seconds, so proxies keep the connection open and the client can tell a slow model from a dead connection.

Events arrive in this order: `meta`, `citations`, optionally `notice`, any number of `delta`, then exactly one of `done` or `error`. After `error` the stream ends without `done`.

```text
: ping

event: meta
data: {"request_id":"req_…","backend":"mock-local","mode":"mock","model":"mock-extractive","attestation_id":"att_mock_…","keyset_digest":"…","started_at":"2026-10-20T14:02:11Z"}

event: citations
data: {"items":[{"n":1,"chunk_id":"…","title":"…","heading":null,"url":"/articles/…/","lang":"en","source":"/articles/…/en.md","source_sha256":"…","start":2792,"end":3483,"context_verified":false}]}

event: delta
data: {"i":0,"text":"From the "}

event: done
data: {"finish_reason":"stop","used_citations":[1],"usage":{"input_tokens":524,"output_tokens":205,"estimated":true},"receipt":null}
```

| Event | Fields | Notes |
| --- | --- | --- |
| `meta` | `request_id`, `backend`, `model`, `attestation_id` (or `null`), `keyset_digest`, `started_at`; `mode` (*extension*) | The client flags the answer if `attestation_id` or `keyset_digest` differs from the bundle it verified. |
| `citations` | `items[]`: `n`, `chunk_id`, `title`, `heading`, `url`, `lang`, `source`, `source_sha256`, `start`, `end`, `context_verified` | Sent before generation and mirrors the chunks the model will see. `context_verified` is `true` only when the backend checked the chunk against its own copy of the corpus (P2); the mock always sends `false`. |
| `notice` | `code`, `message` | Example: `context_truncated` when passages were dropped to fit the model's context window. |
| `delta` | `i` (0, 1, 2, …), `text` | Concatenating `text` in order gives the answer. Answers use `[n]` markers that refer to `citations.items[].n`. |
| `done` | `finish_reason` (`stop`, `length`, `refused`), `used_citations` (the `[n]` that appear in the answer, in order of first use), `usage` or `null` (`estimated` is an *extension*), `receipt` or `null` | `receipt` is `null` until P2. |
| `error` | `code`, `message`, `retry_after_s` or `null` | Same codes as the HTTP errors below. |

### Receipts (P2)

From phase 2 the enclave signs each answer with the Ed25519 key in `keyset.receipt`. The signature covers this string, joined with LF and without a trailing LF:

```text
vp-receipt/v1
<request_sha256>
<response_sha256>
<model_digest>
<image_digest>
<system_prompt_sha256>
<corpus_manifest_digest>
<keyset_digest>
<nonce>
<issued_at>
```

`request_sha256` is the SHA-256 of the exact plaintext request bytes; `response_sha256` is the SHA-256 of the UTF-8 concatenation of all `delta.text` values. The client trusts the receipt key because `keyset_digest` is bound into the hardware report.

### Errors outside the stream

Every non-2xx response is JSON: `{"error":{"code":"…","message":"…","retry_after_s":120}}`, with `retry_after_s` only where it applies.

| Status | Code | When | Client action |
| --- | --- | --- | --- |
| 400 | `bad_request` | Malformed request; wrong content type; an encrypted body sent to a `none` backend | Fix the request |
| 403 | `origin_not_allowed` | CORS preflight from an origin outside the allowlist (*extension*) | None; the browser blocks the call |
| 404 | `not_found` | Unknown path (*extension*) | |
| 405 | `method_not_allowed` | Wrong method, with an `Allow` header (*extension*) | |
| 409 | `attestation_expired` | `VP-Attestation-Id` past `expires_at` | Re-attest and retry |
| 411 | `bad_request` | No `Content-Length` (chunked upload) | |
| 412 | `attestation_mismatch` | Unknown attestation id, other keyset digest, or a nonce that differs from the attested one | Re-attest and retry. In P1+ also treat EHBP's `422 application/problem+json` key-configuration error this way. |
| 413 | `too_long` | Over a published limit or over `max_body_bytes` | Shorten |
| 429 | `rate_limited` | Token bucket or daily cap exhausted; carries `Retry-After`, `RateLimit` and `RateLimit-Policy` | Wait, or offer the explicit "Use demo answers instead" button |
| 503 | `upstream_unavailable` | Model provider or enclave unreachable (P1+) | Same as 429 |
| 500 | `internal` | Server bug | Retry once |

## CORS

```text
Access-Control-Allow-Origin: <the request's Origin, if it is on the allowlist>
Vary: Origin
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: content-type, ehbp-encapsulated-key, vp-attestation-id, vp-keyset-digest, vp-challenge
Access-Control-Expose-Headers: ehbp-response-nonce, vp-request-id, retry-after, ratelimit, ratelimit-policy
Access-Control-Max-Age: 600
```

There is no `Access-Control-Allow-Credentials`; the widget sends no cookies. Production allows exactly `https://verifiable.pro` and `https://www.verifiable.pro`, plus `http://localhost:8767` in development builds. The mock allows `http://localhost:*` and `http://127.0.0.1:*` by default. `/healthz` answers any origin. In phase 1 with Tinfoil's SDK the proxy also allows `x-tinfoil-enclave-url` and `x-tinfoil-model`, and validates the enclave URL against its own allowlist. CORS only controls what a browser page may read. It authenticates nothing, which is why abuse control is a separate mechanism.

## Rate limits

The limiter counts per client network, not per person. The key is `HMAC(secret, IPv4 /24 or IPv6 /56)`; the secret is generated in memory and replaced at UTC midnight, and only the HMAC is held. In phase 2 this happens inside the confidential VM, so not even the counters are visible to the operator. The production targets are 10 requests per 10 minutes and 40 per day per key, plus a global daily cap as a cost ceiling. The mock implements the token bucket and the global cap.

Rate-limit headers follow the structured-field syntax of the IETF draft `draft-ietf-httpapi-ratelimit-headers`, which is not yet an RFC and may change:

```text
RateLimit-Policy: "chat";q=10;w=600
RateLimit: "chat";r=0;t=42
Retry-After: 42
```

## Client-side verification and the badge

The browser builds a `VerificationResult` (`#/$defs/VerificationResult`) from its own checks and renders the badge from it. The server never sends this object.

| `overall` | When |
| --- | --- |
| `demo` | The in-browser demo transport, or any backend whose `mode` is `mock` |
| `reported` | A non-mock backend whose claims are shown but not checked in the browser |
| `partly_verified` | Some checks ran in the browser and passed, others were skipped or are unverifiable |
| `verified` | Every applicable check passed in the browser |
| `failed` | A check failed |

Phase 0 can produce only `demo` and `reported`. The other three exist in the code so later phases fill them in rather than change the format. No state is drawn as a green check mark, and any skipped check makes the headline read "Partly verified".

Each check has an `id` and a `status`: `verified_in_browser`, `verified_by_third_party` (a vendor token whose signature the browser checked), `reported`, `not_checked`, `failed`, `not_applicable` or `unverifiable`. Planned check ids are `cpu_evidence_signature`, `report_data_binding`, `nonce_fresh`, `measurement_matches_release`, `release_sigstore`, `gpu_nras_signature`, `gpu_cc_on`, `gpu_nonce_bound`, `model_digest_matches_release`, `tls_binding` (always `not_checked` in a browser, which cannot read the TLS certificate) and `citation_source_digest`. The result also lists `still_trusted`: what the reader must trust even when everything passes, including the page's own JavaScript, whose SHA-256 is listed in `/manifest.json`.

### Hooks left for later phases

These are not implemented in phase 0. The widget leaves named stubs for them, and a backend must not claim them.

- **Request and stream encryption (P1).** EHBP framing: HPKE base mode (RFC 9180) with X25519, HKDF-SHA256 and AES-256-GCM, 4-byte big-endian length-prefixed chunks, and the `Ehbp-Encapsulated-Key` and `Ehbp-Response-Nonce` headers. EHBP passes a request without `Ehbp-Encapsulated-Key` through as plaintext, so in `ehbp-v1` mode the client must always encrypt, must fail when `Ehbp-Response-Nonce` is missing, and the production gateway must reject plaintext requests.
- **Evidence verification (P1, P2).** Provider bundle verification (Tinfoil's JS verifier), TDX quote and SEV-SNP report verification, Confidential Space token verification, NVIDIA token signature and `x5c` chain verification against the pinned NVIDIA root, and Sigstore release verification.
- **Receipt verification (P2).** Ed25519 over the canonical string above, with the request and response hashes recomputed in the browser.

## Transports in the widget

The widget has two transports. `demo` answers entirely in the browser from the site's own files and makes no network request beyond same-origin static files. `http` talks to `{api}` with this contract. The widget never falls back from `http` to `demo` on its own; when the backend fails or rate-limits, it offers an explicit "Use demo answers instead" button.

## Fixtures

| File | Content | How it is made |
| --- | --- | --- |
| `meta.json` | Mock `GET /v1/meta` | Generated |
| `attestation.mock.json` | Mock bundle for the fixture nonce | Generated |
| `attestation.selfhosted.example.json` | P2 bundle with realistic shape and fake values, marked `"example": true`; for laying out the verification panel only | Curated; its `keyset_digest` and `gpu_nonce` are computed correctly from its fake values |
| `chat.request.json`, `chat.request.zh.json` | Requests with real passages, three from two EN articles and two from one zh article, with offsets and source digests from the build whose manifest digest is `d78789be…` | Curated: the questions and the chosen passages; `backend/mock/refresh_requests.py` refreshes the rest from a build |
| `chat.sse.json`, `chat.sse.zh.json` | The mock's streams for those requests, as parsed events and as raw text | Generated |
| `chat.sse.error.json` | The `error` test trigger: a few deltas, then `error` and no `done` | Generated |
| `errors.json` | Error responses: 400, 409, 412, 413 and 429 from the mock, plus a P1 503 | Generated |

Generated fixtures come from the mock with a fixed clock and deterministic ids. Regenerate them after changing the mock with `python3 backend/mock/make_fixtures.py`; the mock's tests fail when they are stale. A change to an article, a page, a data file, or a lead image's spec or picture changes the manifest digest, and editing a chunk's article can move its offsets, so after a content change run `python3 backend/mock/refresh_requests.py --write`. It cuts the request fixtures' passages again from a production build with the widget's own parser, updates the digest named above, and leaves the questions and the chosen passages as they are; then regenerate the generated fixtures. Until then, the tests re-slice offsets only while a chunk's source digest still matches its article.

## Differences from the design report's draft

This contract follows the API draft in the GPU confidential-computing backend report (section 5), with these changes:

- A mock bundle reports `summary.cc_mode: "off"` (the draft had `"unknown"`) and `summary.verified_by: []`.
- The badge's `overall` values are `demo`, `reported`, `partly_verified`, `verified` and `failed`. The draft's `not_verified` is replaced by `reported`.
- Phase-0 values are nullable where the draft assumed later phases: `keyset.hpke`, `release`, `report_url`, `privacy_url`, and in the summary `system_prompt_sha256`, `corpus` and `verified_at`.
- Defined here: what `max_turns` counts, the unit of `start` and `end` (UTF-16 code units), and the request validation rules.
- Extensions: `meta.system_prompt_sha256`, `meta.notice`, `limits.max_body_bytes`, the bundle's `notice` and `example`, `meta` event `mode`, `usage.estimated`, the error codes `not_found`, `method_not_allowed` and `origin_not_allowed`, and `411` for chunked uploads.
- The mock's model passthrough is `--openai-base URL --model NAME` (the draft called it `--llm`).
