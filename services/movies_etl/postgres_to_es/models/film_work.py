from typing import Optional, List
from pydantic import BaseModel, Field


class FilmWork(BaseModel):
    id: str
    title: str
    rating: Optional[float]
    description: Optional[str]
    genres: List[dict] = Field(default_factory=dict)
    writers: List[str] = Field(default_factory=list)
    actors: List[str] = Field(default_factory=list)
    directors: List[str] = Field(default_factory=list)
