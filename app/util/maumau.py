import random

VALUE = 'value'
SUIT = 'suit'


def can_place_card_on_stack(new_card, last_card, game_state_j_choice):
    # No Jack on Jack action 😳
    if new_card[VALUE] == 'J' and last_card[VALUE] == 'J':
        return False

    # Jack gets whatever he wants 😏
    if last_card[VALUE] == 'J':
        return new_card[SUIT] == game_state_j_choice

    # Cards are homo and need the same value or suit
    return new_card[VALUE] == last_card[VALUE] or new_card[SUIT] == last_card[SUIT] or new_card[VALUE] == 'J'


def generate_card_deck(size):
    if size not in [32, 52, 64, 104]:
        raise ValueError("Deck size must be one of 32, 52, 64, 104")
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    values = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    if size in [52, 104]:
        values += ['2', '3', '4', '5', '6']

    deck = [{SUIT: suit, VALUE: value} for suit in suits for value in values]
    if size in [64, 104]:
        deck = deck * 2
        # deck.extend(deck)
    random.shuffle(deck)
    return deck


def turn_first_card(game_state_draw_pile, game_state_discard_pile):
    game_state_discard_pile.append(game_state_draw_pile.pop())
    if game_state_discard_pile[-1]["value"] in ['7', '8', 'J']:
        return turn_first_card(game_state_draw_pile, game_state_discard_pile)
    return game_state_draw_pile, game_state_discard_pile


def get_next_player(current_player_id, game_players, skip=0):
    sorted_players = sorted(game_players.keys(), key=lambda pid: game_players[pid]['join_sequence'])
    current_index = sorted_players.index(current_player_id)
    next_index = (current_index + 1 + skip) % len(sorted_players)

    return sorted_players[next_index]
