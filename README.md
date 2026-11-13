# Pique Signal for Hermes

**Catch new Solana memecoins early, and see through the junk.**

Pique Signal puts a live board of new Solana memecoins inside Hermes Desktop and turns Hermes into a research partner
that can see it. Deep Check and Board talk numbers come from the board or live data, never from the AI. On X counts
the posts Grok cites (the search asks for up to 15 of the most recent, so at 15 or more the line reads "N+ posts (only
the most recent posts were read)", for example "15+ posts"). Research
only; nothing trades.

**Our own systems, built in-house:** the Pique Signal engine finds new Solana memecoins worth watching as they launch
and runs rug and safety checks before it calls a coin (risky coins are removed or tagged). **Fake Volume** flags faked
or bundled trading and **DEX paid** marks a paid Dexscreener listing. Members also get **Real Crowd** (padded holder
counts), **Clear Eyes** (a plain strength read: Early, Building, Peak or Faded), **Early Edge**, **Featured Callers**
(also on the free board) and a board with known rugs and dead coins removed. Past calls are on a public track record at
piquesignal.xyz/track-record. No check catches every rug.

**What the plugin adds to Hermes:**

- **Deep Check:** one click and Hermes sends out a team of sub-agents (its built-in `delegate_task`) that check the
  coin at the same time: Fake Volume, what changed since the call, live numbers from Dexscreener, posts on X (through
  Grok) and, for members, Clear Eyes and Real Crowd. A card fills in red, green or grey on your board as each check
  reports back, and **Re-check** shows what changed since your last look.
- **A live price chart** (TradingView Lightweight Charts, GeckoTerminal data) with live trades up to every 10 seconds
  while the chart is open and visible.
- **Point and Talk:** click a coin and Hermes knows which one you mean; it lights up coins, opens cards and sets
  filters while it answers. Every coin has an **Ask Hermes** button, and Hermes shows coin cards in its replies.
  It says numbers in words, and it gives a contract address only in a code block you can copy, never read aloud.
- **Board talk:** two hosts (one voice with a non-Edge voice) read your board out loud with captions. To talk to Hermes about it, use Hermes' own mic
  button or Ctrl+Alt+V.
- **Rewind, alerts and a morning brief:** see the board as it was, get pop-ups for new calls and saved coins, and
  schedule a daily summary.
- The board as a full page or as a side pane beside your chat. It also works in chat apps like Telegram or Discord,
  with the free board.

**Why a plugin and not a prompt:** live data, tools that act on the board on your screen, numbers the plugin works out
itself, and a member board that is given only to your local Hermes chats (chat apps get the free board).

The free board needs no key. A member plan ($49 Gated or $99 Builder at piquesignal.xyz/unlock) adds the live member
board; nothing is bought inside Hermes. Deep Check and Board talk run on your own AI model and use your own AI
credits. Hermes' x_search uses your xAI API key if one is set in Hermes (billed by xAI per search), otherwise your
Grok sign-in. A Deep Check starts only when your own message asks for one (the words Deep Check or X check, or the
panel's Deep Check / Refresh X buttons): one coin per message, a message without those words is refused, never from a schedule, and never
inside a helper (delegate_task) or a chat the plugin has not seen.

The plugin's own page, with every feature, what it costs and the full disclosure of what it sends and stores, is
[piquesignal/README.md](piquesignal/README.md).

## Install

Once Pique Signal is listed in the Hermes plugin catalog:

1. Run `hermes plugins install piquesignal`.
2. Run `hermes plugins enable piquesignal`, then restart Hermes.
3. Switch on Pique Signal in Capabilities › Plugins.
4. Click **Pique Signal** in the Hermes sidebar.
5. Optional: paste your member key in Settings › Plugins › Pique Signal.

Full steps: [piquesignal/README.md#install](piquesignal/README.md#install). It needs Hermes Desktop 0.23.0 or later
with an AI model set up.

## Layout

- `piquesignal/` is the plugin. This is the folder Hermes installs and loads.
- `gen/` shows how `piquesignal/desktop/plugin.js` is built. It is for the maintainer only: rebuilding needs private
  files that are not in this repository, and you don't need anything in it to run the plugin. See
  [gen/README.md](gen/README.md).

## Support

Made by Pique Signal. Questions or bugs: piquesignal@gmail.com.

## Licences

The plugin is not open source. You may install and use it unchanged as a Hermes plugin and read its source to review
it: every file the plugin runs is in this repository, so anyone can check exactly what it does. See [LICENSE](LICENSE).

Three parts are under their own open licences:

- the fonts Hanken Grotesk, JetBrains Mono and Bricolage Grotesque: SIL Open Font License 1.1
  (`piquesignal/fonts/`);
- TradingView Lightweight Charts™: Apache License 2.0
  (`piquesignal/licenses/lightweight-charts-LICENSE.txt`);
- fancy-canvas, which Lightweight Charts uses: MIT (`piquesignal/licenses/fancy-canvas-LICENSE.txt`).

The chart data comes from GeckoTerminal's public API, a CoinGecko product ("Powered by GeckoTerminal",
https://www.geckoterminal.com/). The data belongs to GeckoTerminal; this plugin gives no rights to it.

Not financial advice. Memecoins are very risky. Pique Signal and its operators may hold or trade coins shown on the
board. Nothing trades or touches a wallet.
