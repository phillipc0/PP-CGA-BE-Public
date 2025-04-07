import random


def generate_card_deck(size):
    if size not in [32, 52, 64, 104]:
        raise ValueError("Deck size must be one of 32, 52, 64, 104")
    suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    values = ['7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    if size in [52, 104]:
        values += ['2', '3', '4', '5', '6']
    deck = [{'suit': suit, 'value': value} for suit in suits for value in values]
    if size in [64, 104]:
        deck = deck * 2
        # deck.extend(deck)
    random.shuffle(deck)
    return deck


def get_next_player(current_player_id, game_players):
    sorted_players = sorted(game_players.keys(), key=lambda pid: game_players[pid]['join_sequence'])
    current_index = sorted_players.index(current_player_id)
    next_index = (current_index + 1) % len(sorted_players)

    return sorted_players[next_index]
