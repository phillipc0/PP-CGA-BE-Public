import time
from typing import Dict, Any, Tuple

from util.generic import send_to_all
from util.lügen import (
    generate_card_deck,
    get_next_player
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
CARDS = "cards"
CLAIMED_VALUE = "claimed_value"
ROUND_VALUE = "round_value"
DRAW_PILE = "draw_pile"
REMOVED_PILE = "removed_pile"
WINNER = "winner"
LAST_ACTION = "last_action"
HAND = "hand"
HAND_COUNT = "hand_count"
VALUE = "value"
REASON = "reason"

OPPONENT = "opponent"
CHALLENGER = "challenger"
SUCCESS = "success"

ACTION_JOIN = "join"
ACTION_READY = "ready"
ACTION_LEAVE_LOBBY = "leave_lobby"
ACTION_REQUEST_LOBBY_DATA = "request_lobby_data"
ACTION_LOBBY_DATA = "lobby_data"
ACTION_REQUEST_GAME_DATA = "request_game_data"
ACTION_GAME_DATA = "game_data"
ACTION_PLACE_CARDS = "place_cards"
ACTION_CHALLENGE = "challenge"
ACTION_LEAVE_GAME = "leave_game"
ACTION_START = "start"

ACTION_WIN = "win"
ACTION_END = "end"
ACTION_HAND = "hand"
ACTION_CARD_COUNT = "card_count"
ACTION_TURN = "turn"
ACTION_TIMEOUT_PENALTY = "timeout_penalty"
ACTION_DISCARD_DUPLICATES = "discard_duplicates"

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
ERROR_NO_CARDS_PROVIDED = "no_cards_provided"
ERROR_NO_CLAIMED_VALUE_PROVIDED = "no_claimed_value_provided"
ERROR_CARD_NOT_IN_HAND = "card_not_in_hand"
ERROR_CARD_NOT_ALLOWED = "card_not_allowed"
ERROR_TOO_MANY_CARDS = "too_many_cards"
ERROR_UNKNOWN_ACTION = "unknown_action"
ERROR_VALUE_NOT_POSSIBLE = "error_value_not_possible"
ERROR_CHALLENGE_NOT_POSSIBLE = "error_challenge_not_possible"

CARD_VALUE_A = "A"
DISCARD_PILE = "discard_pile"
DISCARD_PILE_COUNT = "discard_pile_count"
LAST_PLAYER = "last_player"
N_LAST = "n_last"
TURN_START_TIME = "turn_start_time"

SETTING_MAX_PLAYERS = "max_players"
SETTING_DECK_SIZE = "deck_size"
SETTING_NUMBER_OF_START_CARDS = "number_of_start_cards"
SETTINGS_GAMEMODE = "gamemode"
SETTINGS_GAMEMODE_OPTIONS_CLASSIC = "gamemode_classic"
SETTINGS_GAMEMODE_OPTIONS_ALTERNATIVE = "gamemode_alternative"

INIT_STATE = {
    STARTED:         False,
    CURRENT_PLAYER:  None,
    DRAW_PILE:       [],
    REMOVED_PILE:    [],
    WINNER:          [],
    ROUND_VALUE:     None,
    N_LAST:          0,
    TURN_START_TIME: None,
    LAST_PLAYER:     None,
    DISCARD_PILE:    [],
    SUCCESS:         False
}


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
    if all_players_ready(players) and len(players) > 2:
        valid_distribution = False
        while not valid_distribution:
            # Spiel starten
            state = INIT_STATE.copy()
            state[STARTED] = True
            state[DRAW_PILE] = generate_card_deck(size=settings[SETTING_DECK_SIZE])
            state[CURRENT_PLAYER] = list(players.keys())[0]
            state[TURN_START_TIME] = time.time()
            state[WINNER] = []
            state[DISCARD_PILE] = []
            state[REMOVED_PILE] = []

            # Karten austeilen
            cards_count = settings[SETTING_DECK_SIZE] // len(players)
            extra_card = settings[SETTING_DECK_SIZE] % len(players)
            for pid in players:
                player_cards = cards_count + (1 if extra_card > 0 else 0)
                players[pid][HAND] = state[DRAW_PILE][:player_cards]
                players[pid][LAST_ACTION] = ACTION_READY
                state[DRAW_PILE] = state[DRAW_PILE][player_cards:]
                extra_card -= 1

                num_aces = sum(1 for card in players[pid][HAND] if card[VALUE] == CARD_VALUE_A)
                if num_aces == 4 and settings[SETTING_DECK_SIZE] in [32, 52]:
                    valid_distribution = False
                    players[pid][HAND] = []
                elif num_aces == 8 and settings[SETTING_DECK_SIZE] in [64, 104]:
                    valid_distribution = False
                    players[pid][HAND] = []
                else:
                    valid_distribution = True

            if valid_distribution:
                break

        # 4/8-gleiche werden angesagt und entfernt
        for pid in players:
            value_counts = {}
            for card in players[pid][HAND]:
                value = card['value']
                if value in value_counts:
                    value_counts[value] += 1
                else:
                    value_counts[value] = 1
            for value, count in value_counts.items():
                if count == 4 and settings[SETTING_DECK_SIZE] in [32, 52]:
                    players[pid][HAND] = [card for card in players[pid][HAND] if card['value'] != value]
                    state[REMOVED_PILE].append(value)
                    await send_to_all(websocket_connections,
                                      {ACTION: ACTION_DISCARD_DUPLICATES, VALUE: value, PLAYER: pid})
                elif count == 8 and settings[SETTING_DECK_SIZE] in [64, 104]:
                    players[pid][HAND] = [card for card in players[pid][HAND] if card['value'] != value]
                    state[REMOVED_PILE].append(value)
                    await send_to_all(websocket_connections,
                                      {ACTION: ACTION_DISCARD_DUPLICATES, VALUE: value, PLAYER: pid})

        # Sende Start-Info
        await send_to_all(websocket_connections, {
            ACTION: ACTION_START
        })

        for pid in players:
            # Jeder bekommt seine Handkarten
            await websocket_connections[pid].send_json({
                ACTION: ACTION_HAND,
                HAND:   players[pid][HAND]
            })

        # Sende Karten-Zusammenfassung
        await send_to_all(websocket_connections, {
            ACTION:     ACTION_CARD_COUNT,
            HAND_COUNT: get_hand_counts(players)
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
        CURRENT_PLAYER: state[CURRENT_PLAYER],
        HAND:           players[user.id][HAND],
        DISCARD_PILE_COUNT:   len(state[DISCARD_PILE]),
        REMOVED_PILE:   state[REMOVED_PILE],
        ROUND_VALUE:    state[ROUND_VALUE],
        N_LAST:         state[N_LAST],
        LAST_PLAYER:    state[LAST_PLAYER]
    })
    return state, players


# noinspection PyUnusedLocal
async def place_cards(
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
    if CARDS not in message:
        await send_error(websocket, ERROR_NO_CARDS_PROVIDED)
        return state, players

    if CLAIMED_VALUE not in message:
        await send_error(websocket, ERROR_NO_CLAIMED_VALUE_PROVIDED)
        return state, players

    # vars setzen
    cards = message[CARDS]
    claimed_value = message[CLAIMED_VALUE]

    # max. 3 cards with 32/52 deck, max. 7 cards with 64/104 deck
    if (settings[SETTING_DECK_SIZE] in [32, 52] and len(cards) > 3) or (
            settings[SETTING_DECK_SIZE] in [64, 104] and len(cards) > 7):
        await send_error(websocket, ERROR_TOO_MANY_CARDS)
        return state, players

    # win-check for last player
    last_player_id = state[LAST_PLAYER]
    if last_player_id and not players[last_player_id][HAND]:
        players.pop(last_player_id)
        state[WINNER].append(last_player_id)
        await send_to_all(websocket_connections, {
            ACTION: ACTION_WIN,
            PLAYER: last_player_id
        })
        # Wenn nur noch 2 Spieler übrig ist -> Spielende
        if len(players) == 2:
            winner = state[WINNER][0] if state[WINNER] else None
            await send_to_all(websocket_connections, {
                ACTION: ACTION_END,
                REASON: "only_two_players_left",
                WINNER: winner
            })

            state = INIT_STATE.copy()

            players = {}

            return state, players

    # check validity of claimed_value
    values = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    if settings[SETTING_DECK_SIZE] in [52, 104]:
        values += ['2', '3', '4', '5', '6']
    if claimed_value not in values:
        await send_error(websocket, ERROR_VALUE_NOT_POSSIBLE)
        return state, players

    # du kannst kein Ass sagen
    if settings[SETTINGS_GAMEMODE] == SETTINGS_GAMEMODE_OPTIONS_CLASSIC:
        if claimed_value == CARD_VALUE_A:
            await send_error(websocket, ERROR_VALUE_NOT_POSSIBLE)
            return state, players

    # Check, ob Karten tatsächlich in der Hand ist
    for card in cards:
        if card not in players[user.id][HAND]:
            await send_error(websocket, ERROR_CARD_NOT_IN_HAND)
            return state, players

    # Set round_value if not existent
    if state[ROUND_VALUE] is None:
        state[ROUND_VALUE] = claimed_value
    elif state[ROUND_VALUE] != claimed_value:
        await send_error(websocket, ERROR_VALUE_NOT_POSSIBLE)
        return state, players

    # Karten wird auf den Ablagestapel gelegt
    for card in cards:
        state[DISCARD_PILE].append(card)
        players[user.id][HAND].remove(card)

    # vars setzen
    state[N_LAST] = len(cards)
    state[LAST_PLAYER] = state[CURRENT_PLAYER]
    state[CURRENT_PLAYER] = get_next_player(user.id, players)  # der nächste ist dran

    # Broadcast
    await send_to_all(websocket_connections, {
        ACTION:        ACTION_PLACE_CARDS,
        CLAIMED_VALUE: claimed_value,
        N_LAST:        state[N_LAST],
        PLAYER:        user.id
    })

    # Allen den neuen Karten-Count senden
    await send_to_all(websocket_connections, {
        ACTION:     ACTION_CARD_COUNT,
        HAND_COUNT: get_hand_counts(players)
    })

    # Nächster Zug
    await send_to_all(websocket_connections, {
        ACTION: ACTION_TURN,
        PLAYER: state[CURRENT_PLAYER]
    })

    players[user.id][LAST_ACTION] = ACTION_PLACE_CARDS
    return state, players


# noinspection PyUnusedLocal,DuplicatedCode
async def challenge(
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

    if not state[DISCARD_PILE]:
        await send_error(websocket, ERROR_CHALLENGE_NOT_POSSIBLE)
        return state, players

    # auswertung
    for card in state[DISCARD_PILE][-state[N_LAST]:]:
        if card[VALUE] != state[ROUND_VALUE]:
            state[SUCCESS] = True
            break
        else:
            state[SUCCESS] = False

    # aufnehmen
    if state[SUCCESS]:
        players[state[LAST_PLAYER]][HAND].extend(state[DISCARD_PILE])
    else:
        players[user.id][HAND].extend(state[DISCARD_PILE])

    await send_to_all(websocket_connections, {
        ACTION:     ACTION_CHALLENGE,
        OPPONENT:   state[LAST_PLAYER],
        CHALLENGER: user.id,
        SUCCESS:    state[SUCCESS],
        CARDS:      state[DISCARD_PILE][-state[N_LAST]:]
    })

    # lose-check
    if settings[SETTINGS_GAMEMODE] == SETTINGS_GAMEMODE_OPTIONS_CLASSIC:
        required_aces = 4 if settings[SETTING_DECK_SIZE] in [32, 52] else 8
        for pid in players:
            num_aces = sum(1 for card in players[pid][HAND] if card[VALUE] == CARD_VALUE_A)

            if num_aces == required_aces:
                await send_to_all(websocket_connections, {
                    ACTION: ACTION_END,
                    REASON: "Pair of Aces",
                    PLAYER: pid
                })

                state = INIT_STATE.copy()

                players = {}

                return state, players

    # 4/8-gleiche werden angesagt und entfernt
    for pid in players:
        value_counts = {}
        for card in players[pid][HAND]:
            value = card['value']
            if value in value_counts:
                value_counts[value] += 1
            else:
                value_counts[value] = 1
        for value, count in value_counts.items():
            if count == 4 and settings[SETTING_DECK_SIZE] in [32, 52]:
                players[pid][HAND] = [card for card in players[pid][HAND] if card['value'] != value]
                state[REMOVED_PILE].append(value)
                await send_to_all(websocket_connections,
                                  {ACTION: ACTION_DISCARD_DUPLICATES, VALUE: value, PLAYER: pid})
            elif count == 8 and settings[SETTING_DECK_SIZE] in [64, 104]:
                players[pid][HAND] = [card for card in players[pid][HAND] if card['value'] != value]
                state[REMOVED_PILE].append(value)
                await send_to_all(websocket_connections,
                                  {ACTION: ACTION_DISCARD_DUPLICATES, VALUE: value, PLAYER: pid})

    # win-check for last player
    last_player_id = state[LAST_PLAYER]
    if last_player_id and not players[last_player_id][HAND]:
        players.pop(last_player_id)
        state[WINNER].append(last_player_id)
        await send_to_all(websocket_connections, {
            ACTION: ACTION_WIN,
            PLAYER: last_player_id
        })
        # Wenn nur noch 2 Spieler übrig ist -> Spielende
        if len(players) == 2:
            winner = state[WINNER][0] if state[WINNER] else None
            await send_to_all(websocket_connections, {
                ACTION: ACTION_END,
                REASON: "only_two_players_left",
                WINNER: winner
            })

            state = INIT_STATE.copy()

            players = {}

            return state, players

    for pid in players:
        await websocket_connections[pid].send_json({
            ACTION: ACTION_HAND,
            HAND:   players[pid][HAND]
        })

    await send_to_all(websocket_connections, {
        ACTION:     ACTION_CARD_COUNT,
        HAND_COUNT: get_hand_counts(players)
    })

    if not state[SUCCESS]:
        state[CURRENT_PLAYER] = get_next_player(user.id, players)  # der nächste ist dran

    players[user.id][LAST_ACTION] = ACTION_CHALLENGE
    state[ROUND_VALUE] = None
    state[N_LAST] = 0
    state[DISCARD_PILE] = []

    await send_to_all(websocket_connections, {
        ACTION: ACTION_TURN,
        PLAYER: state[CURRENT_PLAYER]
    })

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
    state[DRAW_PILE] = players[user.id][HAND]
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
    if len(players) == 2:
        winner = state[WINNER][0] if state[WINNER] else None
        await send_to_all(websocket_connections, {
            ACTION: ACTION_END,
            REASON: "only_two_players_left",
            WINNER: winner
        })

        state = INIT_STATE.copy()

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

    # Karten austeilen
    cards_count = len(state[DRAW_PILE]) // len(players)
    extra_card = len(state[DRAW_PILE]) % len(players)
    for pid in players:
        player_cards = cards_count + (1 if extra_card > 0 else 0)
        players[pid][HAND].extend(state[DRAW_PILE][:player_cards])
        state[DRAW_PILE] = state[DRAW_PILE][player_cards:]
        extra_card -= 1

    # lose-check
    if settings[SETTINGS_GAMEMODE] == SETTINGS_GAMEMODE_OPTIONS_CLASSIC:
        required_aces = 4 if settings[SETTING_DECK_SIZE] in [32, 52] else 8
        for pid in players:
            num_aces = sum(1 for card in players[pid][HAND] if card[VALUE] == CARD_VALUE_A)

            if num_aces == required_aces:
                await send_to_all(websocket_connections, {
                    ACTION: ACTION_END,
                    REASON: "Pair of Aces",
                    PLAYER: pid
                })

                state = INIT_STATE.copy()

                players = {}

                return state, players

    # 4/8-gleiche werden angesagt und entfernt
    for pid in players:
        value_counts = {}
        for card in players[pid][HAND]:
            value = card['value']
            if value in value_counts:
                value_counts[value] += 1
            else:
                value_counts[value] = 1
        for value, count in value_counts.items():
            if count == 4 and settings[SETTING_DECK_SIZE] in [32, 52]:
                players[pid][HAND] = [card for card in players[pid][HAND] if card['value'] != value]
                state[REMOVED_PILE].append(value)
                await send_to_all(websocket_connections,
                                  {ACTION: ACTION_DISCARD_DUPLICATES, VALUE: value, PLAYER: pid})
            elif count == 8 and settings[SETTING_DECK_SIZE] in [64, 104]:
                players[pid][HAND] = [card for card in players[pid][HAND] if card['value'] != value]
                state[REMOVED_PILE].append(value)
                await send_to_all(websocket_connections,
                                  {ACTION: ACTION_DISCARD_DUPLICATES, VALUE: value, PLAYER: pid})

    for pid in players:
        await websocket_connections[pid].send_json({
            ACTION: ACTION_HAND,
            HAND:   players[pid][HAND]
        })

    # Karten-Zusammenfassung
    await send_to_all(websocket_connections, {
        ACTION:     ACTION_CARD_COUNT,
        HAND_COUNT: get_hand_counts(players)
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
        ACTION_JOIN:               handle_join,
        ACTION_READY:              handle_ready,
        ACTION_LEAVE_LOBBY:        handle_leave_lobby,
        ACTION_REQUEST_LOBBY_DATA: handle_request_lobby_data,
        ACTION_REQUEST_GAME_DATA:  handle_request_game_data,
        ACTION_PLACE_CARDS:        place_cards,
        ACTION_CHALLENGE:          challenge,
        ACTION_LEAVE_GAME:         handle_leave_game
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
