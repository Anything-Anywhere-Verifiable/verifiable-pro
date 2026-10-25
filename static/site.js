/* verifiable.pro: progressive enhancements. Every page works without this file. */
(function () {
  "use strict";

  document.querySelectorAll("link[data-font-css]").forEach(function (l) { l.rel = "stylesheet"; });

  var site = document.querySelector(".site");
  var root = (site && site.getAttribute("data-root")) || "/";
  var pageLang = (site && site.getAttribute("data-lang")) || "en";
  var each = function (list, fn) { Array.prototype.forEach.call(list, fn); };

  function link(path) {
    if (root === "/") return path;
    var parts = path.split("#");
    var p = parts[0].replace(/^\//, "");
    if (p === "" || p.slice(-1) === "/") p += "index.html";
    return root + p + (parts[1] ? "#" + parts[1] : "");
  }

  function esc(text) {
    return String(text).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  /* lang for text in the other language than the page, as render.island_lang does. */
  var CJK = /[　-〿㐀-鿿豈-﫿＀-￯]/;
  function langAttr(text) {
    text = String(text || "");
    if (pageLang === "zh" && /[A-Za-z]/.test(text) && !CJK.test(text)) return ' lang="en"';
    if (pageLang === "en" && CJK.test(text) && !/[A-Za-z]/.test(text)) return ' lang="zh-CN"';
    return "";
  }

  /* One polite status line for messages that have no visible place to appear. */
  var announcer = null;
  function announce(msg) {
    if (!announcer) {
      announcer = document.createElement("p");
      announcer.className = "vh";
      announcer.setAttribute("role", "status");
      (site || document.body).appendChild(announcer);
    }
    announcer.textContent = "";
    setTimeout(function () { announcer.textContent = msg; }, 50);
  }

  /* The number in a control's or heading's .count, rewritten only when it changes. */
  function setCount(el, n) {
    var c = el && el.querySelector(".count");
    if (c && c.textContent !== String(n)) c.textContent = n;
  }

  /* Per-reader storage. localStorage can be missing or throw (private windows,
     blocked site data, sandboxed frames), so every access sits in try/catch and
     nothing on any page depends on what it returns. */
  function storeGet(key) {
    try { return window.localStorage.getItem(key); } catch (e) { return null; }
  }
  function storeSet(key, value) {
    try { window.localStorage.setItem(key, value); } catch (e) { /* full or blocked: the marks are optional */ }
  }

  /* Light or dark. The page follows the system until the reader picks one with the
     header's toggle; the choice is kept in localStorage ("vp-theme") and applied by
     the inline script in the head before the first paint, as data-theme on <html>. */
  var themeBtn = document.querySelector("[data-theme-toggle]");
  if (themeBtn) {
    var darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
    var isDark = function () {
      var set = document.documentElement.getAttribute("data-theme");
      return set ? set === "dark" : darkQuery.matches;
    };
    var paintTheme = function () {
      var dark = isDark();
      themeBtn.setAttribute("aria-label", themeBtn.getAttribute(dark ? "data-label-light" : "data-label-dark"));
      themeBtn.title = themeBtn.getAttribute("aria-label");
      themeBtn.setAttribute("aria-pressed", dark ? "true" : "false");
    };
    themeBtn.hidden = false;
    paintTheme();
    themeBtn.addEventListener("click", function () {
      var next = isDark() ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      storeSet("vp-theme", next);
      paintTheme();
    });
    if (darkQuery.addEventListener) darkQuery.addEventListener("change", paintTheme);
  }

  /* Read marks: the slugs of articles this browser has read to the end, newest last. */
  var READ_KEY = "vp-read";
  var READ_MAX = 200;
  function readSlugs() {
    var raw = storeGet(READ_KEY);
    if (!raw) return [];
    try {
      var list = JSON.parse(raw);
      return Array.isArray(list) ? list.filter(function (s) { return typeof s === "string"; }) : [];
    } catch (e) {
      return [];
    }
  }
  function markRead(slug) {
    var list = readSlugs().filter(function (s) { return s !== slug; });
    list.push(slug);
    storeSet(READ_KEY, JSON.stringify(list.slice(-READ_MAX)));
  }

  /* Latest: the kind buttons, the TEE toggle and the stack-layer select combine.
     The hash holds the view as tokens joined by "+": one kind (news, analysis,
     explainer, guide), "tee" and one layer code (t1 to t7), as in #news+tee+t2.
     Any other hash, such as a month anchor, shows every story. Each control's
     count says how many stories it would show with the other two filters, and a
     control that would show none is disabled, so the river is never empty. */
  var group = document.querySelector('[data-filter-group="latest"]');
  var river = document.querySelector('[data-filter-target="latest"]');
  if (group && river) {
    group.hidden = false;
    var kinds = Array.prototype.map.call(group.querySelectorAll(".filter-btn[data-filter]"), function (b) {
      /* off: the build disabled the button because its kind has no stories */
      return { el: b, kind: b.getAttribute("data-filter"), off: b.disabled };
    });
    var teeBtn = group.querySelector('[data-toggle="tee"]');
    var teeOff = !!(teeBtn && teeBtn.disabled);
    var layerSel = group.querySelector("#layer-filter");
    var codeToLayer = {};
    var layerToCode = {};
    if (layerSel) {
      each(layerSel.options, function (o) {
        var code = (o.getAttribute("data-code") || "").toLowerCase();
        if (code && o.value) { codeToLayer[code] = o.value; layerToCode[o.value] = code; }
      });
    }
    var rows = Array.prototype.map.call(river.querySelectorAll(".river-item"), function (el) {
      return {
        el: el,
        kind: el.getAttribute("data-kind"),
        tee: el.getAttribute("data-tee") === "1",
        layers: " " + (el.getAttribute("data-layers") || "").trim().split(/\s+/).join(" ") + " "
      };
    });
    var view = function (kind, tee, layer) { return { kind: kind, tee: tee, layer: layer }; };
    var ALL = view("all", false, "");
    var matches = function (row, v) {
      return (v.kind === "all" || row.kind === v.kind) && (!v.tee || row.tee) &&
        (!v.layer || row.layers.indexOf(" " + v.layer + " ") >= 0);
    };
    var count = function (v) {
      var n = 0;
      rows.forEach(function (r) { if (matches(r, v)) n++; });
      return n;
    };
    /* The view a filter hash names, or null when the hash is not one: it has
       an unknown or repeated token, or a kind or toggle the build disabled. */
    var parse = function (hash) {
      if (!hash) return ALL;
      var v = view("all", false, "");
      var kindSet = false;
      var ok = hash.toLowerCase().split("+").every(function (t) {
        /* links from before the layers were renamed T1 to T7 say l1 to l7 */
        if (/^l[1-7]$/.test(t)) t = "t" + t.charAt(1);
        var k = kinds.filter(function (x) { return x.kind === t && !x.off; })[0];
        if (k) {
          if (kindSet) return false;
          kindSet = true;
          v.kind = t;
          return true;
        }
        if (t === "tee" && teeBtn && !teeOff) {
          if (v.tee) return false;
          v.tee = true;
          return true;
        }
        if (Object.prototype.hasOwnProperty.call(codeToLayer, t)) {
          if (v.layer) return false;
          v.layer = codeToLayer[t];
          return true;
        }
        return false;
      });
      return ok ? v : null;
    };
    /* A view with no stories, which only a typed or stale hash can name, shows every story */
    var orAll = function (v) { return v && count(v) ? v : ALL; };
    var current = ALL;
    var apply = function (v) {
      current = v;
      kinds.forEach(function (k) {
        var on = k.kind === v.kind;
        var n = count(view(k.kind, v.tee, v.layer));
        k.el.setAttribute("aria-pressed", on ? "true" : "false");
        k.el.disabled = k.off || (!on && n === 0);
        setCount(k.el, n);
      });
      if (teeBtn) {
        var teeN = count(view(v.kind, true, v.layer));
        teeBtn.setAttribute("aria-pressed", v.tee ? "true" : "false");
        teeBtn.disabled = teeOff || (!v.tee && teeN === 0);
        setCount(teeBtn, teeN);
      }
      if (layerSel) {
        layerSel.value = v.layer;
        each(layerSel.options, function (o) {
          o.disabled = !!o.value && o.value !== v.layer && count(view(v.kind, v.tee, o.value)) === 0;
        });
      }
      rows.forEach(function (r) { r.el.hidden = !matches(r, v); });
      river.querySelectorAll(".river-group").forEach(function (g) {
        g.hidden = !g.querySelector(".river-item:not([hidden])");
      });
    };
    var write = function () {
      var t = [];
      if (current.kind !== "all") t.push(current.kind);
      if (current.tee) t.push("tee");
      if (current.layer && layerToCode[current.layer]) t.push(layerToCode[current.layer]);
      try { history.replaceState(null, "", t.length ? "#" + t.join("+") : location.pathname + location.search); } catch (e) { /* ignore */ }
    };
    var choose = function (v) {
      apply(orAll(v));
      write();
    };
    kinds.forEach(function (k) {
      k.el.addEventListener("click", function () { choose(view(k.kind, current.tee, current.layer)); });
    });
    if (teeBtn) {
      teeBtn.addEventListener("click", function () { choose(view(current.kind, !current.tee, current.layer)); });
    }
    if (layerSel) {
      layerSel.addEventListener("change", function () { choose(view(current.kind, current.tee, layerSel.value)); });
    }
    var hashText = function () {
      var hash = location.hash.replace(/^#/, "");
      try { hash = decodeURIComponent(hash); } catch (e) { /* a malformed escape stays as typed */ }
      return hash;
    };
    window.addEventListener("hashchange", function () {
      var hash = hashText();
      var v = parse(hash);
      if (v) { apply(orAll(v)); return; }
      /* Any other hash shows every story, except an anchor elsewhere on the
         page, such as the skip link's #main, which keeps the view. An anchor
         inside the river (a month heading) is scrolled to once every story shows. */
      var target = hash ? document.getElementById(hash) : null;
      if (target && !river.contains(target) && !group.contains(target)) return;
      apply(ALL);
      if (target) target.scrollIntoView();
    });
    apply(orAll(parse(hashText())));
  }

  /* Resources: search and filter the catalog. A TEE area subhead hides with its list. */
  var form = document.querySelector("[data-resource-filters]");
  if (form) {
    form.hidden = false;
    var q = form.querySelector("#res-q");
    var selects = [
      { el: form.querySelector("#res-topic"), ok: function (item, value) { return (" " + (item.getAttribute("data-topics") || "") + " ").indexOf(" " + value + " ") >= 0; } },
      { el: form.querySelector("#res-area"), ok: function (item, value) { return item.getAttribute("data-area") === value; } },
      { el: form.querySelector("#res-type"), ok: function (item, value) { return item.getAttribute("data-type") === value; } }
    ].filter(function (s) { return s.el; });
    var catalog = document.querySelector(".resource-catalog");
    var items = document.querySelectorAll(".resource-catalog .resource");
    var countLine = document.querySelector(".result-count");
    var empty = document.querySelector("[data-empty]");
    var template = countLine ? countLine.getAttribute("data-template") || "" : "";
    var visible = function (box) { return box.querySelectorAll(".resource:not([hidden])").length; };
    var update = function () {
      var terms = q ? q.value.toLowerCase().split(/\s+/).filter(Boolean) : [];
      var shown = 0;
      items.forEach(function (item) {
        var text = item.getAttribute("data-text") || "";
        var ok = selects.every(function (s) { return !s.el.value || s.ok(item, s.el.value); }) &&
          terms.every(function (t) { return text.indexOf(t) >= 0; });
        item.hidden = !ok;
        if (ok) shown++;
      });
      if (catalog) {
        /* Subheads count what is shown under them, and so do the group titles */
        catalog.querySelectorAll(".resource-list[data-area]").forEach(function (list) {
          var n = visible(list);
          var head = list.previousElementSibling;
          list.hidden = !n;
          if (head && head.classList.contains("catalog-sub")) {
            head.hidden = !n;
            setCount(head, n);
          }
        });
        catalog.querySelectorAll(".catalog-group").forEach(function (g) {
          var n = visible(g);
          g.hidden = !n;
          setCount(g.querySelector(".catalog-title"), n);
        });
      }
      var text = template.replace("{shown}", shown).replace("{total}", items.length);
      if (countLine && text && countLine.textContent !== text) countLine.textContent = text;
      if (empty) empty.hidden = shown !== 0;
    };
    form.addEventListener("input", update);
    form.addEventListener("change", update);
    form.addEventListener("submit", function (e) { e.preventDefault(); update(); });
    update();
  }

  /* Learn: mark the path steps this reader has read to the end. The marks live
     only in this browser and change nothing else on the page. The label comes
     from data-read-label on the path when the build sets it. */
  var steps = document.querySelectorAll(".path-step[data-slug]");
  if (steps.length) {
    var done = readSlugs();
    steps.forEach(function (step) {
      if (done.indexOf(step.getAttribute("data-slug")) < 0) return;
      var kindLine = step.querySelector(".path-kind");
      step.classList.add("is-read");
      if (!kindLine || kindLine.querySelector(".path-read")) return;
      var labelled = step.closest("[data-read-label]");
      var mark = document.createElement("span");
      mark.className = "path-read";
      mark.textContent = (labelled && labelled.getAttribute("data-read-label")) || (pageLang === "zh" ? "已读" : "Read");
      kindLine.appendChild(document.createTextNode(" · "));
      kindLine.appendChild(mark);
    });
  }

  /* Article pages: once the end of the article (the "Check or correct this
     page" block) comes into view, remember the article as read for Learn. */
  if (site && site.classList.contains("page-article") && "IntersectionObserver" in window) {
    var canonical = document.querySelector('link[rel="canonical"]');
    var slug = canonical && /\/articles\/([a-z0-9]+(?:-[a-z0-9]+)*)\/$/.exec(canonical.getAttribute("href") || "");
    var end = document.querySelector("main .check-strip") || document.querySelector("main .sources");
    if (slug && end) {
      var watch = new IntersectionObserver(function (entries) {
        if (!entries.some(function (e) { return e.isIntersecting; })) return;
        watch.disconnect();
        markRead(slug[1]);
      });
      watch.observe(end);
    }
  }

  /* Copy a digest or command to the clipboard; fall back to selecting it. */
  document.querySelectorAll(".copy-btn").forEach(function (btn) {
    var label = btn.textContent; /* read once: a second click while "Copied" shows must not keep it */
    var timer = null;
    btn.addEventListener("click", function () {
      var value = btn.getAttribute("data-copy");
      var done = function () {
        var copied = btn.getAttribute("data-copied") || label;
        btn.textContent = copied;
        announce(copied);
        clearTimeout(timer);
        timer = setTimeout(function () { btn.textContent = label; }, 1600);
      };
      var select = function () {
        var code = btn.parentNode.querySelector("code");
        if (!code) return;
        code.textContent = value;
        var range = document.createRange();
        range.selectNodeContents(code);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
      };
      try {
        navigator.clipboard.writeText(value).then(done, select);
      } catch (e) {
        select();
      }
    });
  });

  /* Site search over a prebuilt JSON index. */
  var search = document.querySelector("[data-site-search]");
  if (search) {
    var input = search.querySelector("input");
    var results = document.querySelector(".search-results");
    var live = document.querySelector("[data-search-count]");
    var labels = {};
    try { labels = JSON.parse(search.getAttribute("data-labels") || "{}"); } catch (e) { /* type names fall back to the ids */ }
    var hint = search.getAttribute("data-hint");
    var none = search.getAttribute("data-none");
    var countText = function (n) {
      var t = n === 1 ? search.getAttribute("data-count-one") : search.getAttribute("data-count");
      return (t || "{n}").replace("{n}", n);
    };
    var index = null;
    var failed = false;
    var order = ["article", "topic", "page", "term", "resource"];
    var said = null;
    var sayTimer = null;
    /* Results are not a live region (every keystroke would read them all);
       a short status line announces the count once typing pauses. */
    var say = function (msg) {
      if (!live) return;
      clearTimeout(sayTimer);
      sayTimer = setTimeout(function () {
        if (msg !== said) { live.textContent = msg; said = msg; }
      }, 600);
    };
    var status = function (msg) { results.innerHTML = '<p class="search-status">' + esc(msg) + "</p>"; };
    var render = function () {
      var raw = input.value.trim().toLowerCase();
      /* one Chinese character is a word; one Latin letter matches too much */
      if (raw.length < 2 && !(raw.length === 1 && CJK.test(raw))) { status(hint); say(""); return; }
      if (!index) { if (failed) { status(none); say(none); } return; }
      var terms = raw.split(/\s+/);
      var hits = index.map(function (e) {
        var title = e.title.toLowerCase();
        var hay = (title + " " + (e.text || "") + " " + (e.meta || "")).toLowerCase();
        if (!terms.every(function (t) { return hay.indexOf(t) >= 0; })) return null;
        var score = title.indexOf(raw) === 0 ? 3 : title.indexOf(raw) >= 0 ? 2 : 1;
        return { e: e, score: score };
      }).filter(Boolean);
      if (!hits.length) { status(none); say(none); return; }
      var html = "";
      var listed = 0;
      order.forEach(function (type) {
        var group = hits.filter(function (h) { return h.e.type === type; })
          .sort(function (a, b) { return b.score - a.score; }).slice(0, 12);
        if (!group.length) return;
        listed += group.length;
        html += '<section class="search-group"><h2 class="mini-label">' + esc(labels[type] || type) + '</h2><ol class="search-list">';
        group.forEach(function (h) {
          var href = h.e.url ? h.e.url : link(h.e.path);
          var ext = h.e.url ? ' rel="noopener" class="ext"' : "";
          html += '<li><a href="' + esc(href) + '"' + ext + langAttr(h.e.title) + ">" + esc(h.e.title) + "</a>" +
            (h.e.meta ? '<span class="search-meta"' + langAttr(h.e.meta) + ">" + esc(h.e.meta) + "</span>" : "") +
            (h.e.text ? "<p" + langAttr(h.e.text) + ">" + esc(h.e.text) + "</p>" : "") + "</li>";
        });
        html += "</ol></section>";
      });
      results.innerHTML = html;
      say(countText(listed));
    };
    search.addEventListener("submit", function (e) { e.preventDefault(); render(); });
    input.addEventListener("input", render);
    /* ?q= (a submitted form, or a shared link) fills the field */
    var initial = new URLSearchParams(location.search).get("q");
    if (initial) input.value = initial;
    fetch(search.getAttribute("data-index"))
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { index = data; render(); })
      .catch(function () { failed = true; render(); });
  }
})();

/* Stack cards. Hovering or focusing a story's layer codes ("T2 T1") shows the
   whole verification stack with that story's layers marked. The codes are
   links to the layers on the Stack page, so without this script, and on touch
   screens, they open the explanation there instead. */
(function () {
  "use strict";
  var source = document.getElementById("stack-data");
  if (!source || !document.body.addEventListener) return;
  var stack;
  try { stack = JSON.parse(source.textContent); } catch (e) { return; }
  var card = null, owner = null, timer = 0;
  var SELECTOR = "a.tag-layers[data-layers]";

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text) node.textContent = text;
    return node;
  }
  function build(link) {
    var on = (link.getAttribute("data-layers") || "").split(" ");
    var box = el("div", "stack-pop");
    box.id = "stack-pop";
    box.setAttribute("role", "tooltip");
    box.appendChild(el("p", "stack-pop-title", stack.title));
    var list = el("ol", "stack-pop-list");
    stack.layers.forEach(function (layer) {
      var row = el("li", "stack-pop-row");
      if (on.indexOf(layer.id) >= 0) row.className += " is-on";
      if (layer.reach === "direct") row.className += " is-direct";
      row.setAttribute("data-bind", layer.bind || "none");
      row.appendChild(el("span", "stack-pop-code", layer.code));
      row.appendChild(el("span", "stack-pop-name", layer.name));
      list.appendChild(row);
    });
    box.appendChild(list);
    box.appendChild(el("p", "stack-pop-note", stack.note));
    return box;
  }
  function place() {
    if (!card || !owner) return;
    var r = owner.getBoundingClientRect();
    var w = card.offsetWidth, h = card.offsetHeight;
    var vw = document.documentElement.clientWidth;
    var x = Math.max(8, Math.min(r.left, vw - w - 8));
    var y = r.bottom + 8 + h <= window.innerHeight ? r.bottom + 8 : Math.max(8, r.top - h - 8);
    card.style.left = (x + window.pageXOffset) + "px";
    card.style.top = (y + window.pageYOffset) + "px";
  }
  function hide() {
    clearTimeout(timer);
    if (card && card.parentNode) card.parentNode.removeChild(card);
    if (owner) owner.removeAttribute("aria-describedby");
    card = owner = null;
  }
  function show(link) {
    clearTimeout(timer);
    if (owner === link) return;
    hide();
    owner = link;
    card = build(link);
    document.body.appendChild(card);
    link.setAttribute("aria-describedby", "stack-pop");
    place();
  }
  function from(target) { return target && target.closest ? target.closest(SELECTOR) : null; }

  document.addEventListener("pointerover", function (e) {
    var link = from(e.target);
    if (link && e.pointerType !== "touch") show(link);
  });
  document.addEventListener("pointerout", function (e) {
    var link = from(e.target);
    if (link && link === owner && !link.contains(e.relatedTarget)) timer = setTimeout(hide, 120);
  });
  document.addEventListener("focusin", function (e) { var link = from(e.target); if (link) show(link); });
  document.addEventListener("focusout", function (e) { if (owner && from(e.target) === owner) hide(); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape" && card) hide(); });
  window.addEventListener("resize", place);
  window.addEventListener("scroll", place, { passive: true });
})();
