# Editing Guide

## Main rules

Edit `game-settings.json`:

```json
{
  "startingHp": 300,
  "basePunchDamage": 20,
  "startingHandSize": 5,
  "showsPerDeck": 3,
  "cardsPerShow": { "3": 10, "4": 5, "5": 1 },
  "poolCardsPerShow": { "3": 15, "4": 7, "5": 2 },
  "deckSize": 48,
  "openingTeamSkipsFirstDraw": true
}
```

`cardsPerShow` is what goes into a legal deck from each selected show. `poolCardsPerShow` describes how many cards are available to choose from in that show.

The current first-player rule is: the coin-flip winner goes first, but the player taking **turn 1** does not draw. Everyone draws normally from turn 2 onward.

## 1v1 / 2v2

The room creator chooses the mode in the lobby. `server.js` stores the mode with the room:

- `1v1` → 2 seats (`A1`, `B1`)
- `2v2` → 4 seats (`A1`, `B1`, `A2`, `B2`)

Turn order in 2v2 is A1 → B1 → A2 → B2. Dead players are skipped.

## How the card files work

`data/canon_references.py` contains the core canon references assigned to each show. The generator first creates the original 16-card core package, then adds alternate cards tied back to those references so each show reaches:

```text
15 × 3★
 7 × 4★
 2 × 5★
--------
24 cards available per show
```

A player still chooses only:

```text
10 × 3★
 5 × 4★
 1 × 5★
--------
16 cards from that show
```

Three shows = 48 cards.

Run:

```bash
python data/generate_cards.py
python data/validate_cards.py
```

**Important:** `generate_cards.py` overwrites `data/cards.json`.

## Balance philosophy

The pure-stat targets are guides:

```text
3★: about 30 damage / 40 healing / 30 armor
4★: about 55–60 damage / 70 healing / 55–60 armor
5★: about 100 damage / 100 healing / 80 armor
```

Utility consumes part of the budget. Draw, discard, turn denial, extra card plays, damage multipliers, delayed attacks, immunity, recursion, and similar effects should reduce raw stats. Setup, self-damage, delayed resolution, or narrow conditions can justify exceeding the pure-stat baseline.

## Alternate pool cards

The extra 8 cards per show are generated from existing canon references. Their subtitle is fanmade, while `canonRef` records the actual show reference the card is based on.

Example:

```json
{
  "name": "Example Character — Breakthrough",
  "show": "Example Show",
  "stars": 3,
  "canonRef": "Example Character",
  "variant": true,
  "effect": "...",
  "action": { "type": "bundle", "main": {}, "after": [] }
}
```

## Structured effects supported by the server

Generated cards can combine:

- damage / delayed damage
- healing
- armor
- drawing
- random discard
- attack bonuses and multipliers
- incoming-damage multipliers/reductions
- marks
- healing prevention
- untargetability
- discard-pile recursion
- punch immunity
- extra punch
- extra card play with rarity restrictions
- skipped turns
- random card stealing
- temporary damage caps
- HP swapping
- revival support
- bonus next-turn draws

## Website files

- `public/index.html` — layout/text.
- `public/style.css` — appearance.
- `public/client.js` — mode picker, deck builder, card selection, targets, and controls.
- `server.js` — server-enforced rules.
