# Events

### Lobby
Only possible if the game has not started yet

* {"action": "join"}
* The player is added to a game
* The own playerId is displayed(player) and all others(players)
> anytime {"action":"join","player":"9f269358-bab5-4435-8439-567f884c4ec6","players":["5c7ceb01-220d-47c7-a799-3067e17d36eb","9f269358-bab5-4435-8439-567f884c4ec6"]}


* {"action": "ready", "ready": true}
* {"action": "ready", "ready": false}
* The player is set to ready and the game starts when everyone is ready
* The player status (ready) is displayed and all other players are set to ready.
> anytime {"action":"ready","player":"9f269358-bab5-4435-8439-567f884c4ec6","ready":true,"players":{"5c7ceb01-220d-47c7-a799-3067e17d36eb":true,"9f269358-bab5-4435-8439-567f884c4ec6":true}}
* Leaves the lobby
* {"action": "leave_lobby"}

### Data
* {"action": "request_lobby_data"}
* All players and their ready status are returned
> Always possible, Players only {"action":"lobby_data","players":{"78970e1b-afab-4dce-9b81-6ab91ec6dc17":true,"3f093d3d-6b9d-4570-8ac4-5d1b70e7c003":true}}
* {"action": "request_game_data"}
* All players and the number of cards in their hand, the last card played, the number of cards in the draw pile and the current player and his own cards are displayed
> Only in the lobby, Only the player {"action":"game_data","players":{"4edbb2ee-9c32-4af9-9576-fe34a7378f92":7,"8f9bea02-4855-43d1-9067-c2ea3aa58e53":7},"discard_pile":{"suit":"Spades","value":"10"},"draw_pile":16,"current_player":"4edbb2ee-9c32-4af9-9576-fe34a7378f92","hand":[{"suit":"Clubs","value":"10"},{"suit":"Hearts","value":"10"},{"suit":"Diamonds","value":"8"},{"suit":"Hearts","value":"7"},{"suit":"Hearts","value":"J"},{"suit":"Clubs","value":"8"},{"suit":"Clubs","value":"9"}]}
* {"action": "leave_game"}

### place_card_on_stack
Only possible when it's your turn
* {"action": "place_card_on_stack",  "card": {"value": "9", "suit": "Hearts"}, "mau": false}
* {"action": "place_card_on_stack",  "card": {"value": "J", "suit": "Clubs"}, "mau": True, "j_choice": "Diamonds"}
* {"action": "place_card_on_stack",  "card": {"value": "J", "suit": "Spades"}, "mau": false, "j_choice": "Clubs"}
* {"action": "place_card_on_stack",  "card": {"value": "K", "suit": "Spades"}, "mau": True}
> anytime {"action":"place_card_on_stack","card":{"value":"K","suit":"Spades"},"player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}

> anytime {"action":"mau","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}

Not executable only for information
> {"action":"discard_duplicates", "value":"value", "player":"playersID"}
> {"action":"discard_duplicates", "value":"A", "player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}

### utils
Only possible when you are on the train but then always allowed
* {"action": "draw_card"}
> anytime {"action":"draw_card","player":"a7df5795-bf8b-4fdd-99e7-7d3a0634675d"}

> active player only {"action":"hand","hand":[{"suit":"Clubs","value":"J"},{"suit":"Spades","value":"A"},{"suit":"Hearts","value":"8"},{"suit":"Spades","value":"Q"},{"suit":"Hearts","value":"Q"},{"suit":"Diamonds","value":"8"}]}

> anytime {"action":"card_count","discard_pile_count":1,"draw_pile_count":20,"hand_count":{"a7df5795-bf8b-4fdd-99e7-7d3a0634675d":6,"be1476cb-cb6c-447b-84c0-bf61702af291":5}}

* {"action": "skip"}
> anytime  {"action":"turn","player":"be1476cb-cb6c-447b-84c0-bf61702af291"}

* {"action": "draw_penalty"}


# Gameplay

Client 1
> {"action": "join"}
< {"action":"join","player":"38784576-7742-45a3-a89e-c6f38bcf43f5","players":["38784576-7742-45a3-a89e-c6f38bcf43f5"]}
Connected (press CTRL+C to quit)
< {"action":"join","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1","players":["38784576-7742-45a3-a89e-c6f38bcf43f5","c61fed8c-58f7-4cae-ab3c-9911924bbbb1"]}
> {"action": "ready", "ready": true}
< {"action":"ready","player":"38784576-7742-45a3-a89e-c6f38bcf43f5","ready":true,"players":{"38784576-7742-45a3-a89e-c6f38bcf43f5":true,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":false}}
Connected (press CTRL+C to quit)
< {"action":"ready","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1","ready":true,"players":{"38784576-7742-45a3-a89e-c6f38bcf43f5":true,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":true}}
< {"action":"start","draw_pile":{"suit":"Spades","value":"Q"}}
< {"action":"hand","hand":[{"suit":"Diamonds","value":"Q"},{"suit":"Diamonds","value":"9"}]}
< {"action":"card_count","discard_pile_count":3,"draw_pile_count":25,"hand_count":{"38784576-7742-45a3-a89e-c6f38bcf43f5":2,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":2}}
< {"action":"turn","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
> {"action": "request_hand_data"}
< {"action":"hand_data","hand":[{"suit":"Diamonds","value":"Q"},{"suit":"Diamonds","value":"9"}]}
> {"action": "skip"}
< {"error":"not_your_turn"}
< {"action":"place_card_on_stack","card":{"value":"J","suit":"Clubs"},"player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"mau","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"card_count","discard_pile_count":4,"draw_pile_count":25,"hand_count":{"38784576-7742-45a3-a89e-c6f38bcf43f5":2,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":1}}
< {"action":"turn","player":"38784576-7742-45a3-a89e-c6f38bcf43f5"}
> {"action": "skip"}
< {"action":"turn","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"place_card_on_stack","card":{"value":"7","suit":"Clubs"},"player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"win","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"end","winner":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}

Client 2
> {"action": "join"}
< {"action":"join","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1","players":["38784576-7742-45a3-a89e-c6f38bcf43f5","c61fed8c-58f7-4cae-ab3c-9911924bbbb1"]}
< {"action":"ready","player":"38784576-7742-45a3-a89e-c6f38bcf43f5","ready":true,"players":{"38784576-7742-45a3-a89e-c6f38bcf43f5":true,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":false}}
Connected (press CTRL+C to quit)
> {"action": "ready", "ready": true}
< {"action":"ready","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1","ready":true,"players":{"38784576-7742-45a3-a89e-c6f38bcf43f5":true,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":true}}
< {"action":"start","draw_pile":{"suit":"Spades","value":"Q"}}
< {"action":"hand","hand":[{"suit":"Clubs","value":"J"},{"suit":"Clubs","value":"7"}]}
< {"action":"card_count","discard_pile_count":3,"draw_pile_count":25,"hand_count":{"38784576-7742-45a3-a89e-c6f38bcf43f5":2,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":2}}
< {"action":"turn","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
Connected (press CTRL+C to quit)
> {"action": "request_game_data"}
< {"action":"game_data","players":{"38784576-7742-45a3-a89e-c6f38bcf43f5":2,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":2},"discard_pile":{"suit":"Clubs","value":"K"},"draw_pile":25,"current_player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
> {"action": "request_hand_data"}
< {"action":"hand_data","hand":[{"suit":"Clubs","value":"J"},{"suit":"Clubs","value":"7"}]}
> {"action": "place_card_on_stack",  "card": {"value": "J", "suit": "Clubs"}, "mau": true, "j_choice": "Clubs"}
< {"action":"place_card_on_stack","card":{"value":"J","suit":"Clubs"},"player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"mau","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"card_count","discard_pile_count":4,"draw_pile_count":25,"hand_count":{"38784576-7742-45a3-a89e-c6f38bcf43f5":2,"c61fed8c-58f7-4cae-ab3c-9911924bbbb1":1}}
< {"action":"turn","player":"38784576-7742-45a3-a89e-c6f38bcf43f5"}
< {"action":"turn","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
> {"action": "request_hand_data"}
< {"action":"hand_data","hand":[{"suit":"Clubs","value":"7"}]}
> {"action": "place_card_on_stack",  "card": {"value": "7", "suit": "Clubs"}, "mau": true}
< {"action":"place_card_on_stack","card":{"value":"7","suit":"Clubs"},"player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"win","player":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
< {"action":"end","winner":"c61fed8c-58f7-4cae-ab3c-9911924bbbb1"}
