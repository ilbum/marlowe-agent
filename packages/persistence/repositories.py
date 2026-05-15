from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.persistence.models import (
    DiscoveredItem,
    ExtractedRecord,
    Investigation,
    InvestigationPlan,
    PageSnapshot,
    TraversalLedger,
)


class InvestigationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, seed_url: str, objective: str) -> Investigation:
        inv = Investigation(seed_url=seed_url, objective=objective)
        self.session.add(inv)
        await self.session.commit()
        await self.session.refresh(inv)
        return inv

    async def get(self, investigation_id: str) -> Investigation | None:
        result = await self.session.execute(
            select(Investigation).where(Investigation.id == investigation_id)
        )
        return result.scalar_one_or_none()

    async def set_status(self, investigation_id: str, status: str) -> None:
        await self.session.execute(
            update(Investigation)
            .where(Investigation.id == investigation_id)
            .values(status=status)
        )
        await self.session.commit()

    async def complete(self, investigation_id: str) -> None:
        from datetime import datetime, timezone
        await self.session.execute(
            update(Investigation)
            .where(Investigation.id == investigation_id)
            .values(status="completed", completed_at=datetime.now(timezone.utc))
        )
        await self.session.commit()


class InvestigationPlanRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, investigation_id: str, **kwargs) -> InvestigationPlan:
        plan = InvestigationPlan(investigation_id=investigation_id, **kwargs)
        self.session.add(plan)
        await self.session.commit()
        await self.session.refresh(plan)
        return plan

    async def get_by_investigation(self, investigation_id: str) -> InvestigationPlan | None:
        result = await self.session.execute(
            select(InvestigationPlan).where(InvestigationPlan.investigation_id == investigation_id)
        )
        return result.scalar_one_or_none()


class PageSnapshotRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, investigation_id: str, url: str, page_type: str,
                     dom_excerpt: str | None = None, screenshot_path: str | None = None) -> PageSnapshot:
        snap = PageSnapshot(
            investigation_id=investigation_id,
            url=url,
            page_type=page_type,
            dom_excerpt=dom_excerpt,
            screenshot_path=screenshot_path,
        )
        self.session.add(snap)
        await self.session.commit()
        await self.session.refresh(snap)
        return snap


class DiscoveredItemRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, investigation_id: str, source_page_url: str,
                     stable_key: str, item_url: str | None = None,
                     title_hint: str | None = None,
                     source_page_index: int | None = None) -> DiscoveredItem:
        item = DiscoveredItem(
            investigation_id=investigation_id,
            source_page_url=source_page_url,
            stable_key=stable_key,
            item_url=item_url,
            title_hint=title_hint,
            source_page_index=source_page_index,
        )
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def exists_by_stable_key(self, investigation_id: str, stable_key: str) -> bool:
        result = await self.session.execute(
            select(DiscoveredItem).where(
                DiscoveredItem.investigation_id == investigation_id,
                DiscoveredItem.stable_key == stable_key,
            )
        )
        return result.scalar_one_or_none() is not None

    async def list_by_investigation(self, investigation_id: str) -> Sequence[DiscoveredItem]:
        result = await self.session.execute(
            select(DiscoveredItem).where(DiscoveredItem.investigation_id == investigation_id)
        )
        return result.scalars().all()

    async def get(self, item_id: str) -> DiscoveredItem | None:
        result = await self.session.execute(
            select(DiscoveredItem).where(DiscoveredItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def set_status(self, item_id: str, status: str) -> None:
        await self.session.execute(
            update(DiscoveredItem)
            .where(DiscoveredItem.id == item_id)
            .values(status=status)
        )
        await self.session.commit()

    async def count_by_status(self, investigation_id: str, status: str) -> int:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.count()).where(
                DiscoveredItem.investigation_id == investigation_id,
                DiscoveredItem.status == status,
            )
        )
        return result.scalar_one()


class ExtractedRecordRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, item_id: str, fields: dict, match_status: str,
                     reasoning_summary: str, evidence: list[str],
                     confidence: float | None = None) -> ExtractedRecord:
        record = ExtractedRecord(
            item_id=item_id,
            fields=fields,
            match_status=match_status,
            reasoning_summary=reasoning_summary,
            evidence=evidence,
            confidence=confidence,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_by_investigation(self, investigation_id: str) -> Sequence[ExtractedRecord]:
        result = await self.session.execute(
            select(ExtractedRecord)
            .join(DiscoveredItem, ExtractedRecord.item_id == DiscoveredItem.id)
            .where(DiscoveredItem.investigation_id == investigation_id)
        )
        return result.scalars().all()


class TraversalLedgerRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, investigation_id: str, **kwargs) -> TraversalLedger:
        ledger = TraversalLedger(investigation_id=investigation_id, **kwargs)
        self.session.add(ledger)
        await self.session.commit()
        await self.session.refresh(ledger)
        return ledger

    async def get_by_investigation(self, investigation_id: str) -> TraversalLedger | None:
        result = await self.session.execute(
            select(TraversalLedger).where(TraversalLedger.investigation_id == investigation_id)
        )
        return result.scalar_one_or_none()
