/* The home hero. The scene is illustrative; motion runs locally without live
   system data. progress() counts the layers the reader has checked: you, the
   person in the scene, are drawn in gray at first and gain colour with each
   layer checked, and the loop (the data that passes through every layer,
   then the pulse up the chain of evidence) waits until all seven are; then
   it runs within moments, also beside a layer still open (free()).
   motion() runs that loop and its pause control; layers() opens the layers
   and the cards that the build puts in each label row, and a layer that opens
   counts as checked. From 45em a mouse or pen opens a layer as it points at
   its plate or at its label's name area (the head line: "T5 Agents"), and
   only there: the examples under a name, its vendor marks and names, open,
   switch, close and check nothing. The layer lights and counts at once, and
   its card shows once the pointer settles on it, so a sweep down or up the
   names or the plates checks each layer in turn with no card in its way, and
   a card then opens where the next label of that sweep stays clear, when it
   can, and never over its own label's examples (place()). The card stays
   while the pointer is on its name, its plate or the card, and while the
   pointer heads for the card: a name or a plate on that way waits instead of
   opening, until the pointer rests on it or turns away. A short while after
   the pointer has left them all, the card closes. Focus on a name opens its
   card at once; touch screens tap a plate or a row's chevron, and the page
   scrolls to the whole card (bring()). Below 45em the chevrons open cards in
   the list, several at a time, and the plates are inert. you() plays the
   person's moment for a click or a tap on them, and once all seven layers
   are checked. tips() shows a vendor mark's brand name in a tooltip over the
   mark that a mouse or pen rests on, or that a tap touches, beside the layers
   and never in their way. The state lives in the DOM:
   data-hv-active (the open layer while the scene marks it, which holds the
   loop), data-hv-hits, data-hv-checked (how many
   layers are checked, 0 to 7), data-hv-cheer (the person's moment) and
   data-hv-hop (their hop, which plays whole once T1 or T2 opens) on the
   figure, which the scene reads, and data-hv-instant while the open card shows
   without its entrance (it replaced an open card, or a tap opened it), which
   the stylesheet reads (21.3); .is-active (from 45em) or .is-open (phones) on
   the rows, and .is-checked on each row checked; on the open row from 45em,
   once its card shows, data-open-place (up, down, fit or past) and, for fit and
   past, an inline top on its card; .is-covered on the other rows, the legend
   and the hint where the shown card overlaps them; .is-active on the leaders
   and aria-expanded on the chevrons. The figure ships with data-hv-wait, under
   which the scene grays you from the first paint where scripts run; this
   script shows what it adds (data-enhanced, the chevrons, the hint, the count
   and "Check all layers") and writes data-hv-checked only at the end, once the
   figure is set up, and the page's inline guard removes data-hv-wait at the
   window's load when data-hv-checked is still missing, because this script
   failed to load or threw first, so you are never left gray, and a figure
   whose set-up threw shows what a page without this script shows. Without
   this script the cards' text is still in the page, hidden from 45em (the
   name links are described by the claim and "Who checks") and open on
   phones, and you are in full colour in a still scene, as the scene's
   description says; once the figure is set up, the description
   gains the sentences on the gray and the data (its data-hv-live). The script
   writes an attribute or a text only when its value changes
   (toggleAttribute, removeAttribute and classList.toggle with a force change
   nothing then): a rewrite of the same value still makes the browser restyle
   the figure or lay it out. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const narrow = window.matchMedia('(max-width: 44.999em)');   // the stylesheet's phone layout
  document.querySelectorAll('[data-verification-visual]').forEach(fig => {
    // done: every layer is checked, so the loop may run; show: what the set-up reveals at its end;
    // enhanced: layers() has set up the labels and the cards; free: what progress() calls once
    // every layer is checked, which takes the layer open then and returns what lets the loop run
    // beside it (layers() sets it; without the labels no layer is ever open)
    const state = { done: false, show: [], enhanced: false, free: () => () => {} };
    const cheer = you(fig);
    const loop = motion(fig, state);
    layers(fig, loop.update, progress(fig, state, loop, cheer), state);
    tips(fig);
    loop.update();
    // Set up, all at once and only now, so that a throw on the way leaves the figure as without
    // this script (the page's guard then gives you your colour back): data-enhanced, which shows
    // the chevrons' list and the cards' layout, the chevrons, the hint, the count and "Check all
    // layers"; then the count, which the scene's gray follows and which tells the guard that this
    // script runs, and the description, which now says that you start in gray. A figure without
    // the count runs its loop at once (state.done) and keeps you in colour
    if (state.enhanced) fig.setAttribute('data-enhanced', '');
    state.show.forEach(el => { el.hidden = false; });
    if (!state.done) {
      if (!fig.hasAttribute('data-hv-checked')) fig.setAttribute('data-hv-checked', '0');
      const desc = fig.querySelector('desc[data-hv-live]');
      if (desc) desc.textContent += desc.getAttribute('data-hv-live');
    }
  });

  /* You, the person in the scene: a click or a tap on them plays a short moment in which
     they are protected (data-hv-cheer on the figure for CHEER ms, which the scene draws:
     "still" when the reader has paused the motion or under reduced motion, else "move", so
     the scene need not watch data-motion, which changes with every card). It is for a
     pointer only, a hidden delight: the scene is an image (role="img"), so a control in it
     would be lost to screen readers, and the same moment plays for every reader, keyboard
     included, who opens T1 or T2, the layers where a TEE gives direct evidence, and once
     all seven layers are checked. One moment at a time: a click while it plays does
     nothing. Returns the function that plays it */
  function you(fig) {
    const CHEER = 1800;
    let t = 0;
    const cheer = () => {
      if (t) return;
      fig.setAttribute('data-hv-cheer', fig.dataset.motion === 'paused' || fig.dataset.motion === 'static' ? 'still' : 'move');
      t = setTimeout(() => { t = 0; fig.removeAttribute('data-hv-cheer'); }, CHEER);
    };
    const hit = fig.querySelector('.hv-you-hit');
    if (hit) hit.addEventListener('click', () => cheer());
    return cheer;
  }

  /* The reader's progress. A layer counts as checked once it opens, as a pointer points at
     it, focus reaches it or a tap opens it (on phones, its row), and stays checked for the
     page view: its row is .is-checked, which shows a check mark by its name. The figure
     counts the layers checked in data-hv-checked (0 is written once the figure is set up),
     from which the scene draws you in gray, with colour coming back a step with each layer,
     and the hint swaps its line for one without the promise of colour once all seven are.
     The status on your label's name line says how many (it and the button show once the
     figure is set up, with what layers() adds),
     politely (role="status"), from its data-progress ({n} is the count) and data-done;
     "Check all layers", in the pause control's place, checks every layer at once, and the
     status says so once. A green completion sentence joins the person's description,
     hidden from screen readers because the status already announces the completion.
     When all seven are checked you are in full colour, your moment
     plays (when the scene is next in view, so that a reader on a phone who checked the last
     row in the list still sees it), the loop starts and the button gives its place, and its
     focus, back to the pause control (to the status under reduced motion, where the control
     stays hidden). A layer open at that moment (the one the last check opened, or a card open
     when the button is clicked) holds the loop only while your moment plays a while: then
     layers() lets the loop run beside it (state.free), so the data moves even if the pointer, the
     focus or the finger stays where it is. Returns the function that checks a row */
  function progress(fig, state, loop, cheer) {
    const rows = [...fig.querySelectorAll('.hero-layer[data-n]')];
    const status = fig.querySelector('.hero-progress'), all = fig.querySelector('.hero-all');
    const complete = fig.querySelector('.hero-complete');
    const pause = fig.querySelector('[data-motion-toggle]');
    if (!rows.length || !status) {
      state.done = true;   // a figure without the status runs its loop at once
      return () => {};
    }
    const seen = new Set();
    const say = () => {
      const text = seen.size < rows.length ? status.dataset.progress.replace('{n}', String(seen.size)) : status.dataset.done;
      if (status.textContent !== text) status.textContent = text;
    };
    const mark = row => {
      if (!row || seen.has(row)) return false;
      seen.add(row);
      row.classList.toggle('is-checked', true);
      fig.setAttribute('data-hv-checked', String(seen.size));
      return true;
    };
    const finish = () => {
      say();
      if (seen.size < rows.length || state.done) return;
      state.done = true;
      if (complete) complete.hidden = false;
      // on a phone the scene stops marking the row opened last (layers()), which would hold the
      // loop and hide the data while the cards stay open in the list; from 45em the layer open now
      // lets the loop run beside it once your moment has played a while (free, from layers())
      if (narrow.matches) fig.removeAttribute('data-hv-active');
      const free = state.free();
      loop.update();   // shows the pause control unless motion is reduced
      if (all) {
        if (document.activeElement === all) (pause && !pause.hidden ? pause : status).focus();
        all.hidden = true;
        loop.settle();   // the control now stands where the button was
      }
      loop.whenShown(() => { cheer(); free(); });
    };
    state.show.push(status);   // shown once the figure is set up
    if (all) {
      state.show.push(all);
      all.addEventListener('click', () => { rows.forEach(mark); finish(); });
    }
    return row => { if (mark(row)) finish(); };
  }

  /* The loop runs once every layer is checked (state.done) and while the scene is in
     view, pauses with the control, and is suspended while the scene is off-screen (on
     phones the list below it can fill the window on its own), in a hidden tab and while a
     card is open; under reduced motion the scene is a still frame. The pause control shows
     only while the loop may run. Returns { update, whenShown, settle }: update brings
     data-motion up to date, and whenShown runs a function now if the scene is in view, else
     the next time it comes into view. update runs on every card switch, so it changes only
     what differs: data-motion restyles the whole figure, and the label's text lays it out.
     settle marks the moment the control takes the place of "Check all layers": for SETTLE ms
     it ignores clicks, so the second click or tap of a double click on the button, which
     lands on the control, does not pause the loop the first one started. A held Enter, whose
     repeats would toggle the control on and off, toggles it once */
  function motion(fig, state) {
    const toggle = fig.querySelector('[data-motion-toggle]');
    const label = fig.querySelector('[data-motion-label]');
    if (!toggle || !label) return { update: () => {}, whenShown: fn => fn(), settle: () => {} };
    const SETTLE = 600;
    let paused = false;
    let visible = true;
    let settled = -Infinity;   // when the control took the place of "Check all layers"
    const waiting = [];   // what runs the next time the scene comes into view
    const update = () => {
      const on = state.done && !reduced.matches;
      if (toggle.hidden !== !on) toggle.hidden = !on;
      const text = paused ? toggle.dataset.labelPlay : toggle.dataset.labelPause;
      if (label.textContent !== text) label.textContent = text;
      if (toggle.getAttribute('aria-label') !== text) toggle.setAttribute('aria-label', text);
      fig.toggleAttribute('data-animated', on);
      // a layer that the scene marks open holds the loop, which would move beside the text being
      // read; the layer open when every layer is checked stops being marked once your moment has
      // played a while (free() in layers()), so that the completion shows
      const held = fig.hasAttribute('data-hv-active');
      const mode = reduced.matches ? 'static' : paused ? 'paused' : document.hidden || !visible || held ? 'suspended' : 'running';
      if (fig.dataset.motion !== mode) fig.dataset.motion = mode;
    };
    toggle.addEventListener('click', () => {
      if (performance.now() - settled < SETTLE) return;
      paused = !paused;
      update();
    });
    toggle.addEventListener('keydown', e => { if (e.repeat && e.key === 'Enter') e.preventDefault(); });
    reduced.addEventListener('change', update);
    document.addEventListener('visibilitychange', update);
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(entries => {
        visible = entries[entries.length - 1].isIntersecting;
        if (visible) waiting.splice(0).forEach(fn => fn());
        update();
      });
      observer.observe(fig.querySelector('.hero-art') || fig);
    }
    return { update, whenShown: fn => { if (visible) fn(); else waiting.push(fn); }, settle: () => { settled = performance.now(); } };
  }

  function layers(fig, update, check, state) {
    const list = fig.querySelector('.hero-layers'), stage = fig.querySelector('.hero-stage');
    if (!list || !stage) return;
    const rows = [...list.querySelectorAll('.hero-layer[data-n]')], leaders = [...fig.querySelectorAll('.hero-leader')];
    const band = fig.closest('.home-hero'), header = document.querySelector('.site-header');
    // the controls at the figure's top right: the pause control, and "Check all layers" in its
    // place until every layer is checked; the room for a card starts below the one shown
    const controls = [fig.querySelector('[data-motion-toggle]'), fig.querySelector('.hero-all')].filter(Boolean);
    // besides the other rows, what an open card can partly cover: the legend and the hint
    const covers = [fig.querySelector('.hero-chain'), fig.querySelector('.hero-hint')].filter(Boolean);
    const plates = new Map();   // each plate's hit area, to its row
    // each label's name area, its head (the icon, the code and name, the TEE label and the tick, under
    // the name link's target, which spans the head line), to its row
    const heads = new Map(rows.map(row => [row.querySelector('.hero-layer-head'), row]));
    // active: the row whose card is open from 45em.
    // dismissed: the row that Esc closed; focus that stays in that row, or that the window gives
    // back to it (blurred), does not reopen it.
    // closeT: the wait (GRACE) after which the open card closes, once a mouse or pen has left its
    // layer's name, its plate and the card.
    // keyed: the last input was a key press, so a focus came from the keyboard; a tap or a click
    // that focuses a name or a chevron opens nothing through focus
    let active = null, dismissed = null, blurred = null, closeT = 0, lastPointer = 'mouse', keyed = true;
    // how: the input that opened the active layer, 'mouse' (or a pen), 'touch' or 'key', which
    // decides when its card shows (a mouse's once the pointer settles) and where place() may put
    // it, then and on resize.
    // travel: the way the pointer came onto the active layer's name along the column, 'down' or
    // 'up' (null from a plate, from the side, or for another input), which tells place() which
    // label a sweep reaches next.
    // pressedIn: the last pointer press was in the figure (a keydown clears it).
    // placed: where place() put the open card, as its top below its row's top (dy) and its
    // height (h), so that bring() and reveal() measure where it ends, not where its entrance
    // has slid it so far (a tapped card has no entrance)
    let how = 'mouse', travel = null, pressedIn = false, placed = null;
    // where the pointer last moved. A card that closes (Esc) or changes (focus, a tap) uncovers
    // the labels under it, and the browser then sends pointerenter to a pointer that has not
    // moved: only a pointer that moves opens a card
    let px = NaN, py = NaN;
    // A mouse or pen over the stage (steer()): trail, its positions over the last TRAIL ms and
    // one before; over, what it last moved over; under, the row whose trigger it is on, its plate
    // or its name area (null off them); frame, the animation frame that reads them; pending, the
    // row of a trigger that waits (while the pointer heads for the open card, or is back over the
    // edge of a plate it has just crossed), with pendingHit, whether that trigger is a plate,
    // pendingDir, the way the pointer came onto it, aimed, when it last began to wait, and restT,
    // the rest that ends the wait; opened, when the open card showed; left, the layer that the
    // pointer's last switch on the plates closed, with lx and ly, where the pointer was then;
    // stillT, the timer that shows the pointed layer's card once the pointer stops; onLabel, the
    // row whose name the pointer came onto last (null once it has come onto a plate since)
    const trail = [];
    let over = null, under = null, frame = 0, pending = null, pendingHit = false, pendingDir = null;
    let aimed = 0, restT = 0, opened = 0, left = null, lx = 0, ly = 0, stillT = 0, onLabel = null;
    const openOrder = [];   // phones: the open rows, the most recently opened last
    // The person's hop plays whole once a TEE layer (T1, T2) opens from another or from none:
    // data-hv-hop, which the scene reads, stays on the figure for HOP ms, the hop's length, so a
    // pointer that leaves T1 or T2 mid-hop does not drop them to the ground, and one that comes
    // back does not restart it
    const HOP = 700, tee = r => !!r && (r.dataset.n === '1' || r.dataset.n === '2');
    let hopT = 0;
    const hop = () => {
      if (hopT) return;
      fig.setAttribute('data-hv-hop', '');
      hopT = setTimeout(() => { hopT = 0; fig.removeAttribute('data-hv-hop'); }, HOP);
    };
    // Once every layer is checked the data moves, also beside a layer still open. The layer open at
    // that moment (the one the last check opened by a pointer, focus or a tap, or a card open when
    // "Check all layers" is clicked) holds the loop only for the first FREE ms of your moment, while
    // its hop, sparkles and first ripple play; then the scene stops marking it (data-hv-active goes:
    // the plates come back whole and the data and the pulse show) and the loop runs, as on phones,
    // while its row and card stay open until they close as any card does, so the card being read
    // is not taken from under the pointer or the focus. A switch to another layer, a close or a
    // reset cancels it first, and a layer opened after it holds the loop as before; under reduced
    // motion there is no loop to show, so the layer stays marked. free(), which progress() calls as
    // state.free once every layer is checked, takes the layer open then (freeing) and returns what
    // starts the wait, which progress() runs as your moment plays, once the scene is in view
    const FREE = 1200;
    let freeing = null, freeT = 0;
    const unfree = () => {
      freeing = null;
      if (freeT) { clearTimeout(freeT); freeT = 0; }
    };
    const free = () => {
      freeing = active;
      return () => {
        if (!freeing || freeT || reduced.matches) return;
        freeT = setTimeout(() => {
          freeT = 0;
          if (!freeing || freeing !== active) return;
          freeing = null;
          fig.removeAttribute('data-hv-active');
          update();
        }, FREE);
      };
    };
    state.free = free;
    const card = row => row.querySelector('.hero-card');
    const more = row => row.querySelector('.hero-more');
    const rowOf = el => rows.find(row => row.contains(el)) || null;
    // the chevrons and the hint show, with data-enhanced, once the figure is set up
    state.show.push(...fig.querySelectorAll('.hero-more, .hero-hint'));

    // From 45em: open ROW (null closes the open layer), with its leader and the scene, and check
    // it. BY is the input that opens it (how). HOVER: a mouse or pen moved onto its plate or
    // name, so its card shows only once the pointer settles there (settle()); a click, focus or
    // a tap shows it at once. DIR is the way the pointer came onto its name (travel). A card
    // that replaces an open one, or that a tap opens, is marked data-hv-instant before it is
    // shown, so it shows at once (21.3); one that the keyboard opens from rest, or that shows
    // once the pointer settles, slides in. Only a card that closes, or a layer that a pointer
    // opens, uncovers everything (its card is not shown yet): a switch that shows its card at
    // once changes only the labels that differ
    const mark = (row, on) => {
      row.classList.toggle('is-active', on);
      const leader = leaders[rows.indexOf(row)];
      if (leader) leader.classList.toggle('is-active', on);
      if (!on) {
        more(row).setAttribute('aria-expanded', 'false');
        row.removeAttribute('data-open-place');
        card(row).style.removeProperty('top');
      }
    };
    // ROW's card shows, placed for BY (and, for a mouse, the way the pointer came); SETTLED: it
    // shows because the pointer settled, with nothing shown since the layer opened, so it slides in
    const show = (row, by, settled = false) => {
      if (settled) fig.removeAttribute('data-hv-instant');
      more(row).setAttribute('aria-expanded', 'true');
      if (by === 'mouse') travel = way(row);
      place(row, by, by === 'mouse' ? travel : null);
      opened = performance.now();
      if (by === 'touch') bring(row);
    };
    const set = (row, by = how, hover = false, dir = null) => {
      keep();
      wait(null);
      if (row === active) {
        // a pointer that comes onto the open layer again before its card shows brings the way it came;
        // a click, a tap or focus shows a layer that a pointer opened, and a card that the mouse
        // fitted over its label's head moves off the name when keyboard focus comes in
        if (row && hover && !row.dataset.openPlace) travel = dir;
        if (row && !hover && (!row.dataset.openPlace || (by === 'key' && row.dataset.openPlace === 'fit'))) {
          how = by;
          show(row, by);
        }
        return;
      }
      how = by;
      travel = dir;
      const from = active;
      if (from) mark(from, false);
      active = row;
      left = null;   // a switch on the plates sets it again (go())
      unfree();   // a layer that waited to let the loop run (free()) waits no more
      if (row) {
        fig.toggleAttribute('data-hv-instant', !!from || by === 'touch');
        mark(row, true);
        if (hover) {
          [...rows, ...covers].forEach(el => el.classList.toggle('is-covered', false));
          placed = null;
        } else show(row, by);
        if (tee(row) && !tee(from)) hop();
        fig.dataset.hvActive = row.dataset.n;
        check(row);   // it is open: the layer is checked
      } else {
        fig.removeAttribute('data-hv-active');
        fig.removeAttribute('data-hv-instant');
        [...rows, ...covers].forEach(el => el.classList.toggle('is-covered', false));
        placed = null;
      }
      update();
    };
    // A mouse or pen that moved onto ROW's name or plate opens it, unless keyboard focus is in
    // another card, which would then hide it; DIR is the way it came onto the name
    const pointed = e => e.pointerType !== 'touch' && !narrow.matches && (e.clientX !== px || e.clientY !== py);
    const point = (row, dir = null) => {
      const held = keyed ? rowOf(document.activeElement) : null;
      if (!held || held === row || !card(held).contains(document.activeElement)) set(row, 'mouse', true, dir);
    };
    // The way the pointer came onto a name, where it is now: 'down' or 'up' when it moved mostly
    // along the column over the last TRAIL ms, else null (from a plate, or from the side). It is
    // measured from the first position in that time, not from where the pointer rested before it,
    // which may lie anywhere
    const travelOf = () => {
      const now = performance.now(), a = trail.find(p => now - p.t <= TRAIL) || trail[trail.length - 1];
      if (!a) return null;
      const dx = px - a.x, dy = py - a.y;
      return Math.abs(dy) > Math.abs(dx) && Math.abs(dy) >= 2 ? (dy > 0 ? 'down' : 'up') : null;
    };
    // The way on from ROW, a label that the pointer came onto from the side (or from its plate): the
    // way to its neighbour that is not checked yet, where the reader goes next to check it, so the
    // card keeps that neighbour clear (T7 and T1 have one neighbour each); null when both neighbours,
    // or neither, are left to check, and the card opens as any other
    const toward = row => {
      const i = rows.indexOf(row), open = r => !!r && !r.classList.contains('is-checked');
      const up = open(rows[i - 1]), down = open(rows[i + 1]);
      return down && !up ? 'down' : up && !down ? 'up' : null;
    };
    // The way on from ROW for its card: the way the pointer came along the column while a label lies
    // ahead that way; else, when the pointer came onto ROW's name last, toward(); else none
    const way = row => {
      const i = rows.indexOf(row);
      if ((travel === 'down' && rows[i + 1]) || (travel === 'up' && rows[i - 1])) return travel;
      return onLabel === row ? toward(row) : null;
    };
    // Where a card opens, from 45em (data-open-place): below its label in the stage's upper half
    // and above it in the lower half (data-place), or on the other side when only that one has
    // room. The room runs from the top of the band when the intro is beside the figure, else of
    // the scene, and from below the control at the figure's top right (the pause control, or
    // "Check all layers" in its place), down to the stage's bottom; for a mouse or a
    // touch it also keeps below the sticky header and above the window's bottom. A card never
    // lies over its own label's examples, so every mark there stays in view and keeps its name
    // for a pointer that rests on it (tips()). With room on neither side, a mouse card is fitted
    // over its label's head (fit), whose code and name its own head repeats, ending at the head's
    // bottom, just above the examples, when it fits between the room's top and there; else it
    // opens below its label and runs past the room's bottom, when its head and first lines (4rem)
    // show; else above. A keyboard card opens below, where the page can always scroll to it, so
    // a focused name is never covered; a touch card opens on the side with more room (below
    // when, above, the page could not scroll its top clear of the header), and bring() then
    // scrolls the page to all of it.
    // A mouse card for a label whose name the pointer reached along the column (DIR, 'down' or
    // 'up') first keeps clear of the label that the sweep reaches next, CLEAR px away, more than the
    // 8px within which a label counts as covered: on the side the pointer came from when the card
    // fits there; else, going down, over its own label's head (fit); else past the next label,
    // beyond it (past); else, on a short window, with at least its head and first lines in view,
    // running past the room's bottom: just below the next label going down (past), below its own
    // label going up (down); and only when none of these can, as above. So a reader who rests on a
    // name to read its card can go on to the next, which is in view: it opens as the pointer reaches
    // it, or, when it lies between the card and its own label (past), as the pointer rests on it or
    // turns away from the card (aim()), and the labels the card lay over come back. A pointer that
    // goes straight on from the name to a card past the next label keeps the card: the name between
    // waits while the pointer heads for the card. A label that the pointer came onto from the side,
    // or from its plate, has no way along the column; its card keeps clear the neighbour not
    // checked yet (toward()), when there is one.
    // The other rows, the legend and the hint that the card overlaps fade out (.is-covered), so
    // no slice of them shows beside it. The card is shown (data-open-place) as it is placed, and
    // measured before: a closed card keeps its size, clipped away. Every box is read first, in
    // one layout: the card's height and width, which are the same on either side, and
    // the boxes around it; its final box is worked out from its row's, so that its entrance,
    // which slides it, is never measured. Then the side, the top and the covered labels are
    // written, each only when it changes
    const CLEAR = 9;
    const place = (row, by, dir) => {
      const c = card(row);
      const h = c.offsetHeight, cb = c.getBoundingClientRect();
      const rem = parseFloat(getComputedStyle(document.documentElement).fontSize) || 16, gap = 0.4 * rem;
      const r = row.getBoundingClientRect();
      // where a card fitted over the label ends: the bottom of its head, just above the examples
      const head = row.querySelector('.hero-layer-head').getBoundingClientRect().bottom;
      const s = list.getBoundingClientRect(), st = stage.getBoundingClientRect();
      const hb = header ? Math.max(0, header.getBoundingClientRect().bottom) : 0;
      const side = band && getComputedStyle(band).getPropertyValue('--hero-band').trim() === 'side';
      const shown = controls.find(el => !el.hidden && el.getClientRects().length), tg = shown ? shown.getBoundingClientRect() : null;
      // the label that a sweep reaches next: rows run T7 first, so the one after ROW lies below it
      const next = dir === 'down' ? rows[rows.indexOf(row) + 1] : dir === 'up' ? rows[rows.indexOf(row) - 1] : null;
      const nb = next ? next.getBoundingClientRect() : null;
      const others = [...rows, ...covers].map(el => [el, el === row ? null : el.getBoundingClientRect()]);
      let top = Math.max(side ? band.getBoundingClientRect().top : s.top, tg ? tg.bottom + gap : -Infinity);
      let bottom = st.bottom;
      if (by !== 'key') { top = Math.max(top, hb + 8); bottom = Math.min(bottom, window.innerHeight - 8); }
      const room = { up: r.top - gap - top, down: bottom - (r.bottom + gap) };
      // a mouse card fits over the label's head (between the room's top and the head's bottom), and
      // below the label at least its head and first lines (4rem) would show
      const over = head - top >= cb.height, shows = room.down >= 4 * rem;
      const pref = row.dataset.place === 'up' ? 'up' : 'down', other = pref === 'up' ? 'down' : 'up';
      // above its label, a touch card must also start low enough in the page for bring() to
      // scroll its top clear of the header: near the page's top, on a short window, it cannot
      const above = r.top - gap - h + window.scrollY >= hb + 8;
      // the card's top as it ends (y): below the label, above it (its bottom 0.4rem over the
      // label's top, as the stylesheet puts it), or a top of its own (fit, over the head and
      // ending at its bottom; past)
      let at = '', y = null;
      if (nb && by === 'mouse') {
        const back = dir === 'down' ? 'up' : 'down';
        if (room[back] >= h) at = back;
        else if (dir === 'down' && over) at = 'fit';   // above the examples, so short of the next label
        else if (dir === 'down' ? bottom - (nb.bottom + CLEAR) >= cb.height : nb.top - CLEAR - top >= cb.height) {
          at = 'past';
          y = dir === 'down' ? nb.bottom + CLEAR : nb.top - CLEAR - cb.height;
        } else if (dir === 'down' ? nb.bottom + CLEAR + 4 * rem <= bottom : shows) {
          // a short window: past the next label going down, below its own label going up
          at = dir === 'down' ? 'past' : 'down';
          if (dir === 'down') y = nb.bottom + CLEAR;
        }
      }
      if (!at) {
        at = room[pref] >= h ? pref : room[other] >= h ? other
          : by === 'mouse' ? (over ? 'fit' : shows ? 'down' : 'up')
          : by === 'key' ? 'down' : room.up > room.down && above ? 'up' : 'down';
      }
      if (y === null) y = at === 'fit' ? head - cb.height : at === 'up' ? r.top - gap - cb.height : r.bottom + gap;
      if (row.dataset.openPlace !== at) row.dataset.openPlace = at;
      if (at === 'fit' || at === 'past') c.style.top = (y - r.top) + 'px';
      else c.style.removeProperty('top');
      placed = { row, dy: y - r.top, h: cb.height };
      others.forEach(([el, b]) => el.classList.toggle('is-covered', !!b && b.height > 0 && y - 8 < b.bottom && y + cb.height + 8 > b.top && cb.left < b.right && cb.right > b.left));
    };
    // The open card's box as place() put it, from its row's box now (the page may have
    // scrolled since), so that a card still sliding in is measured where it ends
    const cardBox = row => {
      if (!placed || placed.row !== row) return card(row).getBoundingClientRect();
      const top = row.getBoundingClientRect().top + placed.dy;
      return { top, bottom: top + placed.h };
    };
    // Keyboard focus: bring the open card and its label into view below the sticky header, or
    // only the focused TARGET when the two are taller than the window; a Tab on to the card's
    // link then does not jump the page, and no focused element is left under the header or
    // below the window. The scroll runs even when it is 0: any scroll from a focus handler
    // replaces the browser's own scroll to the focus, which Chrome aims at where the element
    // was before this handler opened or moved its card
    const reveal = (row, target) => {
      const hb = header ? Math.max(0, header.getBoundingClientRect().bottom) : 0;
      const lo = hb + 8, hi = window.innerHeight - 8;
      const c = cardBox(row), r = row.getBoundingClientRect();
      let a = Math.min(c.top, r.top), b = Math.max(c.bottom, r.bottom);
      if (b - a > hi - lo && target) { const q = target.getBoundingClientRect(); a = q.top; b = q.bottom; }
      const dy = a < lo ? a - lo : b > hi ? Math.min(b - hi, a - lo) : 0;
      try { window.scrollBy({ top: dy, behavior: 'instant' }); } catch (e) { window.scrollBy(0, dy); }
    };
    // A tap, from 45em: a card that a tap opened ends wholly in view, never under the sticky
    // header or past the window's bottom. Placed on the side with more room, it may not fit
    // there, so the page scrolls by the least that brings the card between the two, or, when it
    // is taller than that, puts its top just under the header; a card in view scrolls nothing.
    // The scroll is instant under reduced motion and otherwise the page's own (smooth). Only the
    // tap scrolls: a resize places the card again but leaves the page where the reader has it. A
    // tapped card has no entrance (data-hv-instant), so its box is where it ends
    const bring = row => {
      const hb = header ? Math.max(0, header.getBoundingClientRect().bottom) : 0;
      const lo = hb + 8, hi = window.innerHeight - 8;
      const c = card(row).getBoundingClientRect();
      const dy = c.height > hi - lo || c.top < lo ? c.top - lo : c.bottom > hi ? c.bottom - hi : 0;
      if (Math.abs(dy) < 1) return;
      try { window.scrollBy({ top: dy, behavior: reduced.matches ? 'instant' : 'auto' }); } catch (e) { window.scrollBy(0, dy); }
    };
    // Phones: open or close ROW in the list; the scene marks the most recently opened row still
    // open, until every layer is checked: then the scene runs the loop instead, which a marked
    // row would hold. A row that opens is checked
    const toggleRow = (row, open = !row.classList.contains('is-open')) => {
      row.classList.toggle('is-open', open);
      more(row).setAttribute('aria-expanded', String(open));
      if (openOrder.includes(row)) openOrder.splice(openOrder.indexOf(row), 1);
      if (open) {
        openOrder.push(row);
        check(row);
      }
      const last = state.done ? null : openOrder[openOrder.length - 1];
      if (tee(last) && !(fig.dataset.hvActive === '1' || fig.dataset.hvActive === '2')) hop();
      if (last) fig.dataset.hvActive = last.dataset.n;
      else fig.removeAttribute('data-hv-active');
      update();
    };

    rows.forEach(row => {
      more(row).addEventListener('click', () => {
        if (narrow.matches) {
          toggleRow(row);
          return;
        }
        dismissed = null;
        set(active === row && row.dataset.openPlace ? null : row, lastPointer === 'touch' ? 'touch' : keyed ? 'key' : 'mouse');
      });
      // A plain click on the card, outside its link, follows the row's name to the Stack page
      card(row).addEventListener('click', e => {
        if (narrow.matches || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        if (e.target.closest('a, button') || String(window.getSelection() || '').trim()) return;
        row.querySelector('.hero-layer-link').click();
      });
    });

    // A mouse or pen. A layer's triggers are its plate in the scene and its label's name area, the
    // head line with its code and name ("T5 Agents"), which the name link's target spans across
    // the label column; the examples under the name, its vendor marks and names, are no trigger:
    // pointing at them shows a mark's name (tips()) and opens, switches, closes and checks nothing.
    // The pointer's moves over the stage are read once a frame (steer()). Moving onto a trigger
    // opens its layer at once, also while another card is open, unless the pointer is heading for
    // that card (heading()), the card has shown for AGE ms, long enough to be seen and aimed at,
    // and the trigger lies on the way: a plate below the open layer, whose card lies below its
    // label (placed), or a name between the open layer's label and its card (between(), a card past
    // the next label). Then the trigger waits, and opens when the pointer turns away or slows almost
    // to a stop while still on it, or once it has not moved towards the card for REST ms (rest(): a
    // pointer that stops on it waits that long, so a short stop on the way to the card keeps the
    // card); a pointer that reaches the card or leaves the trigger drops the wait. The way to a card
    // below its label crosses the plates below its layer; the way to one above it (T1 to T3, a card
    // fitted over its label's head, one past the label above) crosses none, so a sweep up the board
    // never waits. So the names and the plates can be scanned without a pause, a card that a passing
    // pointer opened on its way gives way at once, and a pointer on its way to the open card,
    // however slowly, switches nothing. A pointer that comes back over the edge of a plate it has
    // just crossed opens the layer it left only once it is EDGE px (along x plus along y) from
    // where it crossed, or rests there for REST ms, so a pen that hovers on an edge does not
    // flicker between two layers. Moving within a trigger opens nothing: after Esc the pointer must
    // enter another plate or name. A tap opens the layer, or closes it when it is open; a click
    // opens it and shows its card. A layer that the mouse or pen opened shows its card once the
    // pointer settles on one of its triggers (settle()): it has moved under 3px over the last TRAIL
    // ms (a pen that hovers drifts), or not at all for STILL ms. A pointer that sweeps on opens and
    // checks each layer whose trigger it crosses, and no card lies over the names and plates ahead
    // of it. The open card stays while the pointer is on its layer's name or plate or on the card,
    // and while the pointer heads for the card, across the gap between them; GRACE ms after the
    // pointer has left them all, the card closes (keep() and linger())
    const REST = 200, TRAIL = 100, SLACK = 12, AGE = 200, EDGE = 8, STILL = 120, GRACE = 300;
    const slow = () => {
      const a = trail[0], b = trail[trail.length - 1];
      return !!a && b.t - a.t >= TRAIL && Math.abs(b.x - a.x) + Math.abs(b.y - a.y) < 3;
    };
    // whether the pointer has not moved for STILL ms
    const stopped = () => !trail.length || performance.now() - trail[trail.length - 1].t >= STILL;
    // The pointer has settled: the open layer's card shows while the pointer is on one of the
    // layer's triggers (a pointer that settles elsewhere shows no card, and the layer closes GRACE
    // ms after the pointer left its triggers). A trigger that waits opens only once the pointer has
    // not headed for the card for REST ms (rest()), so a short stop on the way keeps the card
    const settle = () => {
      if (!narrow.matches && active && !active.dataset.openPlace && how === 'mouse' && under === active) show(active, 'mouse', true);
    };
    // Whether the pointer heads for the open card: the ray from where it is, along its heading
    // over the last TRAIL ms, meets the card's box grown by SLACK px. A pointer that has moved
    // under 3px in that time heads nowhere, and nothing heads for a card that has not shown
    const heading = () => {
      const a = trail[0], b = trail[trail.length - 1];
      if (!a || !active || !active.dataset.openPlace) return false;
      const dx = b.x - a.x, dy = b.y - a.y;
      if (Math.abs(dx) + Math.abs(dy) < 3) return false;
      const c = card(active).getBoundingClientRect();
      let near = 0, far = Infinity;
      for (const [p, d, lo, hi] of [[b.x, dx, c.left - SLACK, c.right + SLACK], [b.y, dy, c.top - SLACK, c.bottom + SLACK]]) {
        if (!d) { if (p < lo || p > hi) return false; continue; }
        const u = (lo - p) / d, v = (hi - p) / d;
        near = Math.max(near, Math.min(u, v));
        far = Math.min(far, Math.max(u, v));
      }
      return near <= far;
    };
    // ROW's trigger waits while the pointer heads for the open card (null: nothing waits); HIT:
    // it is a plate; DIR: the way the pointer came onto it, a name. One timer runs while something
    // waits and checks, when it fires, that the pointer has not headed for the card for REST ms
    const wait = (row, hit = false, dir = null) => {
      if (!row) {
        pending = null;
        if (restT) { clearTimeout(restT); restT = 0; }
        return;
      }
      if (row !== pending) { pendingHit = hit; pendingDir = dir; }
      pending = row;
      aimed = performance.now();
      if (!restT) restT = setTimeout(rest, REST);
    };
    const rest = () => {
      restT = 0;
      if (!pending) return;
      const due = REST - (performance.now() - aimed);
      if (due > 4) { restT = setTimeout(rest, due); return; }
      const row = pending;
      pending = null;
      if (row === active) return;
      go(row, pendingHit, pendingDir);
      if (stopped()) settle();   // a pointer that has stopped on it sees its card at once
    };
    // Open ROW from one of its triggers: from its plate (HIT), remembering the layer it replaced
    // and where the pointer was; from its name, with DIR, the way the pointer came onto it
    const go = (row, hit, dir) => {
      const from = active;
      point(row, hit ? null : dir);
      if (hit && from && active === row) { left = from; lx = px; ly = py; }
    };
    // Whether ROW's label lies on the way from the open layer's label to its card: below the label
    // and above the card's bottom for a card below its label, above the label and below the card's
    // top for one above it (the card's box as place() put it)
    const between = row => {
      if (!active || !placed || placed.row !== active) return false;
      const a = active.getBoundingClientRect(), r = row.getBoundingClientRect();
      const top = a.top + placed.dy, bottom = top + placed.h;
      return placed.dy > 0 ? r.top >= a.bottom - 1 && r.bottom <= bottom + 1 : r.bottom <= a.top + 1 && r.top >= top - 1;
    };
    // The open card: keep() while the pointer is on its layer's name or plate or on the card;
    // linger() once it has left them, after which the card closes in GRACE ms, unless keyboard focus
    // is in its row. AGAIN starts the wait over, while the pointer heads for the card: it closes
    // GRACE ms after the pointer stopped heading for it, also when the pointer stops on its way
    const keep = () => {
      clearTimeout(closeT);
      closeT = 0;
    };
    const linger = again => {
      if (closeT && !again) return;
      clearTimeout(closeT);
      closeT = setTimeout(() => {
        closeT = 0;
        if (active && !(keyed && active.contains(document.activeElement))) set(null);
      }, GRACE);
    };
    const steer = () => {
      frame = 0;
      aim();
      if (slow()) settle();
    };
    // What the pointer is on, once a frame: the row of the trigger under it (its plate, or its
    // label's head; the name link's target spans the head line), or the open card; the examples
    // under a name are neither, and open nothing
    const aim = () => {
      const el = over && over.closest ? over : null;
      const hit = el ? el.closest('.hv-hit[data-hv-n]') : null;
      const head = el && !hit ? el.closest('.hero-layer-head') : null;
      const row = (hit ? plates.get(hit) : head ? heads.get(head) : null) || null;
      const box = el && !row ? el.closest('.hero-card') : null;
      const entered = row !== under;
      under = row;
      if (row && entered) onLabel = head ? row : null;
      const dir = head && entered ? travelOf() : null;
      if (active) {
        // the open layer's own examples hold its card too, because the way from a name to a card
        // below it crosses them; they still open nothing, and another row's examples let it go
        const own = !row && !box && el && el.closest('.hero-examples') && rowOf(el) === active;
        if (row === active || (box && rowOf(box) === active) || own) keep();
        else linger(!!active.dataset.openPlace && heading());
      }
      if (!row || row === active) {
        wait(null);
        if (row && entered && head) point(row, dir);   // back on the open layer's name: the way it came
        return;
      }
      if (!entered && row !== pending) return;
      const came = entered ? dir : pendingDir;
      if (!active) go(row, !!hit, came);
      else if (hit && row === left && Math.abs(px - lx) + Math.abs(py - ly) < EDGE) wait(row, true);
      else if (performance.now() - opened >= AGE && onWay(row, hit) && heading()) wait(row, !!hit, came);
      else { wait(null); go(row, !!hit, came); }
    };
    // Whether the trigger of ROW (its plate when HIT, else its name) lies on the way to the open card
    const onWay = (row, hit) => {
      if (hit) return !!placed && placed.row === active && placed.dy > 0 && +row.dataset.n < +active.dataset.n;
      return between(row);
    };
    fig.querySelectorAll('.hv-hit[data-hv-n]').forEach(hit => {
      const row = rows.find(r => r.dataset.n === hit.getAttribute('data-hv-n'));
      if (!row) return;
      plates.set(hit, row);
      hit.addEventListener('click', () => {
        if (narrow.matches) return;
        dismissed = null;
        set(lastPointer === 'touch' && active === row ? null : row, lastPointer === 'touch' ? 'touch' : 'mouse');
      });
    });
    stage.addEventListener('pointermove', e => {
      if (!pointed(e)) return;
      over = e.target;
      if (!frame) frame = requestAnimationFrame(steer);
    }, { passive: true });
    // Leaving the stage leaves the open card too: it closes GRACE ms after the pointer left its
    // layer's name, its plate and the card, unless keyboard focus is in its row, and a card not
    // shown yet stays so
    stage.addEventListener('pointerleave', e => {
      if (frame) { cancelAnimationFrame(frame); frame = 0; }
      over = under = null;
      wait(null);
      if (e.pointerType !== 'touch' && active) linger(false);
    });

    // Focus in a row opens it from 45em: its name, its chevron or its card's stories link.
    // Focus elsewhere in the figure (the controls at its top right, the progress, the caption's
    // links) closes the card,
    // which could cover it, and so does focus that moves on to the rest of the page. Focus that
    // the window gives back scrolls nothing: the reader may have scrolled on since
    fig.addEventListener('focusin', e => {
      const back = e.target === blurred && !e.relatedTarget;   // the window gave focus back
      blurred = null;
      if (narrow.matches) return;
      const row = rowOf(e.target);
      if (!row) {
        set(null);
        return;
      }
      if (card(row).contains(e.target)) {   // the focused link must be seen, so its card opens
        dismissed = null;
        set(row, keyed ? 'key' : lastPointer === 'touch' ? 'touch' : 'mouse');
        if (keyed && !back) reveal(row, e.target);   // never under a pointer: a click would land on moved content
        return;
      }
      // Esc's dismissal holds while focus stays in the row or comes back to it with the window
      if (dismissed !== row || !(back || rowOf(e.relatedTarget) === row)) dismissed = null;
      if (keyed && !dismissed) {
        set(row, 'key');
        if (!back) reveal(row, e.target);
      }
    });
    // Focus that leaves for nothing (relatedTarget null) closes the card only when the page kept
    // focus and the press was not inside the figure: a press on a card's text moves focus to the
    // body, but the card stays under the pointer and its click follows the card's link; and the
    // window losing focus leaves the card as it is. Presses outside close it below
    fig.addEventListener('focusout', e => {
      if (!e.relatedTarget) blurred = e.target;
      if (narrow.matches || fig.contains(e.relatedTarget)) return;
      if (e.relatedTarget) { set(null); return; }
      if (pressedIn) return;
      setTimeout(() => { if (document.hasFocus() && !fig.contains(document.activeElement)) set(null); }, 0);
    });
    document.addEventListener('keydown', e => { if (!e.metaKey && !e.ctrlKey && !e.altKey) { keyed = true; pressedIn = false; } }, true);
    // Every mouse or pen move, also off the stage, joins the trail that gives the pointer's
    // heading, and starts again the wait for it to stop (STILL); this listener runs after the
    // stage's, which compares with the last position
    document.addEventListener('pointermove', e => {
      px = e.clientX;
      py = e.clientY;
      if (e.pointerType === 'touch') return;
      const now = performance.now();
      trail.push({ x: px, y: py, t: now });
      while (trail.length > 2 && now - trail[1].t > TRAIL) trail.shift();
      clearTimeout(stillT);
      stillT = setTimeout(settle, STILL);
    }, { passive: true });
    // A press outside the figure closes the card: a mouse or pen at once, a touch only when it
    // ends in a tap (a click), so a swipe that scrolls the page to the rest of the card keeps it
    document.addEventListener('pointerdown', e => {
      keyed = false;
      lastPointer = e.pointerType;
      pressedIn = fig.contains(e.target);
      if (active && !narrow.matches && !pressedIn && e.pointerType !== 'touch') set(null);
    }, true);
    document.addEventListener('click', e => {
      if (active && !narrow.matches && lastPointer === 'touch' && !fig.contains(e.target)) set(null);
    }, true);
    // Esc. From 45em it closes the card and dismisses it, and focus in the card moves to the
    // row's name (within the row, so the dismissal holds). On phones it closes the row that
    // holds focus and returns focus to the row's chevron
    document.addEventListener('keydown', e => {
      if (e.key !== 'Escape' || e.defaultPrevented || e.isComposing) return;
      if (narrow.matches) {
        const row = rowOf(document.activeElement);
        if (row && row.classList.contains('is-open')) {
          toggleRow(row, false);
          more(row).focus();
        }
        return;
      }
      const row = active;
      if (!row) return;
      dismissed = row;
      set(null);
      if (card(row).contains(document.activeElement)) row.querySelector('.hero-layer-link').focus();
    });

    // Crossing 45em closes everything and turns the plates on or off. A focused card stays
    // open, so its link is not hidden, and is placed as for the keyboard. A card shown from 45em
    // is placed again on resize, for the input that opened it, not on scroll
    const reset = () => {
      const focused = rows.find(row => card(row).contains(document.activeElement));
      keep();
      clearTimeout(stillT);
      wait(null);
      unfree();
      if (frame) { cancelAnimationFrame(frame); frame = 0; }
      over = under = onLabel = null;
      active = dismissed = placed = left = travel = null;
      openOrder.length = 0;
      [...rows, ...covers].forEach(el => el.classList.toggle('is-covered', false));
      rows.forEach(row => {
        row.classList.remove('is-active', 'is-open');
        row.removeAttribute('data-open-place');
        card(row).style.removeProperty('top');
        more(row).setAttribute('aria-expanded', 'false');
      });
      leaders.forEach(leader => leader.classList.remove('is-active'));
      fig.removeAttribute('data-hv-active');
      fig.removeAttribute('data-hv-instant');
      fig.toggleAttribute('data-hv-hits', !narrow.matches);
      if (focused && narrow.matches) toggleRow(focused, true);
      else if (focused) set(focused, 'key');
      update();
    };
    narrow.addEventListener('change', reset);
    window.addEventListener('resize', () => { if (active && active.dataset.openPlace && !narrow.matches) place(active, how, how === 'mouse' ? travel : null); });
    reset();
    state.enhanced = true;
  }

  /* The vendor marks' brand names. A mark in a layer's label that is named for screen readers
     (an svg.hero-logo with an aria-label) shows that name in the figure's one tooltip, .hero-tip,
     which the build ships hidden and aria-hidden, since screen readers have the name already. A
     mouse or pen shows it once the pointer has rested on the mark for TIP ms, or at once when a
     name went less than CHAIN ms before, so a sweep across the labels shows none while a reader
     who moves along a row's marks reads each; leaving the mark hides it. Pointing at a mark opens,
     switches, closes and checks no layer: only a layer's name and its plate do (layers()). A tap on
     a mark shows its name at once, until a second tap on it, a tap elsewhere or LINGER ms. The name
     stands GAP px above the mark, or below it where the open card, the sticky header or the
     window's top is in the way, and SIDE px inside the window's sides; once shown it keeps its side
     while it fits there, so it does not jump when an open card beside it goes; it moves when the
     open card shows or moves beside it (place() never lays a card over its own label's marks), and
     goes if a card covers the mark, on a key, a press, a scroll or a resize, and when focus moves
     in the figure. It adds no tab stop: from the keyboard the names stay with screen readers. On
     touch tablets the chevron's 44px target lies over part of some marks: a tap there opens the
     row's card, whose Examples line (shown where no pointer can rest) names every example in the
     label, so each name is reachable by touch, on the mark or in the card. It takes no pointer
     events and writes only its own text, hidden, top and left, so the layers, their checks, the
     cards and the sweeps run as they would without it */
  function tips(fig) {
    const tip = fig.querySelector('.hero-tip'), list = fig.querySelector('.hero-layers');
    if (!tip || !list) return;
    const header = document.querySelector('.site-header');
    const TIP = 150, CHAIN = 400, LINGER = 3000, GAP = 6, SIDE = 8;
    // on: the mark whose name shows; side: where the name stands, 'above' or 'below' it; tipT: the
    // wait before a name shows; lingerT: how long a tapped name stays; went: when a name last went;
    // tapped: the last press was a touch
    let on = null, side = 'above', tipT = 0, lingerT = 0, went = -Infinity, tapped = false;
    const markOf = el => (el && el.closest ? el.closest('svg.hero-logo[aria-label]') : null);
    const meets = (a, b) => a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
    const tipHide = () => {
      clearTimeout(tipT);
      clearTimeout(lingerT);
      tipT = lingerT = 0;
      if (!on) return;
      on = null;
      went = performance.now();
      tip.hidden = true;
    };
    // Places the name shown beside its mark, in the figure's box, on its side when it fits there,
    // else on the other; false when the open card covers the mark or neither side has room
    const tipFit = () => {
      const m = on.getBoundingClientRect();
      const open = fig.querySelector('.hero-layer[data-open-place] > .hero-card');
      const card = open ? open.getBoundingClientRect() : null;
      if (!m.width || (card && meets(card, m))) return false;
      const w = tip.offsetWidth, h = tip.offsetHeight;
      const hb = header ? Math.max(0, header.getBoundingClientRect().bottom) : 0;
      const left = Math.max(SIDE, Math.min(m.left + m.width / 2 - w / 2, document.documentElement.clientWidth - SIDE - w));
      const at = top => ({ left, right: left + w, top, bottom: top + h });
      const sides = { above: at(m.top - GAP - h), below: at(m.bottom + GAP) };
      const fits = b => b.top >= hb + 4 && b.bottom <= window.innerHeight - 4 && !(card && meets(card, b));
      const pick = [side, side === 'above' ? 'below' : 'above'].find(k => fits(sides[k]));
      if (!pick) return false;
      side = pick;
      const box = sides[pick];
      const f = fig.getBoundingClientRect();
      const x = Math.round(box.left - f.left) + 'px', y = Math.round(box.top - f.top) + 'px';
      if (tip.style.left !== x) tip.style.left = x;
      if (tip.style.top !== y) tip.style.top = y;
      return true;
    };
    const tipOpen = mark => {
      clearTimeout(tipT);
      tipT = 0;
      on = mark;
      side = 'above';
      const name = mark.getAttribute('aria-label');
      if (tip.textContent !== name) tip.textContent = name;
      if (tip.hidden) tip.hidden = false;
      if (!tipFit()) tipHide();
    };
    list.addEventListener('pointerover', e => {
      if (e.pointerType === 'touch') return;
      const mark = markOf(e.target);
      if (mark === on) return;
      if (!mark) { tipHide(); return; }
      if (on || performance.now() - went < CHAIN) tipOpen(mark);
      else {
        clearTimeout(tipT);
        tipT = setTimeout(() => tipOpen(mark), TIP);
      }
    });
    list.addEventListener('pointerout', e => {
      if (e.pointerType === 'touch') return;
      const mark = markOf(e.target);
      if (!mark || mark.contains(e.relatedTarget)) return;
      clearTimeout(tipT);
      tipT = 0;
      if (mark === on) tipHide();
    });
    document.addEventListener('pointerdown', e => {
      tapped = e.pointerType === 'touch';
      if (!(tapped && on && markOf(e.target) === on)) tipHide();
    }, true);
    // Each row's examples take the click themselves, not the list around them: a touch screen
    // moves a tap to the nearest element that takes taps (touch adjustment) and prefers the
    // innermost, so a tap on a mark or a name in the examples stays there instead of going to the
    // name link just above, and a tap on a name opens nothing
    list.querySelectorAll('.hero-examples').forEach(line => line.addEventListener('click', e => {
      const mark = tapped ? markOf(e.target) : null;
      if (!mark) return;
      if (mark === on) { tipHide(); return; }
      tipOpen(mark);
      if (on) lingerT = setTimeout(tipHide, LINGER);
    }));
    document.addEventListener('keydown', tipHide, true);
    fig.addEventListener('focusin', tipHide);
    window.addEventListener('scroll', tipHide, { passive: true });
    window.addEventListener('resize', tipHide);
    // the open card shows, moves or goes beside the name: the name moves clear of it, or goes
    new MutationObserver(() => { if (on && !tipFit()) tipHide(); })
      .observe(list, { subtree: true, attributes: true, attributeFilter: ['data-open-place', 'class'] });
  }
})();
