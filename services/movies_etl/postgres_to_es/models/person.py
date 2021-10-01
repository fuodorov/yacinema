from typing import Optional, List

from pydantic import BaseModel, Field


class Person(BaseModel):
    full_name: str
    id: str
    role: List[str] = Field(default_factory=list)
    film_ids: List[str] = Field(default_factory=list)
