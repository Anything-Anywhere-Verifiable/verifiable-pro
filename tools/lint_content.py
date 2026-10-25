#!/usr/bin/env python3
"""Editorial lint for verifiable.pro content (warnings, not build errors).

    python3 tools/lint_content.py [slug ...]

With slugs it checks those articles. With none it checks every article, the
pages in content/pages and the texts in the JSON data files in content/.

Articles: structure (news callouts, citations, word counts), the stack layers
of news briefs, the "You need" line of guides, phrases the style guide avoids,
British spellings ("grey", "colour", "centre"), wording that claims more than a
check shows, and Chinese typesetting (spacing
around Latin text, half-width punctuation inside Chinese sentences). An
article's illustration.json gets the same checks on its alt text and caption,
and a caption must say what the picture is and what it does not depict (the
build checks the file's structure and digests). Pages and data files get the
phrase, wording and Chinese typesetting checks.

A few article bodies used the overstated wording before the rule existed.
Bodies stay untouched, because an edit changes the source digest, so
LEGACY_BODY_WORDING lists those known uses. The lint counts them apart as legacy
uses on the last line, which always ends with the number of warnings, and any
further use still warns.
"""

import functools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sitegen import md  # noqa: E402

WORDS = {"news": (200, 520), "analysis": (800, 1900), "explainer": (800, 1900), "guide": (800, 2100)}
BANNED_EN = [
    (r"—", "em dash (use a comma, colon or a new sentence)"),
    (r"\bnot (just|only|merely)\b", "'not just/only' construction"),
    (r"\b(game[- ]changing|revolutionary|unprecedented|groundbreaking|cutting[- ]edge|seamless(ly)?)\b", "hype word"),
    (r"\b(it is worth noting|worth noting|needless to say|in today's world|delve)\b", "stock phrase"),
    (r"\b(convincingly|clearly shows|obviously)\b", "subjective modifier"),
]
# Wording that claims more than a check shows. Attestation establishes or shows
# and never proves; Chinese keeps 远程证明 for attestation and 数学证明 for proofs.
WORDING = [
    (r"\bproves the software", "say what the check establishes or shows about the software that was loaded"),
    (r"\bproves the model", "say what the check establishes about the model"),
    (r"\bguarantees privacy\b", "say what isolation is designed to keep from whom"),
    (r"\bverified services?\b", "report the provider's claim as its claim; the site never calls a service verified"),
    (r"硬件证明", "write 远程证明, or say that the hardware signs a report (硬件签署的证明报告)"),
    (r"能证明什么", "write 能确立什么 or 能说明什么"),
    (r"可证明审计", "write 基于远程证明的审计"),
]
# Known uses of that wording in article bodies that an editor has not yet rewritten:
# (language, slug) -> {phrase: count}. Only these uses in these bodies are allowed;
# any other use warns. The six Chinese bodies that used it were reworded on
# 21 October 2026, so none is allowed now. tests/test_sitegen.py keeps the same
# table (as phrase sets) in its own LEGACY_BODY_WORDING.
LEGACY_BODY_WORDING = {}
# Quoted text reports someone else's words, such as a vendor's claim, so the wording check skips it.
QUOTED = re.compile(r'"[^"\n]{1,200}"|“[^”\n]{1,200}”|「[^」\n]{1,200}」|『[^』\n]{1,200}』')
SMALL = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "nor", "of", "on", "or", "per", "the", "to", "vs", "via", "with", "from", "into", "over"}


def title_case_issues(title):
    words = re.findall(r"[A-Za-z][\w'’-]*", title)
    bad = []
    for i, w in enumerate(words):
        if i and w.lower() in SMALL:
            continue
        if w[0].islower() and not re.match(r"^(e|i|x)[A-Z]", w):
            bad.append(w)
    return bad


def front_matter(path):
    try:
        return md.parse_front_matter(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        return None, str(exc)


def body_h1(body):
    """'# Heading' lines outside code blocks; the build renders them as h2."""
    fence = None
    for line in body.split("\n"):
        s = line.strip()
        if fence:
            fence = None if s.startswith(fence) and not s.strip(fence[0]) else fence
        elif s.startswith(("```", "~~~")):
            fence = s[:3]
        elif s.startswith("# "):
            return s
    return ""


def prose(body):
    """The body in the site's own words: no code, link targets, addresses or block quotes."""
    lines, fence = [], None
    for line in body.split("\n"):
        s = line.strip()
        if fence:
            fence = None if s.startswith(fence) and not s.strip(fence[0]) else fence
        elif s.startswith(("```", "~~~")):
            fence = s[:3]
        elif not s.startswith(">"):
            lines.append(line)
    return re.sub(r"`[^`\n]*`|\]\([^)]*\)|<https?://[^>\s]*>|https?://\S+", " ", "\n".join(lines))


def meta_words(meta):
    """Front matter texts stated by the site itself; source titles are left out."""
    parts = [str(meta.get(key) or "") for key in ("title", "dek", "disclosure", "needs", "caption")]
    changes = meta.get("changes") or []
    parts += [str(line).partition(" | ")[2] for line in (changes if isinstance(changes, list) else [changes])]
    return QUOTED.sub(" ", "\n".join(parts))


def body_words(body):
    """Body prose stated by the site itself, without quotations."""
    return QUOTED.sub(" ", prose(body))


def own_words(meta, body):
    """Front matter texts and body prose stated by the site itself; source titles are left out."""
    return meta_words(meta) + "\n" + body_words(body)


def wording_hits(text):
    """(phrase, warning) for each overstated phrase in a text."""
    return [(m.group(0), f"overstated wording '{m.group(0)}': {advice}")
            for pattern, advice in WORDING for m in re.finditer(pattern, text, re.I)]


def wording(text):
    return [msg for _, msg in wording_hits(text)]


def article_wording(lang, slug, meta, body):
    """Wording warnings for one edition of an article, and the number of legacy uses in its body.

    A body use counts as legacy while LEGACY_BODY_WORDING still allows that
    phrase in that body; uses beyond the allowance warn, and so does an
    allowance the body no longer needs."""
    issues = [f"{lang}: {msg}" for msg in wording(meta_words(meta))]
    allowed = LEGACY_BODY_WORDING.get((lang, slug), {})
    used = {}
    for phrase, msg in wording_hits(body_words(body)):
        used[phrase] = used.get(phrase, 0) + 1
        if used[phrase] > allowed.get(phrase, 0):
            issues.append(f"{lang}: {msg}")
    legacy = sum(min(n, allowed.get(phrase, 0)) for phrase, n in used.items())
    for phrase, n in allowed.items():
        k = used.get(phrase, 0)
        if k < n:
            issues.append(f"{lang}: LEGACY_BODY_WORDING allows '{phrase}' {n} {'time' if n == 1 else 'times'}, but the "
                          f"body now uses it {k} {'time' if k == 1 else 'times'}; lower or remove the allowance in "
                          "tools/lint_content.py and tests/test_sitegen.py")
    return issues, legacy


# American spelling (CONTENT_GUIDE.md, "Style"). Lower case only, so a proper name such as
# the National Cyber Security Centre still passes; link targets and addresses are skipped
BRITISH_EN = re.compile(r"\b(?:grey(?:s|ish|er|est)?|colour(?:s|ed|ful|less|ing)?|centre(?:s|d)?)\b")
BRITISH_LABEL = "use American spelling ('gray', 'color', 'center')"


def style_en(text):
    issues = [f"{label}: '{m.group(0)}'" for pattern, label in BANNED_EN for m in re.finditer(pattern, text, re.I)]
    plain = re.sub(r"\]\([^)]*\)|https?://\S+", " ", text)
    return issues + [f"{BRITISH_LABEL}: '{m.group(0)}'" for m in BRITISH_EN.finditer(plain)]


def zh_typesetting(text):
    """The first spacing problem and the first half-width punctuation problem in a Chinese text."""
    issues = []
    for m in re.finditer(r"[一-鿿][A-Za-z0-9]|[A-Za-z0-9][一-鿿]", text):
        issues.append(f"add a space between Chinese and Latin text near '{m.group(0)}'")
        break
    for m in re.finditer(r"[一-鿿][,;:?!](?!\d)|[一-鿿]\.(\s|$)", text):
        issues.append(f"half-width punctuation after Chinese text near '{m.group(0).strip()}'")
        break
    return issues


def zh_text(meta, body):
    return meta.get("title", "") + "\n" + meta.get("dek", "") + "\n" + re.sub(r"`[^`]*`|\]\([^)]*\)|https?://\S+", "", body)


@functools.lru_cache(maxsize=None)
def stack_ids():
    """Layer ids from content/topics.json, T7 first; empty when the file cannot be read."""
    try:
        stack = json.loads((ROOT / "content" / "topics.json").read_text(encoding="utf-8"))["stack"]
        return tuple(layer["id"] for layer in stack)
    except (OSError, ValueError, KeyError, TypeError):
        return ()


def layer_issues(meta, kind):
    """Stack layers: news briefs name the layers of the claim they report, T7 first, at most three."""
    if "layers" not in meta:
        return ["en: news brief has no layers; add the stack layers of the claim it reports, T7 first"] if kind == "news" else []
    raw = meta["layers"]
    layers = raw if isinstance(raw, list) else [raw]
    issues = []
    if kind == "news" and not layers:
        issues.append("en: news brief has an empty layers list, so lists show no layer codes for it")
    if len(layers) > 3:
        issues.append(f"en: {len(layers)} layers; list at most three")
    known = stack_ids()
    unknown = [layer for layer in layers if known and layer not in known]
    for layer in unknown:
        issues.append(f"en: unknown layer {layer!r}; use a stack id from content/topics.json")
    for layer in sorted({layer for layer in layers if layers.count(layer) > 1}):
        issues.append(f"en: layer {layer!r} is listed twice")
    if known and not unknown and layers != sorted(layers, key=known.index):
        issues.append(f"en: list layers in stack order, T7 first: [{', '.join(sorted(layers, key=known.index))}]")
    return issues


def lint_article(folder):
    """(warnings, legacy uses) for one article folder."""
    issues = []
    en = folder / "en.md"
    meta, body = front_matter(en)
    if meta is None:
        return [f"en: front matter: {body}"], 0
    if body_h1(body):
        issues.append(f"en: '{body_h1(body)[:40]}' uses '#'; the title is the page's only h1, so write '##'")
    kind = meta.get("kind", "")
    words = len(re.sub(r"[`*_>#|\[\]()]", " ", body).split())
    lo, hi = WORDS.get(kind, (0, 10**6))
    if not lo <= words <= hi:
        issues.append(f"en: {words} words, expected {lo}-{hi} for {kind}")
    if kind == "news":
        for box in ("analysis", "checked"):
            if f":::{box}" not in body:
                issues.append(f"en: news brief lacks :::{box} callout")
        bad = title_case_issues(meta.get("title", ""))
        if bad:
            issues.append(f"en: headline not in Title Case ({', '.join(bad[:4])})")
    else:
        t = meta.get("title", "")
        rest = re.findall(r"\b[A-Z][a-z]+\b", t)[1:]
        if kind in ("explainer", "guide") and len(rest) > 3:
            issues.append("en: explainer/guide titles use sentence case")
    issues += layer_issues(meta, kind)
    if kind == "guide" and not meta.get("needs"):
        issues.append("en: guide has no needs line, which Learn shows as 'You need'")
    if "illustration" in meta:
        issues.append("en: remove illustration from the front matter; the lead image is described by illustration.json")
    issues += illustration_issues(folder)
    for pattern, label in BANNED_EN:
        for m in re.finditer(pattern, body + " " + meta.get("title", "") + " " + meta.get("dek", ""), re.I):
            issues.append(f"en: {label}: '{m.group(0)}'")
    found, legacy = article_wording("en", folder.name, meta, body)
    issues += found
    n_sources = len(meta.get("sources") or [])
    cited = {int(n) for grp in re.findall(r"\[\^(\d+(?:\s*,\s*\d+)*)\]", body) for n in re.split(r"\s*,\s*", grp)}
    if n_sources and not cited:
        issues.append("en: sources listed but never cited")
    if cited and max(cited) > n_sources:
        issues.append(f"en: cites [^{max(cited)}] but only {n_sources} sources")
    unused = set(range(1, n_sources + 1)) - cited
    if unused:
        issues.append(f"en: sources never cited: {sorted(unused)}")
    zh = folder / "zh.md"
    if not zh.exists():
        issues.append("zh: missing")
    else:
        zmeta, zbody = front_matter(zh)
        if zmeta is None:
            return issues + [f"zh: front matter: {zbody}"], legacy
        if body_h1(zbody):
            issues.append(f"zh: '{body_h1(zbody)[:40]}' uses '#'; write '##'")
        if meta.get("disclosure") and not zmeta.get("disclosure"):
            issues.append("zh: disclosure not translated (the Chinese page shows the English one)")
        if "layers" in zmeta:
            issues.append("zh: layers is inherited from en.md; remove it here")
        if kind == "guide" and not zmeta.get("needs"):
            issues.append("zh: guide has no needs line; translate the one in en.md")
        if "illustration" in zmeta:
            issues.append("zh: remove illustration from the front matter; the lead image is described by illustration.json")
        zcited = {int(n) for grp in re.findall(r"\[\^(\d+(?:\s*,\s*\d+)*)\]", zbody) for n in re.split(r"\s*,\s*", grp)}
        if zcited != cited:
            issues.append(f"zh: citations {sorted(zcited)} differ from en {sorted(cited)}")
        for box in re.findall(r"^:::(\w+)", body, re.M):
            if f":::{box}" not in zbody:
                issues.append(f"zh: missing :::{box} callout")
        issues += [f"zh: {msg}" for msg in zh_typesetting(zh_text(zmeta, zbody))]
        if zmeta.get("title", "").endswith("。"):
            issues.append("zh: headline ends with a full stop")
        found, zlegacy = article_wording("zh", folder.name, zmeta, zbody)
        issues += found
        legacy += zlegacy
    return issues, legacy


# How an illustration's caption opens in each language (a photo's caption is free)
CAPTION_OPENING = {"en": "Illustration:", "zh": "示意图："}
# What says that the caption names what the picture does not depict
CAPTION_NEGATION = {"en": re.compile(r"\b(?:not|no)\b", re.I), "zh": re.compile(r"不|没有|并非")}
MAX_ALT = {"en": 320, "zh": 140}  # one or two sentences


def illustration_issues(folder):
    """Editorial checks of an article's illustration.json: the alt text and caption in both
    languages follow the style and wording rules, and an illustration's caption says what
    it is and what it does not depict. A file the build would refuse is reported once."""
    path = folder / "illustration.json"
    if not path.exists():
        return []
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        return [f"illustration.json: not valid JSON: {exc}"]
    issues = []
    for key in ("alt", "caption"):
        value = spec.get(key) if isinstance(spec, dict) else None
        for lang in ("en", "zh"):
            text = value.get(lang) if isinstance(value, dict) else None
            if not isinstance(text, str) or not text.strip():
                issues.append(f"illustration.json: {key}.{lang} is missing")
                continue
            where = f"illustration.json: {key}.{lang}"
            found = style_en(text) if lang == "en" else zh_typesetting(text)
            issues += [f"{where}: {msg}" for msg in found + wording(QUOTED.sub(" ", text))]
            if key == "alt" and len(text) > MAX_ALT[lang]:
                issues.append(f"{where}: {len(text)} characters; alt text is one or two sentences")
            if key == "caption" and spec.get("kind") == "illustration":
                if not text.startswith(CAPTION_OPENING[lang]):
                    issues.append(f"{where}: start with {CAPTION_OPENING[lang]!r}")
                if not CAPTION_NEGATION[lang].search(text):
                    issues.append(f"{where}: say what the picture does not depict")
    return issues


def lint_pages():
    """Each page in content/pages, in both languages, as (label, issues)."""
    files = {}
    for path in sorted((ROOT / "content" / "pages").glob("*.md")):
        name, _, lang = path.stem.rpartition(".")
        files.setdefault(name or path.stem, {})[lang if name else ""] = path
    results = []
    for name, by_lang in sorted(files.items()):
        issues = []
        for odd in sorted(set(by_lang) - {"en", "zh"}):
            issues.append(f"{by_lang[odd].name}: page files are named <name>.en.md and <name>.zh.md")
        for lang in ("en", "zh"):
            if lang not in by_lang:
                issues.append(f"{lang}: missing")
                continue
            meta, body = front_matter(by_lang[lang])
            if meta is None:
                issues.append(f"{lang}: front matter: {body}")
                continue
            if body_h1(body):
                issues.append(f"{lang}: '{body_h1(body)[:40]}' uses '#'; the title is the page's only h1, so write '##'")
            if "plate" in meta or "illustration" in meta:
                issues.append(f"{lang}: remove {'plate' if 'plate' in meta else 'illustration'}; pages carry no lead images")
            if lang == "en":
                issues += [f"en: {msg}" for msg in style_en(body + " " + str(meta.get("title", "")) + " " + str(meta.get("dek", "")))]
            else:
                issues += [f"zh: {msg}" for msg in zh_typesetting(zh_text(meta, body))]
                if str(meta.get("title", "")).endswith("。"):
                    issues.append("zh: title ends with a full stop")
            issues += [f"{lang}: {msg}" for msg in wording(own_words(meta, body))]
        results.append((f"pages/{name}", issues))
    return results


def texts(node, path="", lang=None):
    """(path, language, text) for each string under an "en" or "zh" key; ids, URLs and external titles have none."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from texts(value, f"{path}.{key}" if path else str(key), lang or (key if key in ("en", "zh") else None))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            label = value.get("id") if isinstance(value, dict) and isinstance(value.get("id"), str) else i
            yield from texts(value, f"{path}[{label}]", lang)
    elif isinstance(node, str) and lang:
        yield path, lang, node


def lint_data():
    """The texts in each JSON data file in content/, as (label, issues)."""
    results = []
    for path in sorted((ROOT / "content").glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            results.append((path.name, [f"not valid JSON: {exc}"]))
            continue
        issues = []
        for where, lang, text in texts(data):
            found = style_en(text) if lang == "en" else zh_typesetting(re.sub(r"`[^`]*`|\]\([^)]*\)|https?://\S+", "", text))
            found += wording(QUOTED.sub(" ", text))
            issues += [f"{where}: {msg}" for msg in found]
        results.append((path.name, issues))
    return results


def main(argv):
    base = ROOT / "content" / "articles"
    folders = [base / s for s in argv] if argv else sorted(p for p in base.iterdir() if p.is_dir())
    missing = [f.name for f in folders if not (f / "en.md").exists()]
    for name in missing:
        print(f"skipping {name!r}: no content/articles/{name}/en.md")
    folders = [f for f in folders if (f / "en.md").exists()]
    total, legacy, legacy_articles = 0, 0, 0
    for folder in folders:
        issues, uses = lint_article(folder)
        total += len(issues)
        legacy += uses
        legacy_articles += bool(uses)
        for issue in issues:
            print(f"{folder.name}: {issue}")
    # CI skips the summary by its shape ("N articles, ... N warnings"), so the
    # legacy count sits between the two
    note = ""
    if legacy:
        note = (f"{legacy} legacy wording {'use' if legacy == 1 else 'uses'} allowed in {legacy_articles} "
                f"{'article' if legacy_articles == 1 else 'articles'} (LEGACY_BODY_WORDING), ")
    if argv:
        print(f"{len(folders)} articles, {note}{total} warnings")
        return 0
    pages, data = lint_pages(), lint_data()
    for label, issues in pages + data:
        total += len(issues)
        for issue in issues:
            print(f"{label}: {issue}")
    print(f"{len(folders)} articles, {len(pages)} pages, {len(data)} data files, {note}{total} warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
