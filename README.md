# Anime Clash TCG — 1v1 / 2v2 Expanded Deck Builder

A realtime browser prototype for a fanmade anime TCG. This build supports **1v1 and 2v2**, custom 48-card deck building, room codes, 300 HP, 20-damage punches, friendly fire in 2v2, and an expanded card pool for every show.

## Rules currently enforced

- 300 HP per player.
- Punch = 20 damage.
- Normally choose **one card OR one punch** on your turn.
- Draw 1 card at the beginning of each turn.
- The player taking the **very first turn of the match does not draw**. After that, draws happen normally.
- Opening hand = 5 cards.
- Deck = 48 cards.
- Unlimited hand size.
- A deck uses exactly 3 shows.
- From each selected show, choose **10× 3★, 5× 4★, and 1× 5★**.
- Each show now has a larger pool: **15× 3★, 7× 4★, and 2× 5★**.
- A coin flip chooses which side goes first.
- 1v1 rooms require 2 players; 2v2 rooms require 4 players.
- Friendly fire is enabled for punches and manually targeted single-target damage in 2v2.
- A side wins when every opposing player is knocked out.

## Card catalog

`data/cards.json` contains **1,392 cards across 58 shows**.

Every show has 24 available cards, so choosing a show no longer forces the same 16 cards every time. The deck builder automatically starts you with a legal 10/5/1 package for each selected show, and you can click cards to swap among the extra options before locking the deck.

The original cards remain in the live catalog. Added cards use canon references already assigned to their listed series, while the card subtitles/effects are fanmade. Generated abilities remain executable by the server rather than being text-only.

The rarity baselines are treated as a **power budget**, not a strict formula. Draw, denial, delayed damage, extra plays, setup, drawbacks, conditions, and team utility can move a card above or below the pure-stat baseline.

## Files for card design

- `data/canon_references.py` — canon references used by each show.
- `data/generate_cards.py` — balance/effect generator, alternate pool options, and curated 5★ effects.
- `data/legacy_cards.json` — preserved source list for the original cards.
- `data/cards.json` — final live catalog used by the website.
- `data/validate_cards.py` — validates pool sizes, names, references, and generated-effect uniqueness.
- `CARD_CATALOG.md` — human-readable list of all cards.

## Run locally

Install Node.js 18+ and run:

```bash
npm install
npm start
```

Then open:

```text
http://localhost:3000
```

## Deploy on Render

```text
Build command: npm install
Start command: npm start
```

Everyone opens the same public Render URL. One player creates either a 1v1 or 2v2 room and shares the five-character room code.

If this folder replaces the files in an existing GitHub repository already connected to Render, committing/pushing the replacement files should trigger a new deploy automatically.

## Main editable files

- `game-settings.json` — HP, punch damage, opening hand, deck composition, and card-pool size.
- `data/cards.json` — final card catalog.
- `data/canon_references.py` — show reference pool.
- `data/generate_cards.py` — generated effects and balance logic.
- `server.js` — multiplayer modes, turns, deck validation, and automated effects.
- `public/index.html` — layout and rules text.
- `public/client.js` — room mode picker, targets, and custom deck builder.
- `public/style.css` — appearance.
