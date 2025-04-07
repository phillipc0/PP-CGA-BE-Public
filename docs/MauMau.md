# Mau-Mau Documentation

This document provides an overview of the implementation and functionality of the `game_decision` function, which
handles player interactions in an asynchronous Mau-Mau card game server. Below, you'll find explanations for the various
actions, their purpose, and how the function manages the game state.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Functions and Utilities](#key-functions-and-utilities)
3. [Actions](#actions)
    - [Join](#join)
    - [Ready](#ready)
    - [Place Card on Stack](#place-card-on-stack)
    - [Draw Card](#draw-card)
    - [Draw Penalty](#draw-penalty)
    - [Skip](#skip)
4. [Game State Management](#game-state-management)
5. [Error Handling](#error-handling)

---

## Overview

The `game_decision` function processes incoming player actions, modifies the game state accordingly, and communicates
updates to all connected players. It uses websockets for real-time communication and ensures the game logic is adhered
to at all times.

---

## Key Functions and Utilities

The function relies on the following helper methods and external utilities:

- **`generate_card_deck`**: Creates a shuffled deck of cards.
- **`send_to_all`**: Broadcasts messages to all connected players.
- **`can_place_card_on_stack`**: Validates if a card can be placed on the discard pile.
- **`flip_pile_if_empty`**: Refills the draw pile if it becomes empty by shuffling the discard pile.
- **`turn_first_card`**: Moves the first card from the draw pile to the discard pile to start the game.

---

## Actions

### Join

**Action**: `join`

- **Purpose**: Adds a player to the game if the game hasn't started and there is room for additional players.
- **Conditions**:
    - Game must not have started.
    - Player must not already be in the game.
    - Maximum of 4 players.
- **Updates**:
    - Adds player to the `game.players` list.
    - Notifies all players about the new participant.

### Ready

**Action**: `ready`

- **Purpose**: Marks a player as ready. Starts the game if all players are ready and at least 2 players are present.
- **Conditions**:
    - Game must not have started.
    - Updates the `ready` status of the player.
- **On Game Start**:
    - Initializes the draw and discard piles.
    - Sets starting values (e.g., `7_count`, `j_choice`).
    - Distributes cards to players.
    - Notifies the first player of their turn.

### Place Card on Stack

**Action**: `place_card_on_stack`

- **Purpose**: Allows a player to place a card on the discard pile if it is valid.
- **Conditions**:
    - Game must be started.
    - It must be the player's turn.
    - The card must be in the player's hand.
    - The card must match the top card of the discard pile (by value or suit) or comply with a `j_choice`.
- **Special Cards**:
    - **7**: Adds a penalty to the next player.
    - **J**: Allows the player to change the active suit.
    - **8**: Skips the next player's turn.
- **Notifications**:
    - Updates all players on the card placed and the new game state.
    - Handles "Mau" declaration for players with one card.

### Draw Card

**Action**: `draw_card`

- **Purpose**: Allows a player to draw a card from the draw pile.
- **Conditions**:
    - Game must be started.
- **Updates**:
    - Adds a card to the player's hand.
    - Refills the draw pile if empty.
    - Updates all players on the new card counts.

### Draw Penalty

**Action**: `draw_penalty`

- **Purpose**: Forces a player to draw multiple cards as a penalty.
- **Conditions**:
    - Game must be started.
    - Triggered by a sequence of 7 cards on the discard pile.
- **Updates**:
    - Adds the penalty cards to the player's hand.
    - Resets the `7_count`.
    - Updates all players on the new card counts.

### Skip

**Action**: `skip`

- **Purpose**: Skips the current player's turn.
- **Conditions**:
    - Game must be started.
    - Valid when no other actions are possible.
- **Updates**:
    - Advances the turn to the next player.
    - Notifies all players of the new turn.

---

## Game State Management

The function manages the game state through the `game` object, which contains:

- **`state`**: Tracks the current game phase, draw/discard piles, active player, and special conditions (e.g.,
  `j_choice`, `7_count`).
- **`players`**: Stores player information, including readiness, hand, and status.

Key state updates include:

- Player readiness and joining.
- Card movements between hands and piles.
- Handling game-ending conditions.

---

## Error Handling

The function ensures robust error handling for invalid actions or states by sending descriptive error messages to
players. Common errors include:

- `no_action_provided`: Triggered when the `action` field is missing.
- `game_already_started`: Prevents invalid actions after the game begins.
- `game_not_started`: Ensures actions are taken only in the correct phase.
- `not_your_turn`: Blocks actions from players who are not the active turn.
- `card_not_in_hand`: Prevents placing cards not owned by the player.
- `card_not_allowed`: Ensures card placement adheres to the rules.
- `j_choice_not_possible`: Handles invalid suit selection for "J" cards.

---

## Future Improvements

- Implement timers for automatic turn skipping if a player takes too long.
- Enhance the penalty logic for invalid "Mau" declarations.
- Add support for spectator mode or rejoining disconnected players.

---

This documentation serves as a reference for developers working on or extending the Mau-Mau game server functionality.

