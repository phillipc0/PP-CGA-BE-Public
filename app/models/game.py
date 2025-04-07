from sqlalchemy import Column, Enum, String

from models.base import BaseModel
from models.custom_type import CustomJSON
from schemas.game import GameType


class GameModel(BaseModel):
    __tablename__ = "game"

    type = Column(Enum(GameType), nullable=False)
    code = Column(String(6), unique=True, nullable=False)
    settings = Column(CustomJSON)
    state = Column(CustomJSON)
    players = Column(CustomJSON)
