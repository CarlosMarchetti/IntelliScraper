import json
import csv
from pathlib import Path
from typing import List, Optional, Dict
from .product import Product
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ProductRepository:
    def __init__(self, base_path: str = "products"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.products: Dict[str, Dict[str, List[Product]]] = {}

    def _get_category_path(self, category: str, subcategory: str) -> Path:
        path = self.base_path / category / subcategory
        path.mkdir(parents=True, exist_ok=True)
        return path

    def add_product(self, product: Product) -> None:
        if product.category not in self.products:
            self.products[product.category] = {}
        
        if product.subcategory not in self.products[product.category]:
            self.products[product.category][product.subcategory] = []
        
        self.products[product.category][product.subcategory].append(product)
        logger.debug(f"Product added: {product.name} ({product.category}/{product.subcategory})")

    def get_products(self, category: str, subcategory: Optional[str] = None) -> List[Product]:
        if category not in self.products:
            return []
        
        if subcategory is None:
            all_products = []
            for subs in self.products[category].values():
                all_products.extend(subs)
            return all_products
        
        return self.products[category].get(subcategory, [])

    def save_json(self, category: str, subcategory: str) -> str:
        products = self.get_products(category, subcategory)
        if not products:
            logger.warning(f"No products to save for {category}/{subcategory}")
            return ""

        path = self._get_category_path(category, subcategory)
        file_path = path / "products.json"

        data = [p.to_dict() for p in products]
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(products)} products to {file_path}")
            return str(file_path)
        except IOError as e:
            logger.error(f"Error saving JSON: {e}")
            return ""

    def save_csv(self, category: str, subcategory: str) -> str:
        products = self.get_products(category, subcategory)
        if not products:
            logger.warning(f"No products to save for {category}/{subcategory}")
            return ""

        path = self._get_category_path(category, subcategory)
        file_path = path / "products.csv"

        try:
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "name", "description", "price", "url", "category",
                    "subcategory", "rating", "reviews_count", "availability",
                    "tags", "vendor", "sku", "weight", "scraped_at"
                ])
                writer.writeheader()
                
                for product in products:
                    row = product.to_dict()
                    row["tags"] = ";".join(row["tags"])
                    row.pop("images", None)
                    row.pop("variants", None)
                    writer.writerow(row)
            
            logger.info(f"Saved {len(products)} products to {file_path}")
            return str(file_path)
        except IOError as e:
            logger.error(f"Error saving CSV: {e}")
            return ""

    def save_all(self) -> Dict[str, List[str]]:
        saved_files = {"json": [], "csv": []}
        
        for category, subcategories in self.products.items():
            for subcategory in subcategories.keys():
                json_file = self.save_json(category, subcategory)
                csv_file = self.save_csv(category, subcategory)
                
                if json_file:
                    saved_files["json"].append(json_file)
                if csv_file:
                    saved_files["csv"].append(csv_file)
        
        return saved_files

    def get_stats(self) -> Dict:
        total_products = 0
        categories = {}
        
        for category, subcategories in self.products.items():
            for subcategory, products_list in subcategories.items():
                total_products += len(products_list)
                if category not in categories:
                    categories[category] = {}
                categories[category][subcategory] = len(products_list)
        
        return {
            "total_products": total_products,
            "categories": categories,
            "total_categories": len(self.products)
        }
