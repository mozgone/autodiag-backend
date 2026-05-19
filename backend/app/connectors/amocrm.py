"""
Коннектор к amoCRM. Требует OAuth-токен.
Документация API: https://www.amocrm.ru/developers/content/crm_platform/api-reference
"""
import httpx
from typing import List, Dict, Any
from datetime import datetime
from app.connectors.base import BaseCRMConnector

class AmoCRMConnector(BaseCRMConnector):
    def __init__(self, subdomain: str, access_token: str):
        self.base_url = f"https://{subdomain}.amocrm.ru/api/v4"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> bool:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/account", headers=self.headers)
            return r.status_code == 200

    async def get_managers(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/users", headers=self.headers)
            r.raise_for_status()
            users = r.json().get("_embedded", {}).get("users", [])
            return [{"id": str(u["id"]), "name": u["name"], "email": u.get("email", ""), "plan": 0} for u in users]

    async def get_deals(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{self.base_url}/leads",
                headers=self.headers,
                params={"filter[responsible_user_id]": manager_id, "filter[updated_at][from]": since_ts, "limit": 250},
            )
            r.raise_for_status()
            leads = r.json().get("_embedded", {}).get("leads", [])
            return [{"id": str(l["id"]), "title": l["name"], "stage": str(l.get("status_id", "")),
                     "stage_order": 0, "amount": l.get("price", 0), "is_won": None,
                     "risk_score": 0.0, "days_in_stage": 0,
                     "created_at": datetime.fromtimestamp(l["created_at"]).isoformat(),
                     "closed_at": None} for l in leads]

    async def get_activities(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        # amoCRM events endpoint
        return []  # TODO: implement via events API
