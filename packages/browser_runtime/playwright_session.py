from typing import Any

from playwright.async_api import Browser, Page, async_playwright


class PlaywrightBrowserSession:
    def __init__(self, page: Page):
        self._page = page

    @classmethod
    async def launch(cls, headless: bool = True) -> "PlaywrightBrowserSession":
        playwright = await async_playwright().start()
        browser: Browser = await playwright.chromium.launch(headless=headless)
        page = await browser.new_page()
        session = cls(page)
        session._playwright = playwright
        session._browser = browser
        return session

    async def close(self) -> None:
        await self._browser.close()
        await self._playwright.stop()

    async def goto(self, url: str) -> None:
        await self._page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    async def click(self, selector: str) -> None:
        await self._page.click(selector, timeout=10_000)

    async def scroll(self, amount: int | None = None) -> None:
        if amount is None:
            await self._page.evaluate("window.scrollBy(0, window.innerHeight)")
        else:
            await self._page.evaluate(f"window.scrollBy(0, {amount})")

    async def screenshot(self) -> bytes:
        return await self._page.screenshot(type="png")

    async def get_html(self) -> str:
        return await self._page.content()

    async def get_visible_text(self) -> str:
        return await self._page.evaluate(
            "document.body ? document.body.innerText : ''"
        )

    async def evaluate_js(self, script: str) -> Any:
        return await self._page.evaluate(script)

    async def wait_for_network_idle(self) -> None:
        try:
            await self._page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass

    async def current_url(self) -> str:
        return self._page.url

    async def __aenter__(self) -> "PlaywrightBrowserSession":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
