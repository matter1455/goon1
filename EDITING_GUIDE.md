# Editing Guide

## Change basic rules
Edit `game-settings.json` for starting HP, punch damage, starting hand size, shows per deck, rarity requirements, pool sizes, and the Environment minimum.

## Change the dark look
Edit `public/style.css`. The dark-theme overrides are at the bottom of the file. The layout is intentionally simple; the bottom section controls the black background, dark panels, and larger card text.

## Change cards
`data/cards.json` is the live generated catalog. For durable changes, edit `data/generate_cards.py` or `data/legacy_cards.json`, then regenerate:

```bash
python data/generate_cards.py
python data/validate_cards.py
```

Generated names are controlled mainly by `TITLE_PHRASES` and `_title_for_generated()` in `data/generate_cards.py`.

## Add or change an original card
Original cards begin in `data/legacy_cards.json`. Special rules that cannot be represented by structured action data are handled in `server.js` inside `resolveCard()`.

## After editing
Run:

```bash
node --check server.js
node --check public/client.js
python data/validate_cards.py
```

Then commit the changed files to the GitHub repository connected to Render.
