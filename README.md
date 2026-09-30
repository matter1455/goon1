# Anime Clash TCG — 2v2 Canon-Card Edition

A realtime browser prototype for a fanmade 2v2 TCG. This build uses the new 300-HP / three-show deck rules and replaces the old generic filler cards with show-specific canon references and unique automated abilities.

## Rules currently enforced

- 300 HP per player.
- Punch = 20 damage.
- Normally choose **one card OR one punch** on your turn.
- Draw 1 card at the beginning of your turn.
- Opening hand = 5 cards.
- Deck = 48 cards.
- Unlimited hand size.
- A deck is exactly 3 shows.
- Every show package is exactly 16 cards: **10× 3★, 5× 4★, 1× 5★**.
- A coin flip chooses the starting team.
- Both players on the team that wins the opening coin flip skip the automatic draw on their first personal turn.
- Friendly fire is enabled for punches and manually targeted single-target damage.
- A team wins when both opposing players are knocked out.

## Card catalog

`data/cards.json` contains **928 cards across 58 shows**:

- the original 90 fanmade cards are preserved and normalized to the new rules where a direct stat adjustment was needed;
- **838 new cards** use characters, abilities, objects, locations, groups, or story concepts tied to their listed series;
- the old generic generated labels such as `Crossfire`, `Second Wind`, and `Guard Stance` have been removed;
- every generated card has unique printed effect text **and a unique structured action sequence**;
- recognizable offensive/defensive/control/support references are assigned suitable mechanical roles instead of blindly inheriting one generic show template;
- generated 5★ cards use hand-designed show-specific marquee effects rather than generic rarity filler.

The baselines are treated as a **power budget**, not a strict formula. A card with draw, denial, delayed damage, extra plays, setup, a drawback, or a conditional effect can sit above or below the raw damage/heal/armor baseline when the total effect justifies it.

## Files for card design

- `data/canon_references.py` — the canon references used to fill each show package.
- `data/generate_cards.py` — the balance/effect generator and curated 5★ effects.
- `data/legacy_cards.json` — preserved source list for the original cards.
- `data/cards.json` — the final live catalog consumed by the game.
- `CARD_CATALOG.md` — a human-readable list of every show, card, rarity, and effect.

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

For development with automatic restart:

```bash
npm run dev
```

## Online multiplayer

Deploy the folder to a Node/WebSocket-capable host such as Render or Railway.

```text
Build command: npm install
Start command: npm start
```

All four players open the same public URL. One creates a room and sends the five-character room code to the other three.

## Main editable files

- `game-settings.json` — HP, punch damage, opening hand, deck size, and show composition.
- `data/cards.json` — final card catalog.
- `data/canon_references.py` — show/card reference pool.
- `data/generate_cards.py` — generated effects and balance logic.
- `server.js` — multiplayer rules and automated effects.
- `public/index.html` — layout.
- `public/client.js` — browser UI, targeting, deck builder, and show tabs.
- `public/style.css` — appearance.
