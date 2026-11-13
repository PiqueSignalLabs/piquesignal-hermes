# How Pique Signal works

Hermes reads this guide to answer "how does Pique Signal work?". The Hermes plugin is section 9; the rest covers the website, plans and APIs.

## 1. What Pique Signal is
Pique Signal finds new Solana memecoins worth watching and puts them on one board. It warns you about junk, and shows how strong each coin has gotten.
- It is for research only. It is not financial advice.
- Memecoins are very risky. You can lose all your money. You make your own choices.
- We run rug and safety checks before we call a coin. Risky coins are removed or get a warning tag. But no check catches every rug. A "Rug risk" label is not a guarantee or an audit.
- Start on the free board. You do not need an account.
- Contact Pique Signal: piquesignal@gmail.com

## 2. All the ways to use Pique Signal
| Way | Who can use it | Where to start |
|---|---|---|
| Free board (website) | Everyone, no account | piquesignal.xyz/free |
| Gated board (website, live) | $49 Gated or $99 Builder | Sign in, open /gated |
| Early Edge | $49 Gated or $99 Builder; x402 passes; Grok blue-check trial | Gated board, ⚡ Early Edge tab |
| Featured Callers | $49 Gated or $99 Builder | Gated board, "Featured Callers" |
| Track record | Everyone, free | /track-record |
| Account page | $49 Gated or $99 Builder | "Account" at the top of the page |
| In-app bell alerts | $49 Gated or $99 Builder | Account → Alerts tab |
| Hermes plugin | Hermes Desktop users (free board without a key; gated board with your member key) | "Pique Signal" in the Hermes sidebar |
| Your AI app (MCP): Claude, ChatGPT, Gemini, Claude Code and others | $49 Gated or $99 Builder (needs your API key) | Account → API key → Connect your AI |
| Grok | Any X account, free (blue check gets a 7-day trial) | Grok connector settings |
| API key: pull the board, website webhooks | $49 Gated or $99 Builder | Account → API key |
| Builder API: backtest, live stream, webhooks by code | $99 Builder only | /api-docs |
| x402: an agent pays per use in USDC | Any agent, no account | /api-docs → Agent Feed |
| Agent listings (where agents find us) | Agents | See section 4.8 |
| X and Telegram (news and community) | Everyone | x.com/PiqueSignal, t.me/pique_signal |
| Affiliate program | Not open yet (coming soon) | /affiliate |

### 2.1 The website pages
- **Home page (piquesignal.xyz):** 4 doors.
  - **Human side** (/humans): a plain overview for people.
  - **AI side** (/ai): what an AI agent gets, and the ways in.
  - **Free board** (/free): look around, no sign-in.
  - **API docs** (/api-docs): technical docs for developers.
  - **Sign in** (top): your Solana wallet signs a message. This is not a payment. Paid members go to the gated board. Everyone else goes to the plans page (/unlock).
- **/humans:** how it works in 3 steps:
  1. Start on the free board. No account needed.
  2. Connect your Solana wallet (like Phantom) and sign in. No password.
  3. Pick a plan and pay from that same wallet. Your plan stays tied to it.
- **/ai:** the 3 ways in for AI: an agent that pays by itself (x402), your AI app with a $49 or $99 plan (MCP), or Grok.
- **/unlock:** the plans page. Buy here.
- **/account:** your Account page (paid members).
- **/featured:** Featured Callers (paid members).
- **/track-record:** our public track record.
- **/affiliate:** the affiliate page (coming soon).
- **/terms** and **/privacy:** the rules and the privacy policy.
- **/api-docs**, **/ai-agents**, **/grok:** pages for agents and developers.

### 2.2 Phones
- Pique Signal works on a phone. Phones get the real pages.
- No wallet in your phone browser? Tap Connect or Sign in. If no wallet is found, you see 3 links: **Phantom**, **Solflare** and **Backpack**. Tap one. The page opens inside that wallet app. Sign in there.

## 3. Plans and prices

### 3.1 The two plans
**Gated — $49**
- Live board, no 10-minute delay
- Clear Eyes strength read on every coin
- Early Edge
- Known rugs and dead coins removed
- Custom alerts in the app bell
- An API key to pull the live board
- Webhook: every pick sent to your server

**Builder — $99**
- Everything in Gated
- Developer REST API: pull and stream your picks
- Backtest (past picks and their results)
- Webhooks you manage with code, for your own systems

The free board stays free. No plan needed.

### 3.2 Subscribe or pay once
| | Subscribe | Pay once |
|---|---|---|
| Price | $49 a month (Gated) or $99 a month (Builder) | $49 (Gated) or $99 (Builder) |
| How long | Renews every 30 days until you cancel | 30 days from the day you pay |
| Pay with | USDC only | USDC or SOL (SOL shows a live price) |
| Renews by itself | Yes | No |

### 3.3 How to buy (step by step)
1. Go to **/unlock**.
2. Pick **Gated** or **Builder**.
3. Pick **Subscribe** or **Pay once**. For Pay once, pick USDC or SOL.
4. Tap **Connect wallet** (Phantom, Solflare or Backpack).
5. Approve in your wallet.
   - Subscribe usually asks for 2 approvals: "Approve 1 of 2 — set up", then "Approve 2 of 2 — confirm". If your wallet was set up before, you may only see the second one.
6. When it is done, you go to the live board.
   - If it says your first month is being set up, wait a minute and refresh. Do not pay again.

Good to know:
- No cards. You pay from your own Solana wallet.
- Keep a little SOL (about 0.01) for network fees, even when you pay in USDC.
- Your plan is tied to the wallet you pay with. Sign in later with the same wallet. Your plan works only with that wallet, so keep it safe. For help, email piquesignal@gmail.com.
- By paying, you agree to the Terms and the Privacy Policy.

### 3.3b If the payment does not go through
- **Not enough USDC:** add USDC to your wallet.
- **Not enough SOL:** add a little SOL (about 0.01) for network fees.
- **Checkout expired:** tap Pay again.
- **Your payment is still finishing:** the page picks it up again by itself, even if your wallet app reloads the page. Do not pay again.
- **Couldn't get the SOL price:** try again, or pay with USDC.
- **Too many attempts:** wait a minute.
- **Billing is paused for safety:** try again later.
- Still stuck? Email piquesignal@gmail.com with your transaction signature.

### 3.4 How the subscription takes money
- You sign a wallet approval. In your wallet, this approval has no set limit.
- But we only take the plan price shown when you subscribed, once every 30 days. Never more.
- Keep enough USDC for each renewal, plus a little SOL for fees.
- If a renewal cannot be paid, your access ends at the end of the time you paid for. We may try again for a short time. Access only goes on once a renewal is paid.
- We will tell you before any price change applies to your subscription.

### 3.5 Renew a pay-once plan
- Pay once does not renew by itself.
- Paying again before your access ends does **not** add days. While your access is active, the checkout sends you back to the board.
- To keep going: after your access ends, go to **/unlock** (opening Account also takes you there) and pay again. Or choose Subscribe.

### 3.6 Upgrade from Gated to Builder
- On /unlock, pick **Builder** and **Subscribe**. If you have Gated days left, the price is lowered and your Gated subscription is stopped for you.
- Your unused Gated days are credited (up to one month). Then Builder is $99 a month.
- The upgrade asks for a few wallet approvals: stop the $49 plan, pay the upgrade, then set up $99 a month.
- If you choose **Pay once** for Builder, you pay the full $99 and your Gated subscription is **not** stopped. Cancel it yourself on the Account page.

### 3.7 Switch plans
- **Gated to Builder:** use the upgrade in 3.6. It stops your Gated subscription for you.
- **Builder to Gated, or any other switch:** cancel on the Account page, wait until your paid time ends, then buy the new plan on /unlock.

### 3.8 Cancel (step by step)
1. Open **Account** (sign in with your paying wallet).
2. Account tab → **Manage plan** → **Cancel subscription**.
3. Then tap **Remove wallet approval** (you can also do this in your own wallet at any time).
- You keep access until the end of the time you already paid for. No more charges.
- It can take a few minutes for the Account page to show the cancel.

### 3.9 Refunds
- All payments are final. No refunds, except where the law requires one.
- EU and UK buyers have a 14-day right to withdraw. Email piquesignal@gmail.com within 14 days of paying.
- A refund is sent as a new payment to your wallet (blockchain payments cannot be reversed).

## 4. x402: AI agents pay per use
x402 is an open payment standard. An AI agent pays a small amount of USDC on Solana and reads the board. No account. No API key. No human login.
- The agent's wallet needs only USDC on Solana. No SOL is needed for fees (the payment service pays the network fee).
- Prices below are the ones our docs state. The price in the payment request (the "402 bill") is the final price. Always pay what the bill shows, to the address the bill shows.

### 4.1 The choices
| Choice | Price | How long | Daily calls | What it buys |
|---|---|---|---|---|
| Pay per call | $0.02 USDC per read | One read | — | One read of the current board (gated by default, or the free board) |
| Hour pass | $0.50 USDC | 1 hour | 600 | Live gated board, Early Edge, live stream |
| Day pass | $5.00 USDC | 24 hours | 5,000 | Live gated board, Early Edge, live stream |

- Early Edge is **not** in pay per call. It comes with the hour and day passes.

### 4.2 Pay per call (step by step)
1. The agent asks for the board: `GET /api/x402/feed?view=gated` (or `view=free` for the free board).
2. It gets a 402 bill. Getting the bill is free.
3. It pays the bill in USDC on Solana.
4. It sends the same request again, with the payment. It gets the board.
- One payment = one read.
- The free view has the same delay as the public free board.

### 4.3 Buy a pass (step by step)
1. Ask for a pass: `GET /api/x402/pass?tenor=hour` (or `tenor=day`).
2. Get the 402 bill (free to look at before paying).
3. Pay it in USDC on Solana. Send the request again with the payment.
4. You get a pass that starts with `pqx_`. **It is shown only once. Save it right away.**
5. Send it on every read: `Authorization: Bearer <your pass>`.

### 4.4 What a pass can read
- **The live board:** `/api/x402/agent-feed` — pick `view=gated` (default) or `view=free`. Add `limit=1` to `200` to get fewer coins. Leave it out to get the whole board.
- **Early Edge:** `/api/x402/early-edge`
- **Live stream:** `/api/x402/agent-feed/stream` — first the whole board, then each new call as it comes in. No polling.
- **Your pass status:** `/api/x402/me` (daily limit and calls used).
- **Health check:** `/api/x402/health` (no pass needed).
- The free view and the gated view are two separate lists. They are never mixed. The gated list is not just a faster copy of the free one: some coins are on both, and some are on only one.
- **What each coin has:** symbol, name, contract, coin age, entry and current market cap, holders and their growth, liquidity, 5m / 1h / 24h volume, 5m trades, top-10 holder % (when known), bundles, snipers, DEX paid, a fake-volume flag and socials. The gated view adds the Clear Eyes read, Real Crowd (when known) and a clean tag.

### 4.5 Pass rules and limits
- 30 requests a minute per pass.
- The daily call limit resets at midnight UTC.
- The stream uses 1 daily call per minute. Up to 2 streams at once per pass. A stream closes when the pass ends, when the daily limit is used up, or after 24 hours.
- We keep only a scrambled copy (a hash) of your pass. We cannot show it again.
- A pass is like cash. Do not share it.
- Pass expired? Buy a new one.

### 4.6 Paid but got no pass?
- Ask for the pass again with the **same** payment. You are not charged twice.
- Or email piquesignal@gmail.com with your Solana transaction signature.

### 4.6b Errors
- **onchain_unconfirmed (402):** the payment is still settling. Wait a few seconds and retry with the **same** payment. No double charge.
- **already_used (409):** this payment already made a pass.
- **pass_expired / pass_revoked / pass_inactive (403):** buy a new pass.
- **rate_limited / daily_quota_exceeded / too_many_streams (429):** slow down. The daily limit resets at midnight UTC. Max 2 streams.
- **502 or 503:** a short problem on our side. Retry later.
- **404:** check `/api/x402/health`.
- Full list: /api-docs.

### 4.7 Referrer
- Our terms let an agent name a referrer wallet that can earn a share of the payment, in USDC.
- This may not be switched on yet. When it is on, it works only on a pass purchase. A wallet cannot refer itself.
- This is separate from the affiliate program.

### 4.8 Where agents find us
- **x402 Bazaar:** listed as "Pique Signal".
- **Official MCP Registry:** listed as `xyz.piquesignal/signals` (our AI-app connector; it needs a paid key).
- **Agent menu:** some agents look for a menu at `/.well-known/agents.json`. When it is there, it lists our products and how to connect. The price in the 402 bill always wins.
- **Pages:** /ai, /ai-agents and /api-docs.

## 5. Your AI app (MCP)
Connect Pique Signal to your AI app and ask about the board in plain words.
- **Works with:** Claude, ChatGPT, Gemini, Claude Code, and any app that supports MCP.
- **Who:** $49 Gated or $99 Builder. You sign in with your API key.
- **Connection address:** `https://piquesignal.xyz/mcp`
- **Limits of the apps:** Claude Free allows one custom connector. ChatGPT depends on your plan. Gemini works with US personal Google accounts for now.

### 5.1 Connect it (Claude, ChatGPT, Gemini)
1. Make an API key: Account → **API key** → name it → **Generate key** → copy it.
2. In your AI app, open the connector settings and add a **custom connector**.
3. Paste the address: `https://piquesignal.xyz/mcp`
4. When it asks you to sign in, paste your API key and approve.
5. Ask: "What's on the board?"

### 5.2 Connect it (Claude Code)
1. Run: `claude mcp add --transport http piquesignal https://piquesignal.xyz/mcp`
2. Type `/mcp` and sign in with your API key.

### 5.3 What your AI can do
- **Read the board:** "Give me the full board." "What's on the board right now?"
- **Look at one coin:** "Tell me everything about <coin>." It can also give a coin's live price in SOL.
- **Switch views:** say "free view" or "gated view".
  - Free view: the same live coins, with the basics and tags only.
  - Gated view: adds the Clear Eyes read (climbing, fading, real, rug, tracking).
  - In AI apps the Clear Eyes read uses these short words. They are not the same as the board's steps (Early, Building, Peak).
- **Welcome screen:** ask for the welcome screen to see what you can ask.
- **Early Edge:** ask for "Early Edge". If it says Early Edge is not available, it is not on for AI apps yet.

### 5.4 Practice trading (fake money)
- Your AI can make practice buys and sells with **fake money**, and show your practice profit or loss. It is never real money.
- Ask: "Make a practice buy of 0.1 SOL of <coin>." "Show my practice positions." "Show my practice portfolio."
- Each practice buy is at most 0.5 SOL.
- Practice trades are kept in memory only. They reset (after about an hour with no use, after 24 hours at most, or when our server restarts).
- Prices come from a coin's pair priced in SOL. A coin with no SOL pair gets no practice price.
- Grok cannot do practice trading.

## 6. Grok
A free connector made for Grok. Sign in with X. No account, no API key, no card, no crypto.

| Your X account | What you get |
|---|---|
| Any X account | The free board (at least 10 minutes behind live). No Clear Eyes read. |
| Blue check (X Premium) | A 7-day free trial of the live gated board, with the Clear Eyes read. The trial also includes Early Edge. One trial per X account. After it ends, you stay on the free board. |

Set it up (about a minute):
1. In Grok, open your custom connector settings ("add your own connector").
2. Add this address: `https://grok.piquesignal.xyz/mcp`
3. Sign in with X when Grok asks.
4. Ask: "show me the Pique Signal board" or "what's moving".

Good to know:
- Just got X Premium? Reconnect the connector once to get your trial.
- Grok can only read. No practice trading.
- There is no separate price lookup in Grok. Ask for a ticker, and you get its row only if it is on the board right now.
- We only ask X for read permission. We never post for you.

## 7. API key, pull API, stream and webhooks

### 7.1 Make an API key (step by step)
1. Open Account → **API key** tab.
2. Type a name → **Generate key**.
3. You see your **API key** and your **signing secret**. Copy both now. They are not shown again.
- Up to 3 keys at a time.
- Send the key in a header: `Authorization: Bearer <key>`. Never put a key in a web address.
- Do not share keys or resell the data.

### 7.2 Pull API (any paid key: $49 Gated or $99 Builder)
- `/api/pull/feed` — your plan's live board (`limit=1` to `200`).
- `/api/pull/me` — your plan and your daily calls (used / limit).
- `/api/pull/early-edge` — the Early Edge list.
- `/api/pull/health` — health check.
- Each coin has the same fields as the x402 board (see 4.4). The gated board is a separate live list, not a faster copy of the free one.

### 7.3 Builder API ($99 Builder key only)
- `/api/pull/builder` — `view=gated` (default, a smaller list of stronger calls) or `view=free` (every call from the last 24 hours, one per coin, known rugs removed).
- `/api/pull/backtest` — past calls and how they ended. 48 hours delayed, last 30 days.
  - Filters: chain, phase, and start and end dates. Page through with `cursor` (the answer gives `next_cursor`). `limit` 1 to 500 (default 100).
- `/api/pull/backtest/stats?days=N` — counts and averages for past calls (days 1 to 365, default 30). This is not the same measure as the public track record.
- `/api/pull/builder/stream` — a live stream of new calls as they come in.
- If your Builder plan ended, you get "builder_expired". Renew to keep going.

### 7.4 Webhooks
Two ways:
- **Website Webhooks (Gated and Builder):**
  1. Make an API key first (7.1).
  2. Account → API key tab → **Webhooks** → type your **Endpoint URL** (must start with `https://`) → **Add webhook**.
  3. Every pick is sent (POSTed) to your address. It is signed in the header `X-Pique-Signature`, so your bot can check it is really from us. It uses the signing secret of your newest API key. If you make a new key, update the secret in your bot.
- **Webhooks by code (Builder only, when this feature is switched on for your key):**
  1. `POST /api/pull/builder/webhooks` with `{"url":"https://..."}`.
  2. Save the secret you get back. It is shown once.
  3. On each delivery, check the `X-Pique-Signature` header (HMAC-SHA256 of the raw body, made with your secret).
  - List: `GET`. Pause or resume: `PATCH` with `{"active":true}` or `false`. Remove: `DELETE`.
  - Up to 5 active webhooks per key. The address must be HTTPS and public.
  - If the call is refused, this feature is not on for your key yet. Use the website Webhooks tab instead.
- **Note:** the **Webhook** switch inside the Account **Alerts** tab shows "Available for Premium" and cannot be turned on. Use the **Webhooks** part of the API key tab (above).

### 7.5 Limits
- 60 requests a minute per key.
- A daily call limit. It resets at midnight UTC. See yours at `/api/pull/me`.
- Streams: up to 2 at once per key. Each uses 1 daily call per minute and closes after 24 hours. There is also a limit for the whole service: "stream_capacity" (503) means try later.
- **Errors:**
  - 401 missing_api_key: send the key in the header.
  - 403 key_revoked: the key was removed. Make a new one.
  - 403 builder_required: this needs a Builder key.
  - 403 builder_expired: renew Builder.
  - 403 quota_required: check `/api/pull/me`, or email us.
  - 429 rate_limited / daily_quota_exceeded: slow down. Resets at midnight UTC.
  - 503: retry later.
- Full details: /api-docs.

## 8. Alerts
- **In-app bell (Gated and Builder):** set your alerts on Account → **Alerts** → **Save alerts**. Read them in the bell on the gated board.
- **Website webhooks:** every pick sent to your server (see 7.4).
- **Telegram, phone push, email:** on the Account page these show "Available for Premium". There is no Premium plan to buy, so Gated and Builder members cannot turn them on there. X DM and phone text are not built yet.
- **The Telegram alert bot (@PiqueSignalAlertBot):** if you already get alerts there:
  - 3 kinds: **Spotted** (we just spotted a coin), **Confirmed** (it got strong enough), **Update** (it reached 2x, 5x, 10x after we confirmed it).
  - Strength: **Early**, **Building**, **Peak**. If it dies, it fades and stops pinging you.
  - Chips: **DEX PAID** (the project paid to boost its listing), **FAKE VOLUME** (the trading looks bundled or faked).
  - The card also shows holders, top 10, bundles, snipers and age.
  - Commands: /menu (change settings), /status, /help.
- **Hermes pop-ups:** see section 9.
- **Public Telegram (t.me/pique_signal)** is our community channel. It is not your personal alert feed.

## 9. The Hermes plugin
The Pique Signal board inside Hermes Desktop. The plugin never trades and never touches your wallet. Nothing is bought inside Hermes.

### 9.0 Install
1. Run `hermes plugins install piquesignal` (once it is in the catalog).
2. Run `hermes plugins enable piquesignal`.
3. Restart Hermes.
4. Turn on the Desktop part: Capabilities → Plugins (or Ctrl+K → Desktop plugins) → Pique Signal.
5. Click **Pique Signal** in the sidebar. A member key is optional (see 9.2).

### 9.1 Open the board
1. Click **Pique Signal** in the Hermes sidebar. The full computer board opens.
2. Without a key you see the free board (see 9.2 for the member board).
3. For the board beside your chat (a side pane; it shows the website's mobile view when you make the pane narrow), use the palette command below.
- Command palette: "Pique Signal: open the board", "Pique Signal: open the board beside the chat", "Pique Signal: preview the pop-ups", "Pique Signal: stop sharing the picked coin with Hermes".
- The status bar shows "Pique Signal" and the number of coins. Click it to open the board.

### 9.2 Free board or gated board
- Without a key, you see the free board. It is the same as piquesignal.xyz/free: at least 10 minutes behind live (up to 60 minutes for strong coins).
- **Member key** = your website API key. It unlocks the gated board in Hermes.
- **Unlock with your key** (the easy way): open the Hermes box (**Open ▾**); in the Ask part press **Unlock with your key** (on the gated board without a key it is also under the message). 3 short steps:
  1. **Get my key** opens your Account page in the browser: open the **API key** tab and copy your key (you need a $49 or $99 plan).
  2. **Open the key box** opens Hermes Settings at Pique Signal: paste your key in **Pique Signal member key** and press **Save**. Hermes keeps it as its own secret; the board never displays or stores it.
  3. Come back and press **Check my key**. It says "Key works - gated board unlocked", or in plain words what is wrong (no key yet, the key does not look right, Pique Signal refused it).
- The second way: paste it yourself in Hermes Settings → Plugins → Pique Signal → **Pique Signal member key**.
- To change the key, paste the new one the same way. The board cannot remove a key for you (it never touches the key).
- No key yet? The lock icon at the top of the free board (in the mobile view, **Unlock** in the menu) and **Unlock the live board** on the gated board without a key open /unlock in your browser.
- With a member key, Hermes reads the member board using your key's daily calls (also Early Edge, Featured Callers, the 24 h history for Rewind and the Missed tiles you click; see 9.14). All together they use at most 60% of your daily limit, and the member board is read never more than once a minute. This is counted per running Hermes program: a second one with the same key counts its own, so two together can use more.
- If your key is refused, Hermes waits about 15 minutes (plus a little random extra) before it tries again, and the member Rewind history and the saved coin pictures are erased. If only Early Edge or Featured Callers is refused for your key, only that part is hidden, and it is asked again about 15 minutes (plus a little random extra) later.

### 9.3 The Hermes box (above the board)
- The box starts **closed**: one line with **Board talk ▶**, **Rewind: Live** and **Open ▾**. The full page and the side pane each remember if you left the box open or closed.
- **Board talk ▶:** two hosts talk through your board out loud (see 9.12). When a Board talk is ready, it reads **Play ▶**.
- **Rewind: Live:** shows a short Rewind row under the line: the slider, the time and **Live**. Press **Rewind** again, **Live** or Esc to hide it (**Live** also goes back to now). It does not open the box. When you look at an earlier board, the button shows that time.
- **Open ▾** shows 4 parts. **Close ▴** (or Esc) folds them again.
  - **Ask:** **Ask about <coin>** (click a coin first; Hermes answers about "this one"), **How it works** (asks Hermes how Pique Signal works) and **Morning brief** (asks Hermes for a quick summary of the board now; this is not the daily Cron job in 9.9).
  - **Listen:** **Board talk ▶**, **Resume** and **Replay last** when they apply. One Board talk is made at a time.
  - **Rewind:** the slider (see 9.8) and **Back to live**.
  - **Alerts:** **Saved coins** on/off (pop-ups when a coin you saved changes) and **New calls** on/off (the same switch as the bell and Settings).
- One short line under the box shows news: a Board talk message first, then Resume, then "since you looked away".
- The buttons that ask Hermes something try to send the question for you. Sometimes the question is only put in the chat box: then press Enter to send it. If no chat is open, open a chat first.

### 9.4 Point and Talk
1. Click a coin card on the board.
2. In the chat, ask about "this one" (for example "show me the ones like it").
3. To stop, click "Hermes sees … ×" in the bottom bar.
- The card you clicked shows **SELECTED**. Hermes knows "this one" in Hermes Desktop and terminal chats, while the board is open.
- You can also stop sharing with the palette command, or turn this off in Settings.
- Every coin pop-up has an **Ask Hermes** button.
- When Hermes points at coins, they get a **FROM HERMES** label.

### 9.5 Ask Hermes to do things
- Read the board: "What's on my board?" "Which coins are like this one?"
- Show coins: Hermes can light up coin cards one by one, or open a coin's pop-up.
- Filter: "Show me only DEX paid." Hermes sets the filters and search for you. "Clear the filters" turns them off.
- Ask what a tag means: "What does Fake Volume mean?"
- Answer how Pique Signal works (from this guide).
- **Contract addresses in replies:** replies may be read aloud, so when you ask for a coin's contract address Hermes writes it only inside a fenced ``` code block (shown and copyable, never read aloud), never in normal text or inline code. The same rule holds in every chat (Desktop, Telegram, Discord ...).

### 9.6 Coin cards in chat
- In Desktop chats, while the board is open, when Hermes names a coin on your board, a small card appears. This works when you picked a coin or your question is about the board. Click it to open the coin.
- Gated-board coins need your member key.

### 9.7 Pop-ups
1. New calls pop up in the corner by themselves (the first load never pops up).
2. Star a coin to get pop-ups when it changes.
3. Turn pop-ups on or off with the bell (gated board), in the Hermes box (Open ▾ → Alerts) or in Settings.
- **New calls:** small pop-ups in the corner, with **Open** and **Ask Hermes**. When Hermes is in the background, you may also get a system notification.
- **Saved coins:** a pop-up when a coin you saved changes (Fake Volume, DEX paid, Clear Eyes, or it left the board).
- **The bell on the gated board** (in Hermes) turns new-call pop-ups on or off. Dimmed = off. The website alert list is not shown in Hermes.

### 9.8 Rewind and "since you looked away"
1. Press **Rewind: Live** in the Hermes box (Rewind is on by default; it can be switched off in Settings).
2. Drag the slider back to an earlier time.
3. Press **Live** to go back to now (Esc only hides the Rewind row).
- **Rewind:** slide back to see the board as it was. It saves the board every 10 minutes while the Pique Signal board is open, for up to one day, only on this computer. It is never uploaded. Rewind is on by default and can be switched off in Settings. The gated board needs your member key. **Back to live** returns to now.
- **The last 24 hours from Pique Signal:** when your newest Rewind snapshot of that board is more than 15 minutes old (or there is none, for example Hermes was closed), Hermes asks piquesignal.xyz for that board's last 24 hours (one board every 10 minutes) and adds it to Rewind. It asks at most once every 20 minutes per board, and waits a random 0 to 2 minutes after Hermes starts. Your own Rewind snapshots win: a server board within 5 minutes of one of yours is skipped. The free board's history has only the coins that are on the free board now, so coins that came and went while you were away are not in it. The member board's history needs your member key and is kept only for that same key. If Pique Signal answers that a board's 24 h history does not exist, Hermes does not ask for it again until Hermes restarts.
- **While you were away:** the first time the history fills Rewind, one line sums up what changed (if anything did), and, if saved-coin pop-ups are on, one pop-up lists your saved coins that changed.
- **Since you looked away:** after 2 minutes or more away, if anything changed, a line shows what changed. **Ask Hermes** gives a short catch-up.

### 9.9 Morning brief (daily)
1. Open the Hermes **Cron** page.
2. Pick **Pique Signal morning brief**.
3. Set the time, the board and where it goes, then save it.
- Pick the time (default 08:00), which board (auto, free or gated), and where it goes (**Where to deliver?**: origin = this chat, local = save only).
- "auto" = your member board if your member key is set, else the free board. If the brief goes to a chat app (not a Hermes chat), it uses the free board.
- It gives the newest calls, the biggest moves and any warning tags. It never gives hit rates.
- The morning brief is a normal Hermes cron job. It keeps running if you turn off the plugin. To stop it, delete it on the Cron page.

### 9.10 Settings (Settings → Plugins → Pique Signal)
6 switches:
1. Pop-ups for new calls (on by default).
2. Pop-ups when a saved coin changes (on by default).
3. Let Hermes see the coin I click on the board (Desktop and terminal chats; on by default).
4. Rewind: keep the board history on this computer (up to a day; never uploaded; on by default).
5. Morning Board talk: get one ready each morning while Hermes is open (it never plays by itself), with its time (off by default).
6. Board talk: short music stings between segments (on by default).
Your member key also goes here, with two more settings: **Let Hermes use my member board in chats** (on by default; see 9.11) and **Speak Board talk through Hermes' tool call** (off by default; see 9.12).

### 9.11 Privacy in Hermes
- Your AI model gets board facts only: the coin's name, symbol, contract, numbers and tags. With a member key, that includes the Clear Eyes step, the Clear Eyes note and the Real Crowd line, so those go to your AI model's provider too.
- Hermes can use the Pique Signal tools in any chat it runs, also in chat apps like Telegram or Discord, and the answer goes to that chat. The member board is given only in Hermes Desktop, terminal and CLI chats (and a scheduled morning brief kept in Hermes; a brief with extra words or settings gets the free board; a cron job that reads the brief's output sends it where that job delivers). Chat apps get the free board. A chat that another agent (Hermes Bot Mode), a chat app or a kanban card wrote in, a chat that sent a message to another agent, and the Bot Chat get the free board from then on, also after Hermes restarts; open a new chat for the member board. Hermes' own notices, such as a cron job's result, get the free board for that one turn. Your own chats keep it after a restart and through pictures, voice, model switches and your own background jobs. A chat also gets the free board from then on when you paste another agent's Bot Mode message or a kanban notice into it. Text another plugin puts into a chat counts as yours when Hermes does not label it; when Hermes labels it, that chat gets the free board from then on. Member facts already shown in a chat stay in its history: start a new chat before Hermes messages another agent. To keep the member board out of every chat, turn off "Let Hermes use my member board in chats" in Settings > Plugins > Pique Signal (do this if a chat of yours is linked to a Telegram or Discord group); turning it back on takes effect after Hermes restarts. The board page itself always keeps your member board. If you use Bot Mode, agents you let message your Hermes can use its tools: only add agents you trust.
- For pop-ups, Hermes saves the coin's picture from Dexscreener on this computer (up to 40). After your member key is removed, changed or refused, they are erased the next time the board checks the key.
- Hermes' plugin storage also keeps your Early Edge panel choices.
- No tracking. The website's analytics are not in the plugin.
- Links open in your browser, not inside Hermes.
- Switching Rewind off erases its history (also the 24 h history it got from Pique Signal).
- The Missed strip, Free Pick, banners, Featured Callers and the 24 h history are shown on the board only. Hermes' tools do not read them. Missed and banner pictures and Missed reveals are kept in memory only (gone when Hermes stops).
- Banners send no view or click counts. A banner link opens in your browser.
- Pique Signal never opens the mic and never records. Talking to Hermes by voice is Hermes' own feature (see 9.13).
- Whenever Deep Check runs (button, chat, or a chat app), this PC sends the coin's public contract address to api.dexscreener.com; that site sees your IP address; no key, no other data. The X check sends the same contract address to xAI (Grok) through Hermes' own x_search. Hermes' x_search uses your xAI API key if one is set in Hermes (billed by xAI per search), otherwise your Grok sign-in. On the member board this lets those services see which coin was checked. Deep Check uses your own AI model: the helpers get a run id, the part name and the contract address, and read back that part's fixed line (on a member check, the member lines too; Hermes may run helpers on the model set for delegation). Dexscreener's answer and the X posts' text never reach it.
- The last Deep Check per coin (up to 20 coins, 24 h) is kept in the Desktop data folder (deepcheck-free.json, deepcheck-gated.json): each checked coin's contract address and ticker, the card's lines, numbers and times, and for On X the account names, post times and public post ids (also from your earlier checks of that coin, so the timeline continues). The member file is tagged with your key's one-way id (never the key); the member file is erased when the key is removed, changed or refused; nothing is uploaded.
- The price chart (the Chart button in a coin pop-up or in the Deep Check card) loads only when you open it or switch its time frame. It sends the coin's contract address to api.dexscreener.com (to find the pair, the same read as Deep Check) and then that pair's pool address and the coin's contract address (both public) to api.geckoterminal.com; those sites see your IP address; no key, no other data. On the member board this lets them see which coin's chart was opened. The candles are kept in memory for a minute only and never reach your AI model. While a chart is open and visible, it asks GeckoTerminal for that pool's latest trades at most every 10 seconds; it pauses when hidden and stops when closed or after 15 minutes without a click or key press in the chart, and 20 minutes after the chart last loaded (a click resumes it: the chart loads again first) (the pool address only; the trades stay in memory and never reach your AI model).
- The Hermes box remembers only whether it is open or closed, on this computer. Hermes' plugin storage also keeps the result of the last voice test and the day of the last morning Board talk try.

### 9.12 Board talk
1. Press **Board talk ▶** in the Hermes box.
2. Wait up to half a minute; it starts by itself when ready.
3. Use **Pause**, **Skip**, **Back** or **Stop** in the player.
- **What it is:** press **Board talk ▶** in the Hermes box. Two hosts talk through your board out loud, coin by coin, with captions. It starts when ready, in up to half a minute. The board lights the coin on air and opens its card.
- **The player:** while Board talk plays, the player takes the place of the box's line. It shows who is speaking, the segment, one dot per coin ("Coin 3 of 6") and big captions. **Hermes ▾** opens the Hermes parts under the player.
- **Segments:** Biggest movers, New arrivals, Watch out (tags that just came on) and Your coins (your saved coins).
- **Buttons:** **Back** (the coin before), **Pause** and **Play**, **Skip** (the next coin), **More**, **Ask** and **Stop**. At the end: **Replay** and **Close**. Keys: Esc = Pause or Play (if the Hermes parts are open under the player, Esc closes them first); ← and → = Back and Skip while you are in the player.
- **More and Ask:** Board talk pauses and the coin on air goes to Hermes. **More** asks what the board says about it now and what changed. **Ask** asks about this one. Hermes answers in the chat.
- **Resume:** after **Stop** (or a pause of 10 minutes), **Resume** goes on from the coin where you stopped. It plays the same Board talk again, so it works only on the same board (on the member board, with the same member key) and while that Board talk is still kept (up to 6 hours; a new Board talk replaces it). If Resume cannot go on, it says why.
- **One at a time:** only one Board talk is made at a time (press again while one is being made and it says so; wait a moment, then try again). It runs on your own AI model and voice, so each new Board talk uses your own credits. **Replay** and **Resume** ask your AI model nothing.
- **Morning Board talk:** off by default. Turn it on in Settings and pick a time. It gets one ready while Hermes is open. It never plays by itself: you press **Play**.
- **Voices:** two voices only with the Edge voice in Hermes settings (Settings → Voice). Any other voice = one voice, through Hermes' own speech tool. The setting **Speak Board talk through Hermes' tool call** (off by default) has Hermes run that tool through its public tool call instead, from the next line; if Board talk stops speaking, turn it off.
- **Numbers:** the board's own values. The "earlier" sentences (holders or status earlier) need the board open for about 30 minutes after Hermes starts.
- **What is sent:** to your own AI model, for the coins it talks about (up to 8): the coin tickers, tags, times on the board, which coins you saved, which part of the Board talk each coin is in (biggest movers, new arrivals or your coins) and which board (free or member), what changed, and the board's own numbers (change since flagged, market cap now and when flagged, holders and earlier holder counts), and the board's counts (coins on the board, new calls, coins that left the board, and the minutes since you looked away or since the earlier board). On the member board also the status words with earlier steps and the Real Crowd real and shown counts. To your voice service: the words to speak, with those numbers. No coin addresses, scores, wallets or keys are sent. Back, Skip and Resume ask your AI model nothing. Each spoken line passes briefly through a temporary file that is deleted as soon as the line is read (a crash can leave one in the system temp folder); the voice already made for this Board talk is then kept in memory only and is gone when it stops.
- Research only, not advice.

### 9.13 Talking to Hermes by voice
- Pique Signal has no voice chat button of its own. To ask about your board by voice, use Hermes' own mic button in the chat box or press Ctrl+Alt+V. Pause Board talk first: the mic may hear the hosts.
- **Hear the answers:** hover an answer in the chat and press the speaker, or turn on **Read replies aloud** in the chat box voice controls (hover the mic button). Spoken answers use the voice set in Hermes (Settings → Voice).
- Your voice is handled by Hermes only (Settings → Voice). Pique Signal never opens the mic and never records.

### 9.14 Missed strip, Free Pick, banners and Featured Callers
1. Free board: the Missed strip, the Free Pick and the banners (marked "Ad") are part of the board.
2. Member board: press **Featured Callers** (computer) or **Featured** in the mobile view's menu (side pane). Free board: the **Featured Callers** link under the Hermes row.
3. Click a call for its details, then **Open on board**; or click a Missed tile (with a member key) to open that coin.
- **Missed strip** ("Paid gets it first", free board): up to 5 paid calls that went up, with the gain and how long ago only. No coin name or address comes with it. With a member key, click a tile and Hermes asks which coin it was and opens it on the member board (only on your click: at most one every 10 seconds and 50 a day, at most 10% of your key's daily limit; an answer is kept 30 minutes). Without a key, a click opens the gated board.
- **Free Pick** (free board): the free board's live pick with its countdown, the same as on the website. When there is no live pick, it says "No live pick right now" with a countdown to the next one.
- **Banners** (free board): banners marked "Ad" above the coins, changing every 4 seconds. A click opens the banner link in your browser. No view or click is counted.
- **Featured Callers** (member board, member key): the website's "Featured Callers" button (computer) or "Featured" in the mobile view's menu (side pane) opens the callers and their newest calls inside Hermes. The button shows only when there are callers (with none, "Featured" in the mobile view's menu (side pane) opens the website page in your browser). Call notes are plain text (no links inside them). Click a call to see its details: **Copy** (the contract), **Dexscreener**, **Solscan** and **pump.fun** (open in your browser) and **Open on board** (that coin on the member board). A caller with a valid Telegram channel name has a **Telegram** button that opens the channel in your browser.
- **Featured Callers on the free board** (no key): the link shows only when there are callers and opens the same pop-up. As on the website, **Open on board** opens that coin on the member board.
- **What is sent:** these parts are read from piquesignal.xyz by the plugin's backend only (fixed addresses, no query string). Missed, Free Pick, banners, their pictures and the free board's Featured Callers (GET /api/free-board/featured) need no key, and your key is never sent with them. Featured Callers, the member 24 h history and Missed reveals use your member key and count toward your daily calls. Missed, Free Pick and banners are asked at most every 30 seconds (banners every 5 minutes) while the free board is open; the free board's Featured Callers at most once a minute while the free board is open; the member Featured Callers at most every 15 minutes while the member board is open. Each part waits a random 0 to 2 minutes after Hermes starts (not Missed reveals and pictures). If Pique Signal refuses a part, Hermes stops asking it for about 15 minutes (plus a little random extra) and hides it. If Pique Signal is busy, the last good answer stays.
- **What is stored:** nothing new on disk except the 24 h history inside Rewind (see 9.8). Missed and banner pictures and Missed reveals are kept in memory only.
- Hermes' tools never read these parts: they are shown on the board only.

### 9.15 Deep Check
1. Open a coin's pop-up and press **Deep Check** (or type "Deep Check $ABC" in a chat).
2. Watch the card fill in line by line. Tap a line for its numbers and source.
3. Later, open it again and press **Re-check** to see what changed.
- **Where:** the **Deep Check** button in every coin pop-up (next to **Ask Hermes**) and on Hermes' chat coin cards. Or type "Deep Check $ABC" in a Hermes chat. "X check $ABC" runs only the On X part.
- **What happens:** Hermes runs the checks of that one coin with its own helpers (or one by one in the chat), on your own AI model (it uses your own model's credits; Hermes may run helpers on the model set for delegation). A blue result card opens on the board and fills in line by line. You can move it and change its size, and the chat stays usable.
- **The card:** the coin, a count line (for example "4 green · 2 red · 1 unknown") and one checked-at time. Red lines first, then green, then unknown. Tap a line to see its numbers, where each one comes from ("Your board", "Dexscreener (live)" or "X via Grok") and its own time. There is no verdict and no advice: each line says only what the board or the live data shows.
- **Free board:** Fake Volume tag, what changed since it was flagged, the live numbers from Dexscreener next to the board's (the free board is at least 10 minutes behind, so the line says how old the board is), and On X. A locked line names what members also get. The card's **Unlock** button opens the 3 key steps in the Hermes box (see 9.2), not the website.
- **Live numbers:** taken from the coin's pair with the most trading in the last hour (its exchange is named in the details). When Dexscreener's pairs disagree (prices more than 5 times apart, that pair had very little trading in the last hour, or a dead pair traded more than it in the last hour while that pair holds under a thousand dollars of liquidity), the line says "Live price unclear: Dexscreener pairs disagree" (grey) and shows no number. A dead pair (under a hundred dollars of liquidity, or no liquidity reported and no trading in the last 5 minutes) is never used while a live pair exists; its price is left out of the 5-times price check only when the pair used clearly took over: at least a thousand dollars of liquidity and at least 3 times that pair's trading over both the last 24 hours and the last hour.
- **Member board:** the same plus Clear Eyes and Real Crowd.
- **No Fake Volume tag** is shown as unknown (grey), never as green: the board only ever adds the tag.
- **On X:** the X posts Grok cites for the coin's contract address in the last two days (the search asks for up to 15 of the most recent, so it stays quick), with the account names and post times. The line counts the last day, for example "On X: 10 posts from 7 accounts in the last day" (when Grok cites 15 or more posts it says "N+ posts (only the most recent posts were read)", for example "15+ posts"); its details add how many accounts posted more than once ("3 accounts posted more than once") and, when 3 or more posts came close together, the biggest burst ("6 posts within 10 minutes", the most posts in any 10 minutes). These come only from the post links' account names and times. The line is grey (unknown): posts found say nothing on their own about the coin. An hourly timeline shows when the posts came; two pickers compare the last 1-24 h with the hours before (for example "4 posts vs 1 post"), from the saved post times (no new search); when the newest X check hit that 15-post limit the compare is left out, since only the most recent posts come back and earlier hours could look quieter than they were. Hermes' x_search uses your xAI API key if one is set in Hermes (billed by xAI per search), otherwise your Grok sign-in; without either, the line says "X check needs a Grok sign-in in Hermes" (or "X check not available"). The X search starts as soon as the Deep Check starts; it can take about a minute, and the other lines fill in first. **Refresh X** runs only On X again. One X search runs at a time: a new X check says "X check already running" until the earlier x_search call has really ended, which can take up to Hermes' own x_search time limit for each of its tries (about 9 minutes with Hermes' defaults; after 15 minutes the next X check starts anyway).
- **Time limits:** a line still open after about 30 seconds says "still checking…"; after about 90 seconds it says "not available, try Re-check". A late On X result still fills in for up to about 150 seconds; after that the plugin stops waiting, drops a later answer and the line says "X check not available".
- **Saved:** the last Deep Check of each coin (up to 20 coins, 24 h) is kept on this computer. Opening it again shows when it was checked; **Re-check** runs a fresh one and shows what changed since your last check.
- **In chat:** Hermes answers with a short 2-3 line version. In a chat app (Telegram, Discord ...) Deep Check is the free one and only that short version is sent there; the card is shown only in Hermes Desktop.
- A Deep Check starts only when your own message asks for one (the words Deep Check or X check, or the panel's Deep Check / Refresh X buttons): one coin per message, a message without those words is refused, never from a schedule, and never inside a helper (delegate_task) or a chat the plugin has not seen.

### 9.16 Price chart
1. Open a coin's pop-up (or a Deep Check card) and press **Chart**.
2. Pick **5m**, **1h** or **24h**.
3. Leave it open to see live trades. Close it to stop them.
- **Where:** the **Chart** button in the coin pop-up or in the Deep Check card. It loads only when you open it or switch its time frame: **5m**, **1h** or **24h** candles (24h candles are whole UTC days and carry their UTC date). The candles are never asked on a timer or in the background (the live trades below run only while the chart is open and visible).
- **Which pair:** the same pair Deep Check uses for its live numbers (the pair with the most trading in the last hour on Dexscreener); the chart names it (its exchange and a short pool address). The chart shows whenever Dexscreener lists a SOL or USDC pair for the coin, good or bad: a quiet coin and pairs that disagree get their chart too (Deep Check still says "Live price unclear" when the pairs disagree). There is no chart only when no pair is found. The coin's own price is always drawn, even in a pool listed the other way round.
- **Data:** the candles come from GeckoTerminal's public API, a CoinGecko product ("Powered by GeckoTerminal" is shown on the chart). Only the pair's pool address and the coin's contract address (both public) are sent to GeckoTerminal, with no key. The data belongs to GeckoTerminal; this plugin gives no rights to it.
- **Drawing:** TradingView Lightweight Charts™ Copyright (c) TradingView, Inc. (https://www.tradingview.com/), bundled under the Apache License 2.0. Its link opens in your browser.
- **Live trades:** while a chart is open and visible, it asks GeckoTerminal for that pool's latest trades at most every 10 seconds; it pauses when hidden and stops when closed or after 15 minutes without a click or key press in the chart, and 20 minutes after the chart last loaded (a click resumes it: "Live updates paused - click to resume"; the chart loads again first, as when you open it). New trades update the last candle or start the next one, and the chart shows "Live · updated" with the time. Only the pool address of that chart is sent (no key); only each trade's time, side, price, USD volume and id are kept, in memory. When GeckoTerminal is busy it says "Live updates paused" and waits longer each time (up to 2 minutes). No live trades when there is no chart.
- **Expand:** opens the same chart as a full page, with the same controls. **Back** returns to the board.
- **Limits:** the same pair and time frame is asked at most once a minute; when GeckoTerminal is busy, the chart says it is not available and the plugin waits quietly (at most 15 minutes) before asking again.
- The chart shows past prices only: no verdict and no advice.

## 10. The boards
- **Free board:** free. It runs at least 10 minutes behind live (up to 60 minutes for strong coins). No account needed.
- **Free live pick:** the free board gives one live pick every 3 hours. If there is none, it says "No live pick right now" with a countdown to the next one.
- **"Paid gets it first" strip** (free board): up to 5 paid calls that went up 2x or more in the last 24 hours. Coin names are hidden; only the gain shows. It is hidden when there is nothing to show.
- **Gated board:** live, no delay. You need a paid plan ($49 Gated or $99 Builder).
- If you open the gated board without a plan, it is blurred. Tap "Unlock the board" to pay, or "Keep viewing the free feed".
- On the website the board updates itself about every 20 seconds. In Hermes the free board updates at most every 30 seconds and the member board at most once a minute. The top line shows the time of the last update. "↻ Refresh" updates it right away.
- Both boards work on a computer and on a phone.

### 10.1 Coin cards and tags
Each card shows the coin picture, name, how much it went up or down since we flagged it (like "2.3x"), its market cap, and how long ago it was flagged.
The faint line behind a card is just decoration. It is not a price chart. For a real chart, press **Chart** in the coin pop-up (in Hermes) or use "Chart on Dexscreener" (it opens Dexscreener).

Tags:
- **Fake Volume:** red = the trading looks faked or bundled; orange = fake volume that comes and goes. Be careful.
- **Padded crowd:** the holder count looks bigger than it really is. Most holders own almost nothing.
- **DEX paid:** the project paid to boost its listing.

Click a card to open the coin pop-up. It shows market cap, liquidity, holders, trading in the last 5 minutes, volume and more. You can copy the contract, open a chart, search on X, visit the coin's own links, and "Buy on" your chosen app (Axiom, Photon, BullX, GMGN, Pump.fun, Jupiter or Phantom). Your "Buy on" choice is remembered on this device.
- **Real Crowd:** compares the holder count the coin shows with how many wallets really hold a real amount. A big gap means a padded crowd.
- **Clear Eyes** (gated board): how strong the coin has gotten. Steps: Flagged → Early → Building → Peak. If it dies, it shows Faded. It can also say Pulled back (below where we flagged it), Under $15k, or Rug risk (the board's rug checks flagged this coin).
- **Top Holders** (gated board on the website only; not in Hermes): the biggest known holders and how much they hold.

### 10.2 Filters, search and saved coins
- **Search:** type a coin name, symbol or contract address.
- **Filters:** Clean (keeps only coins that pass the board's safety checks), Fresh (flagged recently), Moving (going up), Low cap (small market cap), DEX paid, Vol 5m / Vol 1h (enough trading), Holders ↑ (holders growing), Hide fake vol. The gated board adds a Clear Eyes filter. There are more filters under "More". "Clear" resets them all.
- **In Hermes:** three website filters (Caller, Flash point and Signals) are left out.
- **Saved coins:** tap the ★ (phone) or drag a card to the side (computer). "Saved" opens your list. It is kept on this device only. The free board and gated board keep separate lists.

### 10.3 Other board parts
- **Alerts bell** (gated board): on the website it shows your unread alerts. Click one to open that coin. You can turn on phone or browser notifications here. On iPhone, add the site to your Home Screen first. In Hermes the bell turns new-call pop-ups on or off (see 9.7).
- **Connect / Account:** sign in by approving a message in your Solana wallet. This is not a payment.
- **Ad banner:** the free board may show a banner marked "Ad".
- **Cookie settings:** at the bottom of the board.

## 11. Early Edge, Featured Callers and the track record

### 11.1 Early Edge
Early Edge is a paid list of coins picked up early. On a computer, click the ⚡ Early Edge tab on the gated board. On a phone, open it from the menu. Without a plan, it shows a locked card with Unlock. Turn it on with its switch. New finds show up in the list. Click a coin to open it. "Tune what you see" has a few on/off choices for what the list shows.
- Who: $49 Gated and $99 Builder. Agents also get it with an x402 hour or day pass, with a paid API key, and in the Grok blue-check trial.

### 11.2 Featured Callers
- Callers we back, with their newest calls.
- Who: paid members ($49 Gated or $99 Builder). Free users cannot open it.
- Open it from the "Featured Callers" button on the gated board (computer) or "Featured" in the phone menu. On a computer the button shows only when there are callers.
- Open a call to see the note, copy the contract, and find links.

### 11.3 Track record
- Free for everyone: **/track-record**.
- It shows how far the coins we flagged ran, from the market cap when we flagged them to their peak: counts of runners (2x and up to 100x and more), recent winners, and all-time numbers.
- Agents can read it as data at `/api/track_record_public` (no key).
- Past results do not promise future results.

## 12. Your Account page
For paid members ($49 Gated or $99 Builder). If you have no plan, it sends you to /unlock. Sign in with the wallet you paid with.

7 tabs:
- **Account:** your plan, status, renew date and wallet. **Manage plan:** Cancel subscription, Renew (pay-once plans), Remove wallet approval.
- **Profile:** an optional username. Type it → **Save name**. Without one, your wallet is your name.
- **Alerts:** choose which coins ping you.
  - Minimum strength: Early+, Building+ or Peak.
  - Max market cap: skip bigger coins.
  - Hide fake volume.
  - Only fresh: brand-new coins (under 1 hour).
  - Repeat: Once, When it gets stronger, or Every time.
  - Where it goes: the in-app bell.
  - Then press **Save alerts**.
  - If shown, you can also pick a Volume (Focused, Balanced or Everything), which signals ping you (Spotted, Confirmed, Updates and the update levels), and which list your alerts watch (Free board or Clean board).
- **Connections:** your wallet, the alert channels and an email field. Telegram, phone push and email alerts show "Available for Premium" and are not open to Gated or Builder.
- **API key:** up to 3 keys (see 7.1). Also **Webhooks** (see 7.4) and **Connect your AI** (see 5 and 6).
- **Billing:** your plan, status, renew or end date, and your past payments with receipts.
- **Security:** **Sign out** of this device. Manage API keys, connected apps and wallet approvals.

## 13. Affiliates
- Coming soon. It is not open yet.
- The page says you will earn 25% in USDC of every payment from people you refer, including renewals, paid to your wallet.
- Until it opens, referral links earn nothing.

## 14. Rules, privacy and help

### 14.1 Rules (Terms, short)
- You must be 18 or older.
- You may not use it if you are on a sanctions list or in a sanctioned country or region.
- Not financial advice. You can lose all your money. Past results do not promise future results.
- Pique Signal and its operators may hold or trade coins shown on the boards.
- Up to 3 API keys at a time.
- Do not share your sign-in, keys or passes. Do not resell, share or post our API data without permission.
- You may mention our calls in your own trading notes or posts if you credit Pique Signal.
- No scraping. Use only the ways we offer: API, AI apps (MCP), Grok, x402.
- Texas law applies. EU and UK consumers keep the protections of their own law.
- Full rules: /terms

### 14.2 Privacy (short)
- You sign in with your wallet. We never see your private key or seed phrase.
- We do not take card payments. Payments are public on the Solana blockchain.
- We do not sell your data.
- Analytics run only if you press **Accept** on the cookie banner. Change it any time with "Cookie settings" at the bottom of the board.
- Board visit records are kept 12 months. Web server and API logs are kept 14 days.
- We use data to improve our AI models. EU and UK users can ask us to stop.
- You can ask us to see, fix or delete your data. We cannot delete blockchain records.
- Signing out on the Account page clears your wallet, name and alert details from this browser. To remove everything, clear this site's data.
- Full policy: /privacy

### 14.3 Help and contact
- Email: piquesignal@gmail.com
- X: x.com/PiqueSignal
- Telegram: t.me/pique_signal
- Past picks: /track-record

## 15. Quick answers
- **Is it free?** The free board, the track record and the Grok free board are free. The live board needs $49 Gated or $99 Builder.
- **Do I need an account for the free board?** No.
- **How do I sign in?** Connect your Solana wallet and approve a message. It is not a payment. No password.
- **How long do I stay signed in?** Up to 90 days, or until you sign out.
- **Can I share a call on X?** Yes, in your own notes or posts, if you credit Pique Signal. Do not resell the data.
- **Are all rugs removed?** No check catches every rug. Risky coins are removed or get a warning tag. Always check for yourself.
- **I lost my wallet or want a new one.** Your plan works only with the wallet you paid from. Email piquesignal@gmail.com for help.
- **Can I pay with a card?** No. USDC or SOL from your Solana wallet.
- **Which wallets?** Phantom, Solflare or Backpack.
- **What is the difference between $49 and $99?** Builder ($99) adds the developer API: backtest, live stream and webhooks by code.
- **Subscribe or pay once?** Subscribe renews every 30 days in USDC. Pay once gives 30 days in USDC or SOL and does not renew.
- **Can I pay early to add days?** No. Renew after your access ends, or subscribe.
- **How do I cancel?** Account → Manage plan → Cancel subscription. Then Remove wallet approval.
- **Do I get a refund?** Payments are final, except where the law requires. EU/UK: email within 14 days.
- **Why can't I open the Account page?** It is for paid members. Sign in with the wallet you paid with.
- **Can I get alerts on Telegram, by email or by push?** Not with Gated or Builder right now. Use the in-app bell or webhooks.
- **Can I get alerts for free?** Website alerts (the bell) are for the $49 and $99 plans. In Hermes, the free board can show pop-ups for new calls with no key.
- **How do I connect Claude, ChatGPT or Gemini?** Make an API key, add a custom connector with `https://piquesignal.xyz/mcp`, and sign in with your key.
- **Is Grok free?** Yes. Any X account gets the free board. A blue check gets a 7-day live trial.
- **Can my AI trade for me?** Only practice trades with fake money, in MCP apps. Never real money.
- **Can an agent use Pique Signal without an account?** Yes, with x402: $0.02 per read, $0.50 for an hour pass, or $5.00 for a day pass (the 402 bill shows the final price).
- **I lost my API key or pass.** We cannot show it again. Make a new key, or buy a new pass.
- **Does my agent need SOL for x402?** No. Only USDC.
- **How do I unlock the gated board in Hermes?** Paste your website API key in Settings → Plugins → Pique Signal.
- **Is my Rewind history uploaded?** No. It stays on your computer, up to one day.
- **Does it work on my phone?** Yes. If your browser has no wallet, open the page in the Phantom, Solflare or Backpack app.
- **Can I join the affiliate program?** Not yet. It is coming soon.
- **How do you pick the coins?** We do not share how we find coins. Check our results on /track-record.
- **Is this financial advice?** No. It is research only.

