from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseCRMConnector(ABC):
    """Базовый интерфейс коннектора к CRM."""

    @abstractmethod
    async def get_managers(self) -> List[Dict[str, Any]]:
        """Получить список менеджеров из CRM."""
        pass

    @abstractmethod
    async def get_deals(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Получить сделки менеджера за период."""
        pass

    @abstractmethod
    async def get_activities(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Получить активности (звонки, письма) менеджера за период."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Проверить подключение к CRM."""
        pass
