# Lügen Game Actions

## Lobby Actions

**Join the Game:**

```json
{
  "action": "join"
}
```

- The player joins the game and receives a player ID.

**Request Game Status:**

```json
{
  "action": "request_lobby_data"
}
```

- Displays all players and their readiness status.

**Leave the Lobby:**

```json
{
  "action": "leave_lobby"
}
```

- The player leaves the lobby.

**Start the Game (automatically when all players are ready):**

```json
{
  "action": "ready",
  "ready": true
}
```

---

## Game Actions

### Place Cards

**Action:**

```json
{
  "action": "place_cards",
  "cards": [
    {
      "value": "K",
      "suit": "Spades"
    },
    {
      "value": "K",
      "suit": "Hearts"
    }
  ],
  "claimed_value": "K"
}
```

- The player places two cards and claims they are two Kings.

### Challenge the Declaration

**Action:**

```json
{
  "action": "challenge"
}
```

- The next player challenges the truthfulness of the claim.

### Reveal the Challenge Result

**Game Response:**  
If the claim is true (not a lie), the challenge failed:

```json
{
  "action": "challenge",
  "success": false,
  "challenger": "Player2",
  "opponent": "player1",
  "cards": [
    {
      "value": "K",
      "suit": "Spades"
    },
    {
      "value": "K",
      "suit": "Hearts"
    }
  ]
}
```

If the claim is false (the player lied), the challenge succeeded:

```json
{
  "action": "challenge",
  "success": true,
  "challenger": "Player2",
  "opponent": "player1",
  "cards": [
    {
      "value": "A",
      "suit": "Spades"
    },
    {
      "value": "K",
      "suit": "Hearts"
    }
  ]
}
```

## Game End

**A Player Wins:**

```json
{
  "action": "win",
  "player": "9f269358-bab5-4435-8439-567f884c4ec6"
}
```

- If a player has placed all their cards.

**Game Ends with Only Two Players Left:**

```json
{
  "action": "end",
  "reason": "only_two_players_left",
  "winner": "9f269358-bab5-4435-8439-567f884c4ec6"
}
```

- The game ends when only two players have cards left.
- alternative reason: "Pair of Aces" and not "winner" but "player" and the id of the user who got the aces

**Alternative Rule: Treating Aces as Normal Cards**  
If an alternative version is played where Aces are treated as regular cards, this is defined in the game settings at the
beginning.

```json
{
  "$or": [
    {
      "game_mode": "classic"
    },
    {
      "game_mode": "alternative"
    }
  ]
}
```
