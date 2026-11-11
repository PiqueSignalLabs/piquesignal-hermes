"""Row cleaning for the GATED board and Early Edge (member key views). Builds on rowclean.py (the exact copy of the
free-board service's cleaner) and adds ONLY the neutral gated reads the member feed sends
(its allow-list): read_state, ce_step, ce_step_index, ce_line, real_crowd, model_approved. Everything else is
dropped, so a source-revealing field (score, sig_count, social_buzz, flash_point, stacked, bail, top holders ...) can
never reach the panel even if a response carried it. Stdlib only.
"""
import importlib.util
import math
import re
from pathlib import Path


def _load_sibling(name):
    """The Hermes plugin host imports dashboard/plugin_api.py standalone (no package), so siblings load by path."""
    spec = importlib.util.spec_from_file_location("piquesignal_" + name, Path(__file__).resolve().parent / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_rc = _load_sibling("rowclean")

READ_STATES = frozenset({"climbing", "fading", "real", "rug", "tracking"})
CE_STEPS = frozenset({"flagged", "heating", "strong", "confirmed", "fading", "cooling", "floor", "early"})
CROWD_TIERS = frozenset({"clean", "borderline", "padded"})
_MINT_RE = _rc._MINT_RE
# the same tail rule as the server's member feed cleaner, exact
_CE_SOURCE_SUFFIX_RE = re.compile(r" (?:1 source|(?:[2-9]|[1-9][0-9]+) sources) on it\.\Z")


def _no_source(v, cap=400):
    """A Clear-Eyes / Real Crowd line with the source-count tail cut off (repeated, as the server's member feed cleaner does:
    a doubled tail can't survive). Second guard only (the server strips first): a line that still names a source
    count, or is empty after the cut, is dropped. Never reveals how many sources a signal has."""
    line = _rc._text(v, cap)
    if line is None:
        return None
    prev = None
    while prev != line:
        prev, line = line, _CE_SOURCE_SUFFIX_RE.sub("", line)
    if not line.strip() or "source on it" in line or "sources on it" in line:
        return None
    return line


def _int(v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        if isinstance(v, float) and math.isfinite(v) and v.is_integer():
            v = int(v)
        else:
            return None
    return v if lo <= v <= hi else None


def _real_crowd(v):
    if not isinstance(v, dict):
        return None
    out = {
        "real": _int(v.get("real"), 0, 10**9),
        "shown": _int(v.get("shown"), 0, 10**9),
        "pct": _rc._num(v.get("pct")),
        "tier": v.get("tier") if v.get("tier") in CROWD_TIERS else None,
        "padded": v.get("padded") if isinstance(v.get("padded"), bool) else None,
        "line": _no_source(v.get("line")),
    }
    out = {k: x for k, x in out.items() if x is not None}
    return out or None


def clean_gated_row(r):
    """A gated board row: the free cleaner first (same fields, same strict types), then the gated reads."""
    out = _rc.clean_row(r)
    if out is None:
        return None
    extra = {
        "read_state": r.get("read_state") if r.get("read_state") in READ_STATES else None,
        "ce_step": r.get("ce_step") if r.get("ce_step") in CE_STEPS else None,
        "ce_step_index": _int(r.get("ce_step_index"), 0, 3),
        "ce_line": _no_source(r.get("ce_line")),
        "real_crowd": _real_crowd(r.get("real_crowd")),
        "model_approved": r.get("model_approved") if isinstance(r.get("model_approved"), bool) else None,
    }
    out.update({k: v for k, v in extra.items() if v is not None})
    return out


def clean_edge_row(r):
    """An Early Edge row: exactly the 8 fields members see (the member feed's Early Edge allow-list)."""
    if not isinstance(r, dict):
        return None
    mint = r.get("mint")
    if not isinstance(mint, str) or not _MINT_RE.fullmatch(mint):
        return None
    out = {
        "mint": mint,
        "symbol": _rc._text(r.get("symbol"), 64),
        "name": _rc._text(r.get("name"), 128),
        "smart_wallets": _int(r.get("smart_wallets"), 0, 100000),
        "tier": _int(r.get("tier"), 0, 100),
        "backed": r.get("backed") if isinstance(r.get("backed"), bool) else None,
        "green_flag": r.get("green_flag") if isinstance(r.get("green_flag"), bool) else None,
        "committed": r.get("committed") if isinstance(r.get("committed"), bool) else None,
    }
    return {k: v for k, v in out.items() if v is not None}


_TIER_RE = re.compile(r"[a-z]{1,16}")


def clean_tier(v):
    return v if isinstance(v, str) and _TIER_RE.fullmatch(v) else None
