# Changes in this version

- Added a public **Last Played Card** panel. Everyone can inspect the card text after it is played.
- Added a short resolution summary under the last played card using the actual battle events produced by the server.
- Made discard piles clearly visible and public. Click a player's discard count or the Discard Piles buttons to inspect every discarded card.
- The target dropdown now includes every living player and stays synchronized with board clicks.
- Clicking any living player selects them as the current target and gives them a visible TARGET outline.
- Punching still cannot target yourself unless a card specifically forces a self-punch.
- Added server-side automatic turn ending when the current player has no legal actions remaining.
- Auto-end respects extra-card-play cards, Golden Ball pairing, and extra-punch effects instead of ending too early.
- Fixed the base action rule so a normal punch cannot be followed by a normal card play on the same turn.
- Added **Play Again**. After a match, every player can ready for a rematch; once everyone clicks it, the same decks are reshuffled and a new coin flip begins in the same room.
