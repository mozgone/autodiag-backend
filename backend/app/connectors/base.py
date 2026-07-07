from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
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

    @abstractmethod
    async def get_notes(self, manager_id: str, since: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        """Получить заметки/переписку по менеджеру."""
        pass

    @abstractmethod
    async def get_deals_with_fields(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        """Получить сделки с кастомными полями для анализа заполненности."""
        pass

    @abstractmethod
    async def get_call_recordings(
        self, manager_id: str, since: datetime, limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Получить список звонков менеджера с записями/транскриптами.

        Returns list of dicts:
          {
            "id": str,
            "type": "call",
            "recording_url": str | None,  # URL аудиофайла для Whisper
            "text": str | None,           # готовый транскрипт (если есть)
            "duration_seconds": int,
            "created_at": str | None,     # ISO datetime string
          }
        """
        pass

    @abstractmethod
    async def get_chat_messages(
        self, manager_id: str, since: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Получить потоки переписки менеджера с клиентами.

        Returns list of dicts:
          {
            "id": str,
            "type": "chat",
            "text": str,            # полный диалог в виде строки
            "messages_count": int,
            "created_at": str | None,  # ISO datetime string первого сообщения
          }
        """
        pass
