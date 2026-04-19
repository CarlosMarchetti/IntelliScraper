import asyncio
from intelliscraper import Scraper

SESSION_FILE = "session.json"


async def main():
    # with_session() loads the file on entry and saves on exit automatically
    async with Scraper.with_session(SESSION_FILE, headless=False) as scraper:
        await scraper.goto("https://quotes.toscrape.com")

        if await scraper.is_visible("a[href='/login']"):
            await scraper.goto("https://quotes.toscrape.com/login")
            await scraper.fill("input[name='username']", "admin")
            await scraper.fill("input[name='password']", "admin")
            await scraper.click("input[type='submit']")
            await scraper.wait_for_url("**/")

        print(scraper.current_url)


asyncio.run(main())
