from typing import Optional
from pydantic import BaseModel


class FilmWork(BaseModel):
    title: str
    rating: Optional[float]
    genres = []
    id: str
    writers = []
    actors = []
    directors = []
    description: Optional[str]
