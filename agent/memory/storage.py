from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseStorage(ABC):
    @abstractmethod
    def add(self, data: Dict[str, Any]):
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        pass

class InMemoryStorage(BaseStorage):
    def __init__(self):
        self.data = []

    def add(self, data: Dict[str, Any]):
        self.data.append(data)

    def get_all(self) -> List[Dict[str, Any]]:
        return self.data
