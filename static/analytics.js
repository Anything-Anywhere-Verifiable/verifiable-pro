/* Optional GA4, with basic consent: no Google tag or analytics request before Allow.
   The site queues one page view. Enhanced measurement must stay off in the GA stream. */
(function () {
  'use strict';
  var node = document.getElementById('analytics-config'), config;
  if (!node) return;
  try { config = JSON.parse(node.textContent); } catch (e) { return; }
  if (!config || typeof config.id !== 'string' || !/^G-[A-Z0-9]{4,20}$/.test(config.id)) return;
  try {
    if (location.protocol !== 'https:' || new URL(config.origin).origin !== location.origin) return;
  } catch (e) { return; }
  var panel = document.getElementById('analytics-choice');
  var open = document.querySelector('[data-analytics-open]');
  if (!panel || !open) return;
  var allow = panel.querySelector('[data-analytics-allow]');
  var decline = panel.querySelector('[data-analytics-decline]');
  var status = panel.querySelector('[data-analytics-status]');
  if (!allow || !decline || !status) return;
  var KEY = 'vp.analytics.v1', DISABLE = 'ga-disable-' + config.id;
  var active = false, tag = null, choice;

  function read() {
    var tabChoice, sharedChoice;
    // A tab-scoped choice is a fallback when localStorage cannot be written.
    try { tabChoice = sessionStorage.getItem(KEY); } catch (e) {}
    try { sharedChoice = localStorage.getItem(KEY); } catch (e) {}
    // A stored refusal wins over a stale Allow that could not be removed.
    if (tabChoice === 'deny' || sharedChoice === 'deny') return 'deny';
    return tabChoice === 'allow' || sharedChoice === 'allow' ? 'allow' : null;
  }
  function save(value) {
    try {
      localStorage.setItem(KEY, value);
      try { sessionStorage.removeItem(KEY); } catch (e) {}
      return;
    } catch (e) {}
    try { sessionStorage.setItem(KEY, value); } catch (e) {}
    if (value === 'deny') {
      // Removing a stale Allow can still work when a browser refuses storage writes.
      try { localStorage.removeItem(KEY); } catch (e) {}
    }
  }
  function clean(url) {
    try {
      var parsed = new URL(url);
      return /^https?:$/.test(parsed.protocol) ? parsed.origin + parsed.pathname : '';
    } catch (e) { return ''; }
  }
  function begin() {
    if (active) return;
    active = true;
    window[DISABLE] = false;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    var denied = { analytics_storage: 'denied', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied' };
    var safe = { page_location: location.origin + location.pathname,
      page_referrer: clean(document.referrer), page_title: location.pathname,
      allow_google_signals: false, allow_ad_personalization_signals: false,
      send_page_view: false, cookie_domain: 'none', cookie_path: '/',
      cookie_flags: 'SameSite=Lax;Secure' };
    window.gtag('consent', 'default', denied);
    window.gtag('consent', 'update', { analytics_storage: 'granted', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied' });
    window.gtag('set', 'ads_data_redaction', true);
    window.gtag('set', safe);
    window.gtag('js', new Date());
    window.gtag('config', config.id, safe);
    window.gtag('event', 'page_view', { send_to: config.id,
      page_location: safe.page_location, page_referrer: safe.page_referrer,
      page_title: safe.page_title });
    tag = document.createElement('script');
    tag.async = true;
    tag.referrerPolicy = 'no-referrer';
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(config.id);
    document.head.appendChild(tag);
  }
  function stop() {
    window[DISABLE] = true;
    active = false;
    if (tag) { tag.remove(); tag = null; }
    // This site configures host-only GA cookies at /, not cookies on parent domains.
    try {
      document.cookie.split(';').forEach(function (cookie) {
        var name = cookie.split('=')[0].trim();
        if (/^_ga(?:_[A-Z0-9]+)?$/.test(name)) {
          document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax; Secure';
        }
      });
    } catch (e) {} // Browsers can block cookie access as well as storage.
  }
  function show(focus) {
    status.textContent = choice === 'allow' ? config.on : choice === 'deny' ? config.off : '';
    status.hidden = !status.textContent;
    panel.hidden = false;
    if (focus) decline.focus();
  }
  function reject() {
    var loaded = active;
    stop();
    choice = 'deny';
    save(choice);
    panel.hidden = true;
    // Reload removes the tag's timers/listeners. Never reload into a stale stored Allow.
    if (loaded && read() !== 'allow') location.reload();
    else if (loaded) {
      show(false);
      status.textContent = config.unsaved;
      status.hidden = false;
    }
  }
  open.hidden = false;
  open.addEventListener('click', function () { show(true); });
  allow.addEventListener('click', function () {
    choice = 'allow'; save(choice); panel.hidden = true; begin();
  });
  decline.addEventListener('click', reject);
  window.addEventListener('storage', function (event) {
    if (event.key !== KEY && event.key !== null) return;
    // A new shared choice overrides a tab's storage fallback.
    try { sessionStorage.removeItem(KEY); } catch (e) {}
    choice = event.key === KEY && (event.newValue === 'allow' || event.newValue === 'deny')
      ? event.newValue : null;
    if (choice === 'allow') begin();
    else {
      var loaded = active;
      stop();
      if (loaded && read() !== 'allow') location.reload();
      else if (loaded) {
        show(false);
        status.textContent = config.unsaved;
        status.hidden = false;
      }
      else if (choice === null) show(false);
    }
  });
  choice = read();
  if (choice === 'allow') begin();
  else {
    window[DISABLE] = true;
    if (choice === null) show(false);
  }
}());
