## Reaction cards
Reaction cards are optional. When a valid trigger occurs, the eligible player gets a reaction window and must choose to use a reaction or pass. Reactions are never auto-played. A timeout only counts as a pass.

# Fanmade Anime TCG

Realtime browser TCG with room codes, 1v1 and 2v2, custom 48-card decks, friendly fire, meme cards, and one shared Environment slot.

## Core deck rules

Pick 3 shows. From each show select exactly 10×3★, 5×4★, and 1×5★ for 16 cards per show / 48 cards total. Every selected show must contribute at least 3 Environment cards, so every deck has at least 9 Environments.

Each show now has a much larger **33-card pool**: 20×3★, 10×4★, and 3×5★. Six of the 3★ cards are Environments. You still only put 16 cards from that show into the actual deck, so the extra cards are choices rather than extra deck size.

## Environment system

There is only **one Environment on the field for the entire match**. The team that played it gets its effect. If either team plays another Environment, the new one immediately replaces the old one. Environments do not expire on their own.

Environment bonuses stay small: +10 attack, -10 incoming attack damage, +10 punch damage, +10 healing at the start of an allied turn, or +10 armor at the start of an allied turn.

## UI

The site keeps the simple beginner-project layout, but uses a black/dark color scheme. Card effect text is larger in the hand, deck builder, library, and card popup.

## Running locally

```bash
npm install
npm start
```

Open `http://localhost:3000`.

## Important files

- `server.js` — multiplayer and rules
- `public/` — website UI
- `data/cards.json` — generated card database
- `data/generate_cards.py` — card generator / naming logic
- `data/validate_cards.py` — validation checks
- `game-settings.json` — HP, punch damage, deck counts, Environment minimum
- `CARD_CATALOG.md` — all cards
- `BALANCE_AUDIT.md` — balance notes

## Turn / information UI

- Use the target dropdown or click a living player to select a target.
- The latest played card remains visible to everyone and can be clicked to inspect its full text.
- Discard piles are public and inspectable.
- If a player has used all legal actions, the server automatically ends their turn.
- After a game ends, all players can click **Play Again** to start a rematch with the same decks.

## Discard recovery and reactions

Cards that return cards from the discard pile now let the player choose the exact eligible cards before the recovery card is played. The recovery card itself cannot be selected.

Snap, Pepper Dance, and Queen are true Reaction cards. They are used from hand during an out-of-turn reaction window instead of as normal main-turn cards. Reaction windows pause the current action for up to 10 seconds.
