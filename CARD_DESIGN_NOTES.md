# Card Design Notes

This build follows four design rules for new cards:

1. **The source reference belongs to its listed show.** Added cards are tied to the canon references in `data/canon_references.py`.
2. **Card subtitles and mechanics are fanmade.** An alternate card can reuse a character/object/concept as its canon source while giving it a new fanmade TCG subtitle and effect.
3. **Abilities are mechanically unique.** Validation checks generated printed effects and structured action data for duplicates.
4. **Rarity baselines are power budgets, not hard caps.** Utility and denial reduce raw stats; delayed/conditional effects and drawbacks can increase them.

## Pool/deck structure

Every show offers:

- 15 three-star cards
- 7 four-star cards
- 2 five-star cards

A deck selects only 10/5/1 from that pool. This creates real deck-building choices while preserving the 16-cards-per-show / 48-card-deck rule.

## Examples of budget logic

### 3★
A straightforward attack can sit near 30 damage. A lower-damage attack may also draw, mark, add armor, or set up the next attack. A delayed or drawback-heavy effect can exceed 30.

### 4★
Straight damage is normally around 55–60. Strong utility such as skipping a turn or stealing a card gets much less direct damage. Risk cards can exceed the line when they also hurt the user or have setup.

### 5★
The 100-damage / 100-heal / 80-armor line is a reference point. Marquee cards can instead manipulate turns, recur cards, grant extra plays, affect teams, cap damage, or trade self-damage for a larger hit.

## Automated validation

Run:

```bash
python data/generate_cards.py
python data/validate_cards.py
```

Validation checks:

- 58 shows;
- 1,392 total cards;
- every show pool = 15×3★ / 7×4★ / 2×5★;
- unique card names;
- generated canon references belong to the correct show's reference list;
- generated effect text is unique;
- generated structured action data is unique.
