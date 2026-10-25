#!/usr/bin/env python3
"""Static accessibility checks for a verifiable.pro build (standard library only).

    python3 tools/check_a11y.py SITE_DIR [--warnings]

Every HTML page is parsed into a small DOM and checked for:

- a lang attribute on <html>, one <main> and a skip link that reaches it;
- one banner <header> and one contentinfo <footer>; navigation landmarks that
  share a role carry distinct names;
- exactly one <h1>, and heading levels that never skip (h2 followed by h4);
- unique ids, and id references (for, aria-labelledby, aria-describedby,
  aria-controls, aria-owns) that resolve;
- accessible names on links, buttons, form controls, images, <svg role="img">
  and named landmarks; other SVGs are hidden with aria-hidden;
- no focusable element inside an aria-hidden subtree (tabindex="-1" excepted),
  no positive tabindex, and no interactive element inside a link, a button, a
  <summary> or a form control (the body of a <details> fold may hold links,
  buttons and further folds);
- valid aria-current values and list and definition-list structure.

Content in a ``hidden`` subtree (the filter bars and the assistant before
site.js and chat.js run) is checked for ids and names but left out of the
heading outline. With --warnings the script also lists best-practice notes,
such as complementary landmarks nested inside <main>. Focus visibility and
colour contrast need a browser; tools/cdp.mjs covers layout.
"""

import sys
from html.parser import HTMLParser
from pathlib import Path

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
INTERACTIVE = {"a", "button", "input", "select", "textarea", "details", "summary"}
# Interactive elements that must not contain other interactive content: links
# and buttons by their HTML content models, a <summary> because it acts as its
# fold's button, and form controls. The body of a <details> fold is ordinary flow
# content, so a <details> is never the outer element of a nesting error.
NO_INTERACTIVE_INSIDE = INTERACTIVE - {"details"}
LABELABLE = {"input", "select", "textarea", "meter", "output", "progress", "button"}
SECTIONING = {"article", "aside", "main", "nav", "section"}
CURRENT_VALUES = {"page", "step", "location", "date", "time", "true", "false"}
LANGS = {"en", "zh-CN"}
NAME_FROM_CONTENT = {"a", "button", "h1", "h2", "h3", "h4", "h5", "h6", "summary", "label", "legend", "caption", "th", "td",
                     "li", "dt", "dd", "option", "figcaption", "p", "span", "code", "strong", "em", "time", "sup", "abbr", "dfn", "b", "i"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent", "line")

    def __init__(self, tag, attrs, parent, line):
        self.tag, self.attrs, self.children, self.parent, self.line = tag, attrs, [], parent, line

    def get(self, key, default=None):
        return self.attrs.get(key, default)

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def walk(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()


class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#document", {}, None, 0)
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, {k: ("" if v is None else v) for k, v in attrs}, self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, {k: ("" if v is None else v) for k, v in attrs}, self.stack[-1], self.getpos()[0])
        self.stack[-1].children.append(node)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def hidden_from_at(node):
    """True when the node or an ancestor is aria-hidden or hidden."""
    for n in [node, *node.ancestors()]:
        if n.get("aria-hidden") == "true" or "hidden" in n.attrs:
            return True
    return False


def in_hidden_attr(node):
    return any("hidden" in n.attrs for n in [node, *node.ancestors()])


class Doc:
    """The ids and labels of one page, for name lookups."""

    def __init__(self, nodes):
        self.ids, self.labels = {}, [n for n in nodes if n.tag == "label"]

    def __contains__(self, key):
        return key in self.ids

    def __getitem__(self, key):
        return self.ids[key]

    def get(self, key):
        return self.ids.get(key)


def text_of(node, ids, skip_hidden=True):
    """Accessible text of a subtree (a simplified accessible-name computation)."""
    out = []
    for child in node.children:
        if isinstance(child, str):
            out.append(child)
            continue
        if skip_hidden and child.get("aria-hidden") == "true":
            continue
        if child.tag in ("script", "style", "template"):
            continue
        if child.tag == "img":
            out.append(child.get("alt", ""))
        elif child.tag == "svg":
            out.append(name_of(child, ids) if child.get("role") == "img" else "")
        elif child.get("aria-label", "").strip():
            out.append(child.get("aria-label"))
        else:
            out.append(text_of(child, ids, skip_hidden))
    return " ".join(" ".join(out).split())


def name_of(node, ids):
    refs = node.get("aria-labelledby")
    if refs is not None:
        parts = [text_of(ids[r], ids, skip_hidden=False) for r in refs.split() if r in ids]
        name = " ".join(p for p in parts if p)
        if name:
            return name
    if node.get("aria-label", "").strip():
        return node.get("aria-label").strip()
    if node.tag == "img":
        return node.get("alt", "").strip()
    if node.tag == "svg":
        titles = [c for c in node.children if isinstance(c, Node) and c.tag == "title"]
        return text_of(titles[0], ids) if titles else ""
    if node.tag in ("input", "select", "textarea"):
        nid = node.get("id")
        labels = [lab for lab in ids.labels if nid and lab.get("for") == nid]
        labels += [a for a in node.ancestors() if a.tag == "label"]
        name = " ".join(text_of(lab, ids) for lab in labels).strip()
        return name or node.get("title", "").strip() or (node.get("value", "") if node.get("type") in ("submit", "button", "reset") else "")
    if node.tag in NAME_FROM_CONTENT:
        return text_of(node, ids) or node.get("title", "").strip()
    return node.get("title", "").strip()


def focusable(node):
    if "disabled" in node.attrs:
        return False
    tabindex = node.get("tabindex")
    if tabindex is not None:
        try:
            return int(tabindex) >= 0
        except ValueError:
            return False
    if node.tag == "a":
        return "href" in node.attrs
    return node.tag in ("button", "select", "textarea", "summary") or (node.tag == "input" and node.get("type") != "hidden")


def landmark(node):
    """The landmark role of a node, or None."""
    role = node.get("role")
    if role in ("banner", "contentinfo", "main", "navigation", "complementary", "search", "region", "form"):
        if role in ("region", "form") and not (node.get("aria-label") or node.get("aria-labelledby")):
            return None
        return role
    if role:
        return None
    scoped = not any(a.tag in SECTIONING for a in node.ancestors())
    named = bool(node.get("aria-label") or node.get("aria-labelledby"))
    if node.tag == "header":
        return "banner" if scoped else None
    if node.tag == "footer":
        return "contentinfo" if scoped else None
    if node.tag == "main":
        return "main"
    if node.tag == "nav":
        return "navigation"
    if node.tag == "aside":
        top = not any(a.tag in ("article", "aside", "nav", "section") for a in node.ancestors())
        return "complementary" if top or named else None
    if node.tag == "section":
        return "region" if named else None
    if node.tag == "form":
        return "form" if named else None
    return None


def check_page(path, rel):
    builder = Builder()
    builder.feed(path.read_text(encoding="utf-8"))
    builder.close()
    root = builder.root
    nodes = list(root.walk())
    errors, warnings = [], []

    def err(node, msg):
        errors.append(f"{rel}:{node.line if node else 0}: {msg}")

    def warn(node, msg):
        warnings.append(f"{rel}:{node.line if node else 0}: {msg}")

    ids = Doc(nodes)
    for n in nodes:
        nid = n.get("id")
        if nid is None:
            continue
        if not nid.strip() or any(c.isspace() for c in nid):
            err(n, f"invalid id {nid!r}")
        if nid in ids:
            err(n, f"duplicate id {nid!r} (first on line {ids[nid].line})")
        else:
            ids.ids[nid] = n

    html_el = next((n for n in nodes if n.tag == "html"), None)
    is_fragment = html_el is None  # the artifact-mode home page is a fragment
    if not is_fragment and html_el.get("lang") not in LANGS:
        err(html_el, f"<html lang={html_el.get('lang')!r}>")
    for n in nodes:
        if "lang" in n.attrs and n.get("lang") not in LANGS:
            err(n, f"unexpected lang={n.get('lang')!r} on <{n.tag}>")
        for key in ("hreflang",):
            # a <link> in the head may also name x-default, the page for readers of neither language
            allowed = LANGS | {"x-default"} if n.tag == "link" else LANGS
            if key in n.attrs and n.get(key) not in allowed:
                err(n, f"unexpected {key}={n.get(key)!r}")

    # landmarks
    mains = [n for n in nodes if landmark(n) == "main"]
    if len(mains) != 1:
        err(None, f"{len(mains)} main landmarks")
    elif mains[0].get("id") != "main":
        err(mains[0], "<main> has no id=\"main\" for the skip link")
    skip = next((n for n in nodes if n.tag == "a" and "skip-link" in n.get("class", "").split()), None)
    if skip is None:
        err(None, "no skip link")
    elif skip.get("href", "").lstrip("#") not in ids or skip.get("href", "")[:1] != "#":
        err(skip, f"skip link target {skip.get('href')!r} does not exist")
    elif nodes.index(skip) > min(nodes.index(n) for n in nodes if n.tag in ("a", "button") and focusable(n)):
        err(skip, "the skip link is not the first focusable element")
    marks = [(landmark(n), n) for n in nodes if landmark(n)]
    for role in ("banner", "contentinfo"):
        count = sum(1 for r, _ in marks if r == role)
        if count != 1:
            err(None, f"{count} {role} landmarks")
    seen = {}
    for role, n in marks:
        name = name_of(n, ids) if (n.get("aria-label") or n.get("aria-labelledby")) else ""
        same = [r for r, _ in marks if r == role]
        if len(same) > 1 and role in ("navigation", "complementary", "region", "search", "form") and not name:
            err(n, f"<{n.tag}> {role} landmark without a name among {len(same)}")
        if name:
            key = (role, name)
            if key in seen:
                err(n, f"two {role} landmarks named {name!r}")
            seen[key] = n
        if role == "complementary" and any(landmark(a) == "main" for a in n.ancestors()):
            warn(n, f"<{n.tag} class={n.get('class', '')!r}> is a complementary landmark inside main")
        if (n.get("aria-label") or n.get("aria-labelledby")) and not name:
            err(n, f"<{n.tag}> landmark label resolves to nothing")

    # headings
    heads = [n for n in nodes if n.tag in ("h1", "h2", "h3", "h4", "h5", "h6") and not in_hidden_attr(n)]
    h1s = [n for n in heads if n.tag == "h1"]
    if len(h1s) != 1:
        err(h1s[1] if len(h1s) > 1 else None, f"{len(h1s)} h1 elements")
    prev = 0
    for n in heads:
        level = int(n.tag[1])
        if prev and level > prev + 1:
            err(n, f"heading jumps from h{prev} to h{level}: {text_of(n, ids)[:60]!r}")
        if not prev and level != 1 and not is_fragment:
            err(n, f"first heading is h{level}")
        if not text_of(n, ids):
            err(n, f"empty <{n.tag}>")
        prev = level

    # id references
    for n in nodes:
        for key in ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns"):
            for ref in (n.get(key) or "").split():
                if ref not in ids:
                    err(n, f"{key} points to missing id {ref!r}")
        if n.tag == "label" and n.get("for"):
            target = ids.get(n.get("for"))
            if target is None:
                err(n, f"label for missing id {n.get('for')!r}")
            elif target.tag not in LABELABLE:
                err(n, f"label for <{target.tag}>, which is not labelable")

    # names, focus and nesting
    for n in nodes:
        tag = n.tag
        hidden = hidden_from_at(n)
        if tag == "a" and "href" in n.attrs and not hidden and not name_of(n, ids):
            err(n, f"link without a name: href={n.get('href')!r}")
        if tag == "button" and not name_of(n, ids):
            err(n, "button without a name")
        if tag in ("input", "select", "textarea") and n.get("type") != "hidden" and not name_of(n, ids):
            err(n, f"<{tag} id={n.get('id')!r}> without a label")
        if tag == "img" and "alt" not in n.attrs:
            err(n, f"<img src={n.get('src')!r}> without alt")
        if tag == "svg" and not hidden and not any(a.tag == "svg" for a in n.ancestors()):
            if n.get("role") == "img":
                if not name_of(n, ids):
                    err(n, "<svg role=img> without a name")
            elif not (n.get("aria-label") or n.get("aria-labelledby")):
                err(n, "<svg> without role=img and a name, or aria-hidden")
        if hidden and not in_hidden_attr(n) and focusable(n):
            err(n, f"focusable <{tag}> inside aria-hidden")
        tabindex = n.get("tabindex")
        if tabindex is not None and tabindex.lstrip("-").isdigit() and int(tabindex) > 0:
            err(n, f"positive tabindex on <{tag}>")
        if tag in INTERACTIVE and (tag != "a" or "href" in n.attrs):
            # a fold's body may hold links and buttons, but a <details> inside a link is still flagged
            outer = next((a for a in n.ancestors()
                          if a.tag in NO_INTERACTIVE_INSIDE and (a.tag != "a" or "href" in a.attrs)), None)
            if outer is not None:
                err(n, f"<{tag}> nested inside <{outer.tag}>")
        if "aria-current" in n.attrs and n.get("aria-current") not in CURRENT_VALUES:
            err(n, f"aria-current={n.get('aria-current')!r}")
        if tag in ("ul", "ol"):
            bad = sorted({c.tag for c in n.children if isinstance(c, Node) and c.tag not in ("li", "script", "template")})
            if bad or any(isinstance(c, str) and c.strip() for c in n.children):
                err(n, f"<{tag}> has children other than <li>: {bad or 'text'}")
        if tag == "li" and n.parent is not None and n.parent.tag not in ("ul", "ol", "menu"):
            err(n, f"<li> inside <{n.parent.tag}>")
        if tag == "dl":
            for c in n.children:
                if isinstance(c, Node) and c.tag not in ("dt", "dd", "div", "script", "template"):
                    err(n, f"<dl> contains <{c.tag}>")
                if isinstance(c, Node) and c.tag == "div":
                    inner = {g.tag for g in c.children if isinstance(g, Node)}
                    if not inner <= {"dt", "dd"} or "dt" not in inner or "dd" not in inner:
                        err(c, f"<div> in <dl> must hold dt and dd, not {sorted(inner)}")
        if tag in ("dt", "dd"):
            parent = n.parent
            if parent is not None and parent.tag == "div":
                parent = parent.parent
            if parent is None or parent.tag != "dl":
                err(n, f"<{tag}> outside <dl>")
        if tag == "table" and not any(isinstance(c, Node) and c.tag == "th" for c in n.walk()):
            err(n, "<table> without header cells")
        if tag == "section" and not (n.get("aria-label") or n.get("aria-labelledby")):
            if not any(c.tag in ("h1", "h2", "h3", "h4", "h5", "h6") for c in n.walk()):
                warn(n, f"<section class={n.get('class', '')!r}> has no heading or name")
    return errors, warnings


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    root = Path(argv[0]).resolve()
    show_warnings = "--warnings" in argv
    pages = sorted(p for p in root.rglob("*.html") if " " not in p.name)
    errors, warnings = [], []
    for path in pages:
        e, w = check_page(path, path.relative_to(root).as_posix())
        errors += e
        warnings += w
    print(f"checked {len(pages)} pages; {len(errors)} problems, {len(warnings)} notes")
    for line in errors[:300]:
        print("  " + line)
    if show_warnings:
        for line in warnings[:300]:
            print("  note: " + line)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
