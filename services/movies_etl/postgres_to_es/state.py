import abc
import json

from typing import Optional, Any


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        pass

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        pass


class JsonFileStorage(BaseStorage):
    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        if self.file_path is None:
            return

        with open(self.file_path, 'w') as fp:
            json.dump(state, fp)

    def retrieve_state(self) -> dict:
        if self.file_path is None:
            return {}

        try:
            with open(self.file_path, 'r') as fp:
                data = json.load(fp)
            return data
        except FileNotFoundError:
            self.save_state({})


class State:
    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.state = self.retrieve_state()

    def retrieve_state(self) -> dict:
        data = self.storage.retrieve_state()
        return data if data else {}

    def set_state(self, key: str, value: Any) -> None:
        self.state[key] = value
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        return self.state.get(key)
