import asyncio
from intelliscraper import Scraper


async def example_basic():
    async with Scraper(headless=True) as scraper:
        await scraper.goto("https://quotes.toscrape.com")

        title = await scraper.get_title()
        print(title)

        soup = await scraper.get_soup()
        meta = soup.extract_metadata()
        print(meta["description"])
        print(meta["og_image"])

        links = soup.extract_links()
        for link in links[:5]:
            print(link["text"], link["href"])


async def example_form():
    async with Scraper(headless=False) as scraper:
        await scraper.goto("https://quotes.toscrape.com/login")

        await scraper.fill("input[name='username']", "admin")
        await scraper.fill("input[name='password']", "admin")
        await scraper.click("input[type='submit']")
        await scraper.wait_for_url("**/")

        print(scraper.current_url)
        await scraper.screenshot("after_login.png")


async def example_list():
    async with Scraper(headless=True) as scraper:
        await scraper.goto("https://quotes.toscrape.com")

        quotes = await scraper.get_texts(".quote .text")
        authors = await scraper.get_texts(".quote .author")

        for quote, author in zip(quotes, authors):
            print(f"{author}: {quote}")


async def example_session():
    # with_session() loads the file on entry and saves on exit automatically
    async with Scraper.with_session("session.json", headless=False) as scraper:
        await scraper.goto("https://quotes.toscrape.com")

        if await scraper.is_visible("a[href='/login']"):
            await scraper.goto("https://quotes.toscrape.com/login")
            await scraper.fill("input[name='username']", "admin")
            await scraper.fill("input[name='password']", "admin")
            await scraper.click("input[type='submit']")
            await scraper.wait_for_url("**/")

        print(scraper.current_url)


async def example_api_intercept():
    captured = []

    async def on_response(response):
        if response.status == 200:
            try:
                captured.append(await response.json())
            except Exception:
                pass

    async with Scraper(headless=True) as scraper:
        await scraper.intercept_requests("**/**", on_response)
        await scraper.goto("https://httpbin.org/get")
        await scraper.sleep(2)

    print(f"Captured {len(captured)} responses")


async def example_proxy():
    async with Scraper(
        headless=True,
        proxy="http://user:pass@proxy-host:8080",
        locale="en-US",
        timezone="America/New_York",
    ) as scraper:
        await scraper.goto("https://httpbin.org/ip")
        print(await scraper.get_html())


if __name__ == "__main__":
    asyncio.run(example_list())
