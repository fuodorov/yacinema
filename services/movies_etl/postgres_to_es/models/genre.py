from typing import Optional, List
from pydantic import BaseModel, Field


class Genre(BaseModel):
    name: str
    id: str
    film_works: List[str] = Field(default_factory=list)
