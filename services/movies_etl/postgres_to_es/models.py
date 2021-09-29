from dataclasses import dataclass
from typing import List


@dataclass
class Person:
    id: str
    full_name: str


@dataclass
class Movie:
    id: str
    title: str
    description: str
    rating: float
    genres: List[str]
    actors_names: List[str]
    writers_names: List[str]
    directors_names: List[str]
    actors: List[Person]
    writers: List[Person]
    directors: List[Person]
