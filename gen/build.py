"""Assemble desktop/plugin.js = imports + generated website board engines (engine_parts.js) + the pinned chart library
(vendor/, in its own private scope) + plugin.src.js.
The plugin part ships without its comments (strip_comments.mjs, Node's own parser, proves only comments changed).
Fails on any pattern the Hermes desktop validator refuses, and on board markup that could run or load anything.
Usage: py build.py"""
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))          # gen_engine.py sits next to this file (also under "py -I build.py")
from gen_engine import skeleton_problems, strip_js_comments  # noqa: E402
OUT = HERE.parent / "piquesignal" / "desktop" / "plugin.js"
HEADER = """// PiqueSignal for Hermes Desktop. Plain ESM, no build tooling needed to run; imports ONLY 'react' and '@hermes/plugin-sdk'.
// This file is ASSEMBLED by plugin/gen/build.py from: the website board engines (generated from the after-go-live website
// pages by gen_engine.py + gen_css.py), the pinned TradingView Lightweight Charts library (in its own scope) and the
// hand-written plugin part (plugin.src.js, shipped here without its comments). Edit those, then rebuild.
import { createElement as h, useEffect, useMemo, useRef, useState } from 'react'
import { host, useQuery } from '@hermes/plugin-sdk'
"""
BANNED = [r"\beval\s*\(", r"new\s+Function", r"\bimport\s*\(", r"createElement\(\s*['\"]script", r"<script", r"\.observe\(\s*document\.body",
          r"querySelector(All)?\(\s*['\"]\[data-(slot|tour|sidebar|testid)", r"getElementsByTagName\(\s*['\"]webview",
          r"(?<![\w$.])(parent|frames|opener)\s*\.", r"\bopener\b", r"\b(Shared)?Worker\s*\(", r"getRootNode",
          r"ownerDocument", r"defaultView", r"\bglobalThis\b", r"sendBeacon", r"new\s+Image\b", r"\bself\.", r"\btop\.",
          r"createElement(NS)?\([^)]*['\"](iframe|object|embed|frame|base|link|meta|form|foreignObject)['\"]",
          r"/api/app2/banner/"]   # the website's banner view / click counter: never in the plugin
# TradingView Lightweight Charts 5.3.0 (Apache-2.0; npm tarball sha512 checked), shipped byte for byte except its
# final "export {...}" statement: it runs inside its own function scope and only VENDOR_NAMES leave it (as LWC).
# The build stops unless the file's sha256 is exactly the pinned one, so a changed library never ships unreviewed.
VENDOR = HERE / "vendor" / "lightweight-charts.standalone.production.mjs"
VENDOR_SHA256 = "0b6d1ed409283a0f9a493a99dcf11c650e111d0c61619cd922198975fb82fa99"
VENDOR_NAMES = ("createChart", "CandlestickSeries", "HistogramSeries", "createSeriesMarkers")
VENDOR_BEGIN = ("// ---- vendored: TradingView Lightweight Charts v5.3.0 (Apache-2.0, piquesignal/licenses/lightweight-charts-LICENSE.txt; "
                "its bundled fancy-canvas 2.1.0: MIT, piquesignal/licenses/fancy-canvas-LICENSE.txt), pinned sha256 " + VENDOR_SHA256 +
                " (of the npm file dist/lightweight-charts.standalone.production.mjs); changed here only: its final export statement "
                "replaced by a private scope (LWC)\n")
VENDOR_END = "// ---- end of vendored TradingView Lightweight Charts\n"
# The ONLY exception to BANNED, and only inside that pinned block: 4 of our own extra bans that the library trips and that
# are not in Hermes' list. .observe(document.body, {box: ...}) = a ResizeObserver feature test (not a MutationObserver);
# ownerDocument / defaultView = its canvas helper finding the element's window; new Image = its image-watermark helper
# (never used here). Every other BANNED pattern still runs on the block, and HERMES_RULES run on everything.
VENDOR_EXCEPT = (r"\.observe\(\s*document\.body", r"ownerDocument", r"defaultView", r"new\s+Image\b")
# Hermes' own desktop validator (hermes_cli/plugin_validate_desktop.py _FORBIDDEN), run on the vendored block as it is and
# on everything outside it (no exception)
HERMES_RULES = [r"(?<![\w$.])eval\(|\bnew\s+Function\(", r"\bimport\(", r"\bimport\s+(?:[^;'\"]*?\bfrom\s*)?['\"][a-zA-Z][\w+.-]*:",
                r"createElement\(\s*['\"]script['\"]\s*\)|<script\b",
                r"\bdocument\.(?:querySelector(?:All)?|getElementsBy\w+|getElementById)\(\s*[`'\"][^`'\"]*\[data-(?:slot|tour|sidebar|testid)\b",
                r"\.observe\(\s*document\.body\s*,\s*\{[^}]*\b(?:childList|subtree)\b",
                r"\b(?:querySelector(?:All)?|closest|getElementsByTagName|createElement)\(\s*[`'\"]webview\b"]


def vendor_block():
    """The pinned library as one private scope: const LWC = (() => { <the file without its export statement> return {...} })()"""
    raw = VENDOR.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    if got != VENDOR_SHA256:
        raise SystemExit("STOP the vendored chart library changed: sha256 %s, pinned %s" % (got, VENDOR_SHA256))
    text = raw.decode("utf-8")
    ex = list(re.finditer(r"\bexport\s*\{([^}]*)\};?\s*$", text))
    if len(ex) != 1 or len(re.findall(r"\bexport\b", text)) != 1 or re.search(r"^\s*import\b", text, re.M):
        raise SystemExit("STOP the vendored chart library is not one plain module with one final export statement")
    names = {}
    for part in ex[0].group(1).split(","):
        m = re.fullmatch(r"\s*([A-Za-z_$][\w$]*)\s+as\s+([A-Za-z_$][\w$]*)\s*", part)
        if not m:
            raise SystemExit("STOP unexpected export item in the vendored chart library: %r" % part)
        names[m.group(2)] = m.group(1)
    if any(n not in names for n in VENDOR_NAMES):
        raise SystemExit("STOP the vendored chart library lacks %s" % [n for n in VENDOR_NAMES if n not in names])
    body = text[:ex[0].start()]
    if not body.startswith("/*!\n * @license\n * TradingView Lightweight Charts"):
        raise SystemExit("STOP the vendored chart library lost its licence header")
    out = ("const LWC = (() => {\n" + body.rstrip() + "\nreturn Object.freeze({ " +
           ", ".join("%s: %s" % (n, names[n]) for n in VENDOR_NAMES) + " })\n})()\n")
    return VENDOR_BEGIN + out + VENDOR_END


def banned_problems(src):
    """Every BANNED hit in the assembled source (the 4 VENDOR_EXCEPT patterns skip ONLY the one pinned vendored block)
    and every HERMES_RULES hit, in that block and outside it. Returns the problems found; an empty list = clean."""
    if src.count(VENDOR_BEGIN) != 1 or src.count(VENDOR_END) != 1 or src.index(VENDOR_BEGIN) > src.index(VENDOR_END):
        return ["the vendored chart block markers must be there exactly once, in order"]
    a = src.index(VENDOR_BEGIN)
    b = src.index(VENDOR_END) + len(VENDOR_END)
    block = src[a:b]
    out = [] if block == vendor_block() else ["the vendored chart block is not the pinned library"]
    outside = src[:a] + "\n" + src[b:]
    for pat in BANNED:
        hay = outside if pat in VENDOR_EXCEPT else src
        m = re.search(pat, hay)
        if m:
            out.append("banned pattern %r at %d: %s" % (pat, m.start(), hay[max(0, m.start()-60):m.start()+60]))
    for pat in HERMES_RULES:
        for where, hay in (("the vendored chart block", block), ("the plugin outside it", outside)):
            m = re.search(pat, hay)
            if m:
                out.append("Hermes desktop rule %r in %s: %s" % (pat, where, hay[max(0, m.start()-60):m.start()+60]))
    return out


def main():
    engines = (HERE / "engine_parts.js").read_text(encoding="utf-8")
    # the 4 board markups (inserted with innerHTML into the Hermes window): inside the markup allow-list (gen_engine.py)
    skeletons = re.findall(r"^const SKELETON_(\w+) = (\".*\");\r?$", engines, re.M)
    if sorted(k for k, _ in skeletons) != ["d_free", "d_gated", "m_free", "m_gated"]:
        raise SystemExit("STOP the 4 board markups were not all found in engine_parts.js: %s" % [k for k, _ in skeletons])
    for key, lit in skeletons:
        bad = skeleton_problems(json.loads(lit))
        if bad:
            raise SystemExit("STOP the %s board markup is outside the markup allow-list: %s" % (key, "; ".join(bad[:5])))
    own = strip_js_comments((HERE / "plugin.src.js").read_text(encoding="utf-8"), module=True)
    src = HEADER + "\n" + engines + "\n" + vendor_block() + "\n" + own
    bad = banned_problems(src)
    if bad:
        raise SystemExit("STOP " + bad[0])
    imports = re.findall(r"^\s*import\s.*?from\s+['\"]([^'\"]+)['\"]", src, re.M)
    if not set(imports) <= {"react", "@hermes/plugin-sdk"}:
        raise SystemExit("STOP imports other than react / @hermes/plugin-sdk: %s" % sorted(set(imports)))
    OUT.write_text(src, encoding="utf-8", newline="\n")
    print("wrote", OUT, len(src), "chars; imports:", sorted(set(imports)))


if __name__ == "__main__":
    main()
