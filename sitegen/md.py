"""Minimal Markdown renderer for verifiable.pro content.

Standard library only. Supported syntax is documented in README.md:
ATX headings, paragraphs, emphasis, code, links, autolinks, lists (nested,
ordered, task items), blockquotes, fenced code, pipe tables, horizontal
rules, raw HTML blocks, source citations ``[^1]`` and callout containers
``:::kind Optional title`` ... ``:::``.
"""

import html
import re

LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$")
CONTAINER_RE = re.compile(r"^:::\s*([A-Za-z][\w-]*)\s*(.*)$")
# a closing run of #s needs a space before it, so "## Learn C#" keeps its "#"
HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)(?:\s+#+)?\s*$")
EXPLICIT_ID_RE = re.compile(r"^(.*?)\s*\{#([A-Za-z][\w-]*)\}$")
HR_RE = re.compile(r"^(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)$")
HTML_BLOCK_RE = re.compile(r"^<(figure|div|aside|table|details|section|svg|img|p|ol|ul|dl)\b", re.I)
CJK_RE = re.compile(r"[　-〿㐀-鿿＀-￯]")
# [label](target "optional title"); the target may hold one level of balanced
# parentheses, as in https://en.wikipedia.org/wiki/Trust_(social_science)
LINK_RE = re.compile(r"\[([^\]]+)\]\(((?:[^()\s]|\([^()\s]*\))+(?:\s+\"[^\"]*\")?)\)")
URL_SCHEME_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.-]*):")
SAFE_SCHEMES = ("http", "https", "mailto")


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = LINK_RE.sub(r"\1", re.sub(r"\[\^[\d,\s]+\]", "", text))
    text = re.sub(r"[^\w㐀-鿿\s-]", "", text.lower()).strip()
    return re.sub(r"[\s_]+", "-", text) or "section"


class Context:
    """Per-document render state: heading ids, citations, form-control ids."""

    def __init__(self, doc_id="doc", source_count=0, callout_titles=None, resolve=None, reserved=()):
        self.doc_id = doc_id
        self.resolve = resolve or (lambda target: target)
        self.source_count = source_count
        self.callout_titles = callout_titles or {}
        self.headings = []
        self.cited = []
        self.reserved = set(reserved)  # ids the page template uses around the document
        self._ids = set(reserved)
        self._pending = set()  # explicit {#ids} further down, kept free for their headings
        self._controls = 0

    def unique_id(self, text):
        base = slugify(text)
        candidate, n = base, 2
        while candidate in self._ids or candidate in self._pending:
            candidate = f"{base}-{n}"
            n += 1
        self._ids.add(candidate)
        return candidate

    def claim_id(self, hid):
        """Take an explicit heading id; ValueError if the page already uses it."""
        if hid in self.reserved:
            raise ValueError(f"heading id {{#{hid}}} is reserved by the page template")
        if hid in self._ids:
            raise ValueError(f"heading id {{#{hid}}} is used twice")
        self._ids.add(hid)
        self._pending.discard(hid)
        return hid

    def control_id(self):
        self._controls += 1
        return f"{self.doc_id}-check-{self._controls}"


def _join_lines(parts):
    out = ""
    for part in parts:
        if out and not (CJK_RE.match(out[-1]) and CJK_RE.match(part[0])):
            out += " "
        out += part
    return out


def _emphasis(text):
    """Escape text and apply **strong**, *em* and _em_; stash markers pass through."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(?!\s)(.+?)(?<!\s)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])", r"<em>\1</em>", text)
    return re.sub(r"(?<![\w])_(?![\s_])(.+?)(?<![\s_])_(?![\w])", r"<em>\1</em>", text)


def render_inline(text, ctx):
    # NUL brackets the index of a stashed fragment, so it cannot come from content
    text = text.replace("\x00", "")
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return f"\x00{len(stash) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: keep(f"<code>{html.escape(m.group(1))}</code>"), text)

    cites = set()

    def cite(match):
        links = []
        for num in [n.strip() for n in match.group(1).split(",")]:
            if num not in ctx.cited:
                ctx.cited.append(num)
            links.append(f'<a href="#source-{num}" class="cite-link">{num}</a>')
        cites.add(len(stash))
        return keep('<sup class="cite">[' + ", ".join(links) + "]</sup>")

    text = re.sub(r"\[\^(\d+(?:\s*,\s*\d+)*)\]", cite, text)

    def link(match):
        label, target = match.group(1), match.group(2).strip()
        title = ""
        titled = re.match(r'^(\S+)\s+"([^"]*)"$', target)
        if titled:
            target, title = titled.group(1), titled.group(2)
        # a citation inside the label moves after the link: links cannot nest
        moved = [m.group(0) for m in re.finditer(r"\x00(\d+)\x00", label) if int(m.group(1)) in cites]
        rest = re.sub(r"\s*\x00(\d+)\x00", lambda m: "" if int(m.group(1)) in cites else m.group(0), label).strip()
        after = ""
        if moved and rest:
            label, after = rest, "".join(moved)
        scheme = URL_SCHEME_RE.match(target)
        if scheme and scheme.group(1).lower() not in SAFE_SCHEMES:
            return keep(_emphasis(label)) + after  # javascript:, data: and the like stay plain text
        if target.startswith("/") and not target.startswith("//"):
            target = ctx.resolve(target)
        attrs = f' href="{html.escape(target, quote=True)}"'
        if title:
            attrs += f' title="{html.escape(title, quote=True)}"'
        if re.match(r"^(https?:)?//", target):
            attrs += ' rel="noopener" class="ext"'
        # code spans in the label are already stashed and restored below
        return keep(f"<a{attrs}>{_emphasis(label)}</a>") + after

    text = LINK_RE.sub(link, text)
    text = re.sub(
        r"<(https?://[^>\s]+)>",
        lambda m: keep(f'<a href="{html.escape(m.group(1), quote=True)}" rel="noopener" class="ext">{html.escape(m.group(1))}</a>'),
        text,
    )
    text = _emphasis(text)
    for _ in range(len(stash) + 1):  # stashed fragments can hold markers of earlier ones
        if "\x00" not in text:
            break
        text = re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)
    return text


def _fence_open(s):
    """(fence, info) when a stripped line opens a code fence, else None."""
    m = FENCE_RE.match(s)
    if not m or (m.group(1)[0] == "`" and "`" in m.group(2)):
        return None
    return m.group(1), m.group(2).strip()


def _fence_closes(s, fence):
    """A closing fence repeats the opening character at least as many times."""
    return len(s) >= len(fence) and s == fence[0] * len(s)


def _list_interrupts(line):
    """A list item can end a paragraph if it is a bullet or starts at 1 (as in CommonMark)."""
    m = LIST_RE.match(line)
    if not m or not m.group(3).strip():
        return False
    return not m.group(2)[0].isdigit() or int(m.group(2)[:-1]) == 1


def _is_block_start(line, lines, i):
    s = line.strip()
    return bool(
        _fence_open(s)
        or CONTAINER_RE.match(s)
        or s == ":::"
        or HEADING_RE.match(s)
        or HR_RE.match(s)
        or s.startswith(">")
        or _list_interrupts(line)
        or HTML_BLOCK_RE.match(s)
        or ("|" in s and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1].strip()))
    )


def _split_row(row):
    """Cells of a table row; a pipe written as \\| stays in its cell."""
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|") and not row.endswith("\\|"):
        row = row[:-1]
    return [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", row)]


def _table(lines, i, ctx):
    header = _split_row(lines[i])
    aligns = []
    for cell in _split_row(lines[i + 1]):
        if cell.startswith(":") and cell.endswith(":"):
            aligns.append("center")
        elif cell.endswith(":"):
            aligns.append("right")
        else:
            aligns.append("")
    i += 2
    rows = []
    while i < len(lines) and lines[i].strip() and "|" in lines[i]:
        rows.append(_split_row(lines[i]))
        i += 1

    def cell(tag, text, col):
        align = aligns[col] if col < len(aligns) else ""
        style = f' style="text-align:{align}"' if align else ""
        scope = ' scope="col"' if tag == "th" else ""
        return f"<{tag}{scope}{style}>{render_inline(text, ctx)}</{tag}>"

    head = "".join(cell("th", t, c) for c, t in enumerate(header))
    body = "".join("<tr>" + "".join(cell("td", t, c) for c, t in enumerate(r)) + "</tr>" for r in rows)
    return f'<div class="table-wrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>', i


def _list(lines, i, ctx):
    first = LIST_RE.match(lines[i])
    indent = len(first.group(1))
    ordered = first.group(2)[0].isdigit()
    start = int(re.match(r"\d+", first.group(2)).group(0)) if ordered else 1
    items = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            nxt = LIST_RE.match(lines[j]) if j < len(lines) else None
            if nxt and len(nxt.group(1)) >= indent:
                i = j
                continue
            break
        match = LIST_RE.match(line)
        lead = len(line) - len(line.lstrip())
        if HR_RE.match(line.strip()):
            break
        if match and len(match.group(1)) == indent and match.group(2)[0].isdigit() != ordered:
            break
        if match and len(match.group(1)) == indent:
            items.append({"text": [match.group(3).strip()], "children": []})
            i += 1
        elif match and len(match.group(1)) > indent and items:
            child, i = _list(lines, i, ctx)
            items[-1]["children"].append(child)
        elif lead > indent and items:
            items[-1]["text"].append(line.strip())
            i += 1
        else:
            break

    tasks = all(re.match(r"^\[[ xX]\]\s", item["text"][0]) for item in items)
    parts = []
    for item in items:
        text = _join_lines(item["text"])
        children = "".join(item["children"])
        task = re.match(r"^\[([ xX])\]\s+(.*)$", text)
        if task:
            control = ctx.control_id()
            checked = " checked" if task.group(1).lower() == "x" else ""
            parts.append(
                f'<li class="task"><input type="checkbox" id="{control}"{checked}>'
                f'<label for="{control}">{render_inline(task.group(2), ctx)}</label>{children}</li>'
            )
        else:
            parts.append(f"<li>{render_inline(text, ctx)}{children}</li>")
    tag = "ol" if ordered else "ul"
    attrs = ' class="checklist"' if tasks else ""
    if ordered and start != 1:
        attrs += f' start="{start}"'
    return f"<{tag}{attrs}>" + "".join(parts) + f"</{tag}>", i


def _callout(kind, title, inner, ctx):
    label = title or ctx.callout_titles.get(kind, "")
    head = f'<p class="callout-label">{render_inline(label, ctx)}</p>' if label else ""
    return f'<aside class="callout callout-{html.escape(kind)}">{head}<div class="callout-body">{inner}</div></aside>'


def render_blocks(text, ctx):
    lines = text.replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        fence = _fence_open(s)
        if fence:
            lang = fence[1].split()[0] if fence[1] else ""
            buf = []
            i += 1
            while i < len(lines) and not _fence_closes(lines[i].strip(), fence[0]):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{html.escape(lang, quote=True)}"' if lang else ""
            out.append(f'<pre class="code"><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>')
            continue
        container = CONTAINER_RE.match(s)
        if container:
            kind, title = container.group(1), container.group(2).strip()
            buf, depth, inner_fence = [], 1, None
            i += 1
            while i < len(lines):
                inner = lines[i].strip()
                if inner_fence:  # a ":::" line inside a code block is code
                    if _fence_closes(inner, inner_fence):
                        inner_fence = None
                elif _fence_open(inner):
                    inner_fence = _fence_open(inner)[0]
                elif CONTAINER_RE.match(inner):
                    depth += 1
                elif inner == ":::":
                    depth -= 1
                    if depth == 0:
                        break
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(_callout(kind, title, render_blocks("\n".join(buf), ctx), ctx))
            continue
        heading = HEADING_RE.match(s)
        if heading:
            # the page title is the only h1, so "# Heading" in a body becomes an h2
            level, label = max(2, len(heading.group(1))), heading.group(2)
            explicit = EXPLICIT_ID_RE.match(label)
            if explicit:
                label = explicit.group(1)
                hid = ctx.claim_id(explicit.group(2))
            else:
                hid = ctx.unique_id(label)
            ctx.headings.append((level, label, hid))
            out.append(f'<h{level} id="{hid}">{render_inline(label, ctx)}</h{level}>')
            i += 1
            continue
        if HR_RE.match(s):
            out.append("<hr>")
            i += 1
            continue
        if "|" in s and i + 1 < len(lines) and TABLE_SEP_RE.match(lines[i + 1].strip()):
            table, i = _table(lines, i, ctx)
            out.append(table)
            continue
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            out.append(f"<blockquote>{render_blocks(chr(10).join(buf), ctx)}</blockquote>")
            continue
        if LIST_RE.match(line):
            block, i = _list(lines, i, ctx)
            out.append(block)
            continue
        if HTML_BLOCK_RE.match(s):
            buf = []
            while i < len(lines) and lines[i].strip():
                buf.append(lines[i])
                i += 1
            out.append("\n".join(buf))
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not (buf and _is_block_start(lines[i], lines, i)):
            buf.append(lines[i].strip())
            i += 1
        out.append(f"<p>{render_inline(_join_lines(buf), ctx)}</p>")
    return "\n".join(out)


def _explicit_ids(text):
    """The {#id} anchors of a document's headings, outside code blocks."""
    ids, fence = [], None
    for line in text.replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if fence:
            if _fence_closes(s, fence):
                fence = None
            continue
        if _fence_open(s):
            fence = _fence_open(s)[0]
            continue
        heading = HEADING_RE.match(s)
        explicit = EXPLICIT_ID_RE.match(heading.group(2)) if heading else None
        if explicit:
            ids.append(explicit.group(2))
    return ids


def render(text, ctx=None):
    """Render a document. Raises ValueError when two headings claim one {#id}."""
    ctx = ctx or Context()
    ctx._pending.update(_explicit_ids(text))
    return render_blocks(text, ctx), ctx


FM_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*)[ \t]*:(?:[ \t]+(.*)|[ \t]*)$")
FM_ITEM_RE = re.compile(r"^\s*-(?:[ \t]+(.*)|[ \t]*)$")


def parse_front_matter(text):
    """Parse front matter written in a small YAML subset.

    Supported: ``key: value`` scalars (plain, "double" or 'single' quoted),
    ``[inline, lists]``, ``- item`` lists, trailing ``# comments``, plain
    values continued on indented lines, and ``>`` (folded) or ``|`` (literal)
    block values. Raises ValueError for front matter that is not closed or a
    line that is none of these, rather than dropping it silently.
    """
    text = text.lstrip("\ufeff")
    first, _, rest = text.partition("\n")
    if first.rstrip() != "---":
        return {}, text
    close = re.search(r"^---[ \t]*\r?$", rest, re.M)
    if not close:
        raise ValueError("front matter is not closed with ---")
    head, body = rest[:close.start()], rest[close.end():].lstrip("\n")
    data, key, block = {}, None, None
    for n, raw in enumerate(head.split("\n"), 2):
        raw = raw.rstrip("\r")
        if block and (raw[:1] in " \t" or not raw.strip()):
            data[key].append(raw.strip())  # a line of a > or | block value
            continue
        if block:
            data[key] = _end_block(data[key], block)
            block = None
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = FM_ITEM_RE.match(raw)
        if item and key:
            if not isinstance(data.get(key), list):
                data[key] = []
            data[key].append(_plain(item.group(1) or ""))
            continue
        pair = FM_KEY_RE.match(raw)
        if pair:
            key, value = pair.group(1), (pair.group(2) or "").strip()
            if _strip_comment(value) in (">", ">-", "|", "|-"):
                block, data[key] = _strip_comment(value)[0], []
            else:
                data[key] = _value(value) if value else []
            continue
        if raw[:1] in " \t" and key is not None:
            # an indented line continues the previous plain value or list item
            extra = _strip_comment(raw.strip())
            value = data[key]
            if isinstance(value, list) and value and isinstance(value[-1], str):
                value[-1] = _join_lines([value[-1], extra])
            elif isinstance(value, str):
                data[key] = _join_lines([value, extra])
            elif value == []:
                data[key] = extra
            continue
        raise ValueError(f"front matter line {n} is not 'key: value': {raw.strip()[:60]!r}")
    if block:
        data[key] = _end_block(data[key], block)
    return data, body


def _end_block(lines, style):
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) if style == "|" else _join_lines([ln for ln in lines if ln])


def _strip_comment(value):
    """Drop a trailing comment: whitespace, '#', then a space or the end of the line."""
    return re.sub(r"\s+#(?:\s.*)?$", "", value)


def _plain(value):
    """A quoted or plain scalar, without a trailing comment."""
    value = value.strip()
    if value[:1] == '"':
        m = re.match(r'^"((?:[^"\\]|\\.)*)"\s*(?:#.*)?$', value)
        if m:
            return re.sub(r'\\(["\\])', r"\1", m.group(1))
    elif value[:1] == "'":
        m = re.match(r"^'((?:[^']|'')*)'\s*(?:#.*)?$", value)
        if m:
            return m.group(1).replace("''", "'")
    return _strip_comment(value)


def _value(value):
    """A scalar, or an [inline, list] when the brackets enclose the whole value."""
    bare = _strip_comment(value) if value[:1] not in "\"'" else value
    if bare.startswith("[") and bare.endswith("]") and not re.search(r"[\[\]]", bare[1:-1]):
        return [_plain(v) for v in bare[1:-1].split(",") if v.strip()]
    return _plain(value)
