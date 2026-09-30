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
  "deckSize": 48,
  "openingTeamSkipsFirstDraw": true
}
```

Restart the server after changing this file.

## How the card files work

`data/canon_references.py` contains the 16 canon references assigned to every show. The order is:

```text
first 10  -> 3★
next 5    -> 4★
last 1    -> 5★
```

`data/generate_cards.py` combines those references with the preserved original cards in `data/legacy_cards.json`, assigns balanced automated abilities, validates the rarity counts, and writes `data/cards.json`.

Run:

```bash
python data/generate_cards.py
```

**Important:** this overwrites `data/cards.json`.

## Balance philosophy

The pure-stat targets are guides:

```text
3★: about 30 damage / 40 healing / 30 armor
4★: about 55–60 damage / 70 healing / 55–60 armor
5★: about 100 damage / 100 healing / 80 armor
```

Do not force a utility card to also receive full baseline damage. Draw, discard, turn denial, extra card plays, damage multipliers, delayed attacks, information, immunity, recursion, and similar effects consume part of the card's power budget. Drawbacks and setup can justify going above the pure-stat line.

## Generated-card roles

`reference_profile()` in `data/generate_cards.py` decides whether a canon reference should behave more like:

- `assault`
- `team`
- `control`
- `social`
- `tempo`
- `sport`
- `risk`
- `mystic`
- `tactical`

Exact overrides and keyword rules prevent obvious mismatches such as an iconic attack being turned into a pure healing card. Add an entry to `ROLE_OVERRIDES` if you want to force a particular reference into another play style.

## Curated 5★ cards

`FIVE_STAR_SPECIALS` in `data/generate_cards.py` contains hand-designed marquee effects for shows whose 5★ slot was not already occupied by one of the original cards.

These deliberately use special mechanics and do **not** need to equal exactly 100 damage / 100 healing / 80 armor.

## Structured effects supported by the server

Generated cards can combine these operations in sequences, bundles, and coin flips:

- damage / delayed damage
- healing
- armor
- drawing
- random discard
- attack bonuses and multipliers
- incoming-damage multipliers/reductions
- marks that increase the next damage taken
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

The server applies these effects rather than merely printing their text.

## Directly editing one card

The final live catalog is `data/cards.json`. A generated card contains both text and automation data:

```json
{
  "name": "Example",
  "show": "Example Show",
  "stars": 3,
  "effect": "Deal 20 damage to one other player, then draw 1 card.",
  "action": {
    "type": "sequence",
    "steps": [
      { "op": "damage", "target": "chosen_other", "amount": 20 },
      { "op": "draw", "target": "self", "count": 1 }
    ]
  }
}
```

If you edit `cards.json` directly, do not rerun `generate_cards.py` unless you also copy the change into the generator or original-card source file.

## Website files

- `public/index.html` — layout/text.
- `public/style.css` — appearance.
- `public/client.js` — deck builder, show tabs, target selector, and controls.
- `server.js` — server-enforced game logic.
