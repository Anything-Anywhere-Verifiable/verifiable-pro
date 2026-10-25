# Mock chat backend (phase 0)

`server.py` implements the [chat API v1](../../api/chat-v1.md) with `mode: "mock"` and `encryption: "none"`, so the site's chat widget can be built and tested against the real endpoints before any confidential-computing backend exists. **Nothing it returns is attested.** It runs no trusted execution environment and uses no GPU confidential computing. It has no hardware evidence, and requests are not encrypted to an enclave key. Its attestation bundle says so in every field: `evidence: []`, `summary.tee.cpu: "none"`, `summary.cc_mode: "off"`, `summary.verified_by: []` and `operator_can_read_plaintext: true`. The widget must show the demo status for it.

The server uses only the Python standard library and runs on Python 3.9 and later.

## Run it

From the repository root:

```bash
python3 backend/mock/server.py
```

It listens on `http://127.0.0.1:8787`. To point a preview build at it, build the site with the chat in live mode and this API base (`build.py --chat live --chat-api http://127.0.0.1:8787`), then serve the preview over HTTP, for example with `python3 -m http.server 8767 --directory <build output>`. The default CORS allowlist accepts any port on `localhost` and `127.0.0.1`. A page opened from a `file://` URL sends `Origin: null`, which the allowlist refuses.

The server answers three endpoints plus a health check:

| Endpoint | What the mock does |
| --- | --- |
| `GET /v1/meta` | Mode `mock`, encryption `none`, the published limits |
| `GET /v1/attestation?nonce=<64 hex>` | A bundle that attests nothing, bound to no hardware, valid for 10 minutes |
| `POST /v1/chat` | Validates the request, then streams `meta`, `citations`, `delta`…, `done` as server-sent events with `: ping` heartbeats |
| `GET /healthz` | `{"status":"ok"}` from any origin |

### Answers

By default the answer is extractive. From each of the first three passages in `context.chunks`, the server quotes the sentence that shares the most terms with the question, in the request's language and with the passage's `[n]` marker. The `citations` event mirrors the passages it received, and `done.used_citations` lists the markers that appear in the answer. When the request carries no passages, the answer says the site has nothing on the question yet. No model is involved, so the answer can only be as good as the browser's retrieval.

### Using a real model

To test with a real model, point the server at any OpenAI-compatible endpoint, such as a local Ollama or vLLM:

```bash
python3 backend/mock/server.py --openai-base http://127.0.0.1:11434/v1 --model qwen3:8b
```

```bash
python3 backend/mock/server.py --openai-base http://127.0.0.1:8000/v1 --model Qwen/Qwen3-8B
```

The server sends a constant, public system prompt, the earlier turns, and one user message that holds the numbered passages and the question. It calls `{base}/chat/completions` with `stream: true` and relays each token as a `delta`. If the passages exceed `max_input_tokens` (estimated), it drops passages from the end and sends a `notice` event with code `context_truncated`. The prompt's SHA-256 appears in `GET /v1/meta` and in the attestation summary as `system_prompt_sha256`. To print the prompt and its digest:

```bash
python3 backend/mock/server.py --print-system-prompt
```

The upstream model is not attested either, and in this mode the questions and passages also reach that endpoint in plaintext. For an endpoint that needs a key, put the key in an environment variable and name the variable with `--api-key-env`; the server never takes a key on the command line. It ignores `http_proxy` and similar environment variables and connects to `--openai-base` directly.

### Test triggers

Words in the question switch the mock into test behaviour. Each must appear as a whole word, case-insensitive; `--no-triggers` turns them off.

| Word | Effect |
| --- | --- |
| `slow` | Waits before the first token and streams slowly (`--slow-step`, 0.25 s per piece), for testing Stop, idle timers and heartbeats |
| `error` | Streams a few deltas, then sends an `error` event (`upstream_unavailable`) and no `done` |
| `429` | Answers `429 rate_limited` with `Retry-After: 30` and the rate-limit headers |

The attestation headers are optional for the mock, but when the widget sends them they are checked as a real backend would check them. An unknown `VP-Attestation-Id` gives `412 attestation_mismatch`, and a restart makes every earlier id unknown. A `VP-Keyset-Digest` other than the current one also gives `412`, as does a body `nonce` that differs from the attested one. An expired id gives `409 attestation_expired`. This exercises the widget's re-attest path.

## Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | Bind address. Anything other than loopback prints a warning: the mock has no TLS and no attestation. |
| `--port` | `8787` | `0` picks a free port |
| `--allow-origin ORIGIN` | `http://localhost:*`, `http://127.0.0.1:*` | Repeatable. An exact origin, `scheme://host:*` for any port on that host, or `*` for any origin. Preflights from other origins get `403`. |
| `--rate N` | `10` | Chat requests per 10 minutes per client network (token bucket) |
| `--daily-cap N` | `2000` | Chat requests per UTC day across all clients; `0` turns it off |
| `--max-body BYTES` | `262144` | Larger bodies get `413 too_long` before they are parsed |
| `--ping-interval S` | `15` | Seconds of silence before a `: ping` comment |
| `--step S` | `0.02` | Delay between extractive deltas |
| `--slow-step S` | `0.25` | Delay between deltas for the `slow` trigger |
| `--attestation-ttl S` | `600` | Attestation lifetime |
| `--no-triggers` | off | Ignore the test words |
| `--openai-base URL`, `--model NAME` | off | Model passthrough; the two go together |
| `--api-key-env VAR` | none | Environment variable holding a bearer key for `--openai-base` |
| `--upstream-timeout S` | `120` | Seconds to wait on the model endpoint |
| `--quiet` | off | No access log |

## Privacy of the mock itself

The access log, on standard error, holds one line per request: the time to the minute, the method, the endpoint path, the status, the latency and an outcome such as `done` or `client-gone`. It never records request or response bodies, query strings (which carry the nonce), IP addresses or user agents. The rate limiter keeps only `HMAC(secret, IPv4 /24 or IPv6 /56)`. The secret is random, lives in memory and is replaced at UTC midnight, when every counter is dropped. Attestation ids and their nonces stay in memory until an hour after they expire. Nothing is written to disk.

## Try it with curl

In a second terminal, with the server running:

```bash
curl -s http://127.0.0.1:8787/v1/meta
```

```bash
NONCE=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
curl -s "http://127.0.0.1:8787/v1/attestation?nonce=$NONCE"
```

```bash
curl -sN http://127.0.0.1:8787/v1/chat -H 'Content-Type: application/json' \
  --data @api/fixtures/chat.request.json
```

```bash
curl -si -X OPTIONS http://127.0.0.1:8787/v1/chat -H 'Origin: http://localhost:8767' \
  -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type'
```

`-N` turns off curl's buffering so the events appear as they are sent.

## Tests and fixtures

```bash
python3 -m unittest discover -s backend/mock -p 'test_*.py'
```

The tests start the server on an ephemeral port in a thread. They cover meta, the mock bundle, the chat stream in both languages, CORS preflights, the token bucket and daily cap, the test triggers, the body-size limit, the attestation-header checks, client disconnects, the passthrough against a fake OpenAI-compatible server, and that the log holds no bodies. They also validate every fixture and every live payload against `api/chat-v1.schema.json` with a small validator for the schema's keyword subset, which rejects any keyword it does not implement.

After changing what the server sends, regenerate the server-produced fixtures in `api/fixtures/`; the tests fail while they are stale:

```bash
python3 backend/mock/make_fixtures.py
```

`python3 backend/mock/make_fixtures.py --check` only compares.

### After a content change

The request fixtures `chat.request.json` and `chat.request.zh.json` hold real passages from the site, with the manifest digest of the build they came from. Changing an article, a page, a data file, or a lead image's spec or picture changes that digest, and editing a chunk's article can move its offsets. Refresh the request fixtures first, then regenerate the fixtures the server produces from them:

```bash
python3 backend/mock/refresh_requests.py --write
python3 backend/mock/make_fixtures.py
python3 backend/mock/make_fixtures.py --check
python3 -m unittest discover -s backend/mock -p 'test_*.py'
```

`refresh_requests.py` builds the production site into a temporary folder, or reads an existing production build given with `--build DIR`. It cuts each fixture's chunks again with the widget's own passage parser from `static/chat.js`, which `chat_passages.mjs` runs in Node.js, so it needs Node.js as well as Python. It keeps the questions and the chunk ids, refreshes every digest, offset and passage text, and updates the digest prefix in `api/chat-v1.md`. Without `--write` it only reports what is stale, and exits with status 1 if anything is. If an edit removed a passage that a fixture uses, it stops and names the chunk id: choose another passage for that chunk by hand.
