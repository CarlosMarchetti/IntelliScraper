import csv
from pathlib import Path
from typing import List, Optional, Dict
from .product import Product, Variant
from intelliscraper.utils.logger import get_logger

logger = get_logger(__name__)


class ShopifyCSVGenerator:
    HANDLE_SEPARATOR = "-"
    
    SHOPIFY_FIELDS = [
        "Handle",
        "Title",
        "Body (HTML)",
        "Vendor",
        "Type",
        "Tags",
        "Published",
        "Option1 Name",
        "Option1 Value",
        "Option2 Name",
        "Option2 Value",
        "Variant SKU",
        "Variant Barcode",
        "Variant Price",
        "Variant Compare At Price",
        "Variant Weight",
        "Variant Weight Unit",
        "Variant Inventory Tracker",
        "Variant Inventory Qty",
        "Variant Inventory Policy",
        "Variant Fulfillment Service",
        "Variant Requires Shipping",
        "Variant Tax Code",
        "Image Src",
        "Image Position",
        "Image Alt Text",
        "Gift Card",
        "SEO Title",
        "SEO Description",
        "Google Shopping / Google Product Category",
        "Google Shopping / Gender",
        "Google Shopping / Age Group",
        "Google Shopping / MPN",
        "Google Shopping / AdWords Grouping",
        "Google Shopping / AdWords Labels",
        "Google Shopping / Condition",
        "Google Shopping / Custom Product",
        "Google Shopping / Custom Label 0",
        "Google Shopping / Custom Label 1",
        "Google Shopping / Custom Label 2",
        "Google Shopping / Custom Label 3",
        "Google Shopping / Custom Label 4",
    ]

    def __init__(self, vendor_name: str = "Store"):
        self.vendor_name = vendor_name
        self.handle_counter: Dict[str, int] = {}

    def slugify(self, text: str) -> str:
        text = text.lower().strip()
        text = "".join(c if c.isalnum() or c.isspace() else "" for c in text)
        text = "-".join(text.split())
        text = text.replace("--", "-")
        return text.rstrip("-").lstrip("-")

    def generate_handle(self, product: Product) -> str:
        base_handle = self.slugify(f"{product.category}-{product.subcategory}-{product.name}")
        
        if base_handle not in self.handle_counter:
            self.handle_counter[base_handle] = 0
            return base_handle
        
        self.handle_counter[base_handle] += 1
        return f"{base_handle}-{self.handle_counter[base_handle]}"

    def generate_csv_rows(self, products: List[Product]) -> List[Dict]:
        rows = []
        
        for product in products:
            handle = self.generate_handle(product)
            
            if not product.variants or len(product.variants) == 0:
                row = self._create_base_row(handle, product)
                row["Variant SKU"] = product.sku or f"{handle}-default"
                row["Variant Price"] = f"{product.price:.2f}"
                
                if product.images:
                    row["Image Src"] = product.images[0].url
                    row["Image Alt Text"] = product.images[0].alt_text or product.name
                
                rows.append(row)
                
                for i, image in enumerate(product.images[1:], 1):
                    image_row = {
                        "Handle": handle,
                        "Image Src": image.url,
                        "Image Position": str(i + 1),
                        "Image Alt Text": image.alt_text or f"{product.name} - Image {i + 1}",
                    }
                    rows.append(image_row)
            else:
                for variant_idx, variant in enumerate(product.variants):
                    row = self._create_base_row(handle, product) if variant_idx == 0 else {}
                    
                    row["Handle"] = handle
                    row["Option1 Name"] = "Variant"
                    row["Option1 Value"] = variant.name
                    row["Variant SKU"] = variant.sku or f"{handle}-{self.slugify(variant.name)}"
                    row["Variant Price"] = f"{variant.price if variant.price else product.price:.2f}"
                    
                    if variant.weight:
                        row["Variant Weight"] = str(variant.weight)
                        row["Variant Weight Unit"] = "kg"
                    
                    if variant_idx == 0 and product.images:
                        row["Image Src"] = product.images[0].url
                        row["Image Alt Text"] = product.images[0].alt_text or product.name
                    
                    rows.append(row)
                
                for i, image in enumerate(product.images[1:], 1):
                    image_row = {
                        "Handle": handle,
                        "Image Src": image.url,
                        "Image Position": str(i + 1),
                        "Image Alt Text": image.alt_text or f"{product.name} - Image {i + 1}",
                    }
                    rows.append(image_row)
        
        return rows

    def _create_base_row(self, handle: str, product: Product) -> Dict:
        body_html = product.description
        if product.rating:
            body_html += f"\n\nRating: {product.rating}/5 ({product.reviews_count} reviews)"
        
        tags = ";".join(product.tags) if product.tags else product.category
        
        return {
            "Handle": handle,
            "Title": product.name,
            "Body (HTML)": body_html,
            "Vendor": product.vendor or self.vendor_name,
            "Type": product.category,
            "Tags": tags,
            "Published": "TRUE",
            "Option1 Name": "",
            "Option1 Value": "",
            "Option2 Name": "",
            "Option2 Value": "",
            "Variant SKU": "",
            "Variant Barcode": "",
            "Variant Price": "",
            "Variant Compare At Price": "",
            "Variant Weight": "",
            "Variant Weight Unit": "kg",
            "Variant Inventory Tracker": "shopify",
            "Variant Inventory Qty": "0",
            "Variant Inventory Policy": "continue",
            "Variant Fulfillment Service": "manual",
            "Variant Requires Shipping": "true",
            "Variant Tax Code": "",
            "Image Src": "",
            "Image Position": "1",
            "Image Alt Text": "",
            "Gift Card": "false",
            "SEO Title": product.name,
            "SEO Description": product.description[:160] if product.description else "",
        }

    def save_csv(self, products: List[Product], output_path: Path) -> str:
        if not products:
            logger.warning("No products to save")
            return ""

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            rows = self.generate_csv_rows(products)
            
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=self.SHOPIFY_FIELDS, restval="")
                writer.writeheader()
                writer.writerows(rows)
            
            logger.info(f"Shopify CSV saved: {output_path} ({len(products)} products, {len(rows)} rows)")
            return str(output_path)
        
        except IOError as e:
            logger.error(f"Error saving Shopify CSV: {e}")
            return ""

    def save_by_category(self, products_by_category: Dict[str, List[Product]], base_path: Path) -> Dict[str, str]:
        saved_files = {}
        
        for category, products in products_by_category.items():
            output_path = base_path / category / "shopify_products.csv"
            saved_path = self.save_csv(products, output_path)
            
            if saved_path:
                saved_files[category] = saved_path
        
        return saved_files

    def save_by_category_subcategory(
        self,
        products_by_category: Dict[str, Dict[str, List[Product]]],
        base_path: Path
    ) -> Dict[str, Dict[str, str]]:
        saved_files = {}
        
        for category, subcategories in products_by_category.items():
            saved_files[category] = {}
            
            for subcategory, products in subcategories.items():
                output_path = base_path / category / subcategory / "shopify_products.csv"
                saved_path = self.save_csv(products, output_path)
                
                if saved_path:
                    saved_files[category][subcategory] = saved_path
        
        return saved_files
