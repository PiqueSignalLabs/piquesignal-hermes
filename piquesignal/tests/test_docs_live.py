"""The docs follow the HERMES_LIVE switch. While it is on (this release), README.md names every piquesignal.xyz
address the code calls (taken from feed_client.py, and checked against what core.py really uses) and every backend
route, and README.md, plugin.yaml, guide.md (section 9) and the core.py / feed_client.py headers carry the live
disclosure words (specific marks, never a bare word like "banners"), with no "switched off" wording left anywhere.
While it is off (the kill switch), README.md, plugin.yaml and guide.md must not name the new addresses (they must not
read as live). The ready words are in hermes_live_docs.md, next to this file. Reads the source text only: no import of
the plugin, no network."""
import ast
import json
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
READY = Path(__file__).resolve().parent / "hermes_live_docs.md"
SRC_JS = PLUGIN.parent / "gen" / "plugin.src.js"
BUILT_JS = PLUGIN / "desktop" / "plugin.js"

# the live disclosure words, per file (specific phrases: each names one part, never a bare common word)
README_WORDS = ("Missed strip", "Free Pick", "Featured Callers", 'banners marked "Ad"', "capped at 3.2 MB",
                "random 0 to 120 seconds", "Missed reveals and pictures have no such wait", "stops it until Hermes restarts",
                "the board's last 24 h as the server sends it", "no banner view or click counts", "the link of a banner",
                "at most 50 a day", "at most 10 % of your key's daily limit", "only while Rewind is on in Settings")
YAML_WORDS = ("Missed strip", "Free Pick", "the Missed and banner pictures (/api/free-board/img/)", "Featured Callers", "24 h history", "Missed reveal",
              "random 0-120 s", "Missed reveals and pictures excepted", "stops it until Hermes restarts", "history answers capped at 3.2 MB",
              "no banner view or click counting", "the server's 24 h history", "banner links too")
GUIDE_WORDS = ("### 9.14 Missed strip, Free Pick, banners and Featured Callers", "Paid gets it first", 'banners marked "Ad"',
               "Featured Callers", "The last 24 hours from PiqueSignal", "random 0 to 2 minutes", "No view or click is counted",
               "not Missed reveals and pictures", "Missed reveals are kept in memory only",
               "does not ask for it again until Hermes restarts")
CORE_WORDS = ("HERMES_LIVE = True", "/api/free-board/missed", "/api/pull/featured-callers", "/api/pull/missed-reveal/",
              "/api/pull/history", "3.2 MB", "not reveal / images", "a history 404 = gone until the next start")
FEED_WORDS = ("HERMES_LIVE = True", "/api/free-board/missed", "/api/pull/featured-callers", "3.2 MB",
              "a history 404 = never again until the next start")
# wording of the switched-off release: never left in any doc while the switch is on
OFF_WORDS = ("switched off in this release", "SWITCHED OFF", "never calls them", "NOT LIVE in this release",
             "HERMES_LIVE = False:", "the addresses switched off")


def _flag(path, pattern):
    m = re.findall(pattern, path.read_text(encoding="utf-8"), re.M)
    if len(m) != 1:
        raise AssertionError("HERMES_LIVE not found exactly once in %s" % path.name)
    return m[0].lower() == "true"


def _flat(text):
    return re.sub(r"\s+", " ", text)


def _read(p):
    return _flat(p.read_text(encoding="utf-8"))


def _doc(path):
    return _flat(ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or "")


def addresses():
    """(every piquesignal.xyz path feed_client.py defines, the NEW ones) - query strings cut (the doc names the path)."""
    src = (PLUGIN / "feed_client.py").read_text(encoding="utf-8")
    every = {v.split("?", 1)[0] for v in re.findall(r'^[A-Z][A-Z_]* = BASE \+ "([^"]+)"\s*$', src, re.M)}
    block = src[src.index("# The NEW read-only addresses"):src.index("IMG_KEY_RE")]
    new = set(re.findall(r'^[A-Z_]+ = BASE \+ "([^"]+)"\s*$', block, re.M))
    return every, new


def routes():
    """Every backend route of dashboard/plugin_api.py, as the README writes it (`/img/{key}` -> `/img`)."""
    src = (PLUGIN / "dashboard" / "plugin_api.py").read_text(encoding="utf-8")
    return {p.split("/{", 1)[0] for p in re.findall(r'@router\.(?:get|post)\("([^"]+)"', src)}


def section9(guide):
    return guide[guide.index("## 9. The Hermes plugin"):guide.index("## 10. The boards")]


def live_doc_gaps(live, readme, yaml, guide9):
    """What is wrong with the docs for this switch position: missing marks when live, live marks present when off."""
    every, new = addresses()
    if live:
        gaps = [("README.md", w) for w in sorted(every) + list(README_WORDS) if w not in readme]
        gaps += [("README.md", "`" + r) for r in sorted(routes()) if "`" + r not in readme]
        if "cdn.dexscreener.com" not in readme:
            gaps.append(("README.md", "cdn.dexscreener.com"))
        gaps += [("plugin.yaml", w) for w in YAML_WORDS if w not in yaml]
        gaps += [("guide.md", w) for w in GUIDE_WORDS if w not in guide9]
        gaps += [(f, w) for f, t in (("README.md", readme), ("plugin.yaml", yaml), ("guide.md", guide9))
                 for w in OFF_WORDS if w in t]
        return gaps
    return ([("README.md", w) for w in sorted(new) if w in readme]
            + [("plugin.yaml", w) for w in YAML_WORDS if w in yaml]
            + [("guide.md", w) for w in GUIDE_WORDS if w in guide9])


class DocsFollowTheSwitch(unittest.TestCase):
    def setUp(self):
        self.live = _flag(PLUGIN / "core.py", r"^HERMES_LIVE = (True|False)\s*$")

    def test_docs_match_hermes_live(self):
        readme, yaml = _read(PLUGIN / "README.md"), _read(PLUGIN / "plugin.yaml")
        guide9 = section9(_read(PLUGIN / "guide.md"))
        self.assertEqual(live_doc_gaps(self.live, readme, yaml, guide9), [],
                         "HERMES_LIVE is %s: update README.md / plugin.yaml / guide.md (ready words: tests/hermes_live_docs.md)"
                         % self.live)

    def test_this_release_is_live(self):
        self.assertIs(self.live, True)

    def test_headers_carry_the_live_text(self):
        """core.py, feed_client.py and plugin_api.py describe the switch as it is: live words in, off words out."""
        if not self.live:
            self.skipTest("kill switch: headers are checked for the live release")
        core, feed, api = _doc(PLUGIN / "core.py"), _doc(PLUGIN / "feed_client.py"), _doc(PLUGIN / "dashboard" / "plugin_api.py")
        for w in CORE_WORDS:
            self.assertIn(w, core, w)
        for w in FEED_WORDS:
            self.assertIn(w, feed, w)
        for name, text in (("core.py", core), ("feed_client.py", feed), ("plugin_api.py", api)):
            for w in OFF_WORDS:
                self.assertNotIn(w, text, (name, w))

    def test_pane_switch_matches_core(self):
        """ONE switch: core.py, plugin.src.js and the built plugin.js carry the same value (a release with them apart
        fails here)."""
        core = _flag(PLUGIN / "core.py", r"^HERMES_LIVE = (True|False)\s*$")
        if SRC_JS.is_file():
            self.assertEqual(_flag(SRC_JS, r"^const HERMES_LIVE = (true|false)\s*$"), core)
        self.assertEqual(_flag(BUILT_JS, r"^const HERMES_LIVE = (true|false)\s*$"), core)

    def test_one_version_everywhere(self):
        """core.py VERSION, plugin.yaml and the dashboard manifest name the same version (a release with them apart
        cannot be told apart for support or rollback)."""
        core = re.findall(r'^VERSION = "([0-9]+\.[0-9]+\.[0-9]+)"\s*$', (PLUGIN / "core.py").read_text(encoding="utf-8"), re.M)
        yaml = re.findall(r"^version: ([0-9]+\.[0-9]+\.[0-9]+)\s*$", (PLUGIN / "plugin.yaml").read_text(encoding="utf-8"), re.M)
        manifest = json.loads((PLUGIN / "dashboard" / "manifest.json").read_text(encoding="utf-8")).get("version")
        self.assertEqual(len(core), 1)
        self.assertEqual(len(yaml), 1)
        self.assertEqual({core[0], yaml[0], manifest}, {core[0]})

    def test_ready_words_cover_every_mark(self):
        ready = _read(READY)
        _every, new = addresses()
        for w in sorted(new) + list(YAML_WORDS):
            self.assertIn(w, ready, w)
        self.assertIn("LIVE in this release", ready)
        self.assertNotIn("NOT LIVE in this release", ready)

    def test_marks_are_specific(self):
        """No mark is a bare common word ('banners', 'history', ...): each names one part or one fact."""
        for w in README_WORDS + YAML_WORDS + GUIDE_WORDS:
            self.assertTrue(len(w) >= 8 and (" " in w or "/" in w), w)
            self.assertNotIn(w.lower(), ("banners", "banner", "history", "featured", "missed", "rewind", "pictures"))

    def test_the_check_bites(self):
        """A live switch with off-release docs is reported; an off switch with live docs is reported too; the full
        live words pass."""
        every, new = addresses()
        self.assertTrue(live_doc_gaps(True, "free board only", "piquesignal.xyz", ""))
        self.assertTrue(live_doc_gaps(False, "GET /api/pull/history", "", ""))
        self.assertTrue(live_doc_gaps(False, "", "Featured Callers", ""))
        self.assertTrue(live_doc_gaps(False, "", "", GUIDE_WORDS[0]))
        full = " ".join(sorted(every) + list(README_WORDS) + ["`" + r for r in sorted(routes())] + ["cdn.dexscreener.com"])
        self.assertEqual(live_doc_gaps(True, full, " ".join(YAML_WORDS), " ".join(GUIDE_WORDS)), [])
        self.assertTrue(live_doc_gaps(True, full + " the routes switched off in this release", " ".join(YAML_WORDS),
                                      " ".join(GUIDE_WORDS)))
        self.assertTrue(live_doc_gaps(True, full.replace("/api/pull/featured-callers", ""), " ".join(YAML_WORDS),
                                      " ".join(GUIDE_WORDS)))

    def test_marks_are_the_real_addresses(self):
        """feed_client.py defines exactly the 4 old + 8 new addresses, and core.py calls only addresses feed_client.py
        defines (so 'README names every address' means every address the live code calls)."""
        every, new = addresses()
        self.assertEqual(len(new), 8)
        self.assertEqual(new, {"/api/free-board/missed", "/api/free-board/free-pick", "/api/free-board/banners",
                               "/api/free-board/img/", "/api/free-board/history", "/api/pull/featured-callers",
                               "/api/pull/missed-reveal/", "/api/pull/history"})
        self.assertEqual(every - new, {"/api/free-board", "/api/pull/feed", "/api/pull/early-edge", "/api/pull/me"})
        fsrc = (PLUGIN / "feed_client.py").read_text(encoding="utf-8")
        defined = set(re.findall(r'^([A-Z][A-Z_]*) = BASE \+ "', fsrc, re.M))
        used = set(re.findall(r"\bfc\.([A-Z_]+_(?:URL|PREFIX))\b", (PLUGIN / "core.py").read_text(encoding="utf-8")))
        self.assertTrue(used, "core.py uses no feed address?")
        self.assertLessEqual(used, defined | {"URL"})
        # the only other hosts in the Python code: the pop-up picture host and, for Deep Check and the price chart only,
        # EXACTLY the Dexscreener token-pairs prefix and the GeckoTerminal pool prefix (all named in README.md); the x.com
        # post-link pattern is only matched against x_search's cited links, never requested
        dex = "https://api.dexscreener.com/token-pairs/v1/solana/"
        gecko = "https://api.geckoterminal.com/api/v2/networks/solana/pools/"
        for name in ("core.py", "__init__.py"):
            for u in re.findall(r"[\"'](https?://[^\"'\s]*)", (PLUGIN / name).read_text(encoding="utf-8")):
                if u.startswith("https://(?:www\\.)?(?:x|twitter)\\.com/"):
                    self.assertEqual(name, "core.py")
                    continue
                self.assertTrue(u.startswith(("https://cdn.dexscreener.com/", "https://piquesignal.xyz")) or u in (dex, gecko),
                                (name, u))
        csrc = (PLUGIN / "core.py").read_text(encoding="utf-8")
        self.assertEqual(csrc.count('"' + dex + '"'), 1)
        self.assertEqual(csrc.count('"' + gecko + '"'), 1)
        self.assertIn("_live_transport(_LIVE_PAIRS + mint,", csrc)          # the prefix + a validated mint, nothing else
        # the GeckoTerminal prefix + a checked pool + fixed path / query words (numbers from CHART_TFS), nothing else
        self.assertIn('url = "%s%s/ohlcv/%s?aggregate=%d&limit=%d&currency=usd" % (_CHART_POOLS, pool, unit, agg, limit)',
                      csrc)
        self.assertEqual(csrc.count("_chart_transport("), 1)
        readme = _read(PLUGIN / "README.md")
        self.assertIn("api.dexscreener.com", readme)
        self.assertIn("/token-pairs/v1/solana/", readme)
        self.assertIn("api.geckoterminal.com", readme)
        self.assertIn("/api/v2/networks/solana/pools/", readme)
        self.assertNotIn("api.coingecko.com", readme)                       # keyed now (401 without a key): not used
        self.assertIn("HISTORY_MAX_BYTES = 3_200_000", fsrc)


if __name__ == "__main__":
    unittest.main()
