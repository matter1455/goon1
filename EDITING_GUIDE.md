# Editing Guide — Anime Card Bonk!!

## Change basic rules
Edit `game-settings.json` for starting HP, punch/BONK damage, starting hand size, shows per deck, deck rarity requirements, and pool sizes.

## Change the goofy look
Edit `public/style.css`. The bottom section is labeled `GOOFY MODE` and contains the main visual overrides. You can change the background, border thickness, button colors, card wobble, shadows, etc. without touching game rules.

Visible lobby/game wording lives mostly in `public/index.html` and dynamic labels/toasts live in `public/client.js`.

## Change cards
`data/cards.json` is the live generated catalog used by the server. For durable changes, edit `data/generate_cards.py` or `data/legacy_cards.json` and then regenerate:

```bash
cd data
python generate_cards.py
python validate_cards.py
```

The generator now includes the broad balance sanity audit, so future generated cards are checked for extremely weak/overloaded power packages.

## Add or change a legacy/original card
Original cards begin in `data/legacy_cards.json`. Special rules that cannot be represented by structured action data are handled in `server.js` inside `resolveCard()`.

## Structured card effects
Generated cards usually use `action` data. Common operations include damage, heal, armor, draw, discard, attack buffs, marks, delayed damage, return from discard, extra card plays, skip turn, punch immunity, damage caps, HP swaps, and more. These are resolved by `structuredStep()` in `server.js`.

## After editing
Run:

```bash
node --check server.js
node --check public/client.js
python data/validate_cards.py
```

Then commit the changed files to the GitHub repository connected to Render. Render should redeploy the existing site automatically.
