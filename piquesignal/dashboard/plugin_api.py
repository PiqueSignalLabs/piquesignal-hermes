"""PiqueSignal backend for the Hermes Desktop panel.

Mounted at /api/plugins/piquesignal/ once the plugin is in plugins.enabled. The Desktop pane calls these routes with
ctx.rest; it never talks to piquesignal.xyz itself, and it never sees the member key.

Routes:
    GET  /status                 {"has_key": bool, "version": str, "key_id": str|null, "refused": bool, "key_bad": bool}
                                 (never the key; key_bad = a value is set but it is not in the key format)
    GET  /board?view=free        the FREE board (no key): https://piquesignal.xyz/api/free-board
    GET  /board?view=gated       the member board: https://piquesignal.xyz/api/pull/feed (Bearer member key)
    GET  /early-edge             the member Early Edge list: https://piquesignal.xyz/api/pull/early-edge
    GET  /coin-icon?mint=<mint>  {"path": <local file or null>}: the coin's board picture saved for a Windows
                                 notification (core.coin_icon_path: fetched from cdn.dexscreener.com, no key; at most
                                 40 files in this plugin's data folder; emptied when the member key is removed/refused)
    GET  /chart?mint=<mint>&tf=5m|1h|24h  {"ok", "mint", "tf", "state": "ok"|"unclear"|"none"|"unavailable", "pool",
                                 "dex", "candles": [[t, o, h, l, c, v] ...], "checked", "source": "GeckoTerminal"}: a
                                 coin pop-up's price chart, only when the user opens or switches it (core.candles: the
                                 pair the Deep Check live pair rule picks on api.dexscreener.com, its candles from
                                 api.geckoterminal.com with the pool address only; no chart when the price is unclear)
    GET  /chart/trades?mint=<mint>&since=<epoch s>  {"ok", "mint", "state": "ok"|"unclear"|"none"|"unavailable"|
                                 "paused"|"stale", "pool", "trades": [[t, price_usd, volume_usd, "b"|"s", id] ...],
                                 "next_in_s", "checked"}: the open chart's live trades (core.trades: only the pool
                                 that coin's chart picked, from api.geckoterminal.com .../pools/<pool>/trades; the pane
                                 asks only while the chart is open and visible, never faster than every 10 s, and
                                 waits next_in_s)
    POST /panel                  {"view": "free"|"gated", "pick": <coin address>|null}: what the panel shows and the
                                 coin the user picked, for the agent's "this one" (local only, no network)
    The NEW addresses (live in this release; all answer "off" with NO network if core.HERMES_LIVE is set False):
    GET  /missed                 the Missed strip: https://piquesignal.xyz/api/free-board/missed (keyless, never a mint)
    GET  /free-pick              the Free Pick {pick, nextInSecs}: /api/free-board/free-pick (keyless)
    GET  /banners                the banners {ok, banners}: /api/free-board/banners (keyless; no view / click counting)
    GET  /featured               Featured Callers: /api/pull/featured-callers (member key)
    GET  /img/{key}              {"data": <data: URL or null>}: /api/free-board/img/{key} (keyless); key = 16 hex or
                                 b<id>-<12 hex>, checked BEFORE anything, and only a key the current Missed / banners
                                 answers reference is ever requested
    POST /reveal                 {"img": "<16 hex>"} -> {"mint": <coin address>|null}: /api/pull/missed-reveal/{img}
                                 (member key; a user click only, never polled)
    GET  /history?view=free      the last 24 h for Rewind: /api/free-board/history (keyless) /
    GET  /history?view=gated       /api/pull/history (member key); decoded + cleaned, handed out once
    POST /live/speak-test        Board talk voice test (the palette's "Board talk voice test"): ONE fixed line
                                 (LIVE_TEST_LINE; the request may carry no text) in host A's voice -> {"ok": true,
                                 "data_url": "data:audio/mpeg;base64,...", "ms"} or {"ok": false, "error": <code>}.
                                 No call to piquesignal.xyz; the user's Hermes voice settings decide the voice (see
                                 _voice_plan: two Edge voices when the provider is Edge, else Hermes' own tool).
    GET  /live/caps              {"used": null, "max_day": null, "gap_s": 0, "next_in_s": 0, "voice", "free_voice",
                                 "script", "voices", "hosts"}: Board talk has no daily limit and no wait (the 4 limit
                                 fields stay, open, for an older pane), the voice provider, the script maker, the hosts
                                 (no network)
    POST /live/episode           {"view", "kind": "now"|"morning", "since": null|{"mins", "added", "changed", "left",
                                 "basis"}, "saved"} (coin addresses + fixed change codes only; ce_ / pad_ codes only for
                                 the member view) -> {"ok", "ep", "view", "kind", "source", "segments": [{"i", "mint",
                                 "caption", "host", "seg", "coin"}], "caps", "hosts", "voices", "as_of"}. The script is
                                 written from the CACHED board: the user's own model (ctx.llm, one capped call) writes
                                 each coin's story with slot tokens, core.talk_check checks every line (a failing first
                                 line = that coin's template story, a failing later line is dropped, no usable story =
                                 the fixed template) and core.talk_story adds our intros, openers, speakers and closing.
                                 No daily limit and no wait between shows (it is the user's own AI model and voice
                                 credits): only ONE show is made at a time (a second press while one is being made,
                                 or within LIVE_EP_PRESS_GAP_S after one was made = "busy"). "caps" = LIVE_CAPS_OPEN.
    POST /live/episode/replay    {} -> the same answer for the last show the voice spoke again ("kind": "replay"): the
                                 stored, already-checked script, NO model call; one every LIVE_REPLAY_GAP_S (a double-press
                                 guard, no daily limit), for LIVE_REPLAY_KEEP_S after the show was made
    GET  /live/episode/audio     ?ep=<16 hex>&seg=<0..47> -> {"ok", "seg", "data_url", "ms"}: ONE stored, checked line
                                 of that show in its host's voice (never any text from the request)
    POST /live/episode/stop      {"ep": <16 hex>} -> {"ok": true, "caps", "replay"}: no more audio for that show;
                                 "replay" = {"view", "left_s"} of the show Replay would play, or null

Every board-like route answers {"state", "board", "retry_in_s", "error"} (see feed_client.FeedClient; "off" = the
address is switched off by the core.HERMES_LIVE kill switch). All the work lives
in core.py, shared with the agent half (__init__.py) in the same process, so one set of rate-polite clients serves
both: one request at a time, a floor between requests, back-off on errors, Retry-After honoured, member requests paced
to stay well under the key's daily limit (read from /api/pull/me, at most once an hour).
"""

from __future__ import annotations

import asyncio
import base64
import importlib.util
import json
import logging
import math
import os
import re
import secrets
import shutil
import sys
import tempfile
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Body, Path as PathParam, Query

_CORE_NAME = "piquesignal_core"


def _load_core():
    """core.py, ONE copy per process (the agent half loads the same one)."""
    mod = sys.modules.get(_CORE_NAME)
    if mod is None:
        spec = importlib.util.spec_from_file_location(_CORE_NAME, Path(__file__).resolve().parents[1] / "core.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod = sys.modules.setdefault(_CORE_NAME, mod)
    return mod


core = _load_core()
router = APIRouter()
VERSION = core.VERSION


@router.get("/status")
def status() -> dict:
    return core.status()


@router.get("/board")
def board(view: str = Query("free", pattern="^(free|gated)$")) -> dict:
    return core.board(view)


@router.get("/early-edge")
def early_edge() -> dict:
    return core.early_edge()


@router.get("/coin-icon")
def coin_icon(mint: str = Query(..., pattern="^[1-9A-HJ-NP-Za-km-z]{32,44}$")) -> dict:
    """The board's own picture of this coin as a local file, for a Windows notification (or none)."""
    return {"path": core.coin_icon_path(mint)}


@router.get("/chart")
def chart(mint: str = Query(..., pattern="^[1-9A-HJ-NP-Za-km-z]{32,44}$"),
          tf: str = Query(..., pattern="^(5m|1h|24h)$")) -> dict:
    """A coin pop-up's price chart, on the user's click only (core.candles: the pool the live pair rule picked). A sync
    handler (a worker thread): inside the 2 s Dexscreener spacing it waits out the rest once and reads again."""
    return core.candles(mint, tf, wait_spacing=True)


@router.get("/chart/trades")
def chart_trades(mint: str = Query(..., pattern="^[1-9A-HJ-NP-Za-km-z]{32,44}$"),
                 since: int = Query(..., ge=0, le=4_102_444_800)) -> dict:
    """The open chart's live trades (core.trades: the pool the chart picked; at most 1 GeckoTerminal request per
    10 s)."""
    return core.trades(mint, since)


@router.get("/missed")
def missed() -> dict:
    return core.missed()


@router.get("/free-pick")
def free_pick() -> dict:
    return core.free_pick()


@router.get("/banners")
def banners() -> dict:
    return core.banners()


@router.get("/featured")
def featured() -> dict:
    return core.featured()


@router.get("/img/{key}")
def img(key: str = PathParam(..., pattern="^([0-9a-f]{16}|b[0-9]{1,9}-[0-9a-f]{12})$")) -> dict:
    if not core.fc.IMG_KEY_RE.fullmatch(key):          # the exact rule again (no trailing newline can pass)
        return {"data": None}
    return {"data": core.image(key)}


@router.post("/reveal")
def reveal(body: dict = Body(...)) -> dict:
    img_id = body.get("img") if isinstance(body, dict) else None
    if not (isinstance(img_id, str) and core.fc.IMG_ID_RE.fullmatch(img_id)):
        return {"mint": None}
    return {"mint": core.reveal(img_id).get("mint")}


@router.get("/history")
def history(view: str = Query(..., pattern="^(free|gated)$")) -> dict:
    return core.history(view)


@router.post("/panel")
def panel(body: dict = Body(...)) -> dict:
    view = body.get("view") if isinstance(body, dict) else None
    if view not in core.VIEWS:
        return {"ok": False, "error": "view"}
    pick = body.get("pick")
    return {"ok": True, **core.set_panel(view, pick if isinstance(pick, str) else None)}


# ------------------------------------------------------------------------------------------- Board talk: the voices
# Board talk's voices come from the user's own Hermes config only (load_config_readonly; never .env, never the
# client): provider Edge (Hermes' free default) with the edge_tts library present = TWO voices (host A = the user's own
# Edge voice when it is a plain English Neural voice name, else Aria; host B = Guy, or Aria when A is a male voice), a
# quicker radio pace (+15%, or the user's own Edge speed); any other provider = ONE voice through Hermes' own
# text-to-speech tool at speed 1.15. Each synthesis runs on a worker thread that carries the request's context
# (asyncio.to_thread copies it), so the profile scope Hermes set for this plugin route applies; the file goes to a
# private temp folder that is always removed, only an MP3 inside that folder and at most LIVE_AUDIO_MAX_BYTES is read,
# a hard timeout, never two syntheses at once (a synthesis that never returns frees its slot after LIVE_STALE_S, so
# Board talk and the voice test do not stay "busy" for one hung call; while LIVE_STUCK_MAX such hung calls have not
# ended, every new one is "busy", so hung threads never pile up). The voice test: the client can send no text
# (a non-empty body is refused), one call per LIVE_MIN_GAP_S per process, at most LIVE_TEST_DAY_MAX a local day (a paid
# voice uses the user's credits; the day's count is kept in this plugin's data folder, so a restart does not reset it).
# Logs carry the short result code only.
LIVE_TEST_LINE = "PiqueSignal Board talk test. If you can hear this, Hermes can host Board talk."
LIVE_TTS_TIMEOUT_S = 12.0
LIVE_AUDIO_MAX_BYTES = 2 * 1024 * 1024
LIVE_MIN_GAP_S = 5.0
_log = logging.getLogger(__name__)
_live_lock = threading.Lock()
# last accepted call (monotonic); syntheses running; the newest job; stale workers whose thread has not ended yet
_live = {"last": None, "running": 0, "job": None, "stuck": 0}
LIVE_STALE_S = 120.0                       # a claimed synthesis still running after this gives its slot back
LIVE_STUCK_MAX = 2                         # this many stale workers still stuck = "busy" (a hard cap on stuck threads)
LIVE_EDGE_SAVE_S = 30.0                    # one Edge line: the save itself is cut off after this
LIVE_TEST_DAY_MAX = 30
_live_day = {"day": None, "count": 0}     # voice tests accepted on this local day (kept in live-test-count.json)
_LIVE_COUNT_FILE = "live-test-count.json"
TALK_EDGE_A = "en-US-AriaNeural"           # Hermes' own Edge default voice
TALK_EDGE_B = "en-US-GuyNeural"
TALK_EDGE_RATE = "+15%"
TALK_TOOL_SPEED = 1.15
TALK_ONE_HOST = "Hermes"
_EDGE_VOICE_RE = re.compile(r"en-[A-Z]{2}-[A-Za-z]{2,40}Neural")
_EDGE_NAME_RE = re.compile(r"en-[A-Z]{2}-([A-Za-z]+?)(?:Multilingual)?Neural")
_HOST_NAME_RE = re.compile(r"[A-Z][a-z]{1,15}")
_EDGE_MALE = frozenset({"Guy", "Davis", "Christopher", "Eric", "Andrew", "Brian", "Roger", "Steffan"})


def _load_tts():
    """Hermes' own text-to-speech tool, imported only when asked (the plugin still loads on a Hermes without it)."""
    from tools.tts_tool import text_to_speech_tool
    return text_to_speech_tool


def _edge_available() -> bool:
    """True when the edge_tts library can be imported. Looked up only (find_spec): nothing is imported or installed
    here (Hermes' own importer may try to install a missing library; this plugin never does)."""
    try:
        import importlib.util as _iu
        return _iu.find_spec("edge_tts") is not None
    except Exception:
        return False


def _load_edge():
    """The edge_tts library (the one Hermes' own Edge voice uses), imported only when a line is spoken."""
    import importlib
    return importlib.import_module("edge_tts")


def _spoken_for_tts(text: str) -> str:
    """Hermes' own text cleanup for speech (the same as its tool uses), or the text as it is."""
    try:
        from tools.tts_text_normalize import prepare_spoken_text
        return prepare_spoken_text(text, max_chars=None)
    except Exception:
        return text.strip()


def _tts_config() -> dict:
    """The "tts" part of the user's Hermes config (never .env), or {}."""
    try:
        from hermes_cli.config import load_config_readonly
        tts = (load_config_readonly() or {}).get("tts")
    except Exception:
        return {}
    return tts if isinstance(tts, dict) else {}


def _provider(tts: dict) -> str:
    prov = tts.get("provider")
    if isinstance(prov, str):
        prov = prov.strip().lower()            # the way Hermes reads it (tools/tts_tool.py _get_provider)
    if prov is None or prov == "":
        return "edge"
    return prov if isinstance(prov, str) and _VOICE_RE.fullmatch(prov) else "unknown"


def _voice() -> str:
    """The configured text-to-speech provider name (Hermes' config, never .env): "edge" when not set."""
    return _provider(_tts_config())


def _edge_name(voice: str):
    m = _EDGE_NAME_RE.fullmatch(voice)
    return m.group(1) if m else None


def _voice_plan() -> dict:
    """Who speaks Board talk, from the user's Hermes config only -> {"engine": "edge"|"tool", "voices": [A, B] (Edge
    voice names) or [], "rate": "+15%"-style or None, "hosts": [{"id", "name"}] (1 or 2)}."""
    tts = _tts_config()
    if _provider(tts) == "edge" and _edge_available():
        edge = tts.get("edge") if isinstance(tts.get("edge"), dict) else {}
        a = edge.get("voice")
        a = a if isinstance(a, str) and _EDGE_VOICE_RE.fullmatch(a) else TALK_EDGE_A
        name_a = _edge_name(a)
        b = TALK_EDGE_A if name_a in _EDGE_MALE else TALK_EDGE_B
        speed = edge.get("speed", tts.get("speed"))
        rate = TALK_EDGE_RATE
        if (isinstance(speed, (int, float)) and not isinstance(speed, bool) and math.isfinite(speed)
                and speed != 1.0 and 0.5 <= speed <= 2.0):
            rate = "%+d%%" % round((speed - 1.0) * 100)
        if not (name_a and _HOST_NAME_RE.fullmatch(name_a)):
            name_a = TALK_ONE_HOST
        return {"engine": "edge", "voices": [a, b], "rate": rate,
                "hosts": [{"id": "A", "name": name_a}, {"id": "B", "name": _edge_name(b)}]}
    return {"engine": "tool", "voices": [], "rate": None, "hosts": [{"id": "A", "name": TALK_ONE_HOST}]}


def _looks_mp3(data: bytes) -> bool:
    """An ID3 tag or an MPEG audio frame sync at the start."""
    return data[:3] == b"ID3" or (len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0)


def _live_slot_busy(now: float) -> bool:
    """True while a synthesis holds the slot (call under _live_lock). A claimed job still running after LIVE_STALE_S
    (a text-to-speech call that never returns) is marked stale and its slot is given back here; its worker then never
    gives it back a second time. While LIVE_STUCK_MAX stale workers have still not ended, every new synthesis is
    refused as busy, so stuck threads never pile up."""
    if _live.get("stuck", 0) >= LIVE_STUCK_MAX:
        return True
    if _live["running"] <= 0:
        return False
    job = _live.get("job")
    if (isinstance(job, dict) and job.get("claimed") and not job.get("stale")
            and now - job.get("at", now) > LIVE_STALE_S):
        job["stale"] = True
        _live["running"] = max(0, _live["running"] - 1)
        _live["stuck"] = _live.get("stuck", 0) + 1
        return _live["running"] > 0 or _live["stuck"] >= LIVE_STUCK_MAX
    return True


def _live_take_slot(job: dict, now: float) -> None:
    """Take the synthesis slot for job (call under _live_lock, after _live_slot_busy said no)."""
    job["at"] = now
    _live["job"] = job
    _live["running"] += 1


def _count_file():
    d = core._data_dir()
    return (d / _LIVE_COUNT_FILE) if d is not None else None


def _load_test_count() -> None:
    """Read today's voice-test count from the plugin data folder once per process (call under _live_lock)."""
    if _live_day["day"] is not None:
        return
    p = _count_file()
    try:
        if p is None or not p.is_file() or p.stat().st_size > 256:
            return
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if (isinstance(d, dict) and isinstance(d.get("day"), str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d["day"])
            and _is_int(d.get("count"), 0, LIVE_TEST_DAY_MAX)):
        _live_day.update(day=d["day"], count=d["count"])


def _save_test_count(snap: dict) -> None:
    """Keep today's voice-test count in the plugin data folder (atomic write: a day and a number, nothing else)."""
    p = _count_file()
    if p is None:
        return
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(p.parent), prefix=".live-count-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump({"day": snap.get("day"), "count": snap.get("count")}, f)
            os.replace(tmp, str(p))
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    except OSError:
        pass


def _live_release_unclaimed(job: dict) -> None:
    """The route gave up on a job (timeout, cancelled request, executor error). If no worker has claimed it yet, the
    job may never run (a still-queued executor job is dropped when its asyncio wrapper is cancelled): mark it cancelled
    and give the 'running' slot back here. A claimed job's worker gives it back itself in its finally."""
    with _live_lock:
        if not job["claimed"] and not job["cancelled"]:
            job["cancelled"] = True
            _live["running"] -= 1


def _edge_say(text: str, path: str, voice: str, rate: str):
    """One line in one Edge voice -> "ok" / "tts_failed", or None when the library cannot be imported (then Hermes'
    own tool speaks it)."""
    try:
        edge = _load_edge()
    except Exception:
        return None
    try:
        spoken = _spoken_for_tts(text)
        if not spoken:
            return "tts_failed"
        try:
            com = edge.Communicate(spoken, voice=voice, rate=rate, connect_timeout=8, receive_timeout=15)
        except TypeError:                      # an older edge_tts without the timeouts (the route's own timeout stays)
            com = edge.Communicate(spoken, voice=voice, rate=rate)
        asyncio.run(asyncio.wait_for(com.save(path), LIVE_EDGE_SAVE_S))
    except Exception:
        return "tts_failed"
    return "ok"


def _tool_say(text: str, path: str):
    """One line through Hermes' own text-to-speech tool -> (code, the file it says it wrote or None)."""
    try:
        tts = _load_tts()
    except Exception:
        return "tts_unavailable", None
    try:
        raw = tts(text, output_path=path, speed=TALK_TOOL_SPEED)
        res = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return "tts_failed", None
    if not isinstance(res, dict) or res.get("success") is not True or not isinstance(res.get("file_path"), str):
        return "tts_failed", None
    return "ok", res["file_path"]


def _live_synth(job: dict, text: str = LIVE_TEST_LINE, fname: str = "live-test.mp3", host: str = "A") -> tuple:
    """Worker-thread body -> (code, mp3 bytes or None). Claims the job under the lock first (a job the route already
    gave up on is not run at all); speaks text in host A's or B's voice (_voice_plan, read again here); then removes its
    private temp folder in every case (also when the route stopped waiting for it) and gives back the route's 'running'
    slot."""
    with _live_lock:
        if job["cancelled"]:
            return "timeout", None
        job["claimed"] = True
    tmp = None
    try:
        tmp = tempfile.mkdtemp(prefix="pqs-live-")
        out = os.path.join(tmp, fname)
        plan = _voice_plan()
        code = None
        if plan["engine"] == "edge":
            voices = plan["voices"]
            code = _edge_say(text, out, voices[1] if host == "B" and len(voices) > 1 else voices[0], plan["rate"])
            got = out
        if code is None:
            code, got = _tool_say(text, out)
        if code != "ok":
            return code, None
        real = os.path.realpath(got)
        if os.path.dirname(real) != os.path.realpath(tmp) or not os.path.isfile(real):
            return "audio_missing", None
        if os.path.splitext(real)[1].lower() != ".mp3":
            return "audio_format", None
        if os.path.getsize(real) > LIVE_AUDIO_MAX_BYTES:
            return "too_large", None
        with open(real, "rb") as fh:
            data = fh.read(LIVE_AUDIO_MAX_BYTES + 1)
        if len(data) > LIVE_AUDIO_MAX_BYTES:
            return "too_large", None
        if not data:
            return "audio_missing", None
        if not _looks_mp3(data):
            return "audio_format", None
        return "ok", data
    except Exception:
        return "tts_failed", None
    finally:
        if tmp is not None:
            shutil.rmtree(tmp, ignore_errors=True)
        with _live_lock:
            if not job.get("stale"):           # a stale job's slot was already given back (_live_slot_busy)
                _live["running"] -= 1
            else:                              # a stuck worker ended at last: it no longer counts as stuck
                _live["stuck"] = max(0, _live.get("stuck", 0) - 1)


def _live_fail(code: str) -> dict:
    _log.info("piquesignal live speak-test: %s", code)
    return {"ok": False, "error": code}


@router.post("/live/speak-test")
async def live_speak_test(body: Optional[dict] = Body(None)) -> dict:
    if body not in (None, {}):                 # the line is fixed here; the client sends nothing
        return _live_fail("bad_request")
    now = time.monotonic()
    job = {"claimed": False, "cancelled": False}
    with _live_lock:
        if _live_slot_busy(now):
            return _live_fail("busy")
        if _live["last"] is not None and now - _live["last"] < LIVE_MIN_GAP_S:
            return _live_fail("rate_limited")
        _load_test_count()
        day = time.strftime("%Y-%m-%d", time.localtime())
        if _live_day["day"] != day:
            _live_day.update(day=day, count=0)
        if _live_day["count"] >= LIVE_TEST_DAY_MAX:
            return _live_fail("daily_cap")
        _live_day["count"] += 1
        snap = dict(_live_day)
        _live["last"] = now
        _live_take_slot(job, now)              # given back by the worker that claims the job, else by the route
    _save_test_count(snap)                     # disk write outside the lock
    try:
        code, data = await asyncio.wait_for(asyncio.to_thread(_live_synth, job), LIVE_TTS_TIMEOUT_S)
    except asyncio.CancelledError:             # the request went away: release an unclaimed slot, keep cancelling
        _live_release_unclaimed(job)
        raise
    except asyncio.TimeoutError:
        _live_release_unclaimed(job)           # a claimed worker still cleans up and gives the slot back when it ends
        return _live_fail("timeout")
    except Exception:                          # _live_synth catches its own errors: the executor failed around it
        _live_release_unclaimed(job)
        return _live_fail("tts_failed")
    if code != "ok":
        return _live_fail(code)
    ms = int((time.monotonic() - now) * 1000)
    _log.info("piquesignal live speak-test: ok")
    return {"ok": True, "data_url": "data:audio/mpeg;base64," + base64.b64encode(data).decode("ascii"), "ms": ms}


# ------------------------------------------------------------------------------------------- Board talk: the show
# Board talk: the pane sends coin addresses and fixed change codes only; the facts and the board's own numbers are
# rebuilt here from the CACHED board (core.talk_pick), the user's own model writes each coin's story in ONE capped call
# (core.talk_prompt; numbers only as slot tokens), core.talk_check checks every line (a failing first line = that coin's
# template story, a failing later line is dropped, no usable story = the fixed template) and core.talk_story adds our
# intros, openers, the two hosts' turns and the closing. The script stays here: the pane gets captions, hosts, segments
# and coin addresses, and asks for each line's audio by show id + line number only.
# No daily limit and no wait between shows (it is the user's own AI model and voice credits). Kept: the build lock (ONE
# show is made at a time: a second press while one is being made = "busy"), a short double-press guard (a new show
# within LIVE_EP_PRESS_GAP_S after the last one was made = "busy"), at most LIVE_EP_SEG_SYNTH_MAX syntheses per line,
# one synthesis at a time, every check of the request (show id + line number only, a member show only with the key it
# was made with). Replay re-speaks the last show the voice spoke (its stored script, no model call), at most one per
# LIVE_REPLAY_GAP_S (the same kind of double-press guard).
LIVE_EP_PRESS_GAP_S = 3.0
LIVE_EP_LLM_TIMEOUT_S = 25.0
LIVE_EP_TTS_TIMEOUT_S = 20.0
LIVE_EP_AUDIO_GAP_S = 1.0
LIVE_EP_KEEP = 3
LIVE_EP_TTL_S = {"now": 1800, "morning": 10800}
LIVE_EP_SEG_SYNTH_MAX = 2
LIVE_EP_MAX_LINES = core.TALK_MAX_LINES      # 48 lines (with the hosts' questions; replaces the 10 segments of the first show)
LIVE_REPLAY_GAP_S = 3.0
LIVE_REPLAY_KEEP_S = 6 * 3600
LIVE_SINCE_BASIS = ("away", "last", "rewind", "show")   # all spoken the same plain way ("In the last 40 minutes")
_EP_ID_RE = re.compile(r"[0-9a-f]{16}")
_VOICE_RE = re.compile(r"[a-z0-9_-]{1,32}")
_ep_lock = threading.Lock()                    # lock order: _ep_lock, then _live_lock
_episodes: "OrderedDict[str, dict]" = OrderedDict()
_ep = {"building": False, "audio_last": None, "replay_last": None, "made_last": None}
# the "caps" field every Board talk answer still carries (an older pane reads it): no daily limit, no wait
LIVE_CAPS_OPEN = {"used": None, "max_day": None, "next_in_s": 0}
# the last show the voice spoke (memory only): set at its first line of audio, so a show the voice never spoke is never
# replayed
_replay = {"ep": None, "story": None, "view": None, "made": 0.0, "hosts": None, "voices": 1, "as_of": None, "fp": None}


def _live_llm():
    return core.live_llm()


@router.get("/live/caps")
def live_caps() -> dict:
    voice = _voice()
    hosts = _voice_plan()["hosts"]
    out = dict(LIVE_CAPS_OPEN)
    out.update({"gap_s": 0, "voice": voice, "free_voice": voice == "edge",
                "script": "model" if _live_llm() is not None else "template", "voices": len(hosts), "hosts": hosts})
    return out


def _is_int(v, lo, hi):
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


def _mint_list(v, cap):
    if not isinstance(v, list) or len(v) > cap:
        return None
    if not all(isinstance(m, str) and core.MINT_RE.fullmatch(m) for m in v):
        return None
    return list(v)


def _episode_body(body):
    """The request -> {"view", "kind", "since", "saved"} or None. Coin addresses and fixed codes only."""
    if not isinstance(body, dict) or not set(body) <= {"view", "kind", "since", "saved"}:
        return None
    view, kind = body.get("view"), body.get("kind")
    if view not in core.VIEWS or kind not in LIVE_EP_TTL_S:
        return None
    saved = _mint_list(body.get("saved", []), 50)
    if saved is None:
        return None
    since = body.get("since")
    if since is not None:
        if not isinstance(since, dict) or not set(since) <= {"mins", "added", "changed", "left", "basis"}:
            return None
        if since.get("basis", "away") not in LIVE_SINCE_BASIS:
            return None
        if not _is_int(since.get("mins"), 2, 1440):
            return None
        added = _mint_list(since.get("added", []), 20)
        left = since.get("left", 0)
        changed = since.get("changed", [])
        if added is None or not _is_int(left, 0, 999) or not isinstance(changed, list) or len(changed) > 20:
            return None
        ch_out = []
        for ch in changed:
            if not isinstance(ch, dict) or set(ch) != {"mint", "codes"}:
                return None
            m, codes = ch["mint"], ch["codes"]
            if not (isinstance(m, str) and core.MINT_RE.fullmatch(m)):
                return None
            if not isinstance(codes, list) or len(codes) > 4:
                return None
            for c in codes:
                if not isinstance(c, str) or c not in core.LIVE_CHANGE_CODES:
                    return None
                if c.startswith(core.MEMBER_ONLY_CODE_PREFIXES) and view != "gated":   # ce_ / pad_: member only
                    return None
            ch_out.append({"mint": m, "codes": list(codes)})
        since = {"mins": since["mins"], "added": added, "changed": ch_out, "left": left,
                 "basis": since.get("basis")}
    return {"view": view, "kind": kind, "since": since, "saved": saved}


def _ep_fail(code: str, **extra) -> dict:
    _log.info("piquesignal live episode: %s", code)
    return {"ok": False, "error": code, **extra}


def _ep_board(view):
    """(rows, "HH:MM" local clock time of the board's own as_of or None) of the cached board, or (None, None)."""
    b = core.cached_board(view) or core.fetch_board(view) or {}
    rows = b.get("signals") if isinstance(b, dict) else None
    if not isinstance(rows, list):
        return None, None
    return rows, _clock(b.get("as_of"))


def _clock(as_of):
    """The board's as_of (ISO 8601 from piquesignal.xyz) -> "HH:MM" in local time, or None."""
    if not isinstance(as_of, str) or not 10 <= len(as_of) <= 40:
        return None
    try:
        from datetime import datetime, timezone
        d = datetime.fromisoformat(as_of.strip().replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone().strftime("%H:%M")
    except Exception:
        return None


def _seg_out(story):
    """The stored script -> what the pane gets per line: never the spoken text."""
    return [{"i": i, "mint": s["mint"], "caption": s["text"], "host": s["host"], "seg": s["seg"], "coin": s["coin"]}
            for i, s in enumerate(story)]


@router.post("/live/episode")
async def live_episode(body: Optional[dict] = Body(None)) -> dict:
    req = _episode_body(body)
    if req is None:
        return _ep_fail("bad_request")
    with _ep_lock:
        if _ep["building"]:
            return _ep_fail("busy")                         # one show is made at a time
        last = _ep["made_last"]
        if last is not None and time.monotonic() - last < LIVE_EP_PRESS_GAP_S:
            return _ep_fail("busy")                         # a double press: the show just made is the one
        _ep["building"] = True
    try:
        view = req["view"]
        if view == "gated" and (core._key() is None or core.refused()):
            return _ep_fail("no_key")
        rows, as_of = await asyncio.to_thread(_ep_board, view)
        if rows is None:
            return _ep_fail("no_board")                     # no board yet: nothing is made
        plan = await asyncio.to_thread(_voice_plan)         # the user's Hermes config: file I/O, never on the loop
        hosts = plan["hosts"]
        coins, header = core.talk_pick(view, rows, req["since"], req["saved"])
        entries, source, reason = None, "template", "empty"
        if coins:
            llm = _live_llm()
            prompt = core.talk_prompt(coins, header)        # None: every coin gets its fixed story (no model call)
            reason = "no_llm" if llm is None else "fixed" if prompt is None else reason
            if llm is not None and prompt is not None:
                try:
                    res = await asyncio.wait_for(asyncio.to_thread(llm.complete_structured, **prompt),
                                                 LIVE_EP_LLM_TIMEOUT_S)
                    parsed = getattr(res, "parsed", None)
                    entries = core.talk_check(parsed, coins, header, [h["name"] for h in hosts])
                    reason = "unparsed" if parsed is None else "rejected"   # unparsed: e.g. cut off at max_tokens
                except asyncio.TimeoutError:
                    reason = "timeout"
                except Exception:
                    reason = "error"
            if entries is not None:
                source = "model"
                reason = "all" if all(e.get("src") == "model" for e in entries) else "partial"
            else:
                entries = core.talk_template(coins, header)
        else:
            entries = []
        story = core.talk_story(entries, coins, header, [h["name"] for h in hosts], any(c.get("news") for c in coins))
        story = story[:LIVE_EP_MAX_LINES - 1] + story[-1:] if len(story) > LIVE_EP_MAX_LINES else story
        ep_id = secrets.token_hex(8)
        fp = core._fp_now() if view == "gated" else None   # a member show belongs to the key it was made with
        with _ep_lock:
            made = time.monotonic()
            _ep["made_last"] = made
            _episodes[ep_id] = {"id": ep_id, "view": view, "kind": req["kind"], "segs": story, "made": made,
                                "ttl": LIVE_EP_TTL_S[req["kind"]], "stopped": False, "synth": [0] * len(story),
                                "played": False, "hosts": hosts, "voices": len(hosts), "as_of": as_of, "fp": fp}
            while len(_episodes) > LIVE_EP_KEEP:
                _episodes.popitem(last=False)
        _log.info("piquesignal live episode: %s", ("model" if reason == "all" else "model+template")
                  if source == "model" else "template:" + reason)
        return {"ok": True, "ep": ep_id, "view": view, "kind": req["kind"], "source": source,
                "segments": _seg_out(story), "caps": dict(LIVE_CAPS_OPEN), "hosts": hosts, "voices": len(hosts),
                "as_of": as_of}
    finally:
        with _ep_lock:
            _ep["building"] = False


def _member_now():
    """(the current member key's fingerprint or None, True when the server refused it): read once per request."""
    return core._fp_now(), core.refused()


def _same_member(view, fp, now_fp, refused):
    """A member show may be spoken / replayed only with the SAME key it was made with, and only while that key is not
    refused (another key, no key or a refused key: never). A free show always."""
    return view != "gated" or (bool(fp) and fp == now_fp and not refused)


def _audio_fail(code: str) -> dict:
    _log.info("piquesignal live audio: %s", code)
    return {"ok": False, "error": code}


def _episode_live(ep_id, now):
    """The stored show, or None when it is unknown or expired (call under _ep_lock)."""
    e = _episodes.get(ep_id)
    if e is None:
        return None
    if now - e["made"] > e["ttl"]:
        del _episodes[ep_id]
        return None
    return e


@router.get("/live/episode/audio")
async def live_episode_audio(ep: str = Query(..., pattern="^[0-9a-f]{16}$"),
                             seg: int = Query(..., ge=0, le=LIVE_EP_MAX_LINES - 1)) -> dict:
    global _replay
    if not (isinstance(ep, str) and _EP_ID_RE.fullmatch(ep)) or not _is_int(seg, 0, LIVE_EP_MAX_LINES - 1):
        return _audio_fail("bad_request")
    now_fp, refused = _member_now()
    now = time.monotonic()
    with _ep_lock:
        e = _episode_live(ep, now)
        if e is None:
            return _audio_fail("unknown_episode")
        if e["stopped"]:
            return _audio_fail("stopped")
        if not _same_member(e["view"], e.get("fp"), now_fp, refused):
            return _audio_fail("no_key")
        if seg >= len(e["segs"]):
            return _audio_fail("bad_request")
        if e["synth"][seg] >= LIVE_EP_SEG_SYNTH_MAX:
            return _audio_fail("seg_limit")
        job = {"claimed": False, "cancelled": False}
        with _live_lock:                       # the speak-test's slot: never two syntheses at once
            if _live_slot_busy(now):
                return _audio_fail("busy")
            if _ep["audio_last"] is not None and now - _ep["audio_last"] < LIVE_EP_AUDIO_GAP_S:
                return _audio_fail("rate_limited")
            _ep["audio_last"] = now
            _live_take_slot(job, now)          # given back by the worker that claims the job, else by the route
        e["synth"][seg] += 1
        text = e["segs"][seg]["say"]           # stored, already-checked spoken text (never from the request)
        host = "B" if e["segs"][seg].get("host") == "B" else "A"
    try:
        code, data = await asyncio.wait_for(asyncio.to_thread(_live_synth, job, text, "seg.mp3", host),
                                            LIVE_EP_TTS_TIMEOUT_S)
    except asyncio.CancelledError:
        _live_release_unclaimed(job)
        raise
    except asyncio.TimeoutError:
        _live_release_unclaimed(job)
        return _audio_fail("timeout")
    except Exception:
        _live_release_unclaimed(job)
        return _audio_fail("tts_failed")
    with _ep_lock:
        e = _episodes.get(ep)
        stopped = e is None or e["stopped"]
        if not stopped and code == "ok" and not e["played"]:
            e["played"] = True                 # a line of audio was made: this show can be replayed
            if e["kind"] != "replay":          # ... and it is the show Replay plays from now on
                _replay = {"ep": ep, "story": [dict(x) for x in e["segs"]], "view": e["view"], "made": e["made"],
                           "hosts": [dict(h) for h in e.get("hosts") or ()], "voices": e.get("voices", 1),
                           "as_of": e.get("as_of"), "fp": e.get("fp")}
    if stopped:
        return _audio_fail("stopped")          # Stop was pressed while it was being made: the audio is thrown away
    if code != "ok":
        return _audio_fail(code)
    ms = int((time.monotonic() - now) * 1000)
    _log.info("piquesignal live audio: ok")
    return {"ok": True, "seg": seg, "data_url": "data:audio/mpeg;base64," + base64.b64encode(data).decode("ascii"),
            "ms": ms}


@router.post("/live/episode/stop")
def live_episode_stop(body: Optional[dict] = Body(None)) -> dict:
    ep = body.get("ep") if isinstance(body, dict) and set(body) == {"ep"} else None
    if not (isinstance(ep, str) and _EP_ID_RE.fullmatch(ep)):
        return {"ok": False, "error": "bad_request"}
    with _ep_lock:
        e = _episodes.get(ep)
        if e is not None:
            e["stopped"] = True
        replay = _replay_out(time.monotonic())
    return {"ok": True, "caps": dict(LIVE_CAPS_OPEN), "replay": replay}


def _replay_out(mono):
    """{"view", "left_s"} of the show Replay would play, or None (call under _ep_lock)."""
    if not _replay.get("story"):
        return None
    left = LIVE_REPLAY_KEEP_S - (mono - _replay.get("made", 0.0))
    return {"view": _replay["view"], "left_s": int(left)} if left > 0 else None


@router.post("/live/episode/replay")
def live_episode_replay(body: Optional[dict] = Body(None)) -> dict:
    if body not in (None, {}):                 # nothing from the client: the stored script is replayed as it is
        return _ep_fail("bad_request")
    mono = time.monotonic()
    with _ep_lock:
        r = dict(_replay)
    if not r.get("story") or mono - r.get("made", 0.0) > LIVE_REPLAY_KEEP_S:
        return _ep_fail("no_replay")
    view = r["view"]
    now_fp, refused = _member_now()
    if not _same_member(view, r.get("fp"), now_fp, refused):
        return _ep_fail("no_key")
    with _ep_lock:
        if _ep["building"] or _replay.get("ep") != r["ep"]:
            return _ep_fail("busy")            # a new show is being made / was made meanwhile
        last = _ep["replay_last"]
        if last is not None and mono - last < LIVE_REPLAY_GAP_S:
            return _ep_fail("replay_soon", next_in_s=int(math.ceil(LIVE_REPLAY_GAP_S - (mono - last))))
        _ep["replay_last"] = mono
        story = [dict(s) for s in r["story"]]
        ep_id = secrets.token_hex(8)
        hosts = [dict(h) for h in r.get("hosts") or ()]
        _episodes[ep_id] = {"id": ep_id, "view": view, "kind": "replay", "segs": story, "made": mono,
                            "ttl": LIVE_EP_TTL_S["now"], "stopped": False, "synth": [0] * len(story),
                            "played": False, "hosts": hosts, "voices": r.get("voices", 1),
                            "as_of": r.get("as_of"), "fp": r.get("fp")}
        while len(_episodes) > LIVE_EP_KEEP:
            _episodes.popitem(last=False)
    _log.info("piquesignal live episode: replay")
    return {"ok": True, "ep": ep_id, "view": view, "kind": "replay", "source": "replay",
            "segments": _seg_out(story), "caps": dict(LIVE_CAPS_OPEN), "hosts": hosts, "voices": r.get("voices", 1),
            "as_of": r.get("as_of")}
