# Balance Audit — Goofy UI Build

## Core philosophy
The pure-stat baseline is a budget, not a strict formula. A card that spends power on draw, denial, protection, card recovery, extra actions, teamwide effects, delayed damage, or flexible targeting gets less raw damage/healing/armor. Risky or conditional effects can exceed the baseline.

Flat combat numbers still use clean 10-point increments. Turn counts, card counts, star counts, and multipliers are allowed to use normal values such as 2 turns or 1.5×.

## Generated-card guardrails
The generator assigns a rough power value to damage, healing, armor, draw/discard, turn skips, extra card plays, multi-target effects, protection, and other utility. It uses broad sanity bands:

- 3★: roughly 20–55 weighted power
- 4★: roughly 45–95 weighted power
- 5★: roughly 80–145 weighted power

These are not player-facing scores and do not decide the game. They only catch obvious generator mistakes. Cards may sit near the edge when they have risk, setup, mode dependence, or delayed effects.

This pass flagged and adjusted 417 generated cards: 260 three-stars, 129 four-stars, and 28 five-stars.

## Rule-breaking effects
HP swaps, full skipped turns, extra plays, resurrection, long-duration immunity, and large card-advantage effects are valued separately from pure damage. This is why Boogie Woogie remains 5★ even though it has no printed damage.

## Important manual rebalances
See `CHANGES_THIS_VERSION.md` for the exact list. The largest changes were Pot of Greed, Equivalent Exchange, Arise, Infinity, The World, The Place Above the Grey Fog, The Father, Return by Death, The Gray Monster, and several team-scaling cards.
