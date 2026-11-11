"""Build plugin/gen/engine_parts.js from the after-go-live website board pages (the exact versions are pinned by md5 in
PAGES below): for each of the 4 pages, (1) the board SKELETON (the page's <body> markup without scripts, styles and the
website-only parts), (2) the page's scoped CSS (from gen_css.py output), (3) a FACTORY function that runs the page's OWN
board scripts inside a sealed scope whose `document`, `window`, `localStorage`, `fetch`, `location`, `navigator` and
timers are the plugin's safe stand-ins (plugin.src.js). The scripts are the website's own code with only the listed
changes: the baked coin list emptied, the CUTS and SUBS below, and every comment removed. Nothing is eval'd: the script
text is embedded as code.

Only these scripts are taken (index = order of <script> tags in the page): the main board script (its baked FEED snapshot of
real coins is replaced by []), the back-to-top script, and on phone pages the status-line fit script. Everything else
(analytics + cookie consent, banners, sign-in, pay gate, the bell's website alerts / push, affiliate bind, Early Edge left panel, ANSEM gate) is
NOT included. Every comment is removed from the taken scripts (strip_comments.mjs, Node's own parser, proven to change
nothing else), and each factory also returns BOARD_HANDLE (filters / saved coins, see HANDLE_JS).
The build fails if a banned pattern (eval, new Function, dynamic import, script elements) shows up, or if the board
markup (inserted with innerHTML) has anything outside its allow-list (skeleton_problems: only the elements, attributes
and links today's pages use; never an inline on*= handler, a javascript: link, a src or style attribute, an encoded
character or an element that loads or sends something).
Usage: py gen_engine.py <dir with the 4 pages> <dir with the 4 css files> <out.js>
"""
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path

PAGES = {
    # key: (file, expected md5 (the pinned page version), variant, view, script indexes)
    "d_free": ("free_desktop.html", "b349fe23", "desktop", "free", [3, 4]),
    "d_gated": ("gated_desktop.html", "0ec65099", "desktop", "gated", [4, 7, 11]),   # 11 = the Early Edge left panel
    "m_free": ("free_page.html", "2bca70ce", "phone", "free", [3, 4, 10]),
    "m_gated": ("gated_page.html", "11931b6b", "phone", "gated", [2, 5, 11]),
}
# Markup removed from the skeleton: website-only, needs sign-in / website data.
DROP_IDS = ["ansemGate"]   # the alerts bell stays: in the plugin it switches the new-call pop-ups (plugin.src.js)
BANNED = [r"\beval\s*\(", r"new\s+Function", r"\bimport\s*\(", r"createElement\(\s*['\"]script", r"<script", r"</script",
          r"\.observe\(\s*document\.body",
          # escape routes out of the sealed scope: none of these may appear in a board script
          r"(?<![\w$.])(parent|frames|opener)\s*\.", r"\bopener\b", r"\b(Shared)?Worker\s*\(", r"getRootNode",
          r"ownerDocument", r"defaultView", r"\bglobalThis\b", r"sendBeacon", r"new\s+Image\b", r"\bself\.", r"\btop\.",
          r"createElement(NS)?\([^)]*['\"](iframe|object|embed|frame|base|link|meta|form|foreignObject)['\"]",
          # the website's banner view / click counter: never in a board script (banners are read only)
          r"/api/app2/banner/"]
# NOT banned on purpose: a board script may set an img src (the website's "Missed" panel sets a relative one,
# '/api/app2/missed-img/...'; the board cards load the coin's dexscreener picture). While HERMES_LIVE is false the
# board's <img> is the plain element (as on the website); while it is true every <img> a board script makes is guarded
# (plugin.src.js guardImg): only the Missed address (as the backend's data: URL) and the exact dexscreener coin picture load.
# The board markup itself is inserted with innerHTML into the Hermes window, so it is held to two stricter checks (it is
# clean today; a page that adds anything else stops the build and is looked at by hand):
#  * an ALLOW-list (skeleton_problems): only the elements and attributes today's 4 board markups use (plus aria-* and
#    data-*), every link an https:// address, a path on the site or a #fragment; no style attribute, no comment;
#  * a deny-list (SKELETON_BANNED) on the raw text, for anything a parser might read differently: no inline event
#    handler, no javascript: / vbscript: link (also with spaces or tabs inside the word), no src attribute, no encoded
#    character, no element that loads or sends.
SKELETON_BANNED = [r"(?i)[\s/\"']on[a-z]+\s*=", r"(?i)(j\s*a\s*v\s*a|v\s*b)\s*s\s*c\s*r\s*i\s*p\s*t\s*:",
                   r"(?i)[\s/\"'](src|srcset|srcdoc|poster|background|style)\s*=", r"(?i)url\s*\(",
                   r"(?i)&#|&(colon|tab|newline);",
                   r"(?i)<(iframe|object|embed|frame|frameset|base|link|meta|form|script|style|img|image|video|audio|source|track|picture|use)\b"]
SKELETON_TAGS = {"div", "header", "span", "a", "svg", "rect", "path", "nav", "input", "button", "main", "footer"}
SKELETON_ATTRS = {"class", "role", "id", "type", "href", "target", "rel", "tabindex", "placeholder", "maxlength", "hidden",
                  "autocomplete", "autocapitalize", "spellcheck", "focusable", "viewbox", "width", "height", "fill",
                  "stroke", "stroke-width", "x", "y", "rx", "d"}
# every id becomes a named property of the Hermes window / document: only the ids today's 4 board markups use
SKELETON_IDS = {"count", "fcount", "filters", "freePick", "modal", "overlay", "plat", "pqAcctLink", "pqBell", "pqBellBadge",
                "pqBellPanel", "pqBellWrap", "pqCookieLink", "pqbar", "pqinfo", "pqtrio", "qclear", "qsearch", "ticker",
                "tkMove", "toTop", "toolbar", "upd", "wall"}
_SKELETON_HREF = re.compile(r"(https://[^\s\"'<>\\]+|/(?![/\\])[^\s\"'<>\\]*|#[^\s\"'<>\\]*)")


class _SkeletonCheck(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag not in SKELETON_TAGS:
            self.problems.append("element <%s>" % tag)
        for name, value in attrs:
            if not (name in SKELETON_ATTRS or re.fullmatch(r"(aria|data)-[a-z0-9-]+", name)):
                self.problems.append("attribute %s on <%s>" % (name, tag))
            elif name == "href" and not _SKELETON_HREF.fullmatch(value or ""):
                self.problems.append("link %r" % (value or "")[:60])
            elif name == "id" and value not in SKELETON_IDS:
                self.problems.append("id %r" % (value or "")[:40])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag not in SKELETON_TAGS:
            self.problems.append("element </%s>" % tag)

    def handle_comment(self, data):
        self.problems.append("comment")

    def handle_decl(self, decl):
        self.problems.append("declaration")

    def handle_pi(self, data):
        self.problems.append("processing instruction")

    def unknown_decl(self, data):
        self.problems.append("declaration")


def skeleton_problems(html):
    """Everything in a board markup outside the allow-list (empty list = clean)."""
    c = _SkeletonCheck()
    c.feed(html)
    c.close()
    return c.problems + ["pattern %r" % pat for pat in SKELETON_BANNED if re.search(pat, html)]
FACTORY_PARAMS = ["document", "window", "localStorage", "sessionStorage", "fetch", "location", "navigator", "setTimeout",
                  "setInterval", "clearTimeout", "clearInterval", "requestAnimationFrame", "cancelAnimationFrame",
                  "ResizeObserver", "MutationObserver", "getComputedStyle", "confirm", "alert", "history", "XMLHttpRequest",
                  "WebSocket", "EventSource", "open"]


def drop_element_by_id(html, el_id):
    m = re.search(r'<(\w+)[^>]*\bid="%s"' % re.escape(el_id), html)
    if not m:
        return html
    tag = m.group(1)
    i = m.start(); depth = 0
    for t in re.finditer(r"<(/?)%s\b[^>]*>" % tag, html[i:]):
        depth += -1 if t.group(1) else 1
        if depth == 0:
            return html[:i] + html[i + t.end():]
    raise ValueError("unbalanced " + el_id)


def skeleton(html):
    body = re.search(r"<body[^>]*>(.*)</body>", html, re.S).group(1)
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.S)
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
    for i in DROP_IDS:
        body = drop_element_by_id(body, i)
    body = re.sub(r">\s+<", "><", body).strip()
    return body


MARKERS = [r"var FEED\s*=", r'getElementById\("toTop"\)', r"SB-1017 narrow|/\* Early Edge left panel"]   # main board, back-to-top, phone status fit OR desktop Early Edge panel
# The main board script must still define what the plugin's board handle (HANDLE_JS) uses.
BOARD_NAMES = [r"\bvar LEAD\s*=\s*\[", r"\bvar MORE\s*=\s*\[", r"\bvar ALLF\s*=", r"\bvar FSTATE\s*=\s*\{\}", r"\bfunction fActive\(",
               r"\bfunction renderFilters\(", r"\bfunction applyFilters\(", r"\bvar SAVEDSET\s*="]
# The plugin's handle on the website board (same names on all 4 pages, checked by BOARD_NAMES): the filter list (ids,
# labels, option labels, what is on), set the filters (only known ids and in-range values; anything else is ignored)
# and the saved coins. It calls the website's own renderFilters / applyFilters, so the board redraws as on a click.
HANDLE_JS = (
    "var BOARD_HANDLE = {\n"
    "  filters: function () { return LEAD.concat(MORE).map(function (f) { return { id: f.id, label: f.label, type: f.type, "
    "opts: f.opts ? f.opts.map(function (o) { return o[0]; }) : null, "
    "on: fActive(f) ? (f.type === 'toggle' ? true : FSTATE[f.id]) : null }; }); },\n"
    "  setFilters: function (st) { var n = {}; if (st && typeof st === 'object') { for (var id in st) { "
    "if (!Object.prototype.hasOwnProperty.call(st, id) || !Object.prototype.hasOwnProperty.call(ALLF, id)) continue; "
    "var f = ALLF[id], v = st[id]; if (f.type === 'toggle' && v === true) n[id] = true; "
    "else if (f.type === 'cycle' && typeof v === 'number' && Math.floor(v) === v && v >= 0 && v < f.opts.length) n[id] = v; } } "
    "FSTATE = n; renderFilters(); applyFilters(); return true; },\n"
    "  saved: function () { return Object.keys(SAVEDSET); }\n"
    "};")


def strip_js_comments(js, module=False):
    """Every comment out (developer notes must never ship in the public plugin). Node's own parser does it and proves
    that only comments changed (strip_comments.mjs). module=True parses the text as an ES module (plugin.src.js)."""
    prog = ("import('./strip_comments.mjs').then(m=>{let s='';process.stdin.setEncoding('utf8');"
            "process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>{try{process.stdout.write(m.strip(s,"
            + ("{module:true}" if module else "undefined") +
            ").out)}catch(e){process.stderr.write(String(e));process.exit(3)}})})")
    r = subprocess.run(["node", "--expose-internals", "-e", prog], input=js.encode("utf-8"), capture_output=True,
                       cwd=str(Path(__file__).resolve().parent))
    if r.returncode != 0:
        raise SystemExit("STOP: comment strip failed: " + r.stderr.decode("utf-8", "replace")[:500])
    return r.stdout.decode("utf-8")


# Exact text cuts made in a taken script BEFORE the comment strip (the plugin has no "scan the address" part; the Early
# Edge wallets are gone). Key = (page key, script index); each cut = (first text, last text), both kept in the cut,
# each must occur exactly once or the build stops (when the website drops the scan itself, delete these cuts).
CUTS = {
    ("d_gated", 11): [
        # the "Ask the agent" section: hint, paste box, Scan button, answer area
        ("    /* 2) drop / paste a coin -> auto read */", "sec2.appendChild(dbox);body.appendChild(sec2);\n"),
        # drag a coin onto the Early Edge tab / panel -> scan
        ("    /* drag-a-coin-in -> auto read;", 'RAIL.addEventListener("drop",function(e){RAIL.classList.remove("dropping");_dropScan(e);});\n'),
        # the scan itself (incl. the __EE_PREVIEW__.scan path and /api/app2/edge/scan)
        ("    /* ---- scan ---- */", "      }catch(e){showScan({known:false,mint:mint},mint);done();}\n    }\n"),
    ],
}


def apply_cuts(s, cuts, where):
    for a, b in cuts:
        if s.count(a) != 1:
            raise SystemExit("STOP: cut start found %d times in %s (the page changed; update CUTS): %r" % (s.count(a), where, a))
        i = s.index(a)
        j = s.find(b, i)
        if j < 0 or s.count(b) != 1:
            raise SystemExit("STOP: cut end not found exactly once after its start in %s (update CUTS): %r" % (where, b))
        s = s[:i] + s[j + len(b):]
    return s


# Exact text swaps made in a taken script BEFORE the comment strip. They mirror the strength-word swap the website makes
# when it serves its /free and /gated pages (desktop and phone), byte for byte, so the panel shows the same words as the
# website (Early / Building / Peak). Plus the gated pages' Clear Eyes filter chip options read Early+ / Building+ / Peak
# (the website gets the same change later). Key = (page key, script index); each swap = (old, new, expected count); the
# count must match exactly or the build stops. When newer pages carry the new words themselves, these swaps stop matching
# ON PURPOSE (the build stops) -> then delete them.
_SRV_STRENGTH_SUBS = [
    # = the website's serve-time swap, both entries, unchanged
    ('var CE_STEP_LABEL={flagged:"Flagged",heating:"Heating up",strong:"Strong",confirmed:"Confirmed"};',
     'var CE_STEP_LABEL={flagged:"Flagged",heating:"Early",strong:"Building",confirmed:"Peak"};', 1),
    ("it climbs: Flagged → Heating up → Strong → Confirmed. If it dies, it shows Faded.",
     "it climbs: Flagged → Early → Building → Peak. If it dies, it shows Faded.", 1),
]
_CHIP_SUB = [  # the Clear Eyes filter chip (gated pages only; the free pages have no such chip)
    ("opts:[['Heating+',1],['Strong+',2],['Confirmed',3]]", "opts:[['Early+',1],['Building+',2],['Peak',3]]", 1),
]
_FREE_LEAD_SWAP = [  # on the free boards (computer + phone) DEX paid comes before Low cap. Only the order of
    # the two LEAD entries changes (renderFilters appends LEAD in array order, so the real DOM / tab order follows); same
    # ids, labels, options, tests. The gated boards keep their own LEAD (no Low cap there; it sits in MORE).
    (" {id:'lowcap',label:'Low cap',type:'cycle',opts:[['<15k',15000],['<30k',30000],['<50k',50000]],test:function(s,v){return num(s.mcapRaw)<=v;}},\n"
     " {id:'dexpaid',label:'DEX paid',type:'toggle',test:function(s){return s.dexPaid===true;}}\n];",
     " {id:'dexpaid',label:'DEX paid',type:'toggle',test:function(s){return s.dexPaid===true;}},\n"
     " {id:'lowcap',label:'Low cap',type:'cycle',opts:[['<15k',15000],['<30k',30000],['<50k',50000]],test:function(s,v){return num(s.mcapRaw)<=v;}}\n];", 1),
]
_NO_DATA_CHIPS = [  # all 4 boards: the More list loses Caller / Flash point / Signals on purpose. The panel never
    # gets their data (socialBuzz / flashPoint / sigCount), so turning one on emptied the board. Every other More entry
    # stays byte for byte, in its place; Signals is the last entry, so Hide fake vol (before it) loses its comma.
    (" {id:'caller',label:'Caller',type:'toggle',test:function(s){return s.socialBuzz===true;}},\n"
     " {id:'flash',label:'Flash point',type:'toggle',test:function(s){return s.flashPoint===true;}},\n", "", 1),
    (" {id:'realvol',label:'Hide fake vol',type:'toggle',test:function(s){return s.feeRug!==true&&s.feeRugFlicker!==true;}},\n"
     " {id:'signals',label:'Signals',type:'cycle',opts:[['2+',2],['3+',3],['4+',4]],test:function(s,v){return num(s.sigCount)>=v;}}\n];",
     " {id:'realvol',label:'Hide fake vol',type:'toggle',test:function(s){return s.feeRug!==true&&s.feeRugFlicker!==true;}}\n];", 1),
]
SUBS = {
    ("d_free", 3): _SRV_STRENGTH_SUBS + _FREE_LEAD_SWAP + _NO_DATA_CHIPS,
    ("d_gated", 4): _SRV_STRENGTH_SUBS + _CHIP_SUB + _NO_DATA_CHIPS,
    ("m_free", 3): _SRV_STRENGTH_SUBS + _FREE_LEAD_SWAP + _NO_DATA_CHIPS,
    ("m_gated", 2): _SRV_STRENGTH_SUBS + _CHIP_SUB + _NO_DATA_CHIPS,
}


def apply_subs(s, subs, where):
    for old, new, n in subs:
        if s.count(old) != n:
            raise SystemExit("STOP: swap text found %d times (expected %d) in %s (the page changed; update SUBS): %r"
                             % (s.count(old), n, where, old))
        s = s.replace(old, new)
    return s


def board_script(html, idx, key=None):
    scripts = [m.group(2) for m in re.finditer(r"<script([^>]*)>(.*?)</script>", html, re.S)]
    parts = []
    for n_i, i in enumerate(idx):
        s = scripts[i]
        if not re.search(MARKERS[n_i], s):
            raise ValueError("script #%d is not the expected one (%s): the page changed; re-list its scripts" % (i, MARKERS[n_i]))
        s, n = re.subn(r"var FEED\s*=\s*\[.*?\];", "var FEED = [];", s, count=1, flags=re.S)
        if i == idx[0] and n != 1:
            raise ValueError("FEED literal not found")
        if (key, i) in CUTS:
            s = apply_cuts(s, CUTS[(key, i)], "%s script #%d" % (key, i))
        if (key, i) in SUBS:
            s = apply_subs(s, SUBS[(key, i)], "%s script #%d" % (key, i))
        if i == idx[0]:
            for pat in BOARD_NAMES:
                if not re.search(pat, s):
                    raise ValueError("main board script lost %s: the page changed; update HANDLE_JS" % pat)
        parts.append(strip_js_comments(s.strip()))
    return "\n;\n".join(parts)


def main(pages_dir, css_dir, out):
    chunks = ["// GENERATED by plugin/gen/gen_engine.py from the after-go-live website board pages. Do not edit by hand.",
              "/* eslint-disable */"]
    for (k, i) in list(CUTS) + list(SUBS):   # a cut / swap for a script that is not taken would silently do nothing
        if k not in PAGES or i not in PAGES[k][4]:
            raise SystemExit("STOP: CUTS/SUBS name %s script #%d, which is not taken (update CUTS/SUBS)" % (k, i))
    for key, (fname, md5, variant, view, idx) in PAGES.items():
        raw = open(pages_dir + "/" + fname, "rb").read()
        got = hashlib.md5(raw).hexdigest()[:8]
        if got != md5:
            raise SystemExit("STOP: %s md5 %s != the pinned version %s (use the matching page copy)" % (fname, got, md5))
        html = raw.decode("utf-8")
        css = open(css_dir + "/" + key + ".css", encoding="utf-8").read()
        sk = skeleton(html)
        js = board_script(html, idx, key)
        for pat in BANNED:
            for name, text in (("script", js), ("skeleton", sk), ("css", css)):
                if re.search(pat, text):
                    raise SystemExit("STOP: banned pattern %r in %s %s" % (pat, key, name))
        bad = skeleton_problems(sk)
        if bad:
            raise SystemExit("STOP: %s skeleton is outside the markup allow-list: %s" % (key, "; ".join(bad[:5])))
        chunks.append("const SKELETON_%s = %s;" % (key, json.dumps(sk, ensure_ascii=True)))
        chunks.append("const CSS_%s = %s;" % (key, json.dumps(css, ensure_ascii=True)))
        chunks.append("function makeBoard_%s(%s) {\n%s\n;\n%s\nreturn { applyLiveData: (typeof applyLiveData === 'function') ? "
                      "applyLiveData : null, closeDetail: (typeof closeDetail === 'function') ? closeDetail : null, "
                      "openDetail: (typeof openDetail === 'function') ? openDetail : null, "
                      "current: function () { return (typeof currentSignal !== 'undefined') ? currentSignal : null; }, "
                      "board: BOARD_HANDLE };\n}"
                      % (key, ", ".join(FACTORY_PARAMS), js, HANDLE_JS))
        print(key, fname, md5, "skeleton", len(sk), "css", len(css), "script", len(js))
    chunks.append("const BOARDS = { d_free: [SKELETON_d_free, CSS_d_free, makeBoard_d_free], d_gated: [SKELETON_d_gated, "
                  "CSS_d_gated, makeBoard_d_gated], m_free: [SKELETON_m_free, CSS_m_free, makeBoard_m_free], m_gated: "
                  "[SKELETON_m_gated, CSS_m_gated, makeBoard_m_gated] };")
    chunks.append("const FACTORY_PARAMS = %s;" % json.dumps(FACTORY_PARAMS))
    # The website fonts (gen_fonts.py: embedded, panel-only family names, SIL OFL 1.1 - licences in piquesignal/fonts/).
    fonts = open(css_dir + "/fonts.css", encoding="utf-8").read()
    if "<" in fonts or not fonts.startswith("@font-face{"):
        raise SystemExit("STOP: fonts.css is not the gen_fonts.py output")
    chunks.append("const FONTS_CSS = %s;" % json.dumps(fonts, ensure_ascii=True))
    open(out, "w", encoding="utf-8", newline="\n").write("\n".join(chunks) + "\n")
    print("wrote", out)


if __name__ == "__main__":
    main(*sys.argv[1:4])
