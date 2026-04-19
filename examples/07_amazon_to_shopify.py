import asyncio
from pathlib import Path
from intelliscraper import Scraper
from intelliscraper.models.product import Product, Image
from intelliscraper.models.shopify import ShopifyCSVGenerator


async def main():
    async with Scraper(headless=False) as scraper:
        await scraper.goto("https://www.amazon.com.br/s?k=computador+completo")

        # Select product cards
        product_cards = await scraper.page.query_selector_all('div[data-cy="asin-faceout-container"]')
        
        products = []
        for card in product_cards[:3]:
            # Extract basic info
            title_el = await card.query_selector('h2 span')
            price_el = await card.query_selector('.a-price .a-offscreen')
            image_el = await card.query_selector('img.s-image')
            link_el  = await card.query_selector('a.a-link-normal')

            name = await title_el.inner_text() if title_el else "Unknown"
            
            # Clean Brazilian price format: "R$ 4.599,00" -> 4599.0
            price_raw = await price_el.inner_text() if price_el else "0"
            price_clean = price_raw.replace("R$", "").replace(".", "").replace(",", ".").strip()
            try:
                price_val = float(price_clean)
            except ValueError:
                price_val = 0.0

            img_url = await image_el.get_attribute("src") if image_el else ""
            prod_url = await link_el.get_attribute("href") if link_el else ""
            if prod_url and not prod_url.startswith("http"):
                prod_url = "https://www.amazon.com.br" + prod_url

            products.append(Product(
                name=name,
                price=price_val,
                url=prod_url,
                category="Computers",
                subcategory="Desktop",
                description=f"Imported from Amazon: {name}",
                images=[Image(url=img_url)] if img_url else []
            ))
            print(f"Scraped: {name[:50]}...")

        if products:
            generator = ShopifyCSVGenerator(vendor_name="Amazon Import")
            output = Path("amazon_products.csv")
            generator.save_csv(products, output)
            print(f"\nDone. Saved {len(products)} products to {output}")


if __name__ == "__main__":
    asyncio.run(main())
