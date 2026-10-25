/* verifiable.pro: site assistant ("Ask verifiable.pro" / "向 verifiable.pro 提问").
   Client for the chat API v1 (api/chat-v1.md, phase 0).

   - Progressive enhancement: launchers ship hidden; the panel is built on first open.
   - Retrieval happens in this browser for both transports: passages are picked from
     the site's own search-index.json, manifest.json and published .md sources and sent
     as context.chunks. The backend is "an attested language model and nothing more".
   - Two transports, one interface: "demo" (answers assembled in this browser; no
     network beyond same-origin static files) and "http" (GET /v1/meta,
     GET /v1/attestation?nonce, POST /v1/chat read as text/event-stream). There is never
     a silent fallback from http to demo; the reader is offered an explicit button.
   - The badge comes only from checks this browser ran (VerificationResult). Whatever
     the service says about itself is shown as "reported". Never a check mark.
   - No innerHTML anywhere: every node is built with the DOM API, and model output is
     parsed into text nodes and a small set of inline elements. */
(function () {
  "use strict";

  var cfgEl = document.getElementById("chat-config");
  if (!cfgEl || !window.fetch || !window.HTMLDialogElement || !window.AbortController ||
      !window.TextDecoder || !window.TextEncoder || !window.crypto || !crypto.getRandomValues) return;
  var cfg;
  try { cfg = JSON.parse(cfgEl.textContent); } catch (e) { return; }
  if (!cfg || typeof cfg !== "object" || cfg.mode === "off") return;

  var VERSION = "1.0.0";
  var MODE = cfg.mode === "live" ? "live" : "demo"; /* "mock" from older configs means demo */
  var API = String(cfg.api || "").replace(/\/+$/, "");
  var S = cfg.strings && typeof cfg.strings === "object" ? cfg.strings : {};
  var site = document.querySelector(".site") || document.body;
  var root = site.getAttribute("data-root") || "/";
  var lang = cfg.lang === "zh" || cfg.lang === "en" ? cfg.lang
    : /^zh/i.test(site.getAttribute("lang") || document.documentElement.lang || "") ? "zh" : "en";
  var page = cfg.page && typeof cfg.page === "object" ? cfg.page : { kind: "page", url: location.pathname };
  var isArticle = page.kind === "article" && !!page.slug && !!page.source;
  var FLOAT = cfg.launcher === "float";
  var KEY = "vp.chat.v1", MAX_MSGS = 40, IDLE_MS = 30000, CONNECT_MS = 10000, SITE_MS = 20000;
  var MAX_CHUNKS = 6, MAX_EARLIER = 8000, PASSAGE = 900;
  var DEFAULT_LIMITS = { max_question_chars: 1200, max_turns: 6, max_context_chunks: 8, max_output_tokens: 700, max_body_bytes: 262144 };
  var HEX64 = /^[0-9a-f]{64}$/;
  var CODES = ["rate_limited", "attestation_expired", "attestation_mismatch", "bad_request", "too_long",
    "upstream_unavailable", "internal", "not_found", "method_not_allowed", "origin_not_allowed"];
  var dock = window.matchMedia("(min-width: 960px)");
  var coarse = window.matchMedia("(pointer: coarse)");

  /* ----- helpers ---------------------------------------------------------- */
  function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }
  function t(key, vars) {
    var s = has(S, key) ? String(S[key]) : key;
    if (vars) Object.keys(vars).forEach(function (k) { s = s.split("{" + k + "}").join(String(vars[k])); });
    return s;
  }
  /* A string whose {slots} may be DOM nodes, so labels stay text and digests stay <code>. */
  function tpl(key, vars) {
    var f = document.createDocumentFragment();
    (has(S, key) ? String(S[key]) : key).split(/(\{\w+\})/).forEach(function (part) {
      var m = /^\{(\w+)\}$/.exec(part);
      if (m && vars && has(vars, m[1])) {
        var v = vars[m[1]];
        f.appendChild(v && v.nodeType ? v : document.createTextNode(String(v)));
      } else if (part) f.appendChild(document.createTextNode(part));
    });
    return f;
  }
  /* Canonical site path -> link that works in prod (absolute) and preview (relative); as site.js. */
  function link(path) {
    if (root === "/") return path;
    var parts = path.split("#");
    var p = parts[0].replace(/^\//, "");
    if (p === "" || p.slice(-1) === "/") p += "index.html";
    return root + p + (parts[1] ? "#" + parts[1] : "");
  }
  /* A same-site path such as /articles/x/#y. Browsers read "/\host" and "/<TAB>/host" as
     "//host", so a backslash, whitespace or control character anywhere disqualifies it. */
  function internal(p) { return typeof p === "string" && /^\/(?![\/\\])[^\\\s\u0000-\u001f\u007f]*$/.test(p); }
  function site_url(path) { return internal(path) ? link(path) : path; }
  function h(tag, attrs, kids) {
    var n = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v == null || v === false) return;
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else n.setAttribute(k, v === true ? "" : String(v));
    });
    (kids || []).forEach(function (c) {
      if (c != null && c !== false) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return n;
  }
  function code(value, full) { return h("code", { title: full || null, text: value }); }
  var SVGNS = "http://www.w3.org/2000/svg";
  function svgIcon(shapes) {
    var s = document.createElementNS(SVGNS, "svg");
    s.setAttribute("viewBox", "0 0 20 20"); s.setAttribute("width", "18"); s.setAttribute("height", "18");
    s.setAttribute("aria-hidden", "true"); s.setAttribute("focusable", "false");
    shapes.forEach(function (d) {
      var n = document.createElementNS(SVGNS, d[0]);
      Object.keys(d[1]).forEach(function (k) { n.setAttribute(k, d[1][k]); });
      s.appendChild(n);
    });
    return s;
  }
  function askIcon() {
    return svgIcon([["path", { d: "M3 3.5h14v10H8.5L5 16.8V13.5H3z", fill: "none", stroke: "currentColor", "stroke-width": "1.5" }],
      ["rect", { "class": "chat-icon-seal", x: "11.5", y: "8", width: "3.5", height: "3.5" }]]);
  }
  function hex(bytes) {
    var a = new Uint8Array(bytes), out = "";
    for (var i = 0; i < a.length; i++) out += (a[i] < 16 ? "0" : "") + a[i].toString(16);
    return out;
  }
  function randomHex(n) { var a = new Uint8Array(n); crypto.getRandomValues(a); return hex(a); }
  /* SHA-256 with WebCrypto; null where it is unavailable (file://, plain http on a LAN address). */
  function sha256(data) {
    if (!crypto.subtle || window.isSecureContext === false) return Promise.resolve(null);
    var bytes = typeof data === "string" ? new TextEncoder().encode(data) : data;
    return crypto.subtle.digest("SHA-256", bytes).then(hex, function () { return null; });
  }
  function short(d, n) { return d ? String(d).slice(0, n || 12) + "…" : ""; }
  function str(v) { return typeof v === "string" ? v : ""; }
  function obj(v) { return v && typeof v === "object" && !Array.isArray(v) ? v : null; }
  function clock(iso) {
    var d = iso ? new Date(iso) : new Date();
    if (isNaN(d)) return "";
    var p = function (n) { return (n < 10 ? "0" : "") + n; };
    return p(d.getUTCHours()) + ":" + p(d.getUTCMinutes()) + " UTC";
  }
  function dur(sec) {
    sec = Math.max(0, Math.ceil(sec));
    return sec < 120 ? t("chat_dur_s", { n: sec }) : t("chat_dur_min", { n: Math.ceil(sec / 60) });
  }
  function fail(code, message, extra) {
    var e = new Error(message || code);
    e.code = code;
    if (extra) Object.keys(extra).forEach(function (k) { e[k] = extra[k]; });
    return e;
  }
  function hostOf(u) { try { return new URL(u, location.href).host; } catch (e) { return u; } }
  function nowIso() { return new Date().toISOString().replace(/\.\d+Z$/, "Z"); }

  /* ----- persistence (sessionStorage; never required) --------------------- */
  function load() {
    try {
      var s = JSON.parse(sessionStorage.getItem(KEY) || "null");
      if (s && s.v === 1 && Array.isArray(s.messages)) return s;
    } catch (e) { /* private mode, blocked storage, corrupt JSON */ }
    return null;
  }
  function fresh() {
    return { v: 1, nonce: randomHex(32), mode: MODE, api: API, transport: MODE === "live" ? "http" : "demo",
             fallback: false, open: false, draft: "", rateUntil: 0, messages: [] };
  }
  var state = load();
  if (!state || state.mode !== MODE || state.api !== API) state = fresh(); /* a mode change resets */
  if (!HEX64.test(state.nonce || "")) state.nonce = randomHex(32);
  if (MODE !== "live") { state.transport = "demo"; state.fallback = false; }
  state.messages.forEach(function (m) { if (m.status === "streaming") m.status = "interrupted"; });
  var saveTimer = 0;
  function save(now) {
    clearTimeout(saveTimer);
    /* Only the stored copy is trimmed: the conversation in memory stays whole, so earlier
       turns are still sent and Copy and Retry keep working when storage is blocked or full. */
    var run = function () {
      var msgs = state.messages.slice(-MAX_MSGS);
      for (var tries = 0; tries < 4; tries++) {
        try { sessionStorage.setItem(KEY, JSON.stringify(Object.assign({}, state, { messages: msgs }))); return; } catch (e) {
          var quota = e && (e.name === "QuotaExceededError" || e.name === "NS_ERROR_DOM_QUOTA_REACHED" || e.code === 22);
          if (!quota || msgs.length <= 2) return; /* blocked storage (SecurityError): keep going without it */
          msgs = msgs.slice(Math.ceil(msgs.length / 2)); /* quota: store without the oldest half */
        }
      }
    };
    if (now) run(); else saveTimer = setTimeout(run, 400);
  }

  /* ----- the site's own published data ------------------------------------ */
  /* A same-origin static file, read as "json" or "arrayBuffer"; gives up after SITE_MS so a
     stalled request cannot leave the widget waiting for ever. */
  function siteFetch(u, as) {
    var c = new AbortController(), timer = setTimeout(function () { c.abort(); }, SITE_MS);
    return fetch(u, { credentials: "same-origin", signal: c.signal }).then(function (r) {
      if (!r.ok) throw fail("http_" + r.status);
      return r[as]();
    }).then(function (v) { clearTimeout(timer); return v; }, function (e) { clearTimeout(timer); throw e; });
  }
  var cache = {};
  function getJSON(u) {
    if (!cache[u]) {
      cache[u] = siteFetch(u, "json");
      cache[u].catch(function () { delete cache[u]; });
    }
    return cache[u];
  }
  function manifest() {
    return getJSON(site_url(cfg.manifest || "/manifest.json")).then(function (m) {
      if (m.__map) return m.__map;
      var byPage = {}, bySource = {};
      (m.entries || []).forEach(function (e) { if (e.page) byPage[e.page] = e; if (e.source) bySource[e.source] = e; });
      m.__map = { digest: HEX64.test(m.digest || "") ? m.digest : null, byPage: byPage, bySource: bySource };
      return m.__map;
    });
  }
  function buildDigest() { return HEX64.test(cfg.build || "") ? cfg.build : null; }

  var docs = {};   /* source path -> Promise<doc> */
  var hashed = {}; /* source path -> sha256 this browser computed */
  function loadDoc(entry) {
    var key = entry.source;
    if (!docs[key]) {
      docs[key] = siteFetch(site_url(key), "arrayBuffer").then(function (buf) {
        return sha256(buf).then(function (d) {
          if (d) hashed[key] = d;
          return parseDoc(new TextDecoder("utf-8", { ignoreBOM: true }).decode(buf), entry);
        });
      });
      docs[key].catch(function () { delete docs[key]; });
    }
    return docs[key];
  }

  /* ----- passages from a published Markdown source ------------------------
     Offsets are JavaScript string indices (UTF-16 code units) into the decoded
     source, so source.slice(start, end) === text, as the contract requires. Heading
     anchors follow sitegen/md.py: slugify() plus -2, -3 for repeats, or {#id}. */
  var HEADING = /^(#{1,4})\s+(.+?)\s*#*$/, CALLOUT = /^:::\s*([A-Za-z][\w-]*)\s*(.*)$/, FENCE = /^(```|~~~)/;
  var NONWORD;
  try { NONWORD = new RegExp("[^\\p{L}\\p{N}_\\s-]", "gu"); } catch (e) { NONWORD = /[^\w㐀-鿿\s-]/g; }
  function slugify(text) {
    text = text.replace(/<[^>]+>/g, "").toLowerCase().replace(NONWORD, "").trim();
    return text.replace(/[\s_]+/g, "-") || "section";
  }
  function plainInline(s) {
    return s.replace(/\[\^[^\]]*\]/g, "").replace(/!?\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/\*\*|__|`/g, "").trim();
  }
  function parseDoc(text, entry) {
    var doc = { entry: entry, text: text, passages: [], sources: null };
    var slug = ((entry.page || "").match(/\/articles\/([^/]+)\//) || [])[1] || null;
    doc.slug = slug;
    var fm = /^---\r?\n([\s\S]*?)\r?\n---[ \t]*(?:\r?\n|$)/.exec(text);
    var pos = 0;
    if (fm) {
      pos = fm[0].length;
      var fmStart = fm[0].indexOf("\n") + 1;
      var sm = /^sources:[ \t]*\r?\n((?:[ \t]+-[^\n]*(?:\n|$))+)/m.exec(fm[1]);
      if (sm) {
        var s0 = fmStart + sm.index + sm[0].length - sm[1].length;
        var body = sm[1].replace(/\s+$/, "");
        doc.sources = { start: s0, end: s0 + body.length, text: body };
      }
    }
    var ids = {}, heading = null, anchor = null, callout = null, fence = false, gap = false, block = [], units = [];
    var flush = function () {
      if (block.length) units.push({ start: block[0][0], end: block[block.length - 1][1], heading: heading, anchor: anchor,
        callout: callout && callout.kind, ctitle: callout && callout.title, gap: gap });
      block = []; gap = false;
    };
    var i = pos, L = text.length;
    while (i <= L) {
      var nl = text.indexOf("\n", i);
      if (nl < 0) nl = L;
      var line = text.slice(i, nl).replace(/\r$/, ""), s = line.trim(), end = i + line.length, m;
      if (fence) { if (FENCE.test(s)) fence = false; }
      else if (FENCE.test(s)) { flush(); fence = true; gap = true; }
      else if (!s) flush();
      else if ((m = HEADING.exec(s))) {
        flush();
        var label = m[2], explicit = /^(.*?)\s*\{#([A-Za-z][\w-]*)\}$/.exec(label), id;
        if (explicit) { label = explicit[1]; id = explicit[2]; }
        else {
          var base = slugify(label), n = 2;
          id = base;
          while (ids[id]) id = base + "-" + n++;
        }
        ids[id] = 1;
        heading = plainInline(label); anchor = id; callout = null;
      } else if (/^:::\s*$/.test(s)) { flush(); callout = null; }
      else if ((m = CALLOUT.exec(s))) { flush(); callout = { kind: m[1], title: plainInline(m[2] || "") || null }; }
      else if (s.charAt(0) === "|" || s.charAt(0) === "<") { flush(); gap = true; }
      else block.push([i + (line.length - line.replace(/^\s+/, "").length), end]);
      if (nl >= L) break;
      i = nl + 1;
    }
    flush();
    var seq = {}, cap = entry.lang === "zh" ? PASSAGE / 2 : PASSAGE; /* CJK carries about twice the content per character */
    units.forEach(function (u) {
      var last = doc.passages[doc.passages.length - 1];
      if (last && !u.gap && last.anchor === u.anchor && last.callout === u.callout && u.end - last.start <= cap) { last.end = u.end; return; }
      doc.passages.push({ start: u.start, end: u.end, heading: u.heading, anchor: u.anchor, callout: u.callout, ctitle: u.ctitle });
    });
    doc.passages.forEach(function (p) {
      var k = p.anchor || "intro";
      p.k = seq[k] = has(seq, k) ? seq[k] + 1 : 0;
      p.text = text.slice(p.start, p.end);
    });
    return doc;
  }
  function passageChunk(doc, p) {
    var e = doc.entry;
    var heading = p.callout ? p.ctitle || (has(S, "chat_callout_" + p.callout) ? t("chat_callout_" + p.callout) : p.heading) : p.heading;
    return { id: (doc.slug || "page") + "/" + (e.lang || lang) + "#" + (p.anchor || "intro") + "/" + p.k,
             slug: doc.slug, lang: e.lang === "zh" || e.lang === "en" ? e.lang : null, kind: e.kind || null,
             title: e.title || "", heading: heading || null,
             url: (e.page || "/") + (p.anchor ? "#" + p.anchor : ""), source: e.source, source_sha256: HEX64.test(e.sha256 || "") ? e.sha256 : null,
             start: p.start, end: p.end, text: p.text, callout: p.callout || null };
  }
  function sourcesChunk(doc) {
    var e = doc.entry, s = doc.sources;
    return { id: (doc.slug || "page") + "/" + (e.lang || lang) + "#sources/0", slug: doc.slug, lang: e.lang || null, kind: e.kind || null,
             title: e.title || "", heading: t("chat_sources_heading"), url: (e.page || "/") + "#sources",
             source: e.source, source_sha256: HEX64.test(e.sha256 || "") ? e.sha256 : null,
             start: s.start, end: s.end, text: s.text, callout: "sources" };
  }

  /* ----- retrieval over the site index ------------------------------------ */
  var STOP = ["what", "is", "the", "a", "an", "of", "to", "how", "does", "do", "and", "or", "in", "on", "for", "about",
    "this", "that", "are", "can", "why", "which", "with", "me", "tell", "explain", "it", "its", "be", "i", "you",
    "was", "were", "has", "have", "should", "would", "there", "their", "from", "into", "than", "then", "when", "who",
    "say", "says", "said", "article", "articles", "page", "pages", "piece", "story", "site", "any", "some", "if", "we", "our"];
  function terms(q) {
    var s = q.toLowerCase();
    var out = (s.match(/[a-z0-9][a-z0-9.+-]*/g) || []).map(function (w) { return w.replace(/[.+-]+$/, ""); })
      .filter(function (w) { return w.length > 1 && STOP.indexOf(w) < 0; });
    (s.match(/[㐀-鿿]+/g) || []).forEach(function (run) {
      run.replace(/[的了是吗呢么什怎如何为这那本请文篇哪些能可以]/g, " ").split(/\s+/).forEach(function (r) {
        if (r.length === 1) out.push(r);
        for (var i = 0; i + 1 < r.length; i++) out.push(r.slice(i, i + 2)); /* CJK bigrams */
      });
    });
    return out.filter(function (w, i) { return w && out.indexOf(w) === i; }).map(matcher);
  }
  /* Latin words match at a word start with a few letters of inflection ("attest" finds
     "attestation", "tee" does not find "committee"); CJK bigrams match as substrings. */
  function matcher(w) {
    if (/[\u3400-\u9fff]/.test(w)) return { w: w, test: function (s) { return s.indexOf(w) >= 0; } };
    var stem = w.length > 5 ? w.replace(/(ations?|ings?|ions?|ies|ied|ers?|es|ed|s|e|y)$/, "") : w.replace(/(es|s)$/, "");
    if (stem.length < 3) stem = w;
    var re = new RegExp("(^|[^a-z0-9])" + stem.replace(/[.+-]/g, "\\$&") + "[a-z]{0," + (stem.length >= 6 ? 5 : Math.max(2, w.length - stem.length + 3)) + "}(?![a-z])");
    return { w: w, test: function (s) { return re.test(s); } };
  }
  function score(ts, text, head) {
    if (!ts.length) return 0;
    var low = (text || "").toLowerCase(), hl = (head || "").toLowerCase(), hit = 0, sc = 0;
    ts.forEach(function (m) {
      var a = m.test(low), b = !!hl && m.test(hl);
      if (a || b) hit++;
      sc += (a ? 1 : 0) + (b ? 3 : 0);
    });
    if (!hit || hit < Math.min(2, ts.length) * 0.5) return 0;
    return sc * hit / ts.length;
  }
  function rank(ts, index) {
    return index.map(function (e) {
      if (!e || e.type === "resource" || !e.path) return null; /* the assistant cites site pages only */
      var sc = score(ts, e.text, e.title);
      if (!sc) return null;
      return { e: e, score: e.type === "term" ? sc * 1.4 : sc };
    }).filter(Boolean).sort(function (a, b) { return b.score - a.score; });
  }
  function dataChunk(hit, man, file) {
    var src = "/data/" + file + ".json", entry = man.bySource[src];
    var anchor = (hit.e.path.split("#")[1] || slugify(hit.e.title));
    return { id: file + "/" + lang + "#" + anchor + "/0", slug: null, lang: lang, kind: hit.e.type, title: hit.e.title, heading: null,
             url: hit.e.path, source: entry ? src : null, source_sha256: entry && HEX64.test(entry.sha256 || "") ? entry.sha256 : null,
             start: null, end: null, text: hit.e.text || "" };
  }
  function indexChunk(hit, entry) {
    var slug = (hit.e.path.match(/\/articles\/([^/]+)\//) || [])[1] || null;
    return { id: (slug || "page") + "/" + lang + "#summary/0", slug: slug, lang: lang, kind: entry ? entry.kind : null, title: hit.e.title,
             heading: null, url: hit.e.path, source: entry ? entry.source : null,
             source_sha256: entry && HEX64.test(entry.sha256 || "") ? entry.sha256 : null, start: null, end: null, text: hit.e.text || "" };
  }
  function pageEntry(man) {
    return man.byPage[page.url] || { source: page.source, page: page.url, sha256: page.sha256, title: page.title, lang: lang, kind: page.article_kind || null };
  }
  /* -> Promise<{chunks, manifest_digest, intent, found}> */
  function retrieve(q, intent) {
    return manifest().then(function (man) {
      var cap = Math.max(0, Math.min(limits().max_context_chunks, MAX_CHUNKS));
      var done = function (list, extra) {
        var chunks = list.filter(Boolean).slice(0, cap);
        chunks.forEach(function (c, i) { c.n = i + 1; });
        var out = { chunks: chunks, manifest_digest: man.digest || buildDigest(), intent: null, found: null };
        if (extra) Object.keys(extra).forEach(function (k) { out[k] = extra[k]; });
        return out;
      };
      if (intent && isArticle) {
        return loadDoc(pageEntry(man)).then(function (doc) {
          var ps = doc.passages, pick = [], found = intent;
          var intro = ps.filter(function (p) { return !p.anchor && !p.callout; })[0] || ps[0];
          var analysis = ps.filter(function (p) { return p.callout === "analysis"; });
          if (intent === "summary") pick = [intro, analysis[0]];
          else if (intent === "limits") {
            var lim = ps.filter(function (p) { return p.callout === "limits"; });
            var open = ps.filter(function (p) { return !p.callout && p.heading && /leave|open|limit|not show|does not|cannot|caveat|gap|局限|不能|无法|未能|尚未|留下/i.test(p.heading); });
            if (lim.length) pick = lim;
            else if (analysis.length) { pick = analysis.slice(0, 2); found = "analysis"; }
            else if (open.length) { pick = open.slice(0, 2); found = "section"; }
            else { pick = [intro]; found = "none"; }
          } else if (intent === "sources") {
            /* zh sources carry only title and dek; the source list lives in the English front matter */
            var en = !doc.sources && doc.slug ? man.bySource["/articles/" + doc.slug + "/en.md"] : null;
            return (en ? loadDoc(en) : Promise.resolve(doc)).then(function (d) {
              return done(d.sources ? [sourcesChunk(d)] : [passageChunk(doc, intro)], { intent: intent, found: d.sources ? "sources" : "none" });
            });
          }
          return done(pick.filter(Boolean).map(function (p) { return passageChunk(doc, p); }), { intent: intent, found: found });
        });
      }
      return getJSON(site_url(cfg.index || (lang === "zh" ? "/zh/search-index.json" : "/search-index.json"))).then(function (index) {
        var ts = terms(q), hits = rank(ts, Array.isArray(index) ? index : []);
        var aboutPage = isArticle && /\bthis (article|page|piece|story|guide|explainer)\b|这篇|本文/i.test(q);
        var term = hits.filter(function (x) { return x.e.type === "term"; })[0];
        var arts = hits.filter(function (x) { return x.e.type === "article" && man.byPage[x.e.path]; });
        if (aboutPage) arts = [{ e: { type: "article", path: page.url, title: page.title, text: "" }, here: true }]
          .concat(arts.filter(function (x) { return x.e.path !== page.url; }));
        arts = arts.slice(0, 3);
        var topic = arts.length < 2 ? hits.filter(function (x) { return x.e.type === "topic"; })[0] : null;
        return Promise.all(arts.map(function (a) {
          var entry = a.here ? pageEntry(man) : man.byPage[a.e.path];
          return loadDoc(entry).then(function (doc) {
            var ranked = doc.passages.map(function (p) { return { p: p, s: score(ts, plainInline(p.text), p.heading) }; })
              .filter(function (x) { return x.s > 0; }).sort(function (a2, b2) { return b2.s - a2.s; }).map(function (x) { return x.p; });
            if (!ranked.length || a.here) ranked = [doc.passages[0]].concat(ranked.filter(function (p) { return p !== doc.passages[0]; }));
            return ranked.slice(0, 2).filter(Boolean).map(function (p) { return passageChunk(doc, p); });
          }, function () { return [indexChunk(a, entry)]; });
        })).then(function (perArt) {
          /* most relevant first: the glossary definition, then one passage per article, then second passages */
          var list = term ? [dataChunk(term, man, "glossary")] : [];
          perArt.forEach(function (cs) { if (cs[0]) list.push(cs[0]); });
          perArt.forEach(function (cs) { if (cs[1]) list.push(cs[1]); });
          if (topic) list.push(dataChunk(topic, man, "topics"));
          return done(list);
        });
      });
    });
  }

  /* ----- demo transport: answers assembled in this browser ----------------- */
  function cleanText(s) {
    return s.split(/\n/).map(function (l) {
      return l.replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "").replace(/^\s*>\s?/, "").replace(/^#{1,6}\s+/, "");
    }).join(lang === "zh" ? "" : " ")
      .replace(/\[\^[^\]]*\]/g, "").replace(/!?\[([^\]]+)\]\([^)]*\)/g, "$1").replace(/\[\d+(?:\s*,\s*\d+)*\]/g, "")
      .replace(/\*\*|__|`/g, "").replace(/\s+/g, " ").trim();
  }
  function listItems(s) {
    var items = [], cur = null;
    s.split(/\n/).forEach(function (l) {
      if (/^\s*(?:[-*+]|\d+[.)])\s+/.test(l)) { cur = l; items.push(cur); }
      else if (cur && l.trim()) items[items.length - 1] += " " + l.trim();
      else if (l.trim()) { cur = null; items.push(l); }
    });
    return items.map(cleanText).filter(Boolean);
  }
  function sentences(s) {
    return cleanText(s).replace(/([.!?])\s+(?=[A-Z0-9“"(])/g, "$1\u0000").replace(/([。！？])/g, "$1\u0000").split("\u0000").map(function (x) { return x.trim(); }).filter(function (x) { return x.length > 1; });
  }
  function bestSentence(s, ts) {
    var list = sentences(s);
    if (!list.length) return "";
    var best = list[0], top = 0;
    list.forEach(function (x) { var sc = score(ts, x, ""); if (sc > top) { top = sc; best = x; } });
    var cjk = (best.match(/[㐀-鿿]/g) || []).length * 3 > best.length, max = cjk ? 160 : 300;
    if (best.length > max) {
      var cut = best.slice(0, max);
      if (!cjk && cut.indexOf(" ") > 0) cut = cut.slice(0, cut.lastIndexOf(" "));
      best = cut.replace(/[ ,;:，；：、]+$/, "") + "…";
    }
    return best;
  }
  function demoAnswer(q, chunks) {
    if (!chunks.length) return t("chat_demo_none", { q: q.slice(0, 80) });
    var ts = terms(q), out = [t("chat_demo_lead")], zh = lang === "zh", colon = zh ? "：" : ": ";
    var term = chunks.filter(function (c) { return c.kind === "term"; })[0];
    if (term) out.push("**" + term.title + "**" + colon + cleanText(term.text) + " [" + term.n + "]");
    var rows = chunks.filter(function (c) { return c !== term; }).slice(0, 4).map(function (c) {
      var label = "**" + c.title + "**" + (c.heading && c.heading !== c.title ? (zh ? "（" + c.heading + "）" : " (" + c.heading + ")") : "");
      return "- " + label + colon + bestSentence(c.text, ts) + " [" + c.n + "]";
    });
    if (rows.length) out.push(t("chat_demo_cover") + "\n" + rows.join("\n"));
    return out.join("\n\n");
  }
  function demoArticle(ret) {
    var cs = ret.chunks, first = cs[0];
    if (!first) return t("chat_demo_article_empty");
    if (ret.intent === "sources") {
      if (ret.found !== "sources") return t("chat_demo_no_sources") + " [1]";
      var rows = first.text.split(/\n/).map(function (l) {
        var f = l.replace(/^\s*-\s*/, "").split(/\s+\|\s+/), title = f[0].replace(/[\[\]*`]/g, "");
        var head = f[3] && /^https:\/\/[^\s()]+$/.test(f[3]) ? "[" + title + "](" + f[3] + ")" : title;
        return "- " + head + [f[1], f[2]].filter(Boolean).map(function (x) { return (lang === "zh" ? "，" : ", ") + x; }).join("");
      });
      return t("chat_demo_sources", { n: rows.length }) + "\n" + rows.join("\n");
    }
    if (ret.intent === "limits") {
      var lead = ret.found === "limits" ? t("chat_demo_limits") : ret.found === "analysis" ? t("chat_demo_limits_analysis")
        : ret.found === "section" ? t("chat_demo_limits_section", { h: first.heading || "" }) : t("chat_demo_no_limits");
      if (ret.found === "none") return lead + " [1]";
      var items = [];
      cs.forEach(function (c) { listItems(c.text).forEach(function (x) { items.push("- " + x + " [" + c.n + "]"); }); });
      return lead + "\n" + items.slice(0, 6).join("\n");
    }
    var parts = [cleanText(first.text.split(/\n\s*\n/)[0]) + " [" + first.n + "]"];
    if (cs[1]) parts.push("**" + t("chat_demo_why") + "** " + cleanText(cs[1].text) + " [" + cs[1].n + "]");
    return parts.join("\n\n");
  }
  function usedCites(text, chunks) {
    var known = {}, out = [], m, re = /\[(\d+(?:\s*,\s*\d+)*)\]/g;
    chunks.forEach(function (c) { known[c.n] = true; });
    while ((m = re.exec(text))) m[1].split(/\s*,\s*/).forEach(function (n) { n = +n; if (known[n] && out.indexOf(n) < 0) out.push(n); });
    return out;
  }
  function citationOf(c) {
    return { n: c.n, chunk_id: c.id, title: c.title, heading: c.heading, url: c.url, lang: c.lang, source: c.source,
             source_sha256: c.source_sha256, start: c.start, end: c.end, context_verified: false };
  }

  function DemoTransport() { this.kind = "demo"; }
  DemoTransport.prototype.connect = function () {
    return Promise.resolve({ meta: { api_version: "1", mode: "mock", backend: { id: "demo-browser", label: t("chat_demo_backend") },
                                     encryption: "none", attestation_required: false, limits: DEFAULT_LIMITS }, bundle: null });
  };
  DemoTransport.prototype.chat = function (req, ret, conn, on, signal) {
    var q = req.messages[req.messages.length - 1].content;
    var text = ret.intent ? demoArticle(ret) : demoAnswer(q, req.context.chunks);
    on("meta", { request_id: "demo_" + randomHex(8), backend: "demo-browser", mode: "mock", model: "demo-template",
                 attestation_id: null, keyset_digest: null, started_at: nowIso() });
    on("citations", { items: req.context.chunks.map(citationOf) });
    var pieces = text.match(/[㐀-鿿　-〿＀-￯]{1,3}|[^\s㐀-鿿　-〿＀-￯]+\s*|\s+/g) || [];
    return new Promise(function (resolve, reject) {
      var i = 0, n = 0;
      (function tick() {
        if (signal.aborted) { reject(fail("aborted")); return; }
        if (i >= pieces.length) {
          on("done", { finish_reason: "stop", used_citations: usedCites(text, req.context.chunks), usage: null, receipt: null });
          resolve(); return;
        }
        on("delta", { i: n++, text: pieces.slice(i, i + 2).join("") });
        i += 2;
        setTimeout(tick, 22);
      })();
    });
  };

  /* ----- http transport: chat API v1 -------------------------------------- */
  function parseRetry(header, body) {
    if (header) {
      var n = parseInt(header, 10);
      if (/^\s*\d+\s*$/.test(header) && n >= 0) return n;
      var d = Date.parse(header);
      if (!isNaN(d)) return Math.max(0, Math.ceil((d - Date.now()) / 1000));
    }
    return typeof body === "number" && body >= 0 ? Math.ceil(body) : null;
  }
  function codeFor(status) {
    return { 400: "bad_request", 409: "attestation_expired", 411: "bad_request", 412: "attestation_mismatch", 413: "too_long",
             429: "rate_limited", 502: "upstream_unavailable", 503: "upstream_unavailable", 504: "upstream_unavailable" }[status] || "internal";
  }
  function httpError(r) {
    return r.json().catch(function () { return null; }).then(function (body) {
      var e = body && body.error && typeof body.error === "object" ? body.error : {};
      var c = CODES.indexOf(e.code) >= 0 ? e.code : codeFor(r.status);
      throw fail(c, str(e.message) || "HTTP " + r.status, { status: r.status, retryAfter: parseRetry(r.headers.get("Retry-After"), e.retry_after_s) });
    });
  }
  function HttpTransport(base) { this.kind = "http"; this.base = base; }
  HttpTransport.prototype.get = function (path, signal) {
    return fetch(this.base + path, { credentials: "omit", cache: "no-store", signal: signal, headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : httpError(r); });
  };
  HttpTransport.prototype.connect = function (nonce, signal) {
    var self = this;
    return self.get("/v1/meta", signal).then(function (meta) {
      if (!meta || meta.api_version !== "1") throw fail("format");
      return self.get("/v1/attestation?nonce=" + nonce, signal).then(function (bundle) { return { meta: meta, bundle: bundle }; });
    });
  };
  HttpTransport.prototype.chat = function (req, ret, conn, on, signal, tick) {
    var headers = { "Content-Type": "application/json", Accept: "text/event-stream" };
    var b = conn && conn.bundle;
    if (b && /^[\x21-\x7e]{1,200}$/.test(str(b.attestation_id))) headers["VP-Attestation-Id"] = b.attestation_id;
    if (b && HEX64.test(str(b.keyset_digest))) headers["VP-Keyset-Digest"] = b.keyset_digest;
    /* P1 hook: with meta.encryption "ehbp-v1" the body must be sealed with openEhbp(); judge() already
       refuses to send when it cannot, so here the body is always the phase-0 plaintext JSON. */
    return fetch(this.base + "/v1/chat", { method: "POST", credentials: "omit", cache: "no-store", signal: signal,
                                           headers: headers, body: JSON.stringify(req) }).then(function (r) {
      if (!r.ok) return httpError(r);
      if (!/^text\/event-stream/i.test(r.headers.get("Content-Type") || "") || !r.body) throw fail("format");
      return readSSE(r.body, on, tick);
    });
  };

  /* Server-sent events over fetch (EventSource cannot POST or send headers). Comment lines
     such as ": ping" are skipped but still count as activity for the idle timer. */
  function readSSE(body, on, tick) {
    var reader = body.getReader(), decoder = new TextDecoder(), buf = "";
    var dispatch = function (block) {
      var name = "message", data = [];
      block.split(/\r\n|\r|\n/).forEach(function (line) {
        if (!line || line.charAt(0) === ":") return;
        var i = line.indexOf(":");
        var field = i < 0 ? line : line.slice(0, i), value = i < 0 ? "" : line.slice(i + 1).replace(/^ /, "");
        if (field === "event") name = value;
        else if (field === "data") data.push(value);
      });
      if (!data.length) return null;
      var payload;
      try { payload = JSON.parse(data.join("\n")); } catch (e) { payload = null; }
      on(name, payload);
      return name;
    };
    var pump = function () {
      return reader.read().then(function (r) {
        if (tick) tick();
        buf += r.done ? decoder.decode() : decoder.decode(r.value, { stream: true });
        /* CRLF, LF and CR all end a line, in any mix ("\n\r\n" is a blank line too). A CR at
           the end of a chunk waits for the next one, which may start with its LF. */
        var hold = !r.done && buf.slice(-1) === "\r";
        if (hold) buf = buf.slice(0, -1);
        var blocks = buf.replace(/\r\n|\r/g, "\n").split("\n\n");
        buf = blocks.pop() + (hold ? "\r" : ""); /* an unterminated block at EOF is discarded, as EventSource does */
        for (var i = 0; i < blocks.length; i++) {
          if (dispatch(blocks[i]) === "done") { /* the answer is complete: do not wait for the server to close */
            try { reader.cancel().catch(function () { /* already closed */ }); } catch (x) { /* already closed */ }
            return undefined;
          }
        }
        return r.done ? undefined : pump();
      });
    };
    return pump().catch(function (e) {
      try { reader.cancel().catch(function () { /* already errored by the abort */ }); } catch (x) { /* already closed */ }
      throw e;
    });
  }

  /* ----- verification: only what this browser checked ----------------------
     Phase-0 code paths produce "demo" or "reported". The hooks below exist so later
     phases fill them in without changing the format (api/chat-v1.md, "Hooks left for
     later phases"). Until then each returns not_checked and the badge cannot rise. */
  function check(id, status, detail) { return { id: id, status: status, label: t("chat_check_" + id), detail: detail || "" }; }
  /* P2: verify bundle.evidence (tdx_quote | snp_report | gcp_cs_token) against vendor roots pinned
     in the site's static trust.json, then report_data[0:32] == keyset_digest and
     report_data[32:64] == nonce per bundle.binding.method. */
  function verifyCpuEvidence(bundle, nonce) {
    return [check("cpu_evidence_signature", "not_checked"), check("report_data_binding", "not_checked")];
  }
  /* P2: verify the NVIDIA NRAS EAT (JWT) and its x5c chain against the pinned NVIDIA root,
     gpu_nonce == sha256(nonce || keyset_digest), and that it states CC mode on. */
  function verifyGpuEat(bundle, nonce) {
    if (!bundle.summary || !bundle.summary.gpu) return [];
    return [check("gpu_nras_signature", "not_checked"), check("gpu_nonce_bound", "not_checked"), check("gpu_cc_on", "not_checked")];
  }
  /* P2: verify the Sigstore bundle of release.json and compare its expected image, model,
     system prompt and GPU policy digests with the attested measurement. */
  function verifyRelease(bundle) {
    return [check("release_sigstore", "not_checked"), check("measurement_matches_release", "not_checked"),
            check("model_digest_matches_release", "not_checked")];
  }
  /* P1: EHBP (HPKE base mode, RFC 9180: X25519, HKDF-SHA256, AES-256-GCM) to
     bundle.keyset.hpke.public_key; must fail when Ehbp-Response-Nonce is missing. Returns
     null until implemented, so a backend that requires encryption is never sent plaintext. */
  function openEhbp(meta, bundle) { return null; }
  /* P2: Ed25519 over the canonical vp-receipt/v1 string, with request and response hashes
     recomputed here; the key is trusted because keyset_digest is bound into the hardware report. */
  function verifyReceipt(receipt, bundle) { return { status: "not_checked" }; }

  /* -> VerificationResult (#/$defs/VerificationResult) plus display fields */
  function judge(meta, bundle, transportKind) {
    var res = { overall: "demo", checked_at: nowIso(), verifier: { name: "verifiable.pro chat widget", version: VERSION, script_sha256: null },
                checks: [], still_trusted: [t("chat_trust_page")], reason: "" };
    if (transportKind === "demo") { res.still_trusted = [t("chat_trust_page")]; return res; }
    res.still_trusted.push(t("chat_trust_operator"));
    if (!bundle || bundle.schema !== "verifiable.pro/attestation/v1" || typeof bundle.attestation_id !== "string") {
      res.overall = "failed"; res.reason = "format"; return res;
    }
    var sum = bundle.summary || {};
    var echo = bundle.nonce === state.nonce && (!sum.nonce || sum.nonce === state.nonce);
    var life = Date.parse(bundle.expires_at) - Date.parse(bundle.issued_at);
    var mock = meta.mode === "mock" || bundle.mode === "mock";
    res.checks.push(check("nonce_fresh", echo ? (mock ? "not_applicable" : "reported") : "failed"));
    if (!echo) { res.overall = "failed"; res.reason = "nonce"; return res; }
    if (!(life > 0)) { res.overall = "failed"; res.reason = "expired"; return res; }
    /* checked for mock backends too: a backend that asks for encryption is never sent plain text */
    var sealed = meta.encryption === "none" || !!openEhbp(meta, bundle);
    if (mock && !sealed) { res.overall = "failed"; res.reason = "encryption"; return res; }
    if (mock) return res; /* the contract: demo status for a mock backend, whatever else it sends */
    res.checks = res.checks.concat(verifyCpuEvidence(bundle, state.nonce), verifyGpuEat(bundle, state.nonce), verifyRelease(bundle),
                                   [check("tls_binding", "not_checked")]);
    if (!sealed) { res.overall = "failed"; res.reason = "encryption"; return res; }
    var applicable = res.checks.filter(function (c) { return c.status !== "not_applicable"; });
    var passed = applicable.filter(function (c) { return c.status === "verified_in_browser" || c.status === "verified_by_third_party"; });
    if (applicable.some(function (c) { return c.status === "failed"; })) { res.overall = "failed"; res.reason = "check"; }
    else if (applicable.length && passed.length === applicable.length) res.overall = "verified";
    else if (passed.length) res.overall = "partly_verified";
    else res.overall = "reported";
    return res;
  }
  function basisOf(res, id) {
    var c = res.checks.filter(function (x) { return x.id === id; })[0];
    return !c ? "service" : c.status === "verified_in_browser" ? "browser" : c.status === "verified_by_third_party" ? "verifier" : "service";
  }

  /* ----- markdown-lite to DOM (no innerHTML) ------------------------------ */
  var INLINE = /\*\*([^*\n]+)\*\*|`([^`\n]+)`|\[(\d+(?:\s*,\s*\d+)*)\]|\[([^\]\n]+)\]\(([^)\s]+)\)|\*([^*\s][^*\n]*)\*/g;
  function inline(parent, text, mid) {
    var last = 0, m;
    INLINE.lastIndex = 0;
    while ((m = INLINE.exec(text))) {
      if (m.index > last) parent.appendChild(document.createTextNode(text.slice(last, m.index)));
      if (m[1]) parent.appendChild(h("strong", { text: m[1] }));
      else if (m[2]) parent.appendChild(h("code", { text: m[2] }));
      else if (m[3]) {
        var sup = h("sup", { "class": "cite" }, ["["]);
        m[3].split(/\s*,\s*/).forEach(function (n, i) {
          if (i) sup.appendChild(document.createTextNode(", "));
          sup.appendChild(h("a", { "class": "cite-link", href: "#" + mid + "-src-" + n, "data-cite": mid + "-src-" + n,
                                   "aria-label": t("chat_source_n", { n: n }), text: n }));
        });
        sup.appendChild(document.createTextNode("]"));
        parent.appendChild(sup);
      } else if (m[4]) parent.appendChild(safeLink(m[4], m[5]));
      else if (m[6]) parent.appendChild(h("em", { text: m[6] }));
      last = INLINE.lastIndex;
    }
    if (last < text.length) parent.appendChild(document.createTextNode(text.slice(last)));
  }
  function safeLink(label, href) {
    if (internal(href)) return h("a", { href: link(href), text: label });
    var u;
    try { u = new URL(href); } catch (e) { return document.createTextNode(label); }
    if (u.protocol !== "https:") return document.createTextNode(label); /* javascript:, data:, http: stay text */
    var f = document.createDocumentFragment();
    f.appendChild(h("a", { "class": "ext", href: u.href, rel: "noopener noreferrer nofollow ugc", text: label }));
    f.appendChild(h("span", { "class": "chat-host", text: " (" + u.hostname + ")" }));
    return f;
  }
  function render(target, text, mid) {
    target.textContent = "";
    text.replace(/\r/g, "").split(/\n{2,}/).forEach(function (block) {
      var lines = block.split("\n").filter(function (l) { return l.trim(); });
      if (!lines.length) return;
      var bullet = /^\s*[-*•]\s+/, number = /^\s*\d+[.)]\s+/;
      if (lines.length > 1 && !bullet.test(lines[0]) && !number.test(lines[0]) && (bullet.test(lines[1]) || number.test(lines[1]))) {
        var lead = h("p");
        inline(lead, lines.shift(), mid);
        target.appendChild(lead);
      }
      if (lines.every(function (l) { return bullet.test(l); }) || lines.every(function (l) { return number.test(l); })) {
        var ordered = number.test(lines[0]), list = h(ordered ? "ol" : "ul");
        lines.forEach(function (l) { var li = h("li"); inline(li, l.replace(ordered ? number : bullet, ""), mid); list.appendChild(li); });
        target.appendChild(list);
      } else {
        var p = h("p"), heading = /^#{1,6}\s/.test(lines[0]);
        var joined = lines.join(lang === "zh" ? "" : " ").replace(/^#{1,6}\s+/, "");
        if (heading) p.appendChild(h("strong", { text: joined })); else inline(p, joined, mid);
        target.appendChild(p);
      }
    });
  }

  /* ----- UI state ----------------------------------------------------------- */
  var transport = state.transport === "http" ? (API ? new HttpTransport(API) : null) : new DemoTransport();
  var conn = { status: "idle" };   /* idle | pending | ready | unavailable | offline */
  var connSeq = 0, connecting = null;
  var busy = null;                  /* {controller, msg, stopped, timedOut} while an answer streams */
  var panel, log, form, input, sendBtn, statusEl, attBox, disc, floatBtn, opener = null;
  var launchers = Array.prototype.slice.call(document.querySelectorAll("[data-chat-open]"));
  function limits() {
    var l = conn.meta && conn.meta.limits && typeof conn.meta.limits === "object" ? conn.meta.limits : {};
    var out = {};
    Object.keys(DEFAULT_LIMITS).forEach(function (k) { out[k] = typeof l[k] === "number" && l[k] > 0 ? l[k] : DEFAULT_LIMITS[k]; });
    if (typeof l.max_context_chunks === "number" && l.max_context_chunks >= 0) out.max_context_chunks = l.max_context_chunks;
    return out;
  }
  function view() {
    if (conn.status !== "ready") return conn.status === "idle" ? "pending" : conn.status;
    return conn.result.overall;
  }
  function rateLeft() { return Math.max(0, ((state.rateUntil || 0) - Date.now()) / 1000); }
  function usable() { return conn.status === "ready" && /^(demo|reported|partly_verified|verified)$/.test(conn.result.overall); }
  function canAsk() {
    if (busy || !transport) return false;
    if (transport.kind === "http" && (navigator.onLine === false || rateLeft() > 0)) return false;
    return usable();
  }

  /* ----- launchers ------------------------------------------------------------ */
  function isMain(b) { return b.getAttribute("data-chat-open") !== "article"; }
  function bindLauncher(b) {
    if (!b.hasAttribute("data-chat-label")) b.setAttribute("data-chat-label", b.getAttribute("aria-label") || t("chat_launch_aria"));
    if (isMain(b)) b.setAttribute("aria-expanded", "false");
    b.addEventListener("click", function (e) {
      if (b.tagName === "A") e.preventDefault();
      if (panel && panel.open && isMain(b)) { close(); return; }
      opener = b;
      open({ focus: true, article: !isMain(b) && isArticle });
    });
  }
  launchers.forEach(function (b) {
    var header = b.classList.contains("chat-launch");
    if (FLOAT && header) return; /* float mode: the header button stays hidden */
    b.hidden = false;
    var wrap = b.closest("[data-chat-wrap]");
    if (wrap) wrap.hidden = false;
    bindLauncher(b);
  });
  launchers = launchers.filter(function (b) { return !b.hidden; });
  if (FLOAT) {
    floatBtn = h("button", { type: "button", "class": "chat-float", "data-chat-open": "", "aria-haspopup": "dialog",
                             "aria-label": t("chat_launch_aria") }, [askIcon()]);
    site.appendChild(floatBtn);
    bindLauncher(floatBtn);
    launchers.unshift(floatBtn);
    var foot = document.querySelector(".site-footer");
    if (foot && window.IntersectionObserver) {
      new IntersectionObserver(function (en) { floatBtn.classList.toggle("is-tucked", en[0].isIntersecting); }).observe(foot);
    }
  }
  function setLaunch(st) {
    launchers.forEach(function (b) {
      if (!isMain(b)) return;
      b.setAttribute("aria-expanded", panel && panel.open ? "true" : "false");
      if (st) b.setAttribute("data-state", st); else b.removeAttribute("data-state");
      var base = b.getAttribute("data-chat-label") || t("chat_launch_aria");
      b.setAttribute("aria-label", st === "unread" ? t("chat_launch_unread", { label: base }) : st === "busy" ? t("chat_launch_busy", { label: base }) : base);
    });
    if (floatBtn) floatBtn.classList.toggle("is-open", !!(panel && panel.open));
  }

  /* ----- panel ---------------------------------------------------------------- */
  function mount() {
    if (panel) return;
    input = h("textarea", { id: "chat-input", rows: "1", maxlength: String(DEFAULT_LIMITS.max_question_chars), autocomplete: "off",
                            enterkeyhint: "send", placeholder: t("chat_placeholder"), "aria-describedby": "chat-disclosure" });
    sendBtn = h("button", { type: "submit", "class": "chat-send", text: t("chat_send") });
    disc = h("p", { "class": "chat-disclosure", id: "chat-disclosure" });
    form = h("form", { "class": "chat-composer", novalidate: true }, [
      h("label", { "class": "chat-sr", "for": "chat-input", text: t("chat_input_label") }),
      h("div", { "class": "chat-input-row" }, [input, sendBtn]), disc]);
    attBox = h("section", { "class": "chat-att", "aria-label": t("chat_att_region") });
    log = h("div", { "class": "chat-log", role: "log", "aria-live": "off", "aria-label": t("chat_log_label"), tabindex: "0" });
    statusEl = h("p", { "class": "chat-sr", role: "status", id: "chat-status" });
    var closeBtn = h("button", { type: "button", "class": "chat-close", "data-act": "close", "aria-label": t("chat_close") },
      [svgIcon([["path", { d: "M5 5l10 10M15 5 5 15", stroke: "currentColor", "stroke-width": "1.6", "stroke-linecap": "square" }]])]);
    panel = h("dialog", { "class": "chat", id: "chat-panel", "aria-labelledby": "chat-title", "aria-describedby": "chat-att-line" }, [
      h("div", { "class": "chat-frame" }, [
        h("header", { "class": "chat-head" }, [
          h("h2", { id: "chat-title", "class": "chat-title", tabindex: "-1", text: t("chat_title") }),
          h("button", { type: "button", "class": "chat-text-btn", "data-act": "new", text: t("chat_new") }), closeBtn]),
        attBox, log, form, statusEl])]);
    site.appendChild(panel);
    launchers.forEach(function (b) { if (isMain(b)) b.setAttribute("aria-controls", "chat-panel"); });

    panel.addEventListener("click", function (e) {
      var b = e.target.closest("button");
      if (!b) { if (e.target === panel && isModal()) close(); return; } /* backdrop */
      var act = b.getAttribute("data-act");
      if (act === "close") close();
      else if (act === "new") reset();
      else if (act === "ask") ask(b.getAttribute("data-q"), b.getAttribute("data-intent"));
      else if (act === "copy") copy(b);
      else if (act === "retry") retry(b.getAttribute("data-id"));
      else if (act === "att") toggleAtt(b);
      else if (act === "demo") useDemo();
      else if (act === "live") useLive();
      else if (act === "reconnect") connect(true);
    });
    panel.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !isModal()) { e.preventDefault(); close(); }
    });
    panel.addEventListener("close", function () {
      if (panel.open) return; /* already reopened in the other placement (the viewport crossed 960px) */
      document.documentElement.classList.remove("chat-modal-open");
      state.open = false;
      save();
      setLaunch(busy ? "busy" : null);
      fitViewport();
      var back = opener && document.contains(opener) && !opener.hidden ? opener : launchers.filter(isMain)[0];
      if (back) back.focus();
    });
    form.addEventListener("submit", function (e) { e.preventDefault(); if (busy) stop(); else ask(input.value); });
    input.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" || e.shiftKey || e.isComposing || e.keyCode === 229) return; /* IME composition: pinyin */
      e.preventDefault();
      if (!busy) ask(input.value);
    });
    input.addEventListener("input", function () { grow(); state.draft = input.value; save(); });
    log.addEventListener("click", function (e) {
      var a = e.target.closest("a");
      if (!a) return;
      if (a.hasAttribute("data-cite")) { /* jump inside the log without touching location.hash */
        e.preventDefault();
        var li = document.getElementById(a.getAttribute("data-cite"));
        if (li) {
          li.tabIndex = -1; li.focus({ preventScroll: true }); li.scrollIntoView({ block: "nearest" });
          li.classList.add("is-hl"); setTimeout(function () { li.classList.remove("is-hl"); }, 2000);
        }
        return;
      }
      if (!dock.matches && (a.getAttribute("href") || "").charAt(0) !== "#") close(); /* leaving: drop the sheet */
    });
    window.addEventListener("online", function () { if (/^(offline|unavailable)$/.test(conn.status)) connect(true); else syncComposer(); });
    window.addEventListener("offline", function () { syncComposer(); paintAtt(); });
    input.value = state.draft || "";
    paintAtt();
    paintLog();
  }

  function open(o) {
    mount();
    var modal = !dock.matches;
    if (!panel.open) {
      var prev = document.activeElement;
      panel.classList.toggle("is-docked", !modal);
      if (modal) { panel.showModal(); document.documentElement.classList.add("chat-modal-open"); fitViewport(); }
      else { placeDock(); panel.show(); }
      /* show() runs the dialog focusing steps; a panel restored after navigation must not take focus */
      if (!(o && o.focus)) { if (prev && prev !== document.body && document.contains(prev)) prev.focus({ preventScroll: true }); else if (document.activeElement) document.activeElement.blur(); }
    }
    state.open = !modal; save();
    setLaunch(null);
    if (conn.status === "idle" || conn.status === "unavailable" || conn.status === "offline") connect(false);
    if (o && o.article && state.messages.length && !(log.lastElementChild && log.lastElementChild.classList.contains("chat-article"))) {
      log.appendChild(articleBlock()); /* mid-conversation: offer this page's questions at the end */
      scrollEnd();
    }
    grow();
    if (o && o.focus) (coarse.matches || input.disabled ? panel.querySelector("#chat-title") : input).focus();
    if (state.messages.length && !(o && o.article)) scrollEnd();
  }
  function close() { if (panel && panel.open) panel.close(); }
  function isModal() {
    try { return panel.matches(":modal"); } catch (e) { return !panel.classList.contains("is-docked"); }
  }
  function placeDock() {
    var hd = document.querySelector(".site-header");
    var top = hd ? Math.max(0, Math.round(hd.getBoundingClientRect().bottom)) : 0;
    panel.style.setProperty("--chat-top", top + "px");
  }
  /* iOS: keep the sheet above the on-screen keyboard (the visual viewport shrinks, the layout one does not). */
  function fitViewport() {
    if (!panel) return;
    var vv = window.visualViewport;
    if (!vv || !panel.open || panel.classList.contains("is-docked")) {
      panel.style.removeProperty("--chat-vh"); panel.style.removeProperty("--chat-vt"); return;
    }
    panel.style.setProperty("--chat-vh", Math.round(vv.height) + "px");
    panel.style.setProperty("--chat-vt", Math.round(vv.offsetTop) + "px");
  }
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", fitViewport);
    window.visualViewport.addEventListener("scroll", fitViewport);
  }
  var onDock = function () {
    if (!panel || !panel.open) return;
    var keep = document.activeElement && panel.contains(document.activeElement);
    panel.close();
    document.documentElement.classList.remove("chat-modal-open");
    open({ focus: keep });
  };
  if (dock.addEventListener) dock.addEventListener("change", onDock); else if (dock.addListener) dock.addListener(onDock);
  window.addEventListener("resize", function () { if (panel && panel.open && dock.matches) placeDock(); });
  window.addEventListener("pagehide", function () {
    if (busy) { busy.msg.status = "interrupted"; save(true); }
  });

  function grow() {
    if (!panel || !panel.open) return; /* scrollHeight is 0 while the dialog is closed */
    input.style.height = "auto";
    var hh = input.scrollHeight + 1; /* +1: sub-pixel line boxes */
    input.style.height = Math.min(hh, 160) + "px";
    input.style.overflowY = hh > 160 ? "auto" : "hidden";
  }
  function scrollEnd() { if (log) log.scrollTop = log.scrollHeight; }
  function announce(text) { statusEl.textContent = ""; setTimeout(function () { statusEl.textContent = text; }, 60); }

  /* ----- connection and attestation --------------------------------------- */
  function connect(force) {
    if (connecting && !force) return connecting;
    var my = ++connSeq;
    conn = { status: "pending" };
    paintAtt();
    if (!transport) { /* live mode without an api_base: misconfigured, never silently demo */
      conn = { status: "unavailable", code: "config" };
      paintAtt();
      return Promise.resolve();
    }
    if (transport.kind === "http" && navigator.onLine === false) {
      conn = { status: "offline" };
      paintAtt();
      return Promise.resolve();
    }
    var ctl = new AbortController();
    var timer = setTimeout(function () { ctl.abort(); }, CONNECT_MS);
    var kind = transport.kind;
    connecting = transport.connect(state.nonce, ctl.signal).then(function (r) {
      if (my !== connSeq) return;
      var res = judge(r.meta, r.bundle, kind);
      var b = r.bundle;
      var c = conn = { status: "ready", meta: r.meta, bundle: b, result: res,
                       expiresAt: b ? Date.now() + Math.max(0, Date.parse(b.expires_at) - Date.parse(b.issued_at)) : Infinity };
      /* paint now with the digest this page was built with; the manifest only refines it */
      manifest().then(function (man) {
        var shown = c.siteDigest || buildDigest();
        c.siteDigest = man.digest;
        if (conn === c && (man.digest || buildDigest()) !== shown) paintAtt();
      }, function () { /* no manifest: the build digest stays */ });
    }, function (e) {
      if (my !== connSeq) return;
      conn = { status: navigator.onLine === false ? "offline" : "unavailable", code: e && e.code || "network" };
      if (e && e.code === "rate_limited") setRate(e.retryAfter);
    }).then(function () {
      clearTimeout(timer);
      if (my !== connSeq) return;
      connecting = null;
      if (input) input.setAttribute("maxlength", String(limits().max_question_chars));
      paintAtt();
    });
    return connecting;
  }
  function freshen() {
    if (transport.kind !== "http" || conn.status !== "ready" || Date.now() < conn.expiresAt - 15000) return Promise.resolve();
    return connect(true).then(function () { if (!usable()) throw fail("attestation"); });
  }
  /* Switching transports stops an answer that is still streaming: the strip must not say
     "the live service is not used" while a request to it is open. */
  function useDemo() {
    if (cfg.allow_demo_fallback === false) return;
    stop();
    transport = new DemoTransport();
    state.transport = "demo"; state.fallback = true; save(true);
    connect(true).then(function () { syncComposer(); if (!input.disabled) input.focus(); });
    paintLog();
  }
  function useLive() {
    if (MODE !== "live" || !API) return;
    stop();
    transport = new HttpTransport(API);
    state.transport = "http"; state.fallback = false; save(true);
    connect(true);
    paintLog();
  }

  /* ----- rate limit countdown ------------------------------------------------ */
  var rateTimer = 0;
  function setRate(sec) {
    if (typeof sec !== "number" || !(sec > 0)) sec = 60;
    state.rateUntil = Date.now() + Math.min(sec, 86400) * 1000;
    save();
    tickRate();
  }
  function tickRate() {
    clearTimeout(rateTimer);
    var left = rateLeft();
    if (panel) Array.prototype.slice.call(panel.querySelectorAll(".chat-countdown")).forEach(function (n) { n.textContent = dur(left); });
    if (left > 0) { rateTimer = setTimeout(tickRate, 1000); return; }
    state.rateUntil = 0;
    if (!panel) return;
    state.messages.forEach(function (m) {
      if (m.error !== "rate") return;
      var node = document.getElementById("chat-" + m.id);
      if (node) paintBody(node, m);
    });
    syncComposer();
  }

  /* ----- strip and record panel ---------------------------------------------- */
  function row(dl, label, value, basis, mono) {
    var dd = h("dd", { "class": mono ? "chat-mono" : null }, [value && value.nodeType ? value : String(value == null || value === "" ? "—" : value)]);
    if (basis) dd.appendChild(h("span", { "class": "chat-basis", text: t("chat_basis_" + basis) }));
    dl.appendChild(h("div", { "class": "chat-row" }, [h("dt", { text: label }), dd]));
  }
  /* With encryption "none" this page itself sends plain text, so who can read is known here,
     whatever the service claims; otherwise the claim is shown as reported. */
  function readerRow(dl, meta, sum) {
    if (meta.encryption === "none") { row(dl, t("chat_row_reader"), t("chat_reader_yes"), "browser"); return; }
    row(dl, t("chat_row_reader"), sum.claims && sum.claims.operator_can_read_plaintext === false ? t("chat_reader_no") : t("chat_reader_yes"), "service");
  }
  function textBtn(act, label) { return h("button", { type: "button", "class": "chat-text-btn", "data-act": act, text: label }); }
  function paintAtt() {
    if (!attBox) return;
    var v = view(), http = transport && transport.kind === "http";
    /* the bundle and summary come from the service: read only the shapes the contract allows */
    var meta = obj(conn.meta) || {}, b = obj(conn.bundle) || {}, sum = obj(b.summary) || {}, res = conn.result || { checks: [] };
    var tee = obj(sum.tee) || {}, gpu = obj(sum.gpu), ms = obj(sum.measurement), cd = obj(sum.code), mdl = obj(sum.model) || {};
    var backend = obj(meta.backend) || {}, cc = str(sum.cc_mode);
    var mockBackend = http && v === "demo";
    attBox.setAttribute("data-state", v);
    attBox.setAttribute("data-transport", http ? "http" : "demo");
    var label = v === "demo" ? (mockBackend ? t("chat_att_mockbackend") : t("chat_att_demo"))
      : v === "pending" && transport && transport.kind === "demo" ? t("chat_demo_pending") : t("chat_att_" + v); /* demo: no attestation to check */
    var line = "";
    if (v === "demo") line = mockBackend ? hostOf(API) + " · " + t("chat_att_mockbackend_meta") : state.fallback ? t("chat_att_fallback_meta") : t("chat_att_demo_meta");
    else if (/^(reported|partly_verified|verified)$/.test(v)) {
      line = [str(tee.label) || str(tee.cpu), gpu && (str(gpu.model) + " CC " + cc), clock(b.issued_at)].filter(Boolean).join(" · ");
    } else if (v === "unavailable" || v === "offline") line = API ? hostOf(API) : "";
    var expanded = !!attBox.querySelector(".chat-att-panel:not([hidden])") || /^(failed|unavailable|offline)$/.test(v);
    attBox.textContent = "";
    attBox.appendChild(h("button", { type: "button", "class": "chat-att-line", id: "chat-att-line", "data-act": "att",
                                     "aria-expanded": expanded ? "true" : "false", "aria-controls": "chat-att-panel" }, [
      h("span", { "class": "chat-seal", "aria-hidden": "true" }),
      h("span", { "class": "chat-att-label", text: label }),
      line ? h("span", { "class": "chat-att-meta", text: line }) : null,
      h("span", { "class": "chat-att-toggle", "aria-hidden": "true" })]));
    var dl = h("dl"), note = h("p", { "class": "chat-att-note" }), links = h("p", { "class": "chat-att-links" });
    var box = h("div", { "class": "chat-att-panel", id: "chat-att-panel", hidden: !expanded }, [dl, note, links]);
    attBox.appendChild(box);
    var siteDigest = conn.siteDigest || buildDigest();
    if (v === "demo" && !mockBackend) {
      row(dl, t("chat_row_mode"), t("chat_demo_mode"));
      row(dl, t("chat_row_tee"), t("chat_none"));
      row(dl, t("chat_row_model"), t("chat_demo_model"));
      row(dl, t("chat_row_index"), tpl("chat_index_here", { d: code(short(siteDigest), siteDigest) }), "browser");
      note.textContent = t("chat_demo_note");
    } else if (v === "demo") {
      row(dl, t("chat_row_backend"), str(backend.label) + (str(backend.id) ? " (" + backend.id + ")" : ""), "service");
      row(dl, t("chat_row_tee"), str(tee.label) || t("chat_none"), "service");
      row(dl, t("chat_row_model"), str(mdl.display) || str(mdl.id), "service");
      row(dl, t("chat_row_encryption"), meta.encryption === "none" ? t("chat_enc_none") : str(meta.encryption), meta.encryption === "none" ? "browser" : "service");
      readerRow(dl, meta, sum);
      row(dl, t("chat_row_index"), tpl("chat_index_here", { d: code(short(siteDigest), siteDigest) }), "browser");
      row(dl, t("chat_row_att"), tpl("chat_att_id", { id: code(short(b.attestation_id, 18), b.attestation_id), time: clock(b.expires_at) }), "service");
      note.textContent = t("chat_mockbackend_note");
    } else if (/^(reported|partly_verified|verified|failed)$/.test(v) && conn.status === "ready") {
      if (v === "failed") row(dl, t("chat_row_problem"), t("chat_fail_" + (res.reason || "check")));
      row(dl, t("chat_row_backend"), str(backend.label), "service");
      row(dl, t("chat_row_tee"), [str(tee.label) || str(tee.cpu), str(tee.platform), str(tee.tcb_status),
                                  tee.debug === true ? t("chat_debug_on") : ""].filter(Boolean).join(" · "), basisOf(res, "cpu_evidence_signature"));
      if (gpu) row(dl, t("chat_row_gpu"), str(gpu.model) + (typeof gpu.count === "number" && gpu.count > 1 ? " ×" + gpu.count : "") + " · CC " + cc, basisOf(res, "gpu_nras_signature"));
      row(dl, t("chat_row_model"), [str(mdl.display) || str(mdl.id), str(sum.model_digest) ? short(sum.model_digest) : ""].filter(Boolean).join(" · "), "service");
      row(dl, t("chat_row_measure"), ms ? short(str(ms.mrtd) || str(ms.launch_measurement) || str(ms.image_digest), 16) : "", basisOf(res, "measurement_matches_release"), true);
      if (cd) row(dl, t("chat_row_release"), str(cd.repo) + " " + str(cd.tag) + " · " + short(str(cd.commit), 10), basisOf(res, "release_sigstore"), true);
      row(dl, t("chat_row_encryption"), meta.encryption === "none" ? t("chat_enc_none") : t("chat_enc_ehbp"), meta.encryption === "none" ? "browser" : "service");
      readerRow(dl, meta, sum);
      var vb = (Array.isArray(sum.verified_by) ? sum.verified_by : []).map(obj).filter(function (x) { return x && str(x.party); });
      if (vb.length) {
        row(dl, t("chat_row_verified_by"), vb.map(function (x) { return x.party + (str(x.subject) ? " (" + x.subject + ")" : ""); }).join(", ") +
            (sum.verified_at ? " · " + clock(sum.verified_at) : ""), "service");
      }
      row(dl, t("chat_row_fresh"), t("chat_fresh_echo"), "service");
      /* only a string the service sent: this browser cannot know which corpus the backend used */
      var cm = str((obj(sum.corpus) || {}).manifest_digest);
      row(dl, t("chat_row_index"), !cm ? t("chat_index_none") : cm === siteDigest ? t("chat_index_match") : tpl("chat_index_differs", { d: code(short(cm), cm) }), cm ? "service" : null);
      var pending = res.checks.filter(function (c) { return c.status === "not_checked"; }).map(function (c) { return c.label; });
      if (pending.length) row(dl, t("chat_row_not_checked"), pending.join(", "));
      row(dl, t("chat_row_checked"), clock(b.issued_at), "service");
      note.textContent = t("chat_att_note");
      if (typeof b.report_url === "string" && /^https:\/\//.test(b.report_url)) {
        links.appendChild(h("a", { "class": "ext", href: b.report_url, rel: "noopener noreferrer", text: t("chat_row_report") }));
      }
    } else if (v === "pending") {
      note.textContent = transport && transport.kind === "http" ? t("chat_att_pending_note") : t("chat_demo_pending_note");
    } else {
      note.textContent = v === "offline" ? t("chat_offline_note") : conn.code === "config" ? t("chat_config_note")
        : conn.code === "rate_limited" ? t("chat_rate_note") : t("chat_unavailable_note");
    }
    var sep = function () { if (links.firstChild) links.appendChild(document.createTextNode(" · ")); };
    sep();
    links.appendChild(h("a", { href: site_url(cfg.about || "/about/#assistant"), text: t("chat_how") }));
    if ((v === "unavailable" || v === "offline") && transport && conn.code !== "config") { sep(); links.appendChild(textBtn("reconnect", t("chat_reconnect"))); }
    if ((v === "unavailable" || v === "offline") && MODE === "live" && cfg.allow_demo_fallback !== false) { sep(); links.appendChild(textBtn("demo", t("chat_use_demo"))); }
    if (state.fallback && MODE === "live" && API && transport && transport.kind === "demo") { sep(); links.appendChild(textBtn("live", t("chat_use_live"))); }
    syncComposer();
  }
  function toggleAtt(b) {
    var p = attBox.querySelector(".chat-att-panel");
    p.hidden = !p.hidden;
    b.setAttribute("aria-expanded", p.hidden ? "false" : "true");
  }
  function syncComposer() {
    if (!form) return;
    var ok = canAsk(), http = transport && transport.kind === "http", v = view();
    input.disabled = !ok && !busy && v !== "pending"; /* typing is fine while the attestation is checked; sending is not */
    sendBtn.disabled = !ok && !busy;
    sendBtn.textContent = busy ? t("chat_stop") : t("chat_send");
    sendBtn.classList.toggle("is-stop", !!busy);
    disc.textContent = "";
    if (http && navigator.onLine === false) disc.textContent = t("chat_offline");
    else if (http && rateLeft() > 0) disc.appendChild(tpl("chat_rate_wait", { wait: h("span", { "class": "chat-countdown", text: dur(rateLeft()) }) }));
    else if (v === "pending") disc.textContent = t(transport && transport.kind === "demo" ? "chat_demo_pending" : "chat_att_pending") + "…";
    else if (v === "failed") disc.textContent = t("chat_paused");
    else if (v === "unavailable" || v === "offline") disc.textContent = t("chat_unavailable");
    else if (!http) disc.textContent = t("chat_disclosure_demo");
    else if (v === "demo") disc.textContent = t("chat_disclosure_mockbackend", { host: hostOf(API) });
    else if (conn.meta && conn.meta.encryption === "none") disc.textContent = t("chat_disclosure_plain", { host: hostOf(API) });
    else disc.textContent = t("chat_disclosure_live");
  }

  /* ----- transcript ------------------------------------------------------- */
  function paintLog() {
    log.textContent = "";
    if (!state.messages.length) { log.appendChild(empty()); return; }
    state.messages.forEach(function (m) { log.appendChild(msgNode(m)); });
    scrollEnd();
  }
  function empty() {
    var box = h("div", { "class": "chat-empty" }, [h("p", { "class": "chat-intro", text: t("chat_intro") })]);
    if (isArticle) box.appendChild(articleBlock(true));
    var sg = Array.isArray(cfg.suggestions) ? cfg.suggestions : cfg.suggestions && Array.isArray(cfg.suggestions[lang]) ? cfg.suggestions[lang] : null;
    var qs = sg ? sg.filter(function (q) { return typeof q === "string" && q; }).slice(0, 6) : [];
    if (qs.length) box.appendChild(suggestList(t("chat_suggest"), qs.map(function (q) { return { q: q }; })));
    return box;
  }
  function suggestList(title, items) {
    var ul = h("ul");
    items.forEach(function (it) {
      ul.appendChild(h("li", null, [h("button", { type: "button", "class": "chat-suggestion", "data-act": "ask", "data-q": it.q, "data-intent": it.intent || null }, [
        h("span", { text: it.q }), h("span", { "class": "chat-arrow", "aria-hidden": "true", text: "→" })])]));
    });
    return h("section", { "class": "chat-suggest" }, [h("h3", { "class": "chat-mini", text: title }), ul]);
  }
  function articleBlock(inEmpty) {
    var box = h("div", { "class": inEmpty ? "chat-article" : "chat-empty chat-article" }, [
      h("div", { "class": "chat-context" }, [
        h("p", { "class": "chat-mini", text: t("chat_this_article") }),
        h("p", { "class": "chat-context-title", text: page.title || "" }),
        HEX64.test(page.sha256 || "") ? h("code", { "class": "chat-digest", title: page.sha256, text: "sha256 " + short(page.sha256) }) : null])]);
    box.appendChild(suggestList(t("chat_ask_article"), [
      { q: t("chat_q_summary"), intent: "summary" }, { q: t("chat_q_limits"), intent: "limits" }, { q: t("chat_q_sources"), intent: "sources" }]));
    return box;
  }
  function msgNode(m) {
    var mid = "chat-" + m.id;
    if (m.role === "user") {
      var u = h("div", { "class": "chat-msg chat-user", id: mid }, [
        h("p", { "class": "chat-who", text: t("chat_you") }), h("p", { "class": "chat-q", text: m.content })]);
      if (m.page && m.page.title) {
        u.appendChild(h("p", { "class": "chat-q-ctx" }, [t("chat_about") + " ", h("a", { href: site_url(m.page.url), text: m.page.title })]));
      }
      return u;
    }
    var b = h("div", { "class": "chat-msg chat-bot", id: mid, lang: m.lang === "zh" ? "zh-CN" : "en" }, [
      h("p", { "class": "chat-who", text: m.transport === "demo" ? t("chat_bot_demo") : m.mock ? t("chat_bot_mockbackend") : t("chat_bot") }),
      h("div", { "class": "chat-body" })]);
    paintBody(b, m);
    return b;
  }
  function errorNote(m) {
    var p = h("p", { "class": "chat-note chat-error" });
    if (m.error === "rate" && rateLeft() > 0) p.appendChild(tpl("chat_err_rate", { wait: h("span", { "class": "chat-countdown", text: dur(rateLeft()) }) }));
    else if (m.error === "rate") p.textContent = t("chat_err_rate_over");
    else p.textContent = t("chat_err_" + (m.error || "generic"));
    return p;
  }
  function paintBody(node, m) {
    var mid = "chat-" + m.id, body = node.querySelector(".chat-body");
    node.setAttribute("aria-busy", m.status === "streaming" ? "true" : "false");
    node.setAttribute("data-status", m.status);
    if (m.content) render(body, m.content, mid);
    else body.textContent = "";
    if (m.status === "streaming" && !m.content) {
      body.appendChild(h("p", { "class": "chat-wait", text: m.phase === "wait" ? t(m.transport === "demo" ? "chat_wait_demo" : "chat_wait_live") : t("chat_wait_search") }));
    }
    Array.prototype.slice.call(node.querySelectorAll(".chat-sources, .chat-receipt, .chat-actions, .chat-note")).forEach(function (n) { n.remove(); });
    if (m.status === "streaming") return;
    (m.notices || []).forEach(function (x) { node.appendChild(h("p", { "class": "chat-note", text: x })); });
    if (m.finish === "length" || m.finish === "refused") node.appendChild(h("p", { "class": "chat-note", text: t("chat_finish_" + m.finish) }));
    if (m.gap) node.appendChild(h("p", { "class": "chat-note chat-error", text: t("chat_gap") }));
    if (m.status === "stopped" || m.status === "interrupted") node.appendChild(h("p", { "class": "chat-note", text: t("chat_" + m.status) }));
    if (m.status === "error") node.appendChild(errorNote(m));
    if (m.citations && m.citations.length) node.appendChild(sources(m, mid));
    if (m.content || m.att) node.appendChild(receipt(m));
    var actions = h("div", { "class": "chat-actions" });
    if (m.content) actions.appendChild(h("button", { type: "button", "class": "chat-text-btn", "data-act": "copy", "data-id": m.id, text: t("chat_copy") }));
    var waiting = m.error === "rate" && rateLeft() > 0 && transport && transport.kind === "http";
    if (m.status !== "done" && !waiting) actions.appendChild(h("button", { type: "button", "class": "chat-text-btn", "data-act": "retry", "data-id": m.id, text: t("chat_retry") }));
    if (m.status === "error" && m.transport === "http" && /^(rate|unavailable|network|timeout)$/.test(m.error || "") &&
        MODE === "live" && cfg.allow_demo_fallback !== false && transport && transport.kind === "http") {
      actions.appendChild(h("button", { type: "button", "class": "chat-text-btn", "data-act": "demo", text: t("chat_use_demo") }));
    }
    node.appendChild(actions);
  }
  function receipt(m) {
    var p = h("p", { "class": "chat-receipt" }), parts = [];
    if (m.transport === "demo") parts.push(document.createTextNode(t("chat_receipt_demo")));
    else {
      parts.push(document.createTextNode(m.backend || hostOf(API)));
      if (m.att) parts.push(tpl("chat_receipt_att", { id: code(short(m.att, 18), m.att) }));
    }
    if (m.unbound) parts.push(document.createTextNode(t("chat_receipt_unbound")));
    if (m.signed) parts.push(document.createTextNode(t("chat_receipt_signed_" + (m.signed === "verified" ? "ok" : m.signed === "failed" ? "bad" : "unchecked"))));
    parts.forEach(function (x, i) { if (i) p.appendChild(document.createTextNode(" · ")); p.appendChild(x); });
    return p;
  }
  function sources(m, mid) {
    var used = Array.isArray(m.used) ? m.used : [];
    var cited = used.length ? m.citations.filter(function (c) { return used.indexOf(c.n) >= 0; }) : m.citations;
    var ol = h("ol");
    cited.forEach(function (c) {
      var li = h("li", { id: mid + "-src-" + c.n }, [h("span", { "class": "chat-n", text: "[" + c.n + "]" })]);
      var label = c.title + (c.heading && c.heading !== c.title ? " · " + c.heading : "");
      if (internal(c.url)) li.appendChild(h("a", { href: link(c.url), text: label }));
      else if (/^https:\/\//.test(c.url || "")) li.appendChild(h("a", { "class": "ext", href: c.url, rel: "noopener noreferrer nofollow", text: label }));
      else li.appendChild(h("span", { "class": "chat-src-title", text: label }));
      if (c.sha) {
        var chip = h("code", { "class": "chat-digest", title: c.sha, text: "sha256 " + short(c.sha) });
        if (c.match === false) { chip.classList.add("is-stale"); chip.textContent += " · " + t("chat_digest_differs"); }
        else if (c.sent === false) { chip.classList.add("is-stale"); chip.textContent += " · " + t("chat_digest_not_sent"); }
        else if (c.here) chip.textContent += " · " + t("chat_digest_here");
        li.appendChild(chip);
      }
      ol.appendChild(li);
    });
    var sec = h("section", { "class": "chat-sources" }, [h("h3", { "class": "chat-mini", text: used.length ? t("chat_sources") : t("chat_passages_sent") }), ol]);
    var more = m.citations.length - cited.length;
    if (more > 0) sec.appendChild(h("p", { "class": "chat-sources-more", text: t(more === 1 ? "chat_sources_more_one" : "chat_sources_more", { n: more }) }));
    return sec;
  }
  /* Compare each cited source digest with this build's manifest, and note where this
     browser fetched and hashed the source file itself. */
  function checkCitations(m) {
    if (!m.citations || !m.citations.length) return Promise.resolve();
    return manifest().then(function (man) {
      m.citations.forEach(function (c) {
        var entry = (c.source && man.bySource[c.source]) || (c.url && man.byPage[String(c.url).split("#")[0]]);
        if (!entry || !c.sha) { c.match = null; return; }
        c.match = entry.sha256 === c.sha;
        c.here = c.match && hashed[entry.source] === entry.sha256;
      });
    }, function () { /* no manifest: chips stay unchecked */ });
  }

  /* ----- asking ----------------------------------------------------------- */
  var seq = 0;
  function uid() { return Date.now().toString(36) + (seq++).toString(36); }
  function ask(text, intent) {
    text = (text || "").trim();
    if (!text || !canAsk()) return;
    text = text.slice(0, limits().max_question_chars);
    intent = intent && isArticle ? intent : null;
    Array.prototype.slice.call(log.querySelectorAll(".chat-empty, .chat-article")).forEach(function (n) { n.remove(); });
    var u = { id: uid(), role: "user", content: text, intent: intent, page: intent ? { url: page.url, title: page.title } : null, ts: Date.now() };
    state.messages.push(u);
    log.appendChild(msgNode(u));
    if (!intent || input.value.trim() === text) { input.value = ""; state.draft = ""; }
    grow();
    run(u);
  }
  function buildRequest(u, ret) {
    var lim = limits(), msgs = state.messages, idx = msgs.indexOf(u), hist = [], users = 0;
    for (var i = idx; i >= 0 && hist.length < 2 * lim.max_turns; i--) {
      var x = msgs[i];
      if (x.role === "user") {
        if (users >= lim.max_turns) break;
        users++;
        hist.unshift({ role: "user", content: x.content.slice(0, i === idx ? lim.max_question_chars : MAX_EARLIER) });
      } else if (x.role === "assistant" && x.content && x.status !== "error") {
        hist.unshift({ role: "assistant", content: x.content.slice(0, MAX_EARLIER) });
      }
    }
    while (hist.length && hist[0].role !== "user") hist.shift();
    var req = {
      api_version: "1", lang: lang, nonce: state.nonce,
      page: { path: page.url || location.pathname, source_sha256: isArticle && HEX64.test(page.sha256 || "") ? page.sha256 : null },
      messages: hist,
      context: { manifest_digest: ret.manifest_digest, chunks: ret.chunks.map(function (c) {
        var o = {};
        ["n", "id", "slug", "lang", "kind", "title", "heading", "url", "source", "source_sha256", "start", "end", "text"].forEach(function (k) { o[k] = c[k] === undefined ? null : c[k]; });
        return o;
      }) },
      options: { max_output_tokens: lim.max_output_tokens, temperature: 0.2 }
    };
    var enc = new TextEncoder();
    while (req.context.chunks.length && enc.encode(JSON.stringify(req)).length > lim.max_body_bytes - 1024) req.context.chunks.pop();
    return req;
  }
  function run(u) {
    var tr = transport;
    var m = { id: uid(), role: "assistant", content: "", lang: lang, status: "streaming", phase: "search", transport: tr.kind,
              mock: tr.kind === "http" && view() === "demo", citations: [], used: null, notices: [], ts: Date.now() };
    /* the answer goes right after its question: Retry on an earlier answer keeps it in place */
    state.messages.splice(state.messages.indexOf(u) + 1, 0, m);
    var node = msgNode(m), qNode = document.getElementById("chat-" + u.id);
    if (qNode && qNode.parentNode === log) log.insertBefore(node, qNode.nextSibling); else log.appendChild(node);
    /* paintLog() (switching transports, Retry) rebuilds the transcript, so paint whichever
       node now carries this message rather than the one created here */
    var el = function () { return document.getElementById("chat-" + m.id) || node; };
    if (node.nextSibling) node.scrollIntoView({ block: "nearest" }); else scrollEnd();
    var ctl = new AbortController();
    busy = { controller: ctl, msg: m, stopped: false, timedOut: false };
    syncComposer();
    setLaunch(panel.open ? null : "busy");
    announce(t("chat_status_start"));
    var frame = 0, nearEnd = !node.nextSibling, expect = 0, sent = {}, ended = false, idle = 0;
    log.onscroll = function () { nearEnd = log.scrollHeight - log.scrollTop - log.clientHeight < 48; };
    var paint = function () { frame = 0; paintBody(el(), m); if (nearEnd) scrollEnd(); };
    var arm = function () {
      clearTimeout(idle);
      idle = setTimeout(function () { if (busy && busy.msg === m) busy.timedOut = true; ctl.abort(); }, IDLE_MS);
    };
    var on = function (ev, data) {
      arm();
      if (!data || typeof data !== "object") data = {};
      if (ev === "meta") {
        m.backend = str(data.backend) || null; m.model = str(data.model) || null; m.att = str(data.attestation_id) || null;
        var bb = conn.bundle;
        if (tr.kind === "http" && bb) m.unbound = data.attestation_id !== bb.attestation_id || (!!data.keyset_digest && data.keyset_digest !== bb.keyset_digest);
      } else if (ev === "citations") {
        m.citations = (Array.isArray(data.items) ? data.items : []).filter(function (c) {
          return c && typeof c.n === "number" && typeof c.title === "string";
        }).map(function (c) {
          return { n: c.n, title: c.title, heading: str(c.heading) || null, url: str(c.url), source: str(c.source) || null,
                   sha: HEX64.test(str(c.source_sha256)) ? c.source_sha256 : null, sent: !!sent[c.chunk_id] };
        });
      } else if (ev === "notice") {
        if (str(data.message)) m.notices.push(data.message);
      } else if (ev === "delta") {
        if (typeof data.i === "number") { if (data.i !== expect) m.gap = true; expect = data.i + 1; } else expect++;
        m.content += str(data.text);
        m.phase = "stream";
        if (!frame) frame = requestAnimationFrame(paint);
      } else if (ev === "done") {
        ended = true;
        m.finish = str(data.finish_reason) || "stop";
        m.used = Array.isArray(data.used_citations) ? data.used_citations.filter(function (n) { return typeof n === "number"; }) : null;
        if (data.receipt) m.signed = verifyReceipt(data.receipt, conn.bundle).status;
      } else if (ev === "error") {
        ended = true;
        throw fail(CODES.indexOf(data.code) >= 0 ? data.code : "internal", str(data.message),
                   { retryAfter: typeof data.retry_after_s === "number" ? data.retry_after_s : null, sse: true });
      }
      save();
    };
    var send = function (req, ret, attempt) {
      return freshen().then(function () {
        if (ctl.signal.aborted) throw fail("aborted");
        arm();
        return tr.chat(req, ret, conn, on, ctl.signal, arm);
      }).catch(function (e) {
        var stale = e && (e.code === "attestation_expired" || e.code === "attestation_mismatch") && !e.sse;
        if (stale && attempt === 0 && !m.content && !ctl.signal.aborted && tr === transport) {
          return connect(true).then(function () {
            if (!usable()) throw fail("attestation");
            return send(req, ret, 1);
          });
        }
        throw e;
      });
    };
    /* Stop works while passages are still being fetched, too */
    var stopped = new Promise(function (resolve, reject) {
      ctl.signal.addEventListener("abort", function () { reject(fail("aborted")); });
    });
    Promise.race([retrieve(u.content, u.intent), stopped]).catch(function (e) {
      if (ctl.signal.aborted) throw fail("aborted");
      if (tr.kind === "demo") throw fail("index");
      return { chunks: [], manifest_digest: buildDigest(), intent: null, found: null }; /* the backend then says it has nothing */
    }).then(function (ret) {
      if (ctl.signal.aborted) throw fail("aborted");
      ret.chunks.forEach(function (c) { sent[c.id] = true; });
      m.phase = "wait";
      paintBody(el(), m);
      return send(buildRequest(u, ret), ret, 0);
    }).then(function () {
      if (!ended) throw fail("incomplete"); /* the stream closed without done or error */
      m.status = "done";
    }).catch(function (e) {
      if (busy && busy.msg === m && busy.stopped) { m.status = "stopped"; return; }
      m.status = "error";
      var c = busy && busy.msg === m && busy.timedOut ? "timeout" : e && e.name === "TypeError" ? "network" : e && e.code;
      m.error = { rate_limited: "rate", upstream_unavailable: "unavailable", timeout: "timeout", network: "network", too_long: "too_long",
                  attestation: "attestation", attestation_expired: "attestation", attestation_mismatch: "attestation", index: "index",
                  incomplete: "incomplete", bad_request: "bad_request", format: "format" }[c] || "generic";
      if (m.error === "rate" || (m.error === "unavailable" && e.retryAfter)) setRate(e.retryAfter);
    }).then(function () {
      clearTimeout(idle);
      return Promise.all([sha256(m.content).then(function (d) { m.digest = d; }), checkCitations(m)]);
    }).then(function () {
      if (busy && busy.msg === m) busy = null;
      if (frame) cancelAnimationFrame(frame);
      if (state.messages.indexOf(m) < 0) { syncComposer(); return; } /* "New chat" replaced the transcript */
      node = el();
      paintBody(node, m);
      save(true);
      syncComposer();
      setLaunch(panel.open ? null : "unread");
      var note = node.querySelector(".chat-note");
      var cited = Array.isArray(m.used) && m.used.length ? m.used.length : (m.citations || []).length;
      announce(m.status === "done" ? node.querySelector(".chat-body").textContent.slice(0, 900) + " " + t("chat_status_done", { n: cited }) : note ? note.textContent : "");
      if (nearEnd) scrollEnd();
    });
  }
  function stop() { if (busy) { busy.stopped = true; busy.controller.abort(); } }
  function retry(id) {
    var i = -1;
    state.messages.forEach(function (x, j) { if (x.id === id) i = j; });
    if (i < 1 || busy || !canAsk()) return;
    var u = state.messages[i - 1];
    if (u.role !== "user") return;
    state.messages.splice(i, 1);
    paintLog();
    run(u);
  }
  function reset() {
    stop();
    busy = null;
    var keep = { transport: state.transport, fallback: state.fallback, open: !!(panel && panel.open && !isModal()) };
    state = fresh();
    if (MODE === "live") { state.transport = keep.transport; state.fallback = keep.fallback; }
    state.open = keep.open;
    save(true);
    paintLog();
    connect(true);
    (input.disabled ? panel.querySelector("#chat-title") : input).focus();
  }
  function copy(b) {
    var m = state.messages.filter(function (x) { return x.id === b.getAttribute("data-id"); })[0];
    if (!m) return;
    var text = m.content + (m.citations && m.citations.length ? "\n\n" + m.citations.map(function (c) {
      var u = internal(c.url) ? new URL(link(c.url), location.href).href : c.url;
      return "[" + c.n + "] " + c.title + (c.heading ? " · " + c.heading : "") + " " + u;
    }).join("\n") : "");
    var done = function () { var l = b.textContent; b.textContent = t("chat_copied"); setTimeout(function () { b.textContent = l; }, 1600); };
    try { navigator.clipboard.writeText(text).then(done, function () { /* permission denied */ }); } catch (e) { /* no clipboard */ }
  }

  /* Reopen the docked panel after navigation (a citation click) without moving focus. */
  if (rateLeft() > 0) tickRate();
  if (state.open && dock.matches) open({ focus: false });
  else if (state.messages.length) setLaunch(null);
})();
