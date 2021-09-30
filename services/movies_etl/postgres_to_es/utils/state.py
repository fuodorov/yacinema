import abc
import os
from typing import Any, Optional
import json


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        """Сохранить состояние в постоянное хранилище"""


    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        """Загрузить состояние локально из постоянного хранилища"""
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
        with open(self.file_path, 'w') as f:
            json.dump(state, f)


class State:
    """
    Класс для хранения состояния при работе с данными, чтобы постоянно не перечитывать данные с начала.
    Здесь представлена реализация с сохранением состояния в файл.
    В целом ничего не мешает поменять это поведение на работу с БД или распределённым хранилищем.
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage
        self.state = storage.retrieve_state()

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа"""
        self.state[key] = value
        self.storage.save_state(self.state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу"""
        state_by_key = self.state.get(key, None)
        return state_by_key


if __name__ == '__main__':
    storage = JsonFileStorage('sandbox.json')
    state = State(storage)
    state.set_state('key', 'value')
    print(state.get_state('key'))