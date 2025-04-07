import asyncio
import json
import time
from math import floor
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi import Path
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker
from starlette.websockets import WebSocket, WebSocketDisconnect

from database import engine
from dependencies import get_db, verify_jwt
from logic.lügen import game_decision as game_decision_lügen
from logic.maumau import game_decision as game_decision_maumau, ACTION, ACTION_END, WINNER
from logic.maumau import get_next_player, get_hand_counts, ACTION_TURN, ACTION_CARD_COUNT
from models.game import GameModel
from models.user import UserModel
from schemas.game import GameCreateSchema, GameSchema
from util.generic import GameLock, generate_random_number_and_check_if_exists, send_to_all

router = APIRouter(prefix="/game", tags=["game"])

lock = GameLock()

# Globale Dictionaries, um die aktiven Websocket-Verbindungen und Timeout-Tasks pro Spiel zu verwalten
websocket_connections = {}  # {game_id: {user_id: websocket, ...}}
turn_timeout_tasks = {}  # {game_id: asyncio.Task}


@router.get("/{game_code}", response_model=GameSchema)
async def game_get(game_code: Annotated[str, Path(min_length=6, max_length=6, pattern="^[0-9]*$")],
                   db: Session = Depends(get_db), user: UserModel = Depends(verify_jwt)):
    game = db.query(GameModel).filter_by(code=game_code).one()
    return {
        "id":                    game.id,
        "type":                  game.type,
        "code":                  game.code,
        "created":               game.created,
        "updated":               game.updated,
        "max_players":           game.settings["max_players"],
        "number_of_start_cards": game.settings["number_of_start_cards"],
        "deck_size":             game.settings["deck_size"],
        "gamemode":              game.settings["gamemode"]
    }


@router.post("", response_model=GameSchema)
async def game_create(game: GameCreateSchema, db: Session = Depends(get_db), user: UserModel = Depends(verify_jwt)):
    max_players = (
        min(floor((game.deck_size - 10) / game.number_of_start_cards), 8)
        if game.type == "maumau"
        else min(floor(game.deck_size / 6), 8)
    )
    new_game = GameModel(
        type=game.type,
        code=generate_random_number_and_check_if_exists(6, db),
        settings={
            "max_players":           max_players,
            "deck_size":             game.deck_size,
            "number_of_start_cards": game.number_of_start_cards,
            "gamemode":              game.gamemode
        },
        state={
            "started": False
        },
        players={}
    )
    db.add(new_game)
    db.commit()
    return {
        "id":                    new_game.id,
        "type":                  new_game.type,
        "code":                  new_game.code,
        "created":               new_game.created,
        "updated":               new_game.updated,
        "max_players":           max_players,
        "number_of_start_cards": game.number_of_start_cards,
        "deck_size":             game.deck_size,
        "gamemode":              game.gamemode
    }


@router.websocket("/ws/{game_id}")
async def game_socket(websocket: WebSocket, game_id: str):
    with sessionmaker(bind=engine)() as db_conn:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close()
            return

        user = verify_jwt(db=db_conn, token=token)
        if not user:
            await websocket.close()
            return

        _game = db_conn.query(GameModel).filter_by(id=game_id).first()
        if not _game:
            await websocket.close()
            return
        game_id = str(_game.id)

    if game_id not in websocket_connections:
        websocket_connections[game_id] = {}
    websocket_connections[game_id][user.id] = websocket

    await websocket.accept()
    print(f"Connected to game {game_id} as {user.id} ({user.username})")

    # Starte den Turn-Timeout-Task, falls noch nicht vorhanden
    if game_id not in turn_timeout_tasks:
        turn_timeout_tasks[game_id] = asyncio.create_task(turn_timeout_loop(game_id))

    while True:
        try:
            message = await websocket.receive_json()
            print(f"Received message: {message} from {user.id} in game {game_id}")
        except WebSocketDisconnect as e:
            print(f"Disconnected from game {game_id} as {user.id} ({user.username})")
            if user.id in websocket_connections.get(game_id, {}):
                del websocket_connections[game_id][user.id]
            break
        except Exception as e:
            await websocket.send_json({"unknown_error": str(e)})
            await websocket.close()
            print(f"Unknown Error: {e}")
            break

        while not lock.acquire(game_id):
            await asyncio.sleep(0.1)

        try:
            with sessionmaker(bind=engine)() as db_conn:
                data = db_conn.execute(text("SELECT * FROM game WHERE id = :id"), {"id": game_id})
                game_list = data.mappings().all()
                if not game_list:
                    await websocket.send_json({"error": "game_not_found"})
                    return

                game_data = game_list[0]
                state = json.loads(game_data["state"]) if isinstance(game_data["state"], str) else game_data["state"]
                players = json.loads(game_data["players"]) if isinstance(game_data["players"], str) else game_data[
                    "players"]
                settings = json.loads(game_data["settings"]) if isinstance(game_data["settings"], str) else game_data[
                    "settings"]

                print(f"Game state: {state}")
                print(f"Game players: {players}")
                print(f"Game settings: {settings}")

                if game_data["type"] == "MAU_MAU":
                    new_state, new_players = await game_decision_maumau(
                        websocket, websocket_connections[game_id], message, state, players, settings, user
                    )
                elif game_data["type"] == "LÜGEN":
                    new_state, new_players = await game_decision_lügen(
                        websocket, websocket_connections[game_id], message, state, players, settings, user
                    )
                else:
                    await websocket.send_json({"error": "unknown_game_type"})
                    continue

                print(f"Game state after: {new_state}")
                print(f"Game players after: {new_players}")

                state_str = json.dumps(new_state)
                players_str = json.dumps(new_players)
                db_conn.execute(
                    text("UPDATE game SET state = :state, players = :players WHERE id = :id"),
                    {"state": state_str, "players": players_str, "id": game_id}
                )
                db_conn.flush()
                db_conn.commit()
        except Exception as e:
            await websocket.send_json({"unknown_error_session": str(e)})
            await websocket.close()
            print(f"Unknown Error: {e}")
            break
        finally:
            lock.release(game_id)


async def turn_timeout_loop(game_id: str):
    """
    Prüft alle 5 Sekunden, ob der aktuelle Spieler länger als 45 Sekunden am Zug ist.
    Falls ja, wird dieser Spieler aus dem Spiel entfernt. Ist danach nur noch ein Spieler übrig,
    wird das Spiel beendet.
    """
    while True:
        await asyncio.sleep(5)  # Überprüfe alle 5 Sekunden
        while not lock.acquire(game_id):
            await asyncio.sleep(0.1)
        try:
            with sessionmaker(bind=engine)() as db_conn:
                data = db_conn.execute(text("SELECT * FROM game WHERE id = :id"), {"id": game_id})
                game_list = data.mappings().all()
                if not game_list:
                    break  # Spiel existiert nicht mehr
                game_data = game_list[0]
                state = json.loads(game_data["state"]) if isinstance(game_data["state"], str) else game_data["state"]
                players = json.loads(game_data["players"]) if isinstance(game_data["players"], str) else game_data[
                    "players"]

                # Falls das Spiel noch nicht gestartet wurde, beenden wir den Loop
                if not state.get("started"):
                    break

                current_player = state.get("CURRENT_PLAYER")
                if not current_player:
                    continue

                turn_start_time = state.get("turn_start_time")
                if not turn_start_time:
                    state["turn_start_time"] = time.time()
                    state_str = json.dumps(state)
                    db_conn.execute(text("UPDATE game SET state = :state WHERE id = :id"),
                                    {"state": state_str, "id": game_id})
                    db_conn.commit()
                    continue

                now = time.time()
                if now - turn_start_time > 45:  # Timeout von 45 Sekunden
                    removed_player = current_player
                    print(f"Player {removed_player} timed out and will be removed from game {game_id}")

                    # Informiere alle Clients über die Timeout-Entfernung
                    await send_to_all(websocket_connections[game_id], {
                        "action": "timeout_penalty",
                        "player": current_player
                    })

                    # Optional: Die Handkarten des Spielers können (falls gewünscht) dem Ablagestapel hinzugefügt werden
                    if removed_player in players:
                        state["DISCARD_PILE"] = players[removed_player].get("HAND", []) + state.get("DISCARD_PILE", [])
                        del players[removed_player]

                    # if removed_player in websocket_connections.get(game_id, {}):
                    #     del websocket_connections[game_id][removed_player]

                    # Prüfe, ob nach Entfernen nur noch ein Spieler übrig bleibt
                    if len(players) <= 1:
                        winner = state[WINNER][0] if state[WINNER] else None
                        await send_to_all(websocket_connections[game_id], {
                            ACTION: ACTION_END,
                            WINNER: winner
                        })
                        state = {
                            "started":        False,
                            "CURRENT_PLAYER": "",
                            "DISCARD_PILE":   [],
                            "DRAW_PILE":      [],
                            "COUNT_7":        0,
                            "J_CHOICE":       "",
                            "WINNER":         []
                        }
                        players = {}
                    else:
                        new_current = get_next_player(removed_player, players)
                        state["CURRENT_PLAYER"] = new_current
                        state["turn_start_time"] = time.time()
                        await send_to_all(websocket_connections[game_id], {
                            ACTION:   ACTION_TURN,
                            "player": new_current
                        })

                        await send_to_all(websocket_connections[game_id], {
                            ACTION:               ACTION_CARD_COUNT,
                            "DISCARD_PILE_COUNT": len(state.get("DISCARD_PILE", [])),
                            "DRAW_PILE_COUNT":    len(state.get("DRAW_PILE", [])),
                            "HAND_COUNT":         get_hand_counts(players)
                        })

                    state_str = json.dumps(state)
                    players_str = json.dumps(players)
                    db_conn.execute(
                        text("UPDATE game SET state = :state, players = :players WHERE id = :id"),
                        {"state": state_str, "players": players_str, "id": game_id}
                    )
                    db_conn.commit()
        except Exception as e:
            print(f"Error in turn timeout loop for game {game_id}: {e}")
        finally:
            lock.release(game_id)
    turn_timeout_tasks.pop(game_id, None)
