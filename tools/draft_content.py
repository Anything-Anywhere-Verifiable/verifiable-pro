#!/usr/bin/env python3
"""Turn research JSON into draft content files for design reviews.

Draft output is a scaffold: news bodies reuse the verified summaries and the
long-form entries are stubs. Final content replaces every file written here.
Every article names who drafted it, as the build requires (CONTENT_GUIDE.md,
"Bylines"): the AI agent that drafts its kind, from content/site.json "agents"
(daily for news briefs, research for analysis, explainers and guides), or the
person that --author names.

Drafting replaces topics.json, resources.json, glossary.json and the whole
articles/ folder in the output folder, so --out is required and may not be
content/ or a folder inside it (a symlink to one counts as the folder itself):
draft elsewhere, compare, and copy what you keep into content/ by hand.

    python3 tools/draft_content.py --out DIR [--author NAME]
"""

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / "research"
TOPIC_IDS = ["confidential-computing", "verifiable-inference", "formal-verification", "evaluation-audits",
             "provenance-supply-chain", "agents-accountability", "governance-compute"]
TYPES = {"paper", "standard", "specification", "tool", "project", "organization", "report", "benchmark", "course", "dataset"}
# The AI agent (an id from content/site.json "agents") that drafts each kind of article
AGENT_BY_KIND = {"news": "daily", "analysis": "research", "explainer": "research", "guide": "research"}

STACK = [
    {"id": "institutions", "name": {"en": "Policy", "zh": "政策"},
     "claim": {"en": "Developers and governments keep the commitments they make about training, deployment and compute.",
               "zh": "开发者与政府信守其关于训练、部署和算力的承诺。"},
     "topics": ["governance-compute"]},
    {"id": "evaluations", "name": {"en": "Evaluations & audits", "zh": "评测与审计"},
     "claim": {"en": "A reported result came from the stated model, tests and conditions.",
               "zh": "公布的结果确实来自所声明的模型、测试与条件。"},
     "topics": ["evaluation-audits", "formal-verification"]},
    {"id": "agents", "name": {"en": "Agents & actions", "zh": "智能体与行动"},
     "claim": {"en": "An agent took these actions, under this policy, on behalf of this principal.",
               "zh": "智能体在这一策略下、代表这一委托方执行了这些操作。"},
     "topics": ["agents-accountability"]},
    {"id": "outputs", "name": {"en": "Outputs & content", "zh": "输出与内容"},
     "claim": {"en": "This output came from this model and input, and this media has this origin.",
               "zh": "这一输出来自这个模型和输入，这份媒体内容有这样的来源。"},
     "topics": ["verifiable-inference", "provenance-supply-chain"]},
    {"id": "models", "name": {"en": "Models & data", "zh": "模型与数据"},
     "claim": {"en": "These are the weights that were trained, signed and deployed, with this lineage.",
               "zh": "部署的权重就是经过训练和签名的那一份，并具有这样的来源链。"},
     "topics": ["provenance-supply-chain", "governance-compute"]},
    {"id": "runtime", "name": {"en": "Software & runtime", "zh": "软件与运行时"},
     "claim": {"en": "This exact code and configuration processed the request.",
               "zh": "处理请求的正是这份代码与配置。"},
     "topics": ["confidential-computing", "formal-verification"]},
    {"id": "hardware", "name": {"en": "Hardware & compute", "zh": "硬件与算力"},
     "claim": {"en": "The computation ran on genuine hardware in a protected mode.",
               "zh": "计算在真实硬件的受保护模式中运行。"},
     "topics": ["confidential-computing", "governance-compute"]},
]

RULES = [
    ("confidential-computing", ("confidential", "attestation", "tee", "enclave")),
    ("verifiable-inference", ("inference", "computation", "zk", "proof-of", "zero-knowledge")),
    ("formal-verification", ("formal", "guaranteed", "proof assistant")),
    ("evaluation-audits", ("evaluation", "audit", "benchmark")),
    ("provenance-supply-chain", ("provenance", "supply", "signing", "content credential", "watermark")),
    ("agents-accountability", ("agent",)),
    ("governance-compute", ("governance", "compute verification", "hardware-enabled", "international", "treaty")),
]


def canon(text):
    low = (text or "").lower()
    if low in TOPIC_IDS:
        return low
    for tid, keys in RULES:
        if any(k in low for k in keys):
            return tid
    return None


def slugify(text, limit=64):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].rstrip("-")


def load(name):
    path = RESEARCH / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def landscape():
    parts = [load("landscape-verified-part1.json"), load("landscape-verified-part2.json")]
    base = load("landscape.json") or {}
    if all(parts):
        pillars = parts[0].get("pillars", []) + parts[1].get("pillars", [])
        glossary = parts[1].get("glossary") or base.get("glossary", [])
        return pillars, glossary
    return base.get("pillars", []), base.get("glossary", [])


def news_items():
    verified = []
    for n in (1, 2):
        doc = load(f"news-verified-part{n}.json")
        if doc:
            verified += doc.get("items", [])
    if verified:
        return verified
    return (load("news-candidates.json") or {}).get("items", [])


def tr(value):
    return {"en": value, "zh": value}


def byline(kind, author=None):
    """The front matter line that says who drafted an article of KIND: author: NAME when a
    person is named, else agent: the id of the AI agent that drafts that kind. zh.md takes it
    from en.md, so only en.md carries it."""
    return f"author: {author}" if author else f"agent: {AGENT_BY_KIND[kind]}"


def out_folder(path):
    """The resolved folder to draft into. It may not be content/ or lie inside it, since drafting
    replaces the data files and every article there; SystemExit says so before anything is read
    or written."""
    out = Path(path).expanduser().resolve()
    content = (ROOT / "content").resolve()
    if out == content or content in out.parents:
        raise SystemExit(f"draft_content.py: refusing to write into {content} (--out {path}): drafting replaces "
                         "its data files and every article. Draft into another folder and copy what you keep by hand.")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Draft content files from research/ into a folder outside content/.")
    ap.add_argument("--out", required=True, metavar="DIR",
                    help="folder to draft into; required, and never content/ or a folder inside it")
    ap.add_argument("--author", metavar="NAME",
                    help="name this person as every article's author, instead of the AI agent that drafts its kind")
    args = ap.parse_args(argv)
    author = " ".join((args.author or "").split()) or None
    out = out_folder(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pillars, glossary = landscape()

    topics, seen_ids = [], set()
    for p in pillars:
        tid = canon(p.get("id", "")) or canon(p.get("name", ""))
        if not tid or tid in seen_ids:
            continue
        seen_ids.add(tid)
        topics.append({
            "id": tid,
            "name": {"en": p["name"], "zh": p.get("name_zh") or p["name"]},
            "one_liner": tr(p.get("one_liner", "")),
            "description": tr(p.get("description", "")),
            "questions": tr(p.get("key_questions", [])),
            "techniques": [{"name": tr(t["name"]), "description": tr(t["description"])} for t in p.get("techniques", [])],
        })
    topics.sort(key=lambda t: TOPIC_IDS.index(t["id"]))
    (out / "topics.json").write_text(json.dumps({"stack": STACK, "topics": topics}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    resources, by_url = [], {}
    for p in pillars:
        tid = canon(p.get("id", "")) or canon(p.get("name", ""))
        for r in p.get("references", []):
            url = r.get("url", "").strip()
            key = url.rstrip("/").lower()
            if not url:
                continue
            if key in by_url:
                if tid and tid not in by_url[key]["topics"]:
                    by_url[key]["topics"].append(tid)
                continue
            rtype = (r.get("type") or "").lower()
            year = re.match(r"\d{4}", str(r.get("date", "")))
            entry = {
                "id": slugify(r.get("title", url), 48), "title": r.get("title", url), "url": url,
                "org": r.get("authors_or_org", ""), "year": int(year.group(0)) if year else "",
                "type": rtype if rtype in TYPES else "project", "topics": [tid] if tid else [],
                "note": tr(r.get("note", "")), "featured": False,
            }
            by_url[key] = entry
            resources.append(entry)
    firsts = {}
    for r in resources:
        if r["topics"] and r["topics"][0] not in firsts:
            firsts[r["topics"][0]] = r
    for r in list(firsts.values())[:6]:
        r["featured"] = True
    (out / "resources.json").write_text(json.dumps({"resources": resources}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    terms, ids = [], set()
    for g in glossary:
        gid = slugify(g["term"], 48)
        if gid in ids:
            continue
        ids.add(gid)
        terms.append({"id": gid, "term": {"en": g["term"], "zh": g.get("term_zh") or g["term"]},
                      "definition": tr(g.get("definition", "")), "topic": canon(g.get("pillar", "")) or ""})
    (out / "glossary.json").write_text(json.dumps({"terms": terms}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    arts = out / "articles"
    if arts.exists():
        shutil.rmtree(arts)
    arts.mkdir(parents=True)
    items = sorted(news_items(), key=lambda i: i.get("date_announced", ""), reverse=True)
    for k, item in enumerate(items):
        tid = canon(item.get("pillar", "")) or "provenance-supply-chain"
        slug = slugify(item["headline"])
        summary = item.get("summary", "").strip()
        dek = re.split(r"(?<=[.!?])\s", summary)[0]
        sources = [f"{item['primary_source_name']} | {item['primary_source_name']} | {item['date_announced']} | {item['primary_source_url']}"]
        body = f"{summary}[^1]\n\n:::analysis\n{item.get('why_it_matters', '')}\n:::\n\n:::checked\nDraft: primary source opened on 2026-10-19.\n:::\n"
        fm = ["---", f"title: {item['headline']}", f"dek: {dek}", "kind: news", byline("news", author), f"topics: [{tid}]",
              f"event_date: {item['date_announced'][:10]}", "published: 2026-10-19"]
        if k == 0:
            fm.append("lead: true")
        fm += ["sources:"] + [f"  - {s}" for s in sources] + ["---", ""]
        (arts / slug).mkdir()
        (arts / slug / "en.md").write_text("\n".join(fm) + body, encoding="utf-8")
        (arts / slug / "zh.md").write_text(f"---\ntitle: {item['headline']}\ndek: {dek}\n---\n" + body, encoding="utf-8")

    stubs = [
        ("analysis", "verifiable-inference", "Three Ways to Check an AI Answer: Proofs, Enclaves and Re-execution Compared",
         "Cryptographic proofs, attested enclaves and sampled re-execution answer different questions at very different costs."),
        ("analysis", "confidential-computing", "Private AI Compute Services: What the Published Designs Let Outsiders Check",
         "Several providers now run AI requests inside attested environments; their public designs differ in what an outsider can verify."),
        ("explainer", "evaluation-audits", "What makes an AI system verifiable?",
         "An orientation to claims, evidence and verifiers, and to the layers where each kind of evidence can be produced."),
        ("explainer", "confidential-computing", "Remote attestation for AI workloads, explained",
         "How CPUs and GPUs report what they loaded, and what a relying party can and cannot conclude from that report."),
        ("guide", "confidential-computing", "How to read a remote attestation report",
         "A worksheet for checking hardware identity, measurements, freshness and session binding before you send data."),
        ("guide", "verifiable-inference", "Checklist: evaluating a verifiable inference claim",
         "Questions to ask when a provider says its model outputs can be verified."),
    ]
    for n, (kind, tid, title, dek) in enumerate(stubs):
        slug = slugify(title)
        featured = "featured: true\n" if n == 2 else ""
        body = "\n\n".join(f"## Section {i}\n\nDraft placeholder text for design review. This paragraph will be replaced by the final article." for i in range(1, 5))
        (arts / slug).mkdir()
        (arts / slug / "en.md").write_text(
            f"---\ntitle: {title}\ndek: {dek}\nkind: {kind}\n{byline(kind, author)}\ntopics: [{tid}]\npublished: 2026-10-19\n{featured}---\n{body}\n",
            encoding="utf-8")
        (arts / slug / "zh.md").write_text(f"---\ntitle: {title}\ndek: {dek}\n---\n{body}\n", encoding="utf-8")
    print(f"topics {len(topics)}, resources {len(resources)}, terms {len(terms)}, news {len(items)}, stubs {len(stubs)}")


if __name__ == "__main__":
    main()
