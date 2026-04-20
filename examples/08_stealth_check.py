import asyncio
from intelliscraper import Scraper


async def main():
    async with Scraper(headless=False) as scraper:
        # 1. Bot Detection Check
        print("Checking bot detection...")
        await scraper.goto("https://www.browserscan.net/bot-detection")
        await scraper.sleep(10)
        await scraper.screenshot("browserscan.png")

        # 2. WebRTC Leaks Check
        print("Checking WebRTC leaks...")
        await scraper.goto("https://browserleaks.com/webrtc")
        await scraper.sleep(30)
        await scraper.screenshot("webrtc.png")

        print("\nScreenshots saved in the 'screenshots' folder.")


if __name__ == "__main__":
    asyncio.run(main())
