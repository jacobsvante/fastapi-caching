import uuid
from datetime import datetime

from pydantic import BaseModel, Field, validator

from .utils import random_ascii


class Product(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("description", pre=True, always=True)
    def ensure_random_description(cls, v):
        return v or random_ascii(20_000)
