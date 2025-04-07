import random
import time
from typing import Dict, Any, Tuple

from util.generic import flip_pile_if_empty, send_to_all
from util.maumau import (
    can_place_card_on_stack,
    generate_card_deck,
    get_next_player,
    turn_first_card
)

# ============================================================
# Konstanten und Schlüssel
# ============================================================
ACTION = "action"
ERROR = "error"
STARTED = "started"
CURRENT_PLAYER = "current_player"
JOIN_SEQUENCE = "join_sequence"

PLAYER = "player"
PLAYERS = "players"
READY = "ready"
MAU = "mau"
CARD = "card"
J_CHOICE = "j_choice"
DISCARD_PILE = "discard_pile"
DISCARD_PILE_COUNT = "discard_pile_count"
DRAW_PILE = "draw_pile"
DRAW_PILE_COUNT = "draw_pile_count"
COUNT_7 = "count_7"
WINNER = "winner"
LAST_ACTION = "last_action"
HAND = "hand"
HAND_COUNT = "hand_count"
VALUE = "value"
CARDS = "cards"

ACTION_JOIN = "join"
ACTION_READY = "ready"
ACTION_LEAVE_LOBBY = "leave_lobby"
ACTION_REQUEST_LOBBY_DATA = "request_lobby_data"
ACTION_LOBBY_DATA = "lobby_data"
ACTION_REQUEST_GAME_DATA = "request_game_data"
ACTION_GAME_DATA = "game_data"
ACTION_PLACE_CARD_ON_STACK = "place_card_on_stack"
ACTION_DRAW_CARD = "draw_card"
ACTION_DRAW_PENALTY = "draw_penalty"
ACTION_SKIP = "skip"
ACTION_LEAVE_GAME = "leave_game"
ACTION_START = "start"
ACTION_MAU = "mau"
ACTION_WIN = "win"
ACTION_END = "end"
ACTION_HAND = "hand"
ACTION_CARD_COUNT = "card_count"
ACTION_TURN = "turn"
ACTION_TIMEOUT_PENALTY = "timeout_penalty"

ERROR_NO_ACTION_PROVIDED = "No action provided"
ERROR_WRONG_DATA = "wrong_data"
ERROR_GAME_ALREADY_STARTED = "game_already_started"
ERROR_PLAYER_ALREADY_JOINED = "player_already_joined"
ERROR_GAME_FULL = "game_full"
ERROR_NO_READY_PROVIDED = "no_ready_provided"
ERROR_WRONG_READY_VALUE = "wrong_ready_value"
ERROR_GAME_NOT_STARTED = "game_not_started"
ERROR_NOT_IN_LOBBY = "player_not_in_lobby"
ERROR_NOT_YOUR_TURN = "not_your_turn"
ERROR_NO_CARD_PROVIDED = "no_card_provided"
ERROR_NO_MAU_PROVIDED = "no_mau_provided"
ERROR_NO_CHOICE_PROVIDED = "no_choice_provided"
ERROR_CARD_NOT_IN_HAND = "card_not_in_hand"
ERROR_CARD_NOT_ALLOWED = "card_not_allowed"
ERROR_HAS_TO_DRAW_PENALTY = "has_to_draw_penalty"
ERROR_J_CHOICE_NOT_POSSIBLE = "j_choice_not_possible"
ERROR_CANT_DRAW_AGAIN = "cant_draw_again"
ERROR_0_COUNT_7 = "0_count_7"
ERROR_CAN_NOT_SKIP = "can_not_skip"
ERROR_UNKNOWN_ACTION = "unknown_action"

CARD_VALUE_7 = "7"
CARD_VALUE_8 = "8"
CARD_VALUE_J = "J"
SUIT_HEARTS = "Hearts"
SUIT_DIAMONDS = "Diamonds"
SUIT_CLUBS = "Clubs"
SUIT_SPADES = "Spades"
TURN_START_TIME = "turn_start_time"

SETTING_MAX_PLAYERS = "max_players"
SETTING_DECK_SIZE = "deck_size"
SETTING_NUMBER_OF_START_CARDS = "number_of_start_cards"


# ============================================================
# Hilfsfunktionen
# ============================================================
async def send_error(websocket, error_msg: str) -> None:
    """Sende eine Fehlermeldung an einen bestimmten Websocket."""
    await websocket.send_json({ERROR: error_msg})


def all_players_ready(players: Dict[str, Dict[str, Any]]) -> bool:
    """Prüft, ob alle Spieler in players als ready markiert sind."""
    return all(player_data[READY] for player_data in players.values())


def remove_player(players: Dict[str, Dict[str, Any]], user_id: str) -> None:
    """Entferne den Spieler aus dem Dictionary, wenn vorhanden."""
    if user_id in players:
        del players[user_id]


def get_hand_counts(players: Dict[str, Dict[str, Any]]) -> Dict[str, int]:
    """Erstellt ein Mapping von PlayerID zu Anzahl Karten auf der Hand."""
    return {pid: len(data[HAND]) for pid, data in players.items()}


# ============================================================
# Action-Handler-Funktionen
# ============================================================
async def handle_join(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Behandelt das Joinen eines neuen Spielers."""
    # Validierung
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if user.id in players:
        await send_error(websocket, ERROR_PLAYER_ALREADY_JOINED)
        return state, players

    if state[STARTED]:
        await send_error(websocket, ERROR_GAME_ALREADY_STARTED)
        return state, players

    if len(players) == settings[SETTING_MAX_PLAYERS]:
        await send_error(websocket, ERROR_GAME_FULL)
        return state, players

    players[user.id] = {
        READY:         False,
        HAND:          [],
        JOIN_SEQUENCE: len(players) + 1
    }

    await send_to_all(websocket_connections, {
        ACTION:  ACTION_JOIN,
        PLAYER:  user.id,
        PLAYERS: list(players.keys())
    })
    return state, players


async def handle_ready(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Setzt den Status READY für einen Spieler und startet ggf. das Spiel."""
    # Validierung
    if user.id not in players:
        await send_error(websocket, ERROR_NOT_IN_LOBBY)
        return state, players

    if len(message) != 1:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if READY not in message:
        await send_error(websocket, ERROR_NO_READY_PROVIDED)
        return state, players

    if message[READY] not in [True, False]:
        await send_error(websocket, ERROR_WRONG_READY_VALUE)
        return state, players

    if state[STARTED]:
        await send_error(websocket, ERROR_GAME_ALREADY_STARTED)
        return state, players

    # Setze Ready-Status
    players[user.id][READY] = message[READY]

    # Informiere alle über den neuen Ready-Status
    await send_to_all(websocket_connections, {
        ACTION:  ACTION_READY,
        PLAYER:  user.id,
        READY:   message[READY],
        PLAYERS: {pid: players[pid][READY] for pid in players}
    })

    # Prüfe, ob alle bereit und ob genügend Spieler
    if all_players_ready(players) and len(players) > 1:
        # Spiel starten
        state[STARTED] = True
        state[DRAW_PILE] = generate_card_deck(size=settings[SETTING_DECK_SIZE])
        state[DRAW_PILE], state[DISCARD_PILE] = turn_first_card(state[DRAW_PILE], [])
        state[COUNT_7] = 0
        state[J_CHOICE] = ""
        state[WINNER] = []
        state[CURRENT_PLAYER] = random.choice(list(players.keys()))
        state[TURN_START_TIME] = time.time()

        # Sende Start-Info
        await send_to_all(websocket_connections, {
            ACTION:       ACTION_START,
            DISCARD_PILE: state[DISCARD_PILE][-1]
        })

        # Karten austeilen
        for pid in players:
            players[pid][HAND] = state[DRAW_PILE][:settings[SETTING_NUMBER_OF_START_CARDS]]
            players[pid][LAST_ACTION] = ACTION_READY
            state[DRAW_PILE] = state[DRAW_PILE][settings[SETTING_NUMBER_OF_START_CARDS]:]
            # Jeder bekommt seine Handkarten
            await websocket_connections[pid].send_json({
                ACTION: ACTION_HAND,
                HAND:   players[pid][HAND]
            })

        # Sende Karten-Zusammenfassung
        await send_to_all(websocket_connections, {
            ACTION:             ACTION_CARD_COUNT,
            DISCARD_PILE_COUNT: len(state[DISCARD_PILE]),
            DRAW_PILE_COUNT:    len(state[DRAW_PILE]),
            HAND_COUNT:         get_hand_counts(players)
        })

        # Nächster Zug
        await send_to_all(websocket_connections, {
            ACTION: ACTION_TURN,
            PLAYER: state[CURRENT_PLAYER]
        })

    return state, players


# noinspection PyUnusedLocal
async def handle_leave_lobby(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Ermöglicht das Verlassen der Lobby, falls das Spiel noch nicht gestartet ist."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if state[STARTED]:
        await send_error(websocket, ERROR_GAME_ALREADY_STARTED)
        return state, players

    remove_player(players, user.id)

    await send_to_all(websocket_connections, {
        ACTION:  ACTION_LEAVE_LOBBY,
        PLAYER:  user.id,
        PLAYERS: list(players.keys())
    })
    return state, players


# noinspection PyUnusedLocal
async def handle_request_lobby_data(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Liefert Lobby-Daten an den anfragenden Spieler."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    # Sende Ready-Status aller Spieler
    await websocket.send_json({
        ACTION:  ACTION_LOBBY_DATA,
        PLAYERS: {pid: player_data[READY] for pid, player_data in players.items()}
    })
    return state, players


# noinspection PyUnusedLocal
async def handle_request_game_data(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Gibt Spiel-Daten zurück (Anzahl der Handkarten, letzte abgelegte Karte etc.)."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if not state[STARTED]:
        await send_error(websocket, ERROR_GAME_NOT_STARTED)
        return state, players

    sorted_players = sorted(players.keys(), key=lambda pid: players[pid]['join_sequence'])
    await websocket.send_json({
        ACTION:         ACTION_GAME_DATA,
        PLAYERS:        {pid: len(players[pid][HAND]) for pid in sorted_players},
        DISCARD_PILE:   state[DISCARD_PILE][-1],
        DRAW_PILE:      len(state[DRAW_PILE]),
        CURRENT_PLAYER: state[CURRENT_PLAYER],
        HAND:           players[user.id][HAND]
    })
    return state, players


# noinspection PyUnusedLocal
async def handle_place_card_on_stack(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Ermöglicht es einem Spieler, eine Karte abzulegen."""
    # Validierung
    if len(message) not in [2, 3]:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if CARD not in message:
        await send_error(websocket, ERROR_NO_CARD_PROVIDED)
        return state, players

    if MAU not in message:
        await send_error(websocket, ERROR_NO_MAU_PROVIDED)
        return state, players

    card = message[CARD]

    # Wenn Karte Bube (J), muss J_CHOICE gesetzt sein
    if card[VALUE] == CARD_VALUE_J and J_CHOICE not in message:
        await send_error(websocket, ERROR_NO_CHOICE_PROVIDED)
        return state, players

    # Check, ob Karte tatsächlich in der Hand ist
    if card not in players[user.id][HAND]:
        await send_error(websocket, ERROR_CARD_NOT_IN_HAND)
        return state, players

    # Überprüfe, ob das Ablegen erlaubt ist
    if not can_place_card_on_stack(card, state[DISCARD_PILE][-1], state[J_CHOICE]):
        await send_error(websocket, ERROR_CARD_NOT_ALLOWED)
        return state, players

    # Karte wird auf den Ablagestapel gelegt
    state[DISCARD_PILE].append(card)
    players[user.id][HAND].remove(card)

    # MAU-Logik: Wenn Spieler 1 Karte auf der Hand hat, muss MAU gesagt werden
    if len(players[user.id][HAND]) == 1:
        if message[MAU]:
            await send_to_all(websocket_connections, {
                ACTION: ACTION_MAU,
                PLAYER: user.id
            })
        else:
            # Falls MAU nicht gesagt, eine Strafkarte ziehen
            if state[DRAW_PILE]:
                players[user.id][HAND].append(state[DRAW_PILE].pop())
            else:
                await send_error(websocket, "No cards left to draw")
                return state, players
            try:
                state = flip_pile_if_empty(state)
            except IndexError as e:
                await send_error(websocket, str(e))
            await websocket.send_json({
                ACTION: ACTION_HAND,
                HAND:   players[user.id][HAND],
                CARDS:  players[user.id][HAND][-1]
            })

    # Effekte je nach Kartenwert (7, J, 8)
    if card[VALUE] == CARD_VALUE_7:
        # 7er erhöht den COUNT_7 für Strafkarten
        state[COUNT_7] += 2
    else:
        if state[COUNT_7] != 0:
            # Kartenwert != 7 aber COUNT_7 != 0 -> erst Strafkarten ziehen
            await send_error(websocket, ERROR_HAS_TO_DRAW_PENALTY)
            return state, players

    if card[VALUE] == CARD_VALUE_J:
        # Bei Bube muss eine Wahl (Farbe) getroffen werden
        j_choice = message[J_CHOICE]
        if j_choice in [SUIT_HEARTS, SUIT_DIAMONDS, SUIT_CLUBS, SUIT_SPADES]:
            state[J_CHOICE] = j_choice
        else:
            await send_error(websocket, ERROR_J_CHOICE_NOT_POSSIBLE)
            return state, players

    # 8er -> nächster Spieler wird übersprungen
    if card[VALUE] == CARD_VALUE_8:
        state[CURRENT_PLAYER] = get_next_player(user.id, players, skip=1)
    else:
        state[CURRENT_PLAYER] = get_next_player(user.id, players)
    state[TURN_START_TIME] = time.time()  # Timer zurücksetzen

    # Reshuffle if draw_pile is empty and we now have enough cards to shuffle
    if not state[DRAW_PILE] and len(state[DISCARD_PILE]) >= 2:
        draw_card = state[DISCARD_PILE][0]
        state[DRAW_PILE] = [draw_card]
        state[DISCARD_PILE].remove(draw_card)

    # Broadcast
    message = {
        ACTION: ACTION_PLACE_CARD_ON_STACK,
        CARD:   card,
        PLAYER: user.id
    }
    if card[VALUE] == CARD_VALUE_J:
        message[J_CHOICE] = state[J_CHOICE]
    await send_to_all(websocket_connections, message)

    # Hat der Spieler nun gewonnen?
    if len(players[user.id][HAND]) == 0:
        players.pop(user.id)
        state[WINNER].append(user.id)
        await send_to_all(websocket_connections, {
            ACTION: ACTION_WIN,
            PLAYER: user.id
        })
        # Wenn nur noch 1 Spieler übrig ist -> Spielende
        if len(players) == 1:
            winner = state[WINNER][0] if state[WINNER] else None
            await send_to_all(websocket_connections, {
                ACTION: ACTION_END,
                WINNER: winner
            })

            state = {
                STARTED:        False,
                CURRENT_PLAYER: "",
                DISCARD_PILE:   [],
                DRAW_PILE:      [],
                COUNT_7:        0,
                J_CHOICE:       "",
                WINNER:         []
            }

            players = {}

            return state, players
    else:
        players[user.id][LAST_ACTION] = ACTION_PLACE_CARD_ON_STACK

    # Allen den neuen Karten-Count senden
    await send_to_all(websocket_connections, {
        ACTION:             ACTION_CARD_COUNT,
        DISCARD_PILE_COUNT: len(state[DISCARD_PILE]),
        DRAW_PILE_COUNT:    len(state[DRAW_PILE]),
        HAND_COUNT:         get_hand_counts(players)
    })

    # Nächster Zug
    await send_to_all(websocket_connections, {
        ACTION: ACTION_TURN,
        PLAYER: state[CURRENT_PLAYER]
    })

    return state, players


# noinspection DuplicatedCode,PyUnusedLocal
async def handle_draw_card(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Ermöglicht das Ziehen einer Karte vom Stapel."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if players[user.id].get(LAST_ACTION) == ACTION_DRAW_CARD:
        await send_error(websocket, ERROR_CANT_DRAW_AGAIN)
        return state, players

    if state[COUNT_7] != 0:
        await send_error(websocket, ERROR_HAS_TO_DRAW_PENALTY)
        return state, players

    # Ziehe Karte
    if state[DRAW_PILE]:
        players[user.id][HAND].append(state[DRAW_PILE].pop())
    else:
        await send_error(websocket, "No cards left to draw")
        return state, players
    try:
        state = flip_pile_if_empty(state)
    except IndexError as e:
        await send_error(websocket, str(e))

    # Sende Info zum Ziehen
    await websocket.send_json({
        ACTION: ACTION_DRAW_CARD,
        PLAYER: user.id
    })
    await websocket.send_json({
        ACTION: ACTION_HAND,
        HAND:   players[user.id][HAND],
        CARDS:  players[user.id][HAND][-1]
    })
    await send_to_all(websocket_connections, {
        ACTION:             ACTION_CARD_COUNT,
        DISCARD_PILE_COUNT: len(state[DISCARD_PILE]),
        DRAW_PILE_COUNT:    len(state[DRAW_PILE]),
        HAND_COUNT:         get_hand_counts(players)
    })

    players[user.id][LAST_ACTION] = ACTION_DRAW_CARD
    return state, players


# noinspection PyUnusedLocal,DuplicatedCode
async def handle_draw_penalty(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Ermöglicht das Ziehen der Strafkarten, wenn COUNT_7 > 0."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    if state[COUNT_7] == 0:
        await send_error(websocket, ERROR_0_COUNT_7)
        return state, players

    # Ziehe COUNT_7 Karten, if possible
    drawn_cards = 0
    for _ in range(state[COUNT_7]):
        if state[DRAW_PILE]:
            players[user.id][HAND].append(state[DRAW_PILE].pop())
            drawn_cards += 1
        else:
            break
        try:
            state = flip_pile_if_empty(state)
        except IndexError as e:
            await send_error(websocket, str(e))

    await send_to_all(websocket_connections, {
        ACTION:  ACTION_DRAW_PENALTY,
        PLAYER:  user.id,
        COUNT_7: drawn_cards
    })

    state[COUNT_7] = 0
    await websocket.send_json({
        ACTION: ACTION_HAND,
        HAND:   players[user.id][HAND],
        CARDS:  players[user.id][HAND][-drawn_cards:]
    })
    await send_to_all(websocket_connections, {
        ACTION:             ACTION_CARD_COUNT,
        DISCARD_PILE_COUNT: len(state[DISCARD_PILE]),
        DRAW_PILE_COUNT:    len(state[DRAW_PILE]),
        HAND_COUNT:         get_hand_counts(players)
    })

    players[user.id][LAST_ACTION] = ACTION_DRAW_PENALTY
    return state, players


# noinspection PyUnusedLocal
async def handle_skip(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Ermöglicht das Überspringen des Zugs (wenn man bereits gezogen hat)."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    # Deny skip if player did not draw and the draw pile is filled
    if players[user.id][LAST_ACTION] != ACTION_DRAW_CARD and state[DRAW_PILE]:
        await send_error(websocket, ERROR_CAN_NOT_SKIP)
        return state, players

    # Nächster Spieler
    state[CURRENT_PLAYER] = get_next_player(user.id, players)
    state[TURN_START_TIME] = time.time()  # Timer neu starten bei Zugwechsel
    await send_to_all(websocket_connections, {
        ACTION: ACTION_TURN,
        PLAYER: state[CURRENT_PLAYER]
    })

    players[user.id][LAST_ACTION] = ACTION_SKIP
    return state, players


# noinspection PyUnusedLocal
async def handle_leave_game(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """Ermöglicht einem Spieler das Verlassen des laufenden Spiels."""
    if len(message) != 0:
        await send_error(websocket, ERROR_WRONG_DATA)
        return state, players

    # Karten des Spielers kommen auf den Ablagestapel
    state[DISCARD_PILE] = players[user.id][HAND] + state[DISCARD_PILE]
    # Save possible next player before removal of current player
    next_player = None
    if state[CURRENT_PLAYER] == user.id:
        next_player = get_next_player(user.id, players)

    remove_player(players, user.id)

    await send_to_all(websocket_connections, {
        ACTION:  ACTION_LEAVE_GAME,
        PLAYER:  user.id,
        PLAYERS: list(players.keys())
    })

    # Prüfen, ob nur ein Spieler übrig
    if len(players) == 1:
        winner = state[WINNER][0] if state[WINNER] else None
        await send_to_all(websocket_connections, {
            ACTION: ACTION_END,
            WINNER: winner
        })

        state = {
            STARTED:        False,
            CURRENT_PLAYER: "",
            DISCARD_PILE:   [],
            DRAW_PILE:      [],
            COUNT_7:        0,
            J_CHOICE:       "",
            WINNER:         []
        }

        players = {}

        return state, players

    # Nächsten Spieler bestimmen
    if next_player:
        state[CURRENT_PLAYER] = next_player
        state[TURN_START_TIME] = time.time()  # Timer zurücksetzen, da Zugwechsel
        await send_to_all(websocket_connections, {
            ACTION: ACTION_TURN,
            PLAYER: state[CURRENT_PLAYER]
        })

    # Karten-Zusammenfassung
    await send_to_all(websocket_connections, {
        ACTION:             ACTION_CARD_COUNT,
        DISCARD_PILE_COUNT: len(state[DISCARD_PILE]),
        DRAW_PILE_COUNT:    len(state[DRAW_PILE]),
        HAND_COUNT:         get_hand_counts(players)
    })
    return state, players


# ============================================================
# Hauptfunktion game_decision
# ============================================================
async def game_decision(
        websocket,
        websocket_connections,
        message: Dict[str, Any],
        state: Dict[str, Any],
        players: Dict[str, Dict[str, Any]],
        settings: Dict[str, Any],
        user
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]]]:
    """
    Steuerung der Spielabläufe basierend auf eingehenden Aktionen.

    :param websocket: Aktuelle WebSocket-Verbindung des Spielers
    :param websocket_connections: Mapping von PlayerID -> WebSocket-Verbindung
    :param message: Eingehende Nachricht (Dictionary) mit Action & Parametern
    :param state: Globaler Spielstatus (Dictionary)
    :param players: Mapping von PlayerID -> Spielerdaten (Handkarten, Ready-Status, etc.)
    :param settings: Spiel-Einstellungen (max. Spieler, Deck-Größe, etc.)
    :param user: Objekt mit Spielerinformationen (z.B. user.id)
    :return: (state, players) - Aktualisierter Spielstatus und Spielerdaten
    """
    action = message.pop(ACTION, None)
    if not action:
        await send_error(websocket, ERROR_NO_ACTION_PROVIDED)
        return state, players

    # Mapping: Aktion -> Handler-Funktion
    action_handlers = {
        ACTION_JOIN:                handle_join,
        ACTION_READY:               handle_ready,
        ACTION_LEAVE_LOBBY:         handle_leave_lobby,
        ACTION_REQUEST_LOBBY_DATA:  handle_request_lobby_data,
        ACTION_REQUEST_GAME_DATA:   handle_request_game_data,
        ACTION_PLACE_CARD_ON_STACK: handle_place_card_on_stack,
        ACTION_DRAW_CARD:           handle_draw_card,
        ACTION_DRAW_PENALTY:        handle_draw_penalty,
        ACTION_SKIP:                handle_skip,
        ACTION_LEAVE_GAME:          handle_leave_game
    }

    # Handhabung der Lobby-spezifischen Aktionen (Spielzustand noch nicht gestartet)
    if action in (ACTION_JOIN, ACTION_READY, ACTION_LEAVE_LOBBY, ACTION_REQUEST_LOBBY_DATA):
        return await action_handlers[action](websocket, websocket_connections, message, state, players, settings,
                                             user) if action in action_handlers else (state, players)

    # Falls das Spiel noch nicht gestartet ist, nur eingeschränkte Aktionen erlauben
    if not state[STARTED]:
        if action == ACTION_REQUEST_GAME_DATA:
            return await handle_request_game_data(websocket, websocket_connections, message, state, players, settings,
                                                  user)
        else:
            await send_error(websocket, ERROR_GAME_NOT_STARTED)
            return state, players

    # Wenn das Spiel läuft, aber eine unbekannte Aktion kommt
    if action not in action_handlers:
        await send_error(websocket, ERROR_UNKNOWN_ACTION)
        return state, players

    # Ab hier: Aktionen, die nur möglich sind, wenn das Spiel läuft (z. B. Karte legen)
    # Prüfen, ob der aktuelle Spieler am Zug ist (sofern kein Request-Game-Data o. Ä.)
    if action not in (ACTION_REQUEST_GAME_DATA, ACTION_LEAVE_GAME) and state[CURRENT_PLAYER] != user.id:
        await send_error(websocket, ERROR_NOT_YOUR_TURN)
        return state, players

    # Aufruf der passenden Handler-Funktion
    return await action_handlers[action](websocket, websocket_connections, message, state, players, settings, user)
