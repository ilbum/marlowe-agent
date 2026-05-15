import asyncio
import hashlib
from dataclasses import dataclass

from packages.browser_runtime.playwright_session import PlaywrightBrowserSession
from packages.traversal.dedupe import stable_key
from packages.traversal.ledger import LedgerState
from packages.understanding.page_model_schema import PageModel


@dataclass
class DiscoveredItemCandidate:
    title: str
    item_url: str | None
    stable_key: str
    source_page_url: str
    source_page_index: int


class PaginationStrategy:
    def __init__(self, browser: PlaywrightBrowserSession, page_model: PageModel, seed_url: str):
        self._browser = browser
        self._page_model = page_model
        self._seed_url = seed_url

    async def run(self, seen_keys: set[str], ledger: LedgerState) -> list[DiscoveredItemCandidate]:
        all_items: list[DiscoveredItemCandidate] = []
        page_index = 0

        await self._browser.goto(self._seed_url)
        await self._browser.wait_for_network_idle()

        while True:
            current_url = await self._browser.current_url()

            if current_url in ledger.visited_urls:
                ledger.stop_reason = "URL repeated — already visited"
                ledger.completion_status = "exhausted_traversal"
                break

            ledger.visited_urls.add(current_url)
            ledger.pages_visited += 1

            items = await self._collect_items(current_url, page_index)
            for item in items:
                if item.stable_key in seen_keys:
                    ledger.duplicate_items_skipped += 1
                else:
                    seen_keys.add(item.stable_key)
                    all_items.append(item)
                    ledger.items_discovered += 1

            prev_fingerprint = await self._fingerprint()

            next_selector = await self._detect_next_control()
            if next_selector is None:
                ledger.stop_reason = "No next control found"
                ledger.completion_status = "exhausted_traversal"
                break

            try:
                await self._browser.click(next_selector)
            except Exception as e:
                ledger.stop_reason = f"Click failed: {e}"
                ledger.completion_status = "partial"
                break

            await asyncio.sleep(1.5)
            await self._browser.wait_for_network_idle()

            new_fingerprint = await self._fingerprint()
            if new_fingerprint == prev_fingerprint:
                ledger.stop_reason = "Click did not change results"
                ledger.completion_status = "exhausted_traversal"
                break

            page_index += 1

        return all_items

    async def _collect_items(self, page_url: str, page_index: int) -> list[DiscoveredItemCandidate]:
        items: list[DiscoveredItemCandidate] = []

        for selector in self._page_model.result_item_selector_candidates:
            try:
                cards = await self._browser._page.query_selector_all(selector)
                if not cards:
                    continue
                for card in cards:
                    title = (await card.inner_text()).strip()[:200]
                    href = None
                    for link_sel in self._page_model.detail_link_selector_candidates:
                        try:
                            link = await card.query_selector(link_sel)
                            if link:
                                href = await link.get_attribute("href")
                                break
                        except Exception:
                            pass
                    if not href:
                        try:
                            a = await card.query_selector("a[href]")
                            if a:
                                href = await a.get_attribute("href")
                        except Exception:
                            pass

                    if href and not href.startswith("http"):
                        base = await self._browser.current_url()
                        from urllib.parse import urljoin
                        href = urljoin(base, href)

                    key = stable_key(title, href or "")
                    items.append(DiscoveredItemCandidate(
                        title=title,
                        item_url=href,
                        stable_key=key,
                        source_page_url=page_url,
                        source_page_index=page_index,
                    ))
                if items:
                    break
            except Exception:
                continue

        return items

    async def _detect_next_control(self) -> str | None:
        for selector in self._page_model.next_control_candidates:
            try:
                element = await self._browser._page.query_selector(selector)
                if element is None:
                    continue
                is_disabled = await element.get_attribute("disabled")
                aria_disabled = await element.get_attribute("aria-disabled")
                if is_disabled is not None or aria_disabled == "true":
                    continue
                return selector
            except Exception:
                continue
        return None

    async def _fingerprint(self) -> str:
        text = await self._browser.get_visible_text()
        return hashlib.md5(text[:2000].encode()).hexdigest()
