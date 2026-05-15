import arq

from packages.browser_runtime.playwright_session import PlaywrightBrowserSession
from packages.config import settings
from packages.persistence.database import async_session_factory
from packages.persistence.repositories import (
    DiscoveredItemRepo,
    InvestigationPlanRepo,
    InvestigationRepo,
    TraversalLedgerRepo,
)
from packages.traversal.ledger import LedgerState
from packages.traversal.strategies.pagination import PaginationStrategy
from packages.understanding.page_classifier import classify_page
from packages.understanding.page_model_schema import PageModel

_BATCH_SIZE = 10


async def traverse_list_pages(ctx: dict, investigation_id: str) -> None:
    async with async_session_factory() as session:
        inv_repo = InvestigationRepo(session)
        plan_repo = InvestigationPlanRepo(session)
        item_repo = DiscoveredItemRepo(session)
        ledger_repo = TraversalLedgerRepo(session)

        inv = await inv_repo.get(investigation_id)
        plan = await plan_repo.get_by_investigation(investigation_id)
        if inv is None or plan is None:
            return

        page_model = await _build_page_model_from_plan(plan, inv.seed_url, inv.objective)

        ledger = LedgerState(traversal_type=page_model.traversal_type_guess or "pagination")
        seen_keys: set[str] = set()

        async with await PlaywrightBrowserSession.launch(headless=True) as browser:
            strategy = PaginationStrategy(browser, page_model, inv.seed_url)
            discovered = await strategy.run(seen_keys, ledger)

        for candidate in discovered:
            await item_repo.create(
                investigation_id=investigation_id,
                source_page_url=candidate.source_page_url,
                stable_key=candidate.stable_key,
                item_url=candidate.item_url,
                title_hint=candidate.title[:200] if candidate.title else None,
                source_page_index=candidate.source_page_index,
            )

        await ledger_repo.create(
            investigation_id=investigation_id,
            traversal_type=ledger.traversal_type,
            pages_visited=ledger.pages_visited,
            items_discovered=ledger.items_discovered,
            duplicate_items_skipped=ledger.duplicate_items_skipped,
            stop_reason=ledger.stop_reason,
            completion_status=ledger.completion_status,
        )

        await inv_repo.set_status(investigation_id, "extracting")

        all_items = await item_repo.list_by_investigation(investigation_id)
        item_ids = [item.id for item in all_items]

        redis = await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
        for i in range(0, len(item_ids), _BATCH_SIZE):
            batch = item_ids[i:i + _BATCH_SIZE]
            await redis.enqueue_job("process_item_batch", investigation_id, batch)
        await redis.aclose()


async def _build_page_model_from_plan(plan, seed_url: str, objective: str) -> PageModel:
    # Re-classify if plan lacks selector candidates; otherwise reconstruct from plan notes.
    # For Phase 1A we always re-classify to get fresh selector candidates.
    from packages.browser_runtime.playwright_session import PlaywrightBrowserSession
    async with await PlaywrightBrowserSession.launch(headless=True) as browser:
        await browser.goto(seed_url)
        await browser.wait_for_network_idle()
        html = await browser.get_html()
        current_url = await browser.current_url()
    return await classify_page(url=current_url, html=html, objective=objective)
