"""Tests for the plugin's network client (feed_client.py): fake clock + fake transport (no network).
Ported from panel/test_freeboard_client.py (the free-board back-off), plus the server-cleaner equivalence check."""
import importlib.util
import json
import os
import sys
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
sys.path.insert(0, str(PLUGIN.parents[1] / "freefeed"))
import freefeed  # noqa: E402  (the server, for the cleaner equivalence test)


def _load(name):
    spec = importlib.util.spec_from_file_location("t_" + name, PLUGIN / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fc = _load("feed_client")
rowclean = _load("rowclean")

MINT = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"
BOARD = {"as_of": "2026-11-05T14:00:00+00:00", "count": 1, "signals": [
    {"mint": MINT, "symbol": "POPCAT", "fee_rug": True, "top_10_holder_pct": None, "website_url": "javascript:x",
     "socials": {"x": "https://x.com/p", "tg": "javascript:y"}, "score": 0.9, "read_state": "climbing",
     "current_mcap": 1e5}]}


class Clock:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


class Net:
    def __init__(self):
        self.calls = 0
        self.replies = []

    def __call__(self, url, headers, timeout):
        self.calls += 1
        assert url == fc.URL and headers["User-Agent"] == fc.USER_AGENT and timeout == fc.TIMEOUT_S
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def ok():
    return 200, {}, json.dumps(BOARD).encode()


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.net = Clock(), Net()
        self.c = fc.FreeBoardClient(self.net, clock=self.clock, rand=lambda: 0.0)

    def test_success_then_no_request_before_30s(self):
        self.net.replies = [ok(), ok()]
        r = self.c.get()
        self.assertEqual(r["state"], "fresh")
        s = r["board"]["signals"][0]
        for k in ("score", "read_state", "website_url"):
            self.assertNotIn(k, s)
        self.assertEqual(s["socials"], {"x": "https://x.com/p"})
        self.assertIsNone(s.get("top_10_holder_pct"))
        for _ in range(20):
            self.clock.t += 1
            self.assertEqual(self.c.get()["state"], "cached")
        self.assertEqual(self.net.calls, 1)
        self.clock.t += 10                       # 30 s after the success
        self.assertEqual(self.c.get()["state"], "fresh")
        self.assertEqual(self.net.calls, 2)

    def test_429_honours_retry_after_and_backoff_grows(self):
        self.net.replies = [ok(), (429, {"retry-after": "60"}, b""), (429, {"retry-after": "5"}, b""),
                            (429, {}, b""), ok()]
        self.c.get()
        self.clock.t += 30
        r = self.c.get()                         # 1st 429: max(backoff 30, Retry-After 60) = 60
        self.assertEqual((r["state"], r["retry_in_s"]), ("waiting", 60.0))
        self.assertIsNotNone(r["board"])         # last good board still shown
        self.clock.t += 59
        self.c.get()
        self.assertEqual(self.net.calls, 2)      # no request while waiting
        self.clock.t += 1
        r = self.c.get()                         # 2nd 429: backoff 60 beats Retry-After 5
        self.assertEqual(r["retry_in_s"], 60.0)
        self.clock.t += 60
        r = self.c.get()                         # 3rd 429, no header: backoff 120
        self.assertEqual(r["retry_in_s"], 120.0)
        self.clock.t += 120
        self.assertEqual(self.c.get()["state"], "fresh")   # success resets
        self.clock.t += 30
        self.net.replies = [(503, {"retry-after": "10"}, b"")]
        self.assertEqual(self.c.get()["retry_in_s"], 30.0)  # back to the 30 s floor

    def test_backoff_caps_at_15_min_and_retry_after_capped(self):
        self.net.replies = [OSError("down")] * 12 + [(429, {"retry-after": "999999"}, b"")]
        waits = []
        for _ in range(12):
            r = self.c.get()
            waits.append(r["retry_in_s"])
            self.clock.t += r["retry_in_s"]
        self.assertEqual(waits[:6], [30.0, 60.0, 120.0, 240.0, 480.0, 900.0])
        self.assertEqual(max(waits), 900.0)
        r = self.c.get()
        self.assertEqual(r["retry_in_s"], fc.MAX_RETRY_AFTER_S)
        self.assertEqual(r["state"], "error")    # never had a board

    def test_jitter_only_upward(self):
        c = fc.FreeBoardClient(self.net, clock=self.clock, rand=lambda: 0.999)
        self.net.replies = [OSError("x")]
        r = c.get()
        self.assertGreaterEqual(r["retry_in_s"], 30.0)
        self.assertLessEqual(r["retry_in_s"], 36.0)

    def test_bad_json_and_other_status_back_off(self):
        self.net.replies = [(200, {}, b"not json"), (500, {}, b""), (302, {"location": "https://evil"}, b""),
                            (200, {}, json.dumps({"signals": "x"}).encode())]
        for expected in (30.0, 60.0, 120.0, 240.0):
            r = self.c.get()
            self.assertEqual((r["state"], r["retry_in_s"]), ("error", expected))
            self.clock.t += expected
        self.assertEqual(self.net.calls, 4)

    def test_too_big_rejected(self):
        self.net.replies = [(200, {}, b" " * (fc.MAX_BYTES + 1))]
        self.assertEqual(self.c.get()["error"], "ValueError")

    def test_one_request_at_a_time(self):
        started, release = threading.Event(), threading.Event()

        def slow(url, headers, timeout):
            started.set()
            release.wait(5)
            return ok()
        c = fc.FreeBoardClient(slow, clock=self.clock)
        out = {}
        t = threading.Thread(target=lambda: out.setdefault("r", c.get()))
        t.start()
        self.assertTrue(started.wait(5))
        self.assertEqual(c.get()["state"], "loading")  # second caller does NOT send a request
        release.set()
        t.join(5)
        self.assertEqual(out["r"]["state"], "fresh")

    def test_retry_after_parsing(self):
        self.assertEqual(fc.parse_retry_after("120"), 120.0)
        self.assertIsNone(fc.parse_retry_after("soon"))
        self.assertIsNone(fc.parse_retry_after(None))
        self.assertEqual(fc.parse_retry_after("Thu, 05 Nov 2026 15:01:00 GMT", now_epoch=1793890800.0), 60.0)

    def test_transport_https_only(self):
        with self.assertRaises(ValueError):
            fc.urllib_transport("http://piquesignal.xyz/api/free-board", {}, 1)


    def test_unicode_digit_retry_after_keeps_backoff(self):
        self.net.replies = [(429, {"retry-after": chr(0xB2)}, b"")] * 3
        r = self.c.get()
        self.assertEqual((r["state"], r["retry_in_s"]), ("error", 30.0))
        for _ in range(5):
            self.c.get()
        self.assertEqual(self.net.calls, 1)              # no hammering

    def test_base_exception_clears_busy_and_keeps_floor(self):
        def boom(url, headers, timeout):
            raise KeyboardInterrupt
        c = fc.FreeBoardClient(boom, clock=self.clock, rand=lambda: 0.0)
        with self.assertRaises(KeyboardInterrupt):
            c.get()
        self.assertFalse(c._busy)
        self.assertGreaterEqual(c.get()["retry_in_s"], 30.0)

    def test_hostile_rows_cleaned_like_server(self):
        rows = [
            {"mint": MINT, "name": "<img src=x onerror=alert(1)>" + chr(0x202E), "website_url": 'https://a" onclick=x',
             "top_10_holder_pct": 55.5, "symbol": "OK", "holders": "12", "chain": "SOL!", "score": 1},
            {"mint": "x" * 400, "symbol": "NOMINT"},
            {"mint": MINT, "socials": {"x": "javascript:alert(1)", "tg": "@ok"}, "twitter_handle": "https://x.com/a b"},
        ]
        mine = [fc.clean_row(r) for r in rows]
        self.assertEqual(mine, [freefeed.clean_row(r) for r in rows])   # identical to the server's cleaner
        self.assertEqual(mine[0], {"mint": MINT, "symbol": "OK", "top_10_holder_pct": 55.5})
        self.assertIsNone(mine[1])
        self.assertEqual(mine[2], {"mint": MINT, "socials": {"tg": "@ok"}})

    def test_rowclean_is_exact_copy_of_server_cleaner(self):
        import inspect
        for name in ("_num", "_text", "_url", "_social", "clean_row"):
            self.assertEqual(inspect.getsource(getattr(rowclean, name)), inspect.getsource(getattr(freefeed, name)))
        for name in ("NUM_FIELDS", "BOOL_FIELDS", "TEXT_FIELDS", "URL_FIELDS", "FREE_FIELDS", "SOCIAL_KEYS",
                     "BLANKED_FIELDS", "_BAD_CATEGORIES", "_BAD_CHARS", "_MAX_ABS_NUM"):
            self.assertEqual(getattr(rowclean, name), getattr(freefeed, name), name)
        for name in ("_MINT_RE", "_HANDLE_RE", "_SOCIAL_HANDLE_RE", "_CHAIN_RE", "_URL_RE"):
            self.assertEqual(getattr(rowclean, name).pattern, getattr(freefeed, name).pattern, name)

    def test_total_deadline_stops_trickling_body(self):
        clock = Clock()

        class Resp:
            status = 200
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def read1(self, n):                  # what the transport uses: at most ONE socket read
                clock.t += 4                     # 4 s per socket read
                return b"x"

            def read(self, n):                   # a real read(n) waits for all n bytes: never used for the body
                raise AssertionError("read(n) would wait for the whole chunk")

        class Opener:
            def open(self, req, timeout):
                return Resp()
        orig = fc._OPENER
        fc._OPENER = Opener()
        try:
            with self.assertRaises(TimeoutError):
                fc.urllib_transport(fc.URL, {}, 1, clock=clock)
        finally:
            fc._OPENER = orig

    def test_total_deadline_stops_a_real_dripping_socket(self):
        """A real HTTP response that drips one byte at a time (each well inside the socket timeout) is
        cut at the total deadline; a plain read(n) would wait for all n bytes. Local socket only (127.0.0.1)."""
        import http.client
        import socket
        import time as _t
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        stop = threading.Event()

        def serve():
            conn, _ = srv.accept()
            try:
                conn.recv(4096)
                conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 1000000\r\n\r\n")
                while not stop.is_set():
                    conn.sendall(b"x")
                    _t.sleep(0.02)
            except OSError:
                pass
            finally:
                conn.close()
        th = threading.Thread(target=serve, daemon=True)
        th.start()

        class Opener:
            def open(self, req, timeout):
                c = http.client.HTTPConnection("127.0.0.1", port, timeout=timeout)
                c.request("GET", "/")
                return c.getresponse()
        orig = (fc._OPENER, fc.TOTAL_DEADLINE_S)
        fc._OPENER, fc.TOTAL_DEADLINE_S = Opener(), 0.5
        t0 = _t.monotonic()
        try:
            with self.assertRaises(TimeoutError):
                fc.urllib_transport(fc.URL, {}, 2)
            self.assertLess(_t.monotonic() - t0, 3.0)
        finally:
            fc._OPENER, fc.TOTAL_DEADLINE_S = orig
            stop.set()
            srv.close()
            th.join(5)

    def test_featured_text_strips_bad_characters_before_urls(self):
        """An invisible character inside a URL cannot hide it from the URL strip."""
        for raw in ("see ht\u200btps://evil.x/a now", "see https\u2060://evil.x now", "see http\u00ad://evil.x now"):
            out = fc._long_text(raw, 150)
            self.assertNotIn("evil.x", out, raw)
            self.assertNotIn("://", out, raw)
        self.assertEqual(fc._long_text("line1\nline2", 150), "line1\nline2")


if __name__ == "__main__":
    unittest.main(verbosity=2)
