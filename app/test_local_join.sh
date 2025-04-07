#!/bin/bash

# Create a guest user and extract JWT
client=$(curl -s -X POST 'http://127.0.0.1:8070/user/guest' -H 'accept: application/json' -d '')
client_jwt=$(echo "$client" | grep -o '"jwt_token":"[^"]*"' | sed 's/"jwt_token":"//;s/"//')

echo "Client JWT: $client_jwt"

echo "Input game_id into console:"
read game_id

# Open WebSocket connection
npx wscat --connect ws://127.0.0.1:8070/game/ws/$game_id?token=$client_jwt  # --proxy $PROXY

# Actions to send to WebSocket (see also https://github.com/phillipc0/PP-CGA-BE/blob/master/docs/)
# {"action": "join"}
# {"action": "ready", "ready": true}
