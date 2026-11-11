"""The gen/ build tools (maintainer-only: skipped where the gen folder or Node is not there)."""
import importlib.util
import json
import re
import shutil
import unittest
from pathlib import Path

GEN = Path(__file__).resolve().parents[2] / "gen"


def _load(name):
    spec = importlib.util.spec_from_file_location("pqs_gen_" + name, GEN / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless((GEN / "gen_css.py").is_file(), "gen/ not here")
class TestGenCssMedia(unittest.TestCase):
    """A negated media query whose touch / hover / print part is false for this screen is ALWAYS true."""

    def setUp(self):
        self.q = _load("gen_css").eval_query

    def test_negated_false_static_is_always_true(self):
        self.assertEqual(self.q("not all and (pointer:fine) and (max-width:500px)", True), ([], []))
        self.assertEqual(self.q("not all and (hover:none) and (min-width:481px)", False), ([], []))
        self.assertEqual(self.q("not all and print and (min-width:1px)", False), ([], []))

    def test_negated_true_static_keeps_the_width_part(self):
        self.assertEqual(self.q("not all and (pointer:fine) and (max-width:500px)", False), (["not (max-width:500px)"], []))

    def test_single_and_plain_cases_unchanged(self):
        self.assertEqual(self.q("not all and (hover:none)", False), ([], []))
        self.assertIsNone(self.q("not all and (hover:none)", True))
        self.assertIsNone(self.q("(hover:none) and (max-width:500px)", False))
        self.assertEqual(self.q("(hover:none) and (max-width:500px)", True), (["(max-width:500px)"], []))
        self.assertEqual(self.q("not all and (max-width:540px)", False), (["not (max-width:540px)"], []))
        self.assertEqual(self.q("(prefers-reduced-motion:reduce)", False), ([], ["(prefers-reduced-motion:reduce)"]))

    def test_negated_all_true_still_refused(self):
        with self.assertRaises(ValueError):
            self.q("not all and screen and (pointer:fine)", False)


@unittest.skipUnless((GEN / "gen_engine.py").is_file(), "gen/ not here")
class TestSkeletonBanned(unittest.TestCase):
    """The board markup (inserted with innerHTML) stays inside an allow-list: no handler, no script link, no src,
    no style, nothing that loads or sends."""

    def setUp(self):
        g = _load("gen_engine")
        self.problems = g.skeleton_problems
        self.pats = g.SKELETON_BANNED

    def test_bad_markup_is_caught(self):
        for bad in ['<a href="#" onclick="x()">a</a>', '<svg/onload=alert(1)>', '<div ONMOUSEOVER = "x">',
                    '<a href="x"onclick="y">', '<a href="javascript:alert(1)">', '<a href="JaVaScRiPt :x">',
                    '<a href="java\tscript:x">', '<a href="java\nscript:x">', '<a href="vbscript:x">',
                    '<img src="x.png">', '<img alt=""/src=x>', '<img srcset="x 1x">', '<iframe srcdoc="x"></iframe>',
                    '<a href="&#106;avascript:x">', '<a href="java&Tab;script:x">', '<a href="x&colon;y">',
                    '<form action="/x">', '<link rel="x">', '<meta http-equiv="refresh">', '<base href="/">',
                    '<object data="x">', '<embed type="x">', '<frame>', '<script>',
                    '<div style="background:url(https://e/x)">', '<video poster="https://e/x">',
                    '<svg><image href="https://e/x"/></svg>', '<style>@import url(//e)</style>', '<table background="x">',
                    '<svg><use href="#x"/></svg>', '<div id="config">', '<a href="//evil.example/x">', '<a href="http://x.example">',
                    '<a href="data:text/html,x">', '<a href="/\\evil">', '<!-- x -->', '<div hidden onfocus>']:
            self.assertTrue(self.problems(bad), bad)

    def test_deny_list_alone_still_catches_the_basics(self):
        for bad in ['<a onclick="x">', '<a href="javascript:x">', '<img src="x">', '<div style="x">', '<iframe>']:
            self.assertTrue(any(re.search(p, bad) for p in self.pats), bad)

    def test_board_markup_kinds_pass(self):
        ok = ('<div class="tk" data-mint="x" role="button" tabindex="0"><button type="button" aria-label="Close" '
              'class="buy">×</button><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false" width="16" height="16">'
              '<rect x="1" y="1" rx="2" width="4" height="4" fill="none" stroke="#fff" stroke-width="2"/>'
              '<path d="M0 0h24"/></svg><input id="qsearch" type="search" placeholder="Search coins" '
              'autocomplete="off" maxlength="64" autocapitalize="off" spellcheck="false">'
              '<a href="https://piquesignal.xyz/unlock" class="buy" target="_blank" rel="noopener">Unlock</a>'
              '<a href="/gated">Gated</a><a href="#">Top</a><nav><main><header><footer><span id="upd">· updated</span>'
              '</footer></header></main></nav></div>')
        self.assertEqual(self.problems(ok), [])

    @unittest.skipUnless((GEN / "engine_parts.js").is_file(), "engine_parts.js not here (maintainer-only)")
    def test_todays_four_board_markups_pass(self):
        text = (GEN / "engine_parts.js").read_text(encoding="utf-8")
        found = re.findall(r"^const SKELETON_(\w+) = (\".*\");$", text, re.M)
        self.assertEqual(sorted(k for k, _ in found), ["d_free", "d_gated", "m_free", "m_gated"])
        for key, lit in found:
            self.assertEqual(self.problems(json.loads(lit)), [], key)

    def test_build_checks_the_markup_and_strips_the_plugin_comments(self):
        b = (GEN / "build.py").read_text(encoding="utf-8")
        self.assertIn("from gen_engine import skeleton_problems, strip_js_comments", b)
        self.assertIn("bad = skeleton_problems(json.loads(lit))", b)
        self.assertNotIn("assert ", b)            # every gate is an explicit stop (also under python -O)
        self.assertIn('strip_js_comments((HERE / "plugin.src.js").read_text(encoding="utf-8"), module=True)', b)


@unittest.skipUnless((GEN / "strip_comments.mjs").is_file() and shutil.which("node"), "gen/ or Node not here")
class TestStripModule(unittest.TestCase):
    """plugin.src.js (an ES module) ships without its comments; only comments change."""

    def test_module_comments_removed_code_kept(self):
        strip = _load("gen_engine").strip_js_comments
        src = ("// team note\nimport { a } from 'react'\nconst x = 1 /* inline */ + 2 // why\n"
               "const s = '// not a comment'\nexport default { x, s }\n")
        out = strip(src, module=True)
        self.assertNotIn("team note", out)
        self.assertNotIn("inline", out)
        self.assertNotIn("why", out)
        self.assertIn("const s = '// not a comment'", out)
        self.assertIn("import { a } from 'react'", out)
        self.assertIn("export default { x, s }", out)

    def test_script_mode_unchanged(self):
        strip = _load("gen_engine").strip_js_comments
        self.assertEqual(strip("var a = 1; // n\nreturn a"), "var a = 1;  \nreturn a")


if __name__ == "__main__":
    unittest.main()
