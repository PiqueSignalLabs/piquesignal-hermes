"""The panel's SECOND lock for the keyless Hermes paths of the free-board service (Missed strip, Free Pick card,
banners, images, and the free board's Featured Callers): EXACT copies of the free-feed service's cleaners
(freefeed/freefeed.py, section "HERMES cleaners"). test_hermes_live.py proves every function here has the same code as
the server's (doc text aside) and gives identical output on hostile input. Edit BOTH or neither. Stdlib only.
The text / number / URL rules are rowclean.py's (itself the exact copy of the server's field cleaner).
"""
import importlib.util
import re
import unicodedata
from pathlib import Path


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location("piquesignal_" + name, Path(__file__).resolve().parent / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rc = _load_sibling("rowclean")
_num, _text, _URL_RE, _MINT_RE, SOCIAL_KEYS = _rc._num, _rc._text, _rc._URL_RE, _rc._MINT_RE, _rc.SOCIAL_KEYS
_BAD_CHARS, _BAD_CATEGORIES = _rc._BAD_CHARS, _rc._BAD_CATEGORIES      # the label / Telegram-text cleaners use them

IMG_PREFIX = "/api/free-board/img/"
_LOGO_KEY_RE = re.compile(r"[0-9a-f]{16}\Z")
CT_MAGIC = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff", "image/webp": None}   # webp: RIFF....WEBP
LOGO_MAX = 65536; BANNER_MAX = 2_000_000
MISSED_MAX = 5
BANNERS_MAX = 5
MISSED_TIERS = frozenset({"strong", "solid", "watch"})
CE_STEPS = frozenset({"flagged", "heating", "strong", "confirmed", "fading", "cooling", "floor", "early"})   # = gatedclean.py
# the same tail rule as the server's member feed cleaner, exact
_CE_SOURCE_SUFFIX_RE = re.compile(r" (?:1 source|(?:[2-9]|[1-9][0-9]+) sources) on it\.\Z")
_BANNER_IMG_RE = re.compile(r"/api/free-board/img/b([0-9]{1,9})-([0-9a-f]{12})\Z")
_BANNER_LINK_RE = re.compile(r"https://[^\s\"'<>\\`]+\Z")
_SHA12_RE = re.compile(r"[0-9a-f]{12}\Z")
PICK_STR_FIELDS = ("age", "tokenAge", "flagMc", "mcap", "liq", "holdersCount", "holders", "txns5m", "top10", "bundles",
                   "snipers", "vol5m", "vol1h", "vol24h")
# The free pick also carries dexPaid / feeRug / feeRugFlicker / realCrowd, ceLine is kept WHOLE (at most
# ONE " N sources on it." tail), ceStepIndex is 0..3 (the website makes 0..3 only).
CE_INDEX_MAX = 3
CROWD_TIERS = frozenset({"clean", "borderline", "padded"})
CROWD_KEYS = frozenset({"real", "shown", "pct", "tier", "padded", "line"})    # = the website's realCrowd keys
CROWD_SHOWN_MAX = 10 ** 12
# Keyless Featured Callers on the free board (the member contract's body, rebuilt by the server's cleaner)
FEATURED_CALLERS_MAX = 10
FEATURED_CALLS_MAX = 20
FEATURED_LABEL_MAX = 200
FEATURED_SYMBOL_MAX = 64
FEATURED_ESSENCE_MAX = 150
FEATURED_BODY_MAX = 600
_FEAT_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)   # the pull API's 2nd URL guard, here case-insensitive
# link forms WITHOUT a scheme + script-like schemes, removed from essence / body too ("Text only: no links")
_FEAT_LINK_RE = re.compile(r"(?i)\b(?:www\.|t\.me/|telegram\.(?:me|dog)/)\S+|\b(?:javascript|vbscript|data|tg):\S+")
_WS_RE = re.compile(r"\s+")   # _no_src squashes every run of white space (also after NFKD folding)
_FEAT_DATE_RE = re.compile(r"[A-Z][a-z]{2} [0-9]{1,2}\Z")
_FEAT_TS_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:[+-][0-9]{2}:[0-9]{2}|Z)?\Z")
_FEAT_MULT_RE = re.compile(r"[0-9]+(?:\.[0-9]+)?x\Z")


# ----------------------------------------------------------------------------------------------- exact server copies
def _int_only(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _https(v, maxlen=300):
    v = _text(v, maxlen)
    return v if v is not None and v.startswith("https://") and _URL_RE.fullmatch(v) else None


def clean_missed_item(it):
    """ONE missed-strip item -> {gain, ageMins, img?, tier, rising} or None (dropped). Never a mint / symbol / name."""
    if not isinstance(it, dict):
        return None
    gain = _num(it.get("gain"))
    if gain is None or not 1 <= gain <= 1e6:
        return None
    age = it.get("ageMins")
    if not _int_only(age) or not 0 <= age <= 10_000_000:
        return None
    tier = it.get("tier")
    if not isinstance(tier, str) or tier not in MISSED_TIERS:
        return None
    out = {"gain": gain, "ageMins": age}
    img = it.get("img")
    if isinstance(img, str) and _LOGO_KEY_RE.fullmatch(img):
        out["img"] = img
    out["tier"] = tier
    out["rising"] = it.get("rising") if isinstance(it.get("rising"), bool) else False
    return out


def clean_missed(items):
    if not isinstance(items, list):
        return []
    return [c for c in (clean_missed_item(it) for it in items[:MISSED_MAX]) if c is not None]


def _no_src(s):
    """True when the text carries no source-count phrase ("source on it" / "sources on it", any case), checked on the
    text as it is AND after NFKD folding with every run of white space squashed to one space (so no
    look-alike letter, odd space or double space passes)."""
    for low in (s.lower(), _WS_RE.sub(" ", unicodedata.normalize("NFKD", s)).lower()):
        if "source on it" in low or "sources on it" in low:
            return False
    return True


def _ce_line(v):
    """The WHOLE Clear-Eyes line or None: at most 300 characters of clean text; at most ONE tail of
    the exact board form (_CE_SOURCE_SUFFIX_RE, anchored at the end) and nothing source-like before it; never blank."""
    line = _text(v, 300)
    if line is None:
        return None
    m = _CE_SOURCE_SUFFIX_RE.search(line)
    head = line[:m.start()] if m else line
    if not head.strip() or not _no_src(head):
        return None
    return line


def _pick_crowd(v):
    """The website's realCrowd {real, shown, pct, tier, padded, line?}, ALL or NOTHING: real / shown / pct strict ints
    (never bool / float), 0 <= real <= shown, 1 <= shown <= 10^12, 0 <= pct <= 100, tier in CROWD_TIERS, padded a bool,
    no other key. line is optional: kept only as clean text <= 300 with no source phrase (else only the line is left
    out). padded is NOT checked against tier (the website's env limits decide that)."""
    if not isinstance(v, dict) or not set(v) <= CROWD_KEYS:
        return None
    real, shown, pct, tier, padded = v.get("real"), v.get("shown"), v.get("pct"), v.get("tier"), v.get("padded")
    if not (_int_only(real) and _int_only(shown) and _int_only(pct)):
        return None
    if not (1 <= shown <= CROWD_SHOWN_MAX and 0 <= real <= shown and 0 <= pct <= 100):
        return None
    if not isinstance(tier, str) or tier not in CROWD_TIERS or not isinstance(padded, bool):
        return None
    out = {"real": real, "shown": shown, "pct": pct, "tier": tier, "padded": padded}
    line = _text(v.get("line"), 300)
    if line is not None and _no_src(line):
        out["line"] = line
    return out


def clean_pick_card(card):
    """The free-pick card allowlist (the website's free-pick card, with dexPaid, feeRug / feeRugFlicker
    (only True; red feeRug wins), realCrowd (all or nothing); the whole ceLine). A bad mint / sym / chain => None (the
    whole pick is null); any other bad value => that key is omitted. spark is always []."""
    if not isinstance(card, dict):
        return None
    mint, sym = card.get("mint"), _text(card.get("sym"), 65)
    if not isinstance(mint, str) or not _MINT_RE.fullmatch(mint) or sym is None or card.get("chain") != "SOL":
        return None
    out = {"mint": mint, "sym": sym}
    name = card.get("name")
    if name == "":
        out["name"] = ""
    elif _text(name, 128) is not None:
        out["name"] = name
    out["chain"] = "SOL"
    for k in PICK_STR_FIELDS:
        v = card.get(k)
        if v == "":
            out[k] = ""
        elif _text(v, 32) is not None:
            out[k] = v
    if isinstance(card.get("fresh"), bool):
        out["fresh"] = card["fresh"]
    pct = card.get("pct")
    if _int_only(pct) and abs(pct) <= 1_000_000_000:
        out["pct"] = pct
    out["spark"] = []
    so = card.get("socials")
    socials = {}
    if isinstance(so, dict):
        for sk in SOCIAL_KEYS:
            u = _https(so.get(sk))
            if u is not None:
                socials[sk] = u
    out["socials"] = socials
    step = card.get("ceStep")
    if isinstance(step, str) and step in CE_STEPS:
        out["ceStep"] = step
    idx = card.get("ceStepIndex")
    if _int_only(idx) and 0 <= idx <= CE_INDEX_MAX:
        out["ceStepIndex"] = idx
    line = _ce_line(card.get("ceLine"))
    if line is not None:
        out["ceLine"] = line
    if isinstance(card.get("dexPaid"), bool):
        out["dexPaid"] = card["dexPaid"]
    if card.get("feeRug") is True:
        out["feeRug"] = True
    elif card.get("feeRugFlicker") is True:
        out["feeRugFlicker"] = True
    crowd = _pick_crowd(card.get("realCrowd"))
    if crowd is not None:
        out["realCrowd"] = crowd
    return out


def clean_banner(it):
    """ONE banner -> {id, img, v?, link, title, weight, w?, h?} or None (dropped). Never counters / advertiser data."""
    if not isinstance(it, dict):
        return None
    bid, img = it.get("id"), it.get("img")
    if not _int_only(bid) or not 1 <= bid <= 999_999_999:
        return None
    m = _BANNER_IMG_RE.fullmatch(img) if isinstance(img, str) else None
    if m is None or m.group(1) != str(bid):
        return None
    link = _text(it.get("link"), 500)
    if link is None or not _BANNER_LINK_RE.fullmatch(link):
        return None
    out = {"id": bid, "img": img}
    v = it.get("v")
    if isinstance(v, str) and _SHA12_RE.fullmatch(v):
        out["v"] = v
    out["link"] = link
    title = _text(it.get("title"), 120)
    out["title"] = title if title is not None else ""
    w8 = _num(it.get("weight"))
    out["weight"] = w8 if w8 is not None and 0 <= w8 <= 1e6 else 0
    for k in ("w", "h"):
        x = it.get(k)
        if _int_only(x) and 1 <= x <= 10000:
            out[k] = x
    return out


def clean_banners(items):
    if not isinstance(items, list):
        return []
    return [c for c in (clean_banner(it) for it in items[:BANNERS_MAX]) if c is not None]


def _feat_label(v, cap=FEATURED_LABEL_MAX):
    """A caller label, CLEANED (never a reason to drop the caller by itself): not a str -> ""; every control / format /
    private-use / line-break character, filler and < > ` removed; trimmed; cut to cap; a source phrase or a
    URL left in it => "" (an empty key / name then drops the caller)."""
    if not isinstance(v, str):
        return ""
    v = v[:cap * 4]
    out = "".join(ch for ch in v if not (ch in _BAD_CHARS or unicodedata.category(ch) in _BAD_CATEGORIES))
    out = out.strip()[:cap]
    return out if _no_src(out) and not _FEAT_URL_RE.search(out) else ""


def _feat_long_text(v, cap):
    """Telegram text (essence / body): line breaks kept, every other bad character removed FIRST, then every URL removed
    (any case), then every scheme-less link (_FEAT_LINK_RE), trimmed, cut to cap; a source phrase (checked on
    the FINAL text) => "". Else ""."""
    if not isinstance(v, str):
        return ""
    v = v[:cap * 4].replace("\r\n", "\n")
    out = "".join(ch for ch in v if ch == "\n" or not (ch in _BAD_CHARS or unicodedata.category(ch) in _BAD_CATEGORIES))
    out = _FEAT_LINK_RE.sub("", _FEAT_URL_RE.sub("", out)).strip()[:cap]
    return out if _no_src(out) else ""


def clean_featured(fe):
    """doc["featured"] -> {"count", "callers": [<= 10 x {key, name, handle, tagline, count, calls: [<= 20 x {symbol,
    mint, date?, ts?, essence, body, mult?}]}]} or None (missing / corrupt => /featured answers 503). The member contract
    (the server's order kept, newest first); recaps / channel / any other key never pass. A caller is dropped when
    its key or name is empty after cleaning; a call when its mint is not base58 32-44 or its symbol is not clean text
    <= 64 with no source phrase and no URL."""
    if not isinstance(fe, dict) or not isinstance(fe.get("callers"), list):
        return None
    callers = []
    for c in fe["callers"][:FEATURED_CALLERS_MAX]:
        if not isinstance(c, dict) or not isinstance(c.get("calls"), list):
            continue
        key, name = _feat_label(c.get("key")), _feat_label(c.get("name"))
        if not key or not name:
            continue
        calls = []
        for x in c["calls"][:FEATURED_CALLS_MAX]:
            if not isinstance(x, dict):
                continue
            mint, sym = x.get("mint"), _text(x.get("symbol"), FEATURED_SYMBOL_MAX)
            if not (isinstance(mint, str) and _MINT_RE.fullmatch(mint)) or sym is None or not _no_src(sym) \
                    or _FEAT_URL_RE.search(sym):
                continue
            call = {"symbol": sym, "mint": mint}
            for k, rx in (("date", _FEAT_DATE_RE), ("ts", _FEAT_TS_RE)):
                if isinstance(x.get(k), str) and rx.fullmatch(x[k]):
                    call[k] = x[k]
            call["essence"] = _feat_long_text(x.get("essence"), FEATURED_ESSENCE_MAX)
            call["body"] = _feat_long_text(x.get("body"), FEATURED_BODY_MAX)
            if isinstance(x.get("mult"), str) and _FEAT_MULT_RE.fullmatch(x["mult"]):
                call["mult"] = x["mult"]
            calls.append(call)
        callers.append({"key": key, "name": name, "handle": _feat_label(c.get("handle")),
                        "tagline": _feat_label(c.get("tagline")), "count": len(calls), "calls": calls})
    return {"count": len(callers), "callers": callers}


def img_ok(key, ctype, data):
    """Re-check ONE image row before it is cached / served: ctype in CT_MAGIC, the format's magic, logo = PNG <= 64 KB,
    banner <= 2 MB."""
    if ctype not in CT_MAGIC or not isinstance(data, (bytes, bytearray)) or not data:
        return False
    magic = CT_MAGIC[ctype]
    if magic is None:
        if not (len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"):
            return False
    elif not data.startswith(magic):
        return False
    if _LOGO_KEY_RE.fullmatch(key):
        return ctype == "image/png" and len(data) <= LOGO_MAX
    return len(data) <= BANNER_MAX
