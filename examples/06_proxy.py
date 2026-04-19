import asyncio
from intelliscraper import Scraper


async def main():
    async with Scraper(
        headless=True,
        proxy="http://user:pass@proxy-host:8080",
        locale="en-US",
        timezone="America/New_York",
    ) as scraper:
        await scraper.goto("https://httpbin.org/ip")
        print(await scraper.get_html())


asyncio.run(main())
