"""Tests for the member (gated) side and the backend routes: gatedclean.py, feed_client parse_*, the no-key / bad-key
paths, daily-limit pacing and dashboard/plugin_api.py with a fake secret store + fake network (no real network)."""
import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
MINT = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"
MINT2 = "So11111111111111111111111111111111111111112"
KEY = "pqs_TESTKEY_0123456789abcdef"


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fc = _load("t2_feed_client", PLUGIN / "feed_client.py")
gc = _load("t2_gatedclean", PLUGIN / "gatedclean.py")

# fake Hermes secret store
# one fake store shared by every test file in the same run
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

api = _load("t2_plugin_api", PLUGIN / "dashboard" / "plugin_api.py")

GATED_ROW = {"mint": MINT, "symbol": "POPCAT", "name": "Popcat", "pct": 140, "current_mcap": 120000.0,
             "read_state": "climbing", "ce_step": "strong", "ce_step_index": 2, "ce_line": "Buyers keep coming.",
             "real_crowd": {"real": 300, "shown": 812, "pct": 37, "tier": "borderline", "padded": False, "line": "ok",
                            "evil": "x"},
             "model_approved": True, "score": 0.91, "sig_count": 4, "social_buzz": True, "flash_point": True,
             "stacked": True, "bail": True, "top_holders": [1], "verdict": "x", "fee_rug": True}


class Net:
    def __init__(self):
        self.calls = []
        self.replies = {}

    def __call__(self, url, headers, timeout):
        self.calls.append((url, dict(headers)))
        r = self.replies.get(url.split("?")[0])
        if r is None:
            raise OSError("no reply")
        return r


class GatedCleanTests(unittest.TestCase):
    def test_gated_row_keeps_reads_drops_sources(self):
        out = gc.clean_gated_row(dict(GATED_ROW))
        for k in ("score", "sig_count", "social_buzz", "flash_point", "stacked", "bail", "top_holders", "verdict"):
            self.assertNotIn(k, out)
        self.assertEqual(out["read_state"], "climbing")
        self.assertEqual(out["ce_step"], "strong")
        self.assertEqual(out["ce_step_index"], 2)
        self.assertEqual(out["real_crowd"], {"real": 300, "shown": 812, "pct": 37, "tier": "borderline",
                                             "padded": False, "line": "ok"})
        self.assertIs(out["model_approved"], True)
        self.assertIs(out["fee_rug"], True)

    def test_gated_bad_values_dropped(self):
        row = {**GATED_ROW, "read_state": "moon", "ce_step": "<b>", "ce_step_index": 9, "ce_line": "a" + chr(0x202E),
               "real_crowd": {"real": -1, "shown": "812", "tier": "x"}, "model_approved": "yes"}
        out = gc.clean_gated_row(row)
        for k in ("read_state", "ce_step", "ce_step_index", "ce_line", "real_crowd", "model_approved"):
            self.assertNotIn(k, out, k)

    def test_gated_source_tail_cut(self):
        # live member feed, second guard: the " N source(s) on it." tail is cut (repeated) or the line dropped
        row = {**GATED_ROW, "ce_line": "Buyers keep coming. 2 sources on it. 1 source on it.",
               "real_crowd": {**GATED_ROW["real_crowd"], "line": "ok 40 sources on it."}}
        out = gc.clean_gated_row(row)
        self.assertEqual(out["ce_line"], "Buyers keep coming.")
        self.assertEqual(out["real_crowd"]["line"], "ok")
        for bad in (" 3 sources on it.", "5 sources on it.", "x sources on it here", "x 1 source on it. "):
            out = gc.clean_gated_row({**GATED_ROW, "ce_line": bad, "real_crowd": {**GATED_ROW["real_crowd"], "line": bad}})
            self.assertNotIn("ce_line", out, bad)
            self.assertNotIn("line", out["real_crowd"], bad)

    def test_edge_row(self):
        row = {"mint": MINT, "symbol": "EE", "name": "Edge", "smart_wallets": 7, "tier": 2, "backed": True,
               "green_flag": False, "committed": True, "wallets": ["w1"], "dump": True, "ageMin": 3}
        self.assertEqual(gc.clean_edge_row(row), {"mint": MINT, "symbol": "EE", "name": "Edge", "smart_wallets": 7,
                                                  "tier": 2, "backed": True, "green_flag": False, "committed": True})
        self.assertIsNone(gc.clean_edge_row({"mint": "bad"}))
        self.assertNotIn("smart_wallets", gc.clean_edge_row({"mint": MINT, "smart_wallets": True}))


class ParseTests(unittest.TestCase):
    def test_parse_gated_edge_me(self):
        g = fc.parse_gated(json.dumps({"tier": "gated", "count": 1, "as_of": "t", "signals": [GATED_ROW]}).encode())
        self.assertEqual((g["tier"], g["count"]), ("gated", 1))
        e = fc.parse_edge(json.dumps({"count": 1, "as_of": "t", "signals": [{"mint": MINT, "smart_wallets": 3}]}).encode())
        self.assertEqual(e["coins"], [{"mint": MINT, "smart_wallets": 3}])
        m = fc.parse_me(json.dumps({"tier": "gated", "daily_limit": 5000, "daily_used": True, "x": 1}).encode())
        self.assertEqual(m, {"tier": "gated", "daily_limit": 5000, "daily_used": None})
        with self.assertRaises(ValueError):
            fc.parse_edge(json.dumps({"coins": []}).encode())

    def test_url_guard(self):
        with self.assertRaises(ValueError):
            fc.FeedClient(url="https://evil.example/api")
        with self.assertRaises(ValueError):
            fc.FeedClient(url="http://piquesignal.xyz/api/free-board")


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class AuthTests(unittest.TestCase):
    def test_no_key_never_requests(self):
        net = Net()
        c = fc.FeedClient(net, url=fc.GATED_URL, parse=fc.parse_gated, auth=lambda: None)
        self.assertEqual(c.get()["state"], "no_key")
        self.assertEqual(net.calls, [])

    def test_401_waits_15_min(self):
        net, clock = Net(), Clock()
        net.replies[fc.GATED_URL.split("?")[0]] = (401, {}, b"")
        c = fc.FeedClient(net, clock=clock, rand=lambda: 0.0, url=fc.GATED_URL, parse=fc.parse_gated,
                          auth=lambda: {"Authorization": "Bearer " + KEY}, min_interval_s=60)
        r = c.get()
        self.assertEqual((r["state"], r["retry_in_s"], r["error"]), ("error", fc.MAX_BACKOFF_S, "http_401"))
        clock.t += 899
        c.get()
        self.assertEqual(len(net.calls), 1)

    def test_member_floor_at_least_min(self):
        c = fc.FeedClient(Net(), url=fc.GATED_URL, min_interval_s=5)
        self.assertEqual(c._min, fc.MIN_INTERVAL_S)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.net = Net()
        api.core._TRANSPORT = self.net
        api.core._members.clear()
        api.core._refusal_hold.clear()
        api.core._free = api.core.fc.FeedClient(api.core._transport, url=api.core.fc.FREE_URL, parse=api.core.fc.parse_board)
        _secret["value"] = None

    def test_status_never_returns_key(self):
        _secret["value"] = KEY
        st = api.status()
        self.assertEqual((st["has_key"], st["version"], len(st["key_id"])), (True, api.VERSION, 12))
        self.assertEqual(set(st), {"has_key", "version", "key_id", "refused", "key_bad"})
        self.assertIs(st["refused"], False)
        self.assertIs(st["key_bad"], False)
        self.assertNotIn(KEY, json.dumps(st))
        self.assertNotIn(st["key_id"], KEY)
        _secret["value"] = "bad key with spaces"
        self.assertFalse(api.status()["has_key"])

    def test_status_key_bad_format_check(self):
        """Unlock with your key, step 3: the SAME format rule as the key itself (_KEY_RE, stripped); only a bool goes out."""
        cases = [(None, False, False), ("", False, False), ("   ", False, False), (KEY, True, False), ("  " + KEY + "\n", True, False),
                 ("bad key with spaces", False, True), ("short", False, True), ("x" * 201, False, True), ("x" * 200, True, False),
                 ("abc$defghijklmnopq", False, True), ("Bearer " + KEY, False, True)]
        for val, has, bad in cases:
            _secret["value"] = val
            st = api.status()
            self.assertEqual((st["has_key"], st["key_bad"]), (has, bad), repr(val))
            self.assertEqual(set(st), {"has_key", "version", "key_id", "refused", "key_bad"})
            if isinstance(val, str) and val.strip():
                self.assertNotIn(val.strip(), json.dumps(st), "the value is never returned")
            self.assertEqual(self.net.calls, [], "status never makes a request")
        _secret["value"] = None

    def test_free_board_no_auth_header(self):
        self.net.replies[api.core.fc.FREE_URL] = (200, {}, json.dumps({"as_of": "t", "count": 1, "signals": [
            {"mint": MINT, "symbol": "A", "read_state": "climbing", "score": 1}]}).encode())
        _secret["value"] = KEY
        r = api.board(view="free")
        self.assertEqual(r["state"], "fresh")
        self.assertEqual(r["board"]["signals"], [{"mint": MINT, "symbol": "A"}])
        url, headers = self.net.calls[0]
        self.assertNotIn("Authorization", headers)
        self.assertEqual(headers["User-Agent"], api.core.fc.USER_AGENT)

    def test_gated_without_key(self):
        r = api.board(view="gated")
        self.assertEqual(r["state"], "no_key")
        self.assertEqual(api.early_edge()["state"], "no_key")
        self.assertEqual(self.net.calls, [])

    def test_gated_with_key_paces_and_sends_bearer(self):
        _secret["value"] = KEY
        self.net.replies[api.core.fc.ME_URL] = (200, {}, json.dumps({"tier": "gated", "daily_limit": 1000, "daily_used": 3}).encode())
        self.net.replies[api.core.fc.GATED_URL.split("?")[0]] = (200, {}, json.dumps({"tier": "gated", "count": 1, "as_of": "t",
                                                                                  "signals": [GATED_ROW]}).encode())
        r = api.board(view="gated")
        self.assertEqual(r["state"], "fresh")
        self.assertNotIn("score", json.dumps(r))
        self.assertNotIn(KEY, json.dumps(r))
        urls = [u for u, _ in self.net.calls]
        self.assertEqual(urls[0], api.core.fc.ME_URL)
        for u, hd in self.net.calls:
            self.assertEqual(hd["Authorization"], "Bearer " + KEY)
            self.assertTrue(u.startswith("https://piquesignal.xyz/"))
        entry = next(iter(api.core._members.values()))
        # 1000/day * 60 % = 600 calls/day, minus the Missed reveals' own cap (50) = 550; board + edge/2 + Featured
        # Callers/6 + member history/6 = 1.5 + 2/6 per cycle (the live release) => board every >= 288 s
        self.assertIs(api.core.HERMES_LIVE, True)
        self.assertEqual(entry["board"]._min, 288.0)
        self.assertEqual(entry["edge"]._min, 576.0)
        self.assertNotIn(KEY, json.dumps({k: str(v) for k, v in entry.items()}))

    def test_key_change_uses_new_clients_and_old_key_is_not_sent(self):
        _secret["value"] = KEY
        self.net.replies[api.core.fc.ME_URL] = (200, {}, json.dumps({"daily_limit": None}).encode())
        self.net.replies[api.core.fc.GATED_URL.split("?")[0]] = (200, {}, json.dumps({"signals": []}).encode())
        api.board(view="gated")
        _secret["value"] = KEY + "_NEW"
        self.net.calls.clear()
        api.board(view="gated")
        self.assertTrue(self.net.calls)
        for _, hd in self.net.calls:
            self.assertEqual(hd["Authorization"], "Bearer " + KEY + "_NEW")
        self.assertEqual(len(api.core._members), 2)

    def test_member_cache_bounded(self):
        self.net.replies[api.core.fc.ME_URL] = (200, {}, b"{}")
        self.net.replies[api.core.fc.GATED_URL.split("?")[0]] = (200, {}, json.dumps({"signals": []}).encode())
        for i in range(10):
            _secret["value"] = KEY + "_%02d" % i
            api.board(view="gated")
        self.assertLessEqual(len(api.core._members), api.core._MAX_KEYS)

    def test_view_param_only_free_or_gated(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        app = FastAPI()
        app.include_router(api.router)
        r = TestClient(app).get("/board?view=../../etc")
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
