from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class EmptySchema(BaseModel):
    pass


class BaseSchema(EmptySchema):
    id: UUID
    created: datetime
    updated: datetime
