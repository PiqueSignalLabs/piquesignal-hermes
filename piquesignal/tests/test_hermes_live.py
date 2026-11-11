"""Tests for the NEW read-only addresses (the server contract): the keyless Missed strip / Free Pick / banners / images /
free history and the keyed Featured Callers / Missed reveal / member history. Fake secret store, fake network, fake
clocks; no real network. Covers 5.6: copies-identical cleaners, image magic / ctype / size caps, placeholder => None,
data: URL format, pacing with featured + history, reveal floor + cache + cap, no query string, no key on keyless URLs,
4xx stops 15 min (history 404: until the next start), the random 0..120 s first call per path (once per start),
Retry-After, the history decoder (strict wire v1) - and 5.7: this release ships HERMES_LIVE = True (core.py and the
pane together, tied by a test), the shipped switch really asks the new addresses, and the kill switch (HERMES_LIVE =
False) still asks nothing new and keeps the old behaviour (incl. pacing)."""
import base64
import importlib.util
import ast
import inspect
import json
import textwrap
import math
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
FREEFEED = PLUGIN.parents[1] / "freefeed"
sys.path.insert(0, str(FREEFEED))
import freefeed       # noqa: E402  (the free-feed service: its cleaners are the originals)
import free_history   # noqa: E402  (the reference free-history encoder = the wire format v1)

MINT = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"
MINT2 = "So11111111111111111111111111111111111111112"
KEY = "pqs_TESTKEY_0123456789abcdef"
KEY2 = "pqs_OTHERKEY_0123456789abcdef"
IMG = "0123456789abcdef"
BIMG = "b7-0123456789ab"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 40
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 40
WEBP = b"RIFF\x00\x00\x00\x00WEBPVP8 " + b"\x00" * 20

_scope = sys.modules.get("agent.secret_scope")
if _scope is None or not hasattr(_scope, "_pqs_secret"):
    _scope = types.ModuleType("agent.secret_scope")
    _scope._pqs_secret = {"value": None}
    _scope.get_secret = lambda name, default=None: _scope._pqs_secret["value"] if name == "PIQUESIGNAL_API_KEY" else default
    _agent = types.ModuleType("agent")
    _agent.secret_scope = _scope
    sys.modules["agent"] = _agent
    sys.modules["agent.secret_scope"] = _scope
_secret = _scope._pqs_secret


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


api = _load("t5_plugin_api", PLUGIN / "dashboard" / "plugin_api.py")
core = api.core
fc = core.fc
hc = fc._hermes
NEW_URLS = (fc.MISSED_URL, fc.FREE_PICK_URL, fc.BANNERS_URL, fc.FREE_HISTORY_URL, fc.FEATURED_URL, fc.HISTORY_URL)
SHIPPED = core.HERMES_LIVE        # the switch as this release ships it (restored after every test: core is shared)
KEYLESS = ("/api/free-board/",)
# The shipped module state this file swaps for fakes (core is shared by every test file): put back by tearDownModule, so
# the next file starts from the real module-level clients, transport and switch, not from these test doubles.
_SHIPPED_STATE = {n: getattr(core, n) for n in ("HERMES_LIVE", "_TRANSPORT", "_missed", "_free_pick", "_banners",
                                                "_free_history", "_images", "_reveal")}


def tearDownModule():
    for n, v in _SHIPPED_STATE.items():
        setattr(core, n, v)
    core._members.clear()
    core._refusal_hold.clear()
    _secret["value"] = None


class Clock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


class Net:
    def __init__(self):
        self.calls = []
        self.replies = {}

    def __call__(self, url, headers, timeout, *cap):
        self.calls.append((url, dict(headers), cap))
        r = self.replies.get(url)
        if r is None:
            raise OSError("no reply")
        return r.pop(0) if isinstance(r, list) else r


def jr(obj, status=200, hdrs=None):
    return status, hdrs or {}, json.dumps(obj).encode()


MISSED = {"as_of": "t", "missed": [{"gain": 4.2, "ageMins": 30, "img": IMG, "tier": "strong", "rising": True,
                                    "mint": MINT, "sym": "X"}]}
BANNERS = {"ok": True, "as_of": "t", "banners": [{"id": 7, "img": "/api/free-board/img/" + BIMG, "link": "https://x.com/a",
                                                  "title": "Hi", "weight": 2, "w": 600, "h": 100, "clicks": 9}]}
CARD = {"mint": MINT, "sym": "$POP", "name": "Pop", "chain": "SOL", "mcap": "$40K", "pct": 20, "fresh": True,
        "socials": {"x": "https://x.com/p", "tg": "http://t.me/p"}, "ceStep": "strong", "ceStepIndex": 2,
        "ceLine": "Buyers keep coming. 3 sources on it.", "dexPaid": True, "realCrowd": {"real": 1}, "score": 0.9}
FEATURED = {"count": 1, "as_of": "t", "callers": [{"key": "k1", "name": "Caller", "handle": "@c", "tagline": "",
                                                   "count": 1, "recaps": [1], "calls": [
                                                       {"symbol": "POP", "mint": MINT, "date": "Nov 5", "ts": "2026-11-05T10:00:00Z",
                                                        "essence": "see https://evil.x now", "body": "line1\nline2‮<b>",
                                                        "mult": "12.5x", "channel": "secret"}]}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.net = Net()
        self.clock = Clock()
        core._TRANSPORT = self.net
        core._members.clear()
        core._refusal_hold.clear()
        core.HERMES_LIVE = False
        _secret["value"] = None
        kw = dict(clock=self.clock, rand=lambda: 0.0, **core._NEW_PATH)
        core._missed = fc.FeedClient(core._transport, url=fc.MISSED_URL, parse=fc.parse_missed, min_interval_s=30, **kw)
        core._free_pick = fc.FeedClient(core._transport, url=fc.FREE_PICK_URL, parse=fc.parse_free_pick, min_interval_s=30, **kw)
        core._banners = fc.FeedClient(core._transport, url=fc.BANNERS_URL, parse=fc.parse_banners, min_interval_s=300, **kw)
        core._free_history = fc.FeedClient(core._transport, url=fc.FREE_HISTORY_URL, parse=core._parse_free_history,
                                           min_interval_s=core._HISTORY_EVERY_S, gone_on_404=True,
                                           max_bytes=fc.HISTORY_MAX_BYTES, **kw)
        core._images = core._Images(clock=self.clock)
        self.day = ["2026-11-07"]
        core._reveal = core._Reveal(clock=self.clock, day=lambda: self.day[0])

    def tearDown(self):
        core.HERMES_LIVE = SHIPPED    # never leak the kill-switch value into later test files (one shared core)
        _secret["value"] = None

    def live(self):
        core.HERMES_LIVE = True

    def member_entry(self):
        entry = next(iter(core._members.values()))
        for n in ("featured", "history"):
            c = entry[n]
            c._clock, c._next_at = self.clock, -math.inf
        return entry


# ----------------------------------------------------------------------------------------------- 5.7 the gate
class GateTests(Base):
    def test_shipped_state_is_put_back_after_this_file(self):
        """tearDownModule puts back the real module state (taken at import, before any test swapped it)."""
        self.assertIs(_SHIPPED_STATE["_TRANSPORT"], fc.urllib_transport)
        self.assertIs(_SHIPPED_STATE["HERMES_LIVE"], SHIPPED)
        self.assertIsInstance(_SHIPPED_STATE["_images"], core._Images)
        self.assertIsInstance(_SHIPPED_STATE["_missed"], fc.FeedClient)

    def test_gate_is_on_in_this_release(self):
        """The live release: core.py, plugin.src.js and the built plugin.js all carry the switch ON, exactly once, and
        none of them carries it OFF (a release with core.py and the pane apart fails here)."""
        self.assertIs(SHIPPED, True)
        src = (PLUGIN / "core.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("\nHERMES_LIVE = True\n"), 1)
        self.assertEqual(src.count("\nHERMES_LIVE = False\n"), 0)
        js = (PLUGIN.parent / "gen" / "plugin.src.js").read_text(encoding="utf-8")
        self.assertEqual(js.count("\nconst HERMES_LIVE = true\n"), 1)
        self.assertEqual(js.count("\nconst HERMES_LIVE = false\n"), 0)
        built = (PLUGIN / "desktop" / "plugin.js").read_text(encoding="utf-8")
        self.assertEqual(built.count("\nconst HERMES_LIVE = true\n"), 1)
        self.assertEqual(built.count("\nconst HERMES_LIVE = false\n"), 0)

    def test_shipped_switch_asks_the_new_addresses(self):
        """As shipped (no test override): every keyless part and Featured Callers really ask their fixed address, with
        the plugin UA, no query string, the key only on the keyed one, and the live pacing (featured + history + reveal
        cap inside the 60 % share)."""
        core.HERMES_LIVE = SHIPPED
        _secret["value"] = KEY
        self.net.replies[fc.MISSED_URL] = jr(MISSED)
        self.net.replies[fc.FREE_PICK_URL] = jr({"pick": None, "nextInSecs": None})
        self.net.replies[fc.BANNERS_URL] = jr(BANNERS)
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        self.net.replies[fc.FEATURED_URL] = jr(FEATURED)
        self.assertEqual(core.missed()["state"], "fresh")
        self.assertEqual(core.free_pick()["state"], "fresh")
        self.assertEqual(core.banners()["state"], "fresh")
        core.featured()
        self.member_entry()
        self.clock.t += 1
        self.assertEqual(core.featured()["state"], "fresh")
        urls = [c[0] for c in self.net.calls]
        for u in (fc.MISSED_URL, fc.FREE_PICK_URL, fc.BANNERS_URL, fc.ME_URL, fc.FEATURED_URL):
            self.assertIn(u, urls)
        for url, headers, _cap in self.net.calls:
            self.assertEqual(headers["User-Agent"], fc.USER_AGENT)
            self.assertNotIn("?", url)
            self.assertEqual("Authorization" in headers, not url.startswith(fc.BASE + "/api/free-board/"), url)
        entry = next(iter(core._members.values()))
        self.assertEqual(entry["featured"]._min, max(900.0, 6 * 288.0))   # ceil(86400 * (1.5 + 2/6) / (600 - 50)) = 288
        self.assertEqual(entry["history"]._min, max(1200.0, 6 * 288.0))

    def test_no_new_path_is_ever_requested(self):
        """The kill switch (HERMES_LIVE = False, set by setUp): nothing new is asked, not even /me."""
        _secret["value"] = KEY
        for url in NEW_URLS:
            self.net.replies[url] = jr({})
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        for _ in range(3):
            self.clock.t += 5000
            self.assertEqual(core.missed()["state"], "off")
            self.assertEqual(core.free_pick()["state"], "off")
            self.assertEqual(core.banners()["state"], "off")
            self.assertEqual(core.featured()["state"], "off")
            self.assertEqual(core.history("free")["state"], "off")
            self.assertEqual(core.history("gated")["state"], "off")
            self.assertEqual(core.reveal(IMG), {"mint": None, "state": "off"})
            self.assertIsNone(core.image(IMG))
            self.assertEqual(api.missed()["state"], "off")
            self.assertEqual(api.free_pick()["state"], "off")
            self.assertEqual(api.banners()["state"], "off")
            self.assertEqual(api.featured()["state"], "off")
            self.assertEqual(api.history("free")["state"], "off")
            self.assertEqual(api.img(IMG), {"data": None})
            self.assertEqual(api.reveal({"img": IMG}), {"mint": None})
        self.assertEqual(self.net.calls, [])          # not one request, not even /me

    def test_old_pacing_unchanged(self):
        _secret["value"] = KEY
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        self.net.replies[fc.GATED_URL] = jr({"tier": "gated", "signals": []})
        core.board("gated")
        entry = next(iter(core._members.values()))
        self.assertEqual(entry["board"]._min, 216.0)  # kill switch: ceil(86400 * 1.5 / 600) = the pre-live spacing
        self.assertEqual(entry["edge"]._min, 432.0)
        self.assertEqual([c[0] for c in self.net.calls], [fc.ME_URL, fc.GATED_URL])
        self.assertFalse(core._entry_refused(entry))

    def test_status_unchanged(self):
        _secret["value"] = KEY
        self.assertEqual(sorted(core.status()), ["has_key", "key_bad", "key_id", "refused", "version"])


# ----------------------------------------------------------------------------------------------- 5.1 / 5.3 rules
class NewPathRulesTests(Base):
    def test_urls_fixed_no_query_string(self):
        for u in NEW_URLS + (fc.IMG_URL_PREFIX, fc.REVEAL_URL_PREFIX):
            self.assertTrue(u.startswith("https://piquesignal.xyz/api/"), u)
            self.assertNotIn("?", u)
            self.assertNotIn("#", u)
        with self.assertRaises(ValueError):
            fc.FeedClient(self.net, url=fc.MISSED_URL + "?t=1", parse=fc.parse_missed, strict_4xx=True)

    def test_first_call_random_delay_per_path_once(self):
        # the real module-level clients: each waits its own random 0..120 s from start
        fresh = _load("t5_core_fresh", PLUGIN / "core.py")
        now = fresh.time.monotonic()
        waits = [c._next_at - now for c in (fresh._missed, fresh._free_pick, fresh._banners, fresh._free_history)]
        for w in waits:
            self.assertTrue(-5.0 <= w <= 120.0, waits)
        # a client with rand 0.5 waits 60 s, then the floor applies (the delay is not applied again)
        clk = Clock(0.0)
        net = Net()
        net.replies[fc.MISSED_URL] = [jr(MISSED), jr(MISSED)]
        c = fc.FeedClient(net, clock=clk, rand=lambda: 0.5, url=fc.MISSED_URL, parse=fc.parse_missed, min_interval_s=30,
                          **core._NEW_PATH)
        self.assertEqual(c.get()["state"], "loading")
        clk.t = 59.9
        c.get()
        self.assertEqual(net.calls, [])
        clk.t = 60.0
        self.assertEqual(c.get()["state"], "fresh")
        clk.t = 90.0
        self.assertEqual(c.get()["state"], "fresh")
        self.assertEqual(len(net.calls), 2)
        clk2 = Clock(0.0)
        c2 = fc.FeedClient(net, clock=clk2, rand=lambda: 1.0, url=fc.MISSED_URL, parse=fc.parse_missed, first_delay_s=999,
                           strict_4xx=True)
        self.assertEqual(c2._next_at, 120.0)       # capped at 120 s

    def test_keyless_never_sends_key_keyed_always(self):
        self.live()
        _secret["value"] = KEY
        self.net.replies[fc.MISSED_URL] = jr(MISSED)
        self.net.replies[fc.FREE_PICK_URL] = jr({"pick": None, "nextInSecs": None})
        self.net.replies[fc.BANNERS_URL] = jr(BANNERS)
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        self.net.replies[fc.FEATURED_URL] = jr(FEATURED)
        core.missed(); core.free_pick(); core.banners()
        core.featured()
        self.member_entry()
        self.clock.t += 1
        core.featured()
        for url, headers, _cap in self.net.calls:
            self.assertEqual(headers["User-Agent"], fc.USER_AGENT)
            self.assertNotIn("?", url)
            if url.startswith(fc.BASE + "/api/free-board/"):
                self.assertNotIn("Authorization", headers)
                self.assertFalse(any(KEY in str(v) for v in headers.values()))
            else:
                self.assertEqual(headers["Authorization"], "Bearer " + KEY)
        self.assertIn(fc.FEATURED_URL, [c[0] for c in self.net.calls])

    def test_404_stops_15_min_and_hides(self):
        self.live()
        self.net.replies[fc.MISSED_URL] = [jr(MISSED), jr({}, 404), jr(MISSED)]
        self.assertEqual(len(core.missed()["board"]["missed"]), 1)
        self.clock.t += 30
        r = core.missed()
        self.assertEqual(r["error"], "http_404")
        self.assertIsNone(r["board"])                # hidden
        self.assertAlmostEqual(r["retry_in_s"], fc.MAX_BACKOFF_S)
        self.clock.t += fc.MAX_BACKOFF_S - 1
        core.missed()
        self.assertEqual(len(self.net.calls), 2)
        self.clock.t += 1
        core.missed()
        self.assertEqual(len(self.net.calls), 3)

    def test_400_is_never_retried_quickly(self):
        self.live()
        self.net.replies[fc.BANNERS_URL] = jr({}, 400)
        r = core.banners()
        self.assertGreaterEqual(r["retry_in_s"], fc.MAX_BACKOFF_S)

    def test_429_keeps_last_good_and_honours_retry_after(self):
        self.live()
        self.net.replies[fc.MISSED_URL] = [jr(MISSED), jr({}, 429, {"retry-after": "1800"})]
        core.missed()
        self.clock.t += 30
        r = core.missed()
        self.assertEqual(r["state"], "waiting")
        self.assertEqual(len(r["board"]["missed"]), 1)   # the last good data stays
        self.assertGreaterEqual(r["retry_in_s"], 1800)
        self.net.replies[fc.MISSED_URL] = [jr({}, 503, {"retry-after": "99999"})]
        self.clock.t += 1800
        r = core.missed()
        self.assertEqual(r["retry_in_s"], fc.MAX_RETRY_AFTER_S)   # capped at 1 h

    def test_history_404_until_next_start(self):
        self.live()
        self.net.replies[fc.FREE_HISTORY_URL] = jr({}, 404)
        r = core.history("free")
        self.assertEqual(r["state"], "gone")
        for _ in range(5):
            self.clock.t += 100000
            self.assertEqual(core.history("free")["state"], "gone")
        self.assertEqual(len(self.net.calls), 1)
        json.dumps(api.history("free"))               # still valid JSON (no infinity)

    def test_history_floor_20_min_and_once(self):
        self.live()
        self.net.replies[fc.FREE_HISTORY_URL] = [jr({}, 503, {"retry-after": "60"}), jr({}, 500)]
        core.history("free")
        self.clock.t += 61
        core.history("free")
        self.assertEqual(len(self.net.calls), 1)      # an error never shortens the 20-minute floor
        self.clock.t += 1200
        core.history("free")
        self.assertEqual(len(self.net.calls), 2)
        self.assertEqual(self.net.calls[0][2], (fc.HISTORY_MAX_BYTES,))


# ----------------------------------------------------------------------------------------------- pacing (5.3)
class PacingLiveTests(Base):
    def test_featured_in_budget(self):
        self.live()
        _secret["value"] = KEY
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        self.net.replies[fc.FEATURED_URL] = jr(FEATURED)
        core.featured()
        entry = next(iter(core._members.values()))
        # 60 % of 1000 = 600, minus the reveals' own daily cap (10 % of the limit, at most 50) = 550
        self.assertEqual(core._reveal_cap(1000), 50)
        board_s = max(60.0, math.ceil(86400.0 * (1.5 + 2.0 / 6) / (600 - 50)))
        self.assertEqual(entry["board"]._min, board_s)
        self.assertEqual(entry["edge"]._min, 2 * board_s)
        self.assertEqual(entry["featured"]._min, max(900.0, 6 * board_s))
        self.assertEqual(entry["history"]._min, max(1200.0, 6 * board_s))
        per_day = (86400 / board_s + 86400 / (2 * board_s) + 86400 / max(900.0, 6 * board_s)
                   + 86400 / max(1200.0, 6 * board_s) + core._reveal_cap(1000))
        self.assertLessEqual(per_day, 0.6 * 1000)
        # every charged read (board + edge + featured + the member history at its worst-case rate) <= 60 % of the limit
        for limit in (50, 100, 150, 200, 500, 5000, 100000):
            entry["paced_limit"] = None
            entry["me"]._board = {"daily_limit": limit}
            entry["me"]._next_at = math.inf
            core._pace(entry)
            b = entry["board"]._min
            calls = (86400 / b + 86400 / (2 * b) + 86400 / entry["featured"]._min + 86400 / entry["history"]._min
                     + core._reveal_cap(limit))
            self.assertLessEqual(calls, 0.6 * limit + 1e-9, limit)
            self.assertGreaterEqual(entry["history"]._min, 1200.0)

    def test_unknown_limit_featured_hourly(self):
        self.live()
        _secret["value"] = KEY
        core.featured()                               # /me fails (no reply)
        entry = next(iter(core._members.values()))
        self.assertEqual(entry["featured"]._min, 3600.0)
        self.assertEqual(entry["board"]._min, core._UNKNOWN_LIMIT_S)
        self.assertEqual(entry["history"]._min, 3600.0)

    def test_featured_403_hides_only_featured(self):
        """A 403 on Featured Callers (a key with the board but not that part) hides only Featured
        Callers; the key is not "refused" (only the member board and /me decide that)."""
        self.live()
        _secret["value"] = KEY
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        self.net.replies[fc.FEATURED_URL] = jr({}, 403)
        self.net.replies[fc.GATED_URL] = jr({"tier": "gated", "signals": []})
        core.featured()
        entry = self.member_entry()
        r = core.featured()
        self.assertEqual(r["board"], None)
        self.assertEqual(r["error"], "http_403")
        self.assertFalse(core.refused())
        self.assertFalse(core.status()["refused"])
        self.assertEqual(core.board("gated")["state"], "fresh")          # the member board still works
        self.assertNotEqual(core.history("gated")["error"], "http_401")
        self.assertGreaterEqual(entry["featured"].next_at() - self.clock.t, 900)   # featured alone waits 15 min


# ----------------------------------------------------------------------------------------------- cleaners (5.2)
class CleanerTests(unittest.TestCase):
    FUNCS = ("_int_only", "_https", "clean_missed_item", "clean_missed", "_ce_line", "clean_pick_card", "clean_banner",
             "clean_banners", "img_ok")
    CONSTS = ("CT_MAGIC", "LOGO_MAX", "BANNER_MAX", "MISSED_MAX", "BANNERS_MAX", "MISSED_TIERS", "CE_STEPS",
              "PICK_STR_FIELDS", "SOCIAL_KEYS", "IMG_PREFIX")
    RES = ("_LOGO_KEY_RE", "_CE_SOURCE_SUFFIX_RE", "_BANNER_IMG_RE", "_BANNER_LINK_RE", "_SHA12_RE", "_MINT_RE", "_URL_RE")

    @staticmethod
    def _code(fn):
        """The function's syntax tree without its doc text: the plugin copy's doc text names no server file."""
        node = ast.parse(textwrap.dedent(inspect.getsource(fn))).body[0]
        first = node.body[0] if node.body else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
            node.body = node.body[1:]
        return ast.dump(node)

    def test_copies_identical(self):
        for name in self.FUNCS:
            self.assertEqual(self._code(getattr(hc, name)), self._code(getattr(freefeed, name)), name)
        for name in self.CONSTS:
            self.assertEqual(getattr(hc, name), getattr(freefeed, name), name)
        for name in self.RES:
            self.assertEqual(getattr(hc, name).pattern, getattr(freefeed, name).pattern, name)
        for name in ("_num", "_text"):
            self.assertEqual(inspect.getsource(getattr(hc, name)), inspect.getsource(getattr(freefeed, name)), name)
        self.assertEqual(fc.PLACEHOLDER_PNG, freefeed.PLACEHOLDER_PNG)
        self.assertEqual(fc.IMG_KEY_RE.pattern, freefeed._IMG_PATH_RE.pattern.replace("/api/free-board/img/", ""))

    HOSTILE = [None, 1, "x", [], {"gain": True, "ageMins": 1, "tier": "strong"}, {"gain": float("nan"), "ageMins": 1, "tier": "strong"},
               {"gain": 2, "ageMins": True, "tier": "strong"}, {"gain": 2, "ageMins": 1.0, "tier": "strong"},
               {"gain": 2, "ageMins": 1, "tier": "STRONG"}, {"gain": 0.5, "ageMins": 1, "tier": "watch"},
               {"gain": 2, "ageMins": 1, "tier": "solid", "img": "ABCDEF0123456789", "mint": MINT, "sym": "$X", "rising": 1},
               {"gain": 1e7, "ageMins": 1, "tier": "solid"}, {"gain": 2, "ageMins": 10_000_001, "tier": "solid"}]

    def test_missed_hostile_same_as_server(self):
        for it in self.HOSTILE:
            self.assertEqual(hc.clean_missed_item(it), freefeed.clean_missed_item(it))
        out = hc.clean_missed([MISSED["missed"][0]] * 8)
        self.assertEqual(len(out), 5)
        self.assertEqual(sorted(out[0]), ["ageMins", "gain", "img", "rising", "tier"])
        self.assertEqual(hc.clean_missed(self.HOSTILE), freefeed.clean_missed(self.HOSTILE))

    def test_pick_hostile_same_as_server(self):
        cards = [CARD, dict(CARD, chain="ETH"), dict(CARD, mint="bad"), dict(CARD, sym="‮$X"), dict(CARD, pct=True),
                 dict(CARD, pct=1.5), dict(CARD, ceLine="ok. 1 source on it."), dict(CARD, ceLine="ok. 12 sources on it."),
                 dict(CARD, ceLine="2 sources on it. more"), dict(CARD, ceStepIndex=11), dict(CARD, socials={"web": "javascript:x"}),
                 dict(CARD, mcap="<b>"), dict(CARD, name="")]
        for c in cards:
            self.assertEqual(hc.clean_pick_card(c), freefeed.clean_pick_card(c))
        out = hc.clean_pick_card(CARD)
        self.assertEqual(out["socials"], {"x": "https://x.com/p"})
        self.assertEqual(out["ceLine"], "Buyers keep coming.")
        for k in ("dexPaid", "realCrowd", "score"):
            self.assertNotIn(k, out)

    def test_banners_hostile_same_as_server(self):
        bs = [BANNERS["banners"][0], dict(BANNERS["banners"][0], id=8), dict(BANNERS["banners"][0], link="http://x.com"),
              dict(BANNERS["banners"][0], link="javascript:alert(1)"), dict(BANNERS["banners"][0], id=True),
              dict(BANNERS["banners"][0], v="0123456789ab"), dict(BANNERS["banners"][0], weight=float("inf"))]
        for b in bs:
            self.assertEqual(hc.clean_banner(b), freefeed.clean_banner(b))
        out = hc.clean_banner(BANNERS["banners"][0])
        self.assertNotIn("clicks", out)
        self.assertEqual(hc.clean_banners(bs * 3), freefeed.clean_banners(bs * 3))


class ParseTests(unittest.TestCase):
    def test_parse_missed_free_pick_banners(self):
        m = fc.parse_missed(json.dumps(MISSED).encode())
        self.assertEqual(m["missed"], [{"gain": 4.2, "ageMins": 30, "img": IMG, "tier": "strong", "rising": True}])
        with self.assertRaises(ValueError):
            fc.parse_missed(b'{"missed": {}}')
        p = fc.parse_free_pick(json.dumps({"pick": CARD, "nextInSecs": 600}).encode())
        self.assertEqual(p["pick"]["mint"], MINT)
        self.assertEqual(p["nextInSecs"], 600)
        p = fc.parse_free_pick(json.dumps({"pick": CARD, "nextInSecs": True}).encode())
        self.assertIsNone(p["pick"])                  # no valid window => never a pick
        b = fc.parse_banners(json.dumps(BANNERS).encode())
        self.assertEqual(b["banners"][0]["id"], 7)
        with self.assertRaises(ValueError):
            fc.parse_banners(b'{"ok": 1, "banners": []}')

    def test_parse_featured(self):
        f = fc.parse_featured(json.dumps(FEATURED).encode())
        c = f["callers"][0]
        self.assertEqual(sorted(c), ["calls", "count", "handle", "key", "name", "tagline"])
        k = c["calls"][0]
        self.assertEqual(sorted(k), ["body", "date", "essence", "mint", "mult", "symbol", "ts"])
        self.assertNotIn("http", k["essence"])
        self.assertEqual(k["body"], "line1\nline2b")  # line break kept; bidi + markup characters removed
        bad = {"callers": [{"key": "k", "name": "n", "handle": "h", "tagline": "t", "calls": [
            {"symbol": "A", "mint": "bad"}, {"symbol": "B", "mint": MINT, "mult": "12x; drop", "date": "nov 5",
                                             "ts": "yesterday", "essence": 5, "body": None}] * 15}] * 12}
        f = fc.parse_featured(json.dumps(bad).encode())
        self.assertEqual(len(f["callers"]), 10)
        self.assertEqual(len(f["callers"][0]["calls"]), 10)   # first 20 looked at, the bad mints dropped
        k = f["callers"][0]["calls"][0]
        self.assertEqual((k["mult"], k["date"], k["ts"], k["essence"], k["body"]), (None, None, None, "", ""))
        # labels are CLEANED (the server may send any string, cut to 200), a caller is dropped only for an empty key / name
        f = fc.parse_featured(json.dumps({"callers": [{"key": "<>`", "name": "n", "handle": "", "tagline": "", "calls": []},
                                                      {"key": "k", "name": "\u200b", "handle": "", "tagline": "", "calls": []},
                                                      {"key": 5, "name": "n", "handle": "", "tagline": "", "calls": []}]}).encode())
        self.assertEqual(f["callers"], [])
        zwj = "\U0001F468\u200d\U0001F4BB"
        long_name = "N" * 120
        f = fc.parse_featured(json.dumps({"callers": [{"key": "<x>", "name": long_name, "handle": None,
                                                       "tagline": "dev " + zwj + " <b>\u202etxt\n" + "t" * 300,
                                                       "calls": []}]}).encode())
        self.assertEqual(len(f["callers"]), 1)
        c = f["callers"][0]
        self.assertEqual((c["key"], c["name"], c["handle"]), ("x", long_name, ""))
        self.assertTrue(c["tagline"].startswith("dev \U0001F468\U0001F4BB btxt"))
        self.assertEqual(len(c["tagline"]), 200)
        for v in (c["key"], c["name"], c["handle"], c["tagline"]):
            self.assertFalse(any(ch in "<>`\n\u200d\u202e" for ch in v))

    def test_parse_reveal(self):
        self.assertEqual(fc.parse_reveal(json.dumps({"mint": MINT, "sym": "$A", "name": "A", "chain": "SOL", "x": 1}).encode()),
                         {"mint": MINT, "sym": "$A", "name": "A"})
        self.assertIsNone(fc.parse_reveal(b'{"mint": null}')["mint"])
        self.assertIsNone(fc.parse_reveal(b'{"mint": "javascript:x"}')["mint"])

    def test_parse_image(self):
        ok = fc.parse_image(IMG, 200, {"content-type": "image/png"}, PNG)
        self.assertTrue(ok.startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(ok.split(",", 1)[1]), PNG)
        self.assertTrue(fc.parse_image(BIMG, 200, {"content-type": "image/jpeg"}, JPG).startswith("data:image/jpeg;base64,"))
        self.assertTrue(fc.parse_image(BIMG, 200, {"content-type": "image/webp"}, WEBP).startswith("data:image/webp;base64,"))
        for args in [(IMG, 200, {"content-type": "image/jpeg"}, JPG),                 # a logo must be PNG
                     (IMG, 200, {"content-type": "image/png"}, PNG + b"\x00" * 65536),  # logo cap
                     (BIMG, 200, {"content-type": "image/png"}, JPG),                 # magic mismatch
                     (BIMG, 200, {"content-type": "image/svg+xml"}, b"<svg/>"),
                     (BIMG, 200, {"content-type": "image/gif"}, b"GIF89a"),
                     (BIMG, 404, {"content-type": "image/png"}, PNG),
                     (IMG, 200, {"content-type": "image/png"}, fc.PLACEHOLDER_PNG),    # placeholder => None
                     ("../x", 200, {"content-type": "image/png"}, PNG)]:
            self.assertIsNone(fc.parse_image(*args), args[:2])
        self.assertEqual(fc.image_cap(IMG), 65536)
        self.assertEqual(fc.image_cap(BIMG), 2_000_000)

    def test_transport_byte_cap_stops_reading(self):
        class Resp:
            status = 200
            headers = {}

            def __init__(self):
                self.read_total = 0

            def read(self, n):
                self.read_total += n
                return b"x" * n

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        resp = Resp()
        old = fc._OPENER
        fc._OPENER = types.SimpleNamespace(open=lambda req, timeout: resp)
        try:
            with self.assertRaises(ValueError):
                fc.urllib_transport(fc.IMG_URL_PREFIX + IMG, {}, 5, 65536)
        finally:
            fc._OPENER = old
        self.assertLessEqual(resp.read_total, 65537)


# ----------------------------------------------------------------------------------------------- free pick ageing
class FreePickTests(Base):
    def test_window_ages_and_never_stale(self):
        self.live()
        self.net.replies[fc.FREE_PICK_URL] = jr({"as_of": "t", "pick": CARD, "nextInSecs": 100})
        real = fc.time.monotonic                   # a fixed stamp: got + 40 / + 100 are exact in floating point
        fc.time.monotonic = lambda: 5000.5         # (a real clock just below a power of two seconds rounds them)
        try:
            r = core.free_pick(now=0.0)
        finally:
            fc.time.monotonic = real
        got = core._free_pick.last()["got"]
        self.assertEqual(got, 5000.5)
        r = core.free_pick(now=got + 40)
        self.assertEqual(r["board"]["nextInSecs"], 60)
        self.assertEqual(r["board"]["pick"]["mint"], MINT)
        r = core.free_pick(now=got + 100)
        self.assertEqual(r["board"], {"pick": None, "nextInSecs": None})


# ----------------------------------------------------------------------------------------------- images
class ImageTests(Base):
    def test_only_referenced_keys_rate_limited_cached(self):
        self.live()
        self.net.replies[fc.MISSED_URL] = jr({"missed": [dict(MISSED["missed"][0], img=k) for k in
                                                         ("0" * 16, "1" * 16, "2" * 16, "3" * 16)]})
        self.net.replies[fc.BANNERS_URL] = jr(BANNERS)
        core.missed(); core.banners()
        n0 = len(self.net.calls)
        self.assertIsNone(core.image("f" * 16))       # not referenced: never requested
        self.assertIsNone(api.img("b8-0123456789ab")["data"])
        self.assertEqual(len(self.net.calls), n0)
        for k in ("0" * 16, "1" * 16, "2" * 16):
            self.net.replies[fc.IMG_URL_PREFIX + k] = (200, {"content-type": "image/png"}, PNG)
        self.assertTrue(core.image("0" * 16).startswith("data:image/png;base64,"))
        self.assertTrue(core.image("1" * 16))
        self.assertIsNone(core.image("2" * 16))       # a 3rd request within 10 s: not now
        self.assertEqual(len(self.net.calls), n0 + 2)
        self.assertEqual(self.net.calls[-1][2], (65536,))
        self.assertTrue(core.image("0" * 16))         # held: never asked again within 600 s
        self.assertEqual(len(self.net.calls), n0 + 2)
        self.clock.t += 10
        self.assertTrue(core.image("2" * 16))
        self.clock.t += 601
        core.image("0" * 16)
        self.assertEqual(len(self.net.calls), n0 + 4)  # a logo is refreshed after 600 s
        self.net.replies[fc.IMG_URL_PREFIX + BIMG] = (200, {"content-type": "image/jpeg"}, JPG)
        self.clock.t += 10
        self.assertTrue(core.image(BIMG).startswith("data:image/jpeg"))
        self.assertEqual(self.net.calls[-1][2], (2_000_000,))
        for url, headers, _ in self.net.calls:
            self.assertNotIn("Authorization", headers)

    def test_placeholder_and_bad_answers_none_and_4xx_stop(self):
        self.live()
        self.net.replies[fc.MISSED_URL] = jr(MISSED)
        core.missed()
        self.net.replies[fc.IMG_URL_PREFIX + IMG] = (200, {"content-type": "image/png"}, fc.PLACEHOLDER_PNG)
        self.assertIsNone(core.image(IMG))
        n = len(self.net.calls)
        self.clock.t += 20
        self.assertIsNone(core.image(IMG))            # a failed key is not asked again for 10 min
        self.assertEqual(len(self.net.calls), n)
        self.clock.t += 600
        self.net.replies[fc.IMG_URL_PREFIX + IMG] = jr({}, 403)
        self.assertIsNone(core.image(IMG))
        self.clock.t += 700
        self.assertIsNone(core.image(IMG))
        self.assertEqual(len(self.net.calls), n + 1)  # 4xx: no picture request for 15 min

    def _many_keys(self, n=5):
        keys = [format(i, "x") * 16 for i in range(n)]
        self.net.replies[fc.MISSED_URL] = jr({"missed": [dict(MISSED["missed"][0], img=k) for k in keys]})
        core.missed()
        self.assertEqual(core._images.allowed(), set(keys))
        return keys

    def test_5xx_and_3xx_grow_the_wait_and_a_200_resets_it(self):
        """A failing free-feed (502 / 500 / 504 / an unfollowed 3xx) is never asked again quickly: 30 s, 60 s, 120 s ...
        no picture request inside the window (any key); the failed key is held 10 min; a 200 resets the wait."""
        self.live()
        keys = self._many_keys()
        n0 = len(self.net.calls)
        for k, st in zip(keys, (502, 500, 504, 302)):
            self.net.replies[fc.IMG_URL_PREFIX + k] = jr({}, st)
        waits = []
        for i, k in enumerate(keys[:4]):
            self.assertIsNone(core.image(k))
            self.assertEqual(len(self.net.calls), n0 + i + 1)
            stop = core._images._stop_until - self.clock.t
            waits.append(stop)
            self.clock.t += stop - 1                 # just inside the window: nothing asked, for any key
            for kk in keys:
                self.assertIsNone(core.image(kk))
            self.assertEqual(len(self.net.calls), n0 + i + 1)
            self.clock.t += 1
        self.assertEqual(waits, [30.0, 60.0, 120.0, 240.0])
        self.assertIsNone(core.image(keys[0]))       # the 502 key: held 10 min (a cached failure), not asked again
        self.assertEqual(len(self.net.calls), n0 + 4)
        self.net.replies[fc.IMG_URL_PREFIX + keys[4]] = (200, {"content-type": "image/png"}, PNG)
        self.assertTrue(core.image(keys[4]))
        self.assertEqual(core._images._fail, 0)
        self.clock.t += 10
        core._images._cache.pop(keys[1])
        self.net.replies[fc.IMG_URL_PREFIX + keys[1]] = jr({}, 502)
        self.assertIsNone(core.image(keys[1]))
        self.assertEqual(core._images._stop_until - self.clock.t, 30.0)   # back to the first step after a 200

    def test_growing_wait_is_capped_at_15_min(self):
        self.live()
        keys = self._many_keys()
        img = core._images
        url = fc.IMG_URL_PREFIX + keys[0]
        self.net.replies[url] = [jr({}, 500) for _ in range(10)]
        waits = []
        for _ in range(10):
            self.clock.t = max(self.clock.t, img._stop_until) + 11
            img._cache.pop(keys[0], None)
            core.image(keys[0])
            waits.append(img._stop_until - self.clock.t)
        self.assertEqual(waits, [30.0, 60.0, 120.0, 240.0, 480.0, 900.0, 900.0, 900.0, 900.0, 900.0])
        self.assertEqual(self.net.replies[url], [])

    def test_429_503_take_the_larger_of_retry_after_and_the_growing_wait(self):
        self.live()
        keys = self._many_keys()
        img = core._images
        self.net.replies[fc.IMG_URL_PREFIX + keys[0]] = jr({}, 503, {"retry-after": "5"})
        core.image(keys[0])
        self.assertEqual(img._stop_until - self.clock.t, 30.0)            # at least 30 s
        self.clock.t += 31
        self.net.replies[fc.IMG_URL_PREFIX + keys[0]] = jr({}, 429, {"retry-after": "300"})
        core.image(keys[0])                                                 # 429 / 503 are not held per key
        self.assertEqual(img._stop_until - self.clock.t, 300.0)           # Retry-After wins over 60 s
        self.clock.t += 301
        self.net.replies[fc.IMG_URL_PREFIX + keys[0]] = jr({}, 503)
        core.image(keys[0])
        self.assertEqual(img._stop_until - self.clock.t, 120.0)           # the growing wait wins (3rd failure)
        self.assertEqual(len([c for c in self.net.calls if c[0].startswith(fc.IMG_URL_PREFIX)]), 3)

    def test_no_answer_also_waits(self):
        self.live()
        keys = self._many_keys()
        self.assertIsNone(core.image(keys[0]))       # no reply set: the fake net raises (a timeout / reset)
        self.assertEqual(core._images._stop_until - self.clock.t, 30.0)
        n = len(self.net.calls)
        self.clock.t += 29
        self.assertIsNone(core.image(keys[1]))
        self.assertEqual(len(self.net.calls), n)

    def test_route_validates_key_first(self):
        self.live()
        for bad in ("0123456789ABCDEF", "0123456789abcdef\n", "b1-0123456789abc", "../etc", ""):
            self.assertEqual(api.img(bad), {"data": None})
        self.assertEqual(self.net.calls, [])


# ----------------------------------------------------------------------------------------------- reveal
class RevealTests(Base):
    def rcalls(self):
        return [c for c in self.net.calls if c[0].startswith(fc.REVEAL_URL_PREFIX)]

    def test_member_only_floor_cache_cap(self):
        self.live()
        self.assertEqual(core.reveal(IMG)["state"], "no_key")
        _secret["value"] = KEY
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        url = fc.REVEAL_URL_PREFIX + IMG
        self.net.replies[url] = jr({"mint": MINT, "sym": "$A", "name": "A", "chain": "SOL"})
        self.assertEqual(api.reveal({"img": IMG}), {"mint": MINT})
        self.assertEqual(self.net.calls[-1][1]["Authorization"], "Bearer " + KEY)
        self.assertEqual(api.reveal({"img": IMG}), {"mint": MINT})   # cached 30 min: no request
        self.assertEqual(len(self.rcalls()), 1)
        other = "f" * 16
        self.net.replies[fc.REVEAL_URL_PREFIX + other] = jr({"mint": None})
        self.assertEqual(core.reveal(other)["state"], "waiting")     # 10 s floor
        self.clock.t += 10
        self.assertEqual(core.reveal(other)["mint"], None)
        self.assertEqual(len(self.rcalls()), 2)
        for bad in ("ABC", "0123456789abcdeg", None, 5):
            self.assertEqual(api.reveal({"img": bad}), {"mint": None})
        self.assertEqual(api.reveal("x"), {"mint": None})
        self.assertEqual(len(self.rcalls()), 2)
        # the daily cap (50 a day, UTC), then a new day
        for i in range(60):
            self.clock.t += 10
            k = "%016x" % (1000 + i)
            self.net.replies[fc.REVEAL_URL_PREFIX + k] = jr({"mint": None})
            core.reveal(k)
        self.assertEqual(len(self.rcalls()), 50)
        self.day[0] = "2026-11-08"
        self.clock.t += 10
        self.net.replies[fc.REVEAL_URL_PREFIX + "e" * 16] = jr({"mint": None})
        core.reveal("e" * 16)
        self.assertEqual(len(self.rcalls()), 51)
        # cache is per key
        self.clock.t += 10
        _secret["value"] = KEY2
        core.reveal(IMG)
        self.assertEqual(self.net.calls[-1][1]["Authorization"], "Bearer " + KEY2)

    def test_4xx_stops_15_min(self):
        self.live()
        _secret["value"] = KEY
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 1000})
        self.net.replies[fc.REVEAL_URL_PREFIX + IMG] = jr({}, 404)
        core.reveal(IMG)
        self.clock.t += 600
        self.assertEqual(core.reveal(IMG)["state"], "waiting")
        self.clock.t += 301
        core.reveal(IMG)
        self.assertEqual(len(self.rcalls()), 2)

    def test_reveal_cap_follows_the_daily_limit(self):
        """Reveals count in the key's 60 % share: 10 % of the limit (at most 50); no /me answer yet =
        no reveal ("waiting", fail closed)."""
        self.assertEqual([core._reveal_cap(x) for x in (100, 300, 1000, 100000)], [10, 30, 50, 50])
        self.assertEqual(core._reveal_cap(None), 50)                       # a key without a daily limit
        self.assertEqual(core._reveal_cap(core._UNKNOWN), 0)
        self.live()
        _secret["value"] = KEY
        self.assertEqual(core.reveal(IMG)["state"], "waiting")            # /me did not answer: unknown limit
        self.assertEqual(self.rcalls(), [])
        core._members.clear()
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 100})
        for i in range(15):
            self.clock.t += 10
            k = "%016x" % (2000 + i)
            self.net.replies[fc.REVEAL_URL_PREFIX + k] = jr({"mint": None})
            core.reveal(k)
        self.assertEqual(len(self.rcalls()), 10)
        core._members.clear()
        self.net.replies[fc.ME_URL] = jr({"daily_limit": 5})                # too small for any reveal: not "waiting"
        self.assertEqual(core.reveal("d" * 16)["state"], "daily_cap")


# ----------------------------------------------------------------------------------------------- history decoder (5.5)
def _free_body(n_frames=3, t0=1_762_500_000):
    live = {MINT: (t0 - 300, 50000.0, ("POP", "Pop", (("x", "https://x.com/p"),)))}
    frames = []
    for i in range(n_frames):
        t = t0 + i * 600
        nums = (t - (t0 - 300), 9000, 50000.0, 60000.0 + i, 20.0, 1000, 10, 5, 3, 12.5, 1.0, 0.5, 100, 1000, 9000)
        frames.append((t, "2026-11-07T00:%02d:00+00:00" % i, ((MINT, nums, "120"),)))
    return free_history.encode_free(tuple(frames), live)[0]


def _gated_body(rows=None, **over):
    d = {"v": 1, "view": "gated", "scope": "board", "as_of": "x", "step_s": 600, "hours": 24, "truncated": False,
         "f": list(fc.HIST_F), "b": list(fc.HIST_B["gated"]),
         "coins": [[MINT, "POP", None, {"x": "https://x.com/p", "evil": 1}], [MINT2, "B", "B", None]],
         "strs": ["Buyers keep coming.", "Padded."],
         "slots": [{"t": 1_762_500_000, "rows": rows if rows is not None else [
             [0] + [1.0] * 15 + ["1120", "strong", 2, 0, [300, 812, 37, "padded", 1, 1]],
             [1] + [None] * 15 + ["0000", None, None, None, None]]}]}
    d.update(over)
    return json.dumps(d).encode()


class HistoryDecodeTests(unittest.TestCase):
    def test_free_reference_body(self):
        h = fc.parse_history(_free_body(), "free")
        self.assertEqual((h["view"], h["scope"]), ("free", "live_coins"))
        self.assertEqual(h["coins"], [[MINT, "POP", "Pop", {"x": "https://x.com/p"}]])
        self.assertEqual(len(h["frames"]), 3)
        row = h["frames"][0]["rows"][0]
        self.assertEqual(len(row), 6)
        self.assertEqual(len(row[1]), 16)
        self.assertEqual(row[1][2], 50000.0)
        self.assertIsNone(row[1][15])
        self.assertEqual(row[2], "1200")              # dex_paid on, fee_rug off, flicker missing, model missing
        self.assertEqual(row[3:], [None, None, None])

    def test_gated_body_cleaned(self):
        h = fc.parse_history(_gated_body(), "gated")
        self.assertEqual(h["coins"][0], [MINT, "POP", None, {"x": "https://x.com/p"}])
        r = h["frames"][0]["rows"][0]
        self.assertEqual(r[2], "1120")
        self.assertEqual((r[3], r[4]), ("strong", "Buyers keep coming."))
        self.assertEqual(r[1][15], 2)
        self.assertEqual(r[5], {"real": 300, "shown": 812, "pct": 37, "tier": "padded", "padded": True, "line": "Padded."})
        self.assertEqual(h["frames"][0]["rows"][1][1], [None] * 16)

    def test_gated_history_source_tail_cut(self):
        # second guard: the board's " N source(s) on it." tail never reaches the panel through the history strs
        h = fc.parse_history(_gated_body(strs=["Buyers keep coming. 3 sources on it. 12 sources on it.",
                                               "Padded. 1 source on it."]), "gated")
        r = h["frames"][0]["rows"][0]
        self.assertEqual(r[4], "Buyers keep coming.")
        self.assertEqual(r[5]["line"], "Padded.")
        h = fc.parse_history(_gated_body(strs=["7 sources on it.", "Padded, sources on it now."]), "gated")
        r = h["frames"][0]["rows"][0]
        self.assertIsNone(r[4])
        self.assertNotIn("line", r[5] or {})

    def test_strict_refusals(self):
        bad = [
            _gated_body(v=2), _gated_body(v=True), _gated_body(view="free"), _gated_body(scope="live_coins"),
            _gated_body(f=list(fc.HIST_F)[:-1]), _gated_body(b=["dex_paid"]), _gated_body(slots=[]),
            _gated_body(rows=[[0] + [1.0] * 15 + ["1120", None, None, None]]),                 # 20 long
            _gated_body(rows=[[5] + [1.0] * 15 + ["1120", None, None, None, None]]),           # coin index out of range
            _gated_body(rows=[[True] + [1.0] * 15 + ["1120", None, None, None, None]]),
            _gated_body(rows=[[0] + [True] + [1.0] * 14 + ["1120", None, None, None, None]]),  # bool as a number
            _gated_body(rows=[[0] + [1.0] * 15 + ["112", None, None, None, None]]),            # 3 flag codes
            _gated_body(rows=[[0] + [1.0] * 15 + ["1129", None, None, None, None]]),
            _gated_body(rows=[[0] + [1.0] * 15 + ["1120", None, None, 9, None]]),              # string index out of range
            _gated_body(rows=[[0] + [1.0] * 15 + ["1120", None, None, None, [1, 2, 3, "x", 1, 7]]]),
            _gated_body(rows=[[0] + [1.0] * 15 + ["1120", None, None, None, [1, 2, 3, "x", True, None]]]),
            _gated_body(strs=[5]),
            json.dumps([1]).encode(), b"not json",
        ]
        for i, body in enumerate(bad):
            with self.assertRaises(ValueError, msg=i):
                fc.parse_history(body, "gated")
        with self.assertRaises(ValueError):
            fc.parse_history(_free_body(), "gated")
        free = json.loads(_free_body())
        free["strs"] = ["x"]
        with self.assertRaises(ValueError):
            fc.parse_history(json.dumps(free).encode(), "free")
        free = json.loads(_free_body())
        free["slots"][0]["rows"][0] = free["slots"][0]["rows"][0] + [None]
        with self.assertRaises(ValueError):
            fc.parse_history(json.dumps(free).encode(), "free")
        nan = _gated_body().replace(b"[0, 1.0,", b"[0, NaN,", 1)
        with self.assertRaises(ValueError):
            fc.parse_history(nan, "gated")
        with self.assertRaises(ValueError):
            fc.parse_history(b" " * (fc.HISTORY_MAX_BYTES + 1), "free")

    def test_free_never_member_reads(self):
        # a free body never carries member reads; even if a coin's meta tried, the free cleaner keeps board fields only
        h = fc.parse_history(_free_body(144), "free")
        self.assertEqual(len(h["frames"]), 144)
        for f in h["frames"]:
            for r in f["rows"]:
                self.assertEqual((r[3], r[4], r[5]), (None, None, None))
                self.assertEqual(r[2][3], "0")

    def test_rw_layout_matches_the_pane(self):
        js = (PLUGIN.parent / "gen" / "plugin.src.js").read_text(encoding="utf-8")
        nums = js.split("const RW_NUMS = [", 1)[1].split("]", 1)[0]
        bools = js.split("const RW_BOOLS = [", 1)[1].split("]", 1)[0]
        self.assertEqual(tuple(x.strip().strip("'") for x in nums.replace("\n", "").split(",")), fc.RW_NUMS)
        self.assertEqual(tuple(x.strip().strip("'") for x in bools.split(",")), fc.RW_BOOLS)


class HistoryCoreTests(Base):
    def test_member_history_handed_out_once_with_key_id(self):
        self.live()
        _secret["value"] = KEY
        self.net.replies[fc.HISTORY_URL] = jr(json.loads(_gated_body()))
        core.history("gated")                         # makes the entry (its first call waits)
        self.member_entry()
        r = core.history("gated")
        self.assertEqual(r["state"], "fresh")
        self.assertEqual(r["key_id"], core.key_id(KEY))
        self.assertEqual(len(r["board"]["frames"]), 1)
        self.assertEqual(self.net.calls[-1][1]["Authorization"], "Bearer " + KEY)
        r = core.history("gated")
        self.assertIsNone(r["board"])                 # handed out once; memory dropped
        self.assertEqual(len([c for c in self.net.calls if c[0] == fc.HISTORY_URL]), 1)

    def test_key_change_mid_flight_drops_rows(self):
        self.live()
        _secret["value"] = KEY
        core.history("gated")
        entry = self.member_entry()

        def swap(url, headers, timeout, *cap):
            _secret["value"] = KEY2                   # the key changes while the answer is on its way
            return jr(json.loads(_gated_body()))
        core._TRANSPORT = swap
        r = core.history("gated")
        self.assertIsNone(r["board"])

    def test_free_history_keyless(self):
        self.live()
        _secret["value"] = KEY
        self.net.replies[fc.FREE_HISTORY_URL] = (200, {}, _free_body())
        r = core.history("free")
        self.assertEqual(len(r["board"]["frames"]), 3)
        self.assertNotIn("Authorization", self.net.calls[0][1])
        self.assertNotIn("key_id", r)


if __name__ == "__main__":
    unittest.main()
