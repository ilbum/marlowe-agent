from packages.browser_runtime.playwright_session import PlaywrightBrowserSession
from packages.extraction.detail_extractor import extract_detail
from packages.persistence.database import async_session_factory
from packages.persistence.repositories import (
    DiscoveredItemRepo,
    ExtractedRecordRepo,
    InvestigationRepo,
)


async def process_item_batch(ctx: dict, investigation_id: str, item_ids: list[str]) -> None:
    async with async_session_factory() as session:
        inv_repo = InvestigationRepo(session)
        item_repo = DiscoveredItemRepo(session)
        record_repo = ExtractedRecordRepo(session)

        inv = await inv_repo.get(investigation_id)
        if inv is None:
            return

        async with await PlaywrightBrowserSession.launch(headless=True) as browser:
            for item_id in item_ids:
                item = await item_repo.get(item_id)
                if item is None or item.item_url is None:
                    await item_repo.set_status(item_id, "failed")
                    continue

                await item_repo.set_status(item_id, "processing")

                try:
                    await browser.goto(item.item_url)
                    await browser.wait_for_network_idle()
                    page_text = await browser.get_visible_text()

                    record = await extract_detail(
                        url=item.item_url,
                        page_text=page_text,
                        objective=inv.objective,
                    )

                    await record_repo.create(
                        item_id=item_id,
                        fields={
                            "entity_title": record.entity_title,
                            "relevant_fields": record.relevant_fields,
                        },
                        match_status=record.match_status,
                        reasoning_summary=record.reasoning_summary,
                        evidence=record.evidence,
                        confidence=record.confidence,
                    )
                    await item_repo.set_status(item_id, "extracted")

                except Exception as e:
                    await record_repo.create(
                        item_id=item_id,
                        fields={},
                        match_status="ambiguous",
                        reasoning_summary=f"Extraction error: {e}",
                        evidence=[],
                    )
                    await item_repo.set_status(item_id, "failed")

        await _finalize_if_complete(investigation_id, inv_repo, item_repo)


async def _finalize_if_complete(investigation_id: str, inv_repo, item_repo) -> None:
    items = await item_repo.list_by_investigation(investigation_id)
    still_pending = any(i.status in ("discovered", "queued", "processing") for i in items)
    if not still_pending:
        await inv_repo.complete(investigation_id)
