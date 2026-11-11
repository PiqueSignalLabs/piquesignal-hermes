"""The panel's SECOND lock for the keyless Hermes paths of the free-board service (Missed strip, Free Pick card,
banners, images): EXACT copies of the free-feed service's cleaners (freefeed/freefeed.py, section "HERMES cleaners").
test_hermes_live.py proves every function here has the same code as the server's (doc text
aside) and gives identical output on hostile input. Edit BOTH or neither. Stdlib only.
The text / number / URL rules are rowclean.py's (itself the exact copy of the server's field cleaner).
"""
import importlib.util
import re
from pathlib import Path


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location("piquesignal_" + name, Path(__file__).resolve().parent / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rc = _load_sibling("rowclean")
_num, _text, _URL_RE, _MINT_RE, SOCIAL_KEYS = _rc._num, _rc._text, _rc._URL_RE, _rc._MINT_RE, _rc.SOCIAL_KEYS

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


def _ce_line(v):
    line = _text(v, 300)
    if line is None:
        return None
    line = _CE_SOURCE_SUFFIX_RE.sub("", line)
    if "source on it" in line or "sources on it" in line or not line:
        return None
    return line


def clean_pick_card(card):
    """The free-pick card allowlist (the website's free-pick card minus dexPaid / realCrowd). A bad mint / sym /
    chain => None (the whole pick is null); any other bad value => that key is omitted. spark is always []."""
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
    if _int_only(idx) and 0 <= idx <= 10:
        out["ceStepIndex"] = idx
    line = _ce_line(card.get("ceLine"))
    if line is not None:
        out["ceLine"] = line
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
