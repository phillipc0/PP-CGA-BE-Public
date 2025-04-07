# npm install -g wscat


client_1=$(curl -s -X POST 'http://127.0.0.1:8070/user/guest' -H 'accept: application/json' -d '')
client_1_jwt=$(echo "$client_1" | grep -o '"jwt_token":"[^"]*"' | sed 's/"jwt_token":"//;s/"//')

game=$(curl -s -X POST 'http://127.0.0.1:8070/game' -H "Authorization: $client_1_jwt" -H "Content-Type: application/json" -d '{"type": "l\u00FCgen", "deck_size": 32, "number_of_start_cards": 5, "gamemode": "gamemode_classic"}')
game_id=$(echo "$game" | grep -o '"id":"[^"]*"' | sed 's/"id":"//;s/"//')

echo "Game: $game"
echo "Game ID: $game_id"
echo "Client 1 JWT: $client_1_jwt"


echo "RealGameID"
read RealGameID


{
   sleep 2
   echo '{"action": "join"}'   # Sende Action join
   sleep 2
} | wscat --connect ws://127.0.0.1:8070/game/ws/$RealGameID?token=$client_1_jwt


{
   sleep 2
   echo '{"action": "ready", "ready": true}'   # Sende Action join
   sleep 2
} | wscat --connect ws://127.0.0.1:8070/game/ws/$RealGameID?token=$client_1_jwt


wscat wscat --connect ws://127.0.0.1:8070/game/ws/$RealGameID?token=$client_1_jwt


trap
while true; do
    read
done
trap