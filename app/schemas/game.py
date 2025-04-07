from enum import Enum
from typing import Literal, Optional

from pydantic import Field

from schemas.base import EmptySchema, BaseSchema


class GameType(str, Enum):
    MAU_MAU = 'maumau'
    LÜGEN = 'lügen'


class GameCreateSchema(EmptySchema):
    type: GameType
    deck_size: Literal[32, 52, 64, 104]
    number_of_start_cards: Optional[int] = Field(ge=5, le=10,
                                                 description="Number of start cards must be between 5 and 10.")
    gamemode: Optional[Literal["gamemode_classic", "gamemode_alternative"]]

    class Config:
        use_enum_values = True


class GameSchema(GameCreateSchema, BaseSchema):
    code: str = Field(min_length=6, max_length=6, pattern="^[0-9]*$")
    max_players: int = Field(..., ge=2, le=8, )
