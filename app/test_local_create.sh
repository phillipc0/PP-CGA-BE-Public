#!/bin/bash

# Create a guest user and extract JWT
client=$(curl -s -X POST 'http://127.0.0.1:8070/user/guest' -H 'accept: application/json' -d '')
client_jwt=$(echo "$client" | grep -o '"jwt_token":"[^"]*"' | sed 's/"jwt_token":"//;s/"//')

# Create a new game and extract Game ID
# Mau Mau
game=$(curl -s -X POST 'http://127.0.0.1:8070/game' -H "Authorization: $client_jwt" -H "Content-Type: application/json" -d '{"type": "maumau", "deck_size": 32, "number_of_start_cards": 10, "gamemode":"gamemode_classic"}')
# Lügen
#game=$(curl -s -X POST 'http://127.0.0.1:8070/game' -H "Authorization: $client_jwt" -H "Content-Type: application/json" -d '{"type": "l\u00FCgen", "deck_size": 32, "number_of_start_cards": 5, "gamemode":"gamemode_classic"}')


game_code=$(echo "$game" | grep -o '"code":"[^"]*"' | sed 's/"code":"//;s/"//')
game_id=$(echo "$game" | grep -o '"id":"[^"]*"' | sed 's/"id":"//;s/"//')

echo "Game Created: $game"
echo "Game Code: $game_code"
echo "Game ID: $game_id"
echo "Client JWT: $client_jwt"

# Open WebSocket connection
npx wscat --connect ws://127.0.0.1:8070/game/ws/$game_id?token=$client_jwt

# Actions to send to WebSocket (see also https://github.com/phillipc0/PP-CGA-BE/blob/master/docs/)
# {"action": "join"}
# {"action": "ready", "ready": true}
# {"action": "leave_game"}
# {"action": "draw_card"}
# {"action": "skip"}
# {"action": "place_card_on_stack",  "card": {"value": "7", "suit": "Clubs"}, "mau": false}
# {"action": "place_card_on_stack",  "card": {"value": "J", "suit": "Spades"}, "mau": false, "j_choice":"Hearts"}
# {"action": "place_cards", "cards": [{"suit":"Hearts","value":"7"}],"claimed_value": "7"}
# {"action":"challenge"}
