import asyncio
from typing import Optional, Callable, List, Dict, Any
from datetime import datetime

from intelliscraper.core.scraper import IntelliScraper
from intelliscraper.parser import HTMLParser
from intelliscraper.utils.logger import get_logger
from intelliscraper.models.product import Product, Image, Variant
from intelliscraper.models.repository import ProductRepository
from intelliscraper.models.shopify import ShopifyCSVGenerator

logger = get_logger(__name__)


class ProductScraper:
    def __init__(self, vendor_name: str = "Store", base_path: str = "products"):
        self.scraper = IntelliScraper(use_cache=False)
        self.repository = ProductRepository(base_path)
        self.shopify_generator = ShopifyCSVGenerator(vendor_name)
        self.vendor_name = vendor_name

    async def scrape_category_list(
        self,
        url: str,
        category_selector: str,
        name_attr: str = "text"
    ) -> Dict[str, str]:
        logger.info(f"Scraping categories from {url}")
        
        try:
            html = await self.scraper.fetch(url)
            parser = HTMLParser(html)
            
            categories = {}
            category_elements = parser.find_elements(category_selector)
            
            for element in category_elements:
                if name_attr == "text":
                    name = element.get("text", "")
                else:
                    name = element.get("attributes", {}).get(name_attr, "")
                
                if name and "href" in element.get("attributes", {}):
                    url_value = element.get("attributes", {}).get("href", "")
                    categories[name] = url_value
            
            logger.info(f"Found {len(categories)} categories")
            return categories
        
        except Exception as e:
            logger.error(f"Error scraping categories: {e}")
            return {}

    async def scrape_products_from_page(
        self,
        url: str,
        product_selector: str,
        name_selector: str,
        price_selector: str,
        image_selector: Optional[str] = None,
        description_selector: Optional[str] = None,
        category: str = "General",
        subcategory: str = "General",
        wait_for: Optional[str] = None
    ) -> List[Product]:
        logger.info(f"Scraping products from {url} ({category}/{subcategory})")
        
        try:
            html = await self.scraper.fetch(url, wait_for=wait_for)
            parser = HTMLParser(html)
            
            products = []
            product_elements = parser.find_elements(product_selector)
            
            for idx, element in enumerate(product_elements):
                try:
                    name = self._extract_text_from_selector(html, name_selector, element)
                    if not name:
                        logger.warning(f"Product {idx} missing name")
                        continue
                    
                    price_text = self._extract_text_from_selector(html, price_selector, element)
                    price = self._parse_price(price_text)
                    
                    description = ""
                    if description_selector:
                        description = self._extract_text_from_selector(html, description_selector, element)
                    
                    images = []
                    if image_selector:
                        image_urls = self._extract_image_urls_from_selector(html, image_selector, element)
                        images = [Image(url=url) for url in image_urls]
                    
                    product = Product(
                        name=name,
                        price=price,
                        category=category,
                        subcategory=subcategory,
                        description=description,
                        images=images,
                        vendor=self.vendor_name,
                        url=url
                    )
                    
                    products.append(product)
                
                except Exception as e:
                    logger.warning(f"Error parsing product {idx}: {e}")
                    continue
            
            logger.info(f"Scraped {len(products)} products from {category}/{subcategory}")
            return products
        
        except Exception as e:
            logger.error(f"Error scraping products: {e}")
            return []

    async def scrape_product_details(
        self,
        product: Product,
        detail_url: str,
        image_selector: Optional[str] = None,
        variant_selector: Optional[str] = None,
        rating_selector: Optional[str] = None,
        reviews_selector: Optional[str] = None,
        wait_for: Optional[str] = None
    ) -> Product:
        logger.debug(f"Scraping details for {product.name}")
        
        try:
            html = await self.scraper.fetch(detail_url, wait_for=wait_for)
            parser = HTMLParser(html)
            
            if image_selector:
                image_urls = parser.extract_images(image_selector)
                product.images = [Image(url=img.get("src", ""), alt_text=img.get("alt", "")) 
                                 for img in image_urls]
            
            if variant_selector:
                variant_elements = parser.find_elements(variant_selector)
                for element in variant_elements:
                    variant_name = element.get("text", "")
                    if variant_name:
                        variant = Variant(name=variant_name)
                        product.variants.append(variant)
            
            if rating_selector:
                rating_text = parser.extract_text(rating_selector)
                product.rating = self._parse_float(rating_text)
            
            if reviews_selector:
                reviews_text = parser.extract_text(reviews_selector)
                product.reviews_count = self._parse_int(reviews_text)
        
        except Exception as e:
            logger.warning(f"Error scraping details for {product.name}: {e}")
        
        return product

    async def scrape_paginated_category(
        self,
        base_url: str,
        page_pattern: str,
        total_pages: int,
        product_selector: str,
        name_selector: str,
        price_selector: str,
        category: str,
        subcategory: str,
        image_selector: Optional[str] = None,
        description_selector: Optional[str] = None,
        wait_for: Optional[str] = None,
        delay_between_pages: float = 1.0
    ) -> List[Product]:
        logger.info(f"Scraping {total_pages} pages for {category}/{subcategory}")
        
        all_products = []
        
        for page_num in range(1, total_pages + 1):
            try:
                page_url = base_url + page_pattern.format(page=page_num)
                logger.info(f"Scraping page {page_num}/{total_pages}: {page_url}")
                
                products = await self.scrape_products_from_page(
                    url=page_url,
                    product_selector=product_selector,
                    name_selector=name_selector,
                    price_selector=price_selector,
                    image_selector=image_selector,
                    description_selector=description_selector,
                    category=category,
                    subcategory=subcategory,
                    wait_for=wait_for
                )
                
                all_products.extend(products)
                
                if page_num < total_pages:
                    await asyncio.sleep(delay_between_pages)
            
            except Exception as e:
                logger.error(f"Error scraping page {page_num}: {e}")
                continue
        
        return all_products

    def _extract_text_from_selector(self, html: str, selector: str, element: Dict) -> str:
        try:
            parser = HTMLParser(html)
            result = parser.extract_text(selector)
            return result.strip() if result else ""
        except:
            return element.get("text", "").strip()

    def _extract_image_urls_from_selector(self, html: str, selector: str, element: Dict) -> List[str]:
        try:
            parser = HTMLParser(html)
            images = parser.extract_images(selector)
            return [img.get("src", "") for img in images if img.get("src", "")]
        except:
            return []

    def _parse_price(self, price_text: str) -> float:
        import re
        match = re.search(r'\d+[.,]\d{2}', price_text)
        if match:
            price_str = match.group().replace(",", ".")
            try:
                return float(price_str)
            except ValueError:
                pass
        return 0.0

    def _parse_float(self, text: str) -> Optional[float]:
        import re
        match = re.search(r'\d+[.,]\d+', text)
        if match:
            return float(match.group().replace(",", "."))
        return None

    def _parse_int(self, text: str) -> int:
        import re
        match = re.search(r'\d+', text)
        return int(match.group()) if match else 0

    def add_product(self, product: Product) -> None:
        self.repository.add_product(product)

    def add_products(self, products: List[Product]) -> None:
        for product in products:
            self.repository.add_product(product)

    def save_json(self, category: str, subcategory: str) -> str:
        return self.repository.save_json(category, subcategory)

    def save_csv(self, category: str, subcategory: str) -> str:
        return self.repository.save_csv(category, subcategory)

    def save_all(self) -> Dict[str, List[str]]:
        return self.repository.save_all()

    def export_shopify_csv(self, category: str, subcategory: str, output_path: str) -> str:
        from pathlib import Path
        products = self.repository.get_products(category, subcategory)
        return self.shopify_generator.save_csv(products, Path(output_path))

    def export_all_shopify_csv(self, output_dir: str = "shopify_export") -> Dict[str, Dict[str, str]]:
        from pathlib import Path
        return self.shopify_generator.save_by_category_subcategory(
            self.repository.products,
            Path(output_dir)
        )

    def get_stats(self) -> Dict:
        return self.repository.get_stats()

    async def close(self) -> None:
        await self.scraper.close()

    async def __aenter__(self):
        await self.scraper.browser.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
