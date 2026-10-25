#!/usr/bin/env node
// True-width screenshots and layout checks for a verifiable.pro preview build.
//
//   node cdp.mjs shots SITE OUT --pages home,article --widths 390 [--height 2400] [--dark home,article] [--article PATH] [--suffix mobile] [--reduced] [--full] [--open N] [--touch]
//   node cdp.mjs check SITE --pages home,article,... --widths 360,390,768,1024,1440 [--article PATH] [--dark] [--reduced] [--small] [--measure]
//   node cdp.mjs hero SITE [--pages home,zh-home] [--widths 1440,390] [--sizes 1366x768,720x450x2] [--tablets 1024x768,932x430] [--tipsizes 1440x900,1366x768] [--frames] [--cpu 4] [--nojs] [--only finale,cards]
//   node cdp.mjs eval SITE --page home --js EXPR [--width 1440] [--dark] [--reduced]
//   node cdp.mjs zoom SITE OUT.png --page home --width 1440 --clip x,y,w,h [--scale 2] [--dark] [--forced] [--reduced] [--hover SELECTOR]
//
// The browser is $CHROME when it is set. Otherwise it is Google Chrome where macOS
// installs it; on Linux the first of google-chrome, google-chrome-stable, chromium and
// chromium-browser on PATH; on Windows chrome.exe under Program Files.
//
// Page names: home, tee (the TEE hub), latest, topics (the Stack page), topic (the
// first other topic), learn, resources, vision, glossary, about, search, 404,
// article (--article PATH, or the alphabetically first), brief (a news brief that
// is not about TEEs), tee-brief (the DDRop brief) and longform (an explainer).
// Each has a zh- twin, such as zh-tee, except 404.
//
// --reduced emulates prefers-reduced-motion: reduce, and shots then end in -reduced.
// --forced (zoom) emulates forced colours (forced-colors: active).
// --hover SELECTOR (zoom) rests the mouse on the first element that matches before the
// capture, such as a vendor mark in the hero's labels, whose name then shows in its tooltip:
// '.hero-layer[data-n="5"] .hero-ex:nth-child(7 of .hero-ex) svg'.
// --full (shots) captures the whole page height instead of --height.
// --open N (shots, home pages) opens layer N's card before the capture, as a reader
// would: the mouse on its plate from 45em, a tap on its chevron with --touch (the
// capture waits for the page to scroll the card into view) or a click on it on
// phones. The shot is then the viewport, --height tall, ending in -lN.
// --touch (shots) emulates a touch screen: touch events, (hover: none) and
// (pointer: coarse), so touch tablets show the hero's chevrons.
// --small (check) also lists text below 12px, and Chinese text below 13px on zh pages.
//
// `hero` checks the home hero with real mouse, key and touch input. Each --widths width
// runs in a window 900px tall (844px for the motion and phone checks below 768); each
// --sizes entry is a window WxH, or WxHxD for a device scale factor of D, such as
// 1366x768 or 720x450x2, at least 720 wide, where the checks from 45em run.
//   - Checking and motion, at each width: before any layer is checked nothing loops, the
//     pause button is hidden and "Check all layers" stands in its place, the person is
//     gray (grayscale 1), and the hint gives a mouse's line (pointing from 45em, a click on
//     the arrows below it); a real double click on the button checks all seven, the progress
//     says so, the button goes, the pause button shows and takes its focus, the loop keeps
//     running (the second click lands on the pause button, which ignores it), the hint's line
//     drops its promise of colour without changing the hint's height, and the
//     person is in full colour. Then the data rests on one object of every layer in order,
//     T1 to T7, each plate's front edges lighting as it arrives (the loop paused and set to
//     each moment), indigo on T1 and T2 and in the reader's colour above. The pause button
//     switches its label and data-motion between running and paused; the animation is
//     suspended while the scene is off-screen and in a hidden tab (simulated by overriding
//     document.hidden), and runs again when the scene is back in view. Under reduced motion
//     "Check all layers" has the corner until it is clicked, the colour comes back at once
//     and focus goes to the progress; no animation runs, the pause button is hidden, the
//     still-image label shows, the pulse is gone, and the chain is drawn as data-hv-chain
//     says (solid, dashed, or stubs where a binding is missing) with the ring on the
//     person's phone in view. The seven labels and the two links to the Stack page are
//     there, and no caption.
//     The data packets run with the pulse and hold when it is paused; under reduced motion
//     they are not drawn, the dotted route of the reader's data is, and a click on the
//     person shows their moment with no animation running.
//   - The legend, at each width, in light and dark: every sample of the line is stroked in
//     the indigo the scene draws the chain in (the computed stroke of the chain's TEE run,
//     .hv-bm.hv-t), the missing run's at opacity 0.6 and the others at 1, while its words
//     keep their ink; in forced colours every sample is in CanvasText, at opacity 1.
//   - The gray and hero.js, at each width: on a normal load, its load event held back about a
//     second by an image request that the check keeps pending (no network), the person is gray
//     in every frame from the first to the load event and after, and the scene's description gains its
//     sentences on the gray and the data (its data-hv-live); with hero.js blocked, and with it
//     made to throw at its first line, the person is in full colour once the page has loaded
//     (the page's guard removed data-hv-wait) and the description says only what the still
//     scene shows.
//   - Sweeps, from 45em at each width and each --sizes window whose label column fits below
//     the header: the mouse down and up the label column (over the codes and names and the
//     examples between them) and down and up the plates at about 250px/s opens every layer in
//     turn and checks all seven, and on the labels it reaches each label itself, never a card
//     over it; then down and up the names with a 400ms rest on each, where the layer opens and
//     is checked on arrival with no card shown, or, for a name that lies between the card before
//     and that card's own label (that card past it), the name waits while the mouse heads for
//     the card and opens with its card once the mouse has rested on it for 200ms (a shorter stop
//     keeps the card before); after the rest its card shows
//     clear of the next label (and of the pause control, the person's label and the intro), so
//     the sweep goes on. A card that runs past the window's bottom to keep the next label clear
//     is noted. Then a rest on the first name only, T7 going down and T1 going up, the mouse
//     coming onto it along the column and from the gap between the scene and the labels (from
//     the side): its card shows clear of its own examples and of the next label, and the next
//     name opens once the mouse goes on to it and rests there. And where T7's card (T1's going
//     up) opens past the next label after a rest, a straight path at about 250px/s from the name
//     across the next name into the card's stories link keeps the layer open and reaches the
//     link, and a path that stops on the next name opens that layer once the mouse rests there.
//   - From 45em: the person's label, the legend and the hint (the pointer line) are
//     shown. Where the intro stands beside the figure and the window is at least 720px
//     tall, the person's label and the hint end on the first screen, the hint under the
//     label column. On the fresh page the mouse on every example under the names, vendor
//     marks and names, opens and checks no layer; then, with T5's card open from its name, the
//     mouse on a mark of another row clear of the card switches nothing and the card closes
//     once the pointer has been off T5's name and card for the grace (300ms in hero.js), the
//     mark's name in the tooltip. The mouse on each plate opens its layer (data-hv-active, the
//     row's .is-active, data-motion=suspended) with the card shown once it rests: on its
//     preferred side, or the other when only that one has room, clear of its own label; fitted
//     over its label (data-open-place="fit") only when neither side has room. A card that fits
//     lies between the ceiling (the band's top when the intro is beside the figure, else
//     the scene's, below the pause control and the sticky header) and the stage's or
//     the window's bottom; a taller one keeps its head there. It covers neither the
//     pause control, the person's label, the links under the stage nor the intro, and every
//     row, the legend and the hint that it lies over are .is-covered, at opacity 0. With each
//     plate open the person is lit and the data packets are hidden; on T1 and T2 the bubble
//     with the shield and the indigo phone screen show, and on T3 to T7 they do not. Each plate
//     pointed at is checked: after three the marks, the count and half the person's colour,
//     after seven all of it and the hint's line without the promise of colour, and with the
//     last card closed the loop runs. Each name area ("T5 Agents", the code a quiet prefix in
//     another colour) is the name link's target from the row's rule to the column's edge, at
//     least 24px tall, with a pointer cursor and the name underlined under the mouse, and no
//     example lies under it; the mouse on each name opens its layer at once and its card after
//     a rest, and from a name onto its own examples the card stays open, closing once the
//     mouse has left the stage for the grace. A click on the person plays their moment (data-hv-cheer) for 1.8s and opens no
//     layer, and with a card open it leaves the card open, to close once the pointer has been
//     off its plate and card for the grace. Leaving the stage closes the card once the grace
//     has run out (within 150ms after it), and Esc closes it.
//   - The ways into the cards (`paths`), from 45em at each width and each --sizes window: on a
//     fresh page for each layer, the mouse rests on its name until the card shows, then goes
//     straight towards the card's stories link at about 250px/s, stopping 150ms halfway, and on
//     into the link: the layer stays open all the way (a name between them waits), the link is
//     under the mouse and a click follows it to the layer's view of Latest. A card whose link
//     lies outside the window is noted and skipped.
//   - The completion, from 45em at each width and each --sizes window (`finale`): six layers
//     checked by pointing at their plates, T7 to T2, then T1 checked by its plate with the mouse
//     left there, or then moved to an empty part of the stage or to the person, by its label with
//     the mouse left there (first off the stage where T2's card lies over that label, as at
//     720x450), and by focus on its name (a real Tab); and on a touch screen, at the width of
//     the regressions below, by a tap on its chevron after taps on the other six, and by "Check
//     all layers" clicked (by script, which moves no focus, as a tap in Safari does not) while
//     T3's card is open from a tap. Each time, timed in the page from the seventh check: the
//     person's moment plays at once, data-motion is running within 2s (hero.js lets go of the
//     open layer 1.2s after the check), and then the data packets are drawn and move, the scene
//     marks no layer and the card that was open stays open beside them (with focus, focus stays
//     on the name), except where the mouse moved off its plate, which closes it. Then the mouse
//     on plate 4 holds the loop while T4 is open, and leaving the stage lets it run again.
//   - From 45em, the keyboard, with real Tab and Shift+Tab from the element before the
//     figure: "Check all layers", then each layer's name and its card's stories link,
//     T7 first, then the two links under the stage; back, the same in reverse, ending on the
//     pause control, which has taken the button's place once every layer was checked.
//     Focus on a name or a stories link opens its card and checks its layer; every
//     focused element ends fully between the sticky header and the window's bottom, and
//     so does the open card when it and its label fit there. Esc on a stories link closes
//     the card and returns focus to the name, and Tab back to the link opens it again.
//   - From 45em on a touch screen: the touch hint and the chevrons in the rows' heads;
//     a tap on a chevron or a plate opens its layer and a second tap closes it; a swipe
//     that starts outside the figure scrolls the page and keeps the card open; a tap
//     outside the figure closes it.
//   - Touch tablets, when a width of 720 or more is asked for, in windows of 1024x768,
//     768x1024, 1180x820 and 820x1180, and a phone on its side (932x430, from 45em, where
//     every card is taller than the window), or the --tablets list (none skips them): a
//     tap on each layer's chevron, from the page as loaded and from the scene in view,
//     and on each plate, opens it, and once the page settles the whole card lies between
//     the sticky header's bottom and the window's (8px clear of each), or, taller than
//     that, starts just under the header. The page scrolls by the least that does so:
//     when it scrolled, the card ends at one of those edges, and a card already there
//     scrolls nothing. The scroll is the page's own (smooth) and, under reduced motion,
//     instant.
//   - Behaviour that broke once, at the first width of 1184 or more (else the first of
//     720 or more), with every layer checked first so that the pause control shows: with
//     each card open by its label, a click on the pause control
//     pauses; a press on a card's text, also after a click on the pause control,
//     follows the card to its layer on the Stack page; a straight path at about 130px/s
//     from each plate to its card's stories link keeps that layer open and the click
//     follows the link; and focus that the window takes and gives back (focusout, then
//     focusin, with no relatedTarget) on a focused name leaves the page where it was.
//   - Below 45em: seven chevrons of at least 44x44px; the hint gives the click line with a
//     mouse and the touch line on a touch screen; the progress and "Check all layers"
//     (a 44px target) fit the width; a click opens the card in its row with
//     aria-expanded="true" and checks the layer, a second closes it, several rows can be
//     open, and the page does not scroll sideways. Once every row has been opened, every
//     mark shows, the hint's line drops its promise of colour and the scene marks no open
//     row, so the loop runs. "Who checks" shows at
//     rest on the TEE rows, T1 and T2, only; on T3 to T7 it shows while the row is open, and
//     goes when it closes. A click on the person plays their moment and opens no row.
//   - The vendor marks' names (`tips`), from 45em in each --tipsizes window (by default
//     1920x1080, 1536x864, 1440x900, 1366x768, 1280x720 and 1024x768, when a width of 720 or
//     more is asked for; none skips them) and at each width below 720: the mouse comes onto
//     every named mark in the labels, each on a fresh page with nothing open or checked (from
//     45em), then all on one page, from 45em each from its layer's name, where it rested until
//     the card showed. The mark opens, switches and checks no layer, and its name does not show
//     yet; after a rest the tooltip shows the mark's aria-label (the one tooltip, at least
//     13px), wholly inside the window and below the sticky header, clear of the mark and of the
//     card still open from the name, which lies over none of its own label's marks, with the
//     page not scrolling sideways; once the card has closed (the pointer is off its name and
//     card) the name stays; every name must show; moving onto the layer's name hides it; an
//     open card does not name the marks to a mouse. A pass along a row's marks at about
//     250px/s shows no name. On a touch screen (a touch tablet at 1024x768 from 45em, the
//     phone itself below it) a tap on each named mark gives its name: in the tooltip, or,
//     where the row's chevron lies over that part of the mark, in the Examples line of the
//     card that the tap opens; a tap outside the figure hides it; and the card that a tap on
//     each row's arrow opens names every example in its label. No mark is in the tab order.
//   - When a width of 1184 or more is asked for: the intro stands beside the figure
//     without touching it at 1184, 1280, 1440, 1600 and 1920.
// --only runs only the checks it names, from motion (the first group above), legend, guard, cards,
// paths, keys, sweeps, touch, finale, regressions, phone, nojs, tablets, tips and band, such as
// --only finale.
// --nojs also loads each page with JavaScript off: the progress and "Check all layers"
// stay hidden, no mark shows, the person is in full colour and the scene's description
// names no gray; the figure has no caption and the tooltip stays hidden; from 45em the
// cards are not displayed, the hint and chevrons stay hidden and the seven names link to
// the Stack page; below 45em the seven cards are open in their rows, each row with its
// "Who checks".
// It exits with 1 on a failure.
// --frames counts animation frames over two seconds, and --cpu N throttles the CPU
// N times while it does, as a rough measure of the hero's cost on phones.
//
// Headless Chrome clamps --window-size to a 500px minimum, so tools/shoot.py lays
// "mobile" pages out at 500px. This script drives Chrome over the DevTools
// protocol and sets the viewport with Emulation.setDeviceMetricsOverride, so
// media queries see a real 360/390px viewport. Node 22+ (built-in WebSocket).

import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync, readFileSync, readdirSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

// The browser: $CHROME, else the usual install for this system
function chromePath() {
  if (process.env.CHROME) return process.env.CHROME;
  if (process.platform === "darwin") return "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  if (process.platform === "win32") {
    const roots = [process.env.PROGRAMFILES, process.env["PROGRAMFILES(X86)"], process.env.LOCALAPPDATA].filter(Boolean);
    return roots.map((r) => path.join(r, "Google", "Chrome", "Application", "chrome.exe")).find((p) => existsSync(p)) || "chrome.exe";
  }
  const dirs = (process.env.PATH || "").split(path.delimiter).filter(Boolean);
  for (const name of ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]) {
    const found = dirs.map((d) => path.join(d, name)).find((p) => existsSync(p));
    if (found) return found;
  }
  return "google-chrome";
}
const CHROME = chromePath();
const TEE_HUB = "topics/confidential-computing/index.html";
const BRIEF = "articles/nist-nsa-cisa-agent-incident-practices/index.html";
const TEE_BRIEF = "articles/ddrop-ddr5-interposer-attack/index.html";
const LONGFORM = "articles/remote-attestation-for-ai-workloads-explained/index.html";

function args() {
  const [cmd, ...rest] = process.argv.slice(2);
  const pos = [], opt = {};
  for (let i = 0; i < rest.length; i++) {
    if (rest[i].startsWith("--")) {
      const key = rest[i].slice(2);
      const next = rest[i + 1];
      if (next === undefined || next.startsWith("--")) opt[key] = true;
      else { opt[key] = next; i++; }
    } else pos.push(rest[i]);
  }
  return { cmd, pos, opt };
}

function pageMap(site, article) {
  if (!existsSync(path.join(site, "index.html"))) throw new Error(`${site} has no index.html; pass the folder of a built site`);
  const dirs = (sub) => existsSync(path.join(site, sub))
    ? readdirSync(path.join(site, sub)).filter((d) => existsSync(path.join(site, sub, d, "index.html"))).sort() : [];
  const arts = dirs("articles");
  const first = article || (arts.length ? `articles/${arts[0]}/index.html` : "index.html");
  const topics = dirs("topics").filter((d) => d !== "confidential-computing");
  const en = {
    home: "index.html", tee: TEE_HUB, latest: "latest/index.html", topics: "topics/index.html",
    topic: topics.length ? `topics/${topics[0]}/index.html` : "topics/index.html",
    learn: "learn/index.html", resources: "resources/index.html", vision: "vision/index.html",
    glossary: "glossary/index.html", about: "about/index.html", search: "search/index.html",
    article: first, brief: BRIEF, "tee-brief": TEE_BRIEF, longform: LONGFORM,
  };
  const map = { ...en, "404": "404.html" };
  for (const [name, rel] of Object.entries(en)) map[`zh-${name}`] = `zh/${rel}`;
  return map;
}

// The file for a page name, or null when the build has no such page.
function pageFile(site, pages, name) {
  if (!Object.hasOwn(pages, name)) throw new Error(`unknown page ${JSON.stringify(name)}; use one of: ${Object.keys(pages).join(", ")}`);
  const file = path.join(site, pages[name]);
  return existsSync(file) ? file : null;
}

const list = (value, fallback) => String(value || fallback).split(",").map((s) => s.trim()).filter(Boolean);

async function launch() {
  const profile = mkdtempSync(path.join(tmpdir(), "vp-cdp-"));
  // the window is larger than any viewport the checks emulate: without it, headless Chrome
  // presents no frames for a viewport 1728px wide or more, so --frames would count none.
  // Port 0: Chrome takes a free port and writes it to DevToolsActivePort in its profile, as for
  // tools/og_images.py, so two runs side by side (one per language, say) never share a browser
  const proc = spawn(CHROME, ["--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=2560,1600", "--remote-debugging-port=0",
    `--user-data-dir=${profile}`, "--no-first-run", "--no-default-browser-check", "--allow-file-access-from-files", "about:blank"],
    { stdio: "ignore" });
  let failed = null, exited = false;
  proc.on("error", (e) => { failed = e; });
  proc.on("exit", () => { exited = true; });
  let version, port = 0;
  for (let i = 0; i < 100 && !failed && !exited; i++) {
    try {
      if (!port) {
        const active = readFileSync(path.join(profile, "DevToolsActivePort"), "utf8");
        if (active.includes("\n")) port = Number(active.split("\n")[0]) || 0;
      }
      if (port) { version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json(); break; }
    } catch {}
    await sleep(100);
  }
  if (!version) {
    proc.kill("SIGKILL");
    try { rmSync(profile, { recursive: true, force: true }); } catch {}
    throw new Error(`Chrome did not start from ${CHROME}${failed ? ` (${failed.message})` : ""}; set CHROME to the browser's path`);
  }
  const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0;
  const pending = new Map();
  const listeners = [];
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { res, rej } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
    } else if (msg.method) {
      for (const l of [...listeners]) l(msg);
    }
  };
  // a browser that goes away fails the calls still waiting for it, rather than leaving them hanging
  ws.onclose = () => {
    for (const { rej } of pending.values()) rej(new Error("Chrome closed the DevTools connection"));
    pending.clear();
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  const once = (method) => new Promise((res) => { const l = (m) => { if (m.method === method) { listeners.splice(listeners.indexOf(l), 1); res(m.params); } }; listeners.push(l); });
  // every event from now on, until the returned function is called
  const on = (fn) => { listeners.push(fn); return () => { const i = listeners.indexOf(fn); if (i >= 0) listeners.splice(i, 1); }; };
  await send("Page.enable");
  await send("Runtime.enable");
  const close = () => { try { ws.close(); } catch {} proc.kill("SIGKILL"); try { rmSync(profile, { recursive: true, force: true }); } catch {} };
  return { send, once, on, close };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Emulated media features: colour scheme, with --reduced reduced motion and with --forced
// forced colours.
const media = (dark, reduced, forced = false) => [
  { name: "prefers-color-scheme", value: dark ? "dark" : "light" },
  { name: "prefers-reduced-motion", value: reduced ? "reduce" : "no-preference" },
  { name: "forced-colors", value: forced ? "active" : "none" },
];

// TOUCH emulates a touch screen: touch events, (hover: none) and (pointer: coarse). DPR is the
// device scale factor.
async function open(cdp, file, width, height, dark, reduced = false, touch = false, dpr = 1) {
  await cdp.send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: dpr, mobile: width < 768 });
  await cdp.send("Emulation.setTouchEmulationEnabled", touch ? { enabled: true, maxTouchPoints: 5 } : { enabled: false });
  await cdp.send("Emulation.setEmulatedMedia", { features: media(dark, reduced) });
  const loaded = cdp.once("Page.loadEventFired");
  await cdp.send("Page.navigate", { url: pathToFileURL(file).href });
  await Promise.race([loaded, sleep(8000)]);
  await cdp.send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => true)", awaitPromise: true });
  await sleep(250);
}

async function evaluate(cdp, expression) {
  const r = await cdp.send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 400));
  return r.result.value;
}

const CHECK = `(() => {
  const vw = document.documentElement.clientWidth;
  const zh = (document.documentElement.lang || '').startsWith('zh');
  const out = { vw, scrollW: document.documentElement.scrollWidth, overflow: [], small: [], smallZh: [], fonts: [] };
  const scrollers = el => { for (let p = el.parentElement; p; p = p.parentElement) { const s = getComputedStyle(p); if (/(auto|scroll|hidden|clip)/.test(s.overflowX) && p !== document.body && !p.classList.contains('site')) return true; } return false; };
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    if ((r.right > vw + 0.5 || r.left < -0.5) && !scrollers(el)) {
      out.overflow.push((el.className && el.className.baseVal === undefined ? el.tagName.toLowerCase() + '.' + String(el.className).split(' ').join('.') : el.tagName.toLowerCase()) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    }
  }
  const seen = new Set();
  for (const el of document.querySelectorAll('body *')) {
    if (!el.childNodes.length || !el.getClientRects().length) continue;
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    if (!own) continue;
    const s = getComputedStyle(el);
    if (s.display === 'none' || s.visibility === 'hidden' || el.closest('svg')) continue;
    const fs = parseFloat(s.fontSize);
    const key = (el.className || el.tagName) + '@' + fs;
    if (fs < 11.95) {
      if (!seen.has(key)) { seen.add(key); out.small.push(key); }
    } else if (zh && fs < 12.95 && /[\\u3400-\\u9fff]/.test(own)) {
      if (!seen.has(key)) { seen.add(key); out.smallZh.push(key); }
    }
  }
  out.overflow = out.overflow.slice(0, 25);
  return out;
})()`;

const MEASURE = `(() => {
  const res = [];
  for (const p of document.querySelectorAll('.prose > p, .callout-body > p')) {
    const node = p; const lines = new Map();
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT);
    const range = document.createRange();
    let t;
    while ((t = walker.nextNode())) {
      for (let i = 0; i < t.length; i++) {
        range.setStart(t, i); range.setEnd(t, i + 1);
        const rect = range.getClientRects()[0];
        if (!rect) continue;
        const k = Math.round(rect.top / 4);
        lines.set(k, (lines.get(k) || 0) + 1);
      }
    }
    const counts = [...lines.values()];
    if (counts.length > 1) res.push({ cls: p.parentElement.className, width: Math.round(p.getBoundingClientRect().width), lines: counts.length, full: counts.slice(0, -1) });
  }
  return res;
})()`;

async function shots(site, out, opt) {
  const pages = pageMap(site, opt.article);
  const widths = list(opt.widths, "390").map(Number);
  const height = Number(opt.height || 2400);
  const suffix = opt.suffix || null;
  const reduced = !!opt.reduced;
  const touch = !!opt.touch;
  const layer = opt.open ? Number(opt.open) : 0;
  if (opt.open && !(Number.isInteger(layer) && layer >= 1 && layer <= 7)) throw new Error("--open takes a layer from 1 to 7");
  const names = list(opt.pages, "home");
  const darks = opt.dark === true ? names : list(opt.dark, "");  // --dark alone repeats --pages in dark
  for (const name of [...names, ...darks]) pageFile(site, pages, name);  // fail on an unknown name before Chrome starts
  mkdirSync(out, { recursive: true });
  const cdp = await launch();
  try {
    const run = async (name, dark) => {
      const file = pageFile(site, pages, name);
      if (!file) { console.log(`${name}: skipped, ${pages[name]} is not in this build`); return; }
      for (const w of widths) {
        await open(cdp, file, w, height, dark, reduced, touch);
        let shot;
        if (layer) {
          // the viewport as it is with the card open: a capture beyond it would resize the
          // page under the resting pointer, and the card would close
          await openLayer(cdp, layer, w, touch);
          shot = await cdp.send("Page.captureScreenshot", { format: "png" });
        } else {
          const full = opt.full ? await evaluate(cdp, "document.documentElement.scrollHeight") : height;
          shot = await cdp.send("Page.captureScreenshot", { format: "png", clip: { x: 0, y: 0, width: w, height: full, scale: 1 }, captureBeyondViewport: true });
        }
        const label = suffix || (w < 768 ? "mobile" : w < 1100 ? `w${w}` : "desktop");
        const state = `${touch ? "-touch" : ""}${layer ? "-l" + layer : ""}`;
        const png = path.join(out, `${name}${dark ? "-dark" : ""}${reduced ? "-reduced" : ""}${state}-${label}${widths.length > 1 && suffix ? "-" + w : ""}.png`);
        writeFileSync(png, Buffer.from(shot.data, "base64"));
        console.log(path.basename(png));
      }
    };
    for (const name of names) await run(name, false);
    for (const name of darks) await run(name, true);
  } finally { cdp.close(); }
}

async function check(site, opt) {
  const pages = pageMap(site, opt.article);
  const widths = list(opt.widths, "360,390,768,1024,1440").map(Number);
  const names = list(opt.pages, "home");
  for (const name of names) pageFile(site, pages, name);
  console.log(`${opt.dark ? "dark" : "light"} theme${opt.reduced ? ", reduced motion" : ""}`);
  const cdp = await launch();
  let problems = 0, missing = 0;
  try {
    for (const name of names) {
      const file = pageFile(site, pages, name);
      if (!file) { missing++; console.log(`${name}: MISSING ${pages[name]}`); continue; }
      for (const w of widths) {
        await open(cdp, file, w, 900, !!opt.dark, !!opt.reduced);
        const r = await evaluate(cdp, CHECK);
        const bad = r.scrollW > r.vw || r.overflow.length;
        if (bad) problems++;
        const small = opt.small ? (r.small.length ? "  small: " + r.small.join(", ") : "") + (r.smallZh.length ? "  small-zh: " + r.smallZh.join(", ") : "") : "";
        console.log(`${name} @${w}: scrollW ${r.scrollW}/${r.vw}${r.overflow.length ? " OVERFLOW " + r.overflow.join(" | ") : ""}${small}`);
        if (opt.measure) {
          const m = await evaluate(cdp, MEASURE);
          for (const row of m.slice(0, 6)) console.log(`   ${row.cls} w${row.width} lines ${row.lines} chars/line ${row.full.join(",")}`);
        }
      }
    }
  } finally { cdp.close(); }
  if (missing) console.log(`${missing} page${missing > 1 ? "s" : ""} not in this build`);
  console.log(problems ? `${problems} page/width combinations with overflow` : "no horizontal overflow");
}

// The state of the home hero: the inline animated SVG scene and its layer labels.
const HERO_STATE = `(() => {
  const hero = document.querySelector('[data-verification-visual]') || document.querySelector('.hero-visual');
  if (!hero) return { found: false };
  const css = el => getComputedStyle(el);
  const shown = el => !!el && !el.hidden && css(el).display !== 'none' && css(el).visibility !== 'hidden' && el.getClientRects().length > 0;
  const svg = hero.querySelector('svg.hero-scene') || hero.querySelector('svg[role="img"]');
  const toggle = hero.querySelector('[data-motion-toggle]');
  const label = hero.querySelector('[data-motion-label]');
  const still = hero.querySelector('.verification-static-label, [data-motion-static]');
  const links = hero.querySelector('.hero-links'), tip = hero.querySelector('.hero-tip');
  const pulse = hero.querySelector('.hv-pulse');
  const all = hero.querySelector('.hero-all'), progress = hero.querySelector('.hero-progress'), person = hero.querySelector('.hv-person');
  const gray = person ? /grayscale\\(([\\d.]+)\\)/.exec(css(person).filter) : null;
  const anims = document.getAnimations().filter(a => a.effect && a.effect.target && hero.contains(a.effect.target));
  const r = hero.getBoundingClientRect();
  return {
    found: true,
    variant: svg ? 'svg' : 'none',
    labels: hero.querySelectorAll('.hero-layer').length,
    lang: document.documentElement.lang,
    motion: hero.dataset.motion || '',
    animated: hero.hasAttribute('data-animated'),
    animations: anims.length,
    running: anims.filter(a => a.playState === 'running').length,
    top: r.top + scrollY, height: r.height,
    pageHeight: document.documentElement.scrollHeight,
    toggle: toggle && {
      shown: shown(toggle), label: label ? label.textContent.trim() : '', aria: toggle.getAttribute('aria-label') || '',
      pause: toggle.dataset.labelPause || '', play: toggle.dataset.labelPlay || '',
      radius: ['borderTopLeftRadius', 'borderTopRightRadius', 'borderBottomRightRadius', 'borderBottomLeftRadius'].map(k => css(toggle)[k]),
      backdrop: css(toggle).backdropFilter || css(toggle).webkitBackdropFilter || 'none',
      fontSize: parseFloat(css(label || toggle).fontSize),
    },
    still: still && { shown: shown(still), text: still.textContent.trim() },
    checked: hero.dataset.hvChecked || '',
    all: all && { shown: shown(all), text: all.textContent.trim(), focused: document.activeElement === all },
    progress: progress && { shown: shown(progress), text: progress.textContent.trim(), done: progress.dataset.done || '' },
    gray: gray ? Number(gray[1]) : 0,
    focus: document.activeElement === toggle ? 'pause' : document.activeElement === progress ? 'progress' : document.activeElement === all ? 'check all' : (document.activeElement || {}).tagName || '',
    caption: !!hero.querySelector('figcaption'),
    links: links && { shown: shown(links), parent: links.parentElement === hero, hrefs: [...links.querySelectorAll('a')].map(a => a.getAttribute('href') || '') },
    tip: tip && { shown: shown(tip), aria: tip.getAttribute('aria-hidden') || '', text: tip.textContent },
    svg: svg && {
      role: svg.getAttribute('role') || '', title: ((svg.querySelector('title') || {}).textContent || '').trim(),
      texts: svg.querySelectorAll('text').length, images: svg.querySelectorAll('image').length,
    },
    pulse: pulse && { shown: css(pulse).display !== 'none' && parseFloat(css(pulse).opacity) > 0 },
    scripts: [...document.querySelectorAll('script[src]')].filter(s => /(^|\\/)hero\\.js(\\?|$)/.test(s.getAttribute('src'))).map(s => ({ src: s.getAttribute('src'), defer: s.defer })),
  };
})()`;

const FRAMES = `new Promise(res => {
  const t0 = performance.now(); let n = 0, last = t0, worst = 0;
  const tick = now => { n++; worst = Math.max(worst, now - last); last = now; if (now - t0 < 2000) requestAnimationFrame(tick); else res({ frames: n, ms: Math.round(now - t0), worst: Math.round(worst) }); };
  requestAnimationFrame(tick);
})`;

const CJK = new RegExp("[\\u3400-\\u9fff]");

// Helpers for the hero's layer cards, set on the page as window.__vpHero. A layer N is
// its row (.hero-layer[data-n="N"]), its card (.hero-card) and its plate in the scene,
// which spec 8.3 reaches at scene point (290, T + 72), T = 10 + 56 (7 - N), or at
// (300, 485.5) on the board (T1), mapped to the viewport through the scene's CTM.
const HERO_KIT = `(() => {
  const fig = document.querySelector('[data-verification-visual]');
  if (!fig || !fig.querySelector('.hero-stage')) return false;
  const css = el => getComputedStyle(el);
  const shown = el => !!el && !el.hidden && css(el).display !== 'none' && css(el).visibility !== 'hidden' && el.getClientRects().length > 0;
  const box = el => { if (!el) return null; const r = el.getBoundingClientRect(); return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height }; };
  const row = n => fig.querySelector('.hero-layer[data-n="' + n + '"]');
  const centre = el => { const r = el.getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; };
  const headerBottom = () => { const h = document.querySelector('.site-header'); return h ? Math.max(0, h.getBoundingClientRect().bottom) : 0; };
  const rem = () => parseFloat(css(document.documentElement).fontSize) || 16;
  const rowsWith = sel => [...fig.querySelectorAll(sel)].map(el => el.closest('.hero-layer').dataset.n).join(',');
  // an element as the checks name it: tag.first-class, then @N in layer N's row or @links (the
  // links to the Stack page under the stage)
  const describe = el => {
    if (!el || el === document.body || el === document.documentElement) return 'body';
    const r = el.closest('.hero-layer');
    let s = el.tagName.toLowerCase();
    if (typeof el.className === 'string' && el.className.trim()) s += '.' + el.className.trim().split(/\\s+/)[0];
    return s + (r ? '@' + r.dataset.n : el.closest('.hero-links') ? '@links' : '');
  };
  // the site scrolls smoothly: wait until the page has not moved for a few frames (or 1.5s)
  const settle = () => new Promise(done => {
    let last = scrollY, still = 0;
    const tick = () => { if (scrollY === last) still++; else { still = 0; last = scrollY; } if (still > 4) done(true); else requestAnimationFrame(tick); };
    requestAnimationFrame(tick);
    setTimeout(() => done(false), 1500);
  });
  // The room that hero.js gives a card opened with the mouse: from the band's top when the
  // intro stands beside the figure, else the scene's, and below the control at the figure's top
  // right (the pause control, or "Check all layers" in its place; 0.4rem) and the sticky header
  // (8px), down to the stage's bottom and 8px above the window's
  const room = () => {
    const band = fig.closest('.home-hero');
    const side = !!band && css(band).getPropertyValue('--hero-band').trim() === 'side';
    const toggle = [fig.querySelector('[data-motion-toggle]'), fig.querySelector('.hero-all')].find(shown);
    const pause = toggle ? box(toggle) : null;
    const gap = 0.4 * rem();
    const lo = Math.max(side ? band.getBoundingClientRect().top : fig.querySelector('.hero-layers').getBoundingClientRect().top,
      pause ? pause.bottom + gap : -Infinity, headerBottom() + 8);
    const hi = Math.min(fig.querySelector('.hero-stage').getBoundingClientRect().bottom, innerHeight - 8);
    return { side, pause, gap, lo, hi };
  };
  window.__vpHero = {
    row,
    plate(n) {
      const p = n === 1 ? new DOMPoint(300, 485.5) : new DOMPoint(290, 10 + 56 * (7 - n) + 72);
      const q = p.matrixTransform(fig.querySelector('svg.hero-scene').getScreenCTM());
      return [Math.round(q.x), Math.round(q.y)];
    },
    // the whole scene in view under the sticky header, unless it already is
    view() {
      const s = fig.querySelector('.hero-art').getBoundingClientRect(), top = headerBottom() + 8;
      if (s.top < top || s.bottom > innerHeight) window.scrollBy({ top: s.top - top, behavior: 'instant' });
      return settle();
    },
    // whether layer N's plate point is between the sticky header and the window's bottom
    plateShown(n) {
      const y = this.plate(n)[1];
      return y >= headerBottom() + 8 && y <= innerHeight - 8;
    },
    // layer N's plate point brought to the middle of the window under the header
    plateInView(n) {
      const y = this.plate(n)[1], lo = headerBottom() + 8, hi = innerHeight - 8;
      if (y < lo || y > hi) window.scrollBy({ top: y - (lo + hi) / 2, behavior: 'instant' });
      return settle();
    },
    // the centre of SEL in layer N's row; with SCROLL, brought into view first if it is not
    async at(sel, n, scroll) {
      const el = row(n).querySelector(sel), r = el.getBoundingClientRect();
      if (scroll && (r.top < headerBottom() + 8 || r.bottom > innerHeight - 8)) {
        el.scrollIntoView({ block: 'center', behavior: 'instant' });
        await settle();
      }
      return centre(el);
    },
    // the centre of SEL in layer N's row, or in the figure without N; null when there is none
    centre(sel, n) {
      const el = n ? row(n).querySelector(sel) : fig.querySelector(sel);
      return el && el.getClientRects().length ? centre(el) : null;
    },
    // layer N's row brought wholly between the sticky header and the window's bottom, unless it is
    // there already
    reachRow(n) {
      const r = row(n).getBoundingClientRect(), lo = headerBottom() + 8, hi = innerHeight - 8;
      if (r.top >= lo && r.bottom <= hi) return Promise.resolve(true);
      row(n).scrollIntoView({ block: 'center', behavior: 'instant' });
      return settle();
    },
    // Layer N's name area against its examples, as a pointer meets them: what lies under points
    // on the name area (at the row's rule, at the column's right edge, 0.25rem above the head line
    // and 0.1rem below it, and at the code and name), with the cursor and whether the name is
    // underlined there once hovered (HOVERED, with the mouse on the name), and under the centre of
    // each example in the row; the head line's height and the gap down to the examples
    target(n, hovered) {
      const r = row(n), rb = r.getBoundingClientRect(), h = r.querySelector('.hero-layer-head').getBoundingClientRect();
      const e = r.querySelector('.hero-examples').getBoundingClientRect(), link = r.querySelector('.hero-layer-link');
      const y = (h.top + h.bottom) / 2, x = rb.left + 40;
      const at = (px, py) => { const el = document.elementFromPoint(Math.round(px), Math.round(py)); return { what: describe(el && (el.closest('a') || el)), cursor: el ? css(el).cursor : '' }; };
      return {
        name: [[rb.left + 1, y], [rb.right - 3, y], [x, h.top - 0.25 * rem()], [x, h.bottom + 0.1 * rem()], centre(link)].map(([px, py]) => at(px, py)),
        examples: [...r.querySelectorAll('.hero-examples .hero-ex')].map(ex => { const b = ex.getBoundingClientRect(); return at(b.left + b.width / 2, (b.top + b.bottom) / 2); }),
        underline: hovered ? css(link).textDecorationLine : '', head: h.height, gap: e.top - h.bottom,
        code: (r.querySelector('.hero-layer-code') || {}).textContent || '', text: link.textContent,
        quiet: !!r.querySelector('.hero-layer-code') && css(r.querySelector('.hero-layer-code')).color !== css(link).color,
      };
    },
    // the centre of each example in layer N's row (its vendor marks and names)
    examples(n) { return [...row(n).querySelectorAll('.hero-examples .hero-ex')].map(centre); },
    // whether the point (X, Y) lies between the sticky header and the window's bottom, 8px clear of each
    seen(x, y) { return x >= 0 && x <= innerWidth && y >= headerBottom() + 8 && y <= innerHeight - 8; },
    // the index, among the named marks, of the first one outside layer N's row that lies wholly in view
    // and clear of N's open card (by its box), or -1
    freeMark(n) {
      const c = row(n).querySelector('.hero-card').getBoundingClientRect(), lo = headerBottom() + 8, hi = innerHeight - 8;
      return [...fig.querySelectorAll('svg.hero-logo[aria-label]')].findIndex(m => {
        const b = m.getBoundingClientRect(), r = m.closest('.hero-layer');
        return r !== row(n) && !r.classList.contains('is-covered') && b.top >= lo && b.bottom <= hi
          && !(b.left < c.right && b.right > c.left && b.top < c.bottom + 8 && b.bottom > c.top - 8);
      });
    },
    // what a pointer at (X, Y) is over
    hit(x, y) { return describe(document.elementFromPoint(x, y)); },
    // the element before the figure in the tab order, focused, so that Tab goes into the figure
    before() {
      const all = [...document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
        .filter(el => el.tabIndex >= 0 && !el.disabled && el.getClientRects().length && css(el).visibility !== 'hidden');
      const first = all.findIndex(el => fig.contains(el));
      if (first < 1) return '';
      const el = all[first - 1];
      el.focus();
      return describe(el) + ' "' + el.textContent.trim().replace(/\\s+/g, ' ').slice(0, 40) + '"';
    },
    // the layers whose card has a stories link
    stories() { return [...fig.querySelectorAll('.hero-layer[data-n]')].filter(r => r.querySelector('a.hc-count')).map(r => Number(r.dataset.n)); },
    // where focus is, against the sticky header and the window, with the open card and its label
    focused() {
      const ae = document.activeElement, n = fig.dataset.hvActive || '', r = n ? row(n) : null, c = r && r.querySelector('.hero-card');
      return { focus: describe(ae), inFig: fig.contains(ae), box: ae && ae !== document.body ? box(ae) : null,
        hb: headerBottom(), ih: innerHeight, active: n, place: r ? (r.dataset.openPlace || 'none') : '',
        card: c ? box(c) : null, row: r ? box(r) : null, shown: !!c && shown(c) && css(c).clipPath === 'none', y: Math.round(scrollY) };
    },
    // the named vendor marks in the labels: each one's row (its code), name and box
    marks() {
      return [...fig.querySelectorAll('svg.hero-logo[aria-label]')].map(m => ({ n: Number(m.closest('.hero-layer').dataset.n), name: m.getAttribute('aria-label'), box: box(m) }));
    },
    // the centre of the Ith named mark, brought to the middle of the window first when it is not wholly
    // between the sticky header and the window's bottom
    async mark(i) {
      const m = fig.querySelectorAll('svg.hero-logo[aria-label]')[i], r = m.getBoundingClientRect();
      if (r.top < headerBottom() + 40 || r.bottom > innerHeight - 40) { m.scrollIntoView({ block: 'center', behavior: 'instant' }); await settle(); }
      return centre(m);
    },
    // the tooltip now (shown, its text, font size and box) with the window, the sticky header's bottom,
    // the open layer, where its card shows and its box while it shows, the layers checked, the page's
    // sideways overflow and the marks in the tab order
    tip() {
      const t = fig.querySelector('.hero-tip'), n = fig.dataset.hvActive || '', r = n ? row(n) : null;
      const card = r && r.dataset.openPlace ? box(r.querySelector('.hero-card')) : null;
      return { shown: shown(t), text: t ? t.textContent : '', size: t ? parseFloat(css(t).fontSize) : 0, box: shown(t) ? box(t) : null,
        vw: document.documentElement.clientWidth, ih: innerHeight, hb: headerBottom(), active: n, card, place: card ? r.dataset.openPlace : '',
        checked: [...fig.querySelectorAll('.hero-layer.is-checked')].map(x => x.dataset.n).join(','),
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        tabbable: [...fig.querySelectorAll('svg.hero-logo')].filter(m => m.tabIndex >= 0 || m.hasAttribute('tabindex')).length };
    },
    // layer N's card's line with the examples' names: whether it shows, and its text
    names(n) {
      const p = row(n).querySelector('.hc-names');
      return { shown: shown(p), text: p ? p.textContent : '' };
    },
    // records from now on, in window.__vpTipShown, whether the tooltip shows at all
    watchTip() {
      const t = fig.querySelector('.hero-tip');
      window.__vpTipShown = false;
      new MutationObserver(() => { if (!t.hidden) window.__vpTipShown = true; }).observe(t, { attributes: true, attributeFilter: ['hidden'] });
      return true;
    },
    // the first screen: where the person's label and the hint end, and where the labels start
    fold() {
      const band = fig.closest('.home-hero'), hint = fig.querySelector('.hero-hint');
      return { side: !!band && css(band).getPropertyValue('--hero-band').trim() === 'side', ih: innerHeight, y: scrollY,
        person: box(fig.querySelector('.hero-person')), hint: shown(hint) ? box(hint) : null, labels: box(fig.querySelector('.hero-layers')) };
    },
    parts() {
      const hint = fig.querySelector('.hero-hint');
      return {
        enhanced: fig.hasAttribute('data-enhanced'), hits: fig.hasAttribute('data-hv-hits'),
        person: shown(fig.querySelector('.hero-person')) && !!fig.querySelector('.hero-person').textContent.trim(),
        legend: shown(fig.querySelector('.hero-chain')) ? fig.querySelectorAll('.hero-chain-runs > li').length : 0,
        hint: shown(hint), pointer: shown(hint && hint.querySelector('.hero-hint-pointer')), touch: shown(hint && hint.querySelector('.hero-hint-touch')),
        chevrons: [...fig.querySelectorAll('.hero-more')].map(b => ({ shown: shown(b), head: !!b.closest('.hero-layer-head'), w: Math.round(b.getBoundingClientRect().width), h: Math.round(b.getBoundingClientRect().height) })),
      };
    },
    // what hero.js has set, and where layer N's card stands among the other boxes
    state(n) {
      const r = n ? row(n) : null, card = r && r.querySelector('.hero-card');
      const ae = document.activeElement;
      const rm = room();
      // what an open card may lie over: the other rows, the legend and the hint
      const others = [...fig.querySelectorAll('.hero-layer[data-n]')].filter(x => x !== r).map(x => ['L' + x.dataset.n, x])
        .concat([['the legend', fig.querySelector('.hero-chain')], ['the hint', fig.querySelector('.hero-hint')]])
        .filter(([, el]) => el && el.getClientRects().length)
        .map(([name, el]) => ({ name, box: box(el), covered: el.classList.contains('is-covered'), opacity: css(el).opacity }));
      return {
        active: fig.dataset.hvActive || '', motion: fig.dataset.motion || '',
        rows: rowsWith('.hero-layer.is-active'), open: rowsWith('.hero-layer.is-open'), expanded: rowsWith('.hero-more[aria-expanded="true"]'),
        leaders: [...fig.querySelectorAll('.hero-leader')].map((g, i) => g.classList.contains('is-active') ? fig.querySelectorAll('.hero-layer[data-n]')[i].dataset.n : '').filter(Boolean).join(','),
        place: r ? (r.dataset.openPlace || 'none') : '', prefers: r ? r.dataset.place : '',
        card: card && { shown: shown(card), clip: css(card).clipPath, box: box(card) },
        row: r && box(r), head: r && box(r.querySelector('.hero-layer-head')), examples: r && box(r.querySelector('.hero-examples')),
        lo: rm.lo, hi: rm.hi, gap: rm.gap, pause: rm.pause,
        figure: box(fig), stage: box(fig.querySelector('.hero-stage')), person: box(fig.querySelector('.hero-person')),
        links: box(fig.querySelector('.hero-links')), intro: box(document.querySelector('.home-intro')),
        others,
        focus: describe(ae), y: Math.round(scrollY),
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    },
    // resolves once the figure's CSS transitions have run (the labels that a card covers fade
    // out in 0.15s), or after 1s
    calm() {
      const running = fig.getAnimations({ subtree: true }).filter(a => a instanceof CSSTransition && a.playState === 'running');
      return Promise.race([Promise.all(running.map(a => a.finished.catch(() => null))), new Promise(r => setTimeout(r, 1000))]).then(() => running.length);
    },
    // records each value that data-hv-active takes from now on, in window.__vpLog
    record() {
      window.__vpLog = [];
      new MutationObserver(() => window.__vpLog.push(fig.dataset.hvActive || '-')).observe(fig, { attributes: true, attributeFilter: ['data-hv-active'] });
      return true;
    },
    // how long after the pointer leaves the stage the card closes (-1: never, -2: no card was open)
    watchLeave() {
      this.left = new Promise(done => {
        fig.querySelector('.hero-stage').addEventListener('pointerleave', () => {
          const t0 = performance.now();
          if (!fig.hasAttribute('data-hv-active')) return done(-2);
          const mo = new MutationObserver(() => { if (!fig.hasAttribute('data-hv-active')) { mo.disconnect(); done(Math.round(performance.now() - t0)); } });
          mo.observe(fig, { attributes: true, attributeFilter: ['data-hv-active'] });
        }, { once: true });
        setTimeout(() => done(-1), 3000);
      });
      return true;
    },
    // the chain as the scene draws it at rest, segment by segment, and the person's phone
    chain() {
      const scene = fig.querySelector('svg.hero-scene');
      const drawn = el => css(el).display !== 'none' && css(el).visibility !== 'hidden';
      const halo = el => el ? css(el).opacity : 'none';
      return {
        rest: fig.dataset.hvRest || '',
        segments: (fig.dataset.hvChain || '').split(/\\s+/).filter(Boolean).map(token => {
          const [k, status] = token.split(':');
          const groups = [...scene.querySelectorAll('g.hv-seg' + k)];
          return { k, status,
            beams: groups.flatMap(g => [...g.querySelectorAll('.hv-bm')]).map(b => drawn(b) ? (css(b).strokeDasharray === 'none' ? 'solid' : 'dashed') : 'hidden'),
            stubs: groups.flatMap(g => [...g.querySelectorAll('.hv-stub')]).map(drawn) };
        }),
        ring: !!scene.querySelector('.hv-person .hv-ph-ring') && drawn(scene.querySelector('.hv-person .hv-ph-ring')) && parseFloat(css(scene.querySelector('.hv-person .hv-ph-ring')).opacity) > 0,
        halos: [halo(scene.querySelector('.hv-person .hv-nh')), halo(scene.querySelector('.hv-ring1 .hv-nh'))],
      };
    },
    // without JavaScript
    plain() {
      return {
        enhanced: fig.hasAttribute('data-enhanced'), hint: shown(fig.querySelector('.hero-hint')),
        chevrons: [...fig.querySelectorAll('.hero-more')].map(shown),
        cards: [...fig.querySelectorAll('.hero-layer[data-n]')].map(r => { const c = r.querySelector('.hero-card'); const b = c.getBoundingClientRect(), rb = r.getBoundingClientRect();
          return { display: css(c).display, height: Math.round(b.height), inRow: b.top >= rb.top - 1 && b.bottom <= rb.bottom + 1 }; }),
        links: [...fig.querySelectorAll('.hero-layer[data-n]')].map(r => new RegExp('/topics/(index\\\\.html)?#layer-' + r.dataset.layer + '$').test(r.querySelector('.hero-layer-link').href)),
        who: this.who(),
        progress: this.progress(),
      };
    },
    // each row's "Who checks" line, T7 first: shown or not, with whether the row is a TEE row
    // and open
    who() {
      return [...fig.querySelectorAll('.hero-layer[data-n]')].map(r => ({ n: Number(r.dataset.n), tee: r.classList.contains('is-tee'),
        open: r.classList.contains('is-open'), shown: shown(r.querySelector('.hero-who-line')) }));
    },
    // the legend's samples beside the chain that the scene draws: the computed stroke of each
    // sample's paths and the sample's opacity, the colour of each run's words, the stroke of the
    // chain's TEE run (.hv-bm.hv-t), and what CanvasText and --ink-2 resolve to
    legend() {
      const resolve = value => { const p = document.createElement('span'); p.style.color = value; document.body.appendChild(p); const c = css(p).color; p.remove(); return c; };
      const chain = fig.querySelector('svg.hero-scene .hv-bm.hv-t');
      return {
        forced: matchMedia('(forced-colors: active)').matches, canvasText: resolve('CanvasText'), ink: resolve('var(--ink-2)'),
        chain: chain ? css(chain).stroke : '',
        samples: [...fig.querySelectorAll('.hero-chain-runs > li')].map(li => { const svg = li.querySelector('.hero-chain-sample');
          return { bind: li.dataset.bind, strokes: svg ? [...svg.querySelectorAll('path')].map(p => css(p).stroke) : [], opacity: svg ? css(svg).opacity : '',
            words: css(li).color, status: css(li.querySelector('.hero-chain-status')).color }; }),
      };
    },
    // SEL in layer N's row brought wholly into view below the sticky header by the least
    // instant scroll, as a reader scrolls to what they mean to tap; its centre
    async reach(sel, n) {
      const el = row(n).querySelector(sel), r = el.getBoundingClientRect(), lo = headerBottom() + 8, hi = innerHeight - 8;
      const dy = r.top < lo ? r.top - lo : r.bottom > hi ? r.bottom - hi : 0;
      if (dy) { window.scrollBy({ top: dy, behavior: 'instant' }); await settle(); }
      return centre(el);
    },
    // records the behaviour asked of each window.scrollBy from now on, in window.__vpScrolls
    spyScroll() {
      window.__vpScrolls = [];
      if (!window.__vpScrollBy) {
        window.__vpScrollBy = window.scrollBy;
        window.scrollBy = function (...a) {
          window.__vpScrolls.push(a[0] && typeof a[0] === 'object' ? a[0].behavior || 'auto' : 'x, y');
          return window.__vpScrollBy.apply(this, a);
        };
      }
      return true;
    },
    // the person's moment and the data flow as the scene draws them now: the opacity of the
    // bubble, the indigo screen and the glow, data-hv-cheer, whether the packets and the dotted
    // route are drawn and how the packets' animations play, the running animations in the
    // figure, and the centre of the person's hit area, brought into view when SCROLL is set
    you(scroll) {
      const scene = fig.querySelector('svg.hero-scene');
      const hit = scene.querySelector('.hv-you-hit');
      if (scroll && hit) hit.scrollIntoView({ block: 'center', behavior: 'instant' });
      const op = sel => { const el = scene.querySelector(sel); return el ? parseFloat(css(el).opacity) : -1; };
      const pks = [...scene.querySelectorAll('.hv-pk')], route = scene.querySelector('.hv-route'), flow = scene.querySelector('.hv-flow');
      const drawn = el => !!el && css(el).display !== 'none' && css(el).visibility !== 'hidden';
      return { bubble: op('.hv-bubble'), screen: op('.hv-ptee'), glow: op('.hv-you-glow'), cheer: fig.hasAttribute('data-hv-cheer'),
        active: fig.dataset.hvActive || '', packets: pks.length > 0 && pks.every(drawn) && parseFloat(css(flow).opacity) > 0,
        plays: [...new Set(pks.flatMap(el => el.getAnimations().map(a => a.playState)))].join(',') || 'none',
        route: drawn(route) && parseFloat(css(flow).opacity) > 0,
        running: fig.getAnimations({ subtree: true }).filter(a => a.playState === 'running').length,
        hit: hit ? centre(hit) : null, pointer: hit ? css(hit).pointerEvents : '' };
    },
    // the reader's progress: how many layers are checked, the rows whose mark shows, the status's
    // text, how gray you are (the grayscale of g.hv-person, 0 without one), whether "Check all
    // layers" shows and whether the loop may run
    progress() {
      const p = fig.querySelector('.hero-progress'), person = fig.querySelector('.hv-person'), all = fig.querySelector('.hero-all');
      const g = person ? /grayscale\\(([\\d.]+)\\)/.exec(css(person).filter) : null;
      return { checked: fig.dataset.hvChecked || '', text: p ? p.textContent.trim() : '', done: p ? p.dataset.done || '' : '', shown: shown(p),
        marks: [...fig.querySelectorAll('.hero-layer[data-n]')].filter(r => r.classList.contains('is-checked') && shown(r.querySelector('.hero-tick'))).map(r => r.dataset.n).join(','),
        gray: g ? Number(g[1]) : 0, all: shown(all), allBox: shown(all) ? box(all) : null, animated: fig.hasAttribute('data-animated'),
        active: fig.dataset.hvActive || '', motion: fig.dataset.motion || '', overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
    },
    // the centre of "Check all layers", brought into view first
    checkAll() {
      const b = fig.querySelector('.hero-all');
      if (!shown(b)) return null;
      b.scrollIntoView({ block: 'center', behavior: 'instant' });
      return centre(b);
    },
    // Where the lead request packet rests at each layer: the loop's animations are set to just
    // after each plate's front edges light (their --hv-d) and read at once, in the same task, the
    // packet's centre matched to the topmost plate whose hit area holds it, and the edges lit then
    // listed. Only their time is set, never pause() or play(), which would take them out of
    // animation-play-state's hands for the rest of the page's life; they run on, in step, from the
    // last moment set. One entry per lit edge, T1 first
    order() {
      const scene = fig.querySelector('svg.hero-scene');
      const loops = fig.getAnimations({ subtree: true }).filter(a => /^hv-(rise|ping|yping|q|r|a|reached)$/.test(a.animationName || ''));
      const edges = [...scene.querySelectorAll('.hv-reach')], hits = [...scene.querySelectorAll('.hv-hit[data-hv-n]')];
      const lead = [...scene.querySelectorAll('.hv-pkq, .hv-pkr')].filter(c => !c.hasAttribute('style'));
      const layerOf = el => (/hv-reach(\\d)/.exec(el.getAttribute('class')) || [])[1] || '?';
      const out = [];
      for (const edge of edges) {
        const t = parseFloat(/--hv-d:([\\d.]+)s/.exec(edge.getAttribute('style'))[1]) + 0.12;
        loops.forEach(a => { a.currentTime = t * 1000; });
        const pk = lead.find(c => parseFloat(css(c).opacity) > 0.5);
        let n = 0;
        if (pk) {
          const m = new DOMMatrix(css(pk).transform), p = new DOMPoint(m.e, m.f);
          n = Math.max(0, ...hits.filter(h => h.isPointInFill(p)).map(h => Number(h.dataset.hvN)));
        }
        out.push({ edge: layerOf(edge), lit: edges.filter(e => parseFloat(css(e).opacity) > 0.5).map(layerOf).join(','), at: n, fill: pk ? css(pk).fill : '' });
      }
      return { loops: loops.length, out };
    },
    // layer N's card against the sticky header and the window, after a tap; open: the rows open
    // (.is-active), which the tap that checks the seventh layer keeps open after the scene lets
    // go of it (data-hv-active)
    tapped(n) {
      const r = row(n), c = r.querySelector('.hero-card');
      return { active: fig.dataset.hvActive || '', open: rowsWith('.hero-layer.is-active'), place: r.dataset.openPlace || 'none', shown: shown(c) && css(c).clipPath === 'none',
        card: box(c), hb: headerBottom(), ih: innerHeight, y: scrollY, scrolls: (window.__vpScrolls || []).slice() };
    },
    // the hint's lines that a reader sees (shown, and not in the state that is only invisible), as
    // mode/state, such as "pointer/todo" or "click/done", and the hint's height
    hints() {
      const hint = fig.querySelector('.hero-hint');
      if (!shown(hint)) return { lines: [], height: 0 };
      const lines = [...hint.querySelectorAll('.hero-hint-todo > span, .hero-hint-done > span')]
        .filter(s => shown(s) && css(s).visibility === 'visible')
        .map(s => s.className.replace('hero-hint-', '') + '/' + s.parentElement.className.replace('hero-hint-', ''));
      return { lines, height: Math.round(hint.getBoundingClientRect().height * 10) / 10 };
    },
    // the scene's description, the sentences that hero.js adds to it once it has set the figure up,
    // and what grays you now
    desc() {
      const d = fig.querySelector('svg.hero-scene desc'), p = fig.querySelector('.hv-person');
      const g = p ? /grayscale\\(([\\d.]+)\\)/.exec(css(p).filter) : null;
      return { text: d.textContent, live: d.getAttribute('data-hv-live') || '', wait: fig.hasAttribute('data-hv-wait'),
        checked: fig.getAttribute('data-hv-checked'), gray: g ? Number(g[1]) : 0, enhanced: fig.hasAttribute('data-enhanced') };
    },
    // the label column for a sweep: the x of the labels' codes and names, the x of the gap between
    // the scene and the labels (between where the cards start and the labels, where the leaders run),
    // each row's box with the middle of its head line (hy, its name area), and whether every row lies
    // between the sticky header and the window's bottom
    column() {
      const l = fig.querySelector('.hero-layers').getBoundingClientRect(), st = fig.querySelector('.hero-stage').getBoundingClientRect();
      const cards = st.left + st.width * parseFloat(css(fig).getPropertyValue('--hero-card')) / 100;
      const rows = [...fig.querySelectorAll('.hero-layer[data-n]')].map(r => { const h = r.querySelector('.hero-layer-head').getBoundingClientRect();
        return { n: Number(r.dataset.n), ...box(r), hy: Math.round((h.top + h.bottom) / 2) }; });
      return { x: Math.round(l.left + 40), gap: Math.round((cards + l.left) / 2), rows,
        fits: rows[0].top >= headerBottom() + 8 && rows[rows.length - 1].bottom <= innerHeight - 8 };
    },
    // records from now on, in window.__vpWatch, each value that data-hv-checked, data-motion,
    // data-hv-active and data-hv-cheer take, with the page's time (ms) when it took it
    watch() {
      const log = window.__vpWatch = [];
      new MutationObserver(ms => ms.forEach(m => log.push({ t: performance.now(), name: m.attributeName, value: fig.getAttribute(m.attributeName) })))
        .observe(fig, { attributes: true, attributeFilter: ['data-hv-checked', 'data-motion', 'data-hv-active', 'data-hv-cheer'] });
      return true;
    },
    // what watch() recorded, and the page's time now
    watched() { return { log: window.__vpWatch || [], now: performance.now() }; },
    // every data packet now: where its transform puts it in the scene, and its opacity
    packets() {
      return [...fig.querySelectorAll('svg.hero-scene .hv-pk')].map(el => {
        const m = new DOMMatrix(css(el).transform);
        return { x: Math.round(m.e * 10) / 10, y: Math.round(m.f * 10) / 10, o: Math.round(parseFloat(css(el).opacity) * 100) / 100 };
      });
    },
    // a point on an empty part of the stage beside the person, in view below the sticky header:
    // left of every plate and above the person, where nothing opens a layer or plays the moment
    empty() {
      const scene = fig.querySelector('svg.hero-scene'), stage = fig.querySelector('.hero-stage'), ctm = scene.getScreenCTM();
      for (const [sx, sy] of [[-15, 300], [-15, 380], [-15, 220], [-20, 140]]) {
        const q = new DOMPoint(sx, sy).matrixTransform(ctm), x = Math.round(q.x), y = Math.round(q.y);
        if (y < headerBottom() + 8 || y > innerHeight - 8 || x < 0 || x > innerWidth) continue;
        const el = document.elementFromPoint(x, y);
        if (el && stage.contains(el) && !el.closest('.hv-hit, .hv-you-hit, .hero-layer, .hero-person, .hero-hint, .hero-chain')) return [x, y];
      }
      return null;
    },
    // the tabbable element just before layer N's name, focused by script, so that Tab then focuses
    // the name as a reader's key press does; what it is
    beforeName(n) {
      const all = [...document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
        .filter(el => el.tabIndex >= 0 && !el.disabled && el.getClientRects().length && css(el).visibility !== 'hidden');
      const i = all.indexOf(row(n).querySelector('.hero-layer-link'));
      if (i < 1) return '';
      all[i - 1].focus();
      return describe(all[i - 1]);
    },
    // records from now on, in window.__vpTrack, each value data-hv-active takes, and, as the mouse
    // first enters each row's box, what lies under it there (that row, or a card of another layer)
    track() {
      const rows = [...fig.querySelectorAll('.hero-layer[data-n]')];
      const log = window.__vpTrack = { active: [], rows: [] };
      new MutationObserver(() => log.active.push(fig.dataset.hvActive || '-')).observe(fig, { attributes: true, attributeFilter: ['data-hv-active'] });
      let last = '';
      document.addEventListener('pointermove', e => {
        const at = rows.find(r => { const b = r.getBoundingClientRect(); return e.clientY >= b.top && e.clientY <= b.bottom && e.clientX >= b.left && e.clientX <= b.right; });
        const n = at ? at.dataset.n : '';
        if (n && n !== last) {
          const el = document.elementFromPoint(e.clientX, e.clientY), under = el && el.closest('.hero-layer');
          log.rows.push({ n, under: under ? under.dataset.n : '', card: !!(el && el.closest('.hero-card')) });
        }
        last = n;
      }, true);
      return true;
    },
  };
  return true;
})()`;

// Samples, from the first frame of a page load, the filter on the person and whether the window has
// loaded, in window.__vpGray: so a check can see you gray from the first paint, never in colour first.
// It also adds an image from HOLD_URL once the page is parsed, which the check keeps pending through
// the Fetch domain (no network), so the load event waits and frames are drawn before it
const HOLD_URL = "https://vp-hold.invalid/hold.png";
const GRAY_SAMPLER = `(() => {
  window.__vpGray = [];
  let loaded = false;
  addEventListener('load', () => { loaded = true; });
  document.addEventListener('DOMContentLoaded', () => { const i = new Image(); i.alt = ''; i.src = ${JSON.stringify(HOLD_URL)}; document.body.appendChild(i); });
  const tick = () => {
    const p = document.querySelector('.hv-person');
    if (p) window.__vpGray.push({ filter: getComputedStyle(p).filter, loaded });
    if (window.__vpGray.filter(s => s.loaded).length < 5 && window.__vpGray.length < 600) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})()`;
// Makes static/hero.js throw at its first line, before it sets anything up: the phone layout's media
// query, which it asks for first, throws
const HERO_THROWS = `(() => { const mm = window.matchMedia; window.matchMedia = function (q) { if (/44\\.999em/.test(q)) throw new Error('hero.js made to throw'); return mm.call(window, q); }; })()`;

// Two boxes overlap by more than a pixel (boxes that share an edge do not)
const meets = (a, b) => !!a && !!b && a.left < b.right - 1 && a.right > b.left + 1 && a.top < b.bottom - 1 && a.bottom > b.top + 1;
// A page address as the reports print it: from the build's folder on
const short = (url) => (url ? url.replace(/^file:\/\/.*?\/(?=(?:zh\/)?(?:index|topics|latest|articles)\b)/, "") : "nowhere");

// Real input through Chrome's input pipeline, so static/hero.js sees what a reader's browser sends
const mouseTo = (cdp, [x, y]) => cdp.send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y, button: "none" });
async function clickAt(cdp, [x, y]) {
  await mouseTo(cdp, [x, y]);
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 1 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", buttons: 0, clickCount: 1 });
}
// a double click: a click, then 80ms later a second press with clickCount 2, as a mouse sends them
async function doubleClickAt(cdp, [x, y]) {
  await clickAt(cdp, [x, y]);
  await sleep(80);
  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", buttons: 1, clickCount: 2 });
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", buttons: 0, clickCount: 2 });
}
const tapAt = (cdp, [x, y]) => cdp.send("Input.synthesizeTapGesture", { x, y, duration: 60, tapCount: 1, gestureSourceType: "touch" });
const KEY_CODES = { Escape: ["Escape", 27], Shift: ["ShiftLeft", 16], Tab: ["Tab", 9] };
// MODIFIERS: 8 is Shift
async function press(cdp, key, modifiers = 0) {
  const [code, vk] = KEY_CODES[key];
  const k = { key, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk, modifiers };
  await cdp.send("Input.dispatchKeyEvent", { type: "rawKeyDown", ...k });
  await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", ...k });
}
// The mouse from A to B in a straight line at SPEED px/s, in steps of about 20ms (Chrome
// handles one mouse move a frame); returns the speed reached
async function glide(cdp, a, b, speed) {
  const d = Math.hypot(b[0] - a[0], b[1] - a[1]), steps = Math.max(1, Math.ceil(d / Math.max(2, Math.round(speed / 50)))), t0 = Date.now();
  for (let i = 1; i <= steps; i++) {
    await mouseTo(cdp, [Math.round(a[0] + (b[0] - a[0]) * i / steps), Math.round(a[1] + (b[1] - a[1]) * i / steps)]);
    const wait = t0 + (d * i / steps / speed) * 1000 - Date.now();
    if (wait > 0) await sleep(wait);
  }
  return Math.round(d / (Math.max(1, Date.now() - t0) / 1000));
}
// Waits until the page has not scrolled for three readings 50ms apart (the site scrolls
// smoothly), or for 2s
async function settle(cdp) {
  await sleep(60);
  for (let i = 0, last = null, same = 0; i < 40 && same < 3; i++) {
    const y = await evaluate(cdp, "scrollY");
    same = y === last ? same + 1 : 0;
    last = y;
    await sleep(50);
  }
}
// The main frame's next navigation within MS: its address, or null
const navigation = (cdp, ms) => new Promise((done) => {
  const t = setTimeout(() => { off(); done(null); }, ms);
  const off = cdp.on((m) => {
    if (m.method === "Page.frameNavigated" && !m.params.frame.parentId) { off(); clearTimeout(t); done(m.params.frame.url + (m.params.frame.urlFragment || "")); }
  });
});

// Opens layer N's card on the loaded home page as a reader would: the mouse on its plate
// from 45em, a tap on its chevron on a touch screen (then the page scrolls the card into
// view), a click on its chevron on phones.
async function openLayer(cdp, n, width, touch) {
  if (!(await evaluate(cdp, HERO_KIT))) throw new Error("no hero figure to open a card in");
  if (width < 720) await clickAt(cdp, await evaluate(cdp, `__vpHero.at('.hero-more', ${n}, true)`));
  else {
    await evaluate(cdp, "__vpHero.view()");
    if (!(await evaluate(cdp, `__vpHero.plateShown(${n})`))) await evaluate(cdp, `__vpHero.plateInView(${n})`);
    if (touch) {
      await tapAt(cdp, await evaluate(cdp, `__vpHero.reach('.hero-more', ${n})`));
      await settle(cdp);
    } else await mouseTo(cdp, await evaluate(cdp, `__vpHero.plate(${n})`));
  }
  await sleep(400);
  const s = await evaluate(cdp, `__vpHero.state(${n})`);
  if (s.active !== String(n)) throw new Error(`layer ${n}'s card did not open (data-hv-active=${s.active || "none"})`);
}

async function hero(site, opt) {
  const pages = pageMap(site, opt.article);
  // The grace after which hero.js closes an open card once a mouse or pen has left its layer's name,
  // its plate and the card, read from the build's copy of the script
  const script = path.join(site, "assets", "hero.js");
  const GRACE = Number((existsSync(script) && /\bGRACE = (\d+)/.exec(readFileSync(script, "utf8")) || [])[1] || 300);
  const names = list(opt.pages, "home,zh-home");
  const widths = list(opt.widths, "1440,390").map(Number);
  const sizes = list(opt.sizes, "").map((s) => {
    const m = /^(\d+)x(\d+)(?:[x@](\d+(?:\.\d+)?))?$/.exec(s);
    if (!m) throw new Error(`--sizes takes WxH or WxHxD, such as 1366x768 or 720x450x2, not ${JSON.stringify(s)}`);
    if (Number(m[1]) < 720) throw new Error(`--sizes are for the layout from 45em (720px at the default text size), not ${s}`);
    return [Number(m[1]), Number(m[2]), m[3] ? Number(m[3]) : 1];
  });
  // touch tablets in both orientations, and a phone on its side (from 45em, with cards taller
  // than its window); they run when a width from 720 is asked for
  const tablets = (opt.tablets === "none" ? [] : list(opt.tablets, "1024x768,768x1024,1180x820,820x1180,932x430")).map((s) => {
    const m = /^(\d+)x(\d+)$/.exec(s);
    if (!m || Number(m[1]) < 720) throw new Error(`--tablets takes windows WxH from 720 wide, such as 1024x768, or none, not ${JSON.stringify(s)}`);
    return [Number(m[1]), Number(m[2])];
  });
  // the windows in which the mouse rests on every vendor mark, from 45em (none skips them)
  const tipSizes = (opt.tipsizes === "none" ? [] : list(opt.tipsizes, "1920x1080,1536x864,1440x900,1366x768,1280x720,1024x768")).map((s) => {
    const m = /^(\d+)x(\d+)$/.exec(s);
    if (!m || Number(m[1]) < 720) throw new Error(`--tipsizes takes windows WxH from 720 wide, such as 1366x768, or none, not ${JSON.stringify(s)}`);
    return [Number(m[1]), Number(m[2])];
  });
  // --only runs only the checks it names (the others are skipped), such as --only finale
  const CHECKS = ["motion", "legend", "guard", "cards", "paths", "keys", "sweeps", "touch", "finale", "regressions", "phone", "nojs", "tablets", "tips", "band"];
  const only = opt.only ? new Set(list(opt.only)) : null;
  for (const c of only || []) if (!CHECKS.includes(c)) throw new Error(`--only takes checks from ${CHECKS.join(", ")}, not ${JSON.stringify(c)}`);
  for (const name of names) pageFile(site, pages, name);
  let checks = 0, failures = 0;
  const report = (where, ok, text) => { checks++; if (!ok) failures++; console.log(`${where}: ${ok ? "ok  " : "FAIL"} ${text}`); };
  const note = (where, text) => console.log(`${where}: note ${text}`);

  // hero.js belongs to the two home pages only.
  const linked = [];
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(p);
      else if (entry.name.endsWith(".html") && /<script[^>]*src="[^"]*hero\.js/.test(readFileSync(p, "utf8"))) linked.push(path.relative(site, p));
    }
  };
  walk(site);
  const strays = linked.filter((p) => !["index.html", path.join("zh", "index.html")].includes(p));
  report("site", strays.length === 0, strays.length ? `hero.js is also linked from ${strays.join(", ")}`
    : linked.length ? `hero.js is linked from ${linked.join(" and ")} only` : "hero.js is linked from no page");

  // A fresh browser for each page and width: after the key presses of one width's checks,
  // Chrome runs the next pages' timers 100-200ms late, which would skew the timing checks.
  // Focus and blur behave as in a window that has focus, as a reader's does
  let cdp = null;
  const relaunch = async () => {
    if (cdp) cdp.close();
    cdp = await launch();
    await cdp.send("Emulation.setFocusEmulationEnabled", { enabled: true });
  };
  const state = () => evaluate(cdp, HERO_STATE);
  const js = (expression) => evaluate(cdp, expression);
  // the scene, which hero.js watches: on phones the whole figure is about 1800px tall
  const focusHero = `(document.querySelector('[data-verification-visual] .hero-art') || document.querySelector('.hero-visual') || document.body).scrollIntoView({ block: 'center', behavior: 'instant' })`;

  const heroAt = async (at, file, w) => {
    const h = w < 768 ? 844 : 900;
    await open(cdp, file, w, h, false, false);
    await js(focusHero);
    await sleep(400);
    let s = await state();
    if (!s.found) return report(at, false, "no hero figure (.hero-visual or [data-verification-visual])");
    // no caption: the scene's description says what it shows; the two links to the Stack page
    // follow the stage, and the tooltip that names a vendor mark waits hidden, aria-hidden
    report(at, !s.caption && !!s.links && s.links.shown && s.links.parent && s.links.hrefs.length === 2
      && s.links.hrefs.every((h) => /topics\/(index\.html)?(#tiers)?$/.test(h)),
      `no caption, and the two links to the Stack page follow the stage (${s.links ? s.links.hrefs.join(", ") : "none"})`);
    report(at, !!s.tip && !s.tip.shown && s.tip.aria === "true" && !s.tip.text, `the vendor marks' tooltip waits hidden and aria-hidden (${s.tip ? `shown ${s.tip.shown}` : "missing"})`);
    if (s.variant !== "svg") return report(at, false, "the hero holds no inline SVG scene");
    report(at, s.labels === 7, `${s.labels} layer labels (7)`);
    report(at, s.svg.role === "img" && !!s.svg.title, `svg role=${s.svg.role} with title ${JSON.stringify(s.svg.title)}`);
    report(at, CJK.test(s.svg.title) === s.lang.startsWith("zh"), `title is in the page language (${s.lang})`);
    report(at, s.svg.texts === 0 && s.svg.images === 0, `no <text> (${s.svg.texts}) and no <image> (${s.svg.images}) in the scene`);
    report(at, s.scripts.length === 1 && s.scripts[0].defer, `hero.js linked once with defer (${JSON.stringify(s.scripts)})`);
    if (!s.toggle) return report(at, false, "no pause button ([data-motion-toggle])");
    report(at, s.toggle.radius.every((v) => parseFloat(v) === 0), `pause button corners are square (${s.toggle.radius.join(" ")})`);
    report(at, s.toggle.backdrop === "none", `pause button has no backdrop filter (${s.toggle.backdrop})`);
    report(at, s.toggle.fontSize >= 12.95, `pause label is ${s.toggle.fontSize}px (13px)`);

    // Before any layer is checked: you are gray, nothing loops, and "Check all layers" holds the
    // pause control's place; a real double click on it checks every layer, brings your colour back,
    // hands its focus to the pause control and starts the loop, which the second click, landing on
    // the pause control, leaves running
    report(at, !s.animated && s.running === 0 && !s.toggle.shown && !!s.all && s.all.shown && s.gray === 1 && s.checked === "0" && !!s.progress && s.progress.shown,
      `before any layer is checked: no loop (data-animated ${s.animated}, ${s.running} running), the pause control hidden and "Check all layers" shown (${s.all ? s.all.shown : "missing"}), you gray (grayscale ${s.gray}), the progress ${s.progress ? JSON.stringify(s.progress.text) : "missing"}`);
    if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the checks");
    // the hint by input: a mouse points from 45em and clicks the arrows in the list below it
    const mode = w >= 720 ? "pointer" : "click";
    const before = await js("__vpHero.hints()");
    report(at, before.lines.length === 1 && before.lines[0] === `${mode}/todo`, `the hint gives the ${mode} line (${before.lines.join(", ") || "none"})`);
    const button = await js("__vpHero.checkAll()");
    if (!button) return report(at, false, `"Check all layers" is not shown`);
    await doubleClickAt(cdp, button);
    await sleep(150);
    s = await state();
    report(at, s.checked === "7" && s.progress.text === s.progress.done && !s.all.shown && s.toggle.shown && s.focus === "pause",
      `"Check all layers" checks all seven (data-hv-checked ${s.checked}): the progress reads ${JSON.stringify(s.progress.text)}, the button goes, the pause control shows and takes its focus (focus on ${s.focus})`);
    report(at, s.motion !== "paused" && s.toggle.label === s.toggle.pause,
      `a double click on "Check all layers" leaves the loop running: data-motion=${s.motion}, the pause control reads ${JSON.stringify(s.toggle.label)}`);
    {
      const after = await js("__vpHero.hints()");
      report(at, after.lines.length === 1 && after.lines[0] === `${mode}/done` && after.height === before.height,
        `once every layer is checked the hint gives its ${mode} line without the promise of colour (${after.lines.join(", ") || "none"}) and keeps its height (${before.height}px, then ${after.height}px)`);
    }
    await sleep(2300);   // your moment (1.8s), and the colour's 0.6s
    await js(focusHero);
    await sleep(300);
    s = await state();
    report(at, s.gray === 0, `you are in full colour (grayscale ${s.gray})`);
    // Motion allowed: running in view, paused by the button, suspended off-screen and in a hidden tab.
    report(at, s.motion === "running" && s.animated && s.running > 0, `in view: data-motion=${s.motion}, ${s.running} of ${s.animations} animations running`);
    {
      const y = await js("__vpHero.you()");
      report(at, y.packets && y.plays === "running" && y.route, `the data packets and their dotted route are drawn, and the packets run (${y.plays})`);
      // the data rests on one object of every layer in order, each plate's edges lighting as it arrives
      const o = await js("__vpHero.order()");
      const ok = o.out.length === 7 && o.out.every((e, i) => e.edge === String(i + 1) && e.lit === e.edge && e.at === i + 1);
      report(at, ok, `the data rests on T1 to T7 in order, each plate's edges lit as it arrives: ${o.out.map((e) => `T${e.edge} at T${e.at}, lit ${e.lit || "none"}`).join("; ")}`);
      const tee = o.out.map((e) => e.fill), [t1, t2, t3] = tee;
      report(at, t1 === t2 && t1 !== t3 && tee.slice(2).every((f) => f === t3), `the data is indigo on T1 and T2 (${t1}) and in your colour above them (${t3})`);
    }
    report(at, s.toggle.shown && s.toggle.label === s.toggle.pause && s.toggle.aria === s.toggle.pause, `button shows ${JSON.stringify(s.toggle.label)}, aria-label ${JSON.stringify(s.toggle.aria)}`);
    report(at, !s.still || !s.still.shown, "still-image label hidden while motion is allowed");
    await js(`document.querySelector('[data-motion-toggle]').click()`);
    await sleep(150);
    s = await state();
    report(at, s.motion === "paused" && s.running === 0, `after a click: data-motion=${s.motion}, ${s.running} running`);
    {
      const y = await js("__vpHero.you()");
      report(at, y.plays === "paused", `paused: the data packets hold where they are (${y.plays})`);
    }
    report(at, s.toggle.label === s.toggle.play && s.toggle.aria === s.toggle.play, `after a click the button reads ${JSON.stringify(s.toggle.label)}, aria-label ${JSON.stringify(s.toggle.aria)}`);
    await js(`document.querySelector('[data-motion-toggle]').click()`);
    await sleep(150);
    s = await state();
    report(at, s.motion === "running" && s.running > 0 && s.toggle.label === s.toggle.pause, `after a second click: data-motion=${s.motion}, label ${JSON.stringify(s.toggle.label)}`);
    const below = s.top + s.height + h;
    if (s.pageHeight > below) {
      await js(`window.scrollTo({ top: ${Math.ceil(below)}, behavior: 'instant' })`);
      await sleep(400);
      s = await state();
      report(at, s.motion === "suspended" && s.running === 0, `scrolled out of view: data-motion=${s.motion}, ${s.running} running`);
      await js(focusHero);
      await sleep(400);
      s = await state();
      report(at, s.motion === "running", `the scene back in view: data-motion=${s.motion}`);
    } else note(at, "page too short to scroll the hero out of view; off-screen suspension not tested");
    await js(`Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange'))`);
    await sleep(150);
    s = await state();
    report(at, s.motion === "suspended" && s.running === 0, `hidden tab (simulated): data-motion=${s.motion}, ${s.running} running`);
    await js(`delete document.hidden; document.dispatchEvent(new Event('visibilitychange'))`);
    await sleep(150);
    s = await state();
    report(at, s.motion === "running", `visible again: data-motion=${s.motion}`);
    if (opt.frames) {
      const rate = Number(opt.cpu || 1);
      if (rate > 1) await cdp.send("Emulation.setCPUThrottlingRate", { rate });
      const f = await js(FRAMES);
      if (rate > 1) await cdp.send("Emulation.setCPUThrottlingRate", { rate: 1 });
      console.log(`${at}: frames ${f.frames} in ${f.ms} ms, longest ${f.worst} ms${rate > 1 ? ` at ${rate}x CPU throttling` : ""}`);
    }

    // Reduced motion: the still frame, with no animation, no pause button and, once every layer is
    // checked, a visible label; before that "Check all layers" has the corner. The colour comes back
    // at once
    await open(cdp, file, w, h, false, true);
    await sleep(300);
    s = await state();
    if (!s.found) return report(at, false, "reduced motion: no hero figure");
    report(at, s.all && s.all.shown && !(s.still && s.still.shown) && s.gray === 1, `reduced motion, before any layer is checked: "Check all layers" shown, the still-image label waiting (${s.still && s.still.shown}), you gray (grayscale ${s.gray})`);
    if (!(await js(HERO_KIT))) return;
    await clickAt(cdp, await js("__vpHero.checkAll()"));
    await sleep(60);
    s = await state();
    report(at, s.checked === "7" && s.gray === 0 && s.focus === "progress", `reduced motion: "Check all layers" brings your colour back at once (grayscale ${s.gray} after 60ms) and hands its focus to the progress (focus on ${s.focus})`);
    await sleep(1900);
    s = await state();
    report(at, s.motion === "static" && !s.animated && s.animations === 0, `reduced motion: data-motion=${s.motion}, ${s.animations} animations in the hero`);
    report(at, !!s.toggle && !s.toggle.shown, "reduced motion: pause button hidden");
    report(at, !!(s.still && s.still.shown && s.still.text), `reduced motion: still-image label ${s.still ? JSON.stringify(s.still.text) : "missing"} is visible`);
    report(at, !!s.pulse && !s.pulse.shown, `reduced motion: the pulse is ${s.pulse ? (s.pulse.shown ? "shown" : "hidden") : "missing"}`);
    // The still frame draws the chain by binding status (data-hv-rest="status"), or whole
    const c = await js("__vpHero.chain()");
    report(at, c.segments.length === 6, `reduced motion: data-hv-chain names segments ${c.segments.map((g) => g.k).join(", ")} (2 to 7)`);
    for (const g of c.segments) {
      const status = c.rest === "status" ? g.status : "deployed";
      const want = { deployed: ["solid", false], emerging: ["dashed", false], missing: ["hidden", true] }[status];
      const ok = !!want && g.beams.length > 0 && g.beams.every((b) => b === want[0]) && g.stubs.length === 2 && g.stubs.every((d) => d === want[1]);
      report(at, ok, `reduced motion: segment ${g.k} (${g.status}, chain at rest "${c.rest}") is drawn ${g.beams.join("/")}, stubs ${g.stubs.map((d) => (d ? "shown" : "hidden")).join("/")}`);
    }
    report(at, c.ring, "reduced motion: the ring on the person's phone is drawn");
    report(at, c.halos[0] !== "none" && c.halos[0] === c.halos[1], `reduced motion: the phone's halo rests at ring 1's opacity (${c.halos.join(" and ")})`);
    let y = await js("__vpHero.you(true)");
    report(at, !y.packets && y.plays === "none" && y.route, `reduced motion: the data packets are not drawn (${y.plays} animation) and the dotted route is (${y.route})`);
    if (y.hit) {
      await sleep(150);
      await clickAt(cdp, (await js("__vpHero.you()")).hit);
      await sleep(150);
      y = await js("__vpHero.you()");
      report(at, y.cheer && y.bubble === 1 && y.screen === 1 && y.running === 0 && !y.active,
        `reduced motion: a click on the person shows their moment still (data-hv-cheer ${y.cheer}, bubble ${y.bubble}, screen ${y.screen}, ${y.running} animations running) and opens no layer`);
    } else report(at, false, "reduced motion: no hit area on the person");
  };

  // From 45em: the person's label, legend and hint, the first screen, the examples that open nothing
  // and a mark beside an open card, the mouse on each plate (spec 8.3, items 1 and 2), each name
  // area and name, leaving the stage (4) and Esc (3)
  const cards = async (at, file, w, h, dpr = 1) => {
    const outside = [4, h - 10];   // the page's left margin, off the stage
    await open(cdp, file, w, h, false, false, false, dpr);
    if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the layer cards");
    // the first screen, before anything scrolls: the stage was capped to fit it
    const f = await js("__vpHero.fold()");
    if (f.side && h >= 720 && f.y === 0) {
      const ok = !!f.person && !!f.hint && f.person.bottom <= f.ih + 0.5 && f.hint.bottom <= f.ih + 0.5 && f.hint.left >= f.labels.left - 0.5;
      report(at, ok, `first screen: the person's label ends at ${Math.round(f.person.bottom)} and the hint at ${f.hint ? Math.round(f.hint.bottom) : "(not shown)"}, within ${f.ih}; the hint starts at ${f.hint ? Math.round(f.hint.left) : "?"}, under the label column (${Math.round(f.labels.left)})`);
    }
    await js("__vpHero.view()");
    const k = await js("__vpHero.parts()");
    report(at, k.enhanced && k.hits, `hero.js ran (data-enhanced ${k.enhanced}) and turned the plates on (data-hv-hits ${k.hits})`);
    report(at, k.person && k.legend > 0 && k.hint, `the person's label, the legend (${k.legend} runs) and the hint are shown`);
    {
      const t = await js("__vpHero.hints()");
      report(at, t.lines.length === 1 && t.lines[0] === "pointer/todo", `the hint gives the pointer line (${t.lines.join(", ") || "none"})`);
    }
    report(at, k.chevrons.length === 7 && k.chevrons.every((c) => !c.shown), "the chevrons stay hidden with a fine pointer");
    // The examples under each name, its vendor marks and names, open nothing: on the fresh page the
    // mouse on every one of them, row by row and after a rest, opens and checks no layer
    {
      const problems = [];
      let count = 0;
      for (let n = 7; n >= 1; n--) {
        await mouseTo(cdp, outside);
        await js(`__vpHero.reachRow(${n})`);
        for (const p of await js(`__vpHero.examples(${n})`)) { await mouseTo(cdp, p); await sleep(40); count++; }
        await sleep(300);
        const s = await js(`__vpHero.state(${n})`), pr = await js("__vpHero.progress()");
        if (s.active || pr.checked !== "0") problems.push(`T${n}: the mouse on its examples opened ${s.active ? "T" + s.active : "nothing"} and checked ${pr.checked} layer(s)`);
      }
      await mouseTo(cdp, outside);
      await sleep(300);
      report(at, problems.length === 0, `the mouse on each of the ${count} examples under the names, marks and names, opens and checks no layer${problems.length ? ": " + problems.join("; ") : ""}`);
    }
    // With T5's card open from its name, the mouse on a vendor mark of another row, clear of the card,
    // switches nothing and checks no other layer; the card, which the pointer has left with its name,
    // closes once the grace (GRACE ms) has run out, and the mark's layer stays unchecked
    {
      await js("__vpHero.reachRow(5)");
      await mouseTo(cdp, await js("__vpHero.centre('.hero-layer-link', 5)"));
      await sleep(400);
      const five = await js("__vpHero.state(5)"), i = await js("__vpHero.freeMark(5)");
      if (five.active !== "5" || five.place === "none") report(at, false, `the mouse resting on T5's name did not show its card (data-hv-active=${five.active || "none"}, ${five.place})`);
      else if (i < 0) note(at, "no vendor mark lies clear of T5's card in view; the mark beside an open card is not tested");
      else {
        const { n, name } = (await js("__vpHero.marks()"))[i];
        await mouseTo(cdp, await js(`__vpHero.mark(${i})`));
        await sleep(60);
        const now = await js(`__vpHero.state(${n})`), p1 = await js("__vpHero.progress()");
        await sleep(GRACE + 150);
        const later = await js(`__vpHero.state(${n})`), p2 = await js("__vpHero.progress()"), t = await js("__vpHero.tip()");
        report(at, now.active === "5" && p1.checked === "1" && !later.active && p2.checked === "1" && t.shown && t.text === name,
          `with T5's card open from its name, the mouse on ${name} (T${n}) switches nothing (data-hv-active=${now.active || "none"}, ${p1.checked} checked) and the card closes once the pointer has been off T5's name and card for the grace (data-hv-active=${later.active || "none"} after ${GRACE + 150}ms, ${p2.checked} checked), while the tooltip names the mark (${t.shown ? JSON.stringify(t.text) : "not shown"})`);
      }
      // a fresh page again, so that the plates below check the layers from none
      await open(cdp, file, w, h, false, false, false, dpr);
      if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the layer cards");
      await js("__vpHero.view()");
    }
    for (let n = 7; n >= 1; n--) {
      const where = `${at} T${n}`;
      if (!(await js(`__vpHero.plateShown(${n})`))) {
        // a short window: let the open card close, then bring the plate into view
        await mouseTo(cdp, outside);
        await sleep(400);
        await js(`__vpHero.plateInView(${n})`);
      }
      await mouseTo(cdp, await js(`__vpHero.plate(${n})`));
      await sleep(320);   // a plate opens at once: hero.js reads the pointer once a frame
      await js("__vpHero.calm()");
      const s = await js(`__vpHero.state(${n})`);
      const b = s.card && s.card.box;
      report(where, s.active === String(n) && s.rows === String(n) && s.leaders === String(n) && s.expanded === String(n),
        `the mouse on plate ${n} opens it: data-hv-active=${s.active || "none"}, .is-active on ${s.rows || "no row"}, leader ${s.leaders || "none"}, aria-expanded ${s.expanded || "none"}`);
      if (!b) continue;
      report(where, s.card.shown && s.card.clip === "none" && b.width > 200, `the card is shown, ${Math.round(b.width)}px wide, opening ${s.place} (prefers ${s.prefers})`);
      const room = { up: s.row.top - s.gap - s.lo, down: s.hi - (s.row.bottom + s.gap) };
      const tall = Math.round(b.height), fits = b.height <= s.hi - s.lo + 0.5;
      // the room for a card fitted over its label's head, from the ceiling to the head's bottom; with
      // room on neither side nor there, the card opens below its label and runs past the room's bottom
      const over = s.head.bottom - s.lo, spill = fits && room.up < b.height && room.down < b.height && over < b.height;
      if (s.place === "fit") {
        report(where, room.up < b.height && room.down < b.height && Math.abs(b.bottom - s.head.bottom) < 1.5,
          `the card is fitted over its own label's head, ending at the head's bottom (${Math.round(b.bottom)}, the head's ${Math.round(s.head.bottom)}), only because neither side has room for its ${tall}px (${Math.round(room.up)}px above, ${Math.round(room.down)}px below)`);
      } else {
        report(where, !meets(b, s.head) && (s.place === s.prefers || room[s.prefers] < b.height),
          `the card is clear of its own label, on ${s.place === s.prefers ? "its preferred side" : `the other side (${Math.round(room[s.prefers])}px ${s.prefers} for its ${tall}px)`}`);
      }
      // a card never lies over its own label's examples, so every mark there keeps its name
      report(where, !meets(b, s.examples), `the card leaves its own label's examples in view (${Math.round(s.examples.top)} to ${Math.round(s.examples.bottom)})`);
      if (spill) {
        report(where, s.place === "down" && b.top >= s.lo - 0.5 && s.hi - b.top >= 64 - 0.5,
          `the card has room on neither side nor over its label's head (${Math.round(over)}px for its ${tall}px), so it opens below its label (${s.place}, from ${Math.round(b.top)}) with its head in the room, running ${Math.round(b.bottom - s.hi)}px past the room's bottom (${Math.round(s.hi)})`);
        note(where, `the card runs ${Math.round(b.bottom - s.hi)}px past the room's bottom, so that its own label's marks stay in view`);
      } else if (fits) {
        report(where, b.top >= s.lo - 0.5 && b.bottom <= s.hi + 0.5,
          `the card (${Math.round(b.top)} to ${Math.round(b.bottom)}) lies between ${Math.round(s.lo)}, below the ceiling, the pause control and the header, and ${Math.round(s.hi)}, the stage's or the window's bottom`);
      } else {
        report(where, b.top >= s.lo - 0.5, `the card (${tall}px) is taller than the room (${Math.round(s.lo)} to ${Math.round(s.hi)}) and keeps its head in it (from ${Math.round(b.top)})`);
      }
      report(where, !meets(b, s.pause) && !meets(b, s.person) && !meets(b, s.intro) && (!fits || spill || !meets(b, s.links)),
        "the card covers neither the pause control, the person's label, the links under the stage nor the intro");
      if ((!fits || spill) && meets(b, s.links)) note(where, "the card, running past the room's bottom, lies over the links under the stage while it is open");
      // what the card lies over is hidden, and only what lies within 8px of it, as hero.js marks it,
      // with half a pixel to spare: hero.js works out where the card ends, this reads its box, and a
      // row exactly 8px away (T6 above T1's card in Chinese at 1184) falls on either side by a
      // rounding error
      const near = (o) => b.top - 8.5 < o.box.bottom && b.bottom + 8.5 > o.box.top && b.left < o.box.right && b.right > o.box.left;
      const under = s.others.filter((o) => meets(b, o.box));
      const wrong = [...under.filter((o) => !o.covered || o.opacity !== "0"), ...s.others.filter((o) => o.covered && !near(o))];
      report(where, wrong.length === 0, `what the card lies over is hidden (.is-covered, opacity 0): ${under.map((o) => o.name).join(", ") || "nothing"}${wrong.length ? "; wrong: " + wrong.map((o) => `${o.name} .is-covered ${o.covered}, opacity ${o.opacity}`).join(", ") : ""}`);
      report(where, s.motion === "suspended", `data-motion=${s.motion} while the card is open`);
      const y = await js("__vpHero.you()");
      const tee = n <= 2;
      report(where, y.glow > 0 && !y.packets && (tee ? y.bubble === 1 && y.screen === 1 : y.bubble === 0 && y.screen === 0),
        `the person is lit (glow ${y.glow}), the data packets are hidden (${!y.packets}), and the bubble and the indigo screen are ${tee ? "shown on a TEE layer" : "hidden off the TEE layers"} (${y.bubble}, ${y.screen})`);
      // pointing at a layer checks it: a mark by its name, the count, and a step of colour back
      const p = await js("__vpHero.progress()"), done = [7, 6, 5, 4, 3, 2, 1].filter((k) => k >= n).join(",");
      if (n === 5 || n === 1) {
        report(where, p.marks === done && p.checked === String(8 - n) && (n === 5 ? p.gray > 0.3 && p.gray < 0.7 && !p.animated : p.gray < 0.05 && p.animated && !p.all),
          `pointing at ${8 - n} layers checks them: marks on ${p.marks || "none"}, data-hv-checked ${p.checked}, the progress ${JSON.stringify(p.text)}, grayscale ${p.gray}, the loop ${p.animated ? "may run" : "waits"}`);
      } else if (p.marks !== done) report(where, false, `pointing at T${n} left marks on ${p.marks || "none"} (${done} expected)`);
    }
    // Each label's name area, the head line with the code and name ("T5 Agents", its code a quiet
    // prefix in another colour than the name), is the target: the name link's target spans it from
    // the row's rule to the column's edge, at least 24px tall, with a pointer cursor and the name
    // underlined under the mouse, and none of the examples under it lies under that target. The
    // mouse on each name opens its layer at once and, after a rest, its card
    {
      const problems = [], codes = [], places = [];
      for (let n = 7; n >= 1; n--) {
        await mouseTo(cdp, outside);
        await sleep(GRACE + 100);
        await js(`__vpHero.reachRow(${n})`);
        const t0 = await js(`__vpHero.target(${n}, false)`);
        await mouseTo(cdp, await js(`__vpHero.centre('.hero-layer-link', ${n})`));
        await sleep(60);
        const t = await js(`__vpHero.target(${n}, true)`), now = await js(`__vpHero.state(${n})`);
        codes.push(t0.text.replace(/\s+/g, " "));
        const link = `a.hero-layer-link@${n}`;
        if (t0.code !== `T${n}` || !t0.quiet) problems.push(`T${n}: the name reads ${JSON.stringify(t0.text)}, its code ${JSON.stringify(t0.code)}${t0.quiet ? "" : " in the name's own colour"}`);
        const missed = t0.name.filter((p) => p.what !== link || p.cursor !== "pointer");
        if (missed.length) problems.push(`T${n}: the name area gives ${missed.map((p) => `${p.what} (${p.cursor})`).join(", ")}`);
        if (t.underline !== "underline") problems.push(`T${n}: the name is not underlined under the mouse (${t.underline})`);
        if (t0.head + 0.45 * 16 < 24 - 0.5) problems.push(`T${n}: the name area is ${Math.round(t0.head + 0.45 * 16)}px tall`);
        const onName = t0.examples.filter((p) => p.what.startsWith("a.hero-layer-link"));
        if (onName.length) problems.push(`T${n}: ${onName.length} example(s) lie under the name's target`);
        if (now.active !== String(n) || now.place !== "none") problems.push(`T${n}: the mouse on its name gave data-hv-active=${now.active || "none"}, card ${now.place}`);
        await sleep(340);
        const s = await js(`__vpHero.state(${n})`);
        places.push(`T${n} ${s.place}`);
        if (s.active !== String(n) || !s.card || !s.card.shown || s.card.clip !== "none") problems.push(`T${n}: no card after a rest on its name (${s.place})`);
      }
      report(at, problems.length === 0, `each name area (${codes.join(", ")}) is the name link's target from the row's rule to the column's edge, at least 24px tall, with a pointer cursor and the name underlined, and no example lies under it; the mouse on each name opens its layer at once and, after a rest, its card (${places.join(", ")})${problems.length ? ": " + problems.join("; ") : ""}`);
      // from a name, the mouse onto its own examples: they open nothing, but they hold the open card
      // (the way to a card below its label crosses them) until the pointer leaves the row
      await mouseTo(cdp, outside);
      await sleep(GRACE + 100);
      await js("__vpHero.reachRow(4)");
      await mouseTo(cdp, await js("__vpHero.centre('.hero-layer-link', 4)"));
      await sleep(400);
      const shown = (await js("__vpHero.state(4)")).place;
      const ex = await js("__vpHero.examples(4)");
      await mouseTo(cdp, ex[ex.length - 1]);
      await sleep(GRACE + 100);
      const kept = (await js("__vpHero.state(4)")).active;
      await mouseTo(cdp, outside);
      await sleep(GRACE + 100);
      const gone = (await js("__vpHero.state(4)")).active;
      report(at, shown !== "none" && kept === "4" && !gone,
        `from T4's name, its card shown (${shown}), the mouse resting on T4's own examples keeps the card open (data-hv-active=${kept || "none"} after ${GRACE + 100}ms there) and leaving the stage closes it once the grace has run out (data-hv-active=${gone || "none"} after ${GRACE + 100}ms)`);
    }
    // With the last card closed the loop runs (finale checks that it runs beside that card too). A
    // click on the person plays their moment for 1.8s and opens no layer; with a card open it leaves
    // the card as it was, to close once the pointer has been off its plate and card for the grace.
    // Then the person's hit area is out of the way of the plates
    await mouseTo(cdp, outside);
    await sleep(1600);   // the moment that the seventh layer played is over
    {
      const p = await js("__vpHero.progress()");
      report(at, p.motion === "running" || p.motion === "suspended" && !p.active, `with every layer checked and no card open the loop runs (data-motion=${p.motion}${p.active ? ", data-hv-active=" + p.active : ""})`);
      const t = await js("__vpHero.hints()");
      report(at, t.lines.length === 1 && t.lines[0] === "pointer/done", `with every layer checked the hint gives the pointer line without the promise of colour (${t.lines.join(", ") || "none"})`);
    }
    let y = await js("__vpHero.you(true)");
    await sleep(150);
    y = await js("__vpHero.you()");
    if (!y.hit) report(at, false, "no hit area on the person");
    else {
      report(at, y.pointer === "all" && !y.cheer, `the person's hit area takes the pointer (pointer-events ${y.pointer})`);
      await clickAt(cdp, y.hit);
      await sleep(800);
      let z = await js("__vpHero.you()");
      report(at, z.cheer && !z.active && z.bubble === 1 && z.screen === 1 && z.glow > 0,
        `a click on the person plays their moment (data-hv-cheer ${z.cheer}, bubble ${z.bubble}, screen ${z.screen}, glow ${z.glow}) and opens no layer (data-hv-active=${z.active || "none"})`);
      await sleep(1400);
      z = await js("__vpHero.you()");
      report(at, !z.cheer && z.bubble === 0, `the moment is over 2.2s after the click (data-hv-cheer ${z.cheer}, bubble ${z.bubble})`);
      if (await js("__vpHero.plateShown(4)")) {
        await mouseTo(cdp, await js("__vpHero.plate(4)"));
        await sleep(320);
        await clickAt(cdp, y.hit);
        await sleep(60);
        z = await js("__vpHero.you()");
        await sleep(GRACE + 100);
        const after = await js("__vpHero.you()");
        report(at, z.cheer && z.active === "4" && after.cheer && !after.active,
          `with T4 open, a click on the person plays the moment and leaves the card open (data-hv-active=${z.active || "none"}), which then closes once the pointer has been off plate 4 and the card for the grace (data-hv-active=${after.active || "none"})`);
        await mouseTo(cdp, outside);
        await sleep(2000);
      } else note(at, "plate 4 is out of view beside the person; the click with a card open is not tested");
    }
    // Leaving the stage closes the card once the grace has run out (spec 5.2)
    if (!(await js("__vpHero.plateShown(4)"))) { await mouseTo(cdp, outside); await sleep(400); await js("__vpHero.plateInView(4)"); }
    await mouseTo(cdp, await js("__vpHero.plate(4)"));
    await sleep(320);
    await js("__vpHero.watchLeave()");
    await mouseTo(cdp, outside);
    const ms = await js("__vpHero.left");
    report(at, ms >= GRACE - 50 && ms <= GRACE + 150, ms === -2 ? "no card was open when the mouse left the stage"
      : ms === -1 ? "the card stays open after the mouse leaves the stage" : `the card closes ${ms}ms after the mouse leaves the stage (after its ${GRACE}ms grace, within ${GRACE + 150}ms)`);
    // Esc closes the card, and the pointer resting on its plate does not reopen it
    await mouseTo(cdp, await js("__vpHero.plate(4)"));
    await sleep(320);
    await press(cdp, "Escape");
    await sleep(320);
    const s = await js("__vpHero.state(4)");
    report(at, !s.active && !s.rows, `Esc closes the card opened by the mouse, and it stays closed (data-hv-active=${s.active || "none"})`);
    await mouseTo(cdp, outside);
    await sleep(320);
  };

  // From 45em, the keyboard (spec 8.3, item 3), with real Tab and Shift+Tab: the order of the
  // stops, each focused element in view, and the open card in view when it and its label fit
  const keys = async (at, file, w, h, dpr = 1) => {
    await open(cdp, file, w, h, false, false, false, dpr);
    if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the keyboard");
    const stories = new Set(await js("__vpHero.stories()"));
    const start = await js("__vpHero.before()");
    if (!start) return report(at, false, "nothing comes before the figure in the tab order");
    const tab = async (back = false) => { await press(cdp, "Tab", back ? 8 : 0); await settle(cdp); return js("__vpHero.focused()"); };
    let problems = [];
    const tall = new Set();
    const stop = (f, want, n) => {
      if (f.focus !== want) problems.push(`${want} expected, focus on ${f.focus}`);
      if (!f.box || f.box.top < f.hb - 1 || f.box.bottom > f.ih + 1) {
        problems.push(`${f.focus} at ${f.box ? Math.round(f.box.top) + " to " + Math.round(f.box.bottom) : "?"}, outside ${Math.round(f.hb)} to ${f.ih}`);
      }
      if (f.active !== (n ? String(n) : "") || (n && !f.shown)) problems.push(`at ${f.focus} T${n || "-"} open expected, data-hv-active=${f.active || "none"}`);
      if (f.card && f.shown) {
        const a = Math.min(f.card.top, f.row.top), b = Math.max(f.card.bottom, f.row.bottom);
        if (b - a > f.ih - 8 - (f.hb + 8)) tall.add(f.active);
        else if (f.card.top < f.hb - 1 || f.card.bottom > f.ih + 1) {
          problems.push(`at ${f.focus} T${f.active}'s card (${f.place}) at ${Math.round(f.card.top)} to ${Math.round(f.card.bottom)}, outside ${Math.round(f.hb)} to ${f.ih}`);
        }
      }
    };
    // before any layer is checked "Check all layers" stands in the pause control's place, so Tab
    // meets it first; focusing each name checks its layer, and once T1's is focused the pause
    // control is back, which Shift+Tab meets last
    stop(await tab(), "button.hero-all", null);
    for (let n = 7; n >= 1; n--) {
      stop(await tab(), `a.hero-layer-link@${n}`, n);
      if (!stories.has(n)) { note(`${at} T${n}`, "the card has no stories link"); continue; }
      stop(await tab(), `a.hc-count@${n}`, n);
      // Esc on the stories link closes the card and returns focus to the name; Tab back reopens it
      await press(cdp, "Escape");
      await settle(cdp);
      const e = await js("__vpHero.focused()");
      report(`${at} T${n}`, !e.active && e.focus === `a.hero-layer-link@${n}`, `Esc on the stories link closes the card and returns focus to the name (focus ${e.focus}, data-hv-active=${e.active || "none"})`);
      stop(await tab(), `a.hc-count@${n}`, n);
    }
    stop(await tab(), "a@links", null);
    stop(await tab(), "a@links", null);
    report(at, problems.length === 0, `Tab from ${start}: "Check all layers", each layer's name and stories link (T7 first), then the two links under the stage, each in view under the header, with its card open and in view${problems.length ? ": " + problems.join("; ") : ""}`);
    {
      const p = await js("__vpHero.progress()");
      report(at, p.checked === "7" && p.marks === "7,6,5,4,3,2,1" && p.animated && !p.all && p.gray < 0.05,
        `focusing the seven names checked every layer (marks on ${p.marks || "none"}, the progress ${JSON.stringify(p.text)}), and the loop may run with "Check all layers" gone`);
    }
    problems = [];
    stop(await tab(true), "a@links", null);
    for (let n = 1; n <= 7; n++) {
      if (stories.has(n)) stop(await tab(true), `a.hc-count@${n}`, n);
      stop(await tab(true), `a.hero-layer-link@${n}`, n);
    }
    stop(await tab(true), "button.verification-motion", null);
    report(at, problems.length === 0, `Shift+Tab back to the pause control, T1 first: each focused element in view under the header, with its card open and in view${problems.length ? ": " + problems.join("; ") : ""}`);
    if (tall.size) note(at, `the card and label of ${[...tall].sort().reverse().map((n) => "T" + n).join(", ")} are taller than the window, so only the focused element was kept in view`);
  };

  // From 45em, sweeps: pointing at each layer checks it, so a reader must be able to point at every
  // name and every plate in one sweep. The mouse goes down and up the label column (over the labels'
  // codes and names, and the examples between them) and down and up the plates (through each plate's
  // point), at about 250px/s, from just outside the first to just past the last: each layer opens in
  // turn, T7 to T1 or T1 to T7, all seven are checked, and the mouse reaches each label itself, never
  // a card lying over it. Then down and up the names again with a rest on each: as the mouse arrives
  // the layer is open and checked but shows no card yet, or, for a name that lies between the card
  // before and that card's own label (that card past it), the name waits while the mouse heads for
  // that card and opens, with its card, once the mouse has rested on it for 200ms; after 400ms its
  // card shows, clear of the next label (not .is-covered, not under the card), of its own label's
  // examples, of the pause control, the person's label and the intro, and the sweep goes on. Then a
  // rest on the first name only, the mouse coming onto it along the column and, again, from the gap
  // between the scene and the labels (from the side): its card shows clear of its own examples and of
  // the next label, and the next name, once the mouse stops on it, opens. A window too short for the
  // whole column in view is noted and skipped
  const sweeps = async (at, file, w, h, dpr = 1) => {
    const outside = [4, h - 10];
    const begin = async () => {
      await open(cdp, file, w, h, false, false, false, dpr);
      if (!(await js(HERO_KIT))) { report(at, false, "no hero figure for the sweeps"); return null; }
      await js("__vpHero.view()");
      const col = await js("__vpHero.column()");
      if (!col.fits) { note(at, "the label column does not fit the window below the header; the sweeps are skipped"); return null; }
      await mouseTo(cdp, outside);
      await sleep(300);
      await js("__vpHero.track()");
      return col;
    };
    const order = (dir) => (dir === "down" ? [7, 6, 5, 4, 3, 2, 1] : [1, 2, 3, 4, 5, 6, 7]);
    // what the tracker saw: the layers opened in turn, and each label the mouse reached under a card
    // of another layer (a row whose box starts where nothing of it is hit, as at its far right edge
    // from the side, counts as reached)
    const tracked = async () => {
      const log = await js("window.__vpTrack");
      return { opened: log.active.filter((v, i, a) => v !== "-" && v !== a[i - 1]).join(","),
        blocked: log.rows.filter((r) => r.under !== r.n && (r.under || r.card)).map((r) => `T${r.n} (${r.card ? `under T${r.under}'s card` : `under T${r.under}`})`) };
    };
    for (const [what, dir] of [["labels", "down"], ["labels", "up"], ["plates", "down"], ["plates", "up"]]) {
      const col = await begin();
      if (!col) return;
      let path;
      if (what === "labels") {
        const top = Math.round(col.rows[0].top - 25), bottom = Math.round(col.rows[6].bottom + 25);
        path = dir === "down" ? [[col.x, top], [col.x, bottom]] : [[col.x, bottom], [col.x, top]];
      } else {
        const points = [];
        for (let n = 7; n >= 1; n--) points.push(await js(`__vpHero.plate(${n})`));
        path = [[points[0][0], points[0][1] - 30], ...points, [points[6][0], points[6][1] + 30]];
        if (dir === "up") path.reverse();
      }
      await mouseTo(cdp, path[0]);
      await sleep(60);
      let speed = 0;
      for (let i = 1; i < path.length; i++) speed = await glide(cdp, path[i - 1], path[i], 250);
      await sleep(150);
      const { opened, blocked } = await tracked();
      const p = await js("__vpHero.progress()");
      report(at, opened === order(dir).join(",") && p.checked === "7" && (what === "plates" || blocked.length === 0),
        `a sweep ${dir} the ${what} at ${speed}px/s opens ${opened || "nothing"} in turn and checks ${p.checked || 0} of 7${what === "labels" ? `, reaching each label itself${blocked.length ? "; a card lay over " + blocked.join(", ") : ""}` : ""}`);
    }
    for (const dir of ["down", "up"]) {
      const col = await begin();
      if (!col) return;
      const centre = (n) => [col.x, col.rows[7 - n].hy];
      let from = [col.x, dir === "down" ? Math.round(col.rows[0].top - 25) : Math.round(col.rows[6].bottom + 25)];
      await mouseTo(cdp, from);
      await sleep(60);
      const problems = [], places = [], notes = [], waited = [];
      let before = null;   // the layer before, and where its card showed
      for (const n of order(dir)) {
        const to = centre(n);
        await glide(cdp, from, to, 250);
        from = to;
        const now = await js(`__vpHero.state(${n})`);
        const marks = (await js("__vpHero.progress()")).marks.split(",");
        // a name opens as the mouse arrives, with no card yet; one that lies between the card before
        // and that card's own label (past it) waits while the mouse heads for that card, and opens
        // with its card once the mouse has rested on it (hero.js's REST, 200ms)
        if (now.active === String(n) && marks.includes(String(n)) && now.place === "none") { /* opened on arrival */ }
        else if (before && before.place === "past" && now.active === String(before.n)) {
          // hero.js opens it REST ms after the mouse stopped heading for the card. A busy page runs
          // that timer late (150ms and more, as seen with several browsers running), so wait for it,
          // up to the grace and 400ms more; a name that never opens still fails
          let later = null;
          for (const t0 = Date.now(); Date.now() - t0 < GRACE + 400;) {
            await sleep(50);
            later = await js(`__vpHero.state(${n})`);
            if (later.active === String(n) && later.place !== "none") break;
          }
          if (later.active === String(n) && later.place !== "none") waited.push(`T${n}`);
          else problems.push(`T${n}, past T${before.n}'s card: once the mouse stopped, data-hv-active=${later.active || "none"}, card ${later.place}`);
        } else {
          problems.push(`T${n} on arrival: data-hv-active=${now.active || "none"}, ${marks.includes(String(n)) ? "checked" : "not checked"}, card ${now.place === "none" ? "not shown" : "shown " + now.place}`);
        }
        await sleep(400);
        const s = await js(`__vpHero.state(${n})`);
        const b = s.card && s.card.box;
        places.push(`T${n} ${s.place}`);
        before = { n, place: s.place };
        if (s.active !== String(n) || !s.card || !s.card.shown || s.card.clip !== "none") { problems.push(`T${n}'s card did not show after a rest (${s.place})`); continue; }
        const next = n + (dir === "down" ? -1 : 1);
        const o = s.others.find((x) => x.name === "L" + next);
        if (o && (o.covered || meets(b, o.box))) problems.push(`T${n}'s card (${s.place}, ${Math.round(b.top)} to ${Math.round(b.bottom)}) covers T${next}`);
        if (meets(b, s.examples)) problems.push(`T${n}'s card (${s.place}, ${Math.round(b.top)} to ${Math.round(b.bottom)}) lies over its own label's examples`);
        if (meets(b, s.pause) || meets(b, s.person) || meets(b, s.intro)) problems.push(`T${n}'s card covers the pause control, the person's label or the intro`);
        if (b.bottom > s.hi + 0.5) notes.push(`T${n}'s card runs ${Math.round(b.bottom - s.hi)}px past the room's bottom to keep T${next} clear`);
      }
      const p = await js("__vpHero.progress()");
      report(at, problems.length === 0 && p.checked === "7",
        `a sweep ${dir} the names with a rest on each: each layer opens and is checked as the mouse arrives, with no card until it rests${waited.length ? `, or, past the card before, once the mouse has rested on its name (${waited.join(", ")})` : ""}, then a card clear of the next label and of its own label's examples (${places.join(", ")})${problems.length ? ": " + problems.join("; ") : ""}`);
      if (notes.length) note(at, notes.join("; "));
    }
    // A rest on the first name only, the mouse coming onto it along the column or from the gap beside
    // the labels: its card shows clear of its own examples and of the next label (on the way into the
    // column from the side, the way to the neighbour not checked yet), and the next name, once the
    // mouse goes on to it and stops, opens and is checked
    for (const [dir, how] of [["down", "along"], ["up", "along"], ["down", "side"], ["up", "side"]]) {
      const col = await begin();
      if (!col) return;
      const n = order(dir)[0], next = order(dir)[1], r = col.rows[7 - n], y = r.hy;
      const start = how === "side" ? [col.gap, y] : [col.x, dir === "down" ? Math.round(r.top - 25) : Math.round(r.bottom + 25)];
      await mouseTo(cdp, start);
      await sleep(60);
      await glide(cdp, start, [col.x, y], 250);
      await sleep(400);
      const s = await js(`__vpHero.state(${n})`);
      const o = s.others.find((x) => x.name === "L" + next);
      const own = s.place !== "none" && !!s.card && meets(s.card.box, s.examples);
      const hides = s.place !== "none" && !!o && (o.covered || meets(s.card.box, o.box));
      const speed = await glide(cdp, [col.x, y], [col.x, col.rows[7 - next].hy], 250);
      await sleep(GRACE + 150);
      const e = await js(`__vpHero.state(${next})`), p = await js("__vpHero.progress()");
      report(at, s.place !== "none" && !own && !hides && e.active === String(next) && p.marks.split(",").includes(String(next)),
        `onto T${n} ${how === "side" ? "from the gap beside the labels" : "along the column"}, a rest (its card shown ${s.place}, ${own ? "over" : "clear of"} its own label's examples and ${hides ? "over" : "clear of"} T${next}), then on at ${speed}px/s to T${next}'s name, where the mouse stops: T${next} opens and is checked (data-hv-active=${e.active || "none"}, card ${e.place})`);
    }
    // A card past the next label: after a rest on T7's name (T1's going up) whose card opens past T6
    // (T2), a path straight on from the name into the card's stories link at about 250px/s keeps T7
    // open, T6's name between them waiting while the mouse heads for the card, and the link is under
    // the mouse at the end; and a path that stops on T6's name opens T6 once the mouse stops there
    for (const dir of ["down", "up"]) {
      const n = order(dir)[0], next = order(dir)[1];
      for (const path of ["straight", "stop"]) {
        const col = await begin();
        if (!col) return;
        const r = col.rows[7 - n], label = [col.x, r.hy];
        const start = [col.x, dir === "down" ? Math.round(r.top - 25) : Math.round(r.bottom + 25)];
        await mouseTo(cdp, start);
        await sleep(60);
        await glide(cdp, start, label, 250);
        await sleep(400);
        const s = await js(`__vpHero.state(${n})`);
        if (s.place !== "past") { note(at, `T${n}'s card opens ${s.place} after a sweep ${dir} to it, so no card lies past the next label here`); break; }
        await js("__vpHero.record()");
        if (path === "stop") {
          await glide(cdp, label, [col.x, col.rows[7 - next].hy], 250);
          await sleep(60);
          const held = (await js(`__vpHero.state(${next})`)).active;
          await sleep(GRACE + 150);
          const e = await js(`__vpHero.state(${next})`);
          report(at, e.active === String(next) && e.place !== "none",
            `from T${n}'s name, its card past T${next}, the mouse that goes on to T${next}'s name and stops there opens T${next} with its card once it has rested there (data-hv-active ${held || "none"} on arrival, then ${e.active || "none"}, card ${e.place})`);
          continue;
        }
        const link = await js(`__vpHero.centre('a.hc-count', ${n})`);
        if (!link) { note(at, `T${n}'s card has no stories link`); continue; }
        const speed = await glide(cdp, label, link, 250);
        await sleep(150);
        const log = await js("window.__vpLog.join(' ')"), end = await js(`__vpHero.state(${n})`), under = await js(`__vpHero.hit(${link[0]}, ${link[1]})`);
        report(at, end.active === String(n) && log.split(" ").filter(Boolean).every((v) => v === String(n)) && under === `a.hc-count@${n}`,
          `from T${n}'s name a straight path at ${speed}px/s across T${next}'s name into its card past T${next} keeps T${n} open (data-hv-active ${log || "unchanged"}) and reaches its stories link (under the mouse: ${under})`);
      }
    }
  };

  // From 45em, the way from a name onto its card: on a fresh page for each layer, the mouse comes onto
  // the name and rests until the card shows, then goes straight towards the card's stories link at
  // about 250px/s, stopping 150ms halfway (under the grace), and on into the link: the layer stays
  // open all the way, across whatever lies between (its own examples, the gap, a name that waits), the
  // link is under the mouse, and a click on it follows it to the layer's view of Latest
  const paths = async (at, file, w, h, dpr = 1) => {
    const outside = [4, h - 10], problems = [], places = [], skipped = [];
    for (let n = 7; n >= 1; n--) {
      await open(cdp, file, w, h, false, false, false, dpr);
      if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the paths into the cards");
      await js("__vpHero.view()");
      await mouseTo(cdp, outside);
      await sleep(100);
      await js(`__vpHero.reachRow(${n})`);
      const name = await js(`__vpHero.centre('.hero-layer-link', ${n})`);
      await mouseTo(cdp, name);
      await sleep(400);
      const s = await js(`__vpHero.state(${n})`);
      if (s.active !== String(n) || s.place === "none") { problems.push(`T${n}: no card after a rest on its name (data-hv-active=${s.active || "none"}, ${s.place})`); continue; }
      const link = await js(`__vpHero.centre('a.hc-count', ${n})`);
      if (!link) { skipped.push(`T${n} (no stories link)`); continue; }
      if (!(await js(`__vpHero.seen(${link[0]}, ${link[1]})`))) { skipped.push(`T${n} (its card's link lies outside the window, ${s.place})`); continue; }
      places.push(`T${n} ${s.place}`);
      await js("__vpHero.record()");
      const mid = [Math.round((name[0] + link[0]) / 2), Math.round((name[1] + link[1]) / 2)];
      let speed = await glide(cdp, name, mid, 250);
      await sleep(150);
      speed = Math.min(speed, await glide(cdp, mid, link, 250));
      await sleep(100);
      const log = await js("window.__vpLog.join(' ')"), end = await js(`__vpHero.state(${n})`), under = await js(`__vpHero.hit(${link[0]}, ${link[1]})`);
      const went = navigation(cdp, 1500);
      await clickAt(cdp, link);
      const url = await went;
      if (!(end.active === String(n) && log.split(" ").filter(Boolean).every((v) => v === String(n)) && under === `a.hc-count@${n}` && !!url && url.endsWith(`latest/index.html#t${n}`))) {
        problems.push(`T${n} (card ${s.place}, ${speed}px/s): data-hv-active ${log || "unchanged"}, then ${end.active || "none"}; under the mouse ${under}; the click went to ${short(url)}`);
      }
    }
    report(at, problems.length === 0 && places.length > 0, `from each name, after a rest, a straight path at about 250px/s into its card's stories link, with a 150ms stop halfway, keeps the layer open all the way and a click on the link follows it to the layer's view of Latest (cards ${places.join(", ") || "none"})${problems.length ? ": " + problems.join("; ") : ""}`);
    if (skipped.length) note(at, `paths into the cards skipped: ${skipped.join(", ")}`);
  };

  // From 45em, the completion: once the seventh layer is checked your moment plays and, within
  // FINALE ms, the data moves, whatever stays where it was. Six layers are checked first by pointing
  // at their plates, T7 to T2; then T1: by its plate, the mouse left there or then moved to an empty
  // part of the stage or to the person; by its label, the mouse left there; or by focus on its name
  // (Tab from the element before it). On a touch screen: by a tap on its chevron after taps on the
  // other six, or by "Check all layers" clicked (by script, which moves no focus, as a tap in Safari
  // does not) while T3's card is open from a tap on its plate. Each time the page records, from the
  // seventh check, your moment (data-hv-cheer) and data-motion running within FINALE ms, and then
  // the data packets drawn and moving, the scene marking no layer, and the card that was open still
  // open beside them (with focus, focus still on the name), or, where the mouse moved off its plate,
  // closed once the grace ran out. Then a layer pointed at again holds the loop while it is open,
  // and leaving the stage lets the loop run again
  const FINALE = 2000;
  const finale = async (at, file, w, h, dpr = 1, touch = false) => {
    const outside = [4, h - 10], where = `${at} finale${touch ? " touch" : ""}`;
    // from the page's record: the seventh check's time, how long after it the loop ran, whether
    // your moment played then, and how long ago the check was
    const timing = async () => {
      const { log, now } = await js("__vpHero.watched()");
      const seven = log.find((e) => e.name === "data-hv-checked" && e.value === "7");
      if (!seven) return null;
      const before = log.filter((e) => e.name === "data-motion" && e.t <= seven.t).pop();
      const run = before && before.value === "running" ? seven
        : log.find((e) => e.name === "data-motion" && e.value === "running" && e.t >= seven.t);
      const cheer = log.some((e) => e.name === "data-hv-cheer" && e.value === "move" && Math.abs(e.t - seven.t) <= 100);
      return { ran: run ? Math.round(run.t - seven.t) : null, cheer, since: Math.round(now - seven.t) };
    };
    // the data packets move: some packet shown in two readings 300ms apart and moved between them
    const moving = async () => {
      const a = await js("__vpHero.packets()");
      await sleep(300);
      const b = await js("__vpHero.packets()");
      return a.some((p, i) => p.o > 0.5 && b[i].o > 0.5 && Math.abs(p.x - b[i].x) + Math.abs(p.y - b[i].y) > 0.5);
    };
    const begin = async () => {
      await open(cdp, file, w, h, false, false, touch, dpr);
      if (!(await js(HERO_KIT))) { report(where, false, "no hero figure for the completion"); return false; }
      await js("__vpHero.view()");
      if (!touch) { await mouseTo(cdp, outside); await sleep(150); }
      return js("__vpHero.watch()");
    };
    // the mouse onto plates T7 to T2 in turn, 60ms apart, so that no card shows on the way
    const pointSix = async () => {
      for (let n = 7; n >= 2; n--) {
        if (!(await js(`__vpHero.plateShown(${n})`))) { await mouseTo(cdp, outside); await sleep(400); await js(`__vpHero.plateInView(${n})`); }
        await mouseTo(cdp, await js(`__vpHero.plate(${n})`));
        await sleep(60);
      }
    };
    // plate 1 in view (off the stage first, so that no scroll moves a plate under a resting mouse)
    const plateOne = async () => {
      if (!(await js("__vpHero.plateShown(1)"))) { await mouseTo(cdp, outside); await sleep(400); await js("__vpHero.plateInView(1)"); }
      return js("__vpHero.plate(1)");
    };
    // 2.3s after the seventh check, the verdict on it: made by HOW, with layer N's card open, or, when
    // STAYS is false, closed, since the mouse has left its plate and the card
    const verdict = async (how, n, more = null, stays = true) => {
      await sleep(2300);
      const t = await timing();
      const p = await js("__vpHero.progress()"), y = await js("__vpHero.you()"), s = await js(`__vpHero.state(${n})`);
      const moves = await moving();
      const open = s.rows === String(n) && s.place !== "none" && !!s.card && s.card.shown && s.card.clip === "none";
      const ok = !!t && t.cheer && t.ran !== null && t.ran <= FINALE && p.motion === "running" && p.animated && !p.active
        && y.packets && y.plays === "running" && moves && open === stays && (!more || more.ok);
      report(where, ok, !t ? `the seventh check by ${how} did not come (data-hv-checked ${p.checked})`
        : `the seventh check by ${how}: your moment ${t.cheer ? "plays" : "does not play"}, the loop runs ${t.ran === null ? "not at all" : `${t.ran}ms after it`} (within ${FINALE}ms; data-motion=${p.motion}, data-hv-active=${p.active || "none"} ${t.since}ms after it), the data packets are ${y.packets ? "drawn" : "hidden"} and ${moves ? "move" : "do not move"} (${y.plays}), and T${n}'s card ${open ? "stays open" : `is closed (${s.place})`}${stays ? "" : ", as the mouse has left its plate and the card"}${more ? more.text : ""}`);
      return ok;
    };
    if (!touch) {
      for (const leave of ["plate", "stage", "person"]) {
        if (!(await begin())) return;
        await pointSix();
        await mouseTo(cdp, await plateOne());
        await sleep(80);
        if (leave === "plate") {
          await verdict("plate 1, the mouse left there", 1);
          continue;
        }
        const to = leave === "stage" ? await js("__vpHero.empty()") : (await js("__vpHero.you()")).hit;
        if (!to || to[1] > h - 8) { note(where, `no point on ${leave === "stage" ? "an empty part of the stage" : "the person"} in view beside plate 1; skipped`); continue; }
        await mouseTo(cdp, to);
        await verdict(`plate 1, the mouse then left on ${leave === "stage" ? "an empty part of the stage" : "the person"}`, 1, null, false);
        if (leave !== "stage") continue;
        // a layer pointed at after that holds the loop while it is open, and leaving lets it run
        if (!(await js("__vpHero.plateShown(4)"))) { note(where, "plate 4 is out of view; the next inspection is not tested"); continue; }
        await mouseTo(cdp, await js("__vpHero.plate(4)"));
        await sleep(250);
        const s = await js("__vpHero.state(4)"), y = await js("__vpHero.you()");
        report(where, s.active === "4" && s.motion === "suspended" && !y.packets,
          `then the mouse on plate 4 holds the loop while T4 is open (data-hv-active=${s.active || "none"}, data-motion=${s.motion}, the data packets ${y.packets ? "drawn" : "hidden"})`);
        await mouseTo(cdp, outside);
        await sleep(700);
        const p = await js("__vpHero.progress()");
        report(where, p.motion === "running" && !p.active, `and leaving the stage lets it run again (data-motion=${p.motion}, data-hv-active=${p.active || "none"})`);
      }
      // by T1's label, coming onto it from plate 2, the mouse left there. On a short window, such as
      // 720 x 450, T2's card, which shows once the mouse rests on plate 2, is fitted over T1's label;
      // the mouse then leaves the stage first, so that the card closes, as a reader's would
      if (await begin()) {
        await pointSix();
        let label = await js("__vpHero.at('.hero-layer-link', 1, true)");
        if (await js("__vpHero.row(1).classList.contains('is-covered')")) {
          note(where, "T2's card lies over T1's label here, so the mouse leaves the stage before it goes to the label");
          await mouseTo(cdp, outside);
          await sleep(400);
          label = await js("__vpHero.at('.hero-layer-link', 1, true)");
        }
        await mouseTo(cdp, label);
        await verdict("T1's label, the mouse left there", 1);
      }
      // by focus on T1's name: Tab from the element before it, the mouse off the stage
      if (await begin()) {
        await pointSix();
        await mouseTo(cdp, outside);
        await sleep(400);
        const from = await js("__vpHero.beforeName(1)");
        await sleep(200);
        await press(cdp, "Tab");
        const focus = async () => (await js("__vpHero.focused()")).focus;
        const first = await focus();
        await verdict(`focus on T1's name (Tab from ${from || "nothing"})`, 1);
        const last = await focus();
        report(where, first === "a.hero-layer-link@1" && last === first, `focus comes to T1's name (${first}) and stays there while the data moves (${last})`);
      }
    } else {
      // a tap on each chevron, T7 to T2, each card closed by a tap outside the figure (an open card
      // may lie over the next chevron), then on T1's
      if (await begin()) {
        for (let n = 7; n >= 1; n--) {
          await tapAt(cdp, await js(`__vpHero.reach('.hero-more', ${n})`));
          if (n === 1) break;
          await sleep(150);
          await settle(cdp);
          await tapAt(cdp, outside);
          await sleep(250);
        }
        await verdict("a tap on T1's chevron, after taps on the other six", 1);
      }
      // "Check all layers" while T3's card is open from a tap on its plate
      if (await begin()) {
        if (!(await js("__vpHero.plateShown(3)"))) await js("__vpHero.plateInView(3)");
        await tapAt(cdp, await js("__vpHero.plate(3)"));
        await sleep(150);
        await settle(cdp);
        const opened = (await js("__vpHero.state(3)")).active;
        await js("(document.querySelector('.hero-all').click(), true)");
        await verdict(`"Check all layers" with T3's card open from a tap (data-hv-active was ${opened || "none"})`, 3);
      }
    }
  };

  // The gray depends on hero.js having set the figure up. On a normal load, its load event held back
  // about a second by an image that never arrives (so that frames are drawn before it), you are gray
  // in every frame from the first, before the load event and after (data-hv-wait, then
  // data-hv-checked 0), and the scene's description gains its sentences on the gray and the data. With
  // hero.js blocked (it fails to load) or made to throw at its first line, you are in full colour once
  // the page has loaded: the guard has removed data-hv-wait, there is no data-hv-checked, and the
  // description says only what the still scene shows
  const guard = async (at, file, w) => {
    const h = w < 768 ? 844 : 900;
    const { identifier } = await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: GRAY_SAMPLER });
    await cdp.send("Fetch.enable", { patterns: [{ urlPattern: "*vp-hold.invalid*" }] });
    const held = cdp.on((m) => {
      if (m.method === "Fetch.requestPaused") setTimeout(() => cdp.send("Fetch.failRequest", { requestId: m.params.requestId, errorReason: "Failed" }).catch(() => {}), 1000);
    });
    try {
      await open(cdp, file, w, h, false, false);
      await sleep(200);
    } finally {
      held();
      await cdp.send("Fetch.disable");
      await cdp.send("Page.removeScriptToEvaluateOnNewDocument", { identifier });
    }
    if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the guard");
    const samples = await js("window.__vpGray || []");
    const early = samples.filter((x) => !x.loaded), colour = samples.filter((x) => !/grayscale\(1\)/.test(x.filter));
    let d = await js("__vpHero.desc()");
    report(at, early.length > 5 && colour.length === 0 && d.wait && d.checked === "0" && d.gray === 1,
      `a normal load: you are gray from the first frame (${samples.length} frames sampled, ${early.length} before the load event, ${colour.length} in colour), with data-hv-wait and data-hv-checked ${d.checked}`);
    report(at, !!d.live && d.text.endsWith(d.live) && d.text.length > d.live.length, "with hero.js running, the description adds the sentences on the gray and the data");
    const base = d.text.slice(0, d.text.length - d.live.length);
    await cdp.send("Network.enable");
    await cdp.send("Network.setBlockedURLs", { urls: ["*hero.js*"] });
    try {
      await open(cdp, file, w, h, false, false);
      await js(HERO_KIT);
      d = await js("__vpHero.desc()");
    } finally { await cdp.send("Network.setBlockedURLs", { urls: [] }); }
    report(at, !d.wait && d.checked === null && !d.enhanced && d.gray === 0 && d.text === base,
      `hero.js failing to load: you are in full colour after the load (grayscale ${d.gray}, data-hv-wait ${d.wait}), and the description says only what the still scene shows (${d.text === base})`);
    const thrown = await cdp.send("Page.addScriptToEvaluateOnNewDocument", { source: HERO_THROWS });
    try {
      await open(cdp, file, w, h, false, false);
      await js(HERO_KIT);
      d = await js("__vpHero.desc()");
    } finally { await cdp.send("Page.removeScriptToEvaluateOnNewDocument", { identifier: thrown.identifier }); }
    report(at, !d.wait && d.checked === null && !d.enhanced && d.gray === 0 && d.text === base,
      `hero.js throwing before it sets the figure up: you are in full colour after the load (grayscale ${d.gray}, data-hv-wait ${d.wait}), and the description says only what the still scene shows (${d.text === base})`);
  };

  // From 45em on a touch screen: the touch hint, chevrons in the rows' heads, taps and a swipe
  const touch = async (at, file, w) => {
    const h = 900, where = `${at} touch`;
    await open(cdp, file, w, h, false, false, true);
    if (!(await js(HERO_KIT))) return report(where, false, "no hero figure");
    await js("__vpHero.view()");
    const k = await js("__vpHero.parts()");
    const t = await js("__vpHero.hints()");
    report(where, k.hint && t.lines.length === 1 && t.lines[0] === "touch/todo", `the hint gives the touch line (${t.lines.join(", ") || "none"})`);
    report(where, k.chevrons.length === 7 && k.chevrons.every((c) => c.shown && c.head), `seven chevrons in the rows' heads (${k.chevrons.map((c) => c.w + "x" + c.h).join(" ")})`);
    // a tap may scroll the page to the whole card, so each tap finds its target where it is now
    await tapAt(cdp, await js("__vpHero.at('.hero-more', 2, false)"));
    await sleep(150);
    await settle(cdp);
    let s = await js("__vpHero.state(2)");
    report(where, s.active === "2" && s.rows === "2" && s.expanded === "2" && !!s.card && s.card.shown && s.card.clip === "none",
      `a tap on T2's chevron opens its card (data-hv-active=${s.active || "none"}, aria-expanded on ${s.expanded || "none"})`);
    await tapAt(cdp, await js("__vpHero.at('.hero-more', 2, false)"));
    await sleep(300);
    s = await js("__vpHero.state(2)");
    report(where, !s.active && !s.rows && !s.expanded, `a second tap closes it (data-hv-active=${s.active || "none"})`);
    if (!(await js("__vpHero.plateShown(3)"))) await js("__vpHero.plateInView(3)");
    await tapAt(cdp, await js("__vpHero.plate(3)"));
    await sleep(150);
    await settle(cdp);
    s = await js("__vpHero.state(3)");
    report(where, s.active === "3" && s.expanded === "3", `a tap on plate 3 opens T3 (data-hv-active=${s.active || "none"})`);
    // a swipe that starts outside the figure scrolls the page to the rest of the card and keeps it
    const from = [Math.max(4, Math.round(s.figure.left / 2)), h - 80], y0 = s.y;
    await cdp.send("Input.synthesizeScrollGesture", { x: from[0], y: from[1], yDistance: -200, speed: 800, gestureSourceType: "touch" });
    await sleep(400);
    s = await js("__vpHero.state(3)");
    report(where, s.active === "3" && s.y > y0, `a swipe that starts outside the figure scrolls the page (scrollY ${y0} to ${s.y}) and keeps T3 open (data-hv-active=${s.active || "none"})`);
    await tapAt(cdp, [4, h - 10]);
    await sleep(300);
    s = await js("__vpHero.state(3)");
    report(where, !s.active && !s.rows, `a tap outside the figure closes it (data-hv-active=${s.active || "none"})`);
  };

  // Touch tablets (and a phone on its side): a card that a tap opens ends wholly in view, by
  // the least scroll, the page's own or, under reduced motion, instant
  const tablet = async (at, file, w, h) => {
    const where = `${at} touch`, outside = [4, h - 10];
    // whether the card that a tap on TARGET opened is in view, and was brought there by the
    // least scroll (from Y0)
    const look = (s, n, target, y0, reduced) => {
      const lo = s.hb + 8, hi = s.ih - 8, b = s.card;
      if (s.open !== String(n) || !s.shown || !b) return `${target} ${n}: T${n}'s card did not open (open row ${s.open || "none"}, data-hv-active=${s.active || "none"})`;
      const fits = b.height <= hi - lo + 0.5, moved = Math.abs(s.y - y0) >= 1;
      const at = `T${n}'s card (${s.place}, ${Math.round(b.height)}px) after a tap on ${target} ${n} at ${Math.round(b.top)} to ${Math.round(b.bottom)}`;
      if (fits && (b.top < lo - 1.5 || b.bottom > hi + 1.5)) return `${at}, outside ${Math.round(lo)} to ${hi}`;
      if (!fits && Math.abs(b.top - lo) > 1.5) return `${at}, taller than ${Math.round(lo)} to ${hi} but not starting just under the header`;
      if (moved && fits && Math.abs(b.top - lo) > 1.5 && Math.abs(b.bottom - hi) > 1.5) return `${at}: the page scrolled ${Math.round(s.y - y0)}px, more than it needed`;
      const want = reduced ? "instant" : "auto";
      if (moved && (s.scrolls.length !== 1 || s.scrolls[0] !== want)) return `${at}: the page scrolled as ${s.scrolls.join(", ") || "nothing asked"}, not ${want}`;
      if (!moved && s.scrolls.length) return `${at}: a card in view asked for a scroll (${s.scrolls.join(", ")})`;
      return "";
    };
    // TAP opens layer N: a chevron or a plate, found where it is once the page is ready
    const tapOpen = async (n, target, ready, reduced = false) => {
      await ready();
      const point = target === "chevron" ? await js(`__vpHero.reach('.hero-more', ${n})`) : await js(`__vpHero.plate(${n})`);
      await js("__vpHero.spyScroll()");
      const y0 = await js("scrollY");
      await tapAt(cdp, point);
      if (reduced) await sleep(120);   // an instant scroll is done by the next frame
      else { await sleep(150); await settle(cdp); }
      const s = await js(`__vpHero.tapped(${n})`);
      await tapAt(cdp, outside);   // closes the card for the next tap
      await sleep(250);
      return { s, y0 };
    };
    const top = () => js("window.scrollTo({ top: 0, behavior: 'instant' }), true");
    const scene = () => js("__vpHero.view()");
    for (const reduced of [false, true]) {
      await open(cdp, file, w, h, false, reduced, true);
      if (!(await js(HERO_KIT))) return report(where, false, "no hero figure");
      const runs = reduced ? [["chevron", "the page as loaded", top]]
        : [["chevron", "the page as loaded", top], ["chevron", "the scene in view", scene], ["plate", "the scene in view", scene]];
      for (const [target, from, ready] of runs) {
        const problems = [], places = [];
        let scrolled = 0;
        for (let n = 7; n >= 1; n--) {
          // a plate must be in view to be tapped; a chevron is reached in tapOpen
          const steady = target === "plate"
            ? async () => { await ready(); if (!(await js(`__vpHero.plateShown(${n})`))) await js(`__vpHero.plateInView(${n})`); } : ready;
          const { s, y0 } = await tapOpen(n, target, steady, reduced);
          const bad = look(s, n, target, y0, reduced);
          if (bad) problems.push(bad);
          if (Math.abs(s.y - y0) >= 1) scrolled++;
          places.push(`T${n} ${s.place}${Math.abs(s.y - y0) >= 1 ? ` ${s.y - y0 > 0 ? "+" : ""}${Math.round(s.y - y0)}px` : ""}`);
        }
        report(where, problems.length === 0, `${reduced ? "reduced motion: " : ""}a tap on each ${target} from ${from} opens its card wholly between the header and the window's bottom, by the least ${reduced ? "instant " : ""}scroll (${scrolled} of 7 scrolled: ${places.join(", ")})${problems.length ? ": " + problems.join("; ") : ""}`);
      }
    }
  };

  // The legend's samples are drawn as the scene draws the chain, in light and dark, and in
  // CanvasText in forced colours; the words keep their ink
  const legend = async (at, file, w) => {
    const h = w < 768 ? 844 : 900;
    try {
      for (const mode of ["light", "dark", "forced colours"]) {
        if (mode === "forced colours") {
          await cdp.send("Emulation.setEmulatedMedia", { features: media(false, false, true) });
          await sleep(150);
        } else await open(cdp, file, w, h, mode === "dark", false);
        if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the legend");
        const g = await js("__vpHero.legend()");
        const samples = g.samples.map((s) => `${s.bind} ${[...new Set(s.strokes)].join("/") || "no path"} at ${s.opacity}`).join(", ");
        if (mode === "forced colours") {
          report(at, g.forced && g.samples.length > 0 && g.samples.every((s) => s.strokes.length > 0 && s.strokes.every((c) => c === g.canvasText) && s.opacity === "1"),
            `${mode}: the legend's samples are in CanvasText (${g.canvasText}) at opacity 1: ${samples}`);
        } else {
          const opacity = (s) => (s.bind === "missing" ? "0.6" : "1");
          report(at, !!g.chain && g.samples.length > 0 && g.samples.every((s) => s.strokes.length > 0 && s.strokes.every((c) => c === g.chain) && s.opacity === opacity(s)),
            `${mode}: the legend's samples are in the scene's chain indigo (${g.chain || "no chain"}), the missing run's at 0.6: ${samples}`);
          report(at, g.samples.every((s) => s.words === g.ink && s.status === g.ink), `${mode}: the legend's words stay in ink (${g.ink}): ${[...new Set(g.samples.flatMap((s) => [s.words, s.status]))].join(", ")}`);
        }
      }
    } finally { await cdp.send("Emulation.setEmulatedMedia", { features: media(false, false) }); }
  };

  // Behaviour that broke once (one width per page): the pause control under an open card, a
  // press on a card's text, slow paths from a plate into its card, and focus that the window
  // takes and gives back
  const regressions = async (at, file, w) => {
    const h = 900;
    // the pause control shows once every layer is checked: "Check all layers", clicked by script
    const checked = () => js("(document.querySelector('.hero-all').click(), new Promise(r => setTimeout(() => r(true), 100)))");
    // With each card open by the mouse on its label, the pointer goes on to the pause control
    // at about 500px/s and clicks it: the click pauses the animation and follows no link
    for (let n = 7; n >= 1; n--) {
      await open(cdp, file, w, h, false, false);
      await js(HERO_KIT);
      await checked();
      await mouseTo(cdp, [2, h - 2]);
      await sleep(100);
      const from = await js(`__vpHero.centre('.hero-layer-link', ${n})`), pause = await js("__vpHero.centre('[data-motion-toggle]')");
      await mouseTo(cdp, from);
      await sleep(300);
      const opened = (await js(`__vpHero.state(${n})`)).active;
      await glide(cdp, from, pause, 500);
      await sleep(100);
      const went = navigation(cdp, 900);
      await clickAt(cdp, pause);
      const url = await went;
      const s = url ? null : await js("__vpHero.state(0)");
      report(`${at} T${n}`, opened === String(n) && !url && s.motion === "paused",
        url ? `with T${n} open, a click on the pause control followed a link to ${short(url)}` : `with T${n} open (data-hv-active=${opened || "none"}), a click on the pause control pauses (data-motion=${s.motion})`);
    }
    // A press on the text of T4's card, opened from its label, follows the card to the layer on
    // the Stack page: also when the pause control, just clicked, holds focus
    for (const first of ["nothing", "the pause control"]) {
      await open(cdp, file, w, h, false, false);
      await js(HERO_KIT);
      await checked();
      // the pause control ignores clicks for 0.6s after it takes the place of "Check all layers"
      if (first !== "nothing") { await sleep(600); await clickAt(cdp, await js("__vpHero.centre('[data-motion-toggle]')")); await sleep(200); }
      const label = await js("__vpHero.centre('.hero-layer-link', 4)"), entry = [w - 8, label[1]];
      await mouseTo(cdp, entry);
      await sleep(300);
      await glide(cdp, entry, label, 500);
      await sleep(300);
      const claim = await js("__vpHero.centre('.hc-claim', 4)"), id = await js("__vpHero.row(4).dataset.layer");
      if (!claim) { report(`${at} T4`, false, `after a click on ${first}, T4's card did not open from its label`); continue; }
      await glide(cdp, label, claim, 500);
      await sleep(200);
      const went = navigation(cdp, 1500);
      await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: claim[0], y: claim[1], button: "left", buttons: 1, clickCount: 1 });
      await sleep(60);
      await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: claim[0], y: claim[1], button: "left", buttons: 0, clickCount: 1 });
      const url = await went;
      report(`${at} T4`, !!url && url.endsWith(`topics/index.html#layer-${id}`), `after a click on ${first}, a press on the card's text follows it to ${short(url)} (#layer-${id} on the Stack page)`);
    }
    // A straight path at about 130px/s from each plate to its card's stories link: the plates
    // it crosses do not take over, and the click follows the link
    for (let n = 7; n >= 1; n--) {
      await open(cdp, file, w, h, false, false);
      await js(HERO_KIT);
      await js("__vpHero.view()");
      await mouseTo(cdp, [3, h - 3]);
      await sleep(100);
      const from = await js(`__vpHero.plate(${n})`);
      await mouseTo(cdp, from);
      await sleep(400);
      const opened = (await js(`__vpHero.state(${n})`)).active;
      const to = await js(`__vpHero.centre('a.hc-count', ${n})`);
      if (!to) { note(`${at} T${n}`, "the card has no stories link"); continue; }
      await js("__vpHero.record()");
      const speed = await glide(cdp, from, to, 130);
      await sleep(150);
      const log = await js("window.__vpLog.join(' ')"), active = (await js(`__vpHero.state(${n})`)).active;
      const went = navigation(cdp, 1500);
      await clickAt(cdp, to);
      const url = await went;
      report(`${at} T${n}`, opened === String(n) && active === String(n) && log.split(" ").filter(Boolean).every((v) => v === String(n)) && !!url && url.endsWith(`latest/index.html#t${n}`),
        `a straight path at ${speed}px/s from plate ${n} to its stories link keeps T${n} open (data-hv-active ${opened || "none"}, then ${log || "unchanged"}), and the click follows the link to ${short(url)}`);
    }
    // Focus that the window takes and gives back (focusout, then focusin, both with no
    // relatedTarget) on a focused name leaves the page where the reader scrolled it
    await open(cdp, file, w, h, false, false);
    await js(HERO_KIT);
    await js("__vpHero.before()");
    await press(cdp, "Tab");
    await settle(cdp);
    await press(cdp, "Tab");
    await settle(cdp);
    const named = (await js("__vpHero.focused()")).focus;
    await cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x: 300, y: Math.round(h * 2 / 3), deltaX: 0, deltaY: 1400 });
    await sleep(1200);
    await settle(cdp);
    const y0 = await js("Math.round(scrollY)");
    await js("document.activeElement.dispatchEvent(new FocusEvent('focusout', { bubbles: true, relatedTarget: null })), true");
    await sleep(300);
    await js("document.activeElement.dispatchEvent(new FocusEvent('focusin', { bubbles: true, relatedTarget: null })), true");
    await sleep(600);
    const y1 = await js("Math.round(scrollY)");
    report(at, named === "a.hero-layer-link@7" && y0 > 0 && y1 === y0, `focus that the window takes and gives back on ${named} leaves the page where the reader scrolled it (scrollY ${y0} to ${y1})`);
  };

  // Below 45em: the chevrons open cards in the list (spec 8.3, item 5)
  const phone = async (at, file, w) => {
    await open(cdp, file, w, 844, false, false);
    if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the layer cards");
    const k = await js("__vpHero.parts()");
    report(at, k.enhanced && !k.hits, `hero.js ran (data-enhanced ${k.enhanced}); the plates stay inert (data-hv-hits ${k.hits})`);
    report(at, k.chevrons.length === 7 && k.chevrons.every((c) => c.shown && c.w >= 44 && c.h >= 44), `seven chevrons, at least 44x44 (${k.chevrons.map((c) => c.w + "x" + c.h).join(" ")})`);
    // the hint by input: a mouse in a narrow window clicks the arrows, a phone's finger taps them
    {
      const t = await js("__vpHero.hints()");
      report(at, t.lines.length === 1 && t.lines[0] === "click/todo", `with a mouse the hint gives the click line (${t.lines.join(", ") || "none"})`);
      await open(cdp, file, w, 844, false, false, true);
      await js(HERO_KIT);
      const u = await js("__vpHero.hints()");
      report(at, u.lines.length === 1 && u.lines[0] === "touch/todo", `on a touch screen the hint gives the touch line (${u.lines.join(", ") || "none"})`);
      await open(cdp, file, w, 844, false, false);
      if (!(await js(HERO_KIT))) return report(at, false, "no hero figure for the layer cards");
    }
    {
      const p = await js("__vpHero.progress()");
      // the button is the pause control's size: 36px tall with a fine pointer, 44px on touch screens
      const fits = !!p.allBox && p.allBox.left >= 0 && p.allBox.right <= w && p.allBox.height >= 35.5;
      report(at, p.shown && fits && p.overflow <= 0 && p.gray === 1, `the progress (${JSON.stringify(p.text)}) and "Check all layers" (${p.allBox ? Math.round(p.allBox.left) + " to " + Math.round(p.allBox.right) + ", " + Math.round(p.allBox.height) + "px tall" : "not shown"}) fit in ${w}px with no sideways scroll; you are gray (${p.gray})`);
    }
    // "Who checks" at rest: on the TEE rows, T1 and T2, where it says the reader's own device
    // checks, and on no other row until it opens
    const rest = await js("__vpHero.who()"), names = (rows) => rows.map((r) => "T" + r.n).join(", ") || "no row";
    report(at, names(rest.filter((r) => r.shown)) === "T2, T1" && names(rest.filter((r) => r.tee)) === "T2, T1",
      `"Who checks" shows at rest on ${names(rest.filter((r) => r.shown))}, the TEE rows (${names(rest.filter((r) => r.tee))}), only`);
    const whoOf = async (n) => (await js("__vpHero.who()")).find((r) => r.n === n);
    const click = async (n) => { await clickAt(cdp, await js(`__vpHero.at('.hero-more', ${n}, true)`)); await sleep(200); return js(`__vpHero.state(${n})`); };
    for (let n = 7; n >= 1; n--) {
      const where = `${at} T${n}`;
      let s = await click(n);
      const inside = !!s.card && s.card.box.top >= s.row.top - 1 && s.card.box.bottom <= s.row.bottom + 1;
      // the scene marks the row opened last, until T1, the last of the seven, completes the checks
      const mark = n === 1 ? "" : String(n);
      report(where, s.open === String(n) && s.expanded === String(n) && s.active === mark && s.card.shown && inside,
        `a click on the chevron opens the card in its row (aria-expanded on ${s.expanded || "none"}, data-hv-active=${s.active || "none"}${n === 1 ? ", none once every layer is checked" : ""})`);
      const opened = await whoOf(n);
      s = await click(n);
      const closed = await whoOf(n);
      report(where, !s.open && !s.expanded && !s.active && !s.card.shown, `a second click closes it (open rows: ${s.open || "none"})`);
      report(where, opened.open && opened.shown && !closed.open && closed.shown === (n <= 2),
        `"Who checks" shows while the row is open (${opened.shown ? "shown" : "hidden"}) and, closed, ${closed.shown ? "stays" : "goes"} (${n <= 2 ? "a TEE row keeps it" : "only the TEE rows keep it"})`);
    }
    {
      // opening each row checked its layer: every mark shows, you are in full colour and the loop may run
      const p = await js("__vpHero.progress()");
      report(at, p.checked === "7" && p.marks === "7,6,5,4,3,2,1" && p.animated && !p.all && !p.active,
        `a tap on each chevron checked every layer (marks on ${p.marks || "none"}, the progress ${JSON.stringify(p.text)}); the loop may run (data-animated ${p.animated}) and the scene marks no row`);
      const t = await js("__vpHero.hints()");
      report(at, t.lines.length === 1 && t.lines[0] === "click/done", `with every layer checked the hint gives the click line without the promise of colour (${t.lines.join(", ") || "none"})`);
    }
    await click(7);
    let s = await click(1);
    report(at, s.open === "7,1" && !s.active && s.overflow <= 0, `two rows open at once (${s.open}); with every layer checked the scene marks none of them (data-hv-active=${s.active || "none"}), so the loop runs; no sideways scroll (${s.overflow}px)`);
    await click(1);
    s = await click(7);
    report(at, !s.open && !s.active && s.overflow <= 0, `both close again; no sideways scroll (${s.overflow}px)`);
    // the person plays their moment for a click on phones too, and opens no row (after the moment
    // that the seventh row played, once the scene came into view, is over)
    await js("__vpHero.you(true)");
    await sleep(1900);
    const hit = (await js("__vpHero.you()")).hit;
    if (hit) {
      await clickAt(cdp, hit);
      await sleep(800);
      const y = await js("__vpHero.you()");
      report(at, y.cheer && !y.active && y.bubble === 1, `a click on the person plays their moment (data-hv-cheer ${y.cheer}, bubble ${y.bubble}) and opens no row (data-hv-active=${y.active || "none"})`);
    } else report(at, false, "no hit area on the person");
  };

  // The intro beside the figure (spec 8.3, item 6)
  const band = async (name, file) => {
    for (const bw of [...new Set([1184, 1280, 1440, 1600, 1920, ...widths.filter((x) => x >= 1184)])].sort((a, b) => a - b)) {
      await open(cdp, file, bw, 900, false, false);
      const b = await js(`(() => { const band = document.querySelector('.home-hero'), box = el => el && el.getBoundingClientRect().toJSON();
        return { side: band ? getComputedStyle(band).getPropertyValue('--hero-band').trim() : '', intro: box(document.querySelector('.home-intro')), fig: box(document.querySelector('.hero-visual')) }; })()`);
      report(`${name} @${bw}`, b.side === "side" && !!b.intro && !!b.fig && !meets(b.intro, b.fig) && b.fig.left >= b.intro.right,
        `the intro (to ${b.intro ? Math.round(b.intro.right) : "?"}px) stands beside the figure (from ${b.fig ? Math.round(b.fig.left) : "?"}px), --hero-band: ${b.side || "unset"}`);
    }
  };

  // The vendor marks' names (static/hero.js tips()). hover() brings the mouse onto the Ith named mark
  // from where it rests: pointing at a mark opens, switches and checks no layer, so the open layer
  // and the layers checked are as they were before the mouse came (WAS), and the name waits; after a
  // rest the tooltip reads the mark's aria-label, at least 13px, wholly inside the window and below
  // the sticky header, clear of the mark and of an open card, which lies over none of its own label's
  // marks, and the page does not scroll sideways; an open card does not name the marks to a mouse.
  // tips() runs it for every named mark twice: each on a fresh page (from 45em), nothing open and
  // nothing checked, the mouse coming from off the stage, as a reader's first move might; then all on
  // one page, the mouse coming to each mark from its layer's name, where it rested until the card
  // showed (from 45em): beside the card, which the layer's own marks keep open, the name shows clear
  // of it and stays; on the layer's name again the tooltip goes. Every name must show. Then a pass
  // along the row with the most marks at
  // about 250px/s shows no name. No mark takes a tab stop
  const tips = async (at, file, w, h, dpr = 1) => {
    const where = `${at} tips`, outside = [4, h - 10], wide = w >= 720;
    const hover = async (i, problems, sides, was) => {
      const { n, name } = (await js("__vpHero.marks()"))[i];
      await mouseTo(cdp, await js(`__vpHero.mark(${i})`));
      const now = await js("__vpHero.tip()");
      if (now.active !== was.active || now.checked !== was.checked) {
        problems.push(`${name}: the mouse on the mark changed the open layer (${was.active || "none"} to ${now.active || "none"}) or the layers checked (${was.checked || "none"} to ${now.checked || "none"})`);
      }
      if (now.shown) problems.push(`${name}: the name shows before the rest`);
      await sleep(was.active ? 200 : 350);   // beside an open card: before the grace closes it
      const t = await js("__vpHero.tip()"), all = await js("__vpHero.marks()"), m = all[i].box;
      const own = all.filter((x) => x.n === n).map((x) => x.box);
      if (t.card && own.some((b) => meets(t.card, b))) problems.push(`${name}: T${t.active}'s card (${t.place}) lies over T${n}'s marks`);
      if (t.checked !== was.checked) problems.push(`${name}: a rest on the mark checked ${t.checked || "none"} (${was.checked || "none"} before)`);
      if (!was.active && t.active) problems.push(`${name}: a rest on the mark opened T${t.active}`);
      if (!t.shown || t.text !== name) {
        problems.push(`${name}: the tooltip ${t.shown ? `reads ${JSON.stringify(t.text)}` : "does not show"}${t.card ? ` (T${t.active}'s card ${t.place})` : ""}`);
      } else {
        const b = t.box;
        if (b.left < 0.5 || b.right > t.vw - 0.5 || b.top < t.hb - 0.5 || b.bottom > t.ih - 0.5) {
          problems.push(`${name}: the tooltip (${Math.round(b.left)},${Math.round(b.top)} to ${Math.round(b.right)},${Math.round(b.bottom)}) leaves the window under the header (0,${Math.round(t.hb)} to ${t.vw},${t.ih})`);
        }
        if (meets(b, m)) problems.push(`${name}: the tooltip covers its mark`);
        if (t.card && meets(b, t.card)) problems.push(`${name}: the tooltip lies over T${t.active}'s card`);
        if (t.size < 12.95) problems.push(`${name}: the tooltip is ${t.size}px`);
        if (t.overflow > 0) problems.push(`${name}: the page scrolls sideways by ${t.overflow}px`);
        sides[b.bottom <= m.top + 0.5 ? "above" : "below"]++;
      }
      // a mouse can rest on the marks, so the open card does not name them
      if (t.card && (await js(`__vpHero.names(${t.active})`)).shown) problems.push(`${name}: T${t.active}'s card shows the examples' names to a mouse`);
      return { n, name, card: t.card ? t.place : "none" };
    };
    const told = (problems) => (problems.length ? ": " + problems.slice(0, 6).join("; ") + (problems.length > 6 ? `; and ${problems.length - 6} more` : "") : "");
    await open(cdp, file, w, h, false, false, false, dpr);
    if (!(await js(HERO_KIT))) return report(where, false, "no hero figure");
    const marks = await js("__vpHero.marks()");
    if (!marks.length) return report(where, false, "no named vendor marks in the labels");
    // each mark on a fresh page: nothing open, nothing checked, and the mouse on the mark changes neither
    if (wide) {
      const problems = [], sides = { above: 0, below: 0 };
      for (let i = 0; i < marks.length; i++) {
        await open(cdp, file, w, h, false, false, false, dpr);
        if (!(await js(HERO_KIT))) { problems.push("no hero figure"); break; }
        await mouseTo(cdp, outside);
        await sleep(60);
        await hover(i, problems, sides, { active: "", checked: "" });
      }
      report(where, problems.length === 0,
        `on a fresh page, the mouse on each of the ${marks.length} named marks opens and checks no layer, and after a rest shows the mark's name inside the window, clear of the mark (${sides.above} above, ${sides.below} below)${told(problems)}`);
      await open(cdp, file, w, h, false, false, false, dpr);
      await js(HERO_KIT);
    }
    // every mark on one page, from 45em each from its layer's name after a rest there: the card shows,
    // and the mark's name shows beside it, clear of it, then stays once the card has closed
    {
      const problems = [], sides = { above: 0, below: 0 }, cards = {};
      for (let i = 0; i < marks.length; i++) {
        const { n, name } = marks[i];
        await mouseTo(cdp, outside);
        await sleep(GRACE + 150);   // the card before closes, and no name follows on at once
        let was = { active: "", checked: (await js("__vpHero.tip()")).checked };
        if (wide) {
          await js(`__vpHero.mark(${i})`);   // the mark, and so its row, in view
          await mouseTo(cdp, await js(`__vpHero.centre('.hero-layer-link', ${n})`));
          await sleep(350);
          const s = await js("__vpHero.tip()");
          if (s.active !== String(n) || !s.card) problems.push(`${name}: a rest on T${n}'s name showed no card (data-hv-active=${s.active || "none"})`);
          was = { active: s.active, checked: s.checked };
        }
        const r = await hover(i, problems, sides, was);
        (cards[`T${r.n}`] = cards[`T${r.n}`] || new Set()).add(r.card);
        if (wide) {
          // the layer's own marks hold its card (the way to a card below its label crosses them)
          await sleep(GRACE);
          const t = await js("__vpHero.tip()");
          if (t.active !== String(n)) problems.push(`${name}: T${n}'s card closed with the mouse on one of its own marks (data-hv-active=${t.active || "none"})`);
          if (!t.shown || t.text !== name) problems.push(`${name}: the name ${t.shown ? `reads ${JSON.stringify(t.text)}` : "goes"} while the card stays open`);
          if (t.shown && t.card && meets(t.box, t.card)) problems.push(`${name}: the name lies over T${n}'s card`);
        }
        const label = await js(`__vpHero.centre('.hero-layer-link', ${n})`);
        if (label) {
          await mouseTo(cdp, label);
          await sleep(60);
          if ((await js("__vpHero.tip()")).shown) problems.push(`${name}: the name stays once the mouse is on T${n}'s name`);
        }
      }
      const tabbable = (await js("__vpHero.tip()")).tabbable;
      report(where, problems.length === 0 && tabbable === 0,
        `on one page, the mouse on each of the ${marks.length} named marks in turn${wide ? ", coming from its layer's name and the card that a rest there showed," : ""} switches nothing and, after a rest, shows the mark's name inside the window, clear of the mark${wide ? ` and of the card (${Object.entries(cards).map(([k, v]) => `${k} ${[...v].join("/")}`).join(", ")}), which stays open while the mouse rests on its own marks, the name still showing` : ""} (${sides.above} above, ${sides.below} below), and the name goes on the layer's name; no mark takes a tab stop (${tabbable})${told(problems)}`);
    }
    // a pass along the row with the most marks, at about 250px/s, shows no name
    {
      const counts = {};
      for (const m of marks) counts[m.n] = (counts[m.n] || 0) + 1;
      const n = Number(Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0]);
      const first = marks.findIndex((m) => m.n === n);
      await mouseTo(cdp, outside);
      await sleep(GRACE + 150);
      await js(`__vpHero.mark(${first})`);
      const row = (await js("__vpHero.marks()")).filter((m) => m.n === n).map((m) => m.box);
      const y = Math.round((row[0].top + row[0].bottom) / 2), from = [Math.round(row[0].left - 12), y], to = [Math.round(row[row.length - 1].right + 12), y];
      await mouseTo(cdp, from);
      await sleep(60);
      await js("__vpHero.watchTip()");
      const speed = await glide(cdp, from, to, 250);
      await sleep(30);
      const shownOnPass = await js("window.__vpTipShown");
      report(where, !shownOnPass, `a pass along T${n}'s ${row.length} marks at ${speed}px/s shows no name (${shownOnPass ? "one showed" : "none showed"})`);
    }
  };

  // The marks' names on a touch screen, in a window W x H (a touch tablet from 45em, a phone below it):
  // a tap on each named mark shows its name in the tooltip, inside the window, or, where the row's
  // chevron, a 44px target, lies over that part of the mark (on touch tablets), opens the row's card,
  // whose Examples line names it; a tap outside the figure hides the name and closes the card. So every
  // name is reachable by touch. Then the card that a tap on each row's arrow opens names every example
  // in that row's label
  const tipsTouch = async (at, file, w, h) => {
    const where = `${at} tips touch`, outside = [4, h - 10];
    await open(cdp, file, w, h, false, false, true);
    if (!(await js(HERO_KIT))) return report(where, false, "no hero figure");
    const marks = await js("__vpHero.marks()");
    if (!marks.length) return report(where, false, "no named vendor marks in the labels");
    const problems = [], inCard = [];
    let tapped = 0;
    for (let i = 0; i < marks.length; i++) {
      const { n, name } = marks[i];
      await tapAt(cdp, await js(`__vpHero.mark(${i})`));
      await sleep(200);
      await settle(cdp);   // a tap that opened a card scrolls it into view
      const t = await js("__vpHero.tip()");
      if (t.shown && t.text === name) {
        const b = t.box;
        if (b.left < 0.5 || b.right > t.vw - 0.5 || b.top < t.hb - 0.5 || b.bottom > t.ih - 0.5) problems.push(`${name}: the tooltip leaves the window`);
        else tapped++;
      } else {
        const s = await js(`__vpHero.state(${n})`), names = await js(`__vpHero.names(${n})`);
        const open = w >= 720 ? s.active === String(n) && s.place !== "none" : s.open.split(",").includes(String(n));
        if (open && names.shown && names.text.includes(name)) inCard.push(name);
        else problems.push(`${name}: a tap ${t.shown ? `shows ${JSON.stringify(t.text)}` : "shows no name"} and ${open ? `T${n}'s card names ${JSON.stringify(names.shown ? names.text : "nothing")}` : "opens no card"}`);
      }
      await tapAt(cdp, outside);
      await sleep(250);
      const after = await js("__vpHero.tip()");
      if (after.shown) problems.push(`${name}: a tap outside the figure leaves the name shown`);
      if (w >= 720 && after.active) problems.push(`${name}: a tap outside the figure leaves T${after.active}'s card open`);
    }
    report(`${where} @${w}x${h}`, problems.length === 0,
      `each of the ${marks.length} named marks gives its name to a tap: ${tapped} in the tooltip, ${inCard.length} in the card that the row's arrow over that part of the mark opens${inCard.length ? ` (${inCard.join(", ")})` : ""}; a tap outside the figure hides it${problems.length ? ": " + problems.slice(0, 6).join("; ") : ""}`);
    // the card that a tap on each row's arrow opens names every example in the label
    const rows = [...new Set(marks.map((m) => m.n))], missing = [];
    for (const n of rows) {
      await tapAt(cdp, await js(`__vpHero.reach('.hero-more', ${n})`));
      await sleep(200);
      await settle(cdp);
      const names = await js(`__vpHero.names(${n})`), want = marks.filter((m) => m.n === n).map((m) => m.name);
      const lost = want.filter((x) => !(names.shown && names.text.includes(x)));
      if (lost.length) missing.push(`T${n}: ${names.shown ? lost.join(", ") : "no names shown"}`);
      await tapAt(cdp, await js(`__vpHero.reach('.hero-more', ${n})`));   // closes it again
      await sleep(250);
      await settle(cdp);
    }
    report(`${where} @${w}x${h}`, missing.length === 0,
      `the card that a tap on each row's arrow opens names every example in its label (${rows.map((n) => "T" + n).join(", ")})${missing.length ? ": missing " + missing.join("; ") : ""}`);
  };

  // Without JavaScript (spec 8.3, item 8): no hover cards from 45em, open cards on phones
  const plain = async (at, file, w) => {
    const where = `${at} no-js`;
    await cdp.send("Emulation.setScriptExecutionDisabled", { value: true });
    try {
      await open(cdp, file, w, w < 768 ? 844 : 900, false, false);
      if (!(await js(HERO_KIT))) return report(where, false, "no hero figure");
      const p = await js("__vpHero.plain()");
      report(where, !p.progress.shown && !p.progress.all && !p.progress.marks && p.progress.gray === 0 && !p.progress.checked,
        `the progress and "Check all layers" stay hidden, no layer shows a mark, and you are in full colour (grayscale ${p.progress.gray})`);
      const s = await state();
      report(where, !s.caption && !!s.links && s.links.shown && !!s.tip && !s.tip.shown,
        "no caption, the links to the Stack page show, and the vendor marks' tooltip stays hidden");
      const d = await js("__vpHero.desc()");
      report(where, !!d.live && !d.text.includes(d.live.trim()) && !/\bgr[ae]y\b|灰/.test(d.text),
        "the scene's description says what the still scene shows, with no word of a gray");
      if (w >= 720) {
        report(where, !p.enhanced && p.cards.length === 7 && p.cards.every((c) => c.display === "none"), `the seven cards are not displayed (${p.cards.map((c) => c.display).join(",")})`);
        report(where, !p.hint && p.chevrons.every((c) => !c), "the hint and the chevrons stay hidden");
        report(where, p.links.length === 7 && p.links.every(Boolean), "the seven names link to their layers on the Stack page");
      } else {
        report(where, p.cards.length === 7 && p.cards.every((c) => c.display !== "none" && c.height > 50 && c.inRow), `the seven cards are open in their rows (${p.cards.map((c) => c.height).join(",")}px tall)`);
        report(where, p.who.length === 7 && p.who.every((r) => r.shown), `every row shows its "Who checks" (${p.who.filter((r) => r.shown).length} of ${p.who.length})`);
      }
    } finally { await cdp.send("Emulation.setScriptExecutionDisabled", { value: false }); }
  };

  try {
    // CHECK runs unless --only names others
    const step = async (check, at, run) => {
      if (only && !only.has(check)) return;
      try { await run(); } catch (e) { report(at, false, `stopped: ${e.message || e}`); }
    };
    const again = widths.find((w) => w >= 1184) ?? widths.find((w) => w >= 720);   // the width for the regressions
    for (const name of names) {
      const file = pageFile(site, pages, name);
      if (!file) { report(name, false, `${pages[name]} is not in this build`); continue; }
      for (const w of widths) {
        const at = `${name} @${w}`;
        await relaunch();
        await step("motion", at, () => heroAt(at, file, w));
        await step("legend", at, () => legend(at, file, w));
        await step("guard", at, () => guard(at, file, w));
        if (w >= 720) {
          await step("cards", at, () => cards(at, file, w, 900));
          await step("paths", at, () => paths(at, file, w, 900));
          await step("keys", at, () => keys(at, file, w, 900));
          await step("sweeps", at, () => sweeps(at, file, w, 900));
          await step("touch", at, () => touch(at, file, w));
          if (!only || only.has("finale")) {
            await relaunch();   // the completion is timed: a fresh browser runs its timers on time
            await step("finale", at, () => finale(at, file, w, 900));
            if (w === again) await step("finale", at, () => finale(at, file, w, 900, 1, true));   // and by touch, at one width
          }
          if (w === again && (!only || only.has("regressions"))) {
            await relaunch();
            await step("regressions", at, () => regressions(at, file, w));
          }
        } else {
          await step("phone", at, () => phone(at, file, w));
          await step("tips", at, () => tips(at, file, w, 844));   // the windows from 45em are --tipsizes
          await step("tips", at, () => tipsTouch(at, file, w, 844));
        }
        if (opt.nojs || (only && only.has("nojs"))) await step("nojs", at, () => plain(at, file, w));
      }
      for (const [w, h, dpr] of sizes) {
        const at = `${name} @${w}x${h}${dpr !== 1 ? `x${dpr}` : ""}`;
        await relaunch();
        await step("cards", at, () => cards(at, file, w, h, dpr));
        await step("paths", at, () => paths(at, file, w, h, dpr));
        await step("keys", at, () => keys(at, file, w, h, dpr));
        await step("sweeps", at, () => sweeps(at, file, w, h, dpr));
        if (!only || only.has("finale")) {
          await relaunch();
          await step("finale", at, () => finale(at, file, w, h, dpr));
        }
      }
      // the marks' names from 45em: the mouse in each --tipsizes window, and taps on a touch tablet
      if (widths.some((w) => w >= 720) && (!only || only.has("tips"))) {
        for (const [w, h] of tipSizes) {
          const at = `${name} @${w}x${h}`;
          await relaunch();
          await step("tips", at, () => tips(at, file, w, h));
        }
        await relaunch();
        await step("tips", name, () => tipsTouch(name, file, 1024, 768));
      }
      if (widths.some((w) => w >= 720) && (!only || only.has("tablets"))) {
        for (const [w, h] of tablets) {
          const at = `${name} @${w}x${h}`;
          await relaunch();
          await step("tablets", at, () => tablet(at, file, w, h));
        }
      }
      if (widths.some((w) => w >= 1184) && (!only || only.has("band"))) {
        await relaunch();
        await step("band", name, () => band(name, file));
      }
    }
  } finally { if (cdp) cdp.close(); }
  console.log(failures ? `hero: ${failures} of ${checks} checks failed` : `hero: all ${checks} checks passed`);
  if (failures) process.exitCode = 1;
}

async function evalCmd(site, opt) {
  const pages = pageMap(site, opt.article);
  const file = pageFile(site, pages, opt.page || "home");
  if (!file) throw new Error(`${pages[opt.page || "home"]} is not in this build`);
  const cdp = await launch();
  try {
    const w = Number(opt.width || 1440);
    await open(cdp, file, w, Number(opt.height || 900), !!opt.dark, !!opt.reduced);
    const v = await evaluate(cdp, opt.js);
    console.log(typeof v === "string" ? v : JSON.stringify(v, null, 1));
  } finally { cdp.close(); }
}

// node cdp.mjs zoom SITE OUT.png --page home --width 1440 --clip x,y,w,h [--scale 2] [--dark] [--forced] [--reduced] [--scroll Y]
async function zoom(site, out, opt) {
  const pages = pageMap(site, opt.article);
  const target = opt.file ? path.resolve(opt.file) : pageFile(site, pages, opt.page || "home");
  if (!target) throw new Error(`${pages[opt.page || "home"]} is not in this build`);
  const cdp = await launch();
  try {
    const w = Number(opt.width || 1440);
    const [x, y, cw, ch] = String(opt.clip || `0,0,${w},800`).split(",").map(Number);
    const scale = Number(opt.scale || 2);
    await cdp.send("Emulation.setDeviceMetricsOverride", { width: w, height: Number(opt.height || 1000), deviceScaleFactor: scale, mobile: w < 768 });
    await cdp.send("Emulation.setEmulatedMedia", { media: opt.print ? "print" : "", features: media(!!opt.dark, !!opt.reduced, !!opt.forced) });
    const loaded = cdp.once("Page.loadEventFired");
    await cdp.send("Page.navigate", { url: pathToFileURL(target).href + (opt.hash ? "#" + opt.hash : "") });
    await Promise.race([loaded, sleep(8000)]);
    await cdp.send("Runtime.evaluate", { expression: "document.fonts.ready.then(() => true)", awaitPromise: true });
    await sleep(300);
    if (opt.focus) {
      // Focus the element by keyboard so :focus-visible applies: focus the one before it, then press Tab.
      await cdp.send("Runtime.evaluate", { expression: `(() => { const els=[...document.querySelectorAll('a[href], button, input, select, [tabindex]:not([tabindex="-1"])')].filter(e => e.offsetParent !== null && e.tabIndex >= 0); const t=document.querySelector(${JSON.stringify(String(opt.focus))}); const i=els.indexOf(t); if (i > 0) els[i-1].focus(); else document.body.focus(); })()` });
      await cdp.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
      await cdp.send("Input.dispatchKeyEvent", { type: "keyUp", key: "Tab", code: "Tab", windowsVirtualKeyCode: 9 });
      await sleep(200);
    }
    if (opt.hover) {
      // Rest the real mouse on the first element that matches, as a reader would, so that its hover
      // states show, such as the hero's tooltip over a vendor mark, or the card of a layer's name. The
      // capture then keeps to the window (the page is not scrolled): one beyond it would resize the
      // page under the resting pointer, and the tooltip and the card would go
      const at = await evaluate(cdp, `(() => { const el = document.querySelector(${JSON.stringify(String(opt.hover))}); if (!el) return null;
        const r = el.getBoundingClientRect(); return [Math.round(r.left + r.width / 2), Math.round(r.top + r.height / 2)]; })()`);
      if (!at) throw new Error(`nothing matches --hover ${opt.hover}`);
      await mouseTo(cdp, at);
      await sleep(500);
    }
    const shot = await cdp.send("Page.captureScreenshot", { format: "png", clip: { x, y, width: cw, height: ch, scale: 1 }, captureBeyondViewport: !opt.hover });
    writeFileSync(out, Buffer.from(shot.data, "base64"));
    console.log(out);
  } finally { cdp.close(); }
}

const { cmd, pos, opt } = args();
const main = {
  shots: () => shots(path.resolve(pos[0]), path.resolve(pos[1]), opt),
  check: () => check(path.resolve(pos[0]), opt),
  hero: () => hero(path.resolve(pos[0]), opt),
  eval: () => evalCmd(path.resolve(pos[0]), opt),
  zoom: () => zoom(path.resolve(pos[0]), path.resolve(pos[1]), opt),
}[cmd];
if (!main || !pos[0]) { console.error("usage: node cdp.mjs shots|check|hero|eval|zoom SITE [OUT] [options]; see the comment at the top of this file"); process.exit(2); }
main().catch((e) => { console.error(e.message || e); process.exit(1); });
