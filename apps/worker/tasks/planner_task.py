import arq

from packages.browser_runtime.playwright_session import PlaywrightBrowserSession
from packages.config import settings
from packages.persistence.database import async_session_factory
from packages.persistence.repositories import (
    InvestigationPlanRepo,
    InvestigationRepo,
    PageSnapshotRepo,
)
from packages.understanding.page_classifier import classify_page


async def plan_investigation(ctx: dict, investigation_id: str) -> None:
    async with async_session_factory() as session:
        inv_repo = InvestigationRepo(session)
        plan_repo = InvestigationPlanRepo(session)
        snap_repo = PageSnapshotRepo(session)

        inv = await inv_repo.get(investigation_id)
        if inv is None:
            return

        await inv_repo.set_status(investigation_id, "planning")

        async with await PlaywrightBrowserSession.launch(headless=True) as browser:
            await browser.goto(inv.seed_url)
            await browser.wait_for_network_idle()

            html = await browser.get_html()
            screenshot_bytes = await browser.screenshot()
            current_url = await browser.current_url()

        page_model = await classify_page(
            url=current_url,
            html=html,
            objective=inv.objective,
        )

        await snap_repo.create(
            investigation_id=investigation_id,
            url=current_url,
            page_type=page_model.page_type,
            dom_excerpt=html[:8000],
        )

        await plan_repo.create(
            investigation_id=investigation_id,
            entity_type=page_model.entity_type,
            traversal_strategy=page_model.traversal_type_guess,
            output_schema={},
            user_condition=inv.objective,
            planner_notes=page_model.planner_notes,
        )

        await inv_repo.set_status(investigation_id, "traversing")

        redis = await arq.create_pool(arq.connections.RedisSettings.from_dsn(settings.redis_url))
        await redis.enqueue_job("traverse_list_pages", investigation_id)
        await redis.aclose()
