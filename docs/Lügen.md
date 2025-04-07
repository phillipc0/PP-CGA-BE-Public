# Lügen Game Documentation

This document describes the game mechanics and the `game_decision` function, which processes player actions.

---

## Table of Contents
1. [Overview](#overview)
2. [Key Functions and Utilities](#key-functions-and-utilities)
3. [Actions](#actions)
    - [Join](#join)
    - [Ready](#ready)
    - [Place Cards and Declare Value](#place-cards-and-declare-value)
    - [Challenge the Declaration](#challenge-the-declaration)
    - [Pick Up Cards](#pick-up-cards)
4. [Game State Management](#game-state-management)
5. [Error Handling](#error-handling)
6. [Alternative Game Modes](#alternative-game-modes)

---

## Overview
The `game_decision` function processes player actions, updates the game state, and communicates changes in real time.

---

## Key Functions and Utilities
The game logic is based on the following methods:

- **`generate_card_deck`**: Creates a shuffled deck of cards.
- **`send_to_all`**: Sends messages to all players.
- **`validate_claim`**: Checks if the declared card value matches the placed cards. - NO
- **`transfer_cards`**: Assigns cards to respective players. - NO

---

## Actions

### Join
**Action:** `join`
- **Purpose:** Adds a player to the game.
- **Requirements:**  
  - The game must not have started yet.
  - The player must not already be in the game.
- **Updates:**  
  - Adds the player to the player list.
  - Notifies all players about the new participant.

### Ready
**Action:** `ready`
- **Purpose:** Marks a player as ready. The game starts when all players (minimum 3) are ready.
- **Requirements:**  
  - The game must not have started yet.
- **Game Start:**  
  - Cards are shuffled and distributed evenly.
  - The first player is chosen randomly.

### Place Cards and Declare Value
**Action:** `place_cards`
- **Purpose:** A player places one or more cards face down and declares an alleged value.
- **Requirements:**  
  - It must be the player's turn.
  - The player can declare any value, regardless of the actual cards.
- **Data Structure:**  
  ```json
  {
    "action": "place_cards",
    "cards": [
      {"value": "K", "suit": "Spades"},
      {"value": "K", "suit": "Hearts"}
    ],
    "claimed_value": {"card": {"value": "K"}, "count": 2}
  }
  ```

### Challenge the Declaration
**Action:** `challenge`
- **Purpose:** The next player can challenge the declared claim.
- **Requirements:**  
  - If the bluff is detected, the previous player takes back the cards.
  - If the declaration was correct, the challenger picks up the cards.

### Pick Up Cards - NO
**Action:** `take_cards`
- **Purpose:** If a player is caught bluffing or makes a false challenge, they must take the cards.
- **Data Structure:**  
  ```json
  {
    "action": "penalty",
    "penalty": {"player": "Player1", "cards_received": [{"value": "K", "suit": "Spades"},{"value": "K", "suit": "Hearts"}]}
  }
  ```

---

## Game State Management
The game manages its state using a `game` object containing:

- **`state`**: Stores the current game status, placed cards, and player order.
- **`players`**: Stores player information, card counts, and the current turn.

---

## Alternative Game Modes
There are two game modes:

1. **Classic Mode (`"classic"`)**:  
   - Four aces immediately end the game. The player with four aces loses.
   - The game ends when only two players remain.
   - A player wins when they have no more cards.

2. **Alternative Mode (`"alternative"`)**:  
   - Aces are treated like normal cards.
   - The game proceeds as usual, but aces have no special role.

At the start of the game, one of the two modes is selected:
```json
{"$or": [{"game_mode": "classic"}, {"game_mode": "alternative"}]}
```
