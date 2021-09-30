from typing import Optional

from pydantic import BaseModel, Field


class Person(BaseModel):
    full_name: str
    id: str
    role: Optional[list[str]] = Field(default_factory=list)
    film_ids: Optional[list[str]] = Field(default_factory=list)
