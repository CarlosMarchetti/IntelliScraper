import asyncio
from intelliscraper import Scraper

captured = []


async def on_response(response):
    if response.status == 200:
        try:
            captured.append(await response.json())
        except Exception:
            pass


async def main():
    async with Scraper(headless=True) as scraper:
        await scraper.intercept_requests("**/**", on_response)
        await scraper.goto("https://httpbin.org/get")
        await scraper.sleep(2)

    print(f"Captured {len(captured)} responses")
    print(captured[0] if captured else "None")


asyncio.run(main())
