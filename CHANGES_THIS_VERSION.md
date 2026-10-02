# Manual reaction choices

- Snap, Pepper Dance, and Queen never auto-play.
- Eligible players explicitly choose **Use Reaction** or **Pass / Let It Happen**.
- Clicking the reaction card itself only inspects it; it does not consume it.
- The reaction window now lasts 20 seconds. If no choice is made, the game auto-passes only so the match cannot be stalled forever.
- A reaction card is discarded only after the player explicitly clicks its Use button.

# Changes in this version

- Discard recovery is now player-selected instead of automatic/random. Recovery cards show your eligible discard cards before you play them.
- A recovery card cannot return itself with its own effect.
- Added real out-of-turn reaction windows.
- Snap can be used when an opponent plays a card to negate that card's entire effect.
- Pepper Dance can be used when you are attacked; it halves that incoming damage and reflects the halved amount back.
- Queen can be used in 2v2 before a direct opponent attack to redirect it to the higher-HP teammate when that redirect is valid.
- Reaction cards are no longer playable as ordinary main-turn cards; they stay in hand until a valid reaction window appears.
- Reaction windows pause the active turn and auto-pass after 10 seconds if the responder does nothing.
- Queen resolves before Pepper Dance so Pepper is not wasted on a target that gets redirected.
- The existing public discard piles, played-card display, click/dropdown targeting, auto-end turns, rematch button, 1v1/2v2 modes, and Environment system are preserved.


## 2v2 lobby and turn flow
- 2v2 turn order is now teammate -> teammate -> enemy -> enemy instead of alternating teams every single turn.
- Added a **Switch Team** button in the 2v2 waiting room. It swaps with the corresponding opposing slot when occupied.
- Closing/reloading/navigating away now explicitly leaves the room so ghost players do not remain in matchmaking.

## Lobby and board clarity update
- Added an **Unready** button in the waiting room. Ready players can unready, edit their deck, and ready again before the match starts.
- Enlarged the central battle board and player panels.
- Enemy player panels now use a thick red border around the whole panel.
- Selected targets use a separate cyan dashed outline and **SELECTED TARGET** badge so targeting does not look like the enemy-team border.
