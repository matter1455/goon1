# Card Design Notes

This build follows three design rules for new cards:

1. **The card reference belongs to its listed show.** New slots use named characters, techniques, objects, locations, groups, or story concepts rather than fabricated generic move names.
2. **Abilities are mechanically unique.** The generator validates that every newly generated card has unique printed effect text and a unique structured action sequence.
3. **Rarity baselines are power budgets, not hard caps.** Utility and denial reduce raw stats; delayed/conditional effects or drawbacks can increase them.

## Examples

### 3★
A straightforward attack can sit around 28–30 damage. A 20-damage attack may also draw, mark, add armor, or set up the next attack. A delayed attack can exceed 30 because the opponent gets time before it resolves.

### 4★
Straight damage is normally around 55–60. Strong utility such as skipping a turn or stealing a card gets much less or no direct damage. Risk cards can reach 75–80 when they also hurt the user.

### 5★
The 100-damage / 100-heal / 80-armor line is a reference point. Marquee cards may instead manipulate turns, recur several cards, grant extra plays, affect both teammates/opponents, or trade self-damage for a larger hit.

## Automated validation

Running `python data/generate_cards.py` checks:

- 58 show packages exist;
- each show contains exactly 10×3★, 5×4★, 1×5★;
- total catalog size is 928;
- all card names are unique;
- generated filler labels from the previous version are absent;
- generated effect text is unique;
- generated structured actions are unique.
