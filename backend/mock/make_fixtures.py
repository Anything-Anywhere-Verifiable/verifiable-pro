#!/usr/bin/env python3
"""Regenerate the server-produced fixtures in api/fixtures/ from the mock.

    python3 backend/mock/make_fixtures.py            # writes api/fixtures/
    python3 backend/mock/make_fixtures.py --check    # exit 1 if they are stale

Writes meta.json, attestation.mock.json, chat.sse.json, chat.sse.zh.json,
chat.sse.error.json and errors.json by running the mock with a fixed clock and
deterministic ids against the request fixtures chat.request.json and
chat.request.zh.json. Those two, and attestation.selfhosted.example.json, are
curated by hand and are only read here.

Stdlib only; Python 3.9+.
"""

import argparse
import calendar
import copy
import hashlib
import http.client
import json
import os
import sys
import tempfile
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import server  # noqa: E402

FIXTURES = os.path.normpath(os.path.join(HERE, "..", "..", "api", "fixtures"))
GENERATED = ("meta.json", "attestation.mock.json", "chat.sse.json", "chat.sse.zh.json",
             "chat.sse.error.json", "errors.json")
ORIGIN = "http://localhost:8767"
NOW = calendar.timegm((2026, 10, 20, 14, 2, 11, 0, 0, 0))
KEPT_HEADERS = ("content-type", "cache-control", "x-accel-buffering", "retry-after", "ratelimit",
                "ratelimit-policy", "vp-request-id", "access-control-allow-origin",
                "access-control-expose-headers", "vary")


class Clock:
    def __init__(self):
        self.now = NOW

    def __call__(self):
        return self.now


def deterministic_app(rate=10):
    clock = Clock()
    app = server.App(server.Config(port=0, step=0, quiet=True, rate=rate), clock=clock, start_time=NOW - 431)
    counter = {"n": 0}

    def new_id(prefix):
        counter["n"] += 1
        return "%s_%s" % (prefix, hashlib.sha256(("%s:%d" % (prefix, counter["n"])).encode()).hexdigest()[:16])

    app.new_id = new_id
    app.attestations.new_id = new_id
    return app, clock


class Running:
    def __init__(self, app):
        self.srv = server.make_server(app)
        self.port = self.srv.server_address[1]
        self.thread = threading.Thread(target=self.srv.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.srv.shutdown()
        self.srv.server_close()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        h = {"Origin": ORIGIN}
        h.update(headers or {})
        data = None
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            h.setdefault("Content-Type", "application/json")
        conn.request(method, path, body=data, headers=h)
        resp = conn.getresponse()
        raw = resp.read()
        kept = {}
        for k, v in resp.getheaders():
            if k.lower() in KEPT_HEADERS:
                kept[k] = v
        conn.close()
        return resp.status, kept, raw


def parse_sse(text):
    """Blocks separated by blank lines -> [{"comment": ...} | {"event": ..., "data": ...}]."""
    out = []
    for block in text.split("\n\n"):
        if not block:
            continue
        name, data, comments = "message", [], []
        for line in block.split("\n"):
            if line.startswith(":"):
                comments.append(line[1:].strip())
            elif line.startswith("event:"):
                name = line[6:].strip()
            elif line.startswith("data:"):
                value = line[5:]
                data.append(value[1:] if value.startswith(" ") else value)
        if data:
            out.append({"event": name, "data": json.loads("\n".join(data))})
        for c in comments:
            out.append({"comment": c})
    return out


def load(name, folder=FIXTURES):
    with open(os.path.join(folder, name), encoding="utf-8") as f:
        return json.load(f)


def stream_fixture(run, request, description, request_fixture, question=None, headers=None):
    status, headers, raw = run.request("POST", "/v1/chat", request, headers)
    text = raw.decode("utf-8")
    doc = {"description": description, "request_fixture": request_fixture}
    if question is not None:
        doc["question"] = question
    doc.update({"response": {"status": status, "headers": headers}, "events": parse_sse(text), "raw": text})
    return doc


def generate():
    """Return {filename: document} for every generated fixture."""
    out = {}
    req_en = load("chat.request.json")
    req_zh = load("chat.request.zh.json")
    nonce = req_en["nonce"]

    app, clock = deterministic_app()
    with Running(app) as run:
        status, _, raw = run.request("GET", "/v1/meta")
        assert status == 200
        out["meta.json"] = json.loads(raw)

        status, _, raw = run.request("GET", "/v1/attestation?nonce=" + nonce)
        assert status == 200
        bundle = json.loads(raw)
        out["attestation.mock.json"] = bundle
        att_headers = {"VP-Attestation-Id": bundle["attestation_id"], "VP-Keyset-Digest": bundle["keyset_digest"]}

        out["chat.sse.json"] = stream_fixture(
            run, req_en, "Mock answer (extractive) to chat.request.json, sent with the VP-Attestation-Id and "
            "VP-Keyset-Digest of attestation.mock.json.", "chat.request.json", headers=att_headers)

        out["chat.sse.zh.json"] = stream_fixture(
            run, req_zh, "Mock answer (extractive) to chat.request.zh.json, sent without attestation headers.",
            "chat.request.zh.json")

        question = "Simulate an error: what does remote attestation prove?"
        req_err = copy.deepcopy(req_en)
        req_err["messages"][-1]["content"] = question
        out["chat.sse.error.json"] = stream_fixture(
            run, req_err, 'The "error" test trigger: a few deltas, then an error event and no done event.',
            "chat.request.json", question)

        examples = []

        def record(note, status, headers, raw):
            examples.append({"note": note, "status": status, "headers": headers, "body": json.loads(raw)})

        record("Malformed nonce on GET /v1/attestation.",
               *run.request("GET", "/v1/attestation?nonce=1234"))
        bad = copy.deepcopy(req_en)
        bad["api_version"] = "2"
        record("Unsupported api_version.", *run.request("POST", "/v1/chat", bad))
        record("Unknown VP-Attestation-Id (for example after the backend restarted).",
               *run.request("POST", "/v1/chat", req_en, {"VP-Attestation-Id": "att_mock_unknown"}))
        clock.now = NOW + 601
        record("The attestation expired (expires_at passed).",
               *run.request("POST", "/v1/chat", req_en, {"VP-Attestation-Id": bundle["attestation_id"]}))
        clock.now = NOW
        long_q = copy.deepcopy(req_en)
        long_q["messages"][-1]["content"] = "x" * (server.LIMITS["max_question_chars"] + 1)
        record("Question longer than limits.max_question_chars.", *run.request("POST", "/v1/chat", long_q))

    app1, _ = deterministic_app(rate=1)
    with Running(app1) as run:
        run.request("POST", "/v1/chat", req_en)
        record("Per-network token bucket exhausted (server started with --rate 1).",
               *run.request("POST", "/v1/chat", req_en))
    examples.append({
        "note": "Phase 1+ only (the mock never sends it): the model provider or enclave is unreachable.",
        "status": 503, "headers": {"Content-Type": "application/json; charset=utf-8", "Retry-After": "120"},
        "body": {"error": {"code": "upstream_unavailable", "message": "The model backend is unavailable.",
                           "retry_after_s": 120}}})
    out["errors.json"] = {"description": "Error responses outside the event stream. Every body is "
                                         "{\"error\":{code,message,retry_after_s?}}.", "examples": examples}
    return out


def dump(doc):
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--check", action="store_true", help="compare instead of writing; exit 1 when stale")
    p.add_argument("--out", default=FIXTURES, help="output folder (default api/fixtures)")
    args = p.parse_args(argv)
    docs = generate()
    stale = []
    for name in GENERATED:
        path = os.path.join(args.out, name)
        text = dump(docs[name])
        if args.check:
            try:
                with open(path, encoding="utf-8") as f:
                    if f.read() != text:
                        stale.append(name)
            except FileNotFoundError:
                stale.append(name)
        else:
            fd, tmp = tempfile.mkstemp(dir=args.out, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(text)
            os.chmod(tmp, 0o644)
            os.replace(tmp, path)
    if args.check:
        if stale:
            sys.stderr.write("stale fixtures (run backend/mock/make_fixtures.py): %s\n" % ", ".join(stale))
            return 1
        print("fixtures up to date")
        return 0
    print("wrote %s to %s" % (", ".join(GENERATED), args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
