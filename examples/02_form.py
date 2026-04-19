import asyncio
from intelliscraper import Scraper


async def main():
    async with Scraper(headless=False) as scraper:
        await scraper.goto("https://quotes.toscrape.com/login")

        await scraper.fill("input[name='username']", "admin")
        await scraper.fill("input[name='password']", "admin")
        await scraper.click("input[type='submit']")
        await scraper.wait_for_url("**/")

        print(scraper.current_url)
        await scraper.screenshot("after_login.png")


asyncio.run(main())
