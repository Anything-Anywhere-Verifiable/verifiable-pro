// Cuts published Markdown sources into passages with static/chat.js's own parser
// (parseDoc and passageChunk), so the request fixtures carry exactly what the widget
// would send. refresh_requests.py runs it; it needs Node.js and only Node's own modules.
//
//   node backend/mock/chat_passages.mjs <repo> <production build> <source path> [<source path> ...]
//
// A source path is a manifest entry's "source", such as /articles/<slug>/en.md. It prints
// {"manifest_digest": ..., "docs": {<source path>: {"entry": ..., "passages": [...], "sources": ...}}}
// as JSON on standard output.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const [repo, build, ...sources] = process.argv.slice(2);
if (!repo || !build || !sources.length) {
  process.stderr.write("usage: node chat_passages.mjs <repo> <production build> <source path> [...]\n");
  process.exit(2);
}
const js = fs.readFileSync(path.join(repo, "static", "chat.js"), "utf8");
const strings = JSON.parse(fs.readFileSync(path.join(repo, "content", "strings.json"), "utf8"));

// chat.js's parser, from its first passage regex up to the retrieval code that follows it
function between(a, b) {
  const i = js.indexOf(a), j = js.indexOf(b, i);
  if (i < 0 || j < 0) throw new Error("static/chat.js has changed: marker not found: " + a + " / " + b);
  return js.slice(i, j);
}
const parser = between("var HEADING =", "/* ----- retrieval over the site index");
// the passage length cap, as chat.js sets it
const cap = /\bPASSAGE = (\d+)/.exec(js);
if (!cap) throw new Error("static/chat.js has changed: PASSAGE not found");

const man = JSON.parse(fs.readFileSync(path.join(build, "manifest.json"), "utf8"));
const bySource = {};
for (const e of man.entries) bySource[e.source] = e;
const out = { manifest_digest: man.digest, docs: {} };
for (const src of sources) {
  const entry = bySource[src];
  if (!entry) throw new Error("not in the build's manifest: " + src);
  const S = strings[entry.lang] || {};
  const ctx = { S, lang: entry.lang, PASSAGE: Number(cap[1]), HEX64: /^[0-9a-f]{64}$/, out: null,
    has: (o, k) => Object.prototype.hasOwnProperty.call(o, k) };
  ctx.t = (key) => (ctx.has(S, key) ? String(S[key]) : key);
  vm.createContext(ctx);
  // decoded as the widget decodes a fetched source, keeping a byte order mark if there is one
  ctx.__text = new TextDecoder("utf-8", { ignoreBOM: true }).decode(fs.readFileSync(path.join(build, src.replace(/^\//, ""))));
  ctx.__entry = entry;
  vm.runInContext(parser + "\nvar __doc = parseDoc(__text, __entry);"
    + " out = { passages: __doc.passages.map(function (p) { return passageChunk(__doc, p); }),"
    + " sources: __doc.sources ? sourcesChunk(__doc) : null };", ctx);
  out.docs[src] = { entry, ...ctx.out };
}
process.stdout.write(JSON.stringify(out, null, 1) + "\n");
