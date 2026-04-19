import asyncio
from intelliscraper import Scraper


async def main():
    async with Scraper(headless=True) as scraper:
        await scraper.goto("https://quotes.toscrape.com")

        quotes = await scraper.get_texts(".quote .text")
        authors = await scraper.get_texts(".quote .author")

        for quote, author in zip(quotes, authors):
            print(f"{author}: {quote}")


asyncio.run(main())
