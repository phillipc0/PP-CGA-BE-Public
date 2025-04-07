import os
import random
import string
from datetime import datetime, timedelta, timezone

import jwt

from models.game import GameModel

SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
AUDIENCE = os.getenv('AUDIENCE', 'PP-CGA-BE')


def generate_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def generate_random_number(length) -> str:
    return ''.join(random.choice(string.digits) for _ in range(length))


def generate_random_number_and_check_if_exists(length, db):
    max_tries = 1000
    for _ in range(max_tries):
        code = generate_random_number(length)
        if not db.query(GameModel).filter_by(code=code).first():
            return code
    raise ValueError("Max tries exceeded while generating a unique code")


async def send_to_all(websockets, message):
    for ws in websockets.values():
        await ws.send_json(message)


def flip_pile_if_empty(state):
    if len(state['draw_pile']) == 0:
        # Ensure that there are enough cards to refill the draw pile.
        if len(state['discard_pile']) <= 1:
            raise IndexError("Failed to reshuffle cards")
        # Preserve the top card of the discard pile.
        top_card = state['discard_pile'][-1]
        # Use the rest of the discard pile.
        new_draw_pile = state['discard_pile'][:-1]
        random.shuffle(new_draw_pile)
        state['draw_pile'] = new_draw_pile
        state['discard_pile'] = [top_card]
    return state


class GameLock:
    def __init__(self):
        self.locks = {}

    def acquire(self, game_id):
        if game_id in self.locks:
            return False
        self.locks[game_id] = True
        return True

    def release(self, game_id):
        if game_id in self.locks:
            del self.locks[game_id]
            return True
        return False


def gen_token(user):
    payload = {
        "aud":      AUDIENCE,
        "sub":      user.id,
        "username": user.username,
        "guest":    user.guest,
        "iat":      datetime.now(timezone.utc),
        "nbf":      datetime.now(timezone.utc),
        "exp":      datetime.now(timezone.utc) + timedelta(days=1 if user.guest else 365)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
