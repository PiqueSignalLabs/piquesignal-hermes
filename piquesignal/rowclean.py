"""Row cleaning for the Hermes panel: an EXACT copy of the free-board service's cleaner (freefeed/freefeed.py,
section "field cleaning"), so the panel's second lock is never weaker than the server's first one.
test_freeboard_client.py proves the two give identical output on hostile input. Edit BOTH or neither.
Stdlib only.
"""
import math
import re
import unicodedata

NUM_FIELDS = frozenset({
    "age_secs", "token_age_secs", "entry_mcap_usd", "current_mcap", "holders", "entry_holders", "liquidity_usd",
    "txns_5m", "top_10_holder_pct", "coord_pct", "sniper_owned_pct", "volume_5m", "volume_1h", "volume_24h", "pct",
})
BOOL_FIELDS = frozenset({"dex_paid", "fee_rug", "fee_rug_flicker"})
TEXT_FIELDS = {"symbol": 64, "name": 128}           # field -> max length
URL_FIELDS = frozenset({"telegram_url", "website_url"})
OTHER_FIELDS = frozenset({"mint", "chain", "twitter_handle", "socials"})
FREE_FIELDS = NUM_FIELDS | BOOL_FIELDS | frozenset(TEXT_FIELDS) | URL_FIELDS | OTHER_FIELDS
SOCIAL_KEYS = ("x", "tg", "web")
BLANKED_FIELDS = frozenset()   # none: top_10_holder_pct is already the clean value (or absent) on the snapshot (the same rule as the website's own cell)

_MINT_RE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
_HANDLE_RE = re.compile(r"@?[A-Za-z0-9_]{1,15}")
_SOCIAL_HANDLE_RE = re.compile(r"@?[A-Za-z0-9_.\-]{1,64}")
_CHAIN_RE = re.compile(r"[a-z]{1,16}")
# Unicode categories never allowed in any text: control, format (bidi marks, zero-width, BOM ...), private use,
# surrogates, line/paragraph separators. Plus the HTML/markup characters < > and the backtick.
_BAD_CATEGORIES = frozenset({"Cc", "Cf", "Co", "Cs", "Zl", "Zp"})
# + known invisible "filler" letters/marks outside those categories (combining grapheme joiner, Hangul fillers,
#   Khmer inherent vowels, Mongolian vowel separator).
_BAD_CHARS = frozenset("<>`") | frozenset(chr(c) for c in (0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x180E, 0x3164,
                                                            0xFFA0))
_URL_RE = re.compile(r"https?://[^\s\"'<>\\`]{1,290}", re.IGNORECASE)
_MAX_ABS_NUM = 1e15


# ----------------------------------------------------------------------------------------------- field cleaning
def _num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v if abs(v) <= _MAX_ABS_NUM else None
    if isinstance(v, float):
        return v if math.isfinite(v) and abs(v) <= _MAX_ABS_NUM else None
    return None


def _text(v, maxlen):
    if not isinstance(v, str) or not v or len(v) > maxlen:
        return None
    for ch in v:
        if ch in _BAD_CHARS or unicodedata.category(ch) in _BAD_CATEGORIES:
            return None
    return v


def _url(v):
    v = _text(v, 300)
    return v if v is not None and _URL_RE.fullmatch(v) else None


def _social(v):
    v = _text(v, 300)
    if v is None:
        return None
    return v if (_URL_RE.fullmatch(v) or _SOCIAL_HANDLE_RE.fullmatch(v)) else None


def clean_row(r):
    """Rebuild ONE snapshot row from the FREE allowlist. Returns None when the row has no valid mint."""
    if not isinstance(r, dict):
        return None
    mint = r.get("mint")
    if not isinstance(mint, str) or not _MINT_RE.fullmatch(mint):
        return None
    out = {"mint": mint}
    for k in sorted(FREE_FIELDS - {"mint"}):
        if k not in r:
            continue
        v = r[k]
        if k in BLANKED_FIELDS:
            out[k] = None
            continue
        if k in NUM_FIELDS:
            c = _num(v)
        elif k in BOOL_FIELDS:
            c = v if isinstance(v, bool) else None
        elif k in TEXT_FIELDS:
            c = _text(v, TEXT_FIELDS[k])
        elif k in URL_FIELDS:
            c = _url(v)
        elif k == "chain":
            c = v if isinstance(v, str) and _CHAIN_RE.fullmatch(v) else None
        elif k == "twitter_handle":
            c = v if isinstance(v, str) and (_HANDLE_RE.fullmatch(v) or _url(v)) else None
        elif k == "socials":
            c = None
            if isinstance(v, dict):
                c = {sk: _social(v.get(sk)) for sk in SOCIAL_KEYS}
                c = {sk: sv for sk, sv in c.items() if sv is not None} or None
        else:   # unreachable: every FREE_FIELDS key is handled above
            c = None
        if c is not None:
            out[k] = c
    return out


