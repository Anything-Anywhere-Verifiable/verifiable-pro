"""Optional GA4 must fail closed and never receive questions or URL queries.

The runtime tests execute the complete local consent script in Node with a
small DOM/storage stand-in. Appending the Google tag only records its URL:
these tests never download a tag or send an Analytics event.
"""

import copy
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sitegen import content  # noqa: E402
from sitegen.render import Site  # noqa: E402

MEASUREMENT_ID = "G-TEST123456"
CONFIG_RE = re.compile(r'<script type="application/json" id="analytics-config">(.*?)</script>', re.S)
MARKERS = ('id="analytics-config"', 'id="analytics-choice"', "data-analytics-open", "assets/analytics.js")


class AnalyticsConfigTests(unittest.TestCase):
    def test_missing_and_empty_ids_disable_analytics(self):
        for site in ({}, {"analytics": {}}, {"analytics": {"ga4_measurement_id": ""}}):
            with self.subTest(site=site):
                self.assertEqual(content.analytics_id(site), "")

    def test_measurement_id_is_returned_without_rewriting(self):
        self.assertEqual(content.analytics_id({"analytics": {"ga4_measurement_id": MEASUREMENT_ID}}),
                         MEASUREMENT_ID)

    def test_invalid_blocks_and_ids_fail_content_validation(self):
        blocks = [None, [], "G-TEST123456", True, {"unknown": "value"}]
        ids = [None, [], {}, True, 123, " G-TEST123456", "G-TEST123456 ", "g-TEST123456",
               "G-test123456", "GT-TEST123456", "UA-123456-1", "G-ABC", "G-" + "A" * 21,
               'G-TEST</script><script>alert(1)</script>']
        blocks += [{"ga4_measurement_id": value} for value in ids]
        for block in blocks:
            with self.subTest(block=block), self.assertRaises(content.ContentError):
                content.analytics_id({"analytics": block})


class AnalyticsTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = content.load(ROOT)

    def page(self, identifier=MEASUREMENT_ID, mode="prod", lang="en"):
        model = dict(self.model, site=dict(self.model["site"]))
        model["site"]["analytics"] = {"ga4_measurement_id": identifier}
        model["site"]["chat"] = {"mode": "off"}
        site = Site(model, mode)
        site.lang = lang
        path, alternate = ("/", "/zh/") if lang == "en" else ("/zh/", "/")
        return site.layout(path=path, title="Test", description="Test", section="latest",
                           body="<p>Test</p>", alt_path=alternate, page_class="test-page")

    def test_configured_production_pages_offer_bilingual_local_controls(self):
        for lang in content.LANGS:
            with self.subTest(lang=lang):
                page = self.page(lang=lang)
                config = json.loads(CONFIG_RE.search(page).group(1))
                self.assertEqual(config["id"], MEASUREMENT_ID)
                self.assertEqual(config["origin"], self.model["site"]["base_url"].rstrip("/"))
                self.assertIn('<script src="/assets/analytics.js" defer></script>', page)
                self.assertIn('data-analytics-open hidden', page)
                self.assertRegex(page, r'<section[^>]+id="analytics-choice"[^>]+hidden>')
                for key in ("analytics_title", "analytics_allow", "analytics_decline", "analytics_choices"):
                    self.assertIn(self.model["strings"][lang][key], page)
                privacy_path = "/privacy/" if lang == "en" else "/zh/privacy/"
                self.assertIn('href="' + privacy_path + '"', page)
                self.assertNotIn("googletagmanager.com", page)
                self.assertNotIn("google-analytics.com", page)

    def test_empty_id_and_nonproduction_builds_emit_no_analytics_markup(self):
        for mode, identifier in (("prod", ""), ("preview", MEASUREMENT_ID), ("artifact", MEASUREMENT_ID)):
            for lang in content.LANGS:
                with self.subTest(mode=mode, lang=lang):
                    page = self.page(identifier, mode, lang)
                    for marker in MARKERS:
                        self.assertNotIn(marker, page)

    def test_analytics_json_cannot_close_its_script(self):
        model = copy.deepcopy(self.model)
        model["site"]["analytics"] = {"ga4_measurement_id": MEASUREMENT_ID}
        model["strings"]["en"]["analytics_on"] = "</script><!-- <b>"
        site = Site(model)
        block = site.analytics_block()
        match = CONFIG_RE.search(block)
        self.assertIsNotNone(match)
        self.assertEqual(json.loads(match.group(1))["on"], "</script><!-- <b>")
        self.assertNotIn("<", match.group(1))


# The stand-in has no input/document text API beyond the configuration and
# controls. This also catches accidental access to Ask or search form values.
HARNESS = r"""
const fs = require('node:fs'), vm = require('node:vm');
const source = fs.readFileSync(process.argv[1], 'utf8');
const options = JSON.parse(process.argv[2]);
const KEY = 'vp.analytics.v1';
const config = Object.assign({id:'G-TEST123456', origin:'https://verifiable.pro',
  on:'Enabled', off:'Disabled', unsaved:'Could not save'}, options.config || {});
const reloads = [], tags = [], cookieWrites = [];
const makeStorage = settings => {
  const s = Object.assign({data:{}}, settings || {});
  s.data = Object.assign({}, s.data);
  return {
    data:s.data,
    getItem(k) { if (s.getFails) throw new Error('storage read blocked'); return s.data[k] === undefined ? null : s.data[k]; },
    setItem(k,v) { if (s.setFails) throw new Error('storage write blocked'); s.data[k] = String(v); },
    removeItem(k) { if (s.removeFails) throw new Error('storage delete blocked'); delete s.data[k]; }
  };
};
const localStorage = makeStorage(options.local), sessionStorage = makeStorage(options.session);
const makeElement = () => ({hidden:true, textContent:'', listeners:{}, focuses:0,
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); },
  focus() { this.focuses++; },
  click() { for (const fn of this.listeners.click || []) fn({type:'click'}); }
});
const allow = makeElement(), decline = makeElement(), status = makeElement();
const panel = makeElement(), open = makeElement();
panel.querySelector = selector => ({'[data-analytics-allow]':allow,
  '[data-analytics-decline]':decline, '[data-analytics-status]':status})[selector] || null;
const url = new URL(options.url || 'https://verifiable.pro/search/?q=PRIVATE_SEARCH#PRIVATE_FRAGMENT');
const location = {protocol:url.protocol, origin:url.origin, pathname:url.pathname,
  search:url.search, hash:url.hash, href:url.href,
  reload() { reloads.push({disabled:window['ga-disable-' + config.id],
    local:Object.assign({}, localStorage.data), session:Object.assign({}, sessionStorage.data)}); }};
const window = {listeners:{}, addEventListener(type,fn) { (this.listeners[type] ||= []).push(fn); }};
const cookies = Object.assign({_ga:'browser-id', _ga_TEST123456:'session-id', unrelated:'keep'}, options.cookies || {});
const document = {
  referrer:options.referrer === undefined ? 'https://example.org/from/?q=PRIVATE_REFERRER#PRIVATE_REF_FRAGMENT' : options.referrer,
  title:'PRIVATE_DOCUMENT_TITLE',
  getElementById(id) { return id === 'analytics-config' ? {textContent:JSON.stringify(config)} : id === 'analytics-choice' ? panel : null; },
  querySelector(selector) { return selector === '[data-analytics-open]' ? open : null; },
  createElement(kind) { if (kind !== 'script') throw new Error('unexpected element: ' + kind);
    return {removed:false, remove() { this.removed = true; }}; },
  head:{appendChild(node) { tags.push(node); }}
};
Object.defineProperty(document, 'cookie', {
  get() { if (options.cookieGetFails) throw new Error('cookie read blocked');
    return Object.entries(cookies).map(([k,v]) => k + '=' + v).join('; '); },
  set(value) { if (options.cookieSetFails) throw new Error('cookie write blocked');
    cookieWrites.push(value); const pair = value.split(';')[0], i = pair.indexOf('=');
    const name = pair.slice(0,i); if (/Max-Age=0/i.test(value)) delete cookies[name]; else cookies[name] = pair.slice(i+1); }
});
vm.runInNewContext(source, {window, document, location, localStorage, sessionStorage,
  URL, Date, JSON, encodeURIComponent}, {timeout:1000});
for (const action of options.actions || []) {
  if (typeof action === 'string') ({allow, decline, open})[action].click();
  else if (action.storage) {
    const event = action.storage;
    if (event.key === null) for (const key of Object.keys(localStorage.data)) delete localStorage.data[key];
    else if (event.newValue === null) delete localStorage.data[event.key || KEY];
    else localStorage.data[event.key || KEY] = event.newValue;
    for (const fn of window.listeners.storage || []) fn({key:event.key === undefined ? KEY : event.key,
      newValue:event.newValue, storageArea:event.session ? sessionStorage : localStorage});
  }
}
console.log(JSON.stringify({tags:tags.map(t => ({src:t.src, async:t.async,
  referrerPolicy:t.referrerPolicy, removed:t.removed})),
  commands:window.dataLayer ? Array.from(window.dataLayer, a => Array.from(a)) : null,
  hasGtag:typeof window.gtag === 'function', disabled:window['ga-disable-' + config.id],
  panelHidden:panel.hidden, openHidden:open.hidden, statusHidden:status.hidden,
  status:status.textContent, declineFocuses:decline.focuses,
  local:localStorage.data, session:sessionStorage.data, reloads, cookies, cookieWrites}));
"""


class AnalyticsRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.node = shutil.which("node")
        if not cls.node:
            raise unittest.SkipTest("Node.js is not installed")

    def run_script(self, **options):
        process = subprocess.run([self.node, "-e", HARNESS, str(ROOT / "static" / "analytics.js"),
                                  json.dumps(options)], capture_output=True, text=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        return json.loads(process.stdout)

    def assert_no_tag(self, result):
        self.assertEqual(result["tags"], [])
        self.assertIsNone(result["commands"])
        self.assertFalse(result["hasGtag"])

    def test_unknown_and_declined_choices_never_initialize_google(self):
        unknown = self.run_script()
        self.assert_no_tag(unknown)
        self.assertFalse(unknown["panelHidden"])
        self.assertFalse(unknown["openHidden"])
        declined = self.run_script(actions=["decline"])
        self.assert_no_tag(declined)
        self.assertTrue(declined["panelHidden"])
        self.assertEqual(declined["local"]["vp.analytics.v1"], "deny")
        self.assertEqual(declined["reloads"], [])
        self.assertTrue(declined["disabled"])
        remembered = self.run_script(local={"data": {"vp.analytics.v1": "deny"}})
        self.assert_no_tag(remembered)
        self.assertTrue(remembered["panelHidden"])

    def test_allow_loads_one_tag_and_sends_only_sanitized_page_view(self):
        result = self.run_script(actions=["allow", "allow"])
        self.assertEqual(len(result["tags"]), 1)
        self.assertEqual(result["tags"][0]["src"],
                         "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID)
        self.assertEqual(result["tags"][0]["referrerPolicy"], "no-referrer")
        self.assertTrue(result["tags"][0]["async"])
        self.assertFalse(result["disabled"])
        commands = result["commands"]
        self.assertEqual(commands[0][:2], ["consent", "default"])
        self.assertEqual(commands[1][:2], ["consent", "update"])
        for command in commands[:2]:
            for key in ("ad_storage", "ad_user_data", "ad_personalization"):
                self.assertEqual(command[2][key], "denied")
        self.assertEqual(commands[0][2]["analytics_storage"], "denied")
        self.assertEqual(commands[1][2]["analytics_storage"], "granted")
        configs = [command for command in commands if command[0] == "config"]
        self.assertEqual(len(configs), 1)
        config = configs[0][2]
        self.assertEqual(configs[0][1], MEASUREMENT_ID)
        self.assertFalse(config["send_page_view"])
        self.assertFalse(config["allow_google_signals"])
        self.assertFalse(config["allow_ad_personalization_signals"])
        self.assertNotIn("user_id", config)
        self.assertEqual(config["cookie_domain"], "none")
        self.assertEqual(config["cookie_path"], "/")
        events = [command for command in commands if command[0] == "event"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1], "page_view")
        self.assertEqual(events[0][2]["send_to"], MEASUREMENT_ID)
        for data in (config, events[0][2]):
            self.assertEqual(data["page_location"], "https://verifiable.pro/search/")
            self.assertEqual(data["page_referrer"], "https://example.org/from/")
            self.assertNotIn("?", data["page_title"])
            self.assertNotIn("#", data["page_title"])
        self.assertNotIn("PRIVATE_", json.dumps(commands))

    def test_reopen_exposes_current_choice_and_keeps_decline_accessible(self):
        result = self.run_script(actions=["allow", "open"])
        self.assertFalse(result["panelHidden"])
        self.assertEqual(result["status"], "Enabled")
        self.assertFalse(result["statusHidden"])
        self.assertEqual(result["declineFocuses"], 1)
        self.assertEqual(len(result["tags"]), 1)

    def test_withdrawal_disables_pending_tag_before_reload_and_clears_only_ga_cookies(self):
        # The remote tag has not executed: withdrawal must also handle this race.
        result = self.run_script(actions=["allow", "decline"])
        self.assertTrue(result["disabled"])
        self.assertTrue(result["tags"][0]["removed"])
        self.assertEqual(result["cookies"], {"unrelated": "keep"})
        self.assertEqual(len(result["reloads"]), 1)
        self.assertTrue(result["reloads"][0]["disabled"])
        self.assertEqual(result["reloads"][0]["local"]["vp.analytics.v1"], "deny")
        self.assertTrue(all("Max-Age=0" in write and "Path=/" in write for write in result["cookieWrites"]))

    def test_cross_tab_deny_overrides_stale_session_allow(self):
        result = self.run_script(local={"data": {"vp.analytics.v1": "allow"}},
                                 session={"data": {"vp.analytics.v1": "allow"}},
                                 actions=[{"storage": {"newValue": "deny"}}])
        self.assertEqual(len(result["tags"]), 1)
        self.assertTrue(result["disabled"])
        self.assertTrue(result["tags"][0]["removed"])
        self.assertNotEqual(result["session"].get("vp.analytics.v1"), "allow")
        self.assertEqual(len(result["reloads"]), 1)

    def test_cross_tab_withdrawal_remains_disabled_when_session_is_unwritable(self):
        result = self.run_script(local={"data": {"vp.analytics.v1": "allow"}},
                                 session={"data": {"vp.analytics.v1": "allow"},
                                          "setFails": True, "removeFails": True},
                                 actions=[{"storage": {"newValue": "deny"}}])
        self.assertTrue(result["disabled"])
        self.assertTrue(result["tags"][0]["removed"])
        if result["reloads"]:
            after = result["reloads"][0]
            self.assert_no_tag(self.run_script(local={"data": after["local"]},
                                              session={"data": after["session"]}))

    def test_shared_deny_still_wins_on_the_next_page_with_stale_session_allow(self):
        # A different tab revoked consent, but this tab could not clear its
        # session fallback. A normal later navigation must stay opted out too.
        result = self.run_script(local={"data": {"vp.analytics.v1": "deny"}},
                                 session={"data": {"vp.analytics.v1": "allow"},
                                          "setFails": True, "removeFails": True})
        self.assert_no_tag(result)
        self.assertTrue(result["disabled"])

    def test_session_deny_overrides_unwritable_shared_allow_on_later_pages(self):
        result = self.run_script(local={"data": {"vp.analytics.v1": "allow"},
                                         "setFails": True, "removeFails": True},
                                 session={"data": {"vp.analytics.v1": "deny"}})
        self.assert_no_tag(result)
        self.assertTrue(result["disabled"])

    def test_cookie_access_failures_do_not_interrupt_withdrawal(self):
        for failure in ("cookieGetFails", "cookieSetFails"):
            with self.subTest(failure=failure):
                result = self.run_script(actions=["allow", "decline"], **{failure: True})
                self.assertTrue(result["disabled"])
                self.assertTrue(result["tags"][0]["removed"])
                self.assertEqual(len(result["reloads"]), 1)
                self.assertEqual(result["local"]["vp.analytics.v1"], "deny")

    def test_storage_clear_revokes_active_consent(self):
        result = self.run_script(local={"data": {"vp.analytics.v1": "allow"}},
                                 actions=[{"storage": {"key": None, "newValue": None}}])
        self.assertTrue(result["disabled"])
        self.assertEqual(len(result["reloads"]), 1)
        self.assertEqual(result["local"], {})

    def test_storage_failures_do_not_automatically_grant_consent(self):
        result = self.run_script(local={"getFails": True, "setFails": True, "removeFails": True},
                                 session={"getFails": True, "setFails": True, "removeFails": True})
        self.assert_no_tag(result)
        self.assertFalse(result["panelHidden"])
        # Explicit Allow may operate for this page even when it cannot be saved.
        result = self.run_script(local={"getFails": True, "setFails": True, "removeFails": True},
                                 session={"getFails": True, "setFails": True, "removeFails": True},
                                 actions=["allow", "decline"])
        self.assertEqual(len(result["tags"]), 1)
        self.assertTrue(result["disabled"])

    def test_failed_withdrawal_persistence_never_reloads_into_stored_allow(self):
        result = self.run_script(local={"data": {"vp.analytics.v1": "allow"},
                                         "setFails": True, "removeFails": True},
                                 session={"setFails": True}, actions=["decline"])
        self.assertTrue(result["disabled"])
        self.assertEqual(result["reloads"], [])
        self.assertFalse(result["panelHidden"])
        self.assertEqual(result["status"], "Could not save")

    def test_malformed_remembered_choice_stays_unknown(self):
        for choice in ("yes", "ALLOW", '{"choice":"allow"}', ""):
            with self.subTest(choice=choice):
                result = self.run_script(local={"data": {"vp.analytics.v1": choice}})
                self.assert_no_tag(result)
                self.assertFalse(result["panelHidden"])

    def test_invalid_ids_or_origins_do_not_enable_controls_or_load_google(self):
        scenarios = [
            {"config": {"id": ""}}, {"config": {"id": "GT-TEST123456"}},
            {"config": {"id": [MEASUREMENT_ID]}},
            {"config": {"id": "G-test123456"}}, {"config": {"id": "G-A</script>"}},
            {"config": {"origin": "https://example.org"}}, {"config": {"origin": "not a URL"}},
            {"url": "http://verifiable.pro/"}, {"url": "https://example.org/"},
        ]
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                result = self.run_script(actions=["allow"], **scenario)
                self.assert_no_tag(result)
                self.assertTrue(result["openHidden"])

    def test_non_http_and_invalid_referrers_are_empty(self):
        for referrer in ("", "not a URL", "javascript:PRIVATE_VALUE", "data:text/plain,PRIVATE_VALUE"):
            with self.subTest(referrer=referrer):
                result = self.run_script(referrer=referrer, actions=["allow"])
                config = next(command[2] for command in result["commands"] if command[0] == "config")
                self.assertEqual(config["page_referrer"], "")


if __name__ == "__main__":
    unittest.main()
