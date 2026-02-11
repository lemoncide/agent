from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def run(self, **kwargs) -> Any:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description
        }
