# Disclosure text for the HERMES_LIVE switch (LIVE in this release)

This file is kept with the tests. It is not shown to users. `core.HERMES_LIVE` and the pane's `HERMES_LIVE` are both
`True` in this release (the server side is installed and public), so the addresses below ARE called, and this text is
in `README.md`, `plugin.yaml`, `guide.md` (section 9.2, 9.8, 9.11 and 9.14) and the `core.py` / `feed_client.py`
headers. The test `test_docs_live.py` fails while the switch is on and these words are missing, and also while the
switch is off (the kill switch) and the docs still name these addresses.

Corrections against the first draft: the random 0-120 s first wait does NOT apply to Missed reveals and
pictures (they are asked only when needed); a 404 on a 24 h history address stops it until Hermes restarts
(gone_on_404), not for 15 minutes; Rewind now also holds the server's 24 h history; Featured Callers calls have no
links (plain text; a call opens the coin on the member board), only banner links open in the browser.

## README.md, "What it does on the network", under piquesignal.xyz

  - also with no key, the free board's own parts (asked only while a free board is open): `GET /api/free-board/missed`
    (the Missed strip: gains only, never a coin name or address) and `GET /api/free-board/free-pick` (the Free Pick),
    each at most once every 30 seconds; `GET /api/free-board/banners` (the banners marked "Ad"), at most once every
    5 minutes; `GET /api/free-board/img/<key>` (only the pictures those Missed and banner answers name, at most 2
    every 10 seconds; a coin logo is kept 10 minutes, a banner picture 24 hours); and `GET /api/free-board/history`
    (the free board's last 24 h, for Rewind; see below).
  - with a member key, also: `GET /api/pull/featured-callers` (Featured Callers, while the member board is open: at
    most once every 15 minutes, hourly until your key's daily limit is known), `GET /api/pull/history` (the member
    board's last 24 h, for Rewind) and `GET /api/pull/missed-reveal/<id>` (the coin behind a Missed tile: only when you
    click the tile, at most one every 10 seconds, each answer kept 30 minutes, at most 50 a day and at most 10 % of
    your key's daily limit). All of them together are paced to use at most 60 % of your key's daily limit (the
    reveals' own daily cap is counted inside it). The key never goes to the no-key addresses.
  - The 24 h history (both views, only while Rewind is on in Settings): a history address is asked only when the
    newest Rewind snapshot of that board is more than 15 minutes old (or there is none), at most once every 20 minutes
    (3 an hour; the server allows 4), one request at a time; an answer is capped at 3.2 MB. The member history is
    asked only while your key works and is kept only for that same key.
  - The Missed strip, Free Pick, banners, Featured Callers and both history addresses wait a random 0 to 120 seconds
    before their first request after Hermes starts (Missed reveals and pictures have no such wait: they are asked only
    when needed). On these addresses a refused request (any 4xx but 429) stops that part for about 15 minutes (plus a
    little random extra) and hides it; a 404 on a history address stops it until Hermes restarts. A 429 or 503 keeps the last good answer (history: the
    local Rewind), with no error message and no faster retry. They never carry a query string. Answers are capped:
    history 3.2 MB, a coin logo 64 KB, a banner picture 2 MB, everything else 2 MB; a picture must be PNG, JPEG or WebP.

## README.md, "Links you click"

Add: the link of a banner (marked "Ad", https only). The plugin sends no banner view or click counts. Featured Callers
calls are shown as plain text (no links); clicking a call opens that coin on the member board inside Hermes.

## README.md, "What it stores"

Rewind: the files also hold, after a gap, the board's last 24 h as the server sends it (merged into the same file;
free: only coins that are on the free board now; member: only for the same key), not only the rows the board already
showed you. In memory only: the Missed and banner pictures and the Missed reveal answers.

## plugin.yaml, the Disclosure sentence

After "Early Edge when a key is set": "; also the Missed strip, Free Pick, banners, the Missed and banner pictures (/api/free-board/img/)
and the free board's 24 h history with no key, and Featured Callers, the member board's 24 h history and a Missed reveal on your
click with a key (fixed addresses, no query string, the key never on the no-key ones; each new part waits a random
0-120 s before its first request after Hermes starts, Missed reveals and pictures excepted; a refused request stops
that part for about 15 minutes (plus a little random extra), a 404 on a 24 h history address stops it until Hermes
restarts; history answers capped at 3.2 MB;
no banner view or click counting)". Links: "banner links too; Featured Callers calls open the coin on the member
board". Stores: "the Rewind history (up to a day; it also holds the server's 24 h history, the member file only for
the same key)".
