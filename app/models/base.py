import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String

from database import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created = Column(DateTime, nullable=False, default=datetime.now())
    updated = Column(DateTime, nullable=False, default=datetime.now(), onupdate=datetime.now())
