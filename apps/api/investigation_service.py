import json

import arq
from sqlalchemy.ext.asyncio import AsyncSession

from packages.config import settings
from packages.persistence.models import Investigation
from packages.persistence.repositories import (
    DiscoveredItemRepo,
    ExtractedRecordRepo,
    InvestigationRepo,
    TraversalLedgerRepo,
)


class InvestigationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self._inv_repo = InvestigationRepo(session)
        self._item_repo = DiscoveredItemRepo(session)
        self._record_repo = ExtractedRecordRepo(session)
        self._ledger_repo = TraversalLedgerRepo(session)

    async def create(self, seed_url: str, objective: str) -> Investigation:
        inv = await self._inv_repo.create(seed_url=seed_url, objective=objective)
        redis = await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
        await redis.enqueue_job("plan_investigation", inv.id)
        await redis.aclose()
        return inv

    async def get_progress(self, investigation_id: str) -> dict | None:
        inv = await self._inv_repo.get(investigation_id)
        if inv is None:
            return None
        items = await self._item_repo.list_by_investigation(investigation_id)
        extracted = sum(1 for i in items if i.status == "extracted")
        ledger = await self._ledger_repo.get_by_investigation(investigation_id)
        return {
            "id": inv.id,
            "status": inv.status,
            "progress": {
                "pages_visited": ledger.pages_visited if ledger else 0,
                "items_discovered": len(items),
                "items_processed": extracted,
                "matches_found": 0,
            },
        }

    async def get_results(self, investigation_id: str) -> dict | None:
        inv = await self._inv_repo.get(investigation_id)
        if inv is None:
            return None

        records = await self._record_repo.list_by_investigation(investigation_id)
        items = await self._item_repo.list_by_investigation(investigation_id)
        ledger = await self._ledger_repo.get_by_investigation(investigation_id)

        items_by_id = {i.id: i for i in items}
        matches = []
        ambiguous = []
        failed = 0

        for rec in records:
            item = items_by_id.get(rec.item_id)
            entry = {
                "title": rec.fields.get("entity_title", ""),
                "url": item.item_url if item else None,
                "relevant_fields": rec.fields.get("relevant_fields", {}),
                "evidence": rec.evidence,
                "reasoning": rec.reasoning_summary,
                "confidence": rec.confidence,
            }
            if rec.match_status == "match":
                matches.append(entry)
            elif rec.match_status == "ambiguous":
                ambiguous.append(entry)

        for item in items:
            if item.status == "failed":
                failed += 1

        completion_status = ledger.completion_status if ledger else "uncertain"
        summary = f"Found {len(matches)} matching result(s)."

        return {
            "summary": summary,
            "completion_status": completion_status,
            "coverage": {
                "pages_visited": ledger.pages_visited if ledger else 0,
                "items_discovered": len(items),
                "items_processed": len(records),
                "failed_items": failed,
                "duplicate_items_skipped": ledger.duplicate_items_skipped if ledger else 0,
                "stop_reason": ledger.stop_reason if ledger else "",
            },
            "matches": matches,
            "ambiguous": ambiguous,
        }
