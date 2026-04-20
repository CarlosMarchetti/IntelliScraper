from typing import Optional
import asyncio
import tempfile
import os
from patchright.async_api import async_playwright, Browser, BrowserContext, Page

from intelliscraper.config import config
from intelliscraper.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    def __init__(
        self,
        locale: str = "pt-BR",
        timezone: str = "America/Sao_Paulo",
    ):
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.locale = locale
        self.timezone = timezone
        self._user_data_dir: Optional[str] = None
        self._tmp_dir_obj = None

    async def init(self) -> None:
        try:
            self.playwright = await async_playwright().start()

            self._tmp_dir_obj = tempfile.TemporaryDirectory()
            self._user_data_dir = self._tmp_dir_obj.name

            proxy = {"server": config.proxy_url} if config.proxy_url else None

            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self._user_data_dir,
                channel="chrome",
                headless=config.headless,
                no_viewport=True,
                locale=self.locale,
                timezone_id=self.timezone,
                proxy=proxy,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding",
                    "--window-size=1920,1080",
                ],
            )

            self.page = await self.context.new_page()

            logger.info(f"Browser ready via Patchright (headless={config.headless}, locale={self.locale})")

        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            await self.close()
            raise

    async def get_page_content(self, url: str, wait_until: str = "domcontentloaded") -> str:
        if not self.page:
            raise RuntimeError("Browser not initialized. Call init() first.")
        await self.page.goto(url, wait_until=wait_until, timeout=config.timeout)
        return await self.page.content()

    async def wait_for_selector(self, selector: str, timeout: int = 5000) -> bool:
        if not self.page:
            raise RuntimeError("Browser not initialized.")
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            return False

    async def execute_script(self, script: str) -> any:
        """
        Executa JS. Por padrão roda em contexto isolado (stealth).
        Use isolated_context=False apenas se precisar acessar o contexto principal da página.
        """
        if not self.page:
            raise RuntimeError("Browser not initialized.")
        return await self.page.evaluate(script, isolated_context=True)

    async def set_viewport(self, width: int = 1920, height: int = 1080) -> None:
        if self.page:
            await self.page.set_viewport_size({"width": width, "height": height})

    async def close(self) -> None:
        components = [
            (self.page, "page"),
            (self.context, "context"),
            (self.playwright, "playwright"),
        ]
        for component, name in components:
            if component:
                try:
                    if name == "playwright":
                        await component.stop()
                    else:
                        await component.close()
                except Exception as e:
                    logger.debug(f"Error closing {name}: {e}")

        if self._tmp_dir_obj:
            try:
                self._tmp_dir_obj.cleanup()
            except Exception:
                pass

        logger.info("Browser closed.")

    async def __aenter__(self):
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()