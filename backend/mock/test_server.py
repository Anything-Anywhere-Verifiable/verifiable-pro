#!/usr/bin/env python3
"""Tests for the phase-0 mock backend, the API schema and the fixtures.

Stdlib unittest; Python 3.9+. From the repository root:

    python3 -m unittest discover -s backend/mock -p 'test_*.py'

Each test class starts its own server on an ephemeral port in a thread.
"""

import calendar
import contextlib
import copy
import hashlib
import http.client
import io
import json
import os
import re
import socket
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_fixtures  # noqa: E402
import server  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FIXTURES = os.path.join(ROOT, "api", "fixtures")
with open(os.path.join(ROOT, "api", "chat-v1.schema.json"), encoding="utf-8") as _f:
    SCHEMA = json.load(_f)
ALLOWED = "http://localhost:8767"
EVENT_SCHEMAS = {"meta": "EventMeta", "citations": "EventCitations", "delta": "EventDelta",
                 "notice": "EventNotice", "done": "EventDone", "error": "EventError"}


# ------------------------------------------------ minimal JSON Schema validator

ANNOTATIONS = {"$schema", "$id", "$comment", "title", "description", "examples", "default"}
KEYWORDS = {"$ref", "$defs", "allOf", "anyOf", "type", "enum", "const", "required", "properties",
            "items", "minItems", "maxItems", "minLength", "pattern", "minimum", "maximum"}


class UnsupportedSchema(Exception):
    pass


def _type_ok(v, t):
    if t == "null":
        return v is None
    if t == "boolean":
        return isinstance(v, bool)
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "string":
        return isinstance(v, str)
    if t == "array":
        return isinstance(v, list)
    if t == "object":
        return isinstance(v, dict)
    raise UnsupportedSchema("type " + t)


def _same(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def _pattern(p):
    return p[:-1] + r"\Z" if p.endswith("$") and not p.endswith("\\$") else p


def _check(v, s, path, errors):
    if s is True:
        return
    if s is False:
        errors.append("%s: no value allowed" % path)
        return
    unknown = set(s) - KEYWORDS - ANNOTATIONS
    if unknown:
        raise UnsupportedSchema("%s uses %s" % (path, sorted(unknown)))
    if "$ref" in s:
        ref = s["$ref"]
        if not ref.startswith("#/$defs/"):
            raise UnsupportedSchema(ref)
        _check(v, SCHEMA["$defs"][ref[len("#/$defs/"):]], path, errors)
    if "type" in s:
        types = s["type"] if isinstance(s["type"], list) else [s["type"]]
        if not any(_type_ok(v, t) for t in types):
            errors.append("%s: expected %s, got %r" % (path, "/".join(types), v))
            return
    if "const" in s and not _same(v, s["const"]):
        errors.append("%s: expected %r, got %r" % (path, s["const"], v))
    if "enum" in s and not any(_same(v, e) for e in s["enum"]):
        errors.append("%s: %r not in %r" % (path, v, s["enum"]))
    for sub in s.get("allOf", []):
        _check(v, sub, path, errors)
    if "anyOf" in s:
        if not any(not schema_errors(v, sub, path) for sub in s["anyOf"]):
            errors.append("%s: %r matches no anyOf branch" % (path, v))
    if isinstance(v, str):
        if "minLength" in s and len(v) < s["minLength"]:
            errors.append("%s: shorter than %d" % (path, s["minLength"]))
        if "pattern" in s and not re.search(_pattern(s["pattern"]), v):
            errors.append("%s: %r does not match %s" % (path, v, s["pattern"]))
    if _type_ok(v, "number"):
        if "minimum" in s and v < s["minimum"]:
            errors.append("%s: %r < %r" % (path, v, s["minimum"]))
        if "maximum" in s and v > s["maximum"]:
            errors.append("%s: %r > %r" % (path, v, s["maximum"]))
    if isinstance(v, list):
        if "minItems" in s and len(v) < s["minItems"]:
            errors.append("%s: fewer than %d items" % (path, s["minItems"]))
        if "maxItems" in s and len(v) > s["maxItems"]:
            errors.append("%s: more than %d items" % (path, s["maxItems"]))
        if "items" in s:
            for i, x in enumerate(v):
                _check(x, s["items"], "%s[%d]" % (path, i), errors)
    if isinstance(v, dict):
        for k in s.get("required", []):
            if k not in v:
                errors.append("%s: missing %s" % (path, k))
        for k, sub in s.get("properties", {}).items():
            if k in v:
                _check(v[k], sub, "%s.%s" % (path, k), errors)


def schema_errors(value, schema, path="$"):
    errors = []
    _check(value, schema, path, errors)
    return errors


def errors_for(value, name):
    return schema_errors(value, {"$ref": "#/$defs/" + name})


# ------------------------------------------------ helpers

class Clock:
    """Real time plus an offset the tests can move."""

    def __init__(self):
        self.offset = 0.0

    def __call__(self):
        return time.time() + self.offset


def load_fixture(name):
    with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
        return json.load(f)


def chat_request(question="What does remote attestation prove?", lang="en", chunks=None):
    req = load_fixture("chat.request.json" if lang == "en" else "chat.request.zh.json")
    req["messages"][-1]["content"] = question
    if chunks is not None:
        req["context"]["chunks"] = chunks
    return req


def events_of(raw):
    return make_fixtures.parse_sse(raw.decode("utf-8"))


def answer_of(events):
    return "".join(e["data"]["text"] for e in events if e.get("event") == "delta")


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerCase(unittest.TestCase):
    config = {}

    @classmethod
    def setUpClass(cls):
        cls.log = io.StringIO()
        cls.clock = Clock()
        cfg = {"port": 0, "step": 0, "rate": 1000, "log_stream": cls.log}
        cfg.update(cls.config)
        cls.app = server.App(server.Config(**cfg), clock=cls.clock)
        cls.srv = server.make_server(cls.app)
        cls.port = cls.srv.server_address[1]
        cls.thread = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        cls.srv.server_close()

    def setUp(self):
        self.clock.offset = 0.0

    def request(self, method, path, body=None, headers=None, origin=ALLOWED, raw=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)
        h = {}
        if origin:
            h["Origin"] = origin
        if body is not None:
            raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
            h["Content-Type"] = "application/json"
        h.update(headers or {})
        conn.request(method, path, body=raw, headers=h)
        resp = conn.getresponse()
        data = resp.read()
        hdrs = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, hdrs, data

    def json_of(self, data):
        return json.loads(data.decode("utf-8"))

    def assertValid(self, value, name):
        errs = errors_for(value, name)
        self.assertEqual(errs, [], "\n".join(errs[:10]))

    def assertApiError(self, status, data, want_status, code):
        self.assertEqual(status, want_status, data)
        body = self.json_of(data)
        self.assertValid(body, "ErrorResponse")
        self.assertEqual(body["error"]["code"], code)
        return body

    def nonce(self):
        return os.urandom(32).hex()


# ------------------------------------------------ schema and fixtures

class SchemaAndFixtureTests(unittest.TestCase):
    def test_schema_uses_only_supported_keywords_and_refs_resolve(self):
        def walk(s, path):
            if isinstance(s, bool):
                return
            self.assertIsInstance(s, dict, path)
            unknown = set(s) - KEYWORDS - ANNOTATIONS
            self.assertFalse(unknown, "%s uses %s" % (path, unknown))
            if "$ref" in s:
                self.assertTrue(s["$ref"].startswith("#/$defs/"), path)
                self.assertIn(s["$ref"][8:], SCHEMA["$defs"], path)
            for k in ("allOf", "anyOf"):
                for i, sub in enumerate(s.get(k, [])):
                    walk(sub, "%s/%s/%d" % (path, k, i))
            for k, sub in s.get("properties", {}).items():
                walk(sub, path + "/properties/" + k)
            for k, sub in s.get("$defs", {}).items():
                walk(sub, path + "/$defs/" + k)
            if "items" in s:
                walk(s["items"], path + "/items")
            if "pattern" in s:
                re.compile(_pattern(s["pattern"]))
        self.assertEqual(SCHEMA["$schema"], "https://json-schema.org/draft/2020-12/schema")
        walk(SCHEMA, "#")

    def test_validator_rejects_bad_values(self):
        meta = load_fixture("meta.json")
        bad = copy.deepcopy(meta)
        bad["mode"] = "production"
        self.assertTrue(errors_for(bad, "Meta"))
        bad = copy.deepcopy(meta)
        del bad["limits"]["max_turns"]
        self.assertTrue(errors_for(bad, "Meta"))
        self.assertTrue(errors_for({"i": True, "text": "x"}, "EventDelta"))      # bool is not an integer
        self.assertTrue(errors_for("a" * 64 + "\n", "Hex64"))                       # $ means end of string
        self.assertEqual(errors_for("a" * 64, "Hex64"), [])

    def test_every_fixture_is_json(self):
        names = sorted(n for n in os.listdir(FIXTURES) if n.endswith(".json"))
        self.assertIn("attestation.selfhosted.example.json", names)
        for n in names:
            load_fixture(n)

    def test_payload_fixtures_match_schema(self):
        errs = errors_for(load_fixture("meta.json"), "Meta")
        self.assertEqual(errs, [], errs)
        errs = errors_for(load_fixture("attestation.mock.json"), "MockAttestationBundle")
        self.assertEqual(errs, [], errs)
        for name in ("chat.request.json", "chat.request.zh.json"):
            req = load_fixture(name)
            self.assertEqual(errors_for(req, "ChatRequest"), [], name)
            server.validate_chat(req, server.LIMITS)       # the mock accepts it too

    def test_selfhosted_example_is_marked_and_consistent(self):
        ex = load_fixture("attestation.selfhosted.example.json")
        self.assertIs(ex["example"], True)
        self.assertIn("EXAMPLE", ex["notice"])
        self.assertEqual(errors_for(ex, "ExampleAttestationBundle"), [])
        self.assertTrue(errors_for(ex, "MockAttestationBundle"), "the example must not pass as a mock bundle")
        self.assertEqual(ex["keyset_digest"], server.keyset_digest(ex["keyset"]))
        want = hashlib.sha256(bytes.fromhex(ex["nonce"]) + bytes.fromhex(ex["keyset_digest"])).hexdigest()
        self.assertEqual(ex["binding"]["gpu_nonce"], want)
        self.assertIn(".invalid", ex["report_url"])

    def test_mock_attestation_fixture_says_nothing_is_attested(self):
        b = load_fixture("attestation.mock.json")
        self.assertEqual(b["mode"], "mock")
        self.assertEqual(b["evidence"], [])
        self.assertEqual(b["summary"]["tee"]["cpu"], "none")
        self.assertEqual(b["summary"]["cc_mode"], "off")
        self.assertEqual(b["summary"]["verified_by"], [])
        self.assertNotIn("example", b)
        self.assertEqual(b["keyset_digest"], server.keyset_digest(b["keyset"]))

    def test_stream_fixtures_match_schema_and_raw_text(self):
        for name in ("chat.sse.json", "chat.sse.zh.json", "chat.sse.error.json"):
            doc = load_fixture(name)
            self.assertEqual(doc["response"]["status"], 200)
            self.assertTrue(doc["response"]["headers"]["Content-Type"].startswith("text/event-stream"))
            self.assertEqual(make_fixtures.parse_sse(doc["raw"]), doc["events"], name)
            for e in doc["events"]:
                if "event" in e:
                    errs = errors_for(e["data"], EVENT_SCHEMAS[e["event"]])
                    self.assertEqual(errs, [], "%s %s %s" % (name, e["event"], errs))
            kinds = [e.get("event") for e in doc["events"]]
            self.assertEqual(kinds[-1], "error" if "error" in name else "done", name)

    def test_error_fixture_bodies_match_schema(self):
        doc = load_fixture("errors.json")
        statuses = set()
        for ex in doc["examples"]:
            self.assertEqual(errors_for(ex["body"], "ErrorResponse"), [], ex["note"])
            statuses.add(ex["status"])
            if ex["status"] == 429:
                self.assertEqual(ex["headers"]["Retry-After"], str(ex["body"]["error"]["retry_after_s"]))
        self.assertTrue({400, 409, 412, 413, 429, 503} <= statuses)

    def test_generated_fixtures_are_in_sync_with_the_mock(self):
        docs = make_fixtures.generate()
        for name in make_fixtures.GENERATED:
            with open(os.path.join(FIXTURES, name), encoding="utf-8") as f:
                self.assertEqual(f.read(), make_fixtures.dump(docs[name]),
                                 "%s is stale; run python3 backend/mock/make_fixtures.py" % name)

    def test_request_fixture_offsets_reslice_current_sources(self):
        for name in ("chat.request.json", "chat.request.zh.json"):
            for c in load_fixture(name)["context"]["chunks"]:
                path = os.path.join(ROOT, "content", c["source"].lstrip("/"))
                if not os.path.exists(path):
                    continue
                with open(path, "rb") as f:
                    raw = f.read()
                if hashlib.sha256(raw).hexdigest() != c["source_sha256"]:
                    continue   # the article changed since the fixture was cut; digests now differ by design
                units = raw.decode("utf-8").encode("utf-16-le")
                self.assertEqual(units[2 * c["start"]:2 * c["end"]].decode("utf-16-le"), c["text"], c["id"])

    def test_contract_names_the_request_fixtures_manifest_digest(self):
        """Both request fixtures come from one build, whose digest api/chat-v1.md names;
        refresh_requests.py --write keeps the three in step."""
        import refresh_requests
        digests = {load_fixture(name)["context"]["manifest_digest"] for name in refresh_requests.NAMES}
        self.assertEqual(len(digests), 1, digests)
        with open(refresh_requests.CONTRACT, encoding="utf-8") as f:
            named = refresh_requests.CONTRACT_DIGEST_RE.search(f.read())
        self.assertIsNotNone(named, "api/chat-v1.md no longer names the request fixtures' manifest digest")
        self.assertEqual(named.group(2), digests.pop()[:8],
                         "run python3 backend/mock/refresh_requests.py --write")


# ------------------------------------------------ pure functions

class HelperTests(unittest.TestCase):
    def test_origin_patterns(self):
        pats = list(server.DEFAULT_ORIGINS)
        self.assertTrue(server.origin_allowed("http://localhost:8767", pats))
        self.assertTrue(server.origin_allowed("http://localhost", pats))
        self.assertTrue(server.origin_allowed("http://127.0.0.1:5500", pats))
        self.assertFalse(server.origin_allowed("http://localhost.evil.example:80", pats))
        self.assertFalse(server.origin_allowed("https://localhost:8767", pats))
        self.assertFalse(server.origin_allowed("null", pats))
        self.assertFalse(server.origin_allowed(None, pats))
        self.assertTrue(server.origin_allowed("https://verifiable.pro", ["https://verifiable.pro"]))
        self.assertFalse(server.origin_allowed("https://www.verifiable.pro", ["https://verifiable.pro"]))
        self.assertTrue(server.origin_allowed("https://anything.example", ["*"]))

    def test_network_prefix(self):
        self.assertEqual(server.network_prefix("203.0.113.77"), "203.0.113.0/24")
        self.assertEqual(server.network_prefix("::ffff:203.0.113.77"), "203.0.113.0/24")
        self.assertEqual(server.network_prefix("2001:db8:aaaa:bbcc::1"), "2001:db8:aaaa:bb00::/56")

    def test_jcs_and_keyset_digest(self):
        self.assertEqual(server.jcs({"b": None, "a": [1, "x", True]}), '{"a":[1,"x",true],"b":null}')
        with self.assertRaises(TypeError):
            server.jcs({"a": 1.5})
        ks = {"epoch": "2026-10-20T13:55:00Z", "hpke": None, "receipt": None, "tls_spki_sha256": None, "release": None}
        want = hashlib.sha256(b"vp-keyset/v1\n" + server.jcs(ks).encode()).hexdigest()
        self.assertEqual(server.keyset_digest(ks), want)

    def test_split_deltas_round_trips(self):
        for text in ("Hello  world.\n\n- **a** [1]", "\u8fdc\u7a0b\u8bc1\u660e\uff1a\u201cTDX\u201d [2]\n", "", "   "):
            self.assertEqual("".join(server.split_deltas(text)), text)

    def test_cited_numbers(self):
        self.assertEqual(server.cited_numbers("a [2] b [1, 3] c [2][9] d [1\uff0c2]", {1, 2, 3}), [2, 1, 3])

    def test_triggers_are_whole_words(self):
        find = lambda q: set(t.lower() for t in server.TRIGGER_RE.findall(q))
        self.assertEqual(find("please be SLOW"), {"slow"})
        self.assertEqual(find("what errors exist? slowly"), set())
        self.assertEqual(find("error 429"), {"error", "429"})
        self.assertEqual(find("x4290"), set())

    def test_compose_answer(self):
        chunk = {"n": 4, "title": "T", "heading": None,
                 "text": "Intro line.[^1] Attestation proves [which code](/x/) loaded. Unrelated."}
        text = server.compose_answer("en", "what does attestation prove", [chunk])
        self.assertIn("\u201cAttestation proves which code loaded.\u201d [4]", text)
        self.assertNotIn("[^1]", text)
        self.assertIn("nothing on this yet", server.compose_answer("en", "q", []))
        self.assertIn("\u76ee\u524d\u8fd8\u6ca1\u6709", server.compose_answer("zh", "q", []))

    def test_system_prompt_digest(self):
        self.assertEqual(server.SYSTEM_PROMPT_SHA256, hashlib.sha256(server.SYSTEM_PROMPT.encode("utf-8")).hexdigest())


# ------------------------------------------------ endpoints

class EndpointTests(ServerCase):
    def test_meta(self):
        status, h, data = self.request("GET", "/v1/meta")
        self.assertEqual(status, 200)
        self.assertEqual(h["cache-control"], "no-store")
        meta = self.json_of(data)
        self.assertValid(meta, "Meta")
        self.assertEqual((meta["mode"], meta["encryption"], meta["attestation_required"]), ("mock", "none", False))
        self.assertEqual(meta["limits"]["max_question_chars"], 1200)
        self.assertIsNone(meta["system_prompt_sha256"])
        self.assertIn("NOTHING", meta["notice"].upper())

    def test_healthz_any_origin(self):
        status, h, data = self.request("GET", "/healthz", origin="https://elsewhere.example")
        self.assertEqual((status, self.json_of(data)), (200, {"status": "ok"}))
        self.assertEqual(h["access-control-allow-origin"], "*")

    def test_attestation_mock_bundle(self):
        nonce = self.nonce()
        status, _, data = self.request("GET", "/v1/attestation?nonce=" + nonce)
        self.assertEqual(status, 200)
        b = self.json_of(data)
        self.assertValid(b, "MockAttestationBundle")
        self.assertEqual(b["nonce"], nonce)
        self.assertEqual(b["summary"]["nonce"], nonce)
        self.assertEqual(b["mode"], "mock")
        self.assertEqual(b["evidence"], [])
        self.assertEqual(b["summary"]["tee"]["cpu"], "none")
        self.assertEqual(b["summary"]["cc_mode"], "off")
        self.assertEqual(b["summary"]["verified_by"], [])
        self.assertIs(b["summary"]["claims"]["operator_can_read_plaintext"], True)
        self.assertEqual(b["binding"]["method"], "none")
        self.assertEqual(b["keyset_digest"], server.keyset_digest(b["keyset"]))
        self.assertNotIn("example", b)
        t = lambda s: calendar.timegm(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ"))
        self.assertEqual(t(b["expires_at"]) - t(b["issued_at"]), 600)

    def test_attestation_rejects_bad_nonces(self):
        for q in ("", "?nonce=", "?nonce=abc", "?nonce=" + "A" * 64, "?nonce=" + "a" * 63,
                  "?nonce=%s&nonce=%s" % ("a" * 64, "b" * 64)):
            status, _, data = self.request("GET", "/v1/attestation" + q)
            self.assertApiError(status, data, 400, "bad_request")

    def test_unknown_path_and_wrong_method(self):
        status, _, data = self.request("GET", "/v1/nope")
        self.assertApiError(status, data, 404, "not_found")
        status, h, data = self.request("GET", "/v1/chat")
        self.assertApiError(status, data, 405, "method_not_allowed")
        self.assertIn("POST", h["allow"])

    # -- CORS
    def test_cors_preflight_allowed(self):
        status, h, data = self.request("OPTIONS", "/v1/chat", headers={
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type, vp-attestation-id, vp-keyset-digest"})
        self.assertEqual(status, 204)
        self.assertEqual(data, b"")
        self.assertEqual(h["access-control-allow-origin"], ALLOWED)
        self.assertEqual(h["vary"], "Origin")
        self.assertEqual(h["access-control-allow-methods"], "GET, POST, OPTIONS")
        allowed = [x.strip() for x in h["access-control-allow-headers"].split(",")]
        for name in ("content-type", "vp-attestation-id", "vp-keyset-digest", "ehbp-encapsulated-key"):
            self.assertIn(name, allowed)
        self.assertEqual(h["access-control-max-age"], "600")
        self.assertNotIn("access-control-allow-credentials", h)

    def test_cors_preflight_other_origins_refused(self):
        for origin in ("https://evil.example", "http://localhost.evil.example:8767", "null"):
            status, h, data = self.request("OPTIONS", "/v1/chat", origin=origin,
                                           headers={"Access-Control-Request-Method": "POST"})
            self.assertApiError(status, data, 403, "origin_not_allowed")
            self.assertNotIn("access-control-allow-origin", h)

    def test_cors_on_simple_requests(self):
        status, h, _ = self.request("GET", "/v1/meta")
        self.assertEqual(h["access-control-allow-origin"], ALLOWED)
        self.assertIn("retry-after", h["access-control-expose-headers"])
        self.assertIn("vp-request-id", h["access-control-expose-headers"])
        status, h, data = self.request("GET", "/v1/meta", origin="https://evil.example")
        self.assertEqual(status, 200)            # CORS is not access control; the browser blocks the read
        self.assertNotIn("access-control-allow-origin", h)
        self.assertEqual(h["vary"], "Origin")
        status, h, _ = self.request("GET", "/v1/meta", origin=None)
        self.assertNotIn("access-control-allow-origin", h)

    # -- chat stream
    def check_stream(self, status, h, data):
        self.assertEqual(status, 200, data[:300])
        self.assertTrue(h["content-type"].startswith("text/event-stream"))
        self.assertEqual(h["cache-control"], "no-store")
        self.assertEqual(h["x-accel-buffering"], "no")
        self.assertEqual(h["access-control-allow-origin"], ALLOWED)
        evs = events_of(data)
        self.assertEqual(evs[0], {"comment": "ping"})
        for e in evs:
            if "event" in e:
                self.assertValid(e["data"], EVENT_SCHEMAS[e["event"]])
        return evs

    def test_chat_stream_en(self):
        req = chat_request("What does a valid remote attestation report prove?")
        status, h, data = self.request("POST", "/v1/chat", req)
        evs = self.check_stream(status, h, data)
        names = [e["event"] for e in evs if "event" in e]
        self.assertEqual(names[:2], ["meta", "citations"])
        self.assertEqual(names[-1], "done")
        self.assertEqual(set(names[2:-1]), {"delta"})
        meta = evs[1]["data"]
        self.assertEqual(meta["backend"], "mock-local")
        self.assertEqual(meta["keyset_digest"], self.app.keyset_digest)
        self.assertIsNone(meta["attestation_id"])
        self.assertEqual(meta["request_id"], h["vp-request-id"])
        items = [e for e in evs if e.get("event") == "citations"][0]["data"]["items"]
        chunks = req["context"]["chunks"]
        self.assertEqual([(i["n"], i["chunk_id"], i["url"], i["source_sha256"], i["start"], i["end"]) for i in items],
                         [(c["n"], c["id"], c["url"], c["source_sha256"], c["start"], c["end"]) for c in chunks])
        self.assertTrue(all(i["context_verified"] is False for i in items))
        deltas = [e["data"] for e in evs if e.get("event") == "delta"]
        self.assertEqual([d["i"] for d in deltas], list(range(len(deltas))))
        text = answer_of(evs)
        self.assertIn("[1]", text)
        self.assertIn("Mock backend", text)
        done = evs[-1]["data"]
        self.assertEqual(done["finish_reason"], "stop")
        self.assertEqual(done["used_citations"], server.cited_numbers(text, {c["n"] for c in chunks}))
        self.assertTrue(set(done["used_citations"]) <= {c["n"] for c in chunks})
        self.assertIsNone(done["receipt"])
        self.assertIn("ratelimit", h)

    def test_chat_stream_zh(self):
        status, h, data = self.request("POST", "/v1/chat", chat_request("\u8fdc\u7a0b\u8bc1\u660e\u80fd\u8bc1\u660e\u4ec0\u4e48\uff1f", lang="zh"))
        evs = self.check_stream(status, h, data)
        text = answer_of(evs)
        self.assertTrue(text.startswith("\u6839\u636e\u6d4f\u89c8\u5668\u53d1\u9001\u7684\u6bb5\u843d"))
        self.assertIn("[1]", text)
        self.assertEqual(evs[-1]["event"], "done")

    def test_chat_without_chunks_says_the_site_has_nothing(self):
        for lang, needle in (("en", "has nothing on this yet"), ("zh", "\u76ee\u524d\u8fd8\u6ca1\u6709")):
            status, h, data = self.request("POST", "/v1/chat", chat_request("Who won the 1998 World Cup?", lang, []))
            evs = self.check_stream(status, h, data)
            self.assertIn(needle, answer_of(evs))
            cites = [e for e in evs if e.get("event") == "citations"][0]["data"]["items"]
            self.assertEqual(cites, [])
            self.assertEqual(evs[-1]["data"]["used_citations"], [])

    def test_error_trigger(self):
        status, h, data = self.request("POST", "/v1/chat", chat_request("Simulate an error please"))
        evs = self.check_stream(status, h, data)
        names = [e["event"] for e in evs if "event" in e]
        self.assertEqual(names[-1], "error")
        self.assertNotIn("done", names)
        self.assertIn("delta", names)
        self.assertEqual(evs[-1]["data"]["code"], "upstream_unavailable")

    def test_429_trigger(self):
        status, h, data = self.request("POST", "/v1/chat", chat_request("pretend 429"))
        body = self.assertApiError(status, data, 429, "rate_limited")
        self.assertEqual(h["retry-after"], "30")
        self.assertEqual(body["error"]["retry_after_s"], 30)
        self.assertIn("ratelimit-policy", h)
        self.assertEqual(h["access-control-allow-origin"], ALLOWED)

    # -- request validation and size limits
    def test_bad_requests(self):
        good = chat_request()
        self.assertEqual(errors_for(good, "ChatRequest"), [])
        # (mutation, whether the JSON Schema alone also rejects it; the server is stricter)
        cases = [
            (lambda r: r.update(api_version="2"), True),
            (lambda r: r.update(lang="fr"), True),
            (lambda r: r.pop("nonce"), True),
            (lambda r: r.update(nonce="ABC"), True),
            (lambda r: r["messages"].append({"role": "assistant", "content": "hi"}), False),
            (lambda r: r["messages"][-1].update(role="system"), True),
            (lambda r: r.update(messages=[]), True),
            (lambda r: r.pop("context"), True),
            (lambda r: r["context"].update(manifest_digest="5232b984"), True),
            (lambda r: r["context"]["chunks"][1].update(n=1), False),
            (lambda r: r["context"]["chunks"][0].pop("text"), True),
            (lambda r: r["context"]["chunks"][0].update(start=-1), True),
            (lambda r: r.update(options={"temperature": 3}), True),
            (lambda r: r.update(options={"max_output_tokens": 0}), True),
            (lambda r: r.update(page="/articles/x/"), True),
        ]
        for mutate, schema_rejects in cases:
            r = copy.deepcopy(good)
            mutate(r)
            self.assertEqual(bool(errors_for(r, "ChatRequest")), schema_rejects, r)
            status, _, data = self.request("POST", "/v1/chat", r)
            self.assertApiError(status, data, 400, "bad_request")
        status, _, data = self.request("POST", "/v1/chat", raw=b"{not json", headers={"Content-Type": "application/json"})
        self.assertApiError(status, data, 400, "bad_request")
        status, _, data = self.request("POST", "/v1/chat", raw=b"[]", headers={"Content-Type": "application/json"})
        self.assertApiError(status, data, 400, "bad_request")
        status, _, data = self.request("POST", "/v1/chat", raw=json.dumps(good).encode(),
                                       headers={"Content-Type": "text/plain"})
        self.assertApiError(status, data, 400, "bad_request")
        status, _, data = self.request("POST", "/v1/chat", raw=b"\x00\x01", headers={
            "Content-Type": "message/ehbp", "Ehbp-Encapsulated-Key": "AAAA"})
        body = self.assertApiError(status, data, 400, "bad_request")
        self.assertIn("none", body["error"]["message"])

    def test_limits_return_413(self):
        too_long = chat_request("x" * 1201)
        status, _, data = self.request("POST", "/v1/chat", too_long)
        self.assertApiError(status, data, 413, "too_long")
        many = chat_request()
        base = many["context"]["chunks"][0]
        many["context"]["chunks"] = [dict(base, n=i + 1, id="c%d" % i) for i in range(9)]
        status, _, data = self.request("POST", "/v1/chat", many)
        self.assertApiError(status, data, 413, "too_long")
        turns = chat_request()
        turns["messages"] = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}] * 6 + \
            [{"role": "user", "content": "q"}]
        status, _, data = self.request("POST", "/v1/chat", turns)
        self.assertApiError(status, data, 413, "too_long")
        ok = chat_request()
        ok["messages"] = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}] * 5 + \
            [{"role": "user", "content": "q"}]
        status, _, _ = self.request("POST", "/v1/chat", ok)
        self.assertEqual(status, 200)

    def test_body_size_limit(self):
        # A declared size far above the limit is refused before any body is read.
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.putrequest("POST", "/v1/chat")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Content-Length", str(50 * 1024 * 1024))
        conn.endheaders()
        resp = conn.getresponse()
        self.assertApiError(resp.status, resp.read(), 413, "too_long")
        conn.close()
        # A real body just over the limit is drained, so the client reads the 413.
        req = chat_request()
        req["padding"] = "p" * (self.app.cfg.max_body + 1)
        status, _, data = self.request("POST", "/v1/chat", req)
        self.assertApiError(status, data, 413, "too_long")
        # Chunked uploads have no length to check.
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        conn.putrequest("POST", "/v1/chat")
        conn.putheader("Content-Type", "application/json")
        conn.putheader("Transfer-Encoding", "chunked")
        conn.endheaders()
        conn.send(b"2\r\n{}\r\n0\r\n\r\n")
        resp = conn.getresponse()
        self.assertApiError(resp.status, resp.read(), 411, "bad_request")
        conn.close()

    # -- attestation headers on chat
    def test_attestation_headers_checked_when_sent(self):
        nonce = self.nonce()
        _, _, data = self.request("GET", "/v1/attestation?nonce=" + nonce)
        b = self.json_of(data)
        req = chat_request()
        req["nonce"] = nonce
        good = {"VP-Attestation-Id": b["attestation_id"], "VP-Keyset-Digest": b["keyset_digest"]}
        status, h, data = self.request("POST", "/v1/chat", req, good)
        evs = self.check_stream(status, h, data)
        self.assertEqual(evs[1]["data"]["attestation_id"], b["attestation_id"])

        status, _, data = self.request("POST", "/v1/chat", req, {"VP-Attestation-Id": "att_mock_0000"})
        self.assertApiError(status, data, 412, "attestation_mismatch")
        status, _, data = self.request("POST", "/v1/chat", req, dict(good, **{"VP-Keyset-Digest": "0" * 64}))
        self.assertApiError(status, data, 412, "attestation_mismatch")
        other = copy.deepcopy(req)
        other["nonce"] = self.nonce()
        status, _, data = self.request("POST", "/v1/chat", other, good)
        self.assertApiError(status, data, 412, "attestation_mismatch")
        self.clock.offset = 601
        status, _, data = self.request("POST", "/v1/chat", req, good)
        self.assertApiError(status, data, 409, "attestation_expired")

    # -- logging
    def test_logs_hold_no_bodies_queries_or_addresses(self):
        nonce = self.nonce()
        self.request("GET", "/v1/attestation?nonce=" + nonce)
        req = chat_request("zebra-marker-7781 what is attested?")
        req["nonce"] = nonce
        req["context"]["chunks"][0]["text"] = "unicorn-passage-4492 attestation evidence."
        status, _, _ = self.request("POST", "/v1/chat", req)
        self.assertEqual(status, 200)
        self.request("POST", "/v1/chat", dict(req, lang="xx"))
        log = self.log.getvalue()
        self.assertIn("POST /v1/chat 200", log)
        self.assertIn("GET /v1/attestation 200", log)
        for secret in ("zebra-marker-7781", "unicorn-passage-4492", nonce, "127.0.0.1", "Python-urllib", "?nonce"):
            self.assertNotIn(secret, log)
        for line in log.splitlines():
            self.assertRegex(line, r"^\d{4}-\d\d-\d\dT\d\d:\d\dZ ")


class StreamingTests(ServerCase):
    config = {"ping_interval": 0.02, "slow_step": 0.03}

    def test_slow_trigger_sends_pings_while_idle(self):
        short = {"n": 1, "id": "c1", "title": "T", "url": "/x/", "text": "Attestation proves which code loaded."}
        status, h, data = self.request("POST", "/v1/chat", chat_request("slow: what does attestation prove?", chunks=[short]))
        self.assertEqual(status, 200)
        evs = events_of(data)
        pings = [i for i, e in enumerate(evs) if e == {"comment": "ping"}]
        self.assertGreaterEqual(len(pings), 3)
        first_delta = next(i for i, e in enumerate(evs) if e.get("event") == "delta")
        self.assertTrue(any(i > 2 for i in pings if i < first_delta), "pings while waiting for the first token")
        self.assertEqual(evs[-1]["event"], "done")

    def test_client_disconnect_mid_stream(self):
        body = json.dumps(chat_request("slow answer please")).encode("utf-8")
        s = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        s.sendall(b"POST /v1/chat HTTP/1.1\r\nHost: x\r\nContent-Type: application/json\r\n"
                  b"Content-Length: " + str(len(body)).encode() + b"\r\n\r\n" + body)
        self.assertIn(b"200", s.recv(64))
        s.close()
        deadline = time.time() + 5
        while "client-gone" not in self.log.getvalue() and time.time() < deadline:
            time.sleep(0.05)
        self.assertIn("client-gone", self.log.getvalue())
        status, _, _ = self.request("GET", "/v1/meta")
        self.assertEqual(status, 200)


class RateLimitTests(ServerCase):
    config = {"rate": 2}

    def test_token_bucket(self):
        if 86400 - time.time() % 86400 < 450:
            self.skipTest("the limiter resets at UTC midnight, which the clock offsets below would cross")
        status, _, data = self.request("GET", "/v1/meta")
        self.assertEqual(self.json_of(data)["limits"]["requests_per_10min"], 2)
        for _ in range(2):
            status, h, _ = self.request("POST", "/v1/chat", chat_request())
            self.assertEqual(status, 200)
        status, h, data = self.request("POST", "/v1/chat", chat_request())
        body = self.assertApiError(status, data, 429, "rate_limited")
        retry = int(h["retry-after"])
        self.assertGreaterEqual(retry, 1)
        self.assertLessEqual(retry, 300)
        self.assertEqual(body["error"]["retry_after_s"], retry)
        self.assertEqual(h["ratelimit-policy"], '"chat";q=2;w=600')
        self.assertTrue(h["ratelimit"].startswith('"chat";r=0;t='))
        self.assertEqual(h["access-control-allow-origin"], ALLOWED)
        # Tokens refill at rate/600 per second: one minute later... still under one token (2/600*60 = 0.2).
        self.clock.offset = 60
        status, _, _ = self.request("POST", "/v1/chat", chat_request())
        self.assertEqual(status, 429)
        self.clock.offset = 400
        status, _, _ = self.request("POST", "/v1/chat", chat_request())
        self.assertEqual(status, 200)

    def test_limiter_keeps_only_hmac_keys(self):
        for k in self.app.limiter.buckets:
            self.assertRegex(k, r"^[0-9a-f]{32}$")
            self.assertNotIn("127.0.0", k)


class DailyCapTests(ServerCase):
    config = {"daily_cap": 1}

    def test_daily_cap(self):
        status, _, _ = self.request("POST", "/v1/chat", chat_request())
        self.assertEqual(status, 200)
        status, h, data = self.request("POST", "/v1/chat", chat_request())
        self.assertApiError(status, data, 429, "rate_limited")
        self.assertGreaterEqual(int(h["retry-after"]), 1)


# ------------------------------------------------ OpenAI-compatible passthrough

class FakeUpstreamHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.server.seen.append({"path": self.path, "headers": {k.lower(): v for k, v in self.headers.items()},
                                 "body": body})
        if self.server.fail_status:
            self.send_response(self.server.fail_status)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        frames = [{"choices": [{"delta": {"role": "assistant"}, "finish_reason": None}]}]
        frames += [{"choices": [{"delta": {"content": p}, "finish_reason": None}]} for p in self.server.pieces]
        frames += [{"choices": [{"delta": {}, "finish_reason": self.server.finish}]}]
        for f in frames:
            self.wfile.write(("data: %s\n\n" % json.dumps(f)).encode())
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")


class PassthroughTests(ServerCase):
    @classmethod
    def setUpClass(cls):
        cls.upstream = ThreadingHTTPServer(("127.0.0.1", 0), FakeUpstreamHandler)
        cls.upstream.seen, cls.upstream.fail_status, cls.upstream.finish = [], None, "stop"
        cls.upstream.pieces = ["Attestation shows ", "which software loaded", " [1]."]
        threading.Thread(target=cls.upstream.serve_forever, daemon=True).start()
        cls.config = {"openai_base": "http://127.0.0.1:%d/v1/" % cls.upstream.server_address[1],
                      "model": "fake-model", "api_key": "test-key-not-secret"}
        ServerCase.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        ServerCase.tearDownClass.__func__(cls)
        cls.upstream.shutdown()
        cls.upstream.server_close()

    def setUp(self):
        ServerCase.setUp(self)
        self.upstream.seen[:] = []
        self.upstream.fail_status = None
        self.upstream.finish = "stop"

    def test_meta_and_attestation_report_the_system_prompt(self):
        _, _, data = self.request("GET", "/v1/meta")
        meta = self.json_of(data)
        self.assertValid(meta, "Meta")
        self.assertEqual(meta["system_prompt_sha256"], hashlib.sha256(server.SYSTEM_PROMPT.encode()).hexdigest())
        self.assertEqual(meta["models"][0]["id"], "fake-model")
        self.assertEqual(meta["mode"], "mock")
        _, _, data = self.request("GET", "/v1/attestation?nonce=" + self.nonce())
        b = self.json_of(data)
        self.assertValid(b, "MockAttestationBundle")
        self.assertEqual(b["summary"]["system_prompt_sha256"], meta["system_prompt_sha256"])
        self.assertIn("forwarded in plaintext", b["summary"]["claims"]["basis"])

    def test_relays_upstream_tokens(self):
        req = chat_request("What does attestation prove?")
        status, h, data = self.request("POST", "/v1/chat", req)
        self.assertEqual(status, 200)
        evs = events_of(data)
        for e in evs:
            if "event" in e:
                self.assertValid(e["data"], EVENT_SCHEMAS[e["event"]])
        self.assertEqual(answer_of(evs), "Attestation shows which software loaded [1].")
        done = evs[-1]
        self.assertEqual(done["event"], "done")
        self.assertEqual(done["data"]["used_citations"], [1])
        self.assertEqual(done["data"]["finish_reason"], "stop")
        self.assertEqual(evs[1]["data"]["model"], "fake-model")

        seen = self.upstream.seen[0]
        self.assertEqual(seen["path"], "/v1/chat/completions")
        self.assertEqual(seen["headers"].get("authorization"), "Bearer test-key-not-secret")
        body = seen["body"]
        self.assertEqual((body["model"], body["stream"], body["max_tokens"]), ("fake-model", True, 700))
        self.assertEqual(body["messages"][0], {"role": "system", "content": server.SYSTEM_PROMPT})
        user = body["messages"][-1]
        self.assertEqual(user["role"], "user")
        c1 = req["context"]["chunks"][0]
        self.assertIn("[1] " + c1["title"], user["content"])
        self.assertIn(c1["text"].strip(), user["content"])
        self.assertIn("[3] ", user["content"])
        self.assertIn("Answer language: English", user["content"])
        self.assertTrue(user["content"].endswith("Question: What does attestation prove?"))

    def test_history_is_forwarded_and_length_is_reported(self):
        self.upstream.finish = "length"
        req = chat_request("And the GPU?")
        req["lang"] = "zh"
        req["messages"] = [{"role": "user", "content": "first"}, {"role": "assistant", "content": "answer [1]"},
                           {"role": "user", "content": "And the GPU?"}]
        status, _, data = self.request("POST", "/v1/chat", req)
        self.assertEqual(status, 200)
        self.assertEqual(events_of(data)[-1]["data"]["finish_reason"], "length")
        msgs = self.upstream.seen[0]["body"]["messages"]
        self.assertEqual([m["role"] for m in msgs], ["system", "user", "assistant", "user"])
        self.assertIn("Simplified Chinese", msgs[-1]["content"])

    def test_context_truncation_notice(self):
        req = chat_request()
        base = req["context"]["chunks"][0]
        req["context"]["chunks"] = [dict(base, n=i + 1, id="c%d" % i, text="word " * 1400) for i in range(8)]
        status, _, data = self.request("POST", "/v1/chat", req)
        self.assertEqual(status, 200)
        evs = events_of(data)
        notice = [e["data"] for e in evs if e.get("event") == "notice"]
        self.assertEqual(notice[0]["code"], "context_truncated")
        cites = [e["data"]["items"] for e in evs if e.get("event") == "citations"][0]
        self.assertLess(len(cites), 8)
        sent = self.upstream.seen[0]["body"]["messages"][-1]["content"]
        self.assertNotIn("[%d] " % (len(cites) + 1), sent)

    def test_upstream_http_error_becomes_error_event(self):
        self.upstream.fail_status = 500
        status, _, data = self.request("POST", "/v1/chat", chat_request())
        self.assertEqual(status, 200)
        evs = events_of(data)
        self.assertEqual(evs[-1]["event"], "error")
        self.assertEqual(evs[-1]["data"]["code"], "upstream_unavailable")
        self.assertIn("500", evs[-1]["data"]["message"])

    def test_unreachable_upstream(self):
        app = server.App(server.Config(port=0, step=0, quiet=True, model="m",
                                       openai_base="http://127.0.0.1:%d/v1" % free_port(), upstream_timeout=5))
        srv = server.make_server(app)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            conn = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=20)
            conn.request("POST", "/v1/chat", body=json.dumps(chat_request()), headers={"Content-Type": "application/json"})
            resp = conn.getresponse()
            evs = events_of(resp.read())
            conn.close()
        finally:
            srv.shutdown()
            srv.server_close()
        self.assertEqual(evs[-1]["event"], "error")
        self.assertEqual(evs[-1]["data"]["code"], "upstream_unavailable")
        self.assertNotIn("done", [e.get("event") for e in evs])


class CommandLineTests(unittest.TestCase):
    def test_flags_pair_and_validate(self):
        args = server.parse_args(["--port", "0", "--allow-origin", "https://verifiable.pro"])
        self.assertEqual(args.allow_origin, ["https://verifiable.pro"])
        for bad in (["--model", "x"], ["--openai-base", "ftp://x", "--model", "y"], ["--rate", "0"]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                server.parse_args(bad)

    def test_print_system_prompt(self):
        out = io.StringIO()
        old = sys.stdout
        sys.stdout = out
        try:
            self.assertEqual(server.main(["--print-system-prompt"]), 0)
        finally:
            sys.stdout = old
        self.assertIn(server.SYSTEM_PROMPT_SHA256, out.getvalue())


if __name__ == "__main__":
    unittest.main()
