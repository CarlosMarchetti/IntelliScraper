import asyncio
from intelliscraper import Scraper


async def main():
    async with Scraper(headless=True) as scraper:
        await scraper.goto("https://quotes.toscrape.com")

        title = await scraper.get_title()
        print(title)

        soup = await scraper.get_soup()
        meta = soup.extract_metadata()
        print(meta["description"])

        links = soup.extract_links()
        for link in links[:5]:
            print(link["text"], "->", link["href"])


asyncio.run(main())
