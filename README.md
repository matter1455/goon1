# Anime Card Bonk!! — Fanmade 1v1 / 2v2 TCG

A realtime browser TCG for 1v1 or 2v2 matches with room codes. This build uses the goofy homemade UI and the expanded balance audit.

## Current rules implemented
- 300 HP per player
- Base BONK/punch = 20 damage
- Normally choose one card OR one punch on your turn
- Draw 1 at the start of your turn
- The player who takes the very first turn does not draw on that first turn
- 5-card opening hand
- Unlimited hand size
- 48-card decks
- Pick exactly 3 shows
- From each selected show, deck uses 10×3★, 5×4★, 1×5★
- Each show pool currently offers 15×3★, 7×4★, 2×5★ so you have choices
- 1v1 and 2v2 modes
- Friendly fire for manually targeted single-target damage/BONKs

## Run locally
```bash
npm install
npm start
```
Open `http://localhost:3000`.

## Put it online
Upload the project contents to the GitHub repository connected to your Render Web Service. Render can use:

- Build command: `npm install`
- Start command: `npm start`

Committing this version over your existing GitHub project will keep the same Render URL once the redeploy finishes.

## Important files
- `public/index.html` — page structure/text
- `public/style.css` — goofy visual theme
- `public/client.js` — browser UI/game interactions
- `server.js` — multiplayer/game rules
- `game-settings.json` — basic game constants
- `data/cards.json` — current generated card database
- `data/generate_cards.py` — card generator + balance audit
- `data/legacy_cards.json` — original card source list
- `data/validate_cards.py` — catalog validation
- `BALANCE_AUDIT.md` — current balancing philosophy
- `CHANGES_THIS_VERSION.md` — specific changes in this build

## Card pool
58 shows × 24 available cards = 1,392 cards total. Every show remains 15×3★ / 7×4★ / 2×5★ in the pool, while a deck selects 10/5/1 from each of its three shows.
