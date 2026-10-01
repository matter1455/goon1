# Changes — Goofy UI + Balance Pass

## GUI
- Replaced the polished dark/glass dashboard look with a deliberately homemade, goofy card-night style.
- Bright paper colors, thick black borders, offset shadows, crooked cards, sticker-like chips, and Comic Sans/Trebuchet-style system fonts.
- Rewrote a lot of lobby/game text to sound like friends playing a fanmade game rather than a SaaS product.
- Renamed visible actions such as Punch → BONK, Battle Log → YAP LOG, Card Library → BIG CARD PILE, etc.
- Kept all existing IDs and multiplayer controls so the redesign does not change the game protocol.

## Balance system
- Added a generator-level rarity sanity audit. Generated cards are evaluated against broad power bands instead of only checking raw damage.
- Utility such as draw, discard, skip-turn, extra-play, multi-target effects, protection, and card recovery now counts toward the power budget.
- 417 generated cards were automatically adjusted in this pass because they fell outside the intended low-side balance floor before the audit.
- The audit preserves the clean-number rule: flat damage/healing/armor/reduction/bonuses remain multiples of 10.

## Hand-tuned cards
- Para-RAID: now +30 to one next attack.
- Murasame: next damage mark increased to +30.
- Equivalent Exchange: discard a 3★, draw 3, gain one extra 3★ play this turn.
- Arise: returns up to 2 non-5★ cards instead of 3.
- Pot of Greed: moved 3★ → 4★. Monster Reborn moved 4★ → 3★ to preserve the Yu-Gi-Oh! pool counts.
- You're Next: changed from multiplicative team scaling to +30 on each teammate's next attack.
- The Gray Monster: reduced from 1.5×/2× to 1.25×/1.5×.
- Bond Forger: now also draws 2 cards.
- World Item: now also grants 20 armor.
- The Place Above the Grey Fog: draw 5 → draw 3; extra card must be non-5★.
- The Father: return 3 → return 2; extra card must be non-5★.
- Return by Death: revive at 80 HP instead of 50.
- Infinity: blocks the next 2 attacks instead of 3.
- The World: still skips both opponents, but now costs the user 40 HP.
- Fluorite Eye's Song: draw 1, next attack ×1.5, plus one extra non-5★ play.
- Piss Dragon: team single-hit cap changed from 30 to 50.
- Boogie Woogie remains 5★ from the previous pass.
