"""
Коннектор к amoCRM API v4.
Документация: https://www.amocrm.ru/developers/content/crm_platform/api-reference
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

import httpx

from app.connectors.base import BaseCRMConnector

logger = logging.getLogger(__name__)

# Зарезервированные статусы amoCRM (едины для всех аккаунтов)
AMO_STATUS_WON = 142
AMO_STATUS_LOST = 143


class AmoCRMConnector(BaseCRMConnector):
    def __init__(self, subdomain: str, access_token: str):
        self.base_url = f"https://{subdomain}.amocrm.ru/api/v4"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def _get(self, path: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"{self.base_url}{path}",
                headers=self.headers,
                params=params or {},
            )
            r.raise_for_status()
            return r.json()

    async def _paginate(self, path: str, embed_key: str, params: dict) -> List[dict]:
        """Обходит все страницы результатов (до 250 × 20 = 5000 записей)."""
        items: List[dict] = []
        page = 1
        while page <= 20:
            try:
                data = await self._get(path, {**params, "page": page, "limit": 250})
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 204:
                    break  # нет больше данных
                raise
            chunk = data.get("_embedded", {}).get(embed_key, [])
            items.extend(chunk)
            if len(chunk) < 250:
                break
            page += 1
        return items

    async def test_connection(self) -> bool:
        try:
            await self._get("/account")
            return True
        except Exception as e:
            logger.warning("amoCRM test_connection failed: %s", e)
            return False

    async def get_managers(self) -> List[Dict[str, Any]]:
        data = await self._get("/users", {"limit": 250})
        users = data.get("_embedded", {}).get("users", [])
        return [
            {
                "id": str(u["id"]),
                "name": u.get("name") or "—",
                "email": u.get("email") or "",
                "plan": 0,
            }
            for u in users
        ]

    async def get_deals(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        leads = await self._paginate(
            "/leads",
            "leads",
            {
                "filter[responsible_user_id]": manager_id,
                "filter[created_at][from]": since_ts,
            },
        )
        result = []
        for lead in leads:
            status_id = lead.get("status_id")
            if status_id == AMO_STATUS_WON:
                is_won = True
            elif status_id == AMO_STATUS_LOST:
                is_won = False
            else:
                is_won = None

            created_ts = lead.get("created_at")
            closed_ts = lead.get("closed_at")
            result.append({
                "id": str(lead["id"]),
                "title": lead.get("name") or "—",
                "stage": str(status_id or ""),
                "amount": float(lead.get("price") or 0),
                "is_won": is_won,
                "created_at": datetime.fromtimestamp(created_ts).isoformat() if created_ts else None,
                "closed_at": datetime.fromtimestamp(closed_ts).isoformat() if closed_ts else None,
            })
        return result

    async def get_activities(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        try:
            events = await self._paginate(
                "/events",
                "events",
                {
                    "filter[type][]": ["outgoing_call", "incoming_call"],
                    "filter[created_at][from]": since_ts,
                    "filter[created_by]": manager_id,
                },
            )
        except Exception as e:
            logger.warning("amoCRM events fetch failed for manager %s: %s", manager_id, e)
            return []

        result = []
        for ev in events:
            # Длительность звонка может лежать в разных местах
            duration = 0
            va = ev.get("value_after")
            if isinstance(va, dict):
                duration = int(va.get("duration") or 0)
            elif isinstance(va, list):
                for item in va:
                    if isinstance(item, dict) and "duration" in item:
                        duration = int(item.get("duration") or 0)
                        break

            created_ts = ev.get("created_at")
            result.append({
                "id": str(ev["id"]),
                "type": "call",
                "duration_seconds": duration,
                "quality_score": 0.0,
                "sentiment": "neutral",
                "created_at": datetime.fromtimestamp(created_ts).isoformat() if created_ts else None,
            })
        return result
