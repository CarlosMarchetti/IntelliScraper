from typing import Optional, List, Dict, Any, Callable
import asyncio
import os
import json
from .browser import BrowserManager
from intelliscraper.utils.logger import get_logger
from intelliscraper.config import config

logger = get_logger(__name__)


class Scraper:
    def __init__(
        self,
        headless: Optional[bool] = None,
        proxy: Optional[str] = None,
        locale: str = "pt-BR",
        timezone: str = "America/Sao_Paulo",
    ):
        if headless is not None:
            config.headless = headless
        if proxy:
            config.proxy_url = proxy

        self.browser_manager = BrowserManager(locale=locale, timezone=timezone)
        self.page = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    @classmethod
    def with_session(cls, session_file: str, **kwargs) -> "_SessionScraper":
        """Context manager that loads a session on enter and saves it on exit."""
        return _SessionScraper(session_file=session_file, **kwargs)

    async def start(self):
        await self.browser_manager.init()
        self.page = self.browser_manager.page
        return self

    async def stop(self):
        await self.browser_manager.close()

    # --- Navigation ---

    async def goto(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int = 30000,
        retries: int = None,
    ) -> None:
        max_retries = retries if retries is not None else config.max_retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to: {url}")
                await self.page.goto(url, wait_until=wait_until, timeout=timeout)
                await asyncio.sleep(1.5)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Navigation failed after {max_retries} attempts: {e}")
                    raise
                wait = config.retry_delay * (attempt + 1)
                logger.warning(f"Retrying ({attempt + 1}/{max_retries}) in {wait:.1f}s...")
                await asyncio.sleep(wait)

    async def wait_for_url(self, pattern: str, timeout: int = 15000) -> None:
        """Waits until the URL matches a glob pattern, e.g. '**/dashboard**'."""
        await self.page.wait_for_url(pattern, timeout=timeout)

    # --- Interaction ---

    async def click(self, selector: str, timeout: int = 15000, retries: int = None) -> None:
        max_retries = retries if retries is not None else config.max_retries
        for attempt in range(max_retries):
            try:
                logger.info(f"Clicking: {selector}")
                await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
                await self.page.click(selector)
                await asyncio.sleep(1)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(config.retry_delay)

    async def fill(self, selector: str, text: str) -> None:
        """Fills a field instantly. Use type() instead when keystroke simulation matters."""
        logger.info(f"Filling: {selector}")
        await self.page.wait_for_selector(selector, state="visible")
        await self.page.fill(selector, text)

    async def type(self, selector: str, text: str, delay: int = 80) -> None:
        """Types text character by character with a human-like delay."""
        logger.info(f"Typing into: {selector}")
        await self.page.wait_for_selector(selector, state="visible")
        await self.page.type(selector, text, delay=delay)

    async def press(self, key: str) -> None:
        await self.page.keyboard.press(key)

    async def scroll(self, amount: int = 400) -> None:
        await self.page.evaluate(f"window.scrollBy(0, {amount})")
        await asyncio.sleep(0.5)

    async def scroll_to_bottom(self) -> None:
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(0.5)

    # --- Waiting ---

    async def wait(self, selector: str, timeout: int = 15000) -> None:
        await self.page.wait_for_selector(selector, state="visible", timeout=timeout)

    async def wait_hidden(self, selector: str, timeout: int = 15000) -> None:
        """Waits for an element to disappear — useful for loading overlays."""
        await self.page.wait_for_selector(selector, state="hidden", timeout=timeout)

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)

    # --- Extraction ---

    async def get_html(self) -> str:
        return await self.page.content()

    async def get_soup(self):
        from intelliscraper.parser import HTMLParser
        return HTMLParser(await self.get_html())

    async def get_json(self) -> Optional[Dict]:
        """Looks for the first parseable <script type='application/json'> on the page."""
        from intelliscraper.parser import HTMLParser
        parser = HTMLParser(await self.get_html())
        for script in parser.soup.find_all("script", type="application/json"):
            try:
                return json.loads(script.string)
            except Exception:
                continue
        return None

    async def get_text(self, selector: str) -> Optional[str]:
        try:
            return await self.page.inner_text(selector)
        except Exception:
            return None

    async def get_texts(self, selector: str) -> List[str]:
        """Returns text from every element matching the selector."""
        try:
            elements = await self.page.query_selector_all(selector)
            return [await el.inner_text() for el in elements]
        except Exception:
            return []

    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        try:
            return await self.page.get_attribute(selector, attribute)
        except Exception:
            return None

    async def get_attributes(self, selector: str, attribute: str) -> List[str]:
        """Returns an attribute value from every element matching the selector."""
        try:
            elements = await self.page.query_selector_all(selector)
            return [v for el in elements if (v := await el.get_attribute(attribute))]
        except Exception:
            return []

    async def is_visible(self, selector: str) -> bool:
        try:
            return await self.page.is_visible(selector)
        except Exception:
            return False

    async def execute(self, script: str) -> Any:
        return await self.page.evaluate(script)

    async def intercept_requests(self, url_pattern: str, callback: Callable) -> None:
        """
        Listens to network responses matching url_pattern and calls callback with each one.

        The callback receives a Playwright Response object:
            async def handler(response):
                data = await response.json()
        """
        self.page.on("response", callback)

    # --- Utilities ---

    async def screenshot(self, filename: str = "debug.png", folder: str = "screenshots") -> str:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved: {path}")
        return path

    async def load_session(self, filepath: str) -> bool:
        """
        Restores cookies and localStorage/sessionStorage from a JSON file.
        Accepts both raw cookie dumps and Playwright's native storage_state format.
        Returns False if the file doesn't exist yet (first run).
        """
        if not os.path.exists(filepath):
            logger.warning(f"Session file not found: '{filepath}'")
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                state = json.load(f)

            valid_keys = {"name", "value", "url", "domain", "path", "expires", "httpOnly", "secure", "sameSite"}
            cookies = []
            for cookie in state.get("cookies", []):
                if "domain" not in cookie and "url" not in cookie:
                    cookie["domain"] = self._domain_from_state(state)
                if "path" not in cookie and "url" not in cookie:
                    cookie["path"] = "/"
                cookies.append({k: v for k, v in cookie.items() if k in valid_keys})

            if cookies:
                await self.browser_manager.context.add_cookies(cookies)
                logger.info(f"Loaded {len(cookies)} cookies.")

            local_storage = state.get("localStorage", {})
            session_storage = state.get("sessionStorage", {})
            origins = state.get("origins", [])

            if local_storage or session_storage or origins:
                domain = self._domain_from_state(state)
                if domain:
                    await self.page.goto(f"{domain}/robots.txt", wait_until="commit")

                for key, value in local_storage.items():
                    await self.page.evaluate(f"window.localStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                for key, value in session_storage.items():
                    await self.page.evaluate(f"window.sessionStorage.setItem({json.dumps(key)}, {json.dumps(value)})")
                for origin_data in origins:
                    for ls in origin_data.get("localStorage", []):
                        await self.page.evaluate(
                            f"window.localStorage.setItem({json.dumps(ls['name'])}, {json.dumps(ls['value'])})"
                        )

            logger.info("Session loaded.")
            return True

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    async def save_session(self, filepath: str) -> None:
        """Saves the current browser state (cookies + storage) to a JSON file."""
        try:
            state = await self.browser_manager.context.storage_state()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
            logger.info(f"Session saved to '{filepath}'")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    # --- Properties ---

    @property
    def current_url(self) -> str:
        return self.page.url if self.page else ""

    async def get_title(self) -> str:
        return await self.page.title()

    # --- Internal ---

    def _domain_from_state(self, state: dict) -> str:
        for cookie in state.get("cookies", []):
            if domain := cookie.get("domain", ""):
                return f"https://{domain.lstrip('.')}"
        origins = state.get("origins", [])
        return origins[0].get("origin", "") if origins else ""

    # --- Backward compatibility ---

    async def getHtml(self) -> str:
        return await self.get_html()

    async def getSoup(self):
        return await self.get_soup()

    async def getJson(self) -> Optional[Dict]:
        return await self.get_json()

    async def getText(self, selector: str) -> Optional[str]:
        return await self.get_text(selector)

    async def getAttribute(self, selector: str, attribute: str) -> Optional[str]:
        return await self.get_attribute(selector, attribute)


class _SessionScraper:
    def __init__(self, session_file: str, **scraper_kwargs):
        self._session_file = session_file
        self._kwargs = scraper_kwargs
        self._scraper: Optional[Scraper] = None

    async def __aenter__(self) -> Scraper:
        self._scraper = Scraper(**self._kwargs)
        await self._scraper.start()
        await self._scraper.load_session(self._session_file)
        return self._scraper

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._scraper:
            await self._scraper.save_session(self._session_file)
            await self._scraper.stop()


IntelliScraper = Scraper
