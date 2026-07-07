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

    async def get_notes(self, manager_id: str, since: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        try:
            notes = await self._paginate("/notes", "notes", {
                "filter[entity_type]": "leads",
                "filter[created_by]": manager_id,
                "filter[created_at][from]": since_ts,
            })
        except Exception as e:
            logger.warning("amoCRM notes fetch failed for %s: %s", manager_id, e)
            return []

        result = []
        for n in notes[:limit]:
            note_type = n.get("note_type")
            is_call = note_type in [10, 13]
            params = n.get("params") or {}
            text = params.get("text") or params.get("talk_time") or ""
            if is_call and not text:
                text = f"Звонок {'входящий' if note_type == 13 else 'исходящий'}"
            created_ts = n.get("created_at")
            result.append({
                "id": str(n["id"]),
                "type": "call" if is_call else "note",
                "text": str(text),
                "created_at": datetime.fromtimestamp(created_ts).isoformat() if created_ts else None,
            })
        return [r for r in result if r["text"]]

    async def get_deals_with_fields(self, manager_id: str, since: datetime) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        leads = await self._paginate("/leads", "leads", {
            "filter[responsible_user_id]": manager_id,
            "filter[created_at][from]": since_ts,
            "with": "custom_fields_values,contacts",
        })
        result = []
        for lead in leads:
            custom = lead.get("custom_fields_values") or []
            contacts = (lead.get("_embedded") or {}).get("contacts") or []
            result.append({
                "id": str(lead["id"]),
                "title": lead.get("name") or "—",
                "amount": float(lead.get("price") or 0),
                "has_contact": len(contacts) > 0,
                "custom_fields": [
                    {
                        "field_id": str(f.get("field_id")),
                        "name": f.get("field_name") or str(f.get("field_id")),
                        "is_empty": not bool(f.get("values")),
                    }
                    for f in custom
                ],
            })
        return result

    async def get_call_recordings(
        self, manager_id: str, since: datetime, limit: int = 15
    ) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        results = []
        # note_type 10 = outgoing call, 13 = incoming call
        for note_type in [10, 13]:
            try:
                notes = await self._paginate("/notes", "notes", {
                    "filter[entity_type]": "leads",
                    "filter[note_type]": note_type,
                    "filter[created_by]": manager_id,
                    "filter[created_at][from]": since_ts,
                })
                for n in notes:
                    params = n.get("params") or {}
                    recording_url = params.get("link") or params.get("record_url")
                    duration = int(params.get("duration") or 0)
                    created_ts = n.get("created_at")
                    results.append({
                        "id": str(n["id"]),
                        "type": "call",
                        "recording_url": recording_url,
                        "text": None,  # will be transcribed by Agent 1
                        "duration_seconds": duration,
                        "created_at": (
                            datetime.fromtimestamp(created_ts).isoformat()
                            if created_ts else None
                        ),
                    })
            except Exception as e:
                logger.warning("amoCRM call notes fetch error type %s: %s", note_type, e)
        # Sort by date desc, return up to limit
        results.sort(key=lambda x: x.get("created_at") or "", reverse=True)
        return results[:limit]

    async def get_chat_messages(
        self, manager_id: str, since: datetime, limit: int = 10
    ) -> List[Dict[str, Any]]:
        since_ts = int(since.timestamp())
        # note_type 4 = incoming chat, 12 = service message, 102/103 = WhatsApp
        all_msgs = []
        for note_type in [4, 12, 102, 103]:
            try:
                notes = await self._paginate("/notes", "notes", {
                    "filter[entity_type]": "leads",
                    "filter[note_type]": note_type,
                    "filter[created_at][from]": since_ts,
                })
                all_msgs.extend(notes)
            except Exception:
                pass
        # Group by entity_id (lead) into conversation threads
        from collections import defaultdict
        threads: dict = defaultdict(list)
        for n in all_msgs:
            entity_id = n.get("entity_id")
            if not entity_id:
                continue
            params = n.get("params") or {}
            text = (params.get("text") or params.get("message") or "").strip()
            if text:
                threads[entity_id].append({
                    "text": text,
                    "note_type": n.get("note_type"),
                    "created_at": n.get("created_at"),
                })
        result = []
        for lead_id, msgs in list(threads.items())[:limit]:
            msgs.sort(key=lambda x: x.get("created_at") or 0)
            lines = []
            for m in msgs:
                role = "Клиент" if m["note_type"] in [4, 102, 103] else "Менеджер"
                lines.append(f"{role}: {m['text']}")
            first_ts = msgs[0].get("created_at") if msgs else None
            result.append({
                "id": f"chat_{lead_id}",
                "type": "chat",
                "text": "\n".join(lines),
                "messages_count": len(msgs),
                "created_at": (
                    datetime.fromtimestamp(first_ts).isoformat()
                    if first_ts else None
                ),
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
