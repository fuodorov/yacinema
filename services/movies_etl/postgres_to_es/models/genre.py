from typing import Optional
from pydantic import BaseModel


class Genre(BaseModel):
    name: str
    id: str
    film_works = []
