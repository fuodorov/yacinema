import abc
import os
from typing import Any, Optional
import json


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Save state to permanent storage."""
        pass


    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Load state locally from permanent storage."""
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def retrieve_state(self) -> dict:
        try:
            with open(self.file_path) as f:
                state = json.load(f)
        except FileNotFoundError:
            state = {
                "content.person": "01-01-1970 00:00:00",
                "content.genre": "01-01-1970 00:00:00",
                "content.film_work": "01-01-1970 00:00:00"
            }
        return state

    def save_state(self, state: dict) -> None:
        if self.file_path is None:
            return None

        with open(self.file_path, 'w') as f:
            json.dump(state, f)


class State:
    """Class for storing state when working with data.

    Class for storing state when working with data, so that you don't have to constantly re-read the data from the beginning.
    Here is an implementation with state saving to a file.
    In general, nothing prevents you from changing this behaviour to work with a database or distributed storage.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.state = storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Set state for the particular key."""
        self.state[key] = value
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        """Get state for a particular key."""
        state_by_key = self.state.get(key, None)
        return state_by_key
