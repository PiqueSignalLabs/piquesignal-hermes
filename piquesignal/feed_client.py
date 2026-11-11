"""PiqueSignal Hermes panel: one polite HTTPS client for every feed the panel reads (free board, member board, member
Early Edge, member /me; and the NEW read-only addresses of the server contract, live in this release (core.py
HERMES_LIVE = True): keyless /api/free-board/missed, /free-pick, /banners, /img/<key> (logo <= 64 KB, banner <= 2 MB,
PNG / JPEG / WebP with matching magic) and /history, keyed /api/pull/featured-callers, /missed-reveal/<id> and
/history; history answers <= 3.2 MB, decoded strictly (wire v1) and re-cleaned row by row). Used
by dashboard/plugin_api.py as SHARED long-lived instances - never one per request, or the floor and the back-off would
do nothing. The desktop pane never calls our server directly.

Rules (polite to the server; error answers are kept rare):
  * never more than one request at a time per feed; never more often than its floor (min 30 s);
  * the floor is recorded BEFORE the request starts, so no error path can skip it;
  * 429 / 503: wait at least what Retry-After says (capped at 1 h) AND at least the growing back-off;
  * any other 4xx (401 / 403 = a bad or unpaid key, 404, 400 ...): stop for 15 min + upward jitter (no quick retry);
  * any other error (network, 5xx, 3xx, bad JSON, too slow): back-off 30 s -> 60 -> ... -> 15 min + upward jitter;
  * a success resets the back-off; while waiting, the last good result is returned, never a new request.
  * the NEW addresses also: a random 0..120 s before the first request (per path, once per start), any 4xx but 429 =
    stop 15 min AND hide the last result, a history 404 = never again until the next start, an error never shortens
    the floor, never a query string (the constructor refuses one).
Security: HTTPS only to fixed piquesignal.xyz URLs, redirects NOT followed, 2 MB cap, hard time limit, every row
re-cleaned (rowclean.py = exact copy of the server's free cleaner; gatedclean.py for member views). A member key is
only ever put in the Authorization header of a request to piquesignal.xyz; it is never logged, returned or stored here.
The pane must render every value as text (never as HTML). Logs carry no data. Stdlib only.
"""

import base64
import email.utils
import importlib.util
import json
import logging
import math
import random
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location("piquesignal_" + name, Path(__file__).resolve().parent / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rowclean = _load_sibling("rowclean")
_gated = _load_sibling("gatedclean")
_hermes = _load_sibling("freepickclean")      # the exact copy of the free-feed's Hermes cleaners (Missed / Free Pick / banners)
clean_row = _rowclean.clean_row

BASE = "https://piquesignal.xyz"
FREE_URL = BASE + "/api/free-board"
GATED_URL = BASE + "/api/pull/feed?limit=200"
EDGE_URL = BASE + "/api/pull/early-edge"
ME_URL = BASE + "/api/pull/me"
# The NEW read-only addresses (fixed, never a query string). Called only while core.HERMES_LIVE (True in this release).
MISSED_URL = BASE + "/api/free-board/missed"
FREE_PICK_URL = BASE + "/api/free-board/free-pick"
BANNERS_URL = BASE + "/api/free-board/banners"
IMG_URL_PREFIX = BASE + "/api/free-board/img/"
FREE_HISTORY_URL = BASE + "/api/free-board/history"
FEATURED_URL = BASE + "/api/pull/featured-callers"
REVEAL_URL_PREFIX = BASE + "/api/pull/missed-reveal/"
HISTORY_URL = BASE + "/api/pull/history"
IMG_KEY_RE = re.compile(r"([0-9a-f]{16}|b[0-9]{1,9}-[0-9a-f]{12})\Z")    # = the free-feed's img route key (1.1)
IMG_ID_RE = re.compile(r"[0-9a-f]{16}\Z")                                # a Missed tile id (= a logo key)
FIRST_CALL_MAX_S = 120.0                   # the first call of a NEW path waits a random 0..120 s after start (5.1)
HISTORY_MAX_BYTES = 3_200_000              # history client byte cap (5.5)
URL = FREE_URL                              # (kept name: the free board)
USER_AGENT = "piquesignal-hermes/1.0"
MIN_INTERVAL_S = 30.0
MAX_BACKOFF_S = 900.0
MAX_RETRY_AFTER_S = 3600.0
TIMEOUT_S = 10.0                           # per socket operation
TOTAL_DEADLINE_S = 15.0                    # body read (checked after every socket read); worst case ~45 s a request
MAX_BYTES = 2_000_000
MAX_ROWS = 500
_CHUNK = 65536
_ALLOWED_PREFIX = BASE + "/"

log = logging.getLogger("piquesignal.feed")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None   # a redirect is returned as an HTTPError (3xx) => treated as an error, never followed


_OPENER = urllib.request.build_opener(_NoRedirect)


def urllib_transport(url, headers, timeout, max_bytes=MAX_BYTES, *, clock=time.monotonic):
    """GET url -> (status, headers_dict_lowercase, body_bytes). Raises on network errors, on a body over max_bytes
    (default MAX_BYTES; reading stops at the cap) and when reading the body takes longer than TOTAL_DEADLINE_S. The
    feeds fetch only https://piquesignal.xyz/...; core.coin_icon_path reuses this for a pop-up's coin picture from
    https://cdn.dexscreener.com/, and Deep Check and the price chart reuse it for https://api.dexscreener.com/ (the
    token pairs) and https://api.geckoterminal.com/ (the pool's candles and trades) (their own fixed URLs, no key). The
    body is read with read1 (at most ONE socket read per call, each
    bounded by the socket timeout), so the deadline is checked after every socket read: a server that drips bytes
    slowly cannot hold the request far past the deadline (a plain read(n) waits for all n bytes)."""
    if not url.startswith("https://"):
        raise ValueError("https only")
    deadline = clock() + TOTAL_DEADLINE_S
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        resp = _OPENER.open(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        resp = e
    with resp:
        status = resp.status if hasattr(resp, "status") else resp.code
        hdrs = {k.lower(): v for k, v in resp.headers.items()}
        parts, size = [], 0
        read = getattr(resp, "read1", None) or resp.read
        while True:
            if clock() > deadline:
                raise TimeoutError("total deadline")
            chunk = read(min(_CHUNK, max_bytes - size + 1))
            if not chunk:
                break
            size += len(chunk)
            if size > max_bytes:
                raise ValueError("too big")
            parts.append(chunk)
    return status, hdrs, b"".join(parts)


def parse_retry_after(value, now_epoch=None):
    """Retry-After as seconds (ASCII delta-seconds or an HTTP date). None when missing/garbage. Never raises."""
    try:
        if value is None:
            return None
        value = str(value).strip()
        if value.isascii() and value.isdigit():
            return float(value)
        dt = email.utils.parsedate_to_datetime(value)
        if dt is None:
            return None
        now_epoch = time.time() if now_epoch is None else now_epoch
        return max(0.0, dt.timestamp() - now_epoch)
    except Exception:
        return None


def _load_json(body):
    if len(body) > MAX_BYTES:
        raise ValueError("too big")
    d = json.loads(body.decode("utf-8"))
    if not isinstance(d, dict):
        raise ValueError("bad shape")
    return d


def _as_of(d):
    v = d.get("as_of")
    return v if isinstance(v, str) and len(v) <= 40 else None


def _rows(d, key, cleaner):
    rows = d.get(key)
    if not isinstance(rows, list):
        raise ValueError("bad shape")
    return [s for s in (cleaner(r) for r in rows[:MAX_ROWS]) if s is not None]


def parse_board(body):
    """Free board bytes -> {"as_of", "count", "signals"}; raises ValueError on anything unexpected."""
    d = _load_json(body)
    signals = _rows(d, "signals", clean_row)
    return {"as_of": _as_of(d), "count": len(signals), "signals": signals}


def parse_gated(body):
    """Member board bytes ({tier, count, as_of, signals[]}) -> {"as_of", "count", "signals", "tier"}."""
    d = _load_json(body)
    signals = _rows(d, "signals", _gated.clean_gated_row)
    return {"as_of": _as_of(d), "count": len(signals), "signals": signals, "tier": _gated.clean_tier(d.get("tier"))}


def parse_edge(body):
    """Member Early Edge bytes ({count, as_of, signals[]}, the member Early Edge feed) -> {"as_of", "count",
    "coins"} (the 8 Early Edge fields only)."""
    d = _load_json(body)
    coins = _rows(d, "signals", _gated.clean_edge_row)
    return {"as_of": _as_of(d), "count": len(coins), "coins": coins}


def parse_me(body):
    """Member /me bytes -> {"tier", "daily_limit", "daily_used"} (numbers only)."""
    d = _load_json(body)

    def _n(v):
        return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 10**9 else None
    return {"tier": _gated.clean_tier(d.get("tier")), "daily_limit": _n(d.get("daily_limit")),
            "daily_used": _n(d.get("daily_used"))}


# ----------------------------------------------------------------------------------------------- the NEW addresses (5.2)
# Every parser re-applies the server's own rules (the panel's second lock). Keyless answers: freepickclean.py = the exact
# copy of the free-feed cleaners. Keyed answers: the member pull API's allow-lists, re-checked here with the panel's
# text rule.
def parse_missed(body):
    """/api/free-board/missed -> {"as_of", "missed": [<= 5 x {gain, ageMins, img?, tier, rising}]} (never a mint)."""
    d = _load_json(body)
    if not isinstance(d.get("missed"), list):
        raise ValueError("bad shape")
    return {"as_of": _as_of(d), "missed": _hermes.clean_missed(d["missed"])}


def _next_in(v):
    return v if isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 86400 else None


def parse_free_pick(body):
    """/api/free-board/free-pick -> {"as_of", "pick": <card or None>, "nextInSecs": <int or None>, "got": <monotonic s>}.
    `got` lets the reader age nextInSecs, so a cached answer never shows a pick after its window ended."""
    d = _load_json(body)
    if "pick" not in d or "nextInSecs" not in d:
        raise ValueError("bad shape")
    pick = _hermes.clean_pick_card(d.get("pick")) if d.get("pick") is not None else None
    nxt = _next_in(d.get("nextInSecs"))
    return {"as_of": _as_of(d), "pick": pick if nxt is not None else None, "nextInSecs": nxt, "got": time.monotonic()}


def parse_banners(body):
    """/api/free-board/banners -> {"ok": True, "as_of", "banners": [<= 5 cleaned]} (no counters, no advertiser data)."""
    d = _load_json(body)
    if d.get("ok") is not True or not isinstance(d.get("banners"), list):
        raise ValueError("bad shape")
    return {"ok": True, "as_of": _as_of(d), "banners": _hermes.clean_banners(d["banners"])}


FEATURED_CALLERS_MAX = 10
FEATURED_CALLS_MAX = 20
ESSENCE_MAX = 150
BODY_MAX = 600
_FEAT_URL_RE = re.compile(r"https?://\S+")                                # = the pull API's 2nd URL guard
_FEAT_MULT_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?x\Z")
_FEAT_DATE_RE = re.compile(r"[A-Z][a-z]{2} [0-9]{1,2}\Z")
_FEAT_TS_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:[+-][0-9]{2}:[0-9]{2}|Z)?\Z")


def _match(v, rx):
    return v if isinstance(v, str) and rx.match(v) else None


def _long_text(v, cap):
    """Telegram text (essence / body): a str, line breaks kept, every other control / format / private-use character
    and < > ` removed FIRST, then URLs stripped again (so an invisible character inside "ht<zero-width>tps://" cannot
    hide a URL from the strip), cut to cap. Never HTML: the pane sets it as text only. Else ""."""
    if not isinstance(v, str):
        return ""
    v = v[:cap * 4].replace("\r\n", "\n")
    out = "".join(ch for ch in v if ch == "\n" or not (ch in _rowclean._BAD_CHARS or
                                                        _rowclean.unicodedata.category(ch) in _rowclean._BAD_CATEGORIES))
    return _FEAT_URL_RE.sub("", out).strip()[:cap]


FEATURED_LABEL_MAX = 200   # = the server's own cut for key / name / handle / tagline


def _label(v, cap=FEATURED_LABEL_MAX):
    """A caller label, CLEANED (never a reason to drop the caller): not a str -> ""; every control / format / private-use
    / line-break character and < > ` removed; trimmed; cut to cap (the server's own cut). Set as text only by the
    pane."""
    if not isinstance(v, str):
        return ""
    v = v[:cap * 4]
    out = "".join(ch for ch in v if not (ch in _rowclean._BAD_CHARS or
                                         _rowclean.unicodedata.category(ch) in _rowclean._BAD_CATEGORIES))
    return out.strip()[:cap]


def parse_featured(body):
    """/api/pull/featured-callers -> {"count", "as_of", "callers": [<= 10 x {key, name, handle, tagline, count,
    calls: [<= 20 x {symbol, mint, date, ts, essence, body, mult}]}]} (contract 0.2). Anything else is dropped."""
    d = _load_json(body)
    if not isinstance(d.get("callers"), list):
        raise ValueError("bad shape")
    callers = []
    for c in d["callers"][:FEATURED_CALLERS_MAX]:
        if not isinstance(c, dict) or not isinstance(c.get("calls"), list):
            continue
        key, name, handle, tagline = _label(c.get("key")), _label(c.get("name")), _label(c.get("handle")), _label(c.get("tagline"))
        if not key or not name:                    # any string may come: labels are cleaned, a caller is dropped only
            continue                               # when its key or name is empty after cleaning
        calls = []
        for x in c["calls"][:FEATURED_CALLS_MAX]:
            if not isinstance(x, dict):
                continue
            mint, sym = x.get("mint"), _rowclean._text(x.get("symbol"), 64)
            if not (isinstance(mint, str) and _rowclean._MINT_RE.fullmatch(mint)) or sym is None:
                continue
            calls.append({"symbol": sym, "mint": mint, "date": _match(x.get("date"), _FEAT_DATE_RE),
                          "ts": _match(x.get("ts"), _FEAT_TS_RE), "essence": _long_text(x.get("essence"), ESSENCE_MAX),
                          "body": _long_text(x.get("body"), BODY_MAX), "mult": _match(x.get("mult"), _FEAT_MULT_RE)})
        callers.append({"key": key, "name": name, "handle": handle, "tagline": tagline, "count": len(calls),
                        "calls": calls})
    return {"count": len(callers), "as_of": _as_of(d), "callers": callers}


def parse_reveal(body):
    """/api/pull/missed-reveal/{id} -> {"mint": <valid mint or None>, "sym", "name"} (contract 0.2)."""
    d = _load_json(body)
    mint = d.get("mint")
    if not (isinstance(mint, str) and _rowclean._MINT_RE.fullmatch(mint)):
        return {"mint": None, "sym": None, "name": None}
    return {"mint": mint, "sym": _rowclean._text(d.get("sym"), 65), "name": _rowclean._text(d.get("name"), 128)}


# ---- images (5.2): a data: URL of the exact bytes, or None
PLACEHOLDER_PNG = base64.b64decode(   # = the free-feed's / website's 1x1 placeholder: means "no picture" (=> None)
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def image_cap(key):
    return _hermes.LOGO_MAX if IMG_ID_RE.fullmatch(key) else _hermes.BANNER_MAX


def parse_image(key, status, hdrs, body):
    """ONE image answer -> "data:<ctype>;base64,..." or None: status 200 only; Content-Type png / jpeg / webp exactly AND
    the bytes' magic must match (freepickclean.img_ok: logo = PNG <= 64 KB, banner <= 2 MB); the placeholder => None."""
    if status != 200 or not isinstance(hdrs, dict) or not isinstance(body, (bytes, bytearray)):
        return None
    if not (isinstance(key, str) and IMG_KEY_RE.fullmatch(key)):
        return None
    ctype = str(hdrs.get("content-type") or "").split(";", 1)[0].strip().lower()
    if not _hermes.img_ok(key, ctype, body) or bytes(body) == PLACEHOLDER_PNG:
        return None
    return "data:" + ctype + ";base64," + base64.b64encode(bytes(body)).decode("ascii")


# ---- history wire format v1 (contract 0.3) -> rows in the pane's own Rewind form (5.5)
HIST_F = ("age_secs", "token_age_secs", "entry_mcap_usd", "current_mcap", "pct", "liquidity_usd", "holders",
          "entry_holders", "txns_5m", "top_10_holder_pct", "coord_pct", "sniper_owned_pct", "volume_5m", "volume_1h",
          "volume_24h")
HIST_B = {"free": ("dex_paid", "fee_rug", "fee_rug_flicker"),
          "gated": ("dex_paid", "fee_rug", "fee_rug_flicker", "model_approved")}
HIST_SCOPE = {"free": "live_coins", "gated": "board"}
HIST_ROW_LEN = {"free": 17, "gated": 21}
HIST_FRAMES_MAX = 144
HIST_ROWS_MAX = 150
# the pane's Rewind row (plugin.src.js RW_NUMS / RW_BOOLS / encodeRow): 16 numbers (the 15 of f + ce_step_index), 4 flags
RW_NUMS = HIST_F + ("ce_step_index",)
RW_BOOLS = ("dex_paid", "fee_rug", "fee_rug_flicker", "model_approved")
_FLAG_CODE = {"1": True, "2": False, "0": None}


def _is_idx(v, n):
    return isinstance(v, int) and not isinstance(v, bool) and 0 <= v < n


def _wire_num(v):
    if v is None:
        return True
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def parse_history(body, view):
    """Wire format v1 bytes -> {"view", "scope", "as_of", "truncated", "coins": [[mint, symbol, name, socials]],
    "frames": [{"t": <epoch s>, "rows": [[coin index, [16 numbers], "<4 flag codes>", ce_step, ce_line, crowd]]}]}
    (oldest -> newest). Strict: v / view / f / b / scope must be exactly the contract's; every row has the exact length
    (17 free / 21 member), every index is in range, every number finite; ANY violation refuses the whole answer
    (ValueError). Then every row goes through rowclean.clean_row (free) / gatedclean.clean_gated_row (member), so nothing
    outside the board's own fields survives."""
    if view not in HIST_SCOPE or len(body) > HISTORY_MAX_BYTES:
        raise ValueError("bad view / too big")
    d = json.loads(body.decode("utf-8"))
    if not isinstance(d, dict):
        raise ValueError("bad shape")
    b = HIST_B[view]
    if not (type(d.get("v")) is int and d.get("v") == 1 and d.get("view") == view and d.get("scope") == HIST_SCOPE[view]
            and d.get("f") == list(HIST_F) and d.get("b") == list(b)):
        raise ValueError("not wire v1")
    coins, strs, slots = d.get("coins"), d.get("strs"), d.get("slots")
    if not (isinstance(coins, list) and isinstance(strs, list) and isinstance(slots, list) and slots):
        raise ValueError("bad shape")
    if view == "free" and strs:
        raise ValueError("free strs")
    if len(coins) > HIST_FRAMES_MAX * HIST_ROWS_MAX or len(strs) > HIST_FRAMES_MAX * HIST_ROWS_MAX * 2:
        raise ValueError("too many")
    for s in strs:
        if not (isinstance(s, str) and len(s) <= 400):
            raise ValueError("bad string")
    clean = _rowclean.clean_row if view == "free" else _gated.clean_gated_row
    meta = []                       # per coin index: (mint, symbol, name, socials) from the cleaner, or None (dropped)
    for c in coins:
        if not (isinstance(c, list) and len(c) == 4):
            raise ValueError("bad coin")
        r = {"mint": c[0]}
        for k, v in zip(("symbol", "name", "socials"), c[1:]):
            if v is not None:
                r[k] = v
        cc = _rowclean.clean_row(r)
        meta.append((cc["mint"], cc.get("symbol"), cc.get("name"), cc.get("socials")) if cc else None)
    n_len, flag_re = HIST_ROW_LEN[view], re.compile("[012]{%d}\\Z" % len(b))
    used, out_coins, frames = {}, [], []
    for slot in slots[-HIST_FRAMES_MAX:]:
        if not isinstance(slot, dict) or not isinstance(slot.get("rows"), list):
            raise ValueError("bad slot")
        t = slot.get("t")
        if not (isinstance(t, int) and not isinstance(t, bool) and 1_500_000_000 <= t <= 4_000_000_000):
            raise ValueError("bad t")
        rows = []
        for a in slot["rows"][:HIST_ROWS_MAX]:
            if not (isinstance(a, list) and len(a) == n_len and _is_idx(a[0], len(coins))):
                raise ValueError("bad row")
            nums, flags = a[1:16], a[16]
            if not all(_wire_num(x) for x in nums) or not (isinstance(flags, str) and flag_re.fullmatch(flags)):
                raise ValueError("bad row values")
            m = meta[a[0]]
            if m is None:
                continue
            r = {"mint": m[0]}
            for k, v in zip(("symbol", "name", "socials"), m[1:]):
                if v is not None:
                    r[k] = v
            for k, v in zip(HIST_F, nums):
                if v is not None:
                    r[k] = v
            for k, ch in zip(b, flags):
                if _FLAG_CODE[ch] is not None:
                    r[k] = _FLAG_CODE[ch]
            if view == "gated":
                step, step_i, line_i, crowd = a[17], a[18], a[19], a[20]
                if not ((step is None or isinstance(step, str)) and _wire_num(step_i)
                        and (line_i is None or _is_idx(line_i, len(strs)))):
                    raise ValueError("bad gated values")
                if step is not None:
                    r["ce_step"] = step
                if step_i is not None:
                    r["ce_step_index"] = step_i
                if line_i is not None:
                    r["ce_line"] = strs[line_i]
                if crowd is not None:
                    if not (isinstance(crowd, list) and len(crowd) == 6
                            and (crowd[5] is None or _is_idx(crowd[5], len(strs)))
                            and (crowd[4] is None or _is_idx(crowd[4], 2))):
                        raise ValueError("bad crowd")
                    rc = {"real": crowd[0], "shown": crowd[1], "pct": crowd[2], "tier": crowd[3],
                          "padded": None if crowd[4] is None else crowd[4] == 1,
                          "line": None if crowd[5] is None else strs[crowd[5]]}
                    r["real_crowd"] = {k: v for k, v in rc.items() if v is not None}
            cr = clean(r)
            if cr is None:
                continue
            ci = used.get(cr["mint"])
            if ci is None:
                ci = used[cr["mint"]] = len(out_coins)
                out_coins.append([cr["mint"], cr.get("symbol"), cr.get("name"), cr.get("socials")])
            rows.append([ci, [cr.get(k) for k in RW_NUMS],
                         "".join("1" if cr.get(k) is True else "2" if cr.get(k) is False else "0" for k in RW_BOOLS),
                         cr.get("ce_step"), cr.get("ce_line"), cr.get("real_crowd")])
        frames.append({"t": t, "rows": rows})
    frames.sort(key=lambda f: f["t"])
    return {"view": view, "scope": HIST_SCOPE[view], "as_of": _as_of(d), "truncated": d.get("truncated") is True,
            "coins": out_coins, "frames": frames}


class FeedClient:
    """get() -> {"state", "board", "retry_in_s", "error"}. States:
       fresh   - a new result was just fetched;
       cached  - the last good result; the next fetch is not due yet;
       loading - the very first fetch is still running (no result yet);
       waiting - backing off after an error; the last good result is returned;
       error   - backing off after an error and there is no result yet;
       no_key  - (member feeds) no key is set: nothing is requested;
       gone    - (gone_on_404) the server answered 404: never requested again until the next start.
    The NEW paths are built with: first_delay_s=120 (the first request waits a random 0..120 s
    after the client is made = after Hermes starts, independently per path), strict_4xx (any 4xx but 429 = stop 15 min
    and hide the last result: never a quick retry), floor_on_error (an error never shortens the floor), max_bytes
    (a per-path byte cap) and, for history, gone_on_404. Without them a client behaves exactly as before."""

    def __init__(self, transport=urllib_transport, *, clock=time.monotonic, rand=random.random, url=URL,
                 parse=parse_board, auth=None, min_interval_s=MIN_INTERVAL_S, first_delay_s=0.0, strict_4xx=False,
                 gone_on_404=False, floor_on_error=False, max_bytes=None):
        if not (isinstance(url, str) and url.startswith(_ALLOWED_PREFIX)):
            raise ValueError("feed URL must be on " + _ALLOWED_PREFIX)
        if strict_4xx and ("?" in url or "#" in url):
            raise ValueError("a new path never carries a query string")
        self._transport, self._clock, self._rand, self._url = transport, clock, rand, url
        self._parse, self._auth = parse, auth
        self._min = max(MIN_INTERVAL_S, float(min_interval_s))
        self._strict_4xx, self._gone_on_404, self._floor_on_error = strict_4xx, gone_on_404, floor_on_error
        self._max_bytes = max_bytes
        self._lock = threading.Lock()
        self._busy = False
        self._board = None
        self._next_at = -math.inf
        if first_delay_s:
            self._next_at = clock() + max(0.0, min(float(first_delay_s), FIRST_CALL_MAX_S)) * rand()
        self._failures = 0
        self._last_error = None
        self._refused = False
        self._gone = False
        self._held = None    # (own next_at before, until) of the newest shared refusal wait (hold_until)

    def last(self):
        """The last good result (or None) WITHOUT any network request: for readers that must never fetch (the
        per-turn agent hook)."""
        with self._lock:
            return self._board

    def refused(self):
        """True after the server refused the key (401/403) and until a later request succeeds. No network."""
        with self._lock:
            return self._refused

    def drop(self):
        """Forget the last result (memory only; no network)."""
        with self._lock:
            self._board = None

    def clear_refused(self):
        """Forget an earlier 401/403 (memory only; no network): the member board of the same key just answered 200."""
        with self._lock:
            self._refused = False

    def next_at(self):
        """When the next request may start (this client's clock)."""
        with self._lock:
            return self._next_at

    def hold_until(self, t):
        """No request before t (this client's clock); never brings a later wait forward. No network."""
        with self._lock:
            if t > self._next_at:
                held = self._held
                own = held[0] if held is not None and self._next_at == held[1] else self._next_at
                self._held = (own, t)
                self._next_at = t

    def release_hold(self):
        """Drop the wait that hold_until set, if it is still the one in force: back to this client's own wait (its
        floor, its own 4xx or Retry-After wait). A wait the client set itself is never shortened. No network."""
        with self._lock:
            held, self._held = self._held, None
            if held is not None and self._next_at == held[1]:
                self._next_at = held[0]

    def set_min_interval(self, seconds):
        with self._lock:
            self._min = max(MIN_INTERVAL_S, float(seconds))

    def _backoff(self):
        base = min(MAX_BACKOFF_S, self._min * (2 ** min(self._failures - 1, 10)))
        return min(MAX_BACKOFF_S, max(self._min, base) * (1.0 + 0.2 * self._rand()))   # jitter only upward

    def _result(self, state, now):
        return {"state": state, "board": self._board,
                "retry_in_s": max(0.0, self._next_at - now) if math.isfinite(self._next_at) else 0.0,
                "error": self._last_error}

    def _idle_state(self):
        if self._gone:
            return "gone"
        if self._board is None:
            return "loading" if self._busy or self._failures == 0 else "error"
        return "cached" if self._failures == 0 else "waiting"

    def get(self):
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        if self._auth is not None:
            extra = self._auth()
            if not extra:
                return {"state": "no_key", "board": None, "retry_in_s": 0.0, "error": None}
            headers.update(extra)
        with self._lock:
            now = self._clock()
            if self._busy or now < self._next_at:
                return self._result(self._idle_state(), now)
            self._busy = True
            # Record the floor NOW: whatever happens below, no second request can start within the floor.
            self._next_at = now + self._min
        status, hdrs, err, board = None, {}, None, None
        try:
            try:
                if self._max_bytes is None:
                    status, hdrs, body = self._transport(self._url, headers, TIMEOUT_S)
                else:
                    status, hdrs, body = self._transport(self._url, headers, TIMEOUT_S, self._max_bytes)
                if status == 200:
                    board = self._parse(body)
                else:
                    err = f"http_{status}"
            except Exception as e:   # network / timeout / bad JSON: never crash the panel
                err = type(e).__name__
        finally:
            headers = None           # drop the key reference as early as possible
            with self._lock:
                self._busy = False
                now = self._clock()
                if board is not None:
                    self._board, self._failures, self._last_error, self._refused = board, 0, None, False
                    self._next_at = now + self._min
                    state = "fresh"
                else:
                    self._failures += 1
                    self._last_error = err or "interrupted"
                    any_4xx = isinstance(status, int) and 400 <= status < 500 and status != 429
                    # any 4xx but 429 (a refused key, 404, 400 ...): never a quick retry: 15 min + upward jitter
                    wait = MAX_BACKOFF_S * (1.0 + 0.2 * self._rand()) if any_4xx else self._backoff()
                    if any_4xx and self._strict_4xx:
                        self._board = None                          # a new path: that part is hidden
                    if self._floor_on_error:
                        wait = max(wait, self._min)
                    self._next_at = now + wait                      # recorded before parsing anything
                    if status == 404 and self._gone_on_404:
                        self._gone, self._board, self._next_at = True, None, math.inf
                    if status in (401, 403) and self._auth is not None:
                        self._board = None                          # a refused member key keeps NO member data
                        self._refused = True
                    if status in (429, 503) and isinstance(hdrs, dict):
                        ra = parse_retry_after(hdrs.get("retry-after"))   # never raises
                        if ra is not None:
                            wait = max(wait, min(ra, MAX_RETRY_AFTER_S))
                            self._next_at = now + wait
                    state = "gone" if self._gone else "waiting" if self._board is not None else "error"
                result = self._result(state, now)
        if state != "fresh":
            log.warning("feed_fetch_failed feed=%s err=%s next_in_s=%.0f", self._url.rsplit("/", 1)[-1].split("?")[0],
                        self._last_error, result["retry_in_s"])
        return result


FreeBoardClient = FeedClient   # (kept name: the free board client is a FeedClient with the defaults)
