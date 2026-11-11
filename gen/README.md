# gen/ — how `piquesignal/desktop/plugin.js` is assembled

**Maintainer-only.** This folder is kept in the repository so you can read how `plugin.js` is made. Rebuilding it, or
running `gen/tests/test_src.mjs`, needs files that are not in the public repository (see `../.gitignore`): the full
website page copies, the generated board CSS (`d_free.css`, `d_gated.css`, `m_free.css`, `m_gated.css`, `fonts.css`),
`engine_parts.js` and `tests/make_expected.py`; one Python test also reads the private free-feed service folder. The
committed `../piquesignal/desktop/plugin.js` is the reviewed result and is what Hermes loads; nothing in this folder is
needed to run the plugin.

The screens must look exactly like piquesignal.xyz, so they reuse the website's own board pages instead of a copy
written by hand.

1. `gen_css.py <page.html> <phone|desktop> <root selector> <out.css>`
   Takes every `<style>` block of a website board page and fences it in to the plugin's root element. It turns
   screen-width `@media` rules into `@container` rules on the pane's or page's own width. It fixes touch and hover
   rules per screen (phone = touch, desktop = mouse), drops print rules, renames `@keyframes` to `pqs-*`, turns
   `vw` into `cqw`, and refuses to write any `<`.
2. `gen_engine.py <pages dir> <css dir> engine_parts.js`
   For each of the 4 pages (free / gated × desktop / phone):
   - checks the page's md5 against the pinned version (listed in `PAGES` in `gen_engine.py`);
   - takes the board markup (without scripts, styles and website-only parts such as sign-in, the alerts bell and
     the ANSEM gate);
   - takes the page's own board scripts, wrapped in a factory whose `document`, `window`, `localStorage`, `fetch`,
     `location`, `navigator`, timers and animation frames are the plugin's stand-ins.
   The scripts are the website's own code with only these changes: the baked list of coins is replaced by `[]`, a few
   exact cuts and word swaps listed in `gen_engine.py` (`CUTS`, `SUBS`; the build stops if one no longer matches), and
   every comment removed by `strip_comments.mjs` (`node --expose-internals`: the JavaScript parser inside Node itself;
   it proves the code tokens are unchanged, so developer notes never ship). Each factory also returns a small board
   handle (the filter list, set filters, saved coins) that calls the website's own `renderFilters` / `applyFilters`;
   the build stops if a page no longer has the names it uses. The build stops on `eval`, `new Function`, dynamic
   `import()`, script elements, a `document.body` observer or a way out of the stand-ins; and on board markup (it is
   inserted with innerHTML) with anything outside a small allow-list of elements, attributes and links (so never an
   inline `on…=` handler, a `javascript:` link, a `src` or `style` attribute, an encoded character or an element that
   loads or sends something).
   The stand-ins track the listeners the scripts add through them (document, window, `document.fonts`, media queries),
   their timers and animation frames, and remove them when a board is taken down; listeners on elements inside the
   board go away with the board's markup. A board `<img>` is the plain element while `HERMES_LIVE` is off (the coin
   pictures load from DexScreener, as on the website); with it on, every `<img>` is guarded so only the exact
   DexScreener coin picture and the backend's own `data:` pictures load.
2b. `gen_fonts.py <fonts dir> fonts.css`
   Embeds the website's own board fonts (our self-hosted `fonts-boards-v1.css`: Hanken Grotesk, JetBrains Mono,
   Bricolage Grotesque; SIL OFL 1.1, licences in `../piquesignal/fonts/`) as data: URLs under panel-only family names
   ("PQS …", so Hermes' own text is never affected); every file md5-checked; same weight choices as the website.
   `gen_css.py` points the board sheets at those names; `gen_engine.py` emits them once as `FONTS_CSS`.
3. `build.py` joins the imports, `engine_parts.js`, the pinned chart library and `plugin.src.js` (the hand-written
   part: the stand-ins, the screens, Hermes registration; shipped without its comments, through the same
   `strip_comments.mjs` proof) into `../piquesignal/desktop/plugin.js`. It checks the board markup again (same
   allow-list), runs the Hermes desktop validator's rules and our own extra bans over the whole file, and checks that
   it imports only `react` and `@hermes/plugin-sdk`.
   The chart library is TradingView Lightweight Charts 5.3.0 from npm (`lightweight-charts@5.3.0`, file
   `dist/lightweight-charts.standalone.production.mjs`, with fancy-canvas 2.1.0 bundled inside it), kept as
   `vendor/lightweight-charts.standalone.production.mjs`. `build.py` pins its sha256
   (`0b6d1ed409283a0f9a493a99dcf11c650e111d0c61619cd922198975fb82fa99`) and the build stops if the file changes. It
   ships byte for byte except its final `export {…}` statement: it runs in its own private scope and only 4 names
   leave it (`createChart`, `CandlestickSeries`, `HistogramSeries`, `createSeriesMarkers`). The only exception to the
   scan: 4 of our own extra bans that are not Hermes rules (`.observe(document.body`, `ownerDocument`, `defaultView`,
   `new Image`) are skipped inside that exact block only; Hermes' rules and every other ban still run on it. Licences:
   `../piquesignal/licenses/lightweight-charts-LICENSE.txt` (Apache-2.0) and
   `../piquesignal/licenses/fancy-canvas-LICENSE.txt` (MIT).

Pages used: the PiqueSignal website board pages after its 2026-11 release (`free_desktop.html`, `gated_desktop.html`,
`free_page.html`, `gated_page.html`). The full page copies are kept private, not in this repository.
