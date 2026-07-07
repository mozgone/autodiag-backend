from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    """Базовый класс ИИ-агента."""

    name: str = "base_agent"

    @abstractmethod
    async def run(self, **kwargs) -> Any:
        pass
